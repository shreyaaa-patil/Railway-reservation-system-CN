import socket
import json


SERVER_IP = "192.168.0.194"   #put server ip everytime you use pesu wifi
PORT = 5002


def send_request(data):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)  #prevents hanging
        client.connect((SERVER_IP, PORT))

        #send request
        client.send(json.dumps(data).encode())

        #receive response
        response = client.recv(4096).decode()
        client.close()

        return json.loads(response)

    except Exception as e:
        return {"error": "Server not reachable"}


#api parts

def get_seats():
    return send_request({"action": "get_seats"})


def get_history():
    return send_request({"action": "get_history"})


def hold(train, seat, client_id):
    return send_request({
        "action": "hold",
        "train": train,
        "seat": seat,
        "client_id": client_id
    })


def book(train, seat, client_id):
    return send_request({
        "action": "book",
        "train": train,
        "seat": seat,
        "client_id": client_id
    })


def release(train, seat, client_id):
    return send_request({
        "action": "release",
        "train": train,
        "seat": seat,
        "client_id": client_id
    })


def reset():
    return send_request({"action": "reset"})