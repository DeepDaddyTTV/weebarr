const backendSetupState = {
  requestSettings: (window.WEEBARR_SETUP_BACKEND || {}).requestSettings || {},
  step: "choice",
  sonarrValidated: false,
  sonarrOptions: {
    rootFolders: [],
    qualityProfiles: [],
    languageProfiles: [],
  },
};

const backendSetupLabels = {
  seerr: "Seerr",
  sonarr: "Sonarr Direct",
};

const backendSetupStepCopy = {
  seerr: {
    title: "Seerr Setup",
    description:
      "Add the Seerr connection Weebarr should use for the current one-click request path.",
    summary: "Current one-click request path.",
  },
  sonarr: {
    title: "Sonarr Direct Setup",
    description:
      "Add the Sonarr Direct defaults Weebarr should use for season-aware adds and updates.",
    summary: "Direct Sonarr lookup, states, and request modal.",
  },
};

const backendSetupSeriesTypeLabels = {
  standard: "Standard",
  anime: "Anime / Absolute",
  daily: "Daily",
};

const backendEls = {
  banner: document.querySelector("#setupBackendBanner"),
  choiceStep: document.querySelector("#setupBackendChoiceStep"),
  form: document.querySelector("#setupBackendForm"),
  modeButtons: Array.from(document.querySelectorAll("[data-backend-mode]")),
  nextButton: document.querySelector("#setupBackendNextBtn"),
  backButton: document.querySelector("#setupBackendBackBtn"),
  skipChoiceButton: document.querySelector("#setupBackendSkipChoiceBtn"),
  skipConfigButton: document.querySelector("#setupBackendSkipConfigBtn"),
  stepTitle: document.querySelector("#setupBackendStepTitle"),
  stepCopy: document.querySelector("#setupBackendStepCopy"),
  selectedLabel: document.querySelector("#setupBackendSelectedLabel"),
  selectedCopy: document.querySelector("#setupBackendSelectedCopy"),
  seerrPanel: document.querySelector("#setupBackendSeerrPanel"),
  sonarrPanel: document.querySelector("#setupBackendSonarrPanel"),
  sonarrValidationNote: document.querySelector("#setupSonarrValidationNote"),
  sonarrValidationCopy: document.querySelector("#setupSonarrValidationCopy"),
  sonarrAdvancedFields: document.querySelector("#setupSonarrAdvancedFields"),
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

function activeBackendStepCopy() {
  return backendSetupStepCopy[activeBackend()] || backendSetupStepCopy.seerr;
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

function savedSonarrSettings() {
  return backendSetupState.requestSettings?.sonarr || {};
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

function setNativeSelectOptions(
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
    return;
  }
  select.value = select.options[0]?.value || "";
}

function resetSonarrOptionFields() {
  setNativeSelectOptions(backendEls.sonarrRootFolderPath, [], {
    emptyLabel: "Validate Sonarr first",
  });
  setNativeSelectOptions(backendEls.sonarrQualityProfileId, [], {
    emptyLabel: "Validate Sonarr first",
  });
  setNativeSelectOptions(backendEls.sonarrLanguageProfileId, [], {
    includeBlankLabel: "Use Sonarr default",
    emptyLabel: null,
  });
}

function renderSonarrValidationState() {
  const sonarrActive = activeBackend() === "sonarr";
  if (backendEls.sonarrValidationNote) {
    backendEls.sonarrValidationNote.hidden = !sonarrActive;
  }
  if (backendEls.sonarrAdvancedFields) {
    backendEls.sonarrAdvancedFields.hidden =
      !sonarrActive || !backendSetupState.sonarrValidated;
  }
  if (backendEls.sonarrValidationCopy) {
    backendEls.sonarrValidationCopy.textContent = backendSetupState.sonarrValidated
      ? "Sonarr validated successfully. Review the live folders and profiles below, then continue."
      : "Enter the Sonarr base URL and API key, then validate Sonarr to load the live root folders and quality profiles before continuing.";
  }
  if (backendEls.testButton) {
    backendEls.testButton.textContent = sonarrActive
      ? backendSetupState.sonarrValidated
        ? "Reload Sonarr Options"
        : "Validate Sonarr"
      : "Test Seerr";
  }
}

function resetSonarrValidation({ resetMetrics = true } = {}) {
  backendSetupState.sonarrValidated = false;
  backendSetupState.sonarrOptions = {
    rootFolders: [],
    qualityProfiles: [],
    languageProfiles: [],
  };
  resetSonarrOptionFields();
  renderSonarrValidationState();
  if (resetMetrics && activeBackend() === "sonarr") {
    resetTestResult();
  }
}

function applySonarrDefaults(result) {
  const saved = savedSonarrSettings();
  const rootFolders = result?.rootFolders || [];
  const qualityProfiles = result?.qualityProfiles || [];
  const languageProfiles = result?.languageProfiles || [];
  const defaults = result?.defaults || {};

  backendSetupState.sonarrValidated = true;
  backendSetupState.sonarrOptions = {
    rootFolders,
    qualityProfiles,
    languageProfiles,
  };

  const rootFolderValue = pickExistingValue(
    rootFolders,
    (item) => item.path,
    [
      backendEls.sonarrRootFolderPath?.value.trim(),
      saved.rootFolderPath,
      defaults.rootFolderPath,
      rootFolders[0]?.path,
    ],
  );
  const qualityProfileValue = pickExistingValue(
    qualityProfiles,
    (item) => item.id,
    [
      backendEls.sonarrQualityProfileId?.value.trim(),
      saved.qualityProfileId,
      defaults.qualityProfileId,
      qualityProfiles[0]?.id,
    ],
  );
  const languageProfileValue = pickExistingValue(
    languageProfiles,
    (item) => item.id,
    [
      backendEls.sonarrLanguageProfileId?.value.trim(),
      saved.languageProfileId,
      defaults.languageProfileId,
    ],
  );

  setNativeSelectOptions(backendEls.sonarrRootFolderPath, rootFolders, {
    getValue: (item) => item.path,
    getLabel: (item) => item.path,
    emptyLabel: "No root folders found",
    selectedValue: rootFolderValue,
  });
  setNativeSelectOptions(backendEls.sonarrQualityProfileId, qualityProfiles, {
    getValue: (item) => item.id,
    getLabel: (item) => item.name,
    emptyLabel: "No quality profiles found",
    selectedValue: qualityProfileValue,
  });
  setNativeSelectOptions(backendEls.sonarrLanguageProfileId, languageProfiles, {
    getValue: (item) => item.id,
    getLabel: (item) => item.name,
    includeBlankLabel: "Use Sonarr default",
    emptyLabel: null,
    selectedValue: languageProfileValue,
  });

  renderSonarrValidationState();
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

function renderStepCopy() {
  const backendName = activeBackendName();
  const copy = activeBackendStepCopy();
  if (backendEls.nextButton) {
    backendEls.nextButton.textContent = `Continue with ${backendName}`;
  }
  if (backendEls.stepTitle) {
    backendEls.stepTitle.textContent = copy.title;
  }
  if (backendEls.stepCopy) {
    backendEls.stepCopy.textContent = copy.description;
  }
  if (backendEls.selectedLabel) {
    backendEls.selectedLabel.textContent = backendName;
  }
  if (backendEls.selectedCopy) {
    backendEls.selectedCopy.textContent = copy.summary;
  }
}

function showStep(step) {
  backendSetupState.step = step === "config" ? "config" : "choice";
  if (backendEls.choiceStep) {
    backendEls.choiceStep.hidden = backendSetupState.step !== "choice";
  }
  if (backendEls.form) {
    backendEls.form.hidden = backendSetupState.step !== "config";
  }
  clearBanner();
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
  renderStepCopy();
  renderSonarrValidationState();
  resetTestResult();
  clearBanner();
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
    if (!backendSetupState.sonarrValidated) missing.push("Validate Sonarr");
    if (!rootFolderPath) missing.push("Root Folder");
    if (!qualityProfileId) missing.push("Quality Profile");
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

async function completeSetup(event) {
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
  const response = await fetch("/api/setup/backend", {
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
  backendSetupState.requestSettings = result.requests || {};
  window.location.assign(result.redirectTo || "/seasonal");
}

async function skipSetup() {
  clearBanner();
  const response = await fetch("/api/setup/backend/skip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      requestBackend: activeBackend(),
    }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const result = await response.json();
  backendSetupState.requestSettings = result.requests || {};
  window.location.assign(result.redirectTo || "/seasonal");
}

backendEls.modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setBackendMode(button.dataset.backendMode || "seerr");
  });
});

if (backendEls.sonarrBaseUrl) {
  ["input", "change"].forEach((eventName) => {
    backendEls.sonarrBaseUrl.addEventListener(eventName, () => {
      resetSonarrValidation();
      clearBanner();
    });
  });
}

if (backendEls.sonarrApiKey) {
  ["input", "change"].forEach((eventName) => {
    backendEls.sonarrApiKey.addEventListener(eventName, () => {
      resetSonarrValidation();
      clearBanner();
    });
  });
}

if (backendEls.nextButton) {
  backendEls.nextButton.addEventListener("click", () => {
    showStep("config");
  });
}

if (backendEls.backButton) {
  backendEls.backButton.addEventListener("click", () => {
    showStep("choice");
  });
}

if (backendEls.skipChoiceButton) {
  backendEls.skipChoiceButton.addEventListener("click", () => {
    void skipSetup().catch((error) => {
      setBanner(`Skip failed. ${error.message}`, "error");
    });
  });
}

if (backendEls.skipConfigButton) {
  backendEls.skipConfigButton.addEventListener("click", () => {
    void skipSetup().catch((error) => {
      setBanner(`Skip failed. ${error.message}`, "error");
    });
  });
}

if (backendEls.testButton) {
  backendEls.testButton.addEventListener("click", () => {
    void testConnection().catch((error) => {
      setBanner(`Connection test failed. ${error.message}`, "error");
    });
  });
}

if (backendEls.form) {
  backendEls.form.addEventListener("submit", (event) => {
    void completeSetup(event).catch((error) => {
      setBanner(`Save failed. ${error.message}`, "error");
    });
  });
}

resetSonarrValidation({ resetMetrics: false });
setBackendMode(activeBackend());
showStep("choice");
