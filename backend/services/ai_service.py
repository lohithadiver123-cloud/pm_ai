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

# Gemini models ordered by performance and stability
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-flash-latest",
]

# Groq fallback models
GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "allam-2-7b",
]


def get_gemini_client():
    """Create and return a Google GenAI client if an API key is configured."""
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini client: {e}")
        return None


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
    """Check whether Google Gemini or Groq AI is configured and functional."""
    gem_client = get_gemini_client()
    if gem_client:
        return {
            "available": True,
            "provider": "Google Gemini (Pure AI)",
            "model": "gemini-3.6-flash",
            "status": "Active",
            "message": "Google Gemini 3.6 Flash active with 1,000,000 token context."
        }

    groq_client = get_groq_client()
    if groq_client:
        return {
            "available": True,
            "provider": "Groq",
            "model": GROQ_MODELS[0],
            "status": "Active",
            "message": f"Groq AI active using {GROQ_MODELS[0]}."
        }

    return {
        "available": False,
        "provider": "None",
        "model": "None",
        "status": "No API key configured",
        "message": "Running in fallback heuristic mode."
    }


def _extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Robustly extract a JSON object from raw LLM response text.
    Handles markdown code fences, thinking tags, and leading/trailing prose.
    """
    if not text:
        return None

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    cleaned = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

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


def _get_stratified_substantive_sample(feedback_records: List[Dict[str, Any]], max_sample_size: int = 120) -> List[str]:
    """
    Stratified sampling of substantive customer reviews for datasets of up to 50,000+ items.
    Filters out 1-2 word noise and collects high-signal representative reviews.
    """
    substantive_items = []
    for item in feedback_records:
        text = f"{item.get('title') or ''} {item.get('content') or ''}".strip()
        words = text.split()
        if len(words) >= 3:
            substantive_items.append((item, text, len(words)))

    if not substantive_items:
        substantive_items = [(it, f"{it.get('title') or ''} {it.get('content') or ''}".strip(), 1) for it in feedback_records]

    complaints = []
    feature_wishes = []
    praise_items = []

    feat_keywords = ["add", "feature", "wish", "please", "would like", "need", "update", "option", "bring back", "improve", "support for", "allow", "button", "scroll", "mode"]

    for item, text, word_len in substantive_items:
        rating = item.get("rating")
        text_lower = text.lower()
        is_feat = any(kw in text_lower for kw in feat_keywords)
        is_neg = (rating is not None and rating <= 2) or item.get("sentiment") == "negative" or any(kw in text_lower for kw in ["bug", "crash", "error", "broken", "ads", "suspend", "deactivated", "stuck", "lag", "slow", "terrible", "worst", "hate"])

        if is_feat and not (rating is not None and rating == 1 and not any(k in text_lower for k in ["add", "option", "feature", "bring back"])):
            feature_wishes.append((item, text))
        elif is_neg:
            complaints.append((item, text))
        else:
            praise_items.append((item, text))

    selected_items = []
    
    # 1. Complaints (up to 60)
    step_c = max(1, len(complaints) // 60)
    for i in range(0, min(len(complaints), 60 * step_c), step_c):
        selected_items.append(complaints[i])
        if len(selected_items) >= 60:
            break

    # 2. Feature Wishes (up to 40)
    step_f = max(1, len(feature_wishes) // 40)
    for i in range(0, min(len(feature_wishes), 40 * step_f), step_f):
        selected_items.append(feature_wishes[i])
        if len(selected_items) >= 100:
            break

    # 3. Praise (up to 20)
    step_p = max(1, len(praise_items) // 20)
    for i in range(0, min(len(praise_items), 20 * step_p), step_p):
        selected_items.append(praise_items[i])
        if len(selected_items) >= max_sample_size:
            break

    formatted_lines = []
    for idx, (it, text) in enumerate(selected_items[:max_sample_size]):
        rating = it.get("rating")
        rating_str = f" ({rating}★)" if rating else ""
        clean_text = text.replace("\n", " ")[:160]
        formatted_lines.append(f"[{idx+1}]{rating_str} {clean_text}")

    return formatted_lines


def analyze_feedback_with_ai(feedback_records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Run 100% Pure AI feedback understanding using Google Gemini with Groq fallback.
    Produces authentic themes, pain points with root causes, feature clusters, and executive summary.
    """
    if not feedback_records:
        return None

    formatted_sample = _get_stratified_substantive_sample(feedback_records, max_sample_size=100)
    feedback_text = "\n".join(formatted_sample)

    prompt = f"""You are a Principal AI Product Manager analyzing real customer reviews.
Generate deep, authentic product intelligence based STRICTLY on the real feedback below.
Do NOT invent generic SaaS categories (like CSV/Excel exports) unless explicitly discussed by users.

Return ONLY a valid JSON object matching this schema:
{{
  "ai_summary": {{
    "headline": "Short strategic summary headline",
    "overview": "2-3 sentence executive overview of customer sentiment, friction, and app health",
    "top_frictions": ["Friction 1", "Friction 2", "Friction 3"],
    "quick_wins": ["Actionable quick win 1", "Actionable quick win 2"]
  }},
  "themes": [
    {{
      "title": "Clear Domain Theme Name",
      "description": "Why users are discussing this theme",
      "category": "bug_report",
      "keywords": ["kw1", "kw2"]
    }}
  ],
  "pain_points": [
    {{
      "title": "Specific authentic pain point title",
      "description": "User experience description of the friction",
      "root_cause": "Underlying technical, moderation, or UX root cause",
      "severity": "high",
      "impact_score": 88.0,
      "category": "bug_report",
      "recommended_action": "Actionable engineering/PM recommendation",
      "keywords": ["kw1", "kw2"]
    }}
  ],
  "feature_clusters": [
    {{
      "cluster_name": "Specific User-Requested Feature Opportunity",
      "summary": "Clear summary of user demand and product value proposition",
      "demand_level": "high",
      "priority_score": 90.0,
      "keywords": ["kw1", "kw2"]
    }}
  ]
}}

Requirements:
- Ground all insights 100% in the real customer reviews provided.
- Provide exactly 5 distinct themes.
- Provide exactly 5 prioritized customer pain points (severity: 'high'/'medium'/'low').
- Provide exactly 5 specific feature request clusters (demand: 'high'/'medium'/'low', priority: 25-95).
- Output valid JSON only.

Customer Reviews Corpus (Sampled from {len(feedback_records)} records):
{feedback_text}
"""

    # 1. Try Google Gemini (Pure AI)
    gem_client = get_gemini_client()
    if gem_client:
        for g_model in GEMINI_MODELS:
            try:
                from google.genai import types
                logger.info(f"Executing Pure AI analysis with Google Gemini model {g_model}...")
                response = gem_client.models.generate_content(
                    model=g_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                parsed = _extract_json_from_text(response.text)
                if parsed and "pain_points" in parsed and "themes" in parsed and "feature_clusters" in parsed:
                    parsed["ai_model"] = f"Google Gemini ({g_model})"
                    logger.info(f"Google Gemini analysis succeeded with {g_model}!")
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini model {g_model} error: {e}. Trying next...")

    # 2. Try Groq AI Fallback
    groq_client = get_groq_client()
    if groq_client:
        for model_name in GROQ_MODELS:
            try:
                logger.info(f"Attempting Groq AI fallback using {model_name}...")
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a Principal AI Product Manager. Respond ONLY in valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=2200,
                    response_format={"type": "json_object"} if model_name in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"] else None
                )
                raw_content = response.choices[0].message.content
                parsed = _extract_json_from_text(raw_content)
                if parsed and "pain_points" in parsed and "themes" in parsed and "feature_clusters" in parsed:
                    parsed["ai_model"] = f"Groq ({model_name})"
                    logger.info(f"Groq AI fallback succeeded with {model_name}!")
                    return parsed
            except Exception as e:
                logger.warning(f"Groq model {model_name} error: {e}. Trying next...")

    logger.error("All AI providers failed. Falling back to heuristic engine.")
    return None



