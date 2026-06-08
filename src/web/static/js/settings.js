const state = {
  weebarr: window.WEEBARR_WEEBARR || {},
  connection: window.WEEBARR_CONNECTION || {},
  access: window.WEEBARR_ACCESS || {},
  openDropdown: null,
  activeTab: "weebarr",
};

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
  currentRequestSeasons: document.querySelector("#currentRequestSeasons"),
  currentProfileSummary: document.querySelector("#currentProfileSummary"),
  currentQualityProfileMode: document.querySelector("#currentQualityProfileMode"),
  currentRootFolder: document.querySelector("#currentRootFolder"),
  currentTags: document.querySelector("#currentTags"),
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

function parseTags(value) {
  if (!value.trim()) return [];
  return value
    .split(",")
    .map((part) => Number(part.trim()))
    .filter((part) => Number.isFinite(part));
}

function applyConnectionOverrideState() {
  if (els.profileId) {
    els.profileId.disabled = !Boolean(els.forceQualityProfile?.checked);
  }
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

function updateConnection(connection) {
  state.connection = connection || {};
  if (els.currentBaseUrl) {
    els.currentBaseUrl.textContent = connection.baseUrl || "Not set";
  }
  if (els.currentApiKey) {
    els.currentApiKey.textContent = connection.apiKeyPreview || "Not set";
  }
  if (els.currentRequestSeasons) {
    els.currentRequestSeasons.textContent = connection.requestSeasons || "all";
  }
  if (els.currentProfileSummary) {
    const seriesTypeLabel =
      seriesTypeLabels[connection.seriesType] || "Use Seerr default";
    els.currentProfileSummary.textContent = `${connection.sonarrServerId || "Default"} / ${seriesTypeLabel}`;
  }
  if (els.currentQualityProfileMode) {
    els.currentQualityProfileMode.textContent = connection.forceQualityProfile
      ? connection.profileId || "Missing ID"
      : "Seerr default";
  }
  if (els.currentRootFolder) {
    els.currentRootFolder.textContent = connection.rootFolder || "Default";
  }
  if (els.currentTags) {
    els.currentTags.textContent = connection.tags?.length
      ? connection.tags.join(", ")
      : "None";
  }
  if (els.connectionStatusPill) {
    els.connectionStatusPill.textContent = connection.configured
      ? "Configured"
      : "Missing";
    els.connectionStatusPill.classList.toggle("connected", connection.configured);
    els.connectionStatusPill.classList.toggle("missing", !connection.configured);
  }
  if (els.baseUrl && !document.activeElement?.isSameNode(els.baseUrl)) {
    els.baseUrl.value = connection.baseUrl || "";
  }
  if (els.requestSeasons && connection.requestSeasons) {
    els.requestSeasons.value = connection.requestSeasons;
  }
  if (
    els.sonarrServerId &&
    !document.activeElement?.isSameNode(els.sonarrServerId)
  ) {
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
  if (
    els.languageProfileId &&
    !document.activeElement?.isSameNode(els.languageProfileId)
  ) {
    els.languageProfileId.value = connection.languageProfileId || "";
  }
  if (
    els.requestUserId &&
    !document.activeElement?.isSameNode(els.requestUserId)
  ) {
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
  if (els.connectionSidebarStatus) {
    els.connectionSidebarStatus.textContent = connection.configured
      ? "Connected"
      : "Seerr missing";
    els.connectionSidebarStatus.dataset.tooltip = connection.configured
      ? "Weebarr can reach Seerr with the saved connection settings."
      : "Save a Seerr base URL and API key to enable requests.";
  }
  if (els.connectionSidebarHost) {
    els.connectionSidebarHost.textContent = "Seerr";
    els.connectionSidebarHost.dataset.tooltip = connection.baseUrl
      ? `Current Seerr endpoint: ${connection.baseUrl}`
      : "No live Seerr endpoint is configured yet.";
  }
  applyConnectionOverrideState();
  syncCustomSelects(["settingsRequestSeasons", "settingsSeriesType"]);
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

function connectionPayload() {
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
    fetch("/api/settings/seerr"),
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
  const payload = connectionPayload();
  if (!payload.baseUrl && !state.connection.baseUrl) {
    showBanner(
      els.connectionBanner,
      "Add a Seerr base URL before testing the connection.",
      "warn",
    );
    return;
  }
  const apiKey = els.apiKey.value.trim();
  const response = await fetch("/api/settings/seerr/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      apiKey: apiKey || null,
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  const defaults = result.defaults || {};
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
  const apiKey = els.apiKey.value.trim();
  const response = await fetch("/api/settings/seerr", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...connectionPayload(),
      apiKey: apiKey || null,
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  updateConnection(result.connection || {});
  els.apiKey.value = "";
  showBanner(
    els.connectionBanner,
    "Connection settings saved. New requests will use the updated Seerr settings immediately.",
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

initializeCustomSelects();
updateWeebarr(state.weebarr);
updateAccess(state.access);
updateConnection(state.connection);
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
