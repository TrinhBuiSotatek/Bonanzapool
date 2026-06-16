# Format of input files

> Reference for the structure of all BA input artifacts that the `qc-uc-read` skill consumes.
> Project: **Bonanzapool — BNZA Ecosystem**.
>
> All BA artifacts live under `docs/BA/plans/bnza-sotatek-260519-0000/`.
> Common (cross-feature) artifacts are in `02_backbone/`.
> Per-feature/module artifacts are in `03_modules/<module>/`.

---

## 1. Common artifacts — `02_backbone/`

Files in this folder are shared across the whole project and apply to every feature/UC.

### 1.1 `common-rules.md`

- **Type:** Catalogue of cross-cutting business rules per portal/module: `BR-MOB-*`, `BR-EX-*`, `BR-PL-*`, `BR-ADM-*`, `BR-WLA-*`.
- **File name:** `common-rules.md` (single canonical file, no version suffix).
- **Logical name in path-registry:** `requirement-common-files`.
- **Language:** Vietnamese/English mixed; rules must be quoted verbatim from this file when referenced from a feature spec.

#### Rule ID conventions

| Prefix | Portal / Module | Example |
|:---|:---|:---|
| `BR-MOB-*` | WL Mobile (OOS — Helix) | `BR-MOB-009` |
| `BR-EX-*` | BNZA-EX (Perps trading) | `BR-EX-04` |
| `BR-PL-*` | BNZA-POOL (LP bot) | `BR-PL-16` |
| `BR-ADM-*` | BNZA-ADMIN (Admin portal) | `BR-ADM-031` |
| `BR-WLA-*` | WL Admin (OOS — Helix) | `BR-WLA-001` |

#### Reference rule

When a UC/spec quotes a `BR-*` rule, the audit MUST resolve the full rule text from `common-rules.md` and inline it verbatim into the audit output (do NOT leave the bare code only).

---

### 1.2 `feature-map.md`

- **Type:** Master index of all features in the project, grouped by portal.
- **File name:** `feature-map.md`.
- **Logical name in path-registry:** part of `requirement-common-files`.
- **Purpose:** Single source of truth for the **feature list** (`FM-*` IDs), their **portal mapping**, **priority tier**, and **cross-feature dependencies**.

#### Feature ID conventions

| Prefix | Portal / Module | Example |
|:---|:---|:---|
| `FM-ADM-*` | BNZA-ADMIN | `FM-ADM-01` |
| `FM-EX-*` | BNZA-EX | `FM-EX-03` |
| `FM-XB-*` | BNZA-EXBOT Infra (backend) | `FM-XB-07` |
| `FM-PL-*` | BNZA-POOL | `FM-PL-01` |
| `FM-OPW-*` | OPERATOR WL Backend | `FM-OPW-02` |
| `FM-WLC-*` | WL Smart Contract | `FM-WLC-01` |
| `FM-WLA-*` | WL Admin (OOS — Helix) | `FM-WLA-01` |
| `FM-MOB-*` | WL Mobile (OOS — Helix) | `FM-MOB-01` |

#### Priority tiers

| Tier | Label | Meaning |
|:---|:---|:---|
| T0 | WL Launch critical | Must pass before WL go-live |
| T1 | Core Dev | Core deliverable |
| T2 | Enhancement | Nice-to-have |
| T3 | Low Priority | Deferred / mock only |

---

### 1.3 `backbone.md`

- **Type:** Full system architecture and delivery structure.
- **File name:** `backbone.md`.
- **Logical name in path-registry:** part of `requirement-common-files`.
- **Purpose:** Portal matrix (PTL-01..06 with tech stack, hosting, auth, Sotatek build flag), actor permissions (ACT-01..07), feature sections (§5), dependency graph (§6), priority ordering (§7).

#### Portal IDs

