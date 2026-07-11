# Paddle Engineering Atlas Visual Profile

`paddle-engineering-atlas` is the default imagegen profile for Paddle engineering teaching notebooks. It produces a coordinated 16:9 image series that combines real project evidence, dense technical explanation, and clear instructional hierarchy.

## Visual Character

- Engineering evidence first, decoration second.
- High information value without a wall-of-text appearance.
- Strong Chinese title hierarchy with accurate English technical terms.
- Grid-aligned panels, thin blue borders, restrained corner radii, and explicit directional arrows.
- Real dataset samples, output artifacts, metrics, charts, filenames, and runtime facts integrated into the composition.
- One dominant teaching question per image, answered through 4-7 coherent information regions.
- Consistent series styling so all images look like one notebook package.

Do not reduce this profile to a generic blue gradient, marketing poster, abstract technology background, or a collection of decorative icons.

## Series Structure

A full series commonly contains:

1. **Dark hero:** actual project object or representative sample, KPI summary, compact dataset atlas, and end-to-end route.
2. **Dataset atlas:** real train/test/class samples, exact counts, class colors, and data-quality conclusion.
3. **Data flow:** source files, metadata, feature/model stage, predictions, evaluation artifacts, and directional arrows.
4. **Principle:** representative samples, feature-space or mechanism explanation, decision logic, and result interpretation.
5. **Runtime architecture:** project inputs, notebook/runtime, Paddle execution boundary, outputs, and cloud/local limitations.
6. **Metrics and results:** large KPI tiles, exact totals, success/failure counts, and a real confusion matrix or equivalent evidence.
7. **Validation or risk flow:** only when validation has meaningful dependencies, branches, fallback behavior, or runtime constraints. A plain checklist remains HTML/cards.
8. **Deliverables map:** only when directory relationships, packaging structure, or cloud upload flow needs spatial explanation. A flat file list remains a table.

The sequence adapts to the notebook. Do not invent a panel solely to fill a slot.

## Canvas and Grid

- Final canvas: 16:9 landscape, preferably 1920x1080 or equivalent.
- Top title zone: approximately 10-16% of image height.
- Main evidence zone: approximately 72-82%.
- Footer conclusion/source-lock zone: approximately 6-12% when needed.
- Use a 12-column mental grid, aligned panel edges, even gutters, and stable margins.
- Use 4-7 major regions. Nested regions are allowed only when the parent remains visually clear.
- Keep one dominant reading direction: left-to-right, top-to-bottom, or center-out. Use no more than two secondary branches.

## Theme

- First hero: deep navy/black background with bright blue highlights, real product/sample imagery, white text, and compact evidence panels.
- Body images: white or very light blue background with dark navy headings and blue structural lines.
- Avoid dark body images unless the subject requires it.
- Avoid glassmorphism, neon decoration, dense shadows, arbitrary gradients, and ornamental 3D elements that do not explain the system.

## Semantic Colors

Use stable meanings across the series:

- Navy/deep blue: framework, structure, headings, primary path.
- Bright blue/cyan: data movement, selected path, active process.
- Green: normal, correct, passed, train, supported.
- Red: defect, failed, blocked, incorrect.
- Orange/amber: warning, limitation, runtime caveat, review needed.
- Purple: secondary category or comparison class when needed.

Do not assign different meanings to the same color in different images.

## Evidence Inputs

Every imagegen visual must record at least one real evidence input. Prefer two or more when they support different parts of the explanation.

Evidence may include:

- Project images or dataset sample thumbnails.
- Existing charts, confusion matrices, previews, or reports.
- Project files and directory structures.
- Source-locked notebook facts such as exact counts, metrics, model names, versions, and limitations.
- Research source IDs for externally verified technical claims.
- Official Paddle brand references.

Pass relevant local images to imagegen as references. Do not ask imagegen to invent representative defect samples, confusion matrices, file trees, metric values, or product appearance when the project already contains them.

When the user supplies an approved visual exemplar or contact sheet, save a project-local reference copy, record its hash as a `project_file` evidence input, and attach it to the imagegen call for composition/style guidance. Preserve the exemplar's layout discipline and information hierarchy without copying its project-specific samples, values, filenames, or conclusions into a different notebook.

## Information Density

- Target 4-7 major information regions.
- Target roughly 12-24 short text items for a body image.
- Combine text with evidence thumbnails, arrows, diagrams, tables, and compact metric blocks.
- Prefer 1-2 short explanatory lines per region instead of paragraphs.
- Use large primary numbers and compact secondary labels.
- A learner should understand the image's main conclusion in 5 seconds and inspect supporting evidence in 30-60 seconds.
- If the image only restyles a short list, reroute it to HTML/table.
- If labels become unreadable at normal notebook width, split the teaching question across two images.

## Typography

- Use one large, direct title that states the teaching subject, not a slogan.
- Use short section labels and exact technical names.
- Keep filenames, counts, class names, model names, and metric values source-locked.
- Avoid long prose, tiny annotations, decorative letter spacing, and mixed font styles.
- Chinese and English may coexist, but the hierarchy must remain obvious.

## Acceptance Gate

Accept an image only when:

- It follows the declared 16:9 series theme and position.
- Its title is readable at notebook width.
- Real evidence is visible and materially supports the explanation.
- Counts, filenames, class names, metrics, and technical terms match the source.
- The reading path and region hierarchy are immediately understandable.
- Semantic colors remain consistent with the rest of the series.
- It contains enough supporting information to replace substantial prose.
- It is not so dense that labels or evidence thumbnails become unusable.

Record `profile_fidelity: passed`, `evidence_fidelity: passed`, and `series_consistency: passed` in the image inspection block.
