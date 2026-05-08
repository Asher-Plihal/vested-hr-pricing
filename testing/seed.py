"""
Idempotent seed script. Run with: python seed.py
Seeds SystemConfig defaults only. SUTA rates, WC rates, and WC guidelines
must be uploaded via the config page before the tool produces valid numbers.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, SessionLocal, Base
from models import SystemConfig

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── SystemConfig ──────────────────────────────────────────────────────────────

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
