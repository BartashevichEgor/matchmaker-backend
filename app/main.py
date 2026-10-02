from fastapi import FastAPI

app = FastAPI(
    title="Matchmaker API",
    version="0.1.0",
)


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/health")
def health():
    return {"status": "ok"}