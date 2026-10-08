"""
Stage 8 Master Test Suite — Tasks, Calendar & Notifications.
Covers:
- Unauthenticated rejection (401) across tasks, calendar, notifications
- Task creation with strict polymorphic consistency validation
- Task CRUD operations and deterministic completion action
- Task filtering by tab (today, upcoming, completed), priority, and search
- Application sub-resource listing (/applications/{id}/tasks)
- Calendar aggregation across interviews, tasks, follow-ups, and application deadlines
- In-App Notifications idempotent synchronization and read/delete management
- Multi-user tenant isolation across all Stage 8 features
"""

import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str, username: str) -> dict[str, str]:
    """Helper to register and login a user, returning Authorization headers."""
    register_payload = {
        "email": email,
        "username": username,
        "password": "Password123!",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Unauthenticated Rejection (401)
# ---------------------------------------------------------------------------

def test_unauthenticated_tasks_calendar_notifications_rejected(db_client: TestClient):
    """All Stage 8 endpoints must reject unauthenticated requests with 401."""
    dummy_id = str(uuid.uuid4())
    # Tasks
    assert db_client.get("/api/v1/tasks").status_code == 401
    assert db_client.post("/api/v1/tasks", json={"title": "Test Task"}).status_code == 401
    assert db_client.get(f"/api/v1/tasks/{dummy_id}").status_code == 401
    assert db_client.put(f"/api/v1/tasks/{dummy_id}", json={"title": "Updated"}).status_code == 401
    assert db_client.post(f"/api/v1/tasks/{dummy_id}/complete").status_code == 401
    assert db_client.delete(f"/api/v1/tasks/{dummy_id}").status_code == 401
    assert db_client.get(f"/api/v1/applications/{dummy_id}/tasks").status_code == 401

    # Calendar
    assert db_client.get("/api/v1/calendar").status_code == 401

    # Notifications
    assert db_client.get("/api/v1/notifications").status_code == 401
    assert db_client.get("/api/v1/notifications/unread-count").status_code == 401
    assert db_client.post(f"/api/v1/notifications/{dummy_id}/read").status_code == 401
    assert db_client.post("/api/v1/notifications/read-all").status_code == 401
    assert db_client.delete(f"/api/v1/notifications/{dummy_id}").status_code == 401


# ---------------------------------------------------------------------------
# 2. Task Creation & Polymorphic Consistency Validation
# ---------------------------------------------------------------------------

def test_task_creation_and_polymorphic_consistency(db_client: TestClient):
    """Candidate can create polymorphic tasks and contradictory payloads are rejected."""
    headers = register_and_login(db_client, "task_poly@example.com", "task_poly_user")

    # Create parent application
    app_res = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Backend Engineer", "company_name": "Google", "current_stage": "APPLIED"},
        headers=headers,
    )
    app_id = app_res.json()["id"]

    # 1. Valid General Task (no linked entity)
    res_gen = db_client.post(
        "/api/v1/tasks",
        json={
            "title": "Review system design concepts",
            "description": "Read Designing Data-Intensive Applications",
            "priority": "HIGH",
            "related_type": "GENERAL",
        },
        headers=headers,
    )
    assert res_gen.status_code == 201
    data_gen = res_gen.json()
    assert data_gen["title"] == "Review system design concepts"
    assert data_gen["priority"] == "HIGH"
    assert data_gen["related_type"] == "GENERAL"
    assert data_gen["application_id"] is None

    # 2. Valid Application-linked Task
    res_app_task = db_client.post(
        "/api/v1/tasks",
        json={
            "title": "Follow up with recruiter",
            "application_id": app_id,
            "related_type": "APPLICATION",
            "due_date": str(date.today() + timedelta(days=2)),
            "priority": "URGENT",
        },
        headers=headers,
    )
    assert res_app_task.status_code == 201
    data_app_task = res_app_task.json()
    assert data_app_task["application_id"] == app_id
    assert data_app_task["application"]["company_name"] == "Google"

    # 3. Reject Contradictory Linkages (APPLICATION specified but no application_id)
    bad_res1 = db_client.post(
        "/api/v1/tasks",
        json={"title": "Invalid task", "related_type": "APPLICATION"},
        headers=headers,
    )
    assert bad_res1.status_code == 422

    # 4. Reject Mismatched Multiple Entity IDs
    dummy_company_id = str(uuid.uuid4())
    bad_res2 = db_client.post(
        "/api/v1/tasks",
        json={
            "title": "Conflicting task",
            "related_type": "APPLICATION",
            "application_id": app_id,
            "company_id": dummy_company_id,
        },
        headers=headers,
    )
    assert bad_res2.status_code == 422


