const authState = {
  page: document.body.dataset.page || "auth",
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
  setupAdminToken: document.querySelector("#setupAdminToken"),
  setupSuccess: document.querySelector("#setupSuccess"),
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
      "The admin account is ready. Continue into Weebarr or come back to the login screen later to use Plex.";
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

if (authEls.setupForm) {
  authEls.setupForm.addEventListener("submit", (event) => {
    void submitSetup(event);
  });
}

if (authEls.setupContinueBtn) {
  authEls.setupContinueBtn.addEventListener("click", continueAfterSetup);
}
