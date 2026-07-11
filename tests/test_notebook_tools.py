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
        wrong_hash=False,
    ):
        artifacts = root / "artifacts"
        assets = artifacts / "teaching_assets"
        assets.mkdir(parents=True)
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
                    "purpose": "Explain pipeline dependencies",
                    "information_goal": "Replace four separate stage explanations",
                    "density": {
                        "target": "moderately_high",
                        "information_regions": 5,
                        "text_items": 16,
                        "reading_path": "left_to_right",
                    },
                    "required_text": ["Input", "Train", "Validate", "Export"],
                    "source_locked_facts": ["model-v1"],
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
                    },
                    "repairs": [],
                }
            )

        manifest = {
            "source_notebook": source.name,
            "output_notebook": teaching.name,
            "source_sha256": validate_module.sha256(source),
            "mode": "quick",
            "mode_reason": "Focused fixture",
            "planned_images": len(images),
            "content_plan": content_plan,
            "generated_assets": generated_assets,
            "inserted_cell_ids": ["m1"],
            "modified_code_cells": code_changes or [],
            "modified_source_cells": source_changes or [],
            "execution_logic_modified": bool(code_changes),
        }
        manifest_path = artifacts / "teaching_manifest.json"
        prompt_path = artifacts / "teaching_imagegen_prompts.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        prompt_path.write_text(json.dumps({"version": 1, "mode": "quick", "images": images}), encoding="utf-8")
        return assets, manifest_path, prompt_path

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
            assets, manifest, prompt = self.write_delivery(
                root,
                source,
                teaching,
                code_changes=[{"cell_id": "c1", "reason": "User requested a functional change"}],
            )
            report = validate_module.validate(teaching, source, assets, manifest, prompt)
            self.assertTrue(report["ok"], report["errors"])

    def test_undisclosed_output_change_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1", outputs=[{"output_type": "stream", "name": "stdout", "text": "1"}])])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt = self.write_delivery(root, source, teaching)
            report = validate_module.validate(teaching, source, assets, manifest, prompt)
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
            assets, manifest, prompt = self.write_delivery(root, source, teaching)
            report = validate_module.validate(teaching, source, assets, manifest, prompt)
            self.assertFalse(report["ok"])
            self.assertTrue(any("code-sequence" in error for error in report["errors"]))

    def test_prompt_pack_asset_hash_and_routing_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt = self.write_delivery(root, source, teaching, image=True)
            report = validate_module.validate(teaching, source, assets, manifest, prompt)
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["checks"]["prompt_pack"]["accepted_assets"], ["flow.png"])

    def test_prompt_pack_hash_mismatch_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [code("x = 1")])
            teaching = self.write_notebook(root, "teaching.ipynb", [code("x = 1")])
            assets, manifest, prompt = self.write_delivery(root, source, teaching, image=True, wrong_hash=True)
            report = validate_module.validate(teaching, source, assets, manifest, prompt)
            self.assertFalse(report["ok"])
            self.assertTrue(any("SHA-256" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
