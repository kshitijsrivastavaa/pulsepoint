"""
PulsePoint ingestion pipeline.

Pulls live tech job postings for India from the Adzuna API, cleans them,
extracts skills mentioned in the description, tags a role category, and
stores everything in Postgres/SQLite - deduped on Adzuna's own job id.

Run manually:
    python -m app.ingestion

Or trigger it via the /ingest API endpoint (see main.py), or schedule it
with a cron job / Render Cron Job for daily refreshes.
"""

import os
import re
import requests
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from .models import JobPosting

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search"

SKILL_VOCAB = [
    "python", "java", "javascript", "typescript", "react", "next.js", "node.js",
    "spring boot", "django", "flask", "fastapi", "sql", "postgresql", "mongodb",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd", "rest api",
    "graphql", "machine learning", "deep learning", "tensorflow", "pytorch",
    "pandas", "numpy", "power bi", "tableau", "excel", "spark", "hadoop",
    "airflow", "kafka", "redis", "html", "css", "c++", "c#", "go", "rust",
    "linux", "agile", "scrum",
]

ROLE_KEYWORDS = {
    "Data Analyst": ["data analyst", "business analyst", "bi analyst"],
    "Data Engineer": ["data engineer", "etl", "data pipeline"],
    "ML/AI": ["machine learning", "ml engineer", "ai engineer", "data scientist"],
    "Backend": ["backend developer", "backend engineer", "api developer"],
    "Frontend": ["frontend developer", "frontend engineer", "react developer"],
    "Full Stack": ["full stack", "fullstack"],
    "SDE": ["software engineer", "software developer", "sde"],
    "DevOps": ["devops", "site reliability", "platform engineer"],
}


def extract_skills(text: str) -> List[str]:
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for skill in SKILL_VOCAB:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def categorize_role(title: str) -> str:
    title_lower = (title or "").lower()
    for category, keywords in ROLE_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return category
    return "Other/Tech"


def fetch_adzuna_jobs(page: int = 1, results_per_page: int = 50, what: str = "software developer") -> List[Dict]:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError(
            "Missing Adzuna credentials. Set ADZUNA_APP_ID and ADZUNA_APP_KEY "
            "env vars (get a free key at https://developer.adzuna.com/)."
        )

    url = f"{ADZUNA_BASE_URL}/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": what,
        "content-type": "application/json",
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json().get("results", [])


def run_ingestion(db: Session, pages: int = 2, search_terms: Optional[List[str]] = None) -> dict:
    if search_terms is None:
        search_terms = ["software developer", "data analyst", "data engineer", "full stack developer"]

    fetched, new_records, skipped = 0, 0, 0

    for term in search_terms:
        for page in range(1, pages + 1):
            try:
                results = fetch_adzuna_jobs(page=page, what=term)
            except Exception as e:
                print(f"[ingestion] failed fetching '{term}' page {page}: {e}")
                continue

            for job in results:
                fetched += 1
                adzuna_id = str(job.get("id"))

                exists = db.query(JobPosting).filter(JobPosting.adzuna_id == adzuna_id).first()
                if exists:
                    skipped += 1
                    continue

                title = job.get("title", "")
                description = job.get("description", "")
                location_area = job.get("location", {}).get("area", [])
                if len(location_area) >= 2:
                    city = location_area[-1]
                elif location_area and location_area[0].strip().lower() == "india":
                    city = "Remote / Pan-India"
                else:
                    city = job.get("location", {}).get("display_name", "Unknown")

                posting = JobPosting(
                    adzuna_id=adzuna_id,
                    title=title,
                    company=job.get("company", {}).get("display_name", "Unknown"),
                    location=job.get("location", {}).get("display_name", "Unknown"),
                    city=city,
                    description=description,
                    salary_min=job.get("salary_min"),
                    salary_max=job.get("salary_max"),
                    role_category=categorize_role(title),
                    skills_extracted=",".join(extract_skills(f"{title} {description}")),
                    posted_date=_parse_date(job.get("created")),
                    source_url=job.get("redirect_url"),
                )
                db.add(posting)
                new_records += 1

            db.commit()

    return {
        "fetched": fetched,
        "new_records": new_records,
        "skipped_duplicates": skipped,
        "message": f"Ingested {new_records} new postings out of {fetched} fetched.",
    }


def _parse_date(date_str: Optional[str]):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        summary = run_ingestion(db)
        print(summary)
    finally:
        db.close()
