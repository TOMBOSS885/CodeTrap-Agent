.PHONY: test run docker

test:
	python -m pytest -q

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

docker:
	docker compose up --build -d

