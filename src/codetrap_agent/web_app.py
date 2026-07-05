"""Local FastAPI web app."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import (
    app_password,
    load_runtime_config,
    parse_models,
    update_local_api_key,
    validate_api_key,
    validate_base_url,
)
from .generator import export_bundle, generate_bundle
from .paths import ensure_tree
from .storage import append_audit, load_state, save_state

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))


def create_app(data_root: Path) -> FastAPI:
    root = ensure_tree(data_root)
    app = FastAPI(title="CodeTrap-Agent")
    jobs: dict[str, dict[str, Any]] = {}
    jobs_lock = threading.Lock()

    @app.middleware("http")
    async def require_basic_auth(request: Request, call_next: Any) -> Any:
        password = app_password()
        if not password:
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        if not _valid_basic_auth(auth, password):
            return PlainTextResponse(
                "authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="CodeTrap-Agent"'},
            )
        return await call_next(request)

    app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> Any:
        return templates.TemplateResponse(request, "index.html", _context(request, root))

    @app.post("/settings")
    async def settings(
        base_url: str = Form(...),
        api_key: str = Form(""),
        models: str = Form(...),
    ) -> Any:
        state = load_state(root)
        runtime = load_runtime_config(root, state.get("settings", {}))
        try:
            validate_base_url(base_url)
            if api_key.strip():
                validate_api_key(api_key)
            elif not runtime.api_key_set:
                raise ValueError("api_key cannot be empty")
            parsed_models = parse_models(models)
            if not parsed_models:
                raise ValueError("at least one model is required")
        except ValueError as exc:
            return _redirect_home(error=str(exc))
        if api_key.strip():
            update_local_api_key(root, api_key)
            runtime = load_runtime_config(root, state.get("settings", {}))
        state["settings"] = {
            "configured": True,
            "base_url": base_url.strip(),
            "api_key_set": runtime.api_key_set,
            "models": parsed_models,
        }
        append_audit(state, "settings.saved", ",".join(parsed_models))
        save_state(root, state)
        return _redirect_home(notice="settings saved")

    @app.post("/generate")
    async def generate(
        request: Request,
        topic: str = Form(...),
        count: int = Form(1),
        model: str = Form(""),
        difficulty: str = Form("hard"),
    ) -> Any:
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "status": "queued",
            "message": "已收到请求，正在准备生成任务。",
            "created_at": datetime.now(UTC).isoformat(),
            "bundle_id": "",
            "bundle_url": "",
            "error": "",
        }
        with jobs_lock:
            _prune_jobs(jobs)
            jobs[job_id] = job
        thread = threading.Thread(
            target=_run_generation_job,
            args=(jobs, jobs_lock, job_id, root, topic, count, model, difficulty),
            daemon=True,
        )
        thread.start()
        if _wants_json(request):
            return JSONResponse(job)
        return _redirect_home(notice="generation started")

    @app.get("/jobs/{job_id}")
    async def job_status(job_id: str) -> Any:
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return JSONResponse(
                    {
                        "job_id": job_id,
                        "status": "failed",
                        "message": "任务不存在，可能是服务重启或任务已过期。",
                        "error": "job not found",
                    },
                    status_code=404,
                )
            return JSONResponse(dict(job))

    @app.get("/bundle/{bundle_id}", response_class=HTMLResponse)
    def bundle_detail(request: Request, bundle_id: str) -> Any:
        state = load_state(root)
        bundle = next((item for item in state.get("bundles", []) if item.get("bundle_id") == bundle_id), None)
        if not bundle:
            return _redirect_home(error="bundle not found")
        return templates.TemplateResponse(
            request,
            "bundle.html",
            {**_context(request, root), "bundle": bundle},
        )

    @app.get("/bundle/{bundle_id}/export")
    def bundle_export(bundle_id: str) -> Any:
        try:
            return FileResponse(export_bundle(root, bundle_id), filename=f"{bundle_id}.json")
        except ValueError:
            return _redirect_home(error="bundle not found")

    return app


def _context(request: Request, root: Path) -> dict[str, Any]:
    state = load_state(root)
    return {
        "request": request,
        "state": state,
        "bundles": state.get("bundles", []),
        "notice": request.query_params.get("notice", ""),
        "error": request.query_params.get("error", ""),
    }


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def _redirect_home(**query: str) -> RedirectResponse:
    return _redirect(f"/?{urlencode(query)}")


def _short_error(exc: Exception) -> str:
    text = str(exc).replace("\n", " ").strip()
    return text[:240] or "request failed"


def _wants_json(request: Request) -> bool:
    return (
        request.headers.get("x-requested-with") == "fetch"
        or "application/json" in request.headers.get("accept", "")
    )


def _set_job(jobs: dict[str, dict[str, Any]], jobs_lock: threading.Lock, job_id: str, **values: Any) -> None:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is not None:
            job.update(values)
            job["updated_at"] = datetime.now(UTC).isoformat()


def _run_generation_job(
    jobs: dict[str, dict[str, Any]],
    jobs_lock: threading.Lock,
    job_id: str,
    root: Path,
    topic: str,
    count: int,
    model: str,
    difficulty: str,
) -> None:
    try:
        _set_job(jobs, jobs_lock, job_id, status="running", message="正在请求模型生成题目、样例和参考答案。")
        bundle = generate_bundle(
            root,
            topic=topic,
            count=max(1, min(int(count), 10)),
            model=model,
            difficulty=difficulty,
            use_mock=False,
            model_timeout=45.0,
        )
        _set_job(jobs, jobs_lock, job_id, status="running", message="模型已返回，正在校验结构并保存题包。")
        bundle_url = f"/bundle/{bundle['bundle_id']}?{urlencode({'notice': 'generated'})}"
        _set_job(
            jobs,
            jobs_lock,
            job_id,
            status="succeeded",
            message="生成完成，正在打开题包。",
            bundle_id=bundle["bundle_id"],
            bundle_url=bundle_url,
        )
    except Exception as exc:
        _set_job(
            jobs,
            jobs_lock,
            job_id,
            status="failed",
            message="生成失败。请检查模型设置、API Key、模型名，或稍后重试。",
            error=_short_error(exc),
        )


def _prune_jobs(jobs: dict[str, dict[str, Any]], limit: int = 100) -> None:
    if len(jobs) <= limit:
        return
    stale = sorted(jobs.items(), key=lambda item: item[1].get("created_at", ""))
    for job_id, _ in stale[: len(jobs) - limit]:
        jobs.pop(job_id, None)


def _valid_basic_auth(header: str, expected_password: str) -> bool:
    import base64
    import hmac

    prefix = "Basic "
    if not header.startswith(prefix):
        return False
    try:
        decoded = base64.b64decode(header[len(prefix) :], validate=True).decode("utf-8")
    except Exception:
        return False
    username, separator, password = decoded.partition(":")
    if not separator or username != "admin":
        return False
    return hmac.compare_digest(password, expected_password)
