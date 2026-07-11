# Content Routing

Choose the rendering method from the teaching purpose, not from a desire to maximize image count.

## Use Imagegen

Use `imagegen` when the learner benefits from seeing several dimensions at once:

- End-to-end workflows with branches, gates, fallbacks, or feedback loops.
- Architecture and module maps with dependencies and runtime boundaries.
- Core principles that combine mechanism, inputs, transformations, and outcomes.
- Technical comparisons where visual grouping reveals tradeoffs.
- Experiment stories that connect parameters, observed behavior, and conclusions.
- Integrated project overviews that combine identity, route, evidence, and deliverables.

An imagegen visual should normally replace multiple paragraphs of explanation or unify information that would otherwise be split across several notebook sections.

## Use Tables or Inline HTML

Do not use imagegen for content that is primarily an exact, linear, or frequently updated list:

- Checklists and pass/fail gates.
- Status summaries with check or cross icons.
- Metric grids and parameter tables.
- File paths, hashes, artifact inventories, and manifests.
- Evidence lists and acceptance criteria.
- Short comparisons that fit naturally into rows and columns.
- Commands, code, schemas, or text users need to copy and search.

For content like a large title followed by several checkmarked statements and one prohibition row, use an inline HTML quality-gate panel or a Markdown table. It is more exact, accessible, searchable, and maintainable than a generated bitmap.

## Decision Test

Before planning an imagegen call, answer:

1. Does this content contain meaningful relationships beyond a list?
2. Will composition help a learner understand sequence, hierarchy, causality, dependency, or tradeoffs?
3. Can the image replace substantial prose without becoming a wall of text?
4. Will the important text remain readable at normal notebook width?

Use imagegen when answers 1-3 are yes and answer 4 can be satisfied. Otherwise use HTML, a table, or Markdown.

Technology-selection explanations usually start as a source-backed comparison table or HTML decision panel. Promote them to imagegen only when an integrated tradeoff map, ecosystem relationship, or architecture fit communicates more than rows and columns. Source citations remain in notebook text even when an imagegen infographic is used.

When imagegen is selected, prefer a project-evidence-driven atlas, flow, principle, architecture, metric, or deliverables composition. Generic illustrations without real samples, artifacts, counts, or source-locked facts do not satisfy the Paddle engineering profile.

## Content Plan Contract

Record every planned teaching element before generation:

```json
{
  "id": "quality-gate",
  "purpose": "Show exact release checks and one prohibited fallback",
  "rendering_method": "html_cards",
  "reason": "Exact linear checklist; no spatial relationship requires imagegen",
  "insertion_point": "## 质量门禁"
}
```

This routing decision belongs in `teaching_manifest.json`. Only elements with `rendering_method: imagegen` belong in the imagegen prompt pack.
