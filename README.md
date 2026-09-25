# Foliora (Phase 1: startup landing page + featured portfolio)

## Run locally
```
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env
# put your deployed portfolio link in PORTFOLIO_URL inside .env
flask --app wsgi run
```
Open http://127.0.0.1:5000

## Structure
- `app/blueprints/main`: public pages (later: catalog, auth, billing, portfolio, admin blueprints)
- `app/data.py`: Phase 1 content (replaced by database models later)
- `portfolio_templates/`: reserved for Phase 2 reusable templates
- `config.py`: all settings via `.env` (portfolio URL is never hardcoded)

## Deploy on Render
Build: `pip install -r requirements.txt`  Start: `gunicorn wsgi:app`
Env vars: `SECRET_KEY`, `FLASK_ENV=production`, `PORTFOLIO_URL`, `STARTUP_NAME`, `CONTACT_EMAIL`
