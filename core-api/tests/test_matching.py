import pytest
from sqlalchemy import func, select

from app.models import Match, Notification, Project, ProjectMember, User
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


def make_project(client, headers, skill=1, **overrides):
    payload = {
        "title": "Hackathon team",
        "description": "We are building a project together.",
        "skills": [{"skill_id": skill, "weight": 5}],
        "role_ids": [1],
        "visibility": "published",
    }
    payload.update(overrides)
    result = client.post(
        "/api/v1/projects",
        headers=headers,
        json=payload,
    )
    assert result.status_code == 201, result.text
    return result.json()


def test_second_project_is_rejected(client, account):
    _, headers, _ = account("single-owner@example.com")
    make_project(client, headers)
    result = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"title": "Second project", "description": "A second project description."},
    )
    assert result.status_code == 409


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
        "/api/v1/profiles/me",
        headers=headers,
        json={"first_name": "Егор", "birth_date": "2005-01-01", "visibility": "published"},
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
    _, other_owner_headers, _ = account("other-owner@example.com")
    unrelated = make_project(client, other_owner_headers, skill=5)
    assert (
        client.patch("/api/v1/profiles/me", headers=headers, json={"visibility": "published"}).status_code
        == 200
    )
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
    assert match["project"] == {
        "id": project["id"],
        "title": project["title"],
        "owner_id": owner["id"],
        "kind": "project",
    }
    assert match["candidate"]["user_id"] == candidate["id"]
    assert match["candidate"]["display_name"] == candidate["username"]
    assert match["candidate"]["headline"] is None
    assert match["candidate"]["avatar_url"] is None
    assert "email" not in match["candidate"] and "birth_date" not in match["candidate"]
    assert (
        client.put(path, headers=owner_headers, json={"decision": "like"}).json()["match"]["id"]
        == match["id"]
    )
    assert client.put(path, headers=owner_headers, json={"decision": "pass"}).status_code == 409
    assert db.scalar(select(func.count()).select_from(Match)) == 1
    assert (
        db.scalar(select(func.count()).select_from(Notification).where(Notification.type == "match_created"))
        == 2
    )
    assert client.get(f"/api/v1/matches/{match['id']}/chat-access", headers=outsider).status_code == 403
    detail = client.get(f"/api/v1/matches/{match['id']}", headers=headers)
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data.pop("created_at")
    assert detail_data == {key: value for key, value in match.items() if key != "created_at"}
    assert client.get(f"/api/v1/matches/{match['id']}", headers=owner_headers).status_code == 200
    assert client.get(f"/api/v1/matches/{match['id']}", headers=outsider).status_code == 403
    assert client.get("/api/v1/matches/99999", headers=headers).status_code == 404
    access = client.get(f"/api/v1/matches/{match['id']}/chat-access", headers=headers)
    assert access.status_code == 200
    access_data = access.json()
    assert access_data["current_user_id"] == candidate["id"]
    assert access_data.pop("created_at")
    expected_access = match | {
        "allowed": True,
        "current_user_id": candidate["id"],
        "project_owner_id": owner["id"],
        "expires_at": None,
    }
    expected_access.pop("created_at")
    assert access_data == expected_access
    assert client.get("/api/v1/matches", headers=outsider).json() == []
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers=headers).status_code == 200
    assert client.post(f"/api/v1/matches/{match['id']}/join", headers=headers).status_code == 200
    assert db.scalar(select(func.count()).select_from(ProjectMember)) == 1
    assert all(
        p["project"]["id"] != project["id"]
        for p in client.get("/api/v1/recommendations/projects", headers=headers).json()
    )


def test_repeated_pass_is_idempotent_and_hides_project(client, account):
    _, owner_headers, _ = account("pass-owner@example.com", mode="project")
    _, candidate_headers, _ = account("pass-candidate@example.com")
    assert (
        client.patch(
            "/api/v1/profiles/me", headers=candidate_headers, json={"visibility": "published"}
        ).status_code
        == 200
    )
    project = make_project(client, owner_headers)
    path = f"/api/v1/projects/{project['id']}/my-swipe"

    first = client.put(path, headers=candidate_headers, json={"decision": "pass"})
    repeated = client.put(path, headers=candidate_headers, json={"decision": "pass"})

    assert first.status_code == repeated.status_code == 200
    assert first.json()["match"] is None and repeated.json()["match"] is None
    assert all(
        item["project"]["id"] != project["id"]
        for item in client.get("/api/v1/recommendations/projects", headers=candidate_headers).json()
    )


def test_unpublished_candidate_cannot_match(client, account):
    _, owner_headers, _ = account("private-owner@example.com", mode="project")
    candidate, _, _ = account("private-candidate@example.com")
    project = make_project(client, owner_headers)

    result = client.put(
        f"/api/v1/projects/{project['id']}/candidates/{candidate['id']}/swipe",
        headers=owner_headers,
        json={"decision": "like"},
    )

    assert result.status_code == 404


@pytest.mark.parametrize(
    ("status", "visibility"),
    [("open", "draft"), ("open", "hidden"), ("closed", "published"), ("blocked", "published")],
)
def test_owner_cannot_swipe_unavailable_project(client, account, db, status, visibility):
    _, owner_headers, _ = account(f"unavailable-owner-{status}-{visibility}@example.com", mode="project")
    candidate, _, _ = account(f"unavailable-candidate-{status}-{visibility}@example.com")
    project = make_project(client, owner_headers)
    stored_project = db.get(Project, project["id"])
    stored_project.status = status
    stored_project.visibility = visibility
    db.commit()

    result = client.put(
        f"/api/v1/projects/{project['id']}/candidates/{candidate['id']}/swipe",
        headers=owner_headers,
        json={"decision": "like"},
    )

    assert result.status_code == 409


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
    health = client.get("/health")
    assert health.status_code == 200 and health.json()["status"] == "UP"
    assert health.json()["database"] in ("sqlite", "postgresql")
    assert client.get("/api/health").json()["status"] == "UP"
    assert client.get("/").json() == {
        "service": "matchmaker-api",
        "docs": "/docs",
        "health": "/health",
    }
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "/swagger-assets/swagger-ui-bundle.js" in docs.text
    assert "/swagger-assets/favicon-32x32.png" in docs.text
    assert client.get("/swagger-assets/swagger-ui-bundle.js").status_code == 200
    assert client.get("/swagger-assets/favicon-32x32.png").status_code == 200
    spec = client.get("/openapi.json").json()
    assert "/api/v1/auth/register" in spec["paths"]
    assert "/api/v1/projects/{project_id}/my-swipe" in spec["paths"]


def test_profile_compatibility_aliases(client, account):
    _, headers, _ = account("aliases@example.com")
    updated = client.patch("/api/v1/users/me", headers=headers, json={"first_name": "Егор"})
    assert updated.status_code == 200 and updated.json()["first_name"] == "Егор"
    skills = client.put(
        "/api/v1/users/me/skills", headers=headers, json={"skills": [{"skill_id": 1, "level": 4}]}
    )
    assert skills.status_code == 200 and skills.json()["skills"] == [{"skill_id": 1, "level": 4}]
