---
title: "UC Readiness Review — UC-EXBOT-hedge-sync (Execute Delta-Only Hedge Adjustment)"
date_created: 2026-07-06
author: QC UC Read ExBot Agent
version: v3
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-hedge-sync.md (updated 2026-07-04)
prior_report: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260702_v2.md
---

# UC Readiness Review — UC-EXBOT-hedge-sync v3

## Feature Brief

UC-EXBOT-hedge-sync mô tả quy trình tự động điều chỉnh vị thế short ETH trên Hyperliquid (HL) của một ExBot đang hoạt động theo nguyên tắc "delta-only" — chỉ điều chỉnh phần chênh lệch giữa kích thước short mục tiêu và kích thước short thực tế. Actor chính là Hedge-Sync Worker (AWS Lambda) xử lý message từ hàng đợi `hedge-sync`. Worker kiểm tra idempotency, stateVersion, recheck circuit breaker, giành phân tán mutex qua **Redis Redlock (ElastiCache)**, lấy vị thế thực tế từ HL, tính delta BigDecimal, gửi lệnh delta-only, thay stop via INV-STOP protocol, và đợi Reconcile Worker xác nhận.

**Thay đổi trong phiên bản này (2026-07-04):** BA cập nhật terminology: `UserLockDO` → `User Lock (Redis Redlock via ElastiCache)` và `D1` → `Aurora PostgreSQL` trên toàn UC. Thay đổi này đồng bộ UC với SRS spec.md FR-EXBOT-092 (đã update sang AWS arc từ 2026-07-03). Không có thay đổi về logic, luồng xử lý, hay business rule.

**Score v2: 82/100 — Conditionally Ready.** Re-audit này đánh giá tác động của thay đổi terminology lên consistency score.

---

## §0 Scope & Linked Artifacts

| Item | Value |
|---|---|
| UC ID | UC-EXBOT-hedge-sync |
| Linked User Stories | US-EXBOT-006, US-EXBOT-008 |
| FR Trace (UC §7) | FR-EXBOT-020, FR-EXBOT-021, FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-035, FR-EXBOT-036 |
| SRS Baseline | srs/spec.md, srs/states.md, srs/flows.md, srs/erd.md (as of 2026-07-04) |
| Prior audit | UC-EXBOT-hedge-sync_hedge-sync_audited_20260702_v2.md (Conditionally Ready, 82/100) |

---

## §1 Summary of Changes (2026-07-04 UC Update)

| Location | Before | After | Impact |
|---|---|---|---|
| §1 Actors — lock component | `UserLockDO` | `User Lock (Redis Redlock via ElastiCache)` | Terminology only — behavior unchanged |
| §1 Actors — DB component | `D1` | `Aurora PostgreSQL` | Terminology only — behavior unchanged |
| §3 step 3 | `User Lock.acquire(holderToken, ttl=90s, idempotencyKey=hedge-sync:{botId}:{stateVersion})` | Same text; label changed to "User Lock (Redis Redlock via ElastiCache)" | Terminology only |
| §3 step 10 | `User Lock.release(holderToken, idempotencyKey, result)` | Same text; label aligned | Terminology only |
| FR Trace §7 | No FR-EXBOT-092 | No FR-EXBOT-092 (not added) | **Gap: FR-092 is the new detailed interface spec for Redlock — not cited in UC §7** |

**Assessment:** The 2026-07-04 update resolves the only terminology inconsistency that existed in v2 between the UC (which still used `UserLockDO`) and the SRS (which had already migrated to Redlock/ElastiCache in the 2026-07-03 arc-migration pass). All logic, business rules, and alternate flows remain unchanged.

**New minor gap found:** UC §7 FR Trace still lists `FR-EXBOT-026` (User Lock conceptual requirement) but does not include `FR-EXBOT-092` (Redlock detailed interface: `acquire/extend/release`, TTL=90s, idempotencyKey pattern, Lua-script ownership check). FR-092 is the implementation-level companion to FR-026. This is the same category of FR Trace gap as Q8 in v1 (resolved in v2). It does not block test design since FR-092 is already cited in v2 report §F.1/F.2 via cross-reference.

---

## §2 Cross-Check: UC vs SRS (v3 delta only)

All §F.1–§F.5, business rules, alternate flows, and issue register from v2 remain valid. Only the following changes apply:

### Terminology consistency (resolved)

| Item | v2 status | v3 status |
|---|---|---|
| UC uses `UserLockDO` vs SRS uses `Redlock/ElastiCache` | Inconsistency noted in v2 §F.2 F1-03 (cited FR-EXBOT-092 but UC text still said UserLockDO) | **Resolved** — UC now says "User Lock (Redis Redlock via ElastiCache)" — matches FR-EXBOT-026 and FR-EXBOT-092 |
| UC uses `D1` vs SRS uses `Aurora PostgreSQL` | Inconsistency in v2 (no issue raised — D1 terminology was consistent within UC context at the time) | **Resolved** — UC now says `Aurora PostgreSQL` consistently |

### New gap: FR-EXBOT-092 not in §7 FR Trace

