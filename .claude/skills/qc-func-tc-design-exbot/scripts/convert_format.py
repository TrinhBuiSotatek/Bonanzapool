#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert heading+bullets TC format to markdown table format expected by md_to_xlsx.py.

Input format:
    #### TC_001
    - **Title:** ...
    - **Pre-condition:**
      1. ...
    - **Step:**
      1. ...
    - **Expected Result:**
      1. ...
    - **Priority:** P0

Output format:
    | TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
    |---|---|---|---|---|---|
    | TC_001 | ... | 1. ... | 1. ... | 1. ... | P0 |
"""
import re
import sys

def collect_numbered_lines(lines, start_idx):
    """Collect continuation lines (numbered items) starting after start_idx."""
    items = []
    i = start_idx
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Stop if we hit a new bullet or heading
        if stripped.startswith('- **') or stripped.startswith('####') or stripped.startswith('###') or stripped.startswith('##') or stripped.startswith('#'):
            break
        if stripped == '':
            # Empty line may separate sections — peek ahead
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if next_stripped.startswith('- **') or next_stripped.startswith('####') or next_stripped.startswith('###') or next_stripped.startswith('#') or next_stripped == '':
                    break
            else:
                break
        if re.match(r'^\d+\.', stripped):
            items.append(stripped)
        i += 1
    return items, i


def escape_pipes(text):
    """Escape pipe characters inside cell content."""
    return text.replace('|', '\\|')


def items_to_cell(items):
    """Join numbered items with literal \\n for the table cell."""
    if not items:
        return ''
    return '\\n'.join(escape_pipes(it) for it in items)


def parse_and_convert(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output = []
    i = 0
    # Track whether we're inside an operation or section block (for inserting table header)
    in_table = False

    while i < len(lines):
        line = lines[i].rstrip('\n')
        stripped = line.strip()

        # H1 prelude: pass through unchanged
        if stripped.startswith('# ') or stripped.startswith('**') or stripped == '---' or stripped == '':
            if in_table and stripped == '':
                pass  # skip blank lines inside table region
            else:
                output.append(line)
            i += 1
            continue

        # #### heading (RTM table header in prelude) — pass through
        if stripped.startswith('#### ') and not re.match(r'^#### TC_\d+', stripped):
            output.append(line)
            in_table = False
            i += 1
            continue

        # ## Operation group header — pass through, reset table state
        if stripped.startswith('## ') and not stripped.startswith('### '):
            output.append('')
            output.append(line)
            in_table = False
            i += 1
            continue

        # ### section header — pass through, emit table header
        if stripped.startswith('### '):
            output.append('')
            output.append(line)
            output.append('')
            output.append('| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |')
            output.append('|---|---|---|---|---|---|')
            in_table = True
            i += 1
            continue

        # #### TC_XXX heading — parse the full TC block
        if re.match(r'^#### TC_\d+', stripped):
            tc_id = stripped[5:].strip()  # e.g. TC_001
            i += 1
            # Skip blank line after heading
            while i < len(lines) and lines[i].strip() == '':
                i += 1

            title = ''
            pre_items = []
            step_items = []
            expected_items = []
            priority = ''

            while i < len(lines):
                l = lines[i].rstrip('\n')
                ls = l.strip()

                if ls.startswith('- **Title:**'):
                    title = ls[len('- **Title:**'):].strip()
                    i += 1
                elif ls.startswith('- **Pre-condition:**') or ls.startswith('- **Pre-conditions:**'):
                    i += 1
                    pre_items, i = collect_numbered_lines(lines, i)
                elif ls.startswith('- **Step:**') or ls.startswith('- **Steps:**'):
                    i += 1
                    step_items, i = collect_numbered_lines(lines, i)
                elif ls.startswith('- **Expected Result:**') or ls.startswith('- **Expected Results:**'):
                    i += 1
                    expected_items, i = collect_numbered_lines(lines, i)
                elif ls.startswith('- **Priority:**'):
                    priority = ls[len('- **Priority:**'):].strip()
                    i += 1
                    break
                elif ls == '' or ls.startswith('####') or ls.startswith('###') or ls.startswith('##'):
                    break
                else:
                    i += 1

            # Build table row
            title_cell = escape_pipes(title)
            pre_cell = items_to_cell(pre_items)
            step_cell = items_to_cell(step_items)
            exp_cell = items_to_cell(expected_items)
            row = f'| {tc_id} | {title_cell} | {pre_cell} | {step_cell} | {exp_cell} | {priority} |'
            output.append(row)
            continue

        # RTM table rows and other table lines — pass through unchanged
        if stripped.startswith('|'):
            output.append(line)
            i += 1
            continue

        # Any other line — pass through
        output.append(line)
        i += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
        if not output[-1].endswith('\n'):
            f.write('\n')

    print(f"Written: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: convert_format.py <input.md> <output.md>")
        sys.exit(1)
    parse_and_convert(sys.argv[1], sys.argv[2])
