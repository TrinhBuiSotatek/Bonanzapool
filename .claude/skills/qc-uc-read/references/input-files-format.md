# Format of input files

> Reference for the structure of all BA input artifacts that the `qc-uc-read` skill
> consumes in the **bonanzapool** project.
> All BA artifacts live under a single plan root:
> `docs/sotatek/ba/plans/<plan-id>/` (current plan: `bnza-sotatek-260519-0000`).

The plan root has three top-level folders:

| Folder           | Purpose                                                   |
| :--------------- | :-------------------------------------------------------- |
| `01_intake/`     | Raw client materials (intake, source spec). Read-only.    |
| `02_backbone/`   | Cross-module canonical registries (see §1).               |
| `03_modules/`    | Per-portal BA artifacts (US / UC / Screen). See §2.       |

---

## 1. Common artifacts — `02_backbone/`

These four files are **the canonical registries**. Every `FM-*`, `BR-*`, `E-*`,
`ACT-*`, `PTL-*` code referenced anywhere in a UC / US / Screen MUST resolve to a
row in one of these files. The audit MUST treat them as the authoritative source
of truth.

### 1.1 `backbone.md`

- **Type:** Top-level system blueprint (actors, portals, delivery structure,
  shared architecture, fee model, deployment topology).
- **Defines:**
  - `ACT-<NN>` — shared actors (e.g. `ACT-04` = Admin / zen).
  - `PTL-<NN>` — portal registry (e.g. `PTL-02` = ops.bnza.io).
  - Numbered top-level sections (`§5`, `§8`, …) referenced from FRDs.
- **Frontmatter:** `type: backbone`, plus `engagement_mode`, `links`, `changelog`.

### 1.2 `feature-map.md`

- **Type:** System-level feature index. **Single source of truth for `FM-*`
  codes**, which are the primary join key between US, UC, and Screen.
- **Defines:**
  - `FM-<MOD>-<NN>` — module feature code (e.g. `FM-ADM-01` = WL Partner
    Onboarding inside the `admin` portal).
  - Portal Registry, Actor Registry, per-module feature tables, priority tiers,
    cross-module dependencies.
- **Frontmatter:** `type: feature-map`, `links` (to `backbone.md`), `changelog`.

### 1.3 `common-rules.md`

- **Type:** Cross-module business-rule registry. **Single source of truth for
  `BR-*` codes**.
- **ID format:** `BR-<MOD>-<NNN>` — module prefix is uppercase (`MOB`, `EX`, `PL`,
  `ADM`, `WLA`, …); `<NNN>` is zero-padded and unique inside the module.
- **Layout:** One `## <MOD>` section per module, each containing a table:

  | Column | Meaning                                              |
  | :----- | :--------------------------------------------------- |
  | `ID`   | `BR-<MOD>-<NNN>` (verbatim — quoted by UCs).          |
  | `Rule` | The rule statement (verbatim — quoted by UCs).        |
  | `Scope`| Which screens / flows the rule applies to.            |

- **Reference rule:** When a UC quotes a `BR-*` rule, the text MUST match this
  file verbatim. Any deviation = a UC override and must be flagged in the audit.
- **Module-level `srs/spec.md` SHOULD NOT redefine `BR-*` inline** — reference
  by ID.

### 1.4 `message-list.md`

- **Type:** Cross-module user-facing message registry. **Single source of truth
  for `E-*` codes**.
- **ID format:** `E-<MOD>-<NNN>` (e.g. `E-ADM-001`, `E-MOB-003`,
  `E-pool-001` — case preserved as written in source).
- **Layout:** One `## <MOD>` section per module, each with a table:

  | Column                | Meaning                                              |
  | :-------------------- | :--------------------------------------------------- |
  | `E-ID`                | `E-<MOD>-<NNN>`                                       |
  | `Type` / `HTTP` / `Code` | Message kind (Error / Info / Warning) and/or HTTP code or backend error code. Column header varies by module. |
  | `Trigger`             | Backend condition / HTTP status that fires the message. |
  | `User-Facing Message` | Verbatim string shown to the user (quoted by UCs).    |

- **Reference rule:** When a UC quotes an `E-*` message, the text MUST match
  this file verbatim. Screen files MUST NOT define message text inline —
  reference by `E-*` ID.

---

## 2. Per-module artifacts — `03_modules/<portal>/[<role>/]…`

### 2.1 Folder layout

