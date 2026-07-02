# -*- coding: utf-8 -*-
"""Convert field-list style QC test case markdown drafts into the xlsx template.

Expected TC format in the markdown:

    #### TC_NNN

    - **Title:** ...
    - **Pre-condition:**
      1. ...
    - **Step:**
      1. ...
    - **Expected Result:**
      1. ...
    - **Priority:** P0

Section headers:
    ## I. Operation: ...       -> level "screen"
    ### I.1. ...               -> level "section"

Usage:
    python md_to_xlsx_fieldlist.py --input PATH --uc-id UC-EXBOT-bot-start
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from typing import Union

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "templates", "Testcase_template.xlsx")
)
SHEET_NAME = "Test cases"
EXPECTED_HEADER_FIRST_CELL = "TC ID"

VERSION_SUFFIX_RE = re.compile(r"_v(\d+)\.xlsx$", re.IGNORECASE)
MOJIBAKE_MARKERS = ("Ã\x83", "Ã\x82", "Ä\x90", "â\x80", "\xc3\x83")
VIET_DIACRITIC_RE = re.compile(
    "[àáâãèéêìíòóôõùúýăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
    "ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐĨŨƠƯẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ]"
)

TC_HEADING_RE = re.compile(r"^####\s+(TC[_\-]?\d+)", re.IGNORECASE)
FIELD_RE = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)")
SECTION2_RE = re.compile(r"^##\s+(.+)")
SECTION3_RE = re.compile(r"^###\s+(.+)")


@dataclass
class TestCase:
    tc_id: str
    title: str = ""
    pre_conditions: str = ""
    test_steps: str = ""
    expected_result: str = ""
    priority: str = ""


@dataclass
class HeaderRow:
    text: str
    level: str  # "screen" or "section"


Item = Union[TestCase, HeaderRow]


def parse_md(path: str) -> list[Item]:
    items: list[Item] = []
    current_tc: TestCase | None = None
    current_field: str | None = None
    field_lines: list[str] = []

    def flush_field():
        nonlocal current_field, field_lines
        if current_tc is None or current_field is None:
            current_field = None
            field_lines = []
            return
        value = "\n".join(field_lines).strip()
        key = current_field.lower().replace("-", " ").strip()
        if "title" in key:
            current_tc.title = value
        elif "pre-condition" in key or "precondition" in key:
            current_tc.pre_conditions = value
        elif "step" in key:
            current_tc.test_steps = value
        elif "expected" in key:
            current_tc.expected_result = value
        elif "priority" in key:
            current_tc.priority = value
        current_field = None
        field_lines = []

    def flush_tc():
        nonlocal current_tc
        if current_tc is not None:
            flush_field()
            items.append(current_tc)
            current_tc = None

    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            stripped = line.strip()

            # Detect TC heading
            m = TC_HEADING_RE.match(stripped)
            if m:
                flush_tc()
                current_tc = TestCase(tc_id=m.group(1))
                continue

            # Detect ## section heading
            if stripped.startswith("#### ") and not TC_HEADING_RE.match(stripped):
                # sub-subheading that is not a TC — ignore
                continue

            m2 = SECTION2_RE.match(stripped)
            if m2 and not stripped.startswith("###"):
                flush_tc()
                items.append(HeaderRow(m2.group(1).strip(), level="screen"))
                continue

            m3 = SECTION3_RE.match(stripped)
            if m3:
                flush_tc()
                items.append(HeaderRow(m3.group(1).strip(), level="section"))
                continue

            # If we are inside a TC, collect field content
            if current_tc is not None:
                mf = FIELD_RE.match(stripped)
                if mf:
                    flush_field()
                    current_field = mf.group(1)
                    inline = mf.group(2).strip()
                    field_lines = [inline] if inline else []
                elif current_field is not None:
                    # continuation line
                    field_lines.append(line)

    flush_tc()
    return items


def next_version(output_dir: str, uc_id: str) -> int:
    versions = []
    for path in glob.glob(os.path.join(output_dir, "*.xlsx")):
        name = os.path.basename(path)
        if uc_id not in name:
            continue
        m = VERSION_SUFFIX_RE.search(name)
        if m:
            versions.append(int(m.group(1)))
    return (max(versions) + 1) if versions else 1


def write_workbook(items: list[Item], template_path: str, output_path: str) -> tuple[int, int]:
    shutil.copy2(template_path, output_path)
    wb = load_workbook(output_path)
    if SHEET_NAME not in wb.sheetnames:
        raise SystemExit(f"Template missing sheet '{SHEET_NAME}'.")
    ws = wb[SHEET_NAME]
    first = ws.cell(row=1, column=1).value
    if not (isinstance(first, str) and first.strip().lower() == EXPECTED_HEADER_FIRST_CELL.lower()):
        raise SystemExit(f"Row-1 col-A is {first!r}, expected '{EXPECTED_HEADER_FIRST_CELL}'.")

    if ws.max_row >= 2:
        ws.delete_rows(2, ws.max_row - 1)

    wrap_top = Alignment(wrap_text=True, vertical="top")
    bold = Font(bold=True)

    row = 2
    tc_count = 0
    header_count = 0
    for item in items:
        if isinstance(item, HeaderRow):
            cell = ws.cell(row=row, column=2, value=item.text)
            cell.font = bold
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            header_count += 1
        else:
            ws.cell(row=row, column=1, value=item.tc_id)
            ws.cell(row=row, column=2, value=item.title)
            ws.cell(row=row, column=3, value=item.pre_conditions)
            ws.cell(row=row, column=4, value=item.test_steps)
            ws.cell(row=row, column=5, value=item.expected_result)
            ws.cell(row=row, column=6, value=item.priority)
            for col in range(1, 7):
                ws.cell(row=row, column=col).alignment = wrap_top
            tc_count += 1
        row += 1

    wb.save(output_path)
    return tc_count, header_count


def verify_output(output_path: str, expected_tc: int) -> None:
    wb = load_workbook(output_path)
    ws = wb[SHEET_NAME]
    actual = sum(
        1 for r in range(2, ws.max_row + 1)
        if ws.cell(row=r, column=1).value and str(ws.cell(row=r, column=1).value).startswith("TC")
    )
    if actual != expected_tc:
        print(f"WARN: Expected {expected_tc} TC rows in xlsx, found {actual}.")
    else:
        print(f"OK: {actual} TC rows verified in xlsx.")

    # spot-check first 3 TC rows for non-empty fields
    checked = 0
    for r in range(2, ws.max_row + 1):
        tc_id = ws.cell(row=r, column=1).value
        if not (tc_id and str(tc_id).startswith("TC")):
            continue
        title = ws.cell(row=r, column=2).value or ""
        steps = ws.cell(row=r, column=4).value or ""
        exp = ws.cell(row=r, column=5).value or ""
        if not title.strip():
            print(f"WARN: {tc_id} — Title is empty.")
        if not steps.strip():
            print(f"WARN: {tc_id} — Test Steps is empty.")
        if not exp.strip():
            print(f"WARN: {tc_id} — Expected Result is empty.")
        checked += 1
        if checked >= 3:
            break

    # Check for mojibake
    bad = []
    for r in range(2, ws.max_row + 1):
        for c in range(2, 6):
            val = ws.cell(row=r, column=c).value
            if isinstance(val, str) and any(m in val for m in MOJIBAKE_MARKERS):
                bad.append((r, c))
    if bad:
        print(f"ERROR: Mojibake detected in {len(bad)} cell(s).")
    else:
        print("OK: No mojibake detected.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="Path to the .md draft file.")
    p.add_argument("--uc-id", required=True)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--template", default=DEFAULT_TEMPLATE)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not os.path.isfile(args.input):
        raise SystemExit(f"Input not found: {args.input}")

    items = parse_md(args.input)
    tc_total = sum(1 for i in items if isinstance(i, TestCase))
    header_total = sum(1 for i in items if isinstance(i, HeaderRow))
    print(f"Parsed: {tc_total} test cases, {header_total} header rows.")

    if tc_total == 0:
        raise SystemExit("Parser found 0 test cases — check heading format (#### TC_NNN).")

    output_dir = args.output_dir or os.path.dirname(os.path.abspath(args.input))
    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(args.input))[0]
    version = next_version(output_dir, args.uc_id)
    output_name = f"{base}_v{version}.xlsx"
    output_path = os.path.join(output_dir, output_name)
    print(f"Output: {output_path}")

    if args.dry_run:
        print("[dry-run] No file written.")
        return 0

    if not os.path.isfile(args.template):
        raise SystemExit(f"Template not found: {args.template}")

    if os.path.exists(output_path):
        raise SystemExit(f"Refusing to overwrite: {output_path}")

    tc, hdr = write_workbook(items, args.template, output_path)
    print(f"Wrote {tc} test cases + {hdr} header rows.")

    verify_output(output_path, tc_total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
