"""
PRD (Product Requirement Document) Generation Service for Milestone 3.
Leverages Google Gemini (gemini-3.6-flash) with Groq and heuristic fallback to generate
comprehensive, enterprise-grade PRDs grounded in authentic customer feedback.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from config import settings
from services.ai_service import get_gemini_client, get_groq_client, _extract_json_from_text, GEMINI_MODELS, GROQ_MODELS
import database
from database import db
import fallback_db

logger = logging.getLogger(__name__)


def _build_markdown_from_prd(prd: Dict[str, Any]) -> str:
    """Format structured PRD data into clean, professional GitHub-flavored Markdown."""
    title = prd.get("title", "Product Requirement Document")
    status = prd.get("status", "draft").upper()
    version = prd.get("version", "1.0")
    created = prd.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    md = [
        f"# {title}",
        f"**Status:** `{status}` | **Version:** `{version}` | **Generated:** `{created}`",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        prd.get("executive_summary", "No executive summary provided."),
        "",
        "## 2. Problem Statement & Customer Evidence",
        prd.get("problem_statement", "No problem statement provided."),
        "",
        "## 3. Goals & Success Objectives",
    ]

    for g in prd.get("goals_and_objectives", []):
        md.append(f"- 🎯 {g}")
    md.append("")

    # Personas
    md.append("## 4. Target User Personas")
    for p in prd.get("target_users_and_personas", []):
        md.append(f"### Persona: {p.get('role', 'User')}")
        if p.get("description"):
            md.append(f"*{p.get('description')}*")
        if p.get("pain_points"):
            md.append("**Frictions:**")
            for pp in p.get("pain_points", []):
                md.append(f"  - ⚠️ {pp}")
        if p.get("goals"):
            md.append("**Goals:**")
            for gl in p.get("goals", []):
                md.append(f"  - 🚀 {gl}")
        md.append("")

    # Scope
    md.append("## 5. Scope Definition")
    md.append("### In-Scope (MVP & Fast Follow)")
    for item in prd.get("scope_in", []):
        md.append(f"- ✅ {item}")
    md.append("")
    md.append("### Out-of-Scope (Future Iterations)")
    for item in prd.get("scope_out", []):
        md.append(f"- ❌ {item}")
    md.append("")

    # User Journeys
    if prd.get("user_journeys"):
        md.append("## 6. Key User Journeys")
        for uj in prd.get("user_journeys", []):
            md.append(f"**Step {uj.get('step', 1)} [{uj.get('stage', 'Action')}]:** {uj.get('user_action', '')}")
            md.append(f"> **System Behavior:** {uj.get('system_response', '')}")
            md.append("")

    # Functional Requirements
    md.append("## 7. Functional Requirements")
    for fr in prd.get("functional_requirements", []):
        pri = fr.get("priority", "P1")
        md.append(f"### [{fr.get('id', 'FR')}] {fr.get('title', 'Requirement')} `[{pri}]`")
        md.append(fr.get("description", ""))
        if fr.get("acceptance_criteria"):
            md.append("\n**Acceptance Criteria:**")
            for ac in fr.get("acceptance_criteria", []):
                md.append(f"- [ ] {ac}")
        if fr.get("edge_cases"):
            md.append("\n**Edge Cases:**")
            for ec in fr.get("edge_cases", []):
                md.append(f"- 🔍 {ec}")
        md.append("")

    # Non-Functional Requirements
    md.append("## 8. Non-Functional Requirements (NFRs)")
    for nfr in prd.get("non_functional_requirements", []):
        cat = nfr.get("category", "General")
        md.append(f"- **{cat}:** {nfr.get('requirement', '')}")
    md.append("")

    # Success Metrics
    md.append("## 9. Success Metrics & Key Performance Indicators")
    md.append("| Metric | Baseline | Target | Tracking Mechanism |")
    md.append("| :--- | :--- | :--- | :--- |")
    for m in prd.get("success_metrics_kpis", []):
        md.append(f"| {m.get('metric', '')} | {m.get('baseline', 'N/A')} | {m.get('target', '')} | {m.get('tracking_mechanism', 'Telemetry')} |")
    md.append("")

    # Technical Architecture & Dependencies
    if prd.get("technical_dependencies"):
        md.append("## 10. Technical Architecture & Dependencies")
        for td in prd.get("technical_dependencies", []):
            md.append(f"- ⚙️ {td}")
        md.append("")

    # Risks & Mitigations
    if prd.get("risks_and_mitigations"):
        md.append("## 11. Risks & Mitigation Strategies")
        for rm in prd.get("risks_and_mitigations", []):
            sev = rm.get("severity", "medium").upper()
            md.append(f"- **Risk [{sev}]:** {rm.get('risk', '')}")
            md.append(f"  *Mitigation:* {rm.get('mitigation', '')}")
        md.append("")

    return "\n".join(md)


def _generate_fallback_prd(
    title: str,
    subject: str,
    source_type: str,
    source_details: Dict[str, Any],
    sample_quotes: List[str],
) -> Dict[str, Any]:
    """Generates an extensive, highly structured deterministic PRD when AI providers are offline."""
    clean_title = title or f"PRD: Resolution & Enhancement for {subject}"
    
    return {
        "title": clean_title,
        "executive_summary": (
            f"This Product Requirement Document addresses critical customer needs regarding '{subject}'. "
            f"Synthesizing customer feedback and support tickets, this initiative focuses on delivering a reliable, "
            f"intuitive user experience while reducing customer churn, boosting daily active engagement, "
            f"and eliminating key friction points identified in recent customer sentiment analysis."
        ),
        "problem_statement": (
            f"Users have experienced friction related to {subject}. Customer support tickets and reviews "
            f"show recurring friction: {('; '.join(sample_quotes[:2])) if sample_quotes else 'performance and UX bottlenecks'}. "
            f"Unresolved, this drives negative app store ratings, increased ticket escalation costs, and user abandonment."
        ),
        "target_users_and_personas": [
            {
                "role": "Primary Active User",
                "description": "Daily user relying on the application for essential daily tasks.",
                "pain_points": [f"Encountering unexpected blocks or latency with {subject}", "Lack of transparency and instant feedback"],
                "goals": ["Smooth, error-free workflow", "Immediate recovery options"]
            },
            {
                "role": "Power Creator / Business User",
                "description": "Professional or power user whose business workflow depends on app stability.",
                "pain_points": ["Disruption to customer engagement", "Slow customer support resolution"],
                "goals": ["High reliability and fast operational transparency", "Self-service management"]
            }
        ],
        "goals_and_objectives": [
            f"Achieve a 99.8% success rate for all workflows involving {subject}.",
            "Reduce customer support tickets related to this topic by 60% within 60 days of launch.",
            "Improve App Store / Play Store rating by at least +0.4 stars over the next release cycle."
        ],
        "scope_in": [
            f"End-to-end user experience redesign for {subject}.",
            "Real-time validation, status telemetry, and inline feedback messaging.",
            "Automated fallback and recovery handling to prevent dead-ends.",
            "Analytics instrumentation for user drop-off tracking."
        ],
        "scope_out": [
            "Complete overhaul of unrelated legacy authentication services.",
            "Third-party enterprise SSO integrations (deferred to Phase 2).",
            "Hardware-level biometric offline persistence."
        ],
        "user_journeys": [
            {
                "step": 1,
                "stage": "Trigger",
                "user_action": f"User attempts to interact with {subject}.",
                "system_response": "System displays immediate interactive state with clear progress indication."
            },
            {
                "step": 2,
                "stage": "Execution",
                "user_action": "User inputs details or initiates the action.",
                "system_response": "Asynchronous validation is performed with sub-300ms roundtrip response."
            },
            {
                "step": 3,
                "stage": "Confirmation",
                "user_action": "User completes the step.",
                "system_response": "Success toast is rendered and state is persisted reliably across sessions."
            }
        ],
        "functional_requirements": [
            {
                "id": "FR-01",
                "title": f"Core {subject} Interface & Interaction Layer",
                "description": f"Provide an intuitive, responsive UI interface allowing users to seamlessly configure and interact with {subject}.",
                "priority": "P0",
                "acceptance_criteria": [
                    "User can complete the primary flow in under 3 clicks/taps.",
                    "All inputs undergo client-side validation before network submission.",
                    "Graceful inline error messages are displayed without dismissing user inputs."
                ],
                "edge_cases": [
                    "Loss of network connectivity during submission triggers offline queueing.",
                    "Rapid duplicate button taps are debounced."
                ]
            },
            {
                "id": "FR-02",
                "title": "Automated Status Notification & Transparency",
                "description": "Send immediate push and in-app notifications whenever status changes occur.",
                "priority": "P0",
                "acceptance_criteria": [
                    "In-app badge updates within 2 seconds of background status update.",
                    "Notification contains direct deep link to the relevant action screen."
                ],
                "edge_cases": [
                    "User has system notifications disabled — fallback to prominent in-app banner."
                ]
            },
            {
                "id": "FR-03",
                "title": "Self-Service Diagnostics and Troubleshooting",
                "description": "Provide a guided self-service resolution flow when an issue occurs.",
                "priority": "P1",
                "acceptance_criteria": [
                    "Diagnose common failure codes automatically.",
                    "Provide a one-click 'Retry with Diagnostics' option."
                ],
                "edge_cases": [
                    "Server 500 error provides human-readable guidance rather than raw stack trace."
                ]
            }
        ],
        "non_functional_requirements": [
            {"category": "Performance", "requirement": "P95 response time must remain below 400ms under 10,000 concurrent active users."},
            {"category": "Availability", "requirement": "Target 99.95% uptime with zero-downtime rolling deployments."},
            {"category": "Security", "requirement": "All payloads encrypted in transit via TLS 1.3; sensitive tokens hashed with Argon2/bcrypt."},
            {"category": "Accessibility", "requirement": "Compliant with WCAG 2.1 AA standards including screen reader contrast and dynamic text sizing."}
        ],
        "success_metrics_kpis": [
            {"metric": "Feature Adoption Rate", "baseline": "0%", "target": "65% of active users within 30 days", "tracking_mechanism": "Amplitude / Mixpanel event tracking"},
            {"metric": "Support Ticket Reduction", "baseline": "1,200 tickets/mo", "target": "< 400 tickets/mo", "tracking_mechanism": "Zendesk / Freshdesk tag analytics"},
            {"metric": "Task Completion Success Rate", "baseline": "74%", "target": "98.5%", "tracking_mechanism": "Datadog / PostHog funnels"}
        ],
        "technical_dependencies": [
            "REST API endpoints with idempotency keys for retry safety",
            "Redis distributed lock manager for concurrent transaction protection",
            "MongoDB schema indexes on workspace_id and status fields"
        ],
        "risks_and_mitigations": [
            {
                "risk": "Legacy data migration mismatch for existing user accounts",
                "severity": "medium",
                "mitigation": "Dual-read dual-write background shadow migration for 14 days before cutover"
            },
            {
                "risk": "Third-party rate limits during peak surge traffic",
                "severity": "high",
                "mitigation": "Exponential backoff with circuit breaker and asynchronous background queue worker"
            }
        ]
    }


async def generate_prd_with_ai(
    workspace_id: str,
    title: Optional[str] = None,
    feature_cluster_id: Optional[str] = None,
    pain_point_id: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    target_audience: Optional[str] = None,
    strategic_goals: Optional[str] = None,
    tone: str = "comprehensive",
) -> Dict[str, Any]:
    """
    Generate a complete, enterprise-grade PRD using Google Gemini (Pure AI)
    with Groq fallback and deterministic fallback engine.
    Grounded 100% in workspace feedback and customer evidence.
    """
    # 1. Gather context from workspace
    source_type = "custom"
    source_id = None
    subject = title or custom_prompt or "Core Product Improvement"
    source_details: Dict[str, Any] = {}
    sample_quotes: List[str] = []

    # Check insights for feature cluster or pain point
    cached_insights = None
    if database._mongodb_available:
        cached_insights = await db.workspace_insights.find_one({"workspace_id": workspace_id})
    else:
        cached_insights = await fallback_db.get_workspace_insights(workspace_id)

    if feature_cluster_id and cached_insights:
        for c in cached_insights.get("feature_clusters", []):
            if c.get("id") == feature_cluster_id:
                source_type = "feature_cluster"
                source_id = feature_cluster_id
                subject = c.get("cluster_name", subject)
                source_details = c
                sample_quotes = c.get("sample_requests", []) or c.get("distinct_sample_quotes", [])
                break

    elif pain_point_id and cached_insights:
        for pp in cached_insights.get("pain_points", []):
            if pp.get("id") == pain_point_id:
                source_type = "pain_point"
                source_id = pain_point_id
                subject = pp.get("title", subject)
                source_details = pp
                sample_quotes = pp.get("sample_quotes", []) or pp.get("distinct_sample_quotes", [])
                break

    # If quotes are still empty, fetch top negative or feature quotes from feedback
    if not sample_quotes:
        if database._mongodb_available:
            cursor = db.feedback.find({"workspace_id": workspace_id}).limit(15)
            fbs = await cursor.to_list(length=15)
        else:
            fbs = await fallback_db.find_all_feedback_by_workspace(workspace_id)
            fbs = fbs[:15]
        sample_quotes = [f.get("content", "") for f in fbs if f.get("content")]

    clean_quotes = "\n".join([f"- \"{q[:150]}\"" for q in sample_quotes[:10]])

    prompt = f"""You are a Principal Product Manager and Enterprise Technical Architect at a tier-1 software company.
