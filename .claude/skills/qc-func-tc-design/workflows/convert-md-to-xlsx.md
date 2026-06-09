## Convert Test Cases MD → XLSX (Phase 3 — Auto-triggered Workflow)

> **Trigger:** This workflow is auto-triggered by `SKILL.md` → Step B, after Phase 2 (`.md` file written) finishes. Do NOT invoke this workflow directly outside that orchestration.
>
> **Phase mapping (per `SKILL.md` → "Phase Map"):** This entire file IS Phase 3 — MD → XLSX Conversion.
>
> **Checkpoint references:** all phase-boundary write/update steps follow `SKILL.md` → "Checkpoint & Resume Protocol" §5. Do NOT duplicate those rules here.

### Purpose

Convert the finalized test case markdown into the project's standard `.xlsx` artifact, using the shared converter script. This workflow performs format translation only — no test case content is added, removed, or rewritten here. Encoding and layout requirements are governed by `qc-func-tc-design/rules/testcase-instruction-rules.md` (Rules 0a–0d, "Sheet Layout & Section Headers").

---

## Phase 3 — MD → XLSX Conversion

### Phase 3 Multi-variant Loop Overview

Phase 3 is **per-variant**. It executes in two passes:

**Pass A — Verification Gate (Step 0):** for EACH variant listed in the `## Phase 2 Summary` block (top-level `**Variants in scope:**` line), run Step 0.1 → 0.2 → 0.3. If ALL variants pass (with auto-recovery if needed) → advance `last_phase_done` to `2` ONCE for the whole UC and proceed to Pass B. If ANY variant fails irrecoverably → STOP and do NOT advance `last_phase_done`.

**Pass B — Convert (Step 1 → Step 4):** for EACH variant, locate that variant's md → verify prerequisites → run converter → self-verify the produced xlsx. After ALL variants complete Pass B successfully → advance `last_phase_done` to `3` and update worklog/dashboard with all xlsx paths.

For single-variant projects, both loops run exactly once. For update workflow runs, both loops also run exactly once (update is always single-variant per run).

### Step 0: Phase 2 Verification Gate + Auto-recovery (MANDATORY — runs BEFORE any other Phase 3 work)

