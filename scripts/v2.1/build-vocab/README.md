# Build Vocabulary Script

This directory contains the vocabulary builder script for Beckn Protocol v2.1. The script ensures that all `beckn:` IRIs referenced in `context.jsonld` exist as properly defined terms in `vocab.jsonld`.

## Purpose

The `update_vocab_from_context.py` script performs a **purely structural transformation** that:

1. Extracts all `beckn:` IRIs from `schema/core/v2.1/context.jsonld`
2. Checks which IRIs are missing from `schema/core/v2.1/vocab.jsonld`
3. Creates vocabulary entries for missing IRIs with metadata inferred from `schema/core/v2.1/attributes.yaml`
4. Writes the updated vocabulary to `schema/core/v2.1/updated.vocab.jsonld`

This is **not** a semantic reasoner or validator. It uses strict, deterministic rules to transform structural references into vocabulary definitions.

## Features

- **Strict inference rules**: Only adds IRIs that exist in context; no guessing
- **Type inference**: Determines `@type` as `rdfs:Class`, `rdf:Property`, or `schema:Enumeration` based on usage in `attributes.yaml`
- **Description extraction**: Pulls `rdfs:comment` from property/schema descriptions in `attributes.yaml`
- **Domain/range inference**: Computes `rdfs:domain` and `schema:rangeIncludes` from property usage patterns
- **Enum scoping**: Properly handles scoped enum member IRIs with parent typing
- **Safe output**: Never overwrites existing vocab; writes to `updated.vocab.jsonld`

## Prerequisites

- Python 3.6 or higher
- PyYAML library

Install PyYAML if not already installed:
```bash
pip install pyyaml
```

## Usage

### Basic usage (default paths)

```bash
cd /home/ravi/www/protocol-specifications-v2
python3 scripts/v2.1/build-vocab/update_vocab_from_context.py
```

This will:
- Read from: `schema/core/v2.1/context.jsonld`, `attributes.yaml`, `vocab.jsonld`
- Write to: `schema/core/v2.1/updated.vocab.jsonld`

### Dry run (preview without writing)

```bash
python3 scripts/v2.1/build-vocab/update_vocab_from_context.py --dry-run
```

Prints all missing IRIs with their inferred metadata without creating any files.

### Custom output path

```bash
python3 scripts/v2.1/build-vocab/update_vocab_from_context.py --out /path/to/output.jsonld
```

### Custom input files

```bash
python3 scripts/v2.1/build-vocab/update_vocab_from_context.py \
  --context path/to/context.jsonld \
  --attributes path/to/attributes.yaml \
  --vocab path/to/vocab.jsonld \
  --out path/to/output.jsonld
```

## How It Works

### 1. IRI Extraction from Context

The script recursively walks the `@context` object in `context.jsonld` to find all IRIs starting with `beckn:`:

- Direct mappings: `"foo": "beckn:foo"`
- Object mappings: `{"@id": "beckn:foo", ...}`
- Scoped contexts (enum members): `{"@context": {"ACK": "beckn:ACK"}}`

### 2. Type Inference

For each missing IRI `beckn:Something`, the script determines `@type` using these rules:

#### `rdfs:Class`
When `Something` matches a schema name in `components.schemas` of `attributes.yaml` **and** is not enum-like.

#### `schema:Enumeration`
When `Something` matches a schema name that has:
- Direct `enum` field, or
- `type: array` with `items.enum`, or
- Is a top-level enum definition

#### `rdf:Property`
When `Something` matches a property name found in any schema's `properties` section in `attributes.yaml`.

#### Enum Members
When the IRI appears as a scoped value in context (e.g., `"CREATED": "beckn:orderCreated"` under `orderStatus`):
- If parent is an enum schema in `attributes.yaml`: `@type: ["beckn:ParentEnum", "schema:Enumeration"]`
- If parent is a property with enums: `@type: "schema:Enumeration"`
- Otherwise: `@type: "schema:Enumeration"`

### 3. Comment Inference

- **Classes/Enums**: Uses schema `description` from `attributes.yaml`
- **Properties**: Uses property `description` from `attributes.yaml`
- **Enum members**: Uses parent property/schema description
- **Fallback**: `"TODO: Add Description of Property"`

### 4. Domain Inference

For properties, `rdfs:domain` is set to all schema names where the property appears:

```json
"rdfs:domain": ["beckn:Order", "beckn:Invoice"]
```

### 5. Range Inference

