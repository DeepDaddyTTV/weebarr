const authState = {
  page: document.body.dataset.page || "auth",
  mode: document.body.dataset.authMode || "local",
};

const authEls = {
  banner: document.querySelector("#authBanner") || document.querySelector("#setupBanner"),
  localLoginForm: document.querySelector("#localLoginForm"),
  loginUsername: document.querySelector("#loginUsername"),
  loginPassword: document.querySelector("#loginPassword"),
  loginNext: document.querySelector("#loginNext"),
  plexLoginBtn: document.querySelector("#plexLoginBtn"),
  setupForm: document.querySelector("#setupForm"),
  setupMode: document.querySelector("#setupMode"),
  setupModeButtons: document.querySelectorAll("[data-mode-choice]"),
  localFields: document.querySelector("#localSetupFields"),
  plexFields: document.querySelector("#plexSetupFields"),
  setupUsername: document.querySelector("#setupUsername"),
  setupPassword: document.querySelector("#setupPassword"),
  setupConfirmPassword: document.querySelector("#setupConfirmPassword"),
  setupPublicUrl: document.querySelector("#setupPublicUrl"),
  setupPlexAllowedUsers: document.querySelector("#setupPlexAllowedUsers"),
  setupGenerateApiKey: document.querySelector("#setupGenerateApiKey"),
  setupApiKeyWrap: document.querySelector("#setupApiKeyWrap"),
  setupApiKey: document.querySelector("#setupApiKey"),
  setupAdminToken: document.querySelector("#setupAdminToken"),
  setupSuccess: document.querySelector("#setupSuccess"),
  setupKeyCard: document.querySelector("#setupKeyCard"),
  setupGeneratedApiKey: document.querySelector("#setupGeneratedApiKey"),
  setupContinueBtn: document.querySelector("#setupContinueBtn"),
  setupSuccessCopy: document.querySelector("#setupSuccessCopy"),
};

function setBanner(message, tone = "error") {
  if (!authEls.banner) return;
  authEls.banner.textContent = message;
  authEls.banner.dataset.tone = tone;
  authEls.banner.hidden = false;
}

function clearBanner() {
  if (!authEls.banner) return;
  authEls.banner.hidden = true;
  authEls.banner.textContent = "";
  delete authEls.banner.dataset.tone;
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

function setSetupMode(mode) {
  authState.mode = mode;
  if (authEls.setupMode) authEls.setupMode.value = mode;
  authEls.setupModeButtons.forEach((button) => {
    const active = button.dataset.modeChoice === mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  if (authEls.localFields) {
    authEls.localFields.hidden = mode !== "local";
  }
  if (authEls.plexFields) {
    authEls.plexFields.hidden = mode !== "plex";
  }
}

function toggleApiKeyInput() {
  if (!authEls.setupGenerateApiKey || !authEls.setupApiKeyWrap) return;
  authEls.setupApiKeyWrap.hidden = !authEls.setupGenerateApiKey.checked;
}

async function submitLocalLogin(event) {
  event.preventDefault();
  clearBanner();
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: authEls.loginUsername.value.trim(),
      password: authEls.loginPassword.value,
      next: authEls.loginNext.value || "/seasonal",
    }),
  });
  if (!response.ok) {
    setBanner(await readError(response));
    return;
  }
  const payload = await response.json();
  window.location.assign(payload.redirectTo || "/seasonal");
}

function startPlexLogin() {
  const next = encodeURIComponent((window.WEEBARR_AUTH || {}).nextPath || "/seasonal");
  window.location.assign(`/auth/plex/start?next=${next}`);
}

function parseAllowedUsers(value) {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

async function submitSetup(event) {
  event.preventDefault();
  clearBanner();

  const response = await fetch("/api/setup/access", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: authState.mode,
      username: authEls.setupUsername?.value.trim() || "",
      password: authEls.setupPassword?.value || "",
      confirmPassword: authEls.setupConfirmPassword?.value || "",
      publicUrl: authEls.setupPublicUrl?.value.trim() || null,
      plexAllowedUsers: parseAllowedUsers(authEls.setupPlexAllowedUsers?.value || ""),
      generateApiKey: Boolean(authEls.setupGenerateApiKey?.checked),
      apiKey: authEls.setupApiKey?.value.trim() || null,
      adminToken: authEls.setupAdminToken?.value.trim() || null,
    }),
  });

  if (!response.ok) {
    setBanner(await readError(response));
    return;
  }

  const payload = await response.json();
  if (authEls.setupForm) authEls.setupForm.hidden = true;
  if (authEls.setupSuccess) authEls.setupSuccess.hidden = false;
  if (authEls.setupSuccessCopy) {
    authEls.setupSuccessCopy.textContent =
      payload.mode === "plex"
        ? "Weebarr access is configured. Continue to Plex sign-in to start using the dashboard."
        : "Weebarr access is configured. Continue into the dashboard.";
  }
  if (payload.generatedApiKey) {
    authEls.setupKeyCard.hidden = false;
    authEls.setupGeneratedApiKey.textContent = payload.generatedApiKey;
  } else {
    authEls.setupKeyCard.hidden = true;
  }
  authEls.setupContinueBtn.dataset.redirectTo = payload.redirectTo || "/seasonal";
}

function continueAfterSetup() {
  const redirectTo = authEls.setupContinueBtn.dataset.redirectTo || "/seasonal";
  window.location.assign(redirectTo);
}

if (authEls.localLoginForm) {
  authEls.localLoginForm.addEventListener("submit", (event) => {
    void submitLocalLogin(event);
  });
}

if (authEls.plexLoginBtn) {
  authEls.plexLoginBtn.addEventListener("click", startPlexLogin);
}

if (authEls.setupModeButtons.length) {
  authEls.setupModeButtons.forEach((button) => {
    button.addEventListener("click", () => setSetupMode(button.dataset.modeChoice));
  });
}

if (authEls.setupGenerateApiKey) {
  authEls.setupGenerateApiKey.addEventListener("change", toggleApiKeyInput);
  toggleApiKeyInput();
}

if (authEls.setupForm) {
  authEls.setupForm.addEventListener("submit", (event) => {
    void submitSetup(event);
  });
  setSetupMode(authEls.setupMode?.value || "local");
}

if (authEls.setupContinueBtn) {
  authEls.setupContinueBtn.addEventListener("click", continueAfterSetup);
}
