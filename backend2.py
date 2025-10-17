"""
backend.py - Flight Booking Simulator with Dynamic Pricing

Run this file with:
    uvicorn backend:app --reload

Steps before running:
1. Run your flight_booking_db.sql and the ALTER TABLE commands in MySQL.
2. Update DATABASE_URL below with your MySQL username, password, and database.
3. Install requirements: fastapi, uvicorn, sqlalchemy, pymysql
"""

import os
import random
import asyncio
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, constr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# -------------------------------
# Database Connection
# -------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:Cherry%402005@localhost:3306/flights"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(title="Flight Booking Simulator with Dynamic Pricing")

# -------------------------------
# Pydantic Models
# -------------------------------
class FlightPriceResponse(BaseModel):
    flight_id: int
    flight_number: Optional[str]
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    base_fare: float
    dynamic_price: float
    seats_available: int
    total_seats: int


class FlightSearchRequest(BaseModel):
    origin: constr(min_length=3, max_length=4)
    destination: constr(min_length=3, max_length=4)
    date: date
    sort: Optional[str] = None  # price or duration

# -------------------------------
# DB Dependency
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# Dynamic Pricing Logic
# -------------------------------
def calculate_dynamic_price(base_fare: float,
                            seats_available: int,
                            total_seats: int,
                            departure_time: datetime,
                            simulated_demand: Optional[float] = None) -> float:
    """Dynamic price based on seats, time, demand, and base fare tiers."""
    seat_ratio = seats_available / max(1, total_seats)
    if seat_ratio < 0.1:
        seat_factor = 0.8
    elif seat_ratio < 0.25:
        seat_factor = 0.5
    elif seat_ratio < 0.5:
        seat_factor = 0.2
    else:
        seat_factor = -0.05

    now = datetime.now(timezone.utc)
    hours_left = max(0, (departure_time - now).total_seconds() / 3600)
    if hours_left <= 24:
        time_factor = 0.6
    elif hours_left <= 168:
        time_factor = 0.25
    else:
        time_factor = -0.05

    if simulated_demand is None:
        demand_factor = random.uniform(-0.1, 0.4)
    else:
        demand_factor = max(-0.5, min(1.0, simulated_demand)) * 0.4

    if base_fare < 2000:
        tier_bonus = 0.0
    elif base_fare < 5000:
        tier_bonus = 0.05
    else:
        tier_bonus = 0.1

    dynamic_price = base_fare * (1 + seat_factor + time_factor + demand_factor + tier_bonus)
    dynamic_price = max(50.0, dynamic_price)
    return round(dynamic_price, 2)

# -------------------------------
# Endpoints
# -------------------------------

# Retrieve all flights
@app.get("/flights", response_model=List[FlightPriceResponse])
def get_all_flights(db=Depends(get_db)):
    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.code AS origin, a2.code AS destination,
               f.departure_date_time AS departure_time,
               f.arrival_date_time AS arrival_time,
               f.base_fare, f.seats_available, f.total_seats
        FROM Flights f
        JOIN Airports a1 ON f.origin_airport = a1.airport_id
        JOIN Airports a2 ON f.destination_airport = a2.airport_id
    """)
    flights = db.execute(query).mappings().all()

    results = []
    for f in flights:
        price = calculate_dynamic_price(
            f["base_fare"], f["seats_available"], f["total_seats"], f["departure_time"]
        )
        results.append(FlightPriceResponse(
            flight_id=f["flight_id"],
            flight_number=f.get("flight_number", ""),
            origin=f["origin"],
            destination=f["destination"],
            departure_time=f["departure_time"],
            arrival_time=f["arrival_time"],
            base_fare=f["base_fare"],
            dynamic_price=price,
            seats_available=f["seats_available"],
            total_seats=f["total_seats"]
        ))

        try:
            db.execute(text("""
                INSERT INTO FareHistory (flight_id, base_fare, dynamic_price, seats_available, total_seats, reason)
                VALUES (:fid, :bf, :dp, :sa, :ts, 'flights_api')
            """), {"fid": f["flight_id"], "bf": f["base_fare"], "dp": price,
                   "sa": f["seats_available"], "ts": f["total_seats"]})
            db.commit()
        except Exception:
            db.rollback()

    return results

# Get single flight with dynamic pricing
@app.get("/dynamic_price/{flight_id}", response_model=FlightPriceResponse)
def get_dynamic_price_for_flight(flight_id: int, db=Depends(get_db)):
    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.code AS origin, a2.code AS destination,
               f.departure_date_time AS departure_time,
               f.arrival_date_time AS arrival_time,
               f.base_fare, f.seats_available, f.total_seats
        FROM Flights f
        JOIN Airports a1 ON f.origin_airport = a1.airport_id
        JOIN Airports a2 ON f.destination_airport = a2.airport_id
        WHERE f.flight_id = :fid
    """)
    flight = db.execute(query, {"fid": flight_id}).mappings().first()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    price = calculate_dynamic_price(
        flight["base_fare"], flight["seats_available"],
        flight["total_seats"], flight["departure_time"]
    )

    try:
        db.execute(text("""
            INSERT INTO FareHistory (flight_id, base_fare, dynamic_price, seats_available, total_seats, reason)
            VALUES (:fid, :bf, :dp, :sa, :ts, 'dynamic_price_api')
        """), {"fid": flight_id, "bf": flight["base_fare"], "dp": price,
               "sa": flight["seats_available"], "ts": flight["total_seats"]})
        db.commit()
    except Exception:
        db.rollback()

    return FlightPriceResponse(
        flight_id=flight["flight_id"],
        flight_number=flight.get("flight_number", ""),
        origin=flight["origin"],
        destination=flight["destination"],
        departure_time=flight["departure_time"],
        arrival_time=flight["arrival_time"],
        base_fare=flight["base_fare"],
        dynamic_price=price,
        seats_available=flight["seats_available"],
        total_seats=flight["total_seats"]
    )

