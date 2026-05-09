# To-Do — VestedHR Pricing Tool

Each item is a single-agent task brief. **Coding agents:** read only your assigned brief plus the files listed in it — you do not need to read this whole file or updates.md. **Task manager:** read the full todo.md each session; read updates.md selectively for context on recently completed work.

---

## Active — Phase 2

### Fix Commission Calculations
**Status:** pending — `fix-commission-calculations`
**Priority:** High — fix before calc-verification runs

Three known bugs in the commission/summary layer. All fixes are in `calc/summary.py` and `routers/calculate.py` — no DB schema changes needed.

**Read these files first:**
- `calc/summary.py` — all three bugs are here
- `calc/commission.py` — `calculate_commission()`, understand what it returns
- `routers/calculate.py` — how `calculate_summary()` is called and what gets passed to it
- `models.py` lines 39–40 — `SystemConfig.consultant_commission_upfront` and `consultant_commission_ongoing` (both Float, default 0.25/0.20, added via migration in `testing/seed.py`)

**Bug 1 — Consultant rates hardcoded instead of reading from SystemConfig**

`calc/summary.py:73-74`:
```python
"consultant_upfront": admin_fee * 0.25,   # hardcoded — wrong
"consultant_ongoing": admin_fee * 0.20,   # hardcoded — wrong
```

Fix: pass `consultant_commission_upfront` and `consultant_commission_ongoing` from `cfg_row` (SystemConfig) through to `calculate_summary()`. In `routers/calculate.py`, add them to the `ancillary_full` dict. In `calc/summary.py`, read them from `ancillary` instead of hardcoding.

**Bug 2 — Conditional consultant rates when a broker is on the deal**

Business rule: if `external_commission_pct > 0` (a broker is on the deal), consultant upfront drops to 0% and ongoing drops to 10% (minimum). Currently there is no conditional logic at all.

In `calc/summary.py`, after reading the rates from config (Bug 1 fix), add:
```python
broker_admin_pct = ancillary.get("external_commission_pct", 0.0)
if broker_admin_pct > 0:
    consultant_upfront_amt = 0.0
    consultant_ongoing_amt = admin_fee * 0.10
else:
    consultant_upfront_amt = admin_fee * consultant_upfront_rate
    consultant_ongoing_amt = admin_fee * consultant_ongoing_rate
```

**Bug 3 — broker_wc_commission_pct has no dollar calculation**

`calc/summary.py:75` passes the WC broker % as a display-only value. It never reduces WC profit. Fix: calculate the dollar amount and subtract it from `wc_profit` before rolling up `total_profit_loss`.

```python
broker_wc_pct = ancillary.get("broker_wc_commission_pct", 0.0)
broker_wc_commission = wc_profit * broker_wc_pct
wc_profit_after_broker = wc_profit - broker_wc_commission
```

Use `wc_profit_after_broker` in `total_profit_loss` instead of `wc_profit`. Add `broker_wc_commission` as a dollar amount to the `commissions` dict in the return value.

**What NOT to change:**
- `internal_commission_pct` — always 0 on the client model, harmless dead weight, leave it alone
- `calc/commission.py` — correct as-is, no changes needed
- Any DB models or schemas — all fixes are pure calc logic

**Commit:** `fix: commission calc — read consultant rates from config, broker WC dollar amount, conditional rates when broker present`

---

### Calculation Verification
**Status:** pending — `calc-verification`
**Priority:** High — do after `sheets-upload-fix`

Run a full end-to-end calculation with the Hartman Industrial LLC test client and verify every output number against the formulas in `pricing_math.md`. The goal is to confirm the calc pipeline is correct now that real rate data is loaded.

**What to do:**

1. Start the server: `uvicorn server:app --reload --port 8000`

2. Get the Hartman client id:
   ```
   GET /clients → find "Hartman Industrial LLC"
   ```

3. Run the calculation:
   ```
   POST /calculate
   Body: full client payload (fetch from GET /clients/{id} to get current values)
   ```

