---
name: teaching-notebook-converter
description: Convert engineering Jupyter notebooks into polished Codex-only teaching notebooks. Use when Codex needs to turn a runnable or engineering-focused .ipynb into a tutorial notebook with narrative structure, 6-9 direct imagegen-generated text infographics, complete per-image prompts, inline HTML card layouts, learner-friendly explanations, validation gates, and final notebook QA.
---

# Teaching Notebook Converter

This is a Codex-only workflow for converting an engineering notebook into a visually polished teaching notebook without breaking the original runnable logic.

## Core Rule

Preserve the engineering notebook's executable path. Add teaching value through Markdown, images, inline HTML cards, visual summaries, and validation cells. Do not rewrite training or inference logic unless the user explicitly asks for a functional change.

## Workflow

1. Inspect the notebook before editing.
   - Read the table of contents implied by Markdown headings.
   - Count code and Markdown cells.
   - Identify setup, data, training, evaluation, export, and packaging stages.
   - Locate existing artifacts, summaries, logs, model outputs, and validation results.

2. Create a teaching copy.
   - Keep the original engineering notebook unchanged unless the user explicitly wants in-place edits.
   - Name the teaching version clearly, such as `*.teaching.ipynb`.
   - Back up the teaching notebook before large visual edits.

3. Build a narrative front matter.
   - Start with a 16:9 horizontal hero poster.
   - Add a short project positioning section.
   - Add outcome cards with final metrics.
   - Add a learner route map before deep technical cells.
   - Add a safety or limitations note when the notebook involves medical, legal, finance, or other high-stakes domains.

4. Plan a 6-9 imagegen visual set before generating images.
   - Target 8 images by default. Generate no fewer than 6 usable images unless the user explicitly asks for fewer or the notebook is too small to justify 6.
   - Generate up to 9 images when the notebook has enough distinct stages, technical choices, evaluation results, or delivery artifacts.
   - Treat 4 images as insufficient for a full teaching conversion.
   - Include these required image types when applicable:
     - **Cover / hero:** show the project identity, core technical route, standout features, final deliverables, and why the project is worth studying.
     - **Principle diagram:** explain the central technical principle, such as LoRA, RAG, model fine-tuning, graph retrieval, validation, or export logic.
     - **Data flow diagram:** show input data, preprocessing, training/evaluation, inference, validation, export, and user-facing artifacts.
     - **Architecture / module map:** show system components, dependencies, and runtime boundaries.
     - **Technical selection infographic:** explain why key models, frameworks, databases, or algorithms were chosen.
     - **Parameter / experiment infographic:** show important hyperparameters, dataset counts, metrics, or ablation conclusions using exact values from the notebook or source docs.
     - **Quality gate / risk control:** show validation checks, failure modes, fallback behavior, and high-stakes caveats.
     - **Deliverables map:** show notebook, model files, reports, package outputs, manifests, and where each artifact lives.

5. Write a complete imagegen prompt pack before calling imagegen.
   - For every image/page, write:
     - Page/image title.
     - Required on-image text, copied exactly as it must appear.
     - Complete imagegen prompt ready to paste and run.
     - Technical names, numeric constraints, metric values, filenames, paths, and any source-locked facts that imagegen must not invent or modify.
     - Negative constraints that ban gibberish, misspellings, fake screenshots, empty placeholders, blank reserved areas, lorem ipsum, random UI chrome, watermarks, logos, and extra text.
     - Target filename under `artifacts/teaching_assets/` and intended notebook insertion point.
   - Do not write schema-only or meta prompts that still require the user to fill in details.
   - Do not ask imagegen to leave blank areas for later text, screenshots, charts, signatures, QR codes, or manual composition.
   - Do not let imagegen complete missing data. If a metric, title, number, or technology name is unknown, inspect source artifacts or mark the issue before generation.

