#!/usr/bin/env python3
"""Validate a teaching notebook and its delivery artifacts without executing it."""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


MARKDOWN_IMAGE_PATTERN = re.compile(
    r"!\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<bare>[^\s)]+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
HTML_IMAGE_PATTERN = re.compile(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"]", re.I)
VALID_MODES = {"quick": (0, 2), "standard": (3, 5), "full": (6, 9)}
VALID_RENDERING_METHODS = {"imagegen", "html_cards", "markdown_table", "markdown"}
FINAL_IMAGE_STATUSES = {"accepted", "repaired"}
INSPECTION_FIELDS = {"text_accuracy", "numeric_accuracy", "readability", "information_density"}


def source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook_language(notebook: dict[str, Any]) -> str:
    metadata = notebook.get("metadata", {})
    language = metadata.get("language_info", {}).get("name")
    if not language:
        language = metadata.get("kernelspec", {}).get("language")
    if not language:
        kernel_name = str(metadata.get("kernelspec", {}).get("name", ""))
        language = "python" if kernel_name.lower().startswith("python") else kernel_name
    return str(language or "python").lower()


def classify_python(text: str) -> str:
    lines = [line.lstrip() for line in text.splitlines() if line.strip()]
    if any(line.startswith("%%") for line in lines):
        return "cell_magic"
    if any(line.startswith("%") for line in lines):
        return "line_magic"
    if any(line.startswith("!") for line in lines):
        return "shell"
    return "python"


def image_references(text: str) -> list[str]:
    refs = []
    for match in MARKDOWN_IMAGE_PATTERN.finditer(text):
        refs.append(match.group("angle") or match.group("bare"))
    refs.extend(HTML_IMAGE_PATTERN.findall(text))
    return [html.unescape(ref.strip()) for ref in refs]


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} could not be read: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a top-level JSON object.")
        return None
    return value


def disclosure_ids(entries: Any, errors: list[str], field: str) -> set[str]:
    if not isinstance(entries, list):
        errors.append(f"Manifest field {field} must be an array.")
        return set()
    result = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"Manifest {field}[{index}] must be an object with cell_id and reason.")
            continue
        cell_id = entry.get("cell_id") or entry.get("id")
        reason = entry.get("reason")
        if not cell_id or not isinstance(reason, str) or not reason.strip():
            errors.append(f"Manifest {field}[{index}] requires non-empty cell_id and reason.")
            continue
        result.add(str(cell_id))
    return result


