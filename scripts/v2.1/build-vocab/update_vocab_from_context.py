#!/usr/bin/env python3
"""
Vocabulary Builder for Beckn Protocol v2.1

This script ensures all beckn: IRIs referenced in context.jsonld exist in vocab.jsonld.
For missing IRIs, it adds entries with inferred metadata from attributes.yaml.

This is a purely structural transformation with strict, deterministic rules.

Usage:
    python3 update_vocab_from_context.py
    python3 update_vocab_from_context.py --dry-run
    python3 update_vocab_from_context.py --out custom.vocab.jsonld
"""

import json
import yaml
import sys
import argparse
from pathlib import Path
from typing import Dict, Set, List, Any, Optional, Tuple
from collections import defaultdict


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_beckn_iris_from_context(context_def: Any, iris: Set[str], scoped_enums: Dict[str, Set[str]], parent_key: str = None) -> None:
    """
    Recursively extract all beckn: IRIs from @context.
    
    Args:
        context_def: The context definition or fragment
        iris: Set to collect IRIs
        scoped_enums: Dict mapping parent IRI to set of enum member IRIs
        parent_key: Parent key for tracking enum scoping
    """
    if isinstance(context_def, str):
        if context_def.startswith('beckn:'):
            iris.add(context_def)
    elif isinstance(context_def, dict):
        # Check for @id
        if '@id' in context_def:
            iri = context_def['@id']
            if isinstance(iri, str) and iri.startswith('beckn:'):
                iris.add(iri)
                parent_key = iri  # This becomes the parent for nested context
        
        # Check for nested @context (enum scoping)
        if '@context' in context_def and isinstance(context_def['@context'], dict):
            parent_iri = context_def.get('@id', parent_key)
            for key, value in context_def['@context'].items():
                if key not in ['@id', '@type', '@version', '@protected', '@container']:
                    # This is likely an enum member mapping
                    if isinstance(value, str) and value.startswith('beckn:'):
                        iris.add(value)
                        if parent_iri and parent_iri.startswith('beckn:'):
                            scoped_enums[parent_iri].add(value)
                    elif isinstance(value, dict):
                        extract_beckn_iris_from_context(value, iris, scoped_enums, parent_iri)
        
        # Recursively process all other keys
        for key, value in context_def.items():
            if key not in ['@id', '@type', '@context', '@version', '@protected']:
                extract_beckn_iris_from_context(value, iris, scoped_enums, parent_key)
    
    elif isinstance(context_def, list):
        for item in context_def:
            extract_beckn_iris_from_context(item, iris, scoped_enums, parent_key)


def extract_vocab_iris(vocab_data: Dict[str, Any]) -> Set[str]:
    """Extract all @id values from vocab @graph."""
    iris = set()
    for item in vocab_data.get('@graph', []):
        if '@id' in item:
            iris.add(item['@id'])
    return iris


def humanize_iri_local(local_name: str) -> str:
    """Convert camelCase or PascalCase IRI local name to human-readable label."""
    # Insert spaces before capitals (except at start)
    import re
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', local_name)
    # Handle sequences of capitals
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', result)
    return result


