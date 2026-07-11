# Visual-First Compression

High-density imagegen visuals are primary teaching explanations, not decoration placed beside an unchanged wall of text.

## Goal

For sections assigned to imagegen, reduce narrative Markdown by roughly 40-65% compared with a full text-first explanation. The image should combine concepts, evidence, relationships, and conclusions that would otherwise require several paragraphs or repeated bullet lists.

Do not optimize for maximum reduction. Preserve text that must remain searchable, copyable, accessible, legally or operationally important, or precisely cited.

## Select Compression Candidates

A topic is a strong visual-compression candidate when it contains at least three related learning points and one or more of:

- Sequence, branching, feedback, fallback, or validation flow.
- Component dependencies or runtime boundaries.
- Several classes, samples, metrics, or experiment outcomes that need comparison.
- A mechanism plus inputs, decisions, and outputs.
- A technical choice plus evidence, advantages, tradeoffs, and alternatives.
- A deliverable lifecycle or directory relationship.

A short exact list, command sequence, parameter table, or pass/fail checklist remains HTML/Markdown unless meaningful relationships justify imagegen.

## Prose-Replacement Contract

Before generation, each prompt-pack image records:

```json
{
  "prose_replacement": {
    "sections_replaced": ["数据组成", "训练/测试划分", "类别分布"],
    "learning_points": [
      "28 张图片如何划分为 train 16 和 test 12",
      "4 个类别如何映射到真实样本",
      "全量 Smoke 数据为什么可以完整核验"
    ],
    "estimated_replaced_characters": 520,
    "replacement_ratio_target": 0.55,
    "duplication_policy": "summary_only",
    "retained_accessibility_summary": "该图展示 28 张全量数据的类别、训练测试划分和核验结论。",
    "retained_copyable_items": ["数据路径", "精确类别计数", "来源链接"]
  }
}
```

Target at least two combined sections, three learning points, and approximately 200 or more replaced characters for each body image. Split an image when readability would otherwise be compromised.

## After Image Insertion

Keep immediately around the image:

- A direct 1-2 sentence orientation or takeaway.
- A concise accessibility summary that communicates the main conclusion without reproducing every visual detail.
- Source links and research citations.
- Exact commands, code, parameters, paths, filenames, hashes, and tabular values users may need to copy.
- Safety, legal, operational, or high-stakes caveats.
- Any fact that cannot be read reliably at normal notebook width.

Remove or shorten:

- Paragraphs that narrate the same flow already shown by arrows and labeled stages.
- Bullet lists that repeat labels already visible in the image.
- Separate mini-sections that the image intentionally combines into one teaching unit.
- Decorative introductions and repeated conclusions.
- Redundant descriptions of metrics already shown through exact KPI blocks and charts.

## Duplication Audit

Read the image and the surrounding Markdown together. Revise when:

- The notebook can lose the image without losing any explanation, indicating the image is merely decorative.
- The same sequence, labels, metrics, or conclusions appear in full both inside and below the image.
- The image requires several long paragraphs to explain how to read it.
- Removing prose also removes citations, copyable facts, caveats, or accessibility.

The desired result is layered communication: fast understanding from the image, exact retrieval from compact notebook text, and deeper implementation detail from code cells.

## Accessibility

Do not make the notebook image-only. Keep concise alt text or an adjacent accessibility summary. For dense figures, summarize the primary conclusion, reading direction, major stages, and critical exception rather than transcribing every label.

## Completion Gate

For every accepted image, confirm:

- It replaces substantial prose or several fragmented teaching sections.
- Its surrounding text uses `summary_only` duplication policy.
- Retained text includes citations and copyable facts where applicable.
- Accessibility remains adequate.
- The visualized section is shorter and easier to scan than a text-first equivalent.
