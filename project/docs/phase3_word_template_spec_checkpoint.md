# Phase 3 Word Template Spec Checkpoint

## 1. 本階段定位

本階段不是正式 Word 報告完成，也不是完整 Word report engine 完成。

目前完成的是 Word template spec / dry-run checker 階段，重點是建立後續正式套版前的安全基礎：

- 去識別化 Word template 對接策略。
- mapping spec。
- 本機 smoke test config。
- dry-run checker。
- 本機使用說明。
- DOCX 不進 repo 的保守策略。

換句話說，目前已經可以安全檢查本機 template 與 config 是否大致對齊，但尚未宣稱真實報告版型、repeat block renderer 或正式排版驗收已完成。

## 2. 已完成項目

本階段已完成並納入 repo 的項目：

- `project/config/word_templates/deidentified_report_mapping.example.json`
- `project/config/word_templates/deidentified_word_report.json`
- `project/docs/word_template_mapping_spec.md`
- `project/docs/word_template_local_smoke_test.md`
- `project/app/word/check_word_config.py`
- `.gitignore` 已忽略 `project/templates/word/deidentified_report_template_repeat.docx`

## 3. 本機未追蹤檔案

`project/templates/word/deidentified_report_template_repeat.docx` 是本機 ignored 檔案。

此檔案：

- 不進 repo。
- 不應 commit。
- 由開發者自行放置到指定路徑。
- 可用 `check_word_config.py` 檢查是否存在，以及 template placeholder 是否與 config 大致對齊。

這個策略的目的，是即使 template 已去識別化，也先保守避免把 DOCX artifact 納入版本庫。

## 4. 已支援範圍

目前 MVP 已支援：

- paragraph placeholder replacement。
- table cell placeholder replacement。
- image placeholder `{{cycle_image}}`。
- output DOCX inspect。
- template/config dry-run check。

其中 `check_word_config.py` 只做 dry-run 檢查，不產生 Word，不修改 template，也不寫入 `project/output/`。

## 5. 尚未支援範圍

目前尚未支援：

- repeat block rendering。
- repeat table row duplication。
- header/footer placeholder。
- text box placeholder。
- complex multi-image layout。
- formal report layout validation。

尤其 6.3 Environmental Test / Thermal Vacuum Test 的 repeat block 目前只是 spec marker，不代表 `build_word.py` 已經能複製 Word table rows。

## 6. 建議驗證指令

檢查本機 ignored DOCX 是否存在：

```powershell
Test-Path project\templates\word\deidentified_report_template_repeat.docx
```

執行本機 template/config dry-run：

```powershell
.\.venv\Scripts\python.exe project\app\word\check_word_config.py --config project\config\word_templates\deidentified_word_report.json
```

執行既有 MVP pipeline smoke test：

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
```

檢查 pipeline 產生的 DOCX output：

```powershell
.\.venv\Scripts\python.exe project\app\word\inspect_word.py
```

注意：`pipeline_main.py` 會重寫 `project/output/` artifact。`project/output/` 必須維持 ignored，不可 commit。

## 7. 建議下一步

下一步不建議直接實作 repeat block renderer。

建議先做：

- deidentified template pipeline smoke test。
- 檢查目前 `build_word.py` 對新 template 的 placeholder 支援程度。
- 確認一般 paragraph / table cell / `{{cycle_image}}` 的行為與限制。

repeat block renderer 建議之後獨立 phase 實作，避免和 template 對接、dry-run checker、pipeline smoke test 混在同一個變更中。

## 8. 建議 tag

Suggested tag:

```text
v0.3.0-word-template-spec
```
