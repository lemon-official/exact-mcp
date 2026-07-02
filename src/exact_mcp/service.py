"""High-level Exact Online workflows exposed through MCP."""

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from exact_mcp.client import ExactClient
from exact_mcp.errors import AmbiguousMatchError, NotFoundError, ValidationFailedError
from exact_mcp.models import DraftSalesOrderRequest, GoodsDeliveryRequest
from exact_mcp.odata import and_, contains, eq, or_, query_params


class ExactService:
    def __init__(self, client: ExactClient) -> None:
        self.client = client
        self.active_warehouse_id: UUID | None = None

    async def administration_current(self) -> dict[str, Any]:
        user = await self.client.current_user()
        return {
            "division": user.get("CurrentDivision"),
            "user_name": user.get("FullName"),
        }

    async def administrations_list(self) -> list[dict[str, Any]]:
        return await self.client.administrations()

    async def administration_switch(self, division: int) -> dict[str, Any]:
        administrations = await self.client.administrations()
        matches = [item for item in administrations if item.get("Division") == division]
        if not matches:
            raise NotFoundError(f"division {division} is not available to this Exact identity")
        self.client.set_division(division)
        self.active_warehouse_id = None
        return matches[0]

    async def accounts_search(
        self,
        query: str,
        *,
        account_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        filters: list[str] = []
        if query != "*":
            filters.append(
                or_(
                    contains("Name", query),
                    contains("Code", query),
                    contains("City", query),
                    contains("Email", query),
                )
            )
        if account_type == "customer":
            filters.append(eq("IsSales", True))
        elif account_type == "supplier":
            filters.append(eq("IsPurchase", True))
        elif account_type not in {None, ""}:
            raise ValidationFailedError("account_type must be customer or supplier")
        filter_expression = (
            and_(*filters) if len(filters) > 1 else (filters[0] if filters else None)
        )
        allowed = {"ID", "Code", "Name", "City", "Email", "IsSales", "IsPurchase"}
        params = query_params(
            select=("ID", "Code", "Name", "City", "Email"),
            allowed_fields=allowed,
            filter_expression=filter_expression,
            top=limit,
            skip=offset,
        )
        records = await self.client.list("crm/Accounts", params=params)
        items = [
            {
                "id": item.get("ID"),
                "code": item.get("Code"),
                "name": item.get("Name"),
                "city": item.get("City"),
                "email": item.get("Email"),
            }
            for item in records
        ]
        return {"items": items, "limit": limit, "offset": offset, "has_more": len(items) == limit}

    async def items_search(self, query: str, *, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        filter_expression = None
        if query != "*":
            filter_expression = or_(contains("Code", query), contains("Description", query))
        allowed = {"ID", "Code", "Description", "SalesPrice", "IsSalesItem"}
        params = query_params(
            select=("ID", "Code", "Description", "SalesPrice"),
            allowed_fields=allowed,
            filter_expression=filter_expression,
            top=limit,
            skip=offset,
        )
        records = await self.client.list("logistics/Items", params=params)
        return {
            "items": [
                {
                    "id": item.get("ID"),
                    "code": item.get("Code"),
                    "description": item.get("Description"),
                    "sales_price": item.get("SalesPrice"),
                }
                for item in records
            ],
            "limit": limit,
            "offset": offset,
            "has_more": len(records) == limit,
        }

    async def vat_codes_list(self, query: str = "") -> list[dict[str, Any]]:
        filter_expression = contains("Description", query) if query else None
        return await self.client.list(
            "vat/VATCodes",
            params=query_params(
                select=("ID", "Code", "Description", "Percentage"),
                allowed_fields={"ID", "Code", "Description", "Percentage"},
                filter_expression=filter_expression,
                top=60,
            ),
        )

    async def warehouses_list(self) -> list[dict[str, Any]]:
        return await self.client.list(
            "inventory/Warehouses",
            params=query_params(
                select=("ID", "Code", "Description", "UseStorageLocations"),
                allowed_fields={"ID", "Code", "Description", "UseStorageLocations"},
                top=60,
            ),
        )

    async def resolve_customer_id(self, customer: str) -> list[dict[str, Any]]:
        result = await self.accounts_search(customer, account_type="customer")
        return cast(list[dict[str, Any]], result["items"])

    async def sales_orders_get(
        self, *, order_id: UUID | None = None, order_number: str | None = None
    ) -> dict[str, Any]:
        order = await self._resolve_order(order_id, order_number)
        return order

    async def sales_order_lines_search(self, order_id: UUID) -> list[dict[str, Any]]:
        return await self.client.list(
            "salesorder/SalesOrderLines",
            params=query_params(
                select=(
                    "ID",
                    "OrderID",
                    "Item",
                    "ItemCode",
                    "Quantity",
                    "QuantityDelivered",
                ),
                allowed_fields={
                    "ID",
                    "OrderID",
                    "Item",
                    "ItemCode",
                    "Quantity",
                    "QuantityDelivered",
                },
                filter_expression=eq("OrderID", order_id),
                top=60,
            ),
        )

    async def draft_sales_order(self, request: DraftSalesOrderRequest) -> dict[str, Any]:
        customer_id = request.customer_id
        if customer_id is None:
            customer = await self._resolve_code(
                "crm/Accounts",
                "Code",
                request.customer_code or "",
                extra_filter=eq("IsSales", True),
            )
            customer_id = UUID(str(customer["ID"]))

        lines: list[dict[str, Any]] = []
        for requested in request.lines:
            item_id = requested.item_id
            if item_id is None:
                item = await self._resolve_code(
                    "logistics/Items", "Code", requested.item_code or ""
                )
                item_id = UUID(str(item["ID"]))
            line: dict[str, Any] = {
                "Item": str(item_id),
                "Quantity": float(requested.quantity),
            }
            if requested.unit_price is not None:
                line["UnitPrice"] = float(requested.unit_price)
            if requested.description:
                line["Description"] = requested.description
            if requested.vat_code:
                line["VATCode"] = requested.vat_code
            lines.append(line)

        payload: dict[str, Any] = {
            "OrderedBy": str(customer_id),
            "SalesOrderLines": lines,
        }
        if request.delivery_date:
            payload["DeliveryDate"] = request.delivery_date.isoformat()
        if request.description:
            payload["Description"] = request.description
        if request.your_reference:
            payload["YourRef"] = request.your_reference
        if request.remarks:
            payload["Remarks"] = request.remarks
        created = await self.client.request("POST", "salesorder/SalesOrders", json=payload)
        return {
            "id": created.get("OrderID") or created.get("ID"),
            "order_number": created.get("OrderNumber"),
            "status": created.get("Status"),
        }

    async def retrieve_unpaid_invoices(
        self,
        *,
        customer_id: UUID | None = None,
        customer_code: str | None = None,
    ) -> list[dict[str, Any]]:
        if (customer_id is None) == (customer_code is None):
            raise ValidationFailedError("provide exactly one customer_id or customer_code")
        if customer_id is None:
            customer = await self._resolve_code("crm/Accounts", "Code", customer_code or "")
            customer_id = UUID(str(customer["ID"]))
        records = await self.client.list(
            "financial/ReceivablesList",
            params=query_params(
                select=(
                    "ID",
                    "InvoiceID",
                    "InvoiceNumber",
                    "InvoiceDate",
                    "DueDate",
                    "Currency",
                    "Amount",
                    "AmountDC",
                ),
                allowed_fields={
                    "ID",
                    "InvoiceID",
                    "InvoiceNumber",
                    "InvoiceDate",
                    "DueDate",
                    "Currency",
                    "Amount",
                    "AmountDC",
                    "Account",
                },
                filter_expression=eq("Account", customer_id),
                top=60,
            ),
        )
        return [
            {
                "id": item.get("ID"),
                "invoice_id": item.get("InvoiceID"),
                "invoice_number": item.get("InvoiceNumber"),
                "invoice_date": item.get("InvoiceDate"),
                "due_date": item.get("DueDate"),
                "currency": item.get("Currency"),
                "original_amount": item.get("Amount", 0),
                "outstanding_amount": item.get("AmountDC", item.get("Amount", 0)),
            }
            for item in records
        ]

    async def execute_goods_delivery(self, request: GoodsDeliveryRequest) -> dict[str, Any]:
        if not request.confirm:
            raise ValidationFailedError("confirm=true is required because delivery reduces stock")
        order = await self._resolve_order(request.order_id, request.order_number)
        order_id = UUID(str(order.get("OrderID") or order.get("ID")))
        open_lines = await self.sales_order_lines_search(order_id)
        by_id = {str(line.get("ID")): line for line in open_lines}
        by_code = {str(line.get("ItemCode")): line for line in open_lines}

        requested_lines = request.lines
        delivery_lines: list[dict[str, Any]] = []
        if requested_lines is None:
            for line in open_lines:
                remaining = _decimal(line.get("Quantity")) - _decimal(line.get("QuantityDelivered"))
                if remaining > 0:
                    delivery_lines.append(self._delivery_payload(line, remaining))
        else:
            for requested in requested_lines:
                matched_line = (
                    by_id.get(str(requested.order_line_id))
                    if requested.order_line_id
                    else by_code.get(requested.item_code or "")
                )
                if matched_line is None:
                    raise NotFoundError("requested sales order line was not found")
                remaining = _decimal(matched_line.get("Quantity")) - _decimal(
                    matched_line.get("QuantityDelivered")
                )
                if requested.quantity > remaining:
                    raise ValidationFailedError("delivery quantity exceeds the open order quantity")
                delivery = self._delivery_payload(matched_line, requested.quantity)
                if requested.storage_location_id:
                    delivery["StorageLocation"] = str(requested.storage_location_id)
                if requested.batch_number:
                    delivery["BatchNumber"] = requested.batch_number
                if requested.serial_number:
                    delivery["SerialNumber"] = requested.serial_number
                delivery_lines.append(delivery)
        if not delivery_lines:
            raise ValidationFailedError("sales order has no open lines to deliver")
        payload: dict[str, Any] = {
            "OrderID": str(order_id),
            "GoodsDeliveryLines": delivery_lines,
        }
        if request.warehouse_id:
            payload["Warehouse"] = str(request.warehouse_id)
        if request.delivery_date:
            payload["DeliveryDate"] = request.delivery_date.isoformat()
        if request.description:
            payload["Description"] = request.description
        if request.tracking_number:
            payload["TrackingNumber"] = request.tracking_number
        if request.remarks:
            payload["Remarks"] = request.remarks
        created = await self.client.request("POST", "salesorder/GoodsDeliveries", json=payload)
        return {"id": created.get("ID"), "delivery_number": created.get("DeliveryNumber")}

    async def _resolve_order(
        self, order_id: UUID | None, order_number: str | None
    ) -> dict[str, Any]:
        if (order_id is None) == (order_number is None):
            raise ValidationFailedError("provide exactly one order_id or order_number")
        field, value = (
            ("OrderID", order_id) if order_id else ("OrderNumber", int(order_number or 0))
        )
        records = await self.client.list(
            "salesorder/SalesOrders",
            params=query_params(
                select=("OrderID", "OrderNumber", "Status", "OrderedBy"),
                allowed_fields={"OrderID", "OrderNumber", "Status", "OrderedBy"},
                filter_expression=eq(field, value),
                top=2,
            ),
        )
        return self._one(records, f"sales order {value}")

    async def _resolve_code(
        self, path: str, field: str, code: str, *, extra_filter: str | None = None
    ) -> dict[str, Any]:
        filters = [eq(field, code)]
        if extra_filter:
            filters.append(extra_filter)
        records = await self.client.list(
            path,
            params={
                "$select": f"ID,{field},Name,Description",
                "$filter": and_(*filters),
                "$top": "2",
            },
        )
        return self._one(records, f"{field} {code}")

    @staticmethod
    def _one(records: list[dict[str, Any]], label: str) -> dict[str, Any]:
        if not records:
            raise NotFoundError(f"{label} was not found")
        if len(records) > 1:
            raise AmbiguousMatchError(f"{label} matched multiple Exact records")
        return records[0]

    @staticmethod
    def _delivery_payload(line: dict[str, Any], quantity: Decimal) -> dict[str, Any]:
        return {
            "SalesOrderLine": str(line["ID"]),
            "Item": str(line["Item"]),
            "Quantity": float(quantity),
        }


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))
