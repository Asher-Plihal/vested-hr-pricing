from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Contact, WCLine, SutaLine, WCLoss
from schemas import ContactCreate, ContactListItem, ContactOut, ContactUpdate, WCLineOut, SutaLineOut, WCLossOut

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _contact_to_out(contact: Contact, db: Session) -> ContactOut:
    wc_lines = db.query(WCLine).filter(WCLine.contact_id == contact.id).all()
    suta_lines = db.query(SutaLine).filter(SutaLine.contact_id == contact.id).all()
    wc_losses = db.query(WCLoss).filter(WCLoss.contact_id == contact.id).all()
    data = ContactOut.model_validate(contact)
    data.wc_lines = [WCLineOut.model_validate(l) for l in wc_lines]
    data.suta_lines = [SutaLineOut.model_validate(l) for l in suta_lines]
    data.wc_losses = [WCLossOut.model_validate(l) for l in wc_losses]
    return data


@router.get("", response_model=list[ContactListItem])
def list_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).order_by(Contact.updated_at.desc()).all()


@router.post("", response_model=dict)
def create_contact(body: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(
        legal_name=body.legal_name,
        consultant_name=body.consultant_name,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"id": contact.id}


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return _contact_to_out(contact, db)


@router.put("/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = body.model_dump(exclude_none=True, exclude={"wc_lines", "suta_lines", "wc_losses"})
    for field, value in update_data.items():
        setattr(contact, field, value)
    contact.updated_at = datetime.utcnow()

    if body.wc_lines is not None:
        db.query(WCLine).filter(WCLine.contact_id == contact_id).delete()
        for line in body.wc_lines:
            db.add(WCLine(contact_id=contact_id, **line.model_dump()))

    if body.suta_lines is not None:
        db.query(SutaLine).filter(SutaLine.contact_id == contact_id).delete()
        for line in body.suta_lines:
            db.add(SutaLine(contact_id=contact_id, **line.model_dump()))

    if body.wc_losses is not None:
        db.query(WCLoss).filter(WCLoss.contact_id == contact_id).delete()
        for loss in body.wc_losses:
            db.add(WCLoss(contact_id=contact_id, **loss.model_dump()))

    db.commit()
    db.refresh(contact)
    return _contact_to_out(contact, db)


@router.delete("/{contact_id}", response_model=dict)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.query(WCLoss).filter(WCLoss.contact_id == contact_id).delete()
    db.query(WCLine).filter(WCLine.contact_id == contact_id).delete()
    db.query(SutaLine).filter(SutaLine.contact_id == contact_id).delete()
    db.delete(contact)
    db.commit()
    return {"success": True}
