---
name: teaching-notebook-converter
description: Convert engineering Jupyter notebooks into polished Codex-only teaching notebooks. Use when Codex needs to turn a runnable or engineering-focused .ipynb into a tutorial notebook with narrative structure, imagegen-generated visuals, inline HTML card layouts, learner-friendly explanations, validation gates, and final notebook QA.
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

4. Use imagegen for bitmap teaching visuals.
   - Use a dark, high-impact poster only for the first screen.
   - Use light-background visuals for body sections so they blend with notebook pages.
   - Generate visuals for concepts that are hard to explain in text: architecture, LoRA principle, data flow, validation gate, export pipeline, and deliverables.
   - Copy generated images from the Codex generated-images directory into a project asset folder such as `artifacts/teaching_assets/`.
   - For cloud portability, embed important images as notebook attachments when practical; also keep project-local PNG copies for reuse.

5. Add inline HTML cards for scanability.
   - Prefer inline `style="..."` attributes because many cloud notebooks strip or ignore global `<style>` blocks.
   - Use cards for outcomes, stage summaries, warnings, file lists, and quality gates.
   - Keep cards readable in static notebook renderers: light backgrounds, visible borders, moderate radius, and short text.
   - Avoid relying on JavaScript, external CSS, custom fonts, or remote assets.

6. Explain each engineering stage.
   - Before code cells, add what the stage does, why it exists, inputs, outputs, and failure modes.
   - After important code cells, add how to read outputs and what a good result looks like.
   - Convert opaque logs into concise teaching notes.

7. Add validation and delivery sections.
   - Show quality gates before export.
   - Explain collapsed output detection, fallback logic, and deployment caveats when present.
   - Include manifest, zip, export, and artifact paths in a deliverables card.
   - Never claim a model is production-ready just because export succeeds.

8. Validate the notebook.
   - Parse notebook JSON.
   - Compile code cells with `ast.parse` when the code is Python.
   - Confirm required images are present or embedded.
   - Confirm no global `<style>` dependency remains if the target cloud environment failed to render it.
   - Optionally run `jupyter nbconvert --to html` to preview static rendering.

## Visual System

Use this visual hierarchy:

- **Hero poster:** 16:9, dark or premium visual, project title, pipeline, outcomes, product list.
- **Body diagrams:** 16:9, white or light-blue background, one concept per image.
- **Cards:** inline HTML, small blocks, one idea per card.
- **Tables:** metrics, file paths, parameters, comparisons.
- **Code blocks:** exact commands, schemas, prompt templates, expected output format.

Suggested teaching images:

- Project overview hero
- Why this framework / dataset / model
- End-to-end workflow
- LoRA principle
- Inference validation and export gate
- Deliverables map

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
- Avoid oversized image batches; a polished teaching notebook usually needs one hero image plus three to five body visuals.

## Quality Checklist

Before finishing, verify:

- The first screen communicates the project purpose visually.
- The notebook has a clear route map.
- Each major code stage has a teaching explanation.
- Metrics and final outcomes are visible near the top.
- Images render in notebook preview.
- Inline card styles render without global CSS.
- The original engineering workflow remains runnable.
- High-stakes caveats are visible when relevant.
