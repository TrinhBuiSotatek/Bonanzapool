# UC Readiness Scoring Rubric

> Shared rubric referenced by both `first-audit` and `re-audit` workflows. Update this file ONCE to change scoring rules everywhere.

## Status Markers

Mark each knowledge area as:

- ✅ **Clear** — explicitly stated and unambiguous (full marks)
- ⚠️ **Partial** — present but vague, incomplete, or only inferred (half marks)
- ❌ **Missing** — absent from all provided artefacts (zero marks)

Additional status markers used throughout the report:

- ✅ **Complete** — explicitly stated and unambiguous
- ⚡ **Partial** — present but vague, incomplete, or only inferred (half marks)
- ⚠️ **Missing** — absent from all provided artefacts (zero marks)
- *(inferred)* — the reviewer inferred information rather than finding it explicitly; these are candidates for confirmation before test design begins

## Knowledge Areas Checklist

Score the **combined artefact set** against these knowledge areas. A tester needs all of these to design complete test cases.

| #   | Knowledge Area                            | Max Pts | Critical? | What to look for                                                                                                                                                                                                                                                                                                                                                                                                       |
| --- | ----------------------------------------- | ------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Feature Identity (title, ID, context)     | 5       | Yes       | Is it clear what this feature is and where it fits in the system?                                                                                                                                                                                                                                                                                                                                                  |
| 2   | Objective & Scope                         | 5       | Yes       | Why does this feature exist? What is in/out of scope?                                                                                                                                                                                                                                                                                                                                                                |
| 3   | Actors & User Roles                       | 10      | Yes       | Who triggers the feature? What roles/permissions are involved?                                                                                                                                                                                                                                                                                                                                                       |
| 4   | Preconditions & Postconditions            | 10      | Yes       | What must be true before? What is the system state after success?                                                                                                                                                                                                                                                                                                                                                    |
| 5   | UI Object Inventory & Mapping             | 15      | Yes       | Every atomic UI element listed as its own row with label/type/required/default/placeholder/enum values. **Auto-cap rules:** if any row collapses ≥ 2 atomic elements (e.g., "9 API fields", "(4 values)"), max score = 8/15. If any design image has < 80% of its visible elements enumerated, max score = 5/15. If any design image is referenced but no element from it appears in Section 4, max score = 0/15. |
| 6   | Object Attributes & Behavior Definition   | 20      | Yes       | Determine the state and response of each UI object based on specific system conditions. **1-to-1 rule:** every row in Section 4 must have ≥ 1 corresponding row here. If < 80% of Section-4 rows are covered, max score = 10/20.                                                                                                                                                                                |
| 7   | Functional Logic & Workflow Decomposition | 20      | Yes       | Analyze in detail the business processes of each function available on the feature screen. Duplicate the block below for each major sub-function (e.g., View List, Create Record).                                                                                                                                                                                                                                |
| 8   | Functional Integration Analysis           | 20      | Yes       | Analyze and evaluate the linkages and influences between the cataloged functions, acting as an integration check between functions.                                                                                                                                                                                                                                                                                |
| 9   | Acceptance Criteria                       | 20      | Yes       | Measurable, verifiable pass/fail statements.                                                                                                                                                                                                                                                                                                                                                                          |
| 10  | Non-functional Requirements               | 5       | No        | Performance, security, compatibility, accessibility.                                                                                                                                                                                                                                                                                                                                                                  |

**Total: 130 points → Normalise to 100 for the final score.**

## Normalization Formula

`Final Score = round((Raw Score / 130) × 100, 1)`

> Example: Raw score 88 / 130 → Final Score = round((88 / 130) × 100, 1) = **67.7 / 100**
> Example: Raw score 95 / 130 → Final Score = round((95 / 130) × 100, 1) = **73.1 / 100**

## Auto-fail Rule

If any Critical knowledge area scores 0, verdict = NOT READY regardless of total score.

- **Critical areas** (rows marked "Yes"): Areas #1–#9. If ANY of these score 0, the verdict is automatically NOT READY regardless of total score.
- **Non-critical areas** (rows marked "No"): Area #10. Scoring 0 here reduces the total but does not trigger auto-fail.

## Readiness Thresholds

| Score   | Verdict                       | Meaning                                                              |
| ------- | ----------------------------- | -------------------------------------------------------------------- |
| 90–100  | ✅ **READY**                  | QA can begin test design immediately                                 |
| 70–89   | ⚠️ **CONDITIONALLY READY**   | QA can start on clear areas; flagged items must be fixed in parallel |
| 0–69    | ❌ **NOT READY**             | Too many gaps; do not begin test design                              |

**Auto-fail:** Any Critical knowledge area scoring 0 → ❌ NOT READY regardless of total.