| Issue ID | Type | Severity | Source Trace | Finding | Impact | Status |
|---|---|---|---|---|---|---|
| Q-N1 | MISSING_INFO | Low | UC §7 FR Trace; spec.md FR-EXBOT-092 | UC §7 FR Trace lists `FR-EXBOT-026` (User Lock conceptual) but not `FR-EXBOT-092` (Redlock interface detail: acquire/extend/release, TTL=90s, idempotencyKey pattern, Lua script ownership). FR-092 was added to SRS in the 2026-07-03 arc-migration pass as a companion to FR-026. | Does not block test design — FR-092 details are already documented in the v2 audit report §F.1 F1-03/F1-23. Tester can reference spec.md FR-EXBOT-092 directly. Minor traceability gap only. | Open — Low priority; BA to add FR-092 to UC §7 FR Trace when convenient |

### Carry-forward: Open issues from v2 (unchanged)

| ID | Priority | Status | Note |
|---|---|---|---|
| Q1 | High | Open — Pending zen (OQ-EXBOT-013) | delta=0 behavior (A6): stop replacement or abort? UC note still says "Behavior pending OQ-EXBOT-013". 2026-07-04 update did not address. |
| Q2 | High | Open — Pending zen (OQ-EXBOT-002) | INV-STOP path: place-before-cancel vs cancel-before-place? 2026-07-04 update did not address. |
| Q3 | High | Open — Pending Tech Lead (OQ-EXBOT-014) | marginSummary fetch order relative to lock acquire. Not addressed. |
| Q6 | Medium | Open — Pending zen (OQ-EXBOT-011) | lpValueUsd formula for partial_repair threshold. Not addressed. |
| Q7 | Medium | Open — Blocked by Q1 | entry_price/liq_price update when delta=0. |
| Q4 | Medium | Deferred | rate-limit weight timing vs lock order. |
| Q11 | Low | Open — No block | SOLUTION_DETAIL_LEAK: step ordering rationale not explained. |
| Q12 | Low | Open — No block | UC diagram is generic placeholder. |

---

## §10.3 Audit Summary

### Scoring Table

| Area | Max | v1 Score | v2 Score | v3 Score | Delta v2→v3 | Notes |
|---|---|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 17 | 19 | **19** | 0 | Terminology fix (UserLockDO → Redlock) improves cross-source consistency but Area 1 was already at 19 (deduction for Q12 diagram). Q-N1 (FR-092 missing from FR Trace) is Low — no additional deduction. |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 18 | 21 | **21** | 0 | Q1/Q2 still open. No new issues in this area. |
| 3. Functional Logic & Workflow Decomposition | 25 | 18 | 21 | **21** | 0 | No change to logic or flows. Q1 caveat (OQ-013) remains. |
| 4. Functional Integration & Data Consistency | 15 | 12 | 13 | **14** | +1 | Terminology mismatch (D1 / UserLockDO vs Aurora/Redlock) was a minor cross-source inconsistency in v2. Now resolved → +1. |
| 5. UC / Spec Documentation Quality | 15 | 9 | 8 | **9** | +1 | UserLockDO→Redlock terminology sync removes a documentation quality issue that was implied in v2. Q-N1 (FR-092 not in FR Trace) is noted but Low → no deduction. |
| **Total** | **100** | **74** | **82** | **84** | **+2** | |

**Score: 84/100 — Conditionally Ready** (unchanged verdict; score improved by +2 from terminology consistency)

### Verdict: CONDITIONALLY READY (84/100)

**Positive changes since v2:**
- UC terminology now consistent with SRS arc-migration: `User Lock (Redis Redlock via ElastiCache)` and `Aurora PostgreSQL` throughout.
- Area 4 improved +1: cross-source consistency between UC and SRS locking terminology resolved.
- Area 5 improved +1: documentation quality improved by terminology alignment.

**Remaining blockers (unchanged from v2):**
- **Q1 (High — OQ-EXBOT-013):** delta=0 behavior in A6: is stop replacement executed or the entire hedge-sync aborted? UC explicitly says "Behavior pending OQ-EXBOT-013". Tester cannot write complete expected result for A6.
- **Q2 (High — OQ-EXBOT-002):** INV-STOP cancel/place order on HL: place-before-cancel vs cancel-before-place? Blocks test design for F1-09/F1-10 sequence.

**Open medium issues (unchanged from v2):**
- **Q3 (OQ-EXBOT-014):** marginSummary fetch ordering relative to Redlock acquire.
- **Q6 (OQ-EXBOT-011):** lpValueUsd formula for partial_repair drift_threshold.
- **Q7:** entry_price/liq_price update when delta=0 (blocked by Q1).

**New low issue:**
- **Q-N1:** FR-EXBOT-092 not in UC §7 FR Trace. Low priority — does not block test design.

**Recommendation:**
84/100 — proceed to test scenario design and test case execution for all confirmed flows (happy path, A1–A6 except A6 full expected result). The two remaining blockers (Q1, Q2) require zen/Tech Lead input. No BA-addressable gaps remain from this re-audit pass; the 2026-07-04 update was complete and correct for what it set out to fix.

---

## §11 Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Initial audit; score 74/100 |
| v2 | 2026-07-02 | QC UC Read ExBot Agent | Re-audit after BA Q&A (qc-notes-temp.md): Q5/Q8/Q9/Q10 closed; score 82/100 |
| v3 | 2026-07-06 | QC UC Read ExBot Agent | Re-audit after BA arc-migration update (2026-07-04): UserLockDO → Redis Redlock, D1 → Aurora PostgreSQL terminology sync; Q-N1 new Low gap; score 84/100 |

---

*Report generated by: QC UC Read ExBot Agent | Device: MTS-978 | Run ID: run-20260706-000020-trinhbui*
