const authState = {
  page: document.body.dataset.page || "auth",
  setupMode: (window.WEEBARR_SETUP || {}).defaultMode || "local",
};

const authEls = {
  banner: document.querySelector("#authBanner") || document.querySelector("#setupBanner"),
  localLoginForm: document.querySelector("#localLoginForm"),
  loginUsername: document.querySelector("#loginUsername"),
  loginPassword: document.querySelector("#loginPassword"),
  loginNext: document.querySelector("#loginNext"),
  plexLoginBtn: document.querySelector("#plexLoginBtn"),
  setupForm: document.querySelector("#setupForm"),
  setupUsername: document.querySelector("#setupUsername"),
  setupPassword: document.querySelector("#setupPassword"),
  setupConfirmPassword: document.querySelector("#setupConfirmPassword"),
  setupSuccess: document.querySelector("#setupSuccess"),
  setupContinueBtn: document.querySelector("#setupContinueBtn"),
  setupSuccessCopy: document.querySelector("#setupSuccessCopy"),
  setupPlexPanel: document.querySelector("#setupPlexPanel"),
  setupPlexBtn: document.querySelector("#setupPlexBtn"),
  setupModeButtons: Array.from(document.querySelectorAll("[data-setup-mode]")),
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

function startPlexLogin({ setup = false } = {}) {
  const params = new URLSearchParams();
  if (setup) {
    params.set("setup", "1");
  } else {
    params.set("next", (window.WEEBARR_AUTH || {}).nextPath || "/seasonal");
  }
  window.location.assign(`/auth/plex/start?${params.toString()}`);
}

function setSetupMode(mode) {
  authState.setupMode = mode === "plex" ? "plex" : "local";
  authEls.setupModeButtons.forEach((button) => {
    const active = button.dataset.setupMode === authState.setupMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  if (authEls.setupForm) {
    authEls.setupForm.hidden = authState.setupMode !== "local";
  }
  if (authEls.setupPlexPanel) {
    authEls.setupPlexPanel.hidden = authState.setupMode !== "plex";
  }
}

async function submitSetup(event) {
  event.preventDefault();
  clearBanner();

  const response = await fetch("/api/setup/access", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: authEls.setupUsername?.value.trim() || "",
      password: authEls.setupPassword?.value || "",
      confirmPassword: authEls.setupConfirmPassword?.value || "",
    }),
  });

  if (!response.ok) {
    setBanner(await readError(response));
    return;
  }

  const payload = await response.json();
  if (authEls.setupForm) authEls.setupForm.hidden = true;
  if (authEls.setupSuccess) authEls.setupSuccess.hidden = false;
  const redirectTo = payload.redirectTo || "/login";
  const continuesToBackend = redirectTo.startsWith("/setup/backend");
  if (authEls.setupSuccessCopy) {
    authEls.setupSuccessCopy.textContent =
      continuesToBackend
        ? "The admin account is ready. Continue to request-backend setup."
        : "The admin account is ready. Continue to the sign-in screen.";
  }
  if (authEls.setupContinueBtn) {
    authEls.setupContinueBtn.textContent = continuesToBackend
      ? "Continue to Request Backend"
      : "Continue";
  }
  authEls.setupContinueBtn.dataset.redirectTo = redirectTo;
}

function continueAfterSetup() {
  const redirectTo = authEls.setupContinueBtn.dataset.redirectTo || "/login";
  window.location.assign(redirectTo);
}

if (authEls.localLoginForm) {
  authEls.localLoginForm.addEventListener("submit", (event) => {
    void submitLocalLogin(event);
  });
}

if (authEls.plexLoginBtn) {
  authEls.plexLoginBtn.addEventListener("click", () => {
    startPlexLogin();
  });
}

if (authEls.setupForm) {
  authEls.setupForm.addEventListener("submit", (event) => {
    void submitSetup(event);
  });
}

if (authEls.setupPlexBtn) {
  authEls.setupPlexBtn.addEventListener("click", () => {
    startPlexLogin({ setup: true });
  });
}

if (authEls.setupModeButtons.length) {
  authEls.setupModeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setSetupMode(button.dataset.setupMode || "local");
    });
  });
  setSetupMode(authState.setupMode);
}

if (authEls.setupContinueBtn) {
  authEls.setupContinueBtn.addEventListener("click", continueAfterSetup);
}
