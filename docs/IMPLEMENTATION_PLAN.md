# Implementation Plan — Placement Readiness & Career Intelligence Portal

## Strategy

**MVP-first vertical slice**: Build one complete path (Student → Resume → Profile → Skill Gap → Coding Analytics → Matching → Readiness Score → Validation → Faculty Approval → Dashboard) before expanding. Follow the 14-lab progression from the specification.

---

## Phase A — Foundations (Labs 1–6) — Week 1–2

### Lab 1: Coordinator Planner Loop
**Goal**: Establish clarify → plan → revise agent loop.

| Deliverable | Details |
|------------|---------|
| Project scaffolding | Backend (FastAPI + SQLAlchemy), Frontend (Next.js + shadcn), Docker Compose |
| Database setup | PostgreSQL + pgvector, Alembic migrations, initial schema |
| Coordinator agent | LangGraph StateGraph with plan/revise loop |
| Basic auth | JWT registration/login |
| **Acceptance** | Given a vague request, asks clarifying questions and yields an editable plan |

**Files created**: Project structure, `docker-compose.yml`, initial models, auth API, coordinator skeleton.

---

### Lab 2: Tool-Using Agent
**Goal**: Agent calls tools for data and computation, not memory.

| Deliverable | Details |
|------------|---------|
| Resume upload API | POST endpoint with file validation |
| Resume text extraction | PDF/DOCX → text (PyPDF2, python-docx) |
| Student profile reader | Tool to read profiles from DB |
| Role requirements reader | Tool to read job requirements |
| Domain calculator | Skill coverage computation tool |
| **Acceptance** | Key data always comes from tools, never invented in prompt |

---

### Lab 3: Reusable Skills
**Goal**: Package repeatable capabilities as typed, reusable skills.

| Deliverable | Details |
|------------|---------|
| Plan/blueprint skill | Creates locked execution plan from parameters |
| Formatting skill | Renders readiness plan in structured format |
| Skill normalization | Maps raw tech names to canonical skills taxonomy |
| **Acceptance** | Same skill works for two different students without code changes |

---

### Lab 4: Memory & Retrieval
**Goal**: Separate short-term run state from long-term stored knowledge.

| Deliverable | Details |
|------------|---------|
| Run state (StateGraph) | Current draft, intermediate results |
| Long-term store | Prior profiles, skill benchmarks (pgvector) |
| Tag-based retrieval | Filter stored data by tags |
| Similarity retrieval | Embedding-based similar student lookup |
| **Acceptance** | Retrieval returns correctly-tagged candidates and similar prior items |

---

### Lab 5: Governed Connector
**Goal**: One typed connector for all data sources.

| Deliverable | Details |
|------------|---------|
| Connector interface | `get_student_profile()`, `get_resume()`, `get_role_requirements()`, etc. |
| Student connector | Profile, resume, skills access |
| Role connector | Job requirements, company roles, benchmarks |
| Coding connector | Coding platform analytics access |
| Evidence connector | Store/retrieve evidence records |
| **Acceptance** | All data access through connector; swapping a source changes no agent code |

---

### Lab 6: Governed Runtime
**Goal**: Runtime with budgets, checkpoints, and audit log.

| Deliverable | Details |
|------------|---------|
| Runtime controller | Budget enforcement, checkpoint/resume |
| Audit service | Write audit events for every step |
| Approval gates | Basic gate interface |
| Token tracking | Per-agent token usage |
| **Acceptance** | Every action is logged; a crashed run resumes from checkpoint |

---

## Phase B — Orchestration (Labs 7–8) — Week 3

### Lab 7: Full Node Graph
**Goal**: Wire all specialist agents into one explicit graph.

| Deliverable | Details |
|------------|---------|
| Resume Agent | Full parse → structured profile |
| Skill Gap Agent | Profile vs requirements → gap report |
| Coding Analytics Agent | Platform data → analytics report |
| Job Matching Agent | Scoring engine + match ranking |
| Interview Agent | Mock Q&A + roadmap generation |
| Complete graph | All agents connected with validation back-edge |
| Validation Agent | All 12 validation checks |
| **Acceptance** | One command yields a validated readiness plan draft end-to-end |

---

### Lab 8: Parallel Processing + Merge
**Goal**: Skill Gap and Coding Analytics run in parallel.

| Deliverable | Details |
|------------|---------|
| Parallel fan-out | Skill Gap + Coding Analytics nodes run concurrently |
| Join/merge node | Combine results for Job Matching Agent |
| Batch processing | Process multiple students (admin feature) |
| **Acceptance** | Parallel run matches sequential quality at lower wall-clock time |

---

## Phase C — Applied Reliability (Labs 9–11) — Week 4–5

### Lab 9: Evidence Grounding
**Goal**: Every output grounded in cited, in-scope evidence.

| Deliverable | Details |
|------------|---------|
| Evidence model | Structured evidence records with source/scope/tags |
| Evidence attachment | Each agent output includes evidence records |
| Evidence API | Retrieve evidence for any entity |
| Grounding step | Verify all outputs have evidence; reject ungrounded |
| **Acceptance** | Every output maps to an in-scope source; ungrounded candidates rejected |

---

### Lab 10: Self-Healing Validation
**Goal**: Diagnose validation failures, regenerate only failing component.

| Deliverable | Details |
|------------|---------|
| Failure diagnosis | Map validation failure → responsible agent |
| Targeted regeneration | Re-run only the failing agent |
| Retry budget | Configurable max retries with escalation |
| Failure injection tests | Tests for each failure type |
| **Acceptance** | Injected faults are detected and fixed within retry budget |

---

### Lab 11: SDLC Factory (Acceptance Suite)
**Goal**: Treat plan as spec, output as tested implementation.

| Deliverable | Details |
|------------|---------|
| Acceptance test suite | Automated tests that run before human review |
| Build command | Plan → readiness plan + passing acceptance report |
| Full test coverage | Unit + integration + E2E tests |
| **Acceptance** | No result advances to officer without a fully passing acceptance report |

---

## Phase D — Governance & Capstone (Labs 12–14) — Week 5–6

### Lab 12: Safety & Governance
**Goal**: Approval workflow, versioning, rollback, security.

| Deliverable | Details |
|------------|---------|
| RBAC enforcement | Complete role-based access control |
| Consent management | Full consent workflow |
| Approval workflow | Officer review → approve/reject/edit → publish |
| Versioning | Create version on approval |
| Rollback | One-click restore previous version |
| Security hardening | CORS, rate limiting, headers, input validation |
| **Acceptance** | Only officer-approved results publish; any release rolls back cleanly |

---

### Lab 13: Domain Specialists
**Goal**: Role-family packs for specialization.

| Deliverable | Details |
|------------|---------|
| Software engineer pack | Specialized benchmarks, interview questions |
| Core engineering pack | DSA-focused analytics, system design questions |
| Analytics pack | Statistics/ML-focused assessment |
| Higher studies pack | Research orientation, GRE/GATE preparation |
| Specialist registry | Pluggable specialist selection |
| **Acceptance** | Specialist outputs use valid domain patterns and produce checkable results |

---

### Lab 14: Capstone — Deployed System
**Goal**: Full integration, deployment, demo.

| Deliverable | Details |
|------------|---------|
| Full Docker deployment | All services containerized |
| Mock data seeding | 10 students, 20 companies, 30 roles |
| Student frontend | Consent → upload → dashboard → interview → roadmap |
| Officer frontend | Queue → review → evidence → approve → audit |
| Admin frontend | Config → skills → companies → users |
| Complete demo | Full flow with one synthetic student |
| Self-healing demo | Injected validation failure → auto-repair |
| Documentation | All docs complete and current |
| **Acceptance** | Full demo completes in one session; audit trail complete |

---

## Implementation Milestones

| Week | Labs | Key Deliverable | Exit Criteria |
|------|------|----------------|---------------|
| 1 | Labs 1–3 | Runnable planner + core skills | Coordinator produces editable plans |
| 2 | Labs 4–6 | Data via connector; audited runs | All data through connector; audit log operational |
| 3 | Labs 7–8 | End-to-end draft pipeline | One command → full readiness plan draft |
| 4 | Labs 9–10 | Grounded output; auto-repair | Evidence attached; failure injection tests pass |
| 5 | Labs 11–12 | Tested artifact; governance | Acceptance suite gates output; approval workflow works |
| 6 | Labs 13–14 | Deployed system + demo | Complete demo on real case; all tests pass |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM latency/cost | Medium | Schedule slip | Mock LLM for tests; budget enforcement |
| Schema changes mid-build | Medium | Rework | Lock schema by Lab 5; migrations for changes |
| LangGraph learning curve | Medium | Slow Lab 7 | Start with simple graphs; expand incrementally |
| Frontend complexity | Medium | Late delivery | Simple functional UI first; polish in Lab 14 |
| Test environment setup | Low | Blocked testing | Docker-compose for reproducible environments |
| API key management | Low | Security incident | Environment variables from Day 1 |
