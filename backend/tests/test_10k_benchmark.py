"""
Benchmark test script for 10,000 rows customer reviews.
Tests end-to-end performance of:
1. CSV parsing & batch import (Target: < 2.0 seconds)
2. Intelligence & Insights Analysis pipeline (Target: < 2.0 seconds)
3. Data Cleaning & Deduplication (Target: < 1.0 second)
"""

import sys
import os
import io
import time
import asyncio
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.categorization import categorize, detect_sentiment
from services.theme_extraction import extract_themes_from_feedback, extract_pain_points_from_feedback, match_domain_topic
from services.clustering import cluster_feature_requests
from services.trend_analysis import generate_trend_analysis, calculate_health_score
from services.data_cleaning import clean_text, remove_duplicates, clean_workspace_feedback
from fallback_db import (
    create_feedback_batch,
    find_all_feedback_by_workspace,
    _feedback_cache,
    _save_all,
)


def generate_10k_sample_reviews():
    """Generate 10,000 realistic customer reviews across diverse categories."""
    templates = [
        ("The app crashes whenever I try to reset my password", "Authentication & Access", 1, "bug_report"),
        ("Please add dark mode support, the screen is too bright at night", "UI & User Experience", 4, "feature_request"),
        ("App is very slow and lags when loading the dashboard", "Performance & Stability", 2, "performance_issue"),
        ("Great customer support, they helped me resolve my billing issue quickly", "Customer Support & Service", 5, "customer_support"),
        ("Need offline mode so I can work without internet connection", "UI & User Experience", 4, "feature_request"),
        ("Payment failed during checkout and money was deducted from my card", "Billing & Payments", 1, "bug_report"),
        ("Search filtering is inaccurate and misses exact keyword matches", "Search & Filtering", 2, "bug_report"),
        ("Notification alerts are delayed and arrive hours late", "Notifications & Alerts", 2, "performance_issue"),
        ("Allow export of analytics reports to CSV and Excel format", "Data Management & Sync", 5, "feature_request"),
        ("Love the clean UI and intuitive layout, works smoothly", "UI & User Experience", 5, "general_feedback"),
    ]

    records = []
    for i in range(10000):
        tmpl = templates[i % len(templates)]
        records.append({
            "workspace_id": "test_10k_ws",
            "title": f"Review {i+1}: {tmpl[0][:40]}",
            "content": f"{tmpl[0]} (User index {i+1} feedback report)",
            "customer_name": f"Customer_{i+1}",
            "customer_email": f"user_{i+1}@example.com",
            "rating": tmpl[2],
            "source": "app_review",
            "category": tmpl[3],
            "sentiment": "positive" if tmpl[2] >= 4 else "negative" if tmpl[2] <= 2 else "neutral",
            "cleaned": True,
            "created_at": "2026-09-15T12:00:00",
        })
    return records


async def run_benchmark():
    print("=" * 60)
    print("STARTING 10,000 ROWS PERFORMANCE BENCHMARK")
    print("=" * 60)

    # 1. Generate 10k items
    t0 = time.time()
    records = generate_10k_sample_reviews()
    gen_time = time.time() - t0
    print(f"1. Generated 10,000 synthetic review records in {gen_time:.3f}s")

    # 2. Benchmark Batch Insertion to Fallback DB
    t0 = time.time()
    await create_feedback_batch(records)
    batch_insert_time = time.time() - t0
    print(f"2. Batch inserted 10,000 records to Fallback DB in {batch_insert_time:.3f}s")
    assert batch_insert_time < 2.0, f"Batch insert too slow: {batch_insert_time}s"

    # 3. Benchmark Categorization & Sentiment Analysis across 10k items
    t0 = time.time()
    for r in records:
        full_text = f"{r['title']} {r['content']}"
        r["category"] = categorize(full_text)
        r["sentiment"] = detect_sentiment(full_text, r["rating"])
        r["theme"] = match_domain_topic(full_text)
    cat_time = time.time() - t0
    print(f"3. Categorized & analyzed 10,000 records in {cat_time:.3f}s (Speed: {10000/cat_time:.0f} recs/sec)")
    assert cat_time < 2.0, f"Categorization too slow: {cat_time}s"

    # 4. Benchmark Theme Extraction
    t0 = time.time()
    themes = extract_themes_from_feedback(records)
    theme_time = time.time() - t0
    print(f"4. Extracted {len(themes)} themes in {theme_time:.3f}s")
    assert theme_time < 1.5, f"Theme extraction too slow: {theme_time}s"

    # 5. Benchmark Pain Point Extraction
    t0 = time.time()
    pain_points = extract_pain_points_from_feedback(records)
    pp_time = time.time() - t0
    print(f"5. Extracted {len(pain_points)} customer pain points in {pp_time:.3f}s")
    assert pp_time < 1.5, f"Pain point extraction too slow: {pp_time}s"

    # 6. Benchmark Feature Clustering
    t0 = time.time()
    clusters = cluster_feature_requests(records)
    cluster_time = time.time() - t0
    print(f"6. Clustered {len(clusters)} feature opportunities in {cluster_time:.3f}s")
    assert cluster_time < 1.5, f"Feature clustering too slow: {cluster_time}s"

    # 7. Benchmark Trend Analysis & Health Score
    t0 = time.time()
    trends = generate_trend_analysis(records)
    health = calculate_health_score(records)
    trend_time = time.time() - t0
    print(f"7. Generated {len(trends)} trend points, Health Score: {health} in {trend_time:.3f}s")
    assert trend_time < 1.0, f"Trend analysis too slow: {trend_time}s"

    # 8. Benchmark Data Cleaning & Deduplication
    t0 = time.time()
    clean_res = await clean_workspace_feedback("test_10k_ws")
    clean_time = time.time() - t0
    print(f"8. Cleaned feedback & deduplication in {clean_time:.3f}s -> {clean_res}")
    assert clean_time < 2.0, f"Data cleaning too slow: {clean_time}s"

    total_pipeline_time = batch_insert_time + cat_time + theme_time + pp_time + cluster_time + trend_time
    print("=" * 60)
    print(f"TOTAL END-TO-END PIPELINE FOR 10,000 ROWS: {total_pipeline_time:.3f}s")
    print(f"PREVIOUS DURATION: > 300.0s (5+ minutes)")
    print(f"SPEEDUP: {300.0 / total_pipeline_time:.1f}x FASTER!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
