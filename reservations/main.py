import os
import logging
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from sqlalchemy.orm import Session
from models import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
    TextFileResponse,
    TextFileCreate,
    TextFileUpdate,
    SessionLocal,
)
from starlette.middleware.cors import CORSMiddleware
from vectors import DocumentProcessor
import crud
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

doc = DocumentProcessor()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoints

@app.get("/reservations", response_model=list[ReservationResponse], tags=["reservations"])
def list_reservations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    reservations = crud.list_reservations(db, skip, limit)
    return reservations


@app.post("/reservations", response_model=ReservationResponse, tags=["reservations"])
def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    new_reservation = crud.create_reservation(db, reservation)
    return new_reservation


@app.get("/reservations/{reservation_id}", response_model=ReservationResponse, tags=["reservations"])
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = crud.get_reservation(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@app.put("/reservations/{reservation_id}", response_model=ReservationResponse, tags=["reservations"])
def update_reservation(
    reservation_id: int, reservation: ReservationUpdate, db: Session = Depends(get_db)
):
    updated_reservation = crud.update_reservation(db, reservation_id, reservation)
    return updated_reservation

@app.get("/textfiles", response_model=list[TextFileResponse], tags=["textfiles"])
def list_textfiles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    textfiles = crud.list_textfiles(db, skip, limit)
    return textfiles

@app.post("/textfiles", response_model=TextFileResponse, tags=["textfiles"])
def upload_textfile(name: str | None = None, file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_extensions = [".pdf", ".docx", ".html"]

    file_name = file.filename
    file_extension = os.path.splitext(file.filename)[1].lower()
    namespace = os.urandom(8).hex()
    logger.info(f"Uploading file {file_name} with extension {file_extension}")
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}",
        )
    
    textfile = TextFileCreate(
        file_name=file_name, name=name, namespace=namespace, type=file_extension
    )
    file_obj = crud.create_textfile(db, textfile)
    logger.info(f"Created textfile with id {file_obj.id}")
    try :
        overview = doc.process_file_upload(file, namespace)
        logger.info(f"Processed file {file_name} with overview: \n {overview}\n")
        updated_file = crud.update_textfile(db, file_obj.id, TextFileUpdate(overview=overview))
        logger.info(f"Updated textfile with the overview")
        return updated_file
    except Exception as e:
        crud.delete_textfile(db, file_obj.id)
        logger.error(f"Failed to process file {file_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# get endpoint with query parameter
@app.get("/textfiles/retrieve", response_model=str, tags=["textfiles"])
async def retrieve_doc(query: str, namespace: str):
    return await doc.retrieve_docs(query, namespace)

@app.get("/textfiles/{textfile_id}", response_model=TextFileResponse, tags=["textfiles"])
def get_textfile(textfile_id: int, db: Session = Depends(get_db)):
    textfile = crud.get_textfile(db, textfile_id)
    return textfile

@app.put("/textfiles/{textfile_id}", response_model=TextFileResponse, tags=["textfiles"])
def update_textfile(
    textfile_id: int, textfile: TextFileUpdate, db: Session = Depends(get_db)
):
    updated_textfile = crud.update_textfile(db, textfile_id, textfile)
    return updated_textfile


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
