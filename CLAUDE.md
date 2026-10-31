# app-scout

Daily pipeline that turns repeated pain in trending iOS apps into small, app-factory-ready app ideas.

- Running the daily analysis: follow `SCOUT.md` exactly.
- Data lives on the orphan `data` branch (rewritten daily by `.github/workflows/collect.yml`); never commit data to `main`.
- `main` holds only code, `SCOUT.md`, `templates/`, `reports/`, `briefs/`, `ideas/ledger.json`.
- Free sources only. iOS only. No games, medical or finance.
- Tuning: `collector/config.json` (volumes, genres, thresholds), `scout/themes.py` (triage keywords), `SCOUT.md` (gates and scoring).
