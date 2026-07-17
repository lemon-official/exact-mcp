# Exact MCP Resilience and Conversational Expressiveness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the Exact Online MCP and prove its conversational usefulness with a deterministic,
exactly 1,000-question accounting evaluation corpus.

**Architecture:** Keep the existing ExactClient → ExactService → FastMCP layers, but make security,
division state, OAuth/rate coordination, pagination, errors, and result metadata shared and explicit.
Add a compact semantic operation catalog instead of expanding the tool list for 330 endpoints, then
exercise the real stack through an XAF-derived Exact emulator and a generated question corpus.

**Tech Stack:** Python 3.12, FastAPI/Starlette, official Python MCP SDK/FastMCP, httpx,
Pydantic v2, asyncpg, pytest/pytest-asyncio, respx, Ruff, mypy, XML ElementTree.

---

### Task 1: Eliminate hosted credential and token leakage

**Files:**
- Modify: `src/exact_mcp/hosted.py:461-515`
- Modify: `src/exact_mcp/logging.py`
- Test: `tests/test_hosted_app.py:342-378`
- Test: `tests/test_hosted_app.py:873-935`

**Step 1: Replace leakage assertions with failing secret-canary tests**

Create tests that submit unique canaries in `Authorization`, cookies, OAuth `code`,
`client_secret`, `code_verifier`, `access_token`, and `refresh_token`. Capture stdout/log records and
assert no canary appears, while method, route, status, MCP method/tool name, division, correlation
ID, and safe error code remain observable.

**Step 2: Run the focused tests and verify RED**

Run: `.venv/bin/pytest -q tests/test_hosted_app.py -k 'logging or token_exchange'`

Expected: FAIL because current helpers print raw headers, forms, request bodies, and responses.

**Step 3: Implement structured secret-safe logging**

Route values through `exact_mcp.logging.redact`, discard raw authorization/cookie headers, and
project request/response bodies to safe metadata. Add a recursive key policy for names containing
`token`, `secret`, `authorization`, `cookie`, `code`, and `verifier`. Never log a complete OAuth or
MCP body.

**Step 4: Verify GREEN and surrounding hosted behavior**

Run: `.venv/bin/pytest -q tests/test_hosted_app.py`

Expected: PASS with no secret canary in captured output.

**Step 5: Commit only the scoped files**

```bash
git add src/exact_mcp/hosted.py src/exact_mcp/logging.py tests/test_hosted_app.py
git commit -m "fix: redact hosted credentials and tokens"
```

### Task 2: Enforce local HTTP authentication and stable division routing

**Files:**
- Modify: `src/exact_mcp/cli.py`
- Modify: `src/exact_mcp/server.py:614-646`
- Modify: `src/exact_mcp/client.py:40-70`
- Modify: `src/exact_mcp/service.py:187-204`
- Modify: `src/exact_mcp/config.py`
- Test: `tests/test_server.py`
- Test: `tests/test_client.py`
- Test: `tests/test_service.py`
- Create: `tests/test_http_transport.py`

**Step 1: Write failing HTTP bearer tests**

Start the Streamable HTTP ASGI app in process with `inbound_bearer_token="canary"`. Assert missing
and incorrect tokens return `401` plus `WWW-Authenticate`, the correct bearer initializes, and
stdio server construction remains unaffected.

**Step 2: Write failing division-state tests**

Assert production construction does not select `4487358`; an unset client discovers its default
once; a selected division survives `administration_current`; and `administration_switch` changes
only an explicitly switchable local runtime.

**Step 3: Verify RED**

Run: `.venv/bin/pytest -q tests/test_http_transport.py tests/test_server.py tests/test_service.py -k 'bearer or division or administration'`

Expected: FAIL because bearer configuration is unused, startup hardcodes the division, and
`current_user()` mutates an existing route.

**Step 4: Implement the boundary and routing changes**

Wrap the ordinary HTTP ASGI app with constant-time bearer validation when configured. Remove the
hardcoded division. Split user discovery from division selection so `administration_current`
reports the selected division and user without overwriting it. Add a `division_locked` mode for
hosted URL-scoped clients.

**Step 5: Verify GREEN**

Run: `.venv/bin/pytest -q tests/test_http_transport.py tests/test_client.py tests/test_service.py tests/test_server.py`

