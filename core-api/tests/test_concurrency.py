from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from app.db import engine
from app.models import Match, Notification, Project, ProjectMember
from tests.test_matching import make_project

pytestmark = pytest.mark.skipif(engine.dialect.name != "postgresql", reason="PostgreSQL row-lock semantics")


def test_simultaneous_project_creation_allows_only_one(client, account, db):
    user, headers, _ = account("project-race@example.com")
    barrier = Barrier(2)
    payload = {"title": "One project", "description": "Only one project per account."}

    def create(_):
        barrier.wait()
        return client.post("/api/v1/projects", headers=headers, json=payload).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(create, range(2)))
    assert statuses == [201, 409]
    assert db.scalar(select(func.count()).select_from(Project).where(Project.owner_id == user["id"])) == 1


def test_simultaneous_likes_create_one_match(client, account, db):
    _, owner_headers, _ = account("owner@example.com")
    candidate, headers, _ = account("candidate@example.com")
    assert (
        client.patch("/api/v1/profiles/me", headers=headers, json={"visibility": "published"}).status_code
        == 200
    )
    project = make_project(client, owner_headers)
    requests = [
        (f"/api/v1/projects/{project['id']}/my-swipe", headers),
        (f"/api/v1/projects/{project['id']}/candidates/{candidate['id']}/swipe", owner_headers),
    ]

    def swipe(item):
        path, auth = item
        return client.put(path, headers=auth, json={"decision": "like"})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(swipe, requests))
    assert all(r.status_code == 200 for r in responses)
    assert db.scalar(select(func.count()).select_from(Match)) == 1
    assert (
        db.scalar(select(func.count()).select_from(Notification).where(Notification.type == "match_created"))
        == 2
    )


def test_simultaneous_join_creates_one_membership_and_notification(client, account, db):
    owner, owner_headers, _ = account("join-owner@example.com", mode="project")
    candidate, candidate_headers, _ = account("join-candidate@example.com")
    assert (
        client.patch(
            "/api/v1/profiles/me", headers=candidate_headers, json={"visibility": "published"}
        ).status_code
        == 200
    )
    project = make_project(client, owner_headers)
    client.put(
        f"/api/v1/projects/{project['id']}/my-swipe",
        headers=candidate_headers,
        json={"decision": "like"},
    )
    result = client.put(
        f"/api/v1/projects/{project['id']}/candidates/{candidate['id']}/swipe",
        headers=owner_headers,
        json={"decision": "like"},
    )
    match_id = result.json()["match"]["id"]
    barrier = Barrier(2)

    def join(_):
        barrier.wait()
        return client.post(f"/api/v1/matches/{match_id}/join", headers=candidate_headers).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(join, range(2)))
    assert statuses == [200, 200]
    assert (
        db.scalar(
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project["id"], ProjectMember.user_id == candidate["id"])
        )
        == 1
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.type == "project_joined",
                Notification.recipient_id == owner["id"],
            )
        )
        == 1
    )


def test_simultaneous_refresh_is_single_use(client, account):
    _, _, tokens = account()

    def refresh(_):
        return client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(refresh, range(2)))
    assert statuses == [200, 401]
