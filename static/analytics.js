// ============================================================
// SECUREVOICEAI - INTERACTIVE ANALYTICS DASHBOARD
// ============================================================

// Store chart instances
let authenticationChart = null;
let activityChart = null;
let similarityChart = null;


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
                        "#22c55e",
                        "#ef4444"
                    ],

                    borderWidth: 0,

                    hoverOffset: 10

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom"
                    }

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

                        borderColor: "#22c55e",

                        backgroundColor: "rgba(34, 197, 94, 0.15)",

                        tension: 0.4,

                        fill: true
                    },

                    {
                        label: "Failed",

                        data: failedData,

                        borderColor: "#ef4444",

                        backgroundColor: "rgba(239, 68, 68, 0.15)",

                        tension: 0.4,

                        fill: true
                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom"
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        ticks: {
                            precision: 0
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

                    backgroundColor: [
                        "#ef4444",
                        "#f97316",
                        "#eab308",
                        "#26c6da",
                        "#8b7cff",
                        "#22c55e"
                    ],

                    borderRadius: 6

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        ticks: {
                            precision: 0
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