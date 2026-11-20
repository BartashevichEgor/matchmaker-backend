from fastapi import APIRouter
from sqlalchemy import select

from app import schemas as s
from app.api.deps import Db, VerifiedUser
from app.models import Profile, ProfileSkill, Project, ProjectRole, ProjectSkill

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("", response_model=s.OnboardingRead)
def onboarding(user: VerifiedUser, db: Db):
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    profile_complete = bool(
        profile
        and profile.first_name.strip()
        and profile.bio.strip()
        and profile.role_id
        and db.scalar(select(ProfileSkill.skill_id).where(ProfileSkill.profile_id == profile.id).limit(1))
    )
    project_complete = bool(
        project
        and project.title.strip()
        and project.description.strip()
        and (
            db.scalar(select(ProjectSkill.skill_id).where(ProjectSkill.project_id == project.id).limit(1))
            or db.scalar(select(ProjectRole.role_id).where(ProjectRole.project_id == project.id).limit(1))
        )
    )
    initial_complete = project_complete if user.onboarding_mode == "project" else profile_complete
    return s.OnboardingRead(
        mode=user.onboarding_mode,
        profile=s.CardStatus(
            exists=profile is not None,
            complete=profile_complete,
            visibility=profile.visibility if profile else None,
        ),
        project=s.CardStatus(
            exists=project is not None,
            complete=project_complete,
            visibility=project.visibility if project else None,
            status=project.status if project else None,
        ),
        next_setup="none"
        if initial_complete
        else ("profile" if user.onboarding_mode == "developer" else "project"),
        can_create_project=project is None,
    )
