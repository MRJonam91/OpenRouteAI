# ADR 0001: Local-first and explicit cloud escalation

- Status: Accepted for the planning baseline
- Date: 2026-09-20

## Context

The product needs differentiation in an established multi-provider gateway category. A generic provider matrix would create high maintenance cost and weak product focus.

## Decision

The gateway will prefer local eligible providers by default and will not select a remote provider unless a configuration and routing policy explicitly permit it. Offline local operation is a first-class acceptance criterion.

## Consequences

- Provider metadata must record locality and routing policies must evaluate it before scoring.
- Remote credentials and remote routes need clear configuration validation.
- The early provider set remains intentionally narrow: Ollama first, then compatible local servers.
- Some users who want a cloud-first proxy will be better served by another project; that is acceptable.
