# project/

`project/` contains the active MVP pipeline implementation, configs, input data, assets, templates, and ignored runtime outputs.

## Active Entry Point

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
```

Then inspect the generated Word files:

```powershell
.\.venv\Scripts\python.exe project\app\word\inspect_word.py
```

## Current MVP Flow

```text
Excel
-> SharedData
-> generate_image
-> overlay_text
-> build_word
-> PNG + DOCX output
```

## Important Files

- `app/pipeline_main.py`: active pipeline entrypoint.
- `app/pipelines/runner.py`: step runner for `generate_image`, `overlay_text`, and `build_word`.
- `app/image/generate_image.py`: cycle diagram image generation.
- `app/image/overlay_text.py`: final text overlay on generated PNG.
- `app/word/build_word.py`: DOCX generation and template placeholder replacement.
- `app/word/inspect_word.py`: minimal DOCX inspection CLI.
- `app/word/create_mvp_template.py`: regenerates the minimal DOCX template.
- `config/pipelines/mvp_image_pipeline.json`: active pipeline config.
- `config/image_templates/cycle_diagram.json`: image template config.
- `config/word_templates/mvp_word_report.json`: Word MVP config.
- `templates/word/mvp_report_template.docx`: minimal Word template.

## Current Outputs

The sample input currently produces:

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

The current Word MVP supports `template_path`, paragraph placeholder replacement, table-cell placeholder replacement, `{{cycle_image}}` image insertion, and direct DOCX fallback when no `template_path` is configured.

Known limitations remain: no header/footer placeholders, no text-box placeholders, no cross-run placeholder handling, no complex multi-image layout, and no visual render validation.
