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
- `smoke_build_deidentified_word.py`: `PASS`
- output DOCX path: `project/output/pipeline_mvp/word/deidentified_smoke_report.docx`
- unresolved placeholders count: `0`
- known unsupported count: `0`
- repeat markers resolved: true
- unexpected unresolved placeholders: none

`project/output/` 是 ignored artifact，不可 commit。

## 5. WARN 判讀

R1 後目前 smoke build 預期為 `PASS`。

原因是 repeat table row expansion 已支援 6.3 thermal vacuum cycle block，output DOCX 不應再殘留 repeat start/end marker 或 repeat block 內的 cycle placeholders。

後續若出現 unresolved placeholder 或 repeat marker 殘留，應視為需要調查或修正的問題。

## 6. Known Unsupported 範圍

目前 known unsupported 不包含 R1 repeat table row block。

尚未支援的範圍仍包含：

- text box placeholder，如果 template 中有。
- complex multi-image layout。

R1 後，header/footer 內的一般文字 placeholder replacement 已支援，6.3 thermal vacuum repeat table row expansion 也已支援。repeat start/end marker 與 repeat block 內 sample cycle placeholders 預期不再殘留。

## 7. 目前已驗證成功的範圍

目前已驗證：

- `deidentified_word_report.json` 可讀。
- 本機 DOCX template 存在時可被檢查。
- DOCX 可讀。
- smoke script 可呼叫既有 `build_word` 邏輯。
- output DOCX 可成功產生。
- repeat marker 已消失。
- demo thermal cycle rows 已展開。
- unexpected unresolved placeholders 為 `0`。

## 8. 尚未代表完成的範圍

目前結果不代表：

- 正式 Word 報告完成。
- nested repeat / cross-table repeat 已完成。
- 正式排版驗收已完成。
- 多圖複雜排版已完成。

目前仍是 MVP smoke build checkpoint，不是正式報告交付節點。

## 9. 下一步建議

下一步仍不建議擴大到 complex multi-image layout 或正式排版驗收。

建議優先順序：

1. 先檢查 smoke output DOCX 的人工版面可讀性。
2. 若需要，補 R2 diagnostics / missing data policy。
3. complex multi-image layout 不要和 R2/R3 repeat block 混在同一輪做。

## 10. 禁止事項

- 不要 commit `project/output/`。
- 不要 commit `project/templates/word/deidentified_report_template_repeat.docx`。
- 不要把目前 `WARN` 當成失敗，除非出現 unexpected unresolved placeholder。
- 不要為了讓 `WARN` 消失而直接大改 `build_word.py`。
- 不要本輪實作 repeat block renderer。
