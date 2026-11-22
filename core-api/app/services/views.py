from fastapi import HTTPException
from sqlalchemy import select

from app import schemas as s
from app.models import Match, Profile, ProfileSkill, Project, ProjectRole, ProjectSkill, Role, User


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
        kind=project.kind,
        work_format=project.work_format,
        commitment=project.commitment,
        website_url=project.website_url,
        logo_url=project.logo_url,
        visibility=project.visibility,
        updated_at=project.updated_at,
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


def match_views(db, matches):
    if not matches:
        return []
    rows = db.execute(
        select(Match, Project, Profile, User, Role)
        .join(Project, Project.id == Match.project_id)
        .join(User, User.id == Match.candidate_id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .outerjoin(Role, Role.id == Profile.role_id)
        .where(Match.id.in_([match.id for match in matches]))
    ).all()
    views = {}
    for match, project, profile, user, role in rows:
        display_name = (
            " ".join(
                value
                for value in (profile.first_name if profile else "", profile.last_name if profile else "")
                if value
            ).strip()
            or user.username
        )
        views[match.id] = s.MatchRead(
            id=match.id,
            project_id=project.id,
            candidate_id=user.id,
            created_at=match.created_at,
            room_key=f"match:{match.id}",
            project=s.MatchProjectSummary(
                id=project.id,
                title=project.title,
                owner_id=project.owner_id,
                kind=project.kind,
            ),
            candidate=s.MatchCandidateSummary(
                user_id=user.id,
                display_name=display_name,
                headline=role.name if role else None,
                avatar_url=None,
            ),
        )
    if len(views) != len(matches):
        raise HTTPException(404, "Match not found")
    return [views[match.id] for match in matches]


def match_view(db, match):
    return match_views(db, [match])[0]


def ensure_ids(db, model, ids):
    if ids and len(list(db.scalars(select(model.id).where(model.id.in_(ids))))) != len(set(ids)):
        raise HTTPException(422, f"Unknown {model.__tablename__} ID")
