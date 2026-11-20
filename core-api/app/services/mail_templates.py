from dataclasses import dataclass
from html import escape
from string import Template
from urllib.parse import urlencode

from app.core.config import ROOT, get_settings

TEMPLATE_DIR = ROOT / "app" / "templates" / "email"


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    plain: str
    html: str


def _html(name: str, values: dict[str, str]) -> str:
    source = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
    safe_values = {key: escape(value, quote=True) for key, value in values.items()}
    return Template(source).substitute(safe_values)


def verification_email(email: str, code: str, link_token: str) -> RenderedEmail:
    query = urlencode({"email": email, "token": link_token})
    # The SPA reads the fragment and submits the credential in a POST body.
    # Fragments are not sent in HTTP requests or Referrer headers.
    link = f"{get_settings().web_base_url.rstrip('/')}/verify-email#{query}"
    plain = (
        "Matchmaker\n"
        "Purpose: verify\n"
        f"Code: {code}\n"
        "Code expires in 10 minutes.\n"
        f"Verification link: {link}\n"
        "The link expires in 24 hours.\n"
    )
    return RenderedEmail(
        subject="Confirm your Matchmaker email",
        plain=plain,
        html=_html("verification.html", {"code": code, "verification_url": link}),
    )


def password_reset_email(email: str, code: str) -> RenderedEmail:
    plain = f"Matchmaker\nPurpose: reset\nCode: {code}\nCode expires in 10 minutes.\nAccount: {email}\n"
    return RenderedEmail(
        subject="Reset your Matchmaker password",
        plain=plain,
        html=_html("password_reset.html", {"code": code}),
    )
