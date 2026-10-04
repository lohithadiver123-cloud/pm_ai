"""
Insights Router for Milestone 2.
Provides canonical analysis pipeline for theme extraction, customer pain points,
feature request clustering, trend trajectory, and product health scoring.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

import database
from database import db
from models.insights import (
    WorkspaceInsightsResponse,
    ThemeItem,
    PainPointItem,
    FeatureCluster,
    TrendDataPoint,
)
from services.categorization import categorize, detect_sentiment, batch_categorize
from services.theme_extraction import (
    extract_themes_from_feedback,
    extract_pain_points_from_feedback,
    assign_record_theme,
    _resolve_category,
    _resolve_sentiment,
)
from services.clustering import (
    cluster_feature_requests,
    count_unique_requesters,
    workspace_has_customer_identity,
)
from services.preprocessing import STOPWORDS_SET
from services.text_mining import match_records_by_terms as _match_records_by_terms, record_text as _record_text
from services.trend_analysis import generate_trend_analysis, calculate_health_score
from services.ai_service import check_ai_status, analyze_feedback_with_ai
from config import settings
import os
from routers.auth import get_authorization_header, get_current_user
from routers.feedback import _verify_workspace_access
from fallback_db import (
    find_feedback_by_workspace as fb_find_feedback_by_workspace,
    find_all_feedback_by_workspace as fb_find_all_feedback_by_workspace,
    save_workspace_insights as fb_save_workspace_insights,
    get_workspace_insights as fb_get_workspace_insights,
    _feedback_cache,
    _save_all,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])


async def _get_user_from_token(authorization: str) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token)


async def _fetch_workspace_feedback_records(workspace_id: str) -> List[dict]:
    """Fetch all feedback records for a workspace, converting Mongo ObjectIds to strings."""
    if not database._mongodb_available:
        return await fb_find_all_feedback_by_workspace(workspace_id)

    cursor = db.feedback.find({"workspace_id": workspace_id}).sort("created_at", -1)
    records = await cursor.to_list(length=None)
    for r in records:
        r["_id"] = str(r["_id"])
    return records


def _sanitize_cached_insights(cached: dict) -> dict:
    """
    Sanitize cached insights dict before feeding into Pydantic.
    - Converts string analyzed_at → datetime
    - Fills missing sentiment_distribution from trends
    - Ensures health_score defaults exist
    """
    from datetime import datetime as dt

    # Fix analyzed_at: Pydantic expects datetime, DB may return string
    if "analyzed_at" in cached and isinstance(cached["analyzed_at"], str):
        try:
            cached["analyzed_at"] = dt.fromisoformat(cached["analyzed_at"].replace("Z", "+00:00"))
        except Exception:
            cached["analyzed_at"] = None

    # Ensure health_score has a sane default
    if not cached.get("health_score"):
        cached["health_score"] = 75.0

    # Fill sentiment_distribution from trend data if missing
    if not cached.get("sentiment_distribution"):
        trends = cached.get("trends", [])
        cached["sentiment_distribution"] = {
            "positive": sum(t.get("positive_count", 0) for t in trends),
            "neutral": sum(t.get("neutral_count", 0) for t in trends),
            "negative": sum(t.get("negative_count", 0) for t in trends),
        }

    # Ensure required list fields exist
    for field in ("themes", "pain_points", "feature_clusters", "trends"):
        if not cached.get(field):
            cached[field] = []

    # Ensure required fields exist
    if "total_analyzed" not in cached:
        cached["total_analyzed"] = cached.get("total_feedback", len(cached.get("pain_points", [])))

    if not cached.get("category_distribution"):
        cached["category_distribution"] = {}

    return cached


def _ai_pain_point_terms(ai_pain_point: Dict[str, Any], limit: int = 10) -> List[str]:
    """Search terms that describe an AI pain point."""
    terms = [str(k).lower() for k in (ai_pain_point.get("keywords") or []) if len(str(k)) > 2]
    terms += re.findall(r"[a-z]{4,}", str(ai_pain_point.get("title") or "").lower())
    return [term for term in dict.fromkeys(terms) if term not in STOPWORDS_SET][:limit]


def _merge_ai_pain_points(
    pain_points: List[dict],
    ai_pain_points: List[dict],
    feedback_records: List[dict],
) -> List[dict]:
    """
    Attach each AI pain point to the deterministic group whose evidence it describes.

    Pairing by list position attached AI titles to unrelated quotes and counts, so a
    pain point about ads could report the complaint volume of the unsorted catch-all
    bucket. Pain points are matched on evidence overlap instead, and an AI pain point
    that matches no group is grounded directly in the feedback it quotes.
    """
    if not ai_pain_points:
        return pain_points

    evidence_texts = [
        [(_record_text(item), _resolve_sentiment(item)) for item in records[:400]]
        for records in _pain_point_evidence(pain_points, feedback_records)
    ]
    used_groups = set()

    for ai_pain_point in ai_pain_points:
        terms = _ai_pain_point_terms(ai_pain_point)
        best_index, best_score = None, 0
        for index, texts in enumerate(evidence_texts):
            if index in used_groups:
                continue
            score = sum(1 for text, _ in texts if any(term in text for term in terms))
            if score > best_score:
                best_index, best_score = index, score

        if best_index is not None:
            used_groups.add(best_index)
            pain_point = pain_points[best_index]
            if ai_pain_point.get("title") and len(str(ai_pain_point["title"])) > 4:
                pain_point["title"] = str(ai_pain_point["title"])
            for field in ("root_cause", "recommended_action"):
                if ai_pain_point.get(field):
                    pain_point[field] = ai_pain_point[field]
            if ai_pain_point.get("impact_score"):
                try:
                    pain_point["impact_score"] = round(float(ai_pain_point["impact_score"]), 1)
                except (TypeError, ValueError):
                    pass
            if ai_pain_point.get("keywords"):
                pain_point["keywords"] = [str(k) for k in ai_pain_point["keywords"]][:6]
            continue

        grounded = _ground_pain_point(ai_pain_point, terms, feedback_records)
        if grounded:
            pain_points.append(grounded)

    for pain_point in pain_points:
        if not pain_point.get("root_cause"):
            pain_point["root_cause"] = (
                f"Underlying friction in {pain_point.get('category', 'system')} flow affecting user workflow."
            )
    return pain_points


def _pain_point_evidence(pain_points: List[dict], feedback_records: List[dict]) -> List[List[dict]]:
    """Recover the feedback records each pain point was built from."""
    quotes_to_records = {}
    for item in feedback_records:
        for quote in ((item.get("content") or ""), (item.get("title") or "")):
            quote = quote.strip()
            if quote:
                quotes_to_records.setdefault(quote[:130], item)

    evidence = []
    for pain_point in pain_points:
        records = []
        for quote in pain_point.get("sample_quotes") or []:
            lookup = str(quote).strip()
            if lookup.endswith("..."):
                lookup = lookup[:-3]
            record = quotes_to_records.get(lookup)
            if record is not None:
                records.append(record)
        evidence.append(records)
    return evidence


def _ground_pain_point(ai_pain_point: dict, terms: List[str], feedback_records: List[dict]) -> Optional[dict]:
    """Build a pain point from the feedback records the AI pain point actually quotes."""
    if not terms:
        return None
    matches = [item for item in feedback_records if any(term in _record_text(item) for term in terms)][:500]
    if not matches:
        return None

    ratings = [item.get("rating") for item in matches if item.get("rating") is not None]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 2.0
    negative_count = sum(1 for item in matches if _resolve_sentiment(item) == "negative")
    impact_score = 20.0
    try:
        impact_score = round(min(98.0, max(20.0, float(ai_pain_point.get("impact_score") or 20.0))), 1)
    except (TypeError, ValueError):
        pass

    seen_quotes = set()
    quotes = []
    for item in matches:
        quote = (item.get("content") or item.get("title") or "").strip()
        if quote and quote not in seen_quotes and len(quotes) < 3:
            seen_quotes.add(quote)
            quotes.append(quote[:130] + ("..." if len(quote) > 130 else ""))

    return {
        "id": "",
        "title": str(ai_pain_point.get("title") or "Customer friction"),
        "description": str(ai_pain_point.get("description") or f"Observed in {len(matches)} customer complaints."),
        "severity": ai_pain_point.get("severity") or "high",
        "impact_score": impact_score,
        "affected_users_count": len(matches),
        "category": ai_pain_point.get("category") or "general_feedback",
        "root_cause": ai_pain_point.get("root_cause"),
        "recommended_action": ai_pain_point.get("recommended_action") or "Triage these complaints with engineering.",
        "keywords": [str(k) for k in (ai_pain_point.get("keywords") or [])][:6],
        "sample_quotes": quotes,
        "distinct_sample_quotes": quotes,
        "score_breakdown": {
            "frequency": len(matches),
            "avg_rating": avg_rating,
            "negative_sentiment_count": negative_count,
            "matched_terms": terms[:6],
            "source": "ai_matched_feedback",
        },
    }


async def _load_stored_insights(workspace_id: str) -> Optional[dict]:
    """
    Return the persisted analysis for a workspace, or None when it has never been analyzed.

    Every insights surface (dashboard, PRD, user stories, prioritisation, copilot) reads
    this same document. Recomputing analysis on the fly for the sub-resources produced a
    second set of cluster ids the PRD service could never resolve.
    """
    if database._mongodb_available:
        cached = await db.workspace_insights.find_one({"workspace_id": workspace_id})
        if cached:
            cached.pop("_id", None)
            return _sanitize_cached_insights(cached)
        return None

    cached = await fb_get_workspace_insights(workspace_id)
    if cached:
        return _sanitize_cached_insights(cached)
    return None


@router.post("/{workspace_id}/analyze", response_model=WorkspaceInsightsResponse)
async def analyze_workspace_insights(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """
    Run the canonical Product Intelligence & Analysis Pipeline:
    1. Categorizes and computes deterministic sentiment for all workspace records.
    2. Mines high-level themes with exact sentiment counts.
    3. Detects customer pain points with severity & explainable impact scoring.
    4. Aggregates feature requests into semantic clusters with unique customer counts & distinct quotes.
    5. Generates chronological trends and product health score.
    6. Persists canonical analysis attributes back onto each feedback record in the database.
    """
    user = await _get_user_from_token(authorization)
    workspace = await _verify_workspace_access(workspace_id, user)

    feedback_records = await _fetch_workspace_feedback_records(workspace_id)
    total_count = len(feedback_records)

    # 1. Deterministic categorization and sentiment for every record
    analyzed_updates = []
    for r in feedback_records:
        full_text = f"{r.get('title') or ''} {r.get('content') or ''}".strip()
        cat = categorize(full_text)
        sent = detect_sentiment(full_text, r.get("rating"))

        r["category"] = cat
        r["sentiment"] = sent
        r["cleaned"] = True
        analyzed_updates.append((r["_id"], {"category": cat, "sentiment": sent, "cleaned": True}))

    # 2. Extract the workspace's themes, then tag each record with its own theme.
    #    Themes come from the corpus, so a record's theme is the mined topic it matches.
    themes = extract_themes_from_feedback(feedback_records)
    updates_by_id = {str(rec_id): fields for rec_id, fields in analyzed_updates}
    for r in feedback_records:
        theme = assign_record_theme(f"{r.get('title') or ''} {r.get('content') or ''}", themes)
        r["theme"] = theme
        if str(r.get("_id")) in updates_by_id:
            updates_by_id[str(r["_id"])]["theme"] = theme

    # Persist canonical fields to DB in high-speed batches
    if database._mongodb_available:
        from pymongo import UpdateOne
        bulk_ops = []
        for rec_id, update_fields in analyzed_updates:
            try:
                target_filter = {"_id": ObjectId(rec_id)} if ObjectId.is_valid(str(rec_id)) else {"_id": rec_id}
            except Exception:
                target_filter = {"_id": rec_id}

            bulk_ops.append(UpdateOne(target_filter, {"$set": update_fields}))
            if len(bulk_ops) >= 1000:
                await db.feedback.bulk_write(bulk_ops, ordered=False)
                bulk_ops = []

        if bulk_ops:
            await db.feedback.bulk_write(bulk_ops, ordered=False)
    else:
        for rec_id, update_fields in analyzed_updates:
            if str(rec_id) in _feedback_cache:
                _feedback_cache[str(rec_id)].update(update_fields)
        _save_all()

    # 3. Customer Pain Points
    pain_points = extract_pain_points_from_feedback(feedback_records)

    # 4. Feature Request Clusters
    feature_clusters = cluster_feature_requests(feedback_records)

    # 5. AI Intelligence Layer (Groq LLM)
    ai_summary = None
    ai_powered = False
    ai_model = None

    ai_status = check_ai_status()
    if ai_status.get("available"):
        try:
            ai_data = analyze_feedback_with_ai(feedback_records)
            if ai_data:
                ai_summary = ai_data.get("ai_summary")
                ai_powered = True
                ai_model = ai_data.get("ai_model")

                # Merge AI root-cause analysis and actions into pain points
                pain_points = _merge_ai_pain_points(
                    pain_points, ai_data.get("pain_points", []), feedback_records
                )

                # Keep pain points ranked by impact after the AI scores replaced them
                pain_points.sort(key=lambda p: p.get("impact_score", 0.0), reverse=True)
                for rank, pp in enumerate(pain_points, start=1):
                    pp["id"] = f"pain_point_{rank}"

                # Synthesize AI Feature Clusters
                ai_clusters = ai_data.get("feature_clusters", [])
                has_customer_identity = workspace_has_customer_identity(feedback_records)
                if ai_clusters and len(ai_clusters) >= 3:
                    synthesized_clusters = []
                    for idx, ac in enumerate(ai_clusters[:6]):
                        c_name = ac.get("cluster_name") or f"Feature Opportunity {idx+1}"
                        c_summary = ac.get("summary") or "High-value user requested capability."
                        c_kws = ac.get("keywords") or [w.lower() for w in c_name.split() if len(w) > 3]
                        
                        # Find matching user requests (whole-word mentions only)
                        matched_items = _match_records_by_terms(
                            feedback_records,
                            [str(kw) for kw in c_kws if len(str(kw)) > 2]
                            + [w for w in c_name.split() if len(w) > 3],
                        )

                        # If no direct match, fallback to matched slice
                        if not matched_items and idx < len(feature_clusters):
                            matched_items = [it for it in feedback_records if it.get("_id") in feature_clusters[idx].get("feedback_ids", [])]
                        if not matched_items:
                            # No workspace record backs this AI cluster — skip it rather
                            # than present an opportunity with fabricated volume.
                            continue

                        count = len(matched_items)
                        unique_users = count_unique_requesters(matched_items, has_customer_identity)
                        
                        seen_q = set()
                        quotes = []
                        for it in matched_items:
                            q = (it.get("content") or it.get("title") or "").strip()
                            if q and q not in seen_q and len(quotes) < 3:
                                seen_q.add(q)
                                quotes.append(q[:130] + ("..." if len(q) > 130 else ""))

                        # Priority and demand
                        p_score = float(ac.get("priority_score", 65.0))
                        d_level = ac.get("demand_level", "high" if p_score >= 55.0 else ("medium" if p_score >= 32.0 else "low")).lower()
                        if d_level not in ("high", "medium", "low"):
                            d_level = "medium"

                        synthesized_clusters.append({
                            "id": f"ai_cluster_{idx+1}",
                            "cluster_name": c_name,
                            "summary": c_summary,
                            "request_count": count,
                            "unique_customers_count": unique_users,
                            "demand_level": d_level,
                            "priority_score": round(p_score, 1),
                            "keywords": c_kws[:5],
                            "sample_requests": quotes if quotes else (feature_clusters[idx].get("sample_requests", []) if idx < len(feature_clusters) else []),
                            "distinct_sample_quotes": quotes if quotes else (feature_clusters[idx].get("distinct_sample_quotes", []) if idx < len(feature_clusters) else []),
                            "feedback_ids": [str(it.get("_id", "")) for it in matched_items[:10]],
                            "score_breakdown": {
                                "request_count": count,
                                "unique_customers_count": unique_users,
                                "unique_customers_count_basis": (
                                    "unique_customers" if has_customer_identity else "unavailable"
                                ),
                                "demand_level": d_level,
                                "formula_weights": (
                                    "Priority score synthesised by the AI model — measured inputs: request volume, unique customers and rating satisfaction"
                                    if has_customer_identity
                                    else "Priority score synthesised by the AI model — measured inputs: request volume and rating satisfaction."
                                         " Requester breadth is excluded because this workspace carries no per-user identity"
                                ),
                            }
                        })
                    if synthesized_clusters:
                        feature_clusters = synthesized_clusters
        except Exception as e:
            logger.warning(f"AI feedback analysis error: {e}")


    # 6. Trend Analysis & Health Score
    trends = generate_trend_analysis(feedback_records)
    health_score = calculate_health_score(feedback_records)

    # Category distribution
    category_counts: Dict[str, int] = {}
    sentiment_counts: Dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0}

    from services.theme_extraction import _resolve_category, _resolve_sentiment

    for it in feedback_records:
        c = _resolve_category(it)
        category_counts[c] = category_counts.get(c, 0) + 1
        s = _resolve_sentiment(it)
        if s in sentiment_counts:
            sentiment_counts[s] += 1
        else:
            sentiment_counts[s] = 1


    now = datetime.utcnow()
    insights_data = {
        "workspace_id": workspace_id,
        "workspace_name": workspace.get("name", "Product Workspace"),
        "total_analyzed": total_count,
        "health_score": health_score,
        "themes": themes,
        "pain_points": pain_points,
        "feature_clusters": feature_clusters,
        "trends": trends,
        "category_distribution": category_counts,
        "sentiment_distribution": sentiment_counts,
        "ai_summary": ai_summary,
        "ai_powered": ai_powered,
        "ai_model": ai_model,
        "analyzed_at": now,
    }

    # Store or update in MongoDB if available
    if database._mongodb_available:
        await db.workspace_insights.update_one(
            {"workspace_id": workspace_id},
            {"$set": insights_data},
            upsert=True,
        )
    else:
        await fb_save_workspace_insights(workspace_id, insights_data)

    return WorkspaceInsightsResponse(**insights_data)


@router.get("/ai/status")
async def get_ai_status(authorization: str = Depends(get_authorization_header)):
    """Check whether Groq AI is active or running in heuristic mode."""
    await _get_user_from_token(authorization)
    return check_ai_status()


@router.post("/ai/configure-key")
async def configure_ai_key(
    payload: Dict[str, str],
    authorization: str = Depends(get_authorization_header),
):
    """Dynamically configure or test the Groq API key."""
    await _get_user_from_token(authorization)
    key = payload.get("api_key", "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key is required")

    settings.GROQ_API_KEY = key
    os.environ["GROQ_API_KEY"] = key
    status_res = check_ai_status()
    if not status_res.get("available"):
        raise HTTPException(status_code=400, detail=f"Failed to activate key: {status_res.get('message')}")
    return status_res


@router.get("/{workspace_id}", response_model=WorkspaceInsightsResponse)
async def get_workspace_insights(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """
    Get the computed insights for a workspace.
    Runs analysis if no cached analysis exists.
    """
    user = await _get_user_from_token(authorization)
    workspace = await _verify_workspace_access(workspace_id, user)

    if database._mongodb_available:
        cached = await db.workspace_insights.find_one({"workspace_id": workspace_id})
        if cached:
            cached.pop("_id", None)
            cached = _sanitize_cached_insights(cached)
            return WorkspaceInsightsResponse(**cached)
    else:
        cached = await fb_get_workspace_insights(workspace_id)
        if cached:
            cached = _sanitize_cached_insights(cached)
            return WorkspaceInsightsResponse(**cached)

    return await analyze_workspace_insights(workspace_id, authorization)


@router.get("/{workspace_id}/themes", response_model=List[ThemeItem])
async def get_workspace_themes(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Get extracted customer feedback themes for a workspace."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    stored = await _load_stored_insights(workspace_id)
    if stored and stored.get("themes"):
        return stored["themes"]
    feedback_records = await _fetch_workspace_feedback_records(workspace_id)
    return extract_themes_from_feedback(feedback_records)


@router.get("/{workspace_id}/pain-points", response_model=List[PainPointItem])
async def get_workspace_pain_points(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Get identified customer pain points and severity rankings."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    stored = await _load_stored_insights(workspace_id)
    if stored and stored.get("pain_points"):
        return sorted(stored["pain_points"], key=lambda p: p.get("impact_score", 0.0), reverse=True)
    feedback_records = await _fetch_workspace_feedback_records(workspace_id)
    return extract_pain_points_from_feedback(feedback_records)


@router.get("/{workspace_id}/clusters", response_model=List[FeatureCluster])
async def get_workspace_feature_clusters(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Get aggregated feature request clusters."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    stored = await _load_stored_insights(workspace_id)
    if stored and stored.get("feature_clusters"):
        return sorted(stored["feature_clusters"], key=lambda c: c.get("priority_score", 0.0), reverse=True)
    feedback_records = await _fetch_workspace_feedback_records(workspace_id)
    return cluster_feature_requests(feedback_records)


@router.get("/{workspace_id}/trends", response_model=List[TrendDataPoint])
async def get_workspace_trends(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Get trend trajectory and sentiment history."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    feedback_records = await _fetch_workspace_feedback_records(workspace_id)
    return generate_trend_analysis(feedback_records)


@router.post("/{workspace_id}/crew-ai-analyze")
async def run_crew_ai_insights_endpoint(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """
    Execute the Milestone 2 CrewAI Multi-Agent Pipeline:
    - Agent 1: Theme & Pain Point Analyst
    - Agent 2: Feature Request & Opportunity Strategist
    - Agent 3: Product Trend & Sentiment Trajectory Analyst
    """
    user = await _get_user_from_token(authorization)
    workspace = await _verify_workspace_access(workspace_id, user)
    feedback_records = await _fetch_workspace_feedback_records(workspace_id)

    if not feedback_records:
        raise HTTPException(status_code=400, detail="No feedback records found in this workspace to run CrewAI analysis.")

    try:
        from agents.crew import run_milestone2_crew
        crew_res = run_milestone2_crew(feedback_records, workspace.get("name", "Product Workspace"))

        # Calculate category and sentiment distributions
        category_counts: Dict[str, int] = {}
        sentiment_counts: Dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0}
        from services.theme_extraction import _resolve_category, _resolve_sentiment

        for it in feedback_records:
            c = _resolve_category(it)
            category_counts[c] = category_counts.get(c, 0) + 1
            s = _resolve_sentiment(it)
            if s in sentiment_counts:
                sentiment_counts[s] += 1
            else:
                sentiment_counts[s] = 1

        # Save to database
        now = datetime.utcnow()
        insights_data = {
            "workspace_id": workspace_id,
            "workspace_name": workspace.get("name", "Product Workspace"),
            "total_analyzed": len(feedback_records),
            "health_score": crew_res.get("health_score", 75.0),
            "themes": crew_res.get("themes", []),
            "pain_points": crew_res.get("pain_points", []),
            "feature_clusters": crew_res.get("feature_clusters", []),
            "trends": crew_res.get("trends", []),
            "category_distribution": category_counts,
            "sentiment_distribution": sentiment_counts,
            "ai_powered": True,
            "ai_model": "CrewAI (3 Multi-Agent Crew)",
            "analyzed_at": now,
        }

        if database._mongodb_available:
            await db.workspace_insights.update_one(
                {"workspace_id": workspace_id},
                {"$set": insights_data},
                upsert=True,
            )

        return {
            "status": "success",
            "message": "Milestone 2 CrewAI Multi-Agent execution finished.",
            "agents_executed": crew_res.get("agents", []),
            "crew_output": crew_res.get("crew_output"),
            "insights": insights_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CrewAI execution error: {str(e)}")

