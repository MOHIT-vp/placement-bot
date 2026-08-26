# Database Design — Placement Readiness & Career Intelligence Portal

## 1. Design Principles

- **Normalized relational model** — use proper foreign keys, indexes, constraints
- **JSON only where genuinely appropriate** — structured data in typed columns
- **Per-student data isolation** — enforced at query level via student_id scoping
- **Audit everything** — every table has `created_at`, `updated_at`; key tables have versioning
- **Migrations via Alembic** — no manual schema changes

---

## 2. Entity-Relationship Overview

```
users ──┬── students ──── consents
        │                  ├── resumes ──── student_profiles
        │                  │                  ├── student_skills
        │                  │                  ├── student_projects
        │                  │                  └── student_experiences
        │                  ├── coding_analytics
        │                  ├── skill_gap_reports ── skill_gap_items
        │                  ├── readiness_scores ── score_breakdowns
        │                  ├── company_matches
        │                  ├── interview_sessions ── interview_questions
        │                  │                          └── interview_responses
        │                  ├── roadmaps ── roadmap_items
        │                  └── evidence_records
        │
        ├── placement_officers
        └── admins

roles ── role_skills
companies ── jobs ── job_requirements
skills (master taxonomy)
scoring_configs

workflow_runs ── agent_executions
              ── validation_reports ── validation_checks
              ── approval_decisions
              ── versions
audit_logs
```

---

## 3. Table Definitions

### 3.1 User & Authentication

```sql
-- Core user account (all roles)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL CHECK (role IN ('student', 'placement_officer', 'faculty', 'admin')),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Student-specific profile
CREATE TABLE students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrollment_no   VARCHAR(50) UNIQUE,
    department      VARCHAR(100),
    semester        INTEGER,
    cgpa            DECIMAL(4,2),
    phone           VARCHAR(20),
    linkedin_url    VARCHAR(500),
    github_url      VARCHAR(500),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Placement officer profile
CREATE TABLE placement_officers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department      VARCHAR(100),
    designation     VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Consent Management

```sql
CREATE TABLE consents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    consent_type    VARCHAR(50) NOT NULL CHECK (consent_type IN (
                        'resume_processing', 'coding_platform', 'academic_records',
                        'placement_matching', 'data_sharing'
                    )),
    granted         BOOLEAN NOT NULL DEFAULT false,
    granted_at      TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    ip_address      VARCHAR(45),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, consent_type)
);
CREATE INDEX idx_consents_student ON consents(student_id);
```

### 3.3 Resume & Profile

```sql
CREATE TABLE resumes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       INTEGER NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    file_hash       VARCHAR(64),  -- SHA-256 for dedup
    raw_text        TEXT,         -- Extracted text (sanitized)
    status          VARCHAR(50) DEFAULT 'uploaded' CHECK (status IN (
                        'uploaded', 'processing', 'parsed', 'failed'
                    )),
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    parsed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_resumes_student ON resumes(student_id);

-- Structured profile extracted from resume + manual data
CREATE TABLE student_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    resume_id       UUID REFERENCES resumes(id),
    summary         TEXT,
    education_level VARCHAR(50),
    specialization  VARCHAR(100),
    years_experience INTEGER DEFAULT 0,
    status          VARCHAR(50) DEFAULT 'draft' CHECK (status IN (
                        'draft', 'validated', 'approved', 'published'
                    )),
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_profiles_student ON student_profiles(student_id);
```

### 3.4 Skills

```sql
-- Master skill taxonomy
CREATE TABLE skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    normalized_name VARCHAR(100) NOT NULL UNIQUE,  -- lowercase, standardized
    category        VARCHAR(50) NOT NULL CHECK (category IN (
                        'programming_language', 'framework', 'database', 'cloud',
                        'devops', 'soft_skill', 'domain', 'tool', 'other'
                    )),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_normalized ON skills(normalized_name);

-- Skills extracted from student profile
CREATE TABLE student_skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    profile_id      UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    skill_id        UUID NOT NULL REFERENCES skills(id),
    proficiency     VARCHAR(20) CHECK (proficiency IN (
                        'beginner', 'intermediate', 'advanced', 'expert'
                    )),
    source          VARCHAR(50) CHECK (source IN (
                        'resume', 'coding_platform', 'self_assessment', 'academic', 'manual'
                    )),
    verified        BOOLEAN DEFAULT false,
    evidence_id     UUID,  -- FK to evidence_records
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, skill_id, profile_id)
);
CREATE INDEX idx_student_skills_student ON student_skills(student_id);
```

### 3.5 Projects & Experience

```sql
CREATE TABLE student_projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    technologies    TEXT[],  -- Array of tech used
    url             VARCHAR(500),
    start_date      DATE,
    end_date        DATE,
    is_academic     BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE student_experiences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    company_name    VARCHAR(255),
    role_title      VARCHAR(255),
    description     TEXT,
    start_date      DATE,
    end_date        DATE,
    is_current      BOOLEAN DEFAULT false,
    experience_type VARCHAR(50) CHECK (experience_type IN (
                        'internship', 'full_time', 'part_time', 'freelance', 'research'
                    )),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.6 Companies, Roles & Requirements

