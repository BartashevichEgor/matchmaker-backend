from fastapi import HTTPException
from sqlalchemy import select

from app import schemas as s
from app.models import Profile, ProfileSkill, ProjectRole, ProjectSkill, User


def profile_for(db, user_id):
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


def profile_view(db, profile):
    values = {c.name: getattr(profile, c.name) for c in Profile.__table__.columns}
    user = db.get(User, profile.user_id)
    if not user:
        raise HTTPException(404, "Profile not found")
    values["username"] = user.username
    values["skills"] = [
        s.SkillLevel(skill_id=p.skill_id, level=p.level)
        for p in db.scalars(
            select(ProfileSkill).where(ProfileSkill.profile_id == profile.id).order_by(ProfileSkill.skill_id)
        )
    ]
    return s.ProfileRead(**values)


def public_profile(db, profile):
    return s.PublicProfile(**profile_view(db, profile).model_dump(exclude={"id", "birth_date"}))


def project_view(db, project):
    return s.ProjectRead(
        id=project.id,
        owner_id=project.owner_id,
        title=project.title,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        skills=[
            s.SkillWeight(skill_id=p.skill_id, weight=p.weight)
            for p in db.scalars(
                select(ProjectSkill)
                .where(ProjectSkill.project_id == project.id)
                .order_by(ProjectSkill.skill_id)
            )
        ],
        role_ids=list(db.scalars(select(ProjectRole.role_id).where(ProjectRole.project_id == project.id))),
    )


def match_view(match):
    return s.MatchRead(
        id=match.id,
        project_id=match.project_id,
        candidate_id=match.candidate_id,
        created_at=match.created_at,
        room_key=f"match:{match.id}",
    )


def ensure_ids(db, model, ids):
    if ids and len(list(db.scalars(select(model.id).where(model.id.in_(ids))))) != len(set(ids)):
        raise HTTPException(422, f"Unknown {model.__tablename__} ID")
