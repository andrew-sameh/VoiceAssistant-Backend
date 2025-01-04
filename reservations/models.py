import os
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Text, DateTime, Sequence, Boolean
from datetime import datetime, date,time
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


# Create the table
Base.metadata.create_all(bind=engine)


# Pydantic schema for validation
class ReservationBase(BaseModel):
    name: str
    number: str
    people_count: int
    date: date 
    time: time
    room: str
    movie_id: int | None
    movie_name: str | None
    movie_desc: str | None
    movie_image: str | None
    snack_package: bool | None
    status: str

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    people_count: Optional[int] = None
    date: Optional[date] = None
    time: Optional[time] = None
    room: Optional[str] = None
    movie_id: Optional[int] = None
    movie_name: Optional[str] = None
    movie_desc: Optional[str] = None
    movie_image: Optional[str] = None
    snack_package: Optional[bool] = None
    status: Optional[str] = None

class ReservationResponse(ReservationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