4. Verify each section against `pricing_math.md` formulas:

   **WSE:** `FTEs + 0.75 × PTEs`
   - Line 1 (5190): 28 + 0.75×6 = 32.5 WSEs
   - Line 2 (8810): 7 + 0.75×2 = 8.5 WSEs
   - Total: 41 WSEs

   **WC:** Rate comes from wc_rates table lookup (TX5190 and TX8810). Verify the rate field is populated (not 0). Then:
   - `Billing = (rate × 0.88) × GW / 100`
   - `Cost = Billing × 0.89`
   - `Margin = Billing − Cost`

   **FICA:** `SS = MIN(GW, WSEs × 176100) × 0.062` + `Medicare = GW × 0.0145`

   **FUTA:** `WSEs × 7000 × 0.006 × turnover_pct` (Approach B). Turnover = w2s_generated / total_wses = 62/41 ≈ 1.51. Check if that's what the code computes.

   **SUTA:** TX threshold=9000, billing_rate=0.027, cost_rate=0.0472, turnover=0.10.
   - `WSEs_with_turnover = 43 × 1.10 = 47.3`
   - `Taxable GWs = MIN(2,220,000, 9000 × 47.3) = MIN(2,220,000, 425,700) = 425,700`
   - `Bill = 0.027 × 425,700 = $11,493.90`
   - `Cost = 0.0472 × 425,700 = $20,093.04`

   **Admin Fee (Method 1):** `0.035 × total_GWs`
   - Total GWs = 1,800,000 + 420,000 = 2,220,000
   - Admin = 0.035 × 2,220,000 = $77,700

   **Commission:** internal=5%, external=0%
   - `Internal = Admin × 0.05 = $3,885`

5. For any number that doesn't match, look at the corresponding `calc/*.py` file and find the bug. Fix it and note the fix in the commit message.

6. If TX WC codes 5190 or 8810 return rate=0 (not found in DB), check `testing/import_rates.py` ran successfully and the wc_rates table has data: `GET /download/wc-rates` should return rows.

**Files to read:**
- `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` — authoritative formulas
- `calc/workers_comp.py`, `calc/fica.py`, `calc/futa.py`, `calc/suta.py`, `calc/admin_fee.py`, `calc/commission.py`, `calc/summary.py`
- `routers/calculate.py` — pipeline orchestration

**Commit:** `fix: calc verification — correct any formula bugs found`

---

### WC Code Searchable Dropdowns
**Status:** pending — `wc-code-searchable-dropdowns`
**Priority:** Medium
**Do after:** `calc-verification`

Replace the plain WC Code text input with a live-search combobox backed by the wc_rates table (now populated).

**What to build:**

1. Add `GET /wc-codes?state=TX&q=clerical` to `routers/rates.py`:
   ```
   → 200: [{"class_code": "8810", "description": "Clerical Office", "rate": 0.12}, ...]
   ```
   - Filter: `WCRate.state == state` AND `func.lower(WCRate.description).contains(q.lower())`
   - Return top 20, ordered by `class_code`
   - If `state` missing: 400. If `q` empty: return first 20 for the state.
   - Response: list of `{"class_code": str, "description": str | None, "rate": float | None}`

2. In `static/client.html`, update `addWCCodeRow()`:
   - Replace `<input type="text" name="wc_code_${idx}">` with:
     - Visible text `<input>` for search/display
     - Hidden `<input type="hidden" name="wc_code_${idx}">` for the committed code value
     - `<ul>` dropdown below, appears on focus/type
   - On each keystroke (debounce 200ms): if state selected, call `GET /wc-codes?state=X&q=<input>`. Render up to 20 `<li>` items showing `code — description`.
   - On `<li>` click: set hidden input to `class_code`, set visible input to `class_code — description`, close dropdown, trigger the existing rate lookup.
   - On blur with no selection: if typed value matches a code exactly, accept it; else clear and show validation hint.
   - Keyboard: arrow up/down to move highlight, Enter to select, Escape to close.

**Files to read:**
- `static/client.html` — `addWCCodeRow()` function and rate lookup event handlers already added
- `static/style.css` — match existing dropdown styles
- `routers/rates.py` — add alongside `GET /wc-rate`
- `models.py` — WCRate fields

---

### Dashboard Search Bar
**Status:** pending — `search-bar`
**Priority:** Low — do after `wc-code-searchable-dropdowns`

