# AGRI INTELLIGENCE 360
**One Farmer. One Platform. Four Intelligent Agricultural Solutions.**

AI-assisted agricultural decision-support web app, starting with Kurnool, Andhra Pradesh. English and Telugu.

| Module | Purpose |
|---|---|
| **Krishi Buddhi** | Stage-wise crop calendar, activities, irrigation and monitoring guidance from the sowing date |
| **Pest Alert** | Leaf-photo analysis through a replaceable AI model, plus community risk alerts |
| **Mandi Mate** | Market price comparison ranked by estimated net return |
| **Smart Intercrop** | Explainable, rule-based companion-crop recommendations with planting arrangements (see `docs/intercrop.md`) |

## 1. Problem statement
Small farmers decide on crop care, pest response and selling using scattered information. Stage timing is guessed, disease is noticed late, and the market with the highest listed price is often not the one that pays most after transport and costs.

## 2. Objectives
Personalised stage-wise guidance; an AI-assisted crop health indication with honest uncertainty; net-return market comparison; one shared crop record across modules; English and Telugu; no paid APIs.

## 3. Features
- Register/login, JWT-protected API, PBKDF2-SHA256 hashing, per-user record ownership
- Dashboard built from the database (crops, activities, health reports, prices, alerts, notifications)
- Crops: Groundnut, Cotton, Paddy, Red gram. Stage data is in `data/crop_catalog.json`, loaded into the `crop_stages` table (extensible without code changes)
- Image upload validated by decoding content (not filename/content-type), with size and dimension limits
- Replaceable model interface. The app starts without a model and says so; it never invents predictions
- Community reports grouped by crop, problem and district. Alert = at least 3 reports from at least 2 farmers in 14 days, labelled suspected, not confirmed
- Market comparison with unit conversion (quintal/kg/tonne), visible formulas, ranking, history chart, source and date per price
- English/Telugu UI from `frontend/src/i18n/translations.js`
- In-app notifications only. **SMS and WhatsApp are not implemented.**

- Smart Intercrop: 16 crops, Kharif/Rabi/Zaid, soil, pH, temperature, rainfall and water inputs, scored by named criteria. Rule-based (not ML) on approximate, unverified crop traits in `data/intercrop_data.json`

## 4. Technology stack
React 18, Vite, Tailwind 3, Recharts, Lucide, React Router. Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, Pillow, PyJWT. SQLite (PostgreSQL via `DATABASE_URL`). Pytest, Vitest.

## 5. Architecture
```
React SPA --REST/JSON (Bearer JWT)--> FastAPI routes (app/api)
   services/crop_guidance.py   stage maths (pure functions)
   services/crop_health.py     validation + DiseaseClassifier interface
   services/community_risk.py  report grouping and alert rules
   services/market_intelligence.py  providers + net-return maths
   SQLAlchemy models --> SQLite / PostgreSQL
```
See `docs/architecture.md` and `docs/api.md`.

## 6. Database overview
`users`, `farmer_profiles`, `crops` (shared crop record), `crop_stages` (stage definitions and recommendations), `health_reports`, `risk_reports`, `market_prices`, `market_comparisons`, `notifications`. Foreign keys, indexes, `created_at`/`updated_at` everywhere. Password hashes are never returned. Tables are created at startup (`create_all`); add Alembic for production migrations (see docs/architecture.md).

## 7. Folder structure
```
backend/app/{api,core,database,models,schemas,services}  backend/tests
frontend/src/{components,pages,layouts,services,hooks,i18n,utils}
data/ (catalog, disease info, sample price parameters, intercrop data)    docs/
```

## 8. Install and run (Windows PowerShell)
Needs Python 3.10+ and Node.js 18+.

