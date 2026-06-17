# BA Docs — BNZA Ecosystem (SOTATEK Scope)

Business-analysis artifacts for the SOTATEK engineering engagement (May 18 – July 12, 2026).

**Owner:** `@hien.duong` | **Workflow:** `/ba-start`

**Location:** `plans/bnza-sotatek-260519-0000/`

---

## Folder Structure

```
ba/
└── plans/
    └── bnza-sotatek-260519-0000/
        ├── 01_intake/
        │   ├── intake.md          ← Project context, scope, stakeholders, timeline
        │   └── plan.md            ← Delivery milestones
        ├── 02_backbone/
        │   ├── backbone.md        ← Actors, portals, permissions, cross-module deps
        │   ├── backbone-index.md  ← Section navigator for backbone.md
        │   ├── feature-map.md     ← Feature IDs (FM-*) per module
        │   └── common-rules.md    ← Shared business rules
        └── 03_modules/
            ├── _shared/           ← Cross-module contracts, WL extension refs
            ├── bnza-ex/           ← Hyperliquid trading frontend (ex.bnza.io)
            ├── bnza-pool/         ← LP management (bnza-pool.sotatek.works)
            ├── admin/             ← Admin dashboard (ops.bnza.io)
            ├── mobile/            ← WL Mobile app
            ├── operator/          ← Backend API engine (api.bnza.io)
            └── exbot/             ← EXBOT infrastructure (deferred)
```

**Per-module structure** (each in `03_modules/{module}/`):

```
{module}/
├── frd.md                  ← Feature Requirements Document — START HERE for module scope
├── frd-wl.md               ← WL extension addendum (some modules only)
├── usecases/               ← Functional use cases (UC-*)
├── userstories/            ← User scenarios with acceptance criteria (optional; UI modules only)
├── ascii-screen/           ← Screen layouts / API surface docs
├── srs/
│   ├── spec.md             ← FRs, NFRs, BRs, data constraints, API constraints
│   ├── flows.md            ← Process flows
│   └── states.md           ← State machines
├── srs.md                  ← Compiled full SRS (generated from srs/ source set)
└── srs-compile-receipt.json ← Compile metadata: counts, hashes, skipped steps
```

---

## Quick Start

### New reader, orienting for the first time:

1. **Project context** → `01_intake/intake.md`
2. **System-wide actors, portals, permissions** → `02_backbone/backbone.md`
3. **Pick a module** → see module table below
4. **Understand what the module covers** → `03_modules/{module}/frd.md`
5. **Detailed requirements** → `03_modules/{module}/srs.md` or `srs/spec.md`

> **Rule of thumb:** `frd.md` tells you *what the module is about and why*. `srs/spec.md` tells you *exactly what it must do*.

### Need to find something fast?

| Need | Where to look |
|------|---------------|
| Project context & scope | `01_intake/intake.md` |
| Who are the actors? | `02_backbone/backbone.md` §3 |
| What portals exist? | `02_backbone/backbone.md` §4 |
| **What does this module cover?** | `03_modules/{module}/frd.md` |
| All feature IDs (FM-*) by module | `02_backbone/feature-map.md` |
| Functional requirements (FR-*) | `03_modules/{module}/srs/spec.md` |
| Process flows | `03_modules/{module}/srs/flows.md` |
| State machines | `03_modules/{module}/srs/states.md` |
| User stories & acceptance criteria | `03_modules/{module}/userstories/` |
| Screen wireframes / API surface | `03_modules/{module}/ascii-screen/` |
| Use case details (UC-*) | `03_modules/{module}/usecases/` |
| Cross-module contracts | `03_modules/_shared/ref-contracts.md` |
| WL extension contracts | `03_modules/_shared/frd-wl-contracts.md` |

---

## Module Summary

| Module | Portal | Primary Actor | What it covers | Status |
|--------|--------|--------------|----------------|--------|
| BNZA-EX | ex.bnza.io | ACT-05 Trader | Hyperliquid trading UI: portfolio, order placement, TradingView | ✅ Done |
| BNZA-POOL | bnza-pool.sotatek.works | ACT-01 End User | LP bot management: create/start/stop bots, view PnL | ✅ Done |
| BNZA-ADMIN | ops.bnza.io | ACT-04 Admin | Ops dashboard: fee reports, user management, system config | 🔄 In progress |
| BNZA-MOBILE | (mobile URLs) | ACT-02 WL User | White-label mobile: pool + bot UI for WL partners | ✅ Done |
| OPERATOR | api.bnza.io | ACT-06 System | Backend API: bot lifecycle, fee collection, relayer pool, WL split | ✅ Done |
| EXBOT | — | ACT-06 System | EXBOT hedging infrastructure (deferred post-WL) | ⚠️ Deferred |

