# Phase 3 MVP Status

This document summarizes the current Phase 3 MVP state after the `build_word`, Word inspection, and minimal Word template replacement work.

## Current MVP Flow

```text
Excel
-> SharedData
-> generate_image
-> overlay_text
-> build_word
-> PNG + DOCX output
```

The active entrypoint is:

```text
project/app/pipeline_main.py
```

The legacy `project/app/main.py` + `project/config/mapping.json` flow is not the current MVP path.

## How To Run

From the repository root:

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
.\.venv\Scripts\python.exe project\app\word\inspect_word.py
```

The pipeline command reads `project/data/input.xlsx`, creates shared row data, generates PNG images, overlays text, and builds one DOCX per Excel row.

The inspection command checks generated DOCX files structurally. It does not perform visual rendering.

## Current Outputs

The current sample input produces:

```text
project/output/pipeline_mvp/report_cycle_2.png
project/output/pipeline_mvp/report_cycle_3.png
project/output/pipeline_mvp/report_cycle_5.png
project/output/pipeline_mvp/word/report_cycle_2.docx
project/output/pipeline_mvp/word/report_cycle_3.docx
project/output/pipeline_mvp/word/report_cycle_5.docx
```

`project/output/` is ignored by git and should not be committed.

## Word MVP Scope

The current Word MVP supports:

- `template_path` in `project/config/word_templates/mvp_word_report.json`.
- Loading `project/templates/word/mvp_report_template.docx`.
- Paragraph placeholder replacement.
- Table-cell placeholder replacement.
- `{{cycle_image}}` replacement with the final PNG from `overlay_text`.
- Direct DOCX fallback when `template_path` is not configured.
- Minimal DOCX inspection through `project/app/word/inspect_word.py`.

The current placeholder set is intentionally small:

```text
{{report_title}}
{{record_id}}
{{project_id}}
{{test_id}}
{{batch_sequence_id}}
{{cycle_count}}
{{cycle_image}}
```

The inspection CLI checks that generated DOCX files can be opened, contain required text, do not contain unresolved `{{...}}` placeholders, and include at least one embedded image.

## Known Limitations

The current MVP does not support:

- Header/footer placeholders.
- Text-box placeholders.
- Placeholders split across multiple Word runs.
- Complex multi-image layout.
- Visual Word render validation.
- A complete production report template.

## Recommended Next Steps

Suggested next work, not yet implemented:

- Table write-value MVP.
- Multi-image insertion MVP.
- Formal Word template mapping spec.
- Real company report template integration.
- Handoff documentation for outsourcing or non-engineering stakeholders.

## Relevant Commits

Recent Phase 3 commits:

- `feat: add end-to-end build_word MVP`
- `test: add Word MVP inspection CLI`
- `feat: add minimal Word template replacement`
