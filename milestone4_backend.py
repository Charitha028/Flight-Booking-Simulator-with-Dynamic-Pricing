"""
milestone4_backend.py - Flight Booking Simulator with Dynamic Pricing & PNR

Run:
    uvicorn milestone4_backend:app --reload

Requirements:
    - fastapi
    - uvicorn
    - sqlalchemy
    - pymysql
"""

import os
import random
import string
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:Cherry@2005@localhost:3306/flights"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="Flight Booking Simulator - Milestone 4")

# Pydantic Models
class FlightResponse(BaseModel):
    flight_id: int
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    base_fare: float
    dynamic_price: float
    seats_available: int
    total_seats: int

class BookingRequest(BaseModel):
    flight_id: int
    passenger_id: int
    seat_no: Optional[str]

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dynamic pricing
def calculate_dynamic_price(base_fare: float, seats_available: int, total_seats: int, departure_time: datetime) -> float:
    seat_ratio = seats_available / max(1, total_seats)
    seat_factor = 0.3 if seat_ratio < 0.2 else (0.1 if seat_ratio < 0.5 else -0.05)
    hours_left = max(0, (departure_time - datetime.now(timezone.utc)).total_seconds() / 3600)
    time_factor = 0.5 if hours_left < 24 else (0.2 if hours_left < 72 else 0)
    demand_factor = random.uniform(-0.1, 0.3)
    dynamic_price = base_fare * (1 + seat_factor + time_factor + demand_factor)
    return round(max(dynamic_price, 50), 2)

# Endpoints
@app.get("/flights", response_model=List[FlightResponse])
def get_flights(origin: Optional[str] = None, destination: Optional[str] = None, db=Depends(get_db)):
    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.airport_name AS origin, a2.airport_name AS destination,
               f.departure_date_time AS departure_time,
               f.arrival_date_time AS arrival_time,
               f.base_fare, f.seats_available, f.total_seats
        FROM Flights f
        JOIN Airports a1 ON f.origin_airport = a1.airport_id
        JOIN Airports a2 ON f.destination_airport = a2.airport_id
        WHERE (:origin IS NULL OR a1.airport_name LIKE :origin)
          AND (:destination IS NULL OR a2.airport_name LIKE :destination)
    """)
    flights = db.execute(query, {"origin": f"%{origin}%" if origin else None,
                                 "destination": f"%{destination}%" if destination else None}).mappings().all()
    result = []
    for f in flights:
        dynamic_price = calculate_dynamic_price(f["base_fare"], f["seats_available"], f["total_seats"], f["departure_time"])
        result.append(FlightResponse(
            flight_id=f["flight_id"],
            flight_number=f["flight_number"],
            origin=f["origin"],
            destination=f["destination"],
            departure_time=f["departure_time"],
            arrival_time=f["arrival_time"],
            base_fare=float(f["base_fare"]),
            dynamic_price=dynamic_price,
            seats_available=f["seats_available"],
            total_seats=f["total_seats"]
        ))
    return result

@app.post("/book")
def book_flight(request: BookingRequest, db=Depends(get_db)):
    flight = db.execute(text("SELECT * FROM Flights WHERE flight_id=:fid"), {"fid": request.flight_id}).mappings().first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if flight["seats_available"] <= 0:
        raise HTTPException(status_code=400, detail="No seats available")

    # Generate PNR
    pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    seat_no = request.seat_no or f"{random.randint(1, flight['total_seats'])}A"

    db.execute(text("""
        INSERT INTO Bookings (flight_id, passenger_id, seat_no, status)
        VALUES (:fid, :pid, :seat, 'CONFIRMED')
    """), {"fid": request.flight_id, "pid": request.passenger_id, "seat": seat_no})
    db.execute(text("UPDATE Flights SET seats_available = seats_available - 1 WHERE flight_id=:fid"),
               {"fid": request.flight_id})
    db.commit()

    return {
        "pnr": pnr,
        "flight_id": flight["flight_id"],
        "passenger_id": request.passenger_id,
        "seat_no": seat_no,
        "status": "CONFIRMED"
    }