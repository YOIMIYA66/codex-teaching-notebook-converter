# Visual Policy

## Primary Rule

Imagegen is the required primary path for planned teaching visuals. Generate the final text-bearing bitmap directly, including substantial exact text when the teaching design requires it.

Do not substitute locally drawn diagrams, Mermaid, SVG, PIL compositions, HTML canvas, screenshots of slides, or blank visual templates for planned imagegen teaching images.

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
- Parameter or experiment infographic.
- Training/evaluation workflow.
- Validation and risk-control gate.
- Deliverables map.

## Visual System

- Hero: 16:9, dark, high-impact, focused on the notebook's actual technical subject.
- Body diagrams: 16:9, light background, high contrast, one primary concept per image.
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

Regenerate first with fewer text blocks, larger typography, clearer hierarchy, and stricter exact-text language. A deterministic local overlay may repair a small remaining defect only after imagegen has produced and been inspected as the primary visual. Record the repair in the prompt pack and validation report.

## Asset Handling

- Save accepted outputs under `artifacts/teaching_assets/`.
- Use descriptive lowercase filenames.
- Reference project-local assets, not only a temporary generated-images location.
- Embed critical images as notebook attachments when portability requires it.
- Never send secrets, raw personal records, confidential code, or identifying local paths to image generation.
