# Conversion Workflow

## Mode Selection

Choose the smallest mode that satisfies the request.

| Mode | Typical source | Images | Expected work |
| --- | --- | ---: | --- |
| `quick` | Fewer than 10 code cells or a focused section | 0-2 | Navigation, explanations, limited visual support |
| `standard` | 10-30 code cells or several engineering stages | 3-5 | Full narrative pass, key diagrams, validation and delivery |
| `full` | More than 30 code cells, a course/demo artifact, or an explicit showcase request | 6-9 | Complete visual system, default target 8 images |

Cell counts are guidance, not a rigid classifier. Increase the mode when the notebook has multiple independent pipelines, high-stakes limitations, or complex delivery artifacts. Decrease it when repeated code cells represent one simple idea.

## Inspection

Run:

```powershell
python scripts/inspect_notebook.py .\source.ipynb --output .\artifacts\notebook_inspection.json
```

Use the report to identify:

- Headings and implied table of contents.
- Setup, data, training, evaluation, inference, validation, export, and packaging stages.
- Code magics, shell commands, non-Python cells, widgets, attachments, and outputs.
- Candidate metrics and source-locked facts.
- External paths, remote URLs, secrets, personal data, and execution risks.

## Required Artifacts

Use this project-local layout unless the repository already has an equivalent convention:

```text
artifacts/
  notebook_inspection.json
  teaching_manifest.json
  teaching_imagegen_prompts.json
  teaching_validation.json
  teaching_assets/
    hero.png
    data-flow.png
```

The manifest should include:

```json
{
  "source_notebook": "source.ipynb",
  "output_notebook": "source.teaching.ipynb",
  "source_sha256": "...",
  "mode": "standard",
  "mode_reason": "18 code cells across data, training, evaluation, and export",
  "planned_images": 4,
  "content_plan": [
    {
      "id": "quality-gate",
      "purpose": "Show exact release checks and prohibited fallback behavior",
      "rendering_method": "html_cards",
      "reason": "Exact checklist without spatial relationships",
      "insertion_point": "## Quality gate"
    }
  ],
  "generated_assets": [],
  "inserted_cell_ids": [],
  "modified_code_cells": [],
  "modified_source_cells": [],
  "execution_logic_modified": false
}
```

The machine-readable contract is `schemas/teaching-manifest.schema.json`. The validator uses equivalent standard-library checks so no JSON Schema dependency is required at runtime.

## Editing Rules

- Create a teaching copy before large edits.
- Insert explanatory Markdown around existing code rather than moving code unnecessarily.
- Preserve code order, cell IDs, metadata, tags, outputs, attachments, and widgets.
- When a code cell must change, record its cell ID and reason in the manifest.
- For an older source notebook whose code cells have no IDs, preserve code order and use the synthetic disclosure ID `code-sequence` if the user explicitly requests a functional change.
- Do not clear outputs by default. Existing outputs may be important evidence for the teaching narrative.
- Keep notebook image references relative to the notebook location when possible.

## Teaching Structure

A full conversion normally contains:

1. Hero visual and project positioning.
2. Outcomes and source-backed metrics.
3. Learner route map.
4. Stage explanations before important code.
5. Output-reading notes after important code.
6. Validation gates and failure modes.
7. Limitations and high-stakes caveats where relevant.
8. Deliverables and artifact locations.

Route each element through `content-routing.md`. The structure above does not imply that every section needs an image. Exact list-like content should remain searchable HTML, tables, or Markdown.

## Execution Policy

Static validation is the default. Notebook execution is opt-in when the notebook is untrusted, expensive, destructive, credentialed, or dependent on unavailable hardware/services.

If execution is appropriate:

- Execute a disposable copy.
- Set a timeout.
- Do not overwrite source outputs until success is confirmed.
- Record environment failures separately from notebook defects.