Two folder shapes exist; both are valid and the skill MUST handle both:

**Shape A — single-role portal (no `<role>` subfolder):**

```
03_modules/<portal>/
├── frd.md
├── srs/                # technical spec (optional context)
├── userstories/
│   ├── index.md
│   └── us-NNN.md
├── usecases/
│   ├── index.md
│   └── uc-<slug>.md
└── ascii-screen/
    ├── index.md
    └── <screen-slug>.md
```

Examples: `bnza-pool/`, `mobile/`, `operator/`, `exbot/`, `bnza-ex/`.

**Shape B — multi-role portal (`<role>` subfolder is required):**

```
03_modules/<portal>/<role>/
├── frd.md
├── srs/
├── userstories/        # may be absent in roles that ship UC-only
├── usecases/
└── ascii-screen/
```

Examples: `admin/bnza-admin/`, `admin/wl-admin/`.

> **Note.** Some roles (e.g. `operator/`) intentionally ship only `usecases/` +
> `ascii-screen/` and have no `userstories/` folder. Do not treat the missing
> folder as a gap.

### 2.2 `index.md` files — inventory + mapping

Each of the three subfolders (`userstories/`, `usecases/`, `ascii-screen/`) has
an `index.md` that the skill MUST read first. The index serves two purposes:

1. **Inventory** — lists every file in the folder.
2. **Mapping** — links each item to its peers (US ↔ UC ↔ Screen) via either
   explicit `Linked …` columns OR a shared `FM-trace` column.

The repo currently contains **two flavours** of `index.md`; the skill must
handle both:

**Flavour 1 — rich index (preferred, observed in `bnza-pool/userstories/index.md`):**

| Column                 | Meaning                                                  |
| :--------------------- | :------------------------------------------------------- |
| `Story ID` / `UC file` / `Screen file` | Identifier of the item.                          |
| `File`                 | Relative path.                                            |
| `Actor`                | `ACT-<NN> <name>`.                                        |
| `Feature / FR`         | Primary `FM-*` link.                                      |
| `AC Count` (US only)   | Number of acceptance criteria.                            |
| `Linked Use Cases`     | `uc-<slug>` of the UC(s) this story maps to.              |
| `Linked Screens`       | `<screen-slug>` of the screen(s) this story maps to.      |
| `Source Backbone IDs`  | Full list of `FM-*` codes.                                |
| `Marker`               | `📋 Spec` (from client spec) or `⚡ Dev-built`.            |
| `Stale Status`         | `unknown` / `fresh` / `stale` — staleness vs source spec. |

Frontmatter (rich flavour): `type: userstories-index` / `usecases-index` /
`screens-index`, `module`, `generated_at`, `stale_status`, …

**Flavour 2 — minimal index (observed in `admin/bnza-admin/*/index.md`):**

| Column                          | Meaning                            |
| :------------------------------ | :--------------------------------- |
| `Story file` / `UC file` / `Screen file` | Filename.                          |
| `story_id` / `usecase_id` / `Screen name` | Identifier.                        |
| `Summary` / `Use case name` / —  | Short title.                       |
| `FM-trace`                      | The `FM-*` code(s) the item supports. |
| `Priority`                      | `P0` / `P1` / `P2` / `P3 (mock)` / `maintain`. |
| `Status`                        | `draft` / `in-review` / `approved`. |

Frontmatter (minimal flavour): `type: user-story` / `use-case` / `screen`,
`status`, `owner`, `module`, `lang`, `changelog`.

**Resolving the US ↔ UC ↔ Screen map:**

The skill MUST resolve the map using this priority:

1. Rich index columns (`Linked Use Cases`, `Linked Screens`) if present.
2. Otherwise, the `linked_usecases` / `linked_stories` / `linked_screens`
   arrays in the frontmatter of each individual file (see §2.3 / §2.4 / §2.5).
3. Otherwise, fall back to the shared `FM-*` code (items sharing the same
   `FM-*` belong to the same feature).

---

### 2.3 User Story file — `userstories/us-NNN.md`

#### Filename

`us-<NNN>.md` (3-digit zero-padded, unique inside the module).

#### Frontmatter