For properties, `schema:rangeIncludes` is inferred from the property schema:

- `$ref` to another schema → `beckn:ReferencedSchema`
- `type: string` → `schema:Text` (with format-specific variants: `schema:URL`, `schema:DateTime`, etc.)
- `type: number` → `schema:Number`
- `type: integer` → `schema:Integer`
- `type: boolean` → `schema:Boolean`
- `type: object` → `schema:Thing`
- `type: array` → range of item type

## Output Format

The script creates `updated.vocab.jsonld` by:

1. Deep-copying the existing `vocab.jsonld`
2. Appending new entries to the `@graph` array (sorted by `@id`)
3. **Not reordering** existing entries (keeps diffs reviewable)

Example new entry:

```json
{
  "@id": "beckn:orderStatus",
  "@type": "rdf:Property",
  "rdfs:label": "Order status",
  "rdfs:comment": "Order status/state.",
  "rdfs:domain": ["beckn:Order"],
  "schema:rangeIncludes": "beckn:OrderStatus"
}
```

## Important Notes

### Case Sensitivity
The script treats `beckn:OrderCreated` and `beckn:orderCreated` as **independent IRIs**. It does not attempt to normalize or reconcile case differences. A separate governance script will handle case normalization later.

### No Schema.org Equivalence
The script does **not** add `owl:equivalentProperty`, `owl:equivalentClass`, or other semantic alignment fields. These will be added by a separate mapping script.

### Non-Destructive
The original `vocab.jsonld` is **never modified**. All output goes to `updated.vocab.jsonld`.

### Deterministic
Running the script multiple times with the same inputs produces identical output (sorted, stable).

## Workflow

1. **Run the script**:
   ```bash
   python3 scripts/v2.1/build-vocab/update_vocab_from_context.py
   ```

2. **Review the output**:
   ```bash
   less schema/core/v2.1/updated.vocab.jsonld
   # or open in VS Code
   code schema/core/v2.1/updated.vocab.jsonld
   ```

3. **Check the diff**:
   ```bash
   diff -u schema/core/v2.1/vocab.jsonld schema/core/v2.1/updated.vocab.jsonld
   ```

4. **Manually copy when satisfied**:
   ```bash
   cp schema/core/v2.1/updated.vocab.jsonld schema/core/v2.1/vocab.jsonld
   ```

## Example Output

```
================================================================================
Beckn Protocol v2.1 - Vocabulary Builder
================================================================================
Context:    /home/ravi/www/protocol-specifications-v2/schema/core/v2.1/context.jsonld
Attributes: /home/ravi/www/protocol-specifications-v2/schema/core/v2.1/attributes.yaml
Vocab:      /home/ravi/www/protocol-specifications-v2/schema/core/v2.1/vocab.jsonld
Output:     /home/ravi/www/protocol-specifications-v2/schema/core/v2.1/updated.vocab.jsonld

Loading files...
Extracting beckn: IRIs from context.jsonld...
  Found 287 beckn: IRIs in context
Extracting existing IRIs from vocab.jsonld...
  Found 245 IRIs in vocabulary

================================================================================
ANALYSIS
================================================================================
Total context IRIs:     287
Existing vocab IRIs:    245
Missing IRIs:           42

⚠️  Found 42 missing IRIs:

================================================================================
WRITING UPDATED VOCABULARY
================================================================================
✅ Successfully wrote updated vocabulary to: schema/core/v2.1/updated.vocab.jsonld

Added 42 new entries to vocabulary
Total entries in updated vocabulary: 287

Next steps:
  1. Review the updated vocabulary file
  2. Manually copy to vocab.jsonld when satisfied
================================================================================
```

## Troubleshooting

### "File not found" error
Ensure you're running the script from the project root or specify full paths with `--context`, `--attributes`, `--vocab` flags.

### Missing descriptions
If you see many `"TODO: Add Description of Property"` entries, the properties may not have `description` fields in `attributes.yaml`. Add descriptions there first.

### Incorrect types
If IRIs are getting wrong types, verify the structure in `attributes.yaml`:
- Classes should be top-level schemas
- Properties should appear under `properties` sections
- Enums should have explicit `enum` fields

## Related Scripts

- `scripts/v2.1/context-checker/` - Checks context coverage
- `scripts/v2.1/vocab-bc-check/` - Checks backward compatibility
- Future: Governance script for case normalization
- Future: Schema.org equivalence mapper

---

For questions or issues, see [scripts/v2.1/README.md](../README.md).
