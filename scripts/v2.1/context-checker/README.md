# Context Checker

A Python script that validates if all unique keywords (class names, property names, and enumeration names) in each schema of `schema/core/v2.1/attributes.yaml` have corresponding IRI definitions in the `schema/core/v2.1/context.jsonld` file.

## Purpose

This script ensures consistency between the OpenAPI schema definitions and the JSON-LD context file by:

- Extracting all schema names (class names) from `attributes.yaml`
- Extracting all property names from each schema definition
- Extracting all enumeration values from enum fields
- Comparing them against the keys defined in `context.jsonld`
- Reporting any missing mappings

## Features

- **Comprehensive Extraction**: Recursively processes all schemas and nested properties
- **Smart Filtering**: Ignores technical keywords that don't need context mappings (e.g., OpenAPI keywords like `type`, `format`, `description`)
- **Categorized Reporting**: Separates missing items into schema names and properties/enums for easier review
- **Schema.org Awareness**: Skips `schema:` prefixed properties that reference schema.org vocabulary directly
- **Interactive Update**: Prompts user to create an `updated.context.jsonld` file with missing mappings
- **Enum Scoping**: Properly encapsulates enumeration values within their parent property's scoped context

## Prerequisites

- Python 3.6 or higher
- PyYAML library

Install PyYAML if not already installed:
```bash
pip install pyyaml
```

## Usage

### Default usage

```bash
python3 scripts/v2.1/context-checker/check_context.py
```

This will:
- Read from: `schema/core/v2.1/attributes.yaml`
- Read from: `schema/core/v2.1/context.jsonld`
- Report any missing context mappings
- Prompt to create `updated.context.jsonld` if missing mappings are found

### Make it executable (optional)

```bash
chmod +x scripts/v2.1/context-checker/check_context.py
./scripts/v2.1/context-checker/check_context.py
```

## Output

The script provides detailed output showing:

1. Number of schemas found
2. Total unique keywords extracted
3. Number of context keys found
4. A coverage report with:
   - Missing schema names (if any)
   - Missing properties/enums (if any)
5. Interactive prompt to create updated context (if missing mappings found)

### Success Example

```
Reading schemas from: /path/to/schema/core/v2.1/attributes.yaml
Found 89 schemas to check
Extracted 542 unique keywords from schemas

Reading context from: /path/to/schema/core/v2.1/context.jsonld
Found 538 keys in context.jsonld

================================================================================
CONTEXT COVERAGE REPORT
================================================================================

✅ All keywords from attributes.yaml are covered in context.jsonld!
================================================================================
```

### Failure Example with Interactive Update

```
Reading schemas from: /path/to/schema/core/v2.1/attributes.yaml
Found 65 schemas to check
Extracted 407 unique keywords from schemas

Reading context from: /path/to/schema/core/v2.1/context.jsonld
Found 289 keys in context.jsonld

================================================================================
CONTEXT COVERAGE REPORT
================================================================================

❌ Found 170 keywords missing from context.jsonld:

Missing Schema Names (14):
  - CheckoutTerminal
  - Consumer
  - FulfillmentMode
  ...

Missing Properties/Enums (156):
  - agentAttributes
  - authToken
  - checkoutAt
  ...

================================================================================

Would you like to create an 'updated.context.jsonld' file with the missing mappings?
Note: Enumeration values will be properly scoped within their parent properties.
Enter 'yes' or 'y' to create the file, anything else to skip: yes

Creating updated context file...

✅ Successfully created: /path/to/schema/core/v2.1/updated.context.jsonld

The updated context includes all 459 terms.

Next steps:
1. Review the updated.context.jsonld file
2. Adjust any IRI mappings as needed
3. Replace context.jsonld with updated.context.jsonld when ready
```

## Interactive Update Feature

When missing keywords are found, the script will prompt you to create an `updated.context.jsonld` file. This feature:

1. **Creates a copy** of the existing context with all missing terms added
2. **Maps schema names** to `beckn:SchemaName` IRIs
3. **Maps properties** to `beckn:propertyName` IRIs
4. **Scopes enumerations** properly within their parent properties

### Example Enum Scoping

For a property `acceptedPaymentMethod` with enum values like `UPI`, `CREDIT_CARD`, etc., the script creates:

```json
{
  "@context": {
    "acceptedPaymentMethod": {
      "@id": "beckn:acceptedPaymentMethod",
      "@type": "@id",
      "@context": {
        "UPI": "beckn:UPI",
        "CREDIT_CARD": "beckn:CREDIT_CARD",
        "WALLET": "beckn:WALLET"
      }
    }
  }
}
```

This ensures enum values are properly namespaced and don't pollute the global context.

### Workflow

1. Run the script: `python3 scripts/v2.1/context-checker/check_context.py`
2. Review the missing keywords report
3. When prompted, enter `yes` or `y` to create the updated context
4. Review the generated `schema/core/v2.1/updated.context.jsonld` file
5. Make any necessary adjustments to IRI mappings
6. When satisfied, replace `context.jsonld` with `updated.context.jsonld`:
   ```bash
   mv schema/core/v2.1/updated.context.jsonld schema/core/v2.1/context.jsonld
   ```
7. Re-run the script to verify all mappings are now present

## Exit Codes

- `0`: All keywords are covered (success)
- `1`: Missing keywords found or error occurred (failure)

## Integration

This script can be integrated into:

- **CI/CD Pipelines**: Add as a validation step before merging schema changes
- **Pre-commit Hooks**: Ensure context is updated when schemas change
- **Documentation Workflows**: Generate reports on schema-context alignment

## What Gets Checked

### Included
- Schema names (e.g., `Item`, `Offer`, `Order`)
- Property names (e.g., `price`, `descriptor`, `fulfillmentAttributes`)
- Enum values (e.g., `UPI`, `CREDIT_CARD`, `ACTIVE`)

### Excluded
- OpenAPI/JSON Schema keywords (`type`, `format`, `description`, etc.)
- JSON-LD keywords (`@context`, `@id`, `@type`, etc.)
- Schema.org prefixed properties (`schema:name`, `schema:price`, etc.)
- URIs and very short technical values

## Maintenance

When adding new schemas or properties to `attributes.yaml`:

1. Run this script to identify missing context mappings
2. Use the interactive update feature to generate `updated.context.jsonld`
3. Review and adjust the generated mappings
4. Replace the original context file when ready
5. Re-run the script to verify coverage

## See Also

- [Schema Design Guide](../../../docs/schema/Schema-Design-Guide.md)
- [JSON-LD Governance](../../../docs/governance/Beckn-JSONLD-Governance.md)
- [Contributing Schemas](../../../docs/governance/CONTRIBUTING_SCHEMAS.md)
