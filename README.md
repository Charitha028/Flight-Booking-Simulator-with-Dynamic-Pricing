✈️ Flight Booking Simulator with Dynamic Pricing

This project is a step-by-step flight booking simulator that demonstrates how airline pricing, seat allocation, and booking logic work.
It is developed in four milestones, each adding new functionality to build the full system.

📌 Milestone 1 — Basic Setup

Designed the initial database schema for flights

Added tables for flights, bookings, and pricing

Inserted sample flight data

Connected Python with the database

Verified all tables and records

📌 Milestone 2 — Dynamic Pricing

Implemented dynamic ticket pricing using Python

Price updates based on:

Days left for the flight

Seats booked / seats remaining

Demand factor

Stored updated prices back into the database

Displayed price changes in a clean table format

Ensured real-time adjustments whenever seats change

Run this file:

python backend2.py

📌 Milestone 3 — Booking System

Implemented the complete booking workflow

Users can:

Search flights

Check availability

View updated ticket prices

Book seats

Updated seat count and pricing after each booking

Error handled:

No seats available

Invalid flight ID

Overbooking

Confirmed each booking is stored in the database

Run this file:

python milestone3.py

📌 Milestone 4 — Frontend Integration

Created a simple HTML frontend

Shows:

List of flights

Available seats

Current price

Frontend interacts with Python backend logic

No external framework required

Can be opened directly in a browser

Open this file:

milestone4_frontend.html

⚙️ How to Run the Whole Project
1️⃣ Clone the project
git clone https://github.com/Charitha028/Flight-Booking-Simulator-with-Dynamic-Pricing.git
cd Flight-Booking-Simulator-with-Dynamic-Pricing

2️⃣ Create the database
sqlite3 flights.db < flights_project.sql

3️⃣ Execute milestone scripts

Use the Python files based on milestone:

python backend2.py          # Dynamic pricing
python milestone3.py        # Booking system

4️⃣ Open the frontend

Just open:

milestone4_frontend.html

📂 Project Structure
📦 Flight-Booking-Simulator-with-Dynamic-Pricing
 ┣ 📄 flights_project.sql
 ┣ 📄 backend2.py
 ┣ 📄 milestone3.py
 ┣ 📄 milestone4_frontend.html
 ┣ 📄 README.md