def validate_manifest(
    manifest: dict[str, Any], source_path: Path, notebook_path: Path, errors: list[str], warnings: list[str]
) -> dict[str, Any]:
    required = {
        "source_notebook",
        "output_notebook",
        "source_sha256",
        "mode",
        "mode_reason",
        "planned_images",
        "content_plan",
        "generated_assets",
        "inserted_cell_ids",
        "modified_code_cells",
        "modified_source_cells",
        "execution_logic_modified",
    }
    missing = sorted(required - manifest.keys())
    if missing:
        errors.append(f"Manifest is missing required fields: {', '.join(missing)}")

    if manifest.get("source_sha256") != sha256(source_path):
        errors.append("Manifest source_sha256 does not match the source notebook.")

    mode = manifest.get("mode")
    planned_images = manifest.get("planned_images")
    if not isinstance(manifest.get("mode_reason"), str) or not manifest.get("mode_reason", "").strip():
        errors.append("Manifest mode_reason must be a non-empty string.")
    if not isinstance(manifest.get("execution_logic_modified"), bool):
        errors.append("Manifest execution_logic_modified must be a boolean.")
    if mode not in VALID_MODES:
        errors.append(f"Manifest mode must be one of: {', '.join(sorted(VALID_MODES))}.")
    elif not isinstance(planned_images, int):
        errors.append("Manifest planned_images must be an integer.")
    else:
        minimum, maximum = VALID_MODES[mode]
        if not minimum <= planned_images <= maximum:
            warnings.append(f"Manifest mode {mode} normally uses {minimum}-{maximum} imagegen visuals, found {planned_images}.")

    content_plan = manifest.get("content_plan", [])
    plan_methods: dict[str, str] = {}
    if not isinstance(content_plan, list):
        errors.append("Manifest content_plan must be an array.")
    else:
        for index, item in enumerate(content_plan):
            if not isinstance(item, dict):
                errors.append(f"Manifest content_plan[{index}] must be an object.")
                continue
            item_id = item.get("id")
            method = item.get("rendering_method")
            reason = item.get("reason")
            purpose = item.get("purpose")
            insertion_point = item.get("insertion_point")
            if (
                not item_id
                or method not in VALID_RENDERING_METHODS
                or not isinstance(reason, str)
                or not reason.strip()
                or not isinstance(purpose, str)
                or not purpose.strip()
                or not isinstance(insertion_point, str)
                or not insertion_point.strip()
            ):
                errors.append(
                    f"Manifest content_plan[{index}] requires id, purpose, insertion_point, a valid rendering_method, and a non-empty reason."
                )
                continue
            if str(item_id) in plan_methods:
                errors.append(f"Duplicate manifest content-plan id: {item_id}")
            plan_methods[str(item_id)] = str(method)

    inserted_ids = manifest.get("inserted_cell_ids", [])
    if not isinstance(inserted_ids, list) or not all(isinstance(value, str) for value in inserted_ids):
        errors.append("Manifest inserted_cell_ids must be an array of strings.")
        inserted_ids = []

    generated_assets = manifest.get("generated_assets", [])
    if not isinstance(generated_assets, list) or not all(isinstance(value, str) for value in generated_assets):
        errors.append("Manifest generated_assets must be an array of project-relative path strings.")
        generated_assets = []

    imagegen_plan_count = sum(method == "imagegen" for method in plan_methods.values())
    if isinstance(planned_images, int) and imagegen_plan_count != planned_images:
        errors.append(
            f"Manifest content_plan contains {imagegen_plan_count} imagegen items but planned_images is {planned_images}."
        )

    code_disclosures = disclosure_ids(manifest.get("modified_code_cells", []), errors, "modified_code_cells")
    source_disclosures = disclosure_ids(manifest.get("modified_source_cells", []), errors, "modified_source_cells")

    for field, expected in (("source_notebook", source_path.name), ("output_notebook", notebook_path.name)):
        value = manifest.get(field)
        if value and Path(str(value)).name != expected:
            warnings.append(f"Manifest {field} names {value!r}, expected filename {expected!r}.")

    return {
        "plan_methods": plan_methods,
        "inserted_ids": set(inserted_ids),
        "code_disclosures": code_disclosures,
        "source_disclosures": source_disclosures,
        "generated_assets": set(generated_assets),
    }


