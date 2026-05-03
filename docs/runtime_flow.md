# Runtime Flow

## Current Flow（MVP）

Current MVP pipeline:

```text
pipeline_main.py
-> SharedData
-> generate_image
-> overlay_text
```

`main.py` + `mapping.json` is legacy flow.

## MVP pipeline config contract

`project/config/pipelines/mvp_image_pipeline.json` is the single MVP pipeline config for Phase 2. It is intentionally not split into Project config and Test Type config yet.

This config owns the minimum runtime contract for the current MVP pipeline:

- project/test identity: `project_id`, `test_id`
- runtime input/output path: `input_excel_path`, `output_dir`
- image template reference: `image_template_mapping`
- render defaults: `render_defaults`
- pipeline steps: `pipeline`

The active `PipelineConfigLoader` validates only the minimum required fields and currently supports the MVP image steps `generate_image` and `overlay_text`.

## Project/test identity flow

`project_id` and `test_id` currently come from `project/config/pipelines/mvp_image_pipeline.json`. `pipeline_main.py` loads them through `PipelineConfigLoader` and passes them into `normalize_excel_row`.

`normalize_excel_row` uses those values to create `SharedData.project_id` and `SharedData.test_id`. Excel currently owns row-level business payload only; it does not own project/test identity.

In the active MVP flow, `runner`, `generate_image`, and `overlay_text` all start from `SharedData` rather than raw Excel rows. The legacy `main.py` / `renderer.py` path may still use raw row data directly, but that is the legacy flow, not the current MVP flow.

本文依據目前 repo 內的實際程式碼說明執行流程，對應檔案主要為：

- `project/app/main.py`
- `project/app/config_loader.py`
- `project/app/excel_reader.py`
- `project/app/renderer.py`
- `project/config/mapping.json`

## 1. `main.py` 的執行流程

目前入口在 `project/app/main.py`，啟動順序如下：

1. Python 直接執行 `main.py` 時，會先進入 `if __name__ == "__main__":` 區塊。
2. 這個區塊以 `try/except` 包住 `main()`。
3. 若 `main()` 任何地方拋出例外，最外層會 `print(f"發生錯誤：{exc}")`，再 `sys.exit(1)`。

`main()` 內部的實際呼叫順序如下：

1. `get_base_dir()`
   - 判斷目前是原始 Python 執行，還是 PyInstaller 打包後的 `exe`。
   - 若 `sys.frozen == True`，回傳 `Path(sys.executable).resolve().parent`。
   - 否則回傳 `Path(__file__).resolve().parent.parent`，也就是 `project/`。
2. 組出固定路徑
   - `config_path = base_dir / "config" / "mapping.json"`
   - `excel_path = base_dir / "data" / "input.xlsx"`
   - `output_dir = base_dir / "output"`
3. `output_dir.mkdir(parents=True, exist_ok=True)`
   - 先保證輸出資料夾存在。
4. `config = ConfigLoader(config_path)`
   - 載入並驗證 `mapping.json`。
5. `rows = read_excel_rows(excel_path)`
   - 把 Excel 轉成 `list[dict]`。
6. 讀取 debug 設定
   - 先取 `config.global_config.get("debug_grid", False)`
   - 若命令列含 `--debug`，則強制覆蓋為 `True`
7. 逐列處理 `rows`
   - 先從 `row_data` 取 `template_id`
   - 若缺少或空白，直接 `raise ValueError`
   - `template_config = config.get_template(template_id)`
   - `output_filename = build_output_filename(row_data, template_id)`
   - `output_path = output_dir / output_filename`
8. 呼叫 `render_image(...)`
   - 傳入 `template_config`
   - 傳入 `row_data`
   - 傳入 `config.global_config`
   - 傳入 `base_dir`
   - 傳入 `output_path`
   - 傳入 `debug_grid`
9. 成功時 `print(f"已產生圖片：{output_path}")`
10. 若單筆資料在 `render_image()` 或其內部流程出錯，`main()` 會用 `RuntimeError(...) from exc` 再包一層，補上 Excel 列號與 `template_id`。

### `main.py` 內的關鍵函式

