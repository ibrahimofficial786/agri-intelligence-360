# Architecture
The React SPA calls `/api/*` with a Bearer JWT. Routers validate input (Pydantic), check ownership and call services, which hold the logic and are testable without HTTP.

- **Shared crop record**: `crops` feeds guidance, `health_reports.crop_id`, and market comparisons (by crop name). Deleting a crop keeps its reports (`crop_id` set NULL).
- **Stage data**: `data/crop_catalog.json` is seeded into `crop_stages` for crops with no rows. To add a crop, add it to the JSON, add a `crop.<Name>` translation and the frontend crop lists. Editing the JSON later does not change existing rows.
- **Model interface**: `DiseaseClassifier` (`available`, `reason`, `predict`) loads once at startup; routes call only `crop_health.analyse`.
- **Market providers**: `market_prices` rows carry `source` and `is_sample`; real rows outrank sample rows.
- **Privacy**: reports store district and mandal only. Uploaded images are served only to their owner; community report photos are stored but not exposed.
- **Migrations**: startup uses `create_all`. For production add Alembic, point `env.py` at `app.database.db.Base.metadata`, autogenerate a baseline, drop `create_all`.
- **Security**: PBKDF2-SHA256 (310k iterations, per-user salt), JWT HS256, other users' records return 404, unhandled errors return a generic 500. Not production-reviewed.
