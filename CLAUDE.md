# VestedHR Pricing Tool

Localhost prototype of VestedHR's PEO pricing calculator. Replaces their Excel-based quoting workflow. FastAPI + SQLite — final production version will be Ruby on Rails.

## Run

```
python seed.py          # first run only — idempotent
uvicorn server:app --reload --port 8000
```

App: `http://localhost:8000/static/dashboard.html` | API docs: `http://localhost:8000/docs`

Use `python`, never `python3` — Windows, Python 3.14 at `C:/Users/asher/AppData/Local/Programs/Python/Python314/`.

## Reference documents (source of truth — read before changing pricing logic or form fields)

| What | Path |
|---|---|
| Pricing math — formulas, config values, calc logic | `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` |
| VHR requirements — form fields, workflow, roles | `C:\workspaces\business\vested-hr\plan_drafts\pricing_tool_outline.md` |
| HTML prototypes — canonical visual reference | `C:\workspaces\business\vested-hr\active\prototypes\` |

## Stack

FastAPI / SQLite (SQLAlchemy sync) / Vanilla HTML+CSS+JS (no framework)

Shared styles: `static/style.css`. Page-specific styles: inline `<style>` blocks.  
Shared JS: `static/app.js` — `apiGet`, `apiPost`, `apiPut`, `apiDelete`, `showToast`, `formatCurrency`, `formatPct`.

## Key files

```
server.py           Mounts /static, registers all routers
database.py         Engine, session factory, Base
models.py           ORM models (see below)
schemas.py          Pydantic request/response shapes
seed.py             Seeds SystemConfig + 51 SUTA placeholder rows + test client (Acme Mfg TX)
routers/
  clients.py        GET/POST /clients, GET/PUT/DELETE /clients/{id}
  config.py         GET/PUT /config
  suta_rates.py     GET/PUT /suta-rates
  rates.py          GET /download/* and POST /upload/* for WC Rates, WC Guidelines, SUTA
  calculate.py      POST /calculate — full pipeline, returns summary (no DB write)
calc/
  wse.py            WSEs = FTEs + 0.75 × PTEs
  workers_comp.py   WC billing, cost, margin, vendor comparison
  fica.py           SS (per-WSE cap) + Medicare passthrough
  futa.py           Approach B: W × $7K × 0.6% × turnover_pct
  suta.py           Per-state billing/cost/profit + prior provider comparison
  admin_fee.py      3 methods: % of GWs, per-check, PEPM
  commission.py     Internal + external commission
  summary.py        Full deal summary rollup
static/
  dashboard.html    Client list, New Client modal, delete
  client.html       5-tab pricing form + live Deal Summary
  config.html       System config (autosaves on change)
data/
  vested_hr.db      SQLite DB
```

## Calculation pipeline

`POST /calculate` runs these in order (pure functions in `calc/`, orchestrated in `routers/calculate.py`):

```
WSE → Workers' Comp → FICA → FUTA → SUTA → Admin Fee → Commission → Summary
```

## Key design decisions

These are non-obvious choices made in Phase 1. Do not undo them without asking.

- **FUTA uses Approach B only**: `W × wage_base × rate × turnover_pct`. Turnover % is a required client input (`w2s_generated` field). No default assumed. Approach A (burden-rate display) is not used.
- **WC manual rate**: The `WCLine.manual_rate` field is entered directly on the client form. The 25K-row `wc_rates` DB table exists and is indexed by `concat` (state+code) but is **not yet wired into calculations** — see todo `wc-rates-vlookup`.
- **Config autosaves**: All system config fields save 600ms after any change. No Save button anywhere.
- **SUTA client-reporting states**: CA, NY, NJ, PA, RI bill at the client's own rate. These rows have `vhr_min_rate = None` and `client_reporting = True` in the DB.
- **WC carve-out**: `proposed_mod = 0` signals full carve-out; `calculate_wc` zeros all WC billing/cost when mod is 0.
- **WC state lists stored as comma-separated strings** in `SystemConfig`: `monopolistic_states` (WA/WY/ND/OH — always carve-out) and `mcp_states` (binding takes longer). These drive UI warnings, not calculation changes.
- **CSV upload replaces entire table**: `POST /upload/wc-rates`, `/upload/wc-guidelines`, `/upload/suta-rates` each delete all existing rows before inserting. There is no merge/upsert.
- **`POST /calculate` is stateless**: takes a full client payload, returns summary dict. Nothing is written to DB.
- **Sub-line records (WCLine, SutaLine, WCLoss) are replace-on-save**: `PUT /clients/{id}` deletes all existing child rows for a given type and re-inserts if the corresponding list is present in the payload.

## Data state (as of Phase 1 completion)

- All 51 SUTA state rows are **placeholder values** — tool will not produce accurate SUTA numbers until VHR provides real data.
- `wc_rates` and `wc_guidelines` tables are **empty** until VHR uploads CSV via config page.
- `wc_policy_adjustment` seeded at `0.0` — purpose not confirmed with VHR.

## Management docs

| Doc | Purpose |
|---|---|
| `management/status.json` | Task states: `pending`/`in-progress`/`complete`/`blocked`. Read first, update when done. |
| `management/todo.md` | Full brief per task — exact function names, file paths, endpoint signatures. |
| `management/updates.md` | Changelog — what was built, what changed. |

### Agent workflow
1. Read `management/status.json`
2. Pick a `pending` task, set to `in-progress`, read its brief in `todo.md`
3. Do the work, commit
4. Set to `complete` in `status.json`, commit
