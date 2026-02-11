# Vocab Backward Compatibility Checker

A Python script that checks backward compatibility between Beckn Protocol vocabulary (vocab.jsonld) files across versions.

## Overview

This tool compares the `@graph` entries in two vocab.jsonld files to ensure backward compatibility by:

1. **Missing IDs Check**: Identifies all `@id` entries present in v2.0 that are missing in v2.1
2. **Field-Level Changes Check**: For matching IDs, detects any modifications, additions, or removals of fields

## Usage

### From the script directory:

```bash
cd scripts/v2.1/vocab-bc-check
python3 check_vocab_bc.py
```

### From the project root:

```bash
python3 scripts/v2.1/vocab-bc-check/check_vocab_bc.py
```

### As an executable:

```bash
./scripts/v2.1/vocab-bc-check/check_vocab_bc.py
```

## Prerequisites

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## What It Checks

### 1. Missing IDs

The script identifies any `@id` entries that exist in `schema/core/v2/vocab.jsonld` but are missing in `schema/core/v2.1/vocab.jsonld`. For each missing ID, it displays:

- The ID name
- The `@type` of the entity
- The label (`rdfs:label` or `schema:name`)

### 2. Field-Level Modifications

For IDs that exist in both versions, the script performs a deep comparison of all fields and reports:

- **Removed fields**: Fields that existed in v2.0 but are missing in v2.1
- **Added fields**: New fields in v2.1 that didn't exist in v2.0
- **Modified fields**: Fields where the value has changed between versions

## Output Format

The script provides:

1. **Statistics**: Count of entries in each version
2. **Missing IDs**: List of IDs not present in v2.1
3. **New IDs**: List of IDs added in v2.1
4. **Modified IDs**: Detailed field-level changes for matching IDs
5. **Summary**: Overall statistics and compatibility status

### Exit Codes

- `0`: No backward compatibility issues detected
- `1`: Backward compatibility issues found (missing IDs or modified fields)

## Example Output

```
================================================================================
Beckn Vocab Backward Compatibility Checker
================================================================================
Comparing:
  v2.0:  /path/to/schema/core/v2/vocab.jsonld
  v2.1:  /path/to/schema/core/v2.1/vocab.jsonld

📊 Statistics:
  v2.0 entries:  152
  v2.1 entries:  165

================================================================================
1. MISSING IDs CHECK
================================================================================
Checking if all 152 IDs from v2.0 are present in v2.1...

✅ All IDs from v2.0 are present in v2.1

ℹ️  Found 13 new IDs added in v2.1:
  ➕ beckn:Feature
      Type: rdfs:Class
      Label: Feature

================================================================================
2. FIELD-LEVEL CHANGES CHECK
================================================================================
Checking field-level modifications for 152 matching IDs...

⚠️  Found 3 IDs with field-level modifications:

📝 beckn:Quantity
  ~ Field 'rdfs:comment' modified:
      v2.0:  "A quantitative value specifying units, codes, and quantity constraints."
      v2.1:  "A quantitative value specifying units, codes, and quantity constraints"

📝 beckn:networkId
  + Field 'rdfs:domain' added (value: ["beckn:Context", "beckn:Item"])
  ~ Field 'rdfs:comment' modified:
      v2.0:  "Network identifiers for the BAP that offers this item."
      v2.1:  "A unique identifier representing a group of platforms..."

================================================================================
SUMMARY
================================================================================
Total IDs in v2.0:           152
Total IDs in v2.1:           165
Missing IDs in v2.1:         0
New IDs in v2.1:             13
Modified IDs:                3
Unchanged IDs:               149

⚠️  Backward compatibility issues detected!
```

## Files Compared

- **Source (v2.0)**: `schema/core/v2/vocab.jsonld`
- **Target (v2.1)**: `schema/core/v2.1/vocab.jsonld`

## Use Cases

- **Pre-release validation**: Run before releasing a new version to ensure backward compatibility
- **Migration planning**: Identify changes that may require documentation or migration guides
- **Breaking change detection**: Catch unintentional modifications or removals
- **Change documentation**: Generate detailed change logs for version updates

## Integration

This script can be integrated into:

- CI/CD pipelines (returns non-zero exit code on issues)
- Pre-commit hooks
- Release verification workflows
- Documentation generation processes

## Notes

- The script performs exact field-level comparison using JSON deep equality
- Array order matters in the comparison
- Both structural and value changes are detected
- The comparison is comprehensive, checking all fields in the JSON-LD objects

## Contributing

When modifying this script:

1. Maintain Python 3.6+ compatibility
2. Keep it dependency-free (standard library only)
3. Preserve clear, readable output formatting
4. Update this README with any new features or changes
