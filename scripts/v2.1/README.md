# Scripts for v2-rc2

This directory contains utility scripts for managing the Beckn Protocol v2-rc2 specifications.

## sort-schemas.py

A Python script to reorganize schemas in `attributes.yaml` files in alphabetical order, including all properties within each schema.

### Features

- **Alphabetically sorts schemas**: All schemas in the `components/schemas` section are sorted alphabetically by name
- **Sorts properties within schemas**: All properties within each schema definition are also sorted alphabetically
- **Preserves structure**: Maintains the OpenAPI 3.1.1 structure and metadata
- **Recursive sorting**: Sorts nested objects throughout the entire schema structure
- **Configurable input/output**: Supports custom input and output file paths

### Prerequisites

- Python 3.6 or higher
- PyYAML library

Install PyYAML if not already installed:
```bash
pip install pyyaml
```

### Usage

#### Default usage (processes schema/core/v2-rc2/attributes.yaml)

```bash
python3 scripts/v2-rc2/sort-schemas.py
```

This will:
- Read from: `schema/core/v2-rc2/attributes.yaml`
- Write to: `schema/core/v2-rc2/attributes.sorted.yaml`

#### Custom input file

```bash
python3 scripts/v2-rc2/sort-schemas.py path/to/input.yaml
```

Outputs to: `schema/core/v2-rc2/attributes.sorted.yaml` (default)

#### Custom input and output files

```bash
python3 scripts/v2-rc2/sort-schemas.py path/to/input.yaml path/to/output.yaml
```

### Example

```bash
# Sort the default attributes.yaml file
cd /home/ravi/www/protocol-specifications-v2
python3 scripts/v2-rc2/sort-schemas.py

# Sort a specific file with custom output
python3 scripts/v2-rc2/sort-schemas.py \
  schema/PaymentSettlement/v2-rc2/attributes.yaml \
  schema/PaymentSettlement/v2-rc2/attributes.sorted.yaml
```

### Output

The script will display progress information:

```
Reading from: /home/ravi/www/protocol-specifications-v2/schema/core/v2-rc2/attributes.yaml
Found 31 schemas to sort
Writing sorted schemas to: /home/ravi/www/protocol-specifications-v2/schema/core/v2-rc2/attributes.sorted.yaml
✓ Schemas sorted successfully!
  - Input:  /home/ravi/www/protocol-specifications-v2/schema/core/v2-rc2/attributes.yaml
  - Output: /home/ravi/www/protocol-specifications-v2/schema/core/v2-rc2/attributes.sorted.yaml
```

### What Gets Sorted

1. **Schema names**: All schemas under `components/schemas` are sorted alphabetically
2. **Schema properties**: All keys within each schema definition (type, required, properties, etc.)
3. **Nested objects**: All nested objects are recursively sorted
4. **Property keys**: All property keys within the `properties` section of each schema

### What Is Preserved

- OpenAPI metadata (openapi, info, etc.)
- Required fields and validation rules
- JSON-LD context and type information
- Examples and descriptions
- All schema relationships and $ref references

### Example Before and After

**Before** (schemas in declaration order):
```yaml
components:
  schemas:
    Catalog:
      # ...
    Item:
      # ...
    Offer:
      # ...
    Attributes:
      # ...
```

**After** (schemas in alphabetical order):
```yaml
components:
  schemas:
    AcceptedPaymentMethod:
      # ...
    AckResponse:
      # ...
    Address:
      # ...
    Attributes:
      # ...
    Buyer:
      # ...
    Catalog:
      # ...
```

## build-vocab/

Contains the vocabulary builder script that ensures all `beckn:` IRIs referenced in `context.jsonld` exist in `vocab.jsonld`. See [build-vocab/README.md](build-vocab/README.md) for detailed documentation.

### Quick Start

```bash
# Generate updated vocabulary with missing IRIs
python3 scripts/v2.1/build-vocab/update_vocab_from_context.py

# Preview what would be added (dry run)
python3 scripts/v2.1/build-vocab/update_vocab_from_context.py --dry-run
```

### What It Does

1. Extracts all `beckn:` IRIs from `schema/core/v2.1/context.jsonld`
2. Identifies which IRIs are missing from `schema/core/v2.1/vocab.jsonld`
3. Infers vocabulary metadata from `schema/core/v2.1/attributes.yaml`:
   - `@type` (rdfs:Class, rdf:Property, or schema:Enumeration)
   - `rdfs:label` (humanized name)
   - `rdfs:comment` (from schema/property descriptions)
   - `rdfs:domain` (where properties appear)
   - `schema:rangeIncludes` (property value types)
4. Writes updated vocabulary to `schema/core/v2.1/updated.vocab.jsonld`

### Key Features

- **Purely structural transformation**: Uses strict, deterministic rules
- **Case-sensitive**: Treats `beckn:OrderCreated` and `beckn:orderCreated` as independent
- **Non-destructive**: Never overwrites original vocab.jsonld
- **Enum scoping**: Properly handles scoped enum members with parent typing
- **Safe defaults**: Uses placeholders when metadata cannot be inferred

## context-checker/

Contains the context coverage checker that validates all schema keywords from `attributes.yaml` have corresponding IRIs in `context.jsonld`. See [context-checker/README.md](context-checker/README.md) for details.

## vocab-bc-check/

Contains backward compatibility checker for vocabulary files between v2 and v2.1. See [vocab-bc-check/check_vocab_bc.py](vocab-bc-check/check_vocab_bc.py) for details.

## network-scaffold/

Contains scripts for network provisioning and scaffolding. See [network-scaffold/README.md](network-scaffold/README.md) for details.

---

## Contributing

When adding new scripts to this directory:

1. Add appropriate documentation in this README
2. Include usage examples
3. Add error handling and validation
4. Make scripts executable: `chmod +x script-name.sh` or `chmod +x script-name.py`
5. Include a shebang line at the top of the file
