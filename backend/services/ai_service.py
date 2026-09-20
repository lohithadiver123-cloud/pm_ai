"""
AI Service utilizing Groq LLMs for intelligent feedback understanding,
root-cause pain point analysis, theme extraction, and feature clustering.
Designed for Milestone 2 product insights with graceful fallback to heuristic models.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

# Valid Groq model IDs for this account — ordered with ALLaM prioritized
GROQ_MODELS = [
    "allam-2-7b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "groq/compound-mini",
]


def get_groq_client():
    """Create and return a Groq client if an API key is configured."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client: {e}")
        return None


def check_ai_status() -> Dict[str, Any]:
    """Check whether Groq AI is configured and functional."""
    client = get_groq_client()
    if not client:
        return {
            "available": False,
            "provider": "Groq",
            "model": GROQ_MODELS[0],
            "status": "No API key configured",
            "message": "Running in deterministic heuristic mode. Add a free GROQ_API_KEY to enable LLM intelligence."
        }

    try:
        # Quick ping to verify key
        models = client.models.list()
        return {
            "available": True,
            "provider": "Groq",
            "model": GROQ_MODELS[0],
            "status": "Active",
            "models_count": len(models.data) if hasattr(models, 'data') else 0,
            "message": f"Groq AI active using {GROQ_MODELS[0]}."
        }
    except Exception as e:
        return {
            "available": False,
            "provider": "Groq",
            "model": GROQ_MODELS[0],
            "status": "Authentication/Connection Error",
            "message": str(e)
        }


def _extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Robustly extract a JSON object from raw LLM response text.
    Handles markdown code fences, thinking tags, and leading/trailing prose.
    """
    if not text:
        return None

    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (```json ... ```)
    cleaned = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract outermost JSON object via brace matching
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def analyze_feedback_with_ai(feedback_records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Run Groq LLM intelligence over customer feedback records.
    Produces:
      - AI Executive Summary with key strategic findings
      - Root-Cause Customer Pain Points with calibrated severity & impact
      - High-level Recurring Themes
      - Synthesized Feature Request Clusters with demand levels
    """
    client = get_groq_client()
    if not client or not feedback_records:
        return None

    # Prepare condensed feedback representation for LLM prompt
    sample_items = []
    for idx, item in enumerate(feedback_records[:80]):  # Analyze up to 80 representative records
        title = item.get("title") or "Feedback"
        content = item.get("content") or ""
        rating = item.get("rating")
        rating_str = f" ({rating}★)" if rating else ""
        sample_items.append(f"[{idx+1}]{rating_str} {title}: {content}")

    feedback_text = "\n".join(sample_items)

    system_prompt = (
        "You are an expert AI Principal Product Manager. Your task is to analyze real customer feedback "
        "and generate high-precision product intelligence. "
        "IMPORTANT: Respond with ONLY a valid JSON object. No markdown, no code fences, no explanation — just raw JSON."
    )

    user_prompt = f"""Analyze the following customer feedback entries and return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:

{{
  "ai_summary": {{
    "headline": "Short strategic summary headline",
    "overview": "2-3 sentence executive overview of customer sentiment and product health",
    "top_frictions": ["Key friction 1", "Key friction 2", "Key friction 3"],
    "quick_wins": ["Immediate recommended engineering or UX action 1", "Immediate action 2"]
  }},
  "themes": [
    {{
      "title": "Theme Name",
      "description": "Why users are discussing this theme",
      "category": "bug_report",
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ],
  "pain_points": [
    {{
      "title": "Clear concise pain point title",
      "description": "User experience description of the friction",
      "root_cause": "Underlying technical, system, or UX root cause",
      "severity": "high",
      "impact_score": 85.0,
      "category": "bug_report",
      "recommended_action": "Actionable recommendation for engineering/design",
      "keywords": ["keyword1", "keyword2"]
    }}
  ],
  "feature_clusters": [
    {{
      "cluster_name": "Synthesized Feature Name",
      "summary": "Clear summary of user demand and value proposition",
      "demand_level": "high",
      "priority_score": 88.0,
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ]
}}

Guidelines:
- Provide 5 to 8 distinct recurring themes.
- Provide 5 to 8 customer pain points sorted from highest to lowest impact. Severity must be 'high', 'medium', or 'low'.
- Provide 4 to 7 feature request clusters. Demand level must be 'high', 'medium', or 'low'. Priority score between 20.0 and 98.0.
- Root causes should be insightful technical explanations.
- Return ONLY the raw JSON. No markdown fences, no explanation.

Customer Feedback Data:
{feedback_text}
"""

    for model_name in GROQ_MODELS:
        try:
            logger.info(f"Attempting Groq AI feedback analysis using {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=4000,
            )

            raw_content = response.choices[0].message.content
            parsed = _extract_json_from_text(raw_content)

            # Validate basic structure
            if parsed and "pain_points" in parsed and "themes" in parsed and "feature_clusters" in parsed:
                parsed["ai_model"] = model_name
                logger.info(f"Groq AI analysis succeeded with {model_name}!")
                return parsed

            logger.warning(f"Model {model_name} returned incomplete JSON, trying next...")

        except Exception as e:
            logger.warning(f"Groq analysis with model {model_name} failed: {e}. Trying next model...")

    logger.error("All Groq AI models failed. Falling back to heuristic engine.")
    return None
