"""
backend_milestone3.py - Flight Booking Simulator w/ Dynamic Pricing + Booking Workflow

Run:
    uvicorn backend_milestone3:app --reload

Requires:
    - fastapi
    - uvicorn
    - sqlalchemy
    - pymysql
    - pydantic
"""

import os
import random
import string
import asyncio
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel, constr, EmailStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# -------------------------------
# Database Connection (update if needed)
# -------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:Cherry@2005@localhost:3306/flights"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(title="Flight Booking Simulator with Dynamic Pricing + Booking Workflow")

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

class StartBookingRequest(BaseModel):
    flight_id: int
    passenger_first_name: str
    passenger_last_name: str
    passenger_email: EmailStr
    # optional client-requested seat hint - not guaranteed
    requested_seat: Optional[str] = None

class PaymentRequest(BaseModel):
    booking_id: int
    simulate_success: Optional[bool] = None  # if None, randomize

class CancelRequest(BaseModel):
    pnr: str

class BookingResponse(BaseModel):
    booking_id: int
    flight_id: int
    passenger_id: int
    seat_no: Optional[str]
    status: str
    pnr: Optional[str]
    price: Optional[float]
    payment_status: Optional[str]
    booking_date: Optional[datetime]

# -------------------------------
# Utility / DB helpers
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_pnr(length: int = 6) -> str:
    # 6-char alphanumeric uppercase PNR, e.g. "A7B9C2"
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# -------------------------------
# Migrations / Schema updates on startup
# - Add PNR, price, payment_status, expand status enum to include PENDING
# -------------------------------
def ensure_booking_schema():
    """Make non-destructive ALTERs so Bookings table can support milestone features."""
    with engine.begin() as conn:
        # 1) Add PNR column if missing
        try:
            conn.execute(text("ALTER TABLE Bookings ADD COLUMN IF NOT EXISTS pnr VARCHAR(16) NULL"))
        except Exception:
            # MySQL < 8 doesn't support IF NOT EXISTS in ADD COLUMN; do existence check
            try:
                res = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='Bookings' AND COLUMN_NAME='pnr'")).fetchone()
                if not res:
                    conn.execute(text("ALTER TABLE Bookings ADD COLUMN pnr VARCHAR(16) NULL"))
            except Exception:
                pass

        # 2) Add price column
        try:
            conn.execute(text("ALTER TABLE Bookings ADD COLUMN IF NOT EXISTS price DECIMAL(10,2) NULL"))
        except Exception:
            res = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='Bookings' AND COLUMN_NAME='price'")).fetchone()
            if not res:
                conn.execute(text("ALTER TABLE Bookings ADD COLUMN price DECIMAL(10,2) NULL"))

        # 3) Add payment_status column
        try:
            conn.execute(text("ALTER TABLE Bookings ADD COLUMN IF NOT EXISTS payment_status ENUM('PENDING','PAID','FAILED') DEFAULT 'PENDING'"))
        except Exception:
            res = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='Bookings' AND COLUMN_NAME='payment_status'")).fetchone()
            if not res:
                # Add as varchar then modify - keep safe
                conn.execute(text("ALTER TABLE Bookings ADD COLUMN payment_status VARCHAR(10) DEFAULT 'PENDING'"))
                try:
                    conn.execute(text("ALTER TABLE Bookings MODIFY COLUMN payment_status ENUM('PENDING','PAID','FAILED') DEFAULT 'PENDING'"))
                except Exception:
                    pass

        # 4) Expand status enum to include 'PENDING' (MySQL requires MODIFY)
        try:
            # check existing values
            res = conn.execute(text("SHOW COLUMNS FROM Bookings LIKE 'status'")).fetchone()
            if res:
                col_def = res[1]  # type string
                if 'PENDING' not in col_def:
                    # Attempt to modify to include PENDING
                    conn.execute(text("ALTER TABLE Bookings MODIFY COLUMN status ENUM('PENDING','CONFIRMED','CANCELLED') DEFAULT 'PENDING'"))
        except Exception:
            # ignore if can't modify
            pass

# Ensure schema on import/run
try:
    ensure_booking_schema()
