# Exact Online MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and verify a production-oriented Python MCP server for the Exact Online workflows and safeguards defined in the approved design.

**Architecture:** A FastMCP adapter delegates to an `ExactService`, which uses a typed asynchronous `ExactClient`. OAuth/token persistence, division routing, OData construction, and rate limiting are isolated behind small protocols so every behavior is testable without live Exact access.

**Tech Stack:** Python 3.12, MCP Python SDK 1.x, HTTPX, Pydantic 2, pydantic-settings, cryptography, Typer, pytest, pytest-asyncio, Ruff, mypy.

---

### Task 1: Project scaffold and configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/exact_mcp/__init__.py`
- Create: `src/exact_mcp/config.py`
- Create: `tests/test_config.py`

**Step 1: Write failing configuration tests**

Test that `Settings` validates region URLs, transport choices, rate-limit bounds, encryption-key requirements, and defaults. Use `Settings(_env_file=None, exact_client_id=..., ...)` so tests never read the developer environment.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_config.py -q`
Expected: FAIL because `exact_mcp.config` does not exist.

**Step 3: Implement the package metadata and settings**

Declare runtime dependencies with `mcp>=1.27,<2`, and test/lint dependencies in a `dev` group. Implement a frozen `Settings(BaseSettings)` with `EXACT_MCP_` environment prefix, HTTPS Exact endpoints by default, validated retry/page limits, `stdio|streamable-http` transport, and optional inbound bearer token.

**Step 4: Verify GREEN and static tooling**

Run: `uv sync --all-groups && uv run pytest tests/test_config.py -q && uv run ruff check src tests`
Expected: all tests pass and Ruff reports no errors.

**Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/exact_mcp tests/test_config.py uv.lock
git commit -m "build: scaffold Exact MCP package"
```

### Task 2: Domain schemas, errors, and safe OData

**Files:**
- Create: `src/exact_mcp/errors.py`
- Create: `src/exact_mcp/models.py`
- Create: `src/exact_mcp/odata.py`
- Create: `tests/test_models.py`
- Create: `tests/test_odata.py`

**Step 1: Write failing tests**

Cover GUID/code validation, positive decimal quantities, non-empty sales-order lines, explicit delivery confirmation, two-character search minimums, OData quote escaping (`O'Brien` -> `O''Brien`), fixed field selection, and bounded pagination.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_models.py tests/test_odata.py -q`
Expected: FAIL on missing modules.

**Step 3: Implement minimal typed models and query builder**

Create stable `ExactMCPError` subclasses carrying `code`, safe `message`, `retryable`, and `details`. Define Pydantic request/result models for administrations, accounts, items, order lines, receivables, and deliveries. Implement only composable helpers owned by the server (`quote`, `eq`, `startswith`, `contains`, `and_`, `or_`, and `query_params`); never accept caller-supplied filter expressions.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_models.py tests/test_odata.py -q`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/exact_mcp/errors.py src/exact_mcp/models.py src/exact_mcp/odata.py tests
git commit -m "feat: add typed domain schemas and safe OData"
```

### Task 3: Encrypted token storage and OAuth lifecycle

**Files:**
- Create: `src/exact_mcp/tokens.py`
- Create: `src/exact_mcp/auth.py`
- Create: `tests/test_tokens.py`
- Create: `tests/test_auth.py`

**Step 1: Write failing tests**

Use a temporary directory and `httpx.MockTransport`. Verify encrypted-at-rest token files do not contain raw tokens, bad keys fail safely, authorization URLs include state, code exchange persists tokens, refresh replaces refresh tokens, concurrent callers trigger one refresh, non-expiring tokens are reused, and HTTP errors never expose credentials.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_tokens.py tests/test_auth.py -q`
Expected: FAIL because token/auth modules are missing.

**Step 3: Implement token protocols and OAuth manager**

Define `TokenStore` with async `load/save/clear`, `MemoryTokenStore`, and atomic `EncryptedFileTokenStore`. Implement `OAuthManager` with an injected clock/client, `authorization_url`, `exchange_code`, and lock-protected `access_token`. Refresh only inside the configured expiry skew and persist the complete replacement token set.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_tokens.py tests/test_auth.py -q`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/exact_mcp/tokens.py src/exact_mcp/auth.py tests/test_tokens.py tests/test_auth.py
git commit -m "feat: manage Exact OAuth tokens securely"
```

### Task 4: Exact transport, division routing, pagination, and rate limiting

**Files:**
- Create: `src/exact_mcp/rate_limit.py`
- Create: `src/exact_mcp/client.py`
- Create: `tests/test_rate_limit.py`
- Create: `tests/test_client.py`

**Step 1: Write failing transport tests**

Verify bearer injection, `/current/Me` discovery, division-scoped paths, rejecting absolute continuation URLs outside the configured Exact origin, parsing `d.results` and `d`, continuation budgets, rate header tracking, reserve-based waits, `Retry-After`, capped backoff/jitter, retry of 429/5xx/network failures, and no retry for 400/401/403/404.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_rate_limit.py tests/test_client.py -q`
Expected: FAIL on missing modules.

**Step 3: Implement transport primitives**

Implement a per-division `RateLimiter` with injected clock/sleeper/random source. Implement `ExactClient.request`, `list`, `current_user`, `administrations`, `set_division`, and `close`. Sanitize Exact errors into `ExactAPIError`; never include authorization headers or full response bodies.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_rate_limit.py tests/test_client.py -q`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/exact_mcp/rate_limit.py src/exact_mcp/client.py tests/test_rate_limit.py tests/test_client.py
git commit -m "feat: add resilient division-aware Exact client"
```

### Task 5: Search, administration, and sales-order workflows

**Files:**
- Create: `src/exact_mcp/service.py`
- Create: `tests/test_service_search.py`
- Create: `tests/test_service_orders.py`

**Step 1: Write failing service tests**

Use a recording fake client. Verify administration list/current/switch and cache invalidation; account and item searches use bounded `$select`/`$filter`; ambiguous codes fail before mutation; codes resolve to GUIDs; and `draft_sales_order` performs all reads before one POST containing mandatory nested `SalesOrderLines`.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_service_search.py tests/test_service_orders.py -q`
Expected: FAIL because `ExactService` is missing.

