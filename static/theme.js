/**
 * SecureVoiceAI - Theme Manager (static/theme.js)
 *
 * Reusable vanilla JavaScript dark/light theme manager with:
 * - LocalStorage persistence with graceful fallback
 * - Immediate root attribute synchronization (data-theme)
 * - Accessible multi-button toggle control binding (aria-label, aria-pressed, title)
 * - Custom "themechange" event dispatching for dynamic components
 * - Cross-tab theme synchronization via storage events
 */
(function (global) {
  "use strict";

  const STORAGE_KEY = "securevoice_theme";
  const THEME_DARK = "dark";
  const THEME_LIGHT = "light";
  const DEFAULT_THEME = THEME_DARK;

  // In-memory fallback in case localStorage is disabled or restricted
  let inMemoryTheme = null;

  /**
   * Safely retrieve the stored theme preference from localStorage.
   * @returns {string|null} "dark", "light", or null if unavailable/invalid.
   */
  function getStoredTheme() {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        if (stored === THEME_DARK || stored === THEME_LIGHT) {
          return stored;
        }
      }
    } catch (err) {
      // Storage access blocked or restricted (e.g. private mode, cookies disabled)
      console.warn("SecureVoiceAI: LocalStorage read unavailable, using fallback.", err);
    }
    return inMemoryTheme;
  }

  /**
   * Safely store the theme preference in localStorage.
   * @param {string} theme - "dark" or "light".
   */
  function setStoredTheme(theme) {
    inMemoryTheme = theme;
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem(STORAGE_KEY, theme);
      }
    } catch (err) {
      // Storage quota exceeded or storage blocked
      console.warn("SecureVoiceAI: LocalStorage write unavailable, using in-memory state.", err);
    }
  }

  /**
   * Determine the effective theme preference (stored value or default).
   * @returns {string} "dark" or "light".
   */
  function getPreferredTheme() {
    const stored = getStoredTheme();
    if (stored === THEME_DARK || stored === THEME_LIGHT) {
      return stored;
    }
    return DEFAULT_THEME;
  }

  /**
   * Get the currently active theme from the DOM root attribute.
   * @returns {string} Current active theme ("dark" or "light").
   */
  function getCurrentTheme() {
    if (typeof document !== "undefined" && document.documentElement) {
      const active = document.documentElement.getAttribute("data-theme");
      if (active === THEME_DARK || active === THEME_LIGHT) {
        return active;
      }
    }
    return getPreferredTheme();
  }

  /**
   * Update visual and accessibility attributes on all theme toggle buttons on the page.
   * @param {string} theme - Active theme ("dark" or "light").
   */
  function updateToggleButtons(theme) {
    if (typeof document === "undefined") return;

    const isLight = theme === THEME_LIGHT;
    const buttons = document.querySelectorAll(".theme-toggle-btn, [data-theme-toggle]");

    buttons.forEach(function (button) {
      button.setAttribute("aria-pressed", isLight ? "true" : "false");
      button.setAttribute(
        "aria-label",
        isLight ? "Switch to dark mode" : "Switch to light mode"
      );
      button.setAttribute(
        "title",
        isLight ? "Switch to dark mode" : "Switch to light mode"
      );

      // Update inner icon if present
      const icon = button.querySelector(".theme-icon");
      if (icon) {
        icon.textContent = isLight ? "🌙" : "☀️";
      }

      // Update inner text label if present
      const label = button.querySelector(".theme-label");
      if (label) {
        label.textContent = isLight ? "Dark Mode" : "Light Mode";
      }
    });
  }

  /**
   * Dispatch custom "themechange" event for subscribers (e.g. Chart.js color adapters).
   * Dispatched once on document with bubbles: true, allowing normal event bubbling to window.
   * @param {string} theme - Newly applied theme.
   */
  function dispatchThemeChangeEvent(theme) {
    if (typeof document === "undefined" || typeof CustomEvent === "undefined") return;

    const event = new CustomEvent("themechange", {
      detail: { theme: theme },
      bubbles: true,
      cancelable: false
    });

    document.dispatchEvent(event);
  }

  /**
   * Apply a theme to the document and notify all components.
   * @param {string} theme - "dark" or "light".
   * @returns {string} The applied theme.
   */
  function applyTheme(theme) {
    const validTheme = theme === THEME_LIGHT ? THEME_LIGHT : THEME_DARK;

    if (typeof document !== "undefined" && document.documentElement) {
      document.documentElement.setAttribute("data-theme", validTheme);
    }

    updateToggleButtons(validTheme);
    dispatchThemeChangeEvent(validTheme);

    return validTheme;
  }

  /**
   * Toggle between dark and light modes, persisting the choice.
   * @returns {string} The new active theme.
   */
  function toggleTheme() {
    const current = getCurrentTheme();
    const nextTheme = current === THEME_DARK ? THEME_LIGHT : THEME_DARK;

    setStoredTheme(nextTheme);
    applyTheme(nextTheme);

    return nextTheme;
  }

  /**
   * Attach event listeners to all theme toggle buttons on the page.
   * Safe to call multiple times without creating duplicate listeners.
   */
  function initToggleButtons() {
    if (typeof document === "undefined") return;

    const buttons = document.querySelectorAll(".theme-toggle-btn, [data-theme-toggle]");
    buttons.forEach(function (button) {
      if (!button.dataset.themeBound) {
        button.addEventListener("click", function (e) {
          e.preventDefault();
          toggleTheme();
        });
        button.dataset.themeBound = "true";
      }
    });

    updateToggleButtons(getCurrentTheme());
  }

  /**
   * Initialize the ThemeManager.
   * Applies the preferred theme immediately and binds toggle buttons when DOM is ready.
   */
  function init() {
    // 1. Immediately apply the saved or default theme to prevent theme flashing
    const theme = getPreferredTheme();
    applyTheme(theme);

    // 2. Bind toggle buttons once DOM is accessible
    if (typeof document !== "undefined") {
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
          initToggleButtons();
        });
      } else {
        initToggleButtons();
      }
    }

    // 3. Sync theme across browser tabs via storage event
    if (typeof window !== "undefined") {
      window.addEventListener("storage", function (e) {
        if (e.key === STORAGE_KEY && (e.newValue === THEME_DARK || e.newValue === THEME_LIGHT)) {
          applyTheme(e.newValue);
        }
      });
    }
  }

  // Public API object
  const ThemeManager = {
    STORAGE_KEY: STORAGE_KEY,
    THEME_DARK: THEME_DARK,
    THEME_LIGHT: THEME_LIGHT,
    DEFAULT_THEME: DEFAULT_THEME,
    getStoredTheme: getStoredTheme,
    setStoredTheme: setStoredTheme,
    getPreferredTheme: getPreferredTheme,
    getCurrentTheme: getCurrentTheme,
    applyTheme: applyTheme,
    toggleTheme: toggleTheme,
    updateToggleButtons: updateToggleButtons,
    initToggleButtons: initToggleButtons,
    init: init
  };

  // Expose to window/global scope
  global.ThemeManager = ThemeManager;

  // Auto-initialize immediately
  init();

})(typeof window !== "undefined" ? window : this);
