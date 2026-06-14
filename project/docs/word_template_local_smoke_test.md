# Word Template Local Smoke Test Guide

本文件說明如何在本機驗證 Word template config 與本機 DOCX template 是否對齊。這是一個安全的 dry-run 流程，只檢查 config/template，不產生 Word、不修改 `project/output/`，也不實作 repeat block renderer。

## 1. 文件目的

本文件用於協助開發者在本機確認：

- Word config JSON 可解析。
- `template_path` 指向的本機 DOCX template 存在。
- DOCX 是可讀的 Word 檔。
- template 內 placeholder 與 config 宣告大致對齊。
- repeat block marker 已被正確列為目前尚未支援項目。

## 2. 為什麼 DOCX 不進 repo

即使 `deidentified_report_template_repeat.docx` 是去識別化範本，仍先保守留在本機，不放入 repo。

目前 repo 只保存：

- mapping spec
- smoke test config
- dry-run checker
- 相關文件

DOCX template 由開發者自行放到指定路徑：

```text
project/templates/word/deidentified_report_template_repeat.docx
```

此檔案已被 `.gitignore` 忽略，不應 commit。

## 3. 本機需要準備的檔案

必要的本機 DOCX：

```text
project/templates/word/deidentified_report_template_repeat.docx
```

追蹤中的 config：

```text
project/config/word_templates/deidentified_word_report.json
```

## 4. 檢查本機 DOCX 是否存在

在 repo root 執行：

```powershell
Test-Path project\templates\word\deidentified_report_template_repeat.docx
```

結果判讀：

- `True`：本機 DOCX 已存在，可以跑 dry-run checker。
- `False`：需要先手動放置 DOCX 到指定路徑。

## 5. 執行 dry-run checker

在 repo root 執行：

```powershell
.\.venv\Scripts\python.exe project\app\word\check_word_config.py --config project\config\word_templates\deidentified_word_report.json
```

此指令只讀取 config 與本機 DOCX，不會執行 `pipeline_main.py`，也不會寫入 `project/output/`。

## 6. PASS 的意義

`PASS` 代表：

- JSON 可解析。
- `template_path` 存在。
- DOCX 可讀。
- template 內 placeholder 與 config 宣告大致對齊。
- known unsupported / repeat marker 已被正確列為未支援項目。

`PASS` 不代表：

- `build_word.py` 已支援 repeat block。
- 已產生正式 Word 報告。
- 已完成正式排版驗收。
- 目前 template 可以直接作為 production output。

## 7. FAIL 的常見原因

常見 `FAIL` 原因：

- DOCX 不存在。
- `template_path` 設定錯誤。
- JSON 格式錯誤。
- DOCX 不是有效 Word 檔。
- template 有 placeholder，但 config 沒宣告。
- repeat marker 沒有列入 `known_unsupported` 或 `repeat_block_rules`。

若 DOCX 不存在，dry-run 應清楚提示該 template 是本機 ignored 檔案，開發者需自行放置到指定路徑。

## 8. declared-but-not-found warning 的意義

`declared-but-not-found` warning 通常代表 config 有預留 placeholder，但目前 template 裡暫時沒用到。

目前可先視為 warning，不一定是錯誤。後續若要收斂正式報告 template，可再決定是否移除多餘 placeholder 或補回 template。

## 9. 與 inspect_word.py 的差異

`check_word_config.py`：

- 檢查 template/config 對齊狀態。
- 不產生 Word。
- 不讀取 pipeline output。
- 不修改 `project/output/`。

`inspect_word.py`：

- 檢查 pipeline 產生後的 output DOCX。
- 用於確認已生成的 DOCX 可開啟、必要文字存在、沒有 unresolved placeholder，且包含圖片。

## 10. 禁止事項

- 不要 commit `project/templates/word/deidentified_report_template_repeat.docx`。
- 不要 commit `project/output/`。
- dry-run 不應修改任何 DOCX。
- dry-run 不應執行 `pipeline_main.py`。
- dry-run 不代表 repeat block 已實作。

## 11. 建議下一步

建議流程：

1. 先用 dry-run 確認本機 template/config 對齊。
2. 再規劃 deidentified template 接入 pipeline smoke test。
3. repeat block renderer 之後再獨立實作，避免和 template 對接、config 檢查混在同一個變更中。