**Step 3: Implement the read and order service methods**

Implement `administrations_list`, `administration_current`, `administration_switch`, `accounts_search`, `items_search`, `vat_codes_list`, `warehouses_list`, `resolve_customer_id`, `sales_orders_get`, `sales_order_lines_search`, and `draft_sales_order`. Return normalized Pydantic models rather than raw Exact envelopes.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_service_search.py tests/test_service_orders.py -q`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/exact_mcp/service.py tests/test_service_search.py tests/test_service_orders.py
git commit -m "feat: add Exact discovery and sales-order workflows"
```

### Task 6: Receivables and guarded goods delivery

**Files:**
- Modify: `src/exact_mcp/service.py`
- Create: `tests/test_service_receivables.py`
- Create: `tests/test_service_delivery.py`

**Step 1: Write failing workflow tests**

Verify unpaid-invoice filtering/normalization, `confirm=False` blocks all writes, order lines are fetched before delivery, delivered quantities cannot exceed open quantities, warehouse storage-location requirements are enforced, tracked items require valid batch/serial data, and successful execution posts one nested delivery payload.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_service_receivables.py tests/test_service_delivery.py -q`
Expected: FAIL because methods do not exist.

**Step 3: Implement workflows**

Add `retrieve_unpaid_invoices` and `execute_goods_delivery`. Keep reconciliation unsupported and return an explicit `unsupported_operation` error if requested. Validate the entire delivery plan before the POST.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_service_receivables.py tests/test_service_delivery.py -q`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/exact_mcp/service.py tests/test_service_receivables.py tests/test_service_delivery.py
git commit -m "feat: add receivables and guarded delivery workflows"
```

### Task 7: FastMCP tools and resources

**Files:**
- Create: `src/exact_mcp/server.py`
- Create: `tests/test_server.py`

**Step 1: Write failing in-process MCP tests**

Create an in-process MCP client session. Assert exact tool/resource names, structured input schemas, read-only/destructive annotations where supported, dependency access through lifespan, stable structured errors, health/current-routing resources, and successful calls for all four PRD workflows.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_server.py -q`
Expected: FAIL because the server factory is missing.

**Step 3: Implement `create_server`**

Create FastMCP with JSON responses and typed lifespan state. Register focused public tools plus supporting discovery tools. Tool functions accept typed arguments (never JSON encoded in strings), include optional audit context, and delegate without business logic.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_server.py -q`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/exact_mcp/server.py tests/test_server.py
git commit -m "feat: expose Exact workflows through MCP"
```

### Task 8: CLI, transports, deployment, and documentation

**Files:**
- Create: `src/exact_mcp/cli.py`
- Create: `tests/test_cli.py`
- Create: `Dockerfile`
- Create: `README.md`
- Modify: `.env.example`

**Step 1: Write failing CLI smoke tests**

Verify `--help`, authorization URL generation, code exchange with mocked HTTP, stdio startup wiring, Streamable HTTP startup wiring, and failure messages for missing credentials/tokens.

**Step 2: Verify RED**

Run: `uv run pytest tests/test_cli.py -q`
Expected: FAIL because the CLI is missing.

**Step 3: Implement CLI and operational files**

Add `auth-url`, `exchange-code`, `auth-status`, and `serve` commands. Document Exact app registration, encryption key creation, OAuth bootstrap, Claude/Codex-compatible stdio configuration, Streamable HTTP deployment, one-identity-per-instance constraint, destructive-tool behavior, and rate-limit caveats. Add a non-root Docker image with a health check.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_cli.py -q && docker build -t exact-mcp:test .`
Expected: CLI tests pass and image builds successfully when Docker is available.

**Step 5: Commit**

```bash
git add src/exact_mcp/cli.py tests/test_cli.py Dockerfile README.md .env.example
git commit -m "docs: add CLI and deployment guidance"
```

### Task 9: Completion audit and release verification

**Files:**
- Modify as required by findings.

**Step 1: Audit requirements**

Map every PRD MCP requirement and approved design requirement to code and tests. Explicitly verify OAuth ownership, division routing, OData bounds, pagination, 60/minute and daily header handling, error-ceiling protection, all four workflow tools, strict schemas, delivery confirmation, both transports, and secret redaction.

**Step 2: Run fresh full verification**

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv build
```

Expected: every command exits 0 with no test failures, lint errors, formatting changes, type errors, or build errors.

**Step 3: Inspect repository state**

Run: `git status --short && git diff --check && git log --oneline --decorate -10`
Expected: no uncommitted implementation changes except the user-provided `PRD.MD`, and no whitespace errors.

**Step 4: Commit audit fixes if any**

```bash
git add <audited-files>
git commit -m "test: complete Exact MCP verification"
```
