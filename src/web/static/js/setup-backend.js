const backendSetupState = {
  requestSettings: (window.WEEBARR_SETUP_BACKEND || {}).requestSettings || {},
};

const backendSetupLabels = {
  seerr: "Seerr",
  sonarr: "Sonarr Direct",
};

const backendSetupSeriesTypeLabels = {
  standard: "Standard",
  anime: "Anime / Absolute",
  daily: "Daily",
};

const backendEls = {
  banner: document.querySelector("#setupBackendBanner"),
  form: document.querySelector("#setupBackendForm"),
  modeButtons: Array.from(document.querySelectorAll("[data-backend-mode]")),
  seerrPanel: document.querySelector("#setupBackendSeerrPanel"),
  sonarrPanel: document.querySelector("#setupBackendSonarrPanel"),
  seerrBaseUrl: document.querySelector("#setupSeerrBaseUrl"),
  seerrApiKey: document.querySelector("#setupSeerrApiKey"),
  seerrRequestSeasons: document.querySelector("#setupSeerrRequestSeasons"),
  sonarrBaseUrl: document.querySelector("#setupSonarrBaseUrl"),
  sonarrApiKey: document.querySelector("#setupSonarrApiKey"),
  sonarrRootFolderPath: document.querySelector("#setupSonarrRootFolderPath"),
  sonarrQualityProfileId: document.querySelector("#setupSonarrQualityProfileId"),
  sonarrSeriesType: document.querySelector("#setupSonarrSeriesType"),
  sonarrDefaultMonitorMode: document.querySelector(
    "#setupSonarrDefaultMonitorMode",
  ),
  sonarrDefaultSearchOnAdd: document.querySelector(
    "#setupSonarrDefaultSearchOnAdd",
  ),
  sonarrDefaultSeasonFolder: document.querySelector(
    "#setupSonarrDefaultSeasonFolder",
  ),
  sonarrLanguageProfileId: document.querySelector(
    "#setupSonarrLanguageProfileId",
  ),
  testButton: document.querySelector("#setupBackendTestBtn"),
  metricOneLabel: document.querySelector("#setupBackendMetricOneLabel"),
  metricTwoLabel: document.querySelector("#setupBackendMetricTwoLabel"),
  metricThreeLabel: document.querySelector("#setupBackendMetricThreeLabel"),
  metricFourLabel: document.querySelector("#setupBackendMetricFourLabel"),
  metricFiveLabel: document.querySelector("#setupBackendMetricFiveLabel"),
  metricOneValue: document.querySelector("#setupBackendMetricOneValue"),
  metricTwoValue: document.querySelector("#setupBackendMetricTwoValue"),
  metricThreeValue: document.querySelector("#setupBackendMetricThreeValue"),
  metricFourValue: document.querySelector("#setupBackendMetricFourValue"),
  metricFiveValue: document.querySelector("#setupBackendMetricFiveValue"),
};

function activeBackend() {
  return backendSetupState.requestSettings?.requestBackend === "sonarr"
    ? "sonarr"
    : "seerr";
}

function activeBackendName() {
  return backendSetupLabels[activeBackend()] || "Seerr";
}

function setBanner(message, tone = "error") {
  if (!backendEls.banner) return;
  backendEls.banner.textContent = message;
  backendEls.banner.dataset.tone = tone;
  backendEls.banner.hidden = false;
}

