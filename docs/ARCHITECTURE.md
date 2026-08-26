# Architecture — Placement Readiness & Career Intelligence Portal

## 1. System Overview

The Placement Readiness & Career Intelligence Portal is a multi-tier, agentic AI system that transforms student data into evidence-grounded placement readiness assessments. The system follows a **coordinator-plus-workers** architecture with an explicit state-machine graph, governed connectors, and a hard human-approval gate.

### Design Principles

1. **Agents draft and flag; a named human approves** — no consequential placement decision is autonomous
2. **Evidence-grounded** — every recommendation cites verifiable sources
3. **Validation is a hard gate** — no output advances without passing automated checks
4. **Data isolation** — student data is strictly isolated per student
5. **Governed data access** — all data flows through typed connectors
6. **Deterministic scoring** — mathematical calculations in application code, not LLM

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                          │
│  Student Portal │ Placement Officer Dashboard │ Admin Panel        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS / REST API
┌───────────────────────────────┴─────────────────────────────────────┐
│                     API GATEWAY (FastAPI)                           │
│  Auth │ RBAC │ Rate Limiting │ Validation │ OpenAPI │ CORS         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼──────────────────────┐
        │                      │                       │
┌───────┴────────┐  ┌──────────┴──────────┐  ┌────────┴───────────┐
│  AGENT LAYER   │  │  APPLICATION LAYER  │  │  GOVERNANCE LAYER  │
│  (LangGraph)   │  │  (Business Logic)   │  │  (Audit/Approval)  │
│                │  │                     │  │                    │
│ Coordinator    │  │ Scoring Engine      │  │ Approval Workflow  │
│ Resume Agent   │  │ Matching Engine     │  │ Audit Service      │
│ Skill Gap Agt  │  │ Eligibility Engine  │  │ Versioning Service │
│ Coding Agt     │  │ Evidence Service    │  │ Rollback Service   │
│ Matching Agt   │  │ Roadmap Generator   │  │ RBAC Service       │
│ Interview Agt  │  │ Validation Service  │  │ Consent Service    │
│ Validation Agt │  │                     │  │                    │
└───────┬────────┘  └──────────┬──────────┘  └────────┬───────────┘
        │                      │                       │
┌───────┴──────────────────────┴───────────────────────┴───────────┐
│                    CONNECTOR LAYER (Governed)                     │
│  get_student_profile() │ get_resume() │ get_role_requirements()  │
│  get_coding_analytics() │ get_skill_benchmarks()                 │
│  store_evidence() │ get_company_roles()                          │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                       DATA LAYER                                  │
│  PostgreSQL (relational) │ pgvector (embeddings) │ Redis (cache) │
│  File Storage (resumes)                                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Frontend** | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui | Per specification; SSR, type safety, modern UI |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2 | Per specification; async, auto-docs, validation |
| **Agent Orchestration** | LangGraph (StateGraph) | Per specification; explicit graph, state machine, checkpoints |
| **LLM Provider** | Google Gemini / OpenAI (configurable) | Structured output support, function calling |
| **Database** | PostgreSQL 16 + pgvector | Per specification; relational + vector similarity |
| **ORM** | SQLAlchemy 2.0 + Alembic | Per specification; async, migrations |
| **Cache** | Redis 7 | Per specification; session cache, rate limiting, background jobs |
| **Background Jobs** | Celery + Redis | Long-running agent workflows |
| **File Storage** | Local filesystem (dev) / S3-compatible (prod) | Resume storage |
| **Auth** | JWT + bcrypt | Stateless auth, role-based |
| **Deployment** | Docker Compose | Per specification; all services containerized |
| **Testing** | pytest (backend), Jest + Playwright (frontend) | Comprehensive test pyramid |

---

## 4. Service Architecture

### 4.1 Core Services

| Service | Responsibility | Port |
|---------|---------------|------|
| `api-gateway` | FastAPI REST API, auth, routing | 8000 |
| `agent-worker` | LangGraph agent execution (Celery) | — |
| `frontend` | Next.js application | 3000 |
| `postgres` | Primary database + pgvector | 5432 |
| `redis` | Cache, message broker, rate limiting | 6379 |

### 4.2 Internal Module Structure

```
backend/
├── app/
│   ├── api/              # FastAPI routers (versioned)
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── students.py
│   │   │   ├── resumes.py
│   │   │   ├── profiles.py
│   │   │   ├── consents.py
│   │   │   ├── analysis.py
│   │   │   ├── matching.py
│   │   │   ├── interviews.py
│   │   │   ├── roadmaps.py
│   │   │   ├── approvals.py
│   │   │   ├── workflows.py
│   │   │   ├── audit.py
│   │   │   ├── versions.py
│   │   │   ├── admin.py
│   │   │   └── dashboard.py
│   │   └── deps.py       # Dependency injection
│   │
│   ├── agents/           # LangGraph agent definitions
│   │   ├── coordinator.py
│   │   ├── resume_agent.py
│   │   ├── skill_gap_agent.py
│   │   ├── coding_analytics_agent.py
│   │   ├── job_matching_agent.py
│   │   ├── interview_agent.py
│   │   ├── validation_agent.py
│   │   ├── graph.py      # LangGraph state machine
│   │   └── state.py      # Shared state schema
│   │
│   ├── connectors/       # Governed data access
│   │   ├── base.py
│   │   ├── student_connector.py
│   │   ├── role_connector.py
│   │   ├── coding_connector.py
│   │   └── evidence_connector.py
│   │
│   ├── core/             # Application services
│   │   ├── scoring.py    # Deterministic scoring engine
│   │   ├── matching.py   # Matching algorithm
│   │   ├── eligibility.py
│   │   ├── evidence.py
│   │   ├── validation.py
│   │   ├── roadmap.py
│   │   └── config.py
│   │
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   │   ├── auth.py
│   │   ├── approval.py
│   │   ├── audit.py
│   │   ├── versioning.py
│   │   ├── consent.py
│   │   └── file_storage.py
│   │
│   ├── middleware/        # Auth, CORS, rate limiting
│   └── config.py         # Settings via env vars
│
├── alembic/              # Database migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── security/
└── scripts/
    └── seed_mock_data.py

frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── (auth)/       # Login/register
│   │   ├── (student)/    # Student views
│   │   ├── (officer)/    # Placement officer views
│   │   └── (admin)/      # Admin views
│   ├── components/       # Reusable UI components
│   ├── lib/              # Utilities, API client
│   ├── hooks/            # Custom React hooks
│   └── types/            # TypeScript types
└── public/
```

