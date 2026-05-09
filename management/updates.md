# Update Log — VestedHR Pricing Tool

Most recent entry at the top. Add an entry when a task completes. This is where completed task context lives — status.json and todo.md only track what's left to do.

---

### 2026-05-09 — Commission logic rewrite + calculate payload fix

**No task ID — ad-hoc session**

**Commission logic rewrite (`calc/commission.py`):**
Replaced the old single-pass commission function with the correct two-scenario model:

- **No broker:** consultant gets 25% upfront (Year 1) + 20% ongoing, both applied to admin margin.
- **Broker on deal:** upfront = 0. Broker earns `broker_admin_pct × admin_margin` and `broker_comp_pct × wc_billed` independently. Consultant ongoing = `max(10%, 40% − broker_admin_pct)` applied to admin margin net of broker's admin cut. Comp-only broker (no admin %): consultant gets 10% floor.

All four rates (pool %, consultant min ongoing %, upfront no-broker %, ongoing no-broker %) are now configurable in `SystemConfig` with migrations in `testing/seed.py`.

**Config page (`static/config.html`):**
Admin tab gains two new fields: "Total Pool %" (40%) and "Consultant Min. Ongoing %" (10%). Existing upfront/ongoing fields labelled "(no broker only)".

**Summary fix (`calc/summary.py`):**
Removed duplicate commission calculations that ignored the new logic. Now reads `consultant_upfront`, `consultant_ongoing`, and `broker_comp` directly from `commission_result`. Fixed `broker_wc_commission` base: was `wc_profit × broker_pct` (wrong), now `wc_billed × broker_pct` via `commission_result["broker_comp"]`.

**Loss Analysis label:** "Commissions" renamed to "Comp Commissions" in the WC Net Billing section of `client.html`.

**Critical bug fix — calculate payload (`static/client.html`):**
`runCalculate()` was sending `{ client: {...}, wc_lines, suta_lines }` to `POST /calculate`, but `CalculateRequest` expects flat fields. Pydantic silently ignored the nested `client` object and used defaults for every client-level field: `admin_method=1`, `admin_rate=0`, `proposed_mod=1`, `broker_wc_commission_pct=0`, `external_commission_pct=0`, `w2s_generated=0`, `payroll_frequency="biweekly"`. This meant admin fee, FUTA, and all commissions were wrong for every calculate call. Fixed by spreading `payload.client` into the top-level calc payload.

---

### 2026-05-08 — Form Safety UX (`form-safety-ux`)

Pure frontend changes in `static/client.html`:

