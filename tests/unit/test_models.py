import pytest

from backend.app import models


def test_account_currency_immutable():
    acc = models.Account(name="Test", currency_code="RUB")
    with pytest.raises(ValueError):
        acc.currency_code = "USD"


from datetime import datetime, timezone


def test_transaction_created_at_tz():
    tx = models.Transaction(
        amount=10,
        currency="RUB",
        amount_rub=10,
        created_at=datetime.now(timezone.utc),
    )
    assert tx.created_at.tzinfo is not None