- `get_base_dir()`
  - 用來統一原始執行與 `exe` 執行時的資源根目錄。
- `build_output_filename(row_data, template_id)`
  - 先讀 Excel 的 `output_name`
  - 若沒有，就退回 `f"{template_id}_{row_data['row_number']}"`
  - 若副檔名不是 `.png`，會自動補上 `.png`
- `main()`
  - 負責整條批次流程 orchestration，本身不處理 Excel 細節與 Pillow 細節。

## 2. 各模組職責

### `project/app/main.py`

職責是流程編排，不直接做資料解析或繪圖：

- 決定 base directory
- 建立固定輸入輸出路徑
- 載入 config
- 載入 Excel
- 逐列 dispatch 到對應 template
- 統一處理批次層級的錯誤包裝

### `project/app/config_loader.py`

核心類別是 `ConfigLoader`，負責 `mapping.json` 的載入、驗證、查找。

實際責任包含：

- `_load_json()`
  - 檢查檔案是否存在
  - 用 `json.load()` 讀檔
  - JSON 格式錯誤時轉成 `ValueError`
- `_validate_root(config_data)`
  - 檢查 root 是否有 `global`、`templates`
  - 檢查 `global` 必須是 `dict`
  - 檢查 `templates` 必須是 `list`
  - 補預設值：
    - `default_font_size = 24`
    - `default_color = "#000000"`
    - `default_align = "left"`
- `_build_template_lookup(templates)`
  - 逐一驗證每個 template
  - 轉成 `{template_id: template_config}` 的 lookup dict
  - 檢查 `template_id` 不可重複
- `_validate_template(template, index)`
  - 檢查每個 template 必須有：
    - `template_id`
    - `template_image`
    - `fields`
- `_validate_field(template_id, field, field_index)`
  - 檢查每個 field 必須有：
    - `source`
    - `x`
    - `y`
  - 也檢查型別是否合法
- `get_template(template_id)`
  - 依 Excel 內的 `template_id` 取出對應 template 設定

### `project/app/excel_reader.py`

目前只有一個主要函式 `read_excel_rows(excel_path)`，責任很單純：

- 用 `openpyxl.load_workbook(..., data_only=True)` 讀 Excel
- 只讀 `workbook.active`
- 第一列視為 header
- 後續每列轉成 `dict`
- 自動加上 `row_number`
- 跳過整列空白資料

它回傳的資料型態是 `list[dict]`，例如目前範例 Excel 會變成近似：

```python
{
    "template_id": "A",
    "output_name": "bakeoutpic_test",
    "name": 123,
    "date": datetime(...),
    "duration": 3,
    "temperature": 567,
    "tolerance": 891,
    "row_number": 2,
}
```

### `project/app/renderer.py`

這個模組負責 Pillow 繪圖與輸出 PNG。

主要函式與責任：

- `render_image(template_config, row_data, global_config, base_dir, output_path, debug_grid=False)`
  - 開 template 圖
  - 依 fields 逐一組字串、載字型、算位置、畫文字
  - 最後存成 PNG
- `draw_debug_grid(image, draw)`
  - 畫 50px 間距的紅色格線與座標文字
- `resolve_path(base_dir, relative_path)`
  - 將 `mapping.json` 內的相對路徑轉成可實際存取的路徑
- `load_font(field, global_config, base_dir)`
  - field 有 `font_path` 就用 field 的
  - 否則退回 `global.default_font_path`
  - 若都沒有則退回 `ImageFont.load_default()`
- `parse_color(color_value)`
  - 支援 `#RRGGBB`
  - 支援 `#RGB`
  - 支援 `[255, 255, 255]`
  - 支援 `(255, 255, 255)`
- `calculate_text_position(draw, text, font, x, y, align)`
  - `left` 直接用 `(x, y)`
  - `center` 會扣掉半個文字寬度
  - `right` 會扣掉整個文字寬度

## 3. Excel -> `template_id` -> mapping -> Pillow 繪圖 -> output 的資料流

目前資料流是很明確的一條線：

