#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 2
LAYOUT = "para-v1"

# PARA top level only. Content production does not add a parallel taxonomy:
# one article is one directory under 01-Projects, and its 成稿包 / 调研 / 草稿 /
# 封面 / 配图 all live inside it. Per-project directories are created on demand
# by the writing flow, not here.
DIRECTORIES = (
    "00-Inbox（灵感库）",
    "01-Projects（项目）",
    "02-Areas（资产）",
    "03-Resources（资源）",
    "04-Archive（归档）",
    "05-Skills（技能）",
    "indexes",
)

# Never created and never written to: Web Clipper originals are read-only.
READ_ONLY_DIRECTORIES = ("Clippings",)

ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets" / "vault-template"
ASSET_FILES = tuple(
    sorted(path.relative_to(ASSET_ROOT) for path in ASSET_ROOT.rglob("*") if path.is_file())
)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_manifest(root):
    manifest_path = root / ".jing-obsidian.json"
    if not manifest_path.exists():
        return None, None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as error:
        return None, str(error)


def audit(root):
    manifest, manifest_error = load_manifest(root)
    missing_dirs = [item for item in DIRECTORIES if not (root / item).is_dir()]
    missing_files = [str(item) for item in ASSET_FILES if not (root / item).is_file()]
    if not root.exists():
        status = "missing"
    elif manifest_error:
        status = "invalid-manifest"
    elif missing_dirs or missing_files or manifest is None:
        status = "incomplete"
    elif manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("layout") != LAYOUT:
        status = "unsupported-manifest"
    else:
        status = "ready"
    return {
        "status": status,
        "vault": str(root),
        "manifest": manifest,
        "manifest_error": manifest_error,
        "missing_directories": missing_dirs,
        "missing_files": missing_files,
    }


def render_asset(source, vault_name):
    text = source.read_text(encoding="utf-8")
    return text.replace("{{vault_name}}", vault_name)


def write_text_safely(destination, text):
    temporary = destination.with_name(destination.name + ".jing-obsidian-tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(destination)


def initialize(root, vault_name, dry_run):
    if root.exists() and not root.is_dir():
        raise ValueError(f"vault path is not a directory: {root}")
    existing_manifest, manifest_error = load_manifest(root) if root.exists() else (None, None)
    if manifest_error:
        raise ValueError(f"existing manifest is invalid: {manifest_error}")
    if existing_manifest and (
        existing_manifest.get("schema_version") != SCHEMA_VERSION
        or existing_manifest.get("layout") != LAYOUT
    ):
        raise ValueError("existing manifest uses an unsupported schema; refusing to overwrite it")

    created_dirs = [item for item in DIRECTORIES if not (root / item).is_dir()]
    created_files = [str(item) for item in ASSET_FILES if not (root / item).exists()]
    preserved_files = [str(item) for item in ASSET_FILES if (root / item).exists()]
    manifest_action = "preserved" if existing_manifest else "created"
    result = {
        "status": "dry-run" if dry_run else "initialized",
        "vault": str(root),
        "created_directories": created_dirs,
        "created_files": created_files,
        "preserved_files": preserved_files,
        "manifest": manifest_action,
        "overwritten_files": [],
    }
    if dry_run:
        return result

    root.mkdir(parents=True, exist_ok=True)
    for item in DIRECTORIES:
        (root / item).mkdir(parents=True, exist_ok=True)
    for relative in ASSET_FILES:
        destination = root / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_text_safely(destination, render_asset(ASSET_ROOT / relative, vault_name))
    if not existing_manifest:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "layout": LAYOUT,
            "name": vault_name,
            "created_at": utc_now(),
            "managed_by": "jing-obsidian",
        }
        write_text_safely(
            root / ".jing-obsidian.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
    return result


def main():
    parser = argparse.ArgumentParser(description="Safely initialize or check a Jing-style Obsidian vault")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Check required structure without writing")
    check_parser.add_argument("--vault", required=True)

    init_parser = subparsers.add_parser("init", help="Create missing structure without overwriting files")
    init_parser.add_argument("--vault", required=True)
    init_parser.add_argument("--name", default="我的知识库")
    init_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    root = Path(args.vault).expanduser().resolve()
    try:
        if args.command == "check":
            result = audit(root)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "ready" else 1
        result = initialize(root, args.name, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "error", "vault": str(root), "error": str(error)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
