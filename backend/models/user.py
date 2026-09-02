"""
User model definitions for request/response validation and database schema.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """Available user roles in the system."""
    PRODUCT_MANAGER = "product_manager"
    ADMIN = "admin"
    VIEWER = "viewer"


class UserCreate(BaseModel):
    """Schema for user registration request."""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=128, description="User's password")


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Schema for user data returned in API responses (excludes password)."""
    id: str = Field(..., alias="_id", description="User's unique identifier")
    name: str
    email: str
    role: UserRole = UserRole.PRODUCT_MANAGER
    workspace_ids: List[str] = Field(default_factory=list, description="List of workspace IDs")
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user data")


class UserInDB(BaseModel):
    """Internal user representation as stored in MongoDB."""
    name: str
    email: str
    password_hash: str
    role: UserRole = UserRole.PRODUCT_MANAGER
    workspace_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        from_attributes = True
