# Visual Policy

## Primary Rule

Imagegen is the required primary path for planned teaching visuals. Generate the final text-bearing bitmap directly, including substantial exact text when the teaching design requires it.

Do not substitute locally drawn diagrams, Mermaid, SVG, PIL compositions, HTML canvas, screenshots of slides, or blank visual templates for planned imagegen teaching images.

Imagegen is not required for every visual-looking section. Simple checklists, status rows, exact evidence matrices, metric grids, parameter tables, hashes, paths, and deliverable inventories should use Markdown tables or inline HTML cards. See `content-routing.md`.

## Image Counts

- `quick`: 0-2 images.
- `standard`: 3-5 images.
- `full`: 6-9 images, default target 8.

Every image must explain a distinct idea. A full conversion commonly uses:

- Project overview hero.
- Core principle diagram.
- Data flow diagram.
- Architecture or module map.
- Technical selection infographic.
- Parameter or experiment infographic when relationships or conclusions matter; otherwise use a table.
- Training/evaluation workflow.
- Validation and risk-control flow when it contains branches, fallback logic, or dependencies; otherwise use HTML cards.
- Deliverables map when artifact relationships or lifecycle matter; otherwise use a table or file inventory.

## Visual System

- Hero: 16:9, dark, high-impact, focused on the notebook's actual technical subject.
- Body diagrams: 16:9, light background, high contrast, one primary concept per image.
- Use moderately high information density. A body image should normally contain 4-7 coherent information regions and roughly 12-24 short text items, depending on language and visual complexity.
- Prefer compact labels, short evidence statements, and grouped annotations over paragraph text. Most Chinese text blocks should stay within about 8-24 characters; use longer text only when the layout clearly supports it.
- Each body image should communicate a complete teaching unit and replace substantial prose, not merely decorate one paragraph.
- Keep one dominant reading path, no more than two secondary paths, and enough whitespace to separate groups.
- Use short, large text blocks even when the overall image contains substantial text.
- Keep technology names, numeric values, metrics, filenames, and paths exactly source-locked.
- Ban fake screenshots, browser chrome, placeholder panels, invented data, logos, and watermarks.

## Acceptance Gate

Inspect each generated image before insertion. Reject or regenerate when:

- Required text is missing, misspelled, unreadable, or materially changed.
- A number, metric, filename, path, model name, or framework name differs from the source.
- Extra text changes the meaning.
- The visual contains empty reserved areas or fake interface elements.
- The image is too dense to read at normal notebook width.
- The image is so sparse that a table, card group, or short Markdown section would communicate the same information more precisely.

When too dense, regenerate with fewer groups, shorter labels, larger typography, and clearer hierarchy. When too sparse or list-like, reroute the content to HTML or a table instead of regenerating another bitmap. A deterministic local overlay may repair a small remaining defect only after imagegen has produced and been inspected as the primary visual. Record the repair in the prompt pack and validation report.

## Asset Handling

- Save accepted outputs under `artifacts/teaching_assets/`.
- Use descriptive lowercase filenames.
- Reference project-local assets, not only a temporary generated-images location.
- Embed critical images as notebook attachments when portability requires it.
- Never send secrets, raw personal records, confidential code, or identifying local paths to image generation.
