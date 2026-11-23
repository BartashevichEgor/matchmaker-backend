from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app import schemas as s
from app.api.deps import Db, VerifiedUser
from app.core.limits import limit as enforce_limit
from app.models import Profile, Project, SavedProfile, SavedProject, User
from app.services.views import project_view, public_profile

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=list[s.PublicProfile | s.ProjectRead])
def list_favorites(
    kind: Literal["profile", "project"],
    user: VerifiedUser,
    db: Db,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    enforce_limit(f"favorites:user:{user.id}", 60, 60)
    if kind == "profile":
        rows = db.execute(
            select(Profile, User)
            .join(User, User.id == Profile.user_id)
            .join(SavedProfile, SavedProfile.target_user_id == User.id)
            .where(
                SavedProfile.user_id == user.id,
                Profile.visibility == "published",
                User.is_active.is_(True),
                User.is_verified.is_(True),
            )
            .order_by(SavedProfile.created_at.desc(), User.id)
            .offset(offset)
            .limit(limit)
        )
        return [public_profile(db, profile) for profile, _ in rows]
    rows = db.scalars(
        select(Project)
        .join(SavedProject, SavedProject.project_id == Project.id)
        .where(
            SavedProject.user_id == user.id,
            Project.visibility == "published",
            Project.status == "open",
        )
        .order_by(SavedProject.created_at.desc(), Project.id)
        .offset(offset)
        .limit(limit)
    )
    return [project_view(db, project) for project in rows]


@router.put("/{kind}/{target_id}", status_code=204)
def save_favorite(kind: Literal["profile", "project"], target_id: int, user: VerifiedUser, db: Db):
    enforce_limit(f"favorites:user:{user.id}", 60, 60)
    if target_id <= 0:
        raise HTTPException(404, "Card not found")
    if kind == "profile":
        target = db.scalar(
            select(Profile)
            .join(User)
            .where(
                User.id == target_id,
                User.id != user.id,
                User.is_active.is_(True),
                User.is_verified.is_(True),
                Profile.visibility == "published",
            )
        )
        if not target:
            raise HTTPException(404, "Profile not found")
        table, values = SavedProfile.__table__, {"user_id": user.id, "target_user_id": target_id}
    else:
        target = db.scalar(
            select(Project).where(
                Project.id == target_id,
                Project.owner_id != user.id,
                Project.status == "open",
                Project.visibility == "published",
            )
        )
        if not target:
            raise HTTPException(404, "Project not found")
        table, values = SavedProject.__table__, {"user_id": user.id, "project_id": target_id}
    insert = (
        pg_insert(table).values(**values).on_conflict_do_nothing()
        if db.bind.dialect.name == "postgresql"
        else sqlite_insert(table).values(**values).on_conflict_do_nothing()
    )
    db.execute(insert)
    db.commit()
    return Response(status_code=204)


@router.delete("/{kind}/{target_id}", status_code=204)
def remove_favorite(kind: Literal["profile", "project"], target_id: int, user: VerifiedUser, db: Db):
    enforce_limit(f"favorites:user:{user.id}", 60, 60)
    model, target_column = (
        (SavedProfile, SavedProfile.target_user_id)
        if kind == "profile"
        else (SavedProject, SavedProject.project_id)
    )
    db.execute(delete(model).where(model.user_id == user.id, target_column == target_id))
    db.commit()
    return Response(status_code=204)
