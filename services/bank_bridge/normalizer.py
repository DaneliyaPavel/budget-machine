from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import json
from jsonschema import Draft202012Validator

from backend.app.schemas.transaction import TransactionCreate
from backend.app.schemas.posting import PostingCreate

from . import kafka

BASE_DIR = Path(__file__).resolve().parents[2]
with open(BASE_DIR / "schemas/bank-bridge/bank.raw/1.0.0/schema.json", "r", encoding="utf-8") as f:
    _schema = json.load(f)

VALIDATOR = Draft202012Validator(_schema)


def normalize_record(raw: dict[str, Any]) -> TransactionCreate:
    """Convert raw bank transaction to :class:`TransactionCreate`."""
    amount = float(raw["amount"])
    return TransactionCreate(
        posted_at=datetime.fromisoformat(raw["date"]),
        payee=raw.get("payee"),
        note=raw.get("description"),
        external_id=str(raw.get("bank_txn_id")),
        postings=[
            PostingCreate(
                amount=abs(amount),
                side="credit" if amount > 0 else "debit",
                account_id=UUID(str(raw["account_id"])),
                currency_code=raw.get("currency", "RUB"),
            )
        ],
    )


async def process(raw: dict[str, Any]) -> None:
    """Normalize raw data and publish to Kafka."""
    user_id = str(raw.get("user_id"))
    bank_txn_id = str(raw.get("bank_txn_id"))
    try:
        VALIDATOR.validate(raw)
        payload = dict(raw.get("payload", {}))
        payload.setdefault("bank_txn_id", bank_txn_id)
        tx = normalize_record(payload)
    except Exception as exc:  # pragma: no cover - simple error path
        await kafka.publish(
            "bank.err",
            user_id,
            bank_txn_id,
            {"error": str(exc), "data": raw},
        )
        return

    await kafka.publish(
        "bank.norm",
        user_id,
        bank_txn_id,
        tx.model_dump(mode="json", exclude_none=True),
    )
