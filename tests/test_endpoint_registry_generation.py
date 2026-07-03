from pathlib import Path

from scripts.generate_endpoint_registry import build_registry, parse_catalog


def test_parse_catalog_deduplicates_and_resolves_function_routes(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.md"
    catalog.write_text(
        """
## CRM
| Resource | URI | Methods |
| --- | --- | --- |
| Addresses | `/api/v1/{division}/crm/Addresses` | GET, POST |
| Addresses | `/api/v1/{division}/crm/Addresses` | GET, POST |
## CustomField
| CustomFields | `CustomFields - Function Details` | GET |
"""
    )

    rows = parse_catalog(catalog)

    assert [(row.service, row.resource, row.uri, row.methods) for row in rows] == [
        ("CRM", "Addresses", "/api/v1/{division}/crm/Addresses", ("GET", "POST")),
        (
            "CustomField",
            "CustomFields",
            "/api/v1/{division}/customfield/CustomFields",
            ("GET",),
        ),
    ]


def test_build_registry_excludes_resources_already_used_by_mcp(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.md"
    catalog.write_text(
        """
## CRM
| Resource | URI | Methods |
| --- | --- | --- |
| Accounts | `/api/v1/{division}/crm/Accounts` | GET, POST, PUT, DELETE |
| Addresses | `/api/v1/{division}/crm/Addresses` | GET, POST, PUT, DELETE |
## Cashflow
| AllocationRule | `/api/v1/beta/{division}/cashflow/AllocationRule` | GET, POST, PUT, DELETE |
"""
    )

    registry = build_registry(parse_catalog(catalog))

    assert [item["id"] for item in registry] == ["cashflow/allocationrule", "crm/addresses"]
    assert registry[0]["methods"] == ["GET"]
    assert registry[1]["methods"] == ["GET", "POST", "PUT", "DELETE"]