Backend (terminal 1):
```powershell
cd agri-intelligence-360\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
Copy-Item .env.example .env       # set SECRET_KEY
python -m uvicorn app.main:app --reload --port 8000
```
Frontend (terminal 2):
```powershell
cd agri-intelligence-360\frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Linux/macOS:
```bash
cd agri-intelligence-360/backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
# second terminal
cd agri-intelligence-360/frontend && npm install && cp .env.example .env && npm run dev
```
App http://localhost:5173 · API http://localhost:8000 · API docs http://localhost:8000/docs

## 8b. One-click start and public link (ngrok)
From the project root: `.\start-all.ps1` (sets up on first run, then opens backend, frontend and ngrok windows). If scripts are blocked: `Set-ExecutionPolicy -Scope Process Bypass`.

The frontend calls `/api` on its own origin and Vite forwards it to the backend, so one tunnel is enough: `ngrok http 5173`. Install with `winget install ngrok.ngrok` and add your token once: `ngrok config add-authtoken YOUR_TOKEN`. Anyone with the link can register and upload images, so share it only for demos and stop ngrok afterwards.

## 9. Environment variables
Backend `.env` (see `backend/.env.example`): `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `UPLOAD_DIR`, `MAX_UPLOAD_MB`, `MODEL_PATH`, `MODEL_LABELS_PATH`, `MODEL_INPUT_SIZE`, `MIN_CONFIDENCE`, `MARKET_PROVIDER`, `DATA_GOV_API_KEY`, `SEED_DEMO`. Frontend: `VITE_API_URL` (leave empty to use the built-in proxy; set only if the backend is on another domain). PostgreSQL: install `psycopg[binary]`, use `postgresql+psycopg://user:pass@host/db`.

## 10. Demo mode
With `SEED_DEMO=true` (default) the first start creates:
- Demo farmer **demo@agri360.example / Demo@12345** (also the "Try the demo account" button)
- 3 crops (groundnut, cotton, red gram) with sowing dates relative to today
- Generated sample prices labelled **Sample data** (not real)
- 4 sample community reports that trigger one labelled demo alert
- 1 crop health demonstration record (no model output; labelled)

Set `SEED_DEMO=false` for a clean database. Delete `backend/agri360.db` to reset.

## 11. Tests
```powershell
cd backend; python -m pytest -q      # 55 tests
cd ..\frontend; npm test              # translation parity + validators
```

## 12. AI model setup
No model is bundled. Pest Alert shows "AI analysis unavailable" and everything else works. To enable:
1. Get or train a Keras classifier (`.keras`/`.h5`), 224x224 RGB, inputs scaled /255, softmax output.
2. Save class labels as a JSON list in output order, named `<crop>__<condition>` (e.g. `groundnut__early_leaf_spot`, `healthy`). Labels matching `data/disease_info.json` get descriptions and advice.
3. `pip install tensorflow`, set `MODEL_PATH` and `MODEL_LABELS_PATH` in `backend/.env`, restart.

PlantVillage has few of the four crops, so use labelled groundnut, cotton, rice and pigeon pea leaf datasets, and document the dataset and licence. Results under `MIN_CONFIDENCE`, or for a different crop than selected, show as uncertain. For another framework, implement `DiseaseClassifier` in `services/crop_health.py`.

## 13. Market data integration
`MARKET_PROVIDER=sample` serves labelled synthetic prices. `DataGovProvider` targets Agmarknet data on data.gov.in: set `MARKET_PROVIDER=datagov` and `DATA_GOV_API_KEY`, then `POST /api/markets/refresh`. **It has not been tested against the live API** (no network in the build environment); field and commodity names may need adjusting. Real rows outrank sample rows; on failure the API returns a clear error and sample data stays available.

## 14. Known limitations
- Intercrop crop traits are approximate and unverified; ratios, yields and profits are not provided
- Stage windows are approximate; review with ANGRAU/KVK experts. No fertilizer or pesticide doses by design
- No trained model shipped
- Telugu covers UI and stage names; stage activity text is English
- Sample prices are synthetic; live provider untested
- No SMS/WhatsApp, password reset, rate limiting or Alembic migrations
- JWT in `localStorage`; no security review done
- No moderation of community reports

## 15. Future improvements
Alembic, verified Agmarknet feed, trained model with documented dataset, weather-adjusted stages, full Telugu guidance text, SMS via a licensed gateway, report moderation, PostgreSQL deployment.

## 16. Troubleshooting
- "Cannot reach the server": backend not running, or `npm run dev` was not restarted after editing `vite.config.js`/`.env`. Test `http://localhost:5173/api/health-check`
- CORS error: add the exact frontend origin to `CORS_ORIGINS`
- Backend on another port: start it with `--port 8001` and run the frontend with `$env:BACKEND_URL='http://127.0.0.1:8001'; npm run dev`
- Plain fonts offline: fonts load from Google Fonts, system fonts are the fallback
