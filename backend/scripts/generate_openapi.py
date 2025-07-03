from pathlib import Path

import yaml

from backend.app.main import app


def main() -> None:
    schema = app.openapi()
    docs_dir = Path("docs/api")
    docs_dir.mkdir(parents=True, exist_ok=True)
    with open(docs_dir / "openapi.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(schema, f, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    main()
