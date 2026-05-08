"""
Idempotent seed script. Run with: python seed.py
SUTA rates sourced from pricing_math.md where explicitly listed.
States not listed use placeholder values and are flagged — verify with VHR staff.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, SessionLocal, Base
from models import SystemConfig, SutaRate

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

# ── SutaRate — 51 rows (50 states + DC) ──────────────────────────────────────
# Threshold = annual SUTA wage base per WSE
# vhr_min_rate = VHR minimum billing rate (None for client-reporting states)
# client_reporting = True means client files under own rate; VHR passes through
# our_cost = VHR's actual cost rate
#
# States marked PLACEHOLDER need verification with VHR staff before going live.

SUTA_ROWS = [
    # state, threshold, vhr_min_rate, client_reporting, our_cost
    # --- States with known values from pricing_math.md / VHR materials ---
    ("AL", 8000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("AK", 49700, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("AZ", 8000,  0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("AR", 10000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("CA", 7000,  None,  True,  0.034),   # Client-reporting; MCP state
    ("CO", 20400, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("CT", 25000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("DC", 9000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("DE", 10500, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("FL", 7000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("GA", 9500,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("HI", 62050, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("ID", 50000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("IL", 13590, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("IN", 9500,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("IA", 38200, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("KS", 14000, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("KY", 11100, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("LA", 7700,  0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("ME", 12000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("MD", 8500,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("MA", 15000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("MI", 9500,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("MN", 42000, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("MS", 14000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("MO", 10000, 0.027, False, 0.027),   # Note: per pricing_math.md, MO is client-reporting for filing but uses VHR rate — verify
    ("MT", 43000, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("NE", 9000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("NV", 40600, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("NH", 14000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("NJ", 42300, None,  True,  0.027),   # Client-reporting; MCP state — verify cost rate
    ("NM", 31700, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("NY", 12800, None,  True,  0.034),   # Client-reporting; MCP state — verify cost rate
    ("NC", 31400, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("ND", 42200, 0.027, False, 0.027),   # Monopolistic WC state — verify SUTA with VHR
    ("OH", 9000,  0.027, False, 0.027),   # Monopolistic WC state — PLACEHOLDER, verify with VHR
    ("OK", 25700, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("OR", 54300, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("PA", 10000, None,  True,  0.034),   # Client-reporting; MCP state — verify cost rate
    ("RI", 29200, None,  True,  0.034),   # Client-reporting; MCP state — verify cost rate
    ("SC", 14000, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("SD", 15000, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("TN", 7000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("TX", 9000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("UT", 47000, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("VT", 14300, 0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("VA", 8000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("WA", 72800, 0.027, False, 0.027),   # Monopolistic WC state — verify SUTA with VHR
    ("WV", 9000,  0.027, False, 0.027),   # PLACEHOLDER — verify with VHR
    ("WI", 14000, 0.027, False, 0.027),   # MCP state — PLACEHOLDER, verify with VHR
    ("WY", 30900, 0.027, False, 0.027),   # Monopolistic WC state — verify SUTA with VHR
]

existing_states = {r.state for r in db.query(SutaRate.state).all()}
added = 0
for state, threshold, vhr_min_rate, client_reporting, our_cost in SUTA_ROWS:
    if state not in existing_states:
        db.add(SutaRate(
            state=state,
            threshold=threshold,
            vhr_min_rate=vhr_min_rate,
            client_reporting=client_reporting,
            our_cost=our_cost,
        ))
        added += 1

db.commit()
print(f"Seeded {added} SutaRate rows ({len(existing_states)} already existed)")
db.close()
print("Seed complete.")