**Per-card lock toggle:** All 12 input cards (General Information, Compliance Questions, Medical Questions, Ancillary Benefit Questions, Payroll Information, Admin Fee, Additional Fees, Commissions, SUTA, Workers' Compensation Codes, Workers' Compensation Losses, Workers' Comp Questions) now have `data-locked="true"` and a 🔒 button in the card-title header. On page load, `applyCardLock` disables all inputs/selects/textareas/buttons inside each locked card. Clicking the lock button toggles to 🔓 and re-enables. Read-only display cards (Proposal, Annual Billing Analysis, Loss Analysis, Deal Summary) were left unchanged.

**Delete confirmations:** `removeWCRow`, `removeSutaRow`, `removeWCLossRow` (new named function, replaces inline onclick), and `removeLocationRow` (new named function, replaces inline onclick) all call `confirm()` before removing the row.

---

### 2026-05-08 — Calculation Verification (`calc-verification`)

All calc formulas were correct. The only issue: `wc_rates`, `wc_guidelines`, and `suta_rates` tables were empty after a DB reset — the `testing/import_rates.py` script referenced in the setup instructions didn't exist in the repo. Created it to import all three rate tables from the Excel pricing template (`Pricing Template 03.10.26_ALL SHEETS.xlsx`): 24,965 WC cost rates, 19,552 WC guidelines, 51 SUTA state rows.

Verified all outputs against `pricing_math.md` expected numbers for Hartman Industrial LLC (TX, biweekly, proposed_mod=0.88, admin_rate=3.5%):

| Section | Expected | Got |
|---|---|---|
| Total WSEs | 41 | 41.0 ✓ |
| WC Billed | $29,293.44 | $29,293.44 ✓ |
| WC Cost | $26,071.16 | $26,071.16 ✓ |
| FICA | $169,830 | $169,830 ✓ |
| FUTA | $2,604 | $2,604 ✓ |
| SUTA Bill | $11,493.90 | $11,493.90 ✓ |
| SUTA Cost | $20,093.04 | $20,093.04 ✓ |
| Admin Fee | $77,700 | $77,700 ✓ |
| Internal Comm | $3,885 | $3,885 ✓ |

TX5190 rate = 1.84 per $100; TX8810 rate = 0.04 per $100 (both from `WC Cost Rates` sheet).

---

### 2026-05-08 — Fix Commission Calculations (`fix-commission-calculations`)

Fixed three bugs in `calc/summary.py` and `routers/calculate.py`:

1. **Consultant rates from config** — `consultant_upfront` and `consultant_ongoing` were hardcoded at 25%/20%. Now read `consultant_commission_upfront` / `consultant_commission_ongoing` from `SystemConfig` via `ancillary_full` in the router.
2. **Conditional rates when broker present** — added logic: if `external_commission_pct > 0`, consultant upfront drops to 0% and ongoing drops to 10%.
3. **Broker WC dollar amount** — `broker_wc_commission_pct` was display-only. Now computes `broker_wc_commission = wc_profit × broker_wc_pct`, subtracts it from `wc_profit` before rolling up `total_profit_loss`, and exposes the dollar amount in the `commissions` response dict.

No DB or schema changes. `calc/commission.py` untouched.

---

### 2026-05-08 — Fix: SUTA GWs always $0

`collectSutaLines()` in `static/client.html` hardcoded `gws: 0` and `total_wses: 0` for every SUTA row. Fixed by aggregating `annual_gw`, `ftes`, and `ptes` from WC lines that match each SUTA state (WSEs = ftes + 0.75 × ptes). Part of the `update-pricing-math` task — other items in that task still require VHR verification.

---

### 2026-05-08 — UI restructure: Workers' Comp Questions, Admin tab, Commissions

**Ad-hoc session — no task ID**

**Workers' Comp Questions (`client.html`):**
- Reformatted from 2-column `q-grid` to single-column `compliance-rows` layout (matches Compliance Questions style)
- All 24 question labels rewritten to match the exact VHR underwriting question text
- Explanation fields changed from `<input type="text">` to `<textarea rows="3">`
- Removed "Company Drivers" and "CDL Drivers" rows (not in the 24-question list)
- All Yes/No dropdowns across Compliance and WC Questions sections: removed blank "—" option, default set to No

**WC Losses section:**
- "Is this a new company?" → "New company?" / note: "Loss History Affidavit required."
- "Any gaps in coverage?" → "Gaps in coverage?" / note: "LHA required for gap period."

**Tab structure:**
- "Payroll" tab renamed to "Admin" and moved to 3rd position (General → Workers' Comp → Admin → Benefits → Pricing)
- Admin tab payroll fields restructured to match prototype layout: Payroll Frequency | Method of Payment, Payroll Cycle Start DAY | Payroll Cycle End DAY, Pay DAY, Effective Date | Requested Payroll Delivery Method
- Method of Payment options updated: Direct Wire, Reverse Wire, ACH (Approval Required)
- Requested Payroll Delivery options updated: Electronic / Paperless, Delivery via Courier / FedEx

**Admin Fee section moved to Admin tab:**
- Redesigned from dropdown to 3 clickable selection boxes: Percentage of GWs, Per Check Fee, Per WSE per Month
- Added "Vested Rate" and "Current Rate" fields (labels update based on selected method)
- `current_admin_rate` added to `models.py` and `schemas.py`

**Additional Fees and Commissions moved from Pricing tab to Admin tab.**
- EPLI label updated to include "(Cannot be less than $0.50 per week)" note
- W-2s Generated (turnover proxy) moved from Commissions to the SUTA section on Pricing tab

**Commissions section simplified:**
- Just 2 inputs: Broker/Referral Partner WC % and Broker/Referral Partner Admin %
- `internal_commission_pct` kept as a hidden field so the calc pipeline still works
- Defaults will be pulled from system config (not yet wired)

**Pricing tab** now contains only SUTA and Deal Summary.

---

### 2026-05-08 — SUTA date_updated column added

**Task:** ad-hoc fix

`SutaRate` model was missing a `date_updated` field. The download CSV always emitted `None` for the "Date Updated" column, so any round-trip edit-and-reupload silently wiped that column.

- Added `date_updated = Column(String, nullable=True)` to `SutaRate` in `models.py`
- Download (`GET /download/suta-rates`) now exports `r.date_updated` instead of `None`
- Upload (`POST /upload/suta-rates`) now reads "Date Updated" from the CSV and saves it to DB
- Live DB migrated: `ALTER TABLE suta_rates ADD COLUMN date_updated TEXT` run directly on `data/vested_hr.db`

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
