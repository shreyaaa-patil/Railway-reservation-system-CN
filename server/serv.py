import socket
import threading
import json
import time
import shutil
import os
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5002

DATA_FILE = "data.json"
BACKUP_FILE = "backup.json"

lock = threading.Lock()

holds = {}
HOLD_TIME = 10  #seconds


#DATA HANDLING

def default_data():
    return {
        "trains": {
            "TrainA": {str(i): "available" for i in range(1, 11)},
            "TrainB": {str(i): "available" for i in range(1, 11)}
        },
        "history": []
    }


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        #crash recovery
        try:
            with open(BACKUP_FILE, "r") as f:
                return json.load(f)
        except:
            data = default_data()
            save_data(data)
            return data


def save_data(data):
    try:
        if os.path.exists(DATA_FILE):
            shutil.copy(DATA_FILE, BACKUP_FILE)
    except:
        pass

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def hold_cleanup_worker():
    while True:
        time.sleep(1)  #check every second

        with lock:
            data = load_data()
            changed = clear_expired_holds(data)

            if changed:
                save_data(data)
#lock expiry
def clear_expired_holds(data):
    now = time.time()
    expired = []

    for key, (ts, client_id) in list(holds.items()):
        if now - ts > HOLD_TIME:
            train, seat = key

            if data["trains"][train][seat] == "held":
                data["trains"][train][seat] = "available"

            expired.append(key)

    for key in expired:
        del holds[key]

    return len(expired) > 0


#CLIENT HANDLER

def handle_client(conn):
    try:
        request = conn.recv(4096).decode()
        req = json.loads(request)

        action = req.get("action")

        with lock:
            data = load_data()
            clear_expired_holds(data)

            response = {}

            #GET SEATS
            if action == "get_seats":
                response = data["trains"]

            #GET HISTORY
            elif action == "get_history":
                response = data["history"]

            #HOLD
            elif action == "hold":
                train = req["train"]
                seat = str(req["seat"])
                client_id = req["client_id"]

                if data["trains"][train][seat] == "available":
                    data["trains"][train][seat] = "held"
                    holds[(train, seat)] = (time.time(), client_id)
                    save_data(data)
                    response = {"status": "held"}
                else:
                    response = {"status": "failed"}

            #BOOK
            elif action == "book":
                train = req["train"]
                seat = str(req["seat"])
                client_id = req["client_id"]

                key = (train, seat)

                if key in holds:
                    ts, owner = holds[key]

                    if owner == client_id:
                        data["trains"][train][seat] = "booked"
                        del holds[key]

                        data["history"].append({
                            "train": train,
                            "seat": seat,
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "client_id": client_id
    
                        })

                        save_data(data)
                        response = {"status": "success"}
                    else:
                        response = {"status": "failed"}
                else:
                    response = {"status": "failed"}

            #RELEASE
            elif action == "release":
                train = req["train"]
                seat = str(req["seat"])
                client_id = req["client_id"]

                key = (train, seat)

                if key in holds:
                    ts, owner = holds[key]

                    if owner == client_id:
                        data["trains"][train][seat] = "available"
                        del holds[key]
                        save_data(data)

                response = {"status": "released"}

            #RESET
            elif action == "reset":
                data = default_data()
                holds.clear()
                save_data(data)
                response = {"status": "reset"}

        conn.send(json.dumps(response).encode())

    except Exception as e:
        print("Server Error:", e)

    finally:
        conn.close()


#SERVER START

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Server running on {HOST}:{PORT}")
    
    threading.Thread(target=hold_cleanup_worker, daemon=True).start()
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client,
                         args=(conn,), daemon=True).start()


if __name__ == "__main__":
    start_server()