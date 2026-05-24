# 外包交接文件

本文件提供給外包工程師、主管、或未來接手者，用來理解目前 Phase 3 MVP 狀態、核心檔案、禁止任意修改的區域、可外包工作項目，以及驗收標準。

## 1. 專案目前狀態

目前系統已完成一條端到端 MVP 流程：

```text
Excel
-> SharedData
-> generate_image
-> overlay_text
-> build_word
-> PNG + DOCX output
```

目前 active entrypoint 是：

```text
project/app/pipeline_main.py
```

目前已完成能力：

- 從 Excel 讀取 row data。
- 將 Excel row 正規化為 `SharedData`。
- 依 config 產生 cycle diagram PNG。
- 對 PNG 疊加文字。
- 使用 Word template 進行最小 placeholder replacement。
- 將 `{{cycle_image}}` 替換為最終 PNG。
- 每筆 Excel row 產生一份 DOCX。
- 使用 `inspect_word.py` 做最小 DOCX 結構檢查。

目前不是正式報告引擎，也不是完整 Word template engine。請把目前狀態視為可跑通、可驗收、可漸進擴充的 Phase 3 MVP。

## 2. 核心檔案

主要入口與 pipeline：

- `project/app/pipeline_main.py`
- `project/app/pipelines/runner.py`
- `project/app/pipelines/config_loader.py`

Word MVP：

- `project/app/word/build_word.py`
- `project/app/word/inspect_word.py`
- `project/app/word/create_mvp_template.py`

Config：

- `project/config/pipelines/mvp_image_pipeline.json`
- `project/config/word_templates/mvp_word_report.json`

Template：

- `project/templates/word/mvp_report_template.docx`

目前輸出位置：

- `project/output/pipeline_mvp/`
- `project/output/pipeline_mvp/word/`

注意：`project/output/` 已被 `.gitignore` 忽略，不應納入 commit。

## 3. 不可任意修改區域

除非任務明確要求，外包工作不得修改以下檔案或行為：

- `project/app/image/generate_image.py`
- `project/app/image/overlay_text.py`
- `project/config/image_templates/cycle_diagram.json`

尤其不要任意改動：

- geometry 邏輯
- marker 邏輯
- guide 邏輯
- anchor 邏輯
- 既有 PNG 輸出檔名規則
- 既有 PNG 可正常產生的流程

也不得 commit：

- `project/output/`
- 任何 smoke test 產生的 PNG / DOCX artifact
- 本機暫存檔、log、cache、render temp

## 4. 可外包項目

以下是建議可切給外包的工作項目。每個項目都應獨立開 branch、獨立 PR、獨立驗收。

### A. 正式 Word template 套版

目標：

- 將目前 MVP template 替換為更接近真實公司報告格式的 DOCX template。
- 保留既有 placeholder replacement 流程。
- 不破壞目前 sample input 的 PNG + DOCX 產出。

建議範圍：

- 新增或更新 `project/templates/word/*.docx`
- 更新 `project/config/word_templates/mvp_word_report.json`
- 必要時小幅調整 `build_word.py` 的 template replacement 能力

### B. 表格寫值 MVP

目標：

- 支援將多個欄位寫入 Word 表格。
- 先做簡單固定表格，不做複雜動態表格引擎。

建議範圍：

- 擴充 Word config 的 table mapping。
- 擴充 `build_word.py` 的表格寫值。
- 擴充 `inspect_word.py` 檢查關鍵表格文字。

### C. 多圖插入 MVP

目標：

- 支援多個圖片 placeholder。
- 先支援固定 placeholder 對固定 image artifact。

建議範圍：

- 擴充 `image_placeholders` config。
- 擴充 runner artifact 傳遞或 Word config 對 image path 的描述。
- 保持現有 `{{cycle_image}}` 行為不變。

### D. Placeholder mapping 規格整理

目標：

- 將目前 `placeholders`、`image_placeholders` 的格式整理成正式規格文件。
- 說明支援與不支援的 Word placeholder 類型。

