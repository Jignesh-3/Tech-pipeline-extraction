# 🧠 Project Brain: Tech Job Intelligence Pipeline

An automated data pipeline and REST service engineered to scrape engineering job listings, parse unstructured text into strictly typed data models, guarantee content deduplication via cryptographic hashing, and serve high-throughput filtered endpoints with pagination.

---

## 📌 Section 1: Target Scope & Planned Features (Backend First)

### 1. Ingestion Engine (`backend/scraper.py`)
- [ ] Connect to job board targets with custom request headers and resilient session handling using `requests`.
- [ ] Parse target job fields (Title, Company, Location, Description Markup, Direct URL) using `beautifulsoup4`.
- [ ] Implement rate-limit compliance, polite request throttling, and robust `try/except` status-code handlers.

### 2. Standout #1: Deterministic Content Deduplication (`backend/database.py` / `backend/pipeline.py`)
- [ ] Compute a deterministic SHA-256 hash across primary attributes: `hash(company + title + normalized_description)`.
- [ ] Set the content hash as a unique index in the database to prevent duplicate writes across multiple scrape cycles.
- [ ] Implement an upsert strategy: if the hash exists, update the `last_seen_at` timestamp instead of throwing an error or inserting a duplicate row.

### 3. Normalization & Type Safety (`backend/schemas.py`)
- [ ] Define strict input and output data contracts using `pydantic v2`.
- [ ] Extract and normalize key data attributes: core stack (Python, FastAPI, SQL, etc.), work type (Remote, Hybrid, Onsite), and experience range.

### 4. Persistence & Database Indexing (`backend/database.py`)
- [ ] Initialize an SQLite/PostgreSQL database with schema indexes on frequently queried columns (`title`, `skills`, `created_at`, `content_hash`).
- [ ] Provide lightweight, connection-safe CRUD helper functions for bulk operations.

### 5. Pipeline Orchestration (`backend/pipeline.py`)
- [ ] Tie together `scraper.py`, `schemas.py`, and `database.py` into a unified execution script.
- [ ] Log ingestion metrics (total parsed, duplicates bypassed, newly inserted records).

### 6. Standout #2: Parameterized Filtering & Pagination API (`backend/main.py`)
- [ ] Serve high-performance endpoints via `FastAPI`.
- [ ] Expose parameterized search supporting multi-tag criteria: `GET /jobs?skills=python,fastapi&experience=fresher&location=remote`.
- [ ] Implement limit/offset or cursor-based pagination with metadata payloads (`total_count`, `page`, `page_size`, `has_next`) to protect database throughput.
- [ ] Expose interactive OpenAPI documentation (`/docs`).

### 7. Frontend Interface (Planned Post-Backend)
- [ ] Modern UI to visualize job cards, search filters, and real-time pagination state.

---

## 🚀 Section 2: Implementation Log & Live Features

### 🕒 Phase 0: Workspace Scaffolding
- [x] Dedicated project workspace initialized (`Tech-pipeline-extractor`).
- [x] Folder architecture established (`backend/` separation).
- [x] Backend files initialized (`schemas.py`, `database.py`, `scraper.py`, `pipeline.py`, `main.py`).
- [x] Project architecture and standout features documented in `brain.md`.

---

* 🕒 Phase 1: Core Backend & Data Engine
- [x] Ingestion Engine (`backend/scraper.py`) with tech skill parsing and clean HTML extraction.
- [x] Standout #1: Deterministic Deduplication engine using SHA-256 content hashing and upsert timestamps.
- [x] Strict data contracts and envelopes defined via Pydantic v2 (`backend/schemas.py`).
- [x] SQLite database layer with indexes on `content_hash`, `title`, and `company` (`backend/database.py`).
- [x] Unified pipeline runner logging ingestion metrics (`backend/pipeline.py`).
- [x] Standout #2: Parameterized multi-tag filtering and paginated API served via FastAPI (`backend/main.py`).
- [x] Verified interactive OpenAPI documentation at `/docs`.

### 🕒 Phase 2: Analytics & Metric Aggregation
- [x] Implemented `get_top_skills` in `backend/database.py` leveraging native `json_each()` SQL unnesting and `GROUP BY` counts.
- [x] Defined `SkillMetric` and `TopSkillsResponse` contracts in `backend/schemas.py`.
- [x] Exposed `GET /analytics/top-skills` with configurable limit parameters in `backend/main.py`.
- [x] Verified real-time aggregation metrics across indexed job postings.

### 🕒 Phase 3: Frontend Architecture & Motion Design

#### 1. Architecture & Delivery
- **Engine:** Vanilla HTML5, Modern CSS (Custom Properties, Flex/Grid, Glassmorphic variables), and ES6+ JavaScript.
- **Serving Strategy:** Mounted via FastAPI `StaticFiles` at `/` for zero-CORS unified runtime.
- **Search Interaction:** 250ms debounced live filtering with instant state hydration; URL query params synced for shareable filter states.

#### 2. Visual & Kinetic Language (Anti-AI Generic)
- **Theme:** Deep Carbon / Obsidian terminal base (`#090D16`) with high-contrast electric emerald (`#00F5A0`) live state indicators.
- **Typography:** Asymmetric pairing—clean technical sans-serif for primary hierarchy, matched with monospace accents for operational data (`SHA-256`, counts, dates).
- **Motion Spec:**
  - Dynamic skill ticker with live proportional frequency bars.
  - Staggered card mounting using spring physics (`cubic-bezier(0.16, 1, 0.3, 1)`).
  - Kinetic telemetry bar for pipeline ingestion runs (`/pipeline/trigger`) showing real-time stage feedback.
  - Interactive chip states with micro-feedback on click.

#### 3. Component Hierarchy
- **Header / Telemetry Strip:** Live index count, active pipeline heartbeat indicator, and on-demand ingestion trigger button.
- **Skill Frequency Ribbon:** Real-time analytics chips directly wired to `/analytics/top-skills` with visual density bars.
- **Filter Matrix:** Debounced title/keyword input, experience level selector pills (`All`, `Entry Level`, `Mid Level`, `Senior`).
- **Interactive Job Feed:** Asymmetric cards featuring company badge, role title, remote tags, extracted tech tags, relative timestamp, and direct outbound application CTA.
- **Pagination HUD:** Monospace page counter with tactile Previous/Next controls.

#### 4. Standout Kinetic Loader Specification
- **Visual Style:** Monospace Telemetry Matrix (Anti-generic spinner).
- **Core Elements:**
  - Dynamic cycling SHA-256 hash stream (`HEX_STREAM::INGESTION`).
  - Asymmetric electric emerald pulsing telemetry equalizer bars.
  - Staggered lifecycle status text (`CONNECTING_NODES` → `EVALUATING_HASH_UNIQUENESS` → `HYDRATING_FEED`).
- **Transition:** Smooth blur/spring collapse into staggered job card cascade (`cubic-bezier(0.16, 1, 0.3, 1)`).