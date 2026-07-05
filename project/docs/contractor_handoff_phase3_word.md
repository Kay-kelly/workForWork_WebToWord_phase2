# Phase 3 Word Contractor Handoff

## 1. 文件目的

本文件用於 Phase 3 Word 報告自動化外包交接，目標是讓外包理解目前已完成範圍、未完成範圍、不可接觸資訊、驗證方式與後續工作。

本文件不包含正式 Word template、真實測試資料、真實圖片或正式 output report。外包應以 repo 內程式、非機密 config、去識別化範例與 smoke test 文件作為技術接手依據。

## 2. 專案一句話定位

WebToWord / BakeOutPic 是 template/config-driven 的報告自動化系統：

```text
Excel / JSON
-> Project 資料規則
-> SharedData
-> generate_image
-> overlay_text
-> build_word
-> PNG + DOCX output
```

核心設計是用 config 與 template 控制資料、圖片與 Word 報告輸出，避免把正式報告邏輯硬寫在單一程式流程中。

## 3. 目前已完成的核心流程

目前已完成：

- Excel / SharedData / generate_image / overlay_text / build_word。
- PNG output。
- DOCX output。
- MVP pipeline 可跑通。
- Word template replacement 已接入。
- deidentified Word smoke build 已可 PASS。

目前已能產生 MVP 圖片與 Word 報告，也能用去識別化 Word template 驗證 Word placeholder、圖片 placeholder 與 repeat row expansion。

## 4. 目前主要檔案

程式：

- `project/app/pipeline_main.py`
- `project/app/pipelines/runner.py`
- `project/app/pipelines/config_loader.py`
- `project/app/word/build_word.py`
- `project/app/word/check_word_config.py`
- `project/app/word/smoke_build_deidentified_word.py`
- `project/app/word/inspect_word.py`

Config：

- `project/config/pipelines/mvp_image_pipeline.json`
- `project/config/word_templates/mvp_word_report.json`
- `project/config/word_templates/deidentified_word_report.json`
- `project/config/word_templates/deidentified_report_mapping.example.json`

文件：

- `project/docs/word_template_mapping_spec.md`
- `project/docs/word_template_local_smoke_test.md`
- `project/docs/word_repeat_block_renderer_design.md`
- `project/docs/phase3_word_template_spec_checkpoint.md`
- `project/docs/deidentified_word_smoke_result_checkpoint.md`
- `project/docs/phase3_word_repeat_r1_checkpoint.md`

Template：

- `project/templates/word/mvp_report_template.docx`
- `project/templates/word/deidentified_report_template_repeat.docx`

`project/templates/word/deidentified_report_template_repeat.docx` 是本機 ignored template，不進 repo，也不一定會交給外包。是否提供去識別化 template，需由業主確認。

## 5. Word 目前已支援功能

目前 Word 自動化已支援：

- paragraph placeholder replacement。
- table cell placeholder replacement。
- header/footer placeholder replacement。
- image placeholder `{{cycle_image}}`。
- Repeat Block R1 table row expansion。
- scoped MVP inspect。
- config/template dry-run check。
- deidentified smoke build。

## 6. Repeat Block R1 說明

Repeat Block R1 支援同一 Word table 內 repeat row expansion。

目前 marker：

- start marker：`{{#repeat:thermal_vacuum_cycle_block}}`
- end marker：`{{/repeat:thermal_vacuum_cycle_block}}`

R1 行為：

- start/end marker 所在 rows 不輸出。
- start/end 中間 rows 會依 `shared_data.thermal_cycles` 或 config repeat source 展開。
- 展開時會 deep copy template rows。
- 每筆 repeat data 可替換 cycle row placeholder。
- 主要服務 6.3 Environmental Test / Thermal Vacuum Test 的 cycle rows。

## 7. 目前尚未支援 / 不保證範圍

目前尚未支援或不保證：

- nested repeat。
- cross-table repeat。
- repeat block image insertion。
- text box placeholder。
- complex multi-image layout。
- complex merged-cell edge cases 的完整保證。
- formal report layout validation。
- 正式 Word template 完整驗收。
- 真實資料端到端驗收。
- Web UI。

## 8. 驗證方式

### A. Word Config Dry-Run

```powershell
.\.venv\Scripts\python.exe project\app\word\check_word_config.py --config project\config\word_templates\deidentified_word_report.json
```

