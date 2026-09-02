"""
Workspace router.
Handles workspace CRUD operations and statistics.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
import database
from fallback_db import (
    create_workspace as fb_create_workspace,
    find_feedback_by_workspace as fb_find_feedback_by_workspace,
    find_workspaces_by_user as fb_find_workspaces_by_user,
)
from models.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceStatsResponse,
)
from routers.auth import get_authorization_header, get_current_user

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


async def _get_user_from_token(authorization: str) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    authorization: str = Depends(get_authorization_header),
):
    """
    Create a new workspace.
    Associates the workspace with the authenticated user.
    """
    user = await _get_user_from_token(authorization)

    # Create workspace document
    workspace_doc = {
        "name": workspace_data.name,
        "description": workspace_data.description,
        "created_by": str(user["_id"]),
        "created_at": datetime.utcnow(),
    }

    if not database._mongodb_available:
        workspace_doc["created_at"] = workspace_doc["created_at"].isoformat()
        return await fb_create_workspace(workspace_doc)

    # Insert into database
    result = await database.db.workspaces.insert_one(workspace_doc)
    workspace_id = str(result.inserted_id)

    # Add workspace ID to user's workspace_ids
    await database.db.users.update_one(
        {"_id": user["_id"]},
        {"$push": {"workspace_ids": workspace_id}},
    )

    # Fetch and return the created workspace
    created = await database.db.workspaces.find_one({"_id": result.inserted_id})
    created["_id"] = workspace_id
    return created


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    authorization: str = Depends(get_authorization_header),
):
    """
    List all workspaces belonging to the authenticated user.
    """
    user = await _get_user_from_token(authorization)

    if not database._mongodb_available:
        return await fb_find_workspaces_by_user(str(user["_id"]))

    # Find all workspaces created by this user
    cursor = database.db.workspaces.find({"created_by": str(user["_id"])}).sort("created_at", -1)
    workspaces = await cursor.to_list(length=None)

    # Convert ObjectId to string for JSON serialization
    for ws in workspaces:
        ws["_id"] = str(ws["_id"])

    return workspaces


@router.get("/{workspace_id}/stats", response_model=WorkspaceStatsResponse)
async def get_workspace_stats(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """
    Get statistics for a specific workspace.
    Returns counts of total feedback, tickets, and breakdowns by category/sentiment/source.
    """
    user = await _get_user_from_token(authorization)

    if not database._mongodb_available:
        workspaces = await fb_find_workspaces_by_user(str(user["_id"]))
        workspace = next((ws for ws in workspaces if ws.get("_id") == workspace_id), None)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        feedback_items, total_feedback = await fb_find_feedback_by_workspace(workspace_id, 0, 100000)
        total_tickets = sum(1 for item in feedback_items if item.get("source") == "support_ticket")
        by_category = {}
        by_sentiment = {}
        by_source = {}

        for item in feedback_items:
            if item.get("category"):
                by_category[item["category"]] = by_category.get(item["category"], 0) + 1
            if item.get("sentiment"):
                by_sentiment[item["sentiment"]] = by_sentiment.get(item["sentiment"], 0) + 1
            if item.get("source"):
                by_source[item["source"]] = by_source.get(item["source"], 0) + 1

        return WorkspaceStatsResponse(
            workspace_id=workspace_id,
            workspace_name=workspace["name"],
            total_feedback=total_feedback,
            total_tickets=total_tickets,
            by_category=by_category,
            by_sentiment=by_sentiment,
            by_source=by_source,
            cleaned_count=sum(1 for item in feedback_items if item.get("cleaned") is True),
            categorized_count=sum(1 for item in feedback_items if item.get("category")),
        )

    # Verify workspace exists and belongs to the user
    workspace = await database.db.workspaces.find_one({"_id": ObjectId(workspace_id)})
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    if workspace["created_by"] != str(user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    # Get total feedback count
    total_feedback = await database.db.feedback.count_documents({"workspace_id": workspace_id})

    # Get support ticket count specifically
    total_tickets = await database.db.feedback.count_documents({
        "workspace_id": workspace_id,
        "source": "support_ticket",
    })

    # Aggregation pipeline for category breakdown
    category_pipeline = [
        {"$match": {"workspace_id": workspace_id, "category": {"$ne": None}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ]
    category_results = await database.db.feedback.aggregate(category_pipeline).to_list(length=None)
    by_category = {str(r["_id"]): r["count"] for r in category_results}

    # Aggregation pipeline for sentiment breakdown
    sentiment_pipeline = [
        {"$match": {"workspace_id": workspace_id, "sentiment": {"$ne": None}}},
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
    ]
    sentiment_results = await database.db.feedback.aggregate(sentiment_pipeline).to_list(length=None)
    by_sentiment = {str(r["_id"]): r["count"] for r in sentiment_results}

    # Aggregation pipeline for source breakdown
    source_pipeline = [
        {"$match": {"workspace_id": workspace_id}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    source_results = await database.db.feedback.aggregate(source_pipeline).to_list(length=None)
    by_source = {str(r["_id"]): r["count"] for r in source_results}

    # Count cleaned and categorized
    cleaned_count = await database.db.feedback.count_documents({
        "workspace_id": workspace_id,
        "cleaned": True,
    })
    categorized_count = await database.db.feedback.count_documents({
        "workspace_id": workspace_id,
        "category": {"$ne": None},
    })

    return WorkspaceStatsResponse(
        workspace_id=workspace_id,
        workspace_name=workspace["name"],
        total_feedback=total_feedback,
        total_tickets=total_tickets,
        by_category=by_category,
        by_sentiment=by_sentiment,
        by_source=by_source,
        cleaned_count=cleaned_count,
        categorized_count=categorized_count,
    )
