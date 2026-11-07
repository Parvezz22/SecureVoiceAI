/**
 * SecureVoiceAI - System Health Status Monitor
 * Dynamically queries the backend /health endpoint to reflect true operational state.
 */

(function () {
    "use strict";

    const HEALTH_ENDPOINT = "/health";
    const REFRESH_INTERVAL_MS = 30000; // 30 seconds
    const REQUEST_TIMEOUT_MS = 5000;   // 5 seconds timeout

    /**
     * Updates the status badge UI and accessibility attributes.
     * @param {HTMLElement} badge
     * @param {HTMLElement} textElem
     * @param {"online" | "warning" | "offline" | "loading"} state
     * @param {string} label
     */
    function updateBadgeState(badge, textElem, state, label) {
        badge.classList.remove(
            "status-badge--loading",
            "status-badge--online",
            "status-badge--warning",
            "status-badge--offline"
        );
        badge.classList.add(`status-badge--${state}`);
        textElem.textContent = label;
    }

    /**
     * Fetches /health and applies the interpreted state to the status badge.
     * The 5-second timeout covers the complete operation, including response parsing.
     */
    async function checkHealth() {
        const badge = document.getElementById("systemStatusBadge");
        const textElem = document.getElementById("systemStatusText");

        if (!badge || !textElem) {
            return;
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        try {
            const response = await fetch(HEALTH_ENDPOINT, {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                signal: controller.signal
            });

            if (!response.ok) {
                updateBadgeState(badge, textElem, "offline", "System Offline");
                return;
            }

            const data = await response.json();

            if (data && data.status === "healthy" && data.model_loaded === true) {
                updateBadgeState(badge, textElem, "online", "System Online");
            } else if (data && data.status === "healthy" && data.model_loaded === false) {
                updateBadgeState(badge, textElem, "warning", "Model Not Ready");
            } else {
                updateBadgeState(badge, textElem, "offline", "System Offline");
            }
        } catch (error) {
            updateBadgeState(badge, textElem, "offline", "System Offline");
        } finally {
            clearTimeout(timeoutId);
        }
    }

    /**
     * Initializes health check immediately on load and starts the recurring interval.
     */
    function initialize() {
        checkHealth();
        setInterval(checkHealth, REFRESH_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
