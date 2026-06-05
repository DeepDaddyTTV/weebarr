const themeStorageKey = "weebarr-theme";
const prefersLight = window.matchMedia("(prefers-color-scheme: light)");

const state = {
  theme: "dark",
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
  banner: document.querySelector("#settingsBanner"),
  statusPill: document.querySelector("#settingsStatusPill"),
  themeButtons: document.querySelectorAll("[data-theme-choice]"),
  form: document.querySelector("#connectionForm"),
  accessForm: document.querySelector("#localAccountForm"),
  baseUrl: document.querySelector("#settingsBaseUrl"),
  apiKey: document.querySelector("#settingsApiKey"),
  requestSeasons: document.querySelector("#settingsRequestSeasons"),
  contentFilterMode: document.querySelector("#settingsContentFilterMode"),
  sonarrServerId: document.querySelector("#settingsSonarrServerId"),
  profileId: document.querySelector("#settingsProfileId"),
  rootFolder: document.querySelector("#settingsRootFolder"),
  languageProfileId: document.querySelector("#settingsLanguageProfileId"),
  requestUserId: document.querySelector("#settingsRequestUserId"),
  tags: document.querySelector("#settingsTags"),
  adminToken: document.querySelector("#settingsAdminToken"),
  accessBanner: document.querySelector("#accessSettingsBanner"),
  localAccountUsername: document.querySelector("#localAccountUsername"),
  localAccountPassword: document.querySelector("#localAccountPassword"),
  localAccountConfirmPassword: document.querySelector(
    "#localAccountConfirmPassword",
  ),
  localAccountStatusPill: document.querySelector("#localAccountStatusPill"),
  saveLocalAccountBtn: document.querySelector("#saveLocalAccountBtn"),
  currentAuthSignIn: document.querySelector("#currentAuthSignIn"),
  testButton: document.querySelector("#testConnectionBtn"),
  saveButton: document.querySelector("#saveConnectionBtn"),
  currentBaseUrl: document.querySelector("#currentBaseUrl"),
  currentApiKey: document.querySelector("#currentApiKey"),
  currentRequestSeasons: document.querySelector("#currentRequestSeasons"),
  currentContentFilter: document.querySelector("#currentContentFilter"),
  currentProfileSummary: document.querySelector("#currentProfileSummary"),
  currentRootFolder: document.querySelector("#currentRootFolder"),
  currentTags: document.querySelector("#currentTags"),
  testServerCount: document.querySelector("#testServerCount"),
  testServerName: document.querySelector("#testServerName"),
  testProfileId: document.querySelector("#testProfileId"),
  testRootFolder: document.querySelector("#testRootFolder"),
};

const customSelectRoots = [...document.querySelectorAll("[data-ui-select]")];
const customSelects = new Map();