```sql
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    industry        VARCHAR(100),
    size            VARCHAR(50) CHECK (size IN ('startup', 'small', 'medium', 'large', 'enterprise')),
    website         VARCHAR(500),
    description     TEXT,
    location        VARCHAR(255),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    role_family     VARCHAR(50) CHECK (role_family IN (
                        'software', 'core', 'analytics', 'higher_studies', 'management', 'other'
                    )),
    description     TEXT,
    min_cgpa        DECIMAL(4,2),
    min_experience  INTEGER DEFAULT 0,
    package_lpa     DECIMAL(6,2),
    location        VARCHAR(255),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_company ON jobs(company_id);
CREATE INDEX idx_jobs_role_family ON jobs(role_family);

-- Skills required for a specific job/role
CREATE TABLE role_skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id        UUID NOT NULL REFERENCES skills(id),
    importance      VARCHAR(20) NOT NULL CHECK (importance IN (
                        'required', 'preferred', 'nice_to_have'
                    )),
    min_proficiency VARCHAR(20) CHECK (min_proficiency IN (
                        'beginner', 'intermediate', 'advanced', 'expert'
                    )),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, skill_id)
);
CREATE INDEX idx_role_skills_job ON role_skills(job_id);

-- Configurable skill benchmarks for target roles
CREATE TABLE skill_benchmarks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_family     VARCHAR(50) NOT NULL,
    skill_id        UUID NOT NULL REFERENCES skills(id),
    expected_level  VARCHAR(20) NOT NULL,
    weight          DECIMAL(5,2) DEFAULT 1.0,
    source          VARCHAR(100),  -- e.g., "Industry survey 2025"
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.7 Coding Analytics

```sql
CREATE TABLE coding_analytics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    platform        VARCHAR(50) NOT NULL,  -- 'leetcode', 'hackerrank', etc.
    total_solved    INTEGER DEFAULT 0,
    easy_solved     INTEGER DEFAULT 0,
    medium_solved   INTEGER DEFAULT 0,
    hard_solved     INTEGER DEFAULT 0,
    contest_rating  INTEGER,
    contests_participated INTEGER DEFAULT 0,
    best_contest_rank INTEGER,
    streak_days     INTEGER DEFAULT 0,
    active_days     INTEGER DEFAULT 0,
    -- Topic-wise breakdown stored as structured JSON (genuinely variable)
    topic_stats     JSONB,  -- {"arrays": {"solved": 45, "total": 100}, ...}
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_coding_analytics_student ON coding_analytics(student_id);
```

### 3.8 Skill Gap Analysis

```sql
CREATE TABLE skill_gap_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    profile_id      UUID NOT NULL REFERENCES student_profiles(id),
    target_role     VARCHAR(100),
    target_job_id   UUID REFERENCES jobs(id),
    overall_coverage DECIMAL(5,2),  -- percentage
    status          VARCHAR(50) DEFAULT 'draft',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_skill_gaps_student ON skill_gap_reports(student_id);

CREATE TABLE skill_gap_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES skill_gap_reports(id) ON DELETE CASCADE,
    skill_id        UUID NOT NULL REFERENCES skills(id),
    required_level  VARCHAR(20) NOT NULL,
    current_level   VARCHAR(20),
    gap_severity    VARCHAR(20) CHECK (gap_severity IN ('none', 'low', 'medium', 'high', 'critical')),
    is_strength     BOOLEAN DEFAULT false,
    evidence_id     UUID,
    recommendation  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_gap_items_report ON skill_gap_items(report_id);
```

### 3.9 Readiness Scores & Matching

```sql
CREATE TABLE readiness_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    workflow_run_id UUID,  -- FK to workflow_runs
    total_score     DECIMAL(5,2) NOT NULL,
    max_score       DECIMAL(5,2) DEFAULT 100.0,
    percentile      DECIMAL(5,2),
    status          VARCHAR(50) DEFAULT 'draft' CHECK (status IN (
                        'draft', 'validated', 'pending_review', 'approved', 'published', 'rejected'
                    )),
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_readiness_student ON readiness_scores(student_id);

