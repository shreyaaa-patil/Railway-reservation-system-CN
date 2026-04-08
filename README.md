# Train Seat Reservation System (TCP + Tkinter)

A lightweight **TCP-based train seat reservation system** with a **Python Tkinter GUI client** and a **multi-threaded Python socket server**. It demonstrates **concurrency control** (mutex lock) and **seat holding with expiry** to prevent double-booking.

- **Client:** Tkinter GUI (books/holds/releases seats)
- **Server:** Socket server, JSON persistence (`server/data.json`)
- **Concurrency:** One seat can be held by only one client at a time
- **Hold timeout:** 10 seconds (auto-release if not confirmed)

---

## Repository structure

```
.
├── client
│   ├── api.py            # TCP client + API wrappers
│   └── client_gui.py     # Tkinter GUI
└── server
    ├── serv.py           # TCP server
    ├── data.json         # Seat + history persistence
    └── backup.json       # Backup in case data.json fails to load
```

---

## Requirements

- **Python 3.9+** recommended (standard library only)
- No external dependencies

> This project uses only the Python standard library (`socket`, `threading`, `tkinter`, `json`, etc.).

---

## Quick start

### 1) Clone the repository

```bash
git clone https://github.com/shreyaaa-patil/Railway-reservation-system-CN.git
cd Railway-reservation-system-CN
```

### 2) Start the server

In one terminal:

```bash
cd server
python serv.py
```

You should see something like:

```
[SERVER] Running on 0.0.0.0:5002  (hold timeout = 10s)
```

### 3) Configure the client to point to the server

Edit `client/api.py` and set `SERVER_IP` to the IP address of the machine running the server:

- On **Windows**: run `ipconfig` and use the IPv4 address
- On **macOS/Linux**: run `ifconfig` or `ip addr`

Example:

```python
SERVER_IP = "192.168.1.10"
PORT = 5002
```

> If you run client and server on the same machine, you can use `SERVER_IP = "127.0.0.1"`.

### 4) Start the client GUI

In another terminal:

```bash
cd client
python client_gui.py
```

---

## Usage

1. Choose **TrainA** or **TrainB** using the toggle at the top of the GUI
2. Click an **available (green)** seat to place a hold
3. A confirmation dialog opens with a **10-second countdown**
4. Click **Confirm** to book the seat
5. Click **Cancel** (or let the timer expire) to release the hold

### Seat status colors

- **Green** → available
- **Yellow** → held (temporary lock)
- **Red** → booked

### Booking history

The table at the bottom of the client UI shows **booking history for the current client session**.

The server also persists history in `server/data.json` under `history`.

---

## How concurrency / holds work

- The server uses a **global mutex lock** (`threading.Lock`) to serialize operations that read/write seat state.
- When a client holds a seat, the server marks it as `held` and stores the hold in memory with a timestamp.
- A background cleanup worker checks every second and **auto-releases** holds older than **10 seconds** (`HOLD_TIME = 10`).
- Only the client who placed the hold can book or release that hold.

---

## Networking notes / troubleshooting

### Client opens, but seats are disabled / frozen

This usually means the client cannot reach the server:

- Ensure the **server is running** (`python serv.py`)
- Ensure `SERVER_IP` in `client/api.py` points to the correct machine
- Ensure client + server are on the **same network** (e.g., same Wi‑Fi), unless you have routed access
- Ensure port **5002** is allowed through the server machine firewall

### Port in use

If you see an error that port 5002 is already in use, either:

- stop the process currently using the port, or
- change `PORT` in both `server/serv.py` and `client/api.py` to a new port

---

## Data persistence

- Seat state and booking history are stored in `server/data.json`.
- Before overwriting `data.json`, the server tries to copy it to `backup.json`.
- If `data.json` fails to load, the server attempts to recover from `backup.json`.

---

## FAQ

**Q: Can I run multiple clients?**

Yes—run the GUI on as many machines as you want as long as they can connect to the server IP/port.

**Q: Will booked seats remain booked if the server restarts?**

Yes—booked seats are persisted to `server/data.json`. Temporary holds may be cleared after restart.

---

## License

No license file is currently included in this repository. If you want one, add a `LICENSE` file (e.g., MIT).