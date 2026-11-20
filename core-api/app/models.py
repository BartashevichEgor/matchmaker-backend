from datetime import UTC, date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

ID = BigInteger().with_variant(Integer, "sqlite")


def now():
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("onboarding_mode IN ('developer', 'project')", name="ck_user_onboarding_mode"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    onboarding_mode: Mapped[str] = mapped_column(String(20), default="developer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'published', 'hidden')", name="ck_profile_visibility"),
        CheckConstraint("work_format IN ('remote', 'hybrid', 'onsite')", name="ck_profile_work_format"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    first_name: Mapped[str] = mapped_column(String(80), default="")
    last_name: Mapped[str] = mapped_column(String(80), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    birth_date: Mapped[date | None] = mapped_column(Date)
    github_url: Mapped[str | None] = mapped_column(String(300))
    experience: Mapped[str] = mapped_column(Text, default="")
    interests: Mapped[str] = mapped_column(Text, default="")
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"))
    visibility: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    work_format: Mapped[str] = mapped_column(String(20), default="remote", server_default="remote")


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class ProfileSkill(Base):
    __tablename__ = "profile_skills"
    __table_args__ = (CheckConstraint("level BETWEEN 1 AND 5", name="ck_profile_skill_level"),)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=1)


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed', 'blocked')", name="ck_project_status"),
        CheckConstraint("visibility IN ('draft', 'published', 'hidden')", name="ck_project_visibility"),
        CheckConstraint("kind IN ('project', 'company')", name="ck_project_kind"),
        CheckConstraint("work_format IN ('remote', 'hybrid', 'onsite')", name="ck_project_work_format"),
        CheckConstraint("commitment IN ('full_time', 'part_time', 'flexible')", name="ck_project_commitment"),
        UniqueConstraint("owner_id", name="uq_project_owner"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, server_default=func.now()
    )
    visibility: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    kind: Mapped[str] = mapped_column(String(20), default="project", server_default="project")
    work_format: Mapped[str] = mapped_column(String(20), default="remote", server_default="remote")
    commitment: Mapped[str] = mapped_column(String(20), default="flexible", server_default="flexible")
    website_url: Mapped[str | None] = mapped_column(String(300))
    logo_url: Mapped[str | None] = mapped_column(String(300))


class SavedProfile(Base):
    __tablename__ = "saved_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SavedProject(Base):
    __tablename__ = "saved_projects"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ProjectSkill(Base):
    __tablename__ = "project_skills"
    __table_args__ = (CheckConstraint("weight BETWEEN 1 AND 5", name="ck_project_skill_weight"),)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)


class ProjectRole(Base):
    __tablename__ = "project_roles"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True)


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (
        UniqueConstraint("project_id", "candidate_id", "direction", name="uq_swipe_direction"),
        CheckConstraint(
            "direction IN ('student_to_project', 'project_to_student')", name="ck_swipe_direction"
        ),
        CheckConstraint("decision IN ('like', 'pass')", name="ck_swipe_decision"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    direction: Mapped[str] = mapped_column(String(30))
    decision: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("project_id", "candidate_id", name="uq_match_pair"),)
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EmailCode(Base):
    __tablename__ = "email_codes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(20), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[int] = mapped_column(BigInteger)
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[int] = mapped_column(BigInteger)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    client_ip_hash: Mapped[str | None] = mapped_column(String(64))