1. Excel 輸入
   - 檔案固定是 `project/data/input.xlsx`
   - `read_excel_rows()` 讀取 active sheet
   - 第一列 header 變成 dict 的 key
   - 每一列資料變成一個 `row_data`

2. 取出 `template_id`
   - 在 `main()` 內用 `row_data.get("template_id")`
   - 這是 routing key，決定該列資料要套哪個模板

3. 查 `mapping.json`
   - `ConfigLoader.get_template(template_id)` 從 `self.templates` 找對應 template
   - `self.templates` 是在 `ConfigLoader.__init__()` 時由 `_build_template_lookup()` 建好的 lookup dict

4. 取得 template 設定內容
   - 每個 template 至少包含：
     - `template_id`
     - `template_image`
     - `fields`
   - 每個 field 至少包含：
     - `source`
     - `x`
     - `y`

5. Pillow 繪圖
   - `render_image()` 先用 `template_image` 開底圖
   - 對每個 `field`：
     - `source = field["source"]`
     - `value = row_data.get(source)`
     - `text_template = field.get("format", "{value}")`
     - `text = text_template.replace("{value}", str(value))`
     - `font = load_font(...)`
     - `color = parse_color(...)`
     - `align = field.get("align", global_config.get("default_align", "left"))`
     - `position = calculate_text_position(...)`
     - `draw.text(position, text, fill=color, font=font)`

6. 輸出檔名與輸出路徑
   - `build_output_filename()` 先看 Excel 的 `output_name`
   - 若沒有，回退成 `template_id_row_number.png`
   - `output_path = output_dir / output_filename`
   - `render_image()` 內 `image.save(output_path, format="PNG")`

可以用簡化呼叫鏈表示：

```text
project/app/main.py: main()
  -> ConfigLoader(config_path)
  -> read_excel_rows(excel_path)
  -> for row_data in rows
       -> row_data["template_id"]
       -> config.get_template(template_id)
       -> build_output_filename(row_data, template_id)
       -> render_image(...)
            -> resolve_path(...)
            -> Image.open(...)
            -> for field in template_config["fields"]
                 -> load_font(...)
                 -> parse_color(...)
                 -> calculate_text_position(...)
                 -> draw.text(...)
            -> image.save(output_path)
```

## 4. 目前錯誤處理方式

目前錯誤處理是「早期驗證 + 逐層補充上下文 + 最外層結束程式」，但還不是很細緻的 recoverable 設計。

### `config_loader.py`

- `mapping.json` 不存在
  - `_load_json()` -> `FileNotFoundError`
- JSON 格式錯誤
  - `_load_json()` 把 `json.JSONDecodeError` 轉成 `ValueError`
- root 結構不對
  - `_validate_root()` 直接 `raise ValueError`
- template 結構不對
  - `_validate_template()` 直接 `raise ValueError`
- field 結構不對
  - `_validate_field()` 直接 `raise ValueError`
- `template_id` 查不到
  - `get_template()` -> `KeyError`

### `excel_reader.py`

- Excel 檔不存在
  - `read_excel_rows()` -> `FileNotFoundError`
- 檔案不是合法 `.xlsx`
  - `InvalidFileException` 轉成 `ValueError`
- 第一列 header 全空
  - `ValueError`
- 某一欄 header 空白
  - `ValueError`
- 空白資料列
  - 不報錯，直接跳過
- `workbook.close()`
  - 寫在 `finally`，確保讀完或出錯都會關檔

### `renderer.py`

- template 圖不存在
  - `render_image()` -> `FileNotFoundError`
- `field["source"]` 在 Excel 列資料中找不到
  - `render_image()` -> `ValueError`
- 字型檔不存在
  - `load_font()` -> `FileNotFoundError`
- 顏色格式不合法
  - `parse_color()` -> `ValueError`
- `align` 不是 `left/center/right`
  - `calculate_text_position()` -> `ValueError`

### `main.py`

- 缺少 `template_id`
  - `main()` 在進入 renderer 前就 `raise ValueError`
- 單筆資料處理失敗
  - `main()` 用 `RuntimeError(... ) from exc` 包一層
  - 補上 `row_number` 與 `template_id`
