"""CodeTrap-Agent CLI."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import typer
import uvicorn

from .config import (
    load_runtime_config,
    parse_models,
    require_models,
    update_local_api_key,
    validate_api_key,
    validate_base_url,
)
from .generator import export_bundle, generate_bundle
from .model_client import ModelAPIError
from .paths import default_root, ensure_tree
from .storage import append_audit, load_state, save_state
from .web_app import create_app

app = typer.Typer(help="AI-assisted adversarial programming problem generator")
settings_app = typer.Typer(help="Settings commands")
app.add_typer(settings_app, name="settings")


@app.command("init")
def init(data_dir: Path = typer.Option(default_root(), "--data-dir")) -> None:
    root = ensure_tree(data_dir)
    save_state(root, load_state(root))
    typer.echo(f"initialized workspace: {root}")


@app.command("reset")
def reset(data_dir: Path = typer.Option(default_root(), "--data-dir")) -> None:
    if data_dir.exists():
        shutil.rmtree(data_dir)
    root = ensure_tree(data_dir)
    save_state(root, load_state(root))
    typer.echo(f"reset workspace: {root}")


@settings_app.command("set")
def settings_set(
    base_url: str = typer.Option(..., "--base-url"),
    api_key: str = typer.Option(..., "--api-key"),
    models: str = typer.Option(..., "--models"),
    data_dir: Path = typer.Option(default_root(), "--data-dir"),
) -> None:
    root = ensure_tree(data_dir)
    parsed_models = parse_models(models)
    try:
        validate_base_url(base_url)
        validate_api_key(api_key)
        require_models(parsed_models)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    update_local_api_key(root, api_key)
    state = load_state(root)
    runtime = load_runtime_config(root)
    state["settings"] = {
        "configured": True,
        "base_url": base_url.strip(),
        "api_key_set": runtime.api_key_set,
        "models": parsed_models,
    }
    append_audit(state, "settings.saved", ",".join(parsed_models))
    save_state(root, state)
    _echo_json({"settings": state["settings"]})


@settings_app.command("show")
def settings_show(data_dir: Path = typer.Option(default_root(), "--data-dir")) -> None:
    root = ensure_tree(data_dir)
    state = load_state(root)
    runtime = load_runtime_config(root, state.get("settings", {}))
    shown = dict(state.get("settings", {}))
    shown["api_key_set"] = runtime.api_key_set
    _echo_json({"settings": shown})


@app.command("generate")
def generate(
    topic: str = typer.Option(..., "--topic"),
    count: int = typer.Option(1, "--count", min=1, max=10),
    model: str = typer.Option("", "--model"),
    language: str = typer.Option("Python", "--language"),
    difficulty: str = typer.Option("hard", "--difficulty"),
    mock: bool = typer.Option(False, "--mock"),
    data_dir: Path = typer.Option(default_root(), "--data-dir"),
) -> None:
    root = ensure_tree(data_dir)
    try:
        bundle = generate_bundle(
            root,
            topic=topic,
            count=count,
            model=model,
            language=language,
            difficulty=difficulty,
            use_mock=mock,
        )
    except (ValueError, ModelAPIError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _echo_json(_bundle_summary(bundle))


@app.command("list")
def list_bundles(data_dir: Path = typer.Option(default_root(), "--data-dir")) -> None:
    state = load_state(ensure_tree(data_dir))
    _echo_json({"bundles": [_bundle_summary(item) for item in state.get("bundles", [])]})


@app.command("show")
def show(bundle_id: str = typer.Argument(...), data_dir: Path = typer.Option(default_root(), "--data-dir")) -> None:
    state = load_state(ensure_tree(data_dir))
    for bundle in state.get("bundles", []):
        if bundle.get("bundle_id") == bundle_id:
            _echo_json(bundle)
            return
    raise typer.BadParameter("bundle not found")


@app.command("export")
def export(bundle_id: str = typer.Argument(...), data_dir: Path = typer.Option(default_root(), "--data-dir")) -> None:
    path = export_bundle(ensure_tree(data_dir), bundle_id)
    _echo_json({"export": str(path)})


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(3141, "--port"),
    data_dir: Path = typer.Option(default_root(), "--data-dir"),
) -> None:
    uvicorn.run(create_app(ensure_tree(data_dir)), host=host, port=port)


def _bundle_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "bundle_id": bundle.get("bundle_id"),
        "created_at": bundle.get("created_at"),
        "model": bundle.get("model"),
        "topic": bundle.get("topic"),
        "problem_count": len(bundle.get("problems", [])),
        "quality": bundle.get("quality", {}),
    }


def _echo_json(payload: Any) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
