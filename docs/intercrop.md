# SMART INTERCROP: engine, data and references

**Tagline:** Grow Together, Earn Better. An independent fourth module (route `/app/smart-intercrop`, API `/api/intercrop/*`). No database tables were added; recommendations are computed per request and not stored.

## Engine (rule-based, not machine learning)
`backend/app/services/intercrop_engine.py`. For a main crop and season it scores every other crop that is grown in that season. Score = points earned / points possible x 100 over the criteria that could be evaluated:

| Criterion | Weight | Rule |
|---|---|---|
| Nitrogen complementarity | 15 | legume companion with non-legume main crop scores highest |
| Light sharing (canopy) | 15 | low + tall best; same canopy scores low |
| Duration fit | 15 | durations differing by 30%+ (staggered) score full; similar durations score about half |
| Root zones | 10 | shallow + deep best |
| Water need match | 10 | same class best; low vs high scores 0 |
| Water supply | 10 | farmer's water availability vs the thirstier crop (needs input) |
| Soil type | 10 | soil suits both / one / neither (needs input) |
| Temperature | 10 | within both crops' range (needs input) |
| Soil pH | 5 | within both crops' range (needs input) |

- **Gates (crop not shown, reason listed):** not grown in the chosen season; same botanical family (except legumes).
- **Missing inputs are skipped, not guessed.** Without soil, pH, temperature and water, completeness is 65% and confidence "low". Water availability is derived from rainfall or an irrigation source only when not entered, and that assumption is shown.
- **Ratings:** at least 85 highly suitable, 70 suitable, 55 marginal; below 55 is not shown.
- **Patterns:** row, strip, mixed and relay each get a suitable/less suitable flag with a reason from the same traits. Diagrams are drawn in the frontend.
- **Known systems:** a flag for combinations commonly reported in Indian intercropping literature. It does not change the score.
- **Extending to ML:** implement the `Recommender` protocol and return it from `get_recommender()`. The API shape stays the same. The response states `engine.ml_model: false`.

## Dataset
`data/intercrop_data.json`: 16 crops (paddy, maize, sorghum, groundnut, cotton, chilli, tomato, onion, coriander, red gram, black gram, green gram, bengal gram, soybean, sunflower, sugarcane) with family, legume flag, canopy, root depth, water class, duration range, seasons, suitable soils, pH and temperature ranges.

**These values are approximate general agronomic knowledge compiled for this project. They are not copied from a verified dataset, are not live data, and have not been reviewed by an agronomist.** Row ratios, seed rates and yield or profit figures are intentionally absent. Edit the JSON (weights, thresholds, crop traits, known systems) without code changes. `regional_overrides` is an empty list where verified Kurnool or other regional recommendations can be added with their source; matching ones appear on results.

## References to verify against (not used as a data source)
ANGRAU package of practices and KVK advisories (angrau.ac.in); ICAR / ICAR-CRIDA intercropping recommendations (icar.org.in); TNAU Agritech Portal (agritech.tnau.ac.in).

## Endpoints (all need a Bearer token)
- `GET /api/intercrop/crops`: supported crops with groups, seasons, water class and duration
- `GET /api/intercrop/meta`: seasons, soils, weights, thresholds, references, engine info
- `POST /api/intercrop/recommend`: body `primary_crop` (required), `season` (kharif|rabi|zaid, required), optional `soil_type`, `soil_ph` (3.5 to 9.5), `rainfall_mm` (0 to 5000), `temperature_c` (5 to 45), `water_availability` (low|medium|high), `irrigation` (rainfed|drip|sprinkler|canal|borewell), `region`, `limit` (1 to 12, default 6). Invalid values return 422. Response: `recommendations[]` (rank, score, rating, criteria with points and notes, patterns, benefits, limitations, known_system), `excluded[]`, `assumptions[]`, `warnings[]`, `data_completeness`, `confidence`, `disclaimer`.
