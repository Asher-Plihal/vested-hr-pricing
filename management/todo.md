# To-Do — VestedHR Pricing Tool

Each item is a single-agent task brief. **Coding agents:** read only your assigned brief plus the files listed in it — you do not need to read this whole file or updates.md. **Task manager:** read the full todo.md each session; read updates.md selectively for context on recently completed work.

---

## Active — Phase 2

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

**3. Annual Billing Analysis — current admin fee comparison method**

When comparing VHR admin fee vs. current provider fee:
- Current implementation applies the same method (% of GWs / per check / PEPM) to `current_admin_rate` as VHR's method.
- Open question: is it valid to compare a "% of GWs" VHR rate against a "per check" current rate using the same formula? The UI labels the current rate field dynamically based on the selected method (e.g., "Current Rate ($ per check)" when method = 2). Confirm this is intentional.

---

**4. WC additional fees — not in billing math**

The following fields are collected in the form but are not wired into any billing formula:
- `shared_claim_fee` — entered per client, never used in WC billing or cost
- `min_wc_fee_per_week` — same

Confirm with VHR: where do these appear in the client bill? Are they added as line items on top of WC billing, or do they affect the WC cost structure?

---

**Commit when done:** `docs: update pricing math — loss analysis formulas, proposal total, open questions`

---

## Blocked — Waiting on VHR Staff

### Benefits Tab
**Status:** blocked — `benefits-tab`
**Blocked by:** VHR staff — need actual plan PEPM data and rate tier band confirmation

Do not start until VHR provides the data. Full brief is in the phase 3 section of the old todo if needed. The `Benefit-RateTierBands` sheet is in the Excel template and the math is in `pricing_math.md` Benefits section — the data exists, just needs VHR sign-off.

