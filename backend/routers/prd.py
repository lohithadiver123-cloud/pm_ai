"""
PRD Router for Milestone 3.
Provides endpoints for:
- Generating AI-driven PRDs from customer feedback, feature clusters, or pain points
- Fetching PRDs for a workspace
- Viewing, editing, updating status, and deleting PRDs
- Exporting PRD as raw Markdown
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from models.prd import PRDGenerateRequest, PRDUpdateRequest, PRDModel
from services import prd_service
from routers.auth import get_authorization_header, get_current_user
from routers.feedback import _verify_workspace_access

router = APIRouter(prefix="/api/prd", tags=["prd"])


async def _get_user_from_token(authorization: str) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token)


@router.post("/generate", response_model=Dict[str, Any])
async def generate_prd(
    payload: PRDGenerateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Generate a comprehensive PRD using Generative AI based on workspace feedback."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(payload.workspace_id, user)

    try:
        prd = await prd_service.generate_prd_with_ai(
            workspace_id=payload.workspace_id,
            title=payload.title,
            feature_cluster_id=payload.feature_cluster_id,
            pain_point_id=payload.pain_point_id,
            custom_prompt=payload.custom_prompt,
            target_audience=payload.target_audience,
            strategic_goals=payload.strategic_goals,
            tone=payload.tone or "comprehensive",
        )
        return prd
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PRD generation failed: {str(e)}",
        )


@router.get("/workspace/{workspace_id}", response_model=List[Dict[str, Any]])
async def list_workspace_prds(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Retrieve all PRDs generated for a specific workspace."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await prd_service.get_prds_for_workspace(workspace_id)


@router.get("/{prd_id}", response_model=Dict[str, Any])
async def get_prd(
    prd_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Retrieve a single PRD by ID."""
    user = await _get_user_from_token(authorization)
    prd = await prd_service.get_prd_by_id(prd_id)
    if not prd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found",
        )
    await _verify_workspace_access(prd["workspace_id"], user)
    return prd


@router.put("/{prd_id}", response_model=Dict[str, Any])
async def update_prd_details(
    prd_id: str,
    payload: PRDUpdateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Update editable fields of an existing PRD."""
    user = await _get_user_from_token(authorization)
    existing = await prd_service.get_prd_by_id(prd_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    updated = await prd_service.update_prd(prd_id, updates)
    return updated


@router.delete("/{prd_id}")
async def delete_prd(
    prd_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Delete a PRD."""
    user = await _get_user_from_token(authorization)
    existing = await prd_service.get_prd_by_id(prd_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    success = await prd_service.delete_prd(prd_id)
    return {"success": success, "deleted_id": prd_id}


@router.get("/{prd_id}/export", response_class=PlainTextResponse)
async def export_prd_markdown(
    prd_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Export PRD as raw GitHub-flavored Markdown."""
    user = await _get_user_from_token(authorization)
    existing = await prd_service.get_prd_by_id(prd_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    md = existing.get("raw_markdown") or prd_service._build_markdown_from_prd(existing)
    return PlainTextResponse(content=md, media_type="text/markdown")
