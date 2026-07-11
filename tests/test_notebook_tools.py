from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


inspect_module = load_module("inspect_notebook", ROOT / "scripts" / "inspect_notebook.py")
validate_module = load_module("validate_notebook", ROOT / "scripts" / "validate_notebook.py")


def notebook(cells, language="python"):
    metadata = {
        "kernelspec": {"name": language, "display_name": language, "language": language},
        "language_info": {"name": language},
    }
    return {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}


def code(source, cell_id="c1", outputs=None, metadata=None):
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": metadata or {},
        "source": source,
        "outputs": outputs or [],
        "execution_count": None,
    }


def markdown(source, cell_id="m1", attachments=None):
    cell = {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": source}
    if attachments is not None:
        cell["attachments"] = attachments
    return cell


class NotebookToolTests(unittest.TestCase):
    def write_notebook(self, directory: Path, name: str, cells, language="python") -> Path:
        path = directory / name
        path.write_text(json.dumps(notebook(cells, language)), encoding="utf-8")
        return path

    def write_delivery(
        self,
        root: Path,
        source: Path,
        teaching: Path,
        *,
        code_changes=None,
        source_changes=None,
        image=False,
        brand=False,
        wrong_hash=False,
        unofficial_paddle_source=False,
    ):
        artifacts = root / "artifacts"
        assets = artifacts / "teaching_assets"
        assets.mkdir(parents=True)
        teaching_data = json.loads(teaching.read_text(encoding="utf-8"))
        if not any(cell.get("id") == "m1" for cell in teaching_data["cells"]):
            teaching_data["cells"].append(
                markdown(
                    "## Technology selection\n"
                    "Paddle is used for the existing execution path. "
                    "[Official documentation](https://www.paddlepaddle.org.cn/documentation/zh/index_cn.html)."
                )
            )
            teaching.write_text(json.dumps(teaching_data), encoding="utf-8")
        content_plan = [
            {
                "id": "quality-gate",
                "purpose": "Show exact checks",
                "rendering_method": "html_cards",
                "reason": "Exact checklist without spatial relationships",
                "insertion_point": "## Quality gate",
            }
        ]
        generated_assets = []
        images = []
        brand_references = []
        brand_reference_ids = []
        if brand:
            brand_assets = artifacts / "brand_assets"
            brand_assets.mkdir(parents=True)
            brand_file = brand_assets / "paddle.png"
            brand_file.write_bytes(b"official-paddle-logo")
            brand_references.append(
                {
                    "id": "paddle-logo",
                    "brand": "PaddlePaddle 飞桨",
                    "official_source_url": "https://www.paddlepaddle.org.cn/",
                    "local_file": "artifacts/brand_assets/paddle.png",
                    "reference_sha256": validate_module.sha256(brand_file),
                    "attribution": "PaddlePaddle 飞桨官方标识",
                    "usage_context": "Open-source Paddle teaching notebook",
                }
            )
            brand_reference_ids.append("paddle-logo")
        if image:
            asset = assets / "flow.png"
            asset.write_bytes(b"generated-image")
            output_file = "artifacts/teaching_assets/flow.png"
            generated_assets.append(output_file)
            content_plan.append(
                {
                    "id": "flow",
                    "purpose": "Explain pipeline dependencies",
                    "rendering_method": "imagegen",
                    "reason": "The learner needs sequence, gates, and dependencies in one view",
                    "insertion_point": "## Flow",
                }
            )
            images.append(
                {
                    "id": "flow",
                    "title": "Flow",
                    "series": {
                        "id": "fixture-series",
                        "position": 1,
                        "total": 1,
                        "theme": "dark_hero",
                    },
                    "layout_contract": {
                        "canvas": "16:9",
                        "major_regions": 5,
                        "reading_path": "left_to_right",
                        "evidence_role": "primary",
                    },
                    "purpose": "Explain pipeline dependencies",
                    "information_goal": "Replace four separate stage explanations",
                    "prose_replacement": {
                        "sections_replaced": ["Data preparation", "Training and validation"],
                        "learning_points": [
                            "How input data enters the pipeline",
                            "How training connects to validation",
                            "Which artifacts are delivered",
                        ],
                        "estimated_replaced_characters": 420,
                        "replacement_ratio_target": 0.55,
                        "duplication_policy": "summary_only",
                        "retained_accessibility_summary": "The image summarizes data, training, validation, and output flow.",
                        "retained_copyable_items": ["Commands", "artifact paths", "source links"],
                    },
                    "density": {
                        "target": "moderately_high",
                        "information_regions": 5,
                        "text_items": 16,
                        "reading_path": "left_to_right",
                    },
                    "required_text": ["Input", "Train", "Validate", "Export"],
                    "source_locked_facts": ["model-v1"],
                    "research_source_ids": ["paddle-docs"],
                    "brand_reference_ids": brand_reference_ids,
                    "evidence_inputs": [
                        {
                            "id": "notebook-counts",
                            "source_type": "notebook_fact",
                            "source_ref": "notebook:dataset-summary",
                            "usage": "Lock dataset and result counts to notebook evidence",
                        }
                    ],
                    "prompt": "Create the final direct-use teaching infographic.",
                    "negative_constraints": ["no invented values"],
                    "output_file": output_file,
                    "insertion_point": "## Flow",
                    "status": "accepted",
                    "accepted_asset_sha256": "0" * 64 if wrong_hash else validate_module.sha256(asset),
                    "inspection": {
                        "text_accuracy": "passed",
                        "numeric_accuracy": "passed",
                        "readability": "passed",
                        "information_density": "passed",
                        "profile_fidelity": "passed",
                        "evidence_fidelity": "passed",
                        "series_consistency": "passed",
                        "prose_replacement": "passed",
                    },
                    "repairs": [],
                }
            )
            if brand:
                images[0]["inspection"]["brand_fidelity"] = "passed"
            teaching_data = json.loads(teaching.read_text(encoding="utf-8"))
            for cell in teaching_data["cells"]:
                if cell.get("id") == "m1":
                    cell["source"] += (
                        "\n\n![Flow](artifacts/teaching_assets/flow.png)\n\n"
                        "The image summarizes data, training, validation, and output flow."
                    )
            teaching.write_text(json.dumps(teaching_data), encoding="utf-8")

        research = {
            "version": 1,
            "researched_at": "2026-07-11",
            "web_search_used": True,
            "search_queries": ["site:paddlepaddle.org.cn Paddle official documentation"],
            "technologies": [
                {
                    "id": "paddle",
                    "name": "PaddlePaddle",
                    "ecosystem": "paddle",
                    "detected_version": "unknown",
                    "selection_context": "Use the framework already present in the notebook.",
                    "why_selected": "It matches the notebook APIs and delivery environment.",
                    "advantages": ["Preserves the existing Paddle execution path"],
                    "tradeoffs": ["Version compatibility must be verified"],
                    "alternatives": [
                        {"name": "PyTorch", "not_selected_reason": "Would require rewriting the existing workflow"}
                    ],
                    "sources": [
                        {
                            "id": "paddle-docs",
                            "title": "Paddle official documentation",
                            "url": (
                                "https://example.com/paddle"
                                if unofficial_paddle_source
                                else "https://www.paddlepaddle.org.cn/documentation/zh/index_cn.html"
                            ),
                            "source_type": "official_documentation",
                            "is_primary": True,
                            "retrieved_at": "2026-07-11",
                            "claims_supported": ["Official framework documentation"],
                        }
                    ],
                }
            ],
        }

        manifest = {
            "source_notebook": source.name,
            "output_notebook": teaching.name,
            "source_sha256": validate_module.sha256(source),
            "mode": "quick",
            "mode_reason": "Focused fixture",
            "planned_images": len(images),
            "research_artifact": "artifacts/teaching_research_sources.json",
            "content_plan": content_plan,
            "generated_assets": generated_assets,
            "inserted_cell_ids": ["m1"],
            "modified_code_cells": code_changes or [],
            "modified_source_cells": source_changes or [],
            "execution_logic_modified": bool(code_changes),
        }
        manifest_path = artifacts / "teaching_manifest.json"
        prompt_path = artifacts / "teaching_imagegen_prompts.json"
        research_path = artifacts / "teaching_research_sources.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        prompt_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "mode": "quick",
                    "visual_profile": "paddle-engineering-atlas",
                    "semantic_color_map": {
                        "structure": "navy",
                        "active_data": "blue_cyan",
                        "success_normal": "green",
                        "failure_defect": "red",
                        "warning_limitation": "orange_amber",
                        "secondary_class": "purple",
                    },
                    "brand_references": brand_references,
                    "images": images,
                }
            ),
            encoding="utf-8",
        )
        research_path.write_text(json.dumps(research), encoding="utf-8")
        return assets, manifest_path, prompt_path, research_path

    def test_inspection_detects_chinese_stages_magics_and_secret_signal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.write_notebook(
                root,
                "source.ipynb",
                [
                    markdown("# 数据处理\n## 模型训练\n## 评估结果"),
                    code("%matplotlib inline\napi_key='secret'"),
                ],
            )
            report = inspect_module.inspect(path)
            self.assertIn("data", report["detected_stages"])
            self.assertIn("training", report["detected_stages"])
            self.assertIn("evaluation", report["detected_stages"])
            self.assertEqual(report["features"]["magic_cells"], [1])
            self.assertEqual(report["risk_signals"]["possible_secrets"][0]["kind"], "api_key")

    def test_non_python_kernel_skips_python_ast(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.write_notebook(root, "julia.ipynb", [code("function f(x)\n  x^2\nend")], "julia")
            report = validate_module.validate(path, None, None)
            self.assertTrue(report["ok"])
            self.assertEqual(report["checks"]["syntax_skipped"][0]["reason"], "non_python:julia")

    def test_missing_attachment_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.write_notebook(root, "teaching.ipynb", [markdown("![x](attachment:missing.png)", attachments={})])
            report = validate_module.validate(path, None, None)
            self.assertFalse(report["ok"])
            self.assertTrue(any("Missing notebook attachment" in error for error in report["errors"]))

    def test_valid_attachment_and_markdown_image_title(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a b.png").write_bytes(b"image")
            path = self.write_notebook(
                root,
                "teaching.ipynb",
                [
                    markdown(
                        "![attached](attachment:inside.png)\n![local](<a%20b.png> \"caption\")",
                        attachments={"inside.png": {"image/png": "aW1hZ2U="}},
                    )
                ],
            )
            report = validate_module.validate(path, None, None)
            self.assertTrue(report["ok"], report["errors"])

    def test_undisclosed_code_change_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 2")])
            report = validate_module.validate(teaching, source, None)
            self.assertFalse(report["ok"])
            self.assertTrue(any("no manifest" in error for error in report["errors"]))

    def test_disclosed_code_change_can_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 2")])
            assets, manifest, prompt, research = self.write_delivery(
                root,
                source,
                teaching,
                code_changes=[{"cell_id": "c1", "reason": "User requested a functional change"}],
            )
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertTrue(report["ok"], report["errors"])

    def test_undisclosed_output_change_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1", outputs=[{"output_type": "stream", "name": "stdout", "text": "1"}])])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching)
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("Undisclosed source-cell changes" in error for error in report["errors"]))

    def test_idless_source_code_change_requires_sequence_disclosure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_cell = code("x = 1")
            source_cell.pop("id")
            teaching_cell = code("x = 2")
            teaching_cell.pop("id")
            source = self.write_notebook(root, "source.ipynb", [source_cell])
            teaching = self.write_notebook(root, "teaching.ipynb", [teaching_cell])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching)
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("code-sequence" in error for error in report["errors"]))

    def test_prompt_pack_asset_hash_and_routing_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching, image=True)
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["checks"]["prompt_pack"]["accepted_assets"], ["flow.png"])

    def test_prompt_pack_hash_mismatch_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching, image=True, wrong_hash=True)
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("SHA-256" in error for error in report["errors"]))

    def test_paddle_research_requires_official_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(
                root, source, teaching, unofficial_paddle_source=True
            )
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("no official Paddle source" in error for error in report["errors"]))

    def test_paddle_brand_reference_and_fidelity_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(
                root, source, teaching, image=True, brand=True
            )
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertTrue(report["ok"], report["errors"])

    def test_brand_reference_requires_fidelity_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(
                root, source, teaching, image=True, brand=True
            )
            prompt_data = json.loads(prompt.read_text(encoding="utf-8"))
            prompt_data["images"][0]["inspection"].pop("brand_fidelity")
            prompt.write_text(json.dumps(prompt_data), encoding="utf-8")
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("brand_fidelity" in error for error in report["errors"]))

    def test_researched_technology_requires_visible_notebook_citation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching)
            teaching_data = json.loads(teaching.read_text(encoding="utf-8"))
            teaching_data["cells"] = [cell for cell in teaching_data["cells"] if cell.get("cell_type") != "markdown"]
            teaching.write_text(json.dumps(teaching_data), encoding="utf-8")
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("no research-source link" in error for error in report["errors"]))

    def test_paddle_profile_requires_evidence_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching, image=True)
            prompt_data = json.loads(prompt.read_text(encoding="utf-8"))
            prompt_data["images"][0]["evidence_inputs"] = []
            prompt.write_text(json.dumps(prompt_data), encoding="utf-8")
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("at least one evidence input" in error for error in report["errors"]))

    def test_paddle_profile_requires_dark_first_hero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching, image=True)
            prompt_data = json.loads(prompt.read_text(encoding="utf-8"))
            prompt_data["images"][0]["series"]["theme"] = "light_body"
            prompt.write_text(json.dumps(prompt_data), encoding="utf-8")
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("position 1 must use the dark_hero" in error for error in report["errors"]))

    def test_visual_compression_requires_substantial_prose_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt, research = self.write_delivery(root, source, teaching, image=True)
            prompt_data = json.loads(prompt.read_text(encoding="utf-8"))
            prompt_data["images"][0]["prose_replacement"]["estimated_replaced_characters"] = 80
            prompt.write_text(json.dumps(prompt_data), encoding="utf-8")
            report = validate_module.validate(teaching, source, assets, manifest, prompt, research)
            self.assertFalse(report["ok"])
            self.assertTrue(any("200 or more characters" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
