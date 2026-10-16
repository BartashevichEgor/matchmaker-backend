from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select

from app import schemas as s
from app.api.deps import CurrentUser, Db, VerifiedUser
from app.models import ProfileSkill, Role, Skill, User
from app.services.views import ensure_ids, profile_for, profile_view, public_profile

router = APIRouter(tags=["Profiles"])


@router.get("/users/me", response_model=s.UserRead)
def me(user: CurrentUser):
    return user


@router.get("/profiles/me", response_model=s.ProfileRead)
def my_profile(user: CurrentUser, db: Db):
    return profile_view(db, profile_for(db, user.id))


@router.patch("/profiles/me", response_model=s.ProfileRead)
def edit_profile(data: s.ProfileUpdate, user: VerifiedUser, db: Db):
    profile = profile_for(db, user.id)
    values = data.model_dump(exclude_unset=True)
    if data.role_id is not None:
        ensure_ids(db, Role, [data.role_id])
    for key, value in values.items():
        setattr(profile, key, str(value) if key == "github_url" and value else value)
    db.commit()
    return profile_view(db, profile)


@router.put("/profiles/me/skills", response_model=s.ProfileRead)
def set_skills(data: s.ProfileSkills, user: VerifiedUser, db: Db):
    profile = profile_for(db, user.id)
    ensure_ids(db, Skill, [v.skill_id for v in data.skills])
    db.execute(delete(ProfileSkill).where(ProfileSkill.profile_id == profile.id))
    db.add_all(ProfileSkill(profile_id=profile.id, **v.model_dump()) for v in data.skills)
    db.commit()
    return profile_view(db, profile)


@router.get("/profiles/{user_id}", response_model=s.PublicProfile)
def get_profile(user_id: int, user: VerifiedUser, db: Db):
    target = db.scalar(
        select(User).where(User.id == user_id, User.is_active.is_(True), User.is_verified.is_(True))
    )
    if not target:
        raise HTTPException(404, "Profile not found")
    return public_profile(db, profile_for(db, target.id))
