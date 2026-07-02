from typing import Any
from uuid import uuid4

import pytest

from exact_mcp.errors import AmbiguousMatchError, ValidationFailedError
from exact_mcp.models import (
    DraftSalesOrderRequest,
    GoodsDeliveryRequest,
    SalesOrderLineInput,
)
from exact_mcp.service import ExactService


class FakeClient:
    def __init__(self) -> None:
        self.division = 123
        self.lists: dict[str, list[dict[str, Any]]] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def current_user(self) -> dict[str, Any]:
        return {"CurrentDivision": self.division, "FullName": "Test User"}

    async def administrations(self) -> list[dict[str, Any]]:
        return self.lists.get("system/Divisions", [])

    def set_division(self, division: int) -> None:
        self.division = division

    async def list(
        self, path: str, *, params: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        self.calls.append(("GET", path, {"params": params or {}}))
        return self.lists.get(path, [])

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        division_scoped: bool = True,
    ) -> Any:
        self.calls.append((method, path, {"params": params or {}, "json": json or {}}))
        return {"ID": str(uuid4()), "OrderNumber": 1001}


@pytest.mark.asyncio
async def test_account_search_is_bounded_and_server_constructed() -> None:
    client = FakeClient()
    client.lists["crm/Accounts"] = [
        {"ID": str(uuid4()), "Code": "C100", "Name": "Acme", "City": "A", "Email": "a@x"}
    ]
    service = ExactService(client)  # type: ignore[arg-type]

    result = await service.accounts_search("Acme", account_type="customer", limit=20, offset=0)

    params = client.calls[0][2]["params"]
    assert params["$top"] == "20"
    assert params["$skip"] == "0"
    assert "substringof('Acme', Name)" in params["$filter"]
    assert "IsSales eq true" in params["$filter"]
    assert result["items"][0]["code"] == "C100"


@pytest.mark.asyncio
async def test_draft_sales_order_resolves_all_codes_before_one_post() -> None:
    customer_id, item_id = uuid4(), uuid4()
    client = FakeClient()
    client.lists["crm/Accounts"] = [{"ID": str(customer_id), "Code": "C100", "Name": "Acme"}]
    client.lists["logistics/Items"] = [{"ID": str(item_id), "Code": "SKU1", "Description": "Item"}]
    service = ExactService(client)  # type: ignore[arg-type]

    result = await service.draft_sales_order(
        DraftSalesOrderRequest(
            customer_code="C100",
            lines=[SalesOrderLineInput(item_code="SKU1", quantity=2)],
        )
    )

    assert [call[0] for call in client.calls] == ["GET", "GET", "POST"]
    post = client.calls[-1]
    assert post[1] == "salesorder/SalesOrders"
    assert post[2]["json"]["OrderedBy"] == str(customer_id)
    assert post[2]["json"]["SalesOrderLines"] == [{"Item": str(item_id), "Quantity": 2.0}]
    assert result["order_number"] == 1001


@pytest.mark.asyncio
async def test_draft_order_rejects_ambiguous_customer_before_post() -> None:
    client = FakeClient()
    client.lists["crm/Accounts"] = [
        {"ID": str(uuid4()), "Code": "C100", "Name": "One"},
        {"ID": str(uuid4()), "Code": "C100", "Name": "Two"},
    ]
    service = ExactService(client)  # type: ignore[arg-type]

    with pytest.raises(AmbiguousMatchError):
        await service.draft_sales_order(
            DraftSalesOrderRequest(
                customer_code="C100",
                lines=[SalesOrderLineInput(item_code="SKU1", quantity=1)],
            )
        )
    assert all(call[0] != "POST" for call in client.calls)


@pytest.mark.asyncio
async def test_retrieve_unpaid_invoices_normalizes_amounts() -> None:
    account_id = uuid4()
    client = FakeClient()
    client.lists["crm/Accounts"] = [{"ID": str(account_id), "Code": "C100", "Name": "Acme"}]
    client.lists["financial/ReceivablesList"] = [
        {
            "ID": str(uuid4()),
            "InvoiceNumber": 42,
            "Amount": 120.5,
            "AmountDC": 20.5,
            "Currency": "EUR",
        }
    ]
    service = ExactService(client)  # type: ignore[arg-type]

    result = await service.retrieve_unpaid_invoices(customer_code="C100")

    assert result[0]["invoice_number"] == 42
    assert result[0]["original_amount"] == 120.5
    assert result[0]["outstanding_amount"] == 20.5


@pytest.mark.asyncio
async def test_delivery_requires_confirmation_before_reads_or_writes() -> None:
    client = FakeClient()
    service = ExactService(client)  # type: ignore[arg-type]

    with pytest.raises(ValidationFailedError, match="confirm"):
        await service.execute_goods_delivery(GoodsDeliveryRequest(order_number="1001"))
    assert client.calls == []


@pytest.mark.asyncio
async def test_delivery_resolves_open_lines_and_posts_once() -> None:
    order_id, line_id, item_id = uuid4(), uuid4(), uuid4()
    client = FakeClient()
    client.lists["salesorder/SalesOrders"] = [{"OrderID": str(order_id), "OrderNumber": 1001}]
    client.lists["salesorder/SalesOrderLines"] = [
        {
            "ID": str(line_id),
            "Item": str(item_id),
            "ItemCode": "SKU1",
            "Quantity": 5,
            "QuantityDelivered": 2,
        }
    ]
    service = ExactService(client)  # type: ignore[arg-type]

    await service.execute_goods_delivery(GoodsDeliveryRequest(order_number="1001", confirm=True))

    assert [call[0] for call in client.calls] == ["GET", "GET", "POST"]
    payload = client.calls[-1][2]["json"]
    assert payload["GoodsDeliveryLines"] == [
        {"SalesOrderLine": str(line_id), "Item": str(item_id), "Quantity": 3.0}
    ]