建議範圍：

- 新增 docs 文件。
- 可補充 config 範例。
- 不需要修改功能程式。

### E. 錯誤訊息與 log 改善

目標：

- 讓 pipeline 失敗時更容易定位是哪一列 Excel、哪一個 placeholder、哪一個 DOCX template 發生問題。

建議範圍：

- 改善 exception message。
- 增加必要的 console output。
- 不導入大型 logging framework。

### F. 使用手冊整理

目標：

- 提供非工程人員可讀的操作手冊。
- 說明如何準備 Excel、如何跑 pipeline、如何找輸出檔。

建議範圍：

- 新增 docs 文件。
- 不修改程式。

### G. 測試資料與驗收案例整理

目標：

- 補齊更多 sample Excel rows。
- 建立明確驗收案例，例如不同 cycle_count、缺欄位、空值、長文字。

建議範圍：

- 新增 sample data 或測試說明。
- 不 commit runtime output。

## 5. 每項外包驗收標準

所有外包 PR 都必須符合以下共通驗收標準：

- `pipeline_main.py` smoke test 必須通過。
- `inspect_word.py` 必須通過。
- 不可破壞既有 PNG 輸出。
- 不可任意修改 image geometry / marker / guide / anchor 行為。
- `project/output/` 不可進 git。
- git diff 必須限制在任務相關檔案。
- PR 必須說明 modified files、added files、risk、limitation。

建議 smoke test：

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
.\.venv\Scripts\python.exe project\app\word\inspect_word.py
```

目前預期 sample outputs：

```text
project/output/pipeline_mvp/report_cycle_2.png
project/output/pipeline_mvp/report_cycle_3.png
project/output/pipeline_mvp/report_cycle_5.png
project/output/pipeline_mvp/word/report_cycle_2.docx
project/output/pipeline_mvp/word/report_cycle_3.docx
project/output/pipeline_mvp/word/report_cycle_5.docx
```

這些 output 是驗收參考，不可 commit。

## 6. 建議工作流程

建議外包工程師依照以下流程工作：

1. 先從最新 `main` 開 feature branch。
2. 每次只做一個明確任務。
3. 小步 commit，避免把不相關修改混在一起。
4. 修改前先跑一次 smoke test，確認 baseline 是好的。
5. 修改後再跑 smoke test 與 inspection。
6. PR 說明必須包含：
   - modified files
   - added files
   - smoke test result
   - risk / limitation
   - 是否碰到 config 或 template
   - 是否碰到 image pipeline
7. PR 不得包含 `project/output/`。

建議 branch 命名：

```text
feature/word-template-layout
feature/word-table-mapping
feature/word-multi-image
docs/placeholder-mapping-spec
```

建議 commit message：

```text
feat: add Word table value mapping MVP
feat: support multiple Word image placeholders
docs: add Word placeholder mapping spec
docs: add contractor usage guide
```

## 7. 已知限制

目前 Word MVP 不支援：

- 頁首頁尾 placeholder。
- 文字框 placeholder。
- 跨 run placeholder。
- 多圖複雜排版。
- Word 視覺 render 驗證。
- 完整正式報告模板。
- 複雜條件式內容。
- 動態增減 Word 表格列。
- 多份 Word template routing。

目前 `inspect_word.py` 是結構檢查，不是視覺驗證。它可以檢查 DOCX 可開啟、必要文字存在、沒有未替換的 `{{...}}` placeholder、至少有一張內嵌圖片，但不能保證 Word 中的視覺排版完全正確。

## 8. 交接重點

接手者應優先理解：

- `SharedData` 是圖片與 Word 共用資料層。
- image pipeline 已可正常輸出，除非任務指定，不要改。
- Word MVP 現在是最小 template replacement，不是完整 template engine。
- 所有外包工作都應該以 smoke test 和 inspection 通過作為最低驗收門檻。
- 文件、config、template、程式碼應分清楚，不要把大量設計變更塞進同一個 PR。
