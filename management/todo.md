# To-Do — VestedHR Pricing Tool

Each item is a single-agent task brief. **Coding agents:** read only your assigned brief plus the files listed in it — you do not need to read this whole file or updates.md. **Task manager:** read the full todo.md each session; read updates.md selectively for context on recently completed work.

---

## Active — Phase 2

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