**Step 6: Commit**

```bash
git add src/exact_mcp/cli.py src/exact_mcp/server.py src/exact_mcp/client.py \
  src/exact_mcp/service.py src/exact_mcp/config.py tests/test_http_transport.py \
  tests/test_client.py tests/test_service.py tests/test_server.py
git commit -m "fix: enforce HTTP auth and stable division routing"
```

### Task 3: Make every state change mechanically safe

**Files:**
- Modify: `src/exact_mcp/models.py:44-58`
- Modify: `src/exact_mcp/service.py:339-387`
- Modify: `src/exact_mcp/server.py:237-400`
- Modify: `src/exact_mcp/errors.py`
- Test: `tests/test_models.py`
- Test: `tests/test_service.py`
- Test: `tests/test_server.py`

**Step 1: Write failing confirmation and annotation tests**

Assert `DraftSalesOrderRequest` defaults `confirm` to false, an unconfirmed call performs zero
reads and zero writes, a confirmed call retains existing behavior, and `administration_switch` is
not advertised read-only. Assert validation errors identify the exact confirmation target.

**Step 2: Verify RED**

Run: `.venv/bin/pytest -q tests/test_models.py tests/test_service.py tests/test_server.py -k 'draft_sales_order or administration_switch or annotation'`

**Step 3: Add the confirmation gate and accurate annotations**

Add `confirm: bool = False` to `DraftSalesOrderRequest`; reject before customer/item resolution.
Use a state-changing annotation for administration switching and preserve destructive/non-idempotent
hints for delivery/delete/action tools.

**Step 4: Verify GREEN and mutation regression tests**

Run: `.venv/bin/pytest -q tests/test_models.py tests/test_service.py tests/test_server.py`

**Step 5: Commit**

```bash
git add src/exact_mcp/models.py src/exact_mcp/service.py src/exact_mcp/server.py \
  src/exact_mcp/errors.py tests/test_models.py tests/test_service.py tests/test_server.py
git commit -m "fix: require confirmation for all Exact writes"
```

### Task 4: Persist refresh-token age and share hosted runtime state

**Files:**
- Create: `migrations/002_refresh_token_obtained_at.sql`
- Modify: `src/exact_mcp/tokens.py`
- Modify: `src/exact_mcp/auth.py`
- Modify: `src/exact_mcp/hosted_storage.py`
- Modify: `src/exact_mcp/hosted.py`
- Create: `src/exact_mcp/hosted_runtime.py`
- Test: `tests/test_auth.py`
- Test: `tests/test_hosted_storage.py`
- Test: `tests/test_hosted_app.py`
- Create: `tests/test_hosted_runtime.py`

**Step 1: Write failing token-age persistence tests**

Assert `refresh_token_obtained_at` survives repository round trips, is retained when Exact does not
rotate the refresh token, and is replaced only when a new refresh token is issued.

**Step 2: Write failing concurrency tests**

Issue concurrent MCP calls for the same installation/division with an expired access token. Assert
one refresh request occurs, all calls use the rotated credentials, and calls share one rate limiter.
Assert distinct installations never share credentials or rate state.

**Step 3: Verify RED**

Run: `.venv/bin/pytest -q tests/test_auth.py tests/test_hosted_storage.py tests/test_hosted_runtime.py tests/test_hosted_app.py -k 'refresh or runtime or concurrent'`

**Step 4: Add the migration and runtime cache**

Create an additive nullable database column and map it through storage/token models. Implement a
bounded async runtime registry keyed by installation and division, with per-key construction locks,
last-used timestamps, deterministic close/eviction, and application-lifespan shutdown. A runtime
contains the shared HTTP client, OAuth manager, rate limiter, Exact client, service, and server.

**Step 5: Verify GREEN, including shutdown**

Run: `.venv/bin/pytest -q tests/test_auth.py tests/test_hosted_storage.py tests/test_hosted_runtime.py tests/test_hosted_app.py`

**Step 6: Commit**

```bash
git add migrations/002_refresh_token_obtained_at.sql src/exact_mcp/tokens.py \
  src/exact_mcp/auth.py src/exact_mcp/hosted_storage.py src/exact_mcp/hosted_runtime.py \
  src/exact_mcp/hosted.py tests/test_auth.py tests/test_hosted_storage.py \
  tests/test_hosted_runtime.py tests/test_hosted_app.py
git commit -m "fix: coordinate hosted OAuth and runtime state"
```

