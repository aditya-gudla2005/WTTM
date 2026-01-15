import matplotlib
matplotlib.use("Agg") # Prevent GUI popups during PDF generation

import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# =========================
# Threat Mitigations
# =========================
MITIGATIONS = {
    "Congestion": [
        "Reduce number of active SSIDs",
        "Enable band steering to 5 GHz",
        "Optimize access point placement"
    ],
    "Leakage": [
        "Reduce transmit power",
        "Reposition access point away from boundaries",
        "Use directional antennas"
    ],
    "Channel Overlap": [
        "Reassign Wi-Fi channels",
        "Use non-overlapping channels (1, 6, 11)",
        "Enable automatic channel selection"
    ],
    "Evil Twin": [
        "Enable WPA3 security",
        "Monitor BSSID changes",
        "Deploy wireless intrusion detection"
    ]
}

def generate_rssi_chart(position):
    """Generates a temporary RSSI chart for the PDF."""
    try:
        df = pd.read_csv(
            "wifi_data.csv",
            names=["position", "ssid", "rssi", "channel"]
        )
        df = df[df["position"] == position]

        if df.empty:
            return None

        plt.figure(figsize=(4, 2))
        plt.plot(df["rssi"].values, color="red")
        plt.title(f"RSSI Trend – {position}")
        plt.ylabel("RSSI (dBm)")
        plt.xlabel("Samples")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(tmp.name)
        plt.close()
        return tmp.name
    except Exception as e:
        print(f"Chart error for {position}: {e}")
        return None

def generate_pdf_report():
    # Load metadata
    try:
        with open("risk_metadata.json") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return None

    pdf_path = "WTTM_Report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 50

    def new_page():
        nonlocal y
        c.showPage()
        y = height - 50

    def draw_text(text, size=11, indent=0):
        nonlocal y
        if y < 80:
            new_page()
        c.setFont("Helvetica", size)
        c.drawString(40 + indent, y, text)
        y -= size + 6

    def draw_image(path, img_width=400, img_height=200):
        nonlocal y
        if y < img_height + 80:
            new_page()
        c.drawImage(path, 40, y - img_height, width=img_width, height=img_height, preserveAspectRatio=True)
        y -= img_height + 20

    # =========================
    # Title Page
    # =========================
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, "Wireless Threat Terrain Mapper (WTTM)")
    y -= 30
    draw_text(f"Survey Date: {datetime.now().strftime('%d %b %Y %H:%M')}", size=10)
    y -= 20

    # =========================
    # Survey Summary
    # =========================
    high = sum(1 for d in data if d["risk"] >= 70)
    medium = sum(1 for d in data if 40 <= d["risk"] < 70)
    low = sum(1 for d in data if d["risk"] < 40)

    draw_text("Survey Summary", 14)
    draw_text(f"Total Positions Scanned: {len(data)}")
    draw_text(f"High Risk Zones: {high}")
    draw_text(f"Medium Risk Zones: {medium}")
    draw_text(f"Low Risk Zones: {low}")
    y -= 20

    # =========================
    # Risk Terrain Map Overlay
    # =========================
    draw_text("Risk Terrain Map Overlay", 14)
    if os.path.exists("static/risk_map.png"):
        draw_image("static/risk_map.png", img_width=450, img_height=450)
    else:
        draw_text("Risk map image not found.", size=10)
    
    new_page()

    # =========================
    # Per Position Analysis
    # =========================
    draw_text("Detailed Risk Analysis", 16)
    y -= 10

    for item in data:
        y -= 10
        draw_text(f"Position: {item['position']}", 12)
        draw_text(f"Top SSID: {item['ssid']}", indent=10)
        draw_text(f"Risk Score: {item['risk']}/100", indent=10)

        threats = item.get("threats", [])
        if not threats:
            draw_text("No threats detected", indent=10)
        else:
            draw_text("Detected Threats & Mitigations:", indent=10)
            for t in threats:
                draw_text(f"- {t}", indent=20)
                for m in MITIGATIONS.get(t, []):
                    draw_text(f"• {m}", size=9, indent=35)

        # Generate and Embed RSSI Chart
        chart_path = generate_rssi_chart(item["position"])
        if chart_path:
            draw_image(chart_path, img_width=350, img_height=175)
            try: os.remove(chart_path) # Cleanup temp file
            except: pass

        y -= 10 # Spacing between positions

    c.save()
    return pdf_path