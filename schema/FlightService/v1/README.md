# Flight Service (v1)

Flight domain extensions for Beckn v2. The pack models aviation-specific `Item.attributes` used during flight discovery and booking while reusing Beckn core schemas for pricing, orders, and fulfillments.

## Files

- `attributes.yaml` — OpenAPI components describing the `FlightService` item attributes (carrier, schedule, cabin, baggage, policies).
- `context.jsonld` — JSON-LD context binding attribute keys to IRIs.
- `vocab.jsonld` — Vocabulary definitions for flight classes and properties.
- `profile.json` — Profile metadata plus operational hints (indexing, PII guidance, API response recommendations).
- `renderer.json` — Placeholder rendering hints for flight list/detail UIs.

## Usage Notes

1. Attach `FlightService` attributes to `beckn:itemAttributes` for flight listings and catalog entries.
2. Represent fare-specific information (price, penalties, availability) via Beckn core Offer/Order objects; use `fareFamily`, `baggageAllowance`, `changePolicy`, and `refundPolicy` fields for summary metadata.
3. Expose SSR, passenger details, and ticketing metadata via dedicated order attribute packs (to be defined) while keeping discovery payloads PII-light.
4. Index key filters (origin/destination codes, departure date/time, cabin, fare family) to support performant flight search experiences.

