"""
Handles reading and updating the system-wide configuration that applies to all clients —
things like FICA rates, FUTA rates, WC cost factors, commission defaults, and additional
fee schedules. There is only ever one config record in the database. The config page in
the UI autosaves every field 600ms after a change, so every edit hits this endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import SystemConfig
from schemas import SystemConfigOut, SystemConfigUpdate

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=SystemConfigOut)
def get_config(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).first()
    if not config:
        raise HTTPException(status_code=404, detail="SystemConfig not seeded")
    return config


@router.put("", response_model=SystemConfigOut)
def update_config(body: SystemConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(SystemConfig).first()
    if not config:
        raise HTTPException(status_code=404, detail="SystemConfig not seeded")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config
