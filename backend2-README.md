Flight Booking Simulator with Dynamic Pricing

This project simulates a flight booking system that dynamically adjusts ticket prices based on various factors such as seat availability, time to departure, and demand. It is built using FastAPI, SQLAlchemy, and MySQL.

Features

Retrieve all available flights with dynamically calculated prices

Search for flights by origin, destination, and date

Sort search results by price or duration

View real-time fare history for each flight

Simulate market demand and seat availability automatically in the background

Mock external airline API for schedule integration

RESTful endpoints with clear data models and validation

Tech Stack

Backend Framework: FastAPI

Database: MySQL

ORM: SQLAlchemy

Language: Python 3.10+

Other Libraries: PyMySQL, Uvicorn, Pydantic

Project Setup
1. Clone the Repository
git clone https://github.com/<your-username>/Flight-Booking-Simulator-with-Dynamic-Pricing.git
cd Flight-Booking-Simulator-with-Dynamic-Pricing

2. Set Up the Database

Run your flight_booking_db.sql file in MySQL Workbench or the MySQL command line.

Apply any necessary ALTER TABLE commands as specified.

Make sure your database is accessible locally.

3. Update Database Credentials

Open backend.py and update the DATABASE_URL line with your own MySQL username, password, and database name:

DATABASE_URL = "mysql+pymysql://<username>:<password>@localhost:3306/<database_name>"

4. Install Dependencies
pip install fastapi uvicorn sqlalchemy pymysql

5. Run the Application

Start the FastAPI server using:

uvicorn backend:app --reload

API Endpoints
Flights

GET /flights – Retrieve all flights with dynamically calculated prices

GET /dynamic_price/{flight_id} – Get real-time dynamic price for a specific flight

Search

GET /search?origin=DEL&destination=BOM&date=2025-11-01&sort=price – Search flights by route and date, with optional sorting

Fare History

GET /fare_history/{flight_id} – Retrieve recent fare history for a given flight

External Mock API

GET /external/airlines/{code} – Simulated external airline API endpoint

Health Check

GET /health – Check if the API is running

Dynamic Pricing Logic

The dynamic pricing engine calculates prices based on:

Seat Availability: Fewer remaining seats increase prices

Time Until Departure: Prices rise as departure nears

Simulated Demand: Randomized demand levels impact fare adjustments

Base Fare Tiers: Different adjustments for low, medium, and high base fares

Each calculated price is stored in the FareHistory table for reference.

Background Simulation

A background task runs every 60 seconds to:

Randomly adjust available seats

Simulate varying market demand

Recalculate dynamic fares

Log results in the FareHistory table

This provides ongoing, realistic updates to the system.

Example Workflow

Run the backend server using uvicorn.

Access the API documentation at:

http://127.0.0.1:8000/docs


Use endpoints like /flights, /search, and /fare_history/{flight_id} to interact with the system.

Folder Structure
Flight-Booking-Simulator-with-Dynamic-Pricing/
│
├── backend.py                 # Main FastAPI application
├── flight_booking_db.sql      # Database schema
├── README.md                  # Project documentation
└── requirements.txt (optional)

Future Enhancements

Add user booking workflows (seat selection, passenger info, payment simulation)

Introduce authentication and role-based access

Visualize fare history and trends on a dashboard

Integrate with real airline APIs for live data

License

This project is provided for educational and demonstration purposes. You may modify and reuse it as needed with proper attribution.
