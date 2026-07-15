# Exact MCP Resilience and Conversational Expressiveness Design

**Date:** 2026-07-15

## Goal

Make the Exact Online MCP safe under failure and concurrency, explicit about the scope and
completeness of every answer, and substantially easier for language models to use across ordinary
Dutch and English accounting conversations. Measure the result with a deterministic corpus of
exactly 1,000 questions derived from the supplied XAF audit export.

## Evidence and current baseline

The current worktree exposes 23 tools, two resources, no prompts, and a generic gateway over 330
Exact endpoints. The local verification baseline is 145 passing tests, clean Ruff lint, clean
strict mypy, a successful package build, a successful official-SDK stdio smoke test, and 27 passing
Postman mock requests. Ruff formatting currently reports seven pre-existing files that need
formatting.

The supplied `export/audit.xaf` is an XAF 3.2 export containing:

- 91 general-ledger accounts and 28 customer/supplier masters;
- 10 VAT codes and 12 accounting periods;
- 28 opening-balance lines;
- 8 journals, 132 balanced transactions, and 615 transaction lines;
- 166 A/R and A/P subledger lines with reconciliation references.

The nominal fiscal scope is 2025, but actual transaction activity ends on 2025-10-01. This is a
concrete example of why a technically valid total can still be misleading without observed-range
and completeness metadata.

Discovery found four release-blocking defects:

1. Hosted request/response logging emits credentials, bearer tokens, authorization codes, access
   tokens, and refresh tokens.
2. The configured inbound bearer token is not enforced by local Streamable HTTP mode.
3. Local production startup hardcodes division `4487358`, while `administration_current` can reset
   an explicitly selected division to the user's Exact default.
4. `draft_sales_order` performs a write without a mechanical confirmation gate.

Additional high-impact defects include request-local hosted OAuth and rate-limit state, missing
refresh-token issue-time persistence, concurrency-unsafe rate budgeting, unbounded search-tool
pagination, partial financial aggregates presented as totals, a partial hand-written hosted
JSON-RPC implementation, loose output schemas, and endpoint discovery with no field/key/parameter
metadata.

## Chosen approach

Use a layered improvement rather than a narrow security patch or a new XAF query product.

1. Fix security and tenant-routing defects before running broad evaluations.
2. Make transport, authentication, rate limiting, pagination, and errors correct under concurrency
   and partial failure.
3. Add shared response semantics for scope, provenance, truncation, and metric definitions.
4. Add semantic operation discovery and endpoint description without flooding the MCP tool list.
5. Build and repeatedly run the 1,000-question corpus against the real MCP stack with a deterministic
   Exact emulator derived from the XAF data.

The XAF file is an evaluation oracle and design reference, not a new production ingestion format.
This keeps the product focused on live Exact Online while still testing the depth of accounting
questions the data model should support.

## Architecture

### Runtime and security boundary

Both stdio/ordinary HTTP mode and hosted mode use the same `ExactClient`, `ExactService`, and
`create_server` behavior. Hosted mode owns a bounded cache of per-installation/per-division runtime
objects so concurrent requests share OAuth refresh coordination and rate-limit state. Cache entries
hold the HTTP client, OAuth manager, Exact client, service, and FastMCP server and are closed on
eviction and application shutdown.

All logs pass through the existing redaction layer. Authorization headers, cookies, OAuth form
fields, client secrets, verifiers, codes, and token-shaped response fields are never logged. Tests
assert absence rather than presence of secrets.

Local HTTP bearer authentication is enforced at the ASGI boundary. Stdio remains unaffected.
Hosted endpoints continue to authenticate per installation/division and must use the official MCP
transport behavior rather than a partial JSON-RPC subset wherever the installed SDK permits.

### Division semantics

An explicit division is stable for the lifetime of a scoped runtime. Reading the current
administration must not mutate routing. Discovering the Exact user's default division is a separate
operation used only when no division has been selected. Switching administration is state-changing
and must not be annotated read-only. Hosted division URLs cannot switch to another division inside
the same runtime.

### Write safety

Every mutating tool has a mechanical gate, not only a descriptive warning. `draft_sales_order`
gains `confirm: bool = false`. Generic writes and goods delivery retain their confirmation gates.
Write errors distinguish a definitely rejected operation from an unknown commit state. Tool
annotations accurately represent read-only, mutating, destructive, and idempotent behavior.

### Resilience

Rate limiting coordinates concurrent calls per division, reserves capacity before dispatch, honors
minute and daily budgets, and rechecks the budget before every retry. GET requests retry bounded
network, 429, and 5xx failures with jitter and server hints. Writes are not automatically retried
after ambiguous transport failures. A rejected 401 can trigger one token refresh path when the
operation is safe to repeat. End-to-end operation deadlines prevent page and retry multiplication
from consuming an entire conversation indefinitely.

