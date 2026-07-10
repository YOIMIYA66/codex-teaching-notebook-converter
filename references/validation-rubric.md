# Validation Rubric

## Required Static Checks

- Notebook is valid JSON with a `cells` array.
- Every cell has a recognized type and a source.
- Cell IDs are unique when present.
- Local Markdown and HTML image references resolve.
- Required teaching assets exist under the project asset directory.
- Python cells compile after notebook magics and shell commands are classified or skipped.
- The source notebook hash is recorded.
- Code-cell changes relative to the source are disclosed.
- Prompt pack entries map to accepted local assets.
- The manifest records selected mode, image count, inserted cells, and functional changes.

## Optional Checks

- `jupyter nbconvert --to html` renders successfully.
- HTML preview contains all expected image references.
- A disposable execution copy succeeds with `nbclient`.
- Generated images were visually inspected at notebook reading size.

## Severity

- `error`: invalid JSON, missing asset, duplicate cell ID, undisclosed code change, or broken required reference.
- `warning`: skipped syntax validation, absolute local path, remote asset, missing optional metadata, or unavailable renderer.
- `info`: execution intentionally skipped, outputs preserved, or attachment embedding not used.

## Delivery Report

`artifacts/teaching_validation.json` must state:

```json
{
  "ok": true,
  "errors": [],
  "warnings": [],
  "skipped": ["notebook execution"],
  "checks": {},
  "remaining_risks": []
}
```

Do not describe a notebook as production-ready solely because it exports, renders, or executes once.
