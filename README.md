# azure-resilient-service-runtime

Resilient cloud service runtime for Azure high-availability microservices: health probes, circuit breaker, failover routing, and telemetry audit.

## Architecture & Features
- **High Availability Probe**: Liveness, readiness, and latency telemetry for multi-region cloud services.
- **Circuit Breaker**: Three-state pattern (Closed, Open, Half-Open) preventing cascading failures during downstream outages.
- **Automated Failover Dispatch**: Dynamic routing to primary and secondary cloud endpoints with latency-based fallback.
- **Audit Telemetry**: Cryptographically verifiable event logging for distributed system state transitions.

## Testing
```bash
pytest -v
```
