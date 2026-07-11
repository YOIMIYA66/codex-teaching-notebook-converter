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
PROFILE_INSPECTION_FIELDS = {
    "profile_fidelity",
    "evidence_fidelity",
    "series_consistency",
    "prose_replacement",
}
SEMANTIC_COLOR_FIELDS = {
    "structure",
    "active_data",
    "success_normal",
    "failure_defect",
    "warning_limitation",
    "secondary_class",
}
SOURCE_TYPES = {
    "official_documentation",
    "official_repository",
    "release_notes",
    "official_tutorial",
    "community_blog",
    "third_party_blog",
    "research_paper",
}


def source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_official_paddle_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    path_parts = [part.lower() for part in parsed.path.split("/") if part]
    if host == "paddlepaddle.org.cn" or host.endswith(".paddlepaddle.org.cn"):
        return True
    if host == "aistudio.baidu.com" or host.endswith(".aistudio.baidu.com"):
        return True
    if host == "pfcc.blog" or host.endswith(".pfcc.blog"):
        return True
    if host in {"github.com", "raw.githubusercontent.com"} and path_parts and path_parts[0] == "paddlepaddle":
        return True
    return host == "paddlepaddle.github.io" or host.endswith(".paddlepaddle.github.io")


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
    manifest: dict[str, Any],
    source_path: Path,
    notebook_path: Path,
    research_path: Path,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    required = {
        "source_notebook",
        "output_notebook",
        "source_sha256",
        "mode",
        "mode_reason",
        "planned_images",
        "research_artifact",
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
    research_artifact = manifest.get("research_artifact")
    if isinstance(research_artifact, str) and research_artifact:
        declared_research = (notebook_path.parent / research_artifact).resolve()
        if declared_research != research_path.resolve():
            errors.append("Manifest research_artifact does not point to the supplied research sources file.")

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


def validate_research_sources(
    research: dict[str, Any], errors: list[str], warnings: list[str]
) -> dict[str, Any]:
    if research.get("version") != 1:
        errors.append("Technology research version must be 1.")
    if not isinstance(research.get("researched_at"), str) or not research.get("researched_at", "").strip():
        errors.append("Technology research researched_at must be a non-empty string.")
    web_search_used = research.get("web_search_used")
    if not isinstance(web_search_used, bool):
        errors.append("Technology research web_search_used must be a boolean.")
    elif not web_search_used:
        warnings.append("Technology research did not use web search; current version and compatibility claims need review.")
    search_queries = research.get("search_queries")
    if not isinstance(search_queries, list) or not all(isinstance(query, str) and query.strip() for query in search_queries):
        errors.append("Technology research search_queries must be an array of non-empty strings.")
    elif web_search_used and not search_queries:
        errors.append("Technology research used web search but recorded no search queries.")

    technologies = research.get("technologies")
    if not isinstance(technologies, list) or not technologies:
        errors.append("Technology research technologies must be a non-empty array.")
        return {
            "technology_ids": set(),
            "source_ids": set(),
            "paddle_technology_ids": set(),
            "technology_source_urls": {},
        }

    technology_ids: set[str] = set()
    source_ids: set[str] = set()
    paddle_technology_ids: set[str] = set()
    technology_source_urls: dict[str, set[str]] = {}
    for index, technology in enumerate(technologies):
        if not isinstance(technology, dict):
            errors.append(f"Technology research technologies[{index}] must be an object.")
            continue
        tech_id = str(technology.get("id", ""))
        if not tech_id:
            errors.append(f"Technology research technologies[{index}] has no id.")
            continue
        if tech_id in technology_ids:
            errors.append(f"Duplicate technology research id: {tech_id}")
        technology_ids.add(tech_id)

        ecosystem = technology.get("ecosystem")
        if ecosystem not in {"paddle", "other"}:
            errors.append(f"Technology {tech_id} ecosystem must be paddle or other.")
        if ecosystem == "paddle":
            paddle_technology_ids.add(tech_id)

        for field in ("name", "detected_version", "selection_context", "why_selected"):
            if not isinstance(technology.get(field), str) or not technology.get(field, "").strip():
                errors.append(f"Technology {tech_id} field {field} must be a non-empty string.")
        for field in ("advantages", "tradeoffs"):
            value = technology.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
                errors.append(f"Technology {tech_id} field {field} must be a non-empty array of strings.")

        alternatives = technology.get("alternatives")
        if not isinstance(alternatives, list) or not alternatives:
            errors.append(f"Technology {tech_id} alternatives must be a non-empty array.")
        else:
            for alt_index, alternative in enumerate(alternatives):
                if (
                    not isinstance(alternative, dict)
                    or not isinstance(alternative.get("name"), str)
                    or not alternative.get("name", "").strip()
                    or not isinstance(alternative.get("not_selected_reason"), str)
                    or not alternative.get("not_selected_reason", "").strip()
                ):
                    errors.append(f"Technology {tech_id} alternatives[{alt_index}] requires name and not_selected_reason.")

        sources = technology.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"Technology {tech_id} sources must be a non-empty array.")
            continue
        if len(sources) < 2:
            warnings.append(f"Technology {tech_id} has only one source; two source types are preferred when available.")
        has_primary = False
        has_official_paddle = False
        technology_source_urls[tech_id] = set()
        for source_index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"Technology {tech_id} sources[{source_index}] must be an object.")
                continue
            source_id = str(source.get("id", ""))
            if not source_id:
                errors.append(f"Technology {tech_id} sources[{source_index}] has no id.")
            elif source_id in source_ids:
                errors.append(f"Duplicate technology research source id: {source_id}")
            else:
                source_ids.add(source_id)
            for field in ("title", "url", "retrieved_at"):
                if not isinstance(source.get(field), str) or not source.get(field, "").strip():
                    errors.append(f"Research source {source_id or source_index} field {field} must be a non-empty string.")
            source_url = str(source.get("url", ""))
            if source_url:
                technology_source_urls[tech_id].add(source_url)
            if urlsplit(source_url).scheme not in {"http", "https"}:
                errors.append(f"Research source {source_id or source_index} must use an HTTP(S) URL.")
            source_type = source.get("source_type")
            if source_type not in SOURCE_TYPES:
                errors.append(f"Research source {source_id or source_index} has invalid source_type.")
            if not isinstance(source.get("is_primary"), bool):
                errors.append(f"Research source {source_id or source_index} is_primary must be a boolean.")
            elif source.get("is_primary"):
                has_primary = True
            claims = source.get("claims_supported")
            if not isinstance(claims, list) or not claims or not all(isinstance(claim, str) and claim.strip() for claim in claims):
                errors.append(f"Research source {source_id or source_index} claims_supported must be a non-empty array.")
            if is_official_paddle_url(source_url):
                has_official_paddle = True
        if not has_primary:
            errors.append(f"Technology {tech_id} has no primary source.")
        if ecosystem == "paddle" and not has_official_paddle:
            errors.append(f"Paddle technology {tech_id} has no official Paddle source.")

    return {
        "technology_ids": technology_ids,
        "source_ids": source_ids,
        "paddle_technology_ids": paddle_technology_ids,
        "technology_source_urls": technology_source_urls,
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
    research_state: dict[str, Any],
    notebook_path: Path,
    notebook_markdown: str,
    assets_dir: Path,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    if prompt_pack.get("version") != 1:
        errors.append("Prompt pack version must be 1.")
    if prompt_pack.get("mode") != manifest.get("mode"):
        errors.append("Prompt pack mode does not match manifest mode.")
    if prompt_pack.get("visual_profile") != "paddle-engineering-atlas":
        errors.append("Prompt pack visual_profile must be paddle-engineering-atlas.")
    semantic_color_map = prompt_pack.get("semantic_color_map")
    if (
        not isinstance(semantic_color_map, dict)
        or any(
            not isinstance(semantic_color_map.get(field), str) or not semantic_color_map.get(field, "").strip()
            for field in SEMANTIC_COLOR_FIELDS
        )
    ):
        errors.append("Prompt pack semantic_color_map must define all Paddle engineering semantic color roles.")
    brand_references = prompt_pack.get("brand_references")
    brand_reference_ids: set[str] = set()
    if not isinstance(brand_references, list):
        errors.append("Prompt pack brand_references must be an array.")
        brand_references = []
    for index, brand_reference in enumerate(brand_references):
        if not isinstance(brand_reference, dict):
            errors.append(f"Prompt pack brand_references[{index}] must be an object.")
            continue
        reference_id = str(brand_reference.get("id", ""))
        if not reference_id:
            errors.append(f"Prompt pack brand_references[{index}] has no id.")
            continue
        if reference_id in brand_reference_ids:
            errors.append(f"Duplicate prompt-pack brand reference id: {reference_id}")
        brand_reference_ids.add(reference_id)
        for field in ("brand", "official_source_url", "local_file", "reference_sha256", "attribution", "usage_context"):
            if not isinstance(brand_reference.get(field), str) or not brand_reference.get(field, "").strip():
                errors.append(f"Brand reference {reference_id} field {field} must be a non-empty string.")
        brand_name = str(brand_reference.get("brand", ""))
        source_url = str(brand_reference.get("official_source_url", ""))
        if "paddle" in brand_name.lower() or "飞桨" in brand_name:
            if not is_official_paddle_url(source_url):
                errors.append(f"Paddle brand reference {reference_id} does not use an official Paddle source URL.")
            attribution = str(brand_reference.get("attribution", ""))
            if "paddle" not in attribution.lower() and "飞桨" not in attribution:
                errors.append(f"Paddle brand reference {reference_id} attribution does not identify PaddlePaddle/飞桨.")
        reference_file = str(brand_reference.get("local_file", ""))
        reference_path = (notebook_path.parent / unquote(reference_file)).resolve()
        if not reference_path.is_file():
            errors.append(f"Brand reference {reference_id} local file does not exist: {reference_file}")
        elif brand_reference.get("reference_sha256") != sha256(reference_path):
            errors.append(f"Brand reference {reference_id} SHA-256 does not match its file.")
    images = prompt_pack.get("images")
    if not isinstance(images, list):
        errors.append("Prompt pack images must be an array.")
        return {"image_count": 0, "accepted_assets": []}

    planned_images = manifest.get("planned_images")
    if isinstance(planned_images, int) and len(images) != planned_images:
        errors.append(f"Prompt pack contains {len(images)} images but manifest planned_images is {planned_images}.")

    plan_methods = manifest_state.get("plan_methods", {})
    image_ids: set[str] = set()
    series_ids: set[str] = set()
    series_positions: set[int] = set()
    series_totals: set[int] = set()
    themes_by_position: dict[int, str] = {}
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
            "series",
            "layout_contract",
            "purpose",
            "information_goal",
            "prose_replacement",
            "density",
            "required_text",
            "source_locked_facts",
            "research_source_ids",
            "brand_reference_ids",
            "evidence_inputs",
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

        series = item.get("series")
        if not isinstance(series, dict):
            errors.append(f"Prompt-pack image {image_id} series must be an object.")
        else:
            series_id = series.get("id")
            position = series.get("position")
            total = series.get("total")
            theme = series.get("theme")
            if not isinstance(series_id, str) or not series_id.strip():
                errors.append(f"Prompt-pack image {image_id} series.id must be a non-empty string.")
            else:
                series_ids.add(series_id)
            if not isinstance(position, int) or position < 1:
                errors.append(f"Prompt-pack image {image_id} series.position must be a positive integer.")
            else:
                if position in series_positions:
                    errors.append(f"Duplicate prompt-pack series position: {position}")
                series_positions.add(position)
                if isinstance(theme, str):
                    themes_by_position[position] = theme
            if not isinstance(total, int) or total < 1:
                errors.append(f"Prompt-pack image {image_id} series.total must be a positive integer.")
            else:
                series_totals.add(total)
            if theme not in {"dark_hero", "light_body"}:
                errors.append(f"Prompt-pack image {image_id} series.theme must be dark_hero or light_body.")

        layout = item.get("layout_contract")
        if not isinstance(layout, dict):
            errors.append(f"Prompt-pack image {image_id} layout_contract must be an object.")
        else:
            if layout.get("canvas") != "16:9":
                errors.append(f"Prompt-pack image {image_id} layout canvas must be 16:9.")
            regions = layout.get("major_regions")
            if not isinstance(regions, int) or not 4 <= regions <= 7:
                errors.append(f"Prompt-pack image {image_id} layout major_regions must be between 4 and 7.")
            if layout.get("reading_path") not in {"left_to_right", "top_to_bottom", "center_out"}:
                errors.append(f"Prompt-pack image {image_id} layout has an invalid reading_path.")
            if layout.get("evidence_role") not in {"primary", "supporting"}:
                errors.append(f"Prompt-pack image {image_id} layout has an invalid evidence_role.")

        prose_replacement = item.get("prose_replacement")
        if not isinstance(prose_replacement, dict):
            errors.append(f"Prompt-pack image {image_id} prose_replacement must be an object.")
        else:
            sections = prose_replacement.get("sections_replaced")
            learning_points = prose_replacement.get("learning_points")
            replaced_characters = prose_replacement.get("estimated_replaced_characters")
            replacement_ratio = prose_replacement.get("replacement_ratio_target")
            retained_summary = prose_replacement.get("retained_accessibility_summary")
            retained_items = prose_replacement.get("retained_copyable_items")
            if (
                not isinstance(sections, list)
                or len(sections) < 2
                or not all(isinstance(section, str) and section.strip() for section in sections)
            ):
                errors.append(f"Prompt-pack image {image_id} must replace at least two named sections.")
            if (
                not isinstance(learning_points, list)
                or len(learning_points) < 3
                or not all(isinstance(point, str) and point.strip() for point in learning_points)
            ):
                errors.append(f"Prompt-pack image {image_id} must cover at least three learning points.")
            if not isinstance(replaced_characters, int) or replaced_characters < 200:
                errors.append(f"Prompt-pack image {image_id} must replace an estimated 200 or more characters.")
            if (
                not isinstance(replacement_ratio, (int, float))
                or isinstance(replacement_ratio, bool)
                or not 0.4 <= replacement_ratio <= 0.65
            ):
                errors.append(f"Prompt-pack image {image_id} replacement_ratio_target must be between 0.4 and 0.65.")
            if prose_replacement.get("duplication_policy") != "summary_only":
                errors.append(f"Prompt-pack image {image_id} duplication_policy must be summary_only.")
            if not isinstance(retained_summary, str) or not retained_summary.strip():
                errors.append(f"Prompt-pack image {image_id} needs a retained accessibility summary.")
            if (
                not isinstance(retained_items, list)
                or not retained_items
                or not all(isinstance(value, str) and value.strip() for value in retained_items)
            ):
                errors.append(f"Prompt-pack image {image_id} must list retained copyable notebook items.")

        for field in ("title", "purpose", "information_goal", "prompt", "output_file", "insertion_point"):
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"Prompt-pack image {image_id} field {field} must be a non-empty string.")
        for field in (
            "required_text",
            "source_locked_facts",
            "research_source_ids",
            "brand_reference_ids",
            "negative_constraints",
            "repairs",
        ):
            if not isinstance(item.get(field), list):
                errors.append(f"Prompt-pack image {image_id} field {field} must be an array.")

        image_research_ids = item.get("research_source_ids", [])
        if isinstance(image_research_ids, list):
            unknown_research_ids = set(image_research_ids) - research_state.get("source_ids", set())
            if unknown_research_ids:
                errors.append(
                    f"Prompt-pack image {image_id} uses unknown research source IDs: {', '.join(sorted(unknown_research_ids))}"
                )
        image_brand_ids = item.get("brand_reference_ids", [])
        if isinstance(image_brand_ids, list):
            unknown_brand_ids = set(image_brand_ids) - brand_reference_ids
            if unknown_brand_ids:
                errors.append(
                    f"Prompt-pack image {image_id} uses unknown brand reference IDs: {', '.join(sorted(unknown_brand_ids))}"
                )

        evidence_inputs = item.get("evidence_inputs")
        if not isinstance(evidence_inputs, list) or not evidence_inputs:
            errors.append(f"Prompt-pack image {image_id} must contain at least one evidence input.")
        else:
            evidence_ids: set[str] = set()
            for evidence_index, evidence in enumerate(evidence_inputs):
                if not isinstance(evidence, dict):
                    errors.append(f"Prompt-pack image {image_id} evidence_inputs[{evidence_index}] must be an object.")
                    continue
                evidence_id = str(evidence.get("id", ""))
                source_type = evidence.get("source_type")
                source_ref = str(evidence.get("source_ref", ""))
                usage = evidence.get("usage")
                if not evidence_id or evidence_id in evidence_ids:
                    errors.append(f"Prompt-pack image {image_id} has a missing or duplicate evidence id: {evidence_id!r}")
                evidence_ids.add(evidence_id)
                if source_type not in {"project_file", "notebook_fact", "research_source", "brand_reference"}:
                    errors.append(f"Prompt-pack image {image_id} evidence {evidence_id} has invalid source_type.")
                if not source_ref:
                    errors.append(f"Prompt-pack image {image_id} evidence {evidence_id} has no source_ref.")
                if not isinstance(usage, str) or not usage.strip():
                    errors.append(f"Prompt-pack image {image_id} evidence {evidence_id} has no usage explanation.")
                if source_type == "project_file" and source_ref:
                    evidence_path = (notebook_path.parent / unquote(source_ref)).resolve()
                    if not evidence_path.is_file():
                        errors.append(f"Prompt-pack image {image_id} evidence file does not exist: {source_ref}")
                    elif evidence.get("sha256") != sha256(evidence_path):
                        errors.append(f"Prompt-pack image {image_id} evidence {evidence_id} SHA-256 does not match.")
                elif source_type == "notebook_fact" and not source_ref.startswith("notebook:"):
                    errors.append(f"Prompt-pack image {image_id} notebook evidence {evidence_id} must use notebook:<reference>.")
                elif source_type == "research_source" and source_ref not in research_state.get("source_ids", set()):
                    errors.append(f"Prompt-pack image {image_id} evidence {evidence_id} uses an unknown research source.")
                elif source_type == "brand_reference" and source_ref not in brand_reference_ids:
                    errors.append(f"Prompt-pack image {image_id} evidence {evidence_id} uses an unknown brand reference.")

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
        if not isinstance(inspection, dict) or any(
            inspection.get(field) != "passed" for field in PROFILE_INSPECTION_FIELDS
        ):
            errors.append(f"Prompt-pack image {image_id} has incomplete Paddle engineering profile inspection.")
        if image_brand_ids and (not isinstance(inspection, dict) or inspection.get("brand_fidelity") != "passed"):
            errors.append(f"Prompt-pack image {image_id} uses a brand reference but has no passed brand_fidelity inspection.")

        output_file = str(item.get("output_file", ""))
        output_files.add(output_file)
        normalized_markdown = notebook_markdown.replace("\\", "/")
        normalized_output = output_file.replace("\\", "/")
        if normalized_output not in normalized_markdown:
            errors.append(f"Accepted prompt-pack image {image_id} is not referenced from notebook Markdown.")
        retained_summary = item.get("prose_replacement", {}).get("retained_accessibility_summary", "")
        if isinstance(retained_summary, str) and retained_summary not in notebook_markdown:
            errors.append(f"Prompt-pack image {image_id} retained accessibility summary is missing from notebook Markdown.")
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
    if images:
        expected_positions = set(range(1, len(images) + 1))
        if len(series_ids) != 1:
            errors.append("Prompt-pack images must share one series.id.")
        if series_positions != expected_positions:
            errors.append("Prompt-pack series positions must be unique and contiguous from 1 to image count.")
        if series_totals != {len(images)}:
            errors.append("Every prompt-pack series.total must equal the image count.")
        if themes_by_position.get(1) != "dark_hero":
            errors.append("Paddle engineering series position 1 must use the dark_hero theme.")
        wrong_body_themes = [
            position for position in range(2, len(images) + 1) if themes_by_position.get(position) != "light_body"
        ]
        if wrong_body_themes:
            errors.append(
                "Paddle engineering body images must use light_body theme at positions: "
                + ", ".join(str(position) for position in wrong_body_themes)
            )
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
    research_sources_path: Path | None = None,
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
    research_sources = (
        load_json(research_sources_path, "Technology research sources", errors) if research_sources_path else None
    )
    manifest_state: dict[str, Any] = {}
    research_state: dict[str, Any] = {
        "technology_ids": set(),
        "source_ids": set(),
        "paddle_technology_ids": set(),
        "technology_source_urls": {},
    }
    notebook_markdown = "\n".join(
        source_text(cell) for cell in cells if isinstance(cell, dict) and cell.get("cell_type") == "markdown"
    )

    if source_path and manifest and research_sources_path:
        manifest_state = validate_manifest(
            manifest, source_path, notebook_path, research_sources_path, errors, warnings
        )
    elif source_path and not manifest_path:
        errors.append("Teaching manifest is required when validating against a source notebook.")
    elif source_path and not research_sources_path:
        errors.append("Technology research sources are required when validating against a source notebook.")

    if research_sources:
        research_state = validate_research_sources(research_sources, errors, warnings)
        checks["technology_research"] = {
            "technology_ids": sorted(research_state["technology_ids"]),
            "source_ids": sorted(research_state["source_ids"]),
            "paddle_technology_ids": sorted(research_state["paddle_technology_ids"]),
        }
        missing_citations = []
        for technology_id, source_urls in research_state["technology_source_urls"].items():
            if source_urls and not any(url in notebook_markdown for url in source_urls):
                missing_citations.append(technology_id)
        if missing_citations:
            errors.append(
                "Teaching notebook Markdown has no research-source link for technologies: "
                + ", ".join(sorted(missing_citations))
            )

    if source:
        checks["source_sha256"] = sha256(source_path)
        checks["source_comparison"] = compare_source(
            source, notebook, manifest, manifest_state, errors, warnings
        )

    if manifest and resolved_assets:
        if prompt_pack:
            checks["prompt_pack"] = validate_prompt_pack(
                prompt_pack,
                manifest,
                manifest_state,
                research_state,
                notebook_path,
                notebook_markdown,
                resolved_assets,
                errors,
                warnings,
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
    parser.add_argument("--research-sources", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = validate(
        args.notebook.resolve(),
        args.source.resolve(),
        args.assets_dir.resolve(),
        args.manifest.resolve(),
        args.prompt_pack.resolve(),
        args.research_sources.resolve(),
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
