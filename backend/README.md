Backend (Flask) for Student Link Manager

Quick start (locally):

1. Create and activate a Python virtualenv

```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

2. Deploy: push this `backend` folder to a GitHub repo and connect to Render/Heroku/Railway. The `Procfile` is included for Heroku-style hosts. Ensure port 5000 is reachable.

The backend exposes JSON endpoints:
- `GET /api/urls`
- `POST /api/add` (JSON body)
- `GET /api/search?q=`
- `GET /api/export`
- `GET /qr/<code>`
- `GET /<short_code>` redirects to long URL
