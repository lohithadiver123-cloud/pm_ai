"""
Feature Request Aggregation and Semantic Clustering engine.
Clusters user requests into product opportunities with deterministic priority scoring,
unique customer counts, and deduplicated representative quotes.
"""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set
from services.preprocessing import normalize, STOPWORDS_SET


FEATURE_OPPORTUNITY_PATTERNS = [
    {
        "cluster_name": "Offline Mode Support",
        "keywords": ["offline", "no internet", "without internet", "without network", "offline mode", "offline access"],
        "summary": "Users need offline functionality to view data and work without an active internet connection.",
    },
    {
        "cluster_name": "Dark Mode & Visual Comfort",
        "keywords": ["dark mode", "bright interface", "night", "theme", "dark theme", "color scheme"],
        "summary": "High demand for dark theme to reduce eye strain and improve readability in low light.",
    },
    {
        "cluster_name": "Multi-Account Switching",
        "keywords": ["multiple account", "switch account", "switch between", "multi account", "several accounts"],
        "summary": "Users want the ability to switch between multiple work or personal accounts without repeated logins.",
    },
    {
        "cluster_name": "Data Export to CSV & Excel",
        "keywords": ["export", "csv", "excel", "download report", "export reports", "spreadsheet"],
        "summary": "Demand for exporting analytics and reports into CSV/Excel for external analysis and reporting.",
    },
    {
        "cluster_name": "Biometric Authentication (Face ID / Fingerprint)",
        "keywords": ["biometric", "face id", "fingerprint", "touch id", "biometric login"],
        "summary": "Requests for modern, secure biometric sign-in on supported devices.",
    },
    {
        "cluster_name": "Accessibility & Large Text Options",
        "keywords": ["accessibility", "larger text", "screen-reader", "screen reader", "text size", "contrast"],
        "summary": "Requests for inclusive accessibility settings including larger font scaling and screen-reader support.",
    },
    {
        "cluster_name": "Interactive Onboarding & Setup Guide",
        "keywords": ["onboarding", "first-time", "setup is confusing", "instructions", "guide", "walkthrough"],
        "summary": "Demand for a clearer first-time product tour and streamlined onboarding setup.",
    },
]


def compute_jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Compute Jaccard token overlap similarity between two sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return intersection / union if union > 0 else 0.0


