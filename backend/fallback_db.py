"""
Fallback in-memory/JSON database when MongoDB is unavailable.
Used for Milestone 1 demo purposes.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Data directory for JSON storage
DATA_DIR = os.path.join(os.path.dirname(__file__), ".demo_data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
WORKSPACES_FILE = os.path.join(DATA_DIR, "workspaces.json")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")

# In-memory cache
_users_cache: Dict[str, Dict] = {}
_workspaces_cache: Dict[str, Dict] = {}
_feedback_cache: Dict[str, Dict] = {}


def _load_json(filepath: str) -> List[Dict]:
    """Load JSON file or return empty list."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def _save_json(filepath: str, data: List[Dict]) -> None:
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def _load_cache() -> None:
    """Load all data from JSON files into memory."""
    global _users_cache, _workspaces_cache, _feedback_cache
    
    users = _load_json(USERS_FILE)
    _users_cache = {u['_id']: u for u in users}
    
    workspaces = _load_json(WORKSPACES_FILE)
    _workspaces_cache = {w['_id']: w for w in workspaces}
    
    feedback = _load_json(FEEDBACK_FILE)
    _feedback_cache = {f['_id']: f for f in feedback}


def _save_all() -> None:
    """Save all caches back to JSON files."""
    _save_json(USERS_FILE, list(_users_cache.values()))
    _save_json(WORKSPACES_FILE, list(_workspaces_cache.values()))
    _save_json(FEEDBACK_FILE, list(_feedback_cache.values()))


# ============= User Operations =============

async def create_user(user_data: Dict[str, Any]) -> Dict:
    """Create a new user."""
    _load_cache()
    user_id = str(len(_users_cache) + 1)
    user_data['_id'] = user_id
    user_data['created_at'] = datetime.utcnow().isoformat()
    user_data.setdefault('role', 'product_manager')
    user_data['workspace_ids'] = []
    _users_cache[user_id] = user_data
    _save_all()
    return user_data


async def find_user_by_email(email: str) -> Optional[Dict]:
    """Find user by email."""
    _load_cache()
    for user in _users_cache.values():
        if user.get('email') == email:
            return user
    return None


async def find_user_by_id(user_id: str) -> Optional[Dict]:
    """Find user by ID."""
    _load_cache()
    return _users_cache.get(user_id)


# ============= Workspace Operations =============

async def create_workspace(workspace_data: Dict[str, Any]) -> Dict:
    """Create a new workspace."""
    _load_cache()
    workspace_id = str(len(_workspaces_cache) + 1)
    workspace_data['_id'] = workspace_id
    workspace_data['created_at'] = datetime.utcnow().isoformat()
    _workspaces_cache[workspace_id] = workspace_data
    
    # Add to user's workspace_ids
    if 'created_by' in workspace_data:
        user = await find_user_by_id(workspace_data['created_by'])
        if user:
            if 'workspace_ids' not in user:
                user['workspace_ids'] = []
            user['workspace_ids'].append(workspace_id)
            _users_cache[workspace_data['created_by']] = user
    
    _save_all()
    return workspace_data


async def find_workspaces_by_user(user_id: str) -> List[Dict]:
    """Find all workspaces for a user."""
    _load_cache()
    return [w for w in _workspaces_cache.values() if w.get('created_by') == user_id]


# ============= Feedback Operations =============

async def create_feedback(feedback_data: Dict[str, Any]) -> Dict:
    """Create feedback entry."""
    _load_cache()
    feedback_id = str(len(_feedback_cache) + 1)
    feedback_data['_id'] = feedback_id
    feedback_data['created_at'] = datetime.utcnow().isoformat()
    _feedback_cache[feedback_id] = feedback_data
    _save_all()
    return feedback_data


async def find_feedback_by_workspace(workspace_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Dict], int]:
    """Find feedback for a workspace with pagination."""
    _load_cache()
    items = [f for f in _feedback_cache.values() if f.get('workspace_id') == workspace_id]
    total = len(items)
    return items[skip:skip+limit], total


async def update_feedback(feedback_id: str, updates: Dict) -> Optional[Dict]:
    """Update feedback entry."""
    _load_cache()
    if feedback_id in _feedback_cache:
        _feedback_cache[feedback_id].update(updates)
        _save_all()
        return _feedback_cache[feedback_id]
    return None


print("Fallback JSON database loaded")
