# Mandatory Generic `$select` Design

## Goal

Require every generic Exact Online GET request exposed through `exact_endpoint_read` to send an explicit OData `$select` field list.

## Root cause

The curated MCP workflows already construct bounded `$select` parameters. The generic endpoint gateway differs: `EndpointReadRequest.select` defaults to an empty list, and `ExactService.endpoint_read` omits `$select` when that list is empty. The checked-in registry contains 312 GET endpoints but no readable-field metadata, so the server cannot safely infer endpoint-specific defaults.

## Contract

`EndpointReadRequest.select` becomes a required list containing between 1 and 100 field names. This keeps the existing upper bound while allowing large resources such as bulk TransactionLines, whose supplied selection contains 74 fields.

Each field continues through the existing simple-identifier validation. Callers cannot supply raw OData fragments, commas, expressions, or unregistered query options through the field list.

`ExactService.endpoint_read` always serializes the validated list as a comma-separated `$select` parameter. Missing or empty selections fail Pydantic validation before any Exact HTTP request. Keyed and collection reads use the same rule.

## Scope

The change applies only to generic `exact_endpoint_read` calls. Curated workflow reads already use explicit `$select` lists and remain unchanged. Mutations do not receive `$select`. The Postman collection is reference evidence and is not modified.

## Testing

Model tests verify that omitted and empty `select` values are rejected. Service tests verify that a representative long TransactionLines field list is serialized exactly into `$select`, and that validation failures dispatch no HTTP request. Existing generic read, curated workflow, server-schema, and full regression suites must remain green.
