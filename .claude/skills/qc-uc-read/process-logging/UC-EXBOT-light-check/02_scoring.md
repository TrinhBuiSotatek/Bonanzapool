# Phase 2 Scoring — UC-EXBOT-light-check

## Working notes
- UC-ID: UC-EXBOT-light-check
- mode: first-audit
- Rubric source: scoring-rubric.md (100 pts, 5 areas)
- Note: Area 1 "UI Object Inventory" is adapted to Function/Operation Inventory for this LOGIC-only backend UC. No UI artefacts exist (expected for PTL-04 CF Workers).
- Generated at 2026-06-17T17:20:00+07:00 by qc-uc-read · Phase 2

---

## §A. Issue Register

| Issue ID | Type | Severity | Affected scoring area | Source trace from 01_synthesis.md | Finding | Impact on Agent/tester understanding | Suggested question or fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-001 | MISSING_INFO | Blocker | F.3, F.4 | §F.2 F2-10; §F.3 E4; §F.4 row 4 | `stop_replacing_started_at` overrun detection (age > 60s → partial_repair + SAFE_MODE) is documented in frd FR-EXBOT-011 and spec FR-EXBOT-033, but is **completely absent from UC §3 main flow and UC §4 alternate flows**. UC has 12 steps in main flow and 4 alternates (A1–A4) — none mention this. | Testers cannot know when this path is expected to trigger, how it manifests in the queue, or whether it is part of the light-check contract. Cannot write a test for it from the UC alone. | BA must add this as either a Step 13 or an Alternate Flow A5 in UC §3/§4, referencing spec FR-EXBOT-033. | Open |
| I-002 | MISSING_INFO | Blocker | F.2, F.3 | §F.2 F2-07; §F.5 AC-13 | The UC uses a **3-way price split** (`uniPoolPrice`, `hlMarkPrice`, `hlOraclePrice`) per frd FR-EXBOT-011, but UC §3 Step 7 only mentions reading `sqrtPriceX96` and `currentTick` from MarketDataDO. The UC never explains the source of `hlMarkPrice` for stop trigger evaluation (Step 11). Since BR-EXBOT-003 forbids HL API calls from light-check, the mechanism by which `hlMarkPrice` reaches the light-check worker is architecturally required but undocumented in the UC. | Testers cannot determine: (a) whether hlMarkPrice needs to come from a second DO, D1 cache, or another source; (b) whether a stale hlMarkPrice causes an incorrect stop evaluation. Cannot write boundary tests for stop trigger. | BA must specify the source of `hlMarkPrice` in UC §3 Step 7 or Step 11, consistent with BR-EXBOT-003. | Open |
| I-003 | MISSING_INFO | Blocker | F.2, F.3 | §F.2 F2-04; §F.5 AC-10; §C OQ-EXBOT-10 | `range_boundary_near` formula — "90% to upper/lower range" — is unconfirmed. OQ-EXBOT-10 (spec) explicitly notes the formula is open: tick distance vs price distance not yet decided. This is one of three light-check evaluation formulas that directly determines when a hedge-sync is triggered. | Testers cannot write boundary value tests for `range_boundary_near` without the confirmed formula. A 1-tick-away vs 1%-price-away boundary produces different test data entirely. | OQ-EXBOT-10 must be resolved by zen/BA before test design. UC §3 Step 9 / frd FR-EXBOT-011 must be updated with the confirmed formula. | Open |
| I-004 | MISSING_INFO | Blocker | F.2, F.3 | §F.2 F2-05; §F.5 AC-11; §C OQ-EXBOT-11 | `drift_threshold` formula uses `lpValueUsd × 3%` but OQ-EXBOT-11 (spec) explicitly states `lpValueUsd` formula is undefined and this blocks FR-EXBOT-012 evaluation. `lpValueUsd` is read from `bot_runtime_state.lp_value_usd` but how this value is computed/updated is not documented anywhere accessible. | Testers cannot construct drift_threshold test scenarios without knowing how `lp_value_usd` is populated. The 3% threshold is relative, so the correct test input depends entirely on the `lpValueUsd` value at test time. | OQ-EXBOT-11 must be resolved. frd FR-EXBOT-011 / UC §3 Step 9 must document the `lp_value_usd` update mechanism or reference the FR that does. | Open |
| I-005 | MISSING_INFO | Blocker | F.2, F.3 | §F.2 F2-06; §F.5 AC-12; §C OQ-EXBOT-12 | `funding_alert` formula — 7d funding APR < −15% — has an undefined APR aggregation formula. OQ-EXBOT-12 (spec) explicitly notes the annualization formula is unconfirmed. | Testers cannot compute expected APR values to test the −15% trigger. No formula = no reproducible test case. | OQ-EXBOT-12 must be resolved by zen. frd FR-EXBOT-011 must document the exact aggregation formula. | Open |
| I-006 | MISSING_INFO | Major | F.2 | §F.2 F2-02; §F.5 AC-08 | `circuit_breakers.state='half_open'` requires an atomic claim on `half_open_probe_used` (0→1). UC §4 A2 states "atomically claim" but does NOT specify the mechanism: DB transaction (D1 does not support SELECT FOR UPDATE), DO atomic counter, or CAS. CF D1 has no row-level locking. | Testers cannot determine whether the atomic claim is implemented via DO or a D1 CHECK constraint, so they cannot construct a concurrent delivery test that verifies exactly-once probe behavior. | BA/Tech Lead must specify the atomic mechanism. If it is DO-based, the DO name and method must be documented in the UC or referenced spec FR. | Open |
| I-007 | MISSING_INFO | Major | F.3 | §F.3 E5; §F.4 row 6 | MarketDataDO cache staleness handling: spec FR-EXBOT-093 says the DO logs a warning and forces a refresh when cache is stale. However, the UC never defines what the light-check worker should do if it reads stale data before the refresh completes — return stale evaluation, wait, or discard the message. | Testers cannot write a stale-cache edge case test without knowing the worker's expected behavior. | BA to add a precondition or exception flow covering MarketDataDO cache state (fresh vs stale > 2× TTL). | Open |
| I-008 | CROSS_SOURCE_CONFLICT | Major | F.3, Area 5 | §F.1 F1-09; §C FR-EXBOT-023 | FR-EXBOT-023 (spec) lists 9 canonical RebalanceReason values. UC §3 Step 9 refers to "RebalanceReason[]" but does not enumerate them. frd FR-EXBOT-011 provides the formulas but the count is effectively 7 evaluations (time_fallback, manual_admin, recovery_reconcile are listed in spec FR-EXBOT-023 but not covered by frd FR-EXBOT-011 evaluation criteria). UC lacks coverage of `manual_admin` and `recovery_reconcile` trigger conditions — are they set by light-check or by a different worker? | Testers cannot know whether light-check is responsible for evaluating all 9 reasons or only a subset. | BA must clarify which RebalanceReasons are evaluated by light-check vs set by other workers. UC §3 Step 9 should enumerate the subset or reference the canonical FR explicitly. | Open |
| I-009 | MISSING_INFO | Major | F.4 | §F.4 row 2 | `stateVersion` mismatch handling: US-EXBOT-006 AC-02 states stale hedge-sync messages are discarded, but the UC does not specify what version token (e.g., `bot_runtime_state.state_version`) is embedded in the light-check→hedge-sync queue message or how the light-check worker should obtain this value (from D1 read at Step 6?). | Testers for the hedge-sync worker need to know what `stateVersion` field to set in test queue messages to simulate the stale-message scenario. | BA to confirm which table/column provides the `stateVersion` value and that it is read at Step 6 of light-check. | Open |
| I-010 | UNCLEAR_INFO | Minor | F.3 | §F.1 F1-02 | Scan Worker batch size: UC §3 Step 2 implies a 500-bot LIMIT per shard. The UC does not state what happens when there are > 500 bots due for light-check in a single shard within one cron tick — are subsequent bots deferred to the next cron tick, or does the Scan Worker issue multiple queries? | Minor ambiguity; does not block test design for core light-check behavior, but could affect scale/load tests. | BA to clarify whether 500 is a hard per-tick limit or per-query limit with loop. | Open |
| I-011 | MISSING_INFO | Minor | F.3 | §F.3 exception flows | No error-code/message definitions for light-check worker failures (e.g., D1 read failure at Step 6, DO read failure at Step 7). Spec §5 has E-EXBOT-001 through E-EXBOT-013 but none appear to cover light-check worker failures specifically. | Minor — light-check uses queue retry semantics so message-level error handling is via CF queue retry, not HTTP error codes. Does not block test design for functional paths. | Note only; no action required if error handling is delegated to CF queue infrastructure. | Open |
| I-012 | INTERNAL_INCONSISTENCY | Minor | Area 5 | §F.1 note on F1-09; §C FR-EXBOT-012 (frd) vs FR-EXBOT-013 (spec) | frd.md uses FR-EXBOT-011/012 for light-check core / jitter; spec.md uses FR-EXBOT-012/013 for the same features. The numbering diverges: frd FR-EXBOT-011 = spec FR-EXBOT-012 (light-check logic), frd FR-EXBOT-012 = spec FR-EXBOT-013 (jitter). This is an internal doc numbering inconsistency, not a behavior conflict. | Low impact — content matches despite numbering. May cause confusion when cross-referencing. | BA to align FR numbering between frd.md and spec.md, or add explicit mapping note. | Open |

