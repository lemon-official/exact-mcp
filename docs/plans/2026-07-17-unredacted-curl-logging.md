# Unredacted cURL Logging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Emit full, copyable cURL commands for every Exact API and OAuth request at debug level.

**Architecture:** Add a small shared formatter that shell-quotes URLs, headers, and JSON or form bodies without redaction. Invoke it immediately before `ExactClient` dispatches an API request and before `OAuthManager` dispatches a token request. Existing informational logs are unchanged; the new explicit debug event is intentionally sensitive.

**Tech Stack:** Python 3.12+, `httpx`, standard-library `json` and `shlex`, `pytest`, `pytest-asyncio`.

---

### Task 1: Add the cURL formatter

**Files:**
- Modify: `src/exact_mcp/logging.py`
- Test: `tests/test_logging.py`

**Step 1: Write the failing test**

Add a test for `curl_command()` using a GET URL with OData parameters and an `Authorization: Bearer token` header. Assert the output begins with `curl`, preserves the literal token and `$filter` value, and shell-quotes each argument. Add a JSON-body assertion including `--data-raw` and compact JSON.

**Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_logging.py::test_curl_command_preserves_full_request_values -v`

Expected: FAIL because `curl_command` does not exist.

**Step 3: Write minimal implementation**

Add `curl_command(method, url, headers, *, json_body=None, form_body=None) -> str`. Use `shlex.quote` for every value, `json.dumps(..., separators=(",", ":"))` for JSON, and `urllib.parse.urlencode` for form data. Reject simultaneous JSON and form bodies with `ValueError`.

**Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_logging.py::test_curl_command_preserves_full_request_values -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/exact_mcp/logging.py tests/test_logging.py
git commit -m "feat: add curl command formatter"
```

### Task 2: Log every Exact API request

**Files:**
- Modify: `src/exact_mcp/client.py`
- Test: `tests/test_client.py`

**Step 1: Write the failing test**

Create a MockTransport-backed request with an OData `$filter`, bearer token, and JSON payload. Capture `exact_mcp.client` debug logs and assert one `exact_curl` event includes the HTTP method, URL, unredacted query value, `Authorization` header, and body.

**Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_client.py::test_client_debug_logs_full_curl_command -v`

Expected: FAIL because no cURL event is emitted.

**Step 3: Write minimal implementation**

Import `curl_command` into `client.py`. After the API token is available and immediately before `self._http.request`, log `exact_curl %s` at debug level using the resolved URL, supplied parameters, headers, and JSON body. Build the logging URL with `httpx.URL(..., params=...)`; leave the actual dispatch unchanged.

**Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_client.py::test_client_debug_logs_full_curl_command -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/exact_mcp/client.py tests/test_client.py
git commit -m "feat: log Exact API curl commands"
```

### Task 3: Log OAuth token calls

**Files:**
- Modify: `src/exact_mcp/auth.py`
- Test: `tests/test_auth.py`

**Step 1: Write the failing test**

Create an OAuth token exchange using MockTransport and capture `exact_mcp.auth` debug logs. Assert the `exact_curl` event contains the token URL and unredacted `client_secret`, `code` or `refresh_token`, and `grant_type` form values.

**Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_auth.py::test_oauth_debug_logs_full_curl_command -v`

Expected: FAIL because OAuth calls do not log cURL commands.

**Step 3: Write minimal implementation**

Import `curl_command` into `auth.py`. Immediately before `self._http.post`, emit the `exact_curl` debug event using `POST`, the token URL, an Accept header, and token form data.

**Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_auth.py::test_oauth_debug_logs_full_curl_command -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/exact_mcp/auth.py tests/test_auth.py
git commit -m "feat: log OAuth curl commands"
```

### Task 4: Verify the integrated change

**Files:**
- Verify: `src/exact_mcp/logging.py`
- Verify: `src/exact_mcp/client.py`
- Verify: `src/exact_mcp/auth.py`
- Verify: `tests/test_logging.py`
- Verify: `tests/test_client.py`
- Verify: `tests/test_auth.py`

**Step 1: Run targeted tests**

Run: `uv run pytest tests/test_logging.py tests/test_client.py tests/test_auth.py -v`

Expected: PASS.

**Step 2: Run linting**

Run: `uv run ruff check src/exact_mcp tests`

Expected: no findings.

**Step 3: Run the full suite**

Run: `uv run pytest`

Expected: PASS.
