from __future__ import annotations

import time
from typing import Any, Callable
from runtime.core import CircuitState, ServiceAuditEntry, ServiceEndpoint, ServiceRuntime


class CircuitBreakerOpenError(RuntimeError):
    """Raised when an operation is attempted while the circuit is OPEN."""
    pass


class CircuitBreaker:
    """Three-state circuit breaker pattern implementation for cloud microservice calls."""

    def __init__(self, runtime: ServiceRuntime, failure_threshold: int = 3, recovery_time: float = 1.0) -> None:
        self.runtime = runtime
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: float = 0.0

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        now = time.time()

        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_time:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit is OPEN; fast-failing request")

        endpoint = self.runtime.select_active_endpoint()

        try:
            start_t = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start_t) * 1000.0

            self._record_success(endpoint, elapsed)
            return result
        except Exception as e:
            self._record_failure(endpoint, str(e))
            raise

    def _record_success(self, endpoint: ServiceEndpoint, latency_ms: float) -> None:
        endpoint.consecutive_failures = 0
        endpoint.is_healthy = True
        endpoint.latency_ms = round(latency_ms, 2)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0

    def _record_failure(self, endpoint: ServiceEndpoint, reason: str) -> None:
        self.failure_count += 1
        endpoint.consecutive_failures += 1
        self.last_failure_time = time.time()

        if endpoint.consecutive_failures >= self.failure_threshold:
            endpoint.is_healthy = False

        if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