CREATE TABLE score_breakdowns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score_id        UUID NOT NULL REFERENCES readiness_scores(id) ON DELETE CASCADE,
    component       VARCHAR(50) NOT NULL CHECK (component IN (
                        'skill_coverage', 'coding_performance', 'project_relevance',
                        'academic', 'interview_performance', 'eligibility'
                    )),
    points          DECIMAL(5,2) NOT NULL,
    max_points      DECIMAL(5,2) NOT NULL,
    weight          DECIMAL(5,2) NOT NULL,
    weighted_score  DECIMAL(5,2) NOT NULL,
    details         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_breakdowns_score ON score_breakdowns(score_id);

CREATE TABLE company_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    score_id        UUID REFERENCES readiness_scores(id),
    job_id          UUID NOT NULL REFERENCES jobs(id),
    company_id      UUID NOT NULL REFERENCES companies(id),
    match_score     DECIMAL(5,2) NOT NULL,
    confidence      DECIMAL(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    rank            INTEGER,
    reasoning       TEXT NOT NULL,
    is_eligible     BOOLEAN DEFAULT true,
    eligibility_notes TEXT,
    is_low_confidence BOOLEAN DEFAULT false,
    evidence_id     UUID,
    status          VARCHAR(50) DEFAULT 'draft',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_matches_student ON company_matches(student_id);
CREATE INDEX idx_matches_confidence ON company_matches(is_low_confidence);

-- Configurable scoring weights
CREATE TABLE scoring_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    role_family     VARCHAR(50),
    config          JSONB NOT NULL,  -- {"skill_coverage": {"weight": 0.4, "max": 40}, ...}
    is_active       BOOLEAN DEFAULT true,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.10 Interview & Roadmap

```sql
CREATE TABLE interview_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    target_role     VARCHAR(100),
    session_type    VARCHAR(50) CHECK (session_type IN ('technical', 'behavioral', 'mixed')),
    status          VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
                        'pending', 'in_progress', 'completed', 'evaluated'
                    )),
    overall_score   DECIMAL(5,2),
    feedback_summary TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_interview_student ON interview_sessions(student_id);

CREATE TABLE interview_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_text   TEXT NOT NULL,
    question_type   VARCHAR(50) CHECK (question_type IN (
                        'technical', 'behavioral', 'situational', 'coding', 'system_design'
                    )),
    difficulty      VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    skill_targeted  UUID REFERENCES skills(id),
    sequence_order  INTEGER NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE interview_responses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id     UUID NOT NULL REFERENCES interview_questions(id) ON DELETE CASCADE,
    response_text   TEXT NOT NULL,
    score           DECIMAL(5,2),
    max_score       DECIMAL(5,2) DEFAULT 10.0,
    ai_feedback     TEXT,
    strengths       TEXT[],
    improvements    TEXT[],
    is_ai_evaluated BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE roadmaps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title           VARCHAR(255),
    target_role     VARCHAR(100),
    total_items     INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    status          VARCHAR(50) DEFAULT 'draft',
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_roadmaps_student ON roadmaps(student_id);

CREATE TABLE roadmap_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id      UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    skill_id        UUID REFERENCES skills(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    priority        VARCHAR(20) CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    category        VARCHAR(50),
    resources       JSONB,   -- [{"type": "course", "title": "...", "url": "..."}]
    estimated_hours INTEGER,
    sequence_order  INTEGER,
    is_completed    BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.11 Evidence

```sql
CREATE TABLE evidence_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50) NOT NULL,  -- 'skill_gap', 'company_match', 'recommendation', etc.
    entity_id       UUID NOT NULL,
    evidence_type   VARCHAR(50) NOT NULL CHECK (evidence_type IN (
                        'skill_source', 'benchmark_source', 'coding_metric',
                        'role_requirement', 'academic_record', 'project_evidence',
                        'interview_evidence', 'match_reasoning'
                    )),
    source          VARCHAR(255) NOT NULL,
    source_id       VARCHAR(255),
    content         TEXT NOT NULL,
    scope_tags      TEXT[],
    confidence      DECIMAL(3,2),
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_evidence_entity ON evidence_records(entity_type, entity_id);
CREATE INDEX idx_evidence_type ON evidence_records(evidence_type);
```

### 3.12 Workflow & Orchestration

```sql
CREATE TABLE workflow_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id),
    initiated_by    UUID NOT NULL REFERENCES users(id),
    status          VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
                        'pending', 'running', 'validating', 'awaiting_review',
                        'approved', 'published', 'rejected', 'failed', 'cancelled'
                    )),
    execution_plan  JSONB,  -- Locked plan
    current_step    VARCHAR(100),
    retry_count     INTEGER DEFAULT 0,
    max_retries     INTEGER DEFAULT 3,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_workflows_student ON workflow_runs(student_id);