---

## How to Read a Module (Recommended Order)

```
frd.md                      ← Scope, constraints, feature list for this module
    ↓
usecases/index.md           ← UC registry + cross-function dependencies
    ↓
srs/spec.md                 ← FRs, NFRs, BRs
    ↓
srs/flows.md                ← Process flows
    ↓
srs/states.md               ← State machines
    ↓
ascii-screen/               ← Screens or API surface
    ↓
userstories/                ← (optional; UI modules only)
```

| File | Shows |
|------|-------|
| `frd.md` | Module scope, pages/routes, feature breakdown, constraints |
| `usecases/index.md` | UC registry, actor mapping, cross-function edges |
| `srs/spec.md` | FRs, NFRs, Business Rules, data/API constraints |
| `srs/flows.md` | Sequenced process flows (producer → consumer → outcome) |
| `srs/states.md` | Entity state machines with guards and transitions |
| `ascii-screen/` | Screen wireframes (UI modules) or API route inventory (API-only) |
| `userstories/` | User scenarios in Gherkin format with acceptance criteria |
| `srs.md` | Full compiled SRS (single-file, for review/sharing) |
| `srs-compile-receipt.json` | Compile metadata: FR counts, source hashes, skipped steps, deferred scope |

---

## Markers Convention

- **📋 Spec** — feature is in the original client specification
- **⚡ Dev-built** — feature built by dev team, NOT in client spec
- **⚠️ Deferred** — out of M1 scope; gate conditions documented in UC index

---

## BA-Kit Conventions

This folder follows BA-Kit conventions:

- **Frontmatter:** `type`, `status`, `owner`, `links`, `changelog`
- **ID format:** `FR-*`, `UC-*`, `US-*`, `AC-*`, `SCR-*`, `FM-*`
- **Content language:** English for specs, Vietnamese comments OK
- **File encoding:** UTF-8

---

## Branch & Commit Conventions (BA Team)

### Branch Hierarchy

```
dev  ←── ba/main  ←── ba/{member}/{topic}
```

- `ba/main` — long-lived BA base branch owned by BA Lead (`@hien.duong`). All BA member work merges here first.
- Individual members branch off `ba/main`, never directly off `dev`.
- When BA work is ready for engineering handoff, BA Lead merges `ba/main` → `dev` via PR.

### Branch Naming

```
ba/{your-name}/{topic}
```

| Example | When to use |
|---------|-------------|
| `ba/tuana/fee-distribution-uc` | Adding/updating a specific UC |
| `ba/tuana/admin-screen-qc` | QC fixes for screen docs |
| `ba/hoa/mobile-wl-flow` | New flow for a module |

Rules:
- All lowercase, hyphens only (no spaces, no underscores)
- `{topic}` describes the artifact being changed, not the Jira ticket
- Base off `ba/main`, not `dev`

### Commit Messages

```
BA({module}): {what changed} — {artifact type}
```

| Example | Meaning |
|---------|---------|
| `BA(admin): add Block Wallet UC — usecase` | New UC in admin module |
| `BA(admin): fix DR-08 WL Code column — screen` | Screen doc fix |
| `BA(pool): update FR-POOL-012 fee tier — srs` | SRS update |
| `BA(backbone): add ACT-07 actor — backbone` | Backbone change |

Artifact type keywords: `usecase` · `screen` · `srs` · `userstory` · `frd` · `backbone` · `readme`

Rules:
- Module slug matches folder name: `admin`, `pool`, `ex`, `mobile`, `operator`, `exbot`, `backbone`
- Keep subject line under 72 chars
- No "fix typo", "update doc", "minor change" — describe the actual artifact touched

### Workflow for BA Members

```
1. git checkout ba/main && git pull origin ba/main
2. git checkout -b ba/{your-name}/{topic}
3. Make changes, commit with BA({module}): convention
4. git push -u origin ba/{your-name}/{topic}
5. Open PR → base: ba/main (NOT dev)
6. BA Lead reviews + merges to ba/main
```

---

## Maintenance

**Last audit:** 2026-06-08
- All modules through OPERATOR have completed SRS lifecycle
- `srs-compile-receipt.json` present in each completed module — use as completeness signal
- BNZA-ADMIN: ascii-screens complete, SRS in progress
- EXBOT: deferred module, placeholder only