預期：

- final result: PASS。

### B. Deidentified Word Smoke Build

```powershell
.\.venv\Scripts\python.exe project\app\word\smoke_build_deidentified_word.py
```

預期：

- final result: PASS。
- unresolved placeholders count: 0。
- repeat markers resolved: true。
- unexpected unresolved placeholders: none。

### C. MVP Pipeline + Inspect

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
.\.venv\Scripts\python.exe project\app\word\inspect_word.py
```

預期：

- report_cycle_2.docx PASS。
- report_cycle_3.docx PASS。
- report_cycle_5.docx PASS。
- Summary: 3/3 passed。

注意事項：

- `pipeline_main.py` 會重寫 `project/output/`。
- `project/output/` 不可 commit。
- `deidentified_smoke_report.docx` 是 ignored smoke artifact，不可 commit。

## 9. 外包可以拿到的內容

外包可以拿到：

- repo 程式碼。
- 非機密 config。
- mapping spec。
- deidentified mapping example。
- dry-run checker。
- smoke build script。
- 本機 smoke test guide。
- repeat block renderer design。
- Repeat R1 checkpoint。
- sample / demo output 說明。
- 去識別化 template，如果業主確認可提供。

## 10. 外包不可以拿到的內容

外包不可以拿到：

- 正式 Word template。
- 未去識別化 Word template。
- 真實測試資料。
- 真實測試圖片。
- 真實 output report。
- 客戶名稱。
- 專案名稱。
- 產品型號。
- 儀器序號。
- 文件編號。
- 公司內部流程與未公開 SOP。
- 任何可反推出正式任務或客戶的資料。

## 11. 建議外包工作項目

Priority 1：正式 Word template 導入協助，但只能透過去識別化 template 或業主本機配合驗收。

Priority 2：Repeat Block R2 強化。

- `missing_data_policy`。
- diagnostics。
- 更完整錯誤訊息。
- empty repeat source policy。

Priority 3：正式排版驗收輔助。

- 頁首頁尾。
- 表格排版。
- 圖片尺寸。
- caption。
- spacing。
- page break。

Priority 4：多圖插入與圖片順序。

- 多個 image placeholder。
- 缺圖 policy。
- 圖片尺寸 config。
- 圖片順序 config。

Priority 5：未來 Web UI / 使用者介面。

## 12. 建議不要外包或暫緩的項目

建議不要外包或暫緩：

- 直接處理正式機密 template。
- 一次重寫整個 pipeline。
- 同時做 repeat block、多圖、Web UI。
- 在沒有 smoke test 的情況下大改 `build_word.py`。
- 將 `project/output/` 納入 git。
- 將正式 docx 納入 git。

## 13. 外包驗收標準

最小驗收條件：

- 現有 MVP pipeline 仍 PASS。
- dry-run PASS。
- deidentified smoke build PASS。
- repeat markers 不殘留。
- unexpected unresolved placeholders 為 0。
- output 不進 git。
- 正式 template 不進 git。
- 不修改 image geometry / marker / guide / anchor 邏輯。
- 不破壞 `generate_image.py`、`overlay_text.py`、`cycle_diagram.json`。

## 14. Git / Commit 規則

外包每次修改前應確認：

```powershell
git status
```

規則：

- 每輪小改、小 commit。
- 不要 commit `project/output/`。
- 不要 commit ignored docx。
- 修改後要提供 modified files、diff stat、測試結果、commit message。
- commit message 使用英文。

## 15. 下一步建議

目前最適合的下一步：

- 先停止新增功能。
- 用此 handoff 文件找外包或詢價。
- 若要內部繼續，優先做正式 template 人工排版驗收。
- 技術上下一階段才是 Repeat R2 或多圖插入。

本輪禁止修改：

- `project/app/word/build_word.py`
- `project/app/word/check_word_config.py`
- `project/app/word/smoke_build_deidentified_word.py`
- `project/app/word/inspect_word.py`
- `project/config/word_templates/deidentified_word_report.json`
- `project/app/pipeline_main.py`
- `project/app/pipelines/runner.py`
- `project/app/image/generate_image.py`
- `project/app/image/overlay_text.py`
- `project/config/image_templates/cycle_diagram.json`
- `project/output/`
