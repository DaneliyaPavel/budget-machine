.PHONY: dev ci

dev:
	python -m webbrowser http://localhost:8000/docs &
	docker-compose up --build

ci:
	ruff .
	black --check .
	mypy backend/app
	pytest backend/tests
