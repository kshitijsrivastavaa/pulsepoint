from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, get_db
from . import models, schemas, analytics
from .ingestion import run_ingestion

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PulsePoint API",
    description="India's tech job market, live. Ingests real postings and serves trend analytics.",
    version="0.1.0",
)

# Wide open for the portfolio project - lock this down to your actual
# frontend domain before you consider this "production".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "PulsePoint API"}


@app.post("/ingest", response_model=schemas.IngestResult)
def ingest(pages: int = 1, db: Session = Depends(get_db)):
    """Triggers a live pull from Adzuna. Call this manually, or wire it to
    a daily cron job (Render Cron Jobs, GitHub Actions schedule, etc.)."""
    result = run_ingestion(db, pages=pages)
    return result


@app.get("/trending-skills", response_model=List[schemas.SkillTrend])
def trending_skills(limit: int = 15, db: Session = Depends(get_db)):
    return analytics.get_trending_skills(db, limit=limit)


@app.get("/hiring-by-city", response_model=List[schemas.CityHeatmap])
def hiring_by_city(limit: int = 15, db: Session = Depends(get_db)):
    return analytics.get_city_heatmap(db, limit=limit)


@app.get("/postings-over-time", response_model=List[schemas.PostingsOverTime])
def postings_over_time(db: Session = Depends(get_db)):
    return analytics.get_postings_over_time(db)


@app.get("/role-breakdown")
def role_breakdown(db: Session = Depends(get_db)):
    return analytics.get_role_breakdown(db)


@app.get("/postings", response_model=List[schemas.JobPostingOut])
def list_postings(limit: int = 50, q: str = "", city: str = "", role: str = "", db: Session = Depends(get_db)):
    query = db.query(models.JobPosting)
    if q:
        query = query.filter(models.JobPosting.title.ilike(f"%{q}%"))
    if city:
        query = query.filter(models.JobPosting.city == city)
    if role:
        query = query.filter(models.JobPosting.role_category == role)
    return query.order_by(models.JobPosting.ingested_at.desc()).limit(limit).all()
