# To-Do — VestedHR Pricing Tool

Each item is a single-agent task brief. Pick one, read it fully, do the work, commit, update status.json.

---

## Data & Calculations

### WC Rates VLOOKUP
**Status:** pending — `wc-rates-vlookup`
**Priority:** High

Wire the `wc_rates` DB table into the calculation pipeline so the manual rate is looked up automatically instead of typed in.

**What to build:**

1. Add `GET /wc-rate` endpoint to `routers/rates.py`:
   ```
   GET /wc-rate?state=TX&code=5645
   → 200: {"rate": 12.34}  or  404: {"detail": "Not found"}
   ```
   Query: `db.query(WCRate).filter(WCRate.concat == (state + code)).first()`

2. In `calc/workers_comp.py`, `calculate_wc(lines, proposed_mod, config, db=None)`:
   - Add optional `db: Session = None` parameter.
   - For each line: if `manual_rate` is 0 or None AND `db` is not None, query `WCRate` by `concat = line["state"] + line["wc_code"]` and use that rate. Fall back to `manual_rate` if not found.
   - The function must remain callable without `db` (smoke tests pass `None`).

3. In `routers/calculate.py`, pass `db` to `calculate_wc`: `calculate_wc(wc_line_dicts, proposed_mod, config, db=db)`.

4. In `static/client.html`, update `addWCCodeRow()`:
   - On state `<select>` change and WC code input `blur`: if both state and code are filled, call `GET /wc-rate?state=X&code=Y`.
   - On success: set `wc_rate_${idx}` value to returned rate, make it `readonly`, add CSS class `auto-populated`.
   - On 404: remove `readonly`, remove `auto-populated` class, add a `⚠` warning icon on the row (`data-rate-missing="true"`).
   - On empty state or code: revert to editable, clear warning.

**Files to read before starting:**
- `calc/workers_comp.py` — current implementation
- `routers/rates.py` — existing download/upload endpoints as pattern
- `models.py` — WCRate fields: `state`, `class_code`, `concat`, `rate`
- `static/client.html` — `addWCCodeRow()` function (~line 1297)
- `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` — WC section

---

### WC Code Search Endpoint
**Status:** pending — `wc-code-search-endpoint`
**Priority:** Medium (prerequisite for searchable dropdown UI)
**Blocked by:** `wc-rates-vlookup` should be done first

Add a search endpoint to `routers/rates.py` so the frontend can offer matching WC codes as the user types.

**What to build:**

Add `GET /wc-codes?state=TX&q=clerical` to `routers/rates.py`:
```
GET /wc-codes?state=TX&q=clerical
→ 200: [{"class_code": "8810", "description": "Clerical Office", "rate": 0.12}, ...]
```
- Filter: `WCRate.state == state` AND `WCRate.description ILIKE %q%` (use `func.lower` + `.contains` for SQLite — no ILIKE).
- Return top 20 results ordered by `class_code`.
- Response schema: list of `{"class_code": str, "description": str | None, "rate": float | None}`.
- If `state` is missing, return 400. If `q` is empty string, return all codes for the state (still limit 20).

**Files to read before starting:**
- `routers/rates.py` — add alongside existing endpoints
- `models.py` — WCRate fields

---

### WC Code Searchable Dropdown UI
**Status:** pending — `wc-code-searchable-dropdowns`
**Priority:** Medium
**Blocked by:** `wc-code-search-endpoint`

Replace the plain WC Code text input on the client form with a live-search combobox.

**What to build:**

In `static/client.html`, update `addWCCodeRow()`:
- Replace `<input type="text" name="wc_code_${idx}">` with a combobox pattern:
  - Visible text input for search/display.
  - Hidden `<input type="hidden" name="wc_code_${idx}">` that holds the committed code value.
  - A `<ul>` dropdown below the input that appears on focus/type.
- On each keystroke (debounce 200ms): if state is selected, call `GET /wc-codes?state=X&q=<input>`. Render up to 20 results as `<li>` items showing `code — description`.
- On `<li>` click: set hidden input to `class_code`, set visible input to `class_code — description`, close dropdown, trigger rate lookup (per `wc-rates-vlookup` task).
- On blur with no selection: if typed value matches a code exactly, accept it; otherwise clear and show validation error.
- Keyboard navigation: arrow up/down to move highlight, Enter to select, Escape to close.

**Files to read before starting:**
- `static/client.html` — `addWCCodeRow()` function (~line 1297)
- `static/style.css` — existing dropdown/combobox patterns to stay consistent

