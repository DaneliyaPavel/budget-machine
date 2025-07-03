.PHONY: dev ci lint test devcontainer proto

dev:
	python -m webbrowser http://localhost:8000/docs &
	docker-compose up --build

lint:
	ruff check .
	black --check .
	mypy backend/app

test:
	pytest backend/tests

ci: lint test

devcontainer:
        devcontainer up --workspace-folder .

proto:
        python -m grpc_tools.protoc -I proto --python_out=backend/app/grpc \
                --grpclib_python_out=backend/app/grpc proto/ledger.proto
