from datetime import UTC, datetime

from sqlalchemy import func, select

from app.models import Match, Notification
from tests.test_matching import make_project


def make_match(client, account):
    owner, owner_headers, _ = account("notify-owner@example.com", mode="project")
    candidate, candidate_headers, _ = account("notify-candidate@example.com", mode="developer")
    assert (
        client.patch(
            "/api/v1/profiles/me", headers=candidate_headers, json={"visibility": "published"}
        ).status_code
        == 200
    )
    project = make_project(client, owner_headers)
    first = client.put(
        f"/api/v1/projects/{project['id']}/my-swipe",
        headers=candidate_headers,
        json={"decision": "like"},
    )
    assert first.status_code == 200 and first.json()["match"] is None
    assert client.get("/api/v1/notifications", headers=candidate_headers).json() == []
    assert client.get("/api/v1/notifications", headers=owner_headers).json() == []
    result = client.put(
        f"/api/v1/projects/{project['id']}/candidates/{candidate['id']}/swipe",
        headers=owner_headers,
        json={"decision": "like"},
    )
    assert result.status_code == 200, result.text
    return owner, owner_headers, candidate, candidate_headers, result.json()["match"]


def test_match_notifications_are_private_and_read_state_is_scoped(client, account, db):
    owner, owner_headers, candidate, candidate_headers, match = make_match(client, account)
    _, outsider_headers, _ = account("notify-outsider@example.com")

    owner_items = client.get("/api/v1/notifications", headers=owner_headers).json()
    candidate_items = client.get("/api/v1/notifications", headers=candidate_headers).json()
    assert len(owner_items) == len(candidate_items) == 1
    assert owner_items[0]["type"] == candidate_items[0]["type"] == "match_created"
    assert owner_items[0]["payload"]["match_id"] == match["id"]
    assert client.get("/api/v1/notifications", headers=outsider_headers).json() == []
    assert client.get("/api/v1/notifications/unread-count", headers=owner_headers).json() == {
        "unread_count": 1
    }

    foreign_read = client.patch(
        f"/api/v1/notifications/{owner_items[0]['id']}/read", headers=candidate_headers
    )
    assert foreign_read.status_code == 404
    assert db.scalar(select(Notification.read_at).where(Notification.id == owner_items[0]["id"])) is None

    read = client.patch(f"/api/v1/notifications/{candidate_items[0]['id']}/read", headers=candidate_headers)
    assert read.status_code == 200 and read.json()["read_at"] is not None
    assert client.get("/api/v1/notifications/unread-count", headers=candidate_headers).json() == {
        "unread_count": 0
    }
    assert client.post("/api/v1/notifications/read-all", headers=owner_headers).status_code == 200
    assert client.get("/api/v1/notifications/unread-count", headers=owner_headers).json() == {
        "unread_count": 0
    }
    assert db.scalar(select(func.count()).select_from(Match)) == 1


def test_join_notifies_only_project_owner_once(client, account, db):
    owner, owner_headers, candidate, candidate_headers, match = make_match(client, account)
    join_path = f"/api/v1/matches/{match['id']}/join"

    assert client.post(join_path, headers=candidate_headers).status_code == 200
    assert client.post(join_path, headers=candidate_headers).status_code == 200

    owner_items = client.get("/api/v1/notifications", headers=owner_headers).json()
    candidate_items = client.get("/api/v1/notifications", headers=candidate_headers).json()
    joined = [item for item in owner_items if item["type"] == "project_joined"]
    assert len(joined) == 1
    assert joined[0]["payload"]["project_id"] == match["project_id"]
    assert all(item["type"] != "project_joined" for item in candidate_items)
    assert (
        db.scalar(select(func.count()).select_from(Notification).where(Notification.type == "project_joined"))
        == 1
    )


def test_notification_list_paginates_newest_first(client, account, db):
    user, headers, _ = account("notify-page@example.com")
    db.add_all(
        [
            Notification(
                recipient_id=user["id"],
                type="match_created",
                payload={"match_id": match_id, "project_id": 1, "project_title": "Project"},
                event_key=f"page:{match_id}",
                created_at=datetime(2026, 11, 22, hour=match_id, tzinfo=UTC),
            )
            for match_id in (1, 2, 3)
        ]
    )
    db.commit()

    first_page = client.get("/api/v1/notifications?limit=2", headers=headers)
    second_page = client.get("/api/v1/notifications?offset=2&limit=2", headers=headers)

    assert [item["payload"]["match_id"] for item in first_page.json()] == [3, 2]
    assert [item["payload"]["match_id"] for item in second_page.json()] == [1]