def cluster_feature_requests(feedback_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cluster all feature requests in the feedback dataset into high-level feature opportunities.
    Computes priority scores, unique customer counts, and distinct quotes.
    """
    if not feedback_list:
        return []

    # 1. Filter feature items or requests with explicit feature intent
    feature_items = []
    for item in feedback_list:
        cat = item.get("category")
        content = (item.get("content") or "").lower()
        title = (item.get("title") or "").lower()
        full_text = f"{title} {content}"

        is_feat = (
            cat == "feature_request"
            or any(kw in full_text for kw in [
                "add", "wish", "would like", "please add", "feature", "want", "need",
                "could you", "please provide", "support for", "option to", "switch between",
                "dark mode", "offline", "export", "biometric", "accessibility", "onboarding"
            ])
        )
        if is_feat:
            feature_items.append(item)

    if not feature_items:
        feature_items = feedback_list[:max(5, len(feedback_list) // 3)]

    total_feature_items = max(len(feature_items), 1)

    # 2. Bucket by canonical opportunity patterns
    cluster_buckets = defaultdict(list)
    unassigned = []

    for item in feature_items:
        text = f"{(item.get('title') or '')} {(item.get('content') or '')}".lower()
        matched_cluster = None

        for pattern in FEATURE_OPPORTUNITY_PATTERNS:
            if any(kw in text for kw in pattern["keywords"]):
                matched_cluster = pattern["cluster_name"]
                break

        if matched_cluster:
            cluster_buckets[matched_cluster].append(item)
        else:
            unassigned.append(item)

    # 3. Dynamic clustering for unassigned requests (capped for fast execution on 10k+ datasets)
    dynamic_clusters = defaultdict(list)
    dynamic_cluster_tokens = {}
    max_dynamic_clusters = 25

    # Process up to 400 unassigned samples to keep grouping fast and responsive
    unassigned_sample = unassigned[:400] if len(unassigned) > 400 else unassigned
    for item in unassigned_sample:
        text = f"{item.get('title', '')} {item.get('content', '')}".strip()
        tokens = {t for t in normalize(text) if t not in STOPWORDS_SET and len(t) > 2}

        assigned_dyn = False
        for rep_name, rep_tokens in dynamic_cluster_tokens.items():
            if compute_jaccard_similarity(tokens, rep_tokens) > 0.25:
                dynamic_clusters[rep_name].append(item)
                assigned_dyn = True
                break

        if not assigned_dyn and len(dynamic_clusters) < max_dynamic_clusters:
            title_clean = (item.get("title") or item.get("content", "")[:35]).strip()
            rep_key = f"Enhancement: {title_clean}"
            dynamic_clusters[rep_key] = [item]
            dynamic_cluster_tokens[rep_key] = set(normalize(rep_key))
        elif not assigned_dyn and dynamic_clusters:
            # Add to most general cluster
            first_key = next(iter(dynamic_clusters))
            dynamic_clusters[first_key].append(item)

    all_clusters = []
    cluster_counter = 1

    # 4. Format canonical clusters
    for pattern in FEATURE_OPPORTUNITY_PATTERNS:
        name = pattern["cluster_name"]
        items = cluster_buckets.get(name, [])
        if not items:
            continue

        count = len(items)
        unique_customers = len({it.get("customer_name") or it.get("customer_email") or f"user_{idx}" for idx, it in enumerate(items)})
        ratings = [it.get("rating") for it in items if it.get("rating") is not None]
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 4.0

        # Deterministic Priority Score:
        # Volume (up to 45 pts) + Customer Breadth (up to 30 pts) + User Rating Boost (up to 25 pts)
        vol_score = min(45.0, (count / total_feature_items) * 100.0 * 1.5)
        breadth_score = min(30.0, (unique_customers / total_feature_items) * 100.0 * 1.5)
        rating_score = (avg_rating / 5.0) * 25.0
        priority_score = round(min(98.0, max(25.0, vol_score + breadth_score + rating_score)), 1)

        demand_level = "high" if count >= 6 or priority_score >= 70.0 else ("medium" if count >= 3 else "low")

        # Distinct representative quotes
        seen_quotes = set()
        quotes = []
        feedback_ids = []
        for it in items:
            feedback_ids.append(str(it.get("_id", "")))
            q = (it.get("content") or it.get("title") or "").strip()
            if q and q not in seen_quotes and len(quotes) < 3:
                seen_quotes.add(q)
                quotes.append(q[:130] + ("..." if len(q) > 130 else ""))

        all_clusters.append({
            "id": f"cluster_{cluster_counter}",
            "cluster_name": name,
            "summary": pattern["summary"],
            "request_count": count,
            "unique_customers_count": unique_customers,
            "demand_level": demand_level,
            "priority_score": priority_score,
            "keywords": pattern["keywords"][:5],
            "sample_requests": quotes,
            "distinct_sample_quotes": quotes,
            "feedback_ids": feedback_ids,
            "score_breakdown": {
                "request_count": count,
                "unique_customers": unique_customers,
                "avg_rating": avg_rating,
                "demand_level": demand_level,
                "formula_weights": "Request Volume (45%) + Unique Users (30%) + Rating Satisfaction (25%)"
            }
        })
        cluster_counter += 1

    # 5. Format dynamic clusters
    for dyn_name, items in dynamic_clusters.items():
        if not items:
            continue
        count = len(items)
        unique_customers = len({it.get("customer_name") or it.get("customer_email") or f"user_{idx}" for idx, it in enumerate(items)})
        priority_score = round(min(80.0, max(25.0, (count / total_feature_items) * 60.0 + 20.0)), 1)
        demand_level = "medium" if count >= 3 else "low"

        seen_quotes = set()
        quotes = []
        feedback_ids = []
        for it in items:
            feedback_ids.append(str(it.get("_id", "")))
            q = (it.get("content") or it.get("title") or "").strip()
            if q and q not in seen_quotes and len(quotes) < 3:
                seen_quotes.add(q)
                quotes.append(q[:130] + ("..." if len(q) > 130 else ""))

        all_clusters.append({
            "id": f"cluster_{cluster_counter}",
            "cluster_name": dyn_name,
            "summary": f"Group of {count} user requests discussing related improvements.",
            "request_count": count,
            "unique_customers_count": unique_customers,
            "demand_level": demand_level,
            "priority_score": priority_score,
            "keywords": [w for w in normalize(dyn_name)[:4] if w not in STOPWORDS_SET],
            "sample_requests": quotes,
            "distinct_sample_quotes": quotes,
            "feedback_ids": feedback_ids,
            "score_breakdown": {
                "request_count": count,
                "unique_customers": unique_customers,
                "demand_level": demand_level,
                "formula_weights": "Volume Weight + Keyword Density"
            }
        })
        cluster_counter += 1

    all_clusters.sort(key=lambda x: x["priority_score"], reverse=True)
    return all_clusters
