from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select, update

from app import schemas as s
from app.api.deps import Db, VerifiedUser
from app.models import Notification, now

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[s.NotificationRead])
def list_notifications(
    user: VerifiedUser,
    db: Db,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return db.scalars(
        select(Notification)
        .where(Notification.recipient_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()


@router.get("/unread-count", response_model=s.UnreadCountRead)
def unread_count(user: VerifiedUser, db: Db):
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.recipient_id == user.id, Notification.read_at.is_(None)
        )
    )
    return s.UnreadCountRead(unread_count=count or 0)


@router.patch("/{notification_id}/read", response_model=s.NotificationRead)
def mark_read(notification_id: int, user: VerifiedUser, db: Db):
    notification = db.scalar(
        select(Notification)
        .where(Notification.id == notification_id, Notification.recipient_id == user.id)
        .with_for_update()
    )
    if not notification:
        raise HTTPException(404, "Notification not found")
    if notification.read_at is None:
        notification.read_at = now()
        db.commit()
    return notification


@router.post("/read-all", response_model=s.Message)
def mark_all_read(user: VerifiedUser, db: Db):
    db.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.read_at.is_(None))
        .values(read_at=now())
    )
    db.commit()
    return s.Message(message="Notifications marked as read.")
