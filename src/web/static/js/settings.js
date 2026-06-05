const themeStorageKey = "weebarr-theme";
const prefersLight = window.matchMedia("(prefers-color-scheme: light)");

const state = {
  theme: "dark",
  weebarr: window.WEEBARR_WEEBARR || {},
  connection: window.WEEBARR_CONNECTION || {},
  access: window.WEEBARR_ACCESS || {},
  openDropdown: null,
};

const contentFilterLabels = {
  hide_nsfw: "Hide NSFW",
  show_all: "Show all",
};

const els = {
  toast: document.querySelector("#toast"),
  weebarrBanner: document.querySelector("#weebarrSettingsBanner"),
  connectionBanner: document.querySelector("#settingsBanner"),
  accessBanner: document.querySelector("#accessSettingsBanner"),
  connectionStatusPill: document.querySelector("#settingsStatusPill"),
  localAccountStatusPill: document.querySelector("#localAccountStatusPill"),
  themeButtons: document.querySelectorAll("[data-theme-choice]"),
  weebarrForm: document.querySelector("#weebarrForm"),
  connectionForm: document.querySelector("#connectionForm"),
  accessForm: document.querySelector("#localAccountForm"),
  contentFilterMode: document.querySelector("#settingsContentFilterMode"),
  strictMonitoring: document.querySelector("#settingsStrictMonitoring"),
  baseUrl: document.querySelector("#settingsBaseUrl"),
  apiKey: document.querySelector("#settingsApiKey"),
  requestSeasons: document.querySelector("#settingsRequestSeasons"),
  sonarrServerId: document.querySelector("#settingsSonarrServerId"),
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
  currentContentFilter: document.querySelector("#currentContentFilter"),
  currentStrictMonitoring: document.querySelector("#currentStrictMonitoring"),
  currentBaseUrl: document.querySelector("#currentBaseUrl"),
  currentApiKey: document.querySelector("#currentApiKey"),
  currentRequestSeasons: document.querySelector("#currentRequestSeasons"),
  currentProfileSummary: document.querySelector("#currentProfileSummary"),
  currentRootFolder: document.querySelector("#currentRootFolder"),
  currentTags: document.querySelector("#currentTags"),
  testServerCount: document.querySelector("#testServerCount"),
  testServerName: document.querySelector("#testServerName"),
  testProfileId: document.querySelector("#testProfileId"),
  testRootFolder: document.querySelector("#testRootFolder"),
  testButton: document.querySelector("#testConnectionBtn"),
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

function resolvedTheme(choice) {
  if (choice === "system") {
    return prefersLight.matches ? "light" : "dark";
  }
  return choice;
}

function applyTheme(choice = localStorage.getItem(themeStorageKey) || "dark") {
  state.theme = choice;
  document.body.dataset.theme = resolvedTheme(choice);
  document.body.dataset.themeChoice = choice;
  localStorage.setItem(themeStorageKey, choice);
  els.themeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.themeChoice === choice);
  });
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

function weebarrPayload() {
  return {
    contentFilterMode: els.contentFilterMode.value,
    strictMonitoring: Boolean(els.strictMonitoring.checked),
  };
}

function connectionPayload() {
  return {
    baseUrl: els.baseUrl.value.trim(),
    requestSeasons: els.requestSeasons.value,
    sonarrServerId: parseOptionalInt(els.sonarrServerId.value),
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
    els.currentProfileSummary.textContent = `${connection.sonarrServerId || "Default"} / ${connection.profileId || "Default"}`;
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
  syncCustomSelects(["settingsRequestSeasons"]);
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
  if (els.localAccountStatusPill) {
    const configured = Boolean(access.localAuthConfigured);
    els.localAccountStatusPill.textContent = configured ? "Configured" : "Not set";
    els.localAccountStatusPill.classList.toggle("connected", configured);
    els.localAccountStatusPill.classList.toggle("missing", !configured);
  }
}

async function refreshSettings() {
  const [weebarrResponse, connectionResponse] = await Promise.all([
    fetch("/api/settings/weebarr"),
    fetch("/api/settings/seerr"),
  ]);
  if (!weebarrResponse.ok) throw new Error(await readError(weebarrResponse));
  if (!connectionResponse.ok) throw new Error(await readError(connectionResponse));
  updateWeebarr(await weebarrResponse.json());
  updateConnection(await connectionResponse.json());
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
    "Weebarr behavior settings saved. Seasonal lookups will use the new filtering and monitoring rules immediately.",
    "success",
  );
  toast("Weebarr settings saved.");
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
    "Local account saved. Login will now offer username/password alongside Plex whenever both are configured.",
    "success",
  );
  toast("Local account saved.");
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
  els.testRootFolder.textContent = defaults.rootFolder || "Default";

  if (!els.sonarrServerId.value && defaults.serverId) {
    els.sonarrServerId.value = defaults.serverId;
  }
  if (!els.profileId.value && defaults.profileId) {
    els.profileId.value = defaults.profileId;
  }
  if (!els.rootFolder.value && defaults.rootFolder) {
    els.rootFolder.value = defaults.rootFolder;
  }

  showBanner(
    els.connectionBanner,
    "Connection test succeeded. Seerr responded and default Sonarr values were detected.",
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

if (els.weebarrForm) {
  els.weebarrForm.addEventListener("submit", async (event) => {
    try {
      await saveWeebarr(event);
    } catch (error) {
      showBanner(els.weebarrBanner, `Save failed. ${error.message}`, "error");
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

els.themeButtons.forEach((button) => {
  button.addEventListener("click", () => applyTheme(button.dataset.themeChoice));
});

prefersLight.addEventListener("change", () => {
  if (state.theme === "system") applyTheme("system");
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

applyTheme();
initializeCustomSelects();
updateWeebarr(state.weebarr);
updateAccess(state.access);
updateConnection(state.connection);
refreshSettings().catch((error) => {
  showBanner(
    els.connectionBanner,
    `Could not load the saved settings. ${error.message}`,
    "error",
  );
});
