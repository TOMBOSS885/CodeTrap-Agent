from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class SandboxResult:
    ok: bool
    output: object | None = None
    error_type: str | None = None
    error_message: str | None = None
    runtime_ms: int = 0


class Sandbox(Protocol):
    backend_name: str

    def run_solution(self, solution_path: str, input_data: dict, timeout_sec: float = 2.0) -> SandboxResult:
        ...


class SubprocessSandbox:
    backend_name = "subprocess"

    def run_solution(self, solution_path: str, input_data: dict, timeout_sec: float = 2.0) -> SandboxResult:
        worker = Path(__file__).with_name("sandbox_worker.py")
        payload = json.dumps(input_data, ensure_ascii=False)
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(worker), solution_path],
                input=payload,
                text=True,
                capture_output=True,
                timeout=timeout_sec,
                cwd=str(Path(solution_path).parent),
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(ok=False, error_type="timeout", error_message=f"exceeded {timeout_sec}s")
        runtime_ms = int((time.perf_counter() - start) * 1000)
        text = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        try:
            data = json.loads(text)
        except Exception:
            return SandboxResult(ok=False, error_type="runtime_error", error_message=proc.stderr[-1000:] or text, runtime_ms=runtime_ms)
        if proc.returncode != 0 or not data.get("ok"):
            return SandboxResult(ok=False, error_type=data.get("error", "runtime_error"), error_message=data.get("message"), runtime_ms=runtime_ms)
        return SandboxResult(ok=True, output=data.get("result"), runtime_ms=runtime_ms)


class DockerSandbox:
    backend_name = "docker"

    def __init__(self, image: str = "python:3.11-slim") -> None:
        self.image = image

    def run_solution(self, solution_path: str, input_data: dict, timeout_sec: float = 2.0) -> SandboxResult:
        if shutil.which("docker") is None:
            return SandboxResult(ok=False, error_type="sandbox_unavailable", error_message="docker command is not available")
        worker = Path(__file__).with_name("sandbox_worker.py").resolve()
        solution = Path(solution_path).resolve()
        payload = json.dumps(input_data, ensure_ascii=False)
        with tempfile.TemporaryDirectory(prefix="codetrap-docker-") as tmp:
            tmp_path = Path(tmp)
            worker_copy = tmp_path / "sandbox_worker.py"
            solution_copy = tmp_path / "solution.py"
            shutil.copy2(worker, worker_copy)
            shutil.copy2(solution, solution_copy)
            cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                "256m",
                "--cpus",
                "1",
                "--pids-limit",
                "64",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=16m",
                "-i",
                "-v",
                f"{tmp_path}:/sandbox:ro",
                "-w",
                "/sandbox",
                self.image,
                "python",
                "-I",
                "/sandbox/sandbox_worker.py",
                "/sandbox/solution.py",
            ]
            start = time.perf_counter()
            try:
                proc = subprocess.run(cmd, input=payload, text=True, capture_output=True, timeout=timeout_sec + 1)
            except subprocess.TimeoutExpired:
                return SandboxResult(ok=False, error_type="timeout", error_message=f"exceeded {timeout_sec}s")
            runtime_ms = int((time.perf_counter() - start) * 1000)
        text = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        try:
            data = json.loads(text)
        except Exception:
            return SandboxResult(ok=False, error_type="runtime_error", error_message=proc.stderr[-1000:] or text, runtime_ms=runtime_ms)
        if proc.returncode != 0 or not data.get("ok"):
            return SandboxResult(ok=False, error_type=data.get("error", "runtime_error"), error_message=data.get("message"), runtime_ms=runtime_ms)
        return SandboxResult(ok=True, output=data.get("result"), runtime_ms=runtime_ms)


def create_sandbox(backend: str = "subprocess", docker_image: str = "python:3.11-slim") -> Sandbox:
    if backend == "docker":
        return DockerSandbox(docker_image)
    return SubprocessSandbox()
