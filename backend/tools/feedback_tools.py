"""
Feedback Tools for CrewAI Multi-Agent System.
Wraps PM Copilot's NLP engines, statistical models, and clustering algorithms
into standard CrewAI tool interfaces.
"""

from typing import List, Dict, Any
from crewai.tools import tool
from services.theme_extraction import (
    extract_themes_from_feedback,
    extract_pain_points_from_feedback,
)
from services.clustering import cluster_feature_requests
from services.trend_analysis import generate_trend_analysis, calculate_health_score


@tool("Extract NLP Themes")
def extract_nlp_themes_tool(feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract high-level recurring product themes, category alignments,
    sentiment distributions, and top keywords across customer feedback.
    """
    return extract_themes_from_feedback(feedback_items)


@tool("Detect Customer Pain Points")
def detect_pain_points_tool(feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect friction areas and customer pain points, calculating deterministic
    impact scores (0-100), severity levels (high/medium/low), and deduplicated quotes.
    """
    return extract_pain_points_from_feedback(feedback_items)


@tool("Cluster Feature Requests")
def cluster_feature_requests_tool(feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group customer feature requests into opportunity clusters with calculated
    priority scores (0-100), demand levels, and unique customer demand counts.
    """
    return cluster_feature_requests(feedback_items)


@tool("Analyze Product Trends and Health")
def analyze_product_trends_tool(feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze chronological sentiment trajectory, volume velocity, and
    calculate overall product sentiment health score (0-100).
    """
    trends = generate_trend_analysis(feedback_items)
    health = calculate_health_score(feedback_items)
    return {
        "health_score": health,
        "trends": trends,
    }