---

## 5. Agent Graph Architecture

The agent pipeline is implemented as a **LangGraph StateGraph** with explicit nodes, edges, conditional branching, and checkpointing.

```
                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Consent   │
                    │  Validation │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Resume    │
                    │    Agent    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │  Skill Gap  │          │   Coding    │
       │    Agent    │          │  Analytics  │
       └──────┬──────┘          └──────┬──────┘
              │                         │
              └────────────┬────────────┘
                           │ (join)
                    ┌──────▼──────┐
                    │     Job     │
                    │  Matching   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Interview  │
                    │    Agent    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Evidence   │
                    │  Grounding  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                 ┌──│ Validation  │──┐
                 │  │    Agent    │  │
                 │  └─────────────┘  │
            FAIL │              PASS │
                 │                   │
        ┌────────▼───────┐   ┌──────▼──────┐
        │   Diagnose &   │   │  Assemble   │
        │   Regenerate   │   │    Draft    │
        └────────┬───────┘   └──────┬──────┘
                 │                   │
                 └──► (retry ≤ MAX)  │
                                     │
                    ┌────────────────▼┐
                    │  HUMAN GATE    │ ◄── Placement Officer
                    │  (Hard Stop)   │     Approve/Edit/Reject
                    └────────┬───────┘
                             │
                      ┌──────▼──────┐
                      │   Publish   │
                      │  (Versioned)│
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │    END      │
                      └─────────────┘
```

---

## 6. Data Flow

### 6.1 Request → Published Result

1. **Student** uploads resume + grants consent via frontend
2. **API Gateway** validates request, authenticates, creates workflow run
3. **Coordinator** initializes LangGraph state, locks execution plan
4. **Resume Agent** extracts structured profile via connector
5. **Skill Gap Agent** + **Coding Analytics Agent** run in parallel via connector
6. **Job Matching Agent** computes scores using deterministic scoring engine
7. **Interview Agent** generates mock interview questions and roadmap
8. **Evidence Grounding** attaches evidence records to each output
9. **Validation Agent** runs all checks; on failure → diagnose + regenerate (bounded)
10. **Draft assembled** and presented to placement officer
11. **Placement Officer** reviews, edits, approves/rejects via dashboard
12. **On approval**: version created, published, audit log written
13. **Student** sees approved readiness plan in their dashboard

### 6.2 State Schema (LangGraph)

```python
class PlacementState(TypedDict):
    run_id: str
    student_id: str
    plan: ExecutionPlan
    consent_status: ConsentStatus
    resume_data: Optional[ResumeData]
    student_profile: Optional[StudentProfile]
    skill_gap_report: Optional[SkillGapReport]
    coding_analytics: Optional[CodingAnalyticsReport]
    matching_result: Optional[MatchingResult]
    interview_result: Optional[InterviewResult]
    roadmap: Optional[Roadmap]
    evidence_records: List[EvidenceRecord]
    validation_report: Optional[ValidationReport]
    retry_count: int
    max_retries: int
    approval_status: ApprovalStatus
    audit_events: List[AuditEvent]
    errors: List[str]
    current_step: str
```

---

## 7. Security Architecture

See `SECURITY_MODEL.md` for full details. Key points:

- **Authentication**: JWT tokens with refresh
- **Authorization**: RBAC with role-scoped data access
- **Data Isolation**: Per-student query scoping at ORM level
- **File Security**: Upload type/size validation, virus scan placeholder, sanitized storage
- **Prompt Injection**: Resume content treated as DATA, sandboxed from LLM instructions
- **Secrets**: All credentials via environment variables, never in code
- **Audit**: Every action logged with actor, timestamp, correlation ID

---

## 8. Integration Points

| External System | Integration Method | Status |
|----------------|-------------------|--------|
| LLM Provider (Gemini/OpenAI) | REST API via SDK | Required |
| Coding Platforms (LeetCode, etc.) | Mock Connector (configurable adapter) | Mock for MVP |
| Email/Notifications | SMTP / mock | Deferred |
| SSO/LDAP | JWT-based auth | Deferred (local auth for MVP) |

---

## 9. Deployment Architecture

```
docker-compose.yml
├── postgres (PostgreSQL 16 + pgvector)
├── redis (Redis 7)
├── backend (FastAPI + Celery worker)
├── frontend (Next.js)
└── nginx (reverse proxy, optional)
```

All configuration via `.env` file. See `DEPLOYMENT.md` for details.
