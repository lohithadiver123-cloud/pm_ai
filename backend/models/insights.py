"""
Insights, Themes, Pain Points, and Feature Clustering model definitions.
Milestone 2: Categorized product insights, theme extraction, and trend analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ThemeItem(BaseModel):
    """Extracted customer feedback theme."""
    id: str = Field(..., description="Unique theme identifier")
    title: str = Field(..., description="Theme title / core topic")
    description: str = Field(..., description="Explanation of what users are discussing")
    category: str = Field(..., description="Primary category associated with this theme")
    frequency: int = Field(..., description="Number of feedback records matching this theme")
    sentiment_breakdown: Dict[str, int] = Field(default_factory=dict, description="Counts of positive/neutral/negative")
    sentiment_score: float = Field(0.0, description="Normalized sentiment score from -1.0 to 1.0")
    keywords: List[str] = Field(default_factory=list, description="Top keywords associated with theme")
    sample_quotes: List[str] = Field(default_factory=list, description="Representative quotes from feedback")


class PainPointItem(BaseModel):
    """Identified customer pain point with severity and business impact."""
    id: str = Field(..., description="Unique pain point identifier")
    title: str = Field(..., description="Pain point summary")
    description: str = Field(..., description="Detailed explanation of the issue")
    severity: str = Field(..., description="Severity level: high, medium, low")
    impact_score: float = Field(..., description="Impact score between 0 and 100")
    affected_users_count: int = Field(..., description="Number of affected feedback entries")
    category: str = Field(..., description="Category: bug_report, performance_issue, general_feedback, etc.")
    root_cause: Optional[str] = Field(None, description="AI-diagnosed underlying root cause of friction")
    recommended_action: str = Field(..., description="Actionable recommendation for product/engineering team")
    sample_quotes: List[str] = Field(default_factory=list, description="Customer quotes highlighting this pain point")
    distinct_sample_quotes: List[str] = Field(default_factory=list, description="Deduplicated customer quotes")
    score_breakdown: Optional[Dict[str, Any]] = Field(None, description="Deterministic components used to compute the impact score")


class FeatureCluster(BaseModel):
    """Clustered feature request group representing an aggregated feature opportunity."""
    id: str = Field(..., description="Unique cluster identifier")
    cluster_name: str = Field(..., description="Synthesized feature request name")
    summary: str = Field(..., description="Summary of user requests in this cluster")
    request_count: int = Field(..., description="Number of individual feedback items in this cluster")
    unique_customers_count: int = Field(0, description="Number of unique customers who requested this feature")
    demand_level: str = Field(..., description="Demand level: high, medium, low")
    priority_score: float = Field(..., description="Calculated priority score (0-100)")
    keywords: List[str] = Field(default_factory=list, description="Key features and capabilities mentioned")
    sample_requests: List[str] = Field(default_factory=list, description="Deduplicated sample user feature requests")
    distinct_sample_quotes: List[str] = Field(default_factory=list, description="Alias for deduplicated quotes")
    feedback_ids: List[str] = Field(default_factory=list, description="List of linked feedback item IDs")
    score_breakdown: Optional[Dict[str, Any]] = Field(None, description="Deterministic components used to compute the priority score")


class TrendDataPoint(BaseModel):
    """Time-series or categorized trend point."""
    period: str = Field(..., description="Date or time bucket")
    total_count: int = Field(0, description="Total feedback in this period")
    positive_count: int = Field(0, description="Positive sentiment count")
    neutral_count: int = Field(0, description="Neutral sentiment count")
    negative_count: int = Field(0, description="Negative sentiment count")
    sentiment_score: float = Field(0.0, description="Average sentiment score (-1.0 to 1.0)")
    top_category: Optional[str] = Field(None, description="Dominant category in this period")
    sentiment_velocity: Optional[float] = Field(0.0, description="Velocity or shift compared to previous period")


class WorkspaceInsightsResponse(BaseModel):
    """Full Milestone 2 Insights Dashboard response model."""
    workspace_id: str
    workspace_name: Optional[str] = None
    total_analyzed: int = Field(..., description="Total feedback items processed")
    health_score: float = Field(..., description="Overall product sentiment health score (0-100)")
    themes: List[ThemeItem] = Field(default_factory=list, description="Extracted recurring product themes")
    pain_points: List[PainPointItem] = Field(default_factory=list, description="Detected customer pain points")
    feature_clusters: List[FeatureCluster] = Field(default_factory=list, description="Aggregated feature request clusters")
    trends: List[TrendDataPoint] = Field(default_factory=list, description="Trend trajectory over time")
    category_distribution: Dict[str, int] = Field(default_factory=dict, description="Category distribution counts")
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict, description="Sentiment distribution counts")
    ai_summary: Optional[Dict[str, Any]] = Field(None, description="AI-generated executive briefing & friction analysis")
    ai_powered: bool = Field(False, description="Whether insights were synthesized with real LLM AI")
    ai_model: Optional[str] = Field(None, description="Name of the AI model used")
    analyzed_at: Optional[datetime] = None
