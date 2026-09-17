# ProjectIQ

An AI-powered project management web application designed for the manufacturing sector. Manage projects with intelligent tools for charter generation, WBS, Gantt scheduling, resource optimization, budget tracking, inventory planning, risk management, quality control, predictive maintenance, and real-time KPI dashboards — all accessible through a modern web interface with an AI chatbot assistant.

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **AI Project Charter Generator** | Defines project scope, objectives, stakeholders, and deliverables |
| 2 | **WBS Generator** | Breaks projects into tasks and milestones automatically |
| 3 | **Smart Gantt Chart & Scheduling** | Plans timelines, dependencies, and critical path |
| 4 | **Resource Allocation Optimizer** | Assigns workers, machines, and equipment efficiently |
| 5 | **Budget & Cost Tracking** | Tracks planned vs. actual costs and identifies overruns |
| 6 | **Inventory & Material Planning** | Ensures materials are available and prevents delays |
| 7 | **AI Risk Management** | Identifies, prioritizes risks and suggests mitigations |
| 8 | **Quality Management System** | Monitors defects, inspections, and CAPA |
| 9 | **Predictive Maintenance** | Predicts machine failures to reduce downtime |
| 10 | **Project KPI Dashboard** | Real-time visibility into schedule, cost, quality, and health |
| 11 | **AI Project Assistant (Chatbot)** | Answers questions, summarizes progress, gives recommendations |
| 12 | **User Authentication & Project CRUD** | Login with username/password, update project details from UI |

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React, Vite, Tailwind CSS, Recharts
- **AI:** OpenAI GPT-4o-mini (with intelligent mock fallback when no API key is set)

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
```

Edit `.env` and optionally set your `OPENAI_API_KEY` for live AI responses.

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Open the App

Navigate to **http://localhost:5173**

### Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Project Manager | `pm_user` | `pm123` |

A demo project "Production Line Upgrade - Line #3" is pre-seeded for the PM user.

## Usage

1. **Login** with demo credentials
2. **Dashboard** — View all projects, create new ones
3. **Project Detail** — Click a project to access all 12 feature tabs
4. **Generate AI Content** — Click "Generate with AI" on any feature tab
5. **Edit Project** — Update details on the Overview tab and click Save
6. **AI Assistant** — Use the chat tab to ask questions about the project

### Example Chat Prompts

- "What's the project status?"
- "What are the top risks?"
- "How is the budget looking?"
- "Are we on schedule?"

## API Documentation

With the backend running, visit **http://localhost:8000/docs** for interactive Swagger API documentation.

## Project Structure

```
aiAgent/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── models.py         # Database models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── auth.py           # JWT authentication
│   │   ├── ai_service.py     # AI feature services
│   │   └── routes/           # API route handlers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Login, Dashboard, ProjectDetail
│   │   ├── components/       # Chatbot, Layout, shared UI
│   │   ├── context/          # Auth context
│   │   └── api.js            # API client
│   └── package.json
└── README.md
```

## AI Configuration

The app works out of the box with intelligent mock AI responses. For live AI-powered generation:

1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Set `OPENAI_API_KEY=sk-...` in `backend/.env`
3. Restart the backend server

## License

MIT
