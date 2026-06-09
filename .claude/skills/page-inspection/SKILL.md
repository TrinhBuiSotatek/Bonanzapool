---
name: page-inspection
description: Visit a URL provided by the user, identify stable locators (role / testid / text / css / xpath in that preference order) for each UI element listed, and persist a versioned page element catalog. Runs before test-script-design can automate any page.
---

# Skill: page-inspection

Auto-run after the `qc-uc-read` skill has produced the `uc-review-report` file.

## Inputs

- **Element list** — the `UI Objects` section of the relevant `uc-review-report`. Lists every element name the testcases will reference on this page.
- **URL** — provided by the user at invocation time. One URL per `page-name`.
- `project-config` (resolved via `path-registry.md` → `docs/qc-lead/project-config.md`) — test accounts (when URL requires login) + Platform & device coverage (decides whether to inspect web vs native).
- `.claude/config/folder-structure.md` — output goes under the references folder.
- `.claude/rules/automation-conventions.md` — locator strategy preference order, stability tier definitions, page catalog rules, MISSING locator handling.
- `.claude/rules/templates/page-element-catalog.md` — authoritative output shape.
- `.claude/rules/naming-conventions.md` — `<page-name>_<YYYYMMDD>_v<N>.md` pattern.

## Process

1. **Locate an existing catalog** for the `page-name` at the canonical references location (per `folder-structure.md`).
   - If none: new file at `_v1`.
   - If one exists: plan to write `_v<N+1>`.
2. **Access the URL.** Pick the mechanism available in the current environment:
   - Playwright MCP tool (if configured) — preferred; live DOM access.
   - `WebFetch` on the URL — returns HTML; usable for static pages, limited for SPA where elements render via JS.
   - **Ask the user to run an inspection script and paste output** — fallback. Provide a short Playwright snippet that dumps candidate locators for each named element.
3. **For each element name** in the input list, resolve a locator following the preference order in `rules/automation-conventions.md` (role > testid > text > css > xpath). Record the **Stability** tier per the same file.
4. **Flag missing elements** — any name with no locator → emit row with `Locator value = MISSING` and a Notes column explaining what was searched. Do NOT skip silently. `test-script-design` will gate on MISSING.
5. **Flag low-stability elements** — for every `Stability = Low` row, add an entry to the plan's Progress log recommending the dev add a `data-testid`.
6. **Write** the new catalog file using the template at `rules/templates/page-element-catalog.md`. Never edit the previous version.

## Output

- Markdown page element catalog conforming to `rules/templates/page-element-catalog.md`.
- File type: `.md` only (no xlsx — automation infra, not a business deliverable).
- **Filename**: `<page-name>_<YYYYMMDD>_v<N>.md` per `naming-conventions.md`. For scenario C (separate web + native mobile), use platform suffix: `<page>-web_<YYYYMMDD>_v<N>.md` / `<page>-mobile_<YYYYMMDD>_v<N>.md` (per `rules/automation-conventions.md` + `rules/testcase-design-techniques.md` → Multi-platform & multi-device coverage).
- **Folder**: see `.claude/config/folder-structure.md`.

## Decision rules

- **Never invent a locator.** If the element cannot be found, mark `MISSING` with the search trail in Notes. `test-script-design` will gate on this.
- **Never hand-craft an xpath when a role-based locator works.** Order from `rules/automation-conventions.md` is mandatory.
- **Credentials / auth**: if the URL requires login, use test accounts from `.claude/config/project.md`. Never paste real user credentials into the catalog or logs.
- **SPA behavior**: if `WebFetch` returns a shell (React root with empty body), do not guess from static HTML. Ask the user to run the Playwright inspection snippet or provide a rendered HTML dump.
- **One page at a time.** A multi-step flow (login → dashboard → settings) is three inspection runs producing three catalog files.
- **Re-inspection bumps version.** Any change (new element, changed locator, stability change) → new `_v<N+1>.md`. Never edit in place.

## Interaction with other skills

- **Input from**: `get-requirement` (the UI Objects section lists what needs cataloging).
- **Consumed by**: `test-script-design` (looks up element names → locators).
- **Re-triggers**: when a testcase step references an element name not present in the catalog, or when `test-execute` fails with a "locator not found" error.
