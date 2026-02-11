#!/usr/bin/env python3
"""
Context Checker Script for Beckn Protocol v2.1

This script checks if all unique keywords (class names, property names, and enumeration names)
in each schema of 'schema/core/v2.1/attributes.yaml' have a corresponding 
IRI in the 'schema/core/v2.1/context.jsonld' file.

Usage:
    python3 scripts/v2.1/context-checker/check_context.py
    python3 scripts/v2.1/context-checker/check_context.py --write-updated
"""

import yaml
import json
import sys
import argparse
from pathlib import Path
from typing import Set, Dict, Any, Tuple
from collections import defaultdict


# Define all JSON Schema keywords to skip
SKIP_KEYWORDS = {
    'type', 'format', 'description', 'example', 'examples', 
    'required', 'additionalProperties', 'minItems', 'maxItems',
    'minimum', 'maximum', 'minLength', 'maxLength', 'pattern',
    'items', 'allOf', 'oneOf', 'anyOf', 'if', 'then', 'else',
    'not', 'const', 'default', 'nullable', '$ref', 'x-jsonld',
    'minProperties', 'maxProperties', 'dependentRequired', 'dependentSchemas',
    'prefixItems', 'contains', 'minContains', 'maxContains',
    'uniqueItems', 'multipleOf', 'exclusiveMinimum', 'exclusiveMaximum'
}


def extract_keywords_from_schema(schema_def: Any, keywords: Set[str], enum_map: Dict[str, Set[str]], parent_key: str = None, schema_name: str = None) -> None:
    """
    Recursively extract property names and enum values from a schema definition.
    
    Args:
        schema_def: The schema definition (dict, list, or other)
        keywords: Set to collect all keywords
        enum_map: Dict mapping property names/schema names to their enum values
        parent_key: The parent property name for enum tracking
        schema_name: The schema name when processing a top-level schema
    """
    
    if isinstance(schema_def, dict):
        for key, value in schema_def.items():
            # Skip special JSON Schema keywords and JSON-LD context keywords
            if key in SKIP_KEYWORDS:
                # Recursively process the value
                extract_keywords_from_schema(value, keywords, enum_map, parent_key, schema_name)
            elif key == 'enum':
                # Collect enum values and track which property/schema they belong to
                if isinstance(value, list):
                    for enum_val in value:
                        if isinstance(enum_val, str):
                            keywords.add(enum_val)
                            # Use schema_name if at schema level, otherwise use parent_key
                            target_key = schema_name if schema_name and not parent_key else parent_key
                            if target_key:
                                enum_map[target_key].add(enum_val)
            elif key == 'properties':
                # When we encounter properties, recursively process but don't track as parent
                if isinstance(value, dict):
                    for prop_name, prop_def in value.items():
                        # Skip JSON-LD reserved keywords
                        if not prop_name.startswith('@'):
                            keywords.add(prop_name)
                        extract_keywords_from_schema(prop_def, keywords, enum_map, prop_name, None)
            else:
                # This is a property name or custom keyword
                # Skip JSON-LD reserved keywords and schema keywords
                if not key.startswith('@') and key not in SKIP_KEYWORDS:
                    keywords.add(key)
                # Recursively process the value
                extract_keywords_from_schema(value, keywords, enum_map, key if key != 'properties' else parent_key, schema_name)
    
    elif isinstance(schema_def, list):
        for item in schema_def:
            extract_keywords_from_schema(item, keywords, enum_map, parent_key, schema_name)


def extract_context_keys(context_def: Any, keys: Set[str]) -> None:
    """
    Recursively extract all keys from the @context definition.
    
    Args:
        context_def: The context definition
        keys: Set to collect all context keys
    """
    if isinstance(context_def, dict):
        for key, value in context_def.items():
            # Skip special JSON-LD keywords
            if key not in ['@id', '@type', '@context', '@version', '@protected']:
                keys.add(key)
            # Recursively process nested contexts
            if isinstance(value, dict) and '@context' in value:
                extract_context_keys(value['@context'], keys)
    elif isinstance(context_def, list):
        for item in context_def:
            extract_context_keys(item, keys)


