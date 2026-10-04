"""
Conversational Product Intelligence Assistant (PM Copilot) Service for Milestone 3.
Provides grounded, multi-turn AI chat answering complex product management questions
by dynamically retrieving context from ingested customer feedback, themes, pain points,
PRDs, and feature prioritization rankings.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from config import settings
from services.ai_service import get_gemini_client, get_groq_client, get_mistral_client, _extract_json_from_text, GEMINI_MODELS, GROQ_MODELS, MISTRAL_MODELS
from services.prd_service import get_prds_for_workspace
from services.user_story_service import get_stories_for_workspace
import database
from database import db
import fallback_db

logger = logging.getLogger(__name__)


async def build_workspace_pm_context(workspace_id: str) -> Dict[str, Any]:
    """
    Assemble complete product knowledge base for the workspace:
    - Feedback count & sentiment breakdown
    - Top Themes
    - Customer Pain Points with root causes
    - Feature Clusters with priority scores
    - Existing PRD titles
    - High-frequency customer quotes
    """
    context: Dict[str, Any] = {
        "workspace_id": workspace_id,
        "total_feedback": 0,
        "themes": [],
        "pain_points": [],
        "feature_clusters": [],
        "sample_quotes": [],
        "existing_prds": [],
        "user_stories_count": 0,
    }

    # 1. Insights
    cached_insights = None
    if database._mongodb_available:
        cached_insights = await db.workspace_insights.find_one({"workspace_id": workspace_id})
    else:
        cached_insights = await fallback_db.get_workspace_insights(workspace_id)

    if cached_insights:
        context["total_feedback"] = cached_insights.get("total_analyzed", 0)
        context["health_score"] = cached_insights.get("health_score", 65.0)
        context["sentiment_distribution"] = cached_insights.get("sentiment_distribution", {})
        
        for t in cached_insights.get("themes", [])[:5]:
            context["themes"].append(f"{t.get('title')} ({t.get('frequency', 0)} mentions, {t.get('category')})")
            
        for pp in cached_insights.get("pain_points", [])[:5]:
            context["pain_points"].append({
                "id": pp.get("id"),
                "title": pp.get("title"),
                "severity": pp.get("severity"),
                "impact_score": pp.get("impact_score"),
                "root_cause": pp.get("root_cause"),
                "action": pp.get("recommended_action"),
                "sample_quote": (pp.get("sample_quotes") or [""])[0][:120]
            })
            
        for fc in cached_insights.get("feature_clusters", [])[:5]:
            context["feature_clusters"].append({
                "id": fc.get("id"),
                "name": fc.get("cluster_name"),
                "demand": fc.get("demand_level"),
                "priority_score": fc.get("priority_score"),
                "summary": fc.get("summary")
            })

    # 2. Feedback Quotes
    if database._mongodb_available:
        cursor = db.feedback.find({"workspace_id": workspace_id}).sort("created_at", -1).limit(12)
        records = await cursor.to_list(length=12)
        context["total_feedback"] = max(context["total_feedback"], await db.feedback.count_documents({"workspace_id": workspace_id}))
    else:
        records = await fallback_db.find_all_feedback_by_workspace(workspace_id)
        context["total_feedback"] = max(context["total_feedback"], len(records))
        records = records[:12]

    for r in records:
        txt = r.get("content", "")
        if txt and len(txt) > 15:
            rating = f"[{r.get('rating')}★] " if r.get("rating") else ""
            context["sample_quotes"].append(f"{rating}\"{txt[:140]}\"")

    # 3. Existing PRDs & Stories
    prds = await get_prds_for_workspace(workspace_id)
    context["existing_prds"] = [p.get("title") for p in prds]
    stories = await get_stories_for_workspace(workspace_id)
    context["user_stories_count"] = len(stories)

    return context


# Displayed whenever the deterministic engine answers instead of an AI model, so the
# user always knows whether they are reading model output or the workspace's own data.
FALLBACK_DISCLOSURE = (
    "Answered by the deterministic engine (no AI provider reachable): every number above "
    "comes from this workspace's stored analysis."
)


def _generate_fallback_chat_reply(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Context-aware PM assistance built from the workspace's own analysis when AI is down."""
    msg_lower = message.lower()
    total_fb = context.get("total_feedback", 0)
    pain_points = context.get("pain_points", [])
    clusters = context.get("feature_clusters", [])
    themes = context.get("themes", [])

    sources = []
    followups = [
        "What are our highest severity pain points?",
        "Which feature has the highest priority score?",
        "Draft a PRD for the most requested feature",
        "Summarize recent negative customer feedback",
    ][: (2 if not pain_points and not clusters else 4)]
    action = None

    if any(k in msg_lower for k in ["pain", "complain", "issue", "bug", "crash", "problem", "frustrat", "friction"]):
        pp_list = "\n".join([f"- **{p['title']}** (Severity: `{p['severity'].upper()}`, Impact: `{p['impact_score']}`)\n  *Root Cause:* {p.get('root_cause', 'N/A')}\n  *Action:* {p.get('action', 'N/A')}" for p in pain_points[:3]]) if pain_points else "No active pain points recorded."
        reply = (
            f"### Top Customer Pain Points & Friction Analysis\n\n"
            f"From **{total_fb:,} analysed feedback records** in this workspace, ranked by measured impact:\n\n"
            f"{pp_list}\n\n"
            f"> {FALLBACK_DISCLOSURE}"
        )
        for p in pain_points[:2]:
            sources.append({"type": "pain_point", "title": p["title"], "detail": f"Impact Score: {p.get('impact_score')}"})
        action = {
            "action_type": "create_prd",
            "label": "Generate PRD for the top pain point",
            "payload": {"pain_point_id": pain_points[0].get("id") if pain_points else None},
        }

    elif any(k in msg_lower for k in ["feature", "request", "cluster", "build", "opportunity", "want", "wish"]):
        fc_list = "\n".join([f"- **{c['name']}** (Demand: `{c['demand'].upper()}`, Priority Score: `{c['priority_score']}`)\n  *{c.get('summary', '')}*" for c in clusters[:3]]) if clusters else "No feature clusters recorded."
        reply = (
            f"### Top Requested Features & Product Opportunities\n\n"
            f"The **{total_fb:,} analysed records** in this workspace group into these demand areas:\n\n"
            f"{fc_list}\n\n"
            f"You can turn any of them into a PRD or a set of sprint stories from the workspace pages.\n\n"
            f"> {FALLBACK_DISCLOSURE}"
        )
        for c in clusters[:2]:
            sources.append({"type": "feature_cluster", "title": c["name"], "detail": f"Priority Score: {c.get('priority_score')}"})
        action = {
            "action_type": "create_prd",
            "label": "Generate PRD for the top opportunity",
            "payload": {"feature_cluster_id": clusters[0].get("id") if clusters else None},
        }

    elif any(k in msg_lower for k in ["prd", "requirement", "spec", "document"]):
        reply = (
            f"### PRD Generation Readiness\n\n"
            f"This workspace has **{len(clusters)} demand clusters** and **{len(pain_points)} ranked "
            f"pain points** that a document can be grounded on.\n\n"
            f"Open **PRD Studio** and pick one, or describe the brief yourself.\n\n"
            f"> {FALLBACK_DISCLOSURE}"
        )
        action = {"action_type": "create_prd", "label": "Open PRD Studio", "payload": {}}

    else:
        top_th = ", ".join(themes[:3]) if themes else "none yet — run the analysis on this workspace"
        reply = (
            f"### Workspace Overview\n\n"
            f"This workspace holds **{total_fb:,} analysed feedback records**.\n\n"
            f"- **Themes:** {top_th}\n"
            f"- **Pain points:** {len(pain_points)} ranked by measured impact\n"
            f"- **Demand clusters:** {len(clusters)} grouped from the feedback\n"
            f"- **PRDs in this workspace:** {len(context.get('existing_prds', []))}\n\n"
            f"Ask me about sentiment, prioritisation, user stories, or the evidence behind any of these.\n\n"
            f"> {FALLBACK_DISCLOSURE}"
        )

    return {
        "reply": reply,
        "sources_cited": sources,
        "suggested_followups": followups,
        "action_suggested": action,
        "ai_model": "PM Copilot Intelligence Engine"
    }


