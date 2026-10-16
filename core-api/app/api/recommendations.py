from fastapi import APIRouter, Query
from sqlalchemy import select

from app import schemas as s
from app.api.deps import Db, VerifiedUser
from app.api.projects import accessible_project
from app.models import Profile, ProfileSkill, Project, ProjectMember, ProjectRole, ProjectSkill, Swipe, User
from app.services.scoring import cosine
from app.services.views import profile_for, project_view, public_profile

router = APIRouter(tags=["Recommendations"])


def user_vector(db, profile_id):
    return dict(
        db.execute(
            select(ProfileSkill.skill_id, ProfileSkill.level).where(ProfileSkill.profile_id == profile_id)
        ).all()
    )


def project_vector(db, project_id):
    return dict(
        db.execute(
            select(ProjectSkill.skill_id, ProjectSkill.weight).where(ProjectSkill.project_id == project_id)
        ).all()
    )


@router.get("/recommendations/projects", response_model=list[s.ProjectScore])
def recommend_projects(
    user: VerifiedUser,
    db: Db,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role_id: int | None = Query(None, gt=0),
):
    vector = user_vector(db, profile_for(db, user.id).id)
    swiped = select(Swipe.project_id).where(
        Swipe.candidate_id == user.id, Swipe.direction == "student_to_project"
    )
    memberships = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    query = select(Project).where(
        Project.status == "open",
        Project.owner_id != user.id,
        Project.id.not_in(swiped),
        Project.id.not_in(memberships),
    )
    if role_id:
        query = query.where(
            Project.id.in_(select(ProjectRole.project_id).where(ProjectRole.role_id == role_id))
        )
    ranked = []
    for project in db.scalars(query):
        requirements = project_vector(db, project.id)
        ranked.append((cosine(vector, requirements), project, sorted(vector.keys() & requirements.keys())))
    ranked.sort(key=lambda x: (-x[0], x[1].id))
    return [
        s.ProjectScore(project=project_view(db, p), score=round(score, 6), matched_skill_ids=matched)
        for score, p, matched in ranked[offset : offset + limit]
    ]


@router.get("/projects/{project_id}/recommendations/candidates", response_model=list[s.CandidateScore])
def recommend_candidates(
    project_id: int,
    user: VerifiedUser,
    db: Db,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role_id: int | None = Query(None, gt=0),
):
    accessible_project(db, project_id, user, owner=True)
    requirements = project_vector(db, project_id)
    swiped = select(Swipe.candidate_id).where(
        Swipe.project_id == project_id, Swipe.direction == "project_to_student"
    )
    members = select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
    query = (
        select(Profile)
        .join(User)
        .where(
            User.is_active.is_(True),
            User.is_verified.is_(True),
            User.id != user.id,
            User.id.not_in(swiped),
            User.id.not_in(members),
        )
    )
    if role_id:
        query = query.where(Profile.role_id == role_id)
    ranked = []
    for profile in db.scalars(query):
        vector = user_vector(db, profile.id)
        ranked.append((cosine(vector, requirements), profile, sorted(vector.keys() & requirements.keys())))
    ranked.sort(key=lambda x: (-x[0], x[1].user_id))
    return [
        s.CandidateScore(profile=public_profile(db, p), score=round(score, 6), matched_skill_ids=matched)
        for score, p, matched in ranked[offset : offset + limit]
    ]
