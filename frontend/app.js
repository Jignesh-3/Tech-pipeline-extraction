/**
 * JOB_STREAM.IO // Application Engine
 * Manages live telemetry, API queries, kinetic loader cycling, and pagination.
 */

// Application State
const state = {
  page: 1,
  pageSize: 9,
  skill: "",
  experienceLevel: "",
  totalJobs: 0,
  totalPages: 1,
  isLoading: false,
};

// DOM Node Cache
const DOM = {
  hudTotalJobs: document.getElementById("hud-total-jobs"),
  skillsRibbon: document.getElementById("skills-ribbon"),
  searchInput: document.getElementById("search-input"),
  inputStatus: document.getElementById("input-status"),
  expPills: document.querySelectorAll(".pill-chip"),
  jobGrid: document.getElementById("job-grid"),
  emptyState: document.getElementById("empty-state"),
  loader: document.getElementById("stream-loader"),
  loaderHash: document.getElementById("loader-hash"),
  loaderLog: document.getElementById("loader-log"),
  btnSync: document.getElementById("btn-trigger-scrape"),
  btnPrev: document.getElementById("btn-prev-page"),
  btnNext: document.getElementById("btn-next-page"),
  pageRange: document.getElementById("page-range"),
  pageTotal: document.getElementById("page-total"),
  pageBadge: document.getElementById("current-page-badge"),
  btnReset: document.getElementById("btn-reset-filters"),
};

// Simulated Hex Generator for Kinetic Telemetry Loader
let hexInterval = null;
const LOG_MESSAGES = [
  "CONNECTING_NODES_AND_DECRYPTING_BUFFERS...",
  "EVALUATING_DETERMINISTIC_SHA256_FINGERPRINTS...",
  "UNNESTING_SQL_JSON_ARRAYS...",
  "HYDRATING_RESPONSIVE_JOB_STREAM...",
];

function startLoaderTelemetry() {
  DOM.loader.classList.remove("hidden");
  DOM.jobGrid.style.opacity = "0.2";
  let logIdx = 0;

  hexInterval = setInterval(() => {
    // Generate pseudo SHA-256 chunk
    const pseudoHash = Array.from({ length: 4 }, () =>
      Math.random().toString(16).substring(2, 8)
    ).join("::");
    DOM.loaderHash.textContent = `SHA-256::[${pseudoHash}]`;

    if (Math.random() > 0.75) {
      DOM.loaderLog.textContent = LOG_MESSAGES[logIdx % LOG_MESSAGES.length];
      logIdx++;
    }
  }, 90);
}

function stopLoaderTelemetry() {
  clearInterval(hexInterval);
  DOM.loader.classList.add("hidden");
  DOM.jobGrid.style.opacity = "1";
}

// Format relative date preview
function formatTimestamp(isoString) {
  if (!isoString) return "RECENT";
  try {
    const d = new Date(isoString);
    return d.toISOString().split("T")[0];
  } catch {
    return "RECENT";
  }
}

// ==========================================
// 0. SYNTHETIC WEB AUDIO TELEMETRY ENGINE
// ==========================================

class AudioTelemetryEngine {
  constructor() {
    this.ctx = null;
    this.muted = false;
  }