Write an authentic, comprehensive Product Requirement Document (PRD) for:
Focus / Subject: {subject}
Custom Specifications: {custom_prompt or 'None'}
Target Audience: {target_audience or 'Active mobile & web product users'}
Strategic Goals: {strategic_goals or 'Eliminate friction, boost retention, reduce support costs'}
Tone: {tone}

Real Customer Feedback & Quotes from Workspace:
{clean_quotes if clean_quotes else 'High volume of customer requests for stability, clarity, and enhanced usability.'}

Return ONLY a valid JSON object matching this exact schema:
{{
  "title": "Clear PRD Title",
  "executive_summary": "Thorough executive briefing (2 paragraphs) summarizing the initiative, strategic importance, and expected business outcome.",
  "problem_statement": "Deep root-cause customer problem statement grounded in the provided customer feedback quotes.",
  "target_users_and_personas": [
    {{
      "role": "Persona Role Name",
      "description": "Background and behavior archetype",
      "pain_points": ["Pain point 1", "Pain point 2"],
      "goals": ["Goal 1", "Goal 2"]
    }}
  ],
  "goals_and_objectives": [
    "Quantitative objective 1 with specific target metric",
    "Quantitative objective 2 with specific target metric"
  ],
  "scope_in": ["Key MVP capability 1", "Key MVP capability 2", "Key MVP capability 3"],
  "scope_out": ["Deferred capability 1", "Deferred capability 2"],
  "user_journeys": [
    {{
      "step": 1,
      "stage": "Discovery / Trigger",
      "user_action": "What the user attempts or clicks",
      "system_response": "What the application responds and displays"
    }},
    {{
      "step": 2,
      "stage": "Execution / Interaction",
      "user_action": "User inputs data or performs core action",
      "system_response": "System verifies, processes asynchronously and displays immediate feedback"
    }}
  ],
  "functional_requirements": [
    {{
      "id": "FR-01",
      "title": "Core Requirement Name",
      "description": "Exhaustive technical and behavioral specification",
      "priority": "P0",
      "acceptance_criteria": [
        "Given X when Y then Z",
        "Criterion 2"
      ],
      "edge_cases": ["Edge case 1", "Edge case 2"]
    }},
    {{
      "id": "FR-02",
      "title": "Secondary Requirement Name",
      "description": "Exhaustive specification",
      "priority": "P1",
      "acceptance_criteria": ["Criterion 1", "Criterion 2"],
      "edge_cases": ["Edge case 1"]
    }}
  ],
  "non_functional_requirements": [
    {{"category": "Performance", "requirement": "P95 latency SLA"}},
    {{"category": "Security", "requirement": "Compliance and encryption standards"}},
    {{"category": "Scalability", "requirement": "Throughput and concurrency targets"}},
    {{"category": "Accessibility", "requirement": "WCAG 2.1 AA specifications"}}
  ],
  "success_metrics_kpis": [
    {{"metric": "Primary North Star Metric", "baseline": "Current baseline", "target": "Target outcome", "tracking_mechanism": "Analytics event name"}},
    {{"metric": "Customer Satisfaction / NPS", "baseline": "Current", "target": "Target", "tracking_mechanism": "In-app CSAT survey"}}
  ],
  "technical_dependencies": [
    "API endpoint requirements",
    "Database schema updates or indexing",
    "Worker queue or third party services"
  ],
  "risks_and_mitigations": [
    {{"risk": "Specific technical or user adoption risk", "severity": "medium", "mitigation": "Actionable engineering or operational mitigation plan"}}
  ]
}}

