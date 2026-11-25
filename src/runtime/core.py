from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
import time


@dataclass
class ServiceEndpoint:
    name: str
    url: str
    is_primary: bool = True
    is_healthy: bool = True
    consecutive_failures: int = 0
    last_checked_at: datetime | None = None
    latency_ms: float = 0.0


class CircuitState:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class ServiceAuditEntry:
    timestamp: datetime
    endpoint_name: str
    action: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


class ServiceRuntime:
    """Core runtime managing high-availability endpoints and circuit telemetry."""

    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: float = 10.0) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self.endpoints: dict[str, ServiceEndpoint] = {}
        self.audit_log: list[ServiceAuditEntry] = []
        self.state = CircuitState.CLOSED
        self.last_state_change: float = time.time()

    def register_endpoint(self, name: str, url: str, is_primary: bool = True) -> ServiceEndpoint:
        ep = ServiceEndpoint(name=name, url=url, is_primary=is_primary)
        self.endpoints[name] = ep
        return ep

    def get_primary_endpoint(self) -> ServiceEndpoint | None:
        return next((ep for ep in self.endpoints.values() if ep.is_primary and ep.is_healthy), None)

    def get_fallback_endpoint(self) -> ServiceEndpoint | None:
        return next((ep for ep in self.endpoints.values() if not ep.is_primary and ep.is_healthy), None)

    def select_active_endpoint(self) -> ServiceEndpoint:
        primary = self.get_primary_endpoint()
        if primary:
            return primary
        fallback = self.get_fallback_endpoint()
        if fallback:
            return fallback
        raise RuntimeError("No healthy service endpoints available in runtime pool")
