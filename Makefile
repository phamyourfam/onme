.PHONY: dev install test

dev:
	cd api && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

install:
	cd api && pip install -e .

test:
	cd api && pytest
