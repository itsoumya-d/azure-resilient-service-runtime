import time
import pytest
from runtime.core import CircuitState, ServiceRuntime
from runtime.circuit import CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_success():
    runtime = ServiceRuntime()
    runtime.register_endpoint("primary", "https://primary.internal", is_primary=True)

    cb = CircuitBreaker(runtime, failure_threshold=2, recovery_time=0.1)

    res = cb.execute(lambda x: x * 2, 5)
    assert res == 10
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_trips_to_open_and_recovers():
    runtime = ServiceRuntime()
    runtime.register_endpoint("primary", "https://primary.internal", is_primary=True)
    runtime.register_endpoint("secondary", "https://secondary.internal", is_primary=False)

    cb = CircuitBreaker(runtime, failure_threshold=2, recovery_time=0.1)

    def failing_call():
        raise ValueError("Downstream timeout")

    # First failure
    with pytest.raises(ValueError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.CLOSED

    # Second failure trips circuit to OPEN
    with pytest.raises(ValueError):
        cb.execute(failing_call)
    assert cb.state == CircuitState.OPEN

    # Immediate call fast-fails with CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        cb.execute(lambda: 123)

    # Wait for recovery timeout
    time.sleep(0.12)

    # Next call executes in HALF_OPEN
    res = cb.execute(lambda: "recovered")
    assert res == "recovered"
    assert cb.state == CircuitState.HALF_OPEN

    # Second success in HALF_OPEN closes circuit
    res2 = cb.execute(lambda: "healthy")
    assert res2 == "healthy"
    assert cb.state == CircuitState.CLOSED
