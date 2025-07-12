.PHONY: dev ci lint test devcontainer proto openapi openapi-bankbridge demo_user bankbridge-tests


dev:
	python -m webbrowser http://localhost:8000/docs &
	docker compose up --build

lint:
	ruff check .
	black --check .
	mypy backend/app

test:
	pytest --cov=backend --cov-fail-under=90 tests

ci: lint test

devcontainer:
	devcontainer up --workspace-folder .

proto:
	buf generate proto

openapi:
	python -m backend.scripts.generate_openapi

openapi-bankbridge:
	python -m services.bank_bridge.scripts.generate_openapi

demo_user:
	python -m backend.scripts.create_demo_user

bankbridge-tests:
	pytest --cov=services/bank_bridge --cov-config=.coveragerc.bankbridge --cov-fail-under=90 tests/bank_bridge
