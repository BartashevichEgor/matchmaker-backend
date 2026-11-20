from tests.test_matching import make_project


def publish_profile(client, headers):
    assert (
        client.patch(
            "/api/v1/profiles/me",
            headers=headers,
            json={
                "first_name": "Grace",
                "bio": "Builds reliable software.",
                "role_id": 1,
                "visibility": "published",
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


def test_profile_favorites_are_private_idempotent_and_removable(client, account):
    _, owner, _ = account("profile-owner@example.com")
    target, target_headers, _ = account("profile-target@example.com")
    publish_profile(client, target_headers)
    path = f"/api/v1/favorites/profile/{target['id']}"

    assert client.put(path, headers=owner).status_code == 204
    assert client.put(path, headers=owner).status_code == 204
    saved = client.get("/api/v1/favorites?kind=profile", headers=owner)
    assert saved.status_code == 200
    assert [profile["user_id"] for profile in saved.json()] == [target["id"]]
    assert "birth_date" not in saved.json()[0] and "email" not in saved.json()[0]
    assert client.get("/api/v1/favorites?kind=profile", headers=target_headers).json() == []
    assert client.put(f"/api/v1/favorites/profile/{target['id']}", headers=target_headers).status_code == 404
    assert client.put("/api/v1/favorites/profile/99999", headers=owner).status_code == 404
    assert client.delete(path, headers=owner).status_code == 204
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get("/api/v1/favorites?kind=profile", headers=owner).json() == []


def test_project_favorites_only_expose_published_cards(client, account):
    _, owner, _ = account("project-favorite-owner@example.com")
    _, project_owner, _ = account("project-favorite-target@example.com")
    project = make_project(client, project_owner)
    path = f"/api/v1/favorites/project/{project['id']}"

    assert client.put(path, headers=owner).status_code == 204
    assert client.put(path, headers=owner).status_code == 204
    assert [item["id"] for item in client.get("/api/v1/favorites?kind=project", headers=owner).json()] == [
        project["id"]
    ]
    assert client.put(path, headers=project_owner).status_code == 404
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get("/api/v1/favorites?kind=project", headers=owner).json() == []
