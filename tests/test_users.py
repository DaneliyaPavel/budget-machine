import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

# добавить корень проекта в путь поиска модулей
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
from app.main import app


def test_create_and_login_user():
    with TestClient(app) as client:
        user = {"email": "u@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=user)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == user["email"]

        r = client.post(
            "/пользователи/token",
            data={"username": user["email"], "password": user["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200
        token = r.json().get("access_token")
        assert token
