# Product brief — OpenRouteAI

## Problem

Developers who use several AI models have to maintain provider-specific clients, credentials, retry logic, routing rules, and observability. Existing multi-provider gateways are powerful, but a user who primarily runs local models can face excessive configuration, cloud-first assumptions, and unclear privacy behaviour.

## Product thesis

OpenRouteAI provides a single OpenAI-compatible endpoint that is useful immediately with a local model server, stays usable offline, and escalates to cloud models only through explicit configuration and policy.

## Primary users

1. Privacy-conscious developers running Ollama or another local OpenAI-compatible server.
2. Small teams that want a simple local default with controlled cloud fallback.
3. Self-hosters who need provider-neutral application code and transparent operations.

## MVP user journey

1. User starts a local provider (initially Ollama).
2. User runs the gateway with defaults or a short configuration file.
3. Existing OpenAI SDK code targets `http://localhost:4000/v1` with any non-empty local key.
4. A request with `model: "auto"` is routed to a healthy eligible local model.
5. If the local attempt fails, an explicitly enabled fallback may run; otherwise the API returns a clear, OpenAI-shaped error.
6. The user can inspect a privacy-preserving decision record: selected route, reason, latency, status, and cost metadata where applicable.

## Non-goals for the first release

- Reimplement every provider feature or all LiteLLM integrations.
- Autonomous cloud use or silently exporting prompts.
- A distributed multi-tenant SaaS control plane.
- Full MCP proxying (reserve an extension boundary first).
- A rich dashboard before reliable routing and API compatibility exist.

## Success measures

- A fresh offline installation routes an OpenAI SDK chat-completions request to Ollama in under ten minutes.
- Compatible clients receive predictable OpenAI-style responses and errors for the documented MVP subset.
- No prompt or response body is persisted by default.
- Fallback behaviour is deterministic, testable, and visible in metadata/logs without raw content.

## Open questions to research before implementation

- Which API surface is the MVP: Chat Completions only, or Responses API too?
- Which backend/runtime gives the best packaging and streaming ergonomics on Windows, Linux, and macOS?
- What exact provider capability contract is needed beyond Ollama?
- Can caching be opt-in and content-safe by default, and what cache key semantics are acceptable?
- What routing signals can be collected locally without leaking prompts?
