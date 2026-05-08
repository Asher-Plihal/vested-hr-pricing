# To-Do — VestedHR Pricing Tool

Each item is a single-agent task brief. Pick one, read it fully, do the work, commit, update status.json.

---

## Active — Phase 2

### Calculation Verification
**Status:** pending — `calc-verification`
**Priority:** High — do this before any other phase 2 work

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

## Blocked — Waiting on VHR Staff

### Benefits Tab
**Status:** blocked — `benefits-tab`
**Blocked by:** VHR staff — need actual plan PEPM data and rate tier band confirmation

Do not start until VHR provides the data. Full brief is in the phase 3 section of the old todo if needed. The `Benefit-RateTierBands` sheet is in the Excel template and the math is in `pricing_math.md` Benefits section — the data exists, just needs VHR sign-off.

---

## Deferred — Phase 3

Do not build in phase 2.

- **Auth / User System** (`auth-roles`) — login page, users table, role-gating on endpoints. Full brief available in status.json.
- **Search Bar** (`search-bar`) — wire the decorative topnav search to a `GET /search?q=` endpoint.
- **Generate Doc / Proposal** (`generate-doc-proposal`) — print-friendly HTML proposal at `GET /clients/{id}/proposal`.
- **HubSpot integration** — auto-create Company, Deal, Contact on quote completion.
- **Approval workflow** — tasks for Justin (pricing), John (WC), Nate (benefits).
- **Client Review tab** — actual vs projected payroll comparison.
