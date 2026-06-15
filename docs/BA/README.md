# BA Docs — BNZA Ecosystem (SOTATEK Scope)

Business-analysis artifacts for the SOTATEK engineering engagement (May 18 – July 12, 2026).
Owner: `@hien.duong` | Workflow: `/ba-start`

**Location:** `docs/sotatek/ba/plans/bnza-sotatek-260519-0000/`

---

## 📁 Folder Structure

```
bnza-sotatek-260519-0000/
│
├── 01_intake/
│   ├── intake.md           ← Project context, scope, stakeholders
│   └── plan.md            ← Delivery plan, milestones
├── 02_backbone/
│   ├── backbone.md        ← System-level: actors, portals, permissions
│   └── feature-map.md     ← Feature map
└── 03_modules/
    ├── bnza-ex/           ← BNZA-EX (Hyperliquid trading)
    │   ├── frd.md         ← Feature Requirements
    │   ├── srs/spec.md    ← System Requirements (main doc)
    │   ├── usecases/
    │   ├── userstories/
    │   └── ascii-screen/
    ├── bnza-pool/         ← BNZA-POOL (Steps 7-8)
    │   ├── frd.md
    │   ├── srs/spec.md
    │   ├── usecases/
    │   ├── userstories/
    │   └── ascii-screen/
    ├── admin/
    ├── mobile/
    ├── operator/
    └── exbot/
```

---

## 🔍 How to Navigate

| Need | Path |
|------|------|
| Hiểu module làm gì | `03_modules/{module}/srs/spec.md` |
| Xem user stories | `03_modules/{module}/userstories/` |
| Xem screen specs | `03_modules/{module}/ascii-screen/` |
| Xem use cases | `03_modules/{module}/usecases/` |
| Xem project context | `01_intake/intake.md` |

**Quick lookup FRs:**
- bnza-ex → `srs/spec.md` §2 (Functional Requirements)
- bnza-pool → `srs/spec.md` §1 (Functional Requirements)

---

## Markers Convention

- **📋 Spec** — feature is in the original client spec
- **⚡ Dev-built** — feature was built by dev team, NOT in client spec

---

## How to Read (Recommended Order)

```
intake.md → backbone.md → module/frd.md → module/userstories/ → module/srs/spec.md → module/ascii-screen/
```

| File | Shows |
|------|-------|
| `intake.md` | Project context, stakeholders, scope |
| `backbone.md` | Actors, portals, cross-module dependencies |
| `{module}/frd.md` | Feature scope, pages/routes |
| `{module}/srs/spec.md` | FRs, NFRs, Business Rules, Errors, Screen inventory |
| `{module}/userstories/us-*.md` | User scenarios with acceptance criteria |
| `{module}/ascii-screen/*.md` | Screen layouts (ASCII), field rules, validation |

---

## Doc Status

| Phase | Status |
|-------|--------|
| Intake + Backbone | ✅ Done |
| Module FRDs | ✅ Done |
| POOL SRS + User Stories | ✅ Done |
| ASCII Screen Rewrite | ✅ Done |
| EX SRS + User Stories | ✅ Done |
| Remaining Modules | 🔄 In progress |