```yaml
---
type: user-story
module: "<module-name>"          # e.g. "bnza-admin"
story_id: "US-<NNN>"
slug: "<kebab-case-name>"
actor: "<Role Name (handle)>"    # e.g. "Super Admin (zen)"
priority: P0 | P1 | P2 | P3
status: draft | in-review | approved
source_backbone_ids: ["FM-<MOD>-<NN>", …]
linked_usecases: ["uc-<slug>", …]   # may be []
linked_screens:  ["<screen-slug>", …] # may be []
created: "YYYY-MM-DD"
owner: "@<handle>"
changelog:
  - YYYY-MM-DD | <source> | <change description>
---
```

#### Body sections (in order)

1. `# US-<NNN>: <Story Name>`
2. `## Story Statement` — one paragraph in **"As a … , I want to … , so that …"** form.
3. `## Acceptance Criteria` — one `### AC-<NNN> (<label>)` subsection per
   criterion. Each AC uses the **Gherkin pattern**:
   `**Given** …` `**When** …` `**Then** …`. Labels include `(Happy Path)`,
   `(Edge Case — …)`, `(Negative — …)`, etc.
4. `## INVEST Check` — 6-row table `| Criterion | Pass? | Note |` for
   Independent / Negotiable / Valuable / Estimable / Small / Testable.
5. `## Trace` — bulleted list of: `Backbone feature: FM-…`, `FRD reference: …`,
   `Screens: …`, `Table: <DB table + columns>`, `RBAC gate: …`.

---

### 2.4 Use Case file — `usecases/uc-<slug>.md`

#### Filename

`uc-<kebab-case-slug>.md`. The `<slug>` is descriptive (no module prefix needed —
the folder path already disambiguates).

#### Frontmatter

```yaml
---
type: use-case
module: "<module-name>"
usecase_id: "UC-<slug>"
slug: "<kebab-case-name>"
actor: "<Role Name (handle)>"
status: draft | in-review | approved
linked_stories: ["US-<NNN>", …]
linked_screens: ["<screen-slug>.md", …]
source_backbone_ids: ["FM-<MOD>-<NN>", …]
created: "YYYY-MM-DD"
owner: "@<handle>"
changelog:
  - YYYY-MM-DD | <source> | <change description>
---
```

#### Body sections (in order)

1. `# UC-<slug>: <Use Case Name>`
2. `## Actors` — primary + secondary, each cited with `ACT-<NN>`.
3. `## Preconditions` — bulleted list.
4. `## Trigger` — one-sentence trigger event.
5. `## Main Flow` — numbered steps. Steps reference `BR-*`, `E-*`,
   `[AF-NN]`, `[EF-NN]` inline as needed.
6. `## Alternate Flows` — one `### AF-<NN>: <name>` subsection per alternate.
   Body describes the deviation point and continuation.
7. `## Error / Exception Flows` — one `### EF-<NN>: <name>` subsection per
   exception. MUST cite an `E-*` code when surfacing a user-facing message.
8. `## Postconditions` — what state holds after success. MAY include
   `**<FM-…> expanded scope:**` callouts for cross-UC handoffs.
9. `## Cross-Function Impact` — two tables:
   - `### Within Module` — `| Direction | UC | Data / State | Type |`.
   - `### Across Modules` — `| Direction | Target Module | Expected UC / Backbone Ref | Data / State | Type |`.
   - `Direction` ∈ {`Input`, `Output`}; `Type` is free-form but typically
     matches `Direction`.
10. `## Diagram` — a `mermaid sequenceDiagram` block (sometimes a flowchart).
11. `## Trace` — bulleted list of: `User stories: US-…`, `Backbone feature: FM-…`,
    `Screens: <relative path>`.
12. `## Open Questions` — bulleted list `[ ] OQ-<MOD>-<NN>: <question>`.

---

### 2.5 ASCII Screen file — `ascii-screen/<screen-slug>.md`

#### Filename

`<kebab-case-screen-slug>.md` (e.g. `whitelabel.md`, `fee-distribution.md`).
Slug matches the screen's nav target, not its display label.

#### Frontmatter

```yaml
---
type: screen
status: draft | current | in-review
owner: "@<handle>"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [<module>, <screen-area>, <build-state>]
changelog:
  - YYYY-MM-DD | <source> | <change description>
---
```

> **Note.** Screen frontmatter intentionally has **no `linked_stories` /
> `linked_usecases` field**. The reverse-link is resolved via the `index.md`
> rich columns OR via each US/UC's `linked_screens` array.

#### Body sections (in order)

1. `# Screen: <Screen Name>`
2. Quick-reference block (3 bold lines):
   - `**Route:** <URL path>`
   - `**Nav label:** <icon + label>`
   - `**Module:** <module-name>`
