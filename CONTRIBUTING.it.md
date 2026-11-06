# Linee guida per i contributi

Grazie per il tuo interesse nel contribuire a OpenRouteAI.

## Principi chiave

1. **Local-first e privacy-first**: Il gateway si lega esclusivamente a loopback e non inoltra traffico verso provider remoti senza configurazione esplicita e consenso trasparente.
2. **Deterministico e guidato dai test**: Ogni logica di routing, fallback tra provider o gestione API deve essere verificata da test unitari o di contratto.
3. **Limite dimensionale del core**: Il codice Python di produzione in `src/openrouteai` deve restare sotto le 1.500 righe di codice, verificato automaticamente in CI.
4. **Documentazione bilingue**: Mantieni allineate le versioni in italiano e inglese della documentazione.

## Flusso di sviluppo

```bash
python -m venv .venv
# Attiva .venv (PowerShell: .\.venv\Scripts\Activate.ps1; Unix: source .venv/bin/activate)
python -m pip install -e '.[test]'
python -m pytest -q -p no:cacheprovider
```

## Licenza dei contributi

Inviando una pull request o un contributo al repository, accetti che il tuo codice venga distribuito sotto la licenza [AGPL-3.0-only](LICENSE) del progetto.
