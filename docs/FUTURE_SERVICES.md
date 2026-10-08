# Future Services & Intelligence Layer
## Career & Job Application Management Platform

**Version:** 1.0.0
**Date:** 2026-09-07

---

## 1. Overview

This document defines the extension points and design for future intelligence, automation, and data engineering capabilities. None of these are implemented in the MVP. The current architecture is designed to accommodate them without requiring major rewrites.

---

## 2. Resume Parser Service

**Trigger:** Stage 10 or later
**Implementation:** Python microservice or background task

### Purpose
Parse uploaded resume files to automatically extract structured information.

### Input
- PDF, DOC, or DOCX file from storage

### Output
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+1-555-0100",
  "summary": "...",
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "education": [
    { "institution": "MIT", "degree": "B.Sc. Computer Science", "year": 2022 }
  ],
  "experience": [
    { "company": "Acme Corp", "title": "Software Engineer", "start": "2022-07", "end": "2026-01" }
  ]
}
```

### Stack
- Python 3.12
- `pdfplumber` or `pdfminer.six` for PDF text extraction
- `python-docx` for DOCX extraction
- `spaCy` or rule-based extraction for entity recognition
- Background task (Celery or FastAPI BackgroundTasks)

### Integration Point
```python
# In resume upload service:
async def upload_resume(file, user_id):
    storage_key = await storage.put(...)
    resume = await create_resume_record(...)
    # Trigger async parsing
    background_tasks.add_task(parse_resume_async, resume.id)
    return resume
```

### Database Extension (future)
```sql
ALTER TABLE resumes ADD COLUMN parsed_data JSONB;
ALTER TABLE resumes ADD COLUMN parse_status VARCHAR(20);  -- PENDING, DONE, FAILED
```

---

## 3. Skill Extractor Service

**Trigger:** Stage 10+
**Dependency:** Resume Parser

### Purpose
Extract and normalize skills from resume text, job descriptions, and experience entries.

### Approach
1. Maintain a curated skills taxonomy (ISCO/O*NET or custom)
2. Use fuzzy matching to normalize raw skill strings to canonical names
3. Score frequency and recency weighting

### Stack
- Python
- `rapidfuzz` for fuzzy string matching
- Optional: fine-tuned NER model with spaCy

---

## 4. ML-Based Job Matching Upgrade

**Trigger:** Stage 11+
**Prerequisite:** Deterministic matching (Stage 10) already shipping

### Phase 1: Deterministic (Stage 10, in MVP roadmap)
Rule-based scoring:
```python
score = (
  skills_match_pct    * 0.40 +
  role_match_pct      * 0.20 +
  location_match_pct  * 0.15 +
  experience_match    * 0.15 +
  preferences_match   * 0.10
)
```

### Phase 2: ML-Enhanced (Future)
- Train a model on historical application outcomes (applied + result)
- Features: skills overlap, title similarity, location, experience delta, compensation delta
- Labels: OFFER_RECEIVED, REJECTED, NO_RESPONSE
- Model: Gradient Boosted Trees (scikit-learn / XGBoost)

### Explainability
Use SHAP values to explain every match score:
```json
{
  "score": 0.78,
  "shap_values": {
    "skills_overlap": +0.32,
    "title_match": +0.18,
    "missing_skills": -0.12,
    "overqualified_risk": -0.05
  }
}
```

### Stack
- Python, scikit-learn, XGBoost, SHAP
- Model serialization: `joblib`
- Served as FastAPI endpoint or background scoring job

---

## 5. Resume-Job Compatibility Checker

**Trigger:** Stage 12+

### Purpose
When a user is about to apply for a job, check how well their current default resume matches the job requirements.

### Flow
```
User opens opportunity detail
    │
    ▼
System compares resume content (parsed skills) with job requirements
    │
    ▼
Returns:
  Matching skills: Python, FastAPI, PostgreSQL ✓
  Missing skills:  Kubernetes, Terraform ✗
  Match score: 74%
  Suggestion: "Your resume doesn't mention Kubernetes — add it if you have experience"