This step is the **single gate** that decides whether Phase 2 truly produced a complete final md for every variant. It compares each variant's deliverable md against that variant's `### Variant: <name>` sub-block in the `## Phase 2 Summary` of `progress.md`. Mismatches trigger auto-recovery (overwrite the variant's same-version md from its scratch); irrecoverable failures STOP the skill.

This step is per `SKILL.md` → "Checkpoint & Resume Protocol" §5.1 (start-of-phase / transition write): it is what advances `last_phase_done` from `1` to `2` for the UC. No other code path in this skill is allowed to advance `last_phase_done` to `2`.

#### Step 0.1 — Read the Phase 2 Summary

1. Open `.claude/skills/qc-func-tc-design/process-logging/<UC-ID>/progress.md`.
2. Locate the `## Phase 2 Summary` block. Parse:
   - The top-level `**Variants in scope:**` line → the ordered list of variant names V₁, V₂, …, Vₙ.
   - For each variant Vᵢ, locate its `### Variant: <Vᵢ>` sub-block and extract: `Total test cases designed`, `GUI total`, `FUNC total`, `Output language`, `Scratch` (absolute path), `Final MD file(s)` (list of absolute paths), and the per-screen table.
3. If the entire `## Phase 2 Summary` block is **missing**:
   - Probe `process-logging/<UC-ID>/` for any `02_designed_tcs_*.md` files.
   - **If at least one scratch exists** → derive a `## Phase 2 Summary` block from the discovered scratches (one `### Variant: <V>` sub-block per scratch found, with `Variants in scope:` listing them all). Write it back to progress.md (atomic). Then jump to Step 0.2 with this derived summary.
   - **If NO scratches exist** → STOP and report on chat: "Phase 2 scratches never persisted (Step 3.5 didn't run before interrupt). Cannot auto-recover. Restart the skill to re-design from Phase 1." Do NOT advance `last_phase_done`. Do NOT continue Phase 3.
4. If the block exists but is missing the `**Variants in scope:**` line, treat as "block missing" per case 3 above.

#### Step 0.2 — Count Actual TCs Per Variant

For EACH variant Vᵢ in the parsed Variants-in-scope list, in order:

1. Open variant Vᵢ's final md file(s) at the path(s) listed in its sub-block (single-file or all parts in order).
2. Parse the md:
   - For each `## <Roman>. <screen-name>` heading, start a new screen group.
   - Inside each screen, GUI count = rows matching the TC ID pattern in the table(s) following `### <Roman>.1. …`; FUNC count = rows matching the TC ID pattern following `### <Roman>.2. …`. Use the TC ID pattern `^\| TC_\d+ \|` (one count per matching row in test case tables).
3. Compute for variant Vᵢ: actual total, actual GUI total, actual FUNC total, actual per-screen totals.

> **TC ID pattern caveat:** The pattern `^\| TC_\d+ \|` matches the conventional `TC_001`, `TC_002`, etc. produced by `references/Testcase-refer-*.md`. If a project's `rules/testcase-instruction-rules.md` declares a different TC ID convention (e.g., `TC-01`, `TC_AUTH_001`), adjust this pattern accordingly when running Phase 3 — failing to adjust would make every check fail and trigger spurious auto-recovery. Verify the pattern matches the project's actual convention before relying on this gate.

#### Step 0.3 — Compare and Decide (per variant)

For EACH variant Vᵢ, run these checks in order; the FIRST failed check for Vᵢ triggers auto-recovery for THAT variant:

| Check | Pass condition |
|---|---|
| Total | `summary[Vᵢ].total == actual[Vᵢ].total` |
| GUI / FUNC totals | `summary[Vᵢ].gui == actual[Vᵢ].gui` AND `summary[Vᵢ].func == actual[Vᵢ].func` |
| Screen set | every screen name in Vᵢ's summary table appears as a `## <Roman>.` heading in Vᵢ's md, AND vice versa |
| Per-screen totals | for every screen of Vᵢ, `summary[Vᵢ][screen].total == actual[Vᵢ][screen].total` AND same for GUI / FUNC |

**If ALL variants pass (no auto-recovery needed, OR auto-recovery succeeded for the ones that failed) — advance the UC to Phase 3:** (Per `SKILL.md` §5.1 transition write; ordering: progress.md → worklog → dashboard.)

1. **Update `progress.md`** → `last_phase_done: 2`, `next_phase: 3`, `updated_at: <now>`. (Preserve all existing fields including the `## Phase 2 Summary` block.)
2. **Worklog**: rewrite last entry → `status = "Running (Phase 3)"`. (No new `input` files appended for Phase 3 — the Phase 2 final mds were already recorded in `output` at end of Phase 2.)
3. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Running — Chuyển MD sang XLSX` (VI) / `Running — MD → XLSX Conversion` (EN). Skip if column missing (graceful degradation).
4. Proceed to Pass B (Step 1 below).

**If a variant Vᵢ FAILS the checks → Auto-recovery for Vᵢ (no user prompt):**
1. Report on chat (informational, not blocking):
   ```
   ℹ️ Phase 3 detected mismatch in variant <Vᵢ> between its final md and the Phase 2 Summary — auto-recovering from scratch.
   Expected (summary): <total> TCs, <screens summary>
   Actual (final md):  <total> TCs, <screens actual>
   ```
2. Check `process-logging/<UC-ID>/02_designed_tcs_<Vᵢ>.md` exists.
   - **If Vᵢ's scratch missing** → STOP and report: "Variant <Vᵢ>: no scratch available. Phase 2 scratch for <Vᵢ> never persisted. Restart the skill to re-design from Phase 1." Do NOT advance `last_phase_done`. Do NOT continue with any remaining variant.
   - **If Vᵢ's scratch exists** → Read it. Determine the target deliverable path for Vᵢ (same path(s) as the variant's partial md, SAME version — overwrite, do NOT bump version). If the deliverable was multi-part, re-derive the same partition strategy from the scratch and write the same parts (overwrite each, same filenames). Each part is an atomic single Write.
     - **Exception to the immutable-versions rule:** This same-version overwrite is the ONE place in this skill where versioned output files are overwritten in place, contradicting `rules/naming-convention.md` ("versions are immutable"). The justification: the partial md is provably wrong (verification gate detected it), so it is not a real "v[N]" — overwriting it produces the v[N] that was always intended. No history is lost because the partial md was never a deliverable accepted by anyone. Do NOT generalize this exception elsewhere in the skill.
3. After recovery write completes for Vᵢ, **re-run Step 0.2 and Step 0.3 for Vᵢ only**.
4. If Vᵢ's verification now passes → continue to the next variant in the gate loop. Add a line to the chat report (kept for Step C reporting): "Auto-recovery executed for variant <Vᵢ>: rewrote `<path>` from scratch."
5. If Vᵢ's verification **still fails after recovery** → STOP and report: "Variant <Vᵢ>: scratch and final md still mismatch the Phase 2 Summary — possible corruption. Manual inspection required. Expected: <...>; scratch-sourced md: <...>; summary: <...>." Do NOT advance `last_phase_done`. Do NOT run the converter for any variant.

After the gate finishes (ALL variants passed), proceed to Step 1.

### Step 1: Locate the MD Input (per variant — Pass B loop start)

For EACH variant Vᵢ in the Variants-in-scope list, perform Step 1 → Step 4 in order before moving to the next variant:

- Identify Vᵢ's finalized `.md` file(s) using the `Final MD file(s)` paths from the Phase 2 Summary sub-block:
  - Single-file output: one `.md` at the test case folder for Vᵢ.
  - Multi-part output: multiple `[UC-ID]_*_<Vᵢ>_*_part*.md` files for Vᵢ.
- DO NOT modify, re-sort, or rewrite the md content. (If verification at Step 0 needed to rewrite Vᵢ's md from its scratch, that has already happened and the md on disk now is the authoritative version for Vᵢ.)

### Step 2: Verify Conversion Prerequisites (per variant)

For Vᵢ, confirm:
- The md file(s) follow the encoding rules in `qc-func-tc-design/rules/testcase-instruction-rules.md` (Rules 0a–0d): UTF-8, preserved Vietnamese diacritics for VI projects, no transliteration applied.
- The md file(s) follow the layout rules ("Sheet Layout & Section Headers"): correct `## <Roman>. …` screen headers and `### <Roman>.1. … / <Roman>.2. …` GUI / FUNC section headers; column hierarchy intact.
- The in-md prelude (summary header + RTM at the top of the md) uses only `#` (h1) and `####` (h4) headings — the converter skips these, so they will NOT leak into the xlsx. If a prelude heading uses `##` or `###`, FIX the md before running the script.
- The template at `qc-func-tc-design/templates/Testcase_template.xlsx` has not changed since the script was last updated. If it has changed, update the script before running.

If any prerequisite fails, STOP and report on chat — do NOT silently fix the md. Do NOT run cleanup; Vᵢ's Phase 2 `.md` remains preserved for the user to re-trigger conversion after fixing the root cause. Already-converted variants (if any) keep their xlsx — they are NOT rolled back.

### Step 3: Run the Converter (per variant)

```bash
python .claude/skills/qc-func-tc-design/scripts/md_to_xlsx.py \
  --input-glob "<test-case-folder>/[UC-ID]_*_<variant>_*_part*.md" \
  --uc-id [UC-ID]
```

For Vᵢ, point `--input-glob` at the variant-specific glob (or at Vᵢ's single file path if Vᵢ's deliverable is single-file). Run the script once per variant; each invocation produces ONE xlsx scoped to its variant's md.

First-time setup (run once per machine):
```bash
pip install -r .claude/skills/qc-func-tc-design/scripts/requirements.txt
```

The script handles the following automatically — do NOT re-implement in your own openpyxl code:
- Reads `qc-func-tc-design/templates/Testcase_template.xlsx` and writes into the **single** `Test cases` sheet (column headers in row 1 are kept; do NOT rename the sheet, do NOT add columns).
- Auto-versioning: scans the test case folder for any existing `*_v{N}.xlsx` whose name contains the UC id, picks the next version. Refuses to overwrite. Per-variant outputs differ by their `_<variant>_` filename segment, so each variant's xlsx is auto-versioned independently.
- Merges multi-part draft files in `partN` order.
- Skips `#` (h1) and `####+` (h4+) headings — the in-md prelude (summary header + RTM) does NOT leak into the xlsx.
- Inserts header rows (text in column B only, other columns blank, NOT counted as test cases) for `## <Roman>. <screen-line>` and `### <Roman>.1. … / <Roman>.2. …`. The script keys off the `##` / `###` prefix only, so any language wording is accepted.
- Strips inline annotations like `[NEW]`, `[UPDATED — …]` from titles before writing — the draft md keeps them, the xlsx does not.
- Re-opens the saved file and verifies Vietnamese diacritics on sample cells; exits non-zero on mojibake (VI projects only — for EN projects this emits a harmless `WARN: No Vietnamese-diacritic sample found` and proceeds).

### Step 4: Self-Verification (per variant, MANDATORY)

After the script exits for Vᵢ, open Vᵢ's produced `.xlsx` and spot-check at least 3 rows containing non-ASCII text. If any cell shows: ASCII-only Vietnamese (no dấu, VI projects only), `?` boxes, mojibake (e.g., `Ä\x90`, `Ã©`), or any character that doesn't match the source — STOP, debug the script, regenerate. Do NOT deliver a partially-stripped output. (See Rule 0d in `testcase-instruction-rules.md`.) Do NOT run cleanup until ALL variants' xlsx pass self-verification.

After Vᵢ's xlsx passes self-verification, move on to the next variant V_(i+1) and return to Step 1. After the last variant completes Step 4, proceed to "Checkpoint write — End of Phase 3" below.

### Checkpoint write — End of Phase 3

Per `SKILL.md` → "Checkpoint & Resume Protocol" §5.2 (end-of-phase). Phase 3 is the last phase, so `last_phase_done: 3` IS written here (there is no Phase 4 to transition into). This block runs ONCE for the whole UC, AFTER all variants have passed Step 4.

1. **The deliverable `.xlsx` files (one per variant, written in Step 3 and verified in Step 4) ARE the Phase 3 deliverables.** Do NOT write a separate file in `process-logging/`.
2. **Update `progress.md`** → `last_phase_done: 3`, `next_phase: -` (done), `updated_at: <now>`. (Preserve `## Phase 2 Summary` and all other fields.)
3. **Worklog**: rewrite last entry → `status = "Phase 3 done"`. Append ALL variants' `.xlsx` paths to `output` (excluding `process-logging/`).
4. **qc-dashboard.md**: update the UC's `TC design stt` cell → `Chuyển MD sang XLSX done` (VI) / `MD → XLSX Conversion done` (EN). Skip if column missing.

### Step 5: Hand Back

Return control to `SKILL.md` → Step C (chat-side reporting). The Step C chat report should list ALL variants' `.md` + `.xlsx` paths (one pair per variant), plus any auto-recovery events that occurred during Step 0. After Step C completes, `SKILL.md` → Step D performs final cleanup (set `TC design stt` to final value `v<N> generated` or `v<N> updated`, mark worklog `Done`, delete `process-logging/<UC-ID>/` folder). This workflow does NOT write a summary file.
