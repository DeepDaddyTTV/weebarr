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

  function ensureTooltipLayer() {
    let layer = document.querySelector("#appTooltip");
    if (!layer) {
      layer = document.createElement("div");
      layer.id = "appTooltip";
      layer.className = "app-tooltip";
      layer.setAttribute("role", "tooltip");
      document.body.appendChild(layer);
    }
    return layer;
  }

  function tooltipAnchors() {
    return document.querySelectorAll(".tooltip-anchor[data-tooltip]");
  }

  function positionTooltip(layer, anchor) {
    const rect = anchor.getBoundingClientRect();
    layer.style.left = "0px";
    layer.style.top = "0px";
    const layerRect = layer.getBoundingClientRect();
    const viewportPadding = 16;
    const maxLeft = Math.max(
      viewportPadding,
      window.innerWidth - layerRect.width - viewportPadding,
    );
    const centeredLeft = rect.left + rect.width / 2 - layerRect.width / 2;
    const left = Math.min(Math.max(centeredLeft, viewportPadding), maxLeft);
    let top = rect.bottom + 10;
    let placement = "below";
    if (top + layerRect.height > window.innerHeight - viewportPadding) {
      top = Math.max(viewportPadding, rect.top - layerRect.height - 10);
      placement = "above";
    }
    layer.dataset.placement = placement;
    layer.style.left = `${Math.round(left)}px`;
    layer.style.top = `${Math.round(top)}px`;
  }

  function bindTooltips() {
    if (!document.body) return;
    document.documentElement.classList.add("js-tooltip-ready");
    const layer = ensureTooltipLayer();
    let activeAnchor = null;

    const showTooltip = (anchor) => {
      const text = anchor?.dataset?.tooltip?.trim();
      if (!text) return;
      activeAnchor = anchor;
      layer.textContent = text;
      layer.classList.add("visible");
      positionTooltip(layer, anchor);
    };

    const hideTooltip = () => {
      activeAnchor = null;
      layer.classList.remove("visible");
      layer.textContent = "";
      delete layer.dataset.placement;
    };

    document.addEventListener("mouseover", (event) => {
      const anchor = event.target.closest(".tooltip-anchor[data-tooltip]");
      if (!anchor) {
        if (!event.relatedTarget?.closest?.(".tooltip-anchor[data-tooltip]")) {
          hideTooltip();
        }
        return;
      }
      if (anchor !== activeAnchor) {
        showTooltip(anchor);
      } else {
        positionTooltip(layer, anchor);
      }
    });

    document.addEventListener("mouseout", (event) => {
      const anchor = event.target.closest(".tooltip-anchor[data-tooltip]");
      if (!anchor) return;
      if (event.relatedTarget?.closest?.(".tooltip-anchor[data-tooltip]") === anchor) {
        return;
      }
      hideTooltip();
    });

    document.addEventListener("focusin", (event) => {
      const anchor = event.target.closest(".tooltip-anchor[data-tooltip]");
      if (anchor) showTooltip(anchor);
    });

    document.addEventListener("focusout", (event) => {
      const anchor = event.target.closest(".tooltip-anchor[data-tooltip]");
      if (!anchor) return;
      if (event.relatedTarget?.closest?.(".tooltip-anchor[data-tooltip]") === anchor) {
        return;
      }
      hideTooltip();
    });

    window.addEventListener(
      "scroll",
      () => {
        if (activeAnchor) {
          positionTooltip(layer, activeAnchor);
        }
      },
      true,
    );
    window.addEventListener("resize", () => {
      if (activeAnchor) {
        positionTooltip(layer, activeAnchor);
      }
    });

    tooltipAnchors().forEach((anchor) => {
      if (!anchor.hasAttribute("tabindex")) {
        anchor.tabIndex = 0;
      }
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
    bindTooltips();
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      applyThemeChoice(readThemeChoice(), state.context);
      bindTooltips();
    });
  }
})();
