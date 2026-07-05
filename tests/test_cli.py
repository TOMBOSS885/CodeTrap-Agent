from __future__ import annotations

from typer.testing import CliRunner

from codetrap_agent.cli import app


def test_cli_generate_mock(tmp_path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["generate", "--topic", "数组", "--count", "1", "--mock", "--data-dir", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "trap_" in result.stdout


def test_cli_settings_set(tmp_path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "settings",
            "set",
            "--base-url",
            "https://example.com/v1",
            "--api-key",
            "sk-test",
            "--models",
            "model-a,model-b",
            "--data-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "model-a" in result.stdout
