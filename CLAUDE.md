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

## Known gaps

These are things that need to be built or verified before going to production.

**Needs VHR staff answers before building:**
- SUTA rates: all 51 state rows are placeholder values — need VHR to confirm actual thresholds, billing rates, and cost rates
- WC Policy Adjustment (Sunz, 1.55%): seeded at 0.0 — when is it non-zero?
- MO SUTA: client files under own account but uses VHR's rate — confirm billing formula
- Open questions flagged throughout `pricing_math.md` (bolded questions in each section)

**Ready to build:**
- WC Rates VLOOKUP: wire the `wc_rates` DB table into `calc/workers_comp.py` so manual_rate is looked up by `state + wc_code` instead of entered manually
- WC code searchable dropdowns: `pricing_tool_outline.md` specifies searchable dropdowns for state and WC code — currently plain text inputs
- Benefits section: full pricing math is in `pricing_math.md` (Master Plan / Client Plan, PEPM tiers, Rate Tier Band) — not yet built
- Search: topnav search bar not wired to any API
- Auth: user menu is static, no role system (Admin / WC Admin / SUTA Admin / Sales / General User)

**Post-prototype (Rails phase):**
- HubSpot integration: auto-create Company, Deal, Contact on quote completion
- Approval workflow: tasks for Justin (pricing), John (WC), Nate (benefits)
- Generate Doc: client-facing proposal PDF
- Client Review tab: actual payroll vs projected, ratio analysis
- New Client Onboarding doc generation

---

## Management docs

| Doc | Purpose |
|---|---|
| `management/updates.md` | Changelog — what was built, what changed, current state of the data. Read this to get up to speed quickly. |
| `management/todo.md` | Prioritised to-do items. Each item is a full agent-ready brief with context, file pointers, and what to build. |