function toast(message) {
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

function showBanner(message, tone = "info") {
  els.banner.textContent = message;
  els.banner.dataset.tone = tone;
  els.banner.hidden = false;
}

function clearBanner() {
  els.banner.hidden = true;
  els.banner.textContent = "";
  delete els.banner.dataset.tone;
}

function showAccessBanner(message, tone = "info") {
  if (!els.accessBanner) return;
  els.accessBanner.textContent = message;
  els.accessBanner.dataset.tone = tone;
  els.accessBanner.hidden = false;
}

function clearAccessBanner() {
  if (!els.accessBanner) return;
  els.accessBanner.hidden = true;
  els.accessBanner.textContent = "";
  delete els.accessBanner.dataset.tone;
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

function payloadFromForm() {
  return {
    baseUrl: els.baseUrl.value.trim(),
    requestSeasons: els.requestSeasons.value,
    contentFilterMode: els.contentFilterMode.value,
    sonarrServerId: parseOptionalInt(els.sonarrServerId.value),
    profileId: parseOptionalInt(els.profileId.value),
    rootFolder: els.rootFolder.value.trim() || null,
    languageProfileId: parseOptionalInt(els.languageProfileId.value),
    requestUserId: parseOptionalInt(els.requestUserId.value),
    tags: parseTags(els.tags.value),
    adminToken: els.adminToken.value.trim() || null,
  };
}

function localAccountPayload() {
  return {
    username: els.localAccountUsername.value.trim(),
    password: els.localAccountPassword.value,
    confirmPassword: els.localAccountConfirmPassword.value,
  };
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

function updateSummary(connection) {
  state.connection = connection;
  els.currentBaseUrl.textContent = connection.baseUrl || "Not set";
  els.currentApiKey.textContent = connection.apiKeyPreview || "Not set";
  els.currentRequestSeasons.textContent = connection.requestSeasons || "all";
  els.currentContentFilter.textContent =
    contentFilterLabels[connection.contentFilterMode] || "Hide NSFW";
  els.currentProfileSummary.textContent = `${connection.sonarrServerId || "Default"} / ${connection.profileId || "Default"}`;
  els.currentRootFolder.textContent = connection.rootFolder || "Default";
  els.currentTags.textContent = connection.tags?.length ? connection.tags.join(", ") : "None";
  els.statusPill.textContent = connection.configured ? "Configured" : "Missing";
  els.statusPill.classList.toggle("connected", connection.configured);
  els.statusPill.classList.toggle("missing", !connection.configured);
  els.apiKey.placeholder = connection.hasApiKey
    ? `Stored ${connection.apiKeyPreview} (leave blank to keep)`
    : "Paste a Seerr API key";
  if (connection.contentFilterMode) {
    els.contentFilterMode.value = connection.contentFilterMode;
  }
  syncCustomSelects(["settingsRequestSeasons", "settingsContentFilterMode"]);
}

function updateAccess(access) {
  state.access = access;
  if (els.localAccountUsername && !document.activeElement?.isSameNode(els.localAccountUsername)) {
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
  if (els.saveLocalAccountBtn) {
    els.saveLocalAccountBtn.textContent = access.localAuthConfigured
      ? "Update Local Account"
      : "Create Local Account";
  }
}

async function refreshConnection() {
  const response = await fetch("/api/settings/seerr");
  if (!response.ok) throw new Error(await response.text());
  const connection = await response.json();
  updateSummary(connection);
  return connection;
}

async function saveLocalAccount(event) {
  event.preventDefault();
  clearAccessBanner();

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
  showAccessBanner(
    "Local account saved. Login will now offer username/password alongside Plex whenever both are configured.",
    "success",
  );
  toast("Local account saved.");
}

async function testConnection() {
  clearBanner();
  const payload = payloadFromForm();
  if (!payload.baseUrl && !state.connection.baseUrl) {
    showBanner("Add a Seerr base URL before testing the connection.", "warn");
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

  showBanner("Connection test succeeded. Seerr responded and default Sonarr values were detected.", "success");
  toast("Seerr connection test passed.");
}

async function saveConnection(event) {
  event.preventDefault();
  clearBanner();

  const apiKey = els.apiKey.value.trim();
  const payload = payloadFromForm();
  const response = await fetch("/api/settings/seerr", {
    method: "PUT",
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
  updateSummary(result.connection);
  els.apiKey.value = "";
  showBanner("Connection settings saved. New requests will use the updated Seerr settings immediately.", "success");
  toast("Connection settings saved.");
}

els.testButton.addEventListener("click", async () => {
  try {
    await testConnection();
  } catch (error) {
    showBanner(`Connection test failed. ${error.message}`, "error");
  }
});

els.form.addEventListener("submit", async (event) => {
  try {
    await saveConnection(event);
  } catch (error) {
    showBanner(`Save failed. ${error.message}`, "error");
  }
});

if (els.accessForm) {
  els.accessForm.addEventListener("submit", async (event) => {
    try {
      await saveLocalAccount(event);
    } catch (error) {
      showAccessBanner(`Save failed. ${error.message}`, "error");
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
updateAccess(state.access);
refreshConnection().catch((error) => {
  showBanner(`Could not load the saved connection settings. ${error.message}`, "error");
});
