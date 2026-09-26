import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

# Database path relative to project root
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "jobs.db"


def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes the database schema and indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                job_url TEXT NOT NULL,
                description TEXT NOT NULL,
                skills TEXT NOT NULL,  -- Stored as JSON array string
                experience_level TEXT DEFAULT 'Entry Level',
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Indexes for fast querying & deduplication lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
        conn.commit()


def upsert_job(job_data: Dict[str, Any]) -> str:
    """
    Standout Feature: Deterministic Deduplication.
    Inserts a job if unique; if hash exists, updates last_seen_at.
    Returns: 'inserted' or 'updated'
    """
    now = datetime.utcnow().isoformat()
    skills_json = json.dumps(job_data.get("skills", []))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if hash already exists
        cursor.execute("SELECT id FROM jobs WHERE content_hash = ?", (job_data["content_hash"],))
        existing_job = cursor.fetchone()

        if existing_job:
            cursor.execute(
                """
                UPDATE jobs 
                SET last_seen_at = ?
                WHERE content_hash = ?
                """,
                (now, job_data["content_hash"])
            )
            conn.commit()
            return "updated"
        else:
            cursor.execute(
                """
                INSERT INTO jobs (
                    content_hash, title, company, location, job_url, 
                    description, skills, experience_level, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_data["content_hash"],
                    job_data["title"],
                    job_data["company"],
                    job_data["location"],
                    job_data["job_url"],
                    job_data["description"],
                    skills_json,
                    job_data.get("experience_level", "Entry Level"),
                    now,
                    now,
                )
            )
            conn.commit()
            return "inserted"


def query_jobs(
    skill: Optional[str] = None,
    experience_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Standout Feature: Parameterized Querying & Pagination.
    Returns: (total_matching_records, paginated_job_list)
    """
    offset = (page - 1) * page_size
    query = "SELECT * FROM jobs WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM jobs WHERE 1=1"
    params: List[Any] = []

    if skill:
        # SQLite JSON search check or LIKE match
        query += " AND skills LIKE ?"
        count_query += " AND skills LIKE ?"
        params.append(f"%{skill}%")

    if experience_level:
        query += " AND experience_level = ?"
        count_query += " AND experience_level = ?"
        params.append(experience_level)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get total matching count
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Fetch paginated rows ordered by latest first
        query += " ORDER BY last_seen_at DESC LIMIT ? OFFSET ?"
        fetch_params = params + [page_size, offset]
        
        cursor.execute(query, fetch_params)
        rows = cursor.fetchall()

        jobs = []
        for row in rows:
            job_dict = dict(row)
            job_dict["skills"] = json.loads(job_dict["skills"])
            jobs.append(job_dict)

        return total_count, jobs

def get_top_skills(limit: int = 10) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Standout Feature: Real-time skill analytics using SQL JSON unnesting.
    Extracts individual array items using SQLite json_each() and computes frequencies.
    Returns: (total_jobs_analyzed, top_skills_list)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Count total jobs sampled
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]

        # Unnest JSON array elements and group by frequency
        query = """
            SELECT 
                j.value AS skill, 
                COUNT(*) AS count
            FROM jobs, json_each(jobs.skills) AS j
            GROUP BY j.value
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        results = [{"skill": row["skill"], "count": row["count"]} for row in rows]
        return total_jobs, results