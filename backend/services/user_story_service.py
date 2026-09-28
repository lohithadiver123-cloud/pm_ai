"""
Automatic User Story and Acceptance Criteria Generation Service for Milestone 3.
Transforms PRDs, feature clusters, or custom requirements into Agile User Stories
with Gherkin Acceptance Criteria, Fibonacci estimation, T-Shirt sizing, and Kanban status tracking.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from config import settings
from services.ai_service import get_gemini_client, get_groq_client, _extract_json_from_text, GEMINI_MODELS, GROQ_MODELS
from services.prd_service import get_prd_by_id
import database
from database import db
import fallback_db

logger = logging.getLogger(__name__)


def _generate_fallback_stories(
    subject: str,
    prd_title: Optional[str] = None,
    count: int = 5,
    persona: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Deterministic Agile decomposition when AI models are unavailable."""
    target_role = persona or "Active Product User"
    
    templates = [
        {
            "title": f"Initiate and configure {subject}",
            "role": target_role,
            "action": f"access a streamlined interface for {subject}",
            "benefit": "I can accomplish my core workflow quickly without encountering friction or confusion",
            "points": 3,
            "size": "S",
            "priority": "high",
            "criteria": [
                {"scenario": f"First-time interaction with {subject}", "given": "the user navigates to the feature screen", "when": "the interface renders", "then": "a clear guided onboarding tooltip highlights the primary action button"},
                {"scenario": "Input validation", "given": "the user submits invalid parameters", "when": "validation runs", "then": "inline error highlights specify the exact field requiring attention"}
            ],
            "dod": ["Unit test coverage >= 85%", "Accessible via keyboard navigation", "API response time < 300ms"],
            "tech": f"Create POST /api/{subject.lower().replace(' ', '-')}/initiate endpoint with payload validation."
        },
        {
            "title": f"Real-time status updates and telemetry for {subject}",
            "role": target_role,
            "action": f"receive immediate visual feedback and status badges when {subject} is processing",
            "benefit": "I never have to guess whether my request succeeded or is still in progress",
            "points": 5,
            "size": "M",
            "priority": "high",
            "criteria": [
                {"scenario": "Background job underway", "given": "the user triggered an asynchronous action", "when": "the job is running", "then": "an animated progress indicator renders with estimated completion time"},
                {"scenario": "Job completes successfully", "given": "the background task finishes", "when": "server emits completion event", "then": "a green success banner appears and the UI updates without page reload"}
            ],
            "dod": ["WebSocket/Polling subscription tested under network disconnect", "Cross-browser verified", "Error states styled"],
            "tech": "Implement Server-Sent Events (SSE) or optimistic UI update pattern."
        },
        {
            "title": f"Graceful error recovery and retry mechanism for {subject}",
            "role": target_role,
            "action": "see human-friendly troubleshooting steps and a one-click retry button when an error occurs",
            "benefit": "I can recover immediately without losing my work or contacting customer support",
            "points": 2,
            "size": "XS",
            "priority": "medium",
            "criteria": [
                {"scenario": "Network timeout occurs", "given": "the user has submitted a request", "when": "a 504 Gateway Timeout is returned", "then": "the system shows 'Network issue detected' with a prominent 'Retry Now' button"},
                {"scenario": "Automatic offline retry", "given": "the user goes offline", "when": "connection is restored", "then": "pending actions are replayed automatically"}
            ],
            "dod": ["Idempotency keys implemented", "Telemetry logged to Sentry/Datadog", "No infinite retry loops"],
            "tech": "Add Exponential backoff retry handler with client-side UUID idempotency key."
        },
        {
            "title": f"Self-service history and audit log for {subject}",
            "role": target_role,
            "action": f"view a searchable history of all past events related to {subject}",
            "benefit": "I can audit past actions and verify historical outcomes anytime",
            "points": 5,
            "size": "M",
            "priority": "medium",
            "criteria": [
                {"scenario": "User filters history by date", "given": "user is on the history tab", "when": "they select 'Last 30 Days'", "then": "table filters instantly and displays paginated results"},
                {"scenario": "Export history records", "given": "results are displayed", "when": "user clicks 'Export CSV'", "then": "a standardized CSV file downloads within 2 seconds"}
            ],
            "dod": ["Pagination tested with 5,000+ items", "CSV injection protection added", "Design review approved"],
            "tech": "Index database collection on (workspace_id, user_id, created_at)."
        },
        {
            "title": f"Admin controls and permission policy for {subject}",
            "role": "Product Admin / Workspace Owner",
            "action": f"configure permissions, thresholds, and limits for {subject}",
            "benefit": "our team can safeguard organizational compliance and prevent accidental misuse",
            "points": 8,
            "size": "L",
            "priority": "low",
            "criteria": [
                {"scenario": "Restricted role attempts unauthorized action", "given": "a user with 'Viewer' permissions", "when": "they attempt to modify settings", "then": "the button is disabled and a tooltip explains permission requirements"},
                {"scenario": "Admin updates security threshold", "given": "an Admin user", "when": "they save updated rules", "then": "the changes take effect across all active sessions within 60 seconds"}
            ],
            "dod": ["Role-based access control (RBAC) middleware verified", "Security penetration tested", "Audit trail logged"],
            "tech": "Integrate JWT claims validation and RBAC policy evaluation."
        }
    ]

    results = []
    for idx, t in enumerate(templates[:count]):
        full_stmt = f"As a {t['role']}, I want to {t['action']}, so that {t['benefit']}."
        results.append({
            "title": t["title"],
            "role": t["role"],
            "action": t["action"],
            "benefit": t["benefit"],
            "full_statement": full_stmt,
            "acceptance_criteria": t["criteria"],
            "story_points": t["points"],
            "t_shirt_size": t["size"],
            "priority": t["priority"],
            "definition_of_done": t["dod"],
            "technical_notes": t["tech"]
        })

    return results