---

## §B. AC Candidate Review — Not Scored

| AC ID | Source trace | Review note | User confirmation needed | Related issue ID |
|---|---|---|---|---|
| AC-01 | §F.5; §F.3 main flow; BR-EXBOT-003 | 0 HL weight for 10,000-bot cycle. Fully traceable to BR-EXBOT-003 and spec FR-EXBOT-012 AC. Observable via HL API rate counter. | No | — |
| AC-02 | §F.5; §F.2 F2-07; frd FR-EXBOT-011 | uniPoolPrice for drift. Fully traceable. Observable via implementation path. | No | — |
| AC-03 | §F.5; §F.2 F2-03; BR-EXBOT-005; spec FR-EXBOT-032 | stop_trigger_crossed_at write-once. Fully traceable. | No | — |
| AC-04 | §F.5; §F.3 E2/E3; UC §2 | Skip for lp_rebalancing/paused. Fully traceable. | No | — |
| AC-05 | §F.5; §F.2 F2-11; UC §3 Step 5 | Idempotency via UNIQUE constraint. Fully traceable. | No | — |
| AC-06 | §F.5; §F.1 F1-04; NFR-EXBOT-005 | Batch next_light_check_at write. Fully traceable. | No | — |
| AC-07 | §F.5; §F.3 A1; spec FR-EXBOT-014 | Circuit open → still do stop monitoring. Fully traceable. | No | — |
| AC-08 | §F.5; §F.3 A2; UC §4 A2 | Half-open exactly-one probe. Traceable but atomic mechanism undefined. | **Yes — BA/Tech Lead must confirm atomic mechanism** | I-006 |
| AC-09 | §F.5; §F.2 F2-10; frd FR-EXBOT-011/033 | stop_replacing_started_at > 60s → partial_repair + SAFE_MODE. Not in UC §3. | **Yes — BA must add to UC main flow** | I-001 |
| AC-10 | §F.5; §F.2 F2-04; OQ-EXBOT-10 | range_boundary_near formula. Blocked by OQ-EXBOT-10. | **Yes — OQ-EXBOT-10 must be resolved** | I-003 |
| AC-11 | §F.5; §F.2 F2-05; OQ-EXBOT-11 | drift_threshold lpValueUsd. Blocked by OQ-EXBOT-11. | **Yes — OQ-EXBOT-11 must be resolved** | I-004 |
| AC-12 | §F.5; §F.2 F2-06; OQ-EXBOT-12 | funding_alert APR formula. Blocked by OQ-EXBOT-12. | **Yes — OQ-EXBOT-12 must be resolved** | I-005 |
| AC-13 | §F.5; §F.2 F2-07 gap | hlMarkPrice source. Blocked by I-002. | **Yes — BA must confirm source** | I-002 |

