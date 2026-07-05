# Word Template Mapping Spec

本文件說明 WebToWord / BakeOutPic 目前 Word template 與 mapping config 的對接原則，並記錄去識別化範本中的 repeat block 需求。此文件是規格與交接說明，不代表目前 `build_word.py` 已支援所有描述的能力。

## 1. Word template 對接原則

- Word template 應使用去識別化範本進行開發與驗收，不得將正式機密報告範本放入 repo。
- template 檔案建議放在 `project/templates/word/`。
- mapping example / spec config 建議放在 `project/config/word_templates/`。
- runtime output 必須維持在 `project/output/`，且不得 commit。
- Word template 內所有需要替換的資料應以明確 placeholder 表示，避免用肉眼位置或樣式推斷資料來源。
- 目前 MVP 的 active Word flow 仍以 `project/config/word_templates/mvp_word_report.json` 為主；`deidentified_report_mapping.example.json` 是 spec/example，不一定可直接由目前 `build_word.py` 執行。
- `project/config/word_templates/deidentified_word_report.json` 是本機 smoke test config，用來測試目前 `build_word.py` 對去識別化 template 的支援程度。
- `deidentified_word_report.json` 的 `template_path` 以 `project/` 作為 base dir 解析，因此設定為 `templates/word/deidentified_report_template_repeat.docx`；從 repo root 看到的實體檔位置是 `project/templates/word/deidentified_report_template_repeat.docx`。
- `project/templates/word/deidentified_report_template_repeat.docx` 不進 repo，開發者需自行放在本機指定路徑；此檔已列入 `.gitignore`。

## 2. Placeholder 命名規則

一般文字 placeholder 使用雙大括號：

```text
{{placeholder_name}}
```

命名建議：

- 使用小寫英文字母、數字與底線。
- 名稱應描述業務意義，例如 `{{cycle_count}}`、`{{high_temperature}}`。
- 不建議使用空白、中文、標點或 Word 自動格式可能拆分的符號。
- 同一份 template 內同名 placeholder 應對應同一個資料來源。
- repeat block marker 使用特殊語法，僅用於標示動態區塊範圍。

repeat block marker 範例：

```text
{{#repeat:thermal_vacuum_cycle_block}}
{{/repeat:thermal_vacuum_cycle_block}}
```

## 3. Paragraph placeholder 規則

paragraph placeholder 指出現在一般段落文字中的 placeholder。

目前 MVP 已支援：

- 在 document paragraphs 中搜尋 placeholder。
- 在 header/footer paragraphs 中搜尋一般文字 placeholder。
- 依 config 將 placeholder 替換成 `SharedData` 或固定值。
- 未設定資料時可依 mapping policy 決定 error 或留空。

限制：

- 目前 MVP 以 paragraph 的合併文字進行替換，替換後會重建該 paragraph 的文字 run。
- 若 placeholder 被 Word 拆成多個 run，複雜樣式可能無法完整保留。
- 文字框內的 placeholder 目前不是 MVP 支援範圍。

## 4. Table cell placeholder 規則

table cell placeholder 指出現在 Word 表格儲存格中的 placeholder。

目前 MVP 已支援：

- 掃描 Word table cell 裡的 paragraphs。
- 替換 table cell 內的文字 placeholder。
- 掃描 header/footer 內 table cell 裡的 paragraphs，並替換一般文字 placeholder。

限制：

- 目前支援的是「儲存格內 placeholder replacement」，不是完整 table mapping engine。
- 目前尚未支援依 config 指定表格座標、動態新增列、條件式表格內容或 repeat table row rendering。
- 若表格內容需要依 cycle data 重複多列，應使用本文件第 9 節的 repeat block 規格描述，待 future renderer 實作。

## 5. Image placeholder 規則

image placeholder 用於將 pipeline 產生的圖片插入 Word。

目前 MVP 已支援：

- 以 `{{cycle_image}}` 作為圖片 placeholder。
- 將 `overlay_text` 後的 final PNG 插入 Word。
- 依 image config 指定插入寬度，例如 `width_inches`。

建議規則：

- 每個 image placeholder 應在 mapping 中指定 `artifact_key` 或圖片來源。
- 必填圖片應標示 `required: true`。
- 圖片寬度應由 mapping 明確指定，避免依 Word 預設尺寸造成版面不穩。

目前限制：

- MVP 主要支援單圖插入。
- 多圖 placeholder、圖片 caption 自動生成、不同 section 的多張圖 routing 尚未正式實作。

## 6. Required / Optional 欄位規則

mapping 中每個 placeholder 建議標示 `required`：

- `required: true` 表示缺值時應視為錯誤。
- `required: false` 表示缺值時可留空。

建議 future policy：

- required placeholder 找不到資料時，`build_word` 應停止並回報明確錯誤。
- optional placeholder 找不到資料時，應以空字串替換。
- 錯誤訊息應包含 template id、placeholder、source 與 Excel row / record id。

## 7. Missing image policy

建議 policy：

- 必填圖片缺失時應直接 error。
- optional 圖片缺失時可以移除 placeholder 或留下空白段落。
- 錯誤訊息應指出缺少哪個 image placeholder、對應 artifact key 與 record id。

