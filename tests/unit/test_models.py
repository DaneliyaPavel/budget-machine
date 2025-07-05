import pytest
from datetime import datetime, timezone

from uuid import uuid4
from backend.app import models, schemas


def test_account_currency_immutable():
    acc = models.Account(name="Test", currency_code="RUB")
    with pytest.raises(ValueError):
        acc.currency_code = "USD"


def test_transaction_posted_at_tz():
    tx = models.Transaction(
        user_id=uuid4(),
        posted_at=datetime.now(timezone.utc),
    )
    assert tx.posted_at.tzinfo is not None


def test_transaction_create_validators():
    cat_id = uuid4()
    tx = schemas.TransactionCreate(
        posted_at="2025-07-05T12:00:00+00:00",
        category_id=str(cat_id),
    )
    assert isinstance(tx.posted_at, datetime)
    assert tx.category_id == cat_id


def test_transaction_from_orm():
    obj = models.Transaction(
        id=uuid4(),
        user_id=uuid4(),
        posted_at=datetime.now(timezone.utc),
    )
    data = schemas.Transaction.model_validate(obj)
    assert data.id == obj.id
    assert data.posted_at == obj.posted_at
