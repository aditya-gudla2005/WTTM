// ===============================
// Threat explanation builders
// ===============================
const threatExplanations = {
  Congestion: m =>
    `Detected ${m.ssid_count} unique SSIDs in this area, increasing spectrum contention.`,

  Leakage: m =>
    `Strong signal detected (max RSSI ${m.max_rssi} dBm), suggesting RF leakage beyond expected range.`,

  "Channel Overlap": m =>
    `${m.channel_overlap} networks are operating on the same Wi-Fi channel.`,

  "Evil Twin": m =>
    `SSID observed ${m.ssid_repeats} times with differing signal patterns, indicating a possible rogue AP.`
};

// ✅ Step 1: Define the spike tooltip text
const spikeTooltip =
  "Signal Spike: Sudden abnormal RSSI jump or drop (≥15 dBm) between consecutive samples. Represents a short-term RF event, not a sustained risk unless repeatedly observed.";

// ===============================
// Build Grid & Process Alerts
// ===============================
fetch("/data")
  .then(res => res.json())
  .then(data => {
    const grid = document.getElementById("grid");
    const details = document.getElementById("details");
    const alertsBox = document.getElementById("alerts");

    grid.innerHTML = "";
    alertsBox.innerHTML = ""; // Clear old alerts

    data.forEach(item => {
      // --- NEW: Signal Spike Logic with Technical Font Wrapping ---
      if (item.signal_spike && item.signal_spike.detected) {
        alertsBox.innerHTML += `
          <div class="alert">
            <div class="alert-title">
              <span>⚠️ SIGNAL SPIKE</span>
              <span class="info-icon" data-tip="${spikeTooltip}">ⓘ</span>
            </div>
            <div class="alert-body">
              POS: ${item.position}<br>
              JUMP: +${item.signal_spike.max_spike} dBm
            </div>
          </div>
        `;
      }

      // --- Grid Generation ---
      const cell = document.createElement("div");
      cell.className = "cell";

      if (item.risk >= 70) cell.classList.add("high");
      else if (item.risk >= 40) cell.classList.add("medium");
      else cell.classList.add("low");

      cell.textContent = item.position;

      cell.onclick = () => {
        if (!item.metrics) {
          details.innerHTML = `
            <div class="card">
              <h3>${item.position}</h3>
              <p>No metrics available for this cell.</p>
            </div>
          `;
          return;
        }

        let threatsHtml = "";
        if (!item.threats || item.threats.length === 0) {
          threatsHtml = `<span class="no-threat">None Detected</span>`;
        } else {
          threatsHtml = item.threats.map(t => {
            const explain = threatExplanations[t]
              ? threatExplanations[t](item.metrics)
              : "No explanation available.";

            return `
              <div class="threat-pill">
                <span class="label">${t}</span>
                <span class="info-icon" data-tip="${explain}">ⓘ</span>
              </div>
            `;
          }).join("");
        }

        // --- UPDATED: Details Panel with Glassy Risk Bar ---
        details.innerHTML = `
          <div class="card">
            <h3>${item.position}</h3>
            <p><b>SSID:</b> ${item.ssid}</p>
            <p class="risk ${cell.classList[1]}">Risk Score: ${item.risk}</p>
            
            <div class="risk-bar-container">
                <div class="risk-bar ${cell.classList[1]}" style="width: ${item.risk}%"></div>
            </div>

            <div class="threats">
              <b>Threats:</b>
              <div class="threat-list">${threatsHtml}</div>
            </div>
          </div>
        `;

        drawRSSI(item.position);
      };

      grid.appendChild(cell);
    });
  });

// ===============================
// RSSI Chart
// ===============================
let chart;

function drawRSSI(position) {
  fetch(`/rssi/${position}`)
    .then(res => {
      if (!res.ok) throw new Error("No RSSI data");
      return res.json();
    })
    .then(data => {
      if (!data.rssi || data.rssi.length === 0) return;

      const canvas = document.getElementById("rssiChart");
      const ctx = canvas.getContext("2d");

      if (chart) chart.destroy();

      chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: data.rssi.map((_, i) => i + 1),
          datasets: [{
            label: "RSSI (dBm)",
            data: data.rssi,
            borderColor: "#ff5252",
            backgroundColor: "rgba(255, 82, 82, 0.2)",
            tension: 0.3,
            fill: true
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { labels: { color: "#eee", font: { family: "'Inter', sans-serif" } } }
          },
          scales: {
            y: {
              title: {
                display: true,
                text: "Signal Strength (dBm)",
                color: "#eee",
                font: { family: "'Inter', sans-serif" }
              },
              grid: { color: "rgba(255,255,255,0.1)" },
              ticks: { color: "#ccc", font: { family: "'JetBrains Mono', monospace" } }
            },
            x: {
              title: {
                display: true,
                text: "Samples",
                color: "#eee",
                font: { family: "'Inter', sans-serif" }
              },
              grid: { display: false },
              ticks: { color: "#ccc", font: { family: "'JetBrains Mono', monospace" } }
            }
          }
        }
      });
    })
    .catch(() => {});
}

// ===============================
// Event Handlers
// ===============================
document.getElementById("resetBtn").onclick = () => {
  fetch("/reset", { method: "POST" })
    .then(res => res.json())
    .then(() => {
      document.getElementById("grid").innerHTML = "";
      document.getElementById("details").innerHTML =
        "<p>Select a cell to view details</p>";
      if (chart) {
        chart.destroy();
        chart = null;
      }
      location.reload();
    });
};

document.getElementById("reportBtn").onclick = () => {
  window.open("/report", "_blank");
};