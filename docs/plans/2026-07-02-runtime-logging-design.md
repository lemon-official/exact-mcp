# Exact MCP Runtime Logging Design

## Goal

Make every MCP run observable enough to diagnose missing Exact Online data without corrupting the stdio protocol or exposing credentials.

## Design

The server will configure Python logging as soon as `exact-mcp serve` has validated its settings. Logs always go to stderr because stdout belongs to MCP JSON-RPC when using stdio. Operators may additionally configure a rotating file. `INFO` records lifecycle and boundary summaries; `DEBUG` adds sanitized tool arguments, tool results, Exact query parameters, request payloads, and response payloads.

Logging is added at the boundaries where data can disappear:

1. CLI/server startup and shutdown, including transport and non-secret routing settings.
2. MCP tool/resource start, completion, duration, arguments/results, and safe domain errors.
3. Exact OAuth state transitions: token presence, reuse, refresh, exchange success, and safe failures.
4. Exact HTTP requests and responses: method, URL path, division, status, duration, request ID, rate-limit headers, sanitized bodies, retries, and network failures.
5. OData pagination: page number, records received, accumulated count, continuation use, and configured budget stops.
6. Division selection/switching and rate-limit waits/updates.

The logging configuration is controlled by:

- `EXACT_MCP_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, or `ERROR`; default `INFO`).
- `EXACT_MCP_LOG_FILE` (optional path for a rotating log file).
- `EXACT_MCP_LOG_MAX_BYTES` (default 10 MiB).
- `EXACT_MCP_LOG_BACKUP_COUNT` (default 5).

## Redaction and data handling

Authorization headers are never passed to logging calls. A recursive sanitizer redacts sensitive mapping keys such as `authorization`, `client_secret`, `access_token`, `refresh_token`, `token_encryption_key`, authorization `code`, and CSRF `state`. It also masks bearer-token strings encountered in nested values.

Business payloads can contain customer and financial data. They are emitted only at `DEBUG`; the default `INFO` level records counts, identifiers needed for correlation, statuses, and timings rather than full bodies.

## Error handling

Logging must never replace or alter existing domain errors. Tool failures are logged with the safe `ExactMCPError` representation before conversion to `ToolError`. Unexpected failures are logged with tracebacks and then re-raised. Logging failures must not prevent MCP startup or tool execution.

## Testing

Tests will prove that logging:

- writes to stderr and an optional rotating file;
- never writes to stdout;
- redacts nested credentials and bearer tokens;
- records MCP tool success and failure;
- records Exact request, response, retry, pagination, division, OAuth, and rate-limit events;
- includes sanitized bodies only at `DEBUG`;
- preserves all existing behavior and passes formatting, linting, typing, and build checks.

