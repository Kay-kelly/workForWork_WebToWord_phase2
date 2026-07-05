# Phase 3 Word Repeat R1 Checkpoint

## 1. 文件目的

本文件用來記錄 Repeat Block R1 的完成狀態，作為後續外包交接與 Phase 3 Word 功能追蹤的節點文件。

此 checkpoint 用於說明目前已完成的能力、驗證結果、仍有限制的範圍，以及下一階段建議。它不是正式 Word 報告驗收文件。

## 2. 本階段定位

目前完成的是 Word repeat block 的 R1 最小可驗證版本：

- 同一 Word table 內 repeat table row expansion。
- deidentified template smoke build 可通過。
- R1 可支援 6.3 Environmental Test / Thermal Vacuum Test 的 cycle rows 展開。

目前仍不是正式 Word 報告完成，也尚未完成正式排版驗收、多圖複雜排版、text box placeholder 等功能。

## 3. 已完成功能

目前 Phase 3 Word MVP 已完成：

- paragraph placeholder replacement。
- table cell placeholder replacement。
- header/footer placeholder replacement。
- image placeholder `{{cycle_image}}`。
- repeat block R1 table row expansion。
- dry-run checker。
- deidentified smoke build。
- scoped MVP inspect。

## 4. Repeat Block R1 支援範圍

Repeat Block R1 支援範圍如下：

- 支援同一個 Word table 內的 start/end marker。
- start marker：`{{#repeat:thermal_vacuum_cycle_block}}`。
- end marker：`{{/repeat:thermal_vacuum_cycle_block}}`。
- start/end marker 所在 rows 不輸出到 final docx。
- start/end 中間的 template rows 依 repeat data 筆數 deep copy。
- 每筆 repeat data 可替換 cycle row placeholder。
- R1 主要服務 6.3 Environmental Test / Thermal Vacuum Test 的 cycle rows。

## 5. Repeat Block R1 不支援範圍

Repeat Block R1 目前不支援：

- nested repeat。
- cross-table repeat。
- repeat block image insertion。
- text box placeholder。
- complex multi-image layout。
- merged-cell 複雜 edge case 的完整保證。
- formal report layout validation。

## 6. 驗證結果

Dry-run：

```powershell
.\.venv\Scripts\python.exe project\app\word\check_word_config.py --config project\config\word_templates\deidentified_word_report.json
```

結果：

- final result: PASS。

Deidentified smoke build：

```powershell
.\.venv\Scripts\python.exe project\app\word\smoke_build_deidentified_word.py
```

結果：

- final result: PASS。
- unresolved placeholders count: 0。
- known unsupported markers count: 0。
- repeat markers resolved: true。
- unexpected unresolved placeholders: none。

MVP pipeline inspect：

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
.\.venv\Scripts\python.exe project\app\word\inspect_word.py
```

結果：

- report_cycle_2.docx PASS。
- report_cycle_3.docx PASS。
- report_cycle_5.docx PASS。
- Summary: 3/3 passed。

## 7. Inspect 分流策略

`inspect_word.py` 預設只檢查 `report_cycle_*.docx`。

`deidentified_smoke_report.docx` 不套用舊 MVP required-text 規則。它由 `smoke_build_deidentified_word.py` 驗證，檢查重點包含 DOCX 可產生、unresolved placeholders 為 0、repeat marker 已消失，以及 demo repeat rows 已展開。

這樣可以避免不同 Word template 共用錯誤 inspect profile，造成 deidentified smoke output 被舊 MVP report 規則誤判。

## 8. 本機 Ignored Artifact / Template 策略

`project/templates/word/deidentified_report_template_repeat.docx` 是本機 ignored template，不進 repo。

`project/output/` 是 ignored artifact，不可 commit。

`deidentified_smoke_report.docx` 是 smoke output，不可 commit。

repo 只保存程式、config、spec、文件，不保存正式或疑似正式 docx。

## 9. 目前可交給外包的內容

目前可交給外包的內容包括：

- repo 程式碼。
- mapping spec。
- deidentified Word config。
- repeat block renderer design。
- Repeat R1 checkpoint。
- dry-run checker。
- smoke build script。
- local smoke test guide。

## 10. 不應交給外包的內容

不應交給外包的內容包括：

- 正式 Word template。
- 真實測試資料。
- 真實測試圖片。
- 真實 output report。
- 客戶 / 專案 / 產品 / 單位資訊。
- 未去識別化文件。

## 11. 後續建議

建議下一步優先順序：

1. 先做 contractor handoff 文件更新。
2. 再做正式 template 人工排版驗收。
3. 如需再強化 repeat block，進入 R2：錯誤處理 / diagnostics / missing_data_policy。
4. 多圖與 complex layout 獨立 phase，不要和 R2 混在一起。
5. text box placeholder 另列未來需求。

## 12. 禁止事項

本文件只是 checkpoint，不代表正式報告完成。

禁止事項：

- 不要 commit `project/output/`。
- 不要 commit ignored docx template。
- 不要把 deidentified smoke PASS 解讀成正式報告驗收完成。
- 不要直接把正式 template 交給外包。

本輪禁止修改：

- `project/app/word/build_word.py`
- `project/app/word/smoke_build_deidentified_word.py`
- `project/app/word/check_word_config.py`
- `project/app/word/inspect_word.py`
- `project/config/word_templates/deidentified_word_report.json`
- `project/app/pipeline_main.py`
- `project/app/pipelines/runner.py`
- `project/app/image/generate_image.py`
- `project/app/image/overlay_text.py`
- `project/config/image_templates/cycle_diagram.json`
- `project/output/`
