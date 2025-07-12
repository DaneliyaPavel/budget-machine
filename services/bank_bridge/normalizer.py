from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import json
from jsonschema import Draft202012Validator
import os


from . import kafka

NORM_TOPIC = os.getenv("BANK_NORM_TOPIC", "bank.norm")
ERR_TOPIC = os.getenv("BANK_ERR_TOPIC", "bank.err")

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
    payload = dict(raw.get("payload", {}))
    try:
        RAW_VALIDATOR.validate(raw)
        raw_copy = dict(payload)
        payload.setdefault("bank_txn_id", bank_txn_id)
        msg = normalize_record(payload)
        msg.update(
            {
                "txn_id": str(uuid4()),
                "user_id": user_id,
                "bank_id": raw.get("bank_id"),
                "raw": raw_copy,
            }
        )
        NORM_VALIDATOR.validate(msg)
    except Exception:  # pragma: no cover - simple error path
        err = {
            "user_id": user_id,
            "external_id": bank_txn_id,
            "bank_id": raw.get("bank_id"),
            "error_code": "INVALID_DATA",
            "stage": "normalize",
            "payload": payload,
        }
        await kafka.publish(ERR_TOPIC, user_id, bank_txn_id, err)
        return

    await kafka.publish(
        NORM_TOPIC,
        user_id,
        bank_txn_id,
        msg,
    )