### Task 5: Coordinate rate budgets and bounded retries

**Files:**
- Modify: `src/exact_mcp/rate_limit.py`
- Modify: `src/exact_mcp/client.py`
- Modify: `src/exact_mcp/config.py`
- Modify: `src/exact_mcp/errors.py`
- Test: `tests/test_rate_limit.py`
- Test: `tests/test_client.py`

**Step 1: Write failing concurrent reservation tests**

With a deterministic clock/sleeper, start multiple requests at the reserve boundary. Assert only
available capacity dispatches, remaining calls wait once, minute and daily budgets are honored,
malformed/reset headers do not crash, and cancellation releases reservations.

**Step 2: Write failing retry-boundary tests**

Assert the limiter is consulted before each retry, server `Retry-After` wins, network/429/5xx GETs
retry within the configured budget, non-GET transport failures never retry, and errors report
`retry_after_seconds` plus `operation_state`.

**Step 3: Verify RED**

Run: `.venv/bin/pytest -q tests/test_rate_limit.py tests/test_client.py -k 'concurrent or retry or daily or reservation'`

**Step 4: Implement locked reservation and retry metadata**

Protect each division state with an async lock/condition, decrement capacity on reservation, update
from response headers, and wake waiters after reset. Move `before_request` inside the retry loop.
Keep write retry policy conservative and secret-safe.

**Step 5: Verify GREEN**

Run: `.venv/bin/pytest -q tests/test_rate_limit.py tests/test_client.py`

**Step 6: Commit**

```bash
git add src/exact_mcp/rate_limit.py src/exact_mcp/client.py src/exact_mcp/config.py \
  src/exact_mcp/errors.py tests/test_rate_limit.py tests/test_client.py
git commit -m "fix: coordinate Exact rate limits and retries"
```

### Task 6: Correct pagination and analytical completeness

**Files:**
- Modify: `src/exact_mcp/client.py:79-128`
- Modify: `src/exact_mcp/models.py:137-193`
- Modify: `src/exact_mcp/service.py:206-786`
- Create: `src/exact_mcp/results.py`
- Test: `tests/test_client.py`
- Test: `tests/test_service.py`
- Test: `tests/test_models.py`

**Step 1: Write failing page-semantics tests**

Assert search tools return at most `limit`, use `offset` when the endpoint supports it, and provide a
stable continuation/`has_more`. Assert page one, exact-full-page, multi-page, record-cap, page-cap,
and failed-continuation cases distinguish complete, partial, and unknown.

**Step 2: Write failing aggregation tests**

For transaction lines, overdue invoices, revenue comparison, and VAT balance, assert summaries are
never labeled complete when only 60 records were retrieved. Cover empty data, overlapping or
reversed comparison ranges, unsupported `$skip`, and failure after a successful page.

**Step 3: Verify RED**

Run: `.venv/bin/pytest -q tests/test_client.py tests/test_models.py tests/test_service.py -k 'page or pagination or partial or completeness or compare'`

**Step 4: Implement explicit page and completeness results**

Separate `list_page` from `list_all`. Return a typed page object containing records, count,
continuation, cap reason, and complete flag. Search workflows call `list_page`; aggregations call
`list_all` with explicit budgets and construct the shared `scope`, `completeness`, `provenance`, and
`warnings` envelope in `results.py`.

**Step 5: Verify GREEN**

Run: `.venv/bin/pytest -q tests/test_client.py tests/test_models.py tests/test_service.py`

**Step 6: Commit**

```bash
git add src/exact_mcp/client.py src/exact_mcp/models.py src/exact_mcp/service.py \
  src/exact_mcp/results.py tests/test_client.py tests/test_models.py tests/test_service.py
git commit -m "fix: expose complete and partial Exact results"
```

### Task 7: Normalize protocol-safe, actionable tool errors

**Files:**
- Modify: `src/exact_mcp/errors.py`
- Modify: `src/exact_mcp/server.py:57-178`
- Modify: `src/exact_mcp/client.py`
- Test: `tests/test_server.py`
- Test: `tests/test_client.py`

