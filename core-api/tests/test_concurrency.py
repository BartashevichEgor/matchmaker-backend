from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import func, select

from app.db import engine
from app.models import Match
from tests.test_matching import make_project

pytestmark = pytest.mark.skipif(engine.dialect.name != "postgresql", reason="PostgreSQL row-lock semantics")


def test_simultaneous_likes_create_one_match(client, account, db):
    _, owner_headers, _ = account("owner@example.com")
    candidate, headers, _ = account("candidate@example.com")
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


def test_simultaneous_refresh_is_single_use(client, account):
    _, _, tokens = account()

    def refresh(_):
        return client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(refresh, range(2)))
    assert statuses == [200, 401]
