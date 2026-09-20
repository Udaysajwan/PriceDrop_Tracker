// Chart.js helper for rendering price trends vs target threshold

let priceChartInstance = null;

function renderPriceHistoryChart(canvasElement, historyData, targetPrice, currency = "₹") {
  if (priceChartInstance) {
    priceChartInstance.destroy();
  }

  const ctx = canvasElement.getContext("2d");

  // Sort history ascending by time
  const sorted = [...historyData].sort((a, b) => new Date(a.scraped_at) - new Date(b.scraped_at));

  const labels = sorted.map(item => {
    const d = new Date(item.scraped_at);
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  });

  const prices = sorted.map(item => item.price);
  const targetLine = sorted.map(() => targetPrice);

  priceChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Recorded Price",
          data: prices,
          borderColor: "#4f46e5",
          backgroundColor: "rgba(79, 70, 229, 0.08)",
          fill: true,
          tension: 0.25,
          pointBackgroundColor: "#4f46e5",
          pointRadius: 5,
          pointHoverRadius: 7,
          borderWidth: 2,
        },
        {
          label: `Target Price (${currency}${targetPrice})`,
          data: targetLine,
          borderColor: "#10b981",
          borderDash: [6, 6],
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index",
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
          labels: {
            font: {
              family: "system-ui, sans-serif",
              weight: "600",
            }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${currency}${context.parsed.y.toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function(value) {
              return currency + value;
            }
          },
          grid: {
            color: "rgba(226, 232, 240, 0.6)",
          }
        },
        x: {
          grid: {
            display: false,
          }
        }
      }
    }
  });

  return priceChartInstance;
}
