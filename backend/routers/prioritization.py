"""
Prioritization and Impact Analysis Router for Milestone 3.
Provides endpoints for:
- RICE framework scoring and rankings
- Value vs Effort (2x2 Matrix) coordinate updates
- MoSCoW categorization
- Configurable multi-factor weighted scoring
- Auto-seeding from customer feedback clusters and pain points
- AI-assisted scoring recommendation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from models.prioritization import (
    PrioritizedItem,
    FrameworkWeights,
    ItemCreateRequest,
    ItemUpdateRequest,
)
from services import prioritization_service
from routers.auth import get_authorization_header, get_current_user
from routers.feedback import _verify_workspace_access

router = APIRouter(prefix="/api/prioritization", tags=["prioritization"])


async def _get_user_from_token(authorization: str) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token)


@router.get("/workspace/{workspace_id}", response_model=List[Dict[str, Any]])
async def list_prioritization_items(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Retrieve all prioritization items for a workspace."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    items = await prioritization_service.get_prioritization_items(workspace_id)
    if not items:
        # Automatically auto-seed if first time opening
        items = await prioritization_service.auto_seed_prioritization_from_insights(workspace_id)
    return items


@router.post("/workspace/{workspace_id}/auto-seed", response_model=List[Dict[str, Any]])
async def auto_seed_items(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Auto-seed prioritization items directly from customer feedback clusters & pain points."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await prioritization_service.auto_seed_prioritization_from_insights(workspace_id)


@router.post("/workspace/{workspace_id}/ai-evaluate", response_model=List[Dict[str, Any]])
async def ai_evaluate_items(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Run Google Gemini AI evaluation to recommend priority scores based on customer demand."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await prioritization_service.ai_evaluate_all_priorities(workspace_id)


@router.get("/workspace/{workspace_id}/weights", response_model=Dict[str, Any])
async def get_weights(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Get configurable framework weights for the workspace."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await prioritization_service.get_or_create_workspace_weights(workspace_id)


@router.post("/workspace/{workspace_id}/weights", response_model=Dict[str, Any])
async def update_weights(
    workspace_id: str,
    weights: Dict[str, float],
    authorization: str = Depends(get_authorization_header),
):
    """Update configurable weights and recompute weighted ranks for all items."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await prioritization_service.save_workspace_weights(workspace_id, weights)


@router.post("/item", response_model=Dict[str, Any])
async def create_item(
    payload: ItemCreateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Create a new custom feature prioritization item."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(payload.workspace_id, user)
    return await prioritization_service.create_prioritization_item(payload.dict())


@router.put("/item/{item_id}", response_model=Dict[str, Any])
async def update_item(
    item_id: str,
    payload: ItemUpdateRequest,
    authorization: str = Depends(get_authorization_header),
):
    """Update scores for a prioritization item (recalculates RICE, 2x2 quadrant, and Weighted scores)."""
    user = await _get_user_from_token(authorization)
    
    # Retrieve to check workspace access
    existing = await prioritization_service.get_prioritization_item(item_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization item not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    updates = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    
    # Map flat update fields into subdocuments if present
    rice_updates = {}
    if "reach" in updates:
        rice_updates["reach"] = updates.pop("reach")
    if "impact" in updates:
        rice_updates["impact"] = updates.pop("impact")
    if "confidence" in updates:
        rice_updates["confidence"] = updates.pop("confidence")
    if "effort" in updates:
        rice_updates["effort"] = updates.pop("effort")
    if rice_updates:
        updates["rice"] = {**existing.get("rice", {}), **rice_updates}

    v_updates = {}
    if "value" in updates:
        v_updates["value"] = updates.pop("value")
    if "effort_score" in updates:
        v_updates["effort"] = updates.pop("effort_score")
    if v_updates:
        updates["value_vs_effort"] = {**existing.get("value_vs_effort", {}), **v_updates}

    w_updates = {}
    if "customer_demand_score" in updates:
        w_updates["customer_demand_score"] = updates.pop("customer_demand_score")
    if "business_impact_score" in updates:
        w_updates["business_impact_score"] = updates.pop("business_impact_score")
    if "feasibility_score" in updates:
        w_updates["feasibility_score"] = updates.pop("feasibility_score")
    if "risk_mitigation_score" in updates:
        w_updates["risk_mitigation_score"] = updates.pop("risk_mitigation_score")
    if w_updates:
        updates["weighted"] = {**existing.get("weighted", {}), **w_updates}

    updated = await prioritization_service.update_prioritization_item(item_id, updates)
    return updated


@router.delete("/item/{item_id}")
async def delete_item(
    item_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Delete a prioritization item."""
    user = await _get_user_from_token(authorization)
    
    existing = await prioritization_service.get_prioritization_item(item_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prioritization item not found",
        )
    await _verify_workspace_access(existing["workspace_id"], user)

    success = await prioritization_service.delete_prioritization_item(item_id)
    return {"success": success, "deleted_id": item_id}
