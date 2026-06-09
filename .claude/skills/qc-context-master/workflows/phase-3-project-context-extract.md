# Phase 3 - Project Context Extraction

Goal: draft Sections 1-8 of `project-context-master.md` using the Vietnamese template and writing guide.

## Required reads

- `references/project-context-master-writing-guide.md`
- `templates/project-context-master-template.vi.md`
- `01_input_audit.md`
- `02_feature_inventory.md`
- all relevant high-level source files
- existing `project-context-master.md` in Update mode

## Section checkpoints

Write one checkpoint per section so the skill can resume if interrupted.

| Checkpoint | Template section |
|---|---|
| `03_context_section_01.md` | How QC Agents should use this file |
| `03_context_section_02.md` | Project summary |
| `03_context_section_03.md` | Overall scope and testing boundaries |
| `03_context_section_04.md` | System structure and related high-level files |
| `03_context_section_05.md` | Users, roles, and high-level permissions |
| `03_context_section_06.md` | Business flows, module relationships, and impact areas |
| `03_context_section_07.md` | Common rules, data/state, and integrations |
| `03_context_section_08.md` | Platform, environment, device, and constraints |

## Extraction rules

1. Keep each section compact and project-level.
2. Use Vietnamese for draft section content.
3. Preserve QC Lead-reviewed content from existing context when still valid.
4. Do not copy detailed spec, wireframe, API schema, endpoint list, field validation, scenario, or test case content.
5. If information belongs to site map, feature list, or dashboard, summarize only and reference the owning file.
6. If technical or compliance information is missing, do not infer. Mark as gap for Phase 4.
7. If a relevant project-level item is not described but likely needed, record it as a gap or question, not as a fact.

## Each section checkpoint format

```markdown
# Context Section <NN> - <section name>

## Draft content
<markdown content for this section in Vietnamese>

## Sources used
| Source | Evidence summary |
|---|---|

## Gaps found
| Gap | Type | Impact | Suggested owner |
|---|---|---|---|

## Assumptions
| Assumption | Why made | Impact if wrong | Needs confirmation? |
|---|---|---|---|

## Conflicts
| Conflict | Sources | QC impact | Suggested owner |
|---|---|---|---|

## Confidence
High | Medium | Low
```

## Progress updates

After each section checkpoint, update `progress.md` with:

- `last_phase_done: 3:<section-number>`
- `next_phase: 3:<next-section-number>` or `4` after Section 8.
