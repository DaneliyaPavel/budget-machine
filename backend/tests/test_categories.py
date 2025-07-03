import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

# добавить корень проекта в путь поиска модулей
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


def _create_user(client):
    user = {"email": "cat@example.com", "password": "pass"}
    r = client.post("/users/", json=user)
    assert r.status_code == 200
    assert r.json()["role"] == "owner"
    return user


def _login(client, user):
    r = client.post(
        "/users/token",
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
            "/categories/",
            json={"name": "Продукты", "monthly_limit": 1000},
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        cat_id = data["id"]
        assert data["name"] == "Продукты"

        r = client.get("/categories/", headers=headers)
        assert r.status_code == 200
        cats = r.json()
        assert len(cats) == 1
        assert cats[0]["id"] == cat_id

        r = client.patch(
            f"/categories/{cat_id}",
            json={"monthly_limit": 2000},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["monthly_limit"] == 2000

        r = client.delete(f"/categories/{cat_id}", headers=headers)
        assert r.status_code == 204
        r = client.get("/categories/", headers=headers)
        assert r.status_code == 200
        assert r.json() == []


def test_subcategory_creation():
    with TestClient(app) as client:
        user = {"email": "cat2@example.com", "password": "pass"}
        r = client.post("/users/", json=user)
        assert r.status_code == 200
        token = _login(client, user)
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/categories/", json={"name": "Быт"}, headers=headers)
        parent_id = r.json()["id"]

        r = client.post(
            "/categories/",
            json={"name": "Химия", "parent_id": parent_id},
            headers=headers,
        )
        assert r.status_code == 200
        sub_id = r.json()["id"]
        assert r.json()["parent_id"] == parent_id

        r = client.get("/categories/", headers=headers)
        data = {c["id"]: c for c in r.json()}
        assert parent_id in data and sub_id in data
        assert data[sub_id]["parent_id"] == parent_id
