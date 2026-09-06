from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from .database import Base


class JobPosting(Base):
    """
    One row = one job posting pulled from Adzuna.
    We store both the raw fields (for traceability) and the
    derived/cleaned fields (skills_extracted, role_category) that
    the analytics endpoints actually query against.
    """
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    adzuna_id = Column(String, unique=True, index=True)  # dedupe key
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String, index=True)
    city = Column(String, index=True)
    description = Column(Text)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    role_category = Column(String, index=True)  # e.g. "SDE", "Data Analyst", "ML"
    skills_extracted = Column(Text)  # comma-separated, e.g. "python,react,aws"
    posted_date = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String, nullable=True)
