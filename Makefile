.PHONY: dev ci lint test devcontainer

dev:
	python -m webbrowser http://localhost:8000/docs &
	docker-compose up --build

lint:
	ruff .
	black --check .
	mypy backend/app

test:
	pytest backend/tests

ci: lint test

devcontainer:
	devcontainer up --workspace-folder .
