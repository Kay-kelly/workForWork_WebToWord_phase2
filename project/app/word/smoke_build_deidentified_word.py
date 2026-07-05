"""
Local smoke build for the deidentified Word template.

This script intentionally avoids the main pipeline and does not implement
repeat-block rendering. It writes one ignored DOCX artifact under project/output/
so developers can see how far the current build_word MVP gets with the
deidentified template.
"""

from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = PROJECT_DIR.parent
CONFIG_PATH = PROJECT_DIR / "config" / "word_templates" / "deidentified_word_report.json"
TEMPLATE_PATH = PROJECT_DIR / "templates" / "word" / "deidentified_report_template_repeat.docx"
IMAGE_PATH = PROJECT_DIR / "output" / "pipeline_mvp" / "report_cycle_2.png"
OUTPUT_PATH = PROJECT_DIR / "output" / "pipeline_mvp" / "word" / "deidentified_smoke_report.docx"

PLACEHOLDER_PATTERN = re.compile(
    r"\{\{(?:[#/]?repeat:[A-Za-z0-9_]+|[A-Za-z0-9_]+)\}\}"
)
REPEAT_START_PATTERN = re.compile(r"\{\{#repeat:[A-Za-z0-9_]+\}\}")


def main() -> int:
    sys.path.insert(0, str(APP_DIR))

    try:
        from models.shared_data import SharedData
        from word.build_word import build_word
    except ImportError as exc:
        print(f"FAIL: could not import build_word dependencies: {exc}")
        return 1

    config_data = load_config(CONFIG_PATH)
    if config_data is None:
        return 1

    if not TEMPLATE_PATH.exists():
        print("FAIL: deidentified Word template not found")
        print(f"template path: {TEMPLATE_PATH}")
        print("This DOCX is a local ignored file and is not committed to repo.")
        print("Place it at the path above before running this smoke build.")
        return 1

    if not IMAGE_PATH.exists():
        print("FAIL: smoke input image not found")
        print(f"image path: {IMAGE_PATH}")
        print("Run the existing MVP pipeline first, or provide the expected ignored PNG artifact.")
        return 1

    word_config = dict(config_data)
    word_config["filename_pattern"] = OUTPUT_PATH.name

    shared_data = SharedData(
        record_id="deidentified-smoke-record",
        project_id="deidentified_smoke_project",
        test_id="thermal_vacuum_smoke",
        batch_sequence_id="smoke-batch-001",
        payload={
            "output_name": "deidentified_smoke_report",
            "report_title": "Deidentified Thermal Vacuum Test Report",
            "test_procedure_title": "Deidentified Test Procedure",
            "test_name": "Thermal Vacuum Test",
            "requirement_source": "Deidentified Requirement Source",
            "cycle_count": 2,
            "high_temperature": "+85 C",
            "low_temperature": "-40 C",
            "pressure_tolerance": "< 1.0E-5 torr",
            "non_operation_condition": "Non-operating thermal vacuum condition",
            "operation_condition": "Operating thermal vacuum condition",
            "temperature_tolerance": "+/- 3 C",
        },
        source_info={
            "source_type": "smoke_build_deidentified_word",
            "row_number": 1,
        },
    )

    try:
        output_path = build_word(
            shared_data,
            word_config=word_config,
            image_path=IMAGE_PATH,
            base_dir=PROJECT_DIR,
        )
    except Exception as exc:
        print(f"FAIL: build_word failed: {exc}")
        return 1

    if not output_path.exists():
        print("FAIL: build_word completed but output DOCX was not produced")
        print(f"expected output docx path: {output_path}")
        return 1

    unresolved, structurally_unsupported = collect_unresolved_placeholders(output_path)
    known_unsupported = collect_known_unsupported(
        config_data,
        unresolved,
        structurally_unsupported,
    )
    unexpected_unresolved = unresolved - known_unsupported

    print(f"output docx path: {output_path}")
    print(f"template path: {TEMPLATE_PATH}")
    print(f"unresolved placeholders count: {len(unresolved)}")
    print(f"known unsupported markers count: {len(known_unsupported & unresolved)}")
    print_list("unresolved placeholders", unresolved)
    print_list("known unsupported unresolved", known_unsupported & unresolved)
    print_list("unexpected unresolved placeholders", unexpected_unresolved)

    if unexpected_unresolved:
        print("final result: FAIL")
        return 1

    if unresolved:
        print("final result: WARN")
        return 0

    print("final result: PASS")
    return 0


