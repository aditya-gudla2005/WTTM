import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# =========================
# Threat Mitigations (Unchanged)
# =========================
MITIGATIONS = {
    "Congestion": ["Reduce number of active SSIDs", "Enable band steering to 5 GHz", "Optimize access point placement"],
    "Leakage": ["Reduce transmit power", "Reposition access point away from boundaries", "Use directional antennas"],
    "Channel Overlap": ["Reassign Wi-Fi channels", "Use non-overlapping channels (1, 6, 11)", "Enable automatic channel selection"],
    "Evil Twin": ["Enable WPA3 security", "Monitor BSSID changes", "Deploy wireless intrusion detection"]
}

def generate_rssi_chart(position):
    try:
        df = pd.read_csv("wifi_data.csv", names=["position", "ssid", "rssi", "channel"])
        df = df[df["position"] == position]
        if df.empty: return None

        plt.figure(figsize=(5, 2.5))
        plt.plot(df["rssi"].values, color="#ff5252", linewidth=2)
        plt.fill_between(range(len(df)), df["rssi"].values, color="#ff5252", alpha=0.1)
        plt.title(f"RSSI Trend: {position}", fontsize=10, fontweight='bold', color='#333333')
        plt.ylabel("dBm", fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(tmp.name, dpi=150)
        plt.close()
        return tmp.name
    except Exception as e:
        print(f"Chart error: {e}")
        return None

def generate_pdf_report():
    try:
        with open("risk_metadata.json") as f:
            data = json.load(f)
    except: return None

    pdf_path = "WTTM_Report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 60

    def draw_footer():
        c.setFont("Helvetica", 8)
        c.setStrokeColor(colors.lightgrey)
        c.line(40, 30, width - 40, 30)
        c.drawString(40, 20, "WTTM - Wireless Threat Terrain Mapper | Internal Security Audit")
        c.drawRightString(width - 40, 20, f"Page {c.getPageNumber()}")

    def new_page():
        nonlocal y
        draw_footer()
        c.showPage()
        y = height - 60

    def draw_text(text, size=11, indent=0, color=colors.black, font="Helvetica"):
        nonlocal y
        if y < 80: new_page()
        c.setFont(font, size)
        c.setFillColor(color)
        c.drawString(40 + indent, y, text)
        y -= size + 6

    # =========================
    # Header Styling
    # =========================
    c.setFillColor(colors.HexColor("#1a1a1a"))
    c.rect(0, height - 80, width, 80, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 50, "WTTM SECURITY AUDIT REPORT")
    
    y = height - 110
    draw_text(f"REPORT GENERATED: {datetime.now().strftime('%d %b %Y | %H:%M')}", size=9, color=colors.grey)
    y -= 15

    # =========================
    # Survey Summary
    # =========================
    draw_text("EXECUTIVE SUMMARY", 14, font="Helvetica-Bold", color=colors.HexColor("#c62828"))
    c.setStrokeColor(colors.HexColor("#c62828"))
    c.line(40, y + 4, 180, y + 4)
    
    high = sum(1 for d in data if d["risk"] >= 70)
    medium = sum(1 for d in data if 40 <= d["risk"] < 70)
    
    summary_box_y = y - 10
    c.setFillColor(colors.HexColor("#f4f4f4"))
    c.rect(40, summary_box_y - 60, width - 80, 70, fill=1, stroke=0)
    y -= 20
    draw_text(f"Total Scan Points: {len(data)}", indent=15)
    draw_text(f"High Risk Alerts: {high}", indent=15, color=colors.red if high > 0 else colors.black)
    draw_text(f"Medium Risk Alerts: {medium}", indent=15, color=colors.orange if medium > 0 else colors.black)
    y -= 30

    # Methodology
    draw_text("SIGNAL SPIKE METHODOLOGY", 12, font="Helvetica-Bold")
    draw_text("Sudden RSSI changes (≥15 dBm) are flagged as short-term events to isolate them from", size=9, indent=10, color=colors.darkgrey)
    draw_text("cumulative risk scores. This reduces false positives from environmental movement.", size=9, indent=10, color=colors.darkgrey)
    y -= 20

    # =========================
    # Terrain Map
    # =========================
    draw_text("RISK TERRAIN VISUALIZATION", 14, font="Helvetica-Bold")
    if os.path.exists("static/risk_map.png"):
        c.drawImage("static/risk_map.png", 40, y - 380, width=450, height=380, preserveAspectRatio=True)
        y -= 400
    else:
        draw_text("Risk map visual not available.", size=10, indent=10)

    new_page()

    # =========================
    # Per Position Analysis
    # =========================
    draw_text("DETAILED SITE ANALYSIS", 16, font="Helvetica-Bold", color=colors.HexColor("#1a237e"))
    y -= 10

    for item in data:
        # Position Header
        c.setFillColor(colors.HexColor("#eeeeee"))
        c.rect(40, y - 2, width - 80, 18, fill=1, stroke=0)
        draw_text(f"LOCATION ID: {item['position']}", 12, font="Helvetica-Bold", color=colors.black)
        
        draw_text(f"Primary SSID: {item['ssid']}", indent=10, size=10)
        risk_color = colors.red if item['risk'] >= 70 else (colors.orange if item['risk'] >= 40 else colors.green)
        draw_text(f"Risk Index: {item['risk']}/100", indent=10, size=10, color=risk_color, font="Helvetica-Bold")

        # Spike Status
        spike = item.get("signal_spike", {})
        if spike.get("detected"):
            draw_text(f"EVENT DETECTED: Signal Spike (+{spike['max_spike']} dB)", indent=10, size=10, color=colors.red)
        
        # Threats
        threats = item.get("threats", [])
        if threats:
            draw_text("Identified Threats & Remediation:", indent=10, size=10, font="Helvetica-Bold")
            for t in threats:
                draw_text(f"- {t}", indent=20, size=9)
                for m in MITIGATIONS.get(t, []):
                    draw_text(f"  • {m}", size=8, indent=30, color=colors.grey)

        # Chart
        chart_path = generate_rssi_chart(item["position"])
        if chart_path:
            if y < 180: new_page()
            c.drawImage(chart_path, 45, y - 160, width=320, height=160, preserveAspectRatio=True)
            y -= 175
            try: os.remove(chart_path)
            except: pass
        
        y -= 15 # Gap between items

    draw_footer()
    c.save()
    return pdf_path