**Step 1: Write failing error-contract tests**

Cover validation, ambiguity, not found, 400, 401, 403, 404, 429, 5xx, timeout, malformed JSON,
partial pagination, cancelled request, rejected write, and unknown write outcome. Assert stable code,
safe message, retryability, retry delay, operation state, correlation/request ID, recovery action,
and absence of stack traces/secrets.

**Step 2: Verify RED**

Run: `.venv/bin/pytest -q tests/test_server.py tests/test_client.py -k 'error or recovery or timeout or malformed or cancelled'`

**Step 3: Implement the error envelope**

Extend domain errors with typed safe details. Convert expected httpx/JSON/cancellation boundaries to
domain errors, and convert unexpected exceptions at the MCP boundary to a correlation-ID error
while retaining full server-side diagnostics through redacted logging.

**Step 4: Verify GREEN**

Run: `.venv/bin/pytest -q tests/test_server.py tests/test_client.py`

**Step 5: Commit**

```bash
git add src/exact_mcp/errors.py src/exact_mcp/server.py src/exact_mcp/client.py \
  tests/test_server.py tests/test_client.py
git commit -m "feat: return actionable Exact tool errors"
```

### Task 8: Replace hosted JSON-RPC subset with SDK protocol behavior

**Files:**
- Modify: `src/exact_mcp/hosted.py:388-430`
- Remove or reduce: `src/exact_mcp/hosted.py:828-888`
- Modify: `src/exact_mcp/hosted_runtime.py`
- Test: `tests/test_hosted_app.py`
- Create: `tests/test_hosted_protocol.py`

**Step 1: Write failing protocol tests with the official MCP client**

Exercise initialize (including instructions/capabilities), tools list/call, resources list/read,
ping, initialized notification, invalid JSON, invalid params, unsupported method, and concurrent
requests against the hosted route. Add batch/cancellation tests only when advertised by the
installed SDK.

**Step 2: Verify RED**

Run: `.venv/bin/pytest -q tests/test_hosted_protocol.py`

Expected: resources, instructions, ping, parse errors, and general protocol behavior fail under the
hand-written dispatcher.

**Step 3: Delegate to the SDK ASGI transport**

After hosted bearer/division authorization, dispatch into the cached FastMCP streamable HTTP ASGI
application with the route path normalized to the SDK mount point. Do not duplicate JSON-RPC
method handling. Preserve authenticated installation/division context through the runtime key and
request scope.

**Step 4: Verify GREEN and existing onboarding/OAuth routes**

Run: `.venv/bin/pytest -q tests/test_hosted_protocol.py tests/test_hosted_app.py`

**Step 5: Commit**

```bash
git add src/exact_mcp/hosted.py src/exact_mcp/hosted_runtime.py \
  tests/test_hosted_protocol.py tests/test_hosted_app.py
git commit -m "fix: use SDK protocol handling in hosted mode"
```

### Task 9: Add semantic capability search and operation descriptions

**Files:**
- Create: `src/exact_mcp/capabilities.py`
- Modify: `src/exact_mcp/endpoints.py`
- Modify: `src/exact_mcp/endpoint_registry.json`
- Modify: `src/exact_mcp/server.py`
- Modify: `src/exact_mcp/models.py`
- Test: `tests/test_capabilities.py`
- Test: `tests/test_endpoints.py`
- Test: `tests/test_server.py`

**Step 1: Write failing catalog-search tests**

Assert Dutch/English terms such as omzet/revenue, btw/VAT, openstaande facturen/receivables,
grootboek/ledger, klanten/customers, leveranciers/suppliers, voorraad/inventory, and audit trail rank
the intended specialized workflow. Cover typos, exact operation IDs, unsafe mutation language,
missing periods, and unsupported forecasts/documents.

**Step 2: Write failing description tests**

Assert every purpose-built tool and endpoint operation has an operation ID, safety class, required
inputs, known limitations, schema completeness marker, and source endpoint/docs. Unknown endpoint
field metadata must be explicit rather than silently unrestricted.

**Step 3: Verify RED**

Run: `.venv/bin/pytest -q tests/test_capabilities.py tests/test_endpoints.py tests/test_server.py -k 'capabilit or describe or operation'`