Pagination returns only the requested page. Aggregations either consume all pages within an
explicit budget or report `partial` with counts, continuation information, and a reason. No result
may expose `has_more` while simultaneously presenting a first-page aggregate as a complete total.

### Conversational surface

Preserve the existing purpose-built tools for compatibility, and add two compact discovery tools:

- `exact_capabilities_search`: rank purpose-built workflows and generic Exact operations from a
  natural-language intent, including Dutch/English synonyms, safety class, required inputs, and
  known limitations.
- `exact_operation_describe`: return the selected operation's input/output contract, fields, keys,
  parameters, examples, availability caveats, and source documentation.

The 330-endpoint catalog remains behind search/execute rather than becoming 330 tools. Registry
metadata is enriched incrementally and explicitly marks unknown fields instead of encouraging the
model to guess.

Analytical tools return a common envelope:

- `summary` and `rows` for conversational use;
- `scope`: division, currency, requested period, observed period, and as-of timestamp;
- `completeness`: complete/partial/unknown, retrieved count, truncation reason, and continuation;
- `provenance`: Exact endpoint, filters, metric definition, and relevant record identifiers;
- `warnings`: ambiguity, unavailable dimensions, privacy, or unsupported inference.

Machine-readable output schemas describe these envelopes. Resources expose metric definitions,
current routing, connector capability coverage, and endpoint/operation descriptions. Workflow
prompts are added only for stable multi-step tasks such as an audit check or period review and are
not relied on for core correctness.

## Error handling

All expected failures become structured tool execution errors with:

- stable code and safe human-readable message;
- `retryable` and optional `retry_after_seconds`;
- operation state: `not_started`, `rejected`, `partial`, or `unknown`;
- recovery action and concrete missing/invalid fields;
- Exact request ID and status where safe;
- alternative operation suggestions when the requested capability is unavailable.

Unexpected exceptions are logged with a correlation ID but returned without stack traces or
secrets. Invalid JSON, unsupported JSON-RPC methods, malformed batches, cancellation, and resource
requests receive protocol-correct responses from the SDK transport.

## Exactly 1,000 conversational questions

The corpus is the Cartesian product of 20 domains, 10 intents, and 5 conversational modes:

- Domains: scope/header, company, counterparties, contact/address, bank/tax identifiers, general
  ledger, reporting taxonomy, dimensions/users, VAT master, periods, opening balance, opening
  subledgers, journals, transactions, transaction lines, documents/invoices/quantity/cost,
  transaction VAT, A/R, A/P, and cross-record audit/completeness.
- Intents: lookup, count/distribution, filter/search, aggregate, rank, compare, trend, drill/join,
  reconcile/validate, and explain/provenance.
- Modes: direct, ambiguous/Dutch/paraphrased/typo, contextual follow-up, boundary/null/leading-zero,
  and unsupported/out-of-scope.

This produces exactly `20 × 10 × 5 = 1,000` unique cases. Each case records the question, expected
operation sequence, allowed clarification, required and forbidden arguments, fixture-derived fact
assertions, completeness expectation, privacy expectation, and mutation prohibition.

The harness parses the XAF into a precision-safe immutable fixture and exposes a deterministic
`httpx.MockTransport` Exact emulator. It runs the real OAuth → Exact client → service → FastMCP
stack, including pagination, 400/401/403/429/5xx, timeouts, malformed payloads, token rotation, and
concurrent calls. Scores cover operation discovery, schema-valid calls, factual assertions,
clarification quality, safety, completeness/provenance, recovery, and tool-call efficiency.

## Testing and release gates

Every behavior change follows red-green-refactor. The release gates are:

1. Secret canaries never appear in captured logs or MCP errors.
2. Local HTTP authentication, division isolation, and mechanical confirmation tests pass.
3. Hosted concurrent refresh and rate-limit tests pass.
4. Protocol tests cover initialize, tools, resources, ping, invalid JSON, unsupported methods,
   notifications, and cancellation where supported.
5. Pagination and aggregate completeness invariants pass for empty, one-page, multi-page, capped,
   and failed-page scenarios.
6. The generated corpus contains exactly 1,000 unique questions with balanced matrix coverage.
7. All deterministic corpus assertions pass, with measured before/after routing and recovery scores.
8. Full pytest, Ruff lint/format, strict mypy, package build, SDK stdio smoke, hosted HTTP smoke,
   Postman mock, and in-app browser onboarding checks pass.

## Compatibility and migration

Existing tool names remain available. New required safety behavior may reject calls that previously
performed writes without confirmation; this is an intentional security correction. Result payloads
retain existing `summary`/`rows` fields while adding metadata. Hosted storage receives an additive
migration for refresh-token issue time. Unknown endpoint schemas remain callable only through the
same constrained identifier/filter rules and are clearly labeled as incomplete metadata.