Wire the decorative topnav search input on `dashboard.html` to filter the client table live as the user types. Pure frontend — no new API endpoint. All clients are already fetched from `GET /clients` into the local `clients` array in `loadDashboard()`.

**What to build:**

1. **Hoist `clients` to module scope** in `dashboard.html`. Currently it's a local variable inside `loadDashboard()`. Move `let clients = [];` above `loadDashboard()` so the search handler can read it.

2. **Add a dropdown `<ul>` below `.search-wrap`** in the HTML (sibling inside `.search-wrap`):
   ```html
   <ul id="search-dropdown" class="search-dropdown" hidden></ul>
   ```
   Style it in the page `<style>` block (not style.css — keep it page-scoped):
   - `position: absolute; top: calc(100% + 6px); left: 0; right: 0;`
   - White background, `border-radius: 8px`, `box-shadow: 0 4px 16px rgba(0,0,0,0.18)`
   - `border: 1px solid #e2e8f0`, `overflow: hidden`, `z-index: 300`, `list-style: none`
   - Each `<li>`: `padding: 9px 14px; font-size: 0.85rem; color: #1a1a2e; cursor: pointer;`
   - `<li>:hover` and `.search-active` highlight: `background: #f4f5f7`

3. **Wire the `input` event** on `.topnav-search`:
   - Trim the query. If empty: hide dropdown, un-hide all table rows, return.
   - Match against `clients` array by `legal_name` (case-insensitive `includes`). Take top 8 matches.
   - Render matched clients as `<li data-id="...">` items showing `client.legal_name`.
   - Show dropdown; hide it when there are 0 matches.
   - **Also filter table rows live**: for each `tr[data-id]` in the rendered table, show the row if its `legal_name` matches, hide it otherwise (`row.style.display`). This lets the user see results in context without clicking.

4. **Keyboard navigation on the dropdown**:
   - `ArrowDown` / `ArrowUp`: move `.search-active` highlight through `<li>` items. Don't let focus leave the input.
   - `Enter`: navigate to the highlighted item's client page (`/static/client.html?id=X`). If nothing is highlighted and there is exactly one visible table row, navigate to it.
   - `Escape`: clear input, hide dropdown, restore all rows.

5. **Close dropdown** on input `blur` with a `setTimeout(50ms)` delay (so clicks on `<li>` items fire first before blur hides the list).

6. **Clicking a `<li>`**: navigate to `/static/client.html?id=${clientId}`.

**No changes needed to:**
- `static/app.js` — no shared utilities needed
- `static/style.css` — keep search-dropdown styles inline in dashboard.html
- Any backend file — purely frontend

**Files to read:**
- `static/dashboard.html` — full file, particularly `loadDashboard()`, `clients` array, and the `.search-wrap` HTML (lines 100–103)
- `static/style.css` lines 47–74 — existing `.search-wrap` and `.topnav-search` styles to match visual language

**Commit:** `feat: wire dashboard search bar — live client filter + name-match dropdown`

---

### Update Pricing Math Documentation
**Status:** pending — `update-pricing-math`
**Priority:** Medium — verify before presenting proposal/analysis views to VHR

Review the formulas and open questions surfaced when building the Proposal, Annual Billing Analysis, and Loss Analysis display cards. Each item needs VHR staff verification against the actual Excel source of truth before the tool can be trusted for client-facing output.

**File to update:** `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md`

---

**1. Proposal — Total Annual Billing formula (not documented)**

Current implementation sums: `WC Billed + SUTA Billed + FICA + FUTA + Admin Fee + EPLI + Implementation Fee`

Open questions:
- Is it correct to include FICA and FUTA as client-facing line items in the proposal? These are employer payroll taxes billed to the client (passthrough), but the Excel proposal sheet needs to be checked.
- Does the proposal show gross client cost (all passthroughs) or net VHR-billed items only (WC + SUTA + Admin + extras)?
- Should TLM and Wire/ACH fees also appear in the proposal total? They're wired in the backend (`other_items.tlm`, `other_items.wire_ach_fee`) but the proposal card currently omits them.

---

**2. Loss Analysis formulas (not documented)**

Current implementation uses:
- **Loss Rate** = Total Losses ÷ Total Annual Payroll × 100
  - Denominator is `total_gws` (all WC lines summed) — is this the right base? Should it be only the payroll for the states covered by each loss period?
