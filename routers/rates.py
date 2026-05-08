import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import SutaRate, WCGuideline, WCRate

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

@router.get("/wc-rate")
def get_wc_rate(
    state: str = Query(..., min_length=2, max_length=2),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """Look up a WC cost rate by state + class code. Returns {"rate": float} or 404."""
    concat_key = state.upper().strip() + code.strip()
    row = db.query(WCRate).filter(WCRate.concat == concat_key).first()
    if row is None or row.rate is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"rate": row.rate}


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


@router.get("/download/suta-rates")
def download_suta_rates(db: Session = Depends(get_db)):
    rows = db.query(SutaRate).order_by(SutaRate.state).all()
    data = [
        [r.state, r.threshold, r.vhr_min_rate,
         "Y" if r.client_reporting else "N",
         r.our_cost, None]
        for r in rows
    ]
    return _csv_response(
        data,
        ["State", "Threshold", "VHR Min Rate",
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
            vhr_min_rate     = _safe_float(row.get("VHR Min Rate") or "")
            client_reporting = (row.get("Client Reporting") or "").strip().upper() == "Y"
            our_cost         = _safe_float(row.get("Our Cost") or "")

            if not state:
                continue

            db.add(SutaRate(
                id=row_id,
                state=state,
                threshold=threshold,
                vhr_min_rate=vhr_min_rate,
                client_reporting=client_reporting,
                our_cost=our_cost,
            ))
            row_id += 1
            imported += 1
        except Exception:
            continue

    db.commit()
    return {"imported": imported}
