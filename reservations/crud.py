from sqlalchemy.orm import Session
from models import Reservation, ReservationCreate, ReservationUpdate, TextFile, TextFileCreate, TextFileUpdate

# Reservations
def get_reservation(db: Session, reservation_id: int):
    return db.query(Reservation).filter(Reservation.id == reservation_id).first()

def list_reservations(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Reservation).offset(skip).limit(limit).all()

def create_reservation(db: Session, reservation: ReservationCreate):
    new_reservation = Reservation(**reservation.dict())
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return new_reservation

def delete_reservation(db: Session, reservation_id: int):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        return None

    db.delete(reservation)
    db.commit()
    return reservation

def update_reservation(db: Session, reservation_id: int, reservation: ReservationUpdate):
    existing_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not existing_reservation:
        return None

    for key, value in reservation.dict(exclude_unset=True).items():
        if value is not None:
            setattr(existing_reservation, key, value)

    db.commit()
    db.refresh(existing_reservation)
    return existing_reservation

# TextFiles
def get_textfile(db: Session, textfile_id: int):
    return db.query(TextFile).filter(TextFile.id == textfile_id).first()

def list_textfiles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(TextFile).offset(skip).limit(limit).all()

def create_textfile(db: Session, textfile: TextFileCreate):
    new_textfile = TextFile(**textfile.dict())
    db.add(new_textfile)
    db.commit()
    db.refresh(new_textfile)
    return new_textfile

def delete_textfile(db: Session, textfile_id: int):
    textfile = db.query(TextFile).filter(TextFile.id == textfile_id).first()
    if not textfile:
        return None

    db.delete(textfile)
    db.commit()
    return textfile

def update_textfile(db: Session, textfile_id: int, textfile: TextFileUpdate):
    existing_textfile = db.query(TextFile).filter(TextFile.id == textfile_id).first()
    if not existing_textfile:
        return None

    for key, value in textfile.dict(exclude_unset=True).items():
        if value is not None:
            setattr(existing_textfile, key, value)

    db.commit()
    db.refresh(existing_textfile)
    return existing_textfile