def compare_source(
    source: dict[str, Any],
    teaching: dict[str, Any],
    manifest: dict[str, Any] | None,
    manifest_state: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    source_cells = source.get("cells", [])
    teaching_cells = teaching.get("cells", [])
    source_ids = [str(cell["id"]) for cell in source_cells if cell.get("id")]
    duplicate_source_ids = sorted({cell_id for cell_id in source_ids if source_ids.count(cell_id) > 1})
    if duplicate_source_ids:
        errors.append(f"Source notebook has duplicate cell IDs: {', '.join(duplicate_source_ids)}")
    source_by_id = {str(cell["id"]): cell for cell in source_cells if cell.get("id")}
    teaching_by_id = {str(cell["id"]): cell for cell in teaching_cells if cell.get("id")}
    code_changes: set[str] = set()
    source_changes: set[str] = set()
    missing_ids: set[str] = set()

    if len(source_by_id) != len(source_cells):
        warnings.append("Some source cells have no ID; structural comparison falls back to code-source order for those cells.")

    for cell_id, source_cell in source_by_id.items():
        teaching_cell = teaching_by_id.get(cell_id)
        if teaching_cell is None:
            missing_ids.add(cell_id)
            source_changes.add(cell_id)
            continue
        changed_fields = []
        for field in ("cell_type", "source", "metadata", "outputs", "attachments"):
            if field in source_cell or field in teaching_cell:
                source_value = source_text(source_cell) if field == "source" else source_cell.get(field)
                teaching_value = source_text(teaching_cell) if field == "source" else teaching_cell.get(field)
                if source_value != teaching_value:
                    changed_fields.append(field)
        if changed_fields:
            source_changes.add(cell_id)
        if source_cell.get("cell_type") == "code" and "source" in changed_fields:
            code_changes.add(cell_id)

    source_code = [source_text(cell) for cell in source_cells if cell.get("cell_type") == "code"]
    teaching_code = [source_text(cell) for cell in teaching_cells if cell.get("cell_type") == "code"]
    unidentified_source_code = any(
        cell.get("cell_type") == "code" and not cell.get("id") for cell in source_cells
    )
    checks = {
        "source_cell_ids_missing": sorted(missing_ids),
        "source_cell_ids_changed": sorted(source_changes),
        "code_cell_ids_changed": sorted(code_changes),
        "code_cell_count_source": len(source_code),
        "code_cell_count_teaching": len(teaching_code),
        "code_cells_unchanged_and_in_order": source_code == teaching_code,
    }

    if source_changes and manifest is None:
        errors.append("Source notebook cells changed but no manifest was supplied to disclose the changes.")
        return checks

    disclosed_code = manifest_state.get("code_disclosures", set())
    disclosed_source = manifest_state.get("source_disclosures", set())
    undisclosed_code = code_changes - disclosed_code
    undisclosed_source = (source_changes - code_changes) - disclosed_source
    if undisclosed_code:
        errors.append(f"Undisclosed code-cell changes: {', '.join(sorted(undisclosed_code))}")
    if undisclosed_source:
        errors.append(f"Undisclosed source-cell changes: {', '.join(sorted(undisclosed_source))}")
    if unidentified_source_code and source_code != teaching_code and "code-sequence" not in disclosed_code:
        errors.append(
            "Code sequence changed in a source notebook with ID-less code cells; disclose cell_id 'code-sequence' in modified_code_cells."
        )
    if missing_ids:
        errors.append(f"Source cells are missing from the teaching notebook: {', '.join(sorted(missing_ids))}")

    execution_modified = bool(manifest and manifest.get("execution_logic_modified"))
    if (code_changes or (unidentified_source_code and source_code != teaching_code)) and not execution_modified:
        errors.append("Code cells changed but manifest execution_logic_modified is false.")
    if code_changes:
        warnings.append("Teaching notebook contains disclosed code changes; review their reasons before delivery.")

    source_order = [str(cell["id"]) for cell in source_cells if cell.get("id")]
    teaching_source_order = [str(cell["id"]) for cell in teaching_cells if str(cell.get("id", "")) in source_by_id]
    if source_order != teaching_source_order:
        errors.append("Original source-cell order changed in the teaching notebook.")

    inserted_code_ids = {
        str(cell.get("id"))
        for cell in teaching_cells
        if cell.get("cell_type") == "code" and str(cell.get("id", "")) not in source_by_id
    }
    undisclosed_insertions = inserted_code_ids - manifest_state.get("inserted_ids", set())
    if undisclosed_insertions:
        errors.append(f"Undisclosed inserted code cells: {', '.join(sorted(undisclosed_insertions))}")
    return checks


def validate_prompt_pack(
    prompt_pack: dict[str, Any],
    manifest: dict[str, Any],
    manifest_state: dict[str, Any],
    notebook_path: Path,
    assets_dir: Path,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    if prompt_pack.get("version") != 1:
        errors.append("Prompt pack version must be 1.")
    if prompt_pack.get("mode") != manifest.get("mode"):
        errors.append("Prompt pack mode does not match manifest mode.")
    images = prompt_pack.get("images")
    if not isinstance(images, list):
        errors.append("Prompt pack images must be an array.")
        return {"image_count": 0, "accepted_assets": []}

    planned_images = manifest.get("planned_images")
    if isinstance(planned_images, int) and len(images) != planned_images:
        errors.append(f"Prompt pack contains {len(images)} images but manifest planned_images is {planned_images}.")

    plan_methods = manifest_state.get("plan_methods", {})
    image_ids: set[str] = set()
    accepted_assets = []
    output_files: set[str] = set()
    resolved_assets = assets_dir.resolve()

    for index, item in enumerate(images):
        if not isinstance(item, dict):
            errors.append(f"Prompt pack images[{index}] must be an object.")
            continue
        image_id = str(item.get("id", ""))
        if not image_id:
            errors.append(f"Prompt pack images[{index}] has no id.")
            continue
        if image_id in image_ids:
            errors.append(f"Duplicate prompt-pack image id: {image_id}")
        image_ids.add(image_id)
        if plan_methods.get(image_id) != "imagegen":
            errors.append(f"Prompt-pack image {image_id} is not routed to imagegen in the manifest content plan.")

        required_fields = {
            "title",
            "purpose",
            "information_goal",
            "density",
            "required_text",
            "source_locked_facts",
            "prompt",
            "negative_constraints",
            "output_file",
            "insertion_point",
            "status",
            "accepted_asset_sha256",
            "inspection",
            "repairs",
        }
        missing = sorted(field for field in required_fields if field not in item)
        if missing:
            errors.append(f"Prompt-pack image {image_id} is missing fields: {', '.join(missing)}")
            continue
        if item.get("status") not in FINAL_IMAGE_STATUSES:
            errors.append(f"Prompt-pack image {image_id} is not in an accepted final status.")

        for field in ("title", "purpose", "information_goal", "prompt", "output_file", "insertion_point"):
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"Prompt-pack image {image_id} field {field} must be a non-empty string.")
        for field in ("required_text", "source_locked_facts", "negative_constraints", "repairs"):
            if not isinstance(item.get(field), list):
                errors.append(f"Prompt-pack image {image_id} field {field} must be an array.")

        density = item.get("density")
        if not isinstance(density, dict) or density.get("target") != "moderately_high":
            errors.append(f"Prompt-pack image {image_id} must declare density.target as moderately_high.")
        else:
            regions = density.get("information_regions")
            text_items = density.get("text_items")
            if not isinstance(regions, int) or not 4 <= regions <= 7:
                warnings.append(f"Image {image_id} density uses {regions!r} information regions; body guidance is 4-7.")
            if not isinstance(text_items, int) or not 12 <= text_items <= 24:
                warnings.append(f"Image {image_id} density uses {text_items!r} text items; body guidance is 12-24.")

        inspection = item.get("inspection")
        if not isinstance(inspection, dict) or any(inspection.get(field) != "passed" for field in INSPECTION_FIELDS):
            errors.append(f"Prompt-pack image {image_id} has incomplete acceptance inspection.")

        output_file = str(item.get("output_file", ""))
        output_files.add(output_file)
        asset = (notebook_path.parent / unquote(output_file)).resolve()
        try:
            asset.relative_to(resolved_assets)
        except ValueError:
            errors.append(f"Prompt-pack image {image_id} output is outside the teaching assets directory: {output_file}")
            continue
        if not asset.is_file():
            errors.append(f"Accepted prompt-pack image {image_id} does not exist: {output_file}")
            continue
        expected_hash = item.get("accepted_asset_sha256")
        actual_hash = sha256(asset)
        if expected_hash != actual_hash:
            errors.append(f"Accepted prompt-pack image {image_id} SHA-256 does not match its file.")
        accepted_assets.append(str(asset.relative_to(resolved_assets)))

    planned_image_ids = {item_id for item_id, method in plan_methods.items() if method == "imagegen"}
    if planned_image_ids != image_ids:
        missing = sorted(planned_image_ids - image_ids)
        extra = sorted(image_ids - planned_image_ids)
        if missing:
            errors.append(f"Imagegen content-plan items missing from prompt pack: {', '.join(missing)}")
        if extra:
            errors.append(f"Prompt-pack images missing from content plan: {', '.join(extra)}")
    generated_assets = manifest_state.get("generated_assets", set())
    if generated_assets != output_files:
        missing = sorted(output_files - generated_assets)
        extra = sorted(generated_assets - output_files)
        if missing:
            errors.append(f"Prompt-pack outputs missing from manifest generated_assets: {', '.join(missing)}")
        if extra:
            errors.append(f"Manifest generated_assets missing from prompt pack: {', '.join(extra)}")
    return {"image_count": len(images), "accepted_assets": sorted(accepted_assets)}


def validate(
    notebook_path: Path,
    source_path: Path | None,
    assets_dir: Path | None,
    manifest_path: Path | None = None,
    prompt_pack_path: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    skipped: list[str] = ["notebook execution"]
    checks: dict[str, Any] = {}

    notebook = load_json(notebook_path, "Notebook JSON", errors)
    if notebook is None:
        return {"ok": False, "errors": errors, "warnings": warnings, "skipped": skipped, "checks": checks}

    cells = notebook.get("cells")
    if not isinstance(cells, list):
        errors.append("Notebook does not contain a cells array.")
        cells = []
    checks["cell_count"] = len(cells)
    language = notebook_language(notebook)
    checks["notebook_language"] = language

    ids: list[str] = []
    local_images: list[str] = []
    remote_images: list[str] = []
    embedded_images: list[str] = []
    attachment_images: list[str] = []
    syntax_checked = 0
    syntax_skipped: list[dict[str, Any]] = []

    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"Cell {index} is not an object.")
            continue
        cell_type = cell.get("cell_type")
        if cell_type not in {"code", "markdown", "raw"}:
            errors.append(f"Cell {index} has unsupported cell_type {cell_type!r}.")
        if "source" not in cell:
            errors.append(f"Cell {index} has no source field.")
        if cell.get("id"):
            ids.append(str(cell["id"]))

        text = source_text(cell)
        if cell_type == "code":
            if not language.startswith("python"):
                syntax_skipped.append({"cell": index, "reason": f"non_python:{language}"})
            else:
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
            attachments = cell.get("attachments", {})
            for ref in image_references(text):
                if ref.startswith("attachment:"):
                    name = unquote(ref.removeprefix("attachment:"))
                    attachment_images.append(name)
                    if not isinstance(attachments, dict) or name not in attachments:
                        errors.append(f"Missing notebook attachment referenced by cell {index}: {name}")
                    continue
                if ref.startswith("data:"):
                    embedded_images.append(ref[:64])
                    continue
                parsed = urlsplit(ref)
                if parsed.scheme.lower() in {"http", "https"}:
                    remote_images.append(ref)
                    continue
                if parsed.scheme and not (len(parsed.scheme) == 1 and len(ref) > 2 and ref[1] == ":"):
                    warnings.append(f"Cell {index} uses an unvalidated image URI scheme: {parsed.scheme}")
                    continue
                if len(parsed.scheme) == 1 and len(ref) > 2 and ref[1] == ":":
                    clean_ref = unquote(ref.split("#", 1)[0].split("?", 1)[0])
                else:
                    clean_ref = unquote(parsed.path if parsed.scheme else ref.split("#", 1)[0].split("?", 1)[0])
                local_images.append(clean_ref)
                candidate = (notebook_path.parent / clean_ref).resolve()
                if not candidate.is_file():
                    errors.append(f"Missing local image referenced by cell {index}: {clean_ref}")

    duplicates = sorted({cell_id for cell_id in ids if ids.count(cell_id) > 1})
    if duplicates:
        errors.append(f"Duplicate cell IDs: {', '.join(duplicates)}")
    if remote_images:
        warnings.append(f"Notebook contains {len(remote_images)} remote image references; review portability.")
    if syntax_skipped:
        warnings.append(f"Skipped Python AST validation for {len(syntax_skipped)} magic, shell, or non-Python cells.")

    checks.update(
        {
            "unique_cell_ids": not duplicates,
            "python_cells_compiled": syntax_checked,
            "syntax_skipped": syntax_skipped,
            "local_image_references": local_images,
            "attachment_image_references": attachment_images,
            "embedded_image_references": len(embedded_images),
            "remote_image_references": remote_images,
        }
    )

    resolved_assets = assets_dir.resolve() if assets_dir else None
    if resolved_assets:
        if not resolved_assets.is_dir():
            errors.append(f"Assets directory does not exist: {resolved_assets}")
        else:
            checks["asset_files"] = sorted(
                str(path.relative_to(resolved_assets)) for path in resolved_assets.rglob("*") if path.is_file()
            )

    source = load_json(source_path, "Source notebook", errors) if source_path else None
    manifest = load_json(manifest_path, "Teaching manifest", errors) if manifest_path else None
    prompt_pack = load_json(prompt_pack_path, "Imagegen prompt pack", errors) if prompt_pack_path else None
    manifest_state: dict[str, Any] = {}

    if source_path and manifest:
        manifest_state = validate_manifest(manifest, source_path, notebook_path, errors, warnings)
    elif source_path and not manifest_path:
        errors.append("Teaching manifest is required when validating against a source notebook.")

    if source:
        checks["source_sha256"] = sha256(source_path)
        checks["source_comparison"] = compare_source(
            source, notebook, manifest, manifest_state, errors, warnings
        )

    if manifest and resolved_assets:
        if prompt_pack:
            checks["prompt_pack"] = validate_prompt_pack(
                prompt_pack, manifest, manifest_state, notebook_path, resolved_assets, errors, warnings
            )
        elif manifest.get("planned_images", 0):
            errors.append("Imagegen prompt pack is required when manifest planned_images is greater than zero.")
    elif prompt_pack:
        errors.append("Prompt pack validation requires both manifest and assets directory.")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "skipped": skipped,
        "checks": checks,
        "remaining_risks": [
            "Static validation does not prove runtime correctness.",
            "Inspection records assert visual acceptance but do not perform OCR or visual analysis.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prompt-pack", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = validate(
        args.notebook.resolve(),
        args.source.resolve(),
        args.assets_dir.resolve(),
        args.manifest.resolve(),
        args.prompt_pack.resolve(),
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
