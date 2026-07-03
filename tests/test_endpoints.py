from dataclasses import FrozenInstanceError

import pytest

from exact_mcp.endpoints import EndpointRegistry, EndpointSpec, load_registry
from exact_mcp.errors import NotFoundError, ValidationFailedError


def test_checked_in_registry_has_approved_inventory() -> None:
    registry = load_registry()

    assert len(registry) == 330
    assert sum(len(item.methods) for item in registry) == 639
    assert len({item.id for item in registry}) == 330
    assert registry.get("customfield/customfields").uri_template == (
        "/api/v1/{division}/customfield/CustomFields"
    )


def test_endpoint_specs_are_immutable_and_reject_unsafe_templates() -> None:
    spec = EndpointSpec(
        id="crm/addresses",
        service="CRM",
        resource="Addresses",
        uri_template="/api/v1/{division}/crm/Addresses",
        methods=("GET",),
    )

    with pytest.raises(FrozenInstanceError):
        spec.id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationFailedError, match="template"):
        EndpointSpec(
            id="bad",
            service="Bad",
            resource="Bad",
            uri_template="https://attacker.example/api/v1/Bad",
            methods=("GET",),
        )


def test_registry_discovery_and_lookup_are_bounded() -> None:
    registry = load_registry()

    result = registry.search(service="CRM", method="GET", query="quotation", limit=2, offset=1)

    assert result["limit"] == 2
    assert result["offset"] == 1
    assert len(result["items"]) <= 2
    assert all("quotation" in item["id"] for item in result["items"])
    with pytest.raises(NotFoundError, match="endpoint"):
        registry.get("crm/does-not-exist")


def test_registry_rejects_duplicate_ids() -> None:
    item = EndpointSpec(
        id="crm/addresses",
        service="CRM",
        resource="Addresses",
        uri_template="/api/v1/{division}/crm/Addresses",
        methods=("GET",),
    )
    with pytest.raises(ValidationFailedError, match="duplicate"):
        EndpointRegistry((item, item))