class AttributesAnalyzer:
    """Analyzes attributes.yaml to infer vocabulary metadata."""
    
    def __init__(self, attributes_path: Path):
        self.data = load_yaml(attributes_path)
        self.schemas = self.data.get('components', {}).get('schemas', {})
        
        # Build property index
        self.property_domains: Dict[str, Set[str]] = defaultdict(set)
        self.property_schemas: Dict[str, List[Any]] = defaultdict(list)
        self.property_descriptions: Dict[str, str] = {}
        self.schema_descriptions: Dict[str, str] = {}
        
        self._index_schemas()
    
    def _index_schemas(self):
        """Index all schemas and properties."""
        for schema_name, schema_def in self.schemas.items():
            # Store schema descriptions
            if 'description' in schema_def:
                self.schema_descriptions[schema_name] = schema_def['description']
            
            # Index properties
            if 'properties' in schema_def and isinstance(schema_def['properties'], dict):
                for prop_name, prop_def in schema_def['properties'].items():
                    self.property_domains[prop_name].add(schema_name)
                    self.property_schemas[prop_name].append(prop_def)
                    
                    if 'description' in prop_def and prop_name not in self.property_descriptions:
                        self.property_descriptions[prop_name] = prop_def['description']
    
    def is_schema(self, local_name: str) -> bool:
        """Check if local name is a schema."""
        return local_name in self.schemas
    
    def is_enum_schema(self, local_name: str) -> bool:
        """Check if schema is enum-like."""
        if local_name not in self.schemas:
            return False
        
        schema_def = self.schemas[local_name]
        
        # Check for direct enum
        if 'enum' in schema_def:
            return True
        
        # Check for array with enum items
        if schema_def.get('type') == 'array' and 'items' in schema_def:
            if 'enum' in schema_def['items']:
                return True
        
        return False
    
    def is_property(self, local_name: str) -> bool:
        """Check if local name appears as a property."""
        return local_name in self.property_domains
    
    def get_schema_description(self, local_name: str) -> Optional[str]:
        """Get schema description."""
        return self.schema_descriptions.get(local_name)
    
    def get_property_description(self, local_name: str) -> Optional[str]:
        """Get property description."""
        return self.property_descriptions.get(local_name)
    
    def get_property_domains(self, local_name: str) -> Set[str]:
        """Get domains (schema names) where property appears."""
        return self.property_domains.get(local_name, set())
    
    def infer_range(self, local_name: str) -> List[str]:
        """Infer range for a property based on its schema definitions."""
        ranges = set()
        
        for prop_def in self.property_schemas.get(local_name, []):
            range_val = self._infer_range_from_schema(prop_def)
            if range_val:
                ranges.update(range_val)
        
        return sorted(ranges)
    
    def _infer_range_from_schema(self, schema_def: Any) -> List[str]:
        """Infer range from a schema definition."""
        if not isinstance(schema_def, dict):
            return []
        
        ranges = []
        
        # Handle $ref
        if '$ref' in schema_def:
            ref = schema_def['$ref']
            if ref.startswith('#/components/schemas/'):
                schema_name = ref.split('/')[-1]
                ranges.append(f'beckn:{schema_name}')
        
        # Handle allOf (merge all ranges)
        elif 'allOf' in schema_def:
            for sub_schema in schema_def['allOf']:
                ranges.extend(self._infer_range_from_schema(sub_schema))
        
        # Handle oneOf/anyOf (include all possible ranges)
        elif 'oneOf' in schema_def or 'anyOf' in schema_def:
            options = schema_def.get('oneOf', schema_def.get('anyOf', []))
            for sub_schema in options:
                ranges.extend(self._infer_range_from_schema(sub_schema))
        
        # Handle primitive types
        elif 'type' in schema_def:
            type_val = schema_def['type']
            format_val = schema_def.get('format')
            
            if type_val == 'string':
                if format_val == 'uri':
                    ranges.append('schema:URL')
                elif format_val == 'email':
                    ranges.append('schema:Text')
                elif format_val == 'date-time':
                    ranges.append('schema:DateTime')
                elif format_val == 'date':
                    ranges.append('schema:Date')
                elif format_val == 'time':
                    ranges.append('schema:Time')
                else:
                    ranges.append('schema:Text')
            elif type_val == 'number':
                ranges.append('schema:Number')
            elif type_val == 'integer':
                ranges.append('schema:Integer')
            elif type_val == 'boolean':
                ranges.append('schema:Boolean')
            elif type_val == 'object':
                ranges.append('schema:Thing')
            elif type_val == 'array':
                # Get item range
                if 'items' in schema_def:
                    item_ranges = self._infer_range_from_schema(schema_def['items'])
                    ranges.extend(item_ranges)
        
        return ranges