  _initContext() {
    if (!this.ctx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContextClass();
    }
    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  playTone(freq = 800, type = "sine", duration = 0.04, gainVal = 0.04) {
    if (this.muted) return;
    try {
      this._initContext();
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type; // "sine" (soft), "triangle" (tactile switch), "square" (chip)
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      // Micro-envelope with fast exponential decay
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch {
      // Graceful fallback if autoplay restrictions trigger before user interaction
    }
  }

  // Preset tactile cues
  click() {
    // Crisp mechanical switch snap (1200Hz -> 200Hz drop over 18ms)
    this.playTone(1100, "triangle", 0.018, 0.04);
  }

  chipSelect() {
    // Sub-harmonic tag switch chime
    this.playTone(720, "sine", 0.035, 0.035);
  }

  cardHover() {
    // Ultra-faint high-hat click on 3D boundary entry
    this.playTone(1800, "triangle", 0.008, 0.015);
  }

  streamStart() {
    // Ascending dual chirp (trigger pipeline initiated)
    this.playTone(480, "sine", 0.06, 0.05);
    setTimeout(() => this.playTone(960, "sine", 0.08, 0.05), 65);
  }

  streamComplete() {
    // Harmonic resolving chord (upsert & commit verified)
    this.playTone(523.25, "sine", 0.12, 0.04); // C5
    setTimeout(() => this.playTone(659.25, "sine", 0.14, 0.04), 70); // E5
    setTimeout(() => this.playTone(783.99, "sine", 0.18, 0.04), 140); // G5
  }
}

const SFX = new AudioTelemetryEngine();

// 1. Fetch Analytics & Render Skill Chips
async function fetchAnalytics() {
  try {
    const res = await fetch("/analytics/top-skills?limit=10");
    if (!res.ok) throw new Error("Failed to load skill analytics");
    const data = await res.json();

    DOM.hudTotalJobs.textContent = data.total_analyzed_jobs || "--";
    renderSkillsRibbon(data.top_skills || []);
  } catch (err) {
    console.error("[!] Analytics error:", err);
  }
}

function renderSkillsRibbon(skills) {
  DOM.skillsRibbon.innerHTML = "";
  skills.forEach(({ skill, count }) => {
    const chip = document.createElement("button");
    chip.className = `skill-chip ${state.skill.toLowerCase() === skill.toLowerCase() ? "active" : ""}`;
    chip.innerHTML = `
      <span>${skill}</span>
      <span class="skill-count-badge">${count}</span>
    `;

    chip.addEventListener("click", () => {
      SFX.chipSelect();
      if (state.skill.toLowerCase() === skill.toLowerCase()) {
        state.skill = "";
        DOM.searchInput.value = "";
      } else {
        state.skill = skill;
        DOM.searchInput.value = skill;
      }
      state.page = 1;
      updateActiveChips();
      fetchJobs();
    });

    DOM.skillsRibbon.appendChild(chip);
  });
}

function updateActiveChips() {
  const chips = DOM.skillsRibbon.querySelectorAll(".skill-chip");
  chips.forEach((c) => {
    const name = c.querySelector("span").textContent.trim();
    if (state.skill.toLowerCase() === name.toLowerCase()) {
      c.classList.add("active");
    } else {
      c.classList.remove("active");
    }
  });
}

// 2. Fetch Jobs Feed with Parameterized Querying & Pagination
async function fetchJobs() {
  state.isLoading = true;
  startLoaderTelemetry();

  try {
    const params = new URLSearchParams({
      page: state.page,
      page_size: state.pageSize,
    });

    if (state.skill) params.append("skill", state.skill);
    if (state.experienceLevel) params.append("experience_level", state.experienceLevel);

    const res = await fetch(`/jobs?${params.toString()}`);
    if (!res.ok) throw new Error("API stream fetch error");

    const data = await res.json();
    state.totalJobs = data.total_count;
    state.totalPages = Math.ceil(data.total_count / state.pageSize) || 1;

    renderJobs(data.items);
    updatePaginationHUD(data);
  } catch (err) {
    console.error("[!] Ingestion query error:", err);
    DOM.jobGrid.innerHTML = "";
    DOM.emptyState.classList.remove("hidden");
  } finally {
    state.isLoading = false;
    stopLoaderTelemetry();
  }
}

// 3. Render Cards with Staggered Kinetic Delays
// --- Kinetic Text-Scramble Decoder Engine ---
const SCRAMBLE_CHARS = "01#X%_<>[]/\\*&^~!=+";

function scrambleText(element, targetText, duration = 300) {
  const steps = 12;
  const stepTime = duration / steps;
  let iteration = 0;

  const timer = setInterval(() => {
    element.textContent = targetText
      .split("")
      .map((char, index) => {
        if (char === " ") return " ";
        if (index < (iteration / steps) * targetText.length) {
          return targetText[index];
        }
        return SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
      })
      .join("");

    iteration++;
    if (iteration > steps) {
      clearInterval(timer);
      element.textContent = targetText;
    }
  }, stepTime);
}

// --- 3D Physics Tilt & Cursor Spotlight Engine ---
function attachCardPhysics(card) {
  const maxTilt = 10; // Max tilt in degrees

  card.addEventListener("mousemove", (e) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Update CSS variables for the radial spotlight gradient
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);

    // Calculate rotational offsets relative to card center
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -maxTilt;
    const rotateY = ((x - centerX) / centerX) * maxTilt;

    card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`;
  });

  card.addEventListener("mouseleave", () => {
    card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    card.style.transition = "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease";
  });

  card.addEventListener("mouseenter", () => {
    card.style.transition = "none";  // Instant response during movement
    SFX.cardHover();
  });
}

// Render Cards with Staggered Kinetic Delays, 3D Physics, & Matrix Decryption
function renderJobs(jobs) {
  DOM.jobGrid.innerHTML = "";

  if (!jobs || jobs.length === 0) {
    DOM.emptyState.classList.remove("hidden");
    return;
  }

  DOM.emptyState.classList.add("hidden");

  jobs.forEach((job, index) => {
    const card = document.createElement("article");
    card.className = "job-card";
    card.style.animationDelay = `${index * 45}ms`;

    const tierClass =
      job.experience_level === "Senior"
        ? "tier-senior"
        : job.experience_level === "Entry Level"
        ? "tier-entry"
        : "tier-mid";

    const skillsHtml = (job.skills || [])
      .slice(0, 5)
      .map((s) => `<span class="card-skill-pill">${s}</span>`)
      .join("");

    const hashShort = job.content_hash ? job.content_hash.substring(0, 12) : "UNHASHED";

    card.innerHTML = `
      <div class="card-top">
        <div>
          <div class="company-name">${escapeHtml(job.company)}</div>
          <h2 class="role-title"></h2>
        </div>
        <span class="tier-badge ${tierClass}">${escapeHtml(job.experience_level || "MID")}</span>
      </div>

      <p class="card-desc">${escapeHtml(job.description || "No preview description provided.")}</p>

      <div class="card-skills-row">
        ${skillsHtml}
      </div>

      <div class="card-footer">
        <span class="hash-preview">HASH::${hashShort} | ${formatTimestamp(job.last_seen_at)}</span>
        <a href="${escapeHtml(job.job_url)}" target="_blank" rel="noopener noreferrer" class="btn-apply-cta">
          VIEW_LISTING ↗
        </a>
      </div>
    `;

    DOM.jobGrid.appendChild(card);

    // Attach 3D tilt tracking & spotlight coords
    attachCardPhysics(card);

    // Trigger matrix text-scramble on title
    const titleElem = card.querySelector(".role-title");
    setTimeout(() => {
      scrambleText(titleElem, job.title, 320);
    }, index * 45);
  });
}

function updatePaginationHUD(data) {
  const start = data.total_count === 0 ? 0 : (state.page - 1) * state.pageSize + 1;
  const end = Math.min(state.page * state.pageSize, data.total_count);

  DOM.pageRange.textContent = `${start}-${end}`;
  DOM.pageTotal.textContent = data.total_count;
  DOM.pageBadge.textContent = `PAGE ${state.page} OF ${state.totalPages}`;

  DOM.btnPrev.disabled = state.page <= 1;
  DOM.btnNext.disabled = !data.has_next;
}

// 4. Debounced Search Handling
let debounceTimer = null;
DOM.searchInput.addEventListener("input", (e) => {
  DOM.inputStatus.textContent = "SYNCING...";
  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    state.skill = e.target.value.trim();
    state.page = 1;
    updateActiveChips();
    fetchJobs();
    DOM.inputStatus.textContent = "READY";
  }, 250);
});

// 5. Experience Pill Filter Toggles
DOM.expPills.forEach((pill) => {
  pill.addEventListener("click", () => {
    DOM.expPills.forEach((p) => p.classList.remove("active"));
    pill.classList.add("active");

    state.experienceLevel = pill.getAttribute("data-exp");
    state.page = 1;
    fetchJobs();
  });
});

// 6. Pagination Navigation Events
DOM.btnPrev.addEventListener("click", () => {
  SFX.click();
  if (state.page > 1) {
    state.page--;
    fetchJobs();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
});

DOM.btnNext.addEventListener("click", () => {
  SFX.click();
  if (state.page < state.totalPages) {
    state.page++;
    fetchJobs();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
});

// 7. Reset Filters Button
DOM.btnReset.addEventListener("click", () => {
  SFX.click();
  state.skill = "";
  state.experienceLevel = "";
  state.page = 1;
  DOM.searchInput.value = "";
  DOM.expPills.forEach((p) => p.classList.remove("active"));
  DOM.expPills[0].classList.add("active");
  updateActiveChips();
  fetchJobs();
});


// 8. On-Demand Pipeline Trigger Button (Acoustic Telemetry Wired)
DOM.btnSync.addEventListener("click", async () => {
  SFX.streamStart(); // Ascending acoustic dual-chirp on trigger

  DOM.btnSync.disabled = true;
  DOM.btnSync.querySelector(".btn-label").textContent = "INGESTING...";
  startLoaderTelemetry();

  try {
    const res = await fetch("/pipeline/trigger", { method: "POST" });
    const result = await res.json();
    console.log("[+] Pipeline trigger metrics:", result.metrics);

    SFX.streamComplete(); // Harmonic resolution chord on SQLite commit

    // Refresh analytics & current feed view
    await fetchAnalytics();
    await fetchJobs();
  } catch (err) {
    console.error("[!] Trigger failed:", err);
  } finally {
    DOM.btnSync.disabled = false;
    DOM.btnSync.querySelector(".btn-label").textContent = "TRIGGER SYNC";
    stopLoaderTelemetry();
  }
});

// XSS Prevention Utility
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initial Boot
document.addEventListener("DOMContentLoaded", () => {
  fetchAnalytics();
  fetchJobs();
});