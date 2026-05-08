# To-Do — VestedHR Pricing Tool

Each item is written so it can be handed directly to an agent as a task brief.
Items are grouped by theme and roughly prioritized within each group.

---

## Data & Calculations

### WC Rates VLOOKUP
**Status:** Ready to build  
**Priority:** High — without this, sales reps must look up manual rates themselves

Currently `WCLine.manual_rate` is a field the user types in on the client form. The `wc_rates` table in the DB has ~25K rows (once uploaded via config page CSV upload) with `state`, `class_code`, `concat` (state+code), and `rate` per $100 payroll.

**What to build:**
- In `calc/workers_comp.py`, accept an optional `db` session and look up `manual_rate` from `wc_rates` by `concat = state + wc_code` when `manual_rate` is not provided or is 0
- In `routers/calculate.py`, pass the DB session to the WC calc function
- In `static/client.html`, the Manual Rate column on the WC Codes table should become read-only once a valid state+code is entered, auto-populated from `GET /wc-rate?state=TX&code=3599`. Add a new `GET /wc-rate` endpoint to `routers/rates.py` that returns the rate for a given state+code concat.
- If no rate is found (code not in table), keep the field editable and show a warning indicator on the row

**Files to read before starting:**
- `calc/workers_comp.py` — current implementation
- `routers/rates.py` — where to add the lookup endpoint
- `models.py` — WCRate model definition
- `static/client.html` — WC Codes table JS (around the `addWcRow` function)
- `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` — WC section for formula context

---

### WC Code Searchable Dropdowns
**Status:** Ready to build  
**Priority:** Medium — current plain text inputs require knowing the exact code

`pricing_tool_outline.md` specifies: "All states and all WC codes as searchable dropdowns." Currently the WC Codes table on the client form has plain `<input type="text">` for State and WC Code.

**What to build:**
- State column: replace text input with a `<select>` of all 50 states (or a searchable combobox)
- WC Code column: replace text input with a searchable input that queries `GET /wc-codes?state=TX&q=clerical` and shows a dropdown of matching codes + descriptions. Add this endpoint to `routers/rates.py` — query `wc_rates` by state + description LIKE search, return top 20 results.
- When a code is selected, auto-populate the Manual Rate field (ties into the VLOOKUP task above)

**Files to read before starting:**
- `static/client.html` — WC Codes table section
- `routers/rates.py` — where to add the search endpoint
- `models.py` — WCRate model (has `description` column)

---

### Benefits Tab
**Status:** Blocked — needs VHR rate data (plan PEPMs) before it produces useful numbers  
**Priority:** Low until data is available

The Benefits section of the client form (Tab 2) currently captures Medical Questionnaire and Ancillary Benefit questions but has no pricing outputs. The full calculation logic is documented.

**What to build:**
- Add benefits pricing inputs to the Pricing tab (or a new Benefits Pricing sub-section): Plan Type (Master/Client), Deductible Tier, Rate Tier Band, Medical PEPM per tier (WAIVED/GOOD/BETTER/BEST), toggles and PEPMs for Dental/Vision/Life/STD/LTD, Benefits Admin Fee PEPM
- Add a `BenefitsConfig` or extend `SystemConfig` with the Rate Tier Band lookup table (bands 6–28 with multipliers)
- Add `calc/benefits.py` using the formulas in `pricing_math.md` Benefits section
- Wire into the `POST /calculate` pipeline and add Benefits output to the Deal Summary

**Files to read before starting:**
- `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` — Benefits section (full formulas, band table, utilization load)
- `calc/summary.py` — where benefits output needs to be added
- `routers/calculate.py` — pipeline orchestration
- `static/client.html` — Pricing tab Deal Summary section

---

### Verify and Correct SUTA Rates
**Status:** Blocked — needs VHR staff input  
**Priority:** High for accuracy

All 51 state rows in the `suta_rates` table were seeded with placeholder values. VHR staff need to confirm actual thresholds, VHR billing rates, and VHR cost rates for every state. Once confirmed, they can be uploaded via the SUTA CSV upload on the config page, or corrected directly in `seed.py`.

**What needs to happen:**
- VHR staff review `seed.py` SUTA_ROWS and correct every row marked `# PLACEHOLDER`
- Particular attention to client-reporting states: CA, NY, NJ, PA, RI (currently have `vhr_min_rate=None`)
- MO needs clarification: files under client account but uses VHR rate — confirm the billing formula
- Once verified, remove the PLACEHOLDER comments from `seed.py`

---

## UI & UX

### Search Bar
**Status:** Ready to build  
**Priority:** Low

The topnav search input on all three pages is currently decorative. 

**What to build:**
- `GET /search?q=acme` endpoint in a new `routers/search.py` — queries `Client.legal_name`, `Client.dba`, `Client.consultant_name` with ILIKE
- On the dashboard, wire the search input to filter the displayed client list in real time (client-side filter is fine given small dataset, or hit the API)
- On client.html and config.html, hitting Enter in the search bar navigates to `dashboard.html?q={query}`

---

### Generate Doc / Proposal PDF
**Status:** Ready to stub, full implementation is post-prototype  
**Priority:** Medium — sales reps need a client-facing output

The "Generate Doc" button on the client page currently fires a toast. 

**What to build (stub for now):**
- A simple HTML print view: `GET /clients/{id}/proposal` renders a clean, print-friendly HTML page with the Deal Summary, client name, date, and key numbers
- The Generate Doc button opens this URL in a new tab — browser print to PDF works fine for a prototype

**Full implementation (Rails phase):**
- Templated PDF via a proper PDF library
- VHR-branded proposal document matching their existing format

---

## Auth & Roles

### Basic Auth / User System
**Status:** Ready to build  
**Priority:** Medium — needed before sharing with VHR staff for testing

Currently the user avatar (AP / Asher Plihal / Admin) is hardcoded static HTML. No login, no sessions.

**What to build (lightweight for prototype):**
- `users` table: id, name, email, role (admin / wc_admin / suta_admin / sales / general)
- Simple session token in localStorage — login page with email + password (bcrypt hash)
- `GET /me` returns current user
- Role-gating on `PUT /config` (admin, wc_admin, suta_admin only) and `DELETE /clients/{id}` (admin, sales only)
- The topnav user menu populates from `GET /me` instead of being hardcoded

**Roles from `pricing_tool_outline.md`:**
| Role | What they can do |
|---|---|
| Admin | Full access |
| WC Admin | Change WC rates in config |
| SUTA Admin | Change SUTA rates in config |
| Sales | Enter and edit client records |
| General User | View and print only |

---

## Post-Prototype (Rails Phase)

These are noted for planning — do not build in the prototype.

- **HubSpot integration**: auto-create Company, Deal, Contact on quote completion. `pricing_tool_outline.md` has the full spec.
- **Approval workflow**: after form completion, create tasks for Justin (pricing pre-approval), John (WC), Nate (benefits). After verbal from prospect, final approval tasks. Workflow is fully documented in `pricing_tool_outline.md` Post-Completion section.
- **Client Review tab**: enter actual payroll data and compare to projected — see if the deal is panning out. Mentioned by Nicole in `pricing_tool_outline.md`.
- **New Client Onboarding doc**: auto-generated from client data.
