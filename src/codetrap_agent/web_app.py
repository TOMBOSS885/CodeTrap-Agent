"""Local FastAPI web app."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import app_password, parse_models, update_local_api_key, validate_api_key, validate_base_url
from .generator import export_bundle, generate_bundle
from .paths import ensure_tree
from .storage import append_audit, load_state, save_state

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))


def create_app(data_root: Path) -> FastAPI:
    root = ensure_tree(data_root)
    app = FastAPI(title="CodeTrap-Agent")

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
        api_key: str = Form(...),
        models: str = Form(...),
    ) -> Any:
        try:
            validate_base_url(base_url)
            validate_api_key(api_key)
            parsed_models = parse_models(models)
            if not parsed_models:
                raise ValueError("at least one model is required")
        except ValueError as exc:
            return _redirect_home(error=str(exc))
        state = load_state(root)
        update_local_api_key(root, api_key)
        state["settings"] = {
            "configured": True,
            "base_url": base_url.strip(),
            "api_key_set": True,
            "models": parsed_models,
        }
        append_audit(state, "settings.saved", ",".join(parsed_models))
        save_state(root, state)
        return _redirect_home(notice="settings saved")

    @app.post("/generate")
    async def generate(
        topic: str = Form(...),
        count: int = Form(1),
        model: str = Form(""),
        difficulty: str = Form("hard"),
    ) -> Any:
        try:
            bundle = generate_bundle(
                root,
                topic=topic,
                count=max(1, min(int(count), 10)),
                model=model,
                difficulty=difficulty,
                use_mock=False,
            )
        except Exception as exc:
            return _redirect_home(error=_short_error(exc))
        return _redirect(f"/bundle/{bundle['bundle_id']}?{urlencode({'notice': 'generated'})}")

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
