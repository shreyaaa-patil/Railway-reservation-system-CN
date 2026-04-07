import tkinter as tk
from tkinter import ttk
import threading
import uuid

from api import get_seats, get_history, hold, book, release

CLIENT_ID = str(uuid.uuid4())

#colours and stuff
BG          = "#0f1117"
SURFACE     = "#1a1d27"
SURFACE2    = "#22263a"
ACCENT      = "#4f8ef7"
ACCENT_DIM  = "#1e3a6e"

GREEN       = "#22c55e"
GREEN_DIM   = "#14532d"

RED         = "#ef4444"
RED_DIM     = "#7f1d1d"

YELLOW      = "#facc15"
YELLOW_DIM  = "#713f12"

TEXT        = "#e8eaf0"
TEXT_DIM    = "#6b7280"

FONT_HEAD   = ("Georgia", 22, "bold")
FONT_SUB    = ("Courier", 10)
FONT_BTN    = ("Courier", 13, "bold")
FONT_SMALL  = ("Courier", 9)
FONT_STATUS = ("Courier", 9)

#tkinter root stuff
root = tk.Tk()
root.title("Train Seat Reservation (TCP)")
root.configure(bg=BG)
root.resizable(False, False)
root.geometry("520x660")

train = tk.StringVar(value="TrainA")
status_var = tk.StringVar(value="Ready.")
buttons = {}

server_down=False

#hdr
header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=24, pady=(22, 4))

tk.Label(header, text="SEAT RESERVATION",
         font=FONT_HEAD, bg=BG, fg=TEXT).pack(side="left")

tk.Frame(root, bg=ACCENT, height=2).pack(fill="x", padx=24, pady=(0, 18))

#select train A or B
toggle_frame = tk.Frame(root, bg=BG)
toggle_frame.pack(pady=(0, 16))

tk.Label(toggle_frame, text="SELECT TRAIN",
         font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="left", padx=(0, 12))

train_toggle_container = tk.Frame(toggle_frame, bg=SURFACE2,
                                 highlightthickness=1,
                                 highlightbackground=ACCENT_DIM)
train_toggle_container.pack(side="left")

toggle_btns = {}

def select_train(name):
    train.set(name)
    for t, b in toggle_btns.items():
        if t == name:
            b.config(bg=ACCENT, fg=TEXT)
        else:
            b.config(bg=SURFACE2, fg=TEXT_DIM)
    refresh()

for t_name in ["TrainA", "TrainB"]:
    b = tk.Button(train_toggle_container, text=t_name,
                  font=FONT_SUB, bg=SURFACE2, fg=TEXT_DIM,
                  relief="flat", bd=0, padx=18, pady=6,
                  command=lambda n=t_name: select_train(n))
    b.pack(side="left")
    toggle_btns[t_name] = b

toggle_btns["TrainA"].config(bg=ACCENT, fg=TEXT)

#seat matrix
seat_section = tk.Frame(root, bg=SURFACE,
                        highlightthickness=1,
                        highlightbackground=SURFACE2)
seat_section.pack(padx=24, pady=(0, 16), fill="x")

tk.Label(seat_section, text="  SEATS",
         font=FONT_SMALL, bg=SURFACE, fg=TEXT_DIM).pack(anchor="w", padx=8)

grid_frame = tk.Frame(seat_section, bg=SURFACE)
grid_frame.pack(padx=16, pady=10)

#legend
legend = tk.Frame(seat_section, bg=SURFACE)
legend.pack(anchor="e", padx=16, pady=(0, 10))

for color, label in [(GREEN, "Available"), (YELLOW, "Held"), (RED, "Booked")]:
    tk.Frame(legend, bg=color, width=10, height=10).pack(side="left", padx=3)
    tk.Label(legend, text=label, font=FONT_SMALL,
             bg=SURFACE, fg=TEXT_DIM).pack(side="left", padx=5)

