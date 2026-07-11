---
name: teaching-notebook-converter
description: Convert an existing engineering or research Jupyter notebook into a polished teaching copy while preserving its executable workflow. Use when Codex is asked to teach, explain, present, or visually restructure an existing .ipynb with narrative guidance, direct-use imagegen infographics, inline HTML cards, learner navigation, validation gates, and delivery artifacts. Do not use for ordinary notebook debugging, analysis, training, or creating a notebook from scratch unless teaching conversion is requested.
---

# Teaching Notebook Converter

Convert a runnable engineering notebook into a teaching-oriented copy. Preserve the source notebook and its executable path. Add teaching value through narrative structure, direct-use imagegen visuals, Markdown, inline HTML cards, output interpretation, and validation.

## Non-Negotiable Rules

- Keep the source notebook unchanged unless the user explicitly requests in-place editing.
- Do not rewrite training, inference, evaluation, export, or packaging logic unless the user requests a functional change.
- Use structured JSON or notebook APIs for `.ipynb` files. Do not edit raw notebook text casually.
- For planned teaching visuals, use the built-in `image_gen` tool to generate final text-bearing bitmap images directly.
- Do not replace required teaching visuals with PIL, SVG, Mermaid, HTML canvas, slide screenshots, or blank backgrounds composed locally later.
- Use imagegen only when visual composition adds teaching value through process, hierarchy, dependency, causality, comparison, spatial structure, or an integrated system view.
- Render simple checklists, status gates, metric grids, parameter tables, file inventories, evidence lists, and pass/fail summaries as Markdown tables or inline HTML cards. Do not spend an imagegen call on content that is primarily a styled list.
- Imagegen visuals should have moderately high information density: enough structured content to replace substantial explanatory prose, but still readable at normal notebook width.
- Local image processing is allowed only for contact sheets, thumbnails, release copies, validation previews, or documented repair of a small defect in an accepted imagegen output.
- Never send secrets, raw personal records, proprietary source code, access tokens, or unnecessary absolute paths to image generation tools. Redact or summarize sensitive source content first.
- Do not execute an untrusted notebook without explicit user approval.

## Required References

Read only the references needed for the active conversion:

- Read `references/workflow.md` for mode selection, artifacts, and the end-to-end procedure.
- Read `references/technology-research.md` before explaining why a framework, model, library, deployment tool, or Paddle component was selected.
- Read `references/content-routing.md` before deciding which material becomes imagegen, a table, cards, or Markdown.
- Read `references/visual-policy.md` before planning or generating teaching images.
- Read `references/prompt-contract.md` before writing the imagegen prompt pack.
- Read `references/validation-rubric.md` before final validation and delivery.

## Workflow

1. Inspect the source before editing.
   - Run `python scripts/inspect_notebook.py <source.ipynb> --output <inspection.json>`.
   - Review headings, code/Markdown counts, execution stages, magics, external files, outputs, metrics, and risk signals.

2. Research the technology choices.
   - Detect the major frameworks, Paddle components, model libraries, training methods, inference tools, and deployment technologies used by the notebook, including versions when available.
   - Use web search for current official documentation, official repositories, release notes, official tutorials, and useful technical blogs. Prefer primary sources for factual claims and use blogs as supporting explanation.
   - Explain the problem each technology solves, why it fits this notebook, its concrete advantages, its tradeoffs, and reasonable alternatives.
   - Save the evidence and claim mapping in `artifacts/teaching_research_sources.json` before writing technology-selection content.

3. Select a conversion mode.
   - `quick`: focused teaching cleanup with 0-2 images.
   - `standard`: normal teaching conversion with 3-5 images.
   - `full`: showcase-quality conversion with 6-9 images, default target 8.
   - Use source complexity and user intent to choose. Explicit user requirements override automatic selection.

4. Create a teaching copy.
   - Prefer `<source-name>.teaching.ipynb`.
   - Record the source SHA-256 and output path in `artifacts/teaching_manifest.json`.
   - Preserve cell IDs, metadata, tags, outputs, attachments, and code-cell order unless a documented change is required.

5. Plan before modifying.
   - Identify setup, data, training, evaluation, inference, validation, export, and delivery stages.
   - Write a narrative and content plan appropriate to the selected mode. Assign each planned teaching element a rendering method: `imagegen`, `html_cards`, `markdown_table`, or `markdown`.
   - For `full`, plan 6-9 purposeful teaching visuals. Do not create filler images merely to satisfy a count.
   - Count only `imagegen` items toward the image target. Simple list-like artifacts do not become imagegen items merely to increase the count.

6. Write the complete prompt pack.
   - Save it as `artifacts/teaching_imagegen_prompts.json` before final image generation.
   - Every planned image must include exact on-image text, source-locked facts, an information-density plan, a complete prompt, negative constraints, target filename, and insertion point.

7. Generate and inspect visuals.
   - Use one imagegen call per distinct teaching image.
   - Require imagegen to place the final required text directly in the bitmap.
   - For Paddle logo-bearing visuals, provide an official Paddle logo asset as an image reference and require exact brand fidelity. Do not rely on a text-only request for an approximate logo.
   - Copy every accepted image into `artifacts/teaching_assets/` and reference only project-local files or notebook attachments.
   - Inspect multilingual text, numbers, model names, filenames, paths, and reading density before acceptance. Regenerate when source-locked content changes or the image is too sparse or too dense.

8. Enrich the teaching copy.
   - Add learner orientation, stage explanations, input/output contracts, failure modes, output-reading guidance, quality gates, limitations, and deliverables.
   - Add a source-backed technology-selection explanation for every major technology: why it was chosen, where it is advantageous, what constraints remain, and which alternatives were considered.
   - Use inline HTML styles for compact cards when cloud renderer compatibility is uncertain.
   - Keep exact metrics, commands, long paths, and dense tables in notebook text when they need to remain searchable and copyable, while still allowing the imagegen visual to display them.

9. Validate and report.
   - Run `python scripts/validate_notebook.py <teaching.ipynb> --source <source.ipynb> --assets-dir artifacts/teaching_assets --manifest artifacts/teaching_manifest.json --prompt-pack artifacts/teaching_imagegen_prompts.json --research-sources artifacts/teaching_research_sources.json --report artifacts/teaching_validation.json`.
   - Optionally render with `jupyter nbconvert --to html`.
   - Execute a disposable copy with `nbclient` only when the environment is trusted and execution is requested or necessary.
   - Deliver the teaching notebook, manifest, research sources, prompt pack, validation report, and local image assets.

## Completion Contract

The conversion is complete only when:

- The original notebook remains unchanged, unless in-place editing was requested.
- The engineering code path is preserved or every functional change is disclosed.
- The selected mode and image count are justified in the manifest.
- Every major technology has a source-backed selection rationale covering fit, advantages, tradeoffs, alternatives, version context, and citations.
- Every accepted teaching image is an inspected direct-use imagegen output stored locally.
- Every Paddle logo-bearing generated image records an official reference asset and passes exact brand-fidelity inspection.
- No sensitive source content was exposed to image generation.
- The teaching notebook parses as JSON and all local image references resolve.
- Python code validation accounts for notebook magics and shell cells rather than treating them as ordinary Python.
- A validation report records passed checks, warnings, skipped checks, and remaining risks.
