from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import schemas as s
from app.api.deps import AdminUser, Db
from app.models import Role, Skill

router = APIRouter(tags=["Catalogs"])


def save_item(db, model, data, item_id=None):
    item = db.get(model, item_id) if item_id else model()
    if item is None:
        raise HTTPException(404, "Item not found")
    existing = db.scalar(select(model).where(func.lower(model.name) == data.name.lower()))
    if existing and existing.id != item_id:
        raise HTTPException(409, "Name already exists")
    item.name = data.name
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Name already exists") from None
    return item


@router.get("/skills", response_model=list[s.CatalogRead])
def skills(
    db: Db,
    q: str = Query("", max_length=80),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return list(
        db.scalars(
            select(Skill)
            .where(Skill.name.icontains(q, autoescape=True))
            .order_by(Skill.id)
            .offset(offset)
            .limit(limit)
        )
    )


@router.get("/roles", response_model=list[s.CatalogRead])
def roles(db: Db, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    return list(db.scalars(select(Role).order_by(Role.id).offset(offset).limit(limit)))


@router.post("/admin/skills", response_model=s.CatalogRead, status_code=201)
def create_skill(data: s.CatalogInput, admin: AdminUser, db: Db):
    return save_item(db, Skill, data)


@router.patch("/admin/skills/{item_id}", response_model=s.CatalogRead)
def edit_skill(item_id: int, data: s.CatalogInput, admin: AdminUser, db: Db):
    return save_item(db, Skill, data, item_id)


@router.post("/admin/roles", response_model=s.CatalogRead, status_code=201)
def create_role(data: s.CatalogInput, admin: AdminUser, db: Db):
    return save_item(db, Role, data)


@router.patch("/admin/roles/{item_id}", response_model=s.CatalogRead)
def edit_role(item_id: int, data: s.CatalogInput, admin: AdminUser, db: Db):
    return save_item(db, Role, data, item_id)