def create_vocab_entry(
    iri: str,
    analyzer: AttributesAnalyzer,
    scoped_enums: Dict[str, Set[str]],
    all_iris: Set[str]
) -> Dict[str, Any]:
    """
    Create a vocabulary entry for a missing IRI.
    
    Args:
        iri: The IRI (e.g., 'beckn:foo')
        analyzer: Attributes analyzer
        scoped_enums: Map of parent IRI to enum member IRIs
        all_iris: All IRIs in context (to check if parent enum exists)
    
    Returns:
        Vocabulary entry dict
    """
    local_name = iri.split(':', 1)[1] if ':' in iri else iri
    
    entry = {
        '@id': iri,
        'rdfs:label': humanize_iri_local(local_name)
    }
    
    # Determine @type
    entry_type = None
    comment = None
    
    # Check if it's a schema (class or enum)
    if analyzer.is_schema(local_name):
        if analyzer.is_enum_schema(local_name):
            entry_type = 'schema:Enumeration'
        else:
            entry_type = 'rdfs:Class'
        comment = analyzer.get_schema_description(local_name)
    
    # Check if it's a property
    elif analyzer.is_property(local_name):
        entry_type = 'rdf:Property'
        comment = analyzer.get_property_description(local_name)
        
        # Add domain
        domains = analyzer.get_property_domains(local_name)
        if domains:
            entry['rdfs:domain'] = sorted([f'beckn:{d}' for d in domains])
        
        # Add range
        ranges = analyzer.infer_range(local_name)
        if ranges:
            entry['schema:rangeIncludes'] = ranges if len(ranges) > 1 else ranges[0]
    
    # Check if it's an enum member (scoped under a parent)
    else:
        # Find if this IRI is scoped under any parent
        parent_iris = [parent for parent, members in scoped_enums.items() if iri in members]
        
        if parent_iris:
            # It's an enum member
            parent_iri = parent_iris[0]  # Use first parent
            parent_local = parent_iri.split(':', 1)[1] if ':' in parent_iri else parent_iri
            
            # Check if parent is an enum schema in attributes.yaml
            if analyzer.is_enum_schema(parent_local):
                # Parent is a proper enum schema, use it in @type
                entry_type = [parent_iri, 'schema:Enumeration']
                comment = analyzer.get_schema_description(parent_local)
            elif analyzer.is_property(parent_local):
                # Parent is a property with enum values
                entry_type = 'schema:Enumeration'
                comment = analyzer.get_property_description(parent_local)
            else:
                # Parent is not in attributes.yaml, just mark as enumeration
                entry_type = 'schema:Enumeration'
        else:
            # Couldn't determine type, default to Thing
            entry_type = 'schema:Thing'
    
    if entry_type:
        entry['@type'] = entry_type
    
    # Add comment
    if comment:
        entry['rdfs:comment'] = comment
    else:
        entry['rdfs:comment'] = 'TODO: Add Description of Property'
    
    return entry


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Build vocabulary from context for Beckn Protocol v2.1',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    script_dir = Path(__file__).resolve().parent.parent.parent.parent
    
    parser.add_argument(
        '--context',
        type=Path,
        default=script_dir / 'schema/core/v2.1/context.jsonld',
        help='Path to context.jsonld'
    )
    parser.add_argument(
        '--attributes',
        type=Path,
        default=script_dir / 'schema/core/v2.1/attributes.yaml',
        help='Path to attributes.yaml'
    )
    parser.add_argument(
        '--vocab',
        type=Path,
        default=script_dir / 'schema/core/v2.1/vocab.jsonld',
        help='Path to vocab.jsonld (input)'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=script_dir / 'schema/core/v2.1/updated.vocab.jsonld',
        help='Path to output vocab file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print missing IRIs without writing output'
    )
    
    args = parser.parse_args()
    
    # Check files exist
    for path in [args.context, args.attributes, args.vocab]:
        if not path.exists():
            print(f"❌ Error: File not found: {path}")
            sys.exit(1)
    
    print("=" * 80)
    print("Beckn Protocol v2.1 - Vocabulary Builder")
    print("=" * 80)
    print(f"Context:    {args.context}")
    print(f"Attributes: {args.attributes}")
    print(f"Vocab:      {args.vocab}")
    print(f"Output:     {args.out}")
    print()
    
    # Load files
    print("Loading files...")
    context_data = load_json(args.context)
    vocab_data = load_json(args.vocab)
    analyzer = AttributesAnalyzer(args.attributes)
    
    # Extract IRIs from context
    print("Extracting beckn: IRIs from context.jsonld...")
    context_iris = set()
    scoped_enums = defaultdict(set)
    
    if '@context' in context_data:
        extract_beckn_iris_from_context(context_data['@context'], context_iris, scoped_enums)
    
    print(f"  Found {len(context_iris)} beckn: IRIs in context")
    
    # Extract existing IRIs from vocab
    print("Extracting existing IRIs from vocab.jsonld...")
    vocab_iris = extract_vocab_iris(vocab_data)
    print(f"  Found {len(vocab_iris)} IRIs in vocabulary")
    
    # Find missing IRIs
    missing_iris = context_iris - vocab_iris
    
    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print(f"Total context IRIs:     {len(context_iris)}")
    print(f"Existing vocab IRIs:    {len(vocab_iris)}")
    print(f"Missing IRIs:           {len(missing_iris)}")
    print()
    
    if not missing_iris:
        print("✅ All context IRIs exist in vocabulary!")
        return 0
    
    print(f"⚠️  Found {len(missing_iris)} missing IRIs:")
    print()
    
    # Create entries for missing IRIs
    new_entries = []
    for iri in sorted(missing_iris):
        entry = create_vocab_entry(iri, analyzer, scoped_enums, context_iris)
        new_entries.append(entry)
        
        # Print in dry-run mode
        if args.dry_run:
            print(f"  {iri}")
            print(f"    @type: {entry.get('@type')}")
            print(f"    rdfs:label: {entry.get('rdfs:label')}")
            print(f"    rdfs:comment: {entry.get('rdfs:comment', '(none)')[:60]}...")
            if 'rdfs:domain' in entry:
                print(f"    rdfs:domain: {entry['rdfs:domain']}")
            if 'schema:rangeIncludes' in entry:
                print(f"    schema:rangeIncludes: {entry['schema:rangeIncludes']}")
            print()
    
    if args.dry_run:
        print("=" * 80)
        print("DRY RUN - No files written")
        print("=" * 80)
        return 0
    
    # Write updated vocabulary
    print("=" * 80)
    print("WRITING UPDATED VOCABULARY")
    print("=" * 80)
    
    # Create updated vocab by appending to existing @graph
    updated_vocab = json.loads(json.dumps(vocab_data))  # Deep copy
    updated_vocab['@graph'].extend(new_entries)
    
    # Write to output file
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(updated_vocab, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully wrote updated vocabulary to: {args.out}")
    print()
    print(f"Added {len(new_entries)} new entries to vocabulary")
    print(f"Total entries in updated vocabulary: {len(updated_vocab['@graph'])}")
    print()
    print("Next steps:")
    print("  1. Review the updated vocabulary file")
    print("  2. Manually copy to vocab.jsonld when satisfied")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
