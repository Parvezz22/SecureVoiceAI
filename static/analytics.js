// ============================================================
// SECUREVOICEAI - INTERACTIVE ANALYTICS DASHBOARD
// ============================================================

// Store chart instances
let authenticationChart = null;
let activityChart = null;
let similarityChart = null;


// ============================================================
// THEME-AWARE CHART PALETTE
// Returns the correct colors based on the active data-theme.
// ============================================================

function getChartTheme() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    return {
        isLight,
        mutedColor:   isLight ? "#475569"                   : "#94a3b8",
        gridColor:    isLight ? "rgba(148, 163, 184, 0.18)" : "rgba(255, 255, 255, 0.05)",
        tooltipBg:    isLight ? "rgba(255, 255, 255, 0.97)" : "rgba(10, 16, 30, 0.95)",
        tooltipTitle: isLight ? "#0f172a"                   : "#ffffff",
        tooltipBody:  isLight ? "#334155"                   : "#cbd5e1",
        tooltipBorder:isLight ? "rgba(14, 165, 233, 0.3)"  : "rgba(56, 189, 248, 0.25)",
        // Doughnut / line point border matches card bg
        borderColor:  isLight ? "#ffffff"                   : "#0c1222",
    };
}


// ============================================================
// COMMON CHART SETTINGS
// ============================================================

const chartFontFamily = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

function buildTooltipOptions(t) {
    return {
        backgroundColor: t.tooltipBg,
        titleColor:      t.tooltipTitle,
        bodyColor:       t.tooltipBody,
        borderColor:     t.tooltipBorder,
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        titleFont: { family: chartFontFamily, size: 12, weight: "600" },
        bodyFont:  { family: chartFontFamily, size: 12 }
    };
}

function buildLegendOptions(t) {
    return {
        position: "bottom",
        labels: {
            color: t.mutedColor,
            font: { family: chartFontFamily, size: 12 },
            padding: 16,
            boxWidth: 12,
            usePointStyle: true
        }
    };
}


// ============================================================
// APPLY THEME TO EXISTING CHARTS (without re-fetching data)
// ============================================================

function applyChartTheme() {
    const t = getChartTheme();

    // Helper: update a legend's label color
    function refreshLegend(chart) {
        if (!chart || !chart.options.plugins.legend) return;
        chart.options.plugins.legend.labels.color = t.mutedColor;
    }

    // Helper: update tooltip options on a chart
    function refreshTooltip(chart) {
        if (!chart || !chart.options.plugins.tooltip) return;
        Object.assign(chart.options.plugins.tooltip, buildTooltipOptions(t));
    }

    // Helper: update a single scale's grid + tick colors
    function refreshScale(scale) {
        if (!scale) return;
        if (scale.grid) scale.grid.color = t.gridColor;
        if (scale.ticks) scale.ticks.color = t.mutedColor;
    }

    // ── Authentication doughnut ──────────────────────────────
    if (authenticationChart) {
        authenticationChart.data.datasets[0].borderColor = t.borderColor;
        refreshLegend(authenticationChart);
        refreshTooltip(authenticationChart);
        authenticationChart.update("none");
    }

    // ── Daily activity line chart ────────────────────────────
    if (activityChart) {
        // Update point border colors to match card background
        activityChart.data.datasets.forEach(function (ds) {
            ds.pointBorderColor = t.borderColor;
        });
        refreshLegend(activityChart);
        refreshTooltip(activityChart);
        refreshScale(activityChart.options.scales.x);
        refreshScale(activityChart.options.scales.y);
        activityChart.update("none");
    }

    // ── Similarity score bar chart ───────────────────────────
    if (similarityChart) {
        refreshTooltip(similarityChart);
        refreshScale(similarityChart.options.scales.x);
        refreshScale(similarityChart.options.scales.y);
        similarityChart.update("none");
    }
}


// ============================================================
// LOAD ANALYTICS DATA
// ============================================================

