from tests.test_matching import make_project


def publish_profile(client, headers, first_name):
    assert (
        client.patch(
            "/api/v1/profiles/me",
            headers=headers,
            json={
                "first_name": first_name,
                "bio": "Builds software for teams.",
                "role_id": 1,
                "visibility": "published",
                "work_format": "remote",
            },
        ).status_code
        == 200
    )
    assert (
        client.put(
            "/api/v1/profiles/me/skills", headers=headers, json={"skills": [{"skill_id": 1, "level": 5}]}
        ).status_code
        == 200
    )


def test_catalogs_filter_paginate_and_hide_unpublished_cards(client, account):
    viewer, headers, _ = account("catalog-viewer@example.com")
    profile_user, profile_headers, _ = account("published-profile@example.com")
    hidden_user, hidden_headers, _ = account("hidden-profile@example.com")
    publish_profile(client, profile_headers, "Public")
    assert (
        client.patch("/api/v1/profiles/me", headers=hidden_headers, json={"visibility": "hidden"}).status_code
        == 200
    )

    visible_profiles = client.get("/api/v1/profiles?skill_id=1&role_id=1", headers=headers)
    assert visible_profiles.status_code == 200
    assert [profile["user_id"] for profile in visible_profiles.json()] == [profile_user["id"]]
    searched_profiles = client.get("/api/v1/profiles?q=published-profile&work_format=remote", headers=headers)
    assert [profile["user_id"] for profile in searched_profiles.json()] == [profile_user["id"]]
    assert client.get("/api/v1/profiles?work_format=hybrid", headers=headers).json() == []
    assert client.get(f"/api/v1/profiles/{hidden_user['id']}", headers=headers).status_code == 404
    assert "birth_date" not in visible_profiles.json()[0]
    assert "email" not in visible_profiles.json()[0]

    _, first_owner, _ = account("first-project@example.com")
    _, second_owner, _ = account("second-project@example.com")
    _, draft_owner, _ = account("draft-project@example.com")
    first = make_project(
        client,
        first_owner,
        kind="company",
        title="Alpha Hiring",
        work_format="hybrid",
        role_ids=[1],
    )
    second = make_project(
        client, second_owner, skill=5, kind="project", title="Beta Studio", work_format="remote", role_ids=[2]
    )
    draft = make_project(client, draft_owner, visibility="draft", title="Private Draft")

    all_public = client.get("/api/v1/projects?limit=1", headers=headers).json()
    assert len(all_public) == 1 and all_public[0]["id"] == second["id"]
    filtered = client.get("/api/v1/projects?kind=company&work_format=hybrid", headers=headers).json()
    assert [item["id"] for item in filtered] == [first["id"]]
    assert [item["id"] for item in client.get("/api/v1/projects?q=Alpha", headers=headers).json()] == [
        first["id"]
    ]
    assert [item["id"] for item in client.get("/api/v1/projects?skill_id=5", headers=headers).json()] == [
        second["id"]
    ]
    assert [item["id"] for item in client.get("/api/v1/projects?role_id=2", headers=headers).json()] == [
        second["id"]
    ]
    assert all(item["id"] != draft["id"] for item in client.get("/api/v1/projects", headers=headers).json())
    assert client.get("/api/v1/projects/mine", headers=draft_owner).json()["id"] == draft["id"]
    assert [item["id"] for item in client.get("/api/v1/projects?mine=true", headers=draft_owner).json()] == [
        draft["id"]
    ]
    assert client.get("/api/v1/projects?offset=1&limit=1", headers=headers).json()[0]["id"] == first["id"]
    assert viewer["id"] not in {profile_user["id"], hidden_user["id"]}


def test_project_urls_can_be_updated_and_are_bounded(client, account):
    _, headers, _ = account("project-url-owner@example.com")
    project = make_project(client, headers)
    payload = {
        "title": project["title"],
        "description": project["description"],
        "skills": project["skills"],
        "role_ids": project["role_ids"],
        "visibility": "published",
        "website_url": "https://example.com/project",
        "logo_url": "https://example.com/logo.png",
    }
    updated = client.put(f"/api/v1/projects/{project['id']}", headers=headers, json=payload)
    assert updated.status_code == 200, updated.text
    assert updated.json()["website_url"] == "https://example.com/project"
    assert updated.json()["logo_url"] == "https://example.com/logo.png"

    prefix = "https://example.com/"
    oversized = prefix + "a" * (301 - len(prefix))
    _, other_headers, _ = account("other-url-owner@example.com")
    for field in ("website_url", "logo_url"):
        invalid = {**payload, field: oversized}
        assert client.post("/api/v1/projects", headers=other_headers, json=invalid).status_code == 422