3. `## Markers` — explains the 📋 Spec / ⚡ Dev-built convention used inline.
4. `## Layout Overview` —
   - **Optional scope callout** `> **FM-<MOD>-<NN> expanded scope (…):** …`
   - **ASCII layout** in a fenced ``` block — the canonical wireframe.
   - **Per-tab / per-state sub-sections** (`### <Tab Name> (new — wireframe TBD)`)
     when the screen is multi-tab and one tab has not been drawn yet.
5. **Element sections** — one `## <Element Group>` per logical block (Stat
   Cards, Table, Buttons, Form, etc.). Each is tagged with `📋 Spec` or
   `⚡ Dev-built`. Tables typically use `| Column | Content |` or
   `| Card | Current Value | Note |`.
6. `## Data Sources` — bulleted list of API endpoints or stores the screen reads.
7. `## Notes` — free-form prose for caveats, current build state, future-work
   flags.

> Screen files MUST NOT define `BR-*` or `E-*` text inline; they reference by ID.

---

## 3. Inline reference codes — quick lookup

| Code prefix          | Meaning                                             | Defined in                                      |
| :------------------- | :-------------------------------------------------- | :---------------------------------------------- |
| `PTL-<NN>`           | Portal (domain/app boundary)                        | `02_backbone/backbone.md` §Portal Registry; mirrored in `feature-map.md` §1 |
| `ACT-<NN>`           | Shared actor                                        | `02_backbone/backbone.md` §Shared Actors; mirrored in `feature-map.md` §2 |
| `FM-<MOD>-<NN>`      | Module-level feature                                | `02_backbone/feature-map.md` (and §5 of `backbone.md`) |
| `BR-<MOD>-<NNN>`     | Business rule                                       | `02_backbone/common-rules.md`                    |
| `E-<MOD>-<NNN>`      | User-facing message                                 | `02_backbone/message-list.md`                    |
| `US-<NNN>`           | User story (scoped inside its module)               | `03_modules/<portal>/[<role>/]userstories/us-<NNN>.md` |
| `UC-<slug>`          | Use case (scoped inside its module)                 | `03_modules/<portal>/[<role>/]usecases/uc-<slug>.md` |
| `<screen-slug>`      | Screen                                              | `03_modules/<portal>/[<role>/]ascii-screen/<screen-slug>.md` |
| `AC-<NNN>`           | Acceptance criterion inside a US                    | The owning US file (§3)                          |
| `AF-<NN>` / `EF-<NN>`| Alternate flow / Error-Exception flow inside a UC   | The owning UC file (§6 / §7)                     |
| `OQ-<MOD>-<NN>`      | Open question scoped to a module / UC               | The owning UC's `## Open Questions` and module's `oq-*-summary.md` |
| `📋 Spec`            | Item is in the original client spec                 | Inline marker (defined in `## Markers` block)    |
| `⚡ Dev-built`        | Item built by dev, NOT in client spec               | Inline marker (defined in `## Markers` block)    |

---

## 4. What `qc-uc-read` MUST open when auditing a single UC

For a UC file at `03_modules/<portal>/[<role>/]usecases/uc-<slug>.md`:

1. **The UC file itself.**
2. **Every linked US** — files listed in `frontmatter.linked_stories` (or
   resolved via the `usecases/index.md` rich columns / shared `FM-*`).
3. **Every linked Screen** — files listed in `frontmatter.linked_screens` (or
   resolved as above).
4. **The three indices** in the same module (`userstories/index.md`,
   `usecases/index.md`, `ascii-screen/index.md`) — to detect coverage gaps and
   stale-status flags.
5. **`02_backbone/common-rules.md`** — to verify every `BR-*` cited in the UC
   exists and the quoted text matches verbatim.
6. **`02_backbone/message-list.md`** — to verify every `E-*` cited in the UC's
   `## Error / Exception Flows` exists and the message text matches verbatim.
7. **`02_backbone/feature-map.md`** — to verify every `FM-*` /
   `ACT-*` / `PTL-*` cited in the UC exists.
8. **`02_backbone/backbone.md`** — only when a reference points to a
   backbone-only artifact (e.g. a `§N` cross-section, an architecture detail not
   present in `feature-map.md`).

> There is **no per-engagement `project-context_*.md` file** in this project.
> The role of "authoritative engagement summary" is filled by `backbone.md` +
> `feature-map.md` together.
