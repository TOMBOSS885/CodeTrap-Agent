# CodeTrap-Agent

CodeTrap-Agent is a Python + FastAPI system for adversarial programming problem generation and judging. It generates problem cases, reference answers, common wrong solutions, judge results, and Markdown/HTML weakness reports for evaluating coding models.

## Features

- Five extensible problem families: graph path counting, JSON Patch, interval merge, expression parser, and DP counting.
- Online search for related algorithm problems and AI-failure-prone edge cases, with offline fallback.
- Full problem bundle generation: original statement, test data, expected outputs, reference answer, and search sources.
- `reference_solve`, `generate_cases`, and `generate_mutants` for every family.
- Case levels: `basic`, `edge`, and `adversarial`.
- Candidate Python solutions use a unified `solve(input_data)` entry point.
- Subprocess-based judge with per-case timeout, exception capture, output comparison, and weakness summaries.
- Pluggable sandbox backend: default subprocess runner, optional Docker isolation.
- SQLite persistence for generated runs, judge runs, and reports.
- FastAPI API plus a static Web UI with family details, generated cases, mutants, result stats, and report links.
- Markdown and structured HTML report generation.
- Docker and Docker Compose deployment.

## Architecture

```text
app/                 FastAPI app, API routers, SQLite setup, static UI
codetrap/core/       Shared abstractions: ProblemFamily, TestCase, JudgeResult, registry
codetrap/families/   Pluggable problem families
codetrap/judge/      Sandbox runner, checker, analyzer
codetrap/reports/    Markdown and HTML report rendering
examples/            Correct and incorrect candidate solutions
tests/               pytest coverage
```

## Local Run

```bash
py -3.12 -m pip install -r requirements.txt
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 3141
```

Open `http://localhost:3141`.

Health check:

```bash
curl http://localhost:3141/health
```

Expected:

```json
{"status":"ok"}
```

## Docker

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:3141/health
```

If the server cannot pull `python:3.11-slim` from Docker Hub, set a mirror-backed base image in `.env` before building:

```env
PYTHON_IMAGE=docker.m.daocloud.io/python:3.11-slim
```

## Sandbox Backends

The default backend is the local subprocess runner:

```bash
CODETRAP_SANDBOX=subprocess
```

To run candidates inside Docker containers:

```bash
CODETRAP_SANDBOX=docker
CODETRAP_DOCKER_IMAGE=python:3.11-slim
```

The Docker backend runs each case with `--network none`, a read-only filesystem, memory and CPU limits, and a small writable `/tmp`. Docker must be installed on the host for this mode.

## API

- `GET /health`
- `GET /api/families`
- `GET /api/families/{family_id}`
- `POST /api/families/{family_id}/cases`
- `POST /api/families/{family_id}/problem`
- `GET /api/problems`
- `GET /api/problems/{problem_id}`
- `POST /api/judge/{family_id}`
- `GET /api/reports/{report_id}`
- `GET /api/reports/{report_id}/download`

Generate cases:

```bash
curl -X POST http://localhost:3141/api/families/graph_paths/cases ^
  -H "Content-Type: application/json" ^
  -d "{\"level\":\"edge\",\"count\":5}"
```

Generate a full problem bundle:

```bash
curl -X POST http://localhost:3141/api/families/graph_paths/problem ^
  -H "Content-Type: application/json" ^
  -d "{\"level\":\"adversarial\",\"count\":5,\"search_online\":true}"
```

The response contains `problem_id`. This ID links the generated statement, cases, expected outputs, sources, and later judge runs.

Judge a solution against a saved problem bundle:

```bash
curl -X POST http://localhost:3141/api/judge/graph_paths ^
  -F "problem_id=<problem_id>" ^
  -F "file=@examples/correct_solution.py"
```

List generated problem records:

```bash
curl http://localhost:3141/api/problems
```

Load one generated problem record:

```bash
curl http://localhost:3141/api/problems/<problem_id>
```

## Database Relations

SQLite data is stored at `data/codetrap.sqlite3`.

- `problem_runs`: generation task metadata.
- `problem_bundles`: one generated problem statement and reference answer. Linked by `problem_bundles.run_id -> problem_runs.id`.
- `problem_cases`: test cases and expected outputs. Linked by `problem_cases.problem_id -> problem_bundles.id`.
- `problem_sources`: online search sources. Linked by `problem_sources.problem_id -> problem_bundles.id`.
- `judge_runs`: candidate judging records. Linked by `judge_runs.problem_id -> problem_bundles.id` when judging a saved bundle.
- `reports`: report files. Linked by `reports.judge_run_id -> judge_runs.id`.

Typical association flow:

1. Call `POST /api/families/{family_id}/problem`.
2. Save the returned `problem_id`.
3. Call `POST /api/judge/{family_id}` with form field `problem_id=<problem_id>`.
4. Use returned `judge_run_id` and `report_id` to trace the judge result and report.

Judge a solution:

```bash
curl -X POST http://localhost:3141/api/judge/graph_paths ^
  -F "level=edge" ^
  -F "count=5" ^
  -F "file=@examples/wrong_solution_graph.py"
```

## Add A Problem Family

1. Create a new directory under `codetrap/families/{family_id}`.
2. Implement a class with `family_id`, metadata, `reference_solve`, `generate_cases`, and `generate_mutants`.
3. Ensure generated cases call `reference_solve` to fill `expected_output`.
4. Register the family in `codetrap/core/registry.py`.
5. Add pytest coverage for reference behavior and generated cases.

## Candidate Solution Contract

Every candidate file must define:

```python
def solve(input_data):
    ...
```

The return value is compared directly with the reference output.

## Testing

```bash
py -3.12 -m pytest -q
```

Current coverage checks registry loading, all family generators, selected reference edge cases, judge acceptance/rejection, Markdown report generation, and `/health`.

## Extension Ideas

- Replace the subprocess sandbox with Docker, Firejail, Kubernetes Jobs, or remote judge workers.
- Add more language runtimes.
- Add model-specific aggregate analytics across repeated judge runs.
- Expand the Web UI with report history and family-specific statement pages.
