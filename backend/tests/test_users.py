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


def test_create_and_login_user():
    with TestClient(app) as client:
        user = {"email": "u@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=user)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == user["email"]
        assert data["role"] == "owner"

        r = client.post(
            "/пользователи/token",
            data={"username": user["email"], "password": user["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200
        token = r.json().get("access_token")
        assert token


def test_join_account():
    with TestClient(app) as client:
        # create first user (owner of account)
        owner = {"email": "owner@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=owner)
        assert r.status_code == 200
        owner_data = r.json()
        client.post(
            "/пользователи/token",
            data={"username": owner["email"], "password": owner["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # create second user
        member = {"email": "member@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=member)
        assert r.status_code == 200
        member_token = client.post(
            "/пользователи/token",
            data={"username": member["email"], "password": member["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ).json()["access_token"]

        # member joins owner's account
        headers = {"Authorization": f"Bearer {member_token}"}
        r = client.post(
            "/пользователи/join",
            json={"account_id": owner_data["account_id"]},
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["account_id"] == owner_data["account_id"]
        assert data["role"] == "member"


def test_members_list_and_remove():
    with TestClient(app) as client:
        owner = {"email": "own2@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=owner)
        assert r.status_code == 200
        owner_data = r.json()
        owner_token = client.post(
            "/пользователи/token",
            data={"username": owner["email"], "password": owner["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ).json()["access_token"]
        headers_owner = {"Authorization": f"Bearer {owner_token}"}

        member = {"email": "mem2@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=member)
        assert r.status_code == 200
        member_token = client.post(
            "/пользователи/token",
            data={"username": member["email"], "password": member["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ).json()["access_token"]
        headers_member = {"Authorization": f"Bearer {member_token}"}

        r = client.post(
            "/пользователи/join",
            json={"account_id": owner_data["account_id"]},
            headers=headers_member,
        )
        assert r.status_code == 200
        member_id = r.json()["id"]

        r = client.get("/пользователи/участники", headers=headers_owner)
        assert r.status_code == 200
        assert len(r.json()) == 2

        r = client.delete(f"/пользователи/{member_id}", headers=headers_owner)
        assert r.status_code == 204

        r = client.get("/пользователи/участники", headers=headers_owner)
        assert r.status_code == 200
        assert len(r.json()) == 1


def test_update_user_profile():
    with TestClient(app) as client:
        user = {"email": "prof@example.com", "password": "pass"}
        r = client.post("/пользователи/", json=user)
        assert r.status_code == 200

        token = client.post(
            "/пользователи/token",
            data={"username": user["email"], "password": user["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # смена email
        r = client.patch(
            "/пользователи/me",
            json={"email": "new@example.com"},
            headers=headers,
        )
        assert r.status_code == 200

        # авторизация с новым email
        token = client.post(
            "/пользователи/token",
            data={"username": "new@example.com", "password": user["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # смена пароля
        r = client.patch(
            "/пользователи/me",
            json={"password": "newpass"},
            headers=headers,
        )
        assert r.status_code == 200

        r = client.post(
            "/пользователи/token",
            data={"username": "new@example.com", "password": "newpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200
