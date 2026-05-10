"""
Idempotent seed script — creates 3 test contacts designed to stress-test
edge cases across all three admin methods, multiple states (including
client-reporting SUTA states), 8 WC codes each, and varied commission/EPLI
setups. Safe to re-run: skips any contact whose legal_name already exists.

Usage:
    python testing/seed_clients.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Contact, WCLine, WCLoss, SutaLine


def _skip_if_exists(db, legal_name: str) -> bool:
    existing = db.query(Contact).filter(Contact.legal_name == legal_name).first()
    if existing:
        print(f"  '{legal_name}' already exists (id={existing.id}) — skipping.")
        return True
    return False


# ── Client 1 ─────────────────────────────────────────────────────────────────
# Admin Method 1 (% of GWs) — multi-state commercial construction
# Tests: high-turnover FUTA, 3-state SUTA (all VHR-reporting), mod < 1.0,
#        weekly payroll, external commission = 0 (direct deal)
def seed_meridian(db):
    NAME = "Meridian Construction Group LLC"
    if _skip_if_exists(db, NAME):
        return

    contact = Contact(
        legal_name=NAME,
        dba="Meridian CG",
        consultant_name="Mike Torres",
        consultant_name_split="Mike Torres",
        date="2026-05-09",
        main_address="3901 Stemmons Fwy",
        city="Dallas",
        state="TX",
        zip="75207",
        fein="47-2831940",
        website="www.meridiancg.com",
        main_phone="214-555-0182",
        owner_name="Greg Meridian",
        owner_email="g.meridian@meridiancg.com",
        contact_name="Lisa Park",
        contact_email="l.park@meridiancg.com",
        contact_cell="214-555-0183",
        org_structure="LLC",
        naics="236220",
        sic="1731",
        years_in_business=9,
        num_locations=3,
        states_operating='["TX","FL","GA"]',
        payroll_frequency="weekly",
        pay_cycle_start="Monday",
        pay_cycle_end="Sunday",
        pay_date="Friday",
        description_of_operations="Commercial construction — electrical, carpentry, HVAC across TX, FL, GA job sites.",
        # WC
        proposed_mod=0.87,
        shared_claim_fee=0.0,
        min_wc_fee_per_week=0.0,
        new_company=False,
        gaps_in_coverage=False,
        # Admin — Method 1: % of GWs
        admin_method=1,
        admin_rate=0.032,
        current_admin_rate=0.038,
        # Commission — direct deal, no broker
        internal_commission_pct=0.05,
        external_commission_pct=0.0,
        broker_wc_commission_pct=0.0,
        implementation_fee=1500.0,
        # FUTA — construction turnover drives W-2s above avg headcount
        futa_turnover_rate=0.45,
        # Compliance
        eeoc_violations=False,
        active_claims=False,
        past_layoffs=False,
        future_layoffs=False,
        # Medical
        medical_carve_out=True,
        currently_has_health_insurance=True,
    )
    db.add(contact)
    db.flush()
    print(f"  Created '{NAME}' (id={contact.id})")

    wc_lines = [
        # TX codes
        WCLine(contact_id=contact.id, state="TX", wc_code="5190",
               wc_description="Electrical Wiring Within Buildings",
               annual_gw=2_200_000.0, ftes=35.0, ptes=8.0, current_client_rate=5.20),
        WCLine(contact_id=contact.id, state="TX", wc_code="5403",
               wc_description="Carpentry - Commercial",
               annual_gw=980_000.0, ftes=18.0, ptes=4.0, current_client_rate=8.50),
        WCLine(contact_id=contact.id, state="TX", wc_code="5645",
               wc_description="Carpentry - Residential",
               annual_gw=650_000.0, ftes=12.0, ptes=3.0, current_client_rate=7.20),
        WCLine(contact_id=contact.id, state="TX", wc_code="5606",
               wc_description="Contractors - Project Manager",
               annual_gw=420_000.0, ftes=6.0, ptes=2.0, current_client_rate=1.85),
        # FL codes
        WCLine(contact_id=contact.id, state="FL", wc_code="5537",
               wc_description="Heating/AC/Refrigeration Installation",
               annual_gw=1_100_000.0, ftes=19.0, ptes=5.0, current_client_rate=4.10),
        WCLine(contact_id=contact.id, state="FL", wc_code="8810",
               wc_description="Clerical Office Employees",
               annual_gw=280_000.0, ftes=5.0, ptes=1.0, current_client_rate=0.30),
        # GA codes
        WCLine(contact_id=contact.id, state="GA", wc_code="7380",
               wc_description="Drivers/Chauffeurs - Trucking",
               annual_gw=340_000.0, ftes=8.0, ptes=2.0, current_client_rate=6.80),
        WCLine(contact_id=contact.id, state="GA", wc_code="8742",
               wc_description="Salespersons/Collectors - Outside",
               annual_gw=190_000.0, ftes=4.0, ptes=0.0, current_client_rate=0.65),
        # BAD WC ROWS — intentional bad inputs for system testing
        # Code "0000" doesn't exist in wc_rates: lookup misses, manual_rate stays 0.0,
        # billing/cost silently zero out for this line.
        WCLine(contact_id=contact.id, state="TX", wc_code="0000",
               wc_description="INVALID CODE — should rate to $0",
               annual_gw=500_000.0, ftes=10.0, ptes=2.0, current_client_rate=3.50,
               manual_rate=0.0),
        # Code "9999" doesn't exist in wc_rates for any state — lookup misses,
        # falls back to manual_rate=0.0, billing/cost silently zero out.
        WCLine(contact_id=contact.id, state="TX", wc_code="9999",
               wc_description="NONEXISTENT CODE — lookup misses, rates to $0",
               annual_gw=300_000.0, ftes=6.0, ptes=0.0, current_client_rate=0.90,
               manual_rate=0.0),
    ]
    for wl in wc_lines:
        db.add(wl)
    print(f"    Added {len(wc_lines)} WC lines across TX/FL/GA (incl. 2 bad codes)")

    # All 3 states are VHR-reporting (client_reporting=False in suta_rates)
    suta_lines = [
        SutaLine(contact_id=contact.id, state="TX",
                 gws=5_250_000.0, total_wses=79.0,
                 current_client_rate=0.027,
                 billing_rate=0.027, cost_rate=0.0472,
                 threshold=9000.0, turnover_pct=0.12),
        SutaLine(contact_id=contact.id, state="FL",
                 gws=1_380_000.0, total_wses=25.0,
                 current_client_rate=0.012,
                 billing_rate=0.015, cost_rate=0.001,
                 threshold=7000.0, turnover_pct=0.08),
        SutaLine(contact_id=contact.id, state="GA",
                 gws=530_000.0, total_wses=12.0,
                 current_client_rate=0.018,
                 billing_rate=0.023, cost_rate=0.0214,
                 threshold=9500.0, turnover_pct=0.10),
        # BAD SUTA ROWS — intentional bad inputs for system testing
        # threshold=0: taxable_gws = min(gws, 0 × wses) = 0 → entire line is $0 bill/cost.
        SutaLine(contact_id=contact.id, state="TX",
                 gws=200_000.0, total_wses=15.0,
                 current_client_rate=0.027,
                 billing_rate=0.027, cost_rate=0.0472,
                 threshold=0.0, turnover_pct=0.10),
        # billing_rate=0 but cost_rate>0: negative margin — VHR pays cost with no recovery.
        SutaLine(contact_id=contact.id, state="FL",
                 gws=150_000.0, total_wses=10.0,
                 current_client_rate=0.015,
                 billing_rate=0.0, cost_rate=0.001,
                 threshold=7000.0, turnover_pct=0.08),
    ]
    for sl in suta_lines:
        db.add(sl)
    print(f"    Added {len(suta_lines)} SUTA lines: TX×2, FL×2, GA (incl. 2 bad rows)")

    # WC loss history — 3 years, moderately adverse (construction)
    wc_losses = [
        WCLoss(contact_id=contact.id,
               coverage_period_start="2021-01-01", coverage_period_end="2021-12-31",
               total_losses_incurred=142_800.0, num_claims=7, months_in_policy=12, open_claims=0),
        WCLoss(contact_id=contact.id,
               coverage_period_start="2022-01-01", coverage_period_end="2022-12-31",
               total_losses_incurred=89_500.0, num_claims=4, months_in_policy=12, open_claims=0),
        WCLoss(contact_id=contact.id,
               coverage_period_start="2023-01-01", coverage_period_end="2023-12-31",
               total_losses_incurred=214_300.0, num_claims=9, months_in_policy=12, open_claims=1),
    ]
    for wl in wc_losses:
        db.add(wl)
    print(f"    Added {len(wc_losses)} WC loss years (2021–2023)")


# ── Client 2 ─────────────────────────────────────────────────────────────────
# Admin Method 2 (per-check) — West Coast staffing, has a broker
# Tests: very high FUTA turnover (staffing), CA (high SUTA rate), NV
#        client-reporting SUTA (skipped — no VHR rates), broker commission,
#        mod=1.0 (new to PEO), biweekly payroll
def seed_pacific_rim(db):
    NAME = "Pacific Rim Staffing LLC"
    if _skip_if_exists(db, NAME):
        return

    contact = Contact(
        legal_name=NAME,
        dba="Pacific Rim",
        consultant_name="Diana Chen",
        consultant_name_split="Diana Chen",
        date="2026-05-09",
        main_address="10880 Wilshire Blvd Ste 1100",
        city="Los Angeles",
        state="CA",
        zip="90024",
        fein="91-5049327",
        website="www.pacificrimstaffing.com",
        main_phone="310-555-0247",
        owner_name="James Tanaka",
        owner_email="j.tanaka@pacificrimstaffing.com",
        contact_name="Maria Gutierrez",
        contact_email="m.gutierrez@pacificrimstaffing.com",
        contact_cell="310-555-0248",
        org_structure="LLC",
        naics="561320",
        sic="7363",
        years_in_business=4,
        num_locations=2,
        states_operating='["CA","NV","AZ"]',
        payroll_frequency="biweekly",
        pay_cycle_start="Sunday",
        pay_cycle_end="Saturday",
        pay_date="Friday",
        description_of_operations="Light industrial and office staffing — CA, NV, and AZ. High W-2 count relative to average headcount due to temp placements.",
        # WC
        proposed_mod=1.0,
        # Admin — Method 2: per-check per WSE
        admin_method=2,
        admin_rate_2=12.50,
        current_admin_rate_2=18.00,
        implementation_fee=2500.0,
        # Commission — broker on the deal
        internal_commission_pct=0.04,
        external_commission_pct=0.03,
        broker_wc_commission_pct=0.01,
        # FUTA — temp staffing routinely generates far more W-2s than avg headcount
        futa_turnover_rate=1.10,
        # Compliance
        eeoc_violations=False,
        active_claims=False,
        past_layoffs=False,
        future_layoffs=False,
        cobra_continuation=False,
        # Medical
        medical_carve_out=False,
        currently_has_health_insurance=False,
        census_available=True,
    )
    db.add(contact)
    db.flush()
    print(f"  Created '{NAME}' (id={contact.id})")

    wc_lines = [
        # CA codes
        WCLine(contact_id=contact.id, state="CA", wc_code="8810",
               wc_description="Clerical Office Employees",
               annual_gw=3_400_000.0, ftes=45.0, ptes=20.0, current_client_rate=0.25),
        WCLine(contact_id=contact.id, state="CA", wc_code="8742",
               wc_description="Salespersons/Collectors - Outside",
               annual_gw=2_100_000.0, ftes=28.0, ptes=8.0, current_client_rate=0.55),
        WCLine(contact_id=contact.id, state="CA", wc_code="5190",
               wc_description="Electrical Wiring Within Buildings",
               annual_gw=1_800_000.0, ftes=22.0, ptes=6.0, current_client_rate=5.80),
        WCLine(contact_id=contact.id, state="CA", wc_code="8018",
               wc_description="Stores - Retail",
               annual_gw=950_000.0, ftes=18.0, ptes=12.0, current_client_rate=1.20),
        # NV codes — NV is a client-reporting SUTA state but WC still applies
        WCLine(contact_id=contact.id, state="NV", wc_code="8810",
               wc_description="Clerical Office Employees",
               annual_gw=680_000.0, ftes=14.0, ptes=4.0, current_client_rate=0.28),
        WCLine(contact_id=contact.id, state="NV", wc_code="9082",
               wc_description="Restaurants",
               annual_gw=420_000.0, ftes=12.0, ptes=8.0, current_client_rate=2.10),
        # AZ codes
        WCLine(contact_id=contact.id, state="AZ", wc_code="8832",
               wc_description="Physicians & Clerical",
               annual_gw=590_000.0, ftes=10.0, ptes=2.0, current_client_rate=0.75),
        WCLine(contact_id=contact.id, state="AZ", wc_code="5537",
               wc_description="Heating/AC/Refrigeration Installation",
               annual_gw=380_000.0, ftes=8.0, ptes=3.0, current_client_rate=4.50),
    ]
    for wl in wc_lines:
        db.add(wl)
    print(f"    Added {len(wc_lines)} WC lines across CA/NV/AZ")

    # NV is client_reporting — client handles own SUTA filing, no VHR billing
    suta_lines = [
        SutaLine(contact_id=contact.id, state="CA",
                 gws=8_250_000.0, total_wses=123.0,
                 current_client_rate=0.034,
                 billing_rate=0.0682, cost_rate=0.062,
                 threshold=7000.0, turnover_pct=0.25),
        SutaLine(contact_id=contact.id, state="AZ",
                 gws=970_000.0, total_wses=21.0,
                 current_client_rate=0.020,
                 billing_rate=0.031, cost_rate=0.0256,
                 threshold=8000.0, turnover_pct=0.15),
    ]
    for sl in suta_lines:
        db.add(sl)
    print(f"    Added {len(suta_lines)} SUTA lines: CA, AZ (NV is client-reporting — omitted)")


# ── Client 3 ─────────────────────────────────────────────────────────────────
# Admin Method 3 (PEPM) — Midwest healthcare, EPLI included
# Tests: 4-state WC spread, 2 client-reporting SUTA states (OH, MI) alongside
#        2 VHR-reporting (IL, WI), EPLI rate, semimonthly payroll, mod < 1.0
def seed_great_lakes(db):
    NAME = "Great Lakes Healthcare Services Inc"
    if _skip_if_exists(db, NAME):
        return

    contact = Contact(
        legal_name=NAME,
        dba="Great Lakes HS",
        consultant_name="Rachel Okafor",
        consultant_name_split="Rachel Okafor",
        date="2026-05-09",
        main_address="233 S Wacker Dr Ste 4400",
        city="Chicago",
        state="IL",
        zip="60606",
        fein="36-7712058",
        website="www.glhealthcare.com",
        main_phone="312-555-0391",
        owner_name="Thomas Bergström",
        owner_email="t.bergstrom@glhealthcare.com",
        contact_name="Priya Nair",
        contact_email="p.nair@glhealthcare.com",
        contact_cell="312-555-0392",
        org_structure="Inc",
        naics="621111",
        sic="8049",
        years_in_business=17,
        num_locations=4,
        states_operating='["IL","OH","MI","WI"]',
        payroll_frequency="semimonthly",
        pay_cycle_start="Monday",
        pay_cycle_end="Sunday",
        pay_date="Friday",
        description_of_operations="Healthcare staffing and physician practice management across IL, OH, MI, WI. Mix of clinical and administrative staff.",
        # WC
        proposed_mod=0.94,
        # Admin — Method 3: PEPM
        admin_method=3,
        admin_rate_3=52.00,
        current_admin_rate_3=65.00,
        implementation_fee=3000.0,
        # Commission — direct (no external broker)
        internal_commission_pct=0.05,
        external_commission_pct=0.0,
        broker_wc_commission_pct=0.0,
        # EPLI — rate is $ / WSE / pay period; min $0.50
        include_epli=True,
        epli_rate=0.85,
        # FUTA — modest turnover, mostly full-time clinical staff
        futa_turnover_rate=0.08,
        # Compliance
        eeoc_violations=False,
        active_claims=True,
        active_claims_explanation="One open WC claim in OH, expected to close within 60 days.",
        past_layoffs=False,
        future_layoffs=False,
        leave_of_absence=True,
        leave_explanation="3 employees on FMLA.",
        # Medical
        medical_carve_out=False,
        currently_has_health_insurance=True,
        enrolled_over_50=False,
        enrolled_under_10=False,
    )
    db.add(contact)
    db.flush()
    print(f"  Created '{NAME}' (id={contact.id})")

    wc_lines = [
        # IL codes
        WCLine(contact_id=contact.id, state="IL", wc_code="8832",
               wc_description="Physicians & Clerical",
               annual_gw=2_800_000.0, ftes=38.0, ptes=6.0, current_client_rate=0.80),
        WCLine(contact_id=contact.id, state="IL", wc_code="8810",
               wc_description="Clerical Office Employees",
               annual_gw=1_200_000.0, ftes=22.0, ptes=4.0, current_client_rate=0.25),
        WCLine(contact_id=contact.id, state="IL", wc_code="8742",
               wc_description="Salespersons/Collectors - Outside",
               annual_gw=750_000.0, ftes=14.0, ptes=2.0, current_client_rate=0.55),
        # OH codes
        WCLine(contact_id=contact.id, state="OH", wc_code="8832",
               wc_description="Physicians & Clerical",
               annual_gw=1_650_000.0, ftes=25.0, ptes=4.0, current_client_rate=0.90),
        WCLine(contact_id=contact.id, state="OH", wc_code="8810",
               wc_description="Clerical Office Employees",
               annual_gw=620_000.0, ftes=12.0, ptes=2.0, current_client_rate=0.22),
        # MI codes
        WCLine(contact_id=contact.id, state="MI", wc_code="8832",
               wc_description="Physicians & Clerical",
               annual_gw=980_000.0, ftes=15.0, ptes=3.0, current_client_rate=0.85),
        WCLine(contact_id=contact.id, state="MI", wc_code="8810",
               wc_description="Clerical Office Employees",
               annual_gw=420_000.0, ftes=8.0, ptes=1.0, current_client_rate=0.24),
        # WI code
        WCLine(contact_id=contact.id, state="WI", wc_code="8832",
               wc_description="Physicians & Clerical",
               annual_gw=780_000.0, ftes=13.0, ptes=2.0, current_client_rate=0.78),
    ]
    for wl in wc_lines:
        db.add(wl)
    print(f"    Added {len(wc_lines)} WC lines across IL/OH/MI/WI")

    # OH and MI are client-reporting — client files own SUTA, no VHR billing
    suta_lines = [
        SutaLine(contact_id=contact.id, state="IL",
                 gws=4_750_000.0, total_wses=78.0,
                 current_client_rate=0.014,
                 billing_rate=0.02, cost_rate=0.0075,
                 threshold=14250.0, turnover_pct=0.09),
        SutaLine(contact_id=contact.id, state="WI",
                 gws=1_560_000.0, total_wses=28.0,
                 current_client_rate=0.011,
                 billing_rate=0.016, cost_rate=0.0135,
                 threshold=14000.0, turnover_pct=0.07),
    ]
    for sl in suta_lines:
        db.add(sl)
    print(f"    Added {len(suta_lines)} SUTA lines: IL, WI (OH + MI are client-reporting — omitted)")

    # WC loss history — 2 years, low severity (healthcare/clerical, mostly medical-only)
    wc_losses = [
        WCLoss(contact_id=contact.id,
               coverage_period_start="2022-01-01", coverage_period_end="2022-12-31",
               total_losses_incurred=31_200.0, num_claims=3, months_in_policy=12, open_claims=0),
        WCLoss(contact_id=contact.id,
               coverage_period_start="2023-01-01", coverage_period_end="2023-12-31",
               total_losses_incurred=58_700.0, num_claims=5, months_in_policy=12, open_claims=1),
    ]
    for wl in wc_losses:
        db.add(wl)
    print(f"    Added {len(wc_losses)} WC loss years (2022–2023)")


# ── Main ──────────────────────────────────────────────────────────────────────
def seed():
    db = SessionLocal()
    try:
        print("Seeding test contacts...")
        print()

        print("[1/3] Meridian Construction Group LLC — Admin Method 1 (% of GWs)")
        seed_meridian(db)

        print()
        print("[2/3] Pacific Rim Staffing LLC — Admin Method 2 (per-check, broker deal)")
        seed_pacific_rim(db)

        print()
        print("[3/3] Great Lakes Healthcare Services Inc — Admin Method 3 (PEPM, EPLI)")
        seed_great_lakes(db)

        db.commit()
        print()
        print("Done — all records committed.")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