---

### Benefits Tab
**Status:** blocked — `benefits-tab`
**Blocked by:** VHR staff — need plan PEPM data and rate tier band confirmation
**Priority:** Low until data is available

Full benefits pricing module. Do not start until VHR provides actual plan PEPM data.

**What to build (once unblocked):**

1. Extend `SystemConfig` model (`models.py`) with benefits config columns:
   - `benefits_rate_tier_bands_json` — JSON encoding of band lookup (bands 6–28, multipliers per band)
   - `medical_pepm_waived`, `medical_pepm_good`, `medical_pepm_better`, `medical_pepm_best` (Float)
   - `dental_pepm`, `vision_pepm`, `life_pepm`, `std_pepm`, `ltd_pepm` (Float)
   - `benefits_admin_fee_pepm` (Float)
   Add corresponding fields to `SystemConfigOut` and `SystemConfigUpdate` in `schemas.py`.

2. Add benefits pricing inputs to the Pricing tab in `static/client.html`:
   - Plan Type (Master/Client) select
   - Deductible Tier select
   - Rate Tier Band number input
   - Medical PEPM per tier (WAIVED/GOOD/BETTER/BEST) — four inputs auto-populated from config
   - Toggles + PEPMs for Dental / Vision / Life / STD / LTD
   - Benefits Admin Fee PEPM input
   Add corresponding fields to `ClientUpdate`, `ClientOut`, and `CalculateRequest` in `schemas.py` and `models.py`.

3. Create `calc/benefits.py`:
   ```python
   def calculate_benefits(inputs: dict, config: dict) -> dict:
       # See pricing_math.md Benefits section for full formulas
   ```

4. Wire into `routers/calculate.py` pipeline between `admin_fee` and `commission`.

5. Add benefits output to Deal Summary in `calc/summary.py` and `static/client.html`.

**Files to read before starting:**
- `C:\workspaces\business\vested-hr\plan_drafts\pricing_math.md` — Benefits section (full formulas, band table, utilization load)
- `calc/summary.py` — where benefits output needs to be added
- `routers/calculate.py` — pipeline orchestration
- `static/client.html` — Pricing tab Deal Summary section

---

### Verify and Correct SUTA Rates
**Status:** blocked — `suta-rates-verify`
**Blocked by:** VHR staff input
**Priority:** High for accuracy

All 51 state rows are placeholder values. Tool will not produce accurate SUTA numbers until resolved.

**What needs to happen (human task, not agent):**
- VHR staff review `seed.py` SUTA_ROWS and correct every row marked `# PLACEHOLDER`
- Check client-reporting states: CA, NY, NJ, PA, RI (currently have `vhr_min_rate=None`)
- Clarify MO: client files under own account but uses VHR rate — confirm billing formula
- Once verified: upload corrected CSV via config page, or edit `seed.py` and remove PLACEHOLDER comments

---

## UI & UX

### Search Bar
**Status:** pending — `search-bar`
**Priority:** Low

Wire the topnav search input on all three pages. It is currently a decorative `<input class="topnav-search">` with no event handlers.

**What to build:**

1. Create `routers/search.py`:
   ```
   GET /search?q=acme
   → 200: [{"id": 1, "legal_name": "Acme Mfg", "dba": null, "consultant_name": "Bob"}, ...]
   ```
   Query: `Client.legal_name`, `Client.dba`, `Client.consultant_name` using `func.lower().contains(q.lower())` (SQLite-safe ILIKE equivalent). Return up to 20 results.

2. Register `routers/search.py` in `server.py` (same pattern as other routers).

3. `static/dashboard.html` — on search input with debounce 300ms:
   - If input length ≥ 2: call `GET /search?q=<value>`, re-render the client list rows to matching results only.
   - If input cleared: restore full client list.
   - No separate results dropdown — filter in place.

4. `static/client.html` and `static/config.html` — on Enter in search input: `window.location.href = '/static/dashboard.html?q=' + encodeURIComponent(value)`.
   On `dashboard.html` load: check `?q=` param, pre-fill search input and fire search.

**Files to read before starting:**
- `static/dashboard.html` — client list render function
- `static/client.html` and `static/config.html` — topnav search input
- `routers/clients.py` — pattern for DB queries
- `server.py` — router registration

---

### Generate Doc / Proposal
**Status:** pending — `generate-doc-proposal`
**Priority:** Medium

The "Generate Doc" button on the client page currently fires a toast. Build a print-friendly HTML proposal view.

**What to build:**

