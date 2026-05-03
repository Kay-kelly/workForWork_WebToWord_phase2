# WorkForWork WebToWord

這個 repo 目前包含兩條路徑：

- 舊版圖片流程
  - `project/app/main.py`
  - 主要對應早期 `mapping.json` + 模板貼字流程
- 目前穩定中的 MVP 圖片流程
  - `project/app/pipeline_main.py`
  - 流程為 `shared data -> generate_image -> overlay_text`
  - 目前重點是 `cycle_diagram` 圖片產出

## 目前穩定版重點

目前主要驗證的是一套資料驅動的 cycle diagram 流程：

1. 由 Excel 讀入資料
2. 整理成 `SharedData`
3. `generate_image` 產生底圖
4. `overlay_text` 疊上文字
5. 輸出 PNG

目前已可用的圖像元素包含：

- cycle path 幾何
- marker
- guides
  - `dashed_line`
  - `arrow`
  - `dimension`
- overlay 文字

## 目前主要檔案

- `project/config/image_templates/cycle_diagram.json`
  - cycle diagram 主要設定
- `project/app/image/generate_image.py`
  - path、marker、guides 的主要實作
- `project/app/image/overlay_text.py`
  - 文字疊圖
- `project/app/pipelines/config_loader.py`
  - pipeline 與 template config 驗證
- `project/docs/cycle_diagram_marker_guide.md`
  - marker / anchor / path config 的實用說明

## 快速執行

請從 repo 根目錄執行：

```powershell
.\.venv\Scripts\python.exe project\app\pipeline_main.py
```

輸出位置：

```text
project/output/pipeline_mvp/
```

## 說明文件

- repo 對外總覽：本檔
- `project/README.md`
  - `project/` 目錄導引
- `project/docs/cycle_diagram_marker_guide.md`
  - cycle diagram 的設定與調整方式

## 注意

目前 repo 內仍保留早期流程與相容性程式碼，因此：

- 舊版 `main.py` 不代表目前唯一主流程
- `mapping.json` 也不是目前 cycle diagram MVP 的唯一設定來源

如果你要調整目前穩定版 cycle diagram，建議先看：

1. `project/config/image_templates/cycle_diagram.json`
2. `project/docs/cycle_diagram_marker_guide.md`
3. `project/app/image/generate_image.py`

## Setup

Required Python version: Python 3.11.9

建議使用 virtual environment。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Quick Start

Current entrypoint: `project/app/pipeline_main.py`

`app/main.py` is legacy.

1. Copy sample input:

```powershell
Copy-Item project\data\sample\demo_input.xlsx project\data\input.xlsx -Force
```

2. Run pipeline:

```powershell
python project/app/pipeline_main.py
```
