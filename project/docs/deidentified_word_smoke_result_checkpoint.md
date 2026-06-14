# Deidentified Word Smoke Result Checkpoint

## 1. 文件目的

本文件用來記錄 deidentified Word template smoke build 的目前結果與判讀方式，避免後續把目前可接受的 `WARN` 狀態誤判為 regression。

這份文件只描述目前 checkpoint 狀態，不代表正式 Word 報告已完成。

## 2. 本階段定位

目前階段不是正式 Word 報告完成，而是確認：

- 本機 ignored deidentified template 可被 smoke script 使用。
- config/template dry-run 可通過。
- `build_word` MVP 可產生 smoke DOCX。
- 目前尚未支援的功能已被列為 known unsupported。

此 checkpoint 的重點是驗證現有 MVP 對去識別化 template 的支援程度，而不是實作 repeat block renderer。

## 3. 執行指令

先檢查 config/template 對齊狀態：

```powershell
.\.venv\Scripts\python.exe project\app\word\check_word_config.py --config project\config\word_templates\deidentified_word_report.json
```

再執行 deidentified Word smoke build：

```powershell
.\.venv\Scripts\python.exe project\app\word\smoke_build_deidentified_word.py
```

## 4. 目前結果

目前結果：

- `check_word_config.py`: `PASS`
- `smoke_build_deidentified_word.py`: `WARN`
- output DOCX path: `project/output/pipeline_mvp/word/deidentified_smoke_report.docx`
- unresolved placeholders count: `24`
- known unsupported count: `24`
- unexpected unresolved placeholders: none

`project/output/` 是 ignored artifact，不可 commit。

## 5. WARN 判讀

目前 `WARN` 是可接受狀態。

原因是所有 unresolved placeholders 都屬於 known unsupported，沒有 unexpected unresolved placeholder。換句話說，目前輸出仍留下的 placeholder 都落在本階段明確尚未支援的 Word 結構或 repeat block 範圍內，不是既有 MVP 支援能力的 regression。

後續若出現 unexpected unresolved placeholder，才應視為需要調查或修正的問題。

## 6. Known Unsupported 範圍

目前 known unsupported 包含：

- repeat block marker:
  - `{{#repeat:thermal_vacuum_cycle_block}}`
  - `{{/repeat:thermal_vacuum_cycle_block}}`
- repeat block 內的 cycle placeholders。
- header/footer placeholder，例如 header 中的 `{{report_title}}`。
- text box placeholder，如果 template 中有。
- complex multi-image layout。

這些項目目前只被辨識與分類，不代表已被 renderer 支援。

## 7. 目前已驗證成功的範圍

目前已驗證：

- `deidentified_word_report.json` 可讀。
- 本機 DOCX template 存在時可被檢查。
- DOCX 可讀。
- smoke script 可呼叫既有 `build_word` 邏輯。
- output DOCX 可成功產生。
- unexpected unresolved placeholders 為 `0`。

## 8. 尚未代表完成的範圍

目前結果不代表：

- 正式 Word 報告完成。
- repeat block renderer 已完成。
- header/footer replacement 已完成。
- 正式排版驗收已完成。
- 多圖複雜排版已完成。

目前仍是 MVP smoke build checkpoint，不是正式報告交付節點。

## 9. 下一步建議

下一步仍不建議直接實作 repeat block renderer。

建議優先順序：

1. 先檢查 smoke output DOCX 的人工版面可讀性。
2. 再決定是否要先支援 header/footer placeholder。
3. repeat block renderer 之後獨立 phase 實作。
4. complex multi-image layout 不要和 repeat block 混在同一輪做。

## 10. 禁止事項

- 不要 commit `project/output/`。
- 不要 commit `project/templates/word/deidentified_report_template_repeat.docx`。
- 不要把目前 `WARN` 當成失敗，除非出現 unexpected unresolved placeholder。
- 不要為了讓 `WARN` 消失而直接大改 `build_word.py`。
- 不要本輪實作 repeat block renderer。