| ID | Portal | Sotatek builds? |
|:---|:---|:---|
| PTL-01 | WL Mobile — wl.bnza.io | ❌ OOS Helix |
| PTL-02 | BNZA-ADMIN — ops.bnza.io | ✅ |
| PTL-03 | BNZA-EX — ex.bnza.io | ✅ |
| PTL-04 | BNZA-EXBOT Infra — api.bnza.io/exbot | ✅ |
| PTL-05 | BNZA-POOL — pool.bnza.io | ✅ |
| PTL-06 | WL Admin — wl-admin.bnza.io | ❌ OOS Helix |

#### Actor IDs

| ID | Actor | Key access |
|:---|:---|:---|
| ACT-01 | End User (LP) | PTL-03 EX, PTL-05 POOL |
| ACT-02 | WL Partner | (registration/config flow) |
| ACT-03 | WL End User (OOS) | PTL-01 WL Mobile |
| ACT-04 | Admin (zen) | PTL-02 ADMIN, PTL-04 config, PTL-05 |
| ACT-05 | Trader | PTL-03 EX |
| ACT-06 | OPERATOR (System) | PTL-04 EXBOT Infra — internal only |
| ACT-07 | WL Operator Admin (OOS) | PTL-06 WL Admin |

---

### 1.4 `backbone-index.md`

- **Type:** Section navigator for `backbone.md`.
- **File name:** `backbone-index.md`.
- **Purpose:** Use to quickly find which §section of `backbone.md` contains a specific topic (permissions, feature map, dependency graph, etc.).

---

## 2. Per-module artifacts — `03_modules/<module>/`

Each module has its own folder under `03_modules/`. Currently only the `exbot` module has detailed BA docs.

### 2.1 Module `exbot` — `03_modules/exbot/`

Structure inside `03_modules/exbot/`:

```
03_modules/exbot/
├── usecases/
│   ├── index.md                    ← UC index (see 2.1.1)
│   └── <UC-ID>.md                    ← UC file (see 2.1.2)
└── srs/
    └── spec.md                     ← Module-level SRS (see 2.1.3)
```

**Logical name in path-registry:** `requirement-files` points to `03_modules/exbot/usecases/`.

---

#### 2.1.1 UC index — `usecases/index.md`

- **Type:** Master list of all EXBOT use cases.
- **Purpose:** Gives each UC a canonical ID, short name, and module section mapping.

##### UC ID conventions — EXBOT

EXBOT UCs use a compound slug, not a numbered pattern:

| UC ID | Short name |
|:---|:---|
| `uc-bot-start` | Bot Start (preflight + lifecycle init) |
| `uc-light-check` | Light Check (cron scan, zero HL calls) |
| `uc-hedge-sync` | Hedge Sync (delta-only rebalance) |
| `uc-user-redeem` | User Redeem (LP-first, SLA 5 min) |
| `uc-bot-safe-close` | Bot Safe Close (admin-initiated) |
| `uc-agent-key` | Agent Key Submit & Approve |

---

#### 2.1.2 Per-UC spec — `usecases/<name-UC>.md`

Each UC has its own folder named with the UC ID slug (e.g., `usecases/uc-bot-start.md`).

##### Document structure

The UC spec SHOULD contain the following sections:

**Header block:**

```markdown
# <name-UC>: <name-UC>

> Feature: <FM-ID> — <Feature name>
> Portal: <PTL-ID> (<portal name>)
> Actor(s): <ACT-ID list>
> Source: backbone.md §<section>, srs/spec.md §<section>
> SPEC ref: SPEC_v5.2.6_EN.md §<section> (if applicable)
> NV items: NV-<N> (if applicable — Phase 0 blockers from SPEC v5.2.6 §0.5)
```

**Section 1 — Use Case Description:**