---

## §C. Scoring Table

> Note: Area 1 is evaluated as Function/Operation Inventory (LOGIC-only UC adaptation, no UI). No auto-cap applies per Area 1 cap rules ("if design or ASCII screen is referenced but no UI evidence is usable, Area 1 = 0") — the UC is a confirmed backend-only UC with no design artefacts expected. Evaluation is adapted to cover function completeness, data-object inventory, and source mapping.

| # | Scoring Area | Max | Score | Status | Main evidence from 01_synthesis.md | Related issues | Rationale |
|---|---|---:|---:|---|---|---|---|
| 1 | UI Object Inventory & Source Mapping (adapted: Function/Operation Inventory) | 20 | 14 | ⚠️ Partial | §F.1: 15 operations enumerated, all major functions covered (trigger, scan, idempotency, DO read, compute, evaluate, enqueue, state write). Key data objects mapped. Source traced to UC §3/§4/frd/spec. | I-001 (stop_replacing flow absent), I-008 (RebalanceReason subset unclear) | The operation inventory is comprehensive for the documented 12-step flow. Two gaps: (1) stop_replacing_started_at overrun detection (frd/spec only, not in UC) is missing from the UC function list; (2) which RebalanceReasons light-check evaluates vs other workers is not clarified. Score: 14/20 (70%). |
| 2 | Object Attributes, Behavior, Rules, Validations & Messages | 25 | 12 | ⚠️ Partial | §F.2: 12 attribute/behavior rules documented. BR-EXBOT-003/005, FR-EXBOT-023/032 resolved verbatim. 3-way price split documented. Circuit breaker states covered. | I-002 (hlMarkPrice source), I-003 (range_boundary_near formula), I-004 (drift_threshold lpValueUsd), I-005 (funding_alert APR), I-006 (half_open atomic mechanism) | 5 of 12 behavior entries have blockers or major gaps. Three formulas are explicitly OQ-blocked (I-003/I-004/I-005). hlMarkPrice source (I-002) is architecturally critical. Half-open atomic mechanism (I-006) is a major gap. Score: 12/25 (48%) — blocker cap applied: max 40% = 10; but multiple areas partially clear; applying 48% (12/25) without dropping to cap since clear entries outweigh blocked; auto-cap from rule §8 triggers at single blocker → affected area max 40% = 10/25. Applying cap: **10/25**. |
| 3 | Functional Logic & Workflow Decomposition | 25 | 13 | ⚠️ Partial | §F.3: happy path fully documented (12 steps), 4 alternates (A1–A4) covered, 5 exception flows. Business rules synthesized. Queue topology flow complete. | I-001 (stop_replacing path missing from UC), I-002 (price source gap in Step 11), I-007 (MarketDataDO stale handling undefined) | Happy path and circuit-state alternates are well-covered. stop_replacing_started_at overrun path (Blocker I-001) is entirely absent from UC §3/§4. MarketDataDO stale handling (I-007) is undefined. Auto-cap (blocker): max 40% = 10/25. Clear majority of flow is documented → 13/25 nominal; cap applies: **10/25**. |
| 4 | Functional Integration & Data Consistency | 15 | 9 | ⚠️ Partial | §F.4: 7 integration/consistency concerns documented. Queue topology, stateVersion, stop trigger → SAFE_MODE chain, MarketDataDO sharing, D1 batch write constraints all noted. | I-001 (partial_repair integration gap), I-009 (stateVersion field source undefined) | Integration picture is mostly clear. Two issues: (1) partial_repair integration path (I-001) is undocumented in UC; (2) stateVersion field source for hedge-sync message (I-009) is not explicitly mapped. Both are addressable. Score: 9/15 (60%). |
| 5 | UC Documentation Quality | 15 | 8 | ⚠️ Partial | Source UC + cross-artefact checks | I-001, I-002, I-008, I-012 | UC is structurally coherent (7 sections, FR Trace present). Gaps: stop_replacing path absent (Blocker, not in UC scope at all — BA omission); hlMarkPrice source creates an architectural ambiguity not resolvable from UC alone; RebalanceReason subset (I-008) creates cross-source ambiguity; frd/spec numbering conflict (I-012). Auto-cap: "UC has unresolved contradiction across sources that changes expected behavior" → Area 5 max 8/15 and affected content area max 70%. Applying: **8/15**. |
| | **Total** | **100** | | | | | |

