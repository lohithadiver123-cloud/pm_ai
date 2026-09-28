"""
Product Requirement Document (PRD) data models for Milestone 3.
Defines schemas for AI-powered PRD generation, persistence, updates, and export.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PersonaItem(BaseModel):
    """Target user persona and user archetype."""
    role: str = Field(..., description="Persona title or archetype, e.g. 'Power Creator'")
    description: str = Field("", description="Brief background of the persona")
    pain_points: List[str] = Field(default_factory=list, description="Primary frustrations")
    goals: List[str] = Field(default_factory=list, description="Key goals and motivations")


class FunctionalRequirement(BaseModel):
    """Specific functional requirement entry."""
    id: str = Field(..., description="Requirement ID (e.g. 'FR-01')")
    title: str = Field(..., description="Requirement title")
    description: str = Field(..., description="Detailed specification of the capability")
    priority: str = Field("P0", description="Priority level: P0 (Must), P1 (Should), P2 (Nice to have)")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Validation criteria")
    edge_cases: List[str] = Field(default_factory=list, description="Known edge cases and boundary conditions")


class NonFunctionalRequirement(BaseModel):
    """Non-functional requirement entry."""
    category: str = Field(..., description="Performance, Security, Scalability, Availability, Accessibility")
    requirement: str = Field(..., description="Quantifiable SLA, threshold, or compliance rule")


class MetricKPI(BaseModel):
    """Success metric or Key Performance Indicator."""
    metric: str = Field(..., description="Name of the metric (e.g. 'Login Success Rate')")
    baseline: str = Field("", description="Current baseline value (e.g. '82%')")
    target: str = Field(..., description="Target value post-launch (e.g. '99.5%')")
    tracking_mechanism: str = Field("", description="Analytics event or monitoring tool")


class RiskMitigation(BaseModel):
    """Identified product/technical risk and its mitigation strategy."""
    risk: str = Field(..., description="Description of the risk")
    severity: str = Field("medium", description="high, medium, or low")
    mitigation: str = Field(..., description="Mitigation approach and fallback plan")


class UserJourneyStep(BaseModel):
    """User journey narrative step."""
    step: int = Field(..., description="Sequence number")
    stage: str = Field(..., description="Stage name (e.g. Discovery, Execution, Resolution)")
    user_action: str = Field(..., description="What the user does")
    system_response: str = Field(..., description="What the product does")


class PRDGenerateRequest(BaseModel):
    """Payload for generating a new PRD using Generative AI."""
    workspace_id: str = Field(..., description="Workspace ID where feedback context is sourced")
    title: Optional[str] = Field(None, description="Optional title or focus for the PRD")
    feature_cluster_id: Optional[str] = Field(None, description="Feature cluster to base the PRD on")
    pain_point_id: Optional[str] = Field(None, description="Customer pain point to solve")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt or feature description")
    target_audience: Optional[str] = Field(None, description="Target customer segment")
    strategic_goals: Optional[str] = Field(None, description="Key strategic business goals")
    tone: Optional[str] = Field("comprehensive", description="comprehensive, lean_mvp, or technical")


class PRDUpdateRequest(BaseModel):
    """Payload for updating an existing PRD."""
    title: Optional[str] = None
    status: Optional[str] = None  # draft, in_review, approved, archived
    executive_summary: Optional[str] = None
    problem_statement: Optional[str] = None
    target_users_and_personas: Optional[List[Dict[str, Any]]] = None
    goals_and_objectives: Optional[List[str]] = None
    scope_in: Optional[List[str]] = None
    scope_out: Optional[List[str]] = None
    functional_requirements: Optional[List[Dict[str, Any]]] = None
    non_functional_requirements: Optional[List[Dict[str, Any]]] = None
    success_metrics_kpis: Optional[List[Dict[str, Any]]] = None
    technical_dependencies: Optional[List[str]] = None
    risks_and_mitigations: Optional[List[Dict[str, Any]]] = None
    raw_markdown: Optional[str] = None


class PRDModel(BaseModel):
    """Complete structured PRD document model."""
    id: str = Field(..., description="Unique PRD document ID")
    workspace_id: str = Field(..., description="Workspace ID")
    title: str = Field(..., description="PRD Document Title")
    status: str = Field("draft", description="draft, in_review, approved, archived")
    version: str = Field("1.0", description="Document semantic version")
    source_type: str = Field("custom", description="feature_cluster, pain_point, or custom")
    source_id: Optional[str] = Field(None, description="Linked cluster or pain point ID")
    executive_summary: str = Field("", description="Executive briefing")
    problem_statement: str = Field("", description="Detailed problem statement grounded in user feedback")
    target_users_and_personas: List[PersonaItem] = Field(default_factory=list)
    goals_and_objectives: List[str] = Field(default_factory=list)
    scope_in: List[str] = Field(default_factory=list)
    scope_out: List[str] = Field(default_factory=list)
    user_journeys: List[UserJourneyStep] = Field(default_factory=list)
    functional_requirements: List[FunctionalRequirement] = Field(default_factory=list)
    non_functional_requirements: List[NonFunctionalRequirement] = Field(default_factory=list)
    success_metrics_kpis: List[MetricKPI] = Field(default_factory=list)
    technical_dependencies: List[str] = Field(default_factory=list)
    risks_and_mitigations: List[RiskMitigation] = Field(default_factory=list)
    raw_markdown: str = Field("", description="Formatted GitHub markdown representation")
    ai_generated: bool = Field(True, description="Whether generated by Generative AI")
    ai_model: Optional[str] = Field(None, description="AI model used for generation")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
