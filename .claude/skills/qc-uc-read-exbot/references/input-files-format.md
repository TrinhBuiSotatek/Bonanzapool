# Input files format — ExBot (no-UI, BE-only)

> Lean reference for `qc-uc-read-exbot`. Scope: the **exbot** module only, tested
> through the Back-End + observed through the Admin site (no interactive UI).
> Plan root: `docs/ba/plans/bnza-sotatek-260519-0000/`. Resolve every path through
> `.claude/config/path-registry.md` — never hard-code.

---

## 1. The source-of-truth baseline — `03_modules/exbot/srs/`

These four files describe **how the bot actually works** and are the canonical
technical truth for cross-checking. Read ALL of them once, before any UC, to build
a holistic mental model of ExBot.

| File | What it gives you |
| :--- | :---------------- |
| `srs/spec.md` | Bot behavior spec: operations, formulas, variables, thresholds, parameters, triggers (request / queue / cron / on-chain event). |
| `srs/states.md` | Lifecycle state registry + transitions (e.g. `lp_opening -> lp_opened` on `VaultMinted`). The full enum sets live here. |
| `srs/flows.md` | Sequence / flow of each operation (bot-start, light-check, hedge-sync, redeem, safe-close, agent-key). |
| `srs/erd.md` | Data objects, fields, types, keys, on-chain <-> off-chain source-of-truth side. |

`frd.md` (module root) holds the `FR-EXBOT-*` functional requirements that UCs and
US trace back to.

---

## 2. Use cases & user stories — `03_modules/exbot/usecases/`, `userstories/`

Both folders have an **`index.md`** read FIRST — it is the tracking + mapping table.

`usecases/index.md` columns: `UC ID | File | Actor(s) | Description | Linked Stories | FR Trace | Stale`.
`userstories/index.md` columns: `Story ID | File | Actor | Feature / FR | AC Count | Linked UCs | Source Backbone IDs | Stale`.

UC IDs are descriptive, e.g. `UC-EXBOT-bot-start` (file `uc-bot-start.md`). Use the
UC-ID verbatim as the on-disk Folder ID and in the output file name.

**Resolving the UC <-> US <-> FR map** (priority order):
1. `usecases/index.md` `Linked Stories` + `FR Trace` columns.
2. The UC file frontmatter: `linked_stories`, `source_backbone_ids`.
3. Shared `FM-*` / `FR-*` code — items sharing it belong to the same feature.

### UC file body (`usecases/uc-<slug>.md`)
`# UC` -> `## Actors` (cite `ACT-*`) -> `## Preconditions` -> `## Trigger` ->
`## Main Flow` (cites `BR-*`, `E-*`, `[AF-NN]`, `[EF-NN]`) -> `## Alternate Flows`
(`### AF-NN`) -> `## Error / Exception Flows` (`### EF-NN`, cite `E-*`) ->
`## Postconditions` -> `## Cross-Function Impact` -> `## Diagram` (mermaid) ->
`## Trace` -> `## Open Questions` (`OQ-EXBOT-NN`).

### US file body (`userstories/us-NNN.md`)
`## Story Statement` (As a / I want / so that) -> `## Acceptance Criteria`
(`### AC-NNN`, Given/When/Then) -> `## INVEST Check` -> `## Trace`.

---

## 3. Cross-module registries — `02_backbone/`

When a UC / US cites a code, resolve it verbatim against these (authoritative):

| Code prefix | Meaning | Defined in |
| :---------- | :------ | :--------- |
| `FR-EXBOT-<NNN>` | Functional requirement | `03_modules/exbot/frd.md` |
| `FM-<MOD>-<NN>` | Module feature | `02_backbone/feature-map.md` |
| `BR-<MOD>-<NNN>` | Business rule | `02_backbone/common-rules.md` |
| `E-<MOD>-<NNN>` | User-facing / system message | `02_backbone/message-list.md` |
| `ACT-<NN>` | Actor | `02_backbone/backbone.md` (mirrored in `feature-map.md`) |
| `AC-<NNN>` | Acceptance criterion | the owning US file |
| `AF-<NN>` / `EF-<NN>` | Alternate / error flow | the owning UC file |
| `OQ-EXBOT-<NN>` | Open question | the owning UC's `## Open Questions` |

**Verbatim rule:** when a UC quotes a `BR-*` or `E-*`, the text MUST match the
registry exactly. Any deviation = a UC override -> flag it as a cross-source conflict.

---

## 4. What to open when auditing one ExBot UC

1. The whole `srs/` baseline (§1) — once per run, the cross-check truth.
2. The UC file itself + `usecases/index.md`.
3. Every linked US (from `linked_stories` / index) + `userstories/index.md`.
4. `frd.md` for the cited `FR-EXBOT-*`.
5. `common-rules.md` + `message-list.md` to resolve every cited `BR-*` / `E-*`.
6. `feature-map.md` / `backbone.md` only when a `FM-*` / `ACT-*` reference needs it.

There is **no UI / screen / wireframe** in scope. Do not look for `ascii-screen/`
artefacts and do not penalize a UC for lacking them. Primary evidence is the
spec, ERD, state machine, and flows.
