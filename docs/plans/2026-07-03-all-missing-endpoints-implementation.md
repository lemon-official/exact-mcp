# All Missing Exact Endpoints Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose all 330 Exact Online resources currently absent from the MCP through a validated registry-backed gateway.

**Architecture:** Generate a checked-in endpoint registry from the supplied catalogue and verified Exact routes. FastMCP discovery/read/write tools delegate through `ExactService`; callers select registry IDs and can never supply arbitrary URLs. Existing curated tools remain unchanged.

**Tech Stack:** Python 3.12, FastMCP, HTTPX, Pydantic 2, pytest, Ruff, mypy.

---

1. Generate `src/exact_mcp/endpoint_registry.json`; assert 330 resources and 639 operations.
2. Load immutable `EndpointSpec` records and implement bounded endpoint discovery.
3. Add structured gateway request models, safe comparisons, and entity-key formatting.
4. Extend `ExactClient` to render only registered normal, read, beta, bulk, sync, and function routes.
5. Implement structured reads plus confirmed create, update, delete, and POST-only actions.
6. Register six FastMCP tools with appropriate read-only, mutating, and destructive annotations.
7. Document discovery-first use, registry regeneration, tenant restrictions, and the exclusion of partially covered resources.
8. Run pytest, Ruff, formatting, mypy, and package-build verification before completion.

Acceptance requires a 330-resource/639-operation registry, no caller-controlled URL or raw
OData filter, no unconfirmed mutation, compatibility with existing tools, and offline tests.
