"""FastMCP adapter for the Exact Online domain service."""

import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from exact_mcp.auth import OAuthManager
from exact_mcp.client import ExactClient
from exact_mcp.config import Settings
from exact_mcp.errors import ExactMCPError
from exact_mcp.logging import redact
from exact_mcp.models import (
    DraftSalesOrderRequest,
    EndpointActionRequest,
    EndpointCreateRequest,
    EndpointDeleteRequest,
    EndpointReadRequest,
    EndpointUpdateRequest,
    GoodsDeliveryRequest,
)
from exact_mcp.rate_limit import RateLimiter
from exact_mcp.service import ExactService
from exact_mcp.tokens import EncryptedFileTokenStore

logger = logging.getLogger(__name__)


async def _operation_call[T](
    kind: str,
    name: str,
    operation: Callable[[], Awaitable[T]],
    *,
    arguments: Any = None,
) -> T:
    started = time.perf_counter()
    logger.info("mcp_operation_started kind=%s name=%s", kind, name)
    logger.debug(
        "mcp_operation_arguments kind=%s name=%s arguments=%r",
        kind,
        name,
        redact(arguments if arguments is not None else {}),
    )
    try:
        result = await operation()
    except ExactMCPError as exc:
        duration_ms = (time.perf_counter() - started) * 1000
        logger.error(
            "mcp_operation_failed kind=%s name=%s duration_ms=%.2f code=%s "
            "retryable=%s details=%r message=%s",
            kind,
            name,
            duration_ms,
            exc.code,
            exc.retryable,
            redact(exc.details),
            redact(exc.message),
        )
        raise ToolError(json.dumps(exc.as_dict())) from exc
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "mcp_operation_crashed kind=%s name=%s duration_ms=%.2f",
            kind,
            name,
            duration_ms,
        )
        raise
    duration_ms = (time.perf_counter() - started) * 1000
    item_count = len(result) if isinstance(result, (dict, list, tuple)) else None
    logger.info(
        "mcp_operation_completed kind=%s name=%s duration_ms=%.2f result_type=%s item_count=%s",
        kind,
        name,
        duration_ms,
        type(result).__name__,
        item_count,
    )
    logger.debug(
        "mcp_operation_result kind=%s name=%s result=%r",
        kind,
        name,
        redact(result),
    )
    return result


