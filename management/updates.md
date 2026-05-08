# Update Log — VestedHR Pricing Tool

Most recent entry at the top. Add an entry any time a meaningful change is made.

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
