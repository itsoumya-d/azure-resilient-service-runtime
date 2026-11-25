from runtime.core import CircuitState, ServiceRuntime


def test_endpoint_registration_and_selection():
    runtime = ServiceRuntime()
    primary = runtime.register_endpoint("primary-azure-east", "https://eastus.service.internal", is_primary=True)
    fallback = runtime.register_endpoint("secondary-azure-west", "https://westus.service.internal", is_primary=False)

    active = runtime.select_active_endpoint()
    assert active.name == "primary-azure-east"

    primary.is_healthy = False
    active = runtime.select_active_endpoint()
    assert active.name == "secondary-azure-west"


def test_no_healthy_endpoints_raises():
    runtime = ServiceRuntime()
    runtime.register_endpoint("ep1", "https://ep1.internal", is_primary=True)
    runtime.endpoints["ep1"].is_healthy = False

    try:
        runtime.select_active_endpoint()
        assert False, "Should have raised RuntimeError"
    except RuntimeError:
        pass