| Field | Content |
|:---|:---|
| `ID` | UC ID (matches folder name) |
| `Feature` | FM-ID + feature name |
| `Portal` | PTL-ID + portal |
| `Actor(s)` | ACT-ID list with roles |
| `Description` | As a `<actor>`, I want to `<goal>`, so that `<benefit>`. |
| `Pre-conditions` | Bulleted list |
| `Trigger` | Event/condition that starts the UC |
| `Post-conditions` | On Success + On Failure |
| `Basic Flow` | Numbered steps referencing `[BR-*]`, `[FR-EXBOT-*]`, `[NV-*]` inline |
| `Alternative Flows` | Named sub-flows |
| `Business Rules` | `[BR-*]` references with verbatim rule text |
| `NV Gate` | Any NV items that must be confirmed before this UC's impl section is active |

**Section 2 — API / Queue / State Interface** *(replaces "Screen Description" for backend-only UCs):*

For EXBOT (PTL-04, no UI):

| Sub-section | Content |
|:---|:---|
| `Endpoints / Queues` | List of REST endpoints or Queue IDs involved (e.g., `POST /api/exbot/start`, `QUE-XB-01 bot-scan`) |
| `Request schema` | Fields, types, required/optional, constraints |
| `Response schema` | Success + error response shapes |
| `D1 state changes` | Which D1 tables/columns are read/written |
| `External calls` | HL API calls made, DO interactions (UserLockDO, HLRateLimitDO, MarketDataDO) |
| `Error codes` | List of error codes + messages |

For UI-bearing portals (PTL-02 ADMIN, PTL-03 EX, PTL-05 POOL), use the standard Screen Description format (one `### Screen SC-<##><letter>: <Screen Name>` subsection per screen state with asset reference, layout overview, and element table).

**Section 3 — Validation Summary:**

Same as standard: table of all fields/params with validation rules. For API: `Field | Required | Type | Constraint | Error`.

**Section 4 — Cross-References:**

Table `| Reference | Type | Notes |` listing every external code referenced. Type values for BNZA:

| Type | When |
|:---|:---|
| `Feature` | FM-* reference |
| `Business Rule` | BR-* reference |
| `Functional Requirement` | FR-EXBOT-* reference |
| `SPEC Section` | SPEC_v5.2.6_EN.md §N reference |
| `NV Item` | NV-N Phase 0 verification item |
| `UC Dependency` | Another UC-EXBOT-* that must complete first |
| `Use Case` | UC-to-UC link (Next Step / Previous Step / Downstream / Upstream) |

**Section 5 — Open Questions:**

Table `# | Question | Status` of unresolved questions. Status values:

- `Open` — pending answer.
- `Resolved: <answer> — <source>` — answer + citation.

**Section 6 — Changelog:**

Append-only table `Date | Source | Changes | NV Resolved`.

---

#### 2.1.3 Module SRS — `srs/spec.md`

- **Type:** Module-level Software Requirements Specification for BNZA-EXBOT Infra.
- **File name:** `spec.md`.
- **Purpose:** Defines `FR-EXBOT-*` functional requirements, lifecycle state machine (18 states), queue topology (10 queues), Durable Object specs (3 DOs), cron schedule, HL adapter rules, and Phase 0 Gate conditions.

##### Key IDs in `srs/spec.md`

| ID prefix | Meaning | Example |
|:---|:---|:---|
| `FM-XB-*` | Feature-level grouping | `FM-XB-07` Lifecycle State Machine |
| `FR-EXBOT-*` | Functional requirement (numbered) | `FR-EXBOT-001` 1-bot-per-user |
| `FR-EXBOT-002` | 5 preflight checks | |
| `FR-EXBOT-003` | 18-state lifecycle machine | |

---

## 3. High-level files — `docs/qc-lead/high-level-files/`

Supplementary high-level documents also used as context when auditing features.

### 3.1 `SPEC_v5.2.6_EN.md`

- **Type:** EXBOT Product Specification — authoritative business/design rules for the ExBot system.
- **Logical name in path-registry:** `High-level-files`.
- **Key sections relevant to QC audit:**

