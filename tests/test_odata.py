from uuid import UUID

import pytest

from exact_mcp.odata import (
    and_,
    comparison,
    contains,
    eq,
    key_predicate,
    or_,
    query_params,
    quote,
    startswith,
)


def test_quote_escapes_odata_string_literals() -> None:
    assert quote("O'Brien") == "'O''Brien'"


def test_filter_helpers_compose_parenthesized_expressions() -> None:
    expression = and_(
        or_(startswith("Name", "Acme"), contains("Code", "AC")),
        eq("IsSales", True),
    )

    assert expression == (
        "((startswith(Name, 'Acme')) or (substringof('AC', Code))) and (IsSales eq true)"
    )


def test_query_params_only_select_allowlisted_fields() -> None:
    params = query_params(
        select=("ID", "Name"),
        allowed_fields={"ID", "Name", "Code"},
        filter_expression="IsSales eq true",
        top=20,
        skip=5,
    )

    assert params == {
        "$select": "ID,Name",
        "$filter": "IsSales eq true",
        "$top": "20",
        "$skip": "5",
    }


def test_query_params_reject_unknown_fields_and_unbounded_top() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        query_params(select=("Secret",), allowed_fields={"ID"}, top=1)
    with pytest.raises(ValueError, match="between 1 and 60"):
        query_params(select=("ID",), allowed_fields={"ID"}, top=61)


def test_comparison_supports_safe_operators_only() -> None:
    assert comparison("Amount", "ge", 10) == "Amount ge 10"
    with pytest.raises(ValueError, match="operator"):
        comparison("Amount", "drop", 10)


def test_key_predicate_formats_single_and_composite_keys() -> None:
    identifier = UUID("11111111-1111-1111-1111-111111111111")

    assert key_predicate({"ID": identifier}) == "(guid'11111111-1111-1111-1111-111111111111')"
    assert key_predicate({"Code": "A", "Line": 2}) == "(Code='A',Line=2)"
