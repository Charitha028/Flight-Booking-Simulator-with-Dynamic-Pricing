Flight Booking Simulator with Dynamic Pricing & Booking Workflow
Overview

This project implements a Flight Booking Simulator built using FastAPI, featuring dynamic pricing and a multi-step booking workflow.
It simulates real-world airline operations, including price fluctuations based on demand, seat availability, and time until departure, as well as a concurrency-safe booking and payment flow.

Features
1. Flight Management

Retrieve all available flights with dynamic prices.

Search flights by origin, destination, and date.

Sort results by price or duration.

View fare history for individual flights.

2. Dynamic Pricing Engine

Dynamic pricing is calculated using:

Remaining seat percentage

Time until departure

Simulated market demand

Base fare and pricing tier

Prices are recorded in a FareHistory table for tracking and analysis.

3. Booking Workflow

A three-step process ensures safe and realistic booking:

Start Booking (/bookings/start)
Locks the flight record to prevent overselling and reserves a seat as PENDING.

Confirm Payment (/bookings/pay)
Simulates payment. On success, marks the booking as CONFIRMED and generates a PNR.
On failure, marks it as CANCELLED and releases the seat.

Cancel Booking (/bookings/cancel)
Allows passengers to cancel their confirmed or pending bookings and release seats.

4. Additional Endpoints

Retrieve booking details by PNR (/bookings/{pnr}).

View booking history by passenger email (/bookings/history/{email}).

System health check (/health).

5. Background Simulation

A background task periodically updates flight seat availability and records new fare entries in FareHistory, simulating real-time market behavior.

Tech Stack

Backend Framework: FastAPI

Database: MySQL (via SQLAlchemy ORM and PyMySQL driver)

Server: Uvicorn

Language: Python 3.9+

Setup Instructions
1. Clone the Repository
git clone https://github.com/<your-username>/Flight-Booking-Simulator-with-Dynamic-Pricing.git
cd Flight-Booking-Simulator-with-Dynamic-Pricing

2. Install Dependencies
pip install fastapi uvicorn sqlalchemy pymysql pydantic

3. Configure Database

Run the SQL scripts to create and initialize your database:

mysql -u root -p < flight_booking_db.sql


If necessary, run the additional ALTER TABLE commands provided in your project setup guide.

Update your database connection string in the Python file:

DATABASE_URL = "mysql+pymysql://<username>:<password>@localhost:3306/flights"

4. Run the Application
uvicorn backend_milestone3:app --reload

5. Access the API

Open the interactive documentation in your browser:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

API Endpoints Summary
Endpoint	Method	Description
/flights	GET	Get all flights with dynamic pricing
/dynamic_price/{flight_id}	GET	Get live dynamic price for a flight
/search	GET	Search flights by origin, destination, and date
/fare_history/{flight_id}	GET	Get recent fare history for a flight
/bookings/start	POST	Start a new booking (PENDING)
/bookings/pay	POST	Confirm booking payment
/bookings/cancel	POST	Cancel a booking by PNR
/bookings/{pnr}	GET	Retrieve booking details by PNR
/bookings/history/{email}	GET	Retrieve booking history by passenger
/health	GET	Health check endpoint
Database Tables

The backend assumes the following key tables exist:

Flights

Airports

Bookings

Passengers

FareHistory

Ensure that the Bookings table includes:

pnr

price

payment_status (PENDING, PAID, FAILED)

status (PENDING, CONFIRMED, CANCELLED)

These are automatically updated on startup if missing.