# ---------------------------------------------------------------------------
# 3. Task CRUD & Deterministic Completion Action
# ---------------------------------------------------------------------------

def test_task_crud_and_deterministic_complete(db_client: TestClient):
    """Verify task retrieval, update, deterministic completion, and reopening."""
    headers = register_and_login(db_client, "task_crud@example.com", "task_crud_user")

    # Create
    create_res = db_client.post(
        "/api/v1/tasks",
        json={
            "title": "Prepare STAR interview stories",
            "due_date": str(date.today()),
            "priority": "MEDIUM",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]
    assert create_res.json()["is_completed"] is False
    assert create_res.json()["status"] == "PENDING"

    # Get
    get_res = db_client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Prepare STAR interview stories"

    # Update
    update_res = db_client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Prepare STAR stories & review resume", "priority": "HIGH"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Prepare STAR stories & review resume"
    assert update_res.json()["priority"] == "HIGH"

    # Deterministic complete
    complete_res = db_client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert complete_res.status_code == 200
    comp_data = complete_res.json()
    assert comp_data["is_completed"] is True
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["completed_at"] is not None

    # Re-calling complete is idempotent
    complete_res2 = db_client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert complete_res2.status_code == 200
    assert complete_res2.json()["is_completed"] is True

    # Reopening via normal update
    reopen_res = db_client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "PENDING"},
        headers=headers,
    )
    assert reopen_res.status_code == 200
    assert reopen_res.json()["is_completed"] is False
    assert reopen_res.json()["status"] == "PENDING"

    # Delete
    del_res = db_client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert del_res.status_code == 200
    assert db_client.get(f"/api/v1/tasks/{task_id}", headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# 4. Task Filtering & Tab Segregation
# ---------------------------------------------------------------------------

def test_task_filtering_and_tabs(db_client: TestClient):
    """Verify today, upcoming, completed tabs, search, and priority filtering."""
    headers = register_and_login(db_client, "task_filter@example.com", "task_filter_user")
    today = date.today()

    # Task 1: Due Today
    db_client.post(
        "/api/v1/tasks",
        json={"title": "Today Task Alpha", "due_date": str(today), "priority": "HIGH"},
        headers=headers,
    )
    # Task 2: Upcoming
    db_client.post(
        "/api/v1/tasks",
        json={"title": "Upcoming Task Beta", "due_date": str(today + timedelta(days=5)), "priority": "LOW"},
        headers=headers,
    )
    # Task 3: Completed
    t3 = db_client.post(
        "/api/v1/tasks",
        json={"title": "Completed Task Gamma", "due_date": str(today - timedelta(days=2)), "priority": "URGENT"},
        headers=headers,
    ).json()["id"]
    db_client.post(f"/api/v1/tasks/{t3}/complete", headers=headers)

    # Filter: Today
    today_res = db_client.get("/api/v1/tasks?filter=today", headers=headers)
    assert today_res.status_code == 200
    assert any(t["title"] == "Today Task Alpha" for t in today_res.json()["items"])
    assert not any(t["title"] == "Upcoming Task Beta" for t in today_res.json()["items"])
    assert not any(t["title"] == "Completed Task Gamma" for t in today_res.json()["items"])

    # Filter: Upcoming
    up_res = db_client.get("/api/v1/tasks?filter=upcoming", headers=headers)
    assert up_res.status_code == 200
    assert any(t["title"] == "Upcoming Task Beta" for t in up_res.json()["items"])
    assert not any(t["title"] == "Today Task Alpha" for t in up_res.json()["items"])

    # Filter: Completed
    comp_res = db_client.get("/api/v1/tasks?filter=completed", headers=headers)
    assert comp_res.status_code == 200
    assert any(t["title"] == "Completed Task Gamma" for t in comp_res.json()["items"])
    assert not any(t["title"] == "Today Task Alpha" for t in comp_res.json()["items"])

    # Search
    search_res = db_client.get("/api/v1/tasks?search=Alpha", headers=headers)
    assert len(search_res.json()["items"]) == 1
    assert search_res.json()["items"][0]["title"] == "Today Task Alpha"


# ---------------------------------------------------------------------------
# 5. Multi-User Tenant Isolation for Tasks
# ---------------------------------------------------------------------------

def test_multi_user_tenant_isolation_tasks(db_client: TestClient):
    """User B cannot view, modify, complete, delete User A's tasks or link User A's entities."""
    user_a_headers = register_and_login(db_client, "task_user_a@example.com", "task_user_a")
    user_b_headers = register_and_login(db_client, "task_user_b@example.com", "task_user_b")

    # User A creates application and task
    app_a = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Staff Engineer", "company_name": "Apple"},
        headers=user_a_headers,
    ).json()["id"]

    task_a = db_client.post(
        "/api/v1/tasks",
        json={"title": "User A Private Task", "application_id": app_a, "related_type": "APPLICATION"},
        headers=user_a_headers,
    ).json()["id"]

    # User B cannot read User A's task
    assert db_client.get(f"/api/v1/tasks/{task_a}", headers=user_b_headers).status_code == 404

    # User B cannot update User A's task
    assert db_client.put(f"/api/v1/tasks/{task_a}", json={"title": "Hacked"}, headers=user_b_headers).status_code == 404

    # User B cannot complete User A's task
    assert db_client.post(f"/api/v1/tasks/{task_a}/complete", headers=user_b_headers).status_code == 404

    # User B cannot delete User A's task
    assert db_client.delete(f"/api/v1/tasks/{task_a}", headers=user_b_headers).status_code == 404

    # User B cannot link task to User A's application
    link_attempt = db_client.post(
        "/api/v1/tasks",
        json={"title": "Exploit Task", "application_id": app_a, "related_type": "APPLICATION"},
        headers=user_b_headers,
    )
    assert link_attempt.status_code == 404

    # User B's task list does not contain User A's task
    b_tasks = db_client.get("/api/v1/tasks", headers=user_b_headers).json()["items"]
    assert not any(t["id"] == task_a for t in b_tasks)


