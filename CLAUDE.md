# VestedHR Pricing Tool

Localhost prototype of VestedHR's PEO pricing calculator. Replaces their Excel-based quoting workflow. Built in FastAPI + SQLite — final production version will be Ruby on Rails.

## Run the app

```
cd C:\workspaces\vested-hr-pricing
python seed.py          # first run only — safe to re-run (idempotent)
uvicorn server:app --reload --port 8000
```

Open: `http://localhost:8000/static/dashboard.html`
API docs: `http://localhost:8000/docs`

Use `python`, never `python3` — Windows machine, Python 3.14 at `C:/Users/asher/AppData/Local/Programs/Python/Python314/`.

## Reference documents

These live in a separate repo and are the source of truth. Read them before changing anything related to pricing logic, form fields, or data models.

| What | Path |
|---|---|
| Pricing math — all formulas, config values, calc logic | `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` |
| VHR requirements — form fields, sections, workflow, roles | `C:\workspaces\business\vested-hr\plan_drafts\pricing_tool_outline.md` |
| HTML prototypes (canonical visual reference) | `C:\workspaces\business\vested-hr\active\prototypes\` |
| Early requirements from Justin (VP Sales, partial) | `C:\workspaces\business\vested-hr\documents\app_requirments.md` |

`pricing_math.md` = source of truth for calculations.
`pricing_tool_outline.md` = source of truth for what VHR staff expect to see.

## Stack

| Layer | Tech |
|---|---|
| API | FastAPI |
| DB | SQLite via SQLAlchemy (sync) |
| Frontend | Vanilla HTML/CSS/JS — no framework |
| Styles | `static/style.css` shared, page-specific in `<style>` blocks |
| Shared JS | `static/app.js` — `apiGet`, `apiPost`, `apiPut`, `apiDelete`, `showToast`, `formatCurrency`, `formatPct` |

## Project structure

```
server.py           FastAPI app — mounts /static, registers all routers
database.py         SQLAlchemy engine, session, Base
models.py           ORM: SystemConfig, Client, WCLine, SutaLine, SutaRate, WCRate, WCGuideline, WCLoss
schemas.py          Pydantic schemas for all request/response shapes
seed.py             Idempotent — seeds SystemConfig defaults + 51 SUTA state rows + test client
routers/
  clients.py        GET/POST /clients, GET/PUT/DELETE /clients/{id}
  config.py         GET/PUT /config
  suta_rates.py     GET/PUT /suta-rates
  rates.py          GET /download/* and POST /upload/* for WC Rates, WC Guidelines, SUTA
  calculate.py      POST /calculate — runs full pipeline, returns summary (no DB write)
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
  config.html       System config — autosaves on change
  style.css         Shared styles
  app.js            Shared utilities
data/
  vested_hr.db      SQLite DB — persists across restarts
```

## Calculation pipeline

`POST /calculate` runs these in order. Each module is a pure function in `calc/`.

```
WSE → Workers' Comp → FICA → FUTA → SUTA → Admin Fee → Commission → Summary
```

All inputs come from the client payload. Config values (rates, factors) are loaded from the `SystemConfig` DB row. See `routers/calculate.py` for the orchestration.

## Key design decisions

- **FUTA**: Approach B only — `W × wage_base × rate × turnover_pct`. Turnover % is a required client input field, no default assumed.
- **WC manual rate**: Entered directly on the WC Codes table at intake. The 25K-row WC Rates lookup table is in the DB (`wc_rates`) but the VLOOKUP is not yet wired into calculations — see Known Gaps.
- **Config autosaves**: All system config fields save automatically 600ms after any change. No Save button.
- **SUTA client-reporting states**: CA, NY, NJ, PA, RI bill at the client's own rate. `vhr_min_rate = None` for these states.


## Management docs

| Doc | Purpose |
|---|---|
| `management/updates.md` | Changelog — what was built, what changed, current state of the data. Read this to get up to speed quickly. |
| `management/todo.md` | Full agent-ready brief per task — context, file pointers, and exactly what to build. |
| `management/status.json` | Machine-readable task state: `pending` / `in-progress` / `complete` / `blocked`. **Always read this first. Always update it when you finish work.** |

### Agent workflow
1. Read `management/status.json` — know what is done, in-progress, and blocked before touching anything
2. Pick a `pending` task, set it to `in-progress` in status.json, read its full brief in `todo.md`
3. Do the work, commit
4. Set the task to `complete` in status.json, commit that too
