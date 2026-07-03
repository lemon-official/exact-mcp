#!/usr/bin/env python3
"""Generate the checked-in Exact endpoint registry from the endpoint catalogue."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

METHOD_ORDER = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3}

FUNCTION_ROUTES = {
    "CustomFields - Function Details": "/api/v1/{division}/customfield/CustomFields",
    "UpdateCustomField - Function Details": "/api/v1/{division}/customfield/UpdateCustomField",
    "GetSharePointDocumentUrl - Function Details": (
        "/api/v1/{division}/documents/GetSharePointDocumentUrl"
    ),
}

# A resource is outside this registry when any operation is already represented by a
# curated MCP workflow. This intentionally leaves partially covered resources alone.
EXISTING_RESOURCE_URIS = {
    "/api/v1/current/Me",
    "/api/v1/{division}/system/Divisions",
    "/api/v1/{division}/crm/Accounts",
    "/api/v1/{division}/logistics/Items",
    "/api/v1/{division}/vat/VATCodes",
    "/api/v1/{division}/inventory/Warehouses",
    "/api/v1/{division}/salesorder/SalesOrderLines",
    "/api/v1/{division}/salesorder/SalesOrders",
    "/api/v1/{division}/read/financial/ReceivablesList",
    "/api/v1/{division}/salesorder/GoodsDeliveries",
}


@dataclass(frozen=True)
class CatalogRow:
    service: str
    resource: str
    uri: str
    methods: tuple[str, ...]


def parse_catalog(path: Path) -> list[CatalogRow]:
    """Parse and de-duplicate Markdown endpoint tables by URI."""
    service = ""
    rows: dict[str, CatalogRow] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            service = line[3:].strip()
            continue
        if not line.startswith("|") or "`" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        uri_match = re.search(r"`([^`]+)`", cells[1])
        if uri_match is None:
            continue
        uri = FUNCTION_ROUTES.get(uri_match.group(1), uri_match.group(1))
        methods = tuple(
            sorted(
                {method.strip().upper() for method in cells[2].split(",")},
                key=METHOD_ORDER.__getitem__,
            )
        )
        rows[uri] = CatalogRow(service, cells[0], uri, methods)
    return list(rows.values())


def endpoint_id(uri: str) -> str:
    for prefix in ("/api/v1/{division}/", "/api/v1/beta/{division}/"):
        if uri.startswith(prefix):
            return uri.removeprefix(prefix).lower()
    if uri == "/api/v1/current/Me":
        return "current/me"
    raise ValueError(f"unsupported Exact URI template: {uri}")


def build_registry(rows: list[CatalogRow]) -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for row in rows:
        if row.uri in EXISTING_RESOURCE_URIS:
            continue
        methods = row.methods
        if row.uri == "/api/v1/beta/{division}/cashflow/AllocationRule":
            methods = ("GET",)
        registry.append(
            {
                "id": endpoint_id(row.uri),
                "service": row.service,
                "resource": row.resource,
                "uri_template": row.uri,
                "methods": list(methods),
                "post_only_action": methods == ("POST",),
                "key_fields": [],
                "readable_fields": [],
                "post_fields": [],
                "put_fields": [],
                "parameters": [],
            }
        )
    return sorted(registry, key=lambda item: str(item["id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    registry = build_registry(parse_catalog(args.catalog))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    operation_count = sum(len(item["methods"]) for item in registry)
    print(f"wrote {len(registry)} resources and {operation_count} operations")


if __name__ == "__main__":
    main()
