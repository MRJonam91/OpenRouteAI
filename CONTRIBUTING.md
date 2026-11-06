# Contributing

Thank you for contributing to OpenRouteAI.

## Principles

1. **Local-first and private by design**: The gateway binds to loopback and never forwards traffic to remote servers without explicit configuration and transparent user consent.
2. **Deterministic & test-driven**: Any routing logic, provider fallback, or API handling must be covered by unit/contract tests.
3. **Core size bound**: Production Python code in `src/openrouteai` must remain under 1,500 lines of code, verified automatically in CI.
4. **Bilingual documentation**: Keep Italian and English versions of user-facing documentation aligned.

## Development workflow

```bash
python -m venv .venv
# Activate .venv (PowerShell: .\.venv\Scripts\Activate.ps1; Unix: source .venv/bin/activate)
python -m pip install -e '.[test]'
python -m pytest -q -p no:cacheprovider
```

## Licensing of contributions

By submitting a pull request, you agree that your contributions will be licensed under the project's [AGPL-3.0-only](LICENSE) license.