async function loadAnalytics() {

    try {

        const response = await fetch("/analytics-data");

        if (!response.ok) {
            throw new Error("Unable to fetch analytics data.");
        }

        const data = await response.json();

        const summary = data.summary;

        // Extract values safely
        const totalAttempts = summary.total_attempts || 0;
        const successful = summary.successful_attempts || 0;
        const failed = summary.failed_attempts || 0;

        const averageSimilarity =
            summary.average_similarity ?? 0;

        const averageProcessingTime =
            summary.average_processing_time ?? 0;


        // ====================================================
        // UPDATE ANALYTICS SUMMARY CARDS
        // ====================================================

        const successRate = totalAttempts > 0
            ? (successful / totalAttempts) * 100
            : 0;

        document.getElementById("successRate").textContent =
            successRate.toFixed(2) + "%";

        document.getElementById("averageSimilarity").textContent =
            Number(averageSimilarity).toFixed(3);

        document.getElementById("averageProcessingTime").textContent =
            Number(averageProcessingTime).toFixed(2) + " sec";


        // Capture theme at render time
        const t = getChartTheme();


        // ====================================================
        // CHART 1: SUCCESSFUL VS FAILED AUTHENTICATION
        // ====================================================

        const authenticationCanvas =
            document.getElementById("authenticationChart");

        if (authenticationChart) {
            authenticationChart.destroy();
        }

        authenticationChart = new Chart(authenticationCanvas, {

            type: "doughnut",

            data: {

                labels: [
                    "Successful",
                    "Failed"
                ],

                datasets: [{

                    data: [
                        successful,
                        failed
                    ],

                    backgroundColor: [
                        "#10b981",
                        "#f43f5e"
                    ],

                    borderColor: t.borderColor,

                    borderWidth: 2,

                    hoverOffset: 8

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: buildLegendOptions(t),

                    tooltip: buildTooltipOptions(t)

                }

            }

        });


        // ====================================================
        // CHART 2: DAILY AUTHENTICATION TRENDS
        // ====================================================

        const dailyData = data.daily_activity || [];

        // Create a map of the returned database records
        const dailyMap = {};

        dailyData.forEach(function (item) {

            dailyMap[item.activity_date] = item;

        });


        // Generate the last seven calendar days
        const labels = [];
        const successData = [];
        const failedData = [];

        for (let i = 6; i >= 0; i--) {

            const date = new Date();

            date.setDate(date.getDate() - i);

            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const day = String(date.getDate()).padStart(2, "0");

            const dateKey = `${year}-${month}-${day}`;

            labels.push(
                date.toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short"
                })
            );

            const record = dailyMap[dateKey];

            successData.push(
                record ? record.successful : 0
            );

            failedData.push(
                record ? record.failed : 0
            );

        }


        const activityCanvas =
            document.getElementById("activityChart");

        if (activityChart) {
            activityChart.destroy();
        }

        activityChart = new Chart(activityCanvas, {

            type: "line",

            data: {

                labels: labels,

                datasets: [

                    {
                        label: "Successful",

                        data: successData,

                        borderColor: "#10b981",

                        backgroundColor: "rgba(16, 185, 129, 0.12)",

                        pointBackgroundColor: "#10b981",

                        pointBorderColor: t.borderColor,

                        pointHoverRadius: 5,

                        tension: 0.35,

                        fill: true
                    },

                    {
                        label: "Failed",

                        data: failedData,

                        borderColor: "#f43f5e",

                        backgroundColor: "rgba(244, 63, 94, 0.12)",

                        pointBackgroundColor: "#f43f5e",

                        pointBorderColor: t.borderColor,

                        pointHoverRadius: 5,

                        tension: 0.35,

                        fill: true
                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: buildLegendOptions(t),

                    tooltip: buildTooltipOptions(t)

                },

                scales: {

                    x: {
                        grid: {
                            color: t.gridColor,
                            drawBorder: false
                        },
                        ticks: {
                            color: t.mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }
                    },

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: t.gridColor,
                            drawBorder: false
                        },

                        ticks: {
                            precision: 0,
                            color: t.mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }

                    }

                }

            }

        });


        // ====================================================
        // CHART 3: SIMILARITY SCORE DISTRIBUTION
        // ====================================================

        const scoreData = data.score_distribution || [];

        const similarityLabels = scoreData.map(
            item => item.score_range
        );

        const similarityValues = scoreData.map(
            item => item.total
        );

        // Cyber security gradient ramp for score buckets
        const scoreColors = [
            "#e11d48", // Below 0.0 (Deep red)
            "#f43f5e", // 0.0 - 0.2 (Rose)
            "#f59e0b", // 0.2 - 0.4 (Amber)
            "#0284c7", // 0.4 - 0.6 (Sky)
            "#06b6d4", // 0.6 - 0.8 (Cyan - Threshold band)
            "#10b981"  // 0.8 - 1.0 (Emerald - High match)
        ];

        const similarityCanvas =
            document.getElementById("similarityChart");

        if (similarityChart) {
            similarityChart.destroy();
        }

        similarityChart = new Chart(similarityCanvas, {

            type: "bar",

            data: {

                labels: similarityLabels,

                datasets: [{

                    label: "Authentication Attempts",

                    data: similarityValues,

                    backgroundColor: scoreColors.slice(0, similarityLabels.length),

                    borderRadius: 6

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: buildTooltipOptions(t)

                },

                scales: {

                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: t.mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }
                    },

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: t.gridColor,
                            drawBorder: false
                        },

                        ticks: {
                            precision: 0,
                            color: t.mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }

                    }

                }

            }

        });


        console.log("Analytics dashboard loaded successfully.");

    }

    catch (error) {

        console.error("Analytics Error:", error);

    }

}


