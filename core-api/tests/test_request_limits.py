import asyncio

from app.core.request_limits import RequestBodyLimitMiddleware


def test_request_body_limit_rejects_chunked_payload():
    sent = []
    messages = iter(
        (
            {"type": "http.request", "body": b"123", "more_body": True},
            {"type": "http.request", "body": b"456", "more_body": False},
        )
    )

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    async def app(scope, receive, send):
        while (await receive()).get("more_body", False):
            pass

    asyncio.run(RequestBodyLimitMiddleware(app, max_bytes=5)({"type": "http", "headers": []}, receive, send))

    assert sent[0]["status"] == 413
