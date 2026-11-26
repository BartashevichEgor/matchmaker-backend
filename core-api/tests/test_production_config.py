from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app, logger

BASE_PRODUCTION = {
    "environment": "production",
    "jwt_secret": "test-only-secret-not-for-any-real-deployment-12345",
    "database_url": "postgresql+psycopg://user:password@db/matchmaker",
    "redis_url": "redis://redis:6379/0",
    "mail_mode": "smtp",
    "refresh_cookie_secure": True,
    "web_base_url": "https://app.example.com",
    "mail_server": "smtp.example.com",
}


def test_jwt_secret_is_required():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", jwt_secret=None)


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("database_url", "sqlite:///local.db", "Production requires PostgreSQL"),
        ("redis_url", None, "Production requires Redis"),
        ("redis_url", "not-a-redis-url", "Production requires a valid Redis URL"),
        ("mail_mode", "outbox", "Production requires SMTP"),
        ("mail_server", "localhost", "Production requires a configured SMTP server"),
        ("mail_from", "noreply@matchmaker.local", "value is not a valid email address"),
    ],
)
def test_production_requires_runtime_dependencies(key, value, message):
    settings = {**BASE_PRODUCTION, key: value}
    with pytest.raises(ValidationError, match=message):
        Settings(**settings)


def test_local_and_test_settings_can_use_local_services():
    for environment in ("local", "test"):
        Settings(
            _env_file=None,
            environment=environment,
            jwt_secret="test-only-secret-not-for-any-real-deployment-12345",
        )


def test_auth_rate_limit_policies_use_normalized_email_and_user(monkeypatch):
    import app.api.auth as auth_module

    calls = []
    monkeypatch.setattr(auth_module, "limit", lambda *args: calls.append(args))
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    auth_module.throttle(request, "login", "  Person@Example.com ")
    assert calls == [
        ("login:ip:127.0.0.1", 30, 300),
        ("login:ip-email:127.0.0.1:person@example.com", 5, 900),
    ]
    calls.clear()

    auth_module.throttle(request, "resend", "Person@Example.com", user_id=42)
    assert calls == [
        ("verification-send:ip:127.0.0.1", 30, 300),
        ("verification-send:email:person@example.com:ip:127.0.0.1", 3, 900),
        ("verification-send:user:42:ip:127.0.0.1", 3, 900),
    ]
    calls.clear()

    auth_module.throttle(request, "verify", "PERSON@example.COM", user_id=42)
    assert calls == [
        ("verification-check:ip:127.0.0.1", 30, 300),
        ("verification-check:email:person@example.com", 5, 600),
        ("verification-check:user:42", 5, 600),
    ]


def test_readiness_reports_smtp_failure_without_connection_details(client, monkeypatch):
    import app.api.health as health_module

    monkeypatch.setattr(
        health_module,
        "get_settings",
        lambda: SimpleNamespace(
            environment="production",
            mail_mode="smtp",
            mail_server="smtp.example.com",
            mail_port=587,
            mail_ssl_tls=False,
            mail_starttls=True,
            mail_use_credentials=False,
        ),
    )
    monkeypatch.setattr(health_module, "redis_client", lambda: None)

    def unavailable(*_args, **_kwargs):
        raise OSError("credential=must-not-leak")

    monkeypatch.setattr(health_module.smtplib, "SMTP", unavailable)
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["dependencies"] == {
        "database": "UP",
        "cache": "local-memory",
        "mail": "DOWN",
    }
    assert "must-not-leak" not in response.text


def test_readiness_checks_smtp_credentials_without_leaking_them(client, monkeypatch):
    import smtplib

    import app.api.health as health_module

    password = "smtp-secret-for-test"
    settings = SimpleNamespace(
        environment="production",
        mail_mode="smtp",
        mail_server="smtp.example.com",
        mail_port=587,
        mail_ssl_tls=False,
        mail_starttls=True,
        mail_use_credentials=True,
        mail_username="mailer@example.com",
        mail_password=SimpleNamespace(get_secret_value=lambda: password),
    )
    monkeypatch.setattr(health_module, "get_settings", lambda: settings)
    monkeypatch.setattr(health_module, "redis_client", lambda: None)

    class SMTP:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def ehlo(self):
            return 250, b"ok"

        def starttls(self, **_kwargs):
            return 220, b"ready"

        def login(self, username, supplied_password):
            assert username == settings.mail_username
            assert supplied_password == password
            raise smtplib.SMTPAuthenticationError(535, b"invalid credentials")

        def noop(self):
            return 250, b"ok"

    monkeypatch.setattr(health_module.smtplib, "SMTP", lambda *_args, **_kwargs: SMTP())
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["dependencies"]["mail"] == "DOWN"
    assert password not in response.text


def test_request_logs_are_redacted_and_unhandled_errors_keep_request_id(client):
    logs = []
    sink_id = logger.add(lambda message: logs.append(str(message)), level="INFO")

    def fail_with_secret():
        raise RuntimeError("password=must-not-leak")

    app.add_api_route("/_test/failure/{secret}", fail_with_secret, methods=["GET"])
    try:
        ok = client.get("/ping?token=query-secret")
        failed = client.get("/_test/failure/path-secret")
    finally:
        app.router.routes[:] = [
            route for route in app.router.routes if getattr(route, "path", None) != "/_test/failure/{secret}"
        ]
        logger.remove(sink_id)

    assert ok.headers["x-request-id"]
    assert failed.status_code == 500
    assert failed.headers["x-request-id"] == failed.json()["request_id"]
    assert "status=200" in "".join(logs)
    assert "status=500" in "".join(logs)
    assert "RuntimeError" in "".join(logs)
    assert "fail_with_secret" in "".join(logs)
    assert "query-secret" not in "".join(logs)
    assert "password=" not in "".join(logs)
    assert "must-not-leak" not in "".join(logs)
