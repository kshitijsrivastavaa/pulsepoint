# PulsePoint — India's Tech Job Market, Live

A full pipeline that pulls real job postings from the Adzuna API, extracts
trending skills and role categories, stores everything in a database, and
serves it through a FastAPI backend to a live dashboard.

**Why this project works for interviews:** it's not a downloaded CSV +
notebook. You built the ingestion, the schema, the API, and the dashboard —
every layer is yours to defend.

---

## Architecture

```
Adzuna API  →  ingestion.py (clean + extract skills + categorize role)
            →  Postgres/SQLite (job_postings table)
            →  FastAPI (/trending-skills, /hiring-by-city, /role-breakdown, /postings-over-time)
            →  dashboard.html (Chart.js, calls the API directly)
```

## 1. Get a free Adzuna API key

1. Go to https://developer.adzuna.com/
2. Sign up (free) → create an app → copy your `app_id` and `app_key`
3. Takes about 2 minutes, no credit card

## 2. Run it locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # then fill in your Adzuna keys
export $(cat .env | xargs)  # loads env vars into your shell (Linux/Mac)

# start the API
uvicorn app.main:app --reload
```

API is now live at `http://127.0.0.1:8000`. Interactive docs at
`http://127.0.0.1:8000/docs`.

Pull your first batch of real data:

```bash
curl -X POST "http://127.0.0.1:8000/ingest?pages=2"
```

This hits Adzuna, cleans the results, extracts skills, and stores them.
Run it again anytime (daily via cron) to keep the dataset fresh — duplicates
are automatically skipped.

## 3. View the dashboard

Open `frontend/dashboard.html` in your browser. If your API isn't running
on `127.0.0.1:8123`, open the file and edit this line in the `<script>`
section:

```js
const API_BASE = window.PULSEPOINT_API_BASE || "http://127.0.0.1:8000";
```

## 4. Deploy for real (free tier)

**Backend + DB → Render**
1. Push this repo to GitHub
2. On Render: New → Web Service → connect the repo, root dir `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a free Postgres instance on Render, attach it — `DATABASE_URL` is
   auto-injected
6. Add `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` as environment variables
7. (Optional) Add a Render Cron Job that hits `POST /ingest` daily to keep
   data fresh automatically

**Frontend → Vercel or just serve the static file from Render**
- Simplest: drop `dashboard.html` into Vercel as a static site, set
  `window.PULSEPOINT_API_BASE` to your Render URL at the top of the file
- Or skip Vercel entirely and serve the HTML file from FastAPI itself with
  `StaticFiles` — one deployment instead of two

## Extending it further (optional, for extra flex)

- Swap the regex skill-extraction in `ingestion.py` for spaCy NER — turns
  the "NLP layer" from rule-based to model-based
- Add a `/forecast` endpoint using a simple linear regression on
  `postings_over_time` to predict next week's volume
- Add salary-band analysis once you're pulling enough postings with
  `salary_min`/`salary_max` populated

## Talking points by role (same project, different framing)

- **Data Analyst**: trend analysis, skill/city breakdowns, dashboard design
- **Backend/SDE**: API design, schema design, deduplication logic
- **Data Engineer**: ingestion pipeline, scheduled refresh, ETL from raw JSON to structured rows
- **Full Stack**: FastAPI + vanilla JS dashboard, deployed end-to-end
- **Cloud**: swap S3 in front of raw Adzuna responses before processing, ties to your AWS cert
