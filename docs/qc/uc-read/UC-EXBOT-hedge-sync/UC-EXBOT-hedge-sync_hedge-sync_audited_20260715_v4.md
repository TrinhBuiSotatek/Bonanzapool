---
title: "UC Readiness Review — UC-EXBOT-hedge-sync (Execute Delta-Only Hedge Adjustment)"
date_created: 2026-07-15
author: QC UC Read ExBot Agent
version: v4
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-hedge-sync.md (updated 2026-07-13)
prior_report: docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260706_v3.md
---

# UC Readiness Review — UC-EXBOT-hedge-sync v4

## Feature Brief

UC-EXBOT-hedge-sync mô tả quy trình tự động điều chỉnh vị thế short ETH trên Hyperliquid (HL) của một ExBot đang hoạt động theo nguyên tắc "delta-only" — chỉ gửi lệnh điều chỉnh đúng phần chênh lệch giữa kích thước short mục tiêu và kích thước short thực tế. Actor chính là Hedge-Sync Worker (AWS Lambda) xử lý message từ hàng đợi `hedge-sync`.

Luồng chính bao gồm: (1) kiểm tra idempotency qua bảng `queue_idempotency`; (2) kiểm tra `stateVersion` và recheck `circuit_breakers.state` trước khi giành khóa; (3) giành phân tán mutex qua **User Lock (Redis Redlock via ElastiCache)** với TTL=90s và `idempotencyKey=hedge-sync:{botId}:{stateVersion}`; (4) fetch `clearinghouseState` từ HL sau khi giành khóa; (5) tính delta BigDecimal; (6) gửi lệnh `adjustShortDelta`; (7) thay stop qua **INV-STOP protocol** (§19.5); (8) giải phóng khóa; (9) Reconcile Worker xác nhận kích thước thực tế và cập nhật `hedge_legs`.

**Thay đổi trong phiên bản này (2026-07-13):** BA bổ sung hai fix: Q-N1 — thêm FR-EXBOT-092 vào §7 FR Trace; Q12 — thay Mermaid placeholder bằng reference tới flows.md F-02. Ngoài ra, BA đã cập nhật spec.md, frd.md, flows.md, states.md, erd.md vào ngày 2026-07-14 với một loạt fix về numbering, state registry, và flow notation.

**Score v3: 84/100 — Conditionally Ready.** Re-audit này đánh giá toàn bộ tác động của các cập nhật tài liệu 2026-07-13 và 2026-07-14.

---

## §0 Scope & Linked Artifacts

| Item | Value |
|---|---|
| UC ID | UC-EXBOT-hedge-sync |
| Linked User Stories | US-EXBOT-006, US-EXBOT-008 |
| FR Trace (UC §7 — updated 2026-07-13) | FR-EXBOT-020, FR-EXBOT-021, FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-035, FR-EXBOT-036, **FR-EXBOT-092** |
| SRS Baseline | srs/spec.md, srs/states.md, srs/flows.md, srs/erd.md (as of 2026-07-14) |
| FRD Baseline | frd.md (as of 2026-07-14 — FR renumbering: 091=Rate Limiter, 092=User Lock, 093=Pool Slot0 Cache) |
| Prior audit | UC-EXBOT-hedge-sync_hedge-sync_audited_20260706_v3.md (Conditionally Ready, 84/100) |

---

## §1 Summary of Changes (2026-07-13 + 2026-07-14 Updates)

### A. UC file changes (2026-07-13)

| Location | Before | After | Impact |
|---|---|---|---|
| §7 FR Trace | FR-EXBOT-020 … FR-EXBOT-036 (no FR-092) | Added **FR-EXBOT-092** | **Q-N1 resolved** — traceability gap closed |
| Diagram section | Generic Mermaid placeholder | Reference to flows.md **F-02: Hedge-Sync Execution (Delta-Only)** | **Q12 resolved** — tester has a concrete diagram to follow |

### B. SRS/FRD document updates (2026-07-14)

| Document | Change | Impact on hedge-sync |
|---|---|---|
| frd.md | FR renumbering: FR-090→091 (Rate Limiter), FR-091→092 (User Lock), FR-092→093 (Pool Slot0 Cache) — aligned with spec.md | UC §7 FR Trace cites FR-EXBOT-092 (User Lock) — now correctly matches both spec.md and frd.md after fix |
| spec.md | FR renumbering aligned; no hedge-sync logic changes | Confirms FR-EXBOT-091 = Rate Limiter, FR-EXBOT-092 = User Lock |
| flows.md | F-01 step 11: "freeze" → "suppress routine hedge-sync (this tick only)"; F-04 added `hedge_close_pending` transition and Redlock participant | F-02 (hedge-sync) unchanged in logic; F-01 clarification removes ambiguity about freeze behavior |
| states.md | Added `user_redeem` column to State Registry (I-N1 fix) | No impact on hedge-sync |
| erd.md | Added `funding_rolling_metrics` to `state_db_shard` table listing note | No direct impact on hedge-sync test design |