## Cross-Artefact Conflict Check

After scoring, check for **conflicts between artefacts**:

- Does the UC doc describe a flow that contradicts the wireframe?
- Does the API spec define fields not mentioned in requirements?
- Are there UI elements in the design with no corresponding business rule?
- Are labels/field names inconsistent across documents?
- **Site-map cross-check (if `qc-site-map` exists):** does the UC cover every screen mapped to its feature in §8 Screen ↔ Feature mapping? Do UC's actors/roles match §7 Role/access by screen? Do UC's flows match §6 Navigation? Any mismatch → Warning + flag in Unified Gap & Question Report.

List all conflicts found — they are automatic Warnings.

## Blocked Artefact Protocol

If a referenced artefact (wireframe, API spec, supporting doc) is **unavailable or inaccessible**:

- Mark the dependent knowledge area(s) as `[BLOCKED: artefact name not accessible]`
- Score those areas as 0
- Since blocked artefacts almost always affect Critical knowledge areas (#1–#9), surface each blocked area as a 🔴 **Blocker** in the report under the "Blockers" section
- Do NOT infer or assume content from unavailable artefacts

## Common Gap Patterns

| Gap Pattern                                  | Impact on Test Design                         |
| -------------------------------------------- | --------------------------------------------- |
| No preconditions stated                      | Tester can't set up test data correctly       |
| Vague actor ("the user")                     | Can't determine which role/permission to test |
| Missing field validation rules               | Can't write boundary value or negative tests  |
| No error messages specified                  | Can't verify error handling behaviour         |
| Acceptance criteria use "should" / "can"     | Not verifiable; can't define pass/fail        |
| Error UI state not described                 | Can't verify UI error behaviour               |
| API error codes not listed                   | Can't verify API error handling               |
| Design shows fields not in requirements      | Ambiguous scope and validation rules          |
| Flows reference other features without links | Can't trace test dependencies                 |

## Platform-Aware Gap Detection

Before scoring, read `project-context-master.md` §1 → "Product Platform Type". The platform variant(s) declared there sharpen what counts as ⚠️ Partial / ❌ Missing inside the existing Knowledge Areas — they do NOT add a new KA, do NOT change the 130-pt total, and do NOT change the normalization formula. They only refine the auditor's eye.

When auditing **KA #6 Object Attributes**, **KA #7 Functional Logic**, **KA #8 Functional Integration**, and **KA #10 NFR**, apply this expectation table:

| Platform variant | UC SHOULD address (else flag the relevant KA's row as Partial/Missing with evidence note "Platform-specific gap: <topic>") |
|---|---|
| `web-responsive` | Browser compatibility matrix; behavior at each declared breakpoint (desktop / tablet / mobile viewport); responsive reflow + mobile-viewport tap targets; URL deep-link / back-forward / refresh state preservation. |
| `web-static` | Min screen resolution + browser matrix; keyboard shortcuts (if back-office); print view (if reports); bulk operations + grid pagination/sorting/filter rules. |
| `mobile-native` | App lifecycle (background → foreground; killed → relaunch; form-draft persistence); OS permissions used (Location/Camera/Notifications/Photo/Biometric) + rationale text + deny-recovery flow; hardware back button (Android) / swipe-back-edge (iOS); push notification + deep-link target (cold/warm/killed); offline behavior + cache invalidation; biometric auth + fallback; safe-area insets; accessibility (VoiceOver/TalkBack labels, Dynamic Type). |
| `mobile-hybrid` | All `mobile-native` items above PLUS: WebView ↔ native bridge methods used; WebView lifecycle vs native shell; cookie / token sync between WebView and native HTTP; in-app browser fallback for external URLs. |
| `desktop-native` | Window management (resize / min size / multi-monitor / DPI scaling); OS file dialogs (open/save with extension filter, drag-and-drop from OS); keyboard shortcuts per OS conventions; system tray + OS notifications; auto-update flow; installer/uninstaller behavior; concurrent edit (multi-window or multi-instance) policy. |

If multiple variants apply (multi-platform project), apply the union of expectations for the variants relevant to the screen the UC describes. If a UC explicitly states "this screen is X-platform-only" then apply only that variant's expectations.

> **Surfacing rule:** Platform-specific gaps appear inline in the affected KA's evidence column (not as a separate KA section), with the prefix `Platform-specific gap (<variant>):` so they are easy to spot. Phase 3 MUST lift each marked gap into a row of the **Unified Gap & Question Report** table (the canonical Q-table appended to the audit's Audit Summary section, with Q-IDs Q1, Q2, …). The `qc-qna` auto-trigger after `qc-uc-read` reads from THAT table — NOT from template §10.1 (which is the BA's UC-local Open Questions section, a different artefact). No change to `qc-qna` is required.