# Search by origin, destination, and date
@app.get("/search", response_model=List[FlightPriceResponse])
def search_flights(origin: str, destination: str, date: str,
                   sort: Optional[str] = None, db=Depends(get_db)):
    try:
        date_obj = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")

    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.code AS origin, a2.code AS destination,
               f.departure_date_time AS departure_time,
               f.arrival_date_time AS arrival_time,
               f.base_fare, f.seats_available, f.total_seats
        FROM Flights f
        JOIN Airports a1 ON f.origin_airport = a1.airport_id
        JOIN Airports a2 ON f.destination_airport = a2.airport_id
        WHERE a1.code = :origin AND a2.code = :destination AND DATE(f.departure_date_time) = :date
    """)
    flights = db.execute(query, {"origin": origin.upper(), "destination": destination.upper(),
                                 "date": date_obj}).mappings().all()

    results = []
    for f in flights:
        price = calculate_dynamic_price(
            f["base_fare"], f["seats_available"], f["total_seats"], f["departure_time"]
        )
        results.append(FlightPriceResponse(
            flight_id=f["flight_id"],
            flight_number=f.get("flight_number", ""),
            origin=f["origin"],
            destination=f["destination"],
            departure_time=f["departure_time"],
            arrival_time=f["arrival_time"],
            base_fare=f["base_fare"],
            dynamic_price=price,
            seats_available=f["seats_available"],
            total_seats=f["total_seats"]
        ))

    if sort == "price":
        results.sort(key=lambda x: x.dynamic_price)
    elif sort == "duration":
        results.sort(key=lambda x: (x.arrival_time - x.departure_time).total_seconds())
    elif sort is not None:
        raise HTTPException(status_code=400, detail="Sort must be 'price' or 'duration'")

    return results

# Fare history
@app.get("/fare_history/{flight_id}")
def get_fare_history(flight_id: int, db=Depends(get_db)):
    rows = db.execute(text("""
        SELECT recorded_at, base_fare, dynamic_price, seats_available, reason
        FROM FareHistory
        WHERE flight_id = :fid
        ORDER BY recorded_at DESC LIMIT 50
    """), {"fid": flight_id}).mappings().all()
    return list(rows)

# Mock external airline API
@app.get("/external/airlines/{code}")
def mock_airline_api(code: str):
    now = datetime.now(timezone.utc)
    return {
        "airline_code": code.upper(),
        "schedules": [
            {"flight_number": f"{code.upper()}101", "origin": "DEL", "destination": "BOM",
             "departure": (now + timedelta(days=1, hours=2)).isoformat(),
             "arrival": (now + timedelta(days=1, hours=4)).isoformat()}
        ]
    }

# -------------------------------
# Background Simulation
# -------------------------------
async def simulate_market():
    while True:
        db = SessionLocal()
        try:
            flights = db.execute(text("SELECT flight_id, base_fare, seats_available, total_seats FROM Flights")).mappings().all()
            for f in flights:
                change = random.choice([-3, -2, -1, 0, 1, 2])
                new_seats = max(0, min(f["total_seats"], f["seats_available"] + change))
                db.execute(text("UPDATE Flights SET seats_available = :s WHERE flight_id = :fid"),
                           {"s": new_seats, "fid": f["flight_id"]})

                demand_level = random.uniform(-0.5, 1.0)
                dynamic_price = calculate_dynamic_price(
                    f["base_fare"], new_seats, f["total_seats"],
                    datetime.now(timezone.utc) + timedelta(days=1),
                    simulated_demand=demand_level
                )
                db.execute(text("""
                    INSERT INTO FareHistory (flight_id, base_fare, dynamic_price, seats_available, total_seats, reason)
                    VALUES (:fid, :bf, :dp, :sa, :ts, 'simulator')
                """), {"fid": f["flight_id"], "bf": f["base_fare"], "dp": dynamic_price,
                       "sa": new_seats, "ts": f["total_seats"]})
            db.commit()
        except Exception as e:
            print("Simulation error:", e)
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(60)

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(simulate_market())

# -------------------------------
# Health Check
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}