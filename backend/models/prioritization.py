"""
Feature Prioritization and Impact Analysis models for Milestone 3.
Implements configurable scoring frameworks:
1. RICE Framework (Reach, Impact, Confidence, Effort)
2. Value vs Effort Matrix (2x2 Quadrant)
3. MoSCoW Framework (Must, Should, Could, Won't have)
4. Configurable Multi-Factor Weighted Scoring
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RICEScores(BaseModel):
    """RICE framework metrics and computed score."""
    reach: float = Field(500.0, description="Estimated customers/events affected per period")
    impact: float = Field(1.0, description="0.25 (minimal), 0.5 (low), 1.0 (medium), 2.0 (high), 3.0 (massive)")
    confidence: float = Field(0.8, description="Confidence fraction: 0.2 to 1.0 (20% to 100%)")
    effort: float = Field(2.0, description="Effort in person-months or sprints (0.5 to 10.0)")
    score: float = Field(200.0, description="Computed RICE Score = (Reach * Impact * Confidence) / Effort")


class ValueVsEffort(BaseModel):
    """Value vs Effort 2x2 Matrix coordinates and quadrant."""
    value: float = Field(7.0, description="Customer & business value (1.0 to 10.0)")
    effort: float = Field(4.0, description="Implementation effort & complexity (1.0 to 10.0)")
    quadrant: str = Field("quick_win", description="quick_win, major_project, fill_in, thankless_task")


class WeightedScores(BaseModel):
    """Multi-factor normalized scores (0-100) and weighted aggregate."""
    customer_demand_score: float = Field(70.0, description="Demand derived from feedback volume (0-100)")
    business_impact_score: float = Field(75.0, description="Revenue/retention impact (0-100)")
    feasibility_score: float = Field(65.0, description="Technical feasibility & ease (0-100)")
    risk_mitigation_score: float = Field(60.0, description="Risk reduction / stability value (0-100)")
    final_score: float = Field(69.0, description="Calculated weighted aggregate (0-100)")


class PrioritizedItem(BaseModel):
    """Individual feature opportunity with scores across all frameworks."""
    id: str = Field(..., description="Unique prioritization item ID")
    workspace_id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Feature or initiative name")
    description: str = Field("", description="Summary of user demand and business opportunity")
    category: str = Field("feature_request", description="feature_request, bug_fix, performance, security")
    source_cluster_id: Optional[str] = Field(None, description="Linked Feature Cluster ID")
    source_pain_point_id: Optional[str] = Field(None, description="Linked Pain Point ID")
    rice: RICEScores = Field(default_factory=RICEScores)
    value_vs_effort: ValueVsEffort = Field(default_factory=ValueVsEffort)
    moscow: str = Field("should_have", description="must_have, should_have, could_have, wont_have")
    weighted: WeightedScores = Field(default_factory=WeightedScores)
    ai_rationale: Optional[str] = Field(None, description="AI justification based on real customer feedback")
    feedback_count: int = Field(0, description="Supporting customer feedback records")
    rank: int = Field(1, description="Priority rank order within workspace")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FrameworkWeights(BaseModel):
    """Configurable weights for the custom multi-factor framework."""
    workspace_id: str = Field(..., description="Workspace ID")
    customer_demand_weight: float = Field(0.35, description="Weight for customer demand (0.0 to 1.0)")
    business_impact_weight: float = Field(0.30, description="Weight for business impact (0.0 to 1.0)")
    feasibility_weight: float = Field(0.20, description="Weight for feasibility (0.0 to 1.0)")
    risk_mitigation_weight: float = Field(0.15, description="Weight for risk mitigation (0.0 to 1.0)")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ItemCreateRequest(BaseModel):
    """Request to create a new prioritization item."""
    workspace_id: str
    name: str
    description: Optional[str] = ""
    category: Optional[str] = "feature_request"
    reach: Optional[float] = 500.0
    impact: Optional[float] = 1.0
    confidence: Optional[float] = 0.8
    effort: Optional[float] = 2.0
    value: Optional[float] = 7.0
    moscow: Optional[str] = "should_have"
    customer_demand_score: Optional[float] = 70.0
    business_impact_score: Optional[float] = 75.0
    feasibility_score: Optional[float] = 65.0
    risk_mitigation_score: Optional[float] = 60.0


class ItemUpdateRequest(BaseModel):
    """Request to update an existing prioritization item's scores."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    reach: Optional[float] = None
    impact: Optional[float] = None
    confidence: Optional[float] = None
    effort: Optional[float] = None
    value: Optional[float] = None
    effort_score: Optional[float] = None
    moscow: Optional[str] = None
    customer_demand_score: Optional[float] = None
    business_impact_score: Optional[float] = None
    feasibility_score: Optional[float] = None
    risk_mitigation_score: Optional[float] = None
    ai_rationale: Optional[str] = None
