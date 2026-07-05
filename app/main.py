from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.judge import router as judge_router
from app.api.problems import router as problems_router
from app.api.reports import router as reports_router
from app.config import BASE_DIR
from app.database import init_db

app = FastAPI(title="CodeTrap-Agent", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(problems_router, prefix="/api")
app.include_router(judge_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.mount("/", StaticFiles(directory=BASE_DIR / "app" / "static", html=True), name="static")