1. Add `GET /clients/{id}/proposal` to `routers/clients.py`:
   - Load the client from DB (404 if not found).
   - Call `POST /calculate` logic inline (reuse the same pipeline from `routers/calculate.py`) by importing and calling the calc functions directly — do not make an internal HTTP call.
   - Render and return an HTML page (use `HTMLResponse` from FastAPI) with: client legal name, date, consultant name, Deal Summary numbers (total GWs, total WSEs, WC billed, SUTA billed, admin fee, total profit/loss), and VHR branding.
   - Page should be clean and print-friendly: no nav, no sidebar, `@media print` styles.

2. In `static/client.html`, update the "Generate Doc" button click handler:
   - Replace the toast with `window.open('/clients/' + CLIENT_ID + '/proposal', '_blank')`.

**Files to read before starting:**
- `routers/clients.py` — existing client fetch pattern
- `routers/calculate.py` — calculation pipeline to replicate inline
- `static/client.html` — Generate Doc button handler and current Deal Summary display

---

## Auth & Roles

### Basic Auth / User System
**Status:** pending — `auth-roles`
**Priority:** Medium — needed before sharing with VHR staff

Topnav user avatar is hardcoded. No login, no sessions, no role-gating.

**What to build:**

1. Add `User` model to `models.py`:
   ```python
   class User(Base):
       __tablename__ = "users"
       id = Column(Integer, primary_key=True, autoincrement=True)
       name = Column(String, nullable=False)
       email = Column(String, unique=True, nullable=False)
       password_hash = Column(String, nullable=False)  # bcrypt
       role = Column(String, default="general")  # admin|wc_admin|suta_admin|sales|general
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

2. Add Pydantic schemas to `schemas.py`: `UserOut` (id, name, email, role), `LoginRequest` (email, password), `TokenResponse` (token, user: UserOut).

3. Create `routers/auth.py`:
   - `POST /auth/login` — verify email+password (bcrypt), return `{"token": "<uuid>", "user": {...}}`. Store token in a simple in-memory dict or `sessions` table for prototype.
   - `GET /auth/me` — read `Authorization: Bearer <token>` header, return current user or 401.
   - `POST /auth/logout` — invalidate token.

4. Add `get_current_user(token)` dependency to `database.py` or a new `auth.py` module. Use it to gate:
   - `PUT /config` — require `role in ("admin", "wc_admin", "suta_admin")`
   - `DELETE /clients/{id}` — require `role in ("admin", "sales")`

5. Create `static/login.html` — email + password form, posts to `POST /auth/login`, stores token in `localStorage`, redirects to dashboard.

6. In `static/app.js`:
   - Add `getToken()` helper that reads `localStorage.getItem("vhr_token")`.
   - Update `apiGet`, `apiPost`, `apiPut`, `apiDelete` to include `Authorization: Bearer <token>` header if token present.
   - Add `checkAuth()` — calls `GET /auth/me`; on 401 redirects to `/static/login.html`.

7. In `static/dashboard.html`, `static/client.html`, `static/config.html`:
   - Call `checkAuth()` on page load.
   - Populate topnav user name and initials from `GET /auth/me` response.
   - Wire the "Sign out" menu item to `POST /auth/logout` then redirect to login.

8. Seed one default admin user in `seed.py`: `admin@vestedhr.com` / `changeme` (bcrypt-hashed).

**Roles from `pricing_tool_outline.md`:**
| Role | Permissions |
|---|---|
| admin | Full access |
| wc_admin | Change WC rates in config |
| suta_admin | Change SUTA rates in config |
| sales | Enter and edit client records |
| general | View and print only |

**Files to read before starting:**
- `models.py`, `schemas.py`, `database.py` — existing patterns
- `server.py` — router registration
- `static/app.js` — `apiGet`/`apiPost` helpers to extend
- `static/dashboard.html` — topnav user menu HTML
- `C:\workspaces\business\vested-hr\plan_drafts\pricing_tool_outline.md` — roles section

---

## Post-Prototype (Rails Phase)

Do not build in prototype.

- **HubSpot integration** — auto-create Company, Deal, Contact on quote completion. Full spec in `pricing_tool_outline.md`.
- **Approval workflow** — tasks for Justin (pricing), John (WC), Nate (benefits). Documented in `pricing_tool_outline.md` Post-Completion section.
- **Client Review tab** — enter actual payroll data, compare to projected. Mentioned by Nicole in `pricing_tool_outline.md`.
- **New Client Onboarding doc** — auto-generated from client data.