6. Use imagegen for direct-use bitmap teaching visuals.
   - Use a dark, high-impact poster only for the first screen.
   - Use light-background visuals for body sections so they blend with notebook pages.
   - Require imagegen to generate the final usable image with the required text already inside the image.
   - Do not default to a "generate blank background, then locally composite all text" workflow.
   - Use local text overlay only as a repair fallback when imagegen text is materially wrong, too small, misspelled, or when exact tabular text must be deterministic.
   - Generate visuals for concepts that are hard to explain in text: architecture, LoRA principle, data flow, validation gate, export pipeline, and deliverables.
   - Copy generated images from the Codex generated-images directory into a project asset folder such as `artifacts/teaching_assets/`.
   - For cloud portability, embed important images as notebook attachments when practical; also keep project-local PNG copies for reuse.

7. Add inline HTML cards for scanability.
   - Prefer inline `style="..."` attributes because many cloud notebooks strip or ignore global `<style>` blocks.
   - Use cards for outcomes, stage summaries, warnings, file lists, and quality gates.
   - Keep cards readable in static notebook renderers: light backgrounds, visible borders, moderate radius, and short text.
   - Avoid relying on JavaScript, external CSS, custom fonts, or remote assets.

8. Explain each engineering stage.
   - Before code cells, add what the stage does, why it exists, inputs, outputs, and failure modes.
   - After important code cells, add how to read outputs and what a good result looks like.
   - Convert opaque logs into concise teaching notes.

9. Add validation and delivery sections.
   - Show quality gates before export.
   - Explain collapsed output detection, fallback logic, and deployment caveats when present.
   - Include manifest, zip, export, and artifact paths in a deliverables card.
   - Never claim a model is production-ready just because export succeeds.

10. Validate the notebook.
   - Parse notebook JSON.
   - Compile code cells with `ast.parse` when the code is Python.
   - Confirm required images are present or embedded.
   - Confirm no global `<style>` dependency remains if the target cloud environment failed to render it.
   - Optionally run `jupyter nbconvert --to html` to preview static rendering.

## Visual System

Use this visual hierarchy:

- **Hero poster:** 16:9, dark or premium visual, focused on the notebook's true technical subject. It may be more dramatic and promotional than the rest of the notebook.
- **Body diagrams:** 16:9, white or light-blue background, one concept per image, optimized for reading in a notebook and screenshots.
- **Cards:** inline HTML, small blocks, one idea per card.
- **Tables:** metrics, file paths, parameters, comparisons.
- **Code blocks:** exact commands, schemas, prompt templates, expected output format.

Default imagegen policy:

- Generate 6-9 text-bearing infographics directly with imagegen when the user asks for teaching images, process charts, parameter cards, comparison panels, or overview posters.
- Put exact required text in the prompt. Use short text blocks, large typography, and "no extra text" constraints.
- Prefer direct-output images: the accepted PNG should be usable in the notebook immediately, without later blank filling or manual text composition.
- For multilingual or Chinese text, inspect whether the generated words are accurate enough before inserting the asset. If text quality is poor, regenerate once with fewer words and larger labels.
- Keep a project copy of every accepted imagegen output under `artifacts/teaching_assets/`; never reference only the default Codex generated-images path.
- Prefer dark hero + light body images: dark first screen for project identity, light diagrams later for readability.

Suggested teaching images:

- Project overview hero / cover
- Core principle diagram
- Data flow diagram
- Architecture / module map
- Why this framework / dataset / model
- Parameter-setting infographic
- Technical selection infographic
- Training and evaluation workflow
- Inference validation and export gate
- Deliverables map

For a full notebook, choose 6-9 from this list and explain why each image exists. A typical complete set is: hero, principle diagram, data flow, architecture map, technical selection, parameters/experiments, validation gate, deliverables map.

## Per-Image Prompt Contract

For each planned image, write a block like this before calling imagegen:

```text
Image <number>: <short title>
Purpose: <why this image belongs in the teaching notebook>
Must include exact on-image text:
- <title text>
- <step/card/metric text>
- <warning or output text>
Technical and numeric constraints:
- <technology names, model names, dataset counts, metrics, filenames, paths, or exact values>
Complete imagegen prompt:
<one complete prompt that can be pasted directly into imagegen>
Negative constraints:
No gibberish text, no misspellings, no invented numbers, no fake screenshots, no browser chrome, no blank placeholders, no empty reserved panels, no lorem ipsum, no watermark, no logo, no extra text beyond the required text.
Output file: artifacts/teaching_assets/<descriptive-name>.png
Notebook insertion point: <section heading or cell position>
```