except Exception as e:
    # If migration fails, we continue but booking APIs will likely fail later with DB errors.
    print("Warning: schema migration attempt failed:", e)

# -------------------------------
# Dynamic Pricing Logic (copied + slightly refactored)
# -------------------------------
def calculate_dynamic_price(base_fare: float,
                            seats_available: int,
                            total_seats: int,
                            departure_time: datetime,
                            simulated_demand: Optional[float] = None) -> float:
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
# Flight endpoints (list / single / search / fare_history) - unchanged behavior
# -------------------------------
@app.get("/flights", response_model=List[FlightPriceResponse])
def get_all_flights(db=Depends(get_db)):
    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.airport_name AS origin, a2.airport_name AS destination,
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
            float(f["base_fare"]), int(f["seats_available"]), int(f["total_seats"]), f["departure_time"]
        )
        results.append(FlightPriceResponse(
            flight_id=f["flight_id"],
            flight_number=f.get("flight_number", ""),
            origin=f["origin"],
            destination=f["destination"],
            departure_time=f["departure_time"],
            arrival_time=f["arrival_time"],
            base_fare=float(f["base_fare"]),
            dynamic_price=price,
            seats_available=int(f["seats_available"]),
            total_seats=int(f["total_seats"])
        ))

        # best-effort insert into FareHistory without disrupting response
        try:
            db.execute(text("""
                INSERT INTO FareHistory (flight_id, base_fare, dynamic_price, seats_available, total_seats, reason)
                VALUES (:fid, :bf, :dp, :sa, :ts, 'flights_api')
            """), {"fid": f["flight_id"], "bf": float(f["base_fare"]), "dp": price,
                   "sa": int(f["seats_available"]), "ts": int(f["total_seats"])})
            db.commit()
        except Exception:
            db.rollback()

    return results

@app.get("/dynamic_price/{flight_id}", response_model=FlightPriceResponse)
def get_dynamic_price_for_flight(flight_id: int, db=Depends(get_db)):
    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.airport_name AS origin, a2.airport_name AS destination,
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
        float(flight["base_fare"]), int(flight["seats_available"]),
        int(flight["total_seats"]), flight["departure_time"]
    )

    try:
        db.execute(text("""
            INSERT INTO FareHistory (flight_id, base_fare, dynamic_price, seats_available, total_seats, reason)
            VALUES (:fid, :bf, :dp, :sa, :ts, 'dynamic_price_api')
        """), {"fid": flight_id, "bf": float(flight["base_fare"]), "dp": price,
               "sa": int(flight["seats_available"]), "ts": int(flight["total_seats"])})
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
        base_fare=float(flight["base_fare"]),
        dynamic_price=price,
        seats_available=int(flight["seats_available"]),
        total_seats=int(flight["total_seats"])
    )

@app.get("/search", response_model=List[FlightPriceResponse])
def search_flights(origin: str, destination: str, date: str,
                   sort: Optional[str] = None, db=Depends(get_db)):
    try:
        date_obj = datetime.fromisoformat(date).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")

    query = text("""
        SELECT f.flight_id, f.flight_number,
               a1.airport_name AS origin, a2.airport_name AS destination,
               f.departure_date_time AS departure_time,
               f.arrival_date_time AS arrival_time,
               f.base_fare, f.seats_available, f.total_seats
        FROM Flights f
        JOIN Airports a1 ON f.origin_airport = a1.airport_id
        JOIN Airports a2 ON f.destination_airport = a2.airport_id
        WHERE a1.city = :origin AND a2.city = :destination AND DATE(f.departure_date_time) = :date
    """)
    flights = db.execute(query, {"origin": origin.title(), "destination": destination.title(),
                                 "date": date_obj}).mappings().all()

    results = []
    for f in flights:
        price = calculate_dynamic_price(
            float(f["base_fare"]), int(f["seats_available"]), int(f["total_seats"]), f["departure_time"]
        )
        results.append(FlightPriceResponse(
            flight_id=f["flight_id"],
            flight_number=f.get("flight_number", ""),
            origin=f["origin"],
            destination=f["destination"],
            departure_time=f["departure_time"],
            arrival_time=f["arrival_time"],
            base_fare=float(f["base_fare"]),
            dynamic_price=price,
            seats_available=int(f["seats_available"]),
            total_seats=int(f["total_seats"])
        ))

    if sort == "price":
        results.sort(key=lambda x: x.dynamic_price)
    elif sort == "duration":
        results.sort(key=lambda x: (x.arrival_time - x.departure_time).total_seconds())
    elif sort is not None:
        raise HTTPException(status_code=400, detail="Sort must be 'price' or 'duration'")

    return results

