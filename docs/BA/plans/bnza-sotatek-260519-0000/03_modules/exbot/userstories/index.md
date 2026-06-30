---
owner: "@hien.duong"
updated: 2026-06-29
type: userstories-index
status: draft
created: 2026-06-12
module: exbot
generated_at: 2026-06-12
stale_status: unknown
changelog:
  - 2026-06-29 | manual | retire US-011; update AC count 46→42; update Epic 4
  - 2026-06-18 | /ba-do | backfill Linked UCs column for all 12 stories
---

# User Stories Index — exbot

| Field | Value |
|---|---|
| index_type | `userstories_index` |
| source_artifact | `plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories` |
| source_hash | `` |
| generated_at | `2026-06-12` |
| generated_by_command | `/ba-do tiep` |
| validated_at | `` |
| validated_by | `` |
| stale_status | `unknown` |

## Story Index

| Story ID | File | Actor | Feature / FR | AC Count | Linked UCs | Linked Screens | Source Backbone IDs | Stale |
|---|---|---|---|---|---|---|---|---|
| US-EXBOT-001 | `us-001.md` | USDC Investor | FR-EXBOT-001, FR-EXBOT-002 | 3 | `uc-bot-start` | — | FM-XB-07 | unknown |
| US-EXBOT-002 | `us-002.md` | USDC Investor | FR-EXBOT-002, FR-EXBOT-050 | 3 | `uc-monitor-status` | — | FM-XB-07 | unknown |
| US-EXBOT-003 | `us-003.md` | USDC Investor | FR-EXBOT-003 | 4 | `uc-pause-resume` | — | FM-XB-07 | unknown |
| US-EXBOT-004 | `us-004.md` | USDC Investor | FR-EXBOT-070 | 3 | `uc-user-redeem` | — | FM-XB-08 | unknown |
| US-EXBOT-005 | `us-005.md` | ExBot System Operator | FR-EXBOT-011, FR-EXBOT-012 | 4 | `uc-light-check` | — | FM-XB-02, FM-XB-07 | unknown |
| US-EXBOT-006 | `us-006.md` | ExBot System Operator | FR-EXBOT-020–023 | 4 | `uc-light-check, uc-hedge-sync` | — | FM-XB-05, FM-XB-02 | unknown |
| US-EXBOT-007 | `us-007.md` | ExBot System Operator | FR-EXBOT-002, FR-EXBOT-080 | 4 | `uc-light-check` | — | FM-XB-07, FM-XB-05 | unknown |
| US-EXBOT-008 | `us-008.md` | ExBot System Operator | FR-EXBOT-040 | 4 | `uc-light-check, uc-hedge-sync` | — | FM-XB-07 | unknown |
| US-EXBOT-009 | `us-009.md` | ExBot System Operator | FR-EXBOT-070, FR-EXBOT-071 | 4 | `uc-bot-safe-close` | — | FM-XB-08, FM-XB-07 | unknown |
| US-EXBOT-010 | `us-010.md` | ExBot System Operator | FR-EXBOT-050, FR-EXBOT-060 | 4 | `uc-bot-safe-close` | — | FM-XB-07 | unknown |
| US-EXBOT-011 | `us-011.md` | USDC Investor (agent key) | FR-EXBOT-081 | 4 | `uc-agent-key` | — | FM-XB-01 | **retired** |
| US-EXBOT-012 | `us-012.md` | ExBot Admin (zen) | FR-EXBOT-070, FR-EXBOT-002 | 4 | `uc-bot-safe-close` | — | FM-XB-08, FM-XB-07 | unknown |

## Epic Summary

| Epic | Stories | Priority |
|------|---------|---------|
| Epic 1: Investor Bot Lifecycle | US-001–004 | P0 (001,004), P1 (003) |
| Epic 2: System Operations | US-005–007 | P0 |
| Epic 3: Risk & Safety | US-008–010 | P0 |
| Epic 4: Admin | US-012 | P1 (012) |

**Total stories: 11 (1 retired) | Total AC: 42**
