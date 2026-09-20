# ADR 0002: Start with a narrow OpenAI-compatible contract

- Status: Proposed
- Date: 2026-09-20

## Context

“OpenAI-compatible” can imply a very large and changing surface. Claiming broad compatibility before testing creates fragile integrations.

## Proposal

The first runtime slice supports non-streaming `POST /v1/chat/completions`, the documented generation fields chosen during Phase 0, and `model: "auto"`. Unsupported fields return clear errors. Streaming, Responses API, embeddings, tools, and other endpoints are separately specified and tested before release.

## Decision needed

Accept this scope after the Phase 0 compatibility research and runtime selection.