@app.get("/fare_history/{flight_id}")
def get_fare_history(flight_id: int, db=Depends(get_db)):
    rows = db.execute(text("""
        SELECT recorded_at, base_fare, dynamic_price, seats_available, reason
        FROM FareHistory
        WHERE flight_id = :fid
        ORDER BY recorded_at DESC LIMIT 50
    """), {"fid": flight_id}).mappings().all()
    return list(rows)

# -------------------------------
# Booking workflow endpoints (multi-step)
# - /bookings/start  -> reserves seat (PENDING) using transaction and SELECT ... FOR UPDATE
# - /bookings/pay    -> attempt payment; on success generate PNR and mark CONFIRMED; on fail release seat
# - /bookings/cancel -> cancel by PNR (or booking id)
# - /bookings/{pnr}  -> get booking details
# - /bookings/history/{email} -> get bookings for passenger
# -------------------------------

@app.post("/bookings/start", response_model=BookingResponse)
def start_booking(req: StartBookingRequest, db=Depends(get_db)):
    """Reserve a seat (PENDING booking). This is concurrency-safe: we lock the Flights row."""
    # Validate flight exists
    flight_row = db.execute(text("SELECT flight_id, seats_available, total_seats, base_fare FROM Flights WHERE flight_id = :fid"),
                            {"fid": req.flight_id}).mappings().first()
    if not flight_row:
        raise HTTPException(status_code=404, detail="Flight not found")

    # Use an explicit transaction with FOR UPDATE to prevent race conditions
    try:
        with engine.begin() as conn:
            # lock the flight row
            locked = conn.execute(text("SELECT seats_available, total_seats, base_fare FROM Flights WHERE flight_id = :fid FOR UPDATE"),
                                  {"fid": req.flight_id}).mappings().first()
            if not locked:
                raise HTTPException(status_code=404, detail="Flight not found (locked)")
            seats_available = int(locked["seats_available"])
            total_seats = int(locked["total_seats"])
            base_fare = float(locked["base_fare"])

            if seats_available <= 0:
                raise HTTPException(status_code=409, detail="No seats available")

            # Simple seat assign strategy: use next seat number index (this is deterministic under the lock)
            used_count = total_seats - seats_available
            seat_row_num = used_count + 1
            # seat letter cycle A-F
            seat_letter = chr(65 + ((seat_row_num - 1) % 6))
            seat_no = f"{seat_row_num}{seat_letter}"

            # create or fetch passenger
            passenger = conn.execute(text("SELECT passenger_id FROM Passengers WHERE email = :email"),
                                     {"email": req.passenger_email}).fetchone()
            if passenger:
                passenger_id = passenger[0]
            else:
                res = conn.execute(text("INSERT INTO Passengers (first_name, last_name, email) VALUES (:fn, :ln, :em)"),
                                   {"fn": req.passenger_first_name, "ln": req.passenger_last_name, "em": req.passenger_email})
                passenger_id = res.lastrowid

            # compute dynamic price at time of hold
            departure_q = conn.execute(text("SELECT departure_date_time FROM Flights WHERE flight_id = :fid"), {"fid": req.flight_id}).fetchone()
            departure_dt = departure_q[0] if departure_q else (datetime.now(timezone.utc) + timedelta(days=1))
            dynamic_price = calculate_dynamic_price(base_fare, seats_available, total_seats, departure_dt)

            # insert booking as PENDING and decrement seats_available
            ins = conn.execute(text("""
                INSERT INTO Bookings (flight_id, passenger_id, seat_no, status, price, payment_status, booking_date)
                VALUES (:fid, :pid, :seat_no, 'PENDING', :price, 'PENDING', NOW())
            """), {"fid": req.flight_id, "pid": passenger_id, "seat_no": seat_no, "price": dynamic_price})

            booking_id = ins.lastrowid

            conn.execute(text("UPDATE Flights SET seats_available = seats_available - 1 WHERE flight_id = :fid"), {"fid": req.flight_id})

            # commit happens on context exit
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not start booking: {e}")

    return BookingResponse(
        booking_id=booking_id,
        flight_id=req.flight_id,
        passenger_id=passenger_id,
        seat_no=seat_no,
        status="PENDING",
        pnr=None,
        price=float(dynamic_price),
        payment_status="PENDING",
        booking_date=datetime.now(timezone.utc)
    )

