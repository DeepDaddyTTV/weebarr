const state = {
  view: window.WEEBARR_PAGE || "seasonal",
  season: window.WEEBARR_DEFAULT_SEASON || "SPRING",
  year: window.WEEBARR_DEFAULT_YEAR || new Date().getFullYear(),
  items: [],
  selectedId: null,
  query: "",
  filter: window.WEEBARR_INITIAL_FILTER || "all",
  audioFilter: "all",
  sort: "popularity",
  page: 1,
  pageSize: 12,
  theme: "dark",
  filterOpen: false,
  openDropdown: null,
  hideRequested: false,
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
  hideRequested: document.querySelector("#hideRequestedToggle"),
  sections: document.querySelector("#animeSections"),
  spotlight: document.querySelector("#spotlight"),
  toast: document.querySelector("#toast"),
  themeButtons: document.querySelectorAll("[data-theme-choice]"),
  stats: {
    total: document.querySelector("#statTotal"),
    requestable: document.querySelector("#statRequestable"),
    requested: document.querySelector("#statRequested"),
    airingSoon: document.querySelector("#statAiringSoon"),
  },
};

const compactDetailsMedia = window.matchMedia("(max-width: 900px)");
const forceCompactPreview = new URLSearchParams(window.location.search).get("compactPreview") === "1";
const customSelectRoots = [...document.querySelectorAll("[data-ui-select]")];
const customSelects = new Map();
const seasonOrder = ["WINTER", "SPRING", "SUMMER", "FALL"];
const themeStorageKey = "weebarr-theme";
const prefersLight = window.matchMedia("(prefers-color-scheme: light)");
const requestQueueStates = new Set(["partial", "requested", "available"]);
const fullyRequestedStates = new Set(["partial", "requested", "available"]);

els.filter.value = state.filter;
els.sort.value = state.sort;

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

function isCompactDetails() {
  return forceCompactPreview || compactDetailsMedia.matches;
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

function formatBucketDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
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
      event.stopPropagation();
      const nextOpen = state.openDropdown === select.id ? null : select.id;
      setFilterOpen(false);
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

function countLabel(count) {
  return `${count} ${count === 1 ? "title" : "titles"}`;
}

function scoreBucket(item) {
  const score = Number(item.averageScore || 0);
  if (!Number.isFinite(score) || score <= 0) return "Unrated";
  const stars = Math.max(1, Math.min(5, Math.ceil(score / 20)));
  return `${stars} Star${stars === 1 ? "" : "s"}`;
}

function airingBucket(item) {
  if (!item.nextAiring?.airingAt) return "No Airing Date";
  return formatBucketDate(item.nextAiring.airingAt);
}

function bucketLabel(item) {
  if (state.sort === "score") return scoreBucket(item);
  if (state.sort === "airing") return airingBucket(item);
  return item.bucket || "Seasonal";
}

function bucketMeta(bucketItems) {
  if (state.sort === "score") {
    return `${countLabel(bucketItems.length)} • grouped by rating`;
  }
  if (state.sort === "airing") {
    return `${countLabel(bucketItems.length)} • grouped by next airing`;
  }
  return `${countLabel(bucketItems.length)} • sorted by popularity`;
}

function totalPagesForCount(visibleCount) {
  return Math.max(1, Math.ceil(visibleCount / state.pageSize));
}

function sanitizePage(value, visibleCount = state.items.length) {
  const parsed = Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return 1;
  }
  return Math.min(parsed, totalPagesForCount(visibleCount));
}

function seasonSummary(item) {
  return [item.installmentLabel, item.seasonLabel].filter(Boolean).join(" • ");
}

