# Exact Online MCP Server Design

## Scope

Build a standalone Python MCP server that gives AI clients a secure, typed interface to the Exact Online order-handling and accounting operations described in `PRD.MD`. The LangGraph agent, human-approval UI, and three-tier memory system are separate consumers and are not part of this repository.

The server exposes focused workflows rather than a generic Exact REST proxy. It owns Exact OAuth credentials, division routing, identifier resolution, OData construction, pagination, rate-limit handling, response sanitization, and mutation safeguards.

## Interface principles

The public tool interface combines the PRD's high-level workflows with useful conventions observed in Ledgerbotje's public MCP catalog:

- Domain-prefixed, verb-suffixed names make tools discoverable.
- Search, get, and list operations are read-only and separate from mutations.
- Users supply recognizable account, item, order, and warehouse codes where possible; the server resolves Exact GUIDs internally.
- Search operations return bounded pages with `offset`, `limit`, and `has_more` metadata.
- Every operation accepts an optional `context` string for audit logs.
- Destructive inventory operations require an explicit confirmation flag and are clearly described as destructive.
- Active division and warehouse state can be inspected and selected explicitly.

The four PRD workflows remain first-class tools:

- `resolve_customer_id`
- `draft_sales_order`
- `retrieve_unpaid_invoices`
- `execute_goods_delivery`

Supporting read-only tools provide safe discovery:

- `administrations_list`, `administration_current`, `administration_switch`
- `accounts_search`, `items_search`
- `vat_codes_list`, `warehouses_list`
- `sales_orders_get`, `sales_order_lines_search`

MCP resources expose server health and current routing state. Resource reads never mutate server state.

## Architecture

The project uses a `src` layout with five layers:

1. **MCP adapter** registers tools/resources, validates schemas, retrieves application dependencies from the FastMCP lifespan, and converts domain failures into concise tool errors.
2. **Domain service** implements Exact-specific workflows: resolving codes, constructing atomic order payloads, retrieving receivables, and assembling goods deliveries.
3. **Exact client** builds division-scoped URLs, performs OData requests, unwraps Exact's response envelopes, follows pagination, sanitizes errors, and updates rate-limit state.
4. **Authentication and routing** owns OAuth tokens, refresh synchronization, current-division discovery, and explicit division/warehouse selection.
5. **Infrastructure** provides settings, encrypted token persistence, rate-limit coordination, structured logging, and transport entry points.

Dependencies are injected so tests can use an in-memory token store, fake clock/sleeper, and `httpx.MockTransport` without contacting Exact Online.

## Authentication and security

Exact OAuth credentials never enter MCP tool arguments or results. Configuration supplies client credentials and a Fernet key. Tokens are stored in an encrypted local file by default behind a `TokenStore` protocol, allowing a production vault adapter later.

The server supports:

- generating an authorization URL with a cryptographically random state value;
- exchanging a callback authorization code;
- loading encrypted access and refresh tokens at startup;
- serialized automatic refresh shortly before access-token expiry;
- replacing the stored refresh token after every successful refresh;
- respecting Exact's minimum refresh timing by refreshing only when required;
- redacting tokens, authorization headers, and sensitive Exact response bodies from errors and logs.

Streamable HTTP deployments may require a static bearer token on inbound MCP requests. Stdio relies on process-level access control. Authentication to the MCP server and outbound Exact OAuth remain separate concerns.

## Routing and state

The `/api/v1/current/Me` response initializes the default division. Available administrations are fetched and cached for bounded periods. A selected division is validated against that list before becoming active.

Process-wide active routing is acceptable for the initial single-tenant server. The documentation states that one server instance must serve one Exact identity. Multi-tenant deployments must run isolated instances or replace this state with request-scoped tenancy.

Warehouse selection follows the same explicit model, but only affects workflows requiring a warehouse. Division changes clear the warehouse selection and division-specific caches.

## OData and traffic control

Callers never supply raw OData expressions. The domain layer uses an escaping helper for string literals and fixed allowlists for selectable fields, filters, and sort keys. Searches enforce bounded limits and server-side `$select`/`$filter` clauses.

The client:

- unwraps both `d.results` and `d` Exact response forms;
- follows `__next` continuation URLs within an explicit page/record budget;
- tracks minutely and daily remaining limits per division;
- pauses before calls when the minutely remainder reaches the configured reserve;
- honors `X-RateLimit-Reset` and `Retry-After`;
- retries 429 and transient 5xx/network failures with capped exponential backoff and jitter;
- does not automatically retry ordinary 4xx failures, protecting Exact's error ceiling;
- raises structured errors containing status, safe message, request ID, and retryability.

## Workflow behavior

`resolve_customer_id`/`accounts_search` search account name, code, city, and email with bounded results and optional customer/supplier filtering. Empty or one-character queries are rejected unless explicitly requesting a bounded page. No-result responses are returned directly rather than triggering speculative spelling retries.

`draft_sales_order` accepts a customer GUID or code plus typed line objects containing item GUID/code and positive decimal quantity. It resolves all identifiers first, rejects missing or ambiguous matches, then posts one atomic payload with nested `SalesOrderLines`. It returns only the created order identifiers, number, status, dates, and sanitized line summary.

`retrieve_unpaid_invoices` resolves the account and queries Exact's receivables list with a mandatory account filter. It returns normalized invoice number, date, due date, currency, original amount, outstanding amount, and identifiers.

`execute_goods_delivery` requires `confirm=True`. It fetches open sales-order lines, rejects already-delivered or over-delivered quantities, resolves warehouse/storage-location requirements and batch/serial data where needed, then posts the nested goods-delivery payload. Unsupported or ambiguous tracking requirements fail before mutation.

## Errors and observability

Domain errors use stable codes such as `authentication_required`, `ambiguous_match`, `not_found`, `validation_failed`, `rate_limited`, and `exact_api_error`. MCP clients receive actionable messages and structured details without secrets. Logs include operation name, supplied audit context, division, duration, request ID, and outcome; mutation payload contents and OAuth tokens are omitted.

## Transport and deployment

The package exposes an `exact-mcp` CLI. `exact-mcp serve --transport stdio` supports local clients. `exact-mcp serve --transport streamable-http` is the production transport and uses stateless JSON responses where compatible with the authentication/routing model.

The repository includes a Dockerfile, health check, `.env.example`, and README covering Exact app registration, OAuth bootstrap, client configuration, and operational limits.

## Testing

Tests follow red-green-refactor cycles and cover:

- settings and schema validation;
- OData escaping and query construction;
- encrypted token persistence and refresh serialization;
- division routing and cache invalidation;
- response-envelope parsing and continuation pagination;
- header-driven throttling, retry delays, and non-retryable 4xx behavior;
- identifier resolution and ambiguity failures;
- atomic sales-order payload construction;
- unpaid-invoice normalization;
- delivery confirmation, line resolution, and inventory safeguards;
- MCP tool discovery, input schemas, resources, and tool invocation through an in-process client;
- stdio/Streamable HTTP startup smoke tests.

Live Exact Online tests are optional and guarded by environment variables. The default suite performs no external network calls.
