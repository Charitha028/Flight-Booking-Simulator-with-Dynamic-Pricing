-- Use your existing database
USE flights;

-- Drop old tables if they exist
DROP TABLE IF EXISTS Bookings;
DROP TABLE IF EXISTS Passengers;
DROP TABLE IF EXISTS Flights;
DROP TABLE IF EXISTS Airports;
DROP TABLE IF EXISTS Airlines;

-- TABLES

-- Airlines
CREATE TABLE Airlines (
    airline_id INT AUTO_INCREMENT PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- Airports
CREATE TABLE Airports (
    airport_id INT AUTO_INCREMENT PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    country VARCHAR(50)
);

-- Flights
CREATE TABLE Flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(50) UNIQUE NOT NULL,
    airline_id INT NOT NULL,
    origin_airport INT NOT NULL,
    destination_airport INT NOT NULL,
    departure_date_time DATETIME NOT NULL,
    arrival_date_time DATETIME NOT NULL,
    base_fare DECIMAL(10,2) CHECK(base_fare > 0),
    total_seats INT CHECK(total_seats > 0),
    seats_available INT CHECK(seats_available >= 0),
    FOREIGN KEY (airline_id) REFERENCES Airlines(airline_id),
    FOREIGN KEY (origin_airport) REFERENCES Airports(airport_id),
    FOREIGN KEY (destination_airport) REFERENCES Airports(airport_id)
);

-- Passengers
CREATE TABLE Passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE
);

-- Bookings
CREATE TABLE Bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    passenger_id INT NOT NULL,
    seat_no VARCHAR(5),
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('CONFIRMED', 'CANCELLED') DEFAULT 'CONFIRMED',
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY (passenger_id) REFERENCES Passengers(passenger_id)
);

-- SAMPLE DATA 
-- Airlines
INSERT INTO Airlines (airline_name, country) VALUES
('Air India', 'India'),
('IndiGo', 'India'),
('SpiceJet', 'India');

-- Airports
INSERT INTO Airports (airport_name, city, country) VALUES
('Indira Gandhi International', 'Delhi', 'India'),
('Chhatrapati Shivaji International', 'Mumbai', 'India'),
('Kempegowda International', 'Bengaluru', 'India'),
('Rajiv Gandhi International', 'Hyderabad', 'India');

-- Flights
INSERT INTO Flights (flight_number, airline_id, origin_airport, destination_airport, 
    departure_date_time, arrival_date_time, base_fare, total_seats, seats_available) 
VALUES
('AI101', 1, 1, 2, '2025-10-10 08:00:00', '2025-10-10 10:15:00', 4500.00, 180, 160),
('6E202', 2, 3, 1, '2025-10-11 06:30:00', '2025-10-11 08:45:00', 3800.00, 200, 180),
('SG303', 3, 4, 2, '2025-10-12 20:00:00', '2025-10-12 22:30:00', 4200.00, 150, 145);

-- Passengers
INSERT INTO Passengers (first_name, last_name, email) VALUES
('Rohit', 'Verma', 'rohit.verma@example.com'),
('Priya', 'Menon', 'priya.menon@example.com'),
('Arjun', 'Reddy', 'arjun.reddy@example.com');

-- Bookings
INSERT INTO Bookings (flight_id, passenger_id, seat_no, status) VALUES
(1, 1, '14A', 'CONFIRMED'),
(2, 2, '22B', 'CONFIRMED'),
(3, 3, '08C', 'CANCELLED');

-- PRACTICE QUERIES

-- View all flights
SELECT * FROM Flights;

-- Join passengers with bookings and flights
SELECT p.first_name, p.last_name, f.flight_number, f.base_fare, b.status
FROM Passengers p
JOIN Bookings b ON p.passenger_id = b.passenger_id
JOIN Flights f ON b.flight_id = f.flight_id;

-- Update base fare (increase by 5%)
UPDATE Flights SET base_fare = base_fare * 1.05 WHERE flight_id = 1;

-- Delete cancelled booking
DELETE FROM Bookings WHERE status = 'CANCELLED';

-- Transaction example
START TRANSACTION;
INSERT INTO Bookings (flight_id, passenger_id, seat_no, status) VALUES (1, 2, '16D', 'CONFIRMED');
UPDATE Flights SET seats_available = seats_available - 1 WHERE flight_id = 1;
COMMIT;