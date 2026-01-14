import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

# ==========================================
# STEP 1: DYNAMIC DATA LOADING
# ==========================================
try:
    df = pd.read_csv(
        "wifi_data.csv",
        names=["position", "ssid", "rssi", "channel"]
    )

    df["rssi"] = pd.to_numeric(df["rssi"], errors="coerce")
    df["channel"] = pd.to_numeric(df["channel"], errors="coerce")
    df = df.dropna(subset=["position", "ssid", "rssi"])
except FileNotFoundError:
    print("Error: 'wifi_data.csv' not found. Please run a capture first.")
    exit()

# ==========================================
# STEP 2: WTTM RISK + METRICS ALGORITHM
# ==========================================
def compute_risk(df_pos):
    risk = 0
    threats = []

    max_rssi = df_pos["rssi"].max()
    ssid_count = df_pos["ssid"].nunique()
    channel_overlap = int(df_pos["channel"].value_counts().max())
    ssid_repeats = int(df_pos["ssid"].value_counts().max())

    if max_rssi > -60:
        risk += 30
        threats.append("Leakage")
    elif max_rssi > -75:
        risk += 15

    if ssid_count >= 8:
        risk += 20
        threats.append("Congestion")
    elif ssid_count >= 4:
        risk += 10

    if channel_overlap >= 3:
        risk += 20
        threats.append("Channel Overlap")
    elif channel_overlap == 2:
        risk += 10

    if ssid_repeats >= 2:
        risk += 30
        threats.append("Evil Twin")

    metrics = {
        "max_rssi": float(max_rssi),
        "ssid_count": int(ssid_count),
        "channel_overlap": int(channel_overlap),
        "ssid_repeats": int(ssid_repeats)
    }

    return min(risk, 100), sorted(set(threats)), metrics

# ==========================================
# STEP 3: LABEL BUILDER
# ==========================================
def build_label(df_pos, risk):
    top = df_pos.sort_values("rssi", ascending=False).iloc[0]

    if risk > 60:
        level = "HIGH"
    elif risk > 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    ssid = top["ssid"]
    short_ssid = ssid[:10] + "…" if len(ssid) > 10 else ssid
    label = f"{level}\n{short_ssid}"

    return label

# ==========================================
# STEP 4: GRID + METADATA GENERATION
# ==========================================
positions = sorted(
    df["position"].unique(),
    key=lambda x: int(x[1:]) if x[1:].isdigit() else x
)

grid_size = int(np.ceil(np.sqrt(len(positions))))
risk_grid = np.zeros((grid_size, grid_size))
label_grid = [["" for _ in range(grid_size)] for _ in range(grid_size)]

cell_metadata = {}

for idx, pos in enumerate(positions):
    row = idx // grid_size
    col = idx % grid_size

    df_pos = df[df["position"] == pos]
    risk, threats, metrics = compute_risk(df_pos)
    label = build_label(df_pos, risk)

    top_ssid = df_pos.sort_values("rssi", ascending=False).iloc[0]["ssid"]

    cell_metadata[pos] = {
        "position": pos,
        "risk": risk,
        "ssid": top_ssid,
        "threats": threats,
        "metrics": metrics
    }

    risk_grid[row, col] = risk
    label_grid[row][col] = label

# ==========================================
# STEP 5: HEATMAP IMAGE (OPTIONAL)
# ==========================================
def generate_map_image(output_path="static/risk_map.png"):
    plt.figure(figsize=(10, 10))
    plt.imshow(risk_grid, cmap="RdYlBu_r", vmin=0, vmax=100)

    for i in range(grid_size):
        for j in range(grid_size):
            if label_grid[i][j]:
                color = "black" if 30 < risk_grid[i, j] < 70 else "white"
                plt.text(j, i, label_grid[i][j],
                         ha="center", va="center",
                         fontsize=11, fontweight="bold", color=color)

    plt.xticks([])
    plt.yticks([])
    plt.title("WTTM – Unified Wireless Threat Terrain", fontsize=16)
    plt.colorbar(label="Risk Score (0–100)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

# ==========================================
# STEP 6: EXPORT JSON FOR DASHBOARD
# ==========================================
def export_metadata():
    export = list(cell_metadata.values())
    with open("risk_metadata.json", "w") as f:
        json.dump(export, f, indent=4)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    generate_map_image()
    export_metadata()
    print("WTTM map + metadata generated successfully")