def create_updated_context(
    context_data: Dict[str, Any],
    missing_schema_names: Set[str],
    missing_properties: Set[str],
    enum_map: Dict[str, Set[str]]
) -> Dict[str, Any]:
    """
    Create an updated context with missing keywords added.
    
    Args:
        context_data: Original context data
        missing_schema_names: Set of missing schema names
        missing_properties: Set of missing properties/enums
        enum_map: Dict mapping property names to their enum values
        
    Returns:
        Updated context data
    """
    # Deep copy the context
    updated_context = json.loads(json.dumps(context_data))
    
    # Add missing schema names
    for schema_name in sorted(missing_schema_names):
        # Check if this schema has enums (like CheckoutTerminal)
        if schema_name in enum_map and enum_map[schema_name]:
            # Schema with enums - create scoped context
            updated_context['@context'][schema_name] = {
                "@id": f"beckn:{schema_name}",
                "@type": "@id",
                "@context": {}
            }
            for enum_val in sorted(enum_map[schema_name]):
                updated_context['@context'][schema_name]["@context"][enum_val] = f"beckn:{enum_val}"
        else:
            # Regular schema without enums
            updated_context['@context'][schema_name] = f"beckn:{schema_name}"
    
    # Separate enums from regular properties
    enum_values = set()
    for enum_set in enum_map.values():
        enum_values.update(enum_set)
    
    regular_properties = missing_properties - enum_values
    missing_enums = missing_properties & enum_values
    
    # Add regular properties
    for prop in sorted(regular_properties):
        # Check if this property has associated enums
        if prop in enum_map and enum_map[prop]:
            # Property with enums - create scoped context
            updated_context['@context'][prop] = {
                "@id": f"beckn:{prop}",
                "@type": "@id",
                "@context": {}
            }
            for enum_val in sorted(enum_map[prop]):
                updated_context['@context'][prop]["@context"][enum_val] = f"beckn:{enum_val}"
        else:
            # Regular property without enums
            updated_context['@context'][prop] = f"beckn:{prop}"
    
    # Add standalone enums (those that don't have a clear parent property)
    for enum_val in sorted(missing_enums):
        # Check if this enum is already added as part of a scoped context
        already_added = False
        for prop, enums in enum_map.items():
            if enum_val in enums and prop in updated_context['@context']:
                already_added = True
                break
        
        if not already_added:
            updated_context['@context'][enum_val] = f"beckn:{enum_val}"
    
    return updated_context


