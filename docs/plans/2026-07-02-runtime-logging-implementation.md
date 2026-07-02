# Exact MCP Runtime Logging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add comprehensive, sanitized runtime logging that exposes where MCP and Exact Online data flows succeed or fail.

**Architecture:** A small logging module owns configuration and recursive redaction. Existing CLI, MCP adapter, OAuth manager, Exact client, and rate limiter emit boundary events through standard Python loggers; INFO contains operational summaries and DEBUG contains sanitized payloads.

**Tech Stack:** Python 3.12, standard-library `logging`, `RotatingFileHandler`, FastMCP, httpx, Pydantic Settings, pytest.

---

### Task 1: Logging configuration and redaction

**Files:**
- Create: `src/exact_mcp/logging.py`
- Create: `tests/test_logging.py`
- Modify: `src/exact_mcp/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write failing configuration and redaction tests**

Test that the settings defaults are INFO, no file, 10 MiB, and five backups. Test environment parsing for DEBUG and a file path. Test recursive mappings/sequences plus free-form `Bearer secret` strings and assert every secret becomes `<redacted>`.

**Step 2: Run tests to verify RED**

Run: `.venv/bin/pytest tests/test_logging.py tests/test_config.py -q`

Expected: FAIL because the logging module and settings do not exist.

**Step 3: Implement minimal logging primitives**

Add `LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]`, settings fields, and validators. Implement `redact(value: Any) -> Any` using normalized sensitive keys and bearer-token masking. Implement `configure_logging(settings)` with a stderr `StreamHandler` and optional `RotatingFileHandler`, a timestamp/level/logger/message formatter, and idempotent handler replacement.

**Step 4: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_logging.py tests/test_config.py -q`

Expected: PASS.

### Task 2: CLI and server lifecycle logging

**Files:**
- Modify: `src/exact_mcp/cli.py`
- Modify: `src/exact_mcp/server.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_server.py`

**Step 1: Write failing lifecycle tests**

Test that `serve` configures logging before server construction. Capture logs around a successful and failing tool call; assert tool name, start/completion/error, duration, and sanitized DEBUG arguments/results are present. Assert stdout remains unused by logging.

**Step 2: Run tests to verify RED**

Run: `.venv/bin/pytest tests/test_cli.py tests/test_server.py -q`

Expected: FAIL because no lifecycle events are emitted.

**Step 3: Implement lifecycle events**

Configure logging in `serve`, then log startup settings without secrets. Extend `_tool_call` with tool name and argument metadata, monotonic timing, safe domain-error records, unexpected exception tracebacks, and sanitized DEBUG payloads. Log lifespan start, shutdown, and HTTP client close. Route every tool and resource through the wrapper.

**Step 4: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_cli.py tests/test_server.py -q`

Expected: PASS.

### Task 3: Exact HTTP, division, retry, and pagination logging

**Files:**
- Modify: `src/exact_mcp/client.py`
- Modify: `tests/test_client.py`

**Step 1: Write failing data-flow tests**

Capture DEBUG logs for a paginated request and assert request method/path/division, sanitized params, response status/duration, page counts, continuation, and final record count. Add retry/network/error cases and assert attempt, delay, status, request ID, and terminal failure. Include `access-secret` in the auth provider and response fixture, then assert it never appears in logs.

**Step 2: Run tests to verify RED**

Run: `.venv/bin/pytest tests/test_client.py -q`

Expected: FAIL because Exact client events are absent.

**Step 3: Implement HTTP data-flow events**

Use a module logger and monotonic clock. Log division discovery/selection, request start, sanitized DEBUG query/body, response metadata and DEBUG body, retry decisions/delays, network errors, invalid JSON, Exact errors, pagination progress, continuation validation, and client close. Never log request headers or raw OAuth tokens.

**Step 4: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_client.py -q`

Expected: PASS.

### Task 4: OAuth and rate-limit logging

**Files:**
- Modify: `src/exact_mcp/auth.py`
- Modify: `src/exact_mcp/rate_limit.py`
- Modify: `tests/test_auth.py`
- Modify: `tests/test_rate_limit.py`

**Step 1: Write failing state-transition tests**

Test token-missing, token-reuse, refresh-start/success, OAuth HTTP failure, rate-header update, reserve wait, and retry-delay events. Fixture secrets must not occur in captured output.

**Step 2: Run tests to verify RED**

Run: `.venv/bin/pytest tests/test_auth.py tests/test_rate_limit.py -q`

Expected: FAIL because state transitions are not logged.

**Step 3: Implement safe state-transition events**

Log only token state and expiry timing, never token values or OAuth form data. Log rate-limit division, remaining budgets, reset, wait duration, retry delay, and sleep completion.

**Step 4: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/test_auth.py tests/test_rate_limit.py -q`

Expected: PASS.

### Task 5: Operator documentation

**Files:**
- Modify: `README.md`

**Step 1: Document runtime logging**

Add environment examples, stderr behavior, optional rotation, INFO/DEBUG differences, data sensitivity warning, and a troubleshooting command using `EXACT_MCP_LOG_LEVEL=DEBUG`.

**Step 2: Verify documentation references actual settings**

Run: `rg -n "EXACT_MCP_LOG_(LEVEL|FILE|MAX_BYTES|BACKUP_COUNT)" README.md src/exact_mcp/config.py`

Expected: every documented setting appears in the settings model.

### Task 6: Full verification and live stdio smoke test

**Files:**
- Modify only if verification exposes a defect.

**Step 1: Run the full automated suite**

Run: `.venv/bin/pytest -q`

Expected: all tests pass.

**Step 2: Run static verification**

Run: `.venv/bin/ruff check src tests && .venv/bin/ruff format --check src tests && .venv/bin/mypy src`

Expected: all commands exit 0.

**Step 3: Build the package**

Run: `.venv/bin/python -m build`

Expected: wheel and source distribution build successfully.

**Step 4: Smoke-test stdio startup**

Start `EXACT_MCP_LOG_LEVEL=DEBUG .venv/bin/exact-mcp serve --transport stdio`, capture stdout and stderr independently, perform MCP initialization/list-tools if practical, and terminate cleanly. Verify stderr contains startup/runtime events while stdout contains only protocol messages and no secrets.

**Step 5: Inspect the final diff and requirement coverage**

Run: `git diff --check && git status --short && git diff -- src tests README.md docs/plans`

Expected: no whitespace errors, no unrelated edits, and every approved boundary represented in code or tests.

