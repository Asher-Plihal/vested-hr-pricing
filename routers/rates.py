import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import SutaRate, SystemConfig, WCGuideline, WCRate

router = APIRouter(tags=["rates"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _csv_response(rows: list[list], headers: list[str], filename: str) -> StreamingResponse:
    """Build a StreamingResponse that sends a CSV file."""
    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        yield buf.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _safe_float(val: str):
    val = val.strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


# ── WC Rate Lookup ────────────────────────────────────────────────────────────

def _lookup_wc_row_and_guideline(state: str, code: str, db: Session, independent_bureau_states: str):
    """Return (WCRate, WCGuideline) using independent bureau or NCCI fallback logic."""
    state = state.upper().strip()
    code = code.strip()
    concat_key = state + code
    ib_states = {s.strip().upper() for s in independent_bureau_states.split(",") if s.strip()}

    rate_row = db.query(WCRate).filter(WCRate.concat == concat_key).first()
    guideline_row = db.query(WCGuideline).filter(WCGuideline.concat == concat_key).first()

    if state not in ib_states:
        fallback_key = "Other" + code
        if rate_row is None:
            rate_row = db.query(WCRate).filter(WCRate.concat == fallback_key).first()
        if guideline_row is None:
            guideline_row = db.query(WCGuideline).filter(WCGuideline.concat == fallback_key).first()

    return rate_row, guideline_row


@router.get("/wc-rate")
def get_wc_rate(
    state: str = Query(..., min_length=2, max_length=2),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """Look up a WC cost rate by state + class code. Returns rate, description, hazard_group, flag_100k or 404."""
    cfg = db.query(SystemConfig).first()
    ib_states_str = (cfg.independent_bureau_states or "") if cfg else ""

    rate_row, guideline_row = _lookup_wc_row_and_guideline(state, code, db, ib_states_str)

    if rate_row is None or rate_row.rate is None:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "rate": rate_row.rate,
        "description": rate_row.description or "",
        "hazard_group": guideline_row.hazard_group if guideline_row else "",
        "flag_100k": guideline_row.flag_100k if guideline_row else None,
    }


# ── Downloads ─────────────────────────────────────────────────────────────────

@router.get("/download/wc-rates")
def download_wc_rates(db: Session = Depends(get_db)):
    rows = db.query(WCRate).all()
    data = [
        [r.carrier, r.state, r.class_code, r.concat, r.rate,
         r.min_premium, r.description, r.effective_date]
        for r in rows
    ]
    return _csv_response(
        data,
        ["Carrier", "State", "Class Code", "Concat", "Rate",
         "Min Premium", "Description", "Effective Date"],
        "wc_rates.csv",
    )


@router.get("/download/wc-guidelines")
def download_wc_guidelines(db: Session = Depends(get_db)):
    rows = db.query(WCGuideline).all()
    data = [
        [r.state, r.ncci_code, r.lookup_code, r.concat,
         r.irmi_classification, r.naics, r.hazard_group,
         r.flag_100k, r.effective_date]
        for r in rows
    ]
    return _csv_response(
        data,
        ["State", "NCCI Code", "Lookup Code", "Concat",
         "IRMI Classification", "NAICS", "Hazard Group",
         "100K Flag", "Effective Date"],
        "wc_guidelines.csv",
    )


_STATE_NAMES = {
    "AK": "Alaska", "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DC": "District of Columbia",
    "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "IA": "Iowa", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts",
    "MD": "Maryland", "ME": "Maine", "MI": "Michigan", "MN": "Minnesota",
    "MO": "Missouri", "MS": "Mississippi", "MT": "Montana", "NC": "North Carolina",
    "ND": "North Dakota", "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NV": "Nevada", "NY": "New York", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VA": "Virginia", "VT": "Vermont", "WA": "Washington",
    "WI": "Wisconsin", "WV": "West Virginia", "WY": "Wyoming",
}


@router.get("/download/suta-rates")
def download_suta_rates(db: Session = Depends(get_db)):
    rows = db.query(SutaRate).order_by(SutaRate.state).all()
    # DB stores decimals (0.027); sheet expects percentages (2.7)
    data = [
        [_STATE_NAMES.get(r.state, ""), r.state, r.threshold,
         round(r.vhr_min_rate * 100, 6) if r.vhr_min_rate is not None else None,
         "Y" if r.client_reporting else "N",
         round(r.our_cost * 100, 6) if r.our_cost is not None else None,
         r.date_updated]
        for r in rows
    ]
    return _csv_response(
        data,
        ["State Name", "State", "Threshold", "VHR Min Rate",
         "Client Reporting", "Our Cost", "Date Updated"],
        "suta_rates.csv",
    )


# ── Uploads ───────────────────────────────────────────────────────────────────

@router.post("/upload/wc-rates")
async def upload_wc_rates(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    db.query(WCRate).delete()

    imported = 0
    row_id = 1
    for row in reader:
        try:
            carrier       = (row.get("Carrier") or "").strip()
            state         = (row.get("State") or "").strip()
            class_code    = (row.get("Class Code") or "").strip()
            concat        = (row.get("Concat") or "").strip()
            rate          = _safe_float(row.get("Rate") or "")
            min_premium   = _safe_float(row.get("Min Premium") or "")
            description   = (row.get("Description") or "").strip() or None
            effective_date = (row.get("Effective Date") or "").strip() or None

            db.add(WCRate(
                id=row_id,
                carrier=carrier,
                state=state,
                class_code=class_code,
                concat=concat,
                rate=rate,
                min_premium=min_premium,
                description=description,
                effective_date=effective_date,
            ))
            row_id += 1
            imported += 1
        except Exception:
            continue

    db.commit()
    return {"imported": imported}


@router.post("/upload/wc-guidelines")
async def upload_wc_guidelines(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    db.query(WCGuideline).delete()

    imported = 0
    row_id = 1
    for row in reader:
        try:
            state             = (row.get("State") or "").strip()
            ncci_code         = (row.get("NCCI Code") or "").strip()
            lookup_code       = (row.get("Lookup Code") or "").strip()
            concat            = (row.get("Concat") or "").strip()
            irmi_classification = (row.get("IRMI Classification") or "").strip() or None
            naics             = (row.get("NAICS") or "").strip() or None
            hazard_group      = (row.get("Hazard Group") or "").strip() or None
            flag_100k         = (row.get("100K Flag") or "").strip() or None
            effective_date    = (row.get("Effective Date") or "").strip() or None

            db.add(WCGuideline(
                id=row_id,
                state=state,
                ncci_code=ncci_code,
                lookup_code=lookup_code,
                concat=concat,
                irmi_classification=irmi_classification,
                naics=naics,
                hazard_group=hazard_group,
                flag_100k=flag_100k,
                effective_date=effective_date,
            ))
            row_id += 1
            imported += 1
        except Exception:
            continue

    db.commit()
    return {"imported": imported}


@router.post("/upload/suta-rates")
async def upload_suta_rates(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    db.query(SutaRate).delete()

    imported = 0
    row_id = 1
    for row in reader:
        try:
            state            = (row.get("State") or "").strip()
            threshold        = _safe_float(row.get("Threshold") or "")
            # Sheet stores rates as percentages (2.7 = 2.7%); DB stores decimals (0.027)
            raw_vhr          = _safe_float(row.get("VHR Min Rate") or "")
            vhr_min_rate     = raw_vhr / 100 if raw_vhr is not None else None
            client_reporting = (row.get("Client Reporting") or "").strip().upper() == "Y"
            raw_cost         = _safe_float(row.get("Our Cost") or "")
            our_cost         = raw_cost / 100 if raw_cost is not None else None
            date_updated     = (row.get("Date Updated") or "").strip() or None

            if not state:
                continue

            db.add(SutaRate(
                id=row_id,
                state=state,
                threshold=threshold,
                vhr_min_rate=vhr_min_rate,
                client_reporting=client_reporting,
                our_cost=our_cost,
                date_updated=date_updated,
            ))
            row_id += 1
            imported += 1
        except Exception:
            continue

    db.commit()
    return {"imported": imported}
