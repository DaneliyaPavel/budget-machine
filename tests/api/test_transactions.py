import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient
from openpyxl import Workbook
import io

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


def _login(client, email="tx@example.com"):
    user = {"email": email, "password": "pass"}
    r = client.post("/users/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/users/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_export_transactions():
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # prepare second account for postings
        acc = client.get("/accounts/me", headers=headers).json()
        r = client.post("/accounts/", json={"name": "Income"}, headers=headers)
        assert r.status_code == 200
        acc2_id = r.json()["id"]

        # create category
        r = client.post("/categories/", json={"name": "Продукты"}, headers=headers)
        assert r.status_code == 200
        cat_id = r.json()["id"]

        tx1 = {
            "payee": "Магазин",
            "posted_at": "2025-07-04T11:21:50",
            "category_id": cat_id,
            "postings": [
                {
                    "amount": 100,
                    "side": "debit",
                    "account_id": acc["id"],
                    "currency_code": "RUB",
                },
                {
                    "amount": 100,
                    "side": "credit",
                    "account_id": acc2_id,
                    "currency_code": "RUB",
                },
            ],
        }
        tx2 = {
            "payee": "Amazon",
            "posted_at": "2025-07-04T11:21:51",
            "category_id": cat_id,
            "postings": [
                {
                    "amount": 50,
                    "side": "debit",
                    "account_id": acc["id"],
                    "currency_code": "USD",
                },
                {
                    "amount": 50,
                    "side": "credit",
                    "account_id": acc2_id,
                    "currency_code": "USD",
                },
            ],
        }
        client.post("/transactions/", json=tx1, headers=headers)
        client.post("/transactions/", json=tx2, headers=headers)

        r = client.get("/transactions/export", headers=headers)
        assert r.status_code == 200
        lines = r.text.strip().splitlines()
        assert len(lines) == 3
        assert lines[0].startswith("id,payee,note")


def test_import_transactions_excel():
    with TestClient(app) as client:
        token = _login(client, email="xlsx@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/categories/", json={"name": "Excel"}, headers=headers)
        assert r.status_code == 200
        cat_id = r.json()["id"]

        wb = Workbook()
        ws = wb.active
        ws.append(
            [
                "payee",
                "note",
                "category_id",
                "posted_at",
            ]
        )
        ws.append(["Row1", "", cat_id, "2025-06-01T12:00:00"])
        ws.append(["Row2", "", cat_id, "2025-06-02T12:00:00"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        files = {
            "file": (
                "data.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        r = client.post("/transactions/import", files=files, headers=headers)
        assert r.status_code == 201
        assert r.json()["created"] == 2

        r = client.get("/transactions/", headers=headers)
        assert r.status_code == 200
        # imported transactions have no postings
        assert r.json() == []


def test_transactions_limit():
    with TestClient(app) as client:
        token = _login(client, email="limit2@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        base_acc = client.get("/accounts/me", headers=headers).json()
        r = client.post("/accounts/", json={"name": "Income"}, headers=headers)
        assert r.status_code == 200
        acc2_id = r.json()["id"]

        r = client.post("/categories/", json={"name": "Lim"}, headers=headers)
        cat_id = r.json()["id"]

        for i in range(5):
            tx = {
                "payee": f"#{i}",
                "category_id": cat_id,
                "postings": [
                    {
                        "amount": i + 1,
                        "side": "debit",
                        "account_id": base_acc["id"],
                        "currency_code": "RUB",
                    },
                    {
                        "amount": i + 1,
                        "side": "credit",
                        "account_id": acc2_id,
                        "currency_code": "RUB",
                    },
                ],
            }
            client.post("/transactions/", json=tx, headers=headers)

        r = client.get("/transactions/?limit=3", headers=headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 3
        assert items[0]["payee"] == "#4"


def test_transactions_filter_by_account():
    with TestClient(app) as client:
        token = _login(client, email="filter@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        base_acc = client.get("/accounts/me", headers=headers).json()
        r = client.post("/accounts/", json={"name": "Income"}, headers=headers)
        acc2_id = r.json()["id"]
        r = client.post("/accounts/", json={"name": "Savings"}, headers=headers)
        acc3_id = r.json()["id"]

        r = client.post("/categories/", json={"name": "Filt"}, headers=headers)
        cat_id = r.json()["id"]

        def make_tx(acc_id):
            return {
                "payee": "t",
                "category_id": cat_id,
                "postings": [
                    {
                        "amount": 1,
                        "side": "debit",
                        "account_id": base_acc["id"],
                        "currency_code": "RUB",
                    },
                    {
                        "amount": 1,
                        "side": "credit",
                        "account_id": acc_id,
                        "currency_code": "RUB",
                    },
                ],
            }

        for _ in range(2):
            client.post("/transactions/", json=make_tx(acc2_id), headers=headers)
        for _ in range(2):
            client.post("/transactions/", json=make_tx(acc3_id), headers=headers)

        r = client.get(f"/transactions/?account_id={acc2_id}", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

        r = client.get(f"/transactions/?account_id={acc3_id}", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2
