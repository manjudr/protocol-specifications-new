#!/usr/bin/env python3
"""
Backward Compatibility Checker for Beckn Vocab Files

This script checks backward compatibility between v2 and v2.1 vocab.jsonld files:
1. Identifies IDs present in v2 but missing in v2.1
2. For matching IDs, compares field-level changes

Usage:
    python3 check_vocab_bc.py
    
    or from project root:
    python3 scripts/v2.1/vocab-bc-check/check_vocab_bc.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any


def load_vocab(file_path: Path) -> Dict[str, Any]:
    """Load and parse a vocab.jsonld file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_ids_map(vocab_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract all @id entries from the @graph array and return as a map.
    
    Returns:
        Dict mapping @id to the full object
    """
    graph = vocab_data.get('@graph', [])
    ids_map = {}
    
    for item in graph:
        item_id = item.get('@id')
        if item_id:
            ids_map[item_id] = item
    
    return ids_map


def compare_objects(v2_obj: Dict[str, Any], v21_obj: Dict[str, Any], id_name: str) -> List[str]:
    """
    Compare two objects field by field and return list of differences.
    
    Args:
        v2_obj: Object from v2 vocab
        v21_obj: Object from v2.1 vocab
        id_name: The @id of the object being compared
    
    Returns:
        List of difference descriptions
    """
    differences = []
    
    # Get all keys from both objects
    v2_keys = set(v2_obj.keys())
    v21_keys = set(v21_obj.keys())
    
    # Check for removed fields
    removed_keys = v2_keys - v21_keys
    for key in removed_keys:
        differences.append(f"  - Field '{key}' removed (was: {json.dumps(v2_obj[key])})")
    
    # Check for added fields
    added_keys = v21_keys - v2_keys
    for key in added_keys:
        differences.append(f"  + Field '{key}' added (value: {json.dumps(v21_obj[key])})")
    
    # Check for modified fields
    common_keys = v2_keys & v21_keys
    for key in common_keys:
        if key == '@id':  # Skip the ID itself
            continue
        
        v2_value = v2_obj[key]
        v21_value = v21_obj[key]
        
        # Deep comparison for nested structures
        if v2_value != v21_value:
            differences.append(f"  ~ Field '{key}' modified:")
            differences.append(f"      v2.0:  {json.dumps(v2_value, indent=8)}")
            differences.append(f"      v2.1:  {json.dumps(v21_value, indent=8)}")
    
    return differences


def main():
    """Main function to run the backward compatibility check."""
    
    # Determine script location and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
    # Define paths to vocab files
    v2_vocab_path = project_root / "schema/core/v2/vocab.jsonld"
    v21_vocab_path = project_root / "schema/core/v2.1/vocab.jsonld"
    
    # Check if files exist
    if not v2_vocab_path.exists():
        print(f"❌ Error: v2 vocab file not found at {v2_vocab_path}")
        sys.exit(1)
    
    if not v21_vocab_path.exists():
        print(f"❌ Error: v2.1 vocab file not found at {v21_vocab_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("Beckn Vocab Backward Compatibility Checker")
    print("=" * 80)
    print(f"Comparing:")
    print(f"  v2.0:  {v2_vocab_path}")
    print(f"  v2.1:  {v21_vocab_path}")
    print()
    
    # Load vocab files
    try:
        v2_vocab = load_vocab(v2_vocab_path)
        v21_vocab = load_vocab(v21_vocab_path)
    except Exception as e:
        print(f"❌ Error loading vocab files: {e}")
        sys.exit(1)
    
    # Extract ID maps
    v2_ids_map = extract_ids_map(v2_vocab)
    v21_ids_map = extract_ids_map(v21_vocab)
    
    v2_ids = set(v2_ids_map.keys())
    v21_ids = set(v21_ids_map.keys())
    
    print(f"📊 Statistics:")
    print(f"  v2.0 entries:  {len(v2_ids)}")
    print(f"  v2.1 entries:  {len(v21_ids)}")
    print()
    
    # Check for missing IDs
    missing_ids = v2_ids - v21_ids
    
    print("=" * 80)
    print("1. MISSING IDs CHECK")
    print("=" * 80)
    print(f"Checking if all {len(v2_ids)} IDs from v2.0 are present in v2.1...")
    print()
    
    if missing_ids:
        print(f"⚠️  Found {len(missing_ids)} IDs missing in v2.1:")
        print()
        for missing_id in sorted(missing_ids):
            print(f"  ❌ {missing_id}")
            # Show the type if available
            obj = v2_ids_map[missing_id]
            obj_type = obj.get('@type', 'N/A')
            label = obj.get('rdfs:label') or obj.get('schema:name', 'N/A')
            print(f"      Type: {obj_type}")
            print(f"      Label: {label}")
            print()
    else:
        print("✅ All IDs from v2.0 are present in v2.1")
        print()
    
    # Check for new IDs in v2.1
    new_ids = v21_ids - v2_ids
    if new_ids:
        print(f"ℹ️  Found {len(new_ids)} new IDs added in v2.1:")
        print()
        for new_id in sorted(new_ids):
            print(f"  ➕ {new_id}")
            obj = v21_ids_map[new_id]
            obj_type = obj.get('@type', 'N/A')
            label = obj.get('rdfs:label') or obj.get('schema:name', 'N/A')
            print(f"      Type: {obj_type}")
            print(f"      Label: {label}")
            print()
    
    # Check for field-level changes
    print("=" * 80)
    print("2. FIELD-LEVEL CHANGES CHECK")
    print("=" * 80)
    print(f"Checking field-level modifications for {len(v2_ids & v21_ids)} matching IDs...")
    print()
    
    common_ids = v2_ids & v21_ids
    modified_ids = []
    
    for id_name in sorted(common_ids):
        v2_obj = v2_ids_map[id_name]
        v21_obj = v21_ids_map[id_name]
        
        differences = compare_objects(v2_obj, v21_obj, id_name)
        
        if differences:
            modified_ids.append((id_name, differences))
    
    if modified_ids:
        print(f"⚠️  Found {len(modified_ids)} IDs with field-level modifications:")
        print()
        
        for id_name, differences in modified_ids:
            print(f"📝 {id_name}")
            for diff in differences:
                print(diff)
            print()
    else:
        print("✅ No field-level modifications found for matching IDs")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total IDs in v2.0:           {len(v2_ids)}")
    print(f"Total IDs in v2.1:           {len(v21_ids)}")
    print(f"Missing IDs in v2.1:         {len(missing_ids)}")
    print(f"New IDs in v2.1:             {len(new_ids)}")
    print(f"Modified IDs:                {len(modified_ids)}")
    print(f"Unchanged IDs:               {len(common_ids) - len(modified_ids)}")
    print()
    
    if missing_ids or modified_ids:
        print("⚠️  Backward compatibility issues detected!")
        return 1
    else:
        print("✅ No backward compatibility issues detected!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
