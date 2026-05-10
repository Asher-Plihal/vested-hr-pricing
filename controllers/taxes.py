import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import SutaRate
from schemas import SutaRateOut, SutaRateUpdate

router = APIRouter(tags=["taxes"])


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


# ── SUTA Rates CRUD ───────────────────────────────────────────────────────────

@router.get("/suta-rates", response_model=list[SutaRateOut])
def get_suta_rates(db: Session = Depends(get_db)):
    return db.query(SutaRate).order_by(SutaRate.state).all()


@router.put("/suta-rates", response_model=list[SutaRateOut])
def update_suta_rates(body: list[SutaRateUpdate], db: Session = Depends(get_db)):
    updated = []
    for item in body:
        row = db.query(SutaRate).filter(SutaRate.state == item.state).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"State not found: {item.state}")
        for field, value in item.model_dump(exclude_none=True, exclude={"state"}).items():
            setattr(row, field, value)
        updated.append(row)
    db.commit()
    for row in updated:
        db.refresh(row)
    return updated


# ── SUTA CSV Download / Upload ────────────────────────────────────────────────

@router.get("/download/suta-rates")
def download_suta_rates(db: Session = Depends(get_db)):
    rows = db.query(SutaRate).order_by(SutaRate.state).all()
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
            state = (row.get("State") or "").strip()
            if not state:
                continue
            threshold = _safe_float(row.get("Threshold") or "")
            # Sheet stores rates as percentages (2.7 = 2.7%); DB stores decimals (0.027)
            raw_vhr = _safe_float(row.get("VHR Min Rate") or "")
            raw_cost = _safe_float(row.get("Our Cost") or "")
            db.add(SutaRate(
                id=row_id,
                state=state,
                threshold=threshold,
                vhr_min_rate=raw_vhr / 100 if raw_vhr is not None else None,
                client_reporting=(row.get("Client Reporting") or "").strip().upper() == "Y",
                our_cost=raw_cost / 100 if raw_cost is not None else None,
                date_updated=(row.get("Date Updated") or "").strip() or None,
            ))
            row_id += 1
            imported += 1
        except Exception:
            continue

    db.commit()
    return {"imported": imported}
