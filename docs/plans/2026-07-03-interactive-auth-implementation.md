# Interactive OAuth CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a one-command pasted-callback authorization flow, reliable encrypted refresh-token persistence, conditional manual refresh, and relative token-expiry status.

**Architecture:** Callback parsing and refresh decisions live beside the OAuth lifecycle rather than being duplicated in CLI commands. `OAuthManager.refresh_if_due()` returns a structured non-secret outcome for refreshed, too-young, and not-due states; the CLI formats those outcomes and relative durations. Existing encrypted token persistence remains unchanged, with stronger regression assertions proving the full token pair round-trips.

**Tech Stack:** Python 3.12, Typer, httpx, Pydantic, pytest, respx, cryptography/Fernet.

---

### Task 1: Callback URL parsing

**Files:**
- Modify: `src/exact_mcp/auth.py`
- Modify: `src/exact_mcp/tokens.py`
- Test: `tests/test_auth.py`

**Step 1: Write failing tests**

Add focused tests for a callback whose `code` contains a percent-encoded HTML entity and for callbacks with no code, an empty code, or duplicate code parameters. The valid case must return the URL-decoded and HTML-decoded authorization code; invalid cases must raise `AuthenticationRequiredError` without including callback contents.

**Step 2: Verify RED**

Run: `.venv/bin/pytest tests/test_auth.py -q`

Expected: collection/import failure because `authorization_code_from_callback` does not exist.

**Step 3: Implement minimally**

Add `authorization_code_from_callback(callback_url: str) -> str`. Use `urlsplit`, require an absolute callback URL, use `parse_qs(..., keep_blank_values=True)`, require exactly one non-empty `code`, and return `html.unescape(code)`.

**Step 4: Verify GREEN**

Run: `.venv/bin/pytest tests/test_auth.py -q`

Expected: all authentication tests pass.

### Task 2: Conditional refresh API

**Files:**
- Modify: `src/exact_mcp/auth.py`
- Test: `tests/test_auth.py`

**Step 1: Write failing tests**

Add tests proving:

- a token younger than 570 seconds returns `too_young` and makes no HTTP request;
- an eligible token outside the configured expiry skew returns `not_due` and makes no request;
- an eligible near-expiry token refreshes and stores the rotated refresh token;
- a successful response without a rotated refresh token preserves the stored refresh token;
- a refresh token at least 30 days old raises an actionable reauthorization error.

**Step 2: Verify RED**

Run: `.venv/bin/pytest tests/test_auth.py -q`

Expected: failures because the refresh result and public conditional refresh API do not exist.

**Step 3: Implement minimally**

Add a frozen `RefreshResult` carrying a `status` literal (`refreshed`, `too_young`, or `not_due`), the current tokens, and their age. Add `OAuthManager.refresh_if_due()` that loads tokens, serializes decisions through the existing refresh lock, enforces the 570-second minimum and 30-day refresh-token lifetime, refreshes only inside the expiry skew, and delegates token persistence to `_token_request`. Track refresh-token issuance separately from access-token issuance so preserving `previous_refresh_token` when Exact omits a replacement does not incorrectly extend its 30-day lifetime.

Keep `access_token()` behavior intact while sharing private helpers where doing so does not change its existing expiry behavior.

**Step 4: Verify GREEN**

Run: `.venv/bin/pytest tests/test_auth.py -q`

Expected: all authentication tests pass.

### Task 3: Interactive and refresh CLI commands

**Files:**
- Modify: `src/exact_mcp/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write failing tests**

Add CLI tests proving:

- `auth` prints the authorization URL, accepts a pasted callback, sends the decoded code, and saves tokens;
- the saved encrypted file decrypts through `EncryptedFileTokenStore` to the returned refresh token;
- malformed callbacks fail without a token request or secret output;
- `auth-refresh` reports the remaining wait for a token under 570 seconds;
- `auth-refresh` reports a not-due access token without an HTTP request;
- `auth-refresh` refreshes near expiry and persists the rotated refresh token;
- command help includes `auth` and `auth-refresh`.

**Step 2: Verify RED**

Run: `.venv/bin/pytest tests/test_cli.py -q`

Expected: failures because the commands do not exist.

**Step 3: Implement minimally**

Extract small internal helpers for URL creation and code exchange so `auth-url`, `exchange-code`, and `auth` compose the same behavior. Use `typer.prompt` for the callback URL. Add `auth-refresh`, map each `RefreshResult` status to a concise message, and retain sanitized `ExactMCPError` handling.

HTML-decode direct `exchange-code` input as well, while the interactive flow uses the callback parser.

**Step 4: Verify GREEN**

Run: `.venv/bin/pytest tests/test_cli.py -q`

Expected: all CLI tests pass.

### Task 4: Relative status output and documentation

**Files:**
- Modify: `src/exact_mcp/cli.py`
- Modify: `README.md`
- Test: `tests/test_cli.py`

**Step 1: Write failing tests**

Add deterministic tests for future and expired access tokens. Patch the CLI clock and assert messages such as `expires in 8m 12s` and `expired 45s ago`; no Unix timestamp should be printed.

**Step 2: Verify RED**

Run: `.venv/bin/pytest tests/test_cli.py -q`

Expected: status-format assertions fail against the current Unix-time output.

**Step 3: Implement minimally**

Add a duration formatter that emits whole minutes and seconds. Update `auth-status` to compare `expires_at` with `time.time()`. Update README authorization and troubleshooting instructions to prefer `exact-mcp auth`, document `auth-refresh`, explain the 570-second minimum, and retain the lower-level commands for scripting.

**Step 4: Verify GREEN**

Run: `.venv/bin/pytest tests/test_cli.py -q`

Expected: all CLI tests pass.

### Task 5: Full verification

**Files:**
- Verify only

**Step 1: Run the complete test suite**

Run: `.venv/bin/pytest -q`

Expected: all tests pass.

**Step 2: Run static and formatting checks**

Run: `.venv/bin/ruff check src tests`

Run: `.venv/bin/ruff format --check src tests`

Run: `.venv/bin/mypy src`

Expected: every command exits successfully with no findings.

**Step 3: Build the package**

Run: `.venv/bin/python -m build`

Expected: wheel and source distribution build successfully.

**Step 4: Review scope**

Run: `git diff --check && git status --short && git diff -- src/exact_mcp/auth.py src/exact_mcp/cli.py tests/test_auth.py tests/test_cli.py README.md`

Expected: no whitespace errors; only authentication implementation, tests, and documentation are part of this work, with pre-existing unrelated workspace changes left untouched.