async def generate_user_stories_with_ai(
    workspace_id: str,
    prd_id: Optional[str] = None,
    feature_cluster_id: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    count: int = 5,
    persona: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generate Agile user stories with Gherkin acceptance criteria
    using Google Gemini with Groq and heuristic fallback.
    """
    count = max(1, min(count, 10))
    subject = custom_prompt or "Product Feature Enhancement"
    context_notes = []

    # 1. Gather context from PRD if provided
    prd_doc = None
    if prd_id:
        prd_doc = await get_prd_by_id(prd_id)
        if prd_doc:
            subject = prd_doc.get("title", subject)
            frs = prd_doc.get("functional_requirements", [])
            for fr in frs:
                context_notes.append(f"- Requirement {fr.get('id')}: {fr.get('title')} ({fr.get('description')})")
            if prd_doc.get("problem_statement"):
                context_notes.append(f"Problem Statement: {prd_doc.get('problem_statement')}")

    # 2. Gather context from Feature Cluster if provided
    if feature_cluster_id:
        cached_insights = None
        if database._mongodb_available:
            cached_insights = await db.workspace_insights.find_one({"workspace_id": workspace_id})
        else:
            cached_insights = await fallback_db.get_workspace_insights(workspace_id)
            
        if cached_insights:
            for c in cached_insights.get("feature_clusters", []):
                if c.get("id") == feature_cluster_id:
                    subject = c.get("cluster_name", subject)
                    context_notes.append(f"Feature Cluster Demand: {c.get('summary')}")
                    sample_reqs = c.get("sample_requests", []) or c.get("distinct_sample_quotes", [])
                    if sample_reqs:
                        context_notes.append("Customer Wishes: " + "; ".join(sample_reqs[:3]))
                    break

    context_str = "\n".join(context_notes) if context_notes else f"Decompose capability '{subject}' into sprint-ready stories."

    prompt = f"""You are a Principal Agile Product Owner and Scrum Master.
Generate exactly {count} production-ready, vertical Agile User Stories for:
Topic / Subject: {subject}
Target Persona: {persona or 'End User / Product Practitioner'}

Context & Functional Requirements:
{context_str}

Return ONLY a valid JSON object matching this schema:
{{
  "stories": [
    {{
      "title": "Short punchy story title",
      "role": "Specific User Persona Role",
      "action": "clear specific capability user performs",
      "benefit": "clear user or business value delivered",
      "acceptance_criteria": [
        {{
          "scenario": "Descriptive scenario name",
          "given": "precondition statement",
          "when": "user action or system trigger",
          "then": "observable verifiable outcome"
        }},
        {{
          "scenario": "Alternative or error flow",
          "given": "precondition statement",
          "when": "action occurs",
          "then": "observable verifiable outcome"
        }}
      ],
      "story_points": 3,
      "t_shirt_size": "S",
      "priority": "high",
      "definition_of_done": [
        "Unit test coverage >= 85%",
        "Accessibility checks passed",
        "API contract reviewed"
      ],
      "technical_notes": "Key backend endpoints, database schema changes, or UI state considerations"
    }}
  ]
}}

Rules:
- Provide exactly {count} distinct vertical user stories.
- Every story MUST have 2-3 Gherkin scenarios with 'given', 'when', 'then'.
- Story points MUST be Fibonacci: 1, 2, 3, 5, 8, or 13.
- T-shirt size MUST be: 'XS', 'S', 'M', 'L', or 'XL'.
- Priority MUST be: 'high', 'medium', or 'low'.
- Output strictly valid JSON.
"""

    parsed_stories = None

    # 1. Attempt Google Gemini Pure AI
    gem_client = get_gemini_client()
    if gem_client:
        for g_model in GEMINI_MODELS:
            try:
                from google.genai import types
                logger.info(f"Generating user stories with Google Gemini model {g_model}...")
                response = gem_client.models.generate_content(
                    model=g_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.25,
                    ),
                )
                parsed = _extract_json_from_text(response.text)
                if parsed and "stories" in parsed and isinstance(parsed["stories"], list):
                    parsed_stories = parsed["stories"]
                    logger.info(f"Generated {len(parsed_stories)} user stories via Gemini!")
                    break
            except Exception as e:
                logger.warning(f"Gemini story generation error on {g_model}: {e}. Retrying next...")

    # 2. Attempt Groq AI Fallback
    if not parsed_stories:
        groq_client = get_groq_client()
        if groq_client:
            for m_name in GROQ_MODELS:
                try:
                    logger.info(f"Attempting Groq story generation with {m_name}...")
                    response = groq_client.chat.completions.create(
                        model=m_name,
                        messages=[
                            {"role": "system", "content": "You are a Principal Agile Product Owner. Respond ONLY in valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                        max_tokens=2500,
                        response_format={"type": "json_object"} if m_name in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"] else None
                    )
                    content = response.choices[0].message.content
                    parsed = _extract_json_from_text(content)
                    if parsed and "stories" in parsed and isinstance(parsed["stories"], list):
                        parsed_stories = parsed["stories"]
                        logger.info("Generated user stories via Groq fallback!")
                        break
                except Exception as e:
                    logger.warning(f"Groq story error on {m_name}: {e}...")

    # 3. Fallback Deterministic Engine
    if not parsed_stories:
        logger.info("Using fallback Agile story generator...")
        parsed_stories = _generate_fallback_stories(
            subject=subject,
            prd_title=prd_doc.get("title") if prd_doc else None,
            count=count,
            persona=persona
        )

    # 4. Drop non-object entries, then top up from the deterministic engine so
    #    the caller always receives the requested number of usable stories.
    parsed_stories = [s for s in parsed_stories if isinstance(s, dict)]
    if len(parsed_stories) < count:
        logger.info(f"AI returned {len(parsed_stories)} of {count} stories; topping up deterministically.")
        parsed_stories.extend(_generate_fallback_stories(
            subject=subject,
            prd_title=prd_doc.get("title") if prd_doc else None,
            count=count,
            persona=persona,
        )[: count - len(parsed_stories)])

    # Save stories to Database
    now = datetime.now(timezone.utc)
    created_items = []
    
    for idx, s in enumerate(parsed_stories[:count]):
        story_id = f"us_{uuid.uuid4().hex[:10]}"
        role = s.get("role", persona or "User")
        action = s.get("action", f"use {subject}")
        benefit = s.get("benefit", "I can improve my product experience")
        full_stmt = s.get("full_statement") or f"As a {role}, I want to {action}, so that {benefit}."

        doc: Dict[str, Any] = {
            "id": story_id,
            "workspace_id": workspace_id,
            "prd_id": prd_id,
            "feature_cluster_id": feature_cluster_id,
            "title": s.get("title", f"Story #{idx+1}: {subject}"),
            "role": role,
            "action": action,
            "benefit": benefit,
            "full_statement": full_stmt,
            "acceptance_criteria": s.get("acceptance_criteria", []),
            "story_points": int(s.get("story_points", 3)),
            "t_shirt_size": s.get("t_shirt_size", "M"),
            "priority": s.get("priority", "medium"),
            "status": "backlog",
            "definition_of_done": s.get("definition_of_done", ["Unit tests written", "Code reviewed"]),
            "technical_notes": s.get("technical_notes", ""),
            "ai_generated": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        created_items.append(doc)

    if database._mongodb_available:
        if created_items:
            await db.user_stories.insert_many([dict(item) for item in created_items])
    else:
        await fallback_db.bulk_save_stories([dict(item) for item in created_items])

    return created_items


async def get_stories_for_workspace(
    workspace_id: str,
    prd_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieve user stories belonging to a workspace with optional PRD filter."""
    if database._mongodb_available:
        query: Dict[str, Any] = {"workspace_id": workspace_id}
        if prd_id:
            query["prd_id"] = prd_id
        cursor = db.user_stories.find(query).sort("created_at", -1)
        records = await cursor.to_list(length=None)
        for r in records:
            if "_id" in r:
                r["_id"] = str(r["_id"])
        return records
    else:
        return await fallback_db.find_stories_by_workspace(workspace_id, prd_id=prd_id)


async def get_story_by_id(story_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single user story by ID."""
    if database._mongodb_available:
        story = await db.user_stories.find_one({"id": story_id})
        if story and "_id" in story:
            story["_id"] = str(story["_id"])
        return story
    else:
        return await fallback_db.find_story_by_id(story_id)


async def update_story(story_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user story fields."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    if database._mongodb_available:
        await db.user_stories.update_one({"id": story_id}, {"$set": updates})
        return await get_story_by_id(story_id)
    else:
        return await fallback_db.update_story(story_id, updates)


async def update_story_status(story_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Quick update of Kanban status (backlog, in_progress, in_review, done)."""
    return await update_story(story_id, {"status": status})


async def delete_story(story_id: str) -> bool:
    """Delete a user story."""
    if database._mongodb_available:
        res = await db.user_stories.delete_one({"id": story_id})
        return res.deleted_count > 0
    else:
        return await fallback_db.delete_story(story_id)
