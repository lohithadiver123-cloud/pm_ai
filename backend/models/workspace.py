"""
Workspace model definitions for request/response validation and database schema.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    """Schema for workspace creation request."""
    name: str = Field(..., min_length=2, max_length=100, description="Workspace name")
    description: Optional[str] = Field(None, max_length=500, description="Workspace description")


class WorkspaceUpdate(BaseModel):
    """Schema for workspace update request."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WorkspaceResponse(BaseModel):
    """Schema for workspace data returned in API responses."""
    id: str = Field(..., alias="_id", description="Workspace unique identifier")
    name: str
    description: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        from_attributes = True


class WorkspaceInDB(BaseModel):
    """Internal workspace representation as stored in MongoDB."""
    name: str
    description: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        from_attributes = True


class WorkspaceStatsResponse(BaseModel):
    """Schema for workspace statistics returned in API responses."""
    workspace_id: str
    workspace_name: str
    total_feedback: int = Field(default=0, description="Total number of feedback entries")
    total_tickets: int = Field(default=0, description="Total number of support tickets")
    by_category: Dict[str, int] = Field(default_factory=dict, description="Feedback count grouped by category")
    by_sentiment: Dict[str, int] = Field(default_factory=dict, description="Feedback count grouped by sentiment")
    by_source: Dict[str, int] = Field(default_factory=dict, description="Feedback count grouped by source")
    cleaned_count: int = Field(default=0, description="Number of cleaned feedback entries")
    categorized_count: int = Field(default=0, description="Number of categorized feedback entries")
