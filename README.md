# OpenRouteAI

OpenRouteAI is a local-first, privacy-first AI gateway: one OpenAI-compatible API for local and cloud models, designed to work usefully even when offline.

## Product direction

- **One endpoint:** existing OpenAI SDK clients point at the gateway.
- **Local by default:** discover and prefer configured local providers such as Ollama.
- **Deliberate cloud escalation:** use a cloud provider only when a routing policy permits it.
- **Private by design:** redact or avoid sensitive request logging; no telemetry by default.
- **Zero-friction start:** a useful configuration should work with a local provider and minimal setup.

This is intentionally not a generic LiteLLM clone. The differentiator is an opinionated local/offline baseline, with cloud capability as an explicit extension.

## Status

Planning scaffold. No runtime implementation exists yet. See [`docs/`](docs/) for the product brief, architecture baseline, decisions, and staged delivery plan.

## Intended quick start

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:4000/v1", api_key="local")
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Ciao"}],
)
```

`auto` is a gateway routing alias, not a model supplied by an upstream provider.

## Repository map

- [`docs/product-brief.md`](docs/product-brief.md) — audience, scope and success measures.
- [`docs/architecture.md`](docs/architecture.md) — proposed MVP boundaries and data flow.
- [`docs/decisions/`](docs/decisions/) — ADRs; record choices before they become implicit.
- [`docs/roadmap.md`](docs/roadmap.md) — delivery slices and acceptance criteria.
- [`docs/research/`](docs/research/) — provider/API compatibility evidence and comparisons.

## Working agreements

1. Keep the OpenAI-compatible surface intentionally small at first; add endpoints only with contract tests.
2. Treat prompt, response, and credential handling as privacy-sensitive data flows.
3. Every routing decision must be explainable without retaining raw user content by default.
4. Validate offline operation in CI-like local tests before adding cloud conveniences.
5. Capture consequential decisions in an ADR.
