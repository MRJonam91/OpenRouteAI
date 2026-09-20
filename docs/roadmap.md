# Delivery roadmap

## Phase 0 — Evidence and decisions

Deliverables:

- Verify OpenAI and Ollama request/response and streaming contracts from primary documentation.
- Compare the relevant local-first gateways and extract concrete differentiation, not feature lists.
- Select runtime, config format, package/distribution strategy, and supported operating systems.
- Write ADRs for each consequential choice.

Exit criteria: a reviewed MVP API contract and a reproducible local development setup.

## Phase 1 — Local vertical slice

Deliverables:

- `GET /health` and non-streaming `POST /v1/chat/completions`.
- Ollama discovery/configuration and a local-only `auto` router.
- OpenAI SDK contract tests plus real-provider integration tests where Ollama is available.
- Content-free structured logs and a default-deny remote-provider policy.

Exit criteria: offline chat request succeeds against a local Ollama model with documented setup.

## Phase 2 — Reliability and control

Deliverables:

- Streaming, timeouts, bounded retries, circuit breaking, and explicit fallback chains.
- Per-key rate limits and an opt-in cache with documented privacy semantics.
- Read-only local usage/decision dashboard.

Exit criteria: deterministic fallback and observable error behaviour under integration tests.

## Phase 3 — Cloud extension

Deliverables:

- Explicitly configured cloud/OpenAI-compatible adapters.
- Policy-controlled routing based on locality, capability, latency, and optional cost metadata.
- Credential-store integration and configuration validation.

Exit criteria: no cloud request is possible without a user-visible allow rule and tests prove it.

## Phase 4 — Extensibility

Deliverables:

- Stable provider-adapter extension contract.
- MCP integration design and a constrained experimental implementation, if the threat model permits it.

Exit criteria: extension APIs do not weaken the default privacy or routing guarantees.
