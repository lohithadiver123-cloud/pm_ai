"""
Trend Analysis and Temporal Sentiment Analytics engine.
Tracks customer feedback volume, sentiment shifts over time,
category velocity, and overall product health score.
"""

from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Any, Tuple


def calculate_health_score(feedback_list: List[Dict[str, Any]]) -> float:
    """
    Calculate an overall Product Sentiment Health Score from 0 to 100.
    Based on positive/negative ratio, average star ratings, and bug proportions.
    """
    if not feedback_list:
        return 75.0

    total = len(feedback_list)
    positives = sum(1 for it in feedback_list if it.get("sentiment") == "positive")
    negatives = sum(1 for it in feedback_list if it.get("sentiment") == "negative")
    neutrals = sum(1 for it in feedback_list if it.get("sentiment") == "neutral")
    bugs = sum(1 for it in feedback_list if it.get("category") == "bug_report")

    # 1. Sentiment ratio component (0 to 45 points)
    sentiment_ratio = (positives + 0.5 * neutrals) / total
    sentiment_points = sentiment_ratio * 45.0

    # 2. Rating component (0 to 35 points)
    ratings = [it.get("rating") for it in feedback_list if it.get("rating") is not None]
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        rating_points = (avg_rating / 5.0) * 35.0
    else:
        rating_points = 25.0

    # 3. Stability component (0 to 20 points, penalized by bug ratio)
    bug_ratio = bugs / total
    stability_points = max(0.0, (1.0 - bug_ratio * 1.5) * 20.0)

    total_health = round(min(100.0, max(10.0, sentiment_points + rating_points + stability_points)), 1)
    return total_health


def parse_date_bucket(item: Dict[str, Any]) -> str:
    """Extract a consistent YYYY-MM-DD bucket string from created_at or imported_at."""
    date_val = item.get("created_at") or item.get("imported_at")
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    elif isinstance(date_val, str) and len(date_val) >= 10:
        return date_val[:10]
    return datetime.utcnow().strftime("%Y-%m-%d")


def generate_trend_analysis(feedback_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate chronological trend analysis data points for feedback items.
    Aggregates volume, positive/neutral/negative counts, sentiment score, and top categories.
    """
    if not feedback_list:
        return []

    # Group by date bucket
    bucket_map = defaultdict(lambda: {
        "total": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "categories": Counter(),
    })

    for item in feedback_list:
        bucket = parse_date_bucket(item)
        sentiment = item.get("sentiment") or "neutral"
        category = item.get("category") or "general_feedback"

        bucket_map[bucket]["total"] += 1
        if sentiment == "positive":
            bucket_map[bucket]["positive"] += 1
        elif sentiment == "negative":
            bucket_map[bucket]["negative"] += 1
        else:
            bucket_map[bucket]["neutral"] += 1

        bucket_map[bucket]["categories"][category] += 1

    trend_points = []
    sorted_periods = sorted(bucket_map.keys())
    prev_score = None

    for period in sorted_periods:
        data = bucket_map[period]
        total = data["total"]
        pos = data["positive"]
        neg = data["negative"]
        neu = data["neutral"]

        score = round((pos - neg) / (total if total > 0 else 1), 2)
        top_cat = data["categories"].most_common(1)[0][0] if data["categories"] else "general_feedback"
        velocity = round(score - prev_score, 2) if prev_score is not None else 0.0
        prev_score = score

        trend_points.append({
            "period": period,
            "total_count": total,
            "positive_count": pos,
            "neutral_count": neu,
            "negative_count": neg,
            "sentiment_score": score,
            "top_category": top_cat,
            "sentiment_velocity": velocity,
        })

    return trend_points
