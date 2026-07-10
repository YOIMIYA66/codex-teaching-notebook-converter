#!/usr/bin/env python3
"""Statically validate a teaching notebook and its local assets."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any


MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\((?:<)?([^)>]+)(?:>)?\)")
HTML_IMAGE_PATTERN = re.compile(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"]", re.I)
REMOTE_PREFIXES = ("http://", "https://", "data:", "attachment:")


def source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_python(text: str) -> str:
    lines = [line.lstrip() for line in text.splitlines() if line.strip()]
    if any(line.startswith("%%") for line in lines):
        return "cell_magic"
    if any(line.startswith("%") for line in lines):
        return "line_magic"
    if any(line.startswith("!") for line in lines):
        return "shell"
    return "python"


def code_signatures(notebook: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for index, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") == "code":
            result.append({"index": index, "id": cell.get("id"), "source": source_text(cell)})
    return result


def validate(notebook_path: Path, source_path: Path | None, assets_dir: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    skipped: list[str] = ["notebook execution"]
    checks: dict[str, Any] = {}

    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "errors": [f"Notebook JSON could not be read: {exc}"], "warnings": [], "skipped": skipped, "checks": {}}

    cells = notebook.get("cells")
    if not isinstance(cells, list):
        errors.append("Notebook does not contain a cells array.")
        cells = []
    checks["cell_count"] = len(cells)

    ids: list[str] = []
    local_images: list[str] = []
    remote_images: list[str] = []
    syntax_checked = 0
    syntax_skipped: list[dict[str, Any]] = []

    for index, cell in enumerate(cells):
        cell_type = cell.get("cell_type")
        if cell_type not in {"code", "markdown", "raw"}:
            errors.append(f"Cell {index} has unsupported cell_type {cell_type!r}.")
        if "source" not in cell:
            errors.append(f"Cell {index} has no source field.")
        if cell.get("id"):
            ids.append(str(cell["id"]))

        text = source_text(cell)
        if cell_type == "code":
            kind = classify_python(text)
            if kind == "python":
                try:
                    ast.parse(text)
                    syntax_checked += 1
                except SyntaxError as exc:
                    errors.append(f"Python syntax error in cell {index}: {exc.msg} at line {exc.lineno}.")
            else:
                syntax_skipped.append({"cell": index, "reason": kind})

        if cell_type == "markdown":
            refs = MARKDOWN_IMAGE_PATTERN.findall(text) + HTML_IMAGE_PATTERN.findall(text)
            for ref in refs:
                clean_ref = ref.strip().split("#", 1)[0].split("?", 1)[0]
                if clean_ref.startswith(REMOTE_PREFIXES):
                    remote_images.append(ref)
                else:
                    local_images.append(clean_ref)
                    candidate = (notebook_path.parent / clean_ref).resolve()
                    if not candidate.is_file():
                        errors.append(f"Missing local image referenced by cell {index}: {clean_ref}")

    duplicates = sorted({cell_id for cell_id in ids if ids.count(cell_id) > 1})
    if duplicates:
        errors.append(f"Duplicate cell IDs: {', '.join(duplicates)}")
    if remote_images:
        warnings.append(f"Notebook contains {len(remote_images)} remote or embedded image references; review portability.")
    if syntax_skipped:
        warnings.append(f"Skipped Python AST validation for {len(syntax_skipped)} magic or shell cells.")

    checks["unique_cell_ids"] = not duplicates
    checks["python_cells_compiled"] = syntax_checked
    checks["syntax_skipped"] = syntax_skipped
    checks["local_image_references"] = local_images
    checks["remote_or_embedded_image_references"] = remote_images

    if assets_dir:
        resolved_assets = assets_dir.resolve()
        if not resolved_assets.is_dir():
            errors.append(f"Assets directory does not exist: {resolved_assets}")
        else:
            checks["asset_files"] = sorted(str(path.relative_to(resolved_assets)) for path in resolved_assets.rglob("*") if path.is_file())

    if source_path:
        try:
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source_code = code_signatures(source)
            teaching_code = code_signatures(notebook)
            code_unchanged = [item["source"] for item in source_code] == [item["source"] for item in teaching_code]
            checks["source_sha256"] = sha256(source_path)
            checks["code_cell_count_source"] = len(source_code)
            checks["code_cell_count_teaching"] = len(teaching_code)
            checks["code_cells_unchanged_and_in_order"] = code_unchanged
            if not code_unchanged:
                warnings.append("Teaching notebook code cells differ from the source; verify that every functional change is disclosed in the manifest.")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Source notebook could not be compared: {exc}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "skipped": skipped,
        "checks": checks,
        "remaining_risks": [
            "Static validation does not prove runtime correctness.",
            "Generated image text and visual quality require human or model visual inspection.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--assets-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = validate(args.notebook.resolve(), args.source.resolve() if args.source else None, args.assets_dir.resolve() if args.assets_dir else None)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
