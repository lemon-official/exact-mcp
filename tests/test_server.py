import logging
from typing import Any

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from exact_mcp.errors import ExactAPIError
from exact_mcp.server import create_server


class StubService:
    async def resolve_customer_id(self, customer: str) -> list[dict[str, Any]]:
        return [{"id": "customer-id", "name": customer}]

    async def administration_current(self) -> dict[str, Any]:
        return {"division": 123}


@pytest.mark.asyncio
async def test_server_advertises_prd_tools_with_safety_annotations() -> None:
    server = create_server(StubService())  # type: ignore[arg-type]

    tools = {tool.name: tool for tool in await server.list_tools()}

    assert {
        "resolve_customer_id",
        "draft_sales_order",
        "retrieve_unpaid_invoices",
        "execute_goods_delivery",
    } <= tools.keys()
    assert tools["resolve_customer_id"].annotations.readOnlyHint is True
    assert tools["execute_goods_delivery"].annotations.destructiveHint is True


@pytest.mark.asyncio
async def test_server_calls_service_and_has_health_resource() -> None:
    server = create_server(StubService())  # type: ignore[arg-type]

    result = await server.call_tool("resolve_customer_id", {"customer": "Acme"})
    resources = {str(resource.uri) for resource in await server.list_resources()}

    assert result[1] == {"result": [{"id": "customer-id", "name": "Acme"}]}
    assert "exact://health/" in resources or "exact://health" in resources


@pytest.mark.asyncio
async def test_server_logs_sanitized_tool_arguments_and_results(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="exact_mcp.server")
    server = create_server(StubService())  # type: ignore[arg-type]

    await server.call_tool("resolve_customer_id", {"customer": "Bearer tool-secret"})

    output = caplog.text
    assert "mcp_operation_started kind=tool name=resolve_customer_id" in output
    assert "mcp_operation_arguments kind=tool name=resolve_customer_id" in output
    assert "mcp_operation_completed kind=tool name=resolve_customer_id" in output
    assert "duration_ms=" in output
    assert "tool-secret" not in output
    assert "<redacted>" in output


@pytest.mark.asyncio
async def test_server_logs_safe_tool_errors(caplog: pytest.LogCaptureFixture) -> None:
    class FailingService(StubService):
        async def resolve_customer_id(self, customer: str) -> list[dict[str, Any]]:
            del customer
            raise ExactAPIError(
                "Exact request failed",
                status_code=403,
                request_id="request-123",
            )

    caplog.set_level(logging.DEBUG, logger="exact_mcp.server")
    server = create_server(FailingService())  # type: ignore[arg-type]

    with pytest.raises(ToolError):
        await server.call_tool("resolve_customer_id", {"customer": "Acme"})

    assert "mcp_operation_failed kind=tool name=resolve_customer_id" in caplog.text
    assert "exact_api_error" in caplog.text
    assert "request-123" in caplog.text
