const state = {
  weebarr: window.WEEBARR_WEEBARR || {},
  connection: window.WEEBARR_CONNECTION || {},
  requestSettings: window.WEEBARR_REQUEST_SETTINGS || {},
  access: window.WEEBARR_ACCESS || {},
  openDropdown: null,
  activeTab: "weebarr",
  sonarrValidated: false,
  sonarrBaseUrlSuffix: "",
  sonarrOptions: {
    rootFolders: [],
    qualityProfiles: [],
    languageProfiles: [],
  },
};

const DEFAULT_SONARR_SCHEME = "http";
const DEFAULT_SONARR_PORT = "8989";

const validSettingsTabs = new Set([
  "weebarr",
  "automation",
  "authentication",
  "api",
  "connections",
]);

const contentFilterLabels = {
  hide_nsfw: "Hide NSFW",
  show_all: "Show all",
};

const requestBackendLabels = {
  seerr: "Seerr",
  sonarr: "Sonarr Direct",
};

const seriesTypeLabels = {
  default: "Use Seerr default",
  standard: "Standard",
  anime: "Anime / Absolute",
  daily: "Daily",
};

const colorPickerFields = [
  { key: "bg", label: "Background" },
  { key: "panel", label: "Panel" },
  { key: "text", label: "Text" },
  { key: "cyan", label: "Cyan Accent" },
  { key: "pink", label: "Pink Accent" },
  { key: "purple", label: "Purple Accent" },
  { key: "green", label: "Success Accent" },
];

const els = {
  toast: document.querySelector("#toast"),
  weebarrBanner: document.querySelector("#weebarrSettingsBanner"),
  automationBanner: document.querySelector("#automationSettingsBanner"),
  connectionBanner: document.querySelector("#settingsBanner"),
  accessBanner: document.querySelector("#accessSettingsBanner"),
  apiBanner: document.querySelector("#apiSettingsBanner"),
  connectionStatusPill: document.querySelector("#settingsStatusPill"),
  localAccountStatusPill: document.querySelector("#localAccountStatusPill"),
  apiKeyStatusPill: document.querySelector("#apiKeyStatusPill"),
  weebarrForm: document.querySelector("#weebarrForm"),
  automationForm: document.querySelector("#automationForm"),
  connectionForm: document.querySelector("#connectionForm"),
  accessForm: document.querySelector("#localAccountForm"),
  settingsTabs: document.querySelectorAll("[data-settings-tab]"),
  settingsPanels: document.querySelectorAll("[data-settings-panel]"),
  settingsShell: document.querySelector(".settings-shell"),
  settingsStack: document.querySelector(".settings-stack"),
  contentFilterMode: document.querySelector("#settingsContentFilterMode"),
  strictMonitoring: document.querySelector("#settingsStrictMonitoring"),
  activeThemeId: document.querySelector("#settingsActiveThemeId"),
  activeThemeDescription: document.querySelector("#activeThemeDescription"),
  colorPickerPanel: document.querySelector("#colorPickerPanel"),
  colorPickerGrid: document.querySelector("#colorPickerGrid"),
  themeImportUrl: document.querySelector("#themeImportUrl"),
  themeImportZip: document.querySelector("#themeImportZip"),
  themeImportZipPickBtn: document.querySelector("#themeImportZipPickBtn"),
  themeImportZipName: document.querySelector("#themeImportZipName"),
  importThemeUrlBtn: document.querySelector("#importThemeUrlBtn"),
  importThemeZipBtn: document.querySelector("#importThemeZipBtn"),
  automationBucketSTier: document.querySelector("#automationBucketSTier"),
  automationBucketCanon: document.querySelector("#automationBucketCanon"),
  automationBucketBingeable: document.querySelector("#automationBucketBingeable"),
  automationBucketFiller: document.querySelector("#automationBucketFiller"),
  automationScanIntervalDays: document.querySelector("#automationScanIntervalDays"),
  automationScanIntervalHours: document.querySelector("#automationScanIntervalHours"),
  automationScanNowBtn: document.querySelector("#automationScanNowBtn"),
  requestBackend: document.querySelector("#settingsRequestBackend"),
  seerrSettingsPanel: document.querySelector("#seerrSettingsPanel"),
  sonarrSettingsPanel: document.querySelector("#sonarrSettingsPanel"),
  sonarrValidationNote: document.querySelector("#sonarrSettingsValidationNote"),
  sonarrValidationCopy: document.querySelector("#sonarrSettingsValidationCopy"),
  sonarrAdvancedFields: document.querySelector("#sonarrSettingsAdvancedFields"),
  baseUrl: document.querySelector("#settingsBaseUrl"),
  apiKey: document.querySelector("#settingsApiKey"),
  requestSeasons: document.querySelector("#settingsRequestSeasons"),
  sonarrServerId: document.querySelector("#settingsSonarrServerId"),
  forceQualityProfile: document.querySelector("#settingsForceQualityProfile"),
  seriesType: document.querySelector("#settingsSeriesType"),
  profileId: document.querySelector("#settingsProfileId"),
  rootFolder: document.querySelector("#settingsRootFolder"),
  languageProfileId: document.querySelector("#settingsLanguageProfileId"),
  requestUserId: document.querySelector("#settingsRequestUserId"),
  tags: document.querySelector("#settingsTags"),
  sonarrScheme: document.querySelector("#sonarrScheme"),
  sonarrHost: document.querySelector("#sonarrHost"),
  sonarrPort: document.querySelector("#sonarrPort"),
  sonarrApiKey: document.querySelector("#sonarrApiKey"),
  sonarrRootFolderPath: document.querySelector("#sonarrRootFolderPath"),
  sonarrQualityProfileId: document.querySelector("#sonarrQualityProfileId"),
  sonarrSeriesType: document.querySelector("#sonarrSeriesType"),
  sonarrDefaultMonitorMode: document.querySelector("#sonarrDefaultMonitorMode"),
  sonarrDefaultSearchOnAdd: document.querySelector("#sonarrDefaultSearchOnAdd"),
  sonarrDefaultSeasonFolder: document.querySelector("#sonarrDefaultSeasonFolder"),
  sonarrLanguageProfileId: document.querySelector("#sonarrLanguageProfileId"),
  sonarrTags: document.querySelector("#sonarrTags"),
  sonarrValidateButton: document.querySelector("#sonarrValidateBtn"),
  localAccountUsername: document.querySelector("#localAccountUsername"),
  localAccountPassword: document.querySelector("#localAccountPassword"),
  localAccountConfirmPassword: document.querySelector(
    "#localAccountConfirmPassword",
  ),
  currentAuthSignIn: document.querySelector("#currentAuthSignIn"),
  currentAppApiKeyPreview: document.querySelector("#currentAppApiKeyPreview"),
  generatedAppApiKeyGroup: document.querySelector("#generatedAppApiKeyGroup"),
  generatedAppApiKey: document.querySelector("#generatedAppApiKey"),
  regenerateAppApiKeyBtn: document.querySelector("#regenerateAppApiKeyBtn"),
  copyAppApiKeyBtn: document.querySelector("#copyAppApiKeyBtn"),
  apiKeyEnabledSummary: document.querySelector("#apiKeyEnabledSummary"),
  apiKeyPreviewSummary: document.querySelector("#apiKeyPreviewSummary"),
  currentActiveTheme: document.querySelector("#currentActiveTheme"),
  currentContentFilter: document.querySelector("#currentContentFilter"),
  currentStrictMonitoring: document.querySelector("#currentStrictMonitoring"),
  automationEnabledBuckets: document.querySelector("#automationEnabledBuckets"),
  automationScanIntervalSummary: document.querySelector(
    "#automationScanIntervalSummary",
  ),
  automationLastScanAt: document.querySelector("#automationLastScanAt"),
  automationLastProcessed: document.querySelector("#automationLastProcessed"),
  currentBaseUrl: document.querySelector("#currentBaseUrl"),
  currentApiKey: document.querySelector("#currentApiKey"),
  currentRequestBackend: document.querySelector("#currentRequestBackend"),
  currentRequestSeasons: document.querySelector("#currentRequestSeasons"),
  currentProfileSummary: document.querySelector("#currentProfileSummary"),
  currentQualityProfileMode: document.querySelector("#currentQualityProfileMode"),
  currentRootFolder: document.querySelector("#currentRootFolder"),
  currentTags: document.querySelector("#currentTags"),
  testMetricOneLabel: document.querySelector("#testMetricOneLabel"),
  testMetricTwoLabel: document.querySelector("#testMetricTwoLabel"),
  testMetricThreeLabel: document.querySelector("#testMetricThreeLabel"),
  testMetricFourLabel: document.querySelector("#testMetricFourLabel"),
  testMetricFiveLabel: document.querySelector("#testMetricFiveLabel"),
  testServerCount: document.querySelector("#testServerCount"),
  testServerName: document.querySelector("#testServerName"),
  testProfileId: document.querySelector("#testProfileId"),
  testSeriesType: document.querySelector("#testSeriesType"),
  testRootFolder: document.querySelector("#testRootFolder"),
  testButton: document.querySelector("#testConnectionBtn"),
  authSidebarStatus: document.querySelector("#authSidebarStatus"),
  authSidebarIdentity: document.querySelector("#authSidebarIdentity"),
  connectionSidebarStatus: document.querySelector("#connectionSidebarStatus"),
  connectionSidebarHost: document.querySelector("#connectionSidebarHost"),
};

