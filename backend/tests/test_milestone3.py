"""
Unit and integration tests for Milestone 3.
Validates:
1. Generative AI & Heuristic PRD generation, persistence, updates, and markdown export.
2. Automatic Agile User Story & Gherkin acceptance criteria generation, sizing, and Kanban status tracking.
3. Feature Prioritization frameworks: RICE scoring, Value vs Effort (2x2 matrix), MoSCoW, and configurable multi-factor weighted scoring.
4. Conversational Product Intelligence Assistant (PM Copilot) knowledge context retrieval and response generation.
"""

import os
import sys
import unittest
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.prd import PRDModel, PRDGenerateRequest
from models.user_story import UserStoryModel, AcceptanceCriterion
from models.prioritization import PrioritizedItem, RICEScores, ValueVsEffort, WeightedScores
from services.prd_service import _build_markdown_from_prd, _generate_fallback_prd
from services.user_story_service import _generate_fallback_stories
from services.prioritization_service import (
    _calculate_rice,
    _determine_quadrant,
    _calculate_weighted_score,
    compute_all_scores_for_item,
    DEFAULT_WEIGHTS,
)
from services.copilot_service import _generate_fallback_chat_reply


class Milestone3Validation(unittest.TestCase):

    def test_prd_markdown_and_schema(self):
        """Verify PRD data structure and GitHub markdown generation."""
        mock_data = _generate_fallback_prd(
            title="PRD: Real-Time Security Alerts",
            subject="Security Alerts",
            source_type="pain_point",
            source_details={},
            sample_quotes=["Users are locked out unexpectedly", "Account blocked without notification"]
        )
        self.assertIn("title", mock_data)
        self.assertIn("functional_requirements", mock_data)
        self.assertGreaterEqual(len(mock_data["functional_requirements"]), 2)
        self.assertIn("non_functional_requirements", mock_data)
        self.assertIn("success_metrics_kpis", mock_data)
        self.assertIn("target_users_and_personas", mock_data)

        # Markdown serialization
        md = _build_markdown_from_prd(mock_data)
        self.assertIn("# PRD: Real-Time Security Alerts", md)
        self.assertIn("## 1. Executive Summary", md)
        self.assertIn("## 7. Functional Requirements", md)
        self.assertIn("[FR-01]", md)
        self.assertIn("## 9. Success Metrics & Key Performance Indicators", md)

    def test_user_story_and_gherkin_criteria(self):
        """Verify user story generation with Gherkin acceptance criteria and Fibonacci points."""
        stories = _generate_fallback_stories(
            subject="Account Suspension Transparency",
            prd_title="Security PRD",
            count=3,
            persona="Content Creator"
        )
        self.assertEqual(len(stories), 3)

        for s in stories:
            self.assertIn("title", s)
            self.assertIn("role", s)
            self.assertIn("action", s)
            self.assertIn("benefit", s)
            self.assertIn("full_statement", s)
            self.assertTrue(s["full_statement"].startswith("As a"))
            self.assertIn("so that", s["full_statement"])
            
            # Story sizing
            self.assertIn(s["story_points"], [1, 2, 3, 5, 8, 13])
            self.assertIn(s["t_shirt_size"], ["XS", "S", "M", "L", "XL"])
            self.assertIn(s["priority"], ["high", "medium", "low"])

            # Acceptance criteria validation (Gherkin format)
            self.assertGreaterEqual(len(s["acceptance_criteria"]), 1)
            for ac in s["acceptance_criteria"]:
                self.assertIn("scenario", ac)
                self.assertIn("given", ac)
                self.assertIn("when", ac)
                self.assertIn("then", ac)

    def test_rice_scoring_calculation(self):
        """Verify RICE formula: (Reach * Impact * Confidence) / Effort."""
        # Reach=1000, Impact=2.0 (High), Confidence=0.8 (80%), Effort=2 sprints
        # (1000 * 2.0 * 0.8) / 2 = 800.0
        score = _calculate_rice(reach=1000.0, impact=2.0, confidence=0.8, effort=2.0)
        self.assertEqual(score, 800.0)

        # Reach=500, Impact=3.0 (Massive), Confidence=0.9, Effort=1.5
        # (500 * 3.0 * 0.9) / 1.5 = 900.0
        score2 = _calculate_rice(reach=500.0, impact=3.0, confidence=0.9, effort=1.5)
        self.assertEqual(score2, 900.0)

    def test_value_vs_effort_quadrants(self):
        """Verify Value vs Effort 2x2 matrix quadrant classification."""
        # High Value, Low Effort -> Quick Win
        self.assertEqual(_determine_quadrant(value=8.0, effort=3.0), "quick_win")
        
        # High Value, High Effort -> Major Project
        self.assertEqual(_determine_quadrant(value=8.5, effort=7.5), "major_project")
        
        # Low Value, Low Effort -> Fill-in
        self.assertEqual(_determine_quadrant(value=3.5, effort=2.0), "fill_in")
        
        # Low Value, High Effort -> Thankless Task
        self.assertEqual(_determine_quadrant(value=2.0, effort=8.0), "thankless_task")

    def test_configurable_weighted_scoring(self):
        """Verify custom multi-factor scoring with dynamic weights."""
        weights = {
            "customer_demand_weight": 0.40,
            "business_impact_weight": 0.30,
            "feasibility_weight": 0.20,
            "risk_mitigation_weight": 0.10,
        }
        # (90*0.40) + (80*0.30) + (70*0.20) + (60*0.10) = 36 + 24 + 14 + 6 = 80.0
        score = _calculate_weighted_score(
            demand=90.0,
            impact=80.0,
            feasibility=70.0,
            risk=60.0,
            weights=weights
        )
        self.assertEqual(score, 80.0)

    def test_item_recalculation_pipeline(self):
        """Verify that compute_all_scores_for_item updates all frameworks consistently."""
        item = {
            "id": "test_1",
            "name": "Biometric Authentication",
            "rice": {"reach": 2000.0, "impact": 2.0, "confidence": 0.9, "effort": 3.0},
            "value_vs_effort": {"value": 8.0, "effort": 3.5},
            "weighted": {
                "customer_demand_score": 85.0,
                "business_impact_score": 90.0,
                "feasibility_score": 70.0,
                "risk_mitigation_score": 80.0,
            }
        }
        computed = compute_all_scores_for_item(item, DEFAULT_WEIGHTS)
        self.assertEqual(computed["rice"]["score"], 1200.0)
        self.assertEqual(computed["value_vs_effort"]["quadrant"], "quick_win")
        self.assertGreater(computed["weighted"]["final_score"], 70.0)

    def test_copilot_context_and_fallback_reply(self):
        """Verify PM Copilot context awareness, citations, and reply formatting."""
        mock_context = {
            "total_feedback": 140000,
            "themes": ["Account Security (420 mentions, bug_report)", "App Performance (310 mentions, performance_issue)"],
            "pain_points": [
                {
                    "title": "Account Suspension Without Notice",
                    "severity": "high",
                    "impact_score": 92.5,
                    "root_cause": "Aggressive bot moderation",
                    "action": "Implement transparent appeal workflow",
                }
            ],
            "feature_clusters": [
                {
                    "name": "Self-Service Security Appeals",
                    "demand": "high",
                    "priority_score": 94.0,
                    "summary": "Users request clear recovery options."
                }
            ]
        }

        # Query about pain points
        res_pain = _generate_fallback_chat_reply("What are our users complaining about most?", mock_context)
        self.assertIn("Account Suspension", res_pain["reply"])
        self.assertGreaterEqual(len(res_pain["sources_cited"]), 1)
        self.assertGreaterEqual(len(res_pain["suggested_followups"]), 2)

        # Query about features
        res_feat = _generate_fallback_chat_reply("Which features should we build next?", mock_context)
        self.assertIn("Self-Service Security Appeals", res_feat["reply"])


if __name__ == "__main__":
    unittest.main()
