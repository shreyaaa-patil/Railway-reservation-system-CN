import socket
import threading
import json
import time
import shutil
import os
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5002

DATA_FILE   = "data.json"
BACKUP_FILE = "backup.json"

lock      = threading.Lock()
holds     = {}       
HOLD_TIME = 10        #seconds


#data handling

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
        try:
            with open(BACKUP_FILE, "r") as f:
                print("[RECOVERY] Loaded from backup")
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


#hold expiry

def clear_expired_holds(data):
    now     = time.time()
    expired = []

    for key, (ts, client_id) in list(holds.items()):
        if now - ts > HOLD_TIME:
            train, seat = key
            if data["trains"][train][str(seat)] == "held":
                data["trains"][train][str(seat)] = "available"
                print(f"[HOLD EXPIRED] {train} seat {seat} → available")
            expired.append(key)

    for key in expired:
        del holds[key]

    return len(expired) > 0


def hold_cleanup_worker():
    while True:
        time.sleep(1)
        try:
            with lock:
                data    = load_data()
                changed = clear_expired_holds(data)
                if changed:
                    save_data(data)
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")


#client handler

def handle_client(conn):
    try:
        raw     = conn.recv(4096).decode()
        req     = json.loads(raw)
        action  = req.get("action")
        response = {}

        with lock:
            data = load_data()
            clear_expired_holds(data) 
            if action == "get_seats":
                result = {}
                for train_name, seats in data["trains"].items():
                    result[train_name] = {}
                    for seat_num, status in seats.items():
                        key = (train_name, seat_num)
                        if status == "held" and key not in holds:
                            #Held on disk but not in memory---stale, fix it
                            result[train_name][seat_num] = "available"
                            data["trains"][train_name][seat_num] = "available"
                        else:
                            result[train_name][seat_num] = status
                save_data(data)   #persist any stale-hold corrections
                response = result

            #GET HISTORY
            elif action == "get_history":
                response = data["history"]

            #HOLD
            elif action == "hold":
                train     = req["train"]
                seat      = str(req["seat"])
                client_id = req["client_id"]
                key       = (train, seat)

                if data["trains"][train][seat] == "available":
                    data["trains"][train][seat] = "held"
                    holds[key] = (time.time(), client_id)
                    save_data(data)
                    print(f"[HOLD] {train} seat {seat} held by {client_id[:8]}")
                    response = {"status": "held"}
                else:
                    response = {"status": "failed"}

            #BOOK
            elif action == "book":
                train     = req["train"]
                seat      = str(req["seat"])
                client_id = req["client_id"]
                key       = (train, seat)

                if key in holds:
                    ts, owner = holds[key]
                    if owner == client_id:
                        data["trains"][train][seat] = "booked"
                        del holds[key]
                        data["history"].append({
                            "train":     train,
                            "seat":      seat,
                            "time":      datetime.now().strftime("%H:%M:%S"),
                            "client_id": client_id
                        })
                        save_data(data)
                        print(f"[BOOK] {train} seat {seat} booked by {client_id[:8]}")
                        response = {"status": "success"}
                    else:
                        response = {"status": "failed", "reason": "not owner"}
                else:
                    response = {"status": "failed", "reason": "no hold found"}

            #RELEASE
            elif action == "release":
                train     = req["train"]
                seat      = str(req["seat"])
                client_id = req["client_id"]
                key       = (train, seat)

                if key in holds:
                    ts, owner = holds[key]
                    if owner == client_id:
                        data["trains"][train][seat] = "available"
                        del holds[key]
                        save_data(data)
                        print(f"[RELEASE] {train} seat {seat} released by {client_id[:8]}")
                response = {"status": "released"}

            #RESET
            elif action == "reset":
                data = default_data()
                holds.clear()
                save_data(data)
                print("[RESET] All seats cleared")
                response = {"status": "reset"}

        conn.send(json.dumps(response).encode())

    except Exception as e:
        print(f"[CLIENT ERROR] {e}")
        try:
            conn.send(json.dumps({"error": str(e)}).encode())
        except:
            pass
    finally:
        conn.close()


#server start

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Running on {HOST}:{PORT}  (hold timeout = {HOLD_TIME}s)")

    threading.Thread(target=hold_cleanup_worker, daemon=True).start()

    while True:
        conn, addr = server.accept()
        print(f"[CONNECT] {addr}")
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    start_server()