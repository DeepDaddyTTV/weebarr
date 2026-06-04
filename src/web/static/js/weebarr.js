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
  year: document.querySelector("#yearInput"),
  refresh: document.querySelector("#refreshBtn"),
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
    available: document.querySelector("#statAvailable"),
  },
};

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
  return `Ep ${nextAiring.episode} · ${when}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
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
  els.stats.total.textContent = formatNumber(stats.total);
  els.stats.requestable.textContent = formatNumber(stats.requestable);
  els.stats.requested.textContent = formatNumber(stats.requested);
  els.stats.available.textContent = formatNumber(stats.available);
}

function cardTemplate(item) {
  const seerr = item.seerr || {};
  const disabled = !seerr.requestable;
  const buttonText = seerr.state === "partial" ? "Request Missing" : "Request in Seerr";
  return `
    <article class="anime-card" data-id="${item.id}">
      <div class="poster">
        ${item.cover ? `<img src="${item.cover}" alt="${escapeHtml(item.title)} poster" loading="lazy" />` : ""}
        <span class="rank">#${item.rank}</span>
      </div>
      <div class="card-body">
        <span class="status-chip ${seerr.state}">${escapeHtml(seerr.label)}</span>
        <h3>${escapeHtml(item.title)}</h3>
        <div class="meta">${escapeHtml(item.format || "TV")} · ${item.episodes || "?"} eps · ${item.averageScore || "--"} score</div>
        <div class="meta">${formatAiring(item.nextAiring)}</div>
        <div class="genre-row">${(item.genres || []).slice(0, 3).map((genre) => `<span>${escapeHtml(genre)}</span>`).join("")}</div>
        <div class="card-actions">
          <button class="request-btn" data-request="${item.id}" ${disabled ? "disabled" : ""}>${buttonText}</button>
          <a href="${item.siteUrl}" target="_blank" rel="noreferrer">AniList</a>
        </div>
      </div>
    </article>
  `;
}

function renderSections() {
  const items = visibleItems();
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
  els.sections.innerHTML = [...groups.entries()].map(([bucket, bucketItems]) => `
    <section>
      <div class="bucket-heading">
        <h2>${escapeHtml(bucket)}</h2>
        <span class="meta">${bucketItems.length} titles · sorted by ${escapeHtml(state.sort)}</span>
      </div>
      <div class="cards-grid">
        ${bucketItems.map(cardTemplate).join("")}
      </div>
    </section>
  `).join("");
}

function renderSpotlight(item) {
  state.selected = item;
  if (!item) {
    return;
  }
  const seerr = item.seerr || {};
  const disabled = !seerr.requestable;
  els.spotlight.innerHTML = `
    <div class="spotlight-banner" style="background-image: url('${item.banner || item.cover || ""}')"></div>
    ${item.cover ? `<img class="spotlight-poster" src="${item.cover}" alt="${escapeHtml(item.title)} poster" />` : ""}
    <span class="status-chip ${seerr.state}">${escapeHtml(seerr.label)}</span>
    <h2>${escapeHtml(item.title)}</h2>
    <p>${escapeHtml(item.description || "No description from AniList.")}</p>
    <div class="detail-list">
      <div><span>Popularity</span><strong>${formatNumber(item.popularity)}</strong></div>
      <div><span>AniList Rank</span><strong>#${item.rank}</strong></div>
      <div><span>Start Date</span><strong>${formatDate(item.startDate)}</strong></div>
      <div><span>Next Airing</span><strong>${formatAiring(item.nextAiring)}</strong></div>
      <div><span>Seerr Match</span><strong>${seerr.title ? `${escapeHtml(seerr.title)} (${seerr.matchScore})` : "None"}</strong></div>
    </div>
    <button class="request-btn" data-request="${item.id}" ${disabled ? "disabled" : ""}>
      ${seerr.state === "partial" ? "Request Missing Seasons" : "Request in Seerr"}
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
    renderStats(data.stats || {});
    renderSections();
    renderSpotlight(state.items[0]);
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
  loadSeason();
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
  }
});

els.spotlight.addEventListener("click", (event) => {
  const requestButton = event.target.closest("[data-request]");
  if (requestButton) {
    requestItem(requestButton.dataset.request);
  }
});

loadSeason();