- 整體流程失敗
  - `__main__` 最外層統一印錯誤訊息並 `sys.exit(1)`

### 目前錯誤處理的特性

- 一筆失敗就整批停止，沒有 continue 到下一列
- 多數錯誤都直接丟 exception，沒有專用錯誤型別
- `main()` 會補充批次脈絡，但不會寫 log file
- 錯誤訊息已經有列號概念，對追查 Excel 問題有幫助

## 5. 目前哪些地方是寫死的，哪些地方已經設定化

## 已設定化的部分

這些內容已經由 `mapping.json` 或 Excel 控制，而不是寫死在 Python：

- template routing key
  - Excel 的 `template_id`
- 模板底圖路徑
  - `template.template_image`
- 每個欄位對應哪個 Excel 欄位
  - `field.source`
- 每個欄位的文字座標
  - `field.x`, `field.y`
- 單欄位字型大小
  - `field.font_size`
- 單欄位字型路徑
  - `field.font_path`
- 單欄位顏色
  - `field.color`
- 單欄位格式字串
  - `field.format`
- 單欄位對齊方式
  - `field.align`
- 全域預設值
  - `global.default_font_path`
  - `global.default_font_size`
  - `global.default_color`
  - `global.default_align`
  - `global.debug_grid`
- 輸出檔名
  - Excel 的 `output_name`

## 仍然寫死的部分

以下仍然固定在程式中，沒有抽成外部設定：

- 主要輸入檔名
  - `main.py` 寫死為 `data/input.xlsx`
- 主要設定檔名
  - `main.py` 寫死為 `config/mapping.json`
- 輸出資料夾
  - `main.py` 寫死為 `output/`
- 只讀 active sheet
  - `excel_reader.py` 沒有 sheet 名稱設定
- Excel 第一列一定是 header
  - 沒有 header row index 設定
- 只支援輸出 PNG
  - `image.save(..., format="PNG")`
- 文字格式替換只支援 `{value}`
  - 目前沒有多欄位模板，例如 `{duration}`、`{date}` 這種通用格式器
- 對齊只支援 `left` / `center` / `right`
- 目前繪圖動作只有 `draw.text(...)`
  - 還沒有貼圖、畫線、框、QR code、barcode 等 action type
- 一筆失敗即整批停止
  - 沒有錯誤容忍或 partial success 策略

## 程式碼與設定之間的灰色地帶

有些地方 technically 可配置，但仍受到程式碼能力限制：

- `mapping.json` 可以定義多個 template
  - 但 renderer 還是只會做「開底圖 + 寫文字 + 存 PNG」
- `field.format` 可以改輸出文字樣式
  - 但只能做字串替換，沒有日期格式化、數字格式化、條件顯示
- `global.debug_grid` 可設定
  - 但格線邏輯本身仍寫死在 `draw_debug_grid()`，例如 step 固定 50

## 目前可觀察到的實際限制

依目前 repo 狀態，`project/config/mapping.json` 有 `template_id = "B"` 的設定，但 repo 內 `project/assets/templates/` 只有 `template_a.png`。這表示：

- 設定檔已經宣告支援模板 B
- 但素材檔尚未齊備
- 若 Excel 某列改用 `template_id = "B"`，流程會進到 `render_image()`，最後在 template 圖檔不存在時拋出 `FileNotFoundError`

## 6. 若未來要擴充成「數據轉圖片」與「圖片後加工貼字」雙流程，哪些部分可共用

先講結論：目前架構最可共用的是「資料準備層」與「繪圖基礎能力」，但 `main.py` 的流程編排需要再抽象化。

### 可以直接共用的部分

#### 1. `ConfigLoader`

只要未來兩種流程都還是使用外部 JSON 描述規則，`ConfigLoader` 的這些能力都能沿用：

- 載入 JSON
- 驗證 schema
- 建立 `template_id -> config` lookup
- 提供全域預設值

未來差別只是 schema 可能不再只有 `template_image + fields`，而是擴成例如：

- `pipeline_type`
- `base_image`
- `text_fields`
- `overlay_images`
- `post_process_steps`

#### 2. `resolve_path()`