| Section | Content |
|:---|:---|
| `§0.4` | Validation points (what zen must verify before each phase) |
| `§0.5` | **NV items (NV-1..14)** — Phase 0 verification blockers |
| `§1.2` | Core Strategy — IL reduction formula, net formula |
| `§1.3` | Phase 1 scope — **dual-chain Base+OP from Phase 1** (🆕 v5.2.6) |
| `§2` | Marketing wording rules (ok/NG, risk disclosures) |
| `§3.1/3.2` | Design decisions — adopt/reject from carter2099 |
| `§3.4` | **BnzaExVault Option C** — independent Solidity contract for NFT custody (Base + OP) |
| `§6.4` | Dual-chain LP setup — wethIndex per-chain (NV-12 blocker) |
| `§19.5` | Stop system — **blocked until NV-1/NV-3 confirmed** |
| `§21.5` | Agent key envelope encryption (AES-GCM) |

##### NV item quick lookup (Phase 0 blockers)

| NV ID | What it blocks | Owner |
|:---|:---|:---|
| NV-1 | HL stop system behavior (isolated margin support) | SOTATEK verify |
| NV-3 | HL stop replacement on hedge-sync | SOTATEK verify |
| NV-5 | cloid idempotency on HL | SOTATEK verify |
| NV-8..11 | CF rate limits | SOTATEK verify |
| NV-12 | USDC/WETH pool address + wethIndex per chain (Base/OP) | zen (BNZA) |

##### Price 3-way split (must NOT be mixed)

| Price type | Used for |
|:---|:---|
| Uniswap price (sqrtPriceX96) | LP math — tick range, liquidity amounts |
| Mark price (HL) | Hedge target — delta calculation |
| Oracle price (HL) | Stop placement — NV-1/NV-3 gate |

---

## 4. Inline reference codes — quick lookup

| Code prefix | Meaning | Defined in |
|:---|:---|:---|
| `FM-*` | Feature ID | `feature-map.md` |
| `BR-PL-*` / `BR-ADM-*` / `BR-EX-*` / `BR-MOB-*` / `BR-WLA-*` | Business rule by portal | `common-rules.md` |
| `FR-EXBOT-*` | Functional requirement (EXBOT SRS) | `srs/spec.md` |
| `PTL-*` | Portal ID | `backbone.md`, `feature-map.md` |
| `ACT-*` | Actor ID | `backbone.md`, `feature-map.md` |
| `UC-EXBOT-*` | Use case (EXBOT) | `usecases/index.md` |
| `NV-*` | Phase 0 Not-Yet-Verified item | `SPEC_v5.2.6_EN.md §0.5` |
| `SC-*` | Screen state inside a UI UC | Per-UC spec §2 (UI portals only) |
| `API-XB-*` | REST endpoint (EXBOT OPERATOR facade) | `qc-site-map.md §5` |
| `QUE-XB-*` | Queue consumer (EXBOT) | `qc-site-map.md §5` |
| `DO-XB-*` | Durable Object (EXBOT) | `qc-site-map.md §5` |
| `SCR-ADM-*` | Screen (BNZA-ADMIN) | `qc-site-map.md §5` |
| `SCR-EX-*` | Screen (BNZA-EX) | `qc-site-map.md §5` |
| `SCR-POOL-*` | Screen (BNZA-POOL) | `qc-site-map.md §5` |
| `SFLOW-*` | Navigation/screen flow | `qc-site-map.md §6` |

---

## 5. OOS boundary reminder

PTL-01 (WL Mobile) and PTL-06 (WL Admin) are **OOS — Helix scope**.
- Features `FM-WLA-*` and `FM-MOB-*` → `In scope? = No` in `qc-dashboard.md`.
- `qc-uc-read` MUST NOT create review reports for OOS features.
- The only BNZA endpoint side to test for OOS portals is the `FM-OPW-*` OPERATOR WL Backend (the API that Helix calls into).
