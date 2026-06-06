(function () {
  const themeChoiceKey = "weebarr-theme-choice";
  const legacyThemeChoiceKey = "weebarr-theme";
  const prefersLight = window.matchMedia("(prefers-color-scheme: light)");
  const state = {
    context: window.WEEBARR_THEME_CONTEXT || {
      activeThemeId: "neon-lights",
      themes: [],
    },
  };

  function readThemeChoice() {
    return (
      localStorage.getItem(themeChoiceKey) ||
      localStorage.getItem(legacyThemeChoiceKey) ||
      "dark"
    );
  }

  function writeThemeChoice(choice) {
    localStorage.setItem(themeChoiceKey, choice);
    localStorage.setItem(legacyThemeChoiceKey, choice);
  }

  function resolveMode(choice) {
    if (choice === "system") {
      return prefersLight.matches ? "light" : "dark";
    }
    return choice;
  }

  function hexToRgba(value, alpha = 1) {
    const normalized = String(value || "").replace("#", "").trim();
    if (![6, 8].includes(normalized.length)) {
      return value;
    }
    const channels =
      normalized.length === 8
        ? [
            Number.parseInt(normalized.slice(0, 2), 16),
            Number.parseInt(normalized.slice(2, 4), 16),
            Number.parseInt(normalized.slice(4, 6), 16),
            Number.parseInt(normalized.slice(6, 8), 16) / 255,
          ]
        : [
            Number.parseInt(normalized.slice(0, 2), 16),
            Number.parseInt(normalized.slice(2, 4), 16),
            Number.parseInt(normalized.slice(4, 6), 16),
            1,
          ];
    return `rgba(${channels[0]}, ${channels[1]}, ${channels[2]}, ${Math.max(
      0,
      Math.min(1, channels[3] * alpha),
    )})`;
  }

  function withAlpha(value, alpha) {
    return hexToRgba(value, alpha);
  }

  function derivedThemeVariables(tokens) {
    return {
      "--bg": tokens.bg,
      "--bg-2": tokens.bg2,
      "--page-tail": tokens.pageTail,
      "--page-glow-a": tokens.pageGlowA,
      "--page-glow-b": tokens.pageGlowB,
      "--page-glow-c": tokens.pageGlowC,
      "--panel": tokens.panel,
      "--panel-2": tokens.panel2,
      "--panel-3": tokens.panel3,
      "--media-scrim": tokens.mediaScrim,
      "--line": tokens.line,
      "--line-strong": tokens.lineStrong,
      "--text": tokens.text,
      "--muted": tokens.muted,
      "--subtle": tokens.subtle,
      "--cyan": tokens.cyan,
      "--pink": tokens.pink,
      "--purple": tokens.purple,
      "--green": tokens.green,
      "--warning": tokens.warning,
      "--hover-gradient": `linear-gradient(135deg, ${withAlpha(
        tokens.cyan,
        0.92,
      )}, ${withAlpha(tokens.purple, 0.78)} 50%, ${withAlpha(
        tokens.pink,
        0.92,
      )})`,
      "--hover-fill": `linear-gradient(145deg, ${withAlpha(
        tokens.cyan,
        0.08,
      )}, ${withAlpha(tokens.purple, 0.04)} 48%, ${withAlpha(
        tokens.pink,
        0.08,
      )})`,
      "--hover-glow": `0 18px 42px ${withAlpha(
        tokens.cyan,
        0.16,
      )}, 0 22px 48px ${withAlpha(tokens.pink, 0.12)}`,
      "--cyan-08": withAlpha(tokens.cyan, 0.08),
      "--cyan-10": withAlpha(tokens.cyan, 0.1),
      "--cyan-12": withAlpha(tokens.cyan, 0.12),
      "--cyan-18": withAlpha(tokens.cyan, 0.18),
      "--cyan-24": withAlpha(tokens.cyan, 0.24),
      "--cyan-42": withAlpha(tokens.cyan, 0.42),
      "--cyan-58": withAlpha(tokens.cyan, 0.58),
      "--cyan-64": withAlpha(tokens.cyan, 0.64),
      "--pink-08": withAlpha(tokens.pink, 0.08),
      "--pink-09": withAlpha(tokens.pink, 0.09),
      "--pink-10": withAlpha(tokens.pink, 0.1),
      "--pink-12": withAlpha(tokens.pink, 0.12),
      "--pink-15": withAlpha(tokens.pink, 0.15),
      "--pink-18": withAlpha(tokens.pink, 0.18),
      "--pink-22": withAlpha(tokens.pink, 0.22),
      "--pink-42": withAlpha(tokens.pink, 0.42),
      "--pink-46": withAlpha(tokens.pink, 0.46),
      "--pink-64": withAlpha(tokens.pink, 0.64),
      "--purple-08": withAlpha(tokens.purple, 0.08),
      "--purple-10": withAlpha(tokens.purple, 0.1),
      "--purple-11": withAlpha(tokens.purple, 0.11),
      "--purple-22": withAlpha(tokens.purple, 0.22),
      "--purple-42": withAlpha(tokens.purple, 0.42),
      "--purple-46": withAlpha(tokens.purple, 0.46),
      "--purple-64": withAlpha(tokens.purple, 0.64),
      "--green-09": withAlpha(tokens.green, 0.09),
      "--green-10": withAlpha(tokens.green, 0.1),
      "--green-11": withAlpha(tokens.green, 0.11),
      "--green-12": withAlpha(tokens.green, 0.12),
      "--warning-10": withAlpha(tokens.warning, 0.1),
      "--warning-11": withAlpha(tokens.warning, 0.11),
      "--warning-12": withAlpha(tokens.warning, 0.12),
    };
  }

  function activeTheme(context) {
    const themes = Array.isArray(context?.themes) ? context.themes : [];
    return (
      themes.find((theme) => theme.id === context?.activeThemeId) ||
      themes[0] || {
        id: "neon-lights",
        name: "Neon Lights",
        tokens: { dark: {}, light: {} },
      }
    );
  }

  function applyThemeTokens(tokens) {
    Object.entries(derivedThemeVariables(tokens)).forEach(([key, value]) => {
      document.documentElement.style.setProperty(key, value);
    });
  }

  function applyThemeChoice(choice = readThemeChoice(), context = state.context) {
    state.context = context || state.context;
    const resolved = resolveMode(choice);
    const theme = activeTheme(state.context);
    const tokens =
      theme.tokens?.[resolved] || theme.tokens?.dark || theme.tokens?.light || {};
    document.body.dataset.theme = resolved;
    document.body.dataset.themeChoice = choice;
    document.body.dataset.themePalette = theme.id || "neon-lights";
    writeThemeChoice(choice);
    applyThemeTokens(tokens);
    document.querySelectorAll("[data-theme-choice]").forEach((button) => {
      button.classList.toggle("active", button.dataset.themeChoice === choice);
    });
    document.dispatchEvent(
      new CustomEvent("weebarr:theme-applied", {
        detail: {
          choice,
          resolved,
          theme,
        },
      }),
    );
  }

  function setThemeContext(context) {
    state.context = context || state.context;
    applyThemeChoice(readThemeChoice(), state.context);
  }

  function bindThemeButtons(scope = document) {
    scope.querySelectorAll("[data-theme-choice]").forEach((button) => {
      button.addEventListener("click", () => {
        applyThemeChoice(button.dataset.themeChoice || "dark");
      });
    });
  }

  prefersLight.addEventListener("change", () => {
    if (readThemeChoice() === "system") {
      applyThemeChoice("system");
    }
  });

  window.WeebarrTheme = {
    activeTheme: () => activeTheme(state.context),
    applyThemeChoice,
    bindThemeButtons,
    readThemeChoice,
    resolveMode,
    setThemeContext,
  };

  if (document.body) {
    applyThemeChoice(readThemeChoice(), state.context);
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      applyThemeChoice(readThemeChoice(), state.context);
    });
  }
})();
