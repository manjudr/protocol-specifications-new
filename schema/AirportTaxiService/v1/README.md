# Airport Taxi Service (v1)

Airport taxi domain extensions for Beckn v2. This pack models ground transport `Item.attributes` for airport-authorised cabs while reusing Beckn core objects for pricing, orders, and fulfillments.

## Files

- `attributes.yaml` — OpenAPI components defining `AirportTaxiService` metadata (service type, airport, queueing, fare model, safety).
- `context.jsonld` — JSON-LD context binding attribute keys to stable IRIs.
- `vocab.jsonld` — Vocabulary declarations for taxi-specific classes and properties.
- `profile.json` — Profile bundle with operational hints for indexing, PII management, and API response configuration.
- `renderer.json` — Placeholder for UI rendering guidance.

## Usage Notes

1. Attach `AirportTaxiService` attributes under `beckn:itemAttributes` for airport ground-transport listings.
2. Populate commercial terms (price, surcharges) using Beckn core `Offer`/`Order` structures; leverage `fareModel`, `tollPolicy`, and `waitAndChargePolicy` for quick summaries.
3. Surface operational metadata (queue type, wait times, pickup instructions) to help passengers plan their curbside experience.
4. Maintain PII (traveller contact, ride notes) within order-level extensions and treat them per the PII guidance in `profile.json`.