```

### Implementation
- Deterministic phase: keyword matching between parsed resume and opportunity description
- Future: embedding-based semantic similarity

---

## 6. Application Recommendations

**Trigger:** Stage 12+

### Purpose
Recommend saved opportunities that best match the candidate's profile and preferences.

### Input
- CandidateProfile
- CandidatePreferences
- All saved/active opportunities

### Output
- Ranked list of opportunities with match scores
- Personalized feed on dashboard

### Implementation
- Phase 1: Sort saved opportunities by deterministic match score
- Phase 2: Collaborative filtering (candidates with similar profiles applied to X)

---

## 7. Interview Preparation Intelligence

**Trigger:** Stage 13+

### Purpose
Help candidates prepare for specific interviews by surfacing relevant context.

### Features (rule-based, no AI)
- Pull all notes from previous applications to the same company
- Show common question categories for the interview type (Technical, Behavioral, HR)
- Checklist auto-generation based on interview type

### Future (AI-assisted)
- Generate likely interview questions from job description
- Suggest answers based on candidate's own experience

### Stack (future AI phase)
- LLM API (OpenAI, Azure OpenAI, or open-source)
- Prompt templating with LangChain or raw API calls

---

## 8. Resume Improvement Service

**Trigger:** Stage 14+

### Purpose
Analyze a resume and suggest improvements.

### Checks (rule-based first)
- Bullet point verb strength
- Quantified achievements present?
- ATS keyword coverage vs target job
- Length/format issues

### Future (AI-assisted)
- Generate improved bullet points
- Tailor summary to specific job description

---

## 9. Analytics Data Pipeline

**Trigger:** When data volume justifies (post-Stage 10)

### Architecture

```
PostgreSQL (transactional)
    │
    ▼ Python ETL (SQLAlchemy + pandas)
    │   - Scheduled: daily or hourly
    │   - Extract changed records since last run
    │   - Transform to analytical schema
    ▼
Parquet files (Azure Blob Storage analytics container)
    │
    ▼ PySpark (only when volume justifies)
    │   - Aggregate metrics
    │   - Conversion funnels
    │   - Cohort analysis
    ▼
Analytical results back to PostgreSQL (for dashboard queries)
or
Azure Synapse / Power BI (for advanced BI)
```

### When to Introduce PySpark
PySpark is only justified when:
- Dataset exceeds ~10M rows in activity/analytics tables
- Daily full-table scans become too slow for PostgreSQL
- Multiple complex aggregations run concurrently

For MVP and early stages, PostgreSQL with indexed queries is sufficient.

### Stack
- Python 3.12
- pandas 2.x
- SQLAlchemy (read from PostgreSQL)
- pyarrow (write Parquet)
- PySpark 3.x (when scale justifies)
- Azure Data Lake Storage Gen2 (when scale justifies)

---

## 10. Future Notification Channels

### Current (MVP)
- In-app notifications only (stored in `notifications` table)

### Phase 2: Email
- Library: FastAPI-Mail or `sendgrid`
- Triggered by: background worker or Celery task
- Events: interview reminders (24h before), follow-up due, task overdue

### Phase 3: Push Notifications
- Progressive Web App (PWA) with Web Push API
- Library: `pywebpush`

### Phase 4: Mobile
- React Native or Flutter app consuming the same REST API
- FCM/APNs push notifications

---

## 11. Background Job Infrastructure

### Current (MVP)
- FastAPI `BackgroundTasks` for lightweight async operations
- No queue

### Phase 2: Task Queue
- Celery with Redis as broker
- Tasks: email sending, notification scheduling, resume parsing, analytics jobs

```python
# Future Celery task example
@celery_app.task
def send_interview_reminders():
    interviews = get_interviews_in_next_24h()
    for interview in interviews:
        create_notification(interview.user_id, type="INTERVIEW_REMINDER", ...)
        # Future: also send email
```

---

## 12. Go Services (When Justified)

Go would only be introduced for services where Python's concurrency model is a genuine bottleneck:

| Service | Justification |
|---------|--------------|
| WebSocket notification gateway | High concurrency, many simultaneous connections |
| File streaming proxy | High throughput streaming of large files |
| Real-time activity feed | Many simultaneous subscribers |

These are post-Stage 16 considerations. Do not introduce Go prematurely.

---

## 13. Summary of Deferred Features

| Feature | Reason Deferred | Intended Stage |
|---------|----------------|----------------|
| Resume parsing | Requires NLP pipeline | 10+ |
| Skill extraction | Depends on resume parsing | 10+ |
| ML matching | Requires training data | 11+ |
| Resume-job checker | Depends on parsing | 12+ |
| App recommendations | Depends on matching | 12+ |
| AI interview prep | Requires LLM integration | 13+ |
| AI resume improvement | Requires LLM integration | 14+ |
| Analytics pipeline | Justified at scale | Post-Stage 10 |
| PySpark | Justified at high volume | Post-Stage 16 |
| Celery/Redis | Justified at task volume | Stage 9+ |
| Email notifications | Requires SMTP setup | Stage 9 |
| Push notifications | Requires PWA/mobile work | Post-MVP |
| Go services | Justified at concurrency scale | Post-Stage 16 |