目前 MVP：

- `build_word` 在輸入 image path 不存在時會 error。
- 目前尚未支援多張圖片的 missing image policy。

## 8. Unresolved placeholder policy

建議 policy：

- 一般 placeholder 在輸出 DOCX 後不應殘留 `{{...}}`。
- smoke inspection 應檢查 unresolved placeholder。
- repeat block marker 在 repeat renderer 尚未實作前，可以作為 future requirement 的例外，但不應接入正式 production output。

目前 MVP：

- `inspect_word.py` 會檢查 DOCX 是否仍包含 `{{` 或 `}}`。
- 若 template 中保留 repeat marker，但目前 renderer 尚未處理，該 template 不應直接用於目前 MVP smoke output。
- `deidentified_word_report.json` 會列出目前已知 unsupported repeat marker，但不會讓目前 MVP 自動展開 repeat block。
- `project/app/word/check_word_config.py` 是安全的 dry-run 工具，可檢查 Word config 與本機 template 的 placeholder 對齊狀態；它不產生 Word、不修改 `project/output/`，也不代表 `build_word.py` 已支援 repeat block。

## 9. 6.3 Environmental Test / Thermal Vacuum Test Repeat Block

6.3 Environmental Test / Thermal Vacuum Test 的表格不是一般固定表格填值，而是動態重複區塊。

此章節包含三段概念：

- head rows：固定開頭列，只出現一次，不重複。
- repeated middle rows：cycle repeat block，依 `cycle_count` 或 `shared_data.thermal_cycles` 的資料筆數重複。
- tail rows：固定結尾列，只出現一次，不重複。

Word template 中使用以下 marker 標記動態區塊：

```text
{{#repeat:thermal_vacuum_cycle_block}}
{{/repeat:thermal_vacuum_cycle_block}}
```

規則：

- start marker 與 end marker 之間的 Word table rows 是 repeat block。
- marker 前面的 rows 是 head rows，不可複製。
- marker 後面的 rows 是 tail rows，不可複製。
- repeat block 內的 rows 應作為 row template，未來依每筆 cycle data 複製。
- 每次複製後，應以該筆 cycle data 替換 block 內的 placeholder，例如 `{{cycle_index}}`、`{{hot_soak_start_time}}`、`{{cold_soak_end_status}}`。

本輪明確不實作此功能。

目前 `build_word.py` MVP 尚未支援 repeat-table-row rendering。若把含 repeat marker 的 template 直接接到目前 MVP inspection，可能會因 unresolved placeholder 或 marker 殘留而失敗。

目前 repeat block marker 是 spec marker，不代表 MVP renderer 已支援功能。`deidentified_word_report.json` 僅作為本機 smoke test config，目的是讓開發者確認一般 paragraph/table-cell placeholder 與 `{{cycle_image}}` 插入能力；repeat block 的 head / repeated middle / tail rows 複製仍是 future work。

## 10. 目前 MVP 已支援項目

目前 Word MVP 已支援：

- `template_path` 讀取 `.docx` template。
- paragraph placeholder replacement。
- table cell placeholder replacement。
- header/footer 一般文字 placeholder replacement。
- `{{cycle_image}}` 圖片插入。
- 無 `template_path` 時 fallback 直接產生 DOCX。
- `inspect_word.py` 檢查 DOCX 可開啟、必要文字、unresolved placeholder 與 embedded image。
- `check_word_config.py` 檢查 config JSON、template path、DOCX zip 可讀性、template placeholders、config declarations 與 known unsupported markers。

## 11. 目前 MVP 尚未支援項目

目前尚未支援：

- 真實工作用 Word template 正式導入。
- 完整 placeholder mapping spec 驗證器。
- table mapping / table write-value engine。
- repeat table row rendering。
- 多圖插入 MVP。
- 文字框 placeholder。
- 跨 run placeholder 的完整樣式保留。
- 視覺 render validation。
- 正式報告排版驗收。

## 12. Future build_word repeat table rows 處理建議

未來 `build_word` 若要支援 repeat table rows，建議流程如下：

1. 讀取 mapping 中的 `repeat_block_rules`。
2. 在 Word table 中尋找 `start_marker` 與 `end_marker`。
3. 將 marker 前的 rows 視為 head rows，保留一次。
4. 將 marker 與 end marker 之間的 rows 視為 repeated middle rows template。
5. 將 marker 後的 rows 視為 tail rows，保留一次。
6. 從 `shared_data.thermal_cycles` 取得 cycle data；若沒有 list，可依 `cycle_count` 建立基本 cycle index。
7. 對每筆 cycle data 複製 middle rows。
8. 在複製出的 rows 中替換 row placeholders。
9. 移除 repeat markers。
10. 完成後再執行 unresolved placeholder inspection。

實作時應注意：

- 複製 Word table row 時需保留 cell count、merge、style、paragraph formatting 與 run formatting。
- 若 repeat source 為空但欄位 required，應 error。
- 若 `cycle_count` 與 `thermal_cycles` 筆數不一致，應有明確 policy。
- repeat renderer 應與現有 paragraph / table cell placeholder replacement 分層，避免破壞目前 MVP。
