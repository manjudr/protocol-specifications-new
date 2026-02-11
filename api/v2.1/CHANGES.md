# Beckn Protocol API v2.1.0 — Change Log (from v2.0.0)

This document explains **what changed** between `api/v2/beckn.yaml` (v2.0.0) and `api/v2.1/beckn.yaml` (v2.1.0), **why** it changed, and how it impacts implementations. The v2.1 spec intentionally keeps the protocol surface thin, moves core schemas to canonical JSON-LD definitions, and formalizes catalog discovery and async flows.

---

## Summary of Major Themes

- **Async-first discovery**: `discover` is now ACK-only; search results are delivered via `on_discover` callbacks.
- **Catalog publishing service formalized**: new `/catalog/publish` + `/catalog/on_publish` action naming standard.
- **Message envelope and schema normalization**: most inline schemas moved to shared core schema refs (`schema/core/v2.1/attributes.yaml`).
- **Try/confirm branching**: updates, cancel, support, rate flows use `context.try` with `oneOf` envelopes.
- **Protocol surface simplification**: removal of non-core endpoints (e.g., browser-search), reduced example noise.

---

## 1) Spec Metadata & Governance

### ✅ Title and Version
- **v2.0.0**: “Beckn Protocol API”
- **v2.1.0**: “Beckn Protocol V2.1 API Specification”

**Why**: Makes the spec version explicit and avoids confusion when multiple protocol versions coexist.

### ✅ License Correction
- **v2.0.0**: MIT (incorrect)
- **v2.1.0**: CC-BY-NC-SA 4.0 (correct, per Beckn governance)

**Why**: v2 was published with a mismatched license. This corrects legal/usage terms.

### ✅ Servers Removed
- v2.0.0 contained staging/local server entries.
- v2.1.0 removes `servers` entirely.

**Why**: Protocol spec should not imply a canonical deployment environment. It is network-agnostic.

---

## 2) Discovery API Changes

### ✅ `/beckn/discover`
- **v2.0.0**: could return ACK **or** synchronous catalog results
- **v2.1.0**: **ACK-only** (results are always async via `on_discover`)

**Why**: Discovery is async by design, especially with catalog indexing and cross-network fan-out.

### ✅ `/beckn/on_discover`
- v2.1 continues to return ACK-only.
- Schema simplified: uses `OnDiscoverMessage` with `catalogs` array.

### ❌ Removed: `/beckn/discover/browser-search`
- Browser-friendly discovery endpoint removed entirely.

**Why**: Out-of-scope for protocol layer; belongs in a reference implementation or UI service.

### ✅ Schema Refactor
- v2.0.0 used `DiscoverRequest` and `DiscoverResponse` inline schemas.
- v2.1.0 uses **`DiscoveryIntent`** (core schema) and `OnDiscoverMessage`.

**Why**: Aligns with shared JSON-LD core schemas and reduces duplicate definitions.

---

## 3) Catalog Publishing Service

### ✅ Endpoint Names Standardized
- **v2.0.0**: `/beckn/catalog/publish` + `/beckn/catalog/on_publish` but action values used `catalog_publish` / `on_catalog_publish`
- **v2.1.0**: action values standardized to **`catalog/publish`** and **`catalog/on_publish`**

**Why**: Action names now mirror path naming. This reduces ambiguity and improves clarity in logs.

### ✅ Results Schema Normalization
- v2.0.0 used `CatalogProcessingResult` with `catalog_id`, `status`, `warnings`, `error`.
- v2.1.0 now defines `CatalogProcessingResult` locally with:
  - `catalogId`
  - `status: accepted | rejected | processing`
  - `errors[]` and `stats` (item/provider/category counts)

**Why**: Harmonizes result model with other v2.1 core conventions and supports incremental processing stats.

---

## 4) Transaction API Envelope Changes

### ✅ Context Handling
- v2.0.0 relied on `TransactionContext` and `DiscoveryContext` wrappers.
- v2.1.0 uses core **`Context`** directly via JSON-LD refs.

**Why**: v2.1 pushes canonical context definition into shared schema and removes duplication.

### ✅ `context.try` Branching (NEW)
The following endpoints now use `oneOf` with `context.try` to separate **draft/negotiation** vs **final/commit** calls:

- `/beckn/update` + `/beckn/on_update`
- `/beckn/cancel` + `/beckn/on_cancel`
- `/beckn/rate` + `/beckn/on_rate`
- `/beckn/support` + `/beckn/on_support`

**Why**: Enables protocol-level negotiation without ambiguous payloads. This separates “draft” intent from “final” commitment in the same endpoint.

---

## 5) Endpoint Renames & Behavior Changes

### ✅ Rating API Renamed & Split
- **v2.0.0**: `/beckn/rating` and `/beckn/on_rating`
- **v2.1.0**: `/beckn/rate` and `/beckn/on_rate`

**Why**: Aligns with Beckn action naming conventions and enables `try` branching.

### ✅ Support API Restructured
- **v2.0.0**: `support` request used `refId` + `refType`.
- **v2.1.0**: `support` payload is normalized under `SupportInfo` with `order` references.

**Why**: Uses canonical `SupportInfo` schema and supports multi-entity support requests.

### ✅ Track API Simplification
- **v2.0.0**: custom tracking handle schema (`id`, `callbackUrl`, `mode_hint`)
- **v2.1.0**: uses shared `TrackAction` with `orderId`, `refId` constraints

**Why**: Moves tracking semantics into core schema and ensures consistent identifiers across domains.

---

## 6) Schema Normalization & External References

v2.1 moves most message-level schema definitions to:

```
https://raw.githubusercontent.com/beckn/protocol-specifications-v2/refs/heads/draft/schema/core/v2.1/attributes.yaml
```

Examples include:
- `Order`, `Catalog`, `TrackAction`, `SupportInfo`, `Rating`, `Feedback`, etc.

**Why**: v2.1 enforces a **single canonical schema source** for all implementations and avoids drift across APIs.

---

## 7) Examples and Response Payloads

### ✅ Example Sources
- v2.0.0 embedded many inline examples in the OpenAPI file.
- v2.1.0 references external YAML examples in `examples/v2.1/`.

**Why**: Keeps spec lighter and avoids bloated OpenAPI docs while ensuring examples stay authoritative.

---

## 8) Validation Fixes Applied in v2.1 (Recent)

During review, these **OpenAPI correctness issues were fixed** in v2.1:

- ✅ **`RateConfirmMessage`** lacked `type: object` and proper structure — now corrected.
- ✅ **`CatalogProcessingResult`** schema was referenced but missing — now defined.
- ✅ **`OnTrackMessage`** duplicate `tracking` key removed (already fixed).

---

## 9) Backward Compatibility Notes

### Potential Breaking Changes
- Removal of `/discover/browser-search` endpoint.
- `rating` → `rate` action rename.
- Async-only discovery (synchronous responses removed).
- Action name changes for catalog publish (`catalog_publish` → `catalog/publish`).

### Migration Guidance
- BAPs should **always expect ACK-only** from discovery and wait for `on_discover`.
- Update action names in `context.action` and routing logic.
- Ensure support/rate/update/cancel clients implement `context.try` branching.

---

## 10) Files and References

- **v2.0.0 source**: `api/v2/beckn.yaml`
- **v2.1.0 source**: `api/v2.1/beckn.yaml`
- **Core schema**: `schema/core/v2.1/attributes.yaml`
- **Examples**: `examples/v2.1/*.yaml`

---

If you want this changelog to include other APIs (e.g., schema/core or domain schemas), let me know and I can extend it.
