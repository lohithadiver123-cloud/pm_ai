# AI-Driven Product Assistant (Milestone 1)

## Project title
AI-Driven Product Assistant based on Customer feedback with Planning & Requirements Generation Workspace.

## Clean project structure
The codebase follows a simple backend/frontend split and keeps concerns separated for a more professional layout:

```text
project2/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # environment and app settings
│   ├── database.py                # MongoDB connection setup
│   ├── fallback_db.py             # demo fallback data store
│   ├── requirements.txt           # Python dependencies
│   ├── models/                    # data schemas for users, workspaces, feedback
│   ├── routers/                   # API endpoints for auth, workspace, feedback
│   ├── services/                  # preprocessing, cleaning, categorization logic
│   ├── tests/                     # milestone validation tests
│   └── .env                       # local environment variables
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── public/
│
├── README.md
├── .gitignore
└── .env.example                  # optional example config template
```

This structure keeps the project easier to follow for interviews, demos, and future expansion.

## Objective
This project helps product managers collect customer feedback from multiple sources, clean and analyze it, identify recurring issues, and classify feedback into actionable product themes. The system is designed to reduce manual effort and improve product decision-making.

## Milestone 1 scope (completed)
This project currently covers only Milestone 1 of the product vision:

- Product management workflow understanding
- System requirement definition
- Architecture and data flow design
- Feedback import from CSV/JSON files
- Cleaning and preprocessing of raw customer feedback
- Rule-based categorization and sentiment detection
- Workspace-based feedback organization
- Authenticated user access for PM workflows
- Dashboard summaries for imported feedback

The following are explicitly out of scope for Milestone 1 and should not be implemented in this phase:

- AI-generated PRDs
- User story generation
- Roadmap planning
- Engineering coordination workflows
- Meeting transcript processing
- Advanced forecasting or recommendation algorithms

## System architecture

### Frontend
- React + Vite application
- Pages:
  - Login
  - Register
  - Dashboard
  - Import Data
  - Feedback List

### Backend
- FastAPI service
- Routes:
  - /api/auth
  - /api/workspaces
  - /api/feedback
- MongoDB Atlas as primary database
- JSON fallback for demo/dev environments when MongoDB is unreachable

### Data processing layer
- Preprocessing service for normalization and token cleanup
- Cleaning service for text sanitization, missing values, and duplicate removal
- Categorization service using keyword-based logic for categories and sentiment

## Data model summary

### User
- _id
- name
- email
- password_hash
- created_at
- role
- workspace_ids

### Workspace
- _id
- name
- description
- created_by
- created_at

### Feedback
- _id
- workspace_id
- source
- title
- content
- customer_name
- customer_email
- rating
- category
- sentiment
- status
- cleaned
- created_at
- imported_at

### Import Log
- _id
- workspace_id
- filename
- record_count
- successful
- failed
- status
- imported_at

## Milestone 1 workflow
1. Register or login as a product manager.
2. Create a workspace.
3. Import customer feedback from CSV or JSON.
4. Validate and clean records.
5. Categorize feedback into bug report, feature request, performance issue, or general feedback.
6. Detect sentiment as positive, neutral, or negative.
7. View workspace statistics and summary breakdowns in the dashboard.

## Setup

### Backend
```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Validation checklist for Milestone 1
- [x] User authentication flow is working
- [x] Workspace management exists
- [x] Feedback import supports CSV/JSON files
- [x] Text cleaning is implemented
- [x] Duplicate handling exists
- [x] Rule-based categorization is implemented
- [x] Sentiment detection is implemented
- [x] Dashboard summary stats are available
-



