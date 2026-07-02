"""Small safe builders for server-owned OData v3 expressions."""

from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def literal(value: str | bool | int | Decimal | UUID | date | datetime | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, UUID):
        return f"guid'{value}'"
    if isinstance(value, datetime):
        return f"datetime'{value.isoformat()}'"
    if isinstance(value, date):
        return f"datetime'{value.isoformat()}T00:00:00'"
    if isinstance(value, str):
        return quote(value)
    return str(value)


def eq(field: str, value: str | bool | int | Decimal | UUID | date | datetime | None) -> str:
    return f"{field} eq {literal(value)}"


def startswith(field: str, value: str) -> str:
    return f"startswith({field}, {quote(value)})"


def contains(field: str, value: str) -> str:
    return f"substringof({quote(value)}, {field})"


def _join(operator: str, expressions: Iterable[str]) -> str:
    parts = [f"({part})" for part in expressions if part]
    if not parts:
        raise ValueError("at least one filter expression is required")
    return f" {operator} ".join(parts)


def and_(*expressions: str) -> str:
    return _join("and", expressions)


def or_(*expressions: str) -> str:
    return _join("or", expressions)


def query_params(
    *,
    select: Iterable[str],
    allowed_fields: set[str],
    filter_expression: str | None = None,
    top: int = 20,
    skip: int = 0,
    order_by: str | None = None,
) -> dict[str, str]:
    fields = tuple(select)
    unknown = set(fields) - allowed_fields
    if unknown:
        raise ValueError(f"fields are not allowed: {', '.join(sorted(unknown))}")
    if not 1 <= top <= 60:
        raise ValueError("top must be between 1 and 60")
    if skip < 0:
        raise ValueError("skip must be non-negative")
    if order_by is not None and order_by not in allowed_fields:
        raise ValueError(f"order field is not allowed: {order_by}")

    params = {"$select": ",".join(fields), "$top": str(top), "$skip": str(skip)}
    if filter_expression:
        params["$filter"] = filter_expression
    if order_by:
        params["$orderby"] = order_by
    return params
