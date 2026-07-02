# Exact Online MCP

A secure Model Context Protocol server for Exact Online order handling and accounting. It keeps Exact OAuth credentials inside the server, resolves divisions and Exact GUIDs, constrains OData queries, and protects write operations with typed validation.

## Requirements

- Python 3.12 or newer
- An Exact Online account
- An Exact Online OAuth application with a client ID, client secret, and redirect URI

The default endpoints target the Netherlands (`start.exactonline.nl`). Override the three Exact URL settings shown below if your Exact account uses another regional host.

## Install for development

Clone the repository and create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

For a runtime-only installation, use:

```bash
python -m pip install .
```

## Configure Exact Online

Copy the example environment file:

```bash
cp .env.example .env
```

Generate the key used to encrypt OAuth tokens at rest:

```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Set the required values in `.env`:

```dotenv
EXACT_MCP_EXACT_CLIENT_ID=your-client-id
EXACT_MCP_EXACT_CLIENT_SECRET=your-client-secret
EXACT_MCP_EXACT_REDIRECT_URI=http://127.0.0.1:8765/oauth/callback
EXACT_MCP_TOKEN_ENCRYPTION_KEY=the-generated-fernet-key
EXACT_MCP_TOKEN_FILE=/absolute/path/to/exact-mcp/tokens.enc
```

The redirect URI must exactly match the URI registered for your Exact OAuth application. HTTPS is required except for loopback addresses such as `127.0.0.1` and `localhost`.

For a non-Netherlands Exact environment, also set:

```dotenv
EXACT_MCP_EXACT_API_BASE=https://start.example/api/v1
EXACT_MCP_EXACT_AUTHORIZE_URL=https://start.example/api/oauth2/auth
EXACT_MCP_EXACT_TOKEN_URL=https://start.example/api/oauth2/token
```

Replace `start.example` with the regional Exact Online host used by your account.

## Authorize the server

Generate an Exact authorization URL:

```bash
exact-mcp auth-url
```

Open the printed URL, sign in to Exact Online, and approve access. Exact redirects to the configured callback URI with a `code` query parameter. Copy that code and exchange it:

```bash
exact-mcp exchange-code 'CODE_FROM_REDIRECT'
```

Confirm that encrypted credentials are available:

```bash
exact-mcp auth-status
```

The resulting access and refresh tokens are encrypted in `EXACT_MCP_TOKEN_FILE`. Do not commit `.env`, the encryption key, or the token file.

## Run over stdio

Stdio is the normal transport when the MCP client launches the server as a child process:

```bash
exact-mcp serve --transport stdio
```

Run the command from the repository directory when relying on `.env`. Otherwise, provide the `EXACT_MCP_*` variables through the process environment.

A generic MCP client configuration looks like this:

```json
{
  "mcpServers": {
    "exact-online": {
      "command": "/absolute/path/to/exact-mcp/.venv/bin/exact-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "EXACT_MCP_EXACT_CLIENT_ID": "your-client-id",
        "EXACT_MCP_EXACT_CLIENT_SECRET": "your-client-secret",
        "EXACT_MCP_EXACT_REDIRECT_URI": "http://127.0.0.1:8765/oauth/callback",
        "EXACT_MCP_TOKEN_ENCRYPTION_KEY": "your-fernet-key",
        "EXACT_MCP_TOKEN_FILE": "/absolute/path/to/exact-mcp/tokens.enc"
      }
    }
  }
}
```

Prefer your MCP client's secret-management mechanism over storing credentials directly in its configuration file.

## Run over Streamable HTTP

Configure the bind address and start the server:

```dotenv
EXACT_MCP_TRANSPORT=streamable-http
EXACT_MCP_HOST=127.0.0.1
EXACT_MCP_PORT=8000
```

```bash
exact-mcp serve --transport streamable-http
```

Clients connect to:

```text
http://127.0.0.1:8000/mcp
```

To require an inbound bearer token from remote MCP clients, set:

```dotenv
EXACT_MCP_INBOUND_BEARER_TOKEN=a-long-random-control-plane-token
```

Bind to a public interface only behind TLS and a trusted reverse proxy. The inbound MCP credential is separate from the outbound Exact OAuth token; MCP clients never receive the Exact token.

## Available workflows

The core tools described by the PRD are:

- `resolve_customer_id`: find Exact customer GUIDs from recognizable customer data.
- `draft_sales_order`: resolve customer/item codes and create an atomic draft order with nested lines.
- `retrieve_unpaid_invoices`: return normalized outstanding receivables for a customer.
- `execute_goods_delivery`: resolve open order lines and post a goods delivery. It requires `confirm=true` because it reduces stock.

Supporting read-only tools cover administration selection, account and item searches, VAT codes, warehouses, sales orders, and sales-order lines.

One server process is scoped to one Exact identity. Changing the active administration clears administration-specific warehouse and lookup state.

## Development checks

Run the complete local verification suite:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/mypy src
python -m build
```

The default test suite uses mocked HTTP transports and never calls Exact Online. Live integration tests, when present, require explicit environment configuration.

## Operational constraints

- Exact applies per-division minutely and daily API limits. The server tracks response headers, reserves capacity, and backs off on throttling.
- Ordinary `400`, `401`, `403`, and `404` responses are not retried automatically because Exact also limits repeated errors.
- Raw OData filters are not accepted from MCP callers. Search fields, selected fields, page sizes, and sort fields are allowlisted.
- Exact Online REST does not support payment/invoice reconciliation. This server does not emulate that operation.
- Never share `.env`, `tokens.enc`, client secrets, refresh tokens, or the Fernet key with an AI client.

## Troubleshooting

`authentication_required`
: Run `exact-mcp auth-url`, complete authorization, then run `exact-mcp exchange-code` again.

`403 Forbidden`
: Confirm that the authenticated Exact user can access the selected administration and that the OAuth application has the required permissions.

`rate_limited`
: Leave the server running. It uses Exact's reset headers and retries only safe transient failures.

No matching account or item
: Search with at least two characters and select one of the returned exact codes. The server rejects ambiguous identifiers before sending a write request.
