.PHONY: test run docker

test:
	python -m pytest -q

run:
	uvicorn app.main:app --host 0.0.0.0 --port 3141

docker:
	docker compose up --build -d
