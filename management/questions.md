# Questions for VHR Team

Short questions only. Answers go inline, then move to the Answered section at the bottom.

---

## Workers' Comp

- Where do **Shared Claim Fee**, **Min WC Fee per Week**, and **Safety Claim Fee** flow into the client bill? The Excel has them as client-level inputs but they don't appear in any WC billing or cost formula.
- When is **WC Policy Adjustment** non-zero? The docs say it's a Sunz recovery charge (1.55%) but both example clients have it at 0. Who sets it and is it always 1.55% or client-specific?
- Should the tool **block EXCLD class codes** and warn on RSTD, or is the acceptability column purely a reference field that underwriters check manually?
- Is the **Min Premium column** in the WC Rates table used anywhere in pricing, or is it reference-only?

---

## FICA

- Do you plan to handle **pre-tax deductions or FICA-exempt wages**, or is it intentional to bill on full gross wages and reconcile later?
  > *Context: the SS wage cap is already implemented (`MIN(GWs, WSEs × $176,100)`). The open question is deductions only.*

---

## SUTA

- **Missouri**: client files under their own SUTA account but uses VHR's rate. Does MO billing work the same as a standard VHR-reporting state, or is there a different formula?

---

## Additional Fees

- Is the **comparison between a % of GWs VHR rate and a per-check current provider rate** valid? The tool applies the same method to both sides of the comparison.

---

## Commission

- **Year 1 vs. residual rates**: does the system need to auto-switch from Year 1 to residual commission rates after 12 months, or is it manually updated each year?
- Can a broker earn commission on **admin, WC, and gross wages all at once**, or is it one base per broker?

---

## Proposal

- Should the proposal total show **FICA and FUTA** as line items, or only VHR-billed items (WC + SUTA + Admin + extras)? These are employer payroll taxes that are technically the client's cost but not VHR's revenue.

---

## Loss Analysis

- What **loss ratio % flags a client as high-risk**? The tool calculates it but has no threshold to color-code or warn against.
- Are loss history periods **calendar years or policy years**?

---

## Benefits

- Is the base medical PEPM (`Bp`) the **employee contribution, employer cost, or full plan premium**? Changes how billing vs. deductions flow.
- Is the **Utilization Load (3%)** applied to medical only, or also ancillary benefits?
- When a client brings their **own carrier**, does the Benefits Admin Fee PEPM still apply?
- **Bands 1–5 are missing** from the Rate Tier Band table — is Band 6 the minimum, or are the lower bands just not in the data we received?

---

## Auth / Access

- Can sales agents **see each other's clients**, or only their own book?
- What **login method** — username/password, Google SSO, or existing identity provider?
- Should **commission rates and margins** be visible to sales agents, or are those internal-only fields?

---

## Answered

- **Setup Fee** — documented as a one-time onboarding charge. Can be waived (sets to $0). *(pricing_math.md)*
- **FUTA Approach** — using Approach B: `WSEs × $7,000 × 0.6% × turnover_pct`. Approach A not used. *(CLAUDE.md key design decisions)*
- **SS wage cap** — implemented: `MIN(GWs, WSEs × $176,100) × 6.2%`. *(calc/fica.py)*
- **Internal vs. external commission base** — confirmed intentional per pricing_math.md and code: internal commission is calculated off Total Admin Fee $ (before ancillary); external is off Total w/ Ancillary $. External brokers earn a cut of ancillary revenue; internal staff don't. *(pricing_math.md Commission section; calc/commission.py)*
- **SUTA turnover_pct default** — already 0.10 (10%) per `SutaLineIn.turnover_pct: float = 0.10` in schemas.py. Client can override per state line. Matches pricing_math.md "Default 10%". No change needed.
- **FUTA W-2s Generated default** — BUG: `CalculateRequest.w2s_generated` defaults to 0.0. If blank, `FUTA = WSEs × $7K × 0.6% × 0 = $0` — silently under-prices every deal where W-2s haven't been entered. Task `fix-futa-w2s-default` created to add a 100% turnover fallback with a Deal Summary warning.
- **TLM, EPLI, Wire/ACH** — BUG: current tool collects these as flat dollar totals (`tlm_fee`, `epli_fee`, `wire_ach_fee` in `CalculateRequest`), but pricing_math.md specifies rates × headcount: TLM = rate × WSEs × 12, EPLI = rate × WSEs × pay_periods, Wire/ACH = rate × pay_periods. Task `fix-tlm-epli-wire-rates` created.
