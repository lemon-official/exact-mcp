from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from exact_mcp.models import (
    DraftSalesOrderRequest,
    EndpointActionRequest,
    EndpointDeleteRequest,
    EndpointFilter,
    EndpointReadRequest,
    EndpointUpdateRequest,
    GoodsDeliveryRequest,
    SalesOrderLineInput,
    SearchRequest,
)


def test_search_requires_two_characters_or_wildcard() -> None:
    with pytest.raises(ValidationError, match="at least 2"):
        SearchRequest(query="x")

    assert SearchRequest(query="*").query == "*"


def test_search_pagination_is_bounded() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(query="acme", limit=61)
    with pytest.raises(ValidationError):
        SearchRequest(query="acme", offset=-1)


def test_order_line_requires_exactly_one_item_identifier() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        SalesOrderLineInput(quantity=1)
    with pytest.raises(ValidationError, match="exactly one"):
        SalesOrderLineInput(item_id=uuid4(), item_code="SKU", quantity=1)


def test_order_line_requires_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        SalesOrderLineInput(item_code="SKU", quantity=Decimal("0"))


def test_draft_order_requires_customer_and_lines() -> None:
    line = SalesOrderLineInput(item_code="SKU", quantity=2)
    with pytest.raises(ValidationError, match="exactly one"):
        DraftSalesOrderRequest(lines=[line])
    with pytest.raises(ValidationError):
        DraftSalesOrderRequest(customer_code="C100", lines=[])


def test_goods_delivery_requires_explicit_confirmation() -> None:
    request = GoodsDeliveryRequest(order_number="10001")

    assert request.confirm is False
    with pytest.raises(ValidationError, match="exactly one"):
        GoodsDeliveryRequest(order_id=uuid4(), order_number="10001", confirm=True)


def test_endpoint_read_request_is_structured_and_bounded() -> None:
    request = EndpointReadRequest(
        endpoint="crm/addresses",
        select=["ID", "City"],
        filters=[EndpointFilter(field="City", operator="eq", value="Amsterdam")],
        order_by=["City"],
        limit=60,
    )

    assert request.filters[0].operator == "eq"
    with pytest.raises(ValidationError):
        EndpointReadRequest(endpoint="https://attacker.example", limit=61)


def test_endpoint_keyed_mutations_require_keys() -> None:
    with pytest.raises(ValidationError):
        EndpointUpdateRequest(endpoint="crm/addresses", key={}, payload={})
    with pytest.raises(ValidationError):
        EndpointDeleteRequest(endpoint="crm/addresses", key={})


def test_endpoint_action_defaults_to_unconfirmed() -> None:
    request = EndpointActionRequest(endpoint="crm/acceptquotation", payload={"ID": "1"})

    assert request.confirm is False
