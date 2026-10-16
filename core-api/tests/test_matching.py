import pytest
from sqlalchemy import func, select

from app.models import Match, ProjectMember, User
from app.services.scoring import cosine


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ({}, {}, 0),
        ({1: 5}, {}, 0),
        ({1: 5}, {2: 5}, 0),
        ({1: 1}, {1: 5}, 1),
        ({1: 3, 2: 4}, {1: 3, 2: 4}, 1),
        ({1: 1, 2: 1}, {1: 1}, 2**-0.5),
    ],
)
def test_cosine(left, right, expected):
    assert cosine(left, right) == pytest.approx(expected)


def make_project(client, headers, skill=1):
    result = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "title": "Hackathon team",
            "description": "We are building a project together.",
            "skills": [{"skill_id": skill, "weight": 5}],
            "role_ids": [1],
        },
    )
    assert result.status_code == 201, result.text
    return result.json()


def test_profile_validation_and_privacy(client, account):
    owner, headers, _ = account()
    _, other, _ = account("other@example.com")
    assert (
        client.patch(
            "/api/v1/profiles/me",
            headers=headers,
            json={
                "github_url": "https://github.com/" + "a" * 300,
            },
        ).status_code
        == 422
    )
    assert (
        client.patch("/api/v1/profiles/me", headers=headers, json={"birth_date": "2999-01-01"}).status_code
        == 422
    )
    assert client.patch("/api/v1/profiles/me", headers=headers, json={"role_id": 9999}).status_code == 422
    result = client.patch(
        "/api/v1/profiles/me", headers=headers, json={"first_name": "Егор", "birth_date": "2005-01-01"}
    )
    assert result.status_code == 200
    assert result.json()["first_name"] == "Егор"
    result = client.get(f"/api/v1/profiles/{owner['id']}", headers=other)
    assert result.status_code == 200
    assert "birth_date" not in result.json() and "email" not in result.json()
    assert (
        client.put(
            "/api/v1/profiles/me/skills", headers=headers, json={"skills": [{"skill_id": 1, "level": 6}]}
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/api/v1/profiles/me/skills", headers=headers, json={"skills": [{"skill_id": 999, "level": 1}]}
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/api/v1/profiles/me/skills", headers=headers, json={"skills": [{"skill_id": 1, "level": 1}] * 2}
        ).status_code
        == 422
    )


def test_recommendations_and_match_permissions(client, account, db):
    owner, owner_headers, _ = account("owner@example.com")
    candidate, headers, _ = account("candidate@example.com")
    _, outsider, _ = account("outsider@example.com")
    project = make_project(client, owner_headers)
    unrelated = make_project(client, owner_headers, skill=5)
    assert (
        client.put(
            "/api/v1/profiles/me/skills", headers=headers, json={"skills": [{"skill_id": 1, "level": 5}]}
        ).status_code
        == 200
    )
    ranked = client.get("/api/v1/recommendations/projects", headers=headers).json()
    assert ranked[0]["project"]["id"] == project["id"] and ranked[0]["score"] == 1
    assert ranked[1]["project"]["id"] == unrelated["id"] and ranked[1]["score"] == 0
    assert (
        client.get(
            f"/api/v1/projects/{project['id']}/recommendations/candidates", headers=outsider
        ).status_code
        == 403
    )
    candidates = client.get(
        f"/api/v1/projects/{project['id']}/recommendations/candidates", headers=owner_headers
    ).json()
    assert candidates[0]["profile"]["user_id"] == candidate["id"]
    first = client.put(
        f"/api/v1/projects/{project['id']}/my-swipe", headers=headers, json={"decision": "like"}
    )
    assert first.status_code == 200 and first.json()["match"] is None
    path = f"/api/v1/projects/{project['id']}/candidates/{candidate['id']}/swipe"
    assert client.put(path, headers=outsider, json={"decision": "like"}).status_code == 403
    result = client.put(path, headers=owner_headers, json={"decision": "like"})
    assert result.status_code == 200, result.text
    match = result.json()["match"]
    assert match and match["room_key"] == f"match:{match['id']}"
    assert (
        client.put(path, headers=owner_headers, json={"decision": "like"}).json()["match"]["id"]
        == match["id"]
    )
    assert db.scalar(select(func.count()).select_from(Match)) == 1
    assert client.get(f"/api/v1/matches/{match['id']}/chat-access", headers=outsider).status_code == 403
    assert client.get(f"/api/v1/matches/{match['id']}/chat-access", headers=headers).status_code == 200
    assert client.get("/api/v1/matches", headers=outsider).json() == []
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers=headers).status_code == 200
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers=headers).status_code == 200
    assert db.scalar(select(func.count()).select_from(ProjectMember)) == 1
    assert all(
        p["project"]["id"] != project["id"]
        for p in client.get("/api/v1/recommendations/projects", headers=headers).json()
    )


def test_moderation_ownership_and_filtering(client, account, db):
    user, headers, _ = account("owner@example.com")
    _, other, _ = account("other@example.com")
    project = make_project(client, headers)
    path = f"/api/v1/projects/{project['id']}"
    assert client.patch(path + "/status", headers=other, json={"status": "closed"}).status_code == 403
    assert client.put(path + "/my-swipe", headers=headers, json={"decision": "like"}).status_code == 422
    assert len(client.get("/api/v1/projects?skill_id=1&role_id=1", headers=other).json()) == 1
    assert client.get("/api/v1/projects?skill_id=5", headers=other).json() == []
    db.get(User, user["id"]).is_admin = True
    db.commit()
    assert (
        client.patch(
            f"/api/v1/admin/projects/{project['id']}/status", headers=headers, json={"status": "blocked"}
        ).status_code
        == 200
    )
    assert client.get(path, headers=other).status_code == 404
    assert client.patch(path + "/status", headers=headers, json={"status": "open"}).status_code == 403
    assert client.get("/api/v1/projects", headers=other).json() == []


def test_health_openapi_and_local_swagger(client):
    assert client.get("/ping").json() == {"message": "pong"}
    assert client.get("/health").json()["database"] in ("sqlite", "postgresql")
    assert client.get("/").status_code == 200
    docs = client.get("/docs")
    assert docs.status_code == 200 and "/swagger-assets/swagger-ui-bundle.js" in docs.text
    assert client.get("/swagger-assets/swagger-ui-bundle.js").status_code == 200
    spec = client.get("/openapi.json").json()
    assert "/api/v1/auth/register" in spec["paths"]
    assert "/api/v1/projects/{project_id}/my-swipe" in spec["paths"]
