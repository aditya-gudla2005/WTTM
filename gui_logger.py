import subprocess
import threading
import serial
import csv
import time
import tkinter as tk
from tkinter import messagebox
import os

PORT = "COM7"
BAUD = 115200
CSV_FILE = "wifi_data.csv"

# Minor (optional but good): CSV header safety
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        pass

current_position = None

def set_position(pos):
    global current_position
    current_position = pos
    status_label.config(text=f"Selected Position: {pos}")

def capture_data():
    if not current_position:
        messagebox.showwarning("No Position", "Select a position first")
        return

    # FIX: Disable button to prevent multiple overlapping threads
    capture_btn.config(state="disabled")
    status_label.config(text=f"Capturing at {current_position}... Stand still")

    def task():
        # ✅ Replace: Open serial only when capturing
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)  # allow ESP to stabilize
        
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            start = time.time()
            end_time = start + 4
            while time.time() < end_time:
                try:
                    line = ser.readline().decode(errors="ignore").strip()
                except:
                    continue

                if not line or line == "END":
                    continue

                try:
                    ssid, rssi, channel = line.split(",")
                    writer.writerow([current_position, ssid, rssi, channel])
                except:
                    pass
                
                time.sleep(0.05) # Prevent serial lock
        
        # ✅ After the loop, close cleanly
        ser.close()
        root.after(0, capture_done)

    threading.Thread(target=task, daemon=True).start()

def capture_done():
    # ✅ Re-enable button
    capture_btn.config(state="normal")
    status_label.config(text=f"Capture complete for {current_position}")
    messagebox.showinfo("Done", f"Capture completed at {current_position}")

def generate_map():
    # ✅ Better UX: Wait for process to finish and show popup
    subprocess.run(["python", "unified_risk_map.py"])
    messagebox.showinfo("Map Ready", "Risk map generated successfully.")

# GUI
root = tk.Tk()
root.title("WTTM – Position Capture Console")
root.geometry("400x400")

status_label = tk.Label(root, text="Select a position", font=("Arial", 12))
status_label.pack(pady=10)

grid_frame = tk.Frame(root)
grid_frame.pack()

positions = [
    ["P1","P2","P3"],
    ["P4","P5","P6"],
    ["P7","P8","P9"]
]

for row in positions:
    row_frame = tk.Frame(grid_frame)
    row_frame.pack()
    for p in row:
        tk.Button(row_frame, text=p, width=8, height=2,
                  command=lambda x=p: set_position(x)).pack(side=tk.LEFT, padx=5, pady=5)

# ✅ Updated capture_btn creation to allow state changes
capture_btn = tk.Button(
    root, text="CAPTURE", bg="green", fg="white",
    font=("Arial", 12), command=capture_data
)
capture_btn.pack(pady=20)

tk.Button(root, text="GENERATE MAP", bg="blue", fg="white",
          font=("Arial", 12), command=generate_map).pack(pady=5)

root.mainloop()