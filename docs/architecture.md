# Architecture baseline

## Scope of this document

This is a design baseline, not an implementation commitment. Validate the provider APIs and OpenAI compatibility requirements in `docs/research/` before locking interfaces.

## Proposed MVP boundary

```text
OpenAI-compatible client
        |
        v
HTTP API adapter (/v1/chat/completions)
        |
        v
Request normalizer -----> Policy / privacy guard
        |                         |
        v                         v
Router <--- Health & capability registry
        |
        v
Provider adapter(s): Ollama first; OpenAI-compatible local server next
        |
        v
Response normalizer ---> Streaming/non-streaming response ---> Client
```

Cross-cutting services: configuration, secret resolution, rate limits, optional cache, and structured event logging.

## Design principles

- **Core is provider-neutral.** Provider adapters own protocol differences; the router sees capabilities and normalized results.
- **Policy precedes routing.** Eligibility is determined before scoring so a cloud provider cannot be selected merely because it is faster or higher quality.
- **Fail closed for privacy.** Remote providers require an explicit allow rule. Sensitive-content detection, if added, must be advisory until its accuracy is validated.
- **Explain choices.** A route decision contains reason codes, candidates considered, and non-content metrics.
- **Keep the data plane local.** No required hosted control plane or telemetry.

## Candidate core contracts

### Normalized request

Fields include requested model/alias, messages, stream flag, generation parameters, tenant/key identity, and an internal request ID. Preserve unsupported fields long enough to reject them accurately rather than silently dropping them.

### Provider capability

`provider_id`, `model_id`, supported endpoint/features, locality (`local` or `remote`), health, estimated cost class, and observed latency statistics. Credentials remain in the provider adapter/configuration layer.

### Routing policy

An ordered eligibility and scoring rule. Start with `local_only`, `local_preferred`, and `explicit_model`; defer unconstrained cost/quality optimisation until measurements and a clear model metadata source exist.

### Route decision event

Request ID, policy name, selected candidate, fallbacks attempted, reason codes, timestamps, status, and usage/cost metadata. Prompt and response content are excluded unless a separate diagnostic policy explicitly enables capture.

## First implementation slice

Implement only non-streaming `POST /v1/chat/completions`, `model: "auto"`, a static/default Ollama adapter, health check, local-only routing, and structured content-free logs. Add contract and integration tests around this vertical slice before caching, cloud fallback, dashboard, or rate limits.
