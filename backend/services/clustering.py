"""
Feature Request Aggregation and Semantic Clustering engine.
Clusters user requests into product opportunities with deterministic priority scoring,
unique customer counts, and deduplicated representative quotes.
"""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set
from services.preprocessing import normalize, STOPWORDS_SET
from services.theme_extraction import _resolve_category, _resolve_sentiment


FEATURE_OPPORTUNITY_PATTERNS = [
    {
        "cluster_name": "Native iOS & Android Mobile Apps",
        "keywords": ["mobile app", "native app", "ios app", "android app", "iphone app", "app store", "play store", "on the go"],
        "summary": "High demand for dedicated native mobile clients with push notifications, background sync, and offline storage.",
    },
    {
        "cluster_name": "Report & Analytics Export to PDF & CSV",
        "keywords": ["export to pdf", "pdf export", "export report", "pdf format", "csv", "excel", "spreadsheet", "download report", "export data"],
        "summary": "Users need automated visual PDF exports and structured CSV downloads for executive reporting and stakeholder meetings.",
    },
    {
        "cluster_name": "High-Contrast Dark Mode & OLED Theme",
        "keywords": ["dark mode", "night mode", "dark theme", "bright white", "eye strain", "night", "amoled", "contrast"],
        "summary": "Requests for a high-contrast true black dark theme to reduce eye fatigue during late-night usage and save battery.",
    },
    {
        "cluster_name": "Auto-Scroll & Hands-Free Feed Navigation",
        "keywords": ["auto scroll", "scroll automatically", "hands free", "auto-scroll", "continuous scroll", "next reel automatically"],
        "summary": "Demand for automated hands-free feed scrolling and continuous video reel progression without repeated swipes.",
    },
    {
        "cluster_name": "One-Tap Video Pausing & Audio Scrubbing",
        "keywords": ["pause", "pausing", "pause video", "audio scrub", "scrub", "volume control", "mute toggle", "video player", "playback"],
        "summary": "Users request reliable tap-to-pause controls on videos and precise audio scrubbing timelines without overlay interference.",
    },
    {
        "cluster_name": "Creator Follower Reach & View Diagnostics",
        "keywords": ["algorithm", "reach", "views", "impression", "impressions", "ranking", "hashtag", "follower", "followers", "shadowban", "engagement"],
        "summary": "Transparent creator diagnostics to understand distribution algorithms, diagnose drop-offs in reach, and verify hashtag visibility.",
    },
    {
        "cluster_name": "Automated Spam Bot & Fake Account Eradication",
        "keywords": ["fake profile", "fake profiles", "spam account", "spam accounts", "bot", "bots", "adult content", "block all", "bulk block", "report spam"],
        "summary": "Demands for proactive bot detection, bulk profile blocking, and automated filtering of unsolicited spam solicitations.",
    },
    {
        "cluster_name": "Fast Multi-Account & Creator Profile Switcher",
        "keywords": ["multiple account", "switch account", "switch profile", "multi account", "several accounts", "switch between accounts"],
        "summary": "One-click toggling between multiple personal, creator, and brand accounts without session logout friction.",
    },
    {
        "cluster_name": "Offline Media & Saved Draft Caching",
        "keywords": ["offline", "no internet", "without internet", "save offline", "cache videos", "offline mode", "drafts offline"],
        "summary": "Ability to review bookmarked content, compose draft posts, and access chat threads without active network connectivity.",
    },
    {
        "cluster_name": "Biometric Authentication (Face ID / Fingerprint)",
        "keywords": ["biometric", "face id", "fingerprint", "touch id", "passkey", "biometric login"],
        "summary": "Streamlined sign-in via hardware biometrics for faster access and enhanced account security.",
    },
]


def compute_jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Compute Jaccard token overlap similarity between two sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return intersection / union if union > 0 else 0.0