def check_context_coverage(
    attributes_file: Path,
    context_file: Path,
    create_updated: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if all keywords from attributes.yaml are covered in context.jsonld.
    
    Args:
        attributes_file: Path to attributes.yaml
        context_file: Path to context.jsonld
        create_updated: Whether to create updated context data
        
    Returns:
        Tuple of (all_covered, updated_context_data)
    """
    print(f"Reading schemas from: {attributes_file}")
    
    # Load attributes.yaml
    with open(attributes_file, 'r', encoding='utf-8') as f:
        attributes_data = yaml.safe_load(f)
    
    # Extract all keywords from schemas
    all_keywords = set()
    schema_names = set()
    enum_map = defaultdict(set)
    
    if 'components' in attributes_data and 'schemas' in attributes_data['components']:
        schemas = attributes_data['components']['schemas']
        print(f"Found {len(schemas)} schemas in attributes.yaml")
        
        # Add schema names (class names)
        for schema_name in schemas.keys():
            schema_names.add(schema_name)
            all_keywords.add(schema_name)
        
        # Extract property names and enum values from each schema
        for schema_name, schema_def in schemas.items():
            extract_keywords_from_schema(schema_def, all_keywords, enum_map, None, schema_name)
    else:
        print("Error: No schemas found in attributes.yaml")
        return False, None
    
    print(f"\nExtracted {len(all_keywords)} unique keywords from attributes.yaml")
    
    # Load context.jsonld
    print(f"\nReading context from: {context_file}")
    with open(context_file, 'r', encoding='utf-8') as f:
        context_data = json.load(f)
    
    # Extract all keys from context
    context_keys = set()
    if '@context' in context_data:
        extract_context_keys(context_data['@context'], context_keys)
    else:
        print("Error: No @context found in context.jsonld")
        return False, None
    
    print(f"Found {len(context_keys)} keys in context.jsonld")
    
    # Check for missing keywords
    missing_keywords = all_keywords - context_keys
    
    # Filter out some known exceptions that don't need to be in context
    filtered_missing = set()
    for keyword in missing_keywords:
        # Skip schema.org prefixed properties
        if keyword.startswith('schema:'):
            continue
        # Skip common property values that are URIs or technical values
        if keyword.startswith('http://') or keyword.startswith('https://'):
            continue
        # Skip single letters or very short technical values
        if len(keyword) <= 1:
            continue
        filtered_missing.add(keyword)
    
    # Report results
    print("\n" + "="*80)
    print("CONTEXT COVERAGE REPORT")
    print("="*80)
    
    missing_schema_names = filtered_missing & schema_names
    missing_properties = filtered_missing - schema_names
    
    # Separate enum values from regular properties
    enum_values = set()
    for enum_set in enum_map.values():
        enum_values.update(enum_set)
    
    missing_enums = missing_properties & enum_values
    missing_regular_properties = missing_properties - enum_values
    
    if filtered_missing:
        print(f"\n❌ Found {len(filtered_missing)} keywords missing from context.jsonld:\n")
        
        if missing_schema_names:
            print(f"Missing Schema Names ({len(missing_schema_names)}):")
            for keyword in sorted(missing_schema_names):
                # Check if this schema has enums that would be scoped
                if keyword in enum_map and enum_map[keyword]:
                    print(f"  - {keyword} (with {len(enum_map[keyword])} scoped enums)")
                else:
                    print(f"  - {keyword}")
        
        if missing_regular_properties:
            print(f"\nMissing Properties ({len(missing_regular_properties)}):")
            for keyword in sorted(missing_regular_properties):
                # Check if this property has enums that would be scoped
                if keyword in enum_map and enum_map[keyword]:
                    print(f"  - {keyword} (with {len(enum_map[keyword])} scoped enums)")
                else:
                    print(f"  - {keyword}")
        
        if missing_enums:
            print(f"\nMissing Enumeration Values ({len(missing_enums)}):")
            print("  (These will be scoped within their parent properties/schemas)\n")
            
            # Group enums by their parent
            enum_to_parents = defaultdict(list)
            for parent, enums in enum_map.items():
                for enum_val in enums:
                    if enum_val in missing_enums:
                        enum_to_parents[enum_val].append(parent)
            
            for enum_val in sorted(missing_enums):
                parents = enum_to_parents.get(enum_val, [])
                if parents:
                    parent_str = ", ".join(sorted(parents))
                    print(f"  - {enum_val} -> scoped under: {parent_str}")
                else:
                    print(f"  - {enum_val} -> standalone")
        
        print("\n" + "="*80)
        
        # Create updated context if requested
        updated_context = None
        if create_updated:
            updated_context = create_updated_context(
                context_data,
                missing_schema_names,
                missing_properties,
                enum_map
            )
        
        return False, updated_context
    else:
        print("\n✅ All keywords from attributes.yaml are covered in context.jsonld!")
        print("="*80)
        
        # Still show scoping information for existing enums
        if enum_map:
            print("\nEnum Scoping Summary:")
            scoped_count = sum(1 for enums in enum_map.values() if enums)
            print(f"  Total properties/schemas with scoped enums: {scoped_count}")
        
        return True, None


def main():
    """Main function to execute the context checker."""
    parser = argparse.ArgumentParser(
        description='Check context coverage for Beckn Protocol v2.1 schemas',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Get script directory for relative path resolution
    script_dir = Path(__file__).resolve().parent.parent.parent.parent
    
    parser.add_argument(
        '--attributes',
        type=Path,
        default=script_dir / "schema/core/v2.1/attributes.yaml",
        help='Path to attributes.yaml (default: schema/core/v2.1/attributes.yaml)'
    )
    parser.add_argument(
        '--context',
        type=Path,
        default=script_dir / "schema/core/v2.1/context.jsonld",
        help='Path to context.jsonld (default: schema/core/v2.1/context.jsonld)'
    )
    parser.add_argument(
        '--write-updated',
        type=Path,
        metavar='PATH',
        help='Write updated context to specified file without prompting'
    )
    
    args = parser.parse_args()
    
    # Check if files exist
    if not args.attributes.exists():
        print(f"Error: attributes.yaml not found at {args.attributes}")
        sys.exit(1)
    
    if not args.context.exists():
        print(f"Error: context.jsonld not found at {args.context}")
        sys.exit(1)
    
    # Run the check
    try:
        all_covered, _ = check_context_coverage(
            args.attributes,
            args.context,
            create_updated=False
        )
        
        # If not all covered, ask user or write updated file
        if not all_covered:
            if args.write_updated:
                print(f"\nCreating updated context file at: {args.write_updated}")
                _, updated_context = check_context_coverage(
                    args.attributes,
                    args.context,
                    create_updated=True
                )
                
                if updated_context:
                    with open(args.write_updated, 'w', encoding='utf-8') as f:
                        json.dump(updated_context, f, indent=4, ensure_ascii=False)
                    
                    print(f"\n✅ Successfully created: {args.write_updated}")
                    print(f"\nThe updated context includes all {len(updated_context['@context'])} terms.")
                else:
                    print("\n❌ Failed to create updated context")
                    sys.exit(1)
            else:
                print("\nWould you like to create an 'updated.context.jsonld' file with the missing mappings?")
                print("Note: Enumeration values will be properly scoped within their parent properties.")
                response = input("Enter 'yes' or 'y' to create the file, anything else to skip: ").strip().lower()
                
                if response in ['yes', 'y']:
                    print("\nCreating updated context file...")
                    _, updated_context = check_context_coverage(
                        args.attributes,
                        args.context,
                        create_updated=True
                    )
                    
                    if updated_context:
                        updated_context_file = args.context.parent / "updated.context.jsonld"
                        with open(updated_context_file, 'w', encoding='utf-8') as f:
                            json.dump(updated_context, f, indent=4, ensure_ascii=False)
                        
                        print(f"\n✅ Successfully created: {updated_context_file}")
                        print(f"\nThe updated context includes all {len(updated_context['@context'])} terms.")
                        print("\nNext steps:")
                        print("1. Review the updated.context.jsonld file")
                        print("2. Adjust any IRI mappings as needed")
                        print("3. Replace context.jsonld with updated.context.jsonld when ready")
                    else:
                        print("\n❌ Failed to create updated context")
                        sys.exit(1)
        
        sys.exit(0 if all_covered else 1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
