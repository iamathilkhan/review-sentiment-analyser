.PHONY: dev migrate seed test lint worker flower setup

setup:
	python -m venv venv
	./venv/Scripts/activate && pip install -r requirements.txt
	cp .env.example .env

dev:
	flask run --debug

migrate:
	flask db migrate -m "Auto migration"
	flask db upgrade

seed:
	python scripts/seed.py

test:
	pytest

lint:
	flake8 app tests
	black --check app tests

worker:
	celery -A celery_app worker --loglevel=info

flower:
	celery -A celery_app flower --port=5555
