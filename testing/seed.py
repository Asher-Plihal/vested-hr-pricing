"""
Idempotent seed script. Run with: python seed.py
Seeds SystemConfig defaults only. SUTA rates, WC rates, and WC guidelines
must be uploaded via the config page before the tool produces valid numbers.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, SessionLocal, Base
from sqlalchemy import text

Base.metadata.create_all(bind=engine)

# ── Column migrations (idempotent) — must run before any ORM query ────────────
with engine.connect() as conn:
    existing = [row[1] for row in conn.execute(text("PRAGMA table_info(system_config)"))]
    for col, ddl in [
        ("consultant_commission_upfront", "ALTER TABLE system_config ADD COLUMN consultant_commission_upfront REAL DEFAULT 0.25"),
        ("consultant_commission_ongoing", "ALTER TABLE system_config ADD COLUMN consultant_commission_ongoing REAL DEFAULT 0.20"),
        ("fee_min_admin_per_cycle", "ALTER TABLE system_config ADD COLUMN fee_min_admin_per_cycle REAL DEFAULT 50.0"),
        ("fee_delivery_min", "ALTER TABLE system_config ADD COLUMN fee_delivery_min REAL DEFAULT 15.0"),
        ("fee_delivery_max", "ALTER TABLE system_config ADD COLUMN fee_delivery_max REAL DEFAULT 60.0"),
        ("fee_out_of_cycle_payroll", "ALTER TABLE system_config ADD COLUMN fee_out_of_cycle_payroll REAL DEFAULT 25.0"),
        ("fee_returned_check", "ALTER TABLE system_config ADD COLUMN fee_returned_check REAL DEFAULT 50.0"),
        ("fee_timekeeping_implementation", "ALTER TABLE system_config ADD COLUMN fee_timekeeping_implementation REAL DEFAULT 250.0"),
        ("fee_timekeeping_monthly_per_ee", "ALTER TABLE system_config ADD COLUMN fee_timekeeping_monthly_per_ee REAL DEFAULT 4.5"),
        ("fee_applicant_tracking_implementation", "ALTER TABLE system_config ADD COLUMN fee_applicant_tracking_implementation REAL DEFAULT 250.0"),
        ("fee_online_lms_implementation", "ALTER TABLE system_config ADD COLUMN fee_online_lms_implementation REAL DEFAULT 200.0"),
        ("fee_online_lms_per_ee_monthly", "ALTER TABLE system_config ADD COLUMN fee_online_lms_per_ee_monthly REAL DEFAULT 1.5"),
        ("fee_mvr_report", "ALTER TABLE system_config ADD COLUMN fee_mvr_report REAL DEFAULT 6.0"),
        ("fee_everify_per_ee", "ALTER TABLE system_config ADD COLUMN fee_everify_per_ee REAL DEFAULT 5.0"),
        ("fee_wc_waiver_subrogation", "ALTER TABLE system_config ADD COLUMN fee_wc_waiver_subrogation REAL DEFAULT 200.0"),
        ("fee_wc_late_reporting", "ALTER TABLE system_config ADD COLUMN fee_wc_late_reporting REAL DEFAULT 250.0"),
        ("fee_wc_alternate_employer_endorsement", "ALTER TABLE system_config ADD COLUMN fee_wc_alternate_employer_endorsement REAL DEFAULT 200.0"),
        ("fee_reactivation", "ALTER TABLE system_config ADD COLUMN fee_reactivation REAL DEFAULT 500.0"),
        ("fee_late_payroll_submission", "ALTER TABLE system_config ADD COLUMN fee_late_payroll_submission REAL DEFAULT 50.0"),
    ]:
        if col not in existing:
            conn.execute(text(ddl))
            conn.commit()
            print(f"Migrated: added {col}")

# ── SystemConfig ──────────────────────────────────────────────────────────────
from models import SystemConfig

db = SessionLocal()

existing_config = db.query(SystemConfig).first()
if not existing_config:
    db.add(SystemConfig(
        id=1,
        ss_rate=0.062,
        medicare_rate=0.0145,
        ss_wage_base=176100,
        futa_rate=0.006,
        futa_wage_base=7000,
        fixed_cost_factor=0.39,
        loss_fund_factor=0.5,
        combined_cost_factor=0.89,
        pte_weight=0.75,
        monopolistic_states="WA,WY,ND,OH",
        mcp_states="RI,NY,NJ,PA,LA,WI,MN,SD,KS,MT,AZ,UT,NV,CA,OR",
        pay_periods_json='{"weekly":52,"biweekly":26,"semimonthly":24,"monthly":12}',
        wc_policy_adjustment=0.0,
        futa_approach="B",
    ))
    db.commit()
    print("Seeded SystemConfig")
else:
    print("SystemConfig already exists — skipped")

db.close()

print("Seed complete.")