Ensure:
- All functional requirements have IDs (FR-01, FR-02, FR-03, etc.).
- Priorities must be 'P0', 'P1', or 'P2'.
- Ground all problem statements in actual customer evidence.
- Return ONLY valid JSON, no markdown formatting around the JSON.
"""

    parsed_result = None
    ai_model_used = None

    # 1. Attempt Google Gemini Pure AI
    gem_client = get_gemini_client()
    if gem_client:
        for g_model in GEMINI_MODELS:
            try:
                from google.genai import types
                logger.info(f"Generating PRD with Google Gemini model {g_model}...")
                response = gem_client.models.generate_content(
                    model=g_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.25,
                    ),
                )
                parsed = _extract_json_from_text(response.text)
                if parsed and "functional_requirements" in parsed and "problem_statement" in parsed:
                    parsed_result = parsed
                    ai_model_used = f"Google Gemini ({g_model})"
                    logger.info("PRD generated successfully with Google Gemini!")
                    break
            except Exception as e:
                logger.warning(f"Gemini PRD generation error on {g_model}: {e}. Retrying next...")

    # 2. Attempt Groq AI Fallback
    if not parsed_result:
        groq_client = get_groq_client()
        if groq_client:
            for m_name in GROQ_MODELS:
                try:
                    logger.info(f"Attempting Groq PRD generation using {m_name}...")
                    response = groq_client.chat.completions.create(
                        model=m_name,
                        messages=[
                            {"role": "system", "content": "You are a Principal Product Manager. Respond ONLY in valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                        max_tokens=3200,
                        response_format={"type": "json_object"} if m_name in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"] else None
                    )
                    content = response.choices[0].message.content
                    parsed = _extract_json_from_text(content)
                    if parsed and "functional_requirements" in parsed:
                        parsed_result = parsed
                        ai_model_used = f"Groq ({m_name})"
                        logger.info("PRD generated successfully with Groq AI fallback!")
                        break
                except Exception as e:
                    logger.warning(f"Groq PRD generation error on {m_name}: {e}...")

    # 3. Deterministic High-Fidelity Fallback if AI offline
    if not parsed_result:
        logger.info("Generating PRD via deterministic PM heuristic engine...")
        parsed_result = _generate_fallback_prd(
            title=title or f"PRD: {subject}",
            subject=subject,
            source_type=source_type,
            source_details=source_details,
            sample_quotes=sample_quotes,
        )
        ai_model_used = "Deterministic PM Engine"

    # 4. Guarantee an actionable minimum when a model returns a valid but thin
    #    document (e.g. the stories/requirements list is truncated).
    requirements = parsed_result.get("functional_requirements") or []
    if len(requirements) < 3:
        logger.info("AI PRD returned fewer than 3 functional requirements; topping up deterministically.")
        filler = _generate_fallback_prd(
            title=title or f"PRD: {subject}",
            subject=subject,
            source_type=source_type,
            source_details=source_details,
            sample_quotes=sample_quotes,
        )
        merged = [dict(fr) for fr in requirements if isinstance(fr, dict)]
        merged.extend(dict(fr) for fr in filler.get("functional_requirements", [])[: 3 - len(merged)])
        # Renumber sequentially so appended IDs cannot collide with the model's.
        for index, fr in enumerate(merged, start=1):
            fr["id"] = f"FR-{index:02d}"
        parsed_result["functional_requirements"] = merged

    # Assemble complete PRD Document
    prd_id = f"prd_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    final_prd: Dict[str, Any] = {
        "id": prd_id,
        "workspace_id": workspace_id,
        "title": parsed_result.get("title", title or f"PRD: {subject}"),
        "status": "draft",
        "version": "1.0",
        "source_type": source_type,
        "source_id": source_id,
        "executive_summary": parsed_result.get("executive_summary", ""),
        "problem_statement": parsed_result.get("problem_statement", ""),
        "target_users_and_personas": parsed_result.get("target_users_and_personas", []),
        "goals_and_objectives": parsed_result.get("goals_and_objectives", []),
        "scope_in": parsed_result.get("scope_in", []),
        "scope_out": parsed_result.get("scope_out", []),
        "user_journeys": parsed_result.get("user_journeys", []),
        "functional_requirements": parsed_result.get("functional_requirements", []),
        "non_functional_requirements": parsed_result.get("non_functional_requirements", []),
        "success_metrics_kpis": parsed_result.get("success_metrics_kpis", []),
        "technical_dependencies": parsed_result.get("technical_dependencies", []),
        "risks_and_mitigations": parsed_result.get("risks_and_mitigations", []),
        "ai_generated": True,
        "ai_model": ai_model_used,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    final_prd["raw_markdown"] = _build_markdown_from_prd(final_prd)

    # Persist in Database
    if database._mongodb_available:
        await db.prds.insert_one(dict(final_prd))
    else:
        await fallback_db.save_prd(dict(final_prd))

    return final_prd


async def get_prds_for_workspace(workspace_id: str) -> List[Dict[str, Any]]:
    """Retrieve all PRDs belonging to a workspace."""
    if database._mongodb_available:
        cursor = db.prds.find({"workspace_id": workspace_id}).sort("created_at", -1)
        records = await cursor.to_list(length=None)
        for r in records:
            if "_id" in r:
                r["_id"] = str(r["_id"])
        return records
    else:
        return await fallback_db.find_prds_by_workspace(workspace_id)


async def get_prd_by_id(prd_id: str) -> Optional[Dict[str, Any]]:
    """Fetch single PRD by ID."""
    if database._mongodb_available:
        prd = await db.prds.find_one({"id": prd_id})
        if prd and "_id" in prd:
            prd["_id"] = str(prd["_id"])
        return prd
    else:
        return await fallback_db.find_prd_by_id(prd_id)


async def update_prd(prd_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update existing PRD details."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # If content changed, rebuild markdown
    existing = await get_prd_by_id(prd_id)
    if not existing:
        return None
        
    merged = {**existing, **updates}
    if "raw_markdown" not in updates:
        updates["raw_markdown"] = _build_markdown_from_prd(merged)

    if database._mongodb_available:
        await db.prds.update_one({"id": prd_id}, {"$set": updates})
        return await get_prd_by_id(prd_id)
    else:
        return await fallback_db.update_prd(prd_id, updates)


async def delete_prd(prd_id: str) -> bool:
    """Delete a PRD."""
    if database._mongodb_available:
        result = await db.prds.delete_one({"id": prd_id})
        return result.deleted_count > 0
    else:
        return await fallback_db.delete_prd(prd_id)
