"""
Workers Comp routes — GET /wc-rate (rate lookup by state + class code),
GET /download/wc-rates, GET /download/wc-guidelines, POST /upload/wc-rates,
POST /upload/wc-guidelines. CSV uploads replace the entire table on each import.
"""
import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import SystemConfig, WCGuideline, WCRate

router = APIRouter(tags=["workers_comp"])


def _csv_response(rows: list[list], headers: list[str], filename: str) -> StreamingResponse:
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


def _lookup_wc_row_and_guideline(state: str, code: str, db: Session, independent_bureau_states: str):
    state = state.upper().strip()
    code = code.strip()
    concat_key = state + code
    ib_states = {s.strip().upper() for s in independent_bureau_states.split(",") if s.strip()}

    rate_row = db.query(WCRate).filter(WCRate.concat == concat_key).first()
    guideline_row = db.query(WCGuideline).filter(WCGuideline.concat == concat_key).first()

    if guideline_row is None and state not in ib_states:
        guideline_row = db.query(WCGuideline).filter(WCGuideline.concat == "Other" + code).first()

    return rate_row, guideline_row


@router.get("/wc-rate")
def get_wc_rate(
    state: str = Query(..., min_length=2, max_length=2),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
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
            db.add(WCRate(
                id=row_id,
                carrier=(row.get("Carrier") or "").strip(),
                state=(row.get("State") or "").strip(),
                class_code=(row.get("Class Code") or "").strip(),
                concat=(row.get("Concat") or "").strip(),
                rate=_safe_float(row.get("Rate") or ""),
                min_premium=_safe_float(row.get("Min Premium") or ""),
                description=(row.get("Description") or "").strip() or None,
                effective_date=(row.get("Effective Date") or "").strip() or None,
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
            db.add(WCGuideline(
                id=row_id,
                state=(row.get("State") or "").strip(),
                ncci_code=(row.get("NCCI Code") or "").strip(),
                lookup_code=(row.get("Lookup Code") or "").strip(),
                concat=(row.get("Concat") or "").strip(),
                irmi_classification=(row.get("IRMI Classification") or "").strip() or None,
                naics=(row.get("NAICS") or "").strip() or None,
                hazard_group=(row.get("Hazard Group") or "").strip() or None,
                flag_100k=(row.get("100K Flag") or "").strip() or None,
                effective_date=(row.get("Effective Date") or "").strip() or None,
            ))
            row_id += 1
            imported += 1
        except Exception:
            continue

    db.commit()
    return {"imported": imported}
