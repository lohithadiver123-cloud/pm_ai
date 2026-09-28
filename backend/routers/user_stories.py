"""
User Story and Acceptance Criteria Router for Milestone 3.
Provides endpoints for:
- Automatically generating Agile user stories and Gherkin acceptance criteria
- Listing stories by workspace (or filtered by PRD)
- Updating story points, T-shirt size, priority, definition of done, and Kanban status
- Deleting user stories
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from models.user_story import (
    UserStoryGenerateRequest,
    UserStoryUpdateRequest,
    UserStoryStatusUpdateRequest,
    UserStoryModel,
)
from services import user_story_service
from routers.auth import get_authorization_header, get_current_user
from routers.feedback import _verify_workspace_access

router = APIRouter(prefix="/api/user-stories", tags=["user_stories"])


async def _get_user_from_token(authorization: str) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token)


@router.post("/generate", response_model=List[Dict[str, Any]])
async def generate_stories(
    payload: UserStoryGenerateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Automatically generate Agile User Stories with Gherkin acceptance criteria."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(payload.workspace_id, user)

    try:
        stories = await user_story_service.generate_user_stories_with_ai(
            workspace_id=payload.workspace_id,
            prd_id=payload.prd_id,
            feature_cluster_id=payload.feature_cluster_id,
            custom_prompt=payload.custom_prompt,
            count=payload.count or 5,
            persona=payload.persona,
        )
        return stories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User story generation failed: {str(e)}",
        )


@router.get("/workspace/{workspace_id}", response_model=List[Dict[str, Any]])
async def list_workspace_stories(
    workspace_id: str,
    prd_id: Optional[str] = Query(None, description="Optional PRD filter"),
    authorization: str = Depends(get_authorization_header),
):
    """Retrieve user stories for a workspace, optionally filtered by PRD."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await user_story_service.get_stories_for_workspace(workspace_id, prd_id=prd_id)


@router.get("/{story_id}", response_model=Dict[str, Any])
async def get_story(
    story_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Retrieve a single user story by ID."""
    user = await _get_user_from_token(authorization)
    story = await user_story_service.get_story_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User story not found",
        )
    await _verify_workspace_access(story["workspace_id"], user)
    return story


@router.put("/{story_id}", response_model=Dict[str, Any])
async def update_story_details(
    story_id: str,
    payload: UserStoryUpdateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Update editable fields of a user story."""
    user = await _get_user_from_token(authorization)
    existing = await user_story_service.get_story_by_id(story_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User story not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    updated = await user_story_service.update_story(story_id, updates)
    return updated


@router.patch("/{story_id}/status", response_model=Dict[str, Any])
async def update_story_status(
    story_id: str,
    payload: UserStoryStatusUpdateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Quick update of Kanban column status (backlog, in_progress, in_review, done)."""
    user = await _get_user_from_token(authorization)
    existing = await user_story_service.get_story_by_id(story_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User story not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    updated = await user_story_service.update_story_status(story_id, payload.status)
    return updated


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Delete a user story."""
    user = await _get_user_from_token(authorization)
    existing = await user_story_service.get_story_by_id(story_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User story not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    success = await user_story_service.delete_story(story_id)
    return {"success": success, "deleted_id": story_id}