const customSelectRoots = [...document.querySelectorAll("[data-ui-select]")];
const customSelects = new Map();

function toast(message) {
  if (!els.toast) return;
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => els.toast.classList.remove("show"), 3600);
}

async function readError(response) {
  const text = await response.text();
  try {
    const payload = JSON.parse(text);
    return payload.detail || text;
  } catch {
    return text;
  }
}

function showBanner(element, message, tone = "info") {
  if (!element) return;
  element.textContent = message;
  element.dataset.tone = tone;
  element.hidden = false;
}

function clearBanner(element) {
  if (!element) return;
  element.hidden = true;
  element.textContent = "";
  delete element.dataset.tone;
}

function parseOptionalInt(value) {
  if (!value || !String(value).trim()) return null;
  return Number(value);
}

function normalizeUrlSuffix(value = "") {
  if (!value || value === "/") {
    return "";
  }
  return value;
}

function splitBaseUrl(baseUrl) {
  const fallback = {
    scheme: DEFAULT_SONARR_SCHEME,
    host: "",
    port: DEFAULT_SONARR_PORT,
    suffix: "",
  };
  if (!baseUrl || !String(baseUrl).trim()) {
    return fallback;
  }
  const raw = String(baseUrl).trim();
  try {
    const parsed = new URL(
      raw.includes("://") ? raw : `${DEFAULT_SONARR_SCHEME}://${raw}`,
    );
    return {
      scheme: parsed.protocol.replace(":", "") || DEFAULT_SONARR_SCHEME,
      host: parsed.hostname || "",
      port: parsed.port || DEFAULT_SONARR_PORT,
      suffix: normalizeUrlSuffix(
        `${parsed.pathname || ""}${parsed.search || ""}${parsed.hash || ""}`,
      ),
    };
  } catch {
    const match = raw.match(/^(https?):\/\/([^/:?#]+)(?::(\d+))?(.*)?$/i);
    if (!match) {
      return { ...fallback, host: raw.replace(/\/+$/, "") };
    }
    return {
      scheme: match[1]?.toLowerCase() || DEFAULT_SONARR_SCHEME,
      host: match[2] || "",
      port: match[3] || DEFAULT_SONARR_PORT,
      suffix: normalizeUrlSuffix(match[4] || ""),
    };
  }
}

function composeSonarrBaseUrl() {
  const host = els.sonarrHost?.value.trim() || "";
  if (!host) {
    return "";
  }
  const scheme =
    els.sonarrScheme?.value === "https" ? "https" : DEFAULT_SONARR_SCHEME;
  const port = els.sonarrPort?.value.trim() || DEFAULT_SONARR_PORT;
  const suffix = normalizeUrlSuffix(state.sonarrBaseUrlSuffix);
  return `${scheme}://${host}:${port}${suffix}`.replace(/\/$/, "");
}

function populateSonarrBaseUrlFields(baseUrl) {
  const parts = splitBaseUrl(baseUrl);
  state.sonarrBaseUrlSuffix = parts.suffix;
  if (els.sonarrScheme) {
    els.sonarrScheme.value = parts.scheme;
  }
  if (els.sonarrHost && !document.activeElement?.isSameNode(els.sonarrHost)) {
    els.sonarrHost.value = parts.host;
  }
  if (els.sonarrPort && !document.activeElement?.isSameNode(els.sonarrPort)) {
    els.sonarrPort.value = parts.port || DEFAULT_SONARR_PORT;
  }
  syncCustomSelects(["sonarrScheme"]);
}

function parseTags(value) {
  if (!value.trim()) return [];
  return value
    .split(",")
    .map((part) => Number(part.trim()))
    .filter((part) => Number.isFinite(part));
}

function savedSonarrSettings() {
  return state.requestSettings?.sonarr || {};
}

function pickExistingValue(items, getValue, candidates) {
  const values = new Set(items.map((item) => String(getValue(item))));
  for (const candidate of candidates) {
    if (candidate === null || candidate === undefined || candidate === "") {
      continue;
    }
    const normalized = String(candidate);
    if (values.has(normalized)) {
      return normalized;
    }
  }
  return null;
}

function setSelectOptions(
  select,
  items,
  {
    getValue = (item) => item.value,
    getLabel = (item) => item.label,
    includeBlankLabel = null,
    emptyLabel = "No options found",
    selectedValue = null,
  } = {},
) {
  if (!select) return;
  select.innerHTML = "";
  if (includeBlankLabel !== null) {
    const blankOption = document.createElement("option");
    blankOption.value = "";
    blankOption.textContent = includeBlankLabel;
    select.append(blankOption);
  }
  if (items.length) {
    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = String(getValue(item) ?? "");
      option.textContent = String(getLabel(item) ?? "");
      select.append(option);
    });
  } else if (emptyLabel) {
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = emptyLabel;
    select.append(emptyOption);
  }
  const normalizedSelected =
    selectedValue === null || selectedValue === undefined || selectedValue === ""
      ? null
      : String(selectedValue);
  if (
    normalizedSelected &&
    [...select.options].some((option) => option.value === normalizedSelected)
  ) {
    select.value = normalizedSelected;
  } else {
    select.value = select.options[0]?.value || "";
  }
  syncCustomSelects([select.id]);
}

function resetSonarrSelectOptions() {
  setSelectOptions(els.sonarrRootFolderPath, [], {
    emptyLabel: "Validate Sonarr first",
  });
  setSelectOptions(els.sonarrQualityProfileId, [], {
    emptyLabel: "Validate Sonarr first",
  });
  setSelectOptions(els.sonarrLanguageProfileId, [], {
    includeBlankLabel: "Use Sonarr default",
    emptyLabel: null,
  });
}

function renderSonarrValidationUi() {
  const sonarrActive = activeRequestBackend() === "sonarr";
  if (els.sonarrValidationNote) {
    els.sonarrValidationNote.hidden = !sonarrActive;
  }
  if (els.sonarrAdvancedFields) {
    els.sonarrAdvancedFields.hidden = !sonarrActive || !state.sonarrValidated;
  }
  if (els.sonarrValidationCopy) {
    els.sonarrValidationCopy.textContent = state.sonarrValidated
      ? "Sonarr validated successfully. Review the live folders and profiles below, then save the backend settings."
      : "Enter the Sonarr host, port, and API key, then validate Sonarr to load the live folders and profiles before saving backend settings.";
  }
  if (els.sonarrValidateButton) {
    els.sonarrValidateButton.hidden = !sonarrActive;
    els.sonarrValidateButton.textContent = state.sonarrValidated
      ? "Reload Sonarr Options"
      : "Validate Sonarr";
  }
  if (els.testButton) {
    els.testButton.hidden = sonarrActive;
    els.testButton.textContent = "Test Seerr";
  }
}

function resetConnectionTestResult() {
  const sonarrActive = activeRequestBackend() === "sonarr";
  if (els.testMetricOneLabel) {
    els.testMetricOneLabel.textContent = sonarrActive
      ? "Root Folders"
      : "Server Count";
  }
  if (els.testMetricTwoLabel) {
    els.testMetricTwoLabel.textContent = sonarrActive
      ? "Quality Profiles"
      : "Default Server";
  }
  if (els.testMetricThreeLabel) {
    els.testMetricThreeLabel.textContent = sonarrActive
      ? "Language Profiles"
      : "Detected Profile";
  }
  if (els.testMetricFourLabel) {
    els.testMetricFourLabel.textContent = sonarrActive
      ? "Default Series Type"
      : "Detected Series Type";
  }
  if (els.testMetricFiveLabel) {
    els.testMetricFiveLabel.textContent = sonarrActive
      ? "Detected Root"
      : "Detected Root";
  }
  [
    els.testServerCount,
    els.testServerName,
    els.testProfileId,
    els.testSeriesType,
    els.testRootFolder,
  ].forEach((element) => {
    if (element) {
      element.textContent = "--";
    }
  });
}

function resetSonarrValidation({ resetTestMetrics = true } = {}) {
  state.sonarrValidated = false;
  state.sonarrOptions = {
    rootFolders: [],
    qualityProfiles: [],
    languageProfiles: [],
  };
  resetSonarrSelectOptions();
  renderSonarrValidationUi();
  if (resetTestMetrics && activeRequestBackend() === "sonarr") {
    resetConnectionTestResult();
  }
}

function applySonarrValidationResult(result) {
  const summary = savedSonarrSettings();
  const defaults = result?.defaults || {};
  const rootFolders = result?.rootFolders || [];
  const qualityProfiles = result?.qualityProfiles || [];
  const languageProfiles = result?.languageProfiles || [];

  state.sonarrValidated = true;
  state.sonarrOptions = {
    rootFolders,
    qualityProfiles,
    languageProfiles,
  };

  const rootFolderValue = pickExistingValue(
    rootFolders,
    (item) => item.path,
    [
      els.sonarrRootFolderPath?.value,
      summary.rootFolderPath,
      defaults.rootFolderPath,
      rootFolders[0]?.path,
    ],
  );
  const qualityProfileValue = pickExistingValue(
    qualityProfiles,
    (item) => item.id,
    [
      els.sonarrQualityProfileId?.value,
      summary.qualityProfileId,
      defaults.qualityProfileId,
      qualityProfiles[0]?.id,
    ],
  );
  const languageProfileValue = pickExistingValue(
    languageProfiles,
    (item) => item.id,
    [
      els.sonarrLanguageProfileId?.value,
      summary.languageProfileId,
      defaults.languageProfileId,
    ],
  );

  setSelectOptions(els.sonarrRootFolderPath, rootFolders, {
    getValue: (item) => item.path,
    getLabel: (item) => item.path,
    emptyLabel: "No root folders found",
    selectedValue: rootFolderValue,
  });
  setSelectOptions(els.sonarrQualityProfileId, qualityProfiles, {
    getValue: (item) => item.id,
    getLabel: (item) => item.name,
    emptyLabel: "No quality profiles found",
    selectedValue: qualityProfileValue,
  });
  setSelectOptions(els.sonarrLanguageProfileId, languageProfiles, {
    getValue: (item) => item.id,
    getLabel: (item) => item.name,
    includeBlankLabel: "Use Sonarr default",
    emptyLabel: null,
    selectedValue: languageProfileValue,
  });
  renderSonarrValidationUi();
}

function activeRequestBackend() {
  return els.requestBackend?.value || state.requestSettings?.requestBackend || "seerr";
}

function activeRequestBackendName() {
  return requestBackendLabels[activeRequestBackend()] || "Seerr";
}

function applyConnectionOverrideState() {
  if (els.profileId) {
    els.profileId.disabled = !Boolean(els.forceQualityProfile?.checked);
  }
}

function applyRequestBackendPanels() {
  const sonarrActive = activeRequestBackend() === "sonarr";
  if (els.seerrSettingsPanel) {
    els.seerrSettingsPanel.hidden = sonarrActive;
  }
  if (els.sonarrSettingsPanel) {
    els.sonarrSettingsPanel.hidden = !sonarrActive;
  }
  renderSonarrValidationUi();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function syncCustomSelect(configOrId) {
  const config =
    typeof configOrId === "string" ? customSelects.get(configOrId) : configOrId;
  if (!config) return;
  const { root, select, trigger, value, menu } = config;
  const selectedOption = select.options[select.selectedIndex];
  value.textContent = selectedOption ? selectedOption.textContent : "";
  root.dataset.value = select.value;
  menu.innerHTML = [...select.options]
    .map((option) => {
      const selected = option.value === select.value;
      return `
        <button
          class="ui-select-option ${selected ? "selected" : ""}"
          type="button"
          role="option"
          aria-selected="${String(selected)}"
          data-select-option="${select.id}"
          data-value="${escapeHtml(option.value)}"
        >
          <span>${escapeHtml(option.textContent)}</span>
          ${selected ? "<i aria-hidden=\"true\">●</i>" : ""}
        </button>
      `;
    })
    .join("");
  trigger.setAttribute("data-value", select.value);
}

function syncCustomSelects(selectIds) {
  if (Array.isArray(selectIds) && selectIds.length) {
    selectIds.forEach((selectId) => syncCustomSelect(selectId));
    return;
  }
  customSelects.forEach((config) => syncCustomSelect(config));
}

function setCustomSelectOpen(selectId = null) {
  state.openDropdown = selectId;
  customSelects.forEach((config, key) => {
    const open = key === selectId;
    config.root.classList.toggle("open", open);
    config.menu.hidden = !open;
    config.trigger.setAttribute("aria-expanded", String(open));
  });
}

function initializeCustomSelects() {
  customSelectRoots.forEach((root) => {
    const select = root.querySelector("select");
    const trigger = root.querySelector(".ui-select-trigger");
    const value = root.querySelector(".ui-select-value");
    const menu = root.querySelector(".ui-select-menu");
    if (!select || !trigger || !value || !menu) return;
    select.setAttribute("aria-hidden", "true");
    select.tabIndex = -1;
    const config = { root, select, trigger, value, menu };
    customSelects.set(select.id, config);
    syncCustomSelect(config);
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const nextOpen = state.openDropdown === select.id ? null : select.id;
      setCustomSelectOpen(nextOpen);
    });
    menu.addEventListener("click", (event) => {
      const option = event.target.closest("[data-select-option]");
      if (!option) return;
      const nextValue = option.dataset.value;
      if (select.value !== nextValue) {
        select.value = nextValue;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      syncCustomSelect(config);
      setCustomSelectOpen(null);
    });
    select.addEventListener("change", () => syncCustomSelect(config));
  });
}

function availableThemes() {
  return state.weebarr?.theme?.themes || [];
}

function activeTheme() {
  return (
    availableThemes().find(
      (theme) => theme.id === state.weebarr?.theme?.activeThemeId,
    ) || availableThemes()[0] || null
  );
}

function formatDateTime(value) {
  if (!value) return "Never";
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function formatAutomationCadence(days, hours) {
  const safeDays = Number.isFinite(Number(days)) ? Number(days) : 30;
  const safeHours = Number.isFinite(Number(hours)) ? Number(hours) : 0;
  return `${safeDays}d ${safeHours}h`;
}

function signInLabel(access) {
  if (access.localAuthConfigured && access.plexLoginEnabled) {
    return "Username/password or Plex";
  }
  if (access.localAuthConfigured) {
    return "Username/password";
  }
  if (access.plexLoginEnabled) {
    return "Plex only";
  }
  return "Setup required";
}

function enabledBucketSummary(buckets) {
  const labels = [];
  if (buckets?.s_tier) labels.push("S-Tier");
  if (buckets?.canon) labels.push("Canon");
  if (buckets?.bingeable) labels.push("Bingeable");
  if (buckets?.filler) labels.push("Filler");
  return labels.length ? labels.join(", ") : "None enabled";
}

function buildColorPickerGrid() {
  if (!els.colorPickerGrid) return;
  const theme =
    availableThemes().find((entry) => entry.id === "color-picker") || activeTheme();
  const tokens = theme?.tokens || { dark: {}, light: {} };
  els.colorPickerGrid.innerHTML = ["dark", "light"]
    .map(
      (mode) => `
        <section class="theme-color-group">
          <div class="settings-subheading">
            <h3>${mode === "dark" ? "Dark Mode Palette" : "Light Mode Palette"}</h3>
          </div>
          <div class="theme-color-fields">
            ${colorPickerFields
              .map(
                (field) => `
                  <label class="theme-color-field">
                    <span>${field.label}</span>
                    <input
                      type="color"
                      data-theme-color-mode="${mode}"
                      data-theme-color-key="${field.key}"
                      value="${tokens[mode]?.[field.key] || "#ffffff"}"
                    />
                  </label>
                `,
              )
              .join("")}
          </div>
        </section>
      `,
    )
    .join("");
}

function readColorPickerTokens() {
  const theme =
    availableThemes().find((entry) => entry.id === "color-picker") || activeTheme();
  const currentTokens = JSON.parse(JSON.stringify(theme?.tokens || { dark: {}, light: {} }));
  els.colorPickerGrid
    ?.querySelectorAll("[data-theme-color-key]")
    .forEach((input) => {
      const mode = input.dataset.themeColorMode;
      const key = input.dataset.themeColorKey;
      if (!mode || !key) return;
      currentTokens[mode] = currentTokens[mode] || {};
      currentTokens[mode][key] = input.value;
    });
  return currentTokens;
}

function updateThemeControls() {
  if (els.activeThemeId && state.weebarr?.theme?.activeThemeId) {
    els.activeThemeId.value = state.weebarr.theme.activeThemeId;
  }
  const theme = activeTheme();
  if (els.activeThemeDescription) {
    els.activeThemeDescription.textContent =
      theme?.description || "Choose a theme to preview its palette across the dashboard shell.";
  }
  if (els.currentActiveTheme) {
    els.currentActiveTheme.textContent = theme?.name || "Neon Lights";
  }
  if (els.colorPickerPanel) {
    els.colorPickerPanel.hidden = theme?.id !== "color-picker";
  }
  buildColorPickerGrid();
  syncCustomSelects(["settingsActiveThemeId"]);
  if (window.WeebarrTheme) {
    window.WeebarrTheme.setThemeContext(state.weebarr?.theme || {});
    window.WeebarrTheme.bindThemeButtons();
  }
}

function updateWeebarr(summary) {
  state.weebarr = summary || {};
  if (els.contentFilterMode && summary.contentFilterMode) {
    els.contentFilterMode.value = summary.contentFilterMode;
  }
  if (els.strictMonitoring) {
    els.strictMonitoring.checked = Boolean(summary.strictMonitoring);
  }
  if (els.currentContentFilter) {
    els.currentContentFilter.textContent =
      contentFilterLabels[summary.contentFilterMode] || "Hide NSFW";
  }
  if (els.currentStrictMonitoring) {
    els.currentStrictMonitoring.textContent = summary.strictMonitoring
      ? "Enabled"
      : "Disabled";
  }
  const automation = summary.automation || {};
  if (els.automationBucketSTier) {
    els.automationBucketSTier.checked = Boolean(automation.enabledBuckets?.s_tier);
    els.automationBucketCanon.checked = Boolean(automation.enabledBuckets?.canon);
    els.automationBucketBingeable.checked = Boolean(
      automation.enabledBuckets?.bingeable,
    );
    els.automationBucketFiller.checked = Boolean(automation.enabledBuckets?.filler);
  }
  if (els.automationScanIntervalDays) {
    els.automationScanIntervalDays.value =
      automation.scanIntervalDays || String(30);
  }
  if (els.automationScanIntervalHours) {
    els.automationScanIntervalHours.value = String(
      automation.scanIntervalHours ?? 0,
    );
  }
  if (els.automationEnabledBuckets) {
    els.automationEnabledBuckets.textContent = enabledBucketSummary(
      automation.enabledBuckets,
    );
  }
  if (els.automationScanIntervalSummary) {
    els.automationScanIntervalSummary.textContent = formatAutomationCadence(
      automation.scanIntervalDays || 30,
      automation.scanIntervalHours ?? 0,
    );
  }
  if (els.automationLastScanAt) {
    els.automationLastScanAt.textContent = formatDateTime(automation.lastScanAt);
  }
  if (els.automationLastProcessed) {
    els.automationLastProcessed.textContent =
      automation.lastProcessedSeason && automation.lastProcessedYear
        ? `${automation.lastProcessedSeason} ${automation.lastProcessedYear}`
        : "Not yet run";
  }
  updateThemeControls();
  syncCustomSelects(["settingsContentFilterMode"]);
}

function updateConnection(summary) {
  state.requestSettings = summary || {};
  state.connection = summary?.seerr || {};
  const connection = state.connection;
  const sonarr = summary?.sonarr || {};
  const selectedBackend =
    summary?.requestBackend || els.requestBackend?.value || "seerr";
  if (els.requestBackend && summary?.requestBackend) {
    els.requestBackend.value = summary.requestBackend;
  }
  const sonarrActive = selectedBackend === "sonarr";
  const selectedBackendName = requestBackendLabels[selectedBackend] || "Seerr";
  const activeSummary = sonarrActive ? sonarr : connection;

  if (els.currentRequestBackend) {
    els.currentRequestBackend.textContent = selectedBackendName;
  }
  if (els.currentBaseUrl) {
    els.currentBaseUrl.textContent = activeSummary.baseUrl || "Not set";
  }
  if (els.currentApiKey) {
    els.currentApiKey.textContent = activeSummary.apiKeyPreview || "Not set";
  }
  if (els.currentRequestSeasons) {
    els.currentRequestSeasons.textContent = sonarrActive
      ? sonarr.defaultMonitorMode || "all"
      : connection.requestSeasons || "all";
  }
  if (els.currentProfileSummary) {
    els.currentProfileSummary.textContent = sonarrActive
      ? `Direct / ${seriesTypeLabels[sonarr.seriesType] || "Not set"}`
      : `${connection.sonarrServerId || "Default"} / ${seriesTypeLabels[connection.seriesType] || "Use Seerr default"}`;
  }
  if (els.currentQualityProfileMode) {
    els.currentQualityProfileMode.textContent = sonarrActive
      ? sonarr.qualityProfileId || "Not set"
      : connection.forceQualityProfile
        ? connection.profileId || "Missing ID"
        : "Seerr default";
  }
  if (els.currentRootFolder) {
    els.currentRootFolder.textContent = sonarrActive
      ? sonarr.rootFolderPath || "Not set"
      : connection.rootFolder || "Default";
  }
  if (els.currentTags) {
    const tags = sonarrActive ? sonarr.tags : connection.tags;
    els.currentTags.textContent = tags?.length ? tags.join(", ") : "None";
  }
  if (els.connectionStatusPill) {
    els.connectionStatusPill.textContent = summary?.requestBackendConfigured
      ? "Configured"
      : "Missing";
    els.connectionStatusPill.classList.toggle(
      "connected",
      Boolean(summary?.requestBackendConfigured),
    );
    els.connectionStatusPill.classList.toggle(
      "missing",
      !summary?.requestBackendConfigured,
    );
  }

  if (els.baseUrl && !document.activeElement?.isSameNode(els.baseUrl)) {
    els.baseUrl.value = connection.baseUrl || "";
  }
  if (els.requestSeasons && connection.requestSeasons) {
    els.requestSeasons.value = connection.requestSeasons;
  }
  if (els.sonarrServerId && !document.activeElement?.isSameNode(els.sonarrServerId)) {
    els.sonarrServerId.value = connection.sonarrServerId || "";
  }
  if (els.profileId && !document.activeElement?.isSameNode(els.profileId)) {
    els.profileId.value = connection.profileId || "";
  }
  if (els.forceQualityProfile) {
    els.forceQualityProfile.checked = Boolean(connection.forceQualityProfile);
  }
  if (els.seriesType && connection.seriesType) {
    els.seriesType.value = connection.seriesType;
  }
  if (els.rootFolder && !document.activeElement?.isSameNode(els.rootFolder)) {
    els.rootFolder.value = connection.rootFolder || "";
  }
  if (els.languageProfileId && !document.activeElement?.isSameNode(els.languageProfileId)) {
    els.languageProfileId.value = connection.languageProfileId || "";
  }
  if (els.requestUserId && !document.activeElement?.isSameNode(els.requestUserId)) {
    els.requestUserId.value = connection.requestUserId || "";
  }
  if (els.tags && !document.activeElement?.isSameNode(els.tags)) {
    els.tags.value = connection.tags?.length ? connection.tags.join(", ") : "";
  }
  if (els.apiKey) {
    els.apiKey.placeholder = connection.hasApiKey
      ? `Stored ${connection.apiKeyPreview} (leave blank to keep)`
      : "Paste a Seerr API key";
  }

  populateSonarrBaseUrlFields(sonarr.baseUrl || "");
  if (els.sonarrApiKey) {
    els.sonarrApiKey.placeholder = sonarr.hasApiKey
      ? `Stored ${sonarr.apiKeyPreview} (leave blank to keep)`
      : "Paste a Sonarr API key";
  }
  if (
    els.sonarrRootFolderPath &&
    !document.activeElement?.isSameNode(els.sonarrRootFolderPath)
  ) {
    els.sonarrRootFolderPath.value = sonarr.rootFolderPath || "";
  }
  if (
    els.sonarrQualityProfileId &&
    !document.activeElement?.isSameNode(els.sonarrQualityProfileId)
  ) {
    els.sonarrQualityProfileId.value = sonarr.qualityProfileId || "";
  }
  if (els.sonarrSeriesType && sonarr.seriesType) {
    els.sonarrSeriesType.value = sonarr.seriesType;
  }
  if (els.sonarrDefaultMonitorMode && sonarr.defaultMonitorMode) {
    els.sonarrDefaultMonitorMode.value = sonarr.defaultMonitorMode;
  }
  if (els.sonarrDefaultSearchOnAdd) {
    els.sonarrDefaultSearchOnAdd.checked = Boolean(sonarr.defaultSearchOnAdd);
  }
  if (els.sonarrDefaultSeasonFolder) {
    els.sonarrDefaultSeasonFolder.checked = Boolean(sonarr.defaultSeasonFolder);
  }
  if (
    els.sonarrLanguageProfileId &&
    !document.activeElement?.isSameNode(els.sonarrLanguageProfileId)
  ) {
    els.sonarrLanguageProfileId.value = sonarr.languageProfileId || "";
  }
  if (els.sonarrTags && !document.activeElement?.isSameNode(els.sonarrTags)) {
    els.sonarrTags.value = sonarr.tags?.length ? sonarr.tags.join(", ") : "";
  }

  if (els.connectionSidebarStatus) {
    els.connectionSidebarStatus.textContent = summary?.requestBackendConfigured
      ? "Connected"
      : `${selectedBackendName} missing`;
    els.connectionSidebarStatus.dataset.tooltip = summary?.requestBackendConfigured
      ? `Weebarr can reach ${selectedBackendName} with the saved connection settings.`
      : `Save a ${selectedBackendName} URL and API key to enable requests.`;
  }
  if (els.connectionSidebarHost) {
    els.connectionSidebarHost.textContent = selectedBackendName;
    els.connectionSidebarHost.dataset.tooltip = activeSummary.baseUrl
      ? `Current ${selectedBackendName} endpoint: ${activeSummary.baseUrl}`
      : `No live ${selectedBackendName} endpoint is configured yet.`;
  }

  applyRequestBackendPanels();
  applyConnectionOverrideState();
  syncCustomSelects([
    "settingsRequestBackend",
    "settingsRequestSeasons",
    "settingsSeriesType",
    "sonarrScheme",
    "sonarrRootFolderPath",
    "sonarrQualityProfileId",
    "sonarrSeriesType",
    "sonarrDefaultMonitorMode",
    "sonarrLanguageProfileId",
  ]);
}

function updateAccess(access) {
  state.access = access || {};
  if (
    els.localAccountUsername &&
    !document.activeElement?.isSameNode(els.localAccountUsername)
  ) {
    els.localAccountUsername.value = access.authUsername || "";
  }
  if (els.currentAuthSignIn) {
    els.currentAuthSignIn.textContent = signInLabel(access);
  }
  if (els.currentAppApiKeyPreview) {
    els.currentAppApiKeyPreview.value = access.apiKeyPreview || "Not generated yet";
  }
  if (els.apiKeyEnabledSummary) {
    els.apiKeyEnabledSummary.textContent = access.apiKeyEnabled
      ? "Enabled"
      : "Not generated";
  }
  if (els.apiKeyPreviewSummary) {
    els.apiKeyPreviewSummary.textContent =
      access.apiKeyPreview || "Not generated";
  }
  if (els.apiKeyStatusPill) {
    els.apiKeyStatusPill.textContent = access.apiKeyEnabled
      ? "Enabled"
      : "Not generated";
    els.apiKeyStatusPill.classList.toggle("connected", access.apiKeyEnabled);
    els.apiKeyStatusPill.classList.toggle("missing", !access.apiKeyEnabled);
  }
  if (els.regenerateAppApiKeyBtn) {
    els.regenerateAppApiKeyBtn.innerHTML = access.apiKeyEnabled
      ? '<span class="action-btn-icon action-btn-icon-refresh" aria-hidden="true"></span><span>Regenerate API Key</span>'
      : '<span class="action-btn-icon action-btn-icon-refresh" aria-hidden="true"></span><span>Generate API Key</span>';
  }
  if (els.authSidebarStatus) {
    const authDescription = access.localAuthConfigured && access.plexLoginEnabled
      ? "Connected with both local and Plex sign-in available."
      : access.localAuthConfigured
        ? "Connected with local sign-in enabled."
        : access.plexLoginEnabled
          ? "Connected with Plex sign-in enabled."
          : "Authentication setup is still required.";
    els.authSidebarStatus.textContent = access.configured ? "Connected" : "Setup required";
    els.authSidebarStatus.dataset.tooltip = authDescription;
  }
  if (els.authSidebarIdentity && access.authUsername) {
    els.authSidebarIdentity.textContent = access.authUsername;
  }
  if (els.authSidebarIdentity) {
    els.authSidebarIdentity.dataset.tooltip = signInLabel(access);
  }
  if (els.localAccountStatusPill) {
    const configured = Boolean(access.localAuthConfigured);
    els.localAccountStatusPill.textContent = configured ? "Configured" : "Not set";
    els.localAccountStatusPill.classList.toggle("connected", configured);
    els.localAccountStatusPill.classList.toggle("missing", !configured);
  }
}

function showGeneratedApiKey(apiKey = "") {
  const hasValue = Boolean(apiKey);
  if (els.generatedAppApiKeyGroup) {
    els.generatedAppApiKeyGroup.hidden = !hasValue;
  }
  if (els.generatedAppApiKey) {
    els.generatedAppApiKey.value = apiKey || "";
  }
  if (els.copyAppApiKeyBtn) {
    els.copyAppApiKeyBtn.hidden = !hasValue;
  }
}

function syncSettingsTabBridge() {
  if (!els.settingsShell || !els.settingsStack || !els.settingsTabs.length) {
    return;
  }
  const activeTab = Array.from(els.settingsTabs).find((button) =>
    button.classList.contains("active"),
  );
  if (!activeTab) {
    els.settingsShell.dataset.settingsTabAttached = "false";
    els.settingsShell.style.removeProperty("--settings-active-tab-left");
    els.settingsShell.style.removeProperty("--settings-active-tab-width");
    return;
  }

  const activeRect = activeTab.getBoundingClientRect();
  const stackRect = els.settingsStack.getBoundingClientRect();
  const bridgeOverlap = 14;
  const previousTab = activeTab.previousElementSibling;
  const nextTab = activeTab.nextElementSibling;
  const previousRect =
    previousTab instanceof HTMLElement
      ? previousTab.getBoundingClientRect()
      : null;
  const nextRect =
    nextTab instanceof HTMLElement ? nextTab.getBoundingClientRect() : null;
  const bridgeStart = previousRect
    ? previousRect.right - stackRect.left - bridgeOverlap
    : activeRect.left - stackRect.left - bridgeOverlap;
  const bridgeEnd = nextRect
    ? nextRect.left - stackRect.left + bridgeOverlap
    : activeRect.right - stackRect.left + bridgeOverlap;
  const bridgeLeft = Math.max(0, bridgeStart);
  const bridgeWidth = Math.max(
    0,
    Math.min(stackRect.width, bridgeEnd) - bridgeLeft,
  );
  const isAttached = Math.abs(stackRect.top - activeRect.bottom) <= 12;

  els.settingsShell.style.setProperty(
    "--settings-active-tab-left",
    `${bridgeLeft}px`,
  );
  els.settingsShell.style.setProperty(
    "--settings-active-tab-width",
    `${bridgeWidth}px`,
  );
  els.settingsShell.dataset.settingsTabAttached = isAttached ? "true" : "false";
}

function openSettingsTab(tabId, replaceHash = true) {
  const nextTab = validSettingsTabs.has(tabId) ? tabId : "weebarr";
  state.activeTab = nextTab;
  els.settingsTabs.forEach((button) => {
    button.classList.toggle("active", button.dataset.settingsTab === nextTab);
  });
  els.settingsPanels.forEach((panel) => {
    panel.hidden = panel.dataset.settingsPanel !== nextTab;
  });
  if (replaceHash) {
    history.replaceState(null, "", `#${nextTab}`);
  }
  setCustomSelectOpen(null);
  syncSettingsTabBridge();
}

function currentAutomationEnabled() {
  return {
    s_tier: Boolean(els.automationBucketSTier?.checked),
    canon: Boolean(els.automationBucketCanon?.checked),
    bingeable: Boolean(els.automationBucketBingeable?.checked),
    filler: Boolean(els.automationBucketFiller?.checked),
  };
}

function hasAnyEnabledBucket(buckets) {
  return Object.values(buckets || {}).some(Boolean);
}

function weebarrPayload() {
  return {
    contentFilterMode: els.contentFilterMode.value,
    strictMonitoring: Boolean(els.strictMonitoring.checked),
    theme: {
      activeThemeId: els.activeThemeId?.value || "neon-lights",
      colorPickerTokens: readColorPickerTokens(),
    },
  };
}

function automationPayload() {
  const scanIntervalDays = Number(els.automationScanIntervalDays?.value || 0);
  const scanIntervalHours = Number(els.automationScanIntervalHours?.value || 0);
  return {
    automation: {
      enabledBuckets: currentAutomationEnabled(),
      scanIntervalDays,
      scanIntervalHours,
    },
  };
}

function seerrConnectionPayload() {
  return {
    baseUrl: els.baseUrl.value.trim(),
    requestSeasons: els.requestSeasons.value,
    sonarrServerId: parseOptionalInt(els.sonarrServerId.value),
    forceQualityProfile: Boolean(els.forceQualityProfile?.checked),
    seriesType: els.seriesType?.value || "default",
    profileId: parseOptionalInt(els.profileId.value),
    rootFolder: els.rootFolder.value.trim() || null,
    languageProfileId: parseOptionalInt(els.languageProfileId.value),
    requestUserId: parseOptionalInt(els.requestUserId.value),
    tags: parseTags(els.tags.value),
  };
}

function sonarrConnectionPayload() {
  return {
    baseUrl: composeSonarrBaseUrl(),
    rootFolderPath: els.sonarrRootFolderPath.value.trim() || null,
    qualityProfileId: parseOptionalInt(els.sonarrQualityProfileId.value),
    seriesType: els.sonarrSeriesType?.value || "anime",
    defaultMonitorMode: els.sonarrDefaultMonitorMode?.value || "all",
    defaultSearchOnAdd: Boolean(els.sonarrDefaultSearchOnAdd?.checked),
    defaultSeasonFolder: Boolean(els.sonarrDefaultSeasonFolder?.checked),
    languageProfileId: parseOptionalInt(els.sonarrLanguageProfileId.value),
    tags: parseTags(els.sonarrTags.value),
  };
}

function requestSettingsPayload() {
  return {
    requestBackend: els.requestBackend?.value || "seerr",
    seerr: seerrConnectionPayload(),
    sonarr: sonarrConnectionPayload(),
  };
}

function localAccountPayload() {
  return {
    username: els.localAccountUsername.value.trim(),
    password: els.localAccountPassword.value,
    confirmPassword: els.localAccountConfirmPassword.value,
  };
}

async function refreshSettings() {
  const [weebarrResponse, connectionResponse, accessResponse] = await Promise.all([
    fetch("/api/settings/weebarr"),
    fetch("/api/settings/requests"),
    fetch("/api/setup/status"),
  ]);
  if (!weebarrResponse.ok) throw new Error(await readError(weebarrResponse));
  if (!connectionResponse.ok) throw new Error(await readError(connectionResponse));
  if (!accessResponse.ok) throw new Error(await readError(accessResponse));
  updateWeebarr(await weebarrResponse.json());
  updateConnection(await connectionResponse.json());
  updateAccess(await accessResponse.json());
}

async function saveWeebarr(event) {
  event.preventDefault();
  clearBanner(els.weebarrBanner);
  const response = await fetch("/api/settings/weebarr", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(weebarrPayload()),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateWeebarr(result.weebarr || {});
  showBanner(
    els.weebarrBanner,
    "Weebarr behavior and theme settings saved.",
    "success",
  );
  toast("Weebarr settings saved.");
}

async function saveAutomation(event) {
  event.preventDefault();
  clearBanner(els.automationBanner);
  const cadence = automationPayload().automation;
  if (!cadence.scanIntervalDays && !cadence.scanIntervalHours) {
    showBanner(
      els.automationBanner,
      "Automation cadence must be at least 1 hour.",
      "warn",
    );
    return;
  }
  const previousBuckets = state.weebarr?.automation?.enabledBuckets || {};
  const nextBuckets = currentAutomationEnabled();
  const firstEnable = !hasAnyEnabledBucket(previousBuckets) && hasAnyEnabledBucket(nextBuckets);
  let automationStartCurrentSeason = false;
  if (firstEnable) {
    automationStartCurrentSeason = window.confirm(
      "Should automations start on the current season?",
    );
  }
  const response = await fetch("/api/settings/weebarr", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      automation: cadence,
      automationStartCurrentSeason,
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateWeebarr(result.weebarr || {});
  const automationResult = result.automationResult;
  const message = automationResult
    ? `${automationResult.message} Requested ${automationResult.requested} title(s).`
    : "Automation settings saved.";
  showBanner(els.automationBanner, message, "success");
  toast("Automation settings saved.");
}

async function runAutomationScan() {
  clearBanner(els.automationBanner);
  const confirmed = window.confirm(
    "Run an immediate automation scan for the current season using the enabled buckets?",
  );
  if (!confirmed) return;
  const response = await fetch("/api/automation/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ force: true }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  await refreshSettings();
  showBanner(
    els.automationBanner,
    `${result.message} Requested ${result.requested} title(s), skipped ${result.skipped}, failed ${result.failed}.`,
    "success",
  );
  toast("Automation scan finished.");
}

async function saveLocalAccount(event) {
  event.preventDefault();
  clearBanner(els.accessBanner);
  const response = await fetch("/api/settings/access/local", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(localAccountPayload()),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateAccess(result.access || {});
  els.localAccountPassword.value = "";
  els.localAccountConfirmPassword.value = "";
  showBanner(
    els.accessBanner,
    "Local account saved. Login will offer local sign-in alongside Plex whenever both are configured.",
    "success",
  );
  toast("Local account saved.");
}

async function regenerateAppApiKey() {
  clearBanner(els.apiBanner);
  const response = await fetch("/api/settings/access/api-key/regenerate", {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateAccess(result.access || {});
  showGeneratedApiKey(result.apiKey || "");
  showBanner(
    els.apiBanner,
    "A new automation API key was generated. Copy it now because the full value will only be shown once.",
    "success",
  );
  toast("Automation API key rotated.");
}

async function copyGeneratedApiKey() {
  if (!els.generatedAppApiKey?.value) return;
  await navigator.clipboard.writeText(els.generatedAppApiKey.value);
  toast("API key copied.");
}

async function testConnection() {
  clearBanner(els.connectionBanner);
  const sonarrActive = activeRequestBackend() === "sonarr";
  const payload = requestSettingsPayload();
  const baseUrl = sonarrActive
    ? payload.sonarr.baseUrl || state.requestSettings?.sonarr?.baseUrl
    : payload.seerr.baseUrl || state.connection.baseUrl;
  const apiKey = sonarrActive
    ? els.sonarrApiKey.value.trim()
    : els.apiKey.value.trim();
  const hasSavedKey = sonarrActive
    ? Boolean(savedSonarrSettings().apiKeyPreview)
    : Boolean(state.connection?.apiKeyPreview);
  if (!baseUrl) {
    showBanner(
      els.connectionBanner,
      sonarrActive
        ? "Add the Sonarr host before testing the connection."
        : `Add a ${activeRequestBackendName()} base URL before testing the connection.`,
      "warn",
    );
    return;
  }
  if (!apiKey && !hasSavedKey) {
    showBanner(
      els.connectionBanner,
      `Add an API key before testing the ${activeRequestBackendName()} connection.`,
      "warn",
    );
    return;
  }
  const response = await fetch("/api/settings/requests/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requestBackend: activeRequestBackend(),
      seerr: {
        ...payload.seerr,
        apiKey: sonarrActive ? undefined : (apiKey || undefined),
      },
      sonarr: {
        ...payload.sonarr,
        apiKey: sonarrActive ? (apiKey || undefined) : undefined,
      },
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  const defaults = result.defaults || {};
  if (sonarrActive) {
    applySonarrValidationResult(result);
    els.testMetricOneLabel.textContent = "Root Folders";
    els.testMetricTwoLabel.textContent = "Quality Profiles";
    els.testMetricThreeLabel.textContent = "Language Profiles";
    els.testMetricFourLabel.textContent = "Default Series Type";
    els.testMetricFiveLabel.textContent = "Detected Root";
    els.testServerCount.textContent = result.rootFolderCount ?? "--";
    els.testServerName.textContent = result.qualityProfileCount ?? "--";
    els.testProfileId.textContent = result.languageProfileCount ?? "--";
    els.testSeriesType.textContent =
      defaults.seriesType
        ? seriesTypeLabels[defaults.seriesType] || defaults.seriesType
        : "Not set";
    els.testRootFolder.textContent = defaults.rootFolderPath || "Not detected";
    showBanner(
      els.connectionBanner,
      "Connection test succeeded. Sonarr Direct responded and Weebarr detected the available root folders, profiles, and defaults.",
      "success",
    );
    toast("Sonarr Direct connection test passed.");
    return;
  }
  els.testMetricOneLabel.textContent = "Server Count";
  els.testMetricTwoLabel.textContent = "Default Server";
  els.testMetricThreeLabel.textContent = "Detected Profile";
  els.testMetricFourLabel.textContent = "Detected Series Type";
  els.testMetricFiveLabel.textContent = "Detected Root";
  els.testServerCount.textContent = result.serverCount ?? "--";
  els.testServerName.textContent = defaults.serverName || "None";
  els.testProfileId.textContent = defaults.profileId || "Default";
  els.testSeriesType.textContent =
    defaults.seriesType
      ? seriesTypeLabels[defaults.seriesType] || "Use Seerr default"
      : "Not exposed by Seerr";
  els.testRootFolder.textContent = defaults.rootFolder || "Default";
  showBanner(
    els.connectionBanner,
    "Connection test succeeded. Seerr responded and its current anime request defaults were detected.",
    "success",
  );
  toast("Seerr connection test passed.");
}

async function saveConnection(event) {
  event.preventDefault();
  clearBanner(els.connectionBanner);
  const sonarrActive = activeRequestBackend() === "sonarr";
  if (sonarrActive && !state.sonarrValidated) {
    showBanner(
      els.connectionBanner,
      "Validate Sonarr first so Weebarr can load the live folders and profiles before saving Sonarr Direct.",
      "warn",
    );
    return;
  }
  const apiKey = sonarrActive
    ? els.sonarrApiKey.value.trim()
    : els.apiKey.value.trim();
  const payload = requestSettingsPayload();
  const response = await fetch("/api/settings/requests", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requestBackend: payload.requestBackend,
      seerr: {
        ...payload.seerr,
        apiKey: sonarrActive ? undefined : (apiKey || undefined),
      },
      sonarr: {
        ...payload.sonarr,
        apiKey: sonarrActive ? (apiKey || undefined) : undefined,
      },
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateConnection(result.requests || {});
  els.apiKey.value = "";
  if (els.sonarrApiKey) {
    els.sonarrApiKey.value = "";
  }
  showBanner(
    els.connectionBanner,
    `${activeRequestBackendName()} settings saved. New requests will use the updated backend settings immediately.`,
    "success",
  );
  toast("Connection settings saved.");
}

async function importThemeUrl() {
  clearBanner(els.weebarrBanner);
  const url = els.themeImportUrl?.value.trim();
  if (!url) {
    showBanner(els.weebarrBanner, "Enter a theme manifest URL first.", "warn");
    return;
  }
  const response = await fetch("/api/themes/import/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateWeebarr(result.weebarr || {});
  els.themeImportUrl.value = "";
  showBanner(els.weebarrBanner, "Theme imported from URL.", "success");
  toast("Theme imported.");
}

async function importThemeZip() {
  clearBanner(els.weebarrBanner);
  const file = els.themeImportZip?.files?.[0];
  if (!file) {
    showBanner(els.weebarrBanner, "Choose a zip file first.", "warn");
    return;
  }
  const body = new FormData();
  body.append("file", file, file.name);
  const response = await fetch("/api/themes/import/zip", {
    method: "POST",
    body,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateWeebarr(result.weebarr || {});
  els.themeImportZip.value = "";
  if (els.themeImportZipName) {
    els.themeImportZipName.textContent = "No file selected";
  }
  showBanner(els.weebarrBanner, "Theme imported from zip.", "success");
  toast("Theme imported.");
}

if (els.weebarrForm) {
  els.weebarrForm.addEventListener("submit", async (event) => {
    try {
      await saveWeebarr(event);
    } catch (error) {
      showBanner(els.weebarrBanner, `Save failed. ${error.message}`, "error");
    }
  });
}

if (els.automationForm) {
  els.automationForm.addEventListener("submit", async (event) => {
    try {
      await saveAutomation(event);
    } catch (error) {
      showBanner(els.automationBanner, `Save failed. ${error.message}`, "error");
    }
  });
}

if (els.automationScanNowBtn) {
  els.automationScanNowBtn.addEventListener("click", async () => {
    try {
      await runAutomationScan();
    } catch (error) {
      showBanner(els.automationBanner, `Scan failed. ${error.message}`, "error");
    }
  });
}

if (els.importThemeUrlBtn) {
  els.importThemeUrlBtn.addEventListener("click", async () => {
    try {
      await importThemeUrl();
    } catch (error) {
      showBanner(els.weebarrBanner, `Import failed. ${error.message}`, "error");
    }
  });
}

if (els.importThemeZipBtn) {
  els.importThemeZipBtn.addEventListener("click", async () => {
    try {
      await importThemeZip();
    } catch (error) {
      showBanner(els.weebarrBanner, `Import failed. ${error.message}`, "error");
    }
  });
}

if (els.themeImportZipPickBtn && els.themeImportZip) {
  els.themeImportZipPickBtn.addEventListener("click", () => {
    els.themeImportZip.click();
  });
  els.themeImportZip.addEventListener("change", () => {
    if (els.themeImportZipName) {
      els.themeImportZipName.textContent =
        els.themeImportZip.files?.[0]?.name || "No file selected";
    }
  });
}

if (els.testButton) {
  els.testButton.addEventListener("click", async () => {
    try {
      await testConnection();
    } catch (error) {
      showBanner(
        els.connectionBanner,
        `Connection test failed. ${error.message}`,
        "error",
      );
    }
  });
}

if (els.connectionForm) {
  els.connectionForm.addEventListener("submit", async (event) => {
    try {
      await saveConnection(event);
    } catch (error) {
      showBanner(els.connectionBanner, `Save failed. ${error.message}`, "error");
    }
  });
}

if (els.accessForm) {
  els.accessForm.addEventListener("submit", async (event) => {
    try {
      await saveLocalAccount(event);
    } catch (error) {
      showBanner(els.accessBanner, `Save failed. ${error.message}`, "error");
    }
  });
}

if (els.regenerateAppApiKeyBtn) {
  els.regenerateAppApiKeyBtn.addEventListener("click", async () => {
    try {
      await regenerateAppApiKey();
    } catch (error) {
      showBanner(els.apiBanner, `Key rotation failed. ${error.message}`, "error");
    }
  });
}

if (els.copyAppApiKeyBtn) {
  els.copyAppApiKeyBtn.addEventListener("click", async () => {
    try {
      await copyGeneratedApiKey();
    } catch (error) {
      showBanner(els.apiBanner, `Copy failed. ${error.message}`, "error");
    }
  });
}

if (els.forceQualityProfile) {
  els.forceQualityProfile.addEventListener("change", () => {
    applyConnectionOverrideState();
  });
}

if (els.requestBackend) {
  els.requestBackend.addEventListener("change", () => {
    if (state.requestSettings) {
      state.requestSettings = {
        ...state.requestSettings,
        requestBackend: els.requestBackend.value,
      };
    }
    applyRequestBackendPanels();
    resetConnectionTestResult();
    clearBanner(els.connectionBanner);
    if (els.currentRequestBackend) {
      els.currentRequestBackend.textContent = activeRequestBackendName();
    }
    syncCustomSelects(["settingsRequestBackend"]);
  });
}

[
  els.sonarrScheme,
  els.sonarrHost,
  els.sonarrPort,
  els.sonarrApiKey,
].forEach((element) => {
  if (!element) return;
  ["input", "change"].forEach((eventName) => {
    element.addEventListener(eventName, () => {
      resetSonarrValidation();
      clearBanner(els.connectionBanner);
    });
  });
});

if (els.sonarrValidateButton) {
  els.sonarrValidateButton.addEventListener("click", async () => {
    try {
      await testConnection();
    } catch (error) {
      showBanner(
        els.connectionBanner,
        `Connection test failed. ${error.message}`,
        "error",
      );
    }
  });
}

if (els.activeThemeId) {
  els.activeThemeId.addEventListener("change", () => {
    state.weebarr = {
      ...state.weebarr,
      theme: {
        ...(state.weebarr.theme || {}),
        activeThemeId: els.activeThemeId.value,
      },
    };
    updateThemeControls();
  });
}

els.settingsTabs.forEach((button) => {
  button.addEventListener("click", () => {
    openSettingsTab(button.dataset.settingsTab || "weebarr");
  });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".ui-select")) {
    setCustomSelectOpen(null);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setCustomSelectOpen(null);
  }
});

window.addEventListener("hashchange", () => {
  openSettingsTab(
    (location.hash || "#weebarr").replace("#", "") || "weebarr",
    false,
  );
});

window.addEventListener("resize", () => {
  syncSettingsTabBridge();
});

initializeCustomSelects();
resetSonarrValidation({ resetTestMetrics: false });
resetConnectionTestResult();
updateWeebarr(state.weebarr);
updateAccess(state.access);
updateConnection(state.requestSettings);
showGeneratedApiKey("");
if (window.WeebarrTheme) {
  window.WeebarrTheme.bindThemeButtons();
}
openSettingsTab(
  (location.hash || "#weebarr").replace("#", "") || "weebarr",
  false,
);
refreshSettings().catch((error) => {
  showBanner(
    els.connectionBanner,
    `Could not load the saved settings. ${error.message}`,
    "error",
  );
});