If a generated image violates required text or numeric constraints, regenerate with fewer words, larger typography, and stricter "exact text only" phrasing. If it still fails, use a deterministic local overlay only for the broken text and clearly note that it is a repair fallback.

Imagegen prompt patterns:

```text
Use case: scientific-educational. Asset type: 16:9 Chinese text infographic for a Jupyter teaching notebook.
Create the final usable image directly. Use exact Chinese text, large readable typography, no extra text.
Title: <exact title>
Cards/steps: <exact short labels and bullet text>
Technical facts and numbers that must not change: <exact names and values>
Visual style: light blue-white academic slide, navy headings, cyan accents, amber warning accents, no logos, no watermark.
Negative constraints: no gibberish, no misspellings, no fake screenshots, no blank placeholders, no invented metrics, no lorem ipsum.
```

For a hero:

```text
Use case: scientific-educational. Asset type: 16:9 Chinese teaching notebook hero cover with exact large text.
Main focus: <technical subject, not the downstream demo>.
Exact title text: <title>
Must show: project highlights, core technical route, main outputs, and standout features.
Visual composition: dark navy premium engineering poster, model architecture, pipeline, checkpoint artifacts, polished cover-worthy composition.
Negative constraints: no extra text, no fake screenshot, no blank placeholder, no logo, no watermark.
```

## Inline Card Pattern

Use inline HTML like this inside Markdown cells:

```html
<div style="display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:12px;margin:12px 0;">
  <div style="padding:12px 14px;border:1px solid #d9e2f2;border-radius:12px;background:#f7fbff;">
    <b>Step 1</b><br/>数据准备
  </div>
  <div style="padding:12px 14px;border:1px solid #d9e2f2;border-radius:12px;background:#f7fbff;">
    <b>Step 2</b><br/>LoRA 训练
  </div>
  <div style="padding:12px 14px;border:1px solid #d9e2f2;border-radius:12px;background:#fff8ed;">
    <b>风险提示</b><br/>部署时保留 fallback 逻辑
  </div>
</div>
```

How it works:

- Outer `<div>` is the layout container.
- `display:grid` or `display:flex` controls arrangement.
- `gap` controls spacing between cards.
- `padding` creates breathing room inside cards.
- `border` defines the card outline.
- `border-radius` softens corners.
- `background` creates visual grouping.
- `margin` separates the card group from surrounding Markdown.

Use inline styles instead of global CSS when cloud notebook rendering is uncertain.

## Notebook Editing Notes

- Use structured notebook APIs or JSON parsing for `.ipynb`; do not edit raw notebook text casually.
- Keep image paths relative when using project-local files, such as `artifacts/teaching_assets/hero.png`.
- Prefer attachments for must-render images in shared notebooks.
- Keep generated image files outside the default Codex generated-images folder before referencing them from the notebook.
- Keep the image set purposeful but complete: a polished teaching notebook usually needs 6-9 direct-use visuals, not only one hero plus a few body visuals.

## Quality Checklist

Before finishing, verify:

- The first screen communicates the project purpose visually.
- The image plan contains 6-9 images, or a documented user/source constraint explains why fewer were used.
- Cover, principle diagram, and data flow diagram are present when the source notebook supports them.
- Every image/page has required text, a complete imagegen prompt, technical/numeric constraints, negative constraints, output filename, and insertion point.
- Accepted images are direct-use outputs without blank placeholders or missing text regions.
- The notebook has a clear route map.
- Each major code stage has a teaching explanation.
- Metrics and final outcomes are visible near the top.
- Images render in notebook preview.
- Inline card styles render without global CSS.
- The original engineering workflow remains runnable.
- High-stakes caveats are visible when relevant.
