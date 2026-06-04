const state = {
  season: window.WEEBARR_DEFAULT_SEASON || "SPRING",
  year: window.WEEBARR_DEFAULT_YEAR || new Date().getFullYear(),
  items: [],
  selected: null,
  query: "",
  filter: "all",
  audioFilter: "all",
  sort: "popularity",
  page: 1,
  pageSize: 12,
  theme: "dark",
  filterOpen: false,
};

const els = {
  season: document.querySelector("#seasonSelect"),
  filterSeason: document.querySelector("#filterSeasonSelect"),
  year: document.querySelector("#yearInput"),
  prevSeason: document.querySelector("#prevSeasonBtn"),
  nextSeason: document.querySelector("#nextSeasonBtn"),
  refresh: document.querySelector("#refreshBtn"),
  filterButton: document.querySelector("#filterBtn"),
  filterMenu: document.querySelector("#filterMenu"),
  search: document.querySelector("#searchInput"),
  filter: document.querySelector("#statusFilter"),
  sort: document.querySelector("#sortSelect"),
  sections: document.querySelector("#animeSections"),
  spotlight: document.querySelector("#spotlight"),
  toast: document.querySelector("#toast"),
  themeButtons: document.querySelectorAll("[data-theme-choice]"),
  manageConnection: document.querySelector("#manageConnectionBtn"),
  connectionModal: document.querySelector("#connectionModal"),
  connectionSummary: document.querySelector("#connectionSummary"),
  connectionStatus: document.querySelector("#connectionStatus"),
  connectionRequestSeasons: document.querySelector("#connectionRequestSeasons"),
  stats: {
    total: document.querySelector("#statTotal"),
    requestable: document.querySelector("#statRequestable"),
    requested: document.querySelector("#statRequested"),
    airingSoon: document.querySelector("#statAiringSoon"),
  },
};

const seasonOrder = ["WINTER", "SPRING", "SUMMER", "FALL"];
const themeStorageKey = "weebarr-theme";
const prefersLight = window.matchMedia("(prefers-color-scheme: light)");

function toast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => els.toast.classList.remove("show"), 3600);
}

function formatNumber(value) {
  if (value === null || value === undefined) return "--";
  return new Intl.NumberFormat().format(value);
}

