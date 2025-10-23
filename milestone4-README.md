# Flight Booking Simulator - Milestone 4

## Overview
This project simulates a flight booking system with dynamic pricing, multi-step booking flow, PNR generation, and downloadable booking receipts. It uses a MySQL database to store flights, passengers, and bookings, and provides a frontend for users to search flights and make bookings.

---

## Features
- **Flight Search:** Search by origin and destination with real-time dynamic prices.
- **Dynamic Pricing:** Prices vary based on seats available, time to departure, and simulated demand.
- **Multi-step Booking:** Select a flight, provide passenger ID, optionally choose a seat.
- **PNR Generation:** Unique booking reference for every confirmed booking.
- **Booking Receipts:** Downloadable JSON receipts for each booking.
- **Database Integration:** Fully integrated with existing MySQL database schema.

---

## Folder Structure
flight-booking-simulator/
├── backend/
│ └── milestone4_backend.py # FastAPI backend
├── frontend/
│ └── milestone4_frontend.html # Single-page HTML with embedded CSS/JS
├── README.md
└── flight_booking_db.sql # MySQL database with tables and sample data

yaml
Copy code

---

## Backend - `milestone4_backend.py`
- **Framework:** FastAPI
- **Database:** MySQL (SQLAlchemy ORM)
- **Endpoints:**
  - `GET /flights` – Search flights with dynamic pricing
  - `POST /book` – Book a flight and generate PNR
- **Run the backend:**
```bash
# Install dependencies
pip install fastapi uvicorn sqlalchemy pymysql

# Run server
uvicorn milestone4_backend:app --reload
Database Setup:

Run flight_booking_db.sql in MySQL to create tables and insert sample data.

Update DATABASE_URL in milestone4_backend.py with your MySQL credentials.

Frontend - milestone4_frontend.html
Single-page HTML with embedded CSS and JS.

Features:

Flight search with origin/destination

Display dynamic pricing and available seats

Book flights using passenger ID

Download booking receipt as JSON

Run the frontend:
Open milestone4_frontend.html in any web browser. Ensure the backend is running at http://127.0.0.1:8000.

How to Use
Start the backend server (uvicorn milestone4_backend:app --reload).

Open milestone4_frontend.html in a browser.

Search for flights, select a flight, and provide passenger ID.

Confirm booking to receive PNR and download the receipt.

Notes
Passenger IDs must exist in the Passengers table.

Dynamic prices are calculated in real-time based on remaining seats, time, and demand.

The frontend interacts directly with the backend via REST API.
