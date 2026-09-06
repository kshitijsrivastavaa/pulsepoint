from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobPostingOut(BaseModel):
    id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    city: Optional[str]
    role_category: Optional[str]
    skills_extracted: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    posted_date: Optional[datetime]
    source_url: Optional[str]

    class Config:
        from_attributes = True


class SkillTrend(BaseModel):
    skill: str
    count: int


class CityHeatmap(BaseModel):
    city: str
    count: int


class PostingsOverTime(BaseModel):
    date: str
    count: int


class IngestResult(BaseModel):
    fetched: int
    new_records: int
    skipped_duplicates: int
    message: str
