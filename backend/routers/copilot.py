"""
Conversational Product Intelligence Assistant Router for Milestone 3.
Provides endpoints for:
- Chatting with PM Copilot powered by Google Gemini (Pure AI)
- Retrieving and managing conversation history
- Querying workspace knowledge context
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from models.copilot import CopilotChatRequest, CopilotChatResponse
from services import copilot_service
from routers.auth import get_authorization_header, get_current_user
from routers.feedback import _verify_workspace_access

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


async def _get_user_from_token(authorization: str) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token)


@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_copilot(
    payload: CopilotChatRequest,
    authorization: str = Depends(get_authorization_header),
):
    """
    Send a message to PM Copilot and receive a data-grounded response
    grounded in the workspace's customer feedback, themes, pain points, and PRDs.
    """
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(payload.workspace_id, user)

    try:
        response = await copilot_service.chat_with_pm_copilot(
            workspace_id=payload.workspace_id,
            message=payload.message,
            session_id=payload.session_id or "default",
            conversation_history=payload.conversation_history or [],
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PM Copilot chat failed: {str(e)}",
        )


@router.get("/history/{workspace_id}", response_model=List[Dict[str, Any]])
async def get_history(
    workspace_id: str,
    session_id: str = Query("default", description="Conversation session ID"),
    authorization: str = Depends(get_authorization_header),
):
    """Retrieve chat message history for a workspace session."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await copilot_service.get_copilot_history(workspace_id, session_id)


@router.delete("/history/{workspace_id}")
async def clear_history(
    workspace_id: str,
    session_id: str = Query("default", description="Conversation session ID"),
    authorization: str = Depends(get_authorization_header),
):
    """Clear chat conversation history for a workspace session."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    success = await copilot_service.clear_copilot_history(workspace_id, session_id)
    return {"success": success, "workspace_id": workspace_id, "session_id": session_id}


@router.get("/context/{workspace_id}", response_model=Dict[str, Any])
async def get_workspace_context(
    workspace_id: str,
    authorization: str = Depends(get_authorization_header),
):
    """Inspect the PM Copilot's active knowledge context for this workspace."""
    user = await _get_user_from_token(authorization)
    await _verify_workspace_access(workspace_id, user)
    return await copilot_service.build_workspace_pm_context(workspace_id)
