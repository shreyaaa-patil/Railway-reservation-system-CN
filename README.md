Train Seat Reservation System
This is a TCP-based seat reservation system with concurrency control, built with Python and Tkinter.

Requirements:
- Python
- No external libraries needed — uses only Python's standard library

Project Structure

client folder - api.py //api calls are handled here
              - client_gui.py //client ui

server folder - serv.py //server side code
              - data.json //seat info
              - backup.json //backup file in case data.json fails to load


Step 1 — Find the Server's IP Address using ipconfig (on windows) on a system where you will run the server side code.

Step 2 — Set the Server IP in api.py

Step 3 — Start the Server

cd server
python serv.py

Step 4 — Start the Client

cd client
python client_gui.py

The GUI window will open. You can run this on as many machines as you want, as long as they are all on the same WiFi network as the server.

Step 5 — Using the App

1. Select **TrainA** or **TrainB** using the toggle at the top
2. Click any **green seat** to begin booking
3. A confirm dialog will appear with a **10 second countdown**
4. Click **Confirm** to complete the booking
5. Click **Cancel** or let the timer run out to release the seat
6. Booked seats appear **red**, held seats appear **yellow**, available seats appear **green**
7. The table at the bottom shows your booking history for the current session


Server crash handling in this case,

GUI opens but seats are all disabled

- The client cannot reach the server.
- Bookings will not be allowed when server side code is not running. Seats will be frozen.

Concurrency control,

Two users cannot hold the same seat at the same time together due to the usage of mutex lock.
Mutex lock is released after 10 seconds in case of no action by the client, If client confirms booking- lock is released and seat becomes unavailable, if client cancels booking- lock is released and seat becomes availablle.

Please note,

- All machines must be connected to the same WiFi network
- The server machine must have port 5002 open for inbound TCP connections
- Booking history shown in the client only includes bookings made in the current session
- If the server restarts, booked seats are preserved but held seats are released