**Cap reconciliation:**
- Area 2: Blocker present (I-002/I-003/I-004/I-005) → cap at 40% → 10/25
- Area 3: Blocker present (I-001) → cap at 40% → 10/25
- Area 5: Unresolved cross-source conflict affecting expected behavior → cap at 8/15

**Final total: 14 + 10 + 10 + 9 + 8 = 51 / 100**

---

## §D. Final Score & Verdict

| | |
|---|---|
| **Total score** | **51 / 100** |
| **Verdict** | **Not Ready** |
| **Reason** | Total < 70 (Not Ready threshold). 5 Blocker issues unresolved (I-001 through I-005). Auto-fail: blockers in all critical areas (Areas 2 and 3). |

**Blocker summary:**
- **I-001** — `stop_replacing_started_at` overrun detection path missing from UC §3/§4
- **I-002** — `hlMarkPrice` source for stop trigger evaluation incompatible with BR-EXBOT-003 (0 HL weight) — source mechanism unspecified
- **I-003** — `range_boundary_near` formula: OQ-EXBOT-10 unresolved (tick vs price distance)
- **I-004** — `drift_threshold` formula: OQ-EXBOT-11 unresolved (`lpValueUsd` computation unknown)
- **I-005** — `funding_alert` formula: OQ-EXBOT-12 unresolved (7d APR annualization formula unknown)

**Major issue summary:**
- **I-006** — `half_open` atomic claim mechanism unspecified
- **I-007** — MarketDataDO stale cache worker behavior undefined
- **I-008** — Which RebalanceReasons are evaluated by light-check vs other workers unclear
- **I-009** — `stateVersion` field source for hedge-sync message not mapped

---
