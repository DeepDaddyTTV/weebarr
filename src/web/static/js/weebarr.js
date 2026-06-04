const state = {
  season: window.WEEBARR_DEFAULT_SEASON || "SPRING",
  year: window.WEEBARR_DEFAULT_YEAR || new Date().getFullYear(),
  items: [],
  selected: null,
  query: "",
  filter: "all",
  sort: "popularity",
};

const els = {
  season: document.querySelector("#seasonSelect"),
  filterSeason: document.querySelector("#filterSeasonSelect"),
  year: document.querySelector("#yearInput"),
  prevSeason: document.querySelector("#prevSeasonBtn"),
  nextSeason: document.querySelector("#nextSeasonBtn"),
  refresh: document.querySelector("#refreshBtn"),
  filterButton: document.querySelector("#filterBtn"),
  search: document.querySelector("#searchInput"),
  filter: document.querySelector("#statusFilter"),
  sort: document.querySelector("#sortSelect"),
  sections: document.querySelector("#animeSections"),
  spotlight: document.querySelector("#spotlight"),
  toast: document.querySelector("#toast"),
  stats: {
    total: document.querySelector("#statTotal"),
    requestable: document.querySelector("#statRequestable"),
    requested: document.querySelector("#statRequested"),
    airingSoon: document.querySelector("#statAiringSoon"),
  },
};

const seasonOrder = ["WINTER", "SPRING", "SUMMER", "FALL"];

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
  updateSeasonControls();
  loadSeason();
}

function visibleItems() {
  const query = state.query.trim().toLowerCase();
  let items = [...state.items];
  if (query) {
    items = items.filter((item) => {
      const haystack = [
        item.title,
        item.romajiTitle,
        item.englishTitle,
        item.nativeTitle,
        ...(item.genres || []),
        ...(item.studios || []),
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }
  if (state.filter !== "all") {
    items = items.filter((item) => {
      if (state.filter === "requestable") {
        return item.seerr.state === "requestable" || item.seerr.state === "partial";
      }
      return item.seerr.state === state.filter;
    });
  }
  if (state.sort === "score") {
    items.sort((a, b) => (b.averageScore || 0) - (a.averageScore || 0));
  } else if (state.sort === "airing") {
    items.sort((a, b) => {
      const left = a.nextAiring?.airingAt ? new Date(a.nextAiring.airingAt).getTime() : Number.MAX_SAFE_INTEGER;
      const right = b.nextAiring?.airingAt ? new Date(b.nextAiring.airingAt).getTime() : Number.MAX_SAFE_INTEGER;
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

function renderPager(items) {
  return `
    <div class="pager">
      <button type="button" aria-label="Previous page">‹</button>
      <button class="active" type="button">1</button>
      <button type="button">2</button>
      <button type="button">3</button>
      <button type="button">4</button>
      <button type="button">5</button>
      <span>…</span>
      <button type="button">24</button>
      <button type="button" aria-label="Next page">›</button>
      <small>Showing 1-${Math.min(items.length, 12)} of ${state.items.length}</small>
    </div>
  `;
}

function renderSections() {
  const items = visibleItems().slice(0, 12);
  if (!items.length) {
    els.sections.innerHTML = `<div class="empty-state">No anime match the current filters.</div>`;
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
  `).join("")}${renderPager(items)}`;
}

function renderSpotlight(item) {
  state.selected = item;
  if (!item) {
    return;
  }
  const seerr = item.seerr || {};
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
      <a href="${item.siteUrl}" target="_blank" rel="noreferrer">View on AniList ↗</a>
    </div>
    <div class="genre-row">${(item.genres || []).slice(0, 3).map((genre) => `<span>${escapeHtml(genre)}</span>`).join("")}</div>
    <div class="detail-list">
      <div><span>Next Episode</span><strong>${formatAiring(item.nextAiring)}</strong></div>
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

async function loadSeason() {
  els.sections.innerHTML = `<div class="loading">Loading ${state.season.toLowerCase()} ${state.year} anime from AniList and matching Seerr...</div>`;
  try {
    const url = `/api/seasonal?season=${encodeURIComponent(state.season)}&year=${encodeURIComponent(state.year)}&perPage=48`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    state.items = data.items || [];
    renderSpotlight(state.items[0]);
    renderStats(data.stats || {});
    renderSections();
  } catch (error) {
    els.sections.innerHTML = `<div class="empty-state">Failed to load seasonal anime. ${escapeHtml(error.message)}</div>`;
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

els.refresh.addEventListener("click", () => {
  state.season = els.season.value;
  state.year = Number(els.year.value);
  updateSeasonControls();
  loadSeason();
});

els.prevSeason.addEventListener("click", () => shiftSeason(-1));
els.nextSeason.addEventListener("click", () => shiftSeason(1));

els.filterSeason.addEventListener("change", (event) => {
  state.season = event.target.value;
  updateSeasonControls();
  loadSeason();
});

els.year.addEventListener("change", () => {
  state.year = Number(els.year.value);
  updateSeasonControls();
});

els.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderSections();
});

els.filter.addEventListener("change", (event) => {
  state.filter = event.target.value;
  renderSections();
});

els.sort.addEventListener("change", (event) => {
  state.sort = event.target.value;
  renderSections();
});

els.filterButton.addEventListener("click", () => {
  toast("Use Search, Status, Sort by, and Season to filter this season.");
});

els.sections.addEventListener("click", (event) => {
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
    renderSpotlight(state.items[0]);
    renderSections();
    return;
  }
  const requestButton = event.target.closest("[data-request]");
  if (requestButton) {
    requestItem(requestButton.dataset.request);
  }
});

updateSeasonControls();
loadSeason();
