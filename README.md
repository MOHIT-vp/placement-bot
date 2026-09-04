# placement-bot

# Placement-Bot: Intelligent Career Guidance System

**Placement-Bot** is a comprehensive career intelligence platform that combines deterministic data processing with cutting-edge AI to provide personalized placement readiness assessments and upskilling roadmaps.

## Features

- 📚 **Student Assessment**: Analyzes resumes, GitHub, and LeetCode profiles to map technical skills against industry demands.
- 🤖 **Agentic Workflow**: Uses a multi-agent system (Skill Agent, Resume Agent, Interview Agent, Gap Analysis Agent) for deep profile understanding.
- 📊 **Deterministic Grounding**: Every AI-generated insight is backed by traceable evidence and a validation pipeline.
- 🎯 **Company Matching**: Scores students against specific company requirements with gap analysis.
- 🛠️ **Upskilling Roadmap**: Generates personalized learning paths to bridge skill gaps.
- 🏢 **Placement Cell Dashboard**: Role-based access for faculty to monitor student progress and manage cohorts.

## Tech Stack

### Backend
- **Framework**: FastAPI
- **AI/ML**: Pydantic, LangChain, LangGraph, Gemini API
- **Database**: MongoDB (with ODM), Redis (for caching/job queues)
- **Infrastructure**: Docker, Docker Compose

### Frontend
- **Framework**: Next.js (React)
- **Styling**: Tailwind CSS, Lucide React
- **Language**: TypeScript

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js and npm (for frontend)

### 1. Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd /run/media/aditya/Windows/Placement Bot/backend
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up environment variables:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` with your MongoDB URI, Gemini API Key, and Redis credentials.

4.  Run the application:
    ```bash
    uvicorn app.main:app --reload --host [IP_ADDRESS] --port 8000
    ```

### 2. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd /run/media/aditya/Windows/Placement Bot/frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Run the development server:
    ```bash
    npm run dev
    ```

### 3. Using Docker Compose (Quick Start)

1.  Ensure Docker is running.
2.  Run the command:
    ```bash
    docker compose up --build
    ```

## Testing

### Acceptance Tests
We run deterministic contract tests to ensure the AI pipeline behaves predictably.

-   **Skill Gap Tests**: Verify skill calculation logic.
-   **Validation Tests**: Ensure the gatekeeper validates all inputs correctly.
-   **Pipeline Tests**: Verify the full E2E flow from assessment to roadmap generation.

**Run tests:**
```bash
# Run all tests
pytest backend/tests/acceptance

# Run specific test suite
pytest backend/tests/acceptance/test_pipeline_contract.py
```

## Project Structure

```
placement-bot/
├── app/                 # Backend Core
│   ├── agents/          # AI Agent Logic
│   ├── config/          # Settings & Config
│   ├── schemas/         # Pydantic Models & Evidence
│   └── main.py          # FastAPI App Entry Point
├── frontend/            # Next.js UI
├── tests/               # Unit & Acceptance Tests
├── scripts/             # Utility Scripts
└── docker-compose.yml   # Container Orchestration
```

## Development

### Adding a New Agent
1.  Create a new module in `app/agents/`.
2.  Define the `*_agent_node(state)` function.
3.  Ensure it returns a state dictionary.
4.  Import it in `app/orchestrator.py`.
5.  Update `app/schemas/evidence.py` with new evidence types if necessary.