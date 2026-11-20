from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import delete, select

from app import schemas as s
from app.api.deps import CurrentUser, Db, VerifiedUser
from app.models import Profile, ProfileSkill, Role, Skill, User
from app.services.views import ensure_ids, profile_for, profile_view, public_profile

router = APIRouter(tags=["Profiles"])


@router.get("/profiles", response_model=list[s.PublicProfile])
def list_profiles(
    user: VerifiedUser,
    db: Db,
    q: str = Query("", max_length=80),
    role_id: int | None = Query(None, gt=0),
    skill_id: int | None = Query(None, gt=0),
    work_format: str | None = Query(None, pattern="^(remote|hybrid|onsite)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = (
        select(Profile)
        .join(User)
        .where(
            User.id != user.id,
            User.is_active.is_(True),
            User.is_verified.is_(True),
            Profile.visibility == "published",
        )
    )
    if q:
        query = query.where(User.username.icontains(q, autoescape=True))
    if role_id:
        query = query.where(Profile.role_id == role_id)
    if skill_id:
        query = query.where(
            Profile.id.in_(select(ProfileSkill.profile_id).where(ProfileSkill.skill_id == skill_id))
        )
    if work_format:
        query = query.where(Profile.work_format == work_format)
    profiles = db.scalars(query.order_by(User.id.asc()).offset(offset).limit(limit))
    return [public_profile(db, profile) for profile in profiles]


@router.get("/users/me", response_model=s.UserRead)
def me(user: CurrentUser):
    return user


@router.get("/profiles/me", response_model=s.ProfileRead)
def my_profile(user: CurrentUser, db: Db):
    return profile_view(db, profile_for(db, user.id))


@router.patch("/profiles/me", response_model=s.ProfileRead)
@router.patch("/users/me", response_model=s.ProfileRead, include_in_schema=False)
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
@router.put("/users/me/skills", response_model=s.ProfileRead, include_in_schema=False)
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
    profile = profile_for(db, target.id)
    if profile.visibility != "published":
        raise HTTPException(404, "Profile not found")
    return public_profile(db, profile)
