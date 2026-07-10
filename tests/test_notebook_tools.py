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


def notebook(cells):
    return {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}


class NotebookToolTests(unittest.TestCase):
    def write_notebook(self, directory: Path, name: str, cells) -> Path:
        path = directory / name
        path.write_text(json.dumps(notebook(cells)), encoding="utf-8")
        return path

    def test_inspection_detects_stages_magics_and_secret_signal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.write_notebook(root, "source.ipynb", [
                {"cell_type": "markdown", "id": "m1", "metadata": {}, "source": "# Training\n## Evaluation"},
                {"cell_type": "code", "id": "c1", "metadata": {}, "source": "%matplotlib inline\napi_key='secret'", "outputs": [], "execution_count": None},
            ])
            report = inspect_module.inspect(path)
            self.assertIn("training", report["detected_stages"])
            self.assertIn("evaluation", report["detected_stages"])
            self.assertEqual(report["features"]["magic_cells"], [1])
            self.assertEqual(report["risk_signals"]["possible_secrets"][0]["kind"], "api_key")

    def test_validation_skips_magics_and_finds_missing_image(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.write_notebook(root, "teaching.ipynb", [
                {"cell_type": "markdown", "id": "m1", "metadata": {}, "source": "![Missing](assets/missing.png)"},
                {"cell_type": "code", "id": "c1", "metadata": {}, "source": "%matplotlib inline", "outputs": [], "execution_count": None},
            ])
            report = validate_module.validate(path, None, None)
            self.assertFalse(report["ok"])
            self.assertTrue(any("Missing local image" in error for error in report["errors"]))
            self.assertEqual(report["checks"]["syntax_skipped"][0]["reason"], "line_magic")

    def test_validation_detects_code_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.write_notebook(root, "source.ipynb", [
                {"cell_type": "code", "id": "c1", "metadata": {}, "source": "x = 1", "outputs": [], "execution_count": None},
            ])
            teaching = self.write_notebook(root, "teaching.ipynb", [
                {"cell_type": "markdown", "id": "m1", "metadata": {}, "source": "# Lesson"},
                {"cell_type": "code", "id": "c1", "metadata": {}, "source": "x = 2", "outputs": [], "execution_count": None},
            ])
            report = validate_module.validate(teaching, source, None)
            self.assertFalse(report["checks"]["code_cells_unchanged_and_in_order"])
            self.assertTrue(any("differ from the source" in warning for warning in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
