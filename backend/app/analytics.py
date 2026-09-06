from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import JobPosting


def get_trending_skills(db: Session, limit: int = 15) -> list[dict]:
    rows = db.query(JobPosting.skills_extracted).all()
    counter = Counter()
    for (skills_str,) in rows:
        if not skills_str:
            continue
        for skill in skills_str.split(","):
            skill = skill.strip()
            if skill:
                counter[skill] += 1
    top = counter.most_common(limit)
    return [{"skill": s, "count": c} for s, c in top]


def get_city_heatmap(db: Session, limit: int = 15) -> list[dict]:
    rows = (
        db.query(JobPosting.city, func.count(JobPosting.id).label("count"))
        .group_by(JobPosting.city)
        .order_by(func.count(JobPosting.id).desc())
        .limit(limit)
        .all()
    )
    return [{"city": city or "Unknown", "count": count} for city, count in rows]


def get_postings_over_time(db: Session) -> list[dict]:
    rows = (
        db.query(
            func.date(JobPosting.ingested_at).label("date"),
            func.count(JobPosting.id).label("count"),
        )
        .group_by(func.date(JobPosting.ingested_at))
        .order_by(func.date(JobPosting.ingested_at))
        .all()
    )
    return [{"date": str(d), "count": c} for d, c in rows]


def get_role_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(JobPosting.role_category, func.count(JobPosting.id).label("count"))
        .group_by(JobPosting.role_category)
        .order_by(func.count(JobPosting.id).desc())
        .all()
    )
    return [{"role": role or "Other/Tech", "count": count} for role, count in rows]
