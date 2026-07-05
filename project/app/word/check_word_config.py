"""
Dry-run checker for Word template/config alignment.

This tool is intentionally read-only. It does not run the pipeline, render a
DOCX, modify the source template, or write to project/output/.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PLACEHOLDER_PATTERN = re.compile(
    r"\{\{(?:[#/]?repeat:[A-Za-z0-9_]+|[A-Za-z0-9_]+)\}\}"
)
REPEAT_START_PATTERN = re.compile(r"\{\{#repeat:[A-Za-z0-9_]+\}\}")


@dataclass
class CheckResult:
    config_path: Path
    template_path_raw: str = ""
    template_path: Path | None = None
    template_candidates: list[Path] = field(default_factory=list)
    template_exists: bool = False
    docx_readable: bool = False
    placeholders_found: set[str] = field(default_factory=set)
    placeholders_declared: set[str] = field(default_factory=set)
    known_unsupported: set[str] = field(default_factory=set)
    found_not_declared: set[str] = field(default_factory=set)
    declared_not_found: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_cli_path(args.config)
    result = check_word_config(config_path)
    print_result(result)
    return 0 if result.passed else 1


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run check a Word config against its DOCX template."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a Word config JSON file.",
    )
    return parser.parse_args(argv)


def resolve_cli_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path

    return (Path.cwd() / path).resolve()


def check_word_config(config_path: Path) -> CheckResult:
    result = CheckResult(config_path=config_path)
    config_data = load_json_config(config_path, result)
    if config_data is None:
        return result

    template_path_raw = config_data.get("template_path")
    if not isinstance(template_path_raw, str) or not template_path_raw.strip():
        result.failures.append("config missing non-empty template_path")
        return result

    result.template_path_raw = template_path_raw.strip()
    result.template_candidates = build_template_candidates(
        config_path,
        result.template_path_raw,
    )
    result.template_path = choose_template_path(result.template_candidates)
    result.template_exists = result.template_path.exists()

    result.placeholders_declared = collect_declared_placeholders(config_data)
    result.known_unsupported = collect_known_unsupported_placeholders(config_data)

    if not result.template_exists:
        result.failures.append(f"template_path does not exist: {result.template_path}")
        result.failures.append(
            "This template is a local ignored file. Place it locally at the "
            "configured path; do not commit the DOCX artifact."
        )
        return result

    xml_texts, error = read_docx_xml_texts(result.template_path)
    if error is not None:
        result.failures.append(error)
        return result

    result.docx_readable = True
    result.placeholders_found = collect_template_placeholders(xml_texts)
    result.known_unsupported.update(
        collect_placeholders_inside_unsupported_repeat_blocks(
            xml_texts,
            result.known_unsupported,
        )
    )

    declared_or_unsupported = result.placeholders_declared | result.known_unsupported
    result.found_not_declared = result.placeholders_found - declared_or_unsupported
    result.declared_not_found = result.placeholders_declared - result.placeholders_found

    if result.found_not_declared:
        result.failures.append(
            "template contains placeholders that are not declared in config "
            "and not listed as known unsupported"
        )

    if result.declared_not_found:
        result.warnings.append("config declares placeholders not found in template")

    return result


def load_json_config(config_path: Path, result: CheckResult) -> dict[str, Any] | None:
    if not config_path.exists():
        result.failures.append(f"config path does not exist: {config_path}")
        return None

    try:
        with config_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        result.failures.append(f"JSON parse failed: {exc}")
        return None
    except OSError as exc:
        result.failures.append(f"could not read config: {exc}")
        return None

    if not isinstance(data, dict):
        result.failures.append("JSON root must be an object")
        return None

    return data


def build_template_candidates(config_path: Path, template_path_raw: str) -> list[Path]:
    template_path = Path(template_path_raw)
    if template_path.is_absolute():
        return [template_path.resolve()]

    project_dir = Path(__file__).resolve().parents[2]
    repo_dir = project_dir.parent
    candidates = [
        (project_dir / template_path).resolve(),
        (repo_dir / template_path).resolve(),
        (config_path.parent / template_path).resolve(),
        (Path.cwd() / template_path).resolve(),
    ]

    deduped: list[Path] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)

    return deduped


def choose_template_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def read_docx_xml_texts(path: Path) -> tuple[list[str], str | None]:
    if not zipfile.is_zipfile(path):
        return [], f"docx is not a readable zip file: {path}"

    try:
        with zipfile.ZipFile(path) as docx_zip:
            xml_names = [
                name
                for name in docx_zip.namelist()
                if name.startswith("word/") and name.endswith(".xml")
            ]
            xml_texts = [
                xml_to_text(docx_zip.read(name).decode("utf-8", errors="replace"))
                for name in xml_names
            ]
    except (OSError, zipfile.BadZipFile) as exc:
        return [], f"docx could not be read: {exc}"

    return xml_texts, None


def xml_to_text(xml_text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", xml_text)
    return html.unescape(without_tags)


def collect_template_placeholders(xml_texts: list[str]) -> set[str]:
    placeholders: set[str] = set()
    for xml_text in xml_texts:
        placeholders.update(PLACEHOLDER_PATTERN.findall(xml_text))

    return placeholders


def collect_declared_placeholders(config_data: dict[str, Any]) -> set[str]:
    declared: set[str] = set()

    placeholders = config_data.get("placeholders")
    if isinstance(placeholders, dict):
        declared.update(
            key for key in placeholders if isinstance(key, str) and is_placeholder(key)
        )

    image_placeholders = config_data.get("image_placeholders")
    if isinstance(image_placeholders, dict):
        declared.update(
            key
            for key in image_placeholders
            if isinstance(key, str) and is_placeholder(key)
        )

    declared.update(extract_placeholder_values(config_data.get("placeholder_rules")))
    declared.update(extract_placeholder_values(config_data.get("image_rules")))
    declared.update(extract_placeholder_values(config_data.get("table_rules")))
    declared.update(extract_placeholder_values(config_data.get("repeat_block_rules")))
    declared.update(collect_repeat_rule_markers(config_data.get("repeat_block_rules")))
    declared.update(collect_known_unsupported_placeholders(config_data))

    return declared


def extract_placeholder_values(value: Any) -> set[str]:
    placeholders: set[str] = set()

    if isinstance(value, dict):
        placeholder = value.get("placeholder")
        if isinstance(placeholder, str) and is_placeholder(placeholder):
            placeholders.add(placeholder)

        for nested_value in value.values():
            placeholders.update(extract_placeholder_values(nested_value))

    if isinstance(value, list):
        for item in value:
            placeholders.update(extract_placeholder_values(item))

    return placeholders


def collect_repeat_rule_markers(value: Any) -> set[str]:
    markers: set[str] = set()

    if isinstance(value, dict):
        for key in ("start_marker", "end_marker"):
            marker = value.get(key)
            if isinstance(marker, str) and is_placeholder(marker):
                markers.add(marker)

        for nested_value in value.values():
            markers.update(collect_repeat_rule_markers(nested_value))

    if isinstance(value, list):
        for item in value:
            markers.update(collect_repeat_rule_markers(item))

    return markers


def collect_known_unsupported_placeholders(config_data: dict[str, Any]) -> set[str]:
    return extract_marker_values(config_data.get("known_unsupported"))


def extract_marker_values(value: Any) -> set[str]:
    markers: set[str] = set()

    if isinstance(value, dict):
        for key in ("placeholder", "start_marker", "end_marker"):
            marker = value.get(key)
            if isinstance(marker, str) and is_placeholder(marker):
                markers.add(marker)

        for nested_value in value.values():
            if isinstance(nested_value, (dict, list)):
                markers.update(extract_marker_values(nested_value))

    if isinstance(value, list):
        for item in value:
            markers.update(extract_marker_values(item))

    return markers


def collect_placeholders_inside_unsupported_repeat_blocks(
    xml_texts: list[str],
    known_unsupported: set[str],
) -> set[str]:
    repeat_block_placeholders: set[str] = set()
    unsupported_start_markers = [
        marker
        for marker in known_unsupported
        if REPEAT_START_PATTERN.fullmatch(marker)
    ]

    for start_marker in unsupported_start_markers:
        end_marker = start_marker.replace("{{#repeat:", "{{/repeat:", 1)
        if end_marker not in known_unsupported:
            continue

        for xml_text in xml_texts:
            search_from = 0
            while True:
                start_index = xml_text.find(start_marker, search_from)
                if start_index == -1:
                    break

                end_index = xml_text.find(end_marker, start_index + len(start_marker))
                if end_index == -1:
                    break

                block_text = xml_text[
                    start_index : end_index + len(end_marker)
                ]
                repeat_block_placeholders.update(
                    PLACEHOLDER_PATTERN.findall(block_text)
                )
                search_from = end_index + len(end_marker)

    return repeat_block_placeholders


def is_placeholder(value: str) -> bool:
    return PLACEHOLDER_PATTERN.fullmatch(value) is not None


def print_result(result: CheckResult) -> None:
    print(f"config path: {result.config_path}")
    print(f"template_path raw: {result.template_path_raw or '<missing>'}")
    print(f"template path: {result.template_path or '<unresolved>'}")
    print(f"template exists: {str(result.template_exists).lower()}")
    print(f"docx readable: {str(result.docx_readable).lower()}")

    if result.template_candidates:
        print_list("template candidates checked", result.template_candidates)

    print_list("placeholders found in template", result.placeholders_found)
    print_list("placeholders declared in config", result.placeholders_declared)
    print_list("placeholders found but not declared", result.found_not_declared)
    print_list("placeholders declared but not found", result.declared_not_found)
    print_list("known unsupported placeholders / markers", result.known_unsupported)

    if result.warnings:
        print_list("warnings", result.warnings)

    if result.failures:
        print_list("failures", result.failures)

    print(f"final result: {'PASS' if result.passed else 'FAIL'}")


def print_list(label: str, values) -> None:
    values_list = sorted(str(value) for value in values)
    print(f"{label}:")
    if not values_list:
        print("  - <none>")
        return

    for value in values_list:
        print(f"  - {value}")


if __name__ == "__main__":
    sys.exit(main())
