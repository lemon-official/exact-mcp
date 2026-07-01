"""Validated public inputs and normalized Exact Online outputs."""

from datetime import date
from decimal import Decimal
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SearchRequest(StrictModel):
    query: str
    limit: int = Field(default=20, ge=1, le=60)
    offset: int = Field(default=0, ge=0)
    context: str = Field(default="", max_length=500)

    @field_validator("query")
    @classmethod
    def valid_query(cls, value: str) -> str:
        if value != "*" and len(value) < 2:
            raise ValueError("query must contain at least 2 characters or be '*'")
        return value


class SalesOrderLineInput(StrictModel):
    item_id: UUID | None = None
    item_code: str | None = Field(default=None, min_length=1, max_length=128)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=1000)
    vat_code: str | None = Field(default=None, max_length=16)

    @model_validator(mode="after")
    def one_item_identifier(self) -> Self:
        if (self.item_id is None) == (self.item_code is None):
            raise ValueError("provide exactly one of item_id or item_code")
        return self


class DraftSalesOrderRequest(StrictModel):
    customer_id: UUID | None = None
    customer_code: str | None = Field(default=None, min_length=1, max_length=128)
    lines: list[SalesOrderLineInput] = Field(min_length=1, max_length=100)
    delivery_date: date | None = None
    description: str = Field(default="", max_length=500)
    your_reference: str = Field(default="", max_length=100)
    remarks: str = Field(default="", max_length=2000)
    context: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def one_customer_identifier(self) -> Self:
        if (self.customer_id is None) == (self.customer_code is None):
            raise ValueError("provide exactly one of customer_id or customer_code")
        return self


class DeliveryLineInput(StrictModel):
    order_line_id: UUID | None = None
    item_code: str | None = Field(default=None, min_length=1, max_length=128)
    quantity: Decimal = Field(gt=0)
    storage_location_id: UUID | None = None
    batch_number: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def one_line_identifier(self) -> Self:
        if (self.order_line_id is None) == (self.item_code is None):
            raise ValueError("provide exactly one of order_line_id or item_code")
        return self


class GoodsDeliveryRequest(StrictModel):
    order_id: UUID | None = None
    order_number: str | None = Field(default=None, min_length=1, max_length=64)
    lines: list[DeliveryLineInput] | None = Field(default=None, min_length=1, max_length=100)
    warehouse_id: UUID | None = None
    delivery_date: date | None = None
    description: str = Field(default="", max_length=500)
    tracking_number: str = Field(default="", max_length=100)
    remarks: str = Field(default="", max_length=2000)
    confirm: bool = False
    context: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def one_order_identifier(self) -> Self:
        if (self.order_id is None) == (self.order_number is None):
            raise ValueError("provide exactly one of order_id or order_number")
        return self


class Page(StrictModel):
    items: list[dict[str, Any]]
    limit: int
    offset: int
    has_more: bool


class Administration(StrictModel):
    division: int
    code: str | None = None
    name: str
    currency: str | None = None


class AccountMatch(StrictModel):
    id: UUID
    code: str | None = None
    name: str
    city: str | None = None
    email: str | None = None


class ItemMatch(StrictModel):
    id: UUID
    code: str
    description: str
    sales_price: Decimal | None = None


class Receivable(StrictModel):
    id: UUID | None = None
    invoice_id: UUID | None = None
    invoice_number: int | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    original_amount: Decimal
    outstanding_amount: Decimal

