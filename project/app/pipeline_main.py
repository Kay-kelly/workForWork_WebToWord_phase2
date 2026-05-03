"""
pipeline_main.py

新的 MVP pipeline 入口。
先保留舊 main.py，可獨立執行最小流程：
shared data -> generate_image -> overlay_text
"""

import sys
from pathlib import Path

from excel_reader import read_excel_rows
from normalizers.excel_to_shared import normalize_excel_row
from pipelines.config_loader import PipelineConfigLoader
from pipelines.runner import run_pipeline


DEFAULT_PIPELINE_CONFIG_PATH = Path("config") / "pipelines" / "mvp_image_pipeline.json"


def get_base_dir() -> Path:
    """比照舊入口，取得 project 根目錄。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def main() -> None:
    """執行第一版最小 pipeline。"""
    base_dir = get_base_dir()
    pipeline_config_path = resolve_pipeline_config_path(base_dir)

    pipeline_config = PipelineConfigLoader(
        pipeline_config_path,
        base_dir=base_dir,
    ).load()
    excel_path = pipeline_config["input_excel_path"]
    output_dir = pipeline_config["output_dir"]
    raw_rows = read_excel_rows(excel_path)

    debug_grid = pipeline_config["render_defaults"].get("debug_grid", False)
    if "--debug" in sys.argv:
        debug_grid = True

    if not raw_rows:
        print("沒有可處理的 Excel 資料。")
        return

    for raw_row in raw_rows:
        shared_data = normalize_excel_row(
            raw_row,
            project_id=pipeline_config["project_id"],
            test_id=pipeline_config["test_id"],
        )

        final_output_path = run_pipeline(
            shared_data,
            pipeline_steps=pipeline_config["pipeline_steps"],
            template_config=pipeline_config["image_template_config"],
            global_config=pipeline_config["render_defaults"],
            base_dir=base_dir,
            output_dir=output_dir,
            debug_grid=debug_grid,
        )
        print(f"完成 MVP pipeline: {final_output_path}")


def resolve_pipeline_config_path(base_dir: Path) -> Path:
    """允許用 --config 指定外部 pipeline config。"""
    if "--config" in sys.argv:
        config_index = sys.argv.index("--config")
        if config_index + 1 >= len(sys.argv):
            raise ValueError("--config 後面必須接 config 路徑。")

        return resolve_cli_path(base_dir, sys.argv[config_index + 1])

    return base_dir / DEFAULT_PIPELINE_CONFIG_PATH


def resolve_cli_path(base_dir: Path, raw_path: str) -> Path:
    """解析 CLI 傳入的相對或絕對路徑。"""
    path = Path(raw_path)
    if path.is_absolute():
        return path

    return (base_dir / path).resolve()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Pipeline 執行失敗: {exc}")
        sys.exit(1)
