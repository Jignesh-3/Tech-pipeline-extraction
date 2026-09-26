# ⚡ JOB_STREAM.IO // Tech Job Intelligence Pipeline

> High-throughput automated tech job ingestion engine featuring deterministic SHA-256 deduplication, native SQLite JSON-array analytics, background scheduling, and a kinetic dark-terminal telemetry interface.

---

## 🛠 System Architecture

```text
[ RemoteOK Feed ] ──> [ Resilient HTTP Scraper ] ──> [ Skill & Seniority Parser ]
                                                             │
                                                             ▼
[ SQLite Storage ] <── [ Idempotent Upsert ] <── [ SHA-256 Hash Digest Engine ]
  (Indexed DB)         (content_hash Unique)      (company | title | description)
       │
       ├─► [ json_each() SQL Unnesting ] ──► /analytics/top-skills
       │
       └─► [ Parameterized Query Router ] ──► /jobs (Pagination & Tag Filters)
                                                        │
                                                        ▼
                                        [ Kinetic Terminal UI (Vanilla JS) ]
                                        - Dynamic Hex Telemetry Loader
                                        - Debounced Live Ingestion Filter
                                        - Real-time Skill Demand Ribbon

🚀 Key Engineering Highlights
1. Deterministic SHA-256 Deduplication (Idempotency)Combines normalized, lowercase strings of company, title, and description to produce a unique 256-bit SHA digest.Indexed on content_hash at the SQLite layer.Incoming jobs that already exist trigger an UPDATE on last_seen_at rather than duplicating rows, ensuring zero data redundancy across scraper cycles.
2. Native SQLite JSON Analytics (json_each)Tech skill sets (["Python", "FastAPI", "Docker"]) are stored as native JSON text within each record.The /analytics/top-skills endpoint uses SQLite’s built-in json_each() virtual table to unnest arrays and run GROUP BY aggregations in pure SQL:SQLSELECT j.value AS skill, COUNT(*) AS count
FROM jobs, json_each(jobs.skills) AS j
GROUP BY j.value
ORDER BY count DESC
LIMIT ?;
Eliminates Python memory overhead and external analytical dependencies (like Pandas) for sub-millisecond aggregation throughput.
3. Asymmetric Kinetic Telemetry UIBuilt with zero-framework vanilla HTML5, CSS3, and ES6+ JavaScript.Avoids generic AI UI clichés in favor of an Obsidian Dark Terminal aesthetic (#07090e).Integrated dynamic telemetry equalizer bars and live SHA-256 hex stream cycling during API fetches.Real-time debounced search (250ms) with bidirectional skill-ribbon syncing.
4. Zero-CORS Unified RuntimeFrontend assets (index.html, style.css, app.js) are directly mounted via FastAPI's StaticFiles.Single command runtime on port 8000 with zero Cross-Origin Resource Sharing (CORS) friction.
5. Automated Background Pipeline (APScheduler)Background thread execution running an hourly ingestion cycle via BackgroundScheduler.Fully hooked into FastAPI startup and shutdown lifecycle events.

📦 Directory StructurePlaintextTech-pipeline-extractor/
├── backend/
│   ├── database.py       # Connection lifecycle, SQLite schemas, indexed queries, json_each()
│   ├── main.py           # FastAPI router, CORS setup, StaticFiles mount, lifecycle hooks
│   ├── pipeline.py       # Orchestration engine: Scrape -> Validate -> Hash -> Upsert
│   ├── scheduler.py      # Background thread management via APScheduler
│   ├── schemas.py        # Strict Pydantic v2 data contracts and envelopes
│   └── scraper.py        # Resilient HTTP client, HTML parser, skill extraction
├── frontend/
│   ├── app.js            # Telemetry loader, dynamic hex generator, API controller
│   ├── index.html        # Semantic HUD structure and filter matrix
│   └── style.css         # Kinetic CSS, custom equalizers, spring physics
├── brain.md              # Engineering decision records and implementation progress
└── requirements.txt      # Locked dependency manifest

## ⚙️ API Specification

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/jobs` | Paginated job feed with skill and experience filters | `200 OK` |
| `GET` | `/jobs/{job_id}` | Fetch a single job record by ID | `200` / `404` |
| `GET` | `/analytics/top-skills` | SQLite `json_each()` frequency aggregation | `200 OK` |
| `POST` | `/pipeline/trigger` | On-demand scrape, validate & SHA-256 deduplication run | `200 OK` |
| `GET` | `/health` | System health check and scheduler status | `200 OK` |
| `GET` | `/docs` | Interactive OpenAPI / Swagger UI | `200 OK` |

---

### Endpoint Details

#### `GET /jobs`
Returns paginated job items matching the requested criteria.
* **Query Parameters:**
  * `skill` *(string, optional)* — Filter by extracted tech skill (e.g. `Python`, `Docker`).
  * `experience_level` *(string, optional)* — `Entry Level`, `Mid Level`, or `Senior`.
  * `page` *(integer, default: 1)* — Current page index.
  * `page_size` *(integer, default: 10, max: 100)* — Number of records per page.
* **Response:** `PaginatedJobResponse` envelope containing `total_count`, `has_next`, and `items[]`.

#### `GET /analytics/top-skills`
Computes real-time market demand metrics via database-native JSON unnesting.
* **Query Parameters:**
  * `limit` *(integer, default: 10, max: 50)* — Top N skills to rank.
* **Response:**
  ```json
  {
    "total_analyzed_jobs": 99,
    "top_skills": [
      { "skill": "REST", "count": 13 },
      { "skill": "Kubernetes", "count": 6 },
      { "skill": "Python", "count": 4 }
    ]
  }

Response:

JSON
{
  "message": "Pipeline execution completed successfully",
  "metrics": {
    "total_fetched": 99,
    "newly_inserted": 0,
    "duplicates_updated": 99,
    "validation_failures": 0
  }
}

🏃 Local Setup & ExecutionPrerequisitesPython 3.10+Virtual environment (venv)
1. Clone & Set Up Environment
Bash
git clone [https://github.com/your-username/Tech-pipeline-extractor.git](https://github.com/your-username/Tech-pipeline-extractor.git)
cd Tech-pipeline-extractor

# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
2. Install Dependencies
Bash
pip install -r requirements.txt
3. Initialize & Populate Database
Bash
python -m backend.pipeline
4. Boot Unified Server
Bash
uvicorn backend.main:app --reload
Navigate to http://127.0.0.1:8000/ for the kinetic dashboard, or http://127.0.0.1:8000/docs for interactive API exploration.


---

### Step 2: Update `requirements.txt`

Ensure all runtime dependencies are cleanly tracked:

```text
fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
requests>=2.31.0
apscheduler>=3.10.4