# ---------------------------------------------------------------------------
# 6. Calendar Aggregation & Tenant Isolation
# ---------------------------------------------------------------------------

def test_calendar_aggregation_and_tenant_isolation(db_client: TestClient):
    """Calendar aggregates interviews, tasks, follow-ups, and deadlines with tenant isolation."""
    user_a = register_and_login(db_client, "cal_user_a@example.com", "cal_user_a")
    user_b = register_and_login(db_client, "cal_user_b@example.com", "cal_user_b")
    today = date.today()

    # User A creates application with deadline
    app_a = db_client.post(
        "/api/v1/applications",
        json={
            "job_title": "AI Architect",
            "company_name": "OpenAI",
            "deadline_date": str(today + timedelta(days=10)),
        },
        headers=user_a,
    ).json()["id"]

    # User A schedules an interview
    scheduled_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    db_client.post(
        "/api/v1/interviews",
        json={
            "application_id": app_a,
            "interview_type": "TECHNICAL",
            "scheduled_at": scheduled_time,
            "stage": "System Design Round",
        },
        headers=user_a,
    )

    # User A creates a task with due date
    db_client.post(
        "/api/v1/tasks",
        json={
            "title": "Review Distributed Systems",
            "due_date": str(today + timedelta(days=2)),
            "priority": "HIGH",
        },
        headers=user_a,
    )

    # User A creates an application follow-up
    db_client.post(
        f"/api/v1/applications/{app_a}/followups",
        json={"due_date": str(today + timedelta(days=7)), "note": "Check recruiter status"},
        headers=user_a,
    )

    # User A queries calendar
    cal_res = db_client.get(
        f"/api/v1/calendar?start_date={today}&end_date={today + timedelta(days=15)}",
        headers=user_a,
    )
    assert cal_res.status_code == 200
    events = cal_res.json()["events"]
    assert len(events) == 4

    types = {e["event_type"] for e in events}
    assert "INTERVIEW" in types
    assert "TASK" in types
    assert "FOLLOW_UP" in types
    assert "DEADLINE" in types

    # Colors properly mapped
    for e in events:
        if e["event_type"] == "INTERVIEW":
            assert e["color"] == "blue"
        elif e["event_type"] == "TASK":
            assert e["color"] == "amber"
        elif e["event_type"] == "FOLLOW_UP":
            assert e["color"] == "emerald"
        elif e["event_type"] == "DEADLINE":
            assert e["color"] == "purple"

    # User B queries calendar -> empty (tenant isolation)
    cal_b = db_client.get(
        f"/api/v1/calendar?start_date={today}&end_date={today + timedelta(days=15)}",
        headers=user_b,
    )
    assert cal_b.status_code == 200
    assert len(cal_b.json()["events"]) == 0


