# Technology Research and Selection Rationale

Teaching conversion must explain not only how the notebook works, but why its major technologies were selected and where their advantages matter.

## Identify Technologies

Inspect imports, installation commands, metadata, configuration files, model names, checkpoint formats, API calls, and export commands. Record:

- Core framework and detected version.
- Paddle ecosystem libraries such as PaddleNLP, PaddleOCR, PaddleX, PaddleFormers, PaddleScience, PaddleSeg, PaddleDetection, FastDeploy, or VisualDL.
- Model architecture and pretrained checkpoint.
- Training or adaptation method such as LoRA, quantization, distillation, or distributed training.
- Inference, export, serving, and deployment components.
- Hardware or runtime requirements that influence the choice.

Do not research every imported utility. Focus on technologies whose selection materially affects architecture, performance, compatibility, teaching value, or delivery.

## Web Research Is the Default

When web search is available, use it before writing technology-selection claims. Current versions, compatibility, supported hardware, release features, and recommended APIs are time-sensitive.

Source priority:

1. Official documentation and API reference.
2. Official GitHub repository, README, release notes, examples, and tracked issues.
3. Official Paddle tutorials, AI Studio projects, Paddle developer community, and PFCC community blog.
4. Original research papers.
5. High-quality third-party technical blogs as supplemental explanation.

Do not use a third-party blog as the sole support for a compatibility, benchmark, security, licensing, or current-version claim. Corroborate material claims with a primary source.

Useful Paddle search patterns:

```text
<technology> official documentation advantages limitations version
site:paddlepaddle.org.cn <technology> guide
site:github.com/PaddlePaddle/<repository> README release
site:aistudio.baidu.com <technology> tutorial
site:pfcc.blog <technology>
```

## Selection Explanation Contract

For every major technology, the teaching notebook should answer:

1. **Problem:** What requirement or constraint needs to be solved?
2. **Selected technology:** What component and version are used?
3. **Why it fits:** Why is it appropriate for this notebook's data, model, hardware, workflow, or delivery target?
4. **Advantages here:** Which concrete capabilities matter in this specific project?
5. **Tradeoffs:** What complexity, compatibility, performance, maintenance, or deployment constraints remain?
6. **Alternatives:** What reasonable alternatives exist, and why were they not selected for this notebook?
7. **Evidence:** Which source supports each material factual claim?

Avoid generic claims such as "fast", "easy to use", or "industry-grade" without project context and evidence. Distinguish sourced facts from an inference made from the notebook and sources.

## Research Artifact

Save `artifacts/teaching_research_sources.json` before finalizing the narrative or image prompts:

```json
{
  "version": 1,
  "researched_at": "2026-07-11",
  "web_search_used": true,
  "search_queries": ["site:paddlepaddle.org.cn PaddleFormers LoRA guide"],
  "technologies": [
    {
      "id": "paddleformers",
      "name": "PaddleFormers",
      "ecosystem": "paddle",
      "detected_version": "unknown",
      "selection_context": "Fine-tune a Paddle-native large language model with LoRA.",
      "why_selected": "It provides Paddle-native pretrained model and fine-tuning workflows that match the existing notebook stack.",
      "advantages": ["Integrates with the existing Paddle runtime", "Provides model and trainer abstractions used by the notebook"],
      "tradeoffs": ["Version and checkpoint compatibility must be verified before reuse"],
      "alternatives": [
        {"name": "PaddleNLP", "not_selected_reason": "The notebook already targets PaddleFormers-specific model APIs"}
      ],
      "sources": [
        {
          "id": "paddleformers-repo",
          "title": "PaddleFormers official repository",
          "url": "https://github.com/PaddlePaddle/PaddleFormers",
          "source_type": "official_repository",
          "is_primary": true,
          "retrieved_at": "2026-07-11",
          "claims_supported": ["Paddle-native pretrained model library"]
        }
      ]
    }
  ]
}
```

Use stable source IDs in notebook citations and image prompt entries. Include clickable Markdown links near the corresponding technology-selection explanation.

## Paddle Source Guidance

For Paddle-related technologies, use at least one official Paddle source. Prefer two independent official source types when available, such as documentation plus repository/release notes. The official Paddle documentation, PaddlePaddle GitHub organization, AI Studio, and official community material are appropriate starting points.

Version-sensitive claims must include the detected or researched version. If the notebook does not reveal a version, state `unknown` and avoid claiming that a current feature was available in the original environment.
