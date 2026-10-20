from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EmailInput(Input):
    email: EmailStr = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value):
        return str(value).lower()


# The React client validates an eight-character minimum.  Keep this server-side
# rule identical so a value accepted by the form is not rejected by the API.
Password = Annotated[str, Field(min_length=8, max_length=128)]


class UsernameInput(Input):
    """A public name shown in the profile and catalogue UI."""

    username: str = Field(min_length=1, max_length=50)

    @field_validator("username")
    @classmethod
    def normalized_username(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Username cannot be blank")
        return value


class Register(EmailInput, UsernameInput):
    password: Password
    password_confirm: str | None = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices("password_confirm", "confirmPassword"),
    )

    @model_validator(mode="after")
    def same_password(self):
        # The React form compares its two password fields before it calls the
        # AuthService and deliberately sends only password.  Other clients may
        # still send either confirmation-field spelling and get this extra check.
        if self.password_confirm is not None and self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class Login(EmailInput):
    password: str = Field(min_length=1, max_length=128)


class Verify(EmailInput):
    code: str = Field(pattern=r"^\d{6}$")


class ResetPassword(Verify):
    password: Password
    password_confirm: str = Field(
        max_length=128,
        validation_alias=AliasChoices("password_confirm", "confirmPassword"),
    )

    @model_validator(mode="after")
    def same_password(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class RefreshInput(Input):
    refresh_token: str = Field(min_length=1, max_length=4096)


class Tokens(Output):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class Message(Output):
    message: str


class UserRead(Output):
    id: int
    username: str
    email: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime


class FrontendUser(Output):
    """The TypeScript AuthService-compatible view of the current user."""

    id: str
    username: str
    email: str
    created_at: datetime = Field(serialization_alias="createdAt")


class CatalogInput(Input):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class CatalogRead(Output):
    id: int
    name: str


class ProfileUpdate(Input):
    first_name: str = Field(default="", max_length=80)
    last_name: str = Field(default="", max_length=80)
    bio: str = Field(default="", max_length=3000)
    birth_date: date | None = None
    github_url: HttpUrl | None = None
    experience: str = Field(default="", max_length=3000)
    interests: str = Field(default="", max_length=2000)
    role_id: int | None = Field(default=None, gt=0)

    @field_validator("github_url")
    @classmethod
    def bounded_url(cls, value):
        if value and len(str(value)) > 300:
            raise ValueError("URL must contain at most 300 characters")
        return value

    @field_validator("birth_date")
    @classmethod
    def past_date(cls, value):
        if value and value > date.today():
            raise ValueError("Birth date cannot be in the future")
        return value


class SkillLevel(Input):
    skill_id: int = Field(gt=0)
    level: int = Field(ge=1, le=5)


class ProfileSkills(Input):
    skills: list[SkillLevel] = Field(max_length=100)

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, values):
        if len({v.skill_id for v in values}) != len(values):
            raise ValueError("Duplicate skills")
        return values


class ProfileRead(Output):
    id: int
    user_id: int
    username: str
    first_name: str
    last_name: str
    bio: str
    birth_date: date | None
    github_url: str | None
    experience: str
    interests: str
    role_id: int | None
    skills: list[SkillLevel]


class PublicProfile(Output):
    user_id: int
    username: str
    first_name: str
    last_name: str
    bio: str
    github_url: str | None
    experience: str
    interests: str
    role_id: int | None
    skills: list[SkillLevel]


class SkillWeight(Input):
    skill_id: int = Field(gt=0)
    weight: int = Field(ge=1, le=5)


class ProjectInput(Input):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=10000)
    skills: list[SkillWeight] = Field(default_factory=list, max_length=100)
    role_ids: list[int] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def unique_requirements(self):
        if len({s.skill_id for s in self.skills}) != len(self.skills):
            raise ValueError("Duplicate skills")
        if len(set(self.role_ids)) != len(self.role_ids) or any(r <= 0 for r in self.role_ids):
            raise ValueError("Invalid or duplicate roles")
        if not self.title.strip() or not self.description.strip():
            raise ValueError("Title and description cannot be blank")
        return self


class ProjectRead(Output):
    id: int
    owner_id: int
    title: str
    description: str
    status: str
    created_at: datetime
    skills: list[SkillWeight]
    role_ids: list[int]


class StatusInput(Input):
    status: Literal["open", "closed"]


class ModerationInput(Input):
    status: Literal["open", "blocked"]


class SwipeInput(Input):
    decision: Literal["like", "pass"]


class MatchRead(Output):
    id: int
    project_id: int
    candidate_id: int
    created_at: datetime
    room_key: str


class SwipeRead(Output):
    decision: str
    match: MatchRead | None


class ProjectScore(Output):
    project: ProjectRead
    score: float
    matched_skill_ids: list[int]


class CandidateScore(Output):
    profile: PublicProfile
    score: float
    matched_skill_ids: list[int]
