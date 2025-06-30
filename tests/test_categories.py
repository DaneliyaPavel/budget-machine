import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

# добавить корень проекта в путь поиска модулей
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.main import app


def _create_user(client):
    user = {"email": "cat@example.com", "password": "pass"}
    r = client.post("/пользователи/", json=user)
    assert r.status_code == 200
    assert r.json()["role"] == "owner"
    return user


def _login(client, user):
    r = client.post(
        "/пользователи/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_category_crud():
    with TestClient(app) as client:
        user = _create_user(client)
        token = _login(client, user)
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post(
            "/категории/",
            json={"name": "Продукты", "monthly_limit": 1000},
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        cat_id = data["id"]
        assert data["name"] == "Продукты"

        r = client.get("/категории/", headers=headers)
        assert r.status_code == 200
        cats = r.json()
        assert len(cats) == 1
        assert cats[0]["id"] == cat_id

        r = client.patch(
            f"/категории/{cat_id}",
            json={"monthly_limit": 2000},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["monthly_limit"] == 2000

        r = client.delete(f"/категории/{cat_id}", headers=headers)
        assert r.status_code == 204
        r = client.get("/категории/", headers=headers)
        assert r.status_code == 200
        assert r.json() == []
