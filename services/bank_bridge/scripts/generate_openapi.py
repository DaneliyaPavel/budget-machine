from pathlib import Path

import yaml

from services.bank_bridge.app import app


def main() -> None:
    schema = app.openapi()
    fixed_paths = {}
    for path, data in schema["paths"].items():
        if path.endswith(":"):
            path = path.rstrip(":")
        fixed_paths[path] = data
    schema["paths"] = fixed_paths

    docs_dir = Path("docs/bank-bridge")
    docs_dir.mkdir(parents=True, exist_ok=True)
    with open(docs_dir / "openapi.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(schema, f, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    main()
