Flight Booking Database Schema

This SQL script sets up a Flight Booking Management System database to store and manage airline, airport, flight, passenger, and booking information. It also includes sample data and practice queries for testing and exploration.

Overview

The database models a simplified flight booking system with the following features:

Stores details about airlines, airports, flights, passengers, and bookings.

Includes foreign key constraints to maintain relational integrity.

Contains sample data for testing queries and backend integrations.

Provides practice queries for testing joins, updates, deletes, and transactions.

Database Name
USE flights;

Tables
1. Airlines

Stores basic information about airlines.

Column	Type	Description
airline_id	INT	Primary key (auto-incremented)
airline_name	VARCHAR(100)	Name of the airline
country	VARCHAR(50)	Country of operation
2. Airports

Stores airport details, including city and country.

Column	Type	Description
airport_id	INT	Primary key (auto-incremented)
airport_name	VARCHAR(100)	Name of the airport
city	VARCHAR(50)	City location
country	VARCHAR(50)	Country location
3. Flights

Stores flight schedule and fare details, linked to airlines and airports.

Column	Type	Description
flight_id	INT	Primary key (auto-incremented)
flight_number	VARCHAR(50)	Unique flight number
airline_id	INT	Foreign key → Airlines
origin_airport	INT	Foreign key → Airports
destination_airport	INT	Foreign key → Airports
departure_date_time	DATETIME	Departure time
arrival_date_time	DATETIME	Arrival time
base_fare	DECIMAL(10,2)	Ticket base fare
total_seats	INT	Total seats available
seats_available	INT	Current available seats
4. Passengers

Stores passenger information.

Column	Type	Description
passenger_id	INT	Primary key (auto-incremented)
first_name	VARCHAR(50)	Passenger first name
last_name	VARCHAR(50)	Passenger last name
email	VARCHAR(100)	Unique passenger email
5. Bookings

Stores booking details and tracks flight reservations.

Column	Type	Description
booking_id	INT	Primary key (auto-incremented)
flight_id	INT	Foreign key → Flights
passenger_id	INT	Foreign key → Passengers
seat_no	VARCHAR(5)	Seat number
booking_date	DATETIME	Defaults to current timestamp
status	ENUM	Booking status (CONFIRMED or CANCELLED)
Sample Data
Airlines
INSERT INTO Airlines (airline_name, country) VALUES
('Air India', 'India'),
('IndiGo', 'India'),
('SpiceJet', 'India');

Airports
INSERT INTO Airports (airport_name, city, country) VALUES
('Indira Gandhi International', 'Delhi', 'India'),
('Chhatrapati Shivaji International', 'Mumbai', 'India'),
('Kempegowda International', 'Bengaluru', 'India'),
('Rajiv Gandhi International', 'Hyderabad', 'India');

Flights
INSERT INTO Flights (flight_number, airline_id, origin_airport, destination_airport, 
    departure_date_time, arrival_date_time, base_fare, total_seats, seats_available) 
VALUES
('AI101', 1, 1, 2, '2025-10-10 08:00:00', '2025-10-10 10:15:00', 4500.00, 180, 160),
('6E202', 2, 3, 1, '2025-10-11 06:30:00', '2025-10-11 08:45:00', 3800.00, 200, 180),
('SG303', 3, 4, 2, '2025-10-12 20:00:00', '2025-10-12 22:30:00', 4200.00, 150, 145);

Passengers
INSERT INTO Passengers (first_name, last_name, email) VALUES
('Rohit', 'Verma', 'rohit.verma@example.com'),
('Priya', 'Menon', 'priya.menon@example.com'),
('Arjun', 'Reddy', 'arjun.reddy@example.com');

Bookings
INSERT INTO Bookings (flight_id, passenger_id, seat_no, status) VALUES
(1, 1, '14A', 'CONFIRMED'),
(2, 2, '22B', 'CONFIRMED'),
(3, 3, '08C', 'CANCELLED');

Practice Queries
View All Flights
SELECT * FROM Flights;

Join Passengers with Bookings and Flights
SELECT p.first_name, p.last_name, f.flight_number, f.base_fare, b.status
FROM Passengers p
JOIN Bookings b ON p.passenger_id = b.passenger_id
JOIN Flights f ON b.flight_id = f.flight_id;

Update Base Fare (Increase by 5%)
UPDATE Flights SET base_fare = base_fare * 1.05 WHERE flight_id = 1;

Delete Cancelled Bookings
DELETE FROM Bookings WHERE status = 'CANCELLED';

Transaction Example
START TRANSACTION;
INSERT INTO Bookings (flight_id, passenger_id, seat_no, status)
VALUES (1, 2, '16D', 'CONFIRMED');
UPDATE Flights SET seats_available = seats_available - 1 WHERE flight_id = 1;
COMMIT;

Usage Notes

Always ensure the flights database exists before running the script.

Run all commands in MySQL Workbench or command line.

You can integrate this database with the FastAPI backend for dynamic pricing and booking simulations.

File Structure
Flight-Booking-Simulator-with-Dynamic-Pricing/
│
├── flight_booking_db.sql        # Database schema and sample data
├── backend.py                   # FastAPI backend (if used)
├── README.md                    # Project documentation
└── requirements.txt (optional)
