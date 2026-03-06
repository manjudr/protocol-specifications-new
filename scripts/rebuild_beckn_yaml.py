#!/usr/bin/env python3
"""
rebuild_beckn_yaml.py — Refactor api/v2.0.0/beckn.yaml so that each endpoint's
requestBody points to the canonical schema IRI at schema.beckn.io instead of
an inline {ActionName}Request schema defined inside the same file.

Before (current state):
  /beckn/discover:
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DiscoverRequest'   ← local inline

After (desired state):
  /beckn/discover:
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: 'https://schema.beckn.io/DiscoverAction/v2.0'   ← canonical IRI

The script also removes the now-redundant {ActionName}Request schemas from
components.schemas (DiscoverRequest, OnDiscoverRequest, SelectRequest, etc.)
while preserving all transport-layer schemas (Ack, Error, Signature, Context, …).

Usage:
    cd /path/to/protocol-specifications-v2
    python3 scripts/rebuild_beckn_yaml.py [--dry-run]
"""

import argparse
import os
import sys

import yaml  # pyyaml

# ---------------------------------------------------------------------------
# Path → canonical action class name mapping
# ---------------------------------------------------------------------------

NAMESPACE_BASE = "https://schema.beckn.io"
VERSION = "v2.0"

# Mapping: Beckn path segment → Action class name in schema.beckn.io
PATH_TO_ACTION: dict[str, str] = {
    "discover":    "DiscoverAction",
    "on_discover": "OnDiscoverAction",
    "select":      "SelectAction",
    "on_select":   "OnSelectAction",
    "init":        "InitAction",
    "on_init":     "OnInitAction",
    "confirm":     "ConfirmAction",
    "on_confirm":  "OnConfirmAction",
    "status":      "StatusAction",
    "on_status":   "OnStatusAction",
    "track":       "TrackAction",
    "on_track":    "OnTrackAction",
    "update":      "UpdateAction",
    "on_update":   "OnUpdateAction",
    "cancel":      "CancelAction",
    "on_cancel":   "OnCancelAction",
    "rate":        "RateAction",
    "on_rate":     "OnRateAction",
    "support":     "SupportAction",
    "on_support":  "OnSupportAction",
}

# Schemas to REMOVE from components.schemas (the old inline action wrappers)
# These are replaced by external $ref to schema.beckn.io
SCHEMAS_TO_REMOVE = {
    "DiscoverRequest",
    "OnDiscoverRequest",
    "SelectRequest",
    "OnSelectRequest",
    "InitRequest",
    "OnInitRequest",
    "ConfirmRequest",
    "OnConfirmRequest",
    "StatusRequest",
    "OnStatusRequest",
    "TrackRequest",
    "OnTrackRequest",
    "UpdateRequest",
    "OnUpdateRequest",
    "CancelRequest",
    "OnCancelRequest",
    "RateRequest",
    "OnRateRequest",
    # support endpoint uses "SupportActionRequest" in the YAML, not "SupportRequest"
    "SupportActionRequest",
    "OnSupportRequest",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def canonical_iri(action_class: str) -> str:
    return f"{NAMESPACE_BASE}/{action_class}/{VERSION}"


class _IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, indentless=False)


def _literal_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

_IndentDumper.add_representer(str, _literal_presenter)


def dump_yaml(data: dict) -> str:
    return yaml.dump(
        data,
        Dumper=_IndentDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


# ---------------------------------------------------------------------------
# Main transformation
# ---------------------------------------------------------------------------

def transform(spec: dict) -> tuple[dict, list[str]]:
    """
    Apply the refactoring to the parsed OpenAPI spec dict.
    Returns (modified_spec, list_of_log_messages).
    """
    log: list[str] = []
    paths: dict = spec.get("paths") or {}
    components: dict = spec.get("components") or {}
    schemas: dict = components.get("schemas") or {}

    # ── 1. Rewrite requestBody $refs in paths ─────────────────────────────────
    for path_key, path_item in paths.items():
        # path_key is e.g. '/beckn/discover'
        # Extract the action segment: last segment after final /
        segment = path_key.lstrip("/").split("/")[-1]  # e.g. 'discover'

        if segment not in PATH_TO_ACTION:
            log.append(f"  SKIP  path {path_key!r} (no action mapping)")
            continue

        action_class = PATH_TO_ACTION[segment]
        iri = canonical_iri(action_class)

        # All Beckn paths use POST
        post_op = path_item.get("post") or {}
        request_body = post_op.get("requestBody") or {}
        content = request_body.get("content") or {}
        json_content = content.get("application/json") or {}
        schema_entry = json_content.get("schema") or {}

        old_ref = schema_entry.get("$ref", "<none>")
        schema_entry["$ref"] = iri
        log.append(f"  ✅  {path_key}: {old_ref!r} → {iri!r}")

    # ── 2. Remove redundant action-wrapper schemas ─────────────────────────────
    removed: list[str] = []
    for name in list(schemas.keys()):
        if name in SCHEMAS_TO_REMOVE:
            del schemas[name]
            removed.append(name)

    if removed:
        log.append(f"\n  Removed {len(removed)} action-wrapper schemas from components.schemas:")
        for name in sorted(removed):
            log.append(f"    - {name}")
    else:
        log.append("\n  No action-wrapper schemas to remove (already clean?).")

    return spec, log


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Refactor api/v2.0.0/beckn.yaml so each endpoint requestBody points to\n"
            "https://schema.beckn.io/{Action}Action/v2.0 instead of an inline schema."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing the file.")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(repo_root, "api", "v2.0.0", "beckn.yaml")

    if not os.path.exists(yaml_path):
        print(f"ERROR: beckn.yaml not found at {yaml_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\nRefactoring: {yaml_path}")
    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Mode: {'dry-run' if args.dry_run else 'write'}\n")

    with open(yaml_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    if not spec or not isinstance(spec, dict):
        print("ERROR: Failed to parse beckn.yaml as a YAML dict.", file=sys.stderr)
        sys.exit(1)

    spec, log_lines = transform(spec)

    print("\n".join(log_lines))

    if args.dry_run:
        print("\n[DRY-RUN] No files written.")
        return

    # Build the header comment
    header = (
        "# AUTO-GENERATED — DO NOT EDIT DIRECTLY\n"
        "# Sources: api/v2.0.0/components/io/core.yaml  |  api/v2.0.0/components/schema/core.yaml  |  github.com/beckn/core_schema\n"
        "# Regenerate: cd protocol-specifications-v2 && python3 scripts/rebuild_beckn_yaml.py\n"
        "#\n"
    )

    content = dump_yaml(spec)

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(content)

    print(f"\n✅  Written: {yaml_path}")


if __name__ == "__main__":
    main()