def create_buttons():
    for i in range(1, 11):
        btn = tk.Button(grid_frame, text=str(i),
                        font=FONT_BTN, width=4, height=2,
                        relief="flat", bg=GREEN_DIM, fg=GREEN,
                        command=lambda i=i: book_seat(i))
        btn.grid(row=(i-1)//5, column=(i-1)%5, padx=8, pady=8)
        buttons[i] = btn

create_buttons()

#store history
tree = ttk.Treeview(root, columns=("time","train","seat"),
                    show="headings", height=6)
tree.heading("time", text="Time")
tree.heading("train", text="Train")
tree.heading("seat", text="Seat")
tree.pack(fill="both", expand=True, padx=10, pady=10)

#status bar
status_bar = tk.Frame(root, bg=SURFACE2)
status_bar.pack(fill="x", side="bottom")

tk.Label(status_bar, textvariable=status_var,
         font=FONT_STATUS, bg=SURFACE2, fg=TEXT_DIM).pack(anchor="w", padx=10)

#timeout alert
def confirm_with_timeout(seat, timeout, on_confirm, on_cancel):
    win = tk.Toplevel(root)
    win.title("Confirm Booking")
    win.geometry("300x160")
    win.configure(bg=SURFACE)
    win.resizable(False, False)
    win.protocol("WM_DELETE_WINDOW", lambda: _do_cancel())

    decided = {"done": False}

    tk.Label(win, text=f"Book Seat {seat}?",
             font=FONT_BTN, bg=SURFACE, fg=TEXT).pack(pady=(16, 4))

    timer_label = tk.Label(win, text=f"Time left: {timeout}s",
                           font=FONT_SUB, bg=SURFACE, fg=YELLOW)
    timer_label.pack(pady=(0, 8))

    def _do_confirm():
        if decided["done"]:
            return
        decided["done"] = True
        win.destroy()
        on_confirm()

    def _do_cancel():
        if decided["done"]:
            return
        decided["done"] = True
        win.destroy()
        on_cancel()

    btn_frame = tk.Frame(win, bg=SURFACE)
    btn_frame.pack()

    tk.Button(btn_frame, text="Confirm", command=_do_confirm,
              font=FONT_SUB, bg=GREEN, fg="white",
              relief="flat", padx=16, pady=6).pack(side="left", padx=16)

    tk.Button(btn_frame, text="Cancel", command=_do_cancel,
              font=FONT_SUB, bg=RED, fg="white",
              relief="flat", padx=16, pady=6).pack(side="right", padx=16)

    def countdown(t):
        if decided["done"]:
            return                         #user already acted,stop ticking
        if t <= 0:
            _do_cancel()                   #time's up then auto-cancel
            return
        timer_label.config(text=f"Time left: {t}s")
        win.after(1000, countdown, t - 1)  #next tick, runs on main thread

    countdown(timeout)

#some more history stuff
def update_history():
    history = get_history()
    if "error" in history:
        return

    for row in tree.get_children():
        tree.delete(row)

    for entry in reversed(history):
        if entry.get("client_id") == CLIENT_ID:
            tree.insert("", "end",
                values=(entry["time"], entry["train"],
                    f"Seat {entry['seat']}"))
        

def refresh():
    global server_down

    data = get_seats()

    if "error" in data:
        if not server_down:
            status_var.set("Server not reachable, please try again later")
            server_down = True

        for b in buttons.values():
            b.config(state="disabled")

        return

    #server when its back
    if server_down:
        status_var.set("Server connected")
        server_down = False

    current = train.get()

    for i in range(1, 11):
        status = data[current][str(i)]
        btn = buttons[i]

        if status == "available":
            btn.config(bg="#14532d", fg="#22c55e", state="normal")

        elif status == "held":
            btn.config(bg="#713f12", fg="#facc15", state="normal")

        else:
            btn.config(bg="#7f1d1d", fg="#ef4444", state="disabled")

    update_history()

def book_seat(seat):
    status_var.set(f"Requesting lock for seat {seat}...")

    def task():
        res = hold(train.get(), seat, CLIENT_ID)

        if res.get("status") != "held":
            root.after(0, lambda: status_var.set("Seat is already taken"))
            root.after(0, refresh)
            return

        #Hold acquired
        def show_dialog():
            status_var.set("Seat held! Confirm within 10 seconds...")

            def on_confirm():
                status_var.set("Booking...")

                def do_book():
                    res2 = book(train.get(), seat, CLIENT_ID)
                    if res2.get("status") == "success":
                        root.after(0, lambda: status_var.set(f"Seat {seat} booked!"))
                    else:
                        root.after(0, lambda: status_var.set("Booking failed"))
                    root.after(0, refresh)

                threading.Thread(target=do_book, daemon=True).start()

            def on_cancel():
            
                status_var.set("Releasing hold...")

                def do_release():
                    release(train.get(), seat, CLIENT_ID)
                    root.after(0, lambda: status_var.set("Booking cancelled / timed out"))
                    root.after(0, refresh)

                threading.Thread(target=do_release, daemon=True).start()

            confirm_with_timeout(seat, 10, on_confirm, on_cancel)

        root.after(0, show_dialog)

    threading.Thread(target=task, daemon=True).start()

def auto_refresh():
    refresh()
    root.after(800, auto_refresh)

auto_refresh()
root.mainloop()