def load_config(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        print(f"FAIL: config not found: {path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"FAIL: config JSON parse failed: {exc}")
        return None
    except OSError as exc:
        print(f"FAIL: could not read config: {exc}")
        return None

    if not isinstance(data, dict):
        print("FAIL: config JSON root must be an object")
        return None

    return data


def collect_unresolved_placeholders(docx_path: Path) -> tuple[set[str], set[str]]:
    if not zipfile.is_zipfile(docx_path):
        return set(), set()

    unresolved: set[str] = set()
    structurally_unsupported: set[str] = set()
    with zipfile.ZipFile(docx_path) as docx_zip:
        for name in docx_zip.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue

            xml_text = docx_zip.read(name).decode("utf-8", errors="replace")
            text = xml_to_text(xml_text)
            placeholders = set(PLACEHOLDER_PATTERN.findall(text))
            unresolved.update(placeholders)
            structurally_unsupported.update(collect_repeat_block_placeholders(text))
            structurally_unsupported.update(collect_text_box_placeholders(xml_text))

    return unresolved, structurally_unsupported


def xml_to_text(xml_text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", xml_text))


def collect_known_unsupported(
    config_data: dict[str, Any],
    unresolved: set[str],
    repeat_block_unresolved: set[str],
) -> set[str]:
    known = extract_marker_values(config_data.get("known_unsupported"))
    known.update(extract_repeat_markers(config_data.get("repeat_block_rules")))
    known.update(collect_repeat_marker_pairs(unresolved))
    if any(REPEAT_START_PATTERN.fullmatch(marker) for marker in known):
        known.update(repeat_block_unresolved)
    return known


def extract_marker_values(value: Any) -> set[str]:
    markers: set[str] = set()

    if isinstance(value, dict):
        for key in ("placeholder", "start_marker", "end_marker"):
            marker = value.get(key)
            if isinstance(marker, str) and PLACEHOLDER_PATTERN.fullmatch(marker):
                markers.add(marker)

        for nested_value in value.values():
            if isinstance(nested_value, (dict, list)):
                markers.update(extract_marker_values(nested_value))

    if isinstance(value, list):
        for item in value:
            markers.update(extract_marker_values(item))

    return markers


def extract_repeat_markers(value: Any) -> set[str]:
    markers: set[str] = set()

    if isinstance(value, dict):
        for key in ("start_marker", "end_marker"):
            marker = value.get(key)
            if isinstance(marker, str) and PLACEHOLDER_PATTERN.fullmatch(marker):
                markers.add(marker)

        for nested_value in value.values():
            markers.update(extract_repeat_markers(nested_value))

    if isinstance(value, list):
        for item in value:
            markers.update(extract_repeat_markers(item))

    return markers


def collect_repeat_marker_pairs(placeholders: set[str]) -> set[str]:
    markers: set[str] = set()
    for placeholder in placeholders:
        if not REPEAT_START_PATTERN.fullmatch(placeholder):
            continue

        end_marker = placeholder.replace("{{#repeat:", "{{/repeat:", 1)
        if end_marker in placeholders:
            markers.add(placeholder)
            markers.add(end_marker)

    return markers


def collect_repeat_block_placeholders(text: str) -> set[str]:
    placeholders: set[str] = set()
    for start_match in REPEAT_START_PATTERN.finditer(text):
        start_marker = start_match.group(0)
        end_marker = start_marker.replace("{{#repeat:", "{{/repeat:", 1)
        end_index = text.find(end_marker, start_match.end())
        if end_index == -1:
            continue

        block_text = text[start_match.start() : end_index + len(end_marker)]
        placeholders.update(PLACEHOLDER_PATTERN.findall(block_text))

    return placeholders


def collect_text_box_placeholders(xml_text: str) -> set[str]:
    placeholders: set[str] = set()
    for match in re.finditer(r"<w:txbxContent\b.*?</w:txbxContent>", xml_text, re.DOTALL):
        placeholders.update(PLACEHOLDER_PATTERN.findall(xml_to_text(match.group(0))))

    return placeholders


def print_list(label: str, values: set[str]) -> None:
    print(f"{label}:")
    if not values:
        print("  - <none>")
        return

    for value in sorted(values):
        print(f"  - {value}")


if __name__ == "__main__":
    sys.exit(main())
