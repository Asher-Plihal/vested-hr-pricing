# VestedHR Pricing Tool

Localhost prototype of VestedHR's PEO pricing calculator. Replaces their Excel-based quoting workflow. FastAPI + SQLite — final production version will be Ruby on Rails.

## Run

```
python testing/seed.py      # first run only — idempotent
uvicorn server:app --reload --port 8000
```

App: `http://localhost:8000/static/dashboard.html` | API docs: `http://localhost:8000/docs`

Use `python`, never `python3` — Windows, Python 3.14 at `C:/Users/asher/AppData/Local/Programs/Python/Python314/`.

## Reference documents (read before changing pricing logic or form fields)

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
models.py           ORM models
schemas.py          Pydantic request/response shapes
testing/seed.py     Seeds SystemConfig defaults — run once on fresh DB
testing/seed_client.py  Creates Hartman Industrial LLC test client — idempotent
routers/
  clients.py        GET/POST /clients, GET/PUT/DELETE /clients/{id}
  config.py         GET/PUT /config
  suta_rates.py     GET/PUT /suta-rates
  rates.py          GET /download/* and POST /upload/* for WC Rates, WC Guidelines, SUTA
  calculate.py      POST /calculate — full pipeline, returns summary (no DB write)
controllers/
  workers_comp.py   WC billing, cost, margin, vendor comparison (Workers Comp tab)
  taxes.py          FICA, FUTA, SUTA — merged tax calcs (Taxes tab)
  admin.py          3 methods: % of GWs, per-check, PEPM (Admin tab)
  commission.py     Internal + external commission
  benefits.py       Placeholder — Benefits tab not yet implemented
  proposal.py       admin_overview + wc_overview → Proposal tab
  summary.py        taxes_overview + other_items + commissions → Analysis & Summary tab
static/
  dashboard.html    Client list, New Client modal, delete
  client.html       5-tab pricing form + live Deal Summary
  config.html       System config (autosaves on change)
data/
  vested_hr.db      SQLite DB
```

## Calculation pipeline

`POST /calculate` — pure functions in `controllers/`, orchestrated in `routers/calculate.py`:

```
WSE → Workers' Comp → FICA → FUTA → SUTA → Admin Fee → Commission → Summary
```

## Key design decisions

Non-obvious choices. Do not undo without asking.

- **FUTA Approach B only**: `W × wage_base × rate × turnover_pct`. Client inputs a direct decimal `futa_turnover_rate` (can exceed 1.0 when W-2s outnumber average headcount). Approach A not used.
- **WC rate auto-lookup**: `controllers/workers_comp.py` queries `wc_rates` by `state+code` concat key. Falls back to `WCLine.manual_rate` if not found or db=None. Rate field in `client.html` is readonly and auto-populated.
- **SUTA client-reporting states**: ~22 states where the client files under their own account (`client_reporting=True`): AK, CT, DE, IA, KS, KY, MA, ME, MI, MN, MS, MT, NE, NV, OH, PA, RI, SC, SD, TN, VT, WA. CA, NY, NJ are VHR-reporting with real rates.
- **Config autosaves**: All system config fields save 600ms after any change. No Save button.
- **WC carve-out**: `proposed_mod = 0` zeros all WC billing/cost in `calculate_wc`.
- **WC state lists**: `SystemConfig.monopolistic_states` and `mcp_states` are comma-separated strings. Drive UI warnings only, not calc changes.
- **CSV upload replaces entire table**: `/upload/wc-rates`, `/upload/wc-guidelines`, `/upload/suta-rates` delete all rows before inserting. No merge/upsert. Rate updates go through the config page upload buttons — no script needed.
- **`POST /calculate` is stateless**: full client payload in, summary dict out. Nothing written to DB.
- **Sub-line replace-on-save**: `PUT /clients/{id}` deletes and re-inserts WCLine, SutaLine, WCLoss rows when those lists are present in the payload.

## Data state

- `wc_rates`: 24,965 rows (2026 UWIC rates). Future updates via config page CSV upload.
- `wc_guidelines`: 19,552 rows. Reference only — not used in billing math.
- `suta_rates`: 51 states, real VHR rates. Rates stored as decimals (0.027 = 2.7%).
- `wc_policy_adjustment`: seeded at 0.0 — purpose not confirmed with VHR.

## Management docs

| Doc | Purpose |
|---|---|
| `management/status.json` | Active tasks only — `pending`, `in-progress`, `blocked`, `deferred`. Full brief lives in the `brief` field of each entry. Completed tasks are deleted. |
| `management/updates.md` | Permanent changelog. Completed task context lives here. |
| `management/questions.md` | Open questions for VHR staff. Each has a direct code consequence when answered. |
| `management/notes.md` | Context and decisions that are true now but may change with further VHR input. |

Completed tasks are never left in `status.json` — they are deleted and a summary entry is added to `updates.md` instead. Read `updates.md` to know what's been done. Read `status.json` to know what's left.

### Agent workflow
1. Read `management/updates.md` — know what's already done
2. Read `management/status.json` — pick a `pending` task, set it to `in-progress`
3. Read the `brief` field of that task for full instructions
4. Do the work, commit
5. Delete the task from `status.json`. Add a summary entry to `management/updates.md`. Commit.