### C. Q3 answered by Tech Lead (2026-07-14)

| Question | Answer | Impact |
|---|---|---|
| Q3 (OQ-EXBOT-014): marginSummary fetch before or after Redlock acquire? | **After lock** — Flow: Lock → fetch marginSummary → update margin_status → check risk → mutation → unlock | **Q3 closed** — UC step 4 confirmed. Test design: lock TTL must account for HL marginSummary fetch time; heartbeat extend() covers slow HL response |

---

## §2 Cross-Check: UC vs SRS (v4 delta)

All §F.1–§F.5, business rules, alternate flows, and baseline issue register from v2 remain valid. The v3 delta (terminology sync) remains resolved. Only the following new findings apply.

### 2.1 Issues resolved in this audit pass

| ID | Resolution |
|---|---|
| Q-N1 | FR-EXBOT-092 added to UC §7 FR Trace in 2026-07-13 update. **Closed.** |
| Q12 | Diagram section updated to reference flows.md F-02. **Closed.** |
| Q3 | marginSummary fetch confirmed AFTER lock by Tech Lead. UC step 4 sequence confirmed. **Closed.** |

### 2.2 New findings from 2026-07-14 SRS update cross-check

#### Finding N4-01 — FR-EXBOT-040 missing from UC §7 FR Trace (MISSING_INFO, Minor)

| Field | Value |
|---|---|
| Issue ID | N4-01 |
| Type | MISSING_INFO |
| Severity | Minor |
| Affected area | Area 1 (Inventory) / Area 5 (Documentation Quality) |
| Source trace | UC §7 FR Trace; UC §3 step 2 "rechecks `circuit_breakers.state`"; UC §4 A3 "call `incrementCircuitBreaker`"; spec.md FR-EXBOT-040; us-008.md AC-EXBOT-008-1/3/4 |
| Finding | UC §7 FR Trace does not cite FR-EXBOT-040 (Circuit Breaker). However, the UC explicitly: (a) requires `circuit_breakers.state IN ('closed','half_open')` as precondition; (b) step 2 rechecks `circuit_breakers.state` at execution time; (c) A3 calls `incrementCircuitBreaker`; (d) postcondition states `circuit_breakers.failure_count` incremented on failure or reset on half_open success. FR-EXBOT-040 governs all of this behavior. US-EXBOT-008 (linked story) is entirely about circuit breaker state management and cites FR-EXBOT-040. The FR Trace omission creates a traceability gap between UC and US-008. |
| Impact on tester | Tester reading FR Trace cannot directly trace to FR-EXBOT-040 for circuit breaker behavior. Minor — the behavior IS described in UC prose and US-008 AC, so test design is not blocked. |
| Suggested fix | Add FR-EXBOT-040 to UC §7 FR Trace. |
| Status | Open — Minor; BA to add when convenient |

#### Finding N4-02 — FR-EXBOT-060 missing from UC §7 FR Trace (MISSING_INFO, Minor)

| Field | Value |
|---|---|
| Issue ID | N4-02 |
| Type | MISSING_INFO |
| Severity | Minor |
| Affected area | Area 1 (Inventory) / Area 5 (Documentation Quality) |
| Source trace | UC §3 step 4 (implicit marginSummary fetch → margin_status update); spec.md FR-EXBOT-060; Q3 answer (Tech Lead 2026-07-14) |
| Finding | UC §7 FR Trace does not cite FR-EXBOT-060 (Margin Status). However, the Q3 answer (now resolved) confirmed that the Worker fetches `marginSummary` from HL AFTER acquiring the lock and updates `margin_status` before executing the hedge mutation. This means FR-EXBOT-060 is directly exercised during every hedge-sync run (the margin thresholds ok < 0.55, warning 0.55–0.75, critical ≥ 0.75 affect whether the hedge mutation proceeds). UC step 4 reads "Fetch actual HL position via `clearinghouseState`" but does not explicitly mention the marginSummary fetch and margin_status update as a separate sub-step. |
| Impact on tester | Tester cannot directly trace margin_status update behavior to a cited FR. The threshold values (0.55, 0.75) and their effect on the flow are not documented in the UC itself — they exist only in spec.md FR-EXBOT-060. Minor gap: tester must look up FR-EXBOT-060 in spec.md independently. |
| Suggested fix | (a) Add FR-EXBOT-060 to UC §7 FR Trace. (b) Add explicit sub-step in UC step 4: "Fetch HL `marginSummary` (weight=X); update `margin_status` per FR-EXBOT-060 thresholds (ok < 0.55, warning 0.55–0.75, critical ≥ 0.75)." |
| Status | Open — Minor; BA to add when convenient |

