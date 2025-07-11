from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import json
from jsonschema import Draft202012Validator


from . import kafka

BASE_DIR = Path(__file__).resolve().parents[2]
with open(
    BASE_DIR / "schemas/bank-bridge/bank.raw/1.0.0/schema.json", "r", encoding="utf-8"
) as f:
    _raw_schema = json.load(f)

with open(
    BASE_DIR / "schemas/bank-bridge/bank.norm/1.0.0/schema.json", "r", encoding="utf-8"
) as f:
    _norm_schema = json.load(f)

RAW_VALIDATOR = Draft202012Validator(_raw_schema)
NORM_VALIDATOR = Draft202012Validator(_norm_schema)


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert raw bank transaction to normalized dictionary."""
    amount = float(raw["amount"])
    dt = datetime.fromisoformat(str(raw["date"]))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    data = {
        "posted_at": dt.isoformat(),
        "amount": {
            "value": str(abs(amount)),
            "currency": str(raw.get("currency", "RUB")),
        },
        "direction": "in" if amount > 0 else "out",
        "external_id": str(raw.get("bank_txn_id")),
    }

    if "account_id" in raw:
        data["account_external"] = str(raw["account_id"])

    if raw.get("payee") or raw.get("description"):
        data["description"] = raw.get("description") or raw.get("payee")

    if "mcc" in raw and raw["mcc"] is not None:
        try:
            data["mcc"] = int(raw["mcc"])
        except (TypeError, ValueError):
            pass

    return data


async def process(raw: dict[str, Any]) -> None:
    """Normalize raw data and publish to Kafka."""
    user_id = str(raw.get("user_id"))
    bank_txn_id = str(raw.get("bank_txn_id"))
    try:
        RAW_VALIDATOR.validate(raw)
        payload = dict(raw.get("payload", {}))
        raw_copy = dict(payload)
        payload.setdefault("bank_txn_id", bank_txn_id)
        msg = normalize_record(payload)
        msg.update(
            {
                "txn_id": str(uuid4()),
                "user_id": user_id,
                "bank_id": payload.get("bank_id", "unknown"),
                "raw": raw_copy,
            }
        )
        NORM_VALIDATOR.validate(msg)
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
        msg,
    )
