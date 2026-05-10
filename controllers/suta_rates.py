from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import SutaRate
from schemas import SutaRateOut, SutaRateUpdate

router = APIRouter(prefix="/suta-rates", tags=["suta-rates"])


@router.get("", response_model=list[SutaRateOut])
def get_suta_rates(db: Session = Depends(get_db)):
    return db.query(SutaRate).order_by(SutaRate.state).all()


@router.put("", response_model=list[SutaRateOut])
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