- **Annualized Losses** = (Total Losses ÷ Months in Policy) × 12
  - Used to normalize periods of varying length. Confirm this is how VHR uses the loss history.

Open questions:
- What is the loss ratio threshold VHR uses to flag a client as high-risk? (e.g., loss ratio > 60% = red flag)
- Are loss history years always calendar years or policy years (which can span two calendar years)?
- Should open claims be weighted differently from closed claims in the risk assessment?

---

**3. SUTA GWs bug — billing always computes as $0**

Root cause: `collectSutaLines()` in `client.html` hardcodes `gws: 0` for every SUTA row. The backend `calculate_suta()` receives `gws=0`, so `taxable_gws = min(0, threshold × WSEs) = 0`, and `suta_bill = billing_rate × 0 = $0`.

This means the SUTA Billed, SUTA Cost, and SUTA Profit/Loss in the Deal Summary are always zero regardless of what rates are entered.

Fix needed: compute per-state GWs on the frontend by aggregating WC lines by state before building the SUTA payload. In `collectSutaLines()`, for each SUTA state row, sum up `annual_gw` from all WC lines matching that state. Pass that sum as `gws`.

This is a frontend-only fix (no backend changes). The person implementing this should also verify that `total_wses` per SUTA state is correct (currently also 0).

---

**4. Annual Billing Analysis — current admin fee comparison method**

When comparing VHR admin fee vs. current provider fee:
- Current implementation applies the same method (% of GWs / per check / PEPM) to `current_admin_rate` as VHR's method.
- Open question: is it valid to compare a "% of GWs" VHR rate against a "per check" current rate using the same formula? The UI labels the current rate field dynamically based on the selected method (e.g., "Current Rate ($ per check)" when method = 2). Confirm this is intentional.

---

**5. WC additional fees — not in billing math**

The following fields are collected in the form but are not wired into any billing formula:
- `shared_claim_fee` — entered per client, never used in WC billing or cost
- `min_wc_fee_per_week` — same

Confirm with VHR: where do these appear in the client bill? Are they added as line items on top of WC billing, or do they affect the WC cost structure?

---

**6. Proposal SUTA column limitation**

The Proposal card shows SUTA billing rate per state but shows "—" for dollar amounts. This is because SUTA billing requires taxable wages by state (see item 3 above). Once item 3 is fixed, the SUTA dollar column in the Proposal card should be populated.

---

**Commit when done:** `docs: update pricing math — loss analysis formulas, proposal total, SUTA GWs bug, open questions`

---

## Blocked — Waiting on VHR Staff

### Benefits Tab
**Status:** blocked — `benefits-tab`
**Blocked by:** VHR staff — need actual plan PEPM data and rate tier band confirmation

Do not start until VHR provides the data. Full brief is in the phase 3 section of the old todo if needed. The `Benefit-RateTierBands` sheet is in the Excel template and the math is in `pricing_math.md` Benefits section — the data exists, just needs VHR sign-off.

---

## Deferred — Phase 3

Do not build in phase 2.

- **Auth / User System** (`auth-roles`) — login page, users table, role-gating on endpoints. Full brief available in status.json.
- **Doc Proposal + Task Management** (`doc-proposal-tasks`) — two parts, build together:
  - *Proposal doc:* `GET /clients/{id}/proposal` returns a print-friendly styled HTML page with the full deal summary (WC lines, SUTA, admin fee, commission breakdown). "Generate Doc" button on client.html navigates to this URL.
  - *Task generation:* when a quote status moves to `in_review`, auto-create approval tasks in a new `tasks` DB table. Assignees: Justin (pricing sign-off), John (WC sign-off), Nate (benefits sign-off). Each task has: `id`, `client_id`, `assigned_to`, `type` (pricing/wc/benefits), `status` (open/approved/rejected), `created_at`.
  - *Task UI:* a task list view per client (new tab or sidebar panel) showing open tasks, who they're assigned to, and approve/reject buttons.
  - Full brief to be written when Phase 3 starts — confirm assignee names and task flow with VHR before building.
- **HubSpot integration** — auto-create Company, Deal, Contact on quote completion.
- **Client Review tab** — actual vs projected payroll comparison.
