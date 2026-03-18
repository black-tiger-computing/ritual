#!/usr/bin/env python3
"""
ritual_quick_patch.py — Automated patching tool for RITUAL installations.

Applies hybrid provider patches to ritual installations.
Supports both ZIP archives and directory-based targets.

Usage:
    python ritual_quick_patch.py [target]

    target: Path to a ZIP archive or directory (defaults to current directory)
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

PATCH_FILES_DIR = Path(__file__).parent / "patch_files"

BANNER = """
╔════════════════════════════════════════╗
║           ⊙ RITUAL ⊙                  ║
║    Quick Patch — Hybrid Provider       ║
╚════════════════════════════════════════╝
"""


def _find_patch_files() -> list[Path]:
    """Return all patch files from the patch_files/ directory."""
    if not PATCH_FILES_DIR.exists():
        return []
    return sorted(PATCH_FILES_DIR.rglob("*"))


def _apply_to_directory(target_dir: Path) -> int:
    """Apply patch files to a directory target. Returns number of files patched."""
    patch_files = _find_patch_files()
    if not patch_files:
        print("⚠  No patch files found in patch_files/ — nothing to apply.")
        return 0

    count = 0
    for patch_file in patch_files:
        if not patch_file.is_file():
            continue
        rel = patch_file.relative_to(PATCH_FILES_DIR)
        dest = target_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(patch_file, dest)
        print(f"  ✓ Patched: {rel}")
        count += 1
    return count


def _apply_to_zip(target_zip: Path) -> int:
    """Apply patch files to a ZIP archive. Returns number of files patched."""
    patch_files = _find_patch_files()
    if not patch_files:
        print("⚠  No patch files found in patch_files/ — nothing to apply.")
        return 0

    if not target_zip.exists():
        print(f"✗  ZIP archive not found: {target_zip}")
        sys.exit(1)

    count = 0
    with zipfile.ZipFile(target_zip, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        existing = set(zf.namelist())
        for patch_file in patch_files:
            if not patch_file.is_file():
                continue
            rel = patch_file.relative_to(PATCH_FILES_DIR)
            arc_name = rel.as_posix()
            if arc_name in existing:
                print(f"  ~ Replacing: {arc_name}")
            else:
                print(f"  ✓ Adding:    {arc_name}")
            zf.write(patch_file, arc_name)
            count += 1
    return count


def patch(target: str | None = None) -> None:
    """
    Apply hybrid provider patches to a ritual installation.

    Args:
        target: Path to a ZIP archive or directory. Defaults to the current
                working directory.
    """
    print(BANNER)

    target_path = Path(target) if target else Path.cwd()

    if not target_path.exists():
        print(f"✗  Target not found: {target_path}")
        sys.exit(1)

    if target_path.is_file() and target_path.suffix.lower() == ".zip":
        print(f"📦 Patching ZIP archive: {target_path}")
        count = _apply_to_zip(target_path)
    elif target_path.is_dir():
        print(f"📁 Patching directory: {target_path}")
        count = _apply_to_directory(target_path)
    else:
        print(f"✗  Target must be a directory or a .zip file: {target_path}")
        sys.exit(1)

    if count:
        print(f"\n✨ Patch complete — {count} file(s) applied.")
    else:
        print("\nNo changes were made.")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply hybrid provider patches to a RITUAL installation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Path to a ZIP archive or directory (default: current directory)",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    args = _build_arg_parser().parse_args()
    patch(args.target)


if __name__ == "__main__":
    main()
