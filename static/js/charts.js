document.addEventListener("DOMContentLoaded", () => {
  if (!window.modelEvaluation || typeof Chart === "undefined") return;
  const palette = ["#2777c8", "#33a58a", "#8b77c7"];
  const models = Object.entries(window.modelEvaluation.comparison);
  const comparison = document.getElementById("comparison-chart");
  if (comparison) {
    new Chart(comparison, {
      type: "bar",
      data: {
        labels: models.map(([name]) => name),
        datasets: [{
          label: "Mean recall",
          data: models.map(([, result]) => result.mean_recall),
          backgroundColor: models.map((_, index) => palette[index % palette.length]),
          borderRadius: 7,
          maxBarThickness: 54
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 1, title: { display: true, text: "Recall (0–1)" } },
          x: { grid: { display: false } }
        },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `Mean recall: ${context.parsed.y.toFixed(3)}` } } }
      }
    });
  }
  const confusion = document.getElementById("confusion-chart");
  const matrix = window.modelEvaluation.confusion;
  if (confusion && matrix && matrix.length === 2) {
    new Chart(confusion, {
      type: "bar",
      data: {
        labels: ["Actual class 0", "Actual class 1"],
        datasets: [
          { label: "Predicted 0", data: [matrix[0][0], matrix[1][0]], backgroundColor: "#2777c8", borderRadius: 5 },
          { label: "Predicted 1", data: [matrix[0][1], matrix[1][1]], backgroundColor: "#ee9b51", borderRadius: 5 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 }, title: { display: true, text: "Records" } } },
        plugins: { legend: { position: "bottom" } }
      }
    });
  }
});
