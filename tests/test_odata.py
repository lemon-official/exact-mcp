import pytest

from exact_mcp.odata import and_, contains, eq, or_, query_params, quote, startswith


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
