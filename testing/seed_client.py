"""
Idempotent seed script — creates one test client (Hartman Industrial LLC)
with 2 WC lines and 1 SUTA line. Safe to re-run: skips creation if the
client already exists.

Usage:
    python testing/seed_client.py
"""

import os
import sys

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Client, WCLine, SutaLine

LEGAL_NAME = "Hartman Industrial LLC"


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Client).filter(Client.legal_name == LEGAL_NAME).first()
        if existing:
            print(f"Client '{LEGAL_NAME}' already exists (id={existing.id}) — skipping.")
            return

        # --- Client ---
        client = Client(
            legal_name=LEGAL_NAME,
            dba="Hartman",
            consultant_name="Sarah Vance",
            date="2026-05-08",
            main_address="4820 Commerce Park Dr",
            city="Houston",
            state="TX",
            zip="77032",
            fein="82-4471839",
            org_structure="LLC",
            naics="332710",
            years_in_business=14,
            num_locations=2,
            payroll_frequency="biweekly",
            proposed_mod=0.88,
            admin_method=1,
            admin_rate=0.035,
            internal_commission_pct=0.05,
            external_commission_pct=0.0,
            futa_turnover_rate=1.5122,
        )
        db.add(client)
        db.flush()  # populate client.id before creating child records
        print(f"Created client '{LEGAL_NAME}' (id={client.id})")

        # --- WC Lines ---
        wc_lines = [
            WCLine(
                client_id=client.id,
                state="TX",
                wc_code="5190",
                annual_gw=1_800_000.0,
                ftes=28.0,
                ptes=6.0,
                current_client_rate=3.2,
                manual_rate=0.0,
            ),
            WCLine(
                client_id=client.id,
                state="TX",
                wc_code="8810",
                annual_gw=420_000.0,
                ftes=7.0,
                ptes=2.0,
                current_client_rate=0.35,
                manual_rate=0.0,
            ),
        ]
        for wl in wc_lines:
            db.add(wl)
        print(f"  Added {len(wc_lines)} WC line(s): codes {[w.wc_code for w in wc_lines]}")

        # --- SUTA Line ---
        suta_line = SutaLine(
            client_id=client.id,
            state="TX",
            gws=2_220_000.0,
            total_wses=43.0,
            current_client_rate=0.027,
            billing_rate=0.027,
            cost_rate=0.0472,
            threshold=9000.0,
            turnover_pct=0.10,
        )
        db.add(suta_line)
        print(f"  Added 1 SUTA line: TX @ billing={suta_line.billing_rate:.4f}, cost={suta_line.cost_rate:.4f}")

        db.commit()
        print("Done — all records committed.")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
