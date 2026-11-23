from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app import schemas as s
from app.api.deps import Db, VerifiedUser
from app.api.projects import accessible_project
from app.core.limits import limit
from app.models import Match, Notification, Profile, Project, ProjectMember, Swipe, User
from app.services.views import match_view, match_views

router = APIRouter(tags=["Matches"])


def record_swipe(db, project, candidate_id, actor, direction, decision):
    if project.status != "open" or project.visibility != "published":
        raise HTTPException(409, "Project is not accepting candidates")
    candidate = db.get(User, candidate_id)
    if not candidate or not candidate.is_active or not candidate.is_verified:
        raise HTTPException(404, "Candidate not found")
    if candidate_id == project.owner_id:
        raise HTTPException(422, "You cannot swipe your own project")
    profile = db.scalar(select(Profile).where(Profile.user_id == candidate_id))
    if not profile or profile.visibility != "published":
        raise HTTPException(404, "Candidate not found")
    match = db.scalar(select(Match).where(Match.project_id == project.id, Match.candidate_id == candidate_id))
    if match and decision == "pass":
        raise HTTPException(409, "A match already exists; its history is preserved")
    swipe = db.scalar(
        select(Swipe).where(
            Swipe.project_id == project.id, Swipe.candidate_id == candidate_id, Swipe.direction == direction
        )
    )
    if swipe:
        swipe.decision = decision
    else:
        db.add(
            Swipe(
                project_id=project.id,
                candidate_id=candidate_id,
                actor_id=actor.id,
                direction=direction,
                decision=decision,
            )
        )
    db.flush()
    likes = list(
        db.scalars(
            select(Swipe).where(
                Swipe.project_id == project.id, Swipe.candidate_id == candidate_id, Swipe.decision == "like"
            )
        )
    )
    if len(likes) == 2 and not match:
        match = Match(project_id=project.id, candidate_id=candidate_id)
        db.add(match)
        db.flush()
        for recipient_id in (candidate_id, project.owner_id):
            db.add(
                Notification(
                    recipient_id=recipient_id,
                    type="match_created",
                    payload={"match_id": match.id, "project_id": project.id, "project_title": project.title},
                    event_key=f"match:{match.id}:user:{recipient_id}",
                )
            )
    db.commit()
    return s.SwipeRead(decision=decision, match=match_view(db, match) if match else None)


@router.put("/projects/{project_id}/my-swipe", response_model=s.SwipeRead)
def student_swipe(project_id: int, data: s.SwipeInput, user: VerifiedUser, db: Db):
    limit(f"swipes:user:{user.id}", 120, 60)
    project = accessible_project(db, project_id, user, lock=True)
    return record_swipe(db, project, user.id, user, "student_to_project", data.decision)


@router.put("/projects/{project_id}/candidates/{candidate_id}/swipe", response_model=s.SwipeRead)
def owner_swipe(project_id: int, candidate_id: int, data: s.SwipeInput, user: VerifiedUser, db: Db):
    limit(f"swipes:user:{user.id}", 120, 60)
    # All swipes for one project share a PostgreSQL row lock: simultaneous likes
    # cannot miss one another or create duplicate matches.
    project = accessible_project(db, project_id, user, owner=True, lock=True)
    return record_swipe(db, project, candidate_id, user, "project_to_student", data.decision)


@router.get("/matches", response_model=list[s.MatchRead])
def matches(user: VerifiedUser, db: Db, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    query = (
        select(Match)
        .join(Project)
        .where(
            or_(Match.candidate_id == user.id, Project.owner_id == user.id),
            Project.status != "blocked",
        )
        .order_by(Match.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return match_views(db, list(db.scalars(query)))


def allowed_match(db, match_id, user):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(404, "Match not found")
    project = db.get(Project, match.project_id)
    if user.id not in (match.candidate_id, project.owner_id) or project.status == "blocked":
        raise HTTPException(403, "Match access denied")
    return match


@router.get("/matches/{match_id}", response_model=s.MatchRead)
def match_detail(match_id: int, user: VerifiedUser, db: Db):
    return match_view(db, allowed_match(db, match_id, user))


@router.get("/matches/{match_id}/chat-access", response_model=s.ChatAccessRead)
def chat_access(match_id: int, user: VerifiedUser, db: Db):
    return _chat_access_response(match_id, user, db)


def _chat_access_response(match_id: int, user, db):
    match = allowed_match(db, match_id, user)
    project = db.get(Project, match.project_id)
    return s.ChatAccessRead(
        **match_view(db, match).model_dump(),
        allowed=True,
        current_user_id=user.id,
        project_owner_id=project.owner_id,
        expires_at=None,
    )


@router.post("/matches/{match_id}/chat-send-access", response_model=s.ChatAccessRead)
def chat_send_access(match_id: int, user: VerifiedUser, db: Db):
    access = _chat_access_response(match_id, user, db)
    limit(f"chat-send:user:{user.id}", 60, 60)
    return access


@router.post("/matches/{match_id}/join", response_model=s.Message)
def join(match_id: int, user: VerifiedUser, db: Db):
    match = allowed_match(db, match_id, user)
    if user.id != match.candidate_id:
        raise HTTPException(403, "Only the candidate can accept membership")
    project = accessible_project(db, match.project_id, user, lock=True)
    if project.status != "open" or project.visibility != "published":
        raise HTTPException(409, "Project is not accepting members")
    if not db.get(ProjectMember, (project.id, user.id)):
        db.add(ProjectMember(project_id=project.id, user_id=user.id))
        db.flush()
        db.add(
            Notification(
                recipient_id=project.owner_id,
                type="project_joined",
                payload={"project_id": project.id, "project_title": project.title, "candidate_id": user.id},
                event_key=f"project_joined:{project.id}:user:{user.id}",
            )
        )
    db.commit()
    return s.Message(message="You joined the project.")
