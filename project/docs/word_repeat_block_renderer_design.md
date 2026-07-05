# Word Repeat Block Renderer Design

## 1. 文件目的

本文件用來設計 `build_word.py` 的 Word repeat block renderer。它描述 repeat block 的資料模型、config 格式、renderer 行為、錯誤處理與驗證策略。

R1 已實作同一個 Word table 內 start/end marker 之間的 table row repeat expansion。nested repeat、跨 table repeat、text box、repeat block 內圖片與 complex multi-image layout 仍不在目前支援範圍。

## 2. Repeat Block 的定義

repeat block 是 Word template 中一段可依資料筆數重複產生的區塊。典型例子是 6.3 Environmental Test / Thermal Vacuum Test 中的 cycle rows：同一組表格列結構會依每個 thermal cycle 重複出現，但前後的固定說明列不應被複製。

在 Word template 中，repeat block 應用明確 marker 標示範圍，讓 renderer 不需要依靠人工版面位置或樣式猜測哪些 row 需要重複。

## 3. 目前 Template Marker

目前 thermal vacuum cycle block 使用以下 marker：

```text
{{#repeat:thermal_vacuum_cycle_block}}
{{/repeat:thermal_vacuum_cycle_block}}
```

這兩個 marker 中間的 Word table rows 是 repeat row template。R1 renderer 會找到 start marker 所在 row 與 end marker 所在 row，並把兩者之間的 row 當作可複製的 row template。

start marker row 與 end marker row 只用於標示範圍，不應出現在最終正式輸出的 DOCX 中。

## 4. 6.3 章節的三段模型

6.3 Environmental Test / Thermal Vacuum Test 建議用三段模型理解：

- head rows：固定開頭，不重複。這些 rows 位於 start marker 前，用於章節標題、固定說明或表格表頭。
- repeat rows：中間動態區塊，依 `cycle_count` 或 `thermal_cycles` 資料筆數重複。這些 rows 位於 start marker 與 end marker 中間。
- tail rows：固定結尾，不重複。這些 rows 位於 end marker 後，用於固定收尾說明、簽核區或後續章節銜接。

renderer 只應複製 repeat rows，不應複製 head rows 或 tail rows。

## 5. 資料來源設計

未來 repeat renderer 應優先使用：

```text
shared_data.thermal_cycles
```

每筆 cycle data 可包含：

- `cycle_index`
- `hot_soak_start_label`
- `hot_soak_end_label`
- `cold_soak_start_label`
- `cold_soak_end_label`
- `function_test_label`
- `date_time`
- `status`
- `signature`

實際資料結構可以是 flat object，也可以在後續版本演進成巢狀結構，例如 `hot_soak_start.date_time`、`hot_soak_start.status`、`hot_soak_start.signature`。R1 實作應先選定最小可用格式，避免同時導入過多 mapping 分支。

R1 需要 `repeat_source` 指向 list。若沒有 `thermal_cycles`，目前會 FAIL，避免產出錯誤報告。未來才考慮用 `cycle_count` 產生最小 demo rows；這個 fallback 只能用於 local smoke 或 MVP demo，不應默默產出正式報告資料。

## 6. JSON Config 設計

可參考目前這兩份 config：

- `project/config/word_templates/deidentified_report_mapping.example.json`
- `project/config/word_templates/deidentified_word_report.json`

未來 `repeat_block_rules` 應包含：

- `block_key`
- `start_marker`
- `end_marker`
- `repeat_source`
- `required`
- `missing_data_policy`
- `placeholder_rules`

範例：

```json
{
  "repeat_block_rules": [
    {
      "block_key": "thermal_vacuum_cycle_block",
      "type": "repeat_table_rows",
      "start_marker": "{{#repeat:thermal_vacuum_cycle_block}}",
      "end_marker": "{{/repeat:thermal_vacuum_cycle_block}}",
      "repeat_source": "shared_data.thermal_cycles",
      "fallback_repeat_count_source": "shared_data.cycle_count",
      "required": true,
      "missing_data_policy": "fail",
      "placeholder_rules": [
        {
          "placeholder": "{{cycle_index}}",
          "source": "thermal_cycles[].cycle_index",
          "required": true
        },
        {
          "placeholder": "{{cycle_hot_soak_start_label}}",
          "source": "thermal_cycles[].hot_soak_start_label",
          "required": true
        },
        {
          "placeholder": "{{hot_soak_start_time}}",
          "source": "thermal_cycles[].hot_soak_start_time",
          "required": false
        },
        {
          "placeholder": "{{hot_soak_start_status}}",
          "source": "thermal_cycles[].hot_soak_start_status",
          "required": false
        },
        {
          "placeholder": "{{hot_soak_start_signature}}",
          "source": "thermal_cycles[].hot_soak_start_signature",
          "required": false
        },
        {
          "placeholder": "{{cycle_cold_soak_end_label}}",
          "source": "thermal_cycles[].cold_soak_end_label",
          "required": true
        },
        {
          "placeholder": "{{cold_soak_end_time}}",
          "source": "thermal_cycles[].cold_soak_end_time",
          "required": false
        },
        {
          "placeholder": "{{cold_soak_end_status}}",
          "source": "thermal_cycles[].cold_soak_end_status",
          "required": false
        },
        {
          "placeholder": "{{cold_soak_end_signature}}",
          "source": "thermal_cycles[].cold_soak_end_signature",
          "required": false
        }
      ]
    }
  ]
}
```

`missing_data_policy` 初期建議支援 `fail`，未來可擴充 `keep_blank` 或 `remove_block`。正式報告預設應使用 `fail`。

