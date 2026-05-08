from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Client, WCLine, SutaLine, WCLoss
from schemas import ClientCreate, ClientListItem, ClientOut, ClientUpdate, WCLineOut, SutaLineOut, WCLossOut

router = APIRouter(prefix="/clients", tags=["clients"])


def _client_to_out(client: Client, db: Session) -> ClientOut:
    wc_lines = db.query(WCLine).filter(WCLine.client_id == client.id).all()
    suta_lines = db.query(SutaLine).filter(SutaLine.client_id == client.id).all()
    wc_losses = db.query(WCLoss).filter(WCLoss.client_id == client.id).all()
    data = ClientOut.model_validate(client)
    data.wc_lines = [WCLineOut.model_validate(l) for l in wc_lines]
    data.suta_lines = [SutaLineOut.model_validate(l) for l in suta_lines]
    data.wc_losses = [WCLossOut.model_validate(l) for l in wc_losses]
    return data


@router.get("", response_model=list[ClientListItem])
def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).order_by(Client.updated_at.desc()).all()


@router.post("", response_model=dict)
def create_client(body: ClientCreate, db: Session = Depends(get_db)):
    client = Client(
        legal_name=body.legal_name,
        consultant_name=body.consultant_name,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"id": client.id}


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return _client_to_out(client, db)


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, body: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = body.model_dump(exclude_none=True, exclude={"wc_lines", "suta_lines", "wc_losses"})
    for field, value in update_data.items():
        setattr(client, field, value)
    client.updated_at = datetime.utcnow()

    if body.wc_lines is not None:
        db.query(WCLine).filter(WCLine.client_id == client_id).delete()
        for line in body.wc_lines:
            db.add(WCLine(client_id=client_id, **line.model_dump()))

    if body.suta_lines is not None:
        db.query(SutaLine).filter(SutaLine.client_id == client_id).delete()
        for line in body.suta_lines:
            db.add(SutaLine(client_id=client_id, **line.model_dump()))

    if body.wc_losses is not None:
        db.query(WCLoss).filter(WCLoss.client_id == client_id).delete()
        for loss in body.wc_losses:
            db.add(WCLoss(client_id=client_id, **loss.model_dump()))

    db.commit()
    db.refresh(client)
    return _client_to_out(client, db)
