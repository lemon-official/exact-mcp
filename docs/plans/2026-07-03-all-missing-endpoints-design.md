# All Missing Exact Endpoints Design

## Goal

Expose the 330 resources in the supplied Exact Online catalogue that are not represented by
the existing MCP workflows, while preserving URL, OData, mutation-confirmation, logging, and
rate-limit safeguards.

## Architecture

A generated, checked-in JSON registry is the only source of generic endpoint routes. Each
entry has a stable lowercase ID, an Exact URI template, supported HTTP methods, service and
resource names, and optional documented field metadata. The client accepts `EndpointSpec`
objects rather than caller paths and renders `{division}` against the configured Exact origin.

`ExactService` validates endpoint IDs, methods, simple field and parameter names, structured
filters, entity keys, and explicit mutation confirmation. FastMCP exposes discovery, read,
create, update, delete, and POST-only action tools. Existing curated workflows and normalized
outputs are unchanged.

## Safety and compatibility

- Raw URLs, path fragments, raw `$filter` expressions, and unconfirmed writes are rejected.
- Reads are bounded to 60 records per request and use structured OData expressions.
- Deletes and POST-only actions are marked destructive; create and update are mutating.
- Runtime and tests do not scrape Exact documentation or make live Exact calls.
- Tenant licensing and scopes remain authoritative; Exact `403` and `404` responses are
  returned through the existing sanitized error envelope.

The 20 methods missing from eight partially covered resources remain out of scope, matching
the approved “absent resources only” decision.