#### Finding N4-03 — UC step 2 combines stateVersion check + circuit recheck in one step without explicit ordering (UNCLEAR_INFO, Minor)

| Field | Value |
|---|---|
| Issue ID | N4-03 |
| Type | UNCLEAR_INFO |
| Severity | Minor |
| Affected area | Area 3 (Functional Logic) |
| Source trace | UC §3 step 2; flows.md F-02; spec.md FR-EXBOT-027; spec.md FR-EXBOT-040 |
| Finding | UC step 2 reads: "Worker reads Aurora PostgreSQL `bots.state_version`; if mismatch with message `stateVersion` → discard (status='skipped'); Worker rechecks `circuit_breakers.state` at execution time; if `open` → discard (status='skipped')" — both checks combined in one step. F-02 (flows.md) separates them: `check stateVersion match` is shown before `recheck circuit_breakers.state`. The step ordering matters: if stateVersion check is first, a stale message is discarded before consuming a circuit breaker recheck DB read. The combined step 2 does not explicitly state which check runs first. |
| Impact on tester | Does not block test design — both checks produce status='skipped', and test cases can verify each independently. However, a tester designing boundary/ordering tests needs to know if a single message delivery can be discarded due to stateVersion mismatch before the circuit recheck is even executed. |
| Suggested fix | Split UC step 2 into two explicit steps: 2a (stateVersion check) and 2b (circuit recheck), or add a note "stateVersion checked first, circuit recheck second" to preserve the explicit ordering from F-02. |
| Status | Open — Minor; no block on current test design |

### 2.3 Carry-forward: Open issues from v3 (status update)

| ID | Priority | Status | Note |
|---|---|---|---|
| Q1 | High | Open — Pending zen (OQ-EXBOT-013) | delta=0 behavior (A6): UC A6 says "skip HL order; proceed to stop replacement." UC note still says "Behavior pending OQ-EXBOT-013." Partial documentation exists — A6 is written — but zen has not confirmed it. |
| Q2 | High | Open — Pending zen (OQ-EXBOT-002) | INV-STOP path: place-before-cancel vs cancel-before-place? Unchanged. |
| Q6 | Medium | Open — Pending zen (OQ-EXBOT-011) | lpValueUsd formula for partial_repair drift_threshold. Unchanged. |
| Q7 | Medium | Open — Blocked by Q1 | entry_price/liq_price update when delta=0. Unchanged. |
| Q4 | Medium | Deferred | Rate-limit weight timing vs lock order (OQ-EXBOT-015). Unchanged. |

---

## §3 Acceptance Criteria — v4 update (incremental)

AC candidates from v2/v3 remain valid. The following are updated or new based on v4 findings.

| AC # | Scenario | Given | When | Then | Source / Note |
|---|---|---|---|---|---|
| AC-13 (updated) | marginSummary fetch ordering | Bot is active; Worker has acquired User Lock | Worker executes step 4 (clearinghouseState + marginSummary fetch) | `margin_status` in DB is updated before hedge mutation proceeds; if marginSummary HL call is slow (> ~80s), `extend()` is called before TTL=90s expires | Q3 answer (Tech Lead 2026-07-14); spec.md FR-EXBOT-060; FR-EXBOT-092 |
| AC-14 (new) | Circuit breaker FR trace | UC §7 FR Trace | — | FR-EXBOT-040 is cited; tester can directly trace circuit breaker pre/postcondition behavior to FR | N4-01 — Suy luận cần xác nhận |
| AC-15 (new) | Margin status FR trace | UC §7 FR Trace | — | FR-EXBOT-060 is cited; tester can directly trace margin threshold rules (0.55/0.75) to FR | N4-02 — Suy luận cần xác nhận |

---

## §10.3 Audit Summary

### Scoring Table