function formatDate(value) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatAiring(nextAiring) {
  if (!nextAiring) return "No airing date";
  const date = new Date(nextAiring.airingAt);
  const when = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
  return `Ep ${nextAiring.episode} • ${when}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function plainDescription(value, limit = 340) {
  const text = String(value || "No description from AniList.")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return escapeHtml(text.length > limit ? `${text.slice(0, limit - 1)}…` : text);
}

function titleCaseSeason(season) {
  return `${season[0]}${season.slice(1).toLowerCase()}`;
}

function resetPage() {
  state.page = 1;
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

function updateSeasonControls() {
  els.season.value = state.season;
  els.year.value = state.year;
  [...els.filterSeason.options].forEach((option) => {
    option.textContent = `${titleCaseSeason(option.value)} ${state.year}`;
    option.selected = option.value === state.season;
  });
}

function shiftSeason(delta) {
  const index = seasonOrder.indexOf(state.season);
  let nextIndex = index + delta;
  let year = Number(state.year);
  if (nextIndex < 0) {
    nextIndex = seasonOrder.length - 1;
    year -= 1;
  } else if (nextIndex >= seasonOrder.length) {
    nextIndex = 0;
    year += 1;
  }
  state.season = seasonOrder[nextIndex];
  state.year = year;
  resetPage();
  updateSeasonControls();
  loadSeason();
}

function audioState(item) {
  return item.audio || {
    state: "unknown",
    label: "Audio ?",
    englishDub: null,
    sourceLanguage: null,
    confidence: "missing",
  };
}

function audioTooltip(item) {
  const audio = audioState(item);
  if (audio.state === "en_dubbed") {
    return "English dub detected from MAL voice actor data.";
  }
  if (audio.englishDub === false) {
    return "No English voice actors were found in MAL character data.";
  }
  return "Dub status could not be confirmed. Showing source-language fallback.";
}

function audioFilterMatches(item) {
  const audio = audioState(item);
  if (state.audioFilter === "all") return true;
  if (state.audioFilter === "en_dubbed") return audio.englishDub === true;
  if (state.audioFilter === "source_only") {
    return audio.englishDub === false || ["ja_only", "ch_only"].includes(audio.state);
  }
  if (state.audioFilter === "unknown") return audio.englishDub === null;
  return audio.sourceLanguage === state.audioFilter;
}

function visibleItems() {
  const query = state.query.trim().toLowerCase();
  let items = [...state.items];
  if (query) {
    items = items.filter((item) => {
      const audio = audioState(item);
      const haystack = [
        item.title,
        item.romajiTitle,
        item.englishTitle,
        item.nativeTitle,
        audio.label,
        audio.sourceLanguage,
        ...(item.genres || []),
        ...(item.studios || []),
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }
  if (state.filter !== "all") {
    items = items.filter((item) => {
      const seerr = item.seerr || {};
      if (state.filter === "requestable") {
        return seerr.state === "requestable" || seerr.state === "partial";
      }
      return seerr.state === state.filter;
    });
  }
  items = items.filter(audioFilterMatches);
  if (state.sort === "score") {
    items.sort((a, b) => (b.averageScore || 0) - (a.averageScore || 0));
  } else if (state.sort === "airing") {
    items.sort((a, b) => {
      const left = a.nextAiring?.airingAt
        ? new Date(a.nextAiring.airingAt).getTime()
        : Number.MAX_SAFE_INTEGER;
      const right = b.nextAiring?.airingAt
        ? new Date(b.nextAiring.airingAt).getTime()
        : Number.MAX_SAFE_INTEGER;
      return left - right;
    });
  } else {
    items.sort((a, b) => a.rank - b.rank);
  }
  return items;
}

function renderStats(stats) {
  const soonCutoff = Date.now() + 7 * 24 * 60 * 60 * 1000;
  const airingSoon = state.items.filter((item) => {
    if (!item.nextAiring?.airingAt) return false;
    const airingAt = new Date(item.nextAiring.airingAt).getTime();
    return airingAt >= Date.now() && airingAt <= soonCutoff;
  }).length;
  els.stats.total.textContent = formatNumber(stats.total);
  els.stats.requestable.textContent = formatNumber(stats.requestable);
  els.stats.requested.textContent = formatNumber(stats.requested);
  els.stats.airingSoon.textContent = formatNumber(airingSoon);
}

function statusLabel(item) {
  const seerr = item.seerr || {};
  if (seerr.state === "partial") return "Not Requested";
  return seerr.label || "Unknown";
}

function cardTemplate(item) {
  const seerr = item.seerr || {};
  const audio = audioState(item);
  const disabled = !seerr.requestable;
  const buttonText = seerr.state === "partial" ? "Request Missing" : "Request in Seerr";
  const isSelected = state.selected && String(state.selected.id) === String(item.id);
  return `
    <article class="anime-card ${isSelected ? "selected" : ""}" data-id="${item.id}">
      <div class="poster">
        ${item.cover ? `<img src="${item.cover}" alt="${escapeHtml(item.title)} poster" loading="lazy" />` : ""}
        <span class="rank">#${item.rank}</span>
      </div>
      <div class="card-body">
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.romajiTitle || item.englishTitle || item.title)}</p>
        <div class="meta">${(item.genres || []).slice(0, 3).map(escapeHtml).join(", ") || escapeHtml(item.format || "TV")}</div>
        <div class="score-row">
          <span>★ ${item.averageScore ? (item.averageScore / 10).toFixed(2) : "--"}</span>
          <span>♨ ${formatNumber(item.popularity)}</span>
          <span class="audio-chip ${escapeHtml(audio.state)}" title="${escapeHtml(audioTooltip(item))}">${escapeHtml(audio.label)}</span>
        </div>
        <div class="next-line"><strong>Next Episode</strong>${formatAiring(item.nextAiring)}</div>
        <div class="card-foot">
          <span class="dot-status ${seerr.state}"><i></i>${escapeHtml(statusLabel(item))}</span>
          ${seerr.state === "requested" || seerr.state === "available" ? "<span class=\"checkmark\">⌄</span>" : ""}
        </div>
      </div>
      <div class="card-menu" aria-hidden="true">⋮</div>
      ${disabled ? `<a class="anilist-btn" href="${item.siteUrl}" target="_blank" rel="noreferrer">AniList ↗</a>` : `<button class="request-btn" data-request="${item.id}">${buttonText}<span aria-hidden="true">↗</span></button>`}
    </article>
  `;
}

function pagerPages(totalPages) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }
  const pages = new Set([1, totalPages, state.page - 1, state.page, state.page + 1]);
  return [...pages]
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right)
    .reduce((acc, page, index, allPages) => {
      if (index > 0 && page - allPages[index - 1] > 1) acc.push("ellipsis");
      acc.push(page);
      return acc;
    }, []);
}

function renderPager(visibleCount) {
  const totalPages = Math.max(1, Math.ceil(visibleCount / state.pageSize));
  const first = visibleCount ? (state.page - 1) * state.pageSize + 1 : 0;
  const last = Math.min(state.page * state.pageSize, visibleCount);
  const totalSuffix = visibleCount === state.items.length ? "" : ` of ${state.items.length} total`;
  return `
    <div class="pager" aria-label="Pagination">
      <button type="button" data-page="${Math.max(1, state.page - 1)}" aria-label="Previous page" ${state.page === 1 ? "disabled" : ""}>‹</button>
      ${pagerPages(totalPages).map((page) => {
        if (page === "ellipsis") return "<span>…</span>";
        return `<button class="${page === state.page ? "active" : ""}" type="button" data-page="${page}" aria-current="${page === state.page ? "page" : "false"}">${page}</button>`;
      }).join("")}
      <button type="button" data-page="${Math.min(totalPages, state.page + 1)}" aria-label="Next page" ${state.page === totalPages ? "disabled" : ""}>›</button>
      <small>Showing ${first}-${last} of ${visibleCount}${totalSuffix}</small>
    </div>
  `;
}

function renderSections() {
  const allItems = visibleItems();
  const totalPages = Math.max(1, Math.ceil(allItems.length / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  const start = (state.page - 1) * state.pageSize;
  const items = allItems.slice(start, start + state.pageSize);
  if (!items.length) {
    els.sections.innerHTML = `<div class="empty-state">No anime match the current filters.</div>${renderPager(0)}`;
    return;
  }
  const groups = new Map();
  for (const item of items) {
    const bucket = item.bucket || "Seasonal";
    if (!groups.has(bucket)) groups.set(bucket, []);
    groups.get(bucket).push(item);
  }
  els.sections.innerHTML = `${[...groups.entries()].map(([bucket, bucketItems]) => `
    <section>
      <div class="bucket-heading">
        <h2>${escapeHtml(bucket)}</h2>
        <span class="meta">${bucketItems.length} titles • sorted by ${escapeHtml(state.sort)}</span>
      </div>
      <div class="cards-grid">
        ${bucketItems.map(cardTemplate).join("")}
      </div>
    </section>
  `).join("")}${renderPager(allItems.length)}`;
}

function renderSpotlight(item) {
  state.selected = item;
  if (!item) {
    els.spotlight.innerHTML = `
      <div class="spotlight-empty">
        <span class="orb"></span>
        <h2>Select an anime</h2>
        <p>Pick a seasonal card to see mapping status, audio signal, next airing data, and the Seerr request action.</p>
      </div>
    `;
    return;
  }
  const seerr = item.seerr || {};
  const audio = audioState(item);
  const disabled = !seerr.requestable;
  els.spotlight.innerHTML = `
    <button class="spotlight-close" type="button" aria-label="Close details">×</button>
    <div class="spotlight-media" style="background-image: url('${item.banner || item.cover || ""}')">
      <span class="rank spotlight-rank">#${item.rank}</span>
    </div>
    <h2>${escapeHtml(item.title)}</h2>
    <p class="spotlight-subtitle">${escapeHtml(item.romajiTitle || item.englishTitle || item.title)}</p>
    <div class="score-row spotlight-score">
      <span>★ ${item.averageScore ? (item.averageScore / 10).toFixed(2) : "--"}</span>
      <span>♨ ${formatNumber(item.popularity)}</span>
      <span class="audio-chip ${escapeHtml(audio.state)}" title="${escapeHtml(audioTooltip(item))}">${escapeHtml(audio.label)}</span>
      <a href="${item.siteUrl}" target="_blank" rel="noreferrer">View on AniList ↗</a>
    </div>
    <div class="genre-row">${(item.genres || []).slice(0, 3).map((genre) => `<span>${escapeHtml(genre)}</span>`).join("")}</div>
    <div class="detail-list">
      <div><span>Next Episode</span><strong>${formatAiring(item.nextAiring)}</strong></div>
      <div><span>Audio</span><strong><span class="audio-chip ${escapeHtml(audio.state)}">${escapeHtml(audio.label)}</span></strong></div>
      <div><span>Overview</span><strong>${plainDescription(item.description)}</strong></div>
      <div><span>Start Date</span><strong>${formatDate(item.startDate)}</strong></div>
      <div><span>Seerr Match</span><strong>${seerr.title ? `${escapeHtml(seerr.title)} (${seerr.matchScore})` : "None"}</strong></div>
      <div><span>Status</span><strong class="dot-status ${seerr.state}"><i></i>${escapeHtml(statusLabel(item))}</strong></div>
    </div>
    <button class="request-btn" data-request="${item.id}" ${disabled ? "disabled" : ""}>
      ${seerr.state === "partial" ? "Request Missing Seasons" : "Request in Seerr"}<span aria-hidden="true">↗</span>
    </button>
  `;
}

function setFilterOpen(open) {
  state.filterOpen = open;
  els.filterMenu.hidden = !open;
  els.filterButton.setAttribute("aria-expanded", String(open));
}

async function loadSeason() {
  els.sections.innerHTML = `<div class="loading">Loading ${state.season.toLowerCase()} ${state.year} anime from AniList, Jikan, and Seerr...</div>`;
  try {
    const url = `/api/seasonal?season=${encodeURIComponent(state.season)}&year=${encodeURIComponent(state.year)}&perPage=48`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    state.items = data.items || [];
    resetPage();
    renderSpotlight(state.items[0] || null);
    renderStats(data.stats || {});
    renderSections();
  } catch (error) {
    els.sections.innerHTML = `<div class="empty-state">Failed to load seasonal anime. ${escapeHtml(error.message)}</div>`;
    renderSpotlight(null);
  }
}

async function requestItem(id) {
  const item = state.items.find((anime) => String(anime.id) === String(id));
  if (!item || !item.seerr?.tmdbId) return;
  try {
    toast(`Sending ${item.title} to Seerr...`);
    const response = await fetch("/api/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mediaId: item.seerr.tmdbId,
        tvdbId: item.seerr.tvdbId,
        title: item.title,
        seasons: "all",
      }),
    });
    if (!response.ok) throw new Error(await response.text());
    item.seerr.state = "requested";
    item.seerr.label = "Requested";
    item.seerr.requestable = false;
    state.selected = item;
    renderSections();
    renderSpotlight(item);
    toast(`${item.title} was requested in Seerr.`);
  } catch (error) {
    toast(`Request failed: ${error.message}`);
  }
}

async function openConnectionModal() {
  els.connectionModal.hidden = false;
  document.body.classList.add("modal-open");
  try {
    const response = await fetch("/api/config");
    if (!response.ok) throw new Error(await response.text());
    const config = await response.json();
    els.connectionStatus.textContent = config.seerrConfigured ? "Configured" : "Missing";
    els.connectionRequestSeasons.textContent = config.requestSeasons || "all";
    els.connectionSummary.textContent = config.seerrConfigured
      ? "Weebarr can read request status and submit matched anime requests to Seerr. API keys are configured only through Docker environment variables."
      : "Weebarr is running, but Seerr request integration needs SEERR_BASE_URL and SEERR_API_KEY in the container environment.";
  } catch (error) {
    els.connectionSummary.textContent = `Could not read connection settings. ${error.message}`;
  }
}

function closeConnectionModal() {
  els.connectionModal.hidden = true;
  document.body.classList.remove("modal-open");
}

els.refresh.addEventListener("click", () => {
  state.season = els.season.value;
  state.year = Number(els.year.value);
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.prevSeason.addEventListener("click", () => shiftSeason(-1));
els.nextSeason.addEventListener("click", () => shiftSeason(1));

els.season.addEventListener("change", (event) => {
  state.season = event.target.value;
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.filterSeason.addEventListener("change", (event) => {
  state.season = event.target.value;
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.year.addEventListener("change", () => {
  state.year = Number(els.year.value);
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  resetPage();
  renderSections();
});

els.filter.addEventListener("change", (event) => {
  state.filter = event.target.value;
  resetPage();
  renderSections();
});

els.sort.addEventListener("change", (event) => {
  state.sort = event.target.value;
  resetPage();
  renderSections();
});

els.filterButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setFilterOpen(!state.filterOpen);
});

els.filterMenu.addEventListener("click", (event) => {
  const button = event.target.closest("[data-quick-filter]");
  if (!button) return;
  const quickFilter = button.dataset.quickFilter;
  if (quickFilter === "clear") {
    state.filter = "all";
    state.audioFilter = "all";
    state.query = "";
    els.filter.value = "all";
    els.search.value = "";
  } else if (quickFilter === "requestable" || quickFilter === "missing_mapping") {
    state.filter = quickFilter;
    els.filter.value = quickFilter;
  } else {
    state.audioFilter = quickFilter;
  }
  resetPage();
  setFilterOpen(false);
  renderSections();
});

document.addEventListener("click", (event) => {
  if (state.filterOpen && !event.target.closest(".filter-actions")) {
    setFilterOpen(false);
  }
});

els.sections.addEventListener("click", (event) => {
  const pagerButton = event.target.closest("[data-page]");
  if (pagerButton) {
    state.page = Number(pagerButton.dataset.page);
    renderSections();
    return;
  }
  const requestButton = event.target.closest("[data-request]");
  if (requestButton) {
    requestItem(requestButton.dataset.request);
    return;
  }
  const card = event.target.closest(".anime-card");
  if (card) {
    const item = state.items.find((anime) => String(anime.id) === card.dataset.id);
    renderSpotlight(item);
    renderSections();
  }
});

els.spotlight.addEventListener("click", (event) => {
  if (event.target.closest(".spotlight-close")) {
    renderSpotlight(state.items[0] || null);
    renderSections();
    return;
  }
  const requestButton = event.target.closest("[data-request]");
  if (requestButton) {
    requestItem(requestButton.dataset.request);
  }
});

els.themeButtons.forEach((button) => {
  button.addEventListener("click", () => applyTheme(button.dataset.themeChoice));
});

prefersLight.addEventListener("change", () => {
  if (state.theme === "system") applyTheme("system");
});

els.manageConnection.addEventListener("click", openConnectionModal);

els.connectionModal.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-modal]")) closeConnectionModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setFilterOpen(false);
    if (!els.connectionModal.hidden) closeConnectionModal();
  }
});

applyTheme();
updateSeasonControls();
loadSeason();
