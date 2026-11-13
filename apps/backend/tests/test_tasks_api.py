"""Tasks API: CRUD, scoping, complete, mine, notifications on assign."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.employees.models import Employee
from apps.notifications.models import Notification
from apps.tasks.models import Task


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_login(api, make_user):
    user, pwd = make_user(email="owner@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    return user


@pytest.fixture
def salesperson(make_user):
    user, pwd = make_user(email="sp@example.com", role_name="Salesperson")
    emp = Employee.objects.create(user=user, employee_code="E001",
                                  full_name="Sales Person")
    return user, pwd, emp


def test_create_task_notifies_assignee(api, owner_login, salesperson):
    _, _, emp = salesperson
    resp = api.post("/api/v1/tasks/",
                    {"title": "Call Alice", "assignee": str(emp.pk),
                     "priority": "high"}, format="json")
    assert resp.status_code == 201, resp.content
    assert Notification.objects.filter(
        recipient=emp.user, kind="task_assigned").count() == 1


def test_salesperson_sees_only_their_tasks(api, owner_login, salesperson, make_user):
    sp_user, sp_pwd, sp_emp = salesperson
    other_user, _ = make_user(email="other@example.com",
                              role_name="Salesperson")
    other_emp = Employee.objects.create(user=other_user, employee_code="E002",
                                         full_name="Other Sales")
    Task.objects.create(title="Mine", assignee=sp_emp)
    Task.objects.create(title="Theirs", assignee=other_emp)
    api.post("/api/v1/auth/logout/")
    api.post("/api/v1/auth/login/",
             {"email": sp_user.email, "password": sp_pwd}, format="json")
    resp = api.get("/api/v1/tasks/")
    titles = [t["title"] for t in resp.json()["results"]]
    assert titles == ["Mine"]


def test_complete_marks_status_and_time(api, owner_login, salesperson):
    _, _, emp = salesperson
    task = Task.objects.create(title="t", assignee=emp)
    resp = api.post(f"/api/v1/tasks/{task.pk}/complete/")
    assert resp.status_code == 200
    task.refresh_from_db()
    assert task.status == "completed"
    assert task.completed_at is not None


def test_mine_endpoint_returns_only_assignee_tasks(api, make_user, salesperson):
    sp_user, sp_pwd, sp_emp = salesperson
    Task.objects.create(title="A", assignee=sp_emp)
    api.post("/api/v1/auth/login/",
             {"email": sp_user.email, "password": sp_pwd}, format="json")
    resp = api.get("/api/v1/tasks/mine/")
    assert resp.status_code == 200
    data = resp.json()
    # paginated
    titles = [t["title"] for t in data.get("results", data)]
    assert "A" in titles


def test_overdue_sweep_emits_once(owner_login, salesperson):
    from apps.tasks.services.tasks import sweep_overdue_tasks
    _, _, emp = salesperson
    Task.objects.create(
        title="Old", assignee=emp,
        due_at=timezone.now() - timedelta(hours=2),
    )
    assert sweep_overdue_tasks() == 1
    # Second run should emit zero (dedup)
    assert sweep_overdue_tasks() == 0