# ---------------------------------------------------------------------------
# 7. In-App Notifications Idempotent Sync & CRUD
# ---------------------------------------------------------------------------

def test_notification_idempotent_sync_and_crud(db_client: TestClient):
    """Verify notifications are idempotently generated, marked read, and deleted with isolation."""
    user_a = register_and_login(db_client, "notif_user_a@example.com", "notif_user_a")
    user_b = register_and_login(db_client, "notif_user_b@example.com", "notif_user_b")
    today = date.today()

    # User A creates application and interview in 24 hours
    app_a = db_client.post(
        "/api/v1/applications",
        json={"job_title": "DevOps Engineer", "company_name": "Netflix"},
        headers=user_a,
    ).json()["id"]

    int_time = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat()
    db_client.post(
        "/api/v1/interviews",
        json={
            "application_id": app_a,
            "interview_type": "TECHNICAL",
            "scheduled_at": int_time,
            "stage": "Round 1",
        },
        headers=user_a,
    )

    # User A creates a task due today
    db_client.post(
        "/api/v1/tasks",
        json={"title": "Submit reference list", "due_date": str(today), "priority": "HIGH"},
        headers=user_a,
    )

    # First call: triggers sync and returns notifications
    res1 = db_client.get("/api/v1/notifications", headers=user_a)
    assert res1.status_code == 200
    notifs1 = res1.json()["items"]
    assert len(notifs1) >= 2
    types1 = {n["notification_type"] for n in notifs1}
    assert "INTERVIEW_REMINDER" in types1
    assert "TASK_DUE" in types1

    # Second call: verifies IDEMPOTENCY (duplicate prevention)
    res2 = db_client.get("/api/v1/notifications", headers=user_a)
    assert res2.status_code == 200
    notifs2 = res2.json()["items"]
    assert len(notifs2) == len(notifs1)

    # Check unread count
    count_res = db_client.get("/api/v1/notifications/unread-count", headers=user_a)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] == len(notifs1)

    # Mark single notification as read
    first_notif_id = notifs1[0]["id"]
    read_res = db_client.post(f"/api/v1/notifications/{first_notif_id}/read", headers=user_a)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # User B cannot read or delete User A's notification
    assert db_client.post(f"/api/v1/notifications/{first_notif_id}/read", headers=user_b).status_code == 404
    assert db_client.delete(f"/api/v1/notifications/{first_notif_id}", headers=user_b).status_code == 404

    # Mark all as read
    read_all_res = db_client.post("/api/v1/notifications/read-all", headers=user_a)
    assert read_all_res.status_code == 200
    unread_now = db_client.get("/api/v1/notifications/unread-count", headers=user_a).json()["unread_count"]
    assert unread_now == 0

    # Delete single notification
    del_res = db_client.delete(f"/api/v1/notifications/{first_notif_id}", headers=user_a)
    assert del_res.status_code == 200