@app.post("/bookings/pay", response_model=BookingResponse)
def confirm_payment(req: PaymentRequest, db=Depends(get_db)):
    """Attempt payment for a PENDING booking.
    On success -> generate PNR, set status CONFIRMED and payment_status PAID.
    On failure -> set status CANCELLED, payment_status FAILED, release seat (increment seats_available).
    All done in a transaction to be concurrency-safe.
    """
    # fetch booking
    booking = db.execute(text("SELECT booking_id, flight_id, passenger_id, seat_no, status, price FROM Bookings WHERE booking_id = :bid"),
                         {"bid": req.booking_id}).mappings().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking["status"] != "PENDING":
        raise HTTPException(status_code=400, detail=f"Booking not in PENDING state (current: {booking['status']})")

    # simulate payment
    if req.simulate_success is None:
        success = random.choice([True, False, True])  # slightly skew to success
    else:
        success = bool(req.simulate_success)

    try:
        with engine.begin() as conn:
            # lock flight row to safely update seats if release needed
            conn.execute(text("SELECT flight_id FROM Flights WHERE flight_id = :fid FOR UPDATE"), {"fid": booking["flight_id"]})

            if success:
                pnr = generate_pnr()
                conn.execute(text("""
                    UPDATE Bookings SET status = 'CONFIRMED', pnr = :pnr, payment_status = 'PAID', booking_date = NOW()
                    WHERE booking_id = :bid
                """), {"pnr": pnr, "bid": req.booking_id})

                # Optionally, record to a BookingHistory or Payment table here (omitted to keep compact)
                booking_out = conn.execute(text("SELECT booking_id, flight_id, passenger_id, seat_no, status, pnr, price, payment_status, booking_date FROM Bookings WHERE booking_id = :bid"),
                                           {"bid": req.booking_id}).mappings().first()
                result = BookingResponse(
                    booking_id=booking_out["booking_id"],
                    flight_id=booking_out["flight_id"],
                    passenger_id=booking_out["passenger_id"],
                    seat_no=booking_out["seat_no"],
                    status=booking_out["status"],
                    pnr=booking_out["pnr"],
                    price=float(booking_out["price"]) if booking_out["price"] is not None else None,
                    payment_status=booking_out["payment_status"],
                    booking_date=booking_out["booking_date"]
                )
            else:
                # failed payment -> mark booking CANCELLED and release seat
                conn.execute(text("""
                    UPDATE Bookings SET status = 'CANCELLED', payment_status = 'FAILED', booking_date = NOW()
                    WHERE booking_id = :bid
                """), {"bid": req.booking_id})

                # release seat
                conn.execute(text("UPDATE Flights SET seats_available = seats_available + 1 WHERE flight_id = :fid"),
                             {"fid": booking["flight_id"]})

                booking_out = conn.execute(text("SELECT booking_id, flight_id, passenger_id, seat_no, status, pnr, price, payment_status, booking_date FROM Bookings WHERE booking_id = :bid"),
                                           {"bid": req.booking_id}).mappings().first()
                result = BookingResponse(
                    booking_id=booking_out["booking_id"],
                    flight_id=booking_out["flight_id"],
                    passenger_id=booking_out["passenger_id"],
                    seat_no=booking_out["seat_no"],
                    status=booking_out["status"],
                    pnr=booking_out["pnr"],
                    price=float(booking_out["price"]) if booking_out["price"] is not None else None,
                    payment_status=booking_out["payment_status"],
                    booking_date=booking_out["booking_date"]
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment update error: {e}")

    return result

@app.post("/bookings/cancel", response_model=BookingResponse)
def cancel_booking(req: CancelRequest, db=Depends(get_db)):
    """Cancel an existing confirmed or pending booking by PNR (or partial match). Releases seat."""
    booking = db.execute(text("SELECT booking_id, flight_id, passenger_id, seat_no, status FROM Bookings WHERE pnr = :pnr OR booking_id = :maybe_id"),
                         {"pnr": req.pnr, "maybe_id": req.pnr}).mappings().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking["status"] == "CANCELLED":
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    try:
        with engine.begin() as conn:
            # mark cancelled and release seat under lock
            conn.execute(text("SELECT flight_id FROM Flights WHERE flight_id = :fid FOR UPDATE"), {"fid": booking["flight_id"]})
            conn.execute(text("UPDATE Bookings SET status = 'CANCELLED' WHERE booking_id = :bid"), {"bid": booking["booking_id"]})
            conn.execute(text("UPDATE Flights SET seats_available = seats_available + 1 WHERE flight_id = :fid"), {"fid": booking["flight_id"]})

            out = conn.execute(text("SELECT booking_id, flight_id, passenger_id, seat_no, status, pnr, price, payment_status, booking_date FROM Bookings WHERE booking_id = :bid"),
                               {"bid": booking["booking_id"]}).mappings().first()
            resp = BookingResponse(
                booking_id=out["booking_id"],
                flight_id=out["flight_id"],
                passenger_id=out["passenger_id"],
                seat_no=out["seat_no"],
                status=out["status"],
                pnr=out["pnr"],
                price=float(out["price"]) if out["price"] is not None else None,
                payment_status=out["payment_status"],
                booking_date=out["booking_date"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel error: {e}")

    return resp

@app.get("/bookings/{pnr}", response_model=BookingResponse)
def get_booking_by_pnr(pnr: str, db=Depends(get_db)):
    booking = db.execute(text("SELECT booking_id, flight_id, passenger_id, seat_no, status, pnr, price, payment_status, booking_date FROM Bookings WHERE pnr = :pnr"),
                         {"pnr": pnr}).mappings().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingResponse(
        booking_id=booking["booking_id"],
        flight_id=booking["flight_id"],
        passenger_id=booking["passenger_id"],
        seat_no=booking["seat_no"],
        status=booking["status"],
        pnr=booking["pnr"],
        price=float(booking["price"]) if booking["price"] is not None else None,
        payment_status=booking["payment_status"],
        booking_date=booking["booking_date"]
    )

@app.get("/bookings/history/{email}", response_model=List[BookingResponse])
def booking_history(email: str, db=Depends(get_db)):
    rows = db.execute(text("""
        SELECT b.booking_id, b.flight_id, b.passenger_id, b.seat_no, b.status, b.pnr, b.price, b.payment_status, b.booking_date
        FROM Bookings b
        JOIN Passengers p ON b.passenger_id = p.passenger_id
        WHERE p.email = :email
        ORDER BY b.booking_date DESC
    """), {"email": email}).mappings().all()

    resp = []
    for r in rows:
        resp.append(BookingResponse(
            booking_id=r["booking_id"],
            flight_id=r["flight_id"],
            passenger_id=r["passenger_id"],
            seat_no=r["seat_no"],
            status=r["status"],
            pnr=r["pnr"],
            price=float(r["price"]) if r["price"] is not None else None,
            payment_status=r["payment_status"],
            booking_date=r["booking_date"]
        ))
    return resp

# -------------------------------
# Background Simulation (keeps FareHistory & seat churn)
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
                    float(f["base_fare"]), new_seats, f["total_seats"],
                    datetime.now(timezone.utc) + timedelta(days=1),
                    simulated_demand=demand_level
                )
                db.execute(text("""
                    INSERT INTO FareHistory (flight_id, base_fare, dynamic_price, seats_available, total_seats, reason)
                    VALUES (:fid, :bf, :dp, :sa, :ts, 'simulator')
                """), {"fid": f["flight_id"], "bf": float(f["base_fare"]), "dp": dynamic_price,
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
    # start market simulator
    asyncio.create_task(simulate_market())

# -------------------------------
# Health Check
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}