# API reference
All endpoints except register, login and health-check need `Authorization: Bearer <token>`. Errors: `{"detail": "..."}`. Live docs at `/docs`.

| Method | Path | Notes |
|---|---|---|
| POST | /api/auth/register | email, password (8+, letter+number), full_name, district, mandal?, language |
| POST | /api/auth/login | returns access_token and user |
| GET/PUT | /api/auth/me | profile |
| GET | /api/crops/catalog | supported crops |
| GET/POST | /api/crops | list (limit, offset) / create |
| GET/PUT/DELETE | /api/crops/{id} | owner only, else 404 |
| GET | /api/guidance/{crop_id} | stage, activities, irrigation, nutrients, monitoring, reminders |
| GET | /api/crop-calendar/{crop_id} | all stages with dates and status |
| GET | /api/health/status | model availability, problem options |
| POST | /api/health/analyse | multipart: file, crop_id or crop_name. 400/413/415 on bad images |
| GET | /api/health/reports, /reports/{id}, /reports/{id}/image | owner only |
| POST | /api/risk/reports | multipart: crop_name, district, area?, report_date, problem, notes?, photo? |
| GET | /api/risk/alerts | crop, district filters |
| GET | /api/risk/reports/mine | own reports |
| GET | /api/markets/prices | crop, district?, days? |
| POST | /api/markets/compare | crop, quantity, quantity_unit, other_expenses, default_transport_cost, transport_costs |
| POST | /api/markets/calculate | manual options: market, price, price_unit, transport_cost |
| GET | /api/markets/history | saved comparisons |
| POST | /api/markets/refresh | live provider; 503 if not configured |
| GET | /api/intercrop/crops, /api/intercrop/meta | Smart Intercrop catalogue and engine info |
| POST | /api/intercrop/recommend | see docs/intercrop.md |
| GET | /api/dashboard/summary | dashboard data |
| GET, PUT | /api/notifications, /api/notifications/{id}/read | |
| GET | /api/health-check | public status |

Net return: gross = quantity (quintals) x price per quintal; net = gross - transport - other expenses. 1 tonne = 10 quintal, 100 kg = 1 quintal; unknown units return 422.
