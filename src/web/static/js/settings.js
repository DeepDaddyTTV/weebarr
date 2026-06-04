const themeStorageKey = "weebarr-theme";
const prefersLight = window.matchMedia("(prefers-color-scheme: light)");

const state = {
  theme: "dark",
  connection: window.WEEBARR_CONNECTION || {},
};

const els = {
  toast: document.querySelector("#toast"),
  banner: document.querySelector("#settingsBanner"),
  statusPill: document.querySelector("#settingsStatusPill"),
  themeButtons: document.querySelectorAll("[data-theme-choice]"),
  form: document.querySelector("#connectionForm"),
  baseUrl: document.querySelector("#settingsBaseUrl"),
  apiKey: document.querySelector("#settingsApiKey"),
  requestSeasons: document.querySelector("#settingsRequestSeasons"),
  sonarrServerId: document.querySelector("#settingsSonarrServerId"),
  profileId: document.querySelector("#settingsProfileId"),
  rootFolder: document.querySelector("#settingsRootFolder"),
  languageProfileId: document.querySelector("#settingsLanguageProfileId"),
  requestUserId: document.querySelector("#settingsRequestUserId"),
  tags: document.querySelector("#settingsTags"),
  adminToken: document.querySelector("#settingsAdminToken"),
  testButton: document.querySelector("#testConnectionBtn"),
  saveButton: document.querySelector("#saveConnectionBtn"),
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
};

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

function payloadFromForm() {
  return {
    baseUrl: els.baseUrl.value.trim(),
    requestSeasons: els.requestSeasons.value,
    sonarrServerId: parseOptionalInt(els.sonarrServerId.value),
    profileId: parseOptionalInt(els.profileId.value),
    rootFolder: els.rootFolder.value.trim() || null,
    languageProfileId: parseOptionalInt(els.languageProfileId.value),
    requestUserId: parseOptionalInt(els.requestUserId.value),
    tags: parseTags(els.tags.value),
    adminToken: els.adminToken.value.trim() || null,
  };
}

function updateSummary(connection) {
  state.connection = connection;
  els.currentBaseUrl.textContent = connection.baseUrl || "Not set";
  els.currentApiKey.textContent = connection.apiKeyPreview || "Not set";
  els.currentRequestSeasons.textContent = connection.requestSeasons || "all";
  els.currentProfileSummary.textContent = `${connection.sonarrServerId || "Default"} / ${connection.profileId || "Default"}`;
  els.currentRootFolder.textContent = connection.rootFolder || "Default";
  els.currentTags.textContent = connection.tags?.length ? connection.tags.join(", ") : "None";
  els.statusPill.textContent = connection.configured ? "Configured" : "Missing";
  els.statusPill.classList.toggle("connected", connection.configured);
  els.statusPill.classList.toggle("missing", !connection.configured);
  els.apiKey.placeholder = connection.hasApiKey
    ? `Stored ${connection.apiKeyPreview} (leave blank to keep)`
    : "Paste a Seerr API key";
}

async function refreshConnection() {
  const response = await fetch("/api/settings/seerr");
  if (!response.ok) throw new Error(await response.text());
  const connection = await response.json();
  updateSummary(connection);
  return connection;
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

els.themeButtons.forEach((button) => {
  button.addEventListener("click", () => applyTheme(button.dataset.themeChoice));
});

prefersLight.addEventListener("change", () => {
  if (state.theme === "system") applyTheme("system");
});

applyTheme();
refreshConnection().catch((error) => {
  showBanner(`Could not load the saved connection settings. ${error.message}`, "error");
});
