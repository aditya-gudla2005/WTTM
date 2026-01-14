from flask import Flask, render_template, jsonify
import json
import os
import pandas as pd # Required for the new route

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    with open("risk_metadata.json") as f:
        return jsonify(json.load(f))

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