"""Immutable registry of Exact Online endpoints exposed by the generic gateway."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Any

from exact_mcp.errors import NotFoundError, ValidationFailedError

_URI_TEMPLATE = re.compile(
    r"^/api/v1/(?:beta/)?(?:\{division\}/[A-Za-z0-9_/]+|current/[A-Za-z0-9_/]+)$"
)
_METHODS = {"GET", "POST", "PUT", "DELETE"}


@dataclass(frozen=True)
class EndpointSpec:
    id: str
    service: str
    resource: str
    uri_template: str
    methods: tuple[str, ...]
    post_only_action: bool = False
    key_fields: tuple[str, ...] = field(default_factory=tuple)
    readable_fields: tuple[str, ...] = field(default_factory=tuple)
    post_fields: tuple[str, ...] = field(default_factory=tuple)
    put_fields: tuple[str, ...] = field(default_factory=tuple)
    parameters: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9_/]+", self.id):
            raise ValidationFailedError("endpoint id is invalid")
        if not _URI_TEMPLATE.fullmatch(self.uri_template) or ".." in self.uri_template:
            raise ValidationFailedError("endpoint URI template is unsafe")
        if not self.methods or not set(self.methods) <= _METHODS:
            raise ValidationFailedError("endpoint methods are invalid")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> EndpointSpec:
        return cls(
            id=str(value["id"]),
            service=str(value["service"]),
            resource=str(value["resource"]),
            uri_template=str(value["uri_template"]),
            methods=tuple(value["methods"]),
            post_only_action=bool(value.get("post_only_action", False)),
            key_fields=tuple(value.get("key_fields", ())),
            readable_fields=tuple(value.get("readable_fields", ())),
            post_fields=tuple(value.get("post_fields", ())),
            put_fields=tuple(value.get("put_fields", ())),
            parameters=tuple(value.get("parameters", ())),
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "service": self.service,
            "resource": self.resource,
            "methods": list(self.methods),
            "post_only_action": self.post_only_action,
        }


class EndpointRegistry:
    def __init__(self, items: tuple[EndpointSpec, ...]) -> None:
        by_id = {item.id: item for item in items}
        if len(by_id) != len(items):
            raise ValidationFailedError("endpoint registry contains duplicate ids")
        self._items = items
        self._by_id = by_id

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def get(self, endpoint: str) -> EndpointSpec:
        try:
            return self._by_id[endpoint.lower()]
        except KeyError as exc:
            raise NotFoundError(f"endpoint {endpoint!r} is not registered") from exc

    def search(
        self,
        *,
        service: str | None = None,
        method: str | None = None,
        query: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100 or offset < 0:
            raise ValidationFailedError("invalid endpoint discovery pagination")
        normalized_method = method.upper() if method else None
        if normalized_method and normalized_method not in _METHODS:
            raise ValidationFailedError("method must be GET, POST, PUT, or DELETE")
        needle = query.casefold()
        matches = [
            item
            for item in self._items
            if (service is None or item.service.casefold() == service.casefold())
            and (normalized_method is None or normalized_method in item.methods)
            and (not needle or needle in item.id.casefold() or needle in item.resource.casefold())
        ]
        page = matches[offset : offset + limit]
        return {
            "items": [item.public_dict() for item in page],
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(page) < len(matches),
        }


def load_registry() -> EndpointRegistry:
    path = files("exact_mcp").joinpath("endpoint_registry.json")
    values = json.loads(path.read_text(encoding="utf-8"))
    return EndpointRegistry(tuple(EndpointSpec.from_dict(value) for value in values))
