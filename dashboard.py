from flask import Flask, render_template, jsonify, send_file
import json
import os
import pandas as pd # Required for the new route
from report_generator import generate_pdf_report

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    with open("risk_metadata.json") as f:
        return jsonify(json.load(f))

# Updated /reset route to clear both files
@app.route("/reset", methods=["POST"])
def reset_data():
    # Clear processed metadata
    with open("risk_metadata.json", "w") as f:
        json.dump([], f, indent=4)

    # Clear raw capture data
    with open("wifi_data.csv", "w") as f:
        pass

    return jsonify({"status": "reset_success"})

# New route to generate & download PDF
@app.route("/report")
def generate_report():
    path = generate_pdf_report()
    return send_file(path, as_attachment=True)

# Step 1: Add this route to dashboard.py
@app.route("/rssi/<pos>")
def rssi_data(pos):
    df = pd.read_csv(
        "wifi_data.csv",
        names=["position", "ssid", "rssi", "channel"]
    )

    df = df[df["position"] == pos]

    return jsonify({
        "rssi": df["rssi"].tolist()
    })

if __name__ == "__main__":
    app.run(debug=True)