async def chat_with_pm_copilot(
    workspace_id: str,
    message: str,
    session_id: str = "default",
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Execute conversational product intelligence using Google Gemini (Pure AI)
    grounded in workspace customer feedback and requirements context.
    """
    context = await build_workspace_pm_context(workspace_id)
    history = conversation_history or []

    # Format history turns
    history_formatted = ""
    for h in history[-6:]:
        role = "User" if h.get("sender") == "user" or h.get("role") == "user" else "Copilot"
        history_formatted += f"{role}: {h.get('content') or h.get('text', '')}\n"

    prompt = f"""You are the PM Copilot — a Principal AI Product Manager and Intelligence Assistant.
You have real-time access to customer feedback data, issue tickets, feature requests, and PRDs for this product workspace.

WORKSPACE KNOWLEDGE BASE:
- Total Analyzed Customer Feedback Items: {context.get('total_feedback', 0):,}
- Sentiment Health Score: {context.get('health_score', 65.0)}/100
- Dominant Themes: {'; '.join(context.get('themes', []))}
- Critical Customer Pain Points: {json.dumps(context.get('pain_points', []), indent=1)}
- Clustered Feature Opportunities: {json.dumps(context.get('feature_clusters', []), indent=1)}
- Real Customer Quotes:
{chr(10).join(context.get('sample_quotes', [])[:8])}
- Existing Workspace PRDs: {', '.join(context.get('existing_prds', [])) or 'None created yet'}

RECENT CONVERSATION:
{history_formatted}

CURRENT USER QUERY:
"{message}"

INSTRUCTIONS:
1. Respond as an insightful, data-driven Principal Product Manager.
2. Ground all answers 100% in the real customer data, pain points, quotes, and metrics above.
3. Structure your answer using clear Markdown (headings, bullet points, callout blocks).
4. Identify which pain points, feature clusters, or customer quotes you cited.
5. Provide 3-4 natural follow-up prompt questions the user might ask next.

Return ONLY a valid JSON object matching this schema:
{{
  "reply": "Rich markdown text response...",
  "sources_cited": [
    {{"type": "pain_point", "title": "Pain point name", "detail": "Impact Score: 88"}},
    {{"type": "feature_cluster", "title": "Feature cluster name", "detail": "Priority Score: 92"}},
    {{"type": "feedback_quote", "title": "Customer quote excerpt", "detail": "Rating / source"}}
  ],
  "suggested_followups": [
    "Suggested question 1?",
    "Suggested question 2?",
    "Suggested question 3?"
  ],
  "action_suggested": {{
    "action_type": "create_prd",
    "label": "Generate PRD for this feature",
    "payload": {{"title": "Title"}}
  }}
}}
"""

    gem_client = get_gemini_client()
    parsed_res = None
    ai_model_name = "Google Gemini 3.6 Flash"

    if gem_client:
        for g_model in GEMINI_MODELS:
            try:
                from google.genai import types
                logger.info(f"Querying PM Copilot with Google Gemini model {g_model}...")
                response = gem_client.models.generate_content(
                    model=g_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                parsed = _extract_json_from_text(response.text)
                if parsed and "reply" in parsed:
                    parsed_res = parsed
                    ai_model_name = f"Google Gemini ({g_model})"
                    break
            except Exception as e:
                logger.warning(f"Gemini Copilot chat error on {g_model}: {e}. Retrying next...")

    # Fallback to Mistral (free Experiment tier, OpenAI-compatible) if Gemini fails
    if not parsed_res:
        mistral_client = get_mistral_client()
        if mistral_client:
            for m_name in MISTRAL_MODELS:
                try:
                    logger.info(f"Attempting Mistral PM Copilot chat using {m_name}...")
                    response = mistral_client.chat.completions.create(
                        model=m_name,
                        messages=[
                            {"role": "system", "content": "You are the PM Copilot. Respond ONLY in valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                        max_tokens=2200,
                        response_format={"type": "json_object"},
                    )
                    content = response.choices[0].message.content
                    parsed = _extract_json_from_text(content)
                    if parsed and "reply" in parsed:
                        parsed_res = parsed
                        ai_model_name = f"Mistral ({m_name})"
                        break
                except Exception as e:
                    logger.warning(f"Mistral Copilot chat error on {m_name}: {e}...")

    # Fallback to Groq if Mistral fails
    if not parsed_res:
        groq_client = get_groq_client()
        if groq_client:
            for m_name in GROQ_MODELS:
                try:
                    logger.info(f"Attempting Groq PM Copilot chat using {m_name}...")
                    response = groq_client.chat.completions.create(
                        model=m_name,
                        messages=[
                            {"role": "system", "content": "You are the PM Copilot. Respond ONLY in valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                        max_tokens=2200,
                        response_format={"type": "json_object"} if m_name in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"] else None
                    )
                    content = response.choices[0].message.content
                    parsed = _extract_json_from_text(content)
                    if parsed and "reply" in parsed:
                        parsed_res = parsed
                        ai_model_name = f"Groq ({m_name})"
                        break
                except Exception as e:
                    logger.warning(f"Groq Copilot chat error on {m_name}: {e}...")

    # Fallback to deterministic response
    if not parsed_res:
        logger.info("Using fallback PM Copilot response generator...")
        parsed_res = _generate_fallback_chat_reply(message, context)
        ai_model_name = parsed_res.get("ai_model", "PM Copilot Intelligence")

    # Save to Chat History
    now = datetime.now(timezone.utc)
    user_msg_doc = {
        "id": f"msg_{uuid.uuid4().hex[:10]}",
        "workspace_id": workspace_id,
        "session_id": session_id,
        "sender": "user",
        "content": message,
        "created_at": now.isoformat(),
    }
    copilot_msg_doc = {
        "id": f"msg_{uuid.uuid4().hex[:10]}",
        "workspace_id": workspace_id,
        "session_id": session_id,
        "sender": "assistant",
        "content": parsed_res.get("reply", ""),
        "sources_cited": parsed_res.get("sources_cited", []),
        "suggested_followups": parsed_res.get("suggested_followups", []),
        "action_suggested": parsed_res.get("action_suggested"),
        "created_at": now.isoformat(),
    }

    if database._mongodb_available:
        await db.copilot_messages.insert_many([user_msg_doc, copilot_msg_doc])
    else:
        await fallback_db.save_copilot_message(user_msg_doc)
        await fallback_db.save_copilot_message(copilot_msg_doc)

    return {
        "reply": parsed_res.get("reply", ""),
        "session_id": session_id,
        "sources_cited": parsed_res.get("sources_cited", []),
        "suggested_followups": parsed_res.get("suggested_followups", []),
        "action_suggested": parsed_res.get("action_suggested"),
        "context_summary": {
            "total_feedback": context.get("total_feedback", 0),
            "themes_count": len(context.get("themes", [])),
            "pain_points_count": len(context.get("pain_points", [])),
            "clusters_count": len(context.get("feature_clusters", [])),
        },
        "ai_model": ai_model_name,
        "timestamp": now.isoformat(),
    }


async def get_copilot_history(workspace_id: str, session_id: str = "default") -> List[Dict[str, Any]]:
    """Retrieve chat message history for a workspace session."""
    if database._mongodb_available:
        cursor = db.copilot_messages.find({"workspace_id": workspace_id, "session_id": session_id}).sort("created_at", 1)
        records = await cursor.to_list(length=100)
        for r in records:
            if "_id" in r:
                r["_id"] = str(r["_id"])
        return records
    else:
        return await fallback_db.get_copilot_history(workspace_id, session_id)


async def clear_copilot_history(workspace_id: str, session_id: str = "default") -> bool:
    """Clear chat history for a workspace session."""
    if database._mongodb_available:
        res = await db.copilot_messages.delete_many({"workspace_id": workspace_id, "session_id": session_id})
        return res.deleted_count > 0
    else:
        return await fallback_db.clear_copilot_history(workspace_id, session_id)
