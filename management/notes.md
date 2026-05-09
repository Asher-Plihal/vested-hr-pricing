# Working Notes

Context and decisions that don't belong in todo.md or updates.md — things that are true right now but may change with further VHR input.

---

## Benefits Tab

The Benefits tab exists in `client.html` but is entirely placeholder UI. `calc/benefits.py` does not exist. No benefits fields are in `SystemConfig` or `CalculateRequest`. The tab collects no data and contributes nothing to the Deal Summary.

**Do not build until VHR provides:**
- Actual plan PEPM data
- Rate tier band confirmation
- Clarification on Exhibit D (see `questions.md`)

The math structure is documented in `pricing_math.md` Benefits section and the `Benefit-RateTierBands` sheet exists in the Excel template — the framework is there, just needs VHR sign-off on the actual numbers.

---

## Additional Fees

The Additional Fees fields (`epli_fee`, `tlm_fee`, `wire_ach_fee`, `implementation_fee`) are collected in the Admin tab and passed through to the Deal Summary as line items. They are **not** incorporated into any billing math beyond being added to the `other_items` total.

Two fields are collected but currently unused in any calculation:
- `shared_claim_fee` — entered per client on the WC tab, never used
- `min_wc_fee_per_week` — same

Waiting on VHR to confirm: where do these appear in the client bill? Are they WC billing add-ons, or separate line items?

---

## SUTA Client Reporting (Y/N)

"Client reporting" means the client files SUTA with that state under their own employer account — VHR does not remit on their behalf and cannot offer a rate advantage.

**How the flag works:**
- The `SutaRate` table has a `client_reporting` boolean per state, set via CSV upload on the config page.
- The UI does **not** read this from the API — it uses a hardcoded JS set (`CLIENT_REPORTING_STATES`) in `client.html` to display `"Y"` or `"N"` in the SUTA tab and `"PT"` (pass-through) in the Deal Summary for those states.
- The flag is **display only** — `calculate_suta()` does not receive or act on it. The math runs identically regardless.

**Critical data requirement:**
Client-reporting states must have `billing_rate = 0` and `cost_rate = 0` entered in the SUTA tab. The calculation does not zero these out automatically — if rates are left non-zero for a client-reporting state, the deal summary will show incorrect billing and profit numbers. This needs to be enforced either by UI (auto-zero on Y states) or by operator discipline until then.

**Client-reporting states (as of seed data):** AK, CT, DE, IA, KS, KY, MA, ME, MI, MN, MS, MT, NE, NV, OH, PA, RI, SC, SD, TN, VT, WA

---

## Authentication & Multi-User Access

Currently there is no authentication, no users table, and no role-gating. The tool runs as a single shared session — anyone with the URL can see and edit any client.

This needs to be designed carefully before the tool goes to production, because the core workflow involves multiple sales agents each managing their own book of clients. Key decisions that need to be made with VHR before building:

- **Data isolation** — can sales agents see each other's clients, or only their own? Is there a manager/admin role that sees everything?
- **Roles** — the requirements mention at least two distinct roles: sales agents (create and edit quotes) and approvers (Justin: pricing, John: WC, Nate: benefits). Are there others?
- **Login method** — username/password, Google SSO, or something else? VHR may have an existing identity provider.
- **Commission visibility** — consultant commission rates are currently visible to anyone. Should sales agents see their own commission but not others', or is this internal-only data?

Auth is deferred to Phase 3. Do not start until VHR answers the above. The full implementation brief will be written at Phase 3 kickoff.