function clearBanner() {
  if (!backendEls.banner) return;
  backendEls.banner.hidden = true;
  backendEls.banner.textContent = "";
  delete backendEls.banner.dataset.tone;
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

function parseOptionalInt(value) {
  if (!value || !String(value).trim()) return null;
  return Number(value);
}

function seerrPayload() {
  return {
    baseUrl: backendEls.seerrBaseUrl?.value.trim() || "",
    requestSeasons: backendEls.seerrRequestSeasons?.value || "all",
  };
}

function sonarrPayload() {
  return {
    baseUrl: backendEls.sonarrBaseUrl?.value.trim() || "",
    rootFolderPath: backendEls.sonarrRootFolderPath?.value.trim() || null,
    qualityProfileId: parseOptionalInt(backendEls.sonarrQualityProfileId?.value),
    seriesType: backendEls.sonarrSeriesType?.value || "anime",
    defaultMonitorMode: backendEls.sonarrDefaultMonitorMode?.value || "all",
    defaultSearchOnAdd: Boolean(backendEls.sonarrDefaultSearchOnAdd?.checked),
    defaultSeasonFolder: Boolean(backendEls.sonarrDefaultSeasonFolder?.checked),
    languageProfileId: parseOptionalInt(backendEls.sonarrLanguageProfileId?.value),
    tags: backendSetupState.requestSettings?.sonarr?.tags || [],
  };
}

function resetTestResult() {
  const sonarrActive = activeBackend() === "sonarr";
  if (!backendEls.metricOneLabel) return;
  if (sonarrActive) {
    backendEls.metricOneLabel.textContent = "Root Folders";
    backendEls.metricTwoLabel.textContent = "Quality Profiles";
    backendEls.metricThreeLabel.textContent = "Language Profiles";
    backendEls.metricFourLabel.textContent = "Default Series Type";
    backendEls.metricFiveLabel.textContent = "Detected Root";
  } else {
    backendEls.metricOneLabel.textContent = "Server Count";
    backendEls.metricTwoLabel.textContent = "Default Server";
    backendEls.metricThreeLabel.textContent = "Detected Profile";
    backendEls.metricFourLabel.textContent = "Detected Series Type";
    backendEls.metricFiveLabel.textContent = "Detected Root";
  }
  [
    backendEls.metricOneValue,
    backendEls.metricTwoValue,
    backendEls.metricThreeValue,
    backendEls.metricFourValue,
    backendEls.metricFiveValue,
  ].forEach((element) => {
    if (element) {
      element.textContent = "--";
    }
  });
}

function setBackendMode(mode) {
  backendSetupState.requestSettings = {
    ...(backendSetupState.requestSettings || {}),
    requestBackend: mode === "sonarr" ? "sonarr" : "seerr",
  };
  backendEls.modeButtons.forEach((button) => {
    const active = button.dataset.backendMode === activeBackend();
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  if (backendEls.seerrPanel) {
    backendEls.seerrPanel.hidden = activeBackend() !== "seerr";
  }
  if (backendEls.sonarrPanel) {
    backendEls.sonarrPanel.hidden = activeBackend() !== "sonarr";
  }
  clearBanner();
  resetTestResult();
}

function missingRequiredFields() {
  const saved = backendSetupState.requestSettings || {};
  if (activeBackend() === "sonarr") {
    const sonarr = saved.sonarr || {};
    const missing = [];
    const baseUrl = backendEls.sonarrBaseUrl?.value.trim() || sonarr.baseUrl;
    const apiKey = backendEls.sonarrApiKey?.value.trim() || sonarr.apiKeyPreview;
    const rootFolderPath =
      backendEls.sonarrRootFolderPath?.value.trim() || sonarr.rootFolderPath;
    const qualityProfileId =
      parseOptionalInt(backendEls.sonarrQualityProfileId?.value) ||
      sonarr.qualityProfileId;
    const seriesType = backendEls.sonarrSeriesType?.value || sonarr.seriesType;
    if (!baseUrl) missing.push("Sonarr Base URL");
    if (!apiKey) missing.push("API Key");
    if (!rootFolderPath) missing.push("Root Folder Path");
    if (!qualityProfileId) missing.push("Quality Profile ID");
    if (!seriesType) missing.push("Series Type");
    return missing;
  }
  const seerr = saved.seerr || {};
  const missing = [];
  const baseUrl = backendEls.seerrBaseUrl?.value.trim() || seerr.baseUrl;
  const apiKey = backendEls.seerrApiKey?.value.trim() || seerr.apiKeyPreview;
  if (!baseUrl) missing.push("Seerr Base URL");
  if (!apiKey) missing.push("API Key");
  return missing;
}

function applySonarrDefaults(result) {
  const defaults = result?.defaults || {};
  if (
    backendEls.sonarrRootFolderPath &&
    !backendEls.sonarrRootFolderPath.value.trim() &&
    defaults.rootFolderPath
  ) {
    backendEls.sonarrRootFolderPath.value = defaults.rootFolderPath;
  }
  if (
    backendEls.sonarrQualityProfileId &&
    !backendEls.sonarrQualityProfileId.value.trim() &&
    defaults.qualityProfileId
  ) {
    backendEls.sonarrQualityProfileId.value = String(defaults.qualityProfileId);
  }
}

function renderTestResult(result) {
  if (!result) {
    resetTestResult();
    return;
  }
  const sonarrActive = activeBackend() === "sonarr";
  if (sonarrActive) {
    applySonarrDefaults(result);
    backendEls.metricOneLabel.textContent = "Root Folders";
    backendEls.metricTwoLabel.textContent = "Quality Profiles";
    backendEls.metricThreeLabel.textContent = "Language Profiles";
    backendEls.metricFourLabel.textContent = "Default Series Type";
    backendEls.metricFiveLabel.textContent = "Detected Root";
    backendEls.metricOneValue.textContent = String(result.rootFolderCount ?? "--");
    backendEls.metricTwoValue.textContent = String(
      result.qualityProfileCount ?? "--",
    );
    backendEls.metricThreeValue.textContent = String(
      result.languageProfileCount ?? "--",
    );
    backendEls.metricFourValue.textContent =
      backendSetupSeriesTypeLabels[result.defaults?.seriesType] ||
      result.defaults?.seriesType ||
      "Anime / Absolute";
    backendEls.metricFiveValue.textContent =
      result.defaults?.rootFolderPath || "Not detected";
    return;
  }
  backendEls.metricOneLabel.textContent = "Server Count";
  backendEls.metricTwoLabel.textContent = "Default Server";
  backendEls.metricThreeLabel.textContent = "Detected Profile";
  backendEls.metricFourLabel.textContent = "Detected Series Type";
  backendEls.metricFiveLabel.textContent = "Detected Root";
  backendEls.metricOneValue.textContent = String(result.serverCount ?? "--");
  backendEls.metricTwoValue.textContent = result.defaults?.serverName || "None";
  backendEls.metricThreeValue.textContent = String(
    result.defaults?.profileId || "Default",
  );
  backendEls.metricFourValue.textContent =
    backendSetupSeriesTypeLabels[result.defaults?.seriesType] ||
    result.defaults?.seriesType ||
    "Not exposed by Seerr";
  backendEls.metricFiveValue.textContent = result.defaults?.rootFolder || "Default";
}

async function testConnection() {
  clearBanner();
  const sonarrActive = activeBackend() === "sonarr";
  const saved = backendSetupState.requestSettings || {};
  const baseUrl = sonarrActive
    ? backendEls.sonarrBaseUrl?.value.trim() || saved.sonarr?.baseUrl
    : backendEls.seerrBaseUrl?.value.trim() || saved.seerr?.baseUrl;
  const apiKey = sonarrActive
    ? backendEls.sonarrApiKey?.value.trim()
    : backendEls.seerrApiKey?.value.trim();
  const hasSavedKey = sonarrActive
    ? Boolean(saved.sonarr?.apiKeyPreview)
    : Boolean(saved.seerr?.apiKeyPreview);
  if (!baseUrl) {
    setBanner(
      `Add a ${activeBackendName()} base URL before testing the connection.`,
      "warn",
    );
    return;
  }
  if (!apiKey && !hasSavedKey) {
    setBanner(
      `Add an API key before testing the ${activeBackendName()} connection.`,
      "warn",
    );
    return;
  }
  const response = await fetch("/api/settings/requests/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requestBackend: activeBackend(),
      seerr: {
        ...seerrPayload(),
        apiKey: sonarrActive ? undefined : (apiKey || undefined),
      },
      sonarr: {
        ...sonarrPayload(),
        apiKey: sonarrActive ? (apiKey || undefined) : undefined,
      },
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  renderTestResult(result);
  setBanner(
    sonarrActive
      ? "Connection test succeeded. Sonarr Direct responded and Weebarr detected the available folders and profiles."
      : "Connection test succeeded. Seerr responded and Weebarr detected its current anime defaults.",
    "success",
  );
}

async function saveBackend(event) {
  event.preventDefault();
  clearBanner();
  const missing = missingRequiredFields();
  if (missing.length) {
    setBanner(
      `Add the required ${activeBackendName()} fields before continuing: ${missing.join(", ")}.`,
      "warn",
    );
    return;
  }

  const sonarrActive = activeBackend() === "sonarr";
  const apiKey = sonarrActive
    ? backendEls.sonarrApiKey?.value.trim()
    : backendEls.seerrApiKey?.value.trim();
  const response = await fetch("/api/settings/requests", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requestBackend: activeBackend(),
      seerr: {
        ...seerrPayload(),
        apiKey: sonarrActive ? undefined : (apiKey || undefined),
      },
      sonarr: {
        ...sonarrPayload(),
        apiKey: sonarrActive ? (apiKey || undefined) : undefined,
      },
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  backendSetupState.requestSettings = result.requests || {};
  if (!result.requestBackendConfigured) {
    setBanner(
      `${activeBackendName()} was saved, but Weebarr still considers it incomplete. Review the required fields and try again.`,
      "warn",
    );
    return;
  }
  window.location.assign("/seasonal");
}

backendEls.modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setBackendMode(button.dataset.backendMode || "seerr");
  });
});

if (backendEls.testButton) {
  backendEls.testButton.addEventListener("click", () => {
    void testConnection().catch((error) => {
      setBanner(`Connection test failed. ${error.message}`, "error");
    });
  });
}

if (backendEls.form) {
  backendEls.form.addEventListener("submit", (event) => {
    void saveBackend(event).catch((error) => {
      setBanner(`Save failed. ${error.message}`, "error");
    });
  });
}

setBackendMode(activeBackend());
