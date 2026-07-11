# Imagegen Prompt Contract

Create `artifacts/teaching_imagegen_prompts.json` before final generation. Use the top-level object shown below. Each image entry must be complete enough to run without user fill-in.

## Required Fields

```json
{
  "version": 1,
  "mode": "standard",
  "images": [
    {
      "id": "data-flow",
      "title": "训练与交付数据流",
      "purpose": "Explain how data moves from input through validation and export.",
      "information_goal": "Replace the separate preprocessing, training, validation, and export explanations with one integrated visual.",
      "density": {
        "target": "moderately_high",
        "information_regions": 5,
        "text_items": 17,
        "reading_path": "left_to_right"
      },
      "required_text": ["输入数据", "预处理", "LoRA 训练", "质量门禁", "模型导出"],
      "source_locked_facts": ["Qwen3-0.6B", "learning_rate=2e-4"],
      "prompt": "Complete imagegen prompt...",
      "negative_constraints": ["no invented metrics", "no misspellings", "no extra text"],
      "output_file": "artifacts/teaching_assets/data-flow.png",
      "insertion_point": "## 训练流程",
      "status": "accepted",
      "accepted_asset_sha256": "<sha256>",
      "inspection": {
        "text_accuracy": "passed",
        "numeric_accuracy": "passed",
        "readability": "passed",
        "information_density": "passed"
      },
      "repairs": []
    }
  ]
}
```

The machine-readable contract is `schemas/imagegen-prompt-pack.schema.json`. The validator checks the completion-critical fields without requiring an external JSON Schema package.

## Prompt Pattern

```text
Use case: scientific-educational.
Asset type: final direct-use 16:9 text infographic for a Jupyter teaching notebook.
Create the complete final image directly. Render all required text inside the image with large readable typography and a clear hierarchy.

Title, exact text: <title>
Required text, exact spelling: <short labels, steps, metrics, warnings>
Source-locked technical facts that must not change: <models, frameworks, values, filenames, paths>
Purpose and information hierarchy: <what the learner should understand first, second, and third>
Information density: moderately high, with <4-7> coherent regions and <12-24> short text items. The visual should replace substantial prose while remaining readable at normal notebook width.
Visual style: <hero or light academic body style>

Negative constraints: no gibberish, no misspellings, no invented values, no fake screenshots, no browser chrome, no blank placeholders, no empty reserved panels, no lorem ipsum, no watermark, no logo, and no additional text.
```

## Prompt Rules

- Copy required text exactly from the source or approved teaching narrative.
- Do not ask imagegen to infer missing metrics or technology names.
- Do not ask it to leave blank space for later text, charts, screenshots, QR codes, or signatures.
- Keep text grouped into a small number of visually coherent blocks.
- Do not use imagegen for a linear checklist, status matrix, file inventory, parameter table, or evidence list that is better rendered as HTML or Markdown.
- Use one generation call per distinct image.
- After acceptance, record the asset SHA-256 and mark all four inspection checks as `passed`.
- During iteration, `status` may be `planned` or `regenerated`. Before final validation it must be `accepted` or `repaired`.
