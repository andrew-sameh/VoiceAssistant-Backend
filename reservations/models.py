import os
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Text, DateTime, Sequence, Boolean
from datetime import datetime, date as dt_date,time as dt_time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
load_dotenv('.env')

# Database setup
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define the reservations table
class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, Sequence('reservation_id_seq', start=100, increment=1), primary_key=True, index=True)
    name = Column(String, nullable=False)
    number = Column(String, nullable=False)
    people_count = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    room = Column(String, nullable=False)
    movie_id = Column(Integer, nullable=True)
    movie_name = Column(String, nullable=True)
    movie_desc = Column(Text, nullable=True)
    movie_image = Column(String, nullable=True)
    snack_package = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class TextFile(Base):
    __tablename__ = "text_files"

    id = Column(Integer, Sequence('textfiles_id_seq', start=1, increment=1), primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    namespace = Column(String, nullable=False)
    type = Column(String, nullable=False)
    overview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the table
Base.metadata.create_all(bind=engine)


# Pydantic schema for validation
class ReservationBase(BaseModel):
    name: str
    number: str
    people_count: int
    date: dt_date 
    time: dt_time
    room: str
    movie_id: int | None
    movie_name: str | None
    movie_desc: str | None
    movie_image: str | None
    snack_package: bool | None
    status: str

class TextFileBase(BaseModel):
    file_name: str
    name: str
    namespace: str
    type: str
    overview: str | None = None

class ReservationCreate(ReservationBase):
    pass

class TextFileCreate(TextFileBase):
    pass

class ReservationUpdate(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    people_count: Optional[int] = None
    date: Optional[dt_date] = None
    time: Optional[dt_time] = None
    room: Optional[str] = None
    movie_id: Optional[int] = None
    movie_name: Optional[str] = None
    movie_desc: Optional[str] = None
    movie_image: Optional[str] = None
    snack_package: Optional[bool] = None
    status: Optional[str] = None

class TextFileUpdate(BaseModel):
    file_name: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    type: Optional[str] = None
    overview: Optional[str] = None

class ReservationResponse(ReservationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TextFileResponse(TextFileBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True