def create_server(
    service: ExactService,
    *,
    settings: Settings | None = None,
    close_on_exit: bool = False,
) -> FastMCP:
    """Create an MCP server around an injected Exact service."""

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[ExactService]:
        del server
        logger.info("mcp_lifespan_started close_on_exit=%s", close_on_exit)
        try:
            yield service
        finally:
            if close_on_exit:
                logger.info("exact_http_client_closing")
                await service.client.close()
            logger.info("mcp_lifespan_stopped")

    server = FastMCP(
        "Exact Online",
        instructions=(
            "Use read-only discovery tools before mutations. "
            "Goods delivery requires explicit confirmation and reduces stock."
        ),
        host=settings.host if settings else "127.0.0.1",
        port=settings.port if settings else 8000,
        json_response=True,
        stateless_http=True,
        lifespan=lifespan,
    )
    read_only = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True)
    mutating = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
    destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    )

    @server.tool(annotations=read_only)
    async def resolve_customer_id(
        customer: str,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """Find Exact customer IDs by name or code. This tool is read-only."""
        return await _operation_call(
            "tool",
            "resolve_customer_id",
            lambda: service.resolve_customer_id(customer),
            arguments={"customer": customer, "context": context},
        )

    @server.tool(annotations=mutating)
    async def draft_sales_order(request: DraftSalesOrderRequest) -> dict[str, Any]:
        """Create a draft sales order after resolving all customer and item identifiers."""
        return await _operation_call(
            "tool",
            "draft_sales_order",
            lambda: service.draft_sales_order(request),
            arguments={"request": request},
        )

    @server.tool(annotations=read_only)
    async def retrieve_unpaid_invoices(
        customer_id: UUID | None = None,
        customer_code: str | None = None,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """Retrieve normalized outstanding receivables for one customer."""
        return await _operation_call(
            "tool",
            "retrieve_unpaid_invoices",
            lambda: service.retrieve_unpaid_invoices(
                customer_id=customer_id,
                customer_code=customer_code,
            ),
            arguments={
                "customer_id": customer_id,
                "customer_code": customer_code,
                "context": context,
            },
        )

    @server.tool(annotations=destructive)
    async def execute_goods_delivery(request: GoodsDeliveryRequest) -> dict[str, Any]:
        """Post a goods delivery. Requires confirm=true and reduces Exact stock."""
        return await _operation_call(
            "tool",
            "execute_goods_delivery",
            lambda: service.execute_goods_delivery(request),
            arguments={"request": request},
        )

    @server.tool(annotations=read_only)
    async def administrations_list(context: str = "") -> list[dict[str, Any]]:
        """List Exact administrations available to the authenticated identity."""
        return await _operation_call(
            "tool",
            "administrations_list",
            service.administrations_list,
            arguments={"context": context},
        )

    @server.tool(annotations=read_only)
    async def administration_current(context: str = "") -> dict[str, Any]:
        """Return the active Exact administration."""
        return await _operation_call(
            "tool",
            "administration_current",
            service.administration_current,
            arguments={"context": context},
        )

    @server.tool(annotations=read_only)
    async def administration_switch(division: int, context: str = "") -> dict[str, Any]:
        """Switch active administration after validating access."""
        return await _operation_call(
            "tool",
            "administration_switch",
            lambda: service.administration_switch(division),
            arguments={"division": division, "context": context},
        )

    @server.tool(annotations=read_only)
    async def accounts_search(
        query: str,
        account_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
        context: str = "",
    ) -> dict[str, Any]:
        """Search Exact customers or suppliers using a bounded server-built query."""
        return await _operation_call(
            "tool",
            "accounts_search",
            lambda: service.accounts_search(
                query,
                account_type=account_type,
                limit=limit,
                offset=offset,
            ),
            arguments={
                "query": query,
                "account_type": account_type,
                "limit": limit,
                "offset": offset,
                "context": context,
            },
        )

    @server.tool(annotations=read_only)
    async def items_search(
        query: str,
        limit: int = 20,
        offset: int = 0,
        context: str = "",
    ) -> dict[str, Any]:
        """Search Exact items by code or description."""
        return await _operation_call(
            "tool",
            "items_search",
            lambda: service.items_search(query, limit=limit, offset=offset),
            arguments={"query": query, "limit": limit, "offset": offset, "context": context},
        )

    @server.tool(annotations=read_only)
    async def vat_codes_list(query: str = "", context: str = "") -> list[dict[str, Any]]:
        """List configured VAT codes and percentages."""
        return await _operation_call(
            "tool",
            "vat_codes_list",
            lambda: service.vat_codes_list(query),
            arguments={"query": query, "context": context},
        )

    @server.tool(annotations=read_only)
    async def warehouses_list(context: str = "") -> list[dict[str, Any]]:
        """List warehouses and storage-location configuration."""
        return await _operation_call(
            "tool",
            "warehouses_list",
            service.warehouses_list,
            arguments={"context": context},
        )

    @server.tool(annotations=read_only)
    async def sales_orders_get(
        order_id: UUID | None = None,
        order_number: str | None = None,
        context: str = "",
    ) -> dict[str, Any]:
        """Get one sales order by ID or order number."""
        return await _operation_call(
            "tool",
            "sales_orders_get",
            lambda: service.sales_orders_get(order_id=order_id, order_number=order_number),
            arguments={
                "order_id": order_id,
                "order_number": order_number,
                "context": context,
            },
        )

    @server.tool(annotations=read_only)
    async def sales_order_lines_search(
        order_id: UUID,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """List sales-order lines for one order."""
        return await _operation_call(
            "tool",
            "sales_order_lines_search",
            lambda: service.sales_order_lines_search(order_id),
            arguments={"order_id": order_id, "context": context},
        )

    @server.tool(annotations=read_only)
    async def exact_endpoints_list(
        service_name: str | None = None,
        method: str | None = None,
        query: str = "",
        limit: int = 50,
        offset: int = 0,
        context: str = "",
    ) -> dict[str, Any]:
        """Discover registered Exact endpoint IDs before using the generic gateway."""

        async def call() -> dict[str, Any]:
            return service.endpoints_list(
                service=service_name,
                method=method,
                query=query,
                limit=limit,
                offset=offset,
            )

        return await _operation_call(
            "tool",
            "exact_endpoints_list",
            call,
            arguments={
                "service": service_name,
                "method": method,
                "query": query,
                "limit": limit,
                "offset": offset,
                "context": context,
            },
        )

    @server.tool(annotations=read_only)
    async def exact_endpoint_read(request: EndpointReadRequest) -> dict[str, Any]:
        """Read one registered Exact resource using structured OData inputs."""
        return await _operation_call(
            "tool",
            "exact_endpoint_read",
            lambda: service.endpoint_read(request),
            arguments={"request": request},
        )

    @server.tool(annotations=mutating)
    async def exact_endpoint_create(request: EndpointCreateRequest) -> dict[str, Any]:
        """Create a record on a registered Exact resource; confirm=true is required."""
        return await _operation_call(
            "tool",
            "exact_endpoint_create",
            lambda: service.endpoint_create(request),
            arguments={"request": request},
        )

    @server.tool(annotations=mutating)
    async def exact_endpoint_update(request: EndpointUpdateRequest) -> dict[str, Any]:
        """Update a keyed record on a registered Exact resource; confirmation is required."""
        return await _operation_call(
            "tool",
            "exact_endpoint_update",
            lambda: service.endpoint_update(request),
            arguments={"request": request},
        )

    @server.tool(annotations=destructive)
    async def exact_endpoint_delete(request: EndpointDeleteRequest) -> dict[str, Any]:
        """Delete a keyed Exact record; confirm=true is required."""
        return await _operation_call(
            "tool",
            "exact_endpoint_delete",
            lambda: service.endpoint_delete(request),
            arguments={"request": request},
        )

    @server.tool(annotations=destructive)
    async def exact_endpoint_action(request: EndpointActionRequest) -> dict[str, Any]:
        """Execute a registered POST-only Exact action; confirm=true is required."""
        return await _operation_call(
            "tool",
            "exact_endpoint_action",
            lambda: service.endpoint_action(request),
            arguments={"request": request},
        )

    @server.resource("exact://health")
    async def health() -> str:
        """Return process health without contacting Exact Online."""

        async def read_health() -> str:
            return json.dumps({"status": "ok", "service": "exact-online-mcp"})

        return await _operation_call("resource", "health", read_health)

    @server.resource("exact://routing/current")
    async def routing_current() -> str:
        """Return the current Exact administration routing state."""
        result = await _operation_call(
            "resource",
            "routing_current",
            service.administration_current,
        )
        return json.dumps(result, default=str)

    return server


def build_server(settings: Settings) -> FastMCP:
    """Construct production dependencies and the FastMCP server."""
    http = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
    store = EncryptedFileTokenStore(
        settings.token_file,
        settings.token_encryption_key.get_secret_value().encode(),
    )
    oauth = OAuthManager(
        client_id=settings.exact_client_id,
        client_secret=settings.exact_client_secret.get_secret_value(),
        redirect_uri=str(settings.exact_redirect_uri),
        authorize_url=str(settings.exact_authorize_url),
        token_url=str(settings.exact_token_url),
        store=store,
        http=http,
        refresh_skew_seconds=settings.refresh_skew_seconds,
    )
    limiter = RateLimiter(reserve=settings.rate_reserve)
    client = ExactClient(
        str(settings.exact_api_base),
        oauth,
        http=http,
        limiter=limiter,
        max_retries=settings.max_retries,
        max_pages=settings.max_pages,
        max_records=settings.max_records,
    )
    return create_server(
        ExactService(client),
        settings=settings,
        close_on_exit=True,
    )
