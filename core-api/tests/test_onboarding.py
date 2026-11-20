from tests.test_matching import make_project


def test_developer_onboarding_moves_to_main_after_profile_is_complete(client, account):
    _, headers, _ = account()

    assert client.get("/api/v1/onboarding", headers=headers).json() == {
        "mode": "developer",
        "profile": {"exists": True, "complete": False, "visibility": "draft", "status": None},
        "project": {"exists": False, "complete": False, "visibility": None, "status": None},
        "next_setup": "profile",
        "can_create_project": True,
    }
    assert (
        client.patch(
            "/api/v1/profiles/me",
            headers=headers,
            json={"first_name": "Ada", "bio": "Builds useful software.", "role_id": 1},
        ).status_code
        == 200
    )
    assert (
        client.put(
            "/api/v1/profiles/me/skills", headers=headers, json={"skills": [{"skill_id": 1, "level": 4}]}
        ).status_code
        == 200
    )

    state = client.get("/api/v1/onboarding", headers=headers)
    assert state.status_code == 200
    assert state.json()["profile"]["complete"] is True
    assert state.json()["next_setup"] == "none"
    assert state.json()["can_create_project"] is True
    assert (
        client.post(
            "/api/v1/projects",
            headers=headers,
            json={"title": "Optional project", "description": "An optional project card."},
        ).status_code
        == 201
    )
    state = client.get("/api/v1/onboarding", headers=headers).json()
    assert state["next_setup"] == "none"
    assert state["can_create_project"] is False


def test_project_onboarding_and_authentication(client, account):
    _, headers, _ = account("project-owner@example.com", mode="project")
    assert client.get("/api/v1/onboarding").status_code == 401
    assert client.get("/api/v1/onboarding", headers=headers).json()["next_setup"] == "project"

    make_project(client, headers)
    state = client.get("/api/v1/onboarding", headers=headers).json()
    assert state["mode"] == "project"
    assert state["project"]["complete"] is True
    assert state["next_setup"] == "none"
    assert state["can_create_project"] is False
