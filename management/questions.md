# Questions for VHR Team

Short questions only. Answers go inline, then move to the Answered section at the bottom.

---

## Workers' Comp

- Where do **Shared Claim Fee**, **Min WC Fee per Week**, and **Safety Claim Fee** flow into the client bill? They are collected on the WC tab and stored in the DB but not used in any billing or cost formula. Answer determines whether to wire them into billing math or remove the fields entirely.

---

## SUTA

- **Missouri**: client files under their own SUTA account but uses VHR's rate. Does MO billing work the same as a standard VHR-reporting state, or is there a different formula?

---

## Commission

- Can a broker earn commission on **both admin and WC** at the same time? The app currently applies `broker_admin_pct × admin_margin` and `broker_wc_pct × wc_billed` independently. Confirm this is correct, or clarify if it's one base per broker.

---

## Proposal

- Should the proposal total show **FICA and FUTA** as line items, or only VHR-billed items (WC + SUTA + Admin + extras)? These are employer payroll taxes — client cost but not VHR revenue.