// ============================================================
// LOAD ANALYTICS WHEN PAGE OPENS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    loadAnalytics
);


// ============================================================
// REACT TO THEME CHANGES (without re-fetching data)
// ============================================================

document.addEventListener("themechange", function () {
    applyChartTheme();
});


// ============================================================
// LOAD ANALYTICS DATA
// ============================================================

async function loadAnalytics() {

    try {

        const response = await fetch("/analytics-data");

        if (!response.ok) {
            throw new Error("Unable to fetch analytics data.");
        }

        const data = await response.json();

        const summary = data.summary;

        // Extract values safely
        const totalAttempts = summary.total_attempts || 0;
        const successful = summary.successful_attempts || 0;
        const failed = summary.failed_attempts || 0;

        const averageSimilarity =
            summary.average_similarity ?? 0;

        const averageProcessingTime =
            summary.average_processing_time ?? 0;


        // ====================================================
        // UPDATE ANALYTICS SUMMARY CARDS
        // ====================================================

        const successRate = totalAttempts > 0
            ? (successful / totalAttempts) * 100
            : 0;

        document.getElementById("successRate").textContent =
            successRate.toFixed(2) + "%";

        document.getElementById("averageSimilarity").textContent =
            Number(averageSimilarity).toFixed(3);

        document.getElementById("averageProcessingTime").textContent =
            Number(averageProcessingTime).toFixed(2) + " sec";


        // ====================================================
        // CHART 1: SUCCESSFUL VS FAILED AUTHENTICATION
        // ====================================================

        const authenticationCanvas =
            document.getElementById("authenticationChart");

        if (authenticationChart) {
            authenticationChart.destroy();
        }

        authenticationChart = new Chart(authenticationCanvas, {

            type: "doughnut",

            data: {

                labels: [
                    "Successful",
                    "Failed"
                ],

                datasets: [{

                    data: [
                        successful,
                        failed
                    ],

                    backgroundColor: [
                        "#10b981",
                        "#f43f5e"
                    ],

                    borderColor: "#0c1222",

                    borderWidth: 2,

                    hoverOffset: 8

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom",
                        labels: {
                            color: getChartTheme().mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 12
                            },
                            padding: 16,
                            boxWidth: 12,
                            usePointStyle: true
                        }
                    },

                    tooltip: buildTooltipOptions(getChartTheme())

                }

            }

        });


        // ====================================================
        // CHART 2: DAILY AUTHENTICATION TRENDS
        // ====================================================

        const dailyData = data.daily_activity || [];

        // Create a map of the returned database records
        const dailyMap = {};

        dailyData.forEach(function (item) {

            dailyMap[item.activity_date] = item;

        });


        // Generate the last seven calendar days
        const labels = [];
        const successData = [];
        const failedData = [];

        for (let i = 6; i >= 0; i--) {

            const date = new Date();

            date.setDate(date.getDate() - i);

            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const day = String(date.getDate()).padStart(2, "0");

            const dateKey = `${year}-${month}-${day}`;

            labels.push(
                date.toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short"
                })
            );

            const record = dailyMap[dateKey];

            successData.push(
                record ? record.successful : 0
            );

            failedData.push(
                record ? record.failed : 0
            );

        }


        const activityCanvas =
            document.getElementById("activityChart");

        if (activityChart) {
            activityChart.destroy();
        }

        activityChart = new Chart(activityCanvas, {

            type: "line",

            data: {

                labels: labels,

                datasets: [

                    {
                        label: "Successful",

                        data: successData,

                        borderColor: "#10b981",

                        backgroundColor: "rgba(16, 185, 129, 0.12)",

                        pointBackgroundColor: "#10b981",

                        pointBorderColor: "#0c1222",

                        pointHoverRadius: 5,

                        tension: 0.35,

                        fill: true
                    },

                    {
                        label: "Failed",

                        data: failedData,

                        borderColor: "#f43f5e",

                        backgroundColor: "rgba(244, 63, 94, 0.12)",

                        pointBackgroundColor: "#f43f5e",

                        pointBorderColor: "#0c1222",

                        pointHoverRadius: 5,

                        tension: 0.35,

                        fill: true
                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom",
                        labels: {
                            color: getChartTheme().mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 12
                            },
                            padding: 16,
                            boxWidth: 12,
                            usePointStyle: true
                        }
                    },

                    tooltip: buildTooltipOptions(getChartTheme())

                },

                scales: {

                    x: {
                        grid: {
                            color: getChartTheme().gridColor,
                            drawBorder: false
                        },
                        ticks: {
                            color: getChartTheme().mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }
                    },

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: getChartTheme().gridColor,
                            drawBorder: false
                        },

                        ticks: {
                            precision: 0,
                            color: getChartTheme().mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }

                    }

                }

            }

        });


        // ====================================================
        // CHART 3: SIMILARITY SCORE DISTRIBUTION
        // ====================================================

        const scoreData = data.score_distribution || [];

        const similarityLabels = scoreData.map(
            item => item.score_range
        );

        const similarityValues = scoreData.map(
            item => item.total
        );

        // Cyber security gradient ramp for score buckets
        const scoreColors = [
            "#e11d48", // Below 0.0 (Deep red)
            "#f43f5e", // 0.0 - 0.2 (Rose)
            "#f59e0b", // 0.2 - 0.4 (Amber)
            "#0284c7", // 0.4 - 0.6 (Sky)
            "#06b6d4", // 0.6 - 0.8 (Cyan - Threshold band)
            "#10b981"  // 0.8 - 1.0 (Emerald - High match)
        ];

        const similarityCanvas =
            document.getElementById("similarityChart");

        if (similarityChart) {
            similarityChart.destroy();
        }

        similarityChart = new Chart(similarityCanvas, {

            type: "bar",

            data: {

                labels: similarityLabels,

                datasets: [{

                    label: "Authentication Attempts",

                    data: similarityValues,

                    backgroundColor: scoreColors.slice(0, similarityLabels.length),

                    borderRadius: 6

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: buildTooltipOptions(getChartTheme())

                },

                scales: {

                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getChartTheme().mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }
                    },

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: getChartTheme().gridColor,
                            drawBorder: false
                        },

                        ticks: {
                            precision: 0,
                            color: getChartTheme().mutedColor,
                            font: {
                                family: chartFontFamily,
                                size: 11
                            }
                        }

                    }

                }

            }

        });


        console.log("Analytics dashboard loaded successfully.");

    }

    catch (error) {

        console.error("Analytics Error:", error);

    }

}


// ============================================================
// LOAD ANALYTICS WHEN PAGE OPENS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    loadAnalytics
);
