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
