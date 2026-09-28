"""Seed a demo account so every UI page renders with realistic data."""

import os
import sys

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
EMAIL, PW = "design@review.dev", "DesignReview1!"
CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_feedback.csv")

requests.post(f"{BASE}/api/auth/register", json={"name": "Avery Chen", "email": EMAIL, "password": PW}, timeout=60)
tok = requests.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PW}, timeout=60).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

ws = next((w["_id"] for w in requests.get(f"{BASE}/api/workspaces", headers=H, timeout=60).json()
           if w["name"] == "Acme Mobile"), None)
if not ws:
    ws = requests.post(f"{BASE}/api/workspaces", headers=H, timeout=60,
                       json={"name": "Acme Mobile", "description": "Q3 mobile feedback"}).json()["_id"]

have = requests.get(f"{BASE}/api/feedback", headers=H, params={"workspace_id": ws, "limit": 1}, timeout=60).json().get("total", 0)
if not have:
    with open(CSV, "rb") as fh:
        requests.post(f"{BASE}/api/feedback/import", headers=H,
                      files={"file": ("sample_feedback.csv", fh, "text/csv")},
                      data={"workspace_id": ws, "source": "app_review"}, timeout=120)
    requests.post(f"{BASE}/api/feedback/clean", headers=H, data={"workspace_id": ws}, timeout=120)
    requests.post(f"{BASE}/api/feedback/categorize", headers=H, data={"workspace_id": ws}, timeout=120)
    requests.post(f"{BASE}/api/insights/{ws}/analyze", headers=H, timeout=300)
    requests.post(f"{BASE}/api/prd/generate", headers=H, json={"workspace_id": ws, "title": "Mobile Stability Program"}, timeout=300)
    requests.post(f"{BASE}/api/user-stories/generate", headers=H, json={"workspace_id": ws, "count": 6}, timeout=300)
    requests.post(f"{BASE}/api/prioritization/workspace/{ws}/auto-seed", headers=H, timeout=180)

print(f"LOGIN {EMAIL} / {PW}")
print(f"workspace_id={ws}")
print("feedback:", requests.get(f"{BASE}/api/feedback", headers=H, params={"workspace_id": ws, "limit": 1}, timeout=60).json().get("total"))
print("prioritization items:", len(requests.get(f"{BASE}/api/prioritization/workspace/{ws}", headers=H, timeout=60).json()))
print("prds:", len(requests.get(f"{BASE}/api/prd/workspace/{ws}", headers=H, timeout=60).json()))
print("stories:", len(requests.get(f"{BASE}/api/user-stories/workspace/{ws}", headers=H, timeout=60).json()))
print("Set localStorage: pm_copilot_active_ws =", ws)