不論是「數據轉圖片」或「圖片後加工貼字」，都還是需要：

- 解析字型路徑
- 解析底圖路徑
- 解析貼圖素材路徑

這個函式很適合保留成共用基礎工具。

#### 3. `load_font()`

兩種流程只要還有文字繪製，就都需要字型載入與 fallback。

#### 4. `parse_color()`

只要還有文字顏色、框線顏色、圖層顏色，這段都可以共用。

#### 5. `calculate_text_position()`

後加工貼字流程一樣需要根據對齊方式計算文字座標，所以可直接共用。

#### 6. `draw_debug_grid()`

只要有人工校正座標需求，兩種流程都能用。

### 可以部分共用，但最好拆出的部分

#### 1. `render_image()`

目前 `render_image()` 同時做了：

- 開底圖
- 迭代 field
- 從 row_data 取值
- 格式化文字
- 載字型與顏色
- 寫字
- 存檔

若未來要支援雙流程，建議把它再拆成更細的共用層，例如：

- `open_canvas_from_template(...)`
- `resolve_field_text(...)`
- `draw_text_field(...)`
- `save_output_image(...)`

這樣：

- 「數據轉圖片」可以從資料列直接生成成品
- 「圖片後加工貼字」可以先接收一張既有圖片，再只重用 `draw_text_field(...)`

#### 2. `build_output_filename()`

目前規則適合 Excel 批次輸出，但若未來有圖片後加工流程，輸出命名策略可能會變成：

- 原檔名加 suffix
- 依工單號命名
- 依批次資料夾命名

邏輯可共用，但應改成可插拔策略。

### 目前不夠共用、未來要先改的部分

#### 1. `main.py` 綁死單一路徑與單一流程

現在 `main()` 預設就是：

`Excel -> template_id -> render_image -> output`

若要變成雙流程，建議把 orchestration 抽成例如：

- `run_excel_to_image_pipeline()`
- `run_image_postprocess_pipeline()`

再由新的入口判斷要跑哪一種。

#### 2. `read_excel_rows()` 只適合 Excel 來源

「數據轉圖片」很適合沿用。

但「圖片後加工貼字」不一定來自 Excel，也可能來自：

- 既有圖片檔清單
- CSV
- API 回傳資料
- 使用者手動輸入 JSON

所以比較好的方向是把它升級成資料來源 adapter 的其中一種，而不是唯一入口。

#### 3. `mapping.json` schema 目前偏向 template-centric

它很適合「拿一列資料，套到一張底圖」。

但若是「圖片後加工貼字」，設定焦點可能會變成：

- input image 來源
- output rule
- 一組 text overlay steps
- 一組 sticker / watermark / crop steps

也就是說，未來比較可能從 `template` 架構，演進成 `pipeline + steps` 架構。

## 建議的雙流程共用切分

如果未來真的要往雙流程擴充，照目前程式最自然的共用邊界大概是：

1. `config_loader.py`
   - 保留為設定載入與驗證層
2. `excel_reader.py`
   - 保留為其中一種資料來源 adapter
3. `renderer.py`
   - 拆成「繪圖 primitives」與「流程型 renderer」
4. `main.py`
   - 改成流程路由入口，不再直接綁死單一 pipeline

可以想成：

```text
資料來源層
  Excel / CSV / JSON / 圖片清單

設定層
  ConfigLoader / schema validation

繪圖能力層
  resolve_path / load_font / parse_color / calculate_text_position / draw_text

流程層
  excel_to_image pipeline
  image_postprocess pipeline
```

## 總結

目前架構其實已經有一個不錯的 MVP 分層：

- `main.py` 負責編排
- `config_loader.py` 負責設定載入與驗證
- `excel_reader.py` 負責 Excel 轉列資料
- `renderer.py` 負責 Pillow 繪圖

它已經足以支撐「Excel 驅動的 template-based 文字貼圖」。  
若未來要往雙流程演進，最值得保留的是 `ConfigLoader` 與 `renderer.py` 內的基礎繪圖工具；最需要先重構的是 `main.py` 的單一路徑 orchestration，以及 `render_image()` 目前過於集中的責任。
