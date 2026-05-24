"""
Minimal Word report builder for the config-driven pipeline.

This module intentionally stays thin: it creates one DOCX per SharedData row,
adds a small metadata section, selected payload fields, and the final PNG from
the image pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from models.shared_data import SharedData


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]+')


def build_word(
    shared_data: SharedData,
    *,
    word_config: dict,
    image_path: Path,
    base_dir: Path,
) -> Path:
    """Create a minimal DOCX report for one SharedData record."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"build_word input image not found: {image_path}")

    output_path = build_output_path(shared_data, word_config, base_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = Document()
    configure_document(document)

    add_title(document, word_config)
    add_metadata_table(document, shared_data)
    add_payload_table(document, shared_data, word_config)
    add_image(document, image_path, word_config)

    document.save(output_path)
    return output_path


def configure_document(document: Document) -> None:
    """Apply simple page and type defaults."""
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(10.5)


def add_title(document: Document, word_config: dict) -> None:
    title = str(word_config.get("title", "MVP Image Report")).strip()
    paragraph = document.add_heading(title, level=0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_metadata_table(document: Document, shared_data: SharedData) -> None:
    document.add_heading("Metadata", level=1)
    rows = [
        ("record_id", shared_data.record_id),
        ("project_id", shared_data.project_id),
        ("test_id", shared_data.test_id),
        ("batch_sequence_id", shared_data.batch_sequence_id),
    ]
    add_key_value_table(document, rows)


def add_payload_table(
    document: Document,
    shared_data: SharedData,
    word_config: dict,
) -> None:
    fields = word_config.get("fields", [])
    if not isinstance(fields, list) or not fields:
        return

    document.add_heading("Payload", level=1)
    rows: list[tuple[str, Any]] = []
    for field_config in fields:
        if not isinstance(field_config, dict):
            continue

        source = str(field_config.get("source", "")).strip()
        if not source:
            continue

        label = str(field_config.get("label", source)).strip() or source
        value = shared_data.get_value(source)
        rows.append((label, "" if value is None else value))

    if rows:
        add_key_value_table(document, rows)


def add_key_value_table(document: Document, rows: list[tuple[str, Any]]) -> None:
    table = document.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.style = "Table Grid"

    for label, value in rows:
        cells = table.add_row().cells
        cells[0].text = str(label)
        cells[1].text = str(value)
        for cell in cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    document.add_paragraph()


def add_image(document: Document, image_path: Path, word_config: dict) -> None:
    image_config = word_config.get("image", {})
    if not isinstance(image_config, dict):
        image_config = {}

    caption = str(image_config.get("caption", "Generated image")).strip()
    if caption:
        paragraph = document.add_heading(caption, level=1)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

    width_inches = float(image_config.get("width_inches", 6.5))
    image_paragraph = document.add_paragraph()
    image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = image_paragraph.add_run()
    run.add_picture(str(image_path), width=Inches(width_inches))


def build_output_path(
    shared_data: SharedData,
    word_config: dict,
    base_dir: Path,
) -> Path:
    output_dir = resolve_project_path(
        base_dir,
        str(word_config.get("output_dir", "output/pipeline_mvp/word")),
    )
    filename_pattern = str(word_config.get("filename_pattern", "{record_id}.docx"))
    filename = render_filename_pattern(filename_pattern, shared_data)

    if not filename.strip():
        filename = shared_data.record_id

    if not filename.lower().endswith(".docx"):
        filename = f"{filename}.docx"

    return output_dir / sanitize_filename(filename)


def render_filename_pattern(pattern: str, shared_data: SharedData) -> str:
    values = {
        "record_id": shared_data.record_id,
        "project_id": shared_data.project_id,
        "test_id": shared_data.test_id,
        "batch_sequence_id": shared_data.batch_sequence_id,
    }
    values.update(
        {
            key: "" if value is None else str(value)
            for key, value in shared_data.payload.items()
        }
    )
    return pattern.format_map(DefaultFormatValues(values))


def sanitize_filename(filename: str) -> str:
    filename = INVALID_FILENAME_CHARS.sub("_", filename).strip()
    return filename or "report.docx"


def resolve_project_path(base_dir: Path, reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path

    return (Path(base_dir) / path).resolve()


class DefaultFormatValues(dict):
    def __missing__(self, key: str) -> str:
        return ""
