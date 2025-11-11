# Accessories Service (v1)

Accessories domain extensions for Beckn v2. This pack models accessory-specific `Item.attributes` such as compatibility, materials, warranty, and usage scenarios, while Beckn core objects carry pricing, offers, and order/fulfillment data.

## Files

- `attributes.yaml` — OpenAPI components defining `AccessoriesService` attributes (compatibility, features, physical specs, warranty).
- `context.jsonld` — JSON-LD context mapping attribute keys to IRIs.
- `vocab.jsonld` — Vocabulary definitions for accessory classes and properties.
- `profile.json` — Profile bundle with operational hints (indexing, PII, response configs, discovery defaults).
- `renderer.json` — Placeholder rendering hints for accessory discovery/detail UIs.

## Usage Notes

1. Attach `AccessoriesService` under `beckn:itemAttributes` for accessory products in retail catalogs.
2. Use compatibility, key features, and warranty metadata to help shoppers assess suitability; keep detailed commercial terms in Beckn core Offer/Order schemas.
3. Leverage `certifications`, `sustainabilityNotes`, and `careInstructions` to communicate compliance and post-purchase expectations.
4. Index accessory type, brand, materials, and compatibility fields to enable robust filtering and cross-sell recommendations.

