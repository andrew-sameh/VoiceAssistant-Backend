from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Reservation, ReservationCreate, ReservationUpdate, ReservationResponse, SessionLocal
from starlette.middleware.cors import CORSMiddleware



# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/reservations/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@app.get("/reservations", response_model=list[ReservationResponse])
def list_reservations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    reservations = db.query(Reservation).offset(skip).limit(limit).all()
    return reservations

@app.post("/reservations", response_model=ReservationResponse)
def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    new_reservation = Reservation(**reservation.dict())
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return new_reservation

@app.put("/reservations/{reservation_id}", response_model=ReservationResponse)
def update_reservation(reservation_id: int, reservation: ReservationUpdate, db: Session = Depends(get_db)):
    existing_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not existing_reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    for key, value in reservation.dict(exclude_unset=True).items():
        if value is not None:
            setattr(existing_reservation, key, value)

    db.commit()
    db.refresh(existing_reservation)
    return existing_reservation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
