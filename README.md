# Task & Budget Manager

Production-ready setup for free deployment.

## Quick Start (Local)

```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
set FLASK_APP=app.py; set FLASK_DEBUG=1; python app.py
```

Or production-like:

```powershell
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:8000
```

## Deploy Options (Free)

- Render (Free Web Service)
  1. Push this repo to GitHub.
  2. Create a new Web Service on Render, connect repo.
  3. Build Command: `pip install -r requirements.txt && pip install gunicorn`
  4. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
  5. (Optional) Add a persistent disk if you need SQLite persistence; otherwise, data resets on redeploy.

- Railway
  1. New Project → Deploy from GitHub.
  2. It detects the Python app; if not, use Dockerfile.
  3. Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
  4. Add a Volume for `/app/instance` to persist the SQLite DB.

- Fly.io (Free credits)
  1. Install `flyctl`, run `fly launch` (use the Dockerfile).
  2. Create a volume: `fly volumes create app_data -r <region> -s 1`.
  3. Mount volume to `/app/instance` in `fly.toml`.

## Configuration

- Port: reads `PORT` env (defaults to 8000 in Procfile/Dockerfile).
- Database: by default uses SQLite at `instance/app.db`.
  - For persistence in the cloud, mount a volume to `/app/instance`.
  - To use Postgres, set `DATABASE_URL` in `config.py` and install `psycopg2-binary`.

## Notes

- Static files served by Flask; for heavy static use, consider a CDN.
- Debug server is not for production; prefer Gunicorn.
