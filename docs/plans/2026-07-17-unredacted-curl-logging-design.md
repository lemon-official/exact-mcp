# Unredacted cURL Logging Design

## Goal

Make every outbound Exact Online API and OAuth request visible as an executable-equivalent cURL command in debug logs.

## Scope

Add a shared shell-safe cURL formatter. The Exact API client will log the full request URL, headers, and JSON body immediately before dispatch. The OAuth token client will log its form-encoded request in the same format.

The commands intentionally include bearer tokens, OData values, OAuth client credentials, and request bodies. This is an explicit debugging choice; these logs must be treated as sensitive.

## Logging

The new `exact_curl` log event is emitted at `DEBUG`; existing `INFO` behavior remains unchanged. Shell escaping makes the command copyable without changing values.

## Tests

Tests will capture Exact API and OAuth debug logs, verify that each includes an unredacted executable-equivalent cURL command, and verify request method, URL, headers, and body representation.
