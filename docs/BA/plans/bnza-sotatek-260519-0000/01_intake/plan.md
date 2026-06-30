---
type: plan
status: in-progress
created: 2026-05-26
updated: 2026-05-27
owner: "@hien.duong"
project: bnza-sotatek-2026-05-19
lang: vi
changelog:
  - "2026-05-27 | manual | meeting 2026-05-27: revised Milestone 1 scope (MLM-first, EXBOT deferred), June 2 go-live, added scalability + migration pending items"
  - 2026-05-27 | manual | Phase 1 ascii-screen rewrite complete (26 files); Phase 2 non-ascii-screen update in-progress
  - 2026-05-26 | manual | initial plan.md — backbone đã có, options phase không cần thiết
---

# Plan: BNZA-SOTATEK BA Documentation

## Trạng thái hiện tại

| Phase | Status | Notes |
|-------|--------|-------|
| 0 — Bootstrap | ✅ Done | Workspace `bnza-sotatek-2026-05-19/` đã tồn tại |
| 1 — Intake | ✅ Done | `01_intake/intake.md` + `escalation-mobile-blockers.md` đã có |
| 2 — Backbone | ✅ Done | `02_backbone/backbone.md` + `feature-map.md` đã có |
| 3 — Options | ⏭️ Not needed | Không có options phase — scope đã lock từ client docs |
| 4 — Module FRDs | ✅ Done | Tất cả FRDs đã có (ADMIN, EXBOT, OPERATOR, POOL, EX, MOBILE) |
| 5 — SRS / Stories | 🔄 In progress | POOL SRS + 12 user stories đã có; ADMIN/EX/EXBOT/MOBILE pending |
| 6 — ASCII Screen Rewrite | ✅ Done | 26 files rewritten từ codebase audit (2026-05-27) |
| 7 — Non-ASCII Doc Update | 🔄 In progress | Update ⚡/📋 markers + codebase corrections cho tất cả docs còn lại |

## Milestone Scope

| Milestone | Scope |
|-----------|-------|
| **M1 — WL Go-Live** | MLM + LPBot, MOBILE (WL gate + LP Bot status), ADMIN (WL mgmt + PF distribution), OPERATOR pre-launch hotfixes |
| **M2 — Core Dev** | POOL Step 7, EXBOT Phase A1, ADMIN remaining features, MOBILE EXBOT flow |
| **M3 — Staging** | WL simulation, E2E tests |
| **M4 — Production** | Full production deployment |

> **Strategy change (meeting 2026-05-27):** WL launch product is MLM with LPBot (not EXBOT). EXBOT est. 6 weeks post-WL. Original Milestone 1 (bug fixing + staging for Pool/Exchange/Admin) has been superseded by this expanded scope.

## Pending Reports (blocking decisions)

| Report | Owner | Blocks |
|--------|-------|--------|
| CF infrastructure feasibility (10k bots, concurrent worker limit) | Daniel | EXBOT scale architecture decisions |
| Mainnet data migration validation plan (~8 users, ~250k fund) | Andrew | Monorepo deploy sequencing |

## Module FRD Status

| Module | Folder | FM-IDs | FRD Status | SRS Status | ASCII Screens | Priority |
|--------|--------|--------|------------|------------|---------------|----------|
| ADMIN | `03_modules/admin/` | FM-ADM-01→FM-ADM-10 | ✅ Done | ✅ Done | ✅ 17 screens done | T0/T1/T2 |
| EXBOT Infra | `03_modules/exbot/` | FM-XB-01→FM-XB-13 | ✅ Done | ⏳ Pending | N/A (backend) | T0/T1 |
| OPERATOR | `03_modules/operator/` | (backend API) | ✅ Done | ⏳ Pending | ✅ api-overview done | T0 |
| POOL | `03_modules/bnza-pool/` | FM-PL-01→FM-PL-02 | ✅ Done | ✅ Done (84 FRs) | ✅ 5 screens done | T1/T2 |
| EX | `03_modules/bnza-ex/` | FM-EX-01→FM-EX-03 | ✅ Done | ✅ Done | ✅ 2 screens done | T2 |
| MOBILE | `03_modules/mobile/` | FM-MOB-01→FM-MOB-11 | ✅ Done | ✅ Done | ✅ 7 screens done | T0/T1 |

## Next Steps

1. **Phase 7 — Non-ASCII Doc Update** — add ⚡/📋 markers + codebase corrections cho tất cả FRDs, use cases, user stories, SRS (in-progress)
2. **MOBILE ASCII Screens** — tạo ascii-screen docs cho MOBILE module (11 FM-IDs)
3. **SRS / User Stories** — bắt đầu từ T0 modules (ADMIN, EXBOT, OPERATOR)
4. **OQ Resolution** — resolve các P0/P1 OQs trước khi SRS

## Open Questions (Cross-module)

| ID | Question | Priority | Owner |
|----|----------|----------|-------|
| OQ-OP-05 | PF Distribution — WL partner payout execution logic missing | P0 | @zen |
| OQ-OP-04 | min_collect_usd / min_estimated_profit_usd not implemented | P1 | @zen |
| OQ-OP-06 | Gas cost not deducted before PF calculation | P1 | @zen |
| OQ-XB-01 | zen D1 schema interface specs (blocker for FM-XB-01) | P0 | @zen |
| OQ-XB-05 | Phase A1 start date | P0 | @zen |
