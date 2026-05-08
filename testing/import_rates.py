"""
Import real rate data from the VHR pricing Excel file into the SQLite DB.

Usage:
    python testing/import_rates.py

Idempotent — safe to re-run.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import openpyxl

from database import SessionLocal
from models import SutaRate, WCGuideline, WCRate

EXCEL_PATH = r"C:\workspaces\business\vested-hr\documents\Pricing Template 03.10.26_ALL SHEETS.xlsx"

BATCH_SIZE = 500


def fmt_date(val):
    """Format a datetime object as YYYY-MM-DD string, or return None."""
    if val is None:
        return None
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    return None


def to_decimal_rate(val):
    """
    Convert a rate value to decimal form.
    Spreadsheet stores rates as percentages (e.g. 2.7 means 2.7%).
    Exception: if val < 0.10 it is already in decimal form — use as-is.
    Returns None if val is None.
    """
    if val is None:
        return None
    try:
        v = float(val)
    except (TypeError, ValueError):
        return None
    if v < 0.10:
        return v
    return v / 100.0


# ── A) WC Cost Rates → wc_rates ───────────────────────────────────────────────

def import_wc_rates(wb, db):
    print("Importing WC Cost Rates...")

    db.query(WCRate).delete()
    db.commit()

    ws = wb["WC Cost Rates"]
    row_id = 1
    batch = []
    imported = 0

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=8):
        # Columns: Carrier(0) State(1) Class(2) Concat(3) Rate(4) EffDate(5) MinPremium(6) Desc(7)
        carrier      = row[0].value
        state        = row[1].value
        class_raw    = row[2].value
        concat       = row[3].value
        rate_val     = row[4].value
        eff_date_raw = row[5].value
        min_prem     = row[6].value
        description  = row[7].value

        if not state:
            continue

        class_code = str(int(class_raw)) if isinstance(class_raw, (int, float)) else (str(class_raw).strip() if class_raw else None)
        concat_str = str(concat).strip() if concat else None
        rate       = float(rate_val) if rate_val is not None else None
        eff_date   = fmt_date(eff_date_raw)
        min_prem_f = float(min_prem) if min_prem is not None else None
        desc_str   = str(description).strip() if description else None
        carrier_str = str(carrier).strip() if carrier else None
        state_str  = str(state).strip()

        batch.append(WCRate(
            id=row_id,
            carrier=carrier_str,
            state=state_str,
            class_code=class_code,
            concat=concat_str,
            rate=rate,
            min_premium=min_prem_f,
            description=desc_str,
            effective_date=eff_date,
        ))
        row_id += 1
        imported += 1

        if len(batch) >= BATCH_SIZE:
            db.add_all(batch)
            db.commit()
            batch = []
            print(f"  ...{imported} rows committed")

    if batch:
        db.add_all(batch)
        db.commit()

    print(f"WC Cost Rates: {imported} rows imported.")
    return imported


# ── B) WC Sunz Guidelines → wc_guidelines ─────────────────────────────────────

def import_wc_guidelines(wb, db):
    print("Importing WC Sunz Guidelines...")

    db.query(WCGuideline).delete()
    db.commit()

    ws = wb["WC Sunz Guidelines"]
    row_id = 1
    batch = []
    imported = 0

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=9):
        # Columns: State(0) NCCICode(1) LookupCode(2) Concat(3) IRMI(4) NAICS(5) Hazard(6) 100K(7) AsOf(8)
        state        = row[0].value
        ncci_raw     = row[1].value
        lookup_raw   = row[2].value
        concat       = row[3].value
        irmi         = row[4].value
        naics        = row[5].value
        hazard       = row[6].value
        flag_100k    = row[7].value
        eff_date_raw = row[8].value

        if not state:
            continue

        state_str    = str(state).strip()
        ncci_code    = str(int(ncci_raw)) if isinstance(ncci_raw, (int, float)) else (str(ncci_raw).strip() if ncci_raw else None)
        lookup_code  = str(int(lookup_raw)) if isinstance(lookup_raw, (int, float)) else (str(lookup_raw).strip() if lookup_raw else None)
        concat_str   = str(concat).strip() if concat else None
        irmi_str     = str(irmi).strip() if irmi else None
        naics_str    = str(int(naics)) if isinstance(naics, (int, float)) else (str(naics).strip() if naics else None)
        hazard_str   = str(hazard).strip() if hazard else None
        flag_str     = str(flag_100k).strip() if flag_100k else None
        eff_date     = fmt_date(eff_date_raw)

        batch.append(WCGuideline(
            id=row_id,
            state=state_str,
            ncci_code=ncci_code,
            lookup_code=lookup_code,
            concat=concat_str,
            irmi_classification=irmi_str,
            naics=naics_str,
            hazard_group=hazard_str,
            flag_100k=flag_str,
            effective_date=eff_date,
        ))
        row_id += 1
        imported += 1

        if len(batch) >= BATCH_SIZE:
            db.add_all(batch)
            db.commit()
            batch = []
            print(f"  ...{imported} rows committed")

    if batch:
        db.add_all(batch)
        db.commit()

    print(f"WC Sunz Guidelines: {imported} rows imported.")
    return imported


# ── C) SUTA Cost Rates → suta_rates ──────────────────────────────────────────

# States whose note rows at the bottom should be skipped
_NOTE_STATES = {"MT", "ME", "ID", "MO"}


def import_suta_rates(wb, db):
    print("Importing SUTA Cost Rates...")

    # Delete-and-reinsert approach (preserves manual corrections via full refresh)
    db.query(SutaRate).delete()
    db.commit()

    ws = wb["SUTA Cost Rates"]
    imported = 0
    row_id = 1

    # Track which states we have already inserted so note rows don't re-insert
    seen_states = set()

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=10):
        state_val = row[0].value

        # Stop on blank state
        if state_val is None:
            continue

        # Skip non-string states (shouldn't happen, but guard)
        if not isinstance(state_val, str):
            continue

        state_str = state_val.strip()
        if not state_str:
            continue

        # Skip the trailing note rows (MT/ME/ID/MO duplicates at bottom)
        if state_str in seen_states:
            continue

        # Columns: A=State(0) B=Threshold(1) C=VHRMinRate(2) D=ClientReporting(3) E=DateUpdated(4)
        # J=OurCost(9) — index 9 in this 10-col range
        threshold_val       = row[1].value
        vhr_min_rate_raw    = row[2].value
        client_rep_raw      = row[3].value
        our_cost_raw        = row[9].value

        threshold = float(threshold_val) if threshold_val is not None else None

        client_reporting = False
        if isinstance(client_rep_raw, str):
            client_reporting = client_rep_raw.strip().upper() == "Y"

        vhr_min_rate = to_decimal_rate(vhr_min_rate_raw)
        our_cost     = to_decimal_rate(our_cost_raw)

        seen_states.add(state_str)

        db.add(SutaRate(
            id=row_id,
            state=state_str,
            threshold=threshold,
            vhr_min_rate=vhr_min_rate,
            client_reporting=client_reporting,
            our_cost=our_cost,
        ))
        row_id += 1
        imported += 1

    db.commit()
    print(f"SUTA Cost Rates: {imported} rows imported.")
    return imported


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Opening {EXCEL_PATH} ...")
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

    db = SessionLocal()
    try:
        wc_count   = import_wc_rates(wb, db)
        wg_count   = import_wc_guidelines(wb, db)
        suta_count = import_suta_rates(wb, db)

        print()
        print("Done.")
        print(f"  wc_rates:      {wc_count:,} rows")
        print(f"  wc_guidelines: {wg_count:,} rows")
        print(f"  suta_rates:    {suta_count:,} rows")
    finally:
        db.close()
        wb.close()


if __name__ == "__main__":
    main()