def cluster_feature_requests(feedback_list: List[Dict[str, Any]], max_clusters: int = 6) -> List[Dict[str, Any]]:
    """
    Cluster all feature requests in the feedback dataset into high-level feature opportunities.
    Computes priority scores, unique customer counts, and distinct quotes with consistent demand tiers.
    """
    if not feedback_list:
        return []

    # 1. Filter feature items or requests with explicit feature intent
    feature_items = []
    for item in feedback_list:
        cat = _resolve_category(item)
        content = (item.get("content") or "").lower()
        title = (item.get("title") or "").lower()
        full_text = f"{title} {content}"

        is_bug = cat in ("bug_report", "performance_issue")
        has_feat_intent = any(kw in full_text for kw in [
            "feature", "wish", "would like", "please add", "suggestion",
            "could you add", "support for", "option to", "switch between",
            "dark mode", "offline", "export", "biometric", "reach control",
            "auto scroll", "pause", "volume", "notification"
        ])

        # Exclude pure bug reports unless they contain explicit enhancement intent
        if is_bug and not has_feat_intent:
            continue

        if cat == "feature_request" or has_feat_intent:
            feature_items.append(item)

    if not feature_items:
        feature_items = [it for it in feedback_list if _resolve_category(it) not in ("bug_report", "performance_issue")]
        if not feature_items:
            feature_items = feedback_list[:max(3, len(feedback_list) // 4)]

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

    all_clusters = []
    cluster_counter = 1

    # 3. Format canonical clusters
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
        priority_score = round(min(98.0, max(20.0, vol_score + breadth_score + rating_score)), 1)

        # Consistent Demand Level based strictly on priority score and relative volume
        if priority_score >= 55.0 or count >= 50:
            demand_level = "high"
        elif priority_score >= 32.0 or count >= 10:
            demand_level = "medium"
        else:
            demand_level = "low"

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

        clean_kws = [k for k in pattern["keywords"] if k not in STOPWORDS_SET][:5]

        all_clusters.append({
            "id": f"cluster_{cluster_counter}",
            "cluster_name": name,
            "summary": pattern["summary"],
            "request_count": count,
            "unique_customers_count": unique_customers,
            "demand_level": demand_level,
            "priority_score": priority_score,
            "keywords": clean_kws,
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

    # 4. Handle unassigned items if any
    if unassigned and len(all_clusters) < max_clusters:
        count = len(unassigned)
        unique_customers = len({it.get("customer_name") or it.get("customer_email") or f"user_{idx}" for idx, it in enumerate(unassigned)})
        vol_score = min(45.0, (count / total_feature_items) * 100.0 * 1.5)
        breadth_score = min(30.0, (unique_customers / total_feature_items) * 100.0 * 1.5)
        priority_score = round(min(90.0, max(25.0, vol_score + breadth_score + 15.0)), 1)
        
        if priority_score >= 55.0 or count >= 50:
            demand_level = "high"
        elif priority_score >= 32.0 or count >= 10:
            demand_level = "medium"
        else:
            demand_level = "low"

        seen_quotes = set()
        quotes = []
        for it in unassigned:
            q = (it.get("content") or it.get("title") or "").strip()
            if q and q not in seen_quotes and len(quotes) < 3:
                seen_quotes.add(q)
                quotes.append(q[:130] + ("..." if len(q) > 130 else ""))

        all_clusters.append({
            "id": f"cluster_{cluster_counter}",
            "cluster_name": "General Workflow & Usability Improvements",
            "summary": "Aggregated user requests focusing on app responsiveness, navigation, and usability adjustments.",
            "request_count": count,
            "unique_customers_count": unique_customers,
            "demand_level": demand_level,
            "priority_score": priority_score,
            "keywords": ["workflow", "usability", "improvements", "interface"],
            "sample_requests": quotes,
            "distinct_sample_quotes": quotes,
            "feedback_ids": [str(it.get("_id", "")) for it in unassigned[:10]],
            "score_breakdown": {
                "request_count": count,
                "unique_customers": unique_customers,
                "demand_level": demand_level,
                "formula_weights": "Request Volume (45%) + Unique Users (30%) + Rating Satisfaction (25%)"
            }
        })

    all_clusters.sort(key=lambda x: x["priority_score"], reverse=True)
    return all_clusters[:max_clusters]


