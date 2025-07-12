import time
import pytest

from services.bank_bridge.limits import CircuitBreaker, get_limits


class DummyGauge:
    def __init__(self) -> None:
        self.values: list[tuple[str, float]] = []

    def labels(self, bank: str):
        gauge = self

        class Child:
            def set(self, value: float):
                gauge.values.append((bank, value))

        return Child()


def test_get_limits_invalid_env(monkeypatch):
    monkeypatch.setenv("BANK_BRIDGE_FAKE_RATE", "bad")
    monkeypatch.setenv("BANK_BRIDGE_FAKE_CAPACITY", "also_bad")
    rate, capacity = get_limits("fake", rate=2.0, capacity=4)
    assert rate == 2.0
    assert capacity == 4


@pytest.mark.asyncio
async def test_circuit_breaker_before_request():
    gauge = DummyGauge()
    cb = CircuitBreaker(failures=1, reset_timeout=10.0, bank="b", gauge=gauge)
    await cb.failure()
    assert gauge.values == [("b", 1)]
    with pytest.raises(RuntimeError):
        await cb.before_request()

    # After timeout circuit should reset
    cb._opened = time.monotonic() - 11.0
    await cb.before_request()
    assert ("b", 0) in gauge.values
    assert cb._count == 0
    assert cb._opened == 0.0
