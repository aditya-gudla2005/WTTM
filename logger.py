import serial
import csv
import time

PORT = 'COM7'
BAUD = 115200
POSITION = 'P5'

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

with open('wifi_data.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['position', 'ssid', 'rssi', 'channel'])

    start = time.time()
    while time.time() - start < 5:
        line = ser.readline().decode(errors='ignore').strip()
        if line and 'END_SCAN' not in line and 'NO_NETWORKS' not in line:
            parts = line.split(',')
            if len(parts) == 3:
                ssid, rssi, channel = parts
                writer.writerow([POSITION, ssid, rssi, channel])

ser.close()