CREATE INDEX idx_workflows_status ON workflow_runs(status);

CREATE TABLE agent_executions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    agent_name      VARCHAR(100) NOT NULL,
    status          VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
                        'pending', 'running', 'completed', 'failed', 'skipped', 'retrying'
                    )),
    input_data      JSONB,
    output_data     JSONB,
    error_message   TEXT,
    duration_ms     INTEGER,
    token_usage     JSONB,  -- {"prompt_tokens": N, "completion_tokens": M}
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_agent_exec_workflow ON agent_executions(workflow_run_id);
CREATE INDEX idx_agent_exec_agent ON agent_executions(agent_name);
```

### 3.13 Validation

```sql
CREATE TABLE validation_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    passed          BOOLEAN NOT NULL,
    total_checks    INTEGER NOT NULL,
    passed_checks   INTEGER NOT NULL,
    failed_checks   INTEGER NOT NULL,
    diagnosis       TEXT,
    attempt_number  INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_validation_workflow ON validation_reports(workflow_run_id);

CREATE TABLE validation_checks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES validation_reports(id) ON DELETE CASCADE,
    check_name      VARCHAR(100) NOT NULL,
    check_code      VARCHAR(50) NOT NULL,  -- e.g., 'SKILL_GAP_CITATION', 'ELIGIBILITY_RULE'
    passed          BOOLEAN NOT NULL,
    message         TEXT,
    severity        VARCHAR(20) CHECK (severity IN ('error', 'warning', 'info')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.14 Approval & Versioning

```sql
CREATE TABLE approval_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id UUID NOT NULL REFERENCES workflow_runs(id),
    reviewer_id     UUID NOT NULL REFERENCES users(id),
    decision        VARCHAR(20) NOT NULL CHECK (decision IN (
                        'approved', 'rejected', 'request_changes'
                    )),
    comments        TEXT,
    edits           JSONB,  -- Specific edits made by reviewer
    reviewed_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_approvals_workflow ON approval_decisions(workflow_run_id);
CREATE INDEX idx_approvals_reviewer ON approval_decisions(reviewer_id);

CREATE TABLE versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id),
    entity_type     VARCHAR(50) NOT NULL,  -- 'readiness_plan'
    version_number  INTEGER NOT NULL,
    status          VARCHAR(50) NOT NULL CHECK (status IN (
                        'draft', 'validated', 'approved', 'published', 'rolled_back'
                    )),
    snapshot        JSONB NOT NULL,  -- Full snapshot of the versioned entity
    workflow_run_id UUID REFERENCES workflow_runs(id),
    approved_by     UUID REFERENCES users(id),
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, entity_type, version_number)
);
CREATE INDEX idx_versions_student ON versions(student_id);
```

### 3.15 Audit Log

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    actor_id        UUID REFERENCES users(id),
    actor_type      VARCHAR(50) NOT NULL CHECK (actor_type IN (
                        'student', 'placement_officer', 'faculty', 'admin', 'system', 'agent'
                    )),
    workflow_run_id UUID REFERENCES workflow_runs(id),
    agent_name      VARCHAR(100),
    action          VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(100),
    entity_id       UUID,
    input_ref       TEXT,
    output_ref      TEXT,
    decision        VARCHAR(50),
    validation_result VARCHAR(50),
    approval_decision VARCHAR(50),
    version         INTEGER,
    correlation_id  UUID NOT NULL,  -- For tracing across the pipeline
    details         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_workflow ON audit_logs(workflow_run_id);
CREATE INDEX idx_audit_correlation ON audit_logs(correlation_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

### 3.16 Vector Embeddings (pgvector)

```sql
-- For similarity-based retrieval (Lab 4)
CREATE TABLE embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50) NOT NULL,
    entity_id       UUID NOT NULL,
    content_hash    VARCHAR(64),
    embedding       vector(1536),  -- OpenAI embedding dimension
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_embeddings_entity ON embeddings(entity_type, entity_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 4. Migration Strategy

- Use **Alembic** for all schema changes
- Initial migration creates all tables
- Seed script populates mock data (10+ students, 20+ companies, 30+ roles)
- Each lab may add incremental migrations as features expand

---

## 5. Key Constraints & Indexes Summary

| Constraint Type | Count | Purpose |
|----------------|-------|---------|
| Primary Keys | 30+ | Identity |
| Foreign Keys | 40+ | Referential integrity |
| Unique Constraints | 15+ | Business rules |
| Check Constraints | 20+ | Domain validation |
| Indexes | 35+ | Query performance |
| NOT NULL | Extensive | Data completeness |
