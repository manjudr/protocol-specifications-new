# Trip Service (v1)

Trip/tour domain extensions for Beckn v2. This pack models multi-day `Item.attributes` for packaged journeys — itinerary, inclusions, transport, guides, policies — while relying on Beckn core objects for offers, orders, and fulfillments.

## Files

- `attributes.yaml` — OpenAPI components for `TripService` attributes (itinerary, inclusions, group configuration, cancellation/payment structure).
- `context.jsonld` — JSON-LD context mapping attribute keys to IRIs.
- `vocab.jsonld` — Vocabulary definitions for trip-specific classes and properties.
- `profile.json` — Profile bundle with operational hints (indexing, PII handling, response configs, discovery filters).
- `renderer.json` — Placeholder rendering hints for client UI components.

## Usage Notes

1. Attach `TripService` under `beckn:itemAttributes` for packaged tour listings. Keep pricing, availability, and fulfillment data in Beckn core Offer/Order structures.
2. Use `itinerary` to publish structured day-wise plans; clients can request detailed itinerary expansion via include flags.
3. Document inclusions/exclusions, cancellation policy, and payment schedule to help travellers compare packages transparently.
4. Maintain traveller PII (passports, rooming preferences) within order-level extensions and handle per the PII guidance in `profile.json`.