## 7. Renderer 行為設計

未來 `build_word.py` 處理 repeat block 時，建議流程如下：

1. 讀取 `repeat_block_rules`。
2. 在 Word document tables 中找到 start marker 所在 table row。
3. 找到 end marker 所在 table row。
4. 判斷 start/end marker 是否在同一個 Word table。
5. 判斷 start marker row index 是否早於 end marker row index。
6. 取得 start/end marker 之間的 row template。
7. 依 `repeat_source` 取得資料筆數。
8. 對每筆 cycle data 複製 row template。
9. 在複製出的 rows 中做該筆 cycle data 的 placeholder replacement。
10. 移除 start marker row 與 end marker row。
11. 保留原始 row style、cell style、border、paragraph formatting 與 run formatting。
12. 若沒有資料，依 `missing_data_policy` 決定 fail、keep template、keep blank 或 remove block。

row 複製應優先保留 Word XML 結構，避免只用 cell text 重建，否則容易遺失表格框線、merge、字型、段落樣式與簽核欄位版面。

## 8. 錯誤處理策略

初期建議以 FAIL 為預設，避免產出看似成功但內容錯誤的正式報告。未來可透過 config 支援 `keep_blank` 或 `remove_block`，但不應在沒有明確設定時自動吞掉錯誤。

建議處理如下：

- 找不到 start marker：FAIL，訊息包含 `block_key` 與 `start_marker`。
- 找不到 end marker：FAIL，訊息包含 `block_key` 與 `end_marker`。
- start/end marker 不在同一 table：FAIL，因 R1 僅支援同一 table 內 row repeat。
- start marker 在 end marker 後面：FAIL，代表 template marker 順序錯誤。
- repeat block 中沒有 template rows：FAIL，因沒有可複製的 row template。
- `repeat_source` 不存在：若 `required: true` 則 FAIL；若未來明確設定 fallback，才可考慮使用 `fallback_repeat_count_source`。
- `repeat_source` 是空陣列：預設 FAIL；未來可依 `missing_data_policy` 設定改為 keep blank 或 remove block。
- repeat block 裡有未知 placeholder：FAIL，除非該 placeholder 已被明確列入 known unsupported 或 future placeholder policy。
- 複製 row 時發生例外：FAIL，並保留原始 exception context，包含 block key、table index、row range。

錯誤訊息應讓使用者能定位是 config、template marker、資料來源或 Word row 複製失敗，而不是只回報一般 unresolved placeholder。

## 9. 與現有 Placeholder Replacement 的關係

repeat block renderer 應和一般 paragraph/table/header/footer placeholder replacement 有明確順序。建議流程：

1. 先處理 repeat block row expansion。
2. 再執行一般 paragraph/table/header/footer placeholder replacement。
3. 再處理 image placeholder。
4. 最後 inspect unresolved placeholder。

原因是 repeat template 裡的 placeholder 需要依每筆 cycle data 替換。如果先跑一般 placeholder replacement，repeat template 中的 placeholder 可能被錯誤地用全域資料替換、被清成空字串，或在 row 複製後殘留成不可辨識的 unresolved placeholder。

repeat expansion 完成後，複製出的 rows 已經帶有每筆 cycle data 的文字；接著再跑一般替換，可以處理文件其他區域的固定 placeholder，例如 paragraph、table cell、header/footer 中的 `{{report_title}}`。

## 10. MVP 實作切分建議

Phase R1：

- 已支援 table row repeat。
- 已支援同一 table 內的 start/end marker。
- 已支援依 `repeat_source` list 複製 start/end 中間的 row template。
- 已支援複製後依每筆 repeat data 替換 row placeholder。
- 已支援移除 start/end marker rows，並清理含 marker 的 template instruction paragraph。
- 不支援 nested repeat。
- 不支援跨 table repeat。
- 不支援 text box。
- 不支援 repeat block 內插圖片。

Phase R2：

- 支援 `missing_data_policy`。
- 支援更完整的 diagnostics。
- 支援 repeat block inspect。

Phase R3：

- 視需求支援多個 repeat block。
- 視需求支援更複雜圖片/表格混排。

## 11. 驗證策略

未來實作後應加入以下驗證：

- `check_word_config.py` 應確認 `repeat_block_rules` 與 template marker 對齊。
- `smoke_build_deidentified_word.py` 應確認 repeat marker 消失。
- output DOCX 不應殘留 repeat start/end marker。
- unexpected unresolved placeholders 必須為 `0`。
- repeat block 中的 cycle placeholders 不應再被列為 known unsupported。
- `project/output/` 不可 commit。
- deidentified template DOCX 不可 commit。

驗證時應把 local ignored artifact 和 repo source 明確分開。`project/output/` 只用於人工檢查與 smoke result，不應成為 git diff 的一部分。

## 12. 本輪禁止事項

本文件只是設計文件。

本輪明確禁止：

- 本輪不修改 `build_word.py`。
- 本輪不實作 repeat renderer。
- 本輪不修改 smoke script。
- 本輪不修改 checker。
- 本輪不修改 pipeline。
- 本輪不修改 image 流程。
- 本輪不碰 `project/output/`。

本輪禁止修改：

- `project/app/word/build_word.py`
- `project/app/word/smoke_build_deidentified_word.py`
- `project/app/word/check_word_config.py`
- `project/app/pipeline_main.py`
- `project/app/pipelines/runner.py`
- `project/app/image/generate_image.py`
- `project/app/image/overlay_text.py`
- `project/config/image_templates/cycle_diagram.json`
- `project/output/`
