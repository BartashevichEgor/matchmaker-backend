from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app import schemas as s
from app.api.deps import AdminUser, Db, VerifiedUser
from app.models import Project, ProjectRole, ProjectSkill, Role, Skill
from app.services.views import ensure_ids, project_view

router = APIRouter(tags=["Projects"])


def accessible_project(db, project_id, user, owner=False, lock=False):
    query = select(Project).where(Project.id == project_id)
    project = db.scalar(query.with_for_update() if lock else query)
    if not project or (
        (project.status == "blocked" or project.visibility != "published")
        and not user.is_admin
        and project.owner_id != user.id
    ):
        raise HTTPException(404, "Project not found")
    if owner and project.owner_id != user.id:
        raise HTTPException(403, "Only the project owner can perform this action")
    return project


def save_requirements(db, project, data):
    ensure_ids(db, Skill, [s.skill_id for s in data.skills])
    ensure_ids(db, Role, data.role_ids)
    db.execute(delete(ProjectSkill).where(ProjectSkill.project_id == project.id))
    db.execute(delete(ProjectRole).where(ProjectRole.project_id == project.id))
    db.add_all(ProjectSkill(project_id=project.id, **s.model_dump()) for s in data.skills)
    db.add_all(ProjectRole(project_id=project.id, role_id=r) for r in data.role_ids)


@router.get("/projects", response_model=list[s.ProjectRead])
def list_projects(
    user: VerifiedUser,
    db: Db,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    mine: bool = False,
    skill_id: int | None = Query(None, gt=0),
    role_id: int | None = Query(None, gt=0),
    work_format: str | None = Query(None, pattern="^(remote|hybrid|onsite)$"),
    kind: str | None = Query(None, pattern="^(project|company)$"),
    q: str = Query("", max_length=100),
):
    query = select(Project)
    query = (
        query.where(Project.owner_id == user.id)
        if mine
        else query.where(Project.visibility == "published", Project.status == "open")
    )
    if skill_id:
        query = query.where(
            Project.id.in_(select(ProjectSkill.project_id).where(ProjectSkill.skill_id == skill_id))
        )
    if role_id:
        query = query.where(
            Project.id.in_(select(ProjectRole.project_id).where(ProjectRole.role_id == role_id))
        )
    if work_format:
        query = query.where(Project.work_format == work_format)
    if kind:
        query = query.where(Project.kind == kind)
    if q:
        query = query.where(Project.title.icontains(q, autoescape=True))
    return [
        project_view(db, p)
        for p in db.scalars(
            query.order_by(Project.updated_at.desc(), Project.id.desc()).offset(offset).limit(limit)
        )
    ]


@router.get("/projects/mine", response_model=s.ProjectRead | None)
def my_project(user: VerifiedUser, db: Db):
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    return project_view(db, project) if project else None


@router.post("/projects", response_model=s.ProjectRead, status_code=201)
def create_project(data: s.ProjectInput, user: VerifiedUser, db: Db):
    fields = data.model_dump(exclude={"skills", "role_ids"})
    fields = {
        key: str(value) if key in {"website_url", "logo_url"} and value else value
        for key, value in fields.items()
    }
    project = Project(owner_id=user.id, **fields)
    db.add(project)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(Project.id).where(Project.owner_id == user.id)):
            raise HTTPException(409, "A project already exists for this account") from None
        raise
    save_requirements(db, project, data)
    db.commit()
    return project_view(db, project)


@router.get("/projects/{project_id}", response_model=s.ProjectRead)
def get_project(project_id: int, user: VerifiedUser, db: Db):
    return project_view(db, accessible_project(db, project_id, user))


@router.put("/projects/{project_id}", response_model=s.ProjectRead)
def edit_project(project_id: int, data: s.ProjectInput, user: VerifiedUser, db: Db):
    project = accessible_project(db, project_id, user, owner=True, lock=True)
    if project.status == "blocked":
        raise HTTPException(403, "Blocked projects cannot be edited")
    for key, value in data.model_dump(exclude={"skills", "role_ids"}).items():
        setattr(project, key, str(value) if key in {"website_url", "logo_url"} and value else value)
    save_requirements(db, project, data)
    db.commit()
    return project_view(db, project)


@router.patch("/projects/{project_id}/status", response_model=s.ProjectRead)
def project_status(project_id: int, data: s.StatusInput, user: VerifiedUser, db: Db):
    project = accessible_project(db, project_id, user, owner=True, lock=True)
    if project.status == "blocked":
        raise HTTPException(403, "Only an administrator can unblock a project")
    project.status = data.status
    db.commit()
    return project_view(db, project)


@router.patch("/admin/projects/{project_id}/status", response_model=s.ProjectRead)
def moderate(project_id: int, data: s.ModerationInput, admin: AdminUser, db: Db):
    project = accessible_project(db, project_id, admin, lock=True)
    project.status = data.status
    db.commit()
    return project_view(db, project)
