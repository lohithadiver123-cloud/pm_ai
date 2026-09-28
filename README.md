# 🚀 PM Copilot — AI-Driven Product Assistant

> An intelligent product management platform that collects customer feedback from multiple sources, cleans and analyzes it using NLP + AI, identifies recurring issues, extracts actionable themes, and helps product managers make data-driven decisions — all from a single dashboard.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [API Reference](#api-reference)
- [Data Models](#data-models)
- [Milestone 1 — Feedback Pipeline (Completed)](#milestone-1--feedback-pipeline-completed)
- [Milestone 2 — AI-Powered Insights (Completed)](#milestone-2--ai-powered-insights-completed)
- [Milestone 3 — Planning & Requirements Generation Workspace (Completed)](#milestone-3--planning--requirements-generation-workspace-completed)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Future Roadmap (Milestone 4)](#future-roadmap-milestone-4)

---

## Overview

**PM Copilot** helps product managers:

1. **Collect** customer feedback from CSV/JSON files (app reviews, support tickets, surveys)
2. **Clean & Preprocess** raw text — normalize, deduplicate, and sanitize
3. **Categorize** feedback into bug reports, feature requests, performance issues, or general feedback
4. **Detect Sentiment** — positive, neutral, or negative (rule-based + rating-based)
5. **Extract Themes** — identify recurring product topics across all feedback
6. **Surface Pain Points** — detect and rank customer friction areas with explainable impact scores
7. **Cluster Feature Requests** — semantically group user requests into product opportunities
8. **Analyze Trends** — track sentiment shifts, volume patterns, and product health over time
9. **AI Intelligence** — optionally leverage Groq LLMs for executive summaries, root-cause analysis, and strategic insights

---

## Tech Stack

| Layer         | Technology                         | Purpose                                      |
| ------------- | ---------------------------------- | -------------------------------------------- |
| **Frontend**  | React 18 + Vite 5                  | Single-page application with protected routes |
| **Backend**   | FastAPI (Python)                   | RESTful API with async request handling       |
| **Database**  | MongoDB Atlas (Motor async driver) | Cloud-hosted NoSQL document store             |
| **Auth**      | JWT (python-jose) + bcrypt         | Stateless token-based authentication          |
| **NLP**       | NLTK + Custom keyword engine       | Text normalization, tokenization, n-grams     |
| **AI (Optional)** | Groq Cloud LLMs (ALLaM, Qwen, GPT) | Executive summaries & root-cause analysis |
| **Data**      | Pandas                             | CSV/JSON import and data transformation       |
| **Styling**   | Vanilla CSS                        | Custom dark-theme UI with responsive design   |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                      │
│                                                                     │
│   ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────────┐ │
│   │  Login   │ │ Register │ │ Dashboard │ │ Insights Dashboard   │ │
│   └──────────┘ └──────────┘ └───────────┘ └──────────────────────┘ │
│   ┌────────────────────┐ ┌────────────────────┐ ┌────────────────┐ │
│   │  PRD Studio (M3)   │ │ User Stories (M3)  │ │ Prioritize(M3) │ │
│   │  • AI Doc View     │ │ • Kanban Board     │ │ • RICE Scoring │ │
│   │  • Markdown Export │ │ • Gherkin Criteria │ │ • 2x2 Matrix   │ │
│   └────────────────────┘ └────────────────────┘ └────────────────┘ │
│   ┌────────────────────────────────┐ ┌───────────────┐ ┌─────────┐ │
│   │  Conversational Copilot (M3)   │ │ Feedback List │ │ Import  │ │
│   │  • Grounded Chat & Citations   │ └───────────────┘ └─────────┘ │
│   └────────────────────────────────┘                               │
│                                                                     │
│   Components: Navbar, Charts, FloatingCopilot Widget                │
│   Services:   api.js (Axios HTTP client with JWT interceptor)       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP (REST API)
                             │ Vite Dev Proxy → localhost:8000
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Python)                       │
│                                                                     │
│   ┌─────────────────────── API ROUTERS ──────────────────────────┐  │
│   │                                                               │  │
│   │  /api/auth           → Register, Login, JWT auth              │  │
│   │  /api/workspaces     → Create, list, manage workspaces        │  │
│   │  /api/feedback       → Import, clean, categorize feedback     │  │
│   │  /api/insights       → Themes, pain points, feature clusters  │  │
│   │  /api/prd (M3)       → AI PRD generation, Markdown export     │  │
│   │  /api/user-stories(M3)→ Agile stories, Gherkin criteria, DoD   │  │
│   │  /api/prioritization(M3)→ RICE, 2x2 Matrix, MoSCoW, Weighted   │  │
│   │  /api/copilot (M3)   → Grounded multi-turn conversational AI   │  │
│   │  /api/health         → Health check endpoint                  │  │
│   │                                                               │  │
│   └───────────────────────────┬───────────────────────────────────┘  │
│                               │                                      │
│   ┌─────────────── SERVICES LAYER ──────────────────────────────┐   │
│   │                                                              │   │
│   │  prd_service.py           → Generative AI PRD synthesis      │   │
│   │  user_story_service.py    → Agile decomposition engine       │   │
│   │  prioritization_service.py→ Configurable scoring frameworks  │   │
│   │  copilot_service.py       → Grounded PM assistant & chat     │   │
│   │  theme_extraction.py      → NLP theme mining & pain points   │   │
│   │  clustering.py            → Feature request semantic cluster │   │
│   │  trend_analysis.py        → Sentiment trajectory & health    │   │
│   │  ai_service.py            → Gemini 3.6 Flash & Groq fallback │   │
│   │                                                              │   │
│   └──────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│   ┌───────────── DATA LAYER ────────────────────────────────────┐   │
│   │  database.py   → Motor async MongoDB connection manager      │   │
│   │  fallback_db.py → In-memory JSON store for dev/demo mode     │   │
│   │  config.py      → Centralized settings from .env             │   │
│   └──────────────────────────┬───────────────────────────────────┘   │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │     MongoDB Atlas (Cloud)       │
              │                                │
              │  Collections:                  │
              │   • users                      │
              │   • workspaces                 │
              │   • feedback                   │
              │   • import_logs                │
              │   • workspace_insights         │
              └────────────────────────────────┘
```

---

## Project Structure

```
pm-AI/
├── backend/
│   ├── main.py                          # FastAPI app entry point + lifespan
│   ├── config.py                        # Environment settings (Mongo, JWT, CORS)
│   ├── database.py                      # Motor async MongoDB connection
│   ├── fallback_db.py                   # In-memory JSON fallback for dev/demo
│   ├── check_mongo.py                   # MongoDB connectivity diagnostic tool
│   ├── requirements.txt                 # Python dependencies
│   │
│   ├── models/
│   │   ├── user.py                      # User schema (registration, login)
│   │   ├── workspace.py                 # Workspace schema
│   │   ├── feedback.py                  # Feedback record schema
│   │   └── insights.py                  # Insights response models (themes, pain points, clusters)
│   │
│   ├── routers/
│   │   ├── auth.py                      # /api/auth — register, login, JWT
│   │   ├── workspace.py                 # /api/workspaces — CRUD operations
│   │   ├── feedback.py                  # /api/feedback — import, list, clean, categorize
│   │   └── insights.py                  # /api/insights — full analysis pipeline
│   │
│   ├── services/
│   │   ├── preprocessing.py             # Text normalization + tokenization
│   │   ├── data_cleaning.py             # Text sanitization, dedup, missing values
│   │   ├── categorization.py            # Rule-based category + sentiment detection
│   │   ├── theme_extraction.py          # NLP theme mining + pain point identification
│   │   ├── clustering.py               # Feature request semantic clustering
│   │   ├── trend_analysis.py            # Temporal trends + product health scoring
│   │   └── ai_service.py               # Groq LLM integration (optional AI layer)
│   │
│   └── tests/
│       ├── test_milestone1.py           # Milestone 1 validation tests
│       ├── test_milestone2.py           # Milestone 2 validation tests
│       └── test_10k_benchmark.py        # Performance benchmark (10k+ records)
│
├── frontend/
│   ├── index.html                       # App entry HTML
│   ├── package.json                     # Node.js dependencies
│   ├── vite.config.ts                   # Vite dev server + API proxy config
│   │
│   └── src/
│       ├── index.jsx                    # React DOM render entry
│       ├── index.css                    # Global styles (dark theme)
│       ├── App.jsx                      # Router setup + protected routes
│       │
│       ├── components/
│       │   ├── Navbar.jsx               # Navigation bar with auth state
│       │   └── Charts.jsx              # SVG data visualization components
│       │
│       ├── pages/
│       │   ├── Login.jsx                # User login page
│       │   ├── Register.jsx             # User registration page
│       │   ├── Dashboard.jsx            # Workspace overview + feedback stats
│       │   ├── ImportData.jsx           # CSV/JSON file upload interface
│       │   ├── FeedbackList.jsx         # Paginated feedback browser
│       │   └── InsightsDashboard.jsx    # AI insights + analytics dashboard
│       │
│       └── services/
│           └── api.js                   # Axios HTTP client with JWT auth
│
├── README.md
├── .gitignore
└── .env.example                         # Environment variable template
```

---

## How It Works

### End-to-End Data Flow

```
 CSV/JSON File Upload
        │
        ▼
 ┌──────────────────┐
 │  1. IMPORT        │  Parse CSV/JSON → validate fields → store raw records
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  2. CLEAN         │  Normalize text → remove HTML/special chars → dedup
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  3. CATEGORIZE    │  Rule-based keyword matching → assign category
 │                   │  Bug Report | Feature Request | Performance | General
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  4. SENTIMENT     │  Rating-based (1-5★) or keyword-based detection
 │                   │  Positive | Neutral | Negative
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  5. THEME MINING  │  Domain topic matching → group by recurring themes
 │                   │  (Auth, Performance, UI/UX, Search, Billing, etc.)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  6. PAIN POINTS   │  Filter negative/bug items → group by domain →
 │                   │  Score impact: Volume(35%) + Rating(25%) +
 │                   │  Negative%(25%) + Bug Ratio(15%)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  7. CLUSTERING    │  Group feature requests by semantic similarity
 │                   │  (Jaccard token overlap + keyword patterns)
 │                   │  Score priority: Volume(45%) + Users(30%) + Rating(25%)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  8. TRENDS        │  Aggregate by date → compute sentiment velocity
 │                   │  Calculate Product Health Score (0-100)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  9. AI LAYER      │  (Optional) Groq LLM executive summary,
 │                   │  root-cause analysis, strategic recommendations
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  10. DASHBOARD    │  Visualize all insights with interactive charts
 └──────────────────┘
```

### User Workflow

1. **Register / Login** → Create an account and receive a JWT token
2. **Create a Workspace** → Organize feedback by product or project
3. **Import Feedback** → Upload CSV or JSON files with customer feedback
4. **Auto-Process** → System cleans, categorizes, and detects sentiment
5. **View Dashboard** → See workspace stats, category breakdowns, sentiment overview
6. **Run Analysis** → Trigger the full insights pipeline
7. **Explore Insights** → Dive into themes, pain points, feature clusters, and trends
8. **AI Intelligence** → (Optional) Get LLM-powered executive summaries and root-cause analysis

---

## API Reference

### Authentication

| Method | Endpoint             | Description                    |
| ------ | -------------------- | ------------------------------ |
| POST   | `/api/auth/register` | Register a new user            |
| POST   | `/api/auth/login`    | Login and receive JWT token    |

### Workspaces

| Method | Endpoint                  | Description                    |
| ------ | ------------------------- | ------------------------------ |
| POST   | `/api/workspaces`         | Create a new workspace         |
| GET    | `/api/workspaces`         | List user's workspaces         |
| GET    | `/api/workspaces/:id`     | Get workspace details          |

### Feedback

| Method | Endpoint                               | Description                          |
| ------ | -------------------------------------- | ------------------------------------ |
| POST   | `/api/feedback/:workspace_id/import`   | Import feedback from CSV/JSON file   |
| GET    | `/api/feedback/:workspace_id`          | List feedback (paginated)            |
| POST   | `/api/feedback/:workspace_id/clean`    | Run cleaning pipeline                |
| POST   | `/api/feedback/:workspace_id/categorize` | Run categorization + sentiment     |

### Insights (Milestone 2)

| Method | Endpoint                                    | Description                                |
| ------ | ------------------------------------------- | ------------------------------------------ |
| POST   | `/api/insights/:workspace_id/analyze`       | Run full analysis pipeline                 |
| GET    | `/api/insights/:workspace_id`               | Get cached or computed insights            |
| GET    | `/api/insights/:workspace_id/themes`        | Get extracted themes only                  |
| GET    | `/api/insights/:workspace_id/pain-points`   | Get pain points with severity rankings     |
| GET    | `/api/insights/:workspace_id/clusters`      | Get feature request clusters               |
| GET    | `/api/insights/:workspace_id/trends`        | Get trend trajectory data                  |
| GET    | `/api/insights/ai/status`                   | Check Groq AI availability                |
| POST   | `/api/insights/ai/configure-key`            | Dynamically set Groq API key               |

### Health

| Method | Endpoint       | Description                 |
| ------ | -------------- | --------------------------- |
| GET    | `/api/health`  | API health check            |

---

## Data Models

### User
```json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string",
  "password_hash": "string",
  "role": "product_manager",
  "workspace_ids": ["workspace_id_1", "workspace_id_2"],
  "created_at": "datetime"
}
```

### Workspace
```json
{
  "_id": "ObjectId",
  "name": "string",
  "description": "string",
  "created_by": "user_id",
  "created_at": "datetime"
}
```

### Feedback
```json
{
  "_id": "ObjectId",
  "workspace_id": "string",
  "source": "app_review | support_ticket | survey | social_media | email",
  "title": "string",
  "content": "string",
  "customer_name": "string",
  "customer_email": "string",
  "rating": 1-5,
  "category": "bug_report | feature_request | performance_issue | general_feedback",
  "sentiment": "positive | neutral | negative",
  "theme": "Authentication & Access | Performance & Stability | ...",
  "status": "new | reviewed | resolved",
  "cleaned": true,
  "created_at": "datetime",
  "imported_at": "datetime"
}
```

### Workspace Insights
```json
{
  "workspace_id": "string",
  "total_analyzed": 500,
  "health_score": 72.5,
  "themes": [{ "title": "...", "frequency": 45, "sentiment_score": -0.3 }],
  "pain_points": [{ "title": "...", "severity": "high", "impact_score": 85.0 }],
  "feature_clusters": [{ "cluster_name": "...", "demand_level": "high", "priority_score": 88.0 }],
  "trends": [{ "period": "2025-01-15", "sentiment_score": 0.2, "total_count": 25 }],
  "ai_summary": { "headline": "...", "overview": "...", "top_frictions": [], "quick_wins": [] },
  "analyzed_at": "datetime"
}
```

---

## Milestone 1 — Feedback Pipeline (Completed ✅)

Milestone 1 covers the core feedback ingestion, cleaning, and rule-based analysis:

- ✅ User authentication (register + login with JWT)
- ✅ Workspace management (create, list, switch)
- ✅ Feedback import from CSV and JSON files
- ✅ Text cleaning and preprocessing (normalization, sanitization, dedup)
- ✅ Rule-based categorization (keyword matching across 4 categories)
- ✅ Sentiment detection (rating-based + keyword-based fallback)
- ✅ Dashboard with workspace statistics and summary breakdowns
- ✅ JSON fallback mode when MongoDB is unreachable (for dev/demo)

---

## Milestone 2 — AI-Powered Insights (Completed ✅)

Milestone 2 adds the full intelligence and analytics layer:

- ✅ **Theme Extraction** — NLP-based topic detection across 8 domain areas (Auth, Performance, UI/UX, Search, Notifications, Data Management, Billing, Support)
- ✅ **Pain Point Detection** — Identifies and ranks customer friction areas with explainable impact scores using a deterministic formula: `Volume (35%) + Low Rating (25%) + Negative Sentiment % (25%) + Bug Ratio (15%)`
- ✅ **Feature Request Clustering** — Semantic grouping using Jaccard similarity + keyword-based pattern matching with priority scoring: `Request Volume (45%) + Unique Users (30%) + Rating Satisfaction (25%)`
- ✅ **Trend Analysis** — Chronological sentiment tracking, volume aggregation, and sentiment velocity computation
- ✅ **Product Health Score** — Overall 0–100 health metric based on: `Sentiment Ratio (45pts) + Avg Rating (35pts) + Stability/Bug Ratio (20pts)`
- ✅ **Groq LLM Integration** — Optional AI layer using Groq Cloud (ALLaM, Qwen, GPT models) for executive summaries, root-cause analysis, and strategic recommendations with graceful fallback to heuristic engine
- ✅ **Insights Dashboard** — Full-featured analytics UI with interactive charts, theme breakdowns, pain point rankings, cluster visualizations, and AI summary panel
- ✅ **Performance Optimized** — Sub-second analysis on 10,000+ feedback records with batched DB writes, subsampling, and pre-compiled regex

---

## Milestone 3 — Planning & Requirements Generation Workspace (Completed ✅)

Milestone 3 implements the complete Planning & Requirements Workspace powered by Generative AI:

1. **Generative AI PRD Generation (`/api/prd`)**
   - Integrates Google Gemini (`gemini-3.6-flash`, 1,000,000 token context window) with Groq and deterministic fallback engines.
   - Grounded 100% in real customer feedback, user reviews, and pain points.
   - Comprehensive PRD structure:
     - Executive Summary & Context
     - Problem Statement & Customer Evidence
     - Target User Personas (Frictions, Motivations, Goals)
     - Strategic Goals & Quantitative OKRs
     - Scope Definition (In-Scope vs. Out-of-Scope)
     - Key User Journeys (Discovery, Execution, Outcome)
     - Functional Requirements (ID, P0/P1/P2 priorities, acceptance criteria, edge cases)
     - Non-Functional Requirements (Performance SLAs, Security, Scalability, WCAG Accessibility)
     - Success Metrics & KPIs Table (Baselines, Targets, Telemetry Mechanisms)
     - Technical Dependencies & Risks Mitigation Matrix
   - Export options: One-click copy, download as GitHub-flavored Markdown (.md), and direct user story generation.

2. **Automated User Story & Acceptance Criteria Generation (`/api/user-stories`)**
   - Decomposes PRDs, feature clusters, or custom initiatives into vertical sprint-ready user stories.
   - Standard Agile format: `"As a <role>, I want to <action>, so that <benefit>."`
   - Gherkin-syntax Acceptance Criteria: Scenario with `Given`, `When`, `Then` blocks.
   - Fibonacci Story Points (`1, 2, 3, 5, 8, 13`) and T-Shirt sizing (`XS, S, M, L, XL`).
   - Definition of Done (DoD) checklist and technical architectural notes.
   - Interactive Kanban Board (Backlog → In Progress → In Review/QA → Done) and List/Table view with CSV export.

3. **Feature Prioritization with Configurable Scoring Frameworks (`/api/prioritization`)**
   - Four industry-standard prioritization frameworks in a single unified interface:
     - **RICE Scoring**: `(Reach × Impact × Confidence) / Effort` with inline interactive sliders and instant rank reordering.
     - **Value vs Effort (2x2 Matrix)**: Interactive scatter plot with automatic quadrant mapping:
       - ⚡ *Quick Wins* (High Value, Low Effort)
       - 🚀 *Major Projects* (High Value, High Effort)
       - 🛠️ *Fill-ins* (Low Value, Low Effort)
       - ⏳ *Thankless Tasks* (Low Value, High Effort)
     - **MoSCoW Method**: Interactive 4-column board (Must Have, Should Have, Could Have, Won't Have).
     - **Custom Weighted Scoring**: Dynamic sliders for Customer Demand (%), Business Impact (%), Technical Feasibility (%), and Risk Mitigation (%) with live-updating leaderboards.
   - **Auto-Seed from Feedback**: One-click extraction from Milestone 2 Feature Clusters and Pain Points.
   - **AI Re-Score All**: Leverages Google Gemini to calibrate parameters based on customer demand and sentiment severity.

4. **Conversational Product Intelligence Assistant / Copilot (`/api/copilot`)**
   - Grounded conversational AI assistant (PM Copilot) with real-time access to workspace feedback, pain points, themes, and PRDs.
   - Dedicated Copilot Page (`/copilot`) plus a global **Floating Copilot Widget** accessible from any page.
   - Multi-turn conversation capability with chat history persistence per workspace session.
   - Sources Cited citations: Points directly to supporting feedback quotes, customer volume, and themes.
   - Quick suggested follow-up chips and interactive shortcut buttons ("Generate PRD for this", "User Stories").

---

## Setup & Installation

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **MongoDB Atlas** account (or use the built-in fallback mode for demo)

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env
# Edit .env with your MongoDB URI and secret key

# Start the API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server (proxied to backend on port 8000)
npm run dev -- --host 0.0.0.0 --port 5173
```

The frontend dev server at `http://localhost:5173` automatically proxies API requests to the backend at `http://localhost:8000`.

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# MongoDB Connection
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=<app-name>
DB_NAME=pm_copilot

# JWT Secret (change in production!)
SECRET_KEY=your-secure-secret-key

# (Optional) Groq AI API Key for LLM-powered insights
GROQ_API_KEY=gsk_your_groq_api_key_here
```

> **Note:** If `MONGO_URI` is not configured or MongoDB is unreachable, the app automatically falls back to an in-memory JSON data store for development and demos.

---

## Running Tests

```bash
cd backend

# Milestone 1 validation
python -m unittest tests/test_milestone1.py

# Milestone 2 validation
python -m unittest tests/test_milestone2.py

# Milestone 3 validation (PRD, Stories, Prioritization, Copilot)
python -m unittest tests/test_milestone3.py

# Milestone 3 Integration pipeline
python -m unittest tests/test_milestone3_integration.py

# Run all milestone tests together (22 unit & integration tests)
python -m unittest tests/test_milestone1.py tests/test_milestone2.py tests/test_milestone3.py tests/test_milestone3_integration.py
```

---

## Future Roadmap (Milestone 4 — Planned)

The following features are planned for Milestone 4 (Week 7-8):

- 🗺️ Automated Roadmap Planning & Gantt Visualization
- 🎯 Release Milestones Recommendation Engine
- 📊 Executive Strategy Reports & PDF Generation
- 🔗 Integrations with Jira, Linear, and GitHub Issues
- 🎙️ Meeting Transcript Processing & Ingestion

---

## License

This project is part of an academic/portfolio demonstration of AI-driven product management tooling.

---

<p align="center">
  Built with ❤️ using FastAPI, React, MongoDB, and Groq AI
</p>
