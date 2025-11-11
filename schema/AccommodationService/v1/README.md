# Accommodation Service (v1)

This pack defines Beckn v2 domain extensions for hospitality accommodations. It introduces lodging-specific `Item.attributes` (rooms, villas, serviced apartments) while reusing Beckn core types for descriptors, pricing, offers, orders, and fulfillments.

## Files

- `attributes.yaml` — OpenAPI component describing `AccommodationService` attributes attached to `Item.attributes`.
- `context.jsonld` — JSON-LD context wiring attribute keys to canonical IRIs.
- `vocab.jsonld` — Vocabulary definitions for the lodging terms introduced in this pack.
- `profile.json` — Profile bundle with operational guidance (indexing, PII handling, response config).
- `renderer.json` — Placeholder rendering hints for UI components.

## Usage Notes

1. Include `AccommodationService` attributes under `beckn:itemAttributes` for room/stay listings.
2. Reuse `core/v2` Offer and Order schemas for commercial terms, payment, and fulfillment tracking.
3. Attach booking-specific attributes (guest list, stay dates, payment guarantees) to `beckn:orderAttributes` in a separate hospitality order pack (planned).
4. For discovery, index key filters such as property type, occupancy, meal plans, amenities, and geo-location.