| Area | Max | v2 Score | v3 Score | v4 Score | Delta v3→v4 | Notes |
|---|---|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 19 | 19 | **19** | 0 | Q-N1 closed (FR-092 now in FR Trace). N4-01/N4-02 are Minor traceability gaps (FR-040 and FR-060 not in FR Trace). Both behaviors ARE described in UC prose and SRS — no inventory blindspot for tester. No deduction. |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 21 | 21 | **22** | +1 | Q3 closed: marginSummary fetch ordering confirmed → margin_status update behavior fully traceable. Q1/Q2 still open but unchanged. |
| 3. Functional Logic & Workflow Decomposition | 25 | 21 | 21 | **22** | +1 | Q3 answer clarifies step 4 explicitly (lock→marginSummary→margin_status→mutation). Q12 closed (F-02 reference added). N4-03 (step 2 ordering ambiguity) is Minor — no deduction. Q1/Q2 blockers unchanged. |
| 4. Functional Integration & Data Consistency | 15 | 13 | 14 | **14** | 0 | No new integration issues. N4-02 (FR-060 marginSummary) is a documentation quality gap, not an integration gap — behavior is defined in spec.md. |
| 5. UC / Spec Documentation Quality | 15 | 8 | 9 | **10** | +1 | Q12 closed (diagram reference added). Q-N1 closed (FR-092 in FR Trace). N4-01/N4-02/N4-03 are Minor — collectively -1 from perfect. |
| **Total** | **100** | **82** | **84** | **87** | **+3** | |

**Score: 87/100 — Conditionally Ready** (score improved +3; verdict unchanged)

### Verdict: CONDITIONALLY READY (87/100)

**Positive changes in v4:**
- Q3 (High — OQ-EXBOT-014) closed: marginSummary fetch confirmed AFTER lock. Full flow sequence locked: Lock → marginSummary → margin_status → mutation → unlock.
- Q-N1 closed: FR-EXBOT-092 added to UC §7 FR Trace.
- Q12 closed: Diagram reference to flows.md F-02 added.

**Remaining blockers (unchanged):**
- **Q1 (High — OQ-EXBOT-013):** delta=0 behavior in A6 — UC documents "skip HL, proceed to stop replacement" but explicitly flags "Behavior pending OQ-EXBOT-013". Zen confirmation outstanding.
- **Q2 (High — OQ-EXBOT-002):** INV-STOP cancel/place order on HL. Blocks test design for F1-09/F1-10 sequence.

**New minor documentation gaps (non-blocking):**
- **N4-01:** FR-EXBOT-040 (Circuit Breaker) not in UC §7 FR Trace. Minor traceability gap only.
- **N4-02:** FR-EXBOT-060 (Margin Status) not in UC §7 FR Trace + UC step 4 does not explicitly mention marginSummary fetch as a sub-step. Minor.
- **N4-03:** UC step 2 combines stateVersion check and circuit recheck without explicit ordering. Minor.

**Open medium issues (unchanged from v3):**
- **Q6 (OQ-EXBOT-011):** lpValueUsd formula for partial_repair drift_threshold.
- **Q7:** entry_price/liq_price update when delta=0 (blocked by Q1).

**Recommendation:**
87/100 — proceed to test scenario design and test case execution for all confirmed flows (happy path, A1–A6 except A6 full expected result pending Q1). The two High blockers (Q1, Q2) require zen input before AC-11 and F1-09/F1-10 test cases can be finalized. BA should add FR-EXBOT-040, FR-EXBOT-060 to §7 FR Trace and clarify step 2 ordering (N4-01/N4-02/N4-03) in the next UC pass.

---

## §11 Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Initial audit; score 74/100 |
| v2 | 2026-07-02 | QC UC Read ExBot Agent | Re-audit after BA Q&A (qc-notes-temp.md): Q5/Q8/Q9/Q10 closed; score 82/100 |
| v3 | 2026-07-06 | QC UC Read ExBot Agent | Re-audit after BA arc-migration update (2026-07-04): UserLockDO→Redlock, D1→Aurora terminology sync; Q-N1 new Low gap; score 84/100 |
| v4 | 2026-07-15 | QC UC Read ExBot Agent | Re-audit after BA updates 2026-07-13 + 2026-07-14: Q3/Q-N1/Q12 closed; new Minor gaps N4-01/N4-02/N4-03; frd.md FR renumbering confirmed; score 87/100 |

---

*Report generated by: QC UC Read ExBot Agent | Device: MTS-978 | Run ID: run-20260715-000001-trinhbui*
