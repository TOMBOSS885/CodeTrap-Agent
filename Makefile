.PHONY: install test lint serve mock

install:
	python -m pip install -e .[dev]

test:
	python -m pytest

lint:
	python -m ruff check src tests

serve:
	codetrap-agent serve

mock:
	codetrap-agent generate --topic "字符串解析" --count 1 --mock