**Step 4: Implement deterministic intent ranking**

Build a small normalized token/synonym index with exact-ID priority, weighted aliases, typo-tolerant
matching, and deterministic tie-breaking. Register `exact_capabilities_search` and
`exact_operation_describe` as read-only tools. Enrich registry public descriptions with keys,
parameters, field-metadata status, examples, and limitations without listing 330 new tools.

**Step 5: Verify GREEN**

Run: `.venv/bin/pytest -q tests/test_capabilities.py tests/test_endpoints.py tests/test_server.py`

**Step 6: Commit**

```bash
git add src/exact_mcp/capabilities.py src/exact_mcp/endpoints.py \
  src/exact_mcp/endpoint_registry.json src/exact_mcp/server.py src/exact_mcp/models.py \
  tests/test_capabilities.py tests/test_endpoints.py tests/test_server.py
git commit -m "feat: add conversational Exact operation discovery"
```

### Task 10: Publish typed outputs and contextual resources

**Files:**
- Modify: `src/exact_mcp/models.py`
- Modify: `src/exact_mcp/server.py`
- Modify: `src/exact_mcp/results.py`
- Test: `tests/test_models.py`
- Test: `tests/test_server.py`
- Create: `tests/test_resources.py`

**Step 1: Write failing schema/resource tests**

Assert high-value analytical and discovery tools advertise concrete output schemas. Assert metric
definitions, capability coverage, endpoint operation descriptions, and current routing can be read
as MCP resources with safe annotations and bounded payloads.

**Step 2: Verify RED**

Run: `.venv/bin/pytest -q tests/test_models.py tests/test_server.py tests/test_resources.py`

**Step 3: Add typed result models and resources**

Define shared scope/completeness/provenance/warning models and specific summary/row models for
financial tools and capability search. Return structured content conforming to advertised schemas,
while retaining JSON text compatibility through FastMCP. Register bounded resources for metric
definitions and capability coverage.

**Step 4: Verify GREEN**

Run: `.venv/bin/pytest -q tests/test_models.py tests/test_server.py tests/test_resources.py`

**Step 5: Commit**

```bash
git add src/exact_mcp/models.py src/exact_mcp/server.py src/exact_mcp/results.py \
  tests/test_models.py tests/test_server.py tests/test_resources.py
git commit -m "feat: publish typed Exact results and resources"
```

### Task 11: Build the XAF-derived Exact evaluation fixture

**Files:**
- Create: `evals/__init__.py`
- Create: `evals/xaf_fixture.py`
- Create: `evals/exact_emulator.py`
- Create: `tests/test_xaf_fixture.py`
- Create: `tests/test_exact_emulator.py`
- Read-only fixture: `export/audit.xaf`

**Step 1: Write failing parser-oracle tests**

Assert XAF version, fiscal/observed ranges, currency, counts, declared totals, balanced transactions,
key uniqueness, foreign-key integrity, leading-zero IDs, empty-vs-absent document references, VAT
usage, and opening/current subledger reconciliation facts from the design document.

**Step 2: Verify RED**

Run: `.venv/bin/pytest -q tests/test_xaf_fixture.py`

**Step 3: Implement a namespace-aware precision-safe parser**

Use ElementTree, `Decimal`, `date`, immutable dataclasses/Pydantic models, path-aware null handling,
unknown-enum preservation, and redacted projections. Do not expose raw personal/bank/payroll fields
unless a test explicitly requests an authorized projection.

**Step 4: Write failing Exact emulator tests**

Cover the Exact response envelope, `$select`, supported structured filters, `$top`, `$skip`,
`__next`, bulk endpoint restrictions, invalid fields, authorization, 429/reset headers, 5xx,
timeouts, malformed JSON, and token rotation.

**Step 5: Implement the `httpx.MockTransport` emulator and verify GREEN**

Run: `.venv/bin/pytest -q tests/test_xaf_fixture.py tests/test_exact_emulator.py`

**Step 6: Commit**

```bash
git add evals/__init__.py evals/xaf_fixture.py evals/exact_emulator.py \
  tests/test_xaf_fixture.py tests/test_exact_emulator.py
git commit -m "test: add XAF-derived Exact evaluation fixture"
```

### Task 12: Generate and run exactly 1,000 conversational cases

