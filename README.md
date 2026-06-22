# CodeAlpha_projectname

This repository contains a Student Link Manager / URL shortener app.

Two folders were added to support deploying the frontend to Netlify and the backend to a Python host:

- `netlify-frontend/` — static single-page frontend suitable for Netlify. Edit `app.js` to set `API_BASE` to your backend.
- `backend/` — Flask app exposing JSON API endpoints and a `Procfile` for deployment to Render/Heroku/Railway.