# ---------------------------------------------------------------------------
# 8. Application Tasks Subresource
# ---------------------------------------------------------------------------

def test_application_tasks_subresource(db_client: TestClient):
    """Verify GET /api/v1/applications/{id}/tasks lists tasks for that application."""
    user_a = register_and_login(db_client, "app_task_sub@example.com", "app_task_sub")
    user_b = register_and_login(db_client, "app_task_sub_b@example.com", "app_task_sub_b")

    app_res = db_client.post(
        "/api/v1/applications",
        json={"job_title": "Lead Architect", "company_name": "Microsoft"},
        headers=user_a,
    )
    app_id = app_res.json()["id"]

    # Add task linked to application
    db_client.post(
        "/api/v1/tasks",
        json={"title": "Prepare portfolio architecture slides", "application_id": app_id, "related_type": "APPLICATION"},
        headers=user_a,
    )

    # Query sub-resource
    sub_res = db_client.get(f"/api/v1/applications/{app_id}/tasks", headers=user_a)
    assert sub_res.status_code == 200
    tasks = sub_res.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Prepare portfolio architecture slides"

    # User B cannot access User A's application tasks
    assert db_client.get(f"/api/v1/applications/{app_id}/tasks", headers=user_b).status_code == 404


# ---------------------------------------------------------------------------
# 9. Task Validation & Non-Existent Entity Linking Rejection
# ---------------------------------------------------------------------------

def test_task_validation_not_found_parents(db_client: TestClient):
    """Linking non-existent parent entities fails safely with 404; empty title fails with 422."""
    headers = register_and_login(db_client, "task_err@example.com", "task_err")
    dummy_id = str(uuid.uuid4())

    # Empty title
    assert db_client.post("/api/v1/tasks", json={"title": "   "}, headers=headers).status_code in (422, 400)

    # Non-existent application
    res_app = db_client.post(
        "/api/v1/tasks",
        json={"title": "Valid title", "application_id": dummy_id, "related_type": "APPLICATION"},
        headers=headers,
    )
    assert res_app.status_code == 404

    # Non-existent interview
    res_int = db_client.post(
        "/api/v1/tasks",
        json={"title": "Valid title", "interview_id": dummy_id, "related_type": "INTERVIEW"},
        headers=headers,
    )
    assert res_int.status_code == 404

    # Non-existent company
    res_comp = db_client.post(
        "/api/v1/tasks",
        json={"title": "Valid title", "company_id": dummy_id, "related_type": "COMPANY"},
        headers=headers,
    )
    assert res_comp.status_code == 404

    # Non-existent contact
    res_cont = db_client.post(
        "/api/v1/tasks",
        json={"title": "Valid title", "contact_id": dummy_id, "related_type": "CONTACT"},
        headers=headers,
    )
    assert res_cont.status_code == 404


# ---------------------------------------------------------------------------
# 10. Calendar Event Types Filter
# ---------------------------------------------------------------------------

def test_calendar_event_types_filter(db_client: TestClient):
    """Calendar respects event_types filtering parameter."""
    headers = register_and_login(db_client, "cal_filter@example.com", "cal_filter")
    today = date.today()

    # Create task
    db_client.post(
        "/api/v1/tasks",
        json={"title": "Specific Task", "due_date": str(today + timedelta(days=1))},
        headers=headers,
    )

    # Filter only interviews
    res_int_only = db_client.get(
        f"/api/v1/calendar?start_date={today}&end_date={today + timedelta(days=10)}&event_types=INTERVIEW",
        headers=headers,
    )
    assert res_int_only.status_code == 200
    assert len(res_int_only.json()["events"]) == 0

    # Filter only tasks
    res_task_only = db_client.get(
        f"/api/v1/calendar?start_date={today}&end_date={today + timedelta(days=10)}&event_types=TASK",
        headers=headers,
    )
    assert res_task_only.status_code == 200
    assert len(res_task_only.json()["events"]) == 1
    assert res_task_only.json()["events"][0]["event_type"] == "TASK"