**Files:**
- Create: `evals/question_matrix.py`
- Create: `evals/generate_questions.py`
- Create: `evals/run_questions.py`
- Create: `evals/questions.jsonl`
- Create: `evals/README.md`
- Create: `tests/test_question_corpus.py`
- Create: `tests/test_question_runner.py`

**Step 1: Write failing matrix tests**

Assert 20 domains × 10 intents × 5 modes, exactly 1,000 unique IDs/questions, exactly 50 per
domain, 100 per intent, 200 per mode, stable regeneration, and required expectation fields.

**Step 2: Verify RED**

Run: `.venv/bin/pytest -q tests/test_question_corpus.py`

**Step 3: Implement deterministic generation and materialize JSONL**

Generate Dutch/English direct questions, ambiguous/typo variants, contextual follow-ups,
null/boundary/leading-zero variants, and unsupported/safety cases. Each row includes operation
expectations, arguments or clarification, fact assertions, completeness/provenance/privacy
requirements, and mutation prohibition.

Run: `.venv/bin/python -m evals.generate_questions --check --output evals/questions.jsonl`

Expected: `1000 questions; 1000 unique; matrix coverage valid`.

**Step 4: Write failing real-stack runner tests**

Run every question through `exact_capabilities_search`; for supported executable cases, call the
declared real MCP tool against the XAF emulator; for clarification/unsupported cases, assert the
structured alternative. Inject error scenarios and enforce per-call/case deadlines and tool-call
budgets.

**Step 5: Implement scoring and verify GREEN**

Produce JSON and Markdown summaries for routing, schema validity, facts, clarification, safety,
completeness, recovery, and call efficiency. Fail the command when any safety/factual invariant
fails or matrix coverage changes.

Run: `.venv/bin/pytest -q tests/test_question_corpus.py tests/test_question_runner.py`

Run: `.venv/bin/python -m evals.run_questions --questions evals/questions.jsonl --xaf export/audit.xaf`

**Step 6: Commit**

```bash
git add evals/question_matrix.py evals/generate_questions.py evals/run_questions.py \
  evals/questions.jsonl evals/README.md tests/test_question_corpus.py tests/test_question_runner.py
git commit -m "test: add 1000-question Exact conversation evaluation"
```

### Task 13: Full verification and browser end-to-end audit

**Files:**
- Modify: `README.md`
- Modify: `.env.example`
- Modify as required: tests and implementation files found by verification

**Step 1: Update operational and conversational documentation**

Document authentication enforcement, division semantics, confirmations, completeness metadata,
capability search/description, error recovery, the question runner, and the refresh-token migration.
Correct hosted URLs and remove any guidance contradicted by runtime behavior.

**Step 2: Run fresh local verification**

```bash
.venv/bin/pytest -q -p no:cacheprovider
.venv/bin/ruff check --no-cache src tests scripts evals
.venv/bin/ruff format --check --no-cache src tests scripts evals
.venv/bin/mypy src
.venv/bin/python -m build
uv run python scripts/postman_testrunner.py
.venv/bin/python -m evals.generate_questions --check --output evals/questions.jsonl
.venv/bin/python -m evals.run_questions --questions evals/questions.jsonl --xaf export/audit.xaf
```

Expected: every command exits zero; corpus count is exactly 1,000; no factual or safety invariant
fails. If the pre-existing Ruff formatting debt remains in touched files, format only the touched
scope first, then run the full check and review the mechanical diff.

**Step 3: Run protocol smoke tests**

Use the official MCP SDK client against stdio, ordinary authenticated Streamable HTTP, and hosted
ASGI. Verify tools, resources, structured results, errors, authentication, and shutdown.

**Step 4: Run in-app browser checks**

Start the hosted app locally, navigate through onboarding without submitting credentials, inspect
the credential field and redirect URI, verify error/recovery pages, and confirm the deployed public
surface if reachable. Do not enter or transmit secrets.

**Step 5: Review all changes**

Dispatch a specification reviewer followed by a code-quality/security reviewer. Fix every critical
or important issue and repeat verification after the last change.

**Step 6: Commit documentation and verification adjustments**

```bash
git add README.md .env.example
git commit -m "docs: explain resilient Exact MCP workflows"
```
