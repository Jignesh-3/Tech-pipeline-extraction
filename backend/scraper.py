import hashlib
import re
import requests
from typing import List, Dict, Any

# Target tech skills for automatic tag extraction
TECH_KEYWORDS = [
    "Python", "FastAPI", "Django", "Flask", "PostgreSQL", "MySQL", 
    "SQLite", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", 
    "Git", "REST", "GraphQL", "Linux", "CI/CD", "Pydantic"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, application/xhtml+xml",
}


def generate_content_hash(company: str, title: str, description: str) -> str:
    """
    Standout Feature: Generates a deterministic SHA-256 digest
    based on core job attributes to eliminate duplicate listings.
    """
    raw_payload = f"{company.strip().lower()}|{title.strip().lower()}|{description.strip().lower()}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


def extract_skills(text: str) -> List[str]:
    """Scans text for predefined backend technologies."""
    found_skills = set()
    for tech in TECH_KEYWORDS:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.add(tech)
    return sorted(list(found_skills))


def extract_experience_level(title: str, text: str) -> str:
    """Classifies role experience tier based on title and description signals."""
    combined = f"{title} {text}".lower()
    if any(k in combined for k in ["senior", "sr.", "lead", "principal", "architect"]):
        return "Senior"
    elif any(k in combined for k in ["junior", "jr.", "entry", "intern", "associate", "graduate"]):
        return "Entry Level"
    return "Mid Level"


def clean_html(raw_html: str) -> str:
    """Strips HTML tags to yield clean plaintext."""
    clean_text = re.sub(r"<[^>]+>", " ", raw_html or "")
    return " ".join(clean_text.split())


# --- SOURCE 1: RemoteOK ---
def fetch_remoteok_jobs() -> List[Dict[str, Any]]:
    """Fetches and normalizes listings from RemoteOK's public API."""
    url = "https://remoteok.com/api"
    jobs = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        raw_items = response.json()

        listing_items = [item for item in raw_items if isinstance(item, dict) and "position" in item]

        for item in listing_items:
            title = item.get("position", "").strip()
            company = item.get("company", "").strip()
            description = clean_html(item.get("description", ""))
            job_url = item.get("url", "").strip()
            location = item.get("location", "").strip() or "Remote"

            if not title or not company:
                continue

            explicit_tags = item.get("tags", [])
            tag_skills = [tag.title() for tag in explicit_tags if tag.title() in TECH_KEYWORDS]
            parsed_skills = extract_skills(description)
            combined_skills = sorted(list(set(tag_skills + parsed_skills)))

            content_hash = generate_content_hash(company, title, description)
            exp_level = extract_experience_level(title, description)

            jobs.append({
                "content_hash": content_hash,
                "title": title,
                "company": company,
                "location": location,
                "job_url": job_url,
                "description": description[:1000],
                "skills": combined_skills,
                "experience_level": exp_level,
            })

    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching RemoteOK postings: {e}")

    return jobs


# --- SOURCE 2: Arbeitnow ---
def fetch_arbeitnow_jobs() -> List[Dict[str, Any]]:
    """Fetches and normalizes listings from Arbeitnow's public European/Remote API."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    jobs = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        payload = response.json()
        raw_items = payload.get("data", [])

        for item in raw_items:
            title = item.get("title", "").strip()
            company = item.get("company_name", "").strip()
            description = clean_html(item.get("description", ""))
            job_url = item.get("url", "").strip()
            location = "Remote" if item.get("remote") else (item.get("location", "").strip() or "Europe")

            if not title or not company:
                continue

            explicit_tags = item.get("tags", [])
            tag_skills = [tag.title() for tag in explicit_tags if tag.title() in TECH_KEYWORDS]
            parsed_skills = extract_skills(description)
            combined_skills = sorted(list(set(tag_skills + parsed_skills)))

            content_hash = generate_content_hash(company, title, description)
            exp_level = extract_experience_level(title, description)

            jobs.append({
                "content_hash": content_hash,
                "title": title,
                "company": company,
                "location": location,
                "job_url": job_url,
                "description": description[:1000],
                "skills": combined_skills,
                "experience_level": exp_level,
            })

    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching Arbeitnow postings: {e}")

    return jobs


# --- Master Multi-Source Extractor ---
def scrape_remote_jobs() -> List[Dict[str, Any]]:
    """
    Standout Feature: Multi-source heterogeneous ingestion pipeline.
    Combines RemoteOK and Arbeitnow, normalizing disparate payloads 
    into identical dictionary contracts ready for SHA-256 deduplication.
    """
    remoteok_jobs = fetch_remoteok_jobs()
    arbeitnow_jobs = fetch_arbeitnow_jobs()

    print(f"[*] Ingested {len(remoteok_jobs)} jobs from RemoteOK, {len(arbeitnow_jobs)} jobs from Arbeitnow.")
    return remoteok_jobs + arbeitnow_jobs