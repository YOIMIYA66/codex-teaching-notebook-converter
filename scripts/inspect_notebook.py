#!/usr/bin/env python3
"""Inspect a Jupyter notebook without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


STAGE_PATTERNS = {
    "setup": re.compile(r"\b(?:setup|install|environment)\b|配置|安装|环境", re.I),
    "data": re.compile(r"\b(?:data|dataset|preprocess|load)\b|数据|预处理|加载", re.I),
    "training": re.compile(r"\b(?:train|training|finetune|fine-tune|lora)\b|训练|微调", re.I),
    "evaluation": re.compile(r"\b(?:eval|evaluation|metric|test)\b|评估|指标|测试", re.I),
    "inference": re.compile(r"\b(?:infer|inference|predict|generate)\b|推理|预测|生成", re.I),
    "validation": re.compile(r"\b(?:validate|validation|quality|gate)\b|校验|验证|质量|门禁", re.I),
    "export": re.compile(r"\b(?:export|save|checkpoint|convert)\b|导出|保存|转换", re.I),
    "packaging": re.compile(r"\b(?:package|manifest|zip|deliver)\b|打包|清单|交付", re.I),
}
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|secret|password|passwd)\s*[=:]\s*['\"][^'\"]+"
)
METRIC_PATTERN = re.compile(
    r"(?i)\b(accuracy|precision|recall|f1|loss|bleu|rouge|auc|perplexity)\b.{0,40}?(-?\d+(?:\.\d+)?)"
)
PATH_PATTERN = re.compile(r"(?:[A-Za-z]:\\[^\s'\"]+|/(?:home|Users|mnt|workspace)/[^\s'\"]+)")
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.I)


def source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def suggest_mode(code_cells: int, stages: list[str]) -> tuple[str, str, str]:
    complexity = code_cells + max(0, len(stages) - 2) * 2
    if complexity < 10:
        return "quick", "0-2", "Small or focused notebook."
    if complexity <= 34:
        return "standard", "3-5", "Multiple teaching stages with moderate complexity."
    return "full", "6-9", "Large or multi-stage notebook suitable for a showcase conversion."


def inspect(path: Path) -> dict[str, Any]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    counts: dict[str, int] = {}
    headings: list[dict[str, Any]] = []
    stages: set[str] = set()
    metrics: list[dict[str, str]] = []
    absolute_paths: set[str] = set()
    remote_urls: set[str] = set()
    secret_signals: list[dict[str, Any]] = []
    magic_cells: list[int] = []
    shell_cells: list[int] = []
    output_cells = 0
    attachment_cells = 0

    for index, cell in enumerate(cells):
        cell_type = str(cell.get("cell_type", "unknown"))
        counts[cell_type] = counts.get(cell_type, 0) + 1
        text = source_text(cell)

        if cell_type == "markdown":
            for line in text.splitlines():
                match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
                if match:
                    headings.append({"level": len(match.group(1)), "title": match.group(2), "cell": index})

        stripped_lines = [line.lstrip() for line in text.splitlines() if line.strip()]
        if any(line.startswith(("%", "%%")) for line in stripped_lines):
            magic_cells.append(index)
        if any(line.startswith("!") for line in stripped_lines):
            shell_cells.append(index)
        if cell.get("outputs"):
            output_cells += 1
        if cell.get("attachments"):
            attachment_cells += 1

        for stage, pattern in STAGE_PATTERNS.items():
            if pattern.search(text):
                stages.add(stage)
        for metric, value in METRIC_PATTERN.findall(text):
            item = {"name": metric, "value": value}
            if item not in metrics:
                metrics.append(item)
        absolute_paths.update(PATH_PATTERN.findall(text))
        remote_urls.update(URL_PATTERN.findall(text))
        for match in SECRET_PATTERN.finditer(text):
            secret_signals.append({"cell": index, "kind": match.group(1)})

    ordered_stages = [stage for stage in STAGE_PATTERNS if stage in stages]
    mode, image_range, reason = suggest_mode(counts.get("code", 0), ordered_stages)
    return {
        "notebook": str(path),
        "sha256": sha256(path),
        "nbformat": notebook.get("nbformat"),
        "cell_counts": counts,
        "headings": headings,
        "detected_stages": ordered_stages,
        "candidate_metrics": metrics[:50],
        "features": {
            "magic_cells": magic_cells,
            "shell_cells": shell_cells,
            "cells_with_outputs": output_cells,
            "cells_with_attachments": attachment_cells,
            "kernelspec": notebook.get("metadata", {}).get("kernelspec"),
            "language_info": notebook.get("metadata", {}).get("language_info"),
        },
        "risk_signals": {
            "possible_secrets": secret_signals,
            "absolute_paths": sorted(absolute_paths),
            "remote_urls": sorted(remote_urls),
            "requires_execution_review": bool(secret_signals or shell_cells or magic_cells),
        },
        "recommendation": {
            "mode": mode,
            "image_range": image_range,
            "reason": reason,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = inspect(args.notebook.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
