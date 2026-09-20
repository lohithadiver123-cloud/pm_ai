"""
Milestone 2 Validation Test Suite.
Validates:
1. Theme extraction & NLP topic mining
2. Customer pain-point detection and impact severity scoring
3. Feature request clustering and aggregation accuracy
4. Temporal trend analysis and Product Health Score calculation
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.theme_extraction import extract_themes_from_feedback, extract_pain_points_from_feedback, extract_keywords_and_phrases
from services.clustering import cluster_feature_requests
from services.trend_analysis import generate_trend_analysis, calculate_health_score


class Milestone2Validation(unittest.TestCase):
    def setUp(self):
        self.sample_dataset = [
            {
                "_id": "1",
                "title": "Login crash on iOS",
                "content": "The app crashes every time I enter my password on the signin screen.",
                "category": "bug_report",
                "sentiment": "negative",
                "rating": 1,
                "created_at": "2025-01-10T10:00:00",
            },
            {
                "_id": "2",
                "title": "Need dark mode support",
                "content": "Please add dark mode support! Working at night hurts my eyes.",
                "category": "feature_request",
                "sentiment": "positive",
                "rating": 5,
                "created_at": "2025-01-11T10:00:00",
            },
            {
                "_id": "3",
                "title": "Dark theme request",
                "content": "Would love a dark theme option in settings.",
                "category": "feature_request",
                "sentiment": "positive",
                "rating": 4,
                "created_at": "2025-01-12T10:00:00",
            },
            {
                "_id": "4",
                "title": "Very slow dashboard load times",
                "content": "Dashboard takes over 15 seconds to load. Performance is unacceptable.",
                "category": "performance_issue",
                "sentiment": "negative",
                "rating": 1,
                "created_at": "2025-01-13T10:00:00",
            },
            {
                "_id": "5",
                "title": "Export to CSV or PDF",
                "content": "Can we please export feedback reports as CSV or PDF for management meetings?",
                "category": "feature_request",
                "sentiment": "neutral",
                "rating": 4,
                "created_at": "2025-01-14T10:00:00",
            },
            {
                "_id": "6",
                "title": "Slack integration please",
                "content": "It would be great to receive real-time notifications in Slack via webhooks.",
                "category": "feature_request",
                "sentiment": "positive",
                "rating": 5,
                "created_at": "2025-01-15T10:00:00",
            },
        ]

    def test_extract_themes(self):
        themes = extract_themes_from_feedback(self.sample_dataset)
        self.assertGreater(len(themes), 0)
        theme_titles = [t["title"] for t in themes]
        # Should detect themes related to Auth, UI/Theming, Performance, etc.
        self.assertTrue(
            any("Authentication" in t or "Performance" in t or "UI" in t or "Export" in t for t in theme_titles)
        )
        for theme in themes:
            self.assertIn("frequency", theme)
            self.assertIn("sentiment_score", theme)
            self.assertIn("keywords", theme)

    def test_extract_pain_points_severity_and_impact(self):
        pain_points = extract_pain_points_from_feedback(self.sample_dataset)
        self.assertGreater(len(pain_points), 0)

        # Pain points should include Login/Auth or Performance issues
        titles = [p["title"] for p in pain_points]
        self.assertTrue(any("Authentication" in t or "Performance" in t for t in titles))

        # Check severity and impact scores
        for pp in pain_points:
            self.assertIn(pp["severity"], ["high", "medium", "low"])
            self.assertGreaterEqual(pp["impact_score"], 0)
            self.assertLessEqual(pp["impact_score"], 100)
            self.assertTrue(len(pp["recommended_action"]) > 10)

    def test_feature_request_clustering(self):
        clusters = cluster_feature_requests(self.sample_dataset)
        self.assertGreater(len(clusters), 0)

        cluster_names = [c["cluster_name"] for c in clusters]
        # Dark mode requests (2 items) should be grouped into Dark Mode cluster
        dark_mode_cluster = next((c for c in clusters if "Dark Mode" in c["cluster_name"]), None)
        self.assertIsNotNone(dark_mode_cluster)
        self.assertGreaterEqual(dark_mode_cluster["request_count"], 2)
        self.assertIn("dark mode", [k.lower() for k in dark_mode_cluster["keywords"]])

    def test_trend_analysis_and_health_score(self):
        trends = generate_trend_analysis(self.sample_dataset)
        self.assertGreater(len(trends), 0)

        for pt in trends:
            self.assertIn("period", pt)
            self.assertIn("total_count", pt)
            self.assertIn("sentiment_score", pt)

        health_score = calculate_health_score(self.sample_dataset)
        self.assertGreaterEqual(health_score, 0.0)
        self.assertLessEqual(health_score, 100.0)

    def test_keyword_and_ngram_extraction(self):
        texts = [
            "Dark mode theme is awesome",
            "Dark mode theme requested by many users",
            "Export reports to CSV or Excel",
        ]
        phrases = extract_keywords_and_phrases(texts, top_k=5)
        phrase_words = [p[0] for p in phrases]
        self.assertTrue(any("dark" in p for p in phrase_words))

    def test_ai_status_and_models(self):
        from services.ai_service import check_ai_status, analyze_feedback_with_ai
        from models.insights import PainPointItem, WorkspaceInsightsResponse

        status = check_ai_status()
        self.assertIn("available", status)
        self.assertIn("provider", status)
        self.assertEqual(status["provider"], "Groq")

        # Fallback handling on empty input
        res = analyze_feedback_with_ai([])
        self.assertIsNone(res)

        # Test model fields
        pp = PainPointItem(
            id="pp1",
            title="Search latency",
            description="Slow search queries",
            severity="high",
            impact_score=85.0,
            affected_users_count=5,
            category="performance_issue",
            root_cause="Missing database compound index on query keywords",
            recommended_action="Create text index"
        )
        self.assertEqual(pp.root_cause, "Missing database compound index on query keywords")


if __name__ == "__main__":
    unittest.main()