function cardMeta(item) {
  const seasonInfo = seasonSummary(item);
  if (seasonInfo) return seasonInfo;
  return item.format || "TV";
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
  syncCustomSelects(["seasonSelect", "filterSeasonSelect"]);
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
  state.selectedId = null;
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

function isRequestQueueItem(item) {
  return requestQueueStates.has((item.seerr || {}).state);
}

function hasWeebarrRequest(item) {
  return Boolean(item.weebarrRequest?.requestedAt);
}

function isHiddenByRequestedToggle(item) {
  return fullyRequestedStates.has((item.seerr || {}).state);
}

function visibleItems() {
  const query = state.query.trim().toLowerCase();
  let items = [...state.items];
  if (state.view === "requests") {
    items = items.filter(hasWeebarrRequest);
  }
  if (state.view === "seasonal" && state.hideRequested) {
    items = items.filter((item) => !isHiddenByRequestedToggle(item));
  }
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
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }
  if (state.filter !== "all") {
    items = items.filter((item) => {
      const seerr = item.seerr || {};
      if (state.filter === "requestable") {
        return seerr.state === "requestable";
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

function currentSelectedItem(items = state.items) {
  if (!state.selectedId) return null;
  return items.find((item) => String(item.id) === String(state.selectedId)) || null;
}

function syncSelectedItem(items) {
  if (!items.length) {
    state.selectedId = null;
    return null;
  }
  const selected = currentSelectedItem(items);
  if (isCompactDetails()) {
    if (selected && items.some((item) => String(item.id) === String(selected.id))) {
      return selected;
    }
    state.selectedId = null;
    return null;
  }
  if (selected && items.some((item) => String(item.id) === String(selected.id))) {
    return selected;
  }
  state.selectedId = String(items[0].id);
  return items[0];
}

function renderStats(stats) {
  const scopedItems =
    state.view === "requests" ? state.items.filter(hasWeebarrRequest) : state.items;
  const soonCutoff = Date.now() + 7 * 24 * 60 * 60 * 1000;
  const airingSoon = scopedItems.filter((item) => {
    if (!item.nextAiring?.airingAt) return false;
    const airingAt = new Date(item.nextAiring.airingAt).getTime();
    return airingAt >= Date.now() && airingAt <= soonCutoff;
  }).length;
  const requestedCount = scopedItems.filter((item) =>
    ["requested", "available"].includes((item.seerr || {}).state),
  ).length;
  const partialCount = scopedItems.filter(
    (item) => (item.seerr || {}).state === "partial",
  ).length;
  els.stats.total.textContent = formatNumber(
    state.view === "requests" ? scopedItems.length : stats.total,
  );
  els.stats.requestable.textContent = formatNumber(
    state.view === "requests" ? partialCount : stats.requestable,
  );
  els.stats.requested.textContent = formatNumber(
    state.view === "requests" ? requestedCount : stats.requested,
  );
  els.stats.airingSoon.textContent = formatNumber(airingSoon);
}

function statusLabel(item) {
  const seerr = item.seerr || {};
  return seerr.label || "Unknown";
}

function actionButtonTemplate(item, inline = false) {
  const seerr = item.seerr || {};
  if (!seerr || seerr.state === "disabled") {
    return `<a class="${inline ? "request-btn" : "anilist-btn"}" href="/settings#connections">Configure Seerr</a>`;
  }
  if (!seerr.requestable) {
    return `<a class="anilist-btn" href="${item.siteUrl}" target="_blank" rel="noreferrer">AniList ↗</a>`;
  }
  const buttonText = seerr.state === "partial" ? "Request Missing" : "Request in Seerr";
  return `<button class="request-btn" type="button" data-request="${item.id}">${buttonText}<span aria-hidden="true">↗</span></button>`;
}

function inlineActionsTemplate(item) {
  const seerr = item.seerr || {};
  const actions = [
    `<a class="anilist-btn inline-link" href="${item.siteUrl}" target="_blank" rel="noreferrer">AniList ↗</a>`,
  ];
  if (!seerr || seerr.state === "disabled") {
    actions.push(`<a class="request-btn inline-link" href="/settings#connections">Configure Seerr</a>`);
  } else if (seerr.requestable) {
    const buttonText = seerr.state === "partial" ? "Request Missing" : "Request in Seerr";
    actions.push(
      `<button class="request-btn inline-link" type="button" data-request="${item.id}">${buttonText}<span aria-hidden="true">↗</span></button>`,
    );
  }
  return `<div class="inline-actions inline-spotlight-actions">${actions.join("")}</div>`;
}

function requestDate(item) {
  return formatDate(item.weebarrRequest?.requestedAt);
}

function requestListTemplate(item) {
  const seerr = item.seerr || {};
  const subtitle = item.romajiTitle && item.romajiTitle !== item.title ? item.romajiTitle : item.englishTitle || "";
  const summary = plainDescription(item.description, 150);
  const checked = hasWeebarrRequest(item) ? "checked" : "";
  return `
    <article class="request-row">
      <div class="request-row-media">
        ${item.cover ? `<img src="${item.cover}" alt="${escapeHtml(item.title)} poster" loading="lazy" />` : ""}
      </div>
      <div class="request-row-copy">
        <div class="request-row-head">
          <div class="request-row-title">
            <h3>${escapeHtml(item.title)}</h3>
            ${subtitle ? `<p>${escapeHtml(subtitle)}</p>` : ""}
          </div>
          <span class="request-check ${checked}" aria-label="Requested through Weebarr" role="img">
            <i aria-hidden="true"></i>
          </span>
        </div>
        <p class="request-row-summary">${escapeHtml(summary || "No summary available.")}</p>
        <div class="request-row-foot">
          <span><strong>Requested</strong>${requestDate(item)}</span>
          <span><strong>Air Date</strong>${formatDate(item.startDate)}</span>
          <span><strong>Status</strong>${escapeHtml(statusLabel(item))}</span>
        </div>
      </div>
    </article>
  `;
}

function inlineDetailTemplate(item) {
  const seerr = item.seerr || {};
  return `
    <div class="inline-detail inline-spotlight">
      <div class="inline-spotlight-media" style="background-image: url('${item.banner || item.cover || ""}')">
        <span class="rank inline-spotlight-rank">#${item.rank}</span>
      </div>
      <div class="inline-spotlight-head">
        <div class="inline-spotlight-copy">
          <h3>${escapeHtml(item.title)}</h3>
          <p class="spotlight-subtitle">${escapeHtml(item.romajiTitle || item.englishTitle || item.title)}</p>
        </div>
        <button class="inline-detail-close" type="button" data-inline-close="${item.id}" aria-label="Close details">×</button>
      </div>
      <div class="score-row inline-spotlight-score">
        <span>★ ${item.averageScore ? (item.averageScore / 10).toFixed(2) : "--"}</span>
        <span>♨ ${formatNumber(item.popularity)}</span>
        <span class="audio-chip ${escapeHtml(audioState(item).state)}" title="${escapeHtml(audioTooltip(item))}">${escapeHtml(audioState(item).label)}</span>
      </div>
      <div class="genre-row">${(item.genres || []).slice(0, 3).map((genre) => `<span>${escapeHtml(genre)}</span>`).join("")}</div>
      <div class="detail-list inline-detail-list">
        <div><span>Season</span><strong>${escapeHtml(seasonSummary(item) || "Current season")}</strong></div>
        <div><span>Next Episode</span><strong>${formatAiring(item.nextAiring)}</strong></div>
        <div><span>Audio</span><strong><span class="audio-chip ${escapeHtml(audioState(item).state)}">${escapeHtml(audioState(item).label)}</span></strong></div>
        <div><span>Overview</span><strong>${plainDescription(item.description, 520)}</strong></div>
        <div><span>Start Date</span><strong>${formatDate(item.startDate)}</strong></div>
        <div><span>Seerr Match</span><strong>${seerr.title ? `${escapeHtml(seerr.title)} (${seerr.matchScore})` : "None"}</strong></div>
        <div><span>Status</span><strong class="dot-status ${seerr.state}"><i></i>${escapeHtml(statusLabel(item))}</strong></div>
      </div>
      ${inlineActionsTemplate(item)}
    </div>
  `;
}

function cardTemplate(item) {
  const seerr = item.seerr || {};
  const audio = audioState(item);
  const compact = isCompactDetails();
  const isSelected = String(state.selectedId) === String(item.id);
  const selectLabel = compact && isSelected ? `Collapse details for ${item.title}` : `Open details for ${item.title}`;
  return `
    <article class="anime-card ${isSelected ? "selected" : ""} ${compact && isSelected ? "inline-selected" : ""}" data-id="${item.id}" aria-expanded="${compact ? String(isSelected) : "false"}">
      <div class="card-surface" data-select="${item.id}" role="button" tabindex="0" aria-label="${escapeHtml(selectLabel)}" aria-expanded="${compact ? String(isSelected) : "false"}">
        <div class="poster">
          ${item.cover ? `<img src="${item.cover}" alt="${escapeHtml(item.title)} poster" loading="lazy" />` : ""}
          <span class="rank">#${item.rank}</span>
        </div>
        <div class="card-body">
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.romajiTitle || item.englishTitle || item.title)}</p>
          <div class="meta">${escapeHtml(cardMeta(item))}</div>
          <div class="score-row">
            <span>★ ${item.averageScore ? (item.averageScore / 10).toFixed(2) : "--"}</span>
            <span>♨ ${formatNumber(item.popularity)}</span>
            <span class="audio-chip ${escapeHtml(audio.state)}" title="${escapeHtml(audioTooltip(item))}">${escapeHtml(audio.label)}</span>
          </div>
          <div class="next-line"><strong>Next Episode</strong>${formatAiring(item.nextAiring)}</div>
          <div class="card-foot">
            <span class="dot-status ${seerr.state}"><i></i>${escapeHtml(statusLabel(item))}</span>
            ${actionButtonTemplate(item)}
          </div>
        </div>
        <div class="card-menu" aria-hidden="true">⋮</div>
      </div>
      ${compact && isSelected ? inlineDetailTemplate(item) : ""}
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
  state.page = sanitizePage(state.page, visibleCount);
  const totalPages = totalPagesForCount(visibleCount);
  const first = visibleCount ? (state.page - 1) * state.pageSize + 1 : 0;
  const last = Math.min(state.page * state.pageSize, visibleCount);
  const totalSuffix = visibleCount === state.items.length ? "" : ` of ${state.items.length} total`;
  return `
    <div class="pager" aria-label="Pagination">
      <button type="button" data-page="${Math.max(1, state.page - 1)}" aria-label="Previous page" ${state.page === 1 ? "disabled" : ""}>‹</button>
      ${pagerPages(totalPages)
        .map((page) => {
          if (page === "ellipsis") return "<span>…</span>";
          return `<button class="${page === state.page ? "active" : ""}" type="button" data-page="${page}" aria-current="${page === state.page ? "page" : "false"}">${page}</button>`;
        })
        .join("")}
      <button type="button" data-page="${Math.min(totalPages, state.page + 1)}" aria-label="Next page" ${state.page === totalPages ? "disabled" : ""}>›</button>
      <small>Showing ${first}-${last} of ${visibleCount}${totalSuffix}</small>
    </div>
  `;
}

function renderSections(allItems) {
  syncSelectedItem(allItems);
  state.page = sanitizePage(state.page, allItems.length);
  const start = (state.page - 1) * state.pageSize;
  const items = allItems.slice(start, start + state.pageSize);
  if (!items.length) {
    const message =
      state.view === "requests"
        ? "No anime have been requested through Weebarr for this season yet."
        : "No anime match the current filters.";
    els.sections.innerHTML = `<div class="empty-state">${message}</div>${renderPager(0)}`;
    return;
  }
  if (state.view === "requests") {
    els.sections.innerHTML = `
      <section class="request-list">
        ${items.map(requestListTemplate).join("")}
      </section>
      ${renderPager(allItems.length)}
    `;
    return;
  }
  const groups = new Map();
  for (const item of items) {
    const bucket = bucketLabel(item);
    if (!groups.has(bucket)) groups.set(bucket, []);
    groups.get(bucket).push(item);
  }
  els.sections.innerHTML = `${[...groups.entries()]
    .map(
      ([bucket, bucketItems]) => `
    <section>
      <div class="bucket-heading">
        <h2>${escapeHtml(bucket)}</h2>
        <span class="meta">${escapeHtml(bucketMeta(bucketItems))}</span>
      </div>
      <div class="cards-grid">
        ${bucketItems.map(cardTemplate).join("")}
      </div>
    </section>
  `,
    )
    .join("")}${renderPager(allItems.length)}`;
  els.sections.querySelectorAll("[data-select]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleSelectedItem(String(button.dataset.select));
    });
    button.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      event.stopPropagation();
      toggleSelectedItem(String(button.dataset.select));
    });
  });
  els.sections.querySelectorAll("[data-inline-close]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      state.selectedId = null;
      renderAll();
    });
  });
}

function renderSpotlight(item) {
  if (state.view === "requests") {
    els.spotlight.hidden = true;
    return;
  }
  if (isCompactDetails()) {
    els.spotlight.hidden = true;
    return;
  }

  els.spotlight.hidden = false;
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
      <div><span>Season</span><strong>${escapeHtml(seasonSummary(item) || "Current season")}</strong></div>
      <div><span>Next Episode</span><strong>${formatAiring(item.nextAiring)}</strong></div>
      <div><span>Audio</span><strong><span class="audio-chip ${escapeHtml(audio.state)}">${escapeHtml(audio.label)}</span></strong></div>
      <div><span>Overview</span><strong>${plainDescription(item.description)}</strong></div>
      <div><span>Start Date</span><strong>${formatDate(item.startDate)}</strong></div>
      <div><span>Seerr Match</span><strong>${seerr.title ? `${escapeHtml(seerr.title)} (${seerr.matchScore})` : "None"}</strong></div>
      <div><span>Status</span><strong class="dot-status ${seerr.state}"><i></i>${escapeHtml(statusLabel(item))}</strong></div>
    </div>
    ${actionButtonTemplate(item, true)}
  `;
}

function renderAll() {
  const filteredItems = visibleItems();
  renderSections(filteredItems);
  renderSpotlight(currentSelectedItem(filteredItems));
}

function toggleSelectedItem(clickedId) {
  if (isCompactDetails() && state.selectedId === clickedId) {
    state.selectedId = null;
  } else {
    state.selectedId = clickedId;
  }
  renderAll();
}

function setFilterOpen(open) {
  state.filterOpen = open;
  els.filterMenu.parentElement?.classList.toggle("is-open", open);
  if (open) {
    setCustomSelectOpen(null);
  }
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
    renderStats(data.stats || {});
    renderAll();
  } catch (error) {
    els.sections.innerHTML = `<div class="empty-state">Failed to load seasonal anime. ${escapeHtml(error.message)}</div>`;
    renderSpotlight(null);
  }
}

async function requestItem(id) {
  const item = state.items.find((anime) => String(anime.id) === String(id));
  if (!item) return;
  if (!item.seerr?.tmdbId) {
    toast("This title does not have a usable Seerr mapping yet.");
    return;
  }
  try {
    toast(`Sending ${item.title} to Seerr...`);
    const response = await fetch("/api/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mediaId: item.seerr.tmdbId,
        animeId: item.id,
        tvdbId: item.seerr.tvdbId,
        title: item.title,
        season: item.season,
        year: item.seasonYear,
        seasons: item.seerr.requestSeasons,
      }),
    });
    if (!response.ok) {
      const detail = await readError(response);
      throw new Error(detail);
    }
    const payload = await response.json();
    item.seerr.state = "requested";
    item.seerr.label = "Requested";
    item.seerr.requestable = false;
    item.weebarrRequest = payload.weebarrRequest || {
      requestedAt: new Date().toISOString(),
      requestSeasons: item.seerr.requestSeasons,
      tmdbId: item.seerr.tmdbId,
      tvdbId: item.seerr.tvdbId,
      title: item.title,
    };
    state.selectedId = String(item.id);
    renderAll();
    toast(`${item.title} was requested in Seerr.`);
  } catch (error) {
    if (error.message === "Already requested in Seerr") {
      item.seerr.state = "requested";
      item.seerr.label = "Requested";
      item.seerr.requestable = false;
      renderAll();
      toast(`${item.title} is already requested in Seerr.`);
      return;
    }
    toast(`Request failed: ${error.message}`);
  }
}

function shouldIgnoreCardToggle(target) {
  if (!(target instanceof Element)) return false;
  return Boolean(
    target.closest(
      "a[href], button, input, select, textarea, summary, [role='button'], [contenteditable='true']",
    ),
  );
}

els.refresh.addEventListener("click", () => {
  state.season = els.season.value;
  state.year = Number(els.year.value);
  state.selectedId = null;
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.prevSeason.addEventListener("click", () => shiftSeason(-1));
els.nextSeason.addEventListener("click", () => shiftSeason(1));

els.season.addEventListener("change", (event) => {
  state.season = event.target.value;
  state.selectedId = null;
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.filterSeason.addEventListener("change", (event) => {
  state.season = event.target.value;
  state.selectedId = null;
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.year.addEventListener("change", () => {
  state.year = Number(els.year.value);
  state.selectedId = null;
  resetPage();
  updateSeasonControls();
  loadSeason();
});

els.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  resetPage();
  renderAll();
});

els.filter.addEventListener("change", (event) => {
  state.filter = event.target.value;
  resetPage();
  renderAll();
});

els.sort.addEventListener("change", (event) => {
  state.sort = event.target.value;
  resetPage();
  renderAll();
});

if (els.hideRequested) {
  els.hideRequested.addEventListener("change", (event) => {
    state.hideRequested = event.target.checked;
    resetPage();
    renderAll();
  });
}

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
    state.hideRequested = false;
    state.query = "";
    els.filter.value = state.filter;
    els.search.value = "";
    if (els.hideRequested) {
      els.hideRequested.checked = false;
    }
  } else if (quickFilter === "requestable" || quickFilter === "missing_mapping") {
    state.filter = quickFilter;
    els.filter.value = quickFilter;
  } else {
    state.audioFilter = quickFilter;
  }
  resetPage();
  setFilterOpen(false);
  renderAll();
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".ui-select")) {
    setCustomSelectOpen(null);
  }
  if (state.filterOpen && !event.target.closest(".filter-actions")) {
    setFilterOpen(false);
  }
});

els.sections.addEventListener("click", (event) => {
  const pagerButton = event.target.closest("[data-page]");
  if (pagerButton) {
    state.page = sanitizePage(pagerButton.dataset.page, visibleItems().length);
    renderAll();
    return;
  }
  const requestButton = event.target.closest("[data-request]");
  if (requestButton) {
    requestItem(requestButton.dataset.request);
    return;
  }
  if (shouldIgnoreCardToggle(event.target)) return;
  const card = event.target.closest(".anime-card");
  if (!card) return;
  toggleSelectedItem(String(card.dataset.id));
});

els.spotlight.addEventListener("click", (event) => {
  if (event.target.closest(".spotlight-close")) {
    state.selectedId = null;
    renderAll();
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

compactDetailsMedia.addEventListener("change", () => {
  renderAll();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setCustomSelectOpen(null);
    setFilterOpen(false);
  }
});

window.weebarrToggleSelect = toggleSelectedItem;
applyTheme();
initializeCustomSelects();
document.body.classList.toggle("compact-preview", forceCompactPreview);
updateSeasonControls();
if (els.hideRequested) {
  els.hideRequested.checked = state.hideRequested;
}
loadSeason();
