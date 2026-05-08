# Update Log — VestedHR Pricing Tool

Most recent entry at the top. Add an entry when a task completes. This is where completed task context lives — status.json and todo.md only track what's left to do.

---

### 2026-05-08 — sheets-upload-fix complete

**Task:** `sheets-upload-fix`

Compared all three rate table handlers in `routers/rates.py` against the live Google Sheet (ID: `1NcHPIhsF1uIOQNFWBo-ZpeXWXNewYcEyinx6-IdIaMc`) using the Sheets API. WC Rates and WC Guidelines column names matched exactly — no changes needed for those. SUTA Rates had two issues:

1. **Missing "State Name" column in download.** Sheet has `State Name | State | ...`; download was emitting `State | ...`. Fixed by adding `State Name` as the first column, backed by a `_STATE_NAMES` lookup dict in `routers/rates.py`.

2. **SUTA rate percentage-to-decimal conversion missing from upload.** The sheet stores `VHR Min Rate` and `Our Cost` as percentages (e.g., 2.7 for 2.7%). The DB stores decimals (0.027) for the calc pipeline (`suta_bill = billing_rate * taxable_gws`). The upload handler was storing raw sheet values without dividing by 100. Fixed: upload now divides both fields by 100. Download now multiplies by 100 so round-trip from sheet → upload → download → sheet is lossless.

All three uploads confirmed working (24,965 / 19,552 / 51 rows) with correct values. DB restored from the full Google Sheet after the fix.

---

### 2026-05-08 — Phase 2 data foundation complete

**Tasks completed:** `import-rate-data`, `wc-rates-vlookup`, `wc-code-search-endpoint`, `seed-client`, `suta-rates-verify`

**Rate data imported from `Pricing Template 03.10.26_ALL SHEETS.xlsx`:**
- `wc_rates`: 24,965 rows (2026 UWIC rates). Source sheet: "WC Cost Rates" cols A–H. Class codes stored as strings. Rates are per $100 payroll, used as-is.
- `wc_guidelines`: 19,552 rows. Source sheet: "WC Sunz Guidelines". Reference only — not used in billing math.
- `suta_rates`: 51 states. Source sheet: "SUTA Cost Rates". **Rates in spreadsheet are in percentage form (2.7 = 2.7%) — divided by 100 on import.** Exception: values already < 0.10 treated as already decimal.

**SUTA client-reporting states corrected.** The original seed had CA, NY, NJ, PA, RI as client-reporting. The real spreadsheet data shows ~22 client-reporting states: AK, CT, DE, IA, KS, KY, MA, ME, MI, MN, MS, MT, NE, NV, OH, PA, RI, SC, SD, TN, VT, WA. CA, NY, NJ are VHR-reporting with real rates (6.82%, 4.5%, 3.75%). CLAUDE.md Key Design Decisions entry for SUTA is now outdated — the spreadsheet is authoritative.

**WC VLOOKUP wired:** `calc/workers_comp.py` now accepts `db=None` and queries `wc_rates` by `state+code` concat key per line. Falls back to `manual_rate` if not found or db is None. `routers/calculate.py` passes `db`. Rate field in `client.html` is readonly and auto-populates via `GET /wc-rate?state=&code=`.

**Test client:** `testing/seed_client.py` creates Hartman Industrial LLC (TX, biweekly, proposed_mod=0.88, admin_rate=3.5%, 2 WC lines: TX5190 + TX8810, 1 TX SUTA line). Idempotent. Does not touch SystemConfig.

**Scripts to run on a fresh DB:**
```
python testing/seed.py          # SystemConfig defaults + 51 SUTA placeholder rows
python testing/import_rates.py  # real WC and SUTA rate data from Excel
python testing/seed_client.py   # Hartman Industrial LLC test client
```

---

### 2026-05-08 — Phase 1 complete, entering Phase 2 (tweak & test)

**What was built:**
- Full FastAPI + SQLite app scaffolded from scratch at `C:\workspaces\vested-hr-pricing\`
- Three pages rebuilt from approved HTML prototypes: dashboard (client list), client pricing form (5 tabs + live Deal Summary), system config (autosaves on change)
- Full calculation pipeline: WSE → WC → FICA → FUTA → SUTA → Admin Fee → Commission → Summary
- CSV upload/download wired for WC Rates (~25K rows), WC Guidelines (~19.5K rows), SUTA Rates (51 states)
- New Client modal on dashboard, delete client support, client list with status badges
- Test client seeded: Acme Manufacturing LLC (TX, biweekly, 28 WSEs, 2 WC lines)
- Smoke test: all 10 route checks pass

**Known state of the data:**
- All 51 SUTA state rows are placeholder values — thresholds and rates need verification with VHR staff before the tool produces accurate numbers
- WC Rates and WC Guidelines tables exist in the DB but are empty until VHR uploads the CSV via the config page
- WC manual rate is entered directly on the client form — the VLOOKUP against the WC Rates table is not yet wired into calculations

**What changed late in Phase 1:**
- Pages were initially built too far from the prototypes (agents told "don't copy code" — bad instruction). All three pages were rebuilt using the prototypes as the direct base.
- Config page originally had an inline 51-row SUTA editable table — removed, replaced with CSV upload/download matching the prototype
- "New Quote" renamed to "New Client" to match the actual workflow
- Config page Save Changes buttons removed — all fields now autosave on change

**Open questions for VHR staff (blocking accurate calculations):**
- SUTA rates: all 51 state rows need verified thresholds, VHR billing rates, and cost rates
- WC Policy Adjustment (Sunz, 1.55%): seeded at 0.0 — when is it applied and to which clients?
- MO SUTA: client files under their own account but uses VHR's rate — confirm how billing works
- See bolded questions throughout `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` for the full list
