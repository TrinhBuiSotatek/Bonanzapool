# Test Case Update Impact Report — UC-EXBOT-hedge-sync

**Status:** Waiting for user approval
**Report revision:** R1
**Trigger type:** REQUIREMENT_DELTA
**Track in scope:** logic
**Audited source (old):** UC-EXBOT-hedge-sync_hedge-sync_audited_20260715_v4.md (87/100, Conditionally Ready)
**Audited source (new):** UC-EXBOT-hedge-sync_hedge-sync_audited_20260724_v5.md (94/100, READY)
**Current TC source:** UC-EXBOT-hedge-sync_hedge-sync_testcases_draft_v5.md (68 TCs)
**User feedback source:** none

#### Summary

| Item | Count |
|---|---:|
| Requirements added | 3 |
| Requirements modified | 1 |
| Requirements removed | 0 |
| Requirements clarified | 1 |
| Requirements still ambiguous / need confirmation | 0 |
| Existing TCs kept | 66 |
| Existing TCs to update | 2 |
| New TCs proposed | 8 |
| TCs proposed to retire | 0 |
| TCs proposed to split | 0 |
| TCs proposed to merge | 0 |
| Items needing user review / confirmation | 0 |

---

#### Requirement Delta

| Change ID | Change type | Old meaning | New meaning | Source | Expected TC impact |
|---|---|---|---|---|---|
| RD-05-01 | MODIFIED | AC-11 (old): delta=0 — no HL order, but Worker proceeds to stop replacement (INV-STOP runs even when delta=0) | AC-12 (v5): delta=0 (abs < 0.000001) → return `{status: 'no_op_dust'}` immediately — no HL order, no reconcile, no stop replacement, `entry_price`/`liq_price`/`stop_trigger_px` all unchanged; `queue_idempotency.state='succeeded'`. Source confirmed from `rebalance.ts` line 83–84 (OQ-EXBOT-013 Closed) | Audit v5 §1.A; UC A6 updated; AC-12 | TC_015 UPDATE (remove stop-replacement reference; update expected result to no_op_dust with no downstream); ADD 3 new BVA TCs (TS_006/007/008) |
| RD-05-02 | ADDED | Q2 open: INV-STOP place-before-cancel unconfirmed; TC_032 had note "(Note: exact sequence … pending OQ-EXBOT-002)" | AC-10: INV-STOP = place-before-cancel confirmed (OQ-EXBOT-002 Closed). Sequence: (1) Place new stop → (2) verifyStopPlaced → (3) Cancel old stop. No 0-stop window. Failure path (AC-11): place fails → old stop remains active → partial_repair enqueued; no SAFE_MODE entry at this step | Audit v5 §1.B; FR-EXBOT-035 updated; OQ-EXBOT-002 Closed | TC_032 UPDATE (remove "pending" note; add confirmed sequence); ADD TC_072 (INV-STOP happy path) + TC_073 (INV-STOP place failure) |
| RD-05-03 | ADDED | Q6 open: drift_threshold formula and lpValueUsd definition unknown; no BVA TCs possible | AC-15: `drift_threshold = max($25, lpValueUsd × 3%)`, `lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount` (principal only; exclude `tokensOwed`; price = Uniswap pool slot0). Formula confirmed (OQ-EXBOT-011 Closed) | Audit v5 §1.B; spec.md FR-EXBOT-025 AC; OQ-EXBOT-011 Closed | ADD TC_074 (BVA at max($25, 3%) boundary), TC_075 ($25 floor when 3% < $25), TC_076 (lpValueUsd excludes tokensOwed) |
| RD-05-04 | CLARIFIED | AC numbering in v5 TC RTM used AC-11 for "delta=0 no HL proceed to stop replacement" which no longer matches v5 audit AC-11 (now INV-STOP place failure) | AC-11 in audit v5 = INV-STOP place failure (new AC). AC-12 = no_op_dust. RTM must be updated to align | Audit v5 §8 Acceptance Criteria re-numbering | RTM UPDATE — no TC body change needed for this item alone; covered by RD-05-01 and RD-05-02 TC updates |

---

#### User Feedback Interpretation

*No user feedback for this run.*

---

#### Test Case Impact Matrix

| TC ID | Current title | Impact Status | Reason | Proposed action |
|---|---|---|---|---|
| TC_001 | Verify a new hedge-sync message is accepted when its message_id has not been seen before | KEEP | No change in idempotency behavior | Preserve as-is |
| TC_002 | Verify delivering the same hedge-sync message twice causes the second delivery to exit immediately | KEEP | No change | Preserve as-is |
| TC_003 | Verify the worker proceeds when the message stateVersion matches the current bot state | KEEP | No change | Preserve as-is |
| TC_004 | Verify a stale hedge-sync message is discarded immediately at step 2a | KEEP | No change | Preserve as-is |
| TC_005 | Verify the worker acquires the user lock and proceeds when the lock is free | KEEP | No change | Preserve as-is |
| TC_006 | Verify the worker re-queues with a delay and takes no action when the lock is held | KEEP | No change | Preserve as-is |
| TC_007 | Verify a size-increase delta adjustment is blocked when margin is warning | KEEP | No change | Preserve as-is |
| TC_008 | Verify both increase and reduce adjustments are allowed when margin is OK | KEEP | No change | Preserve as-is |
| TC_009 | Verify two concurrent deliveries result in exactly one execution | KEEP | No change | Preserve as-is |
| TC_010 | Verify the exact stateVersion boundary | KEEP | No change | Preserve as-is |
| TC_011 | Verify User Lock lease auto-releases if worker holds past TTL | KEEP | No change | Preserve as-is |
| TC_012 | Verify User Lock returns cached result for same idempotency key | KEEP | No change | Preserve as-is |
| TC_013 | Verify hedge-sync only sends the difference when short position needs to increase | KEEP | No change | Preserve as-is |
| TC_014 | Verify hedge-sync sends reduce-only adjustment when position needs to decrease | KEEP | No change | Preserve as-is |
| TC_015 | Verify no HL order is placed when the computed delta is zero — reason equals original payload value | **UPDATE** | Old expected result: "Worker proceeds to stop replacement step (INV-STOP protocol)" — this contradicts v5 AC-12 (no_op_dust; no stop replacement). Expected result must change to: no HL call, no reconcile enqueued, no INV-STOP stop replacement, `entry_price`/`liq_price`/`stop_trigger_px` unchanged; Worker returns `{status: 'no_op_dust'}` | Update expected result; remove stop replacement reference; add reference to AC-12 and OQ-EXBOT-013 Closed |
| TC_016 | Verify target ratio normalizer converts decimal string to correct BigInt | KEEP | No change | Preserve as-is |
| TC_017 | Verify delta calculation uses BigDecimal throughout | KEEP | No change | Preserve as-is |
| TC_018 | Verify order id for same attempt is always the same | KEEP | No change | Preserve as-is |
| TC_019 | Verify HL order rejection increments circuit breaker failure count | KEEP | No change | Preserve as-is |
| TC_020 | Verify delta computed and order placed correctly at exact drift threshold boundary | KEEP | No change — still valid for non-zero delta | Preserve as-is |
| TC_021 | Verify worker checks HL rate limiter before calling Hyperliquid | KEEP | No change | Preserve as-is |
| TC_022 | Verify bot enters safe mode when HL unreachable | KEEP | No change | Preserve as-is |
| TC_023 | Verify bot enters safe mode when signing service fails | KEEP | No change | Preserve as-is |
| TC_024 | Verify duplicate cloid is detected and reconciled before retry | KEEP | No change | Preserve as-is |
| TC_025 | Verify stop trigger price computed with full BigDecimal precision | KEEP | No change | Preserve as-is |
| TC_026 | Verify hedge-sync does not open more than six outbound connections | KEEP | No change | Preserve as-is |
| TC_027 | Verify stop_replacing_started_at is set before critical section begins | KEEP | No change (still correct — only applies when delta ≠ 0) | Preserve as-is |
| TC_028 | Verify stop_replacing_started_at is cleared after stop replacement succeeds | KEEP | No change | Preserve as-is |
| TC_029 | Verify stop_replacing_started_at is cleared even when stop replacement fails midway | KEEP | No change | Preserve as-is |
| TC_030 | Verify new stop placed with correct trigger price and as reduce-only | KEEP | No change | Preserve as-is |
| TC_031 | Verify bot enters safe mode when stop_replacing_started_at is stuck | KEEP | No change | Preserve as-is |
| TC_032 | Verify stop replacement always uses INV-STOP protocol and not direct cancel-then-place | **UPDATE** | Current note says "(Note: exact sequence — place-before-cancel or cancel-before-place — pending OQ-EXBOT-002.)" — this is superseded by v5 confirmation. Must remove "pending" note and add confirmed sequence: place → verifyStopPlaced → cancel. Also add reference to OQ-EXBOT-002 Closed and AC-10 | Update Notes/Expected Result to remove pending caveat; document confirmed place-before-cancel with verifyStopPlaced; cite AC-10 and OQ-EXBOT-002 Closed |
| TC_033 | Verify new stop trigger price recomputed from latest entry and liquidation prices | KEEP | No change | Preserve as-is |
| TC_034 | Verify successful reconcile updates all hedge leg fields | KEEP | No change | Preserve as-is |
| TC_035 | Verify attempt only marked successful after reconcile confirms | KEEP | No change | Preserve as-is |
| TC_036 | Verify bot's last known HL short size updated to reconciled value | KEEP | No change | Preserve as-is |
| TC_037 | Verify partial fill causes repair message queued, attempt marked partial, circuit unchanged | KEEP | No change | Preserve as-is |
| TC_038 | Verify three consecutive partial repair failures trigger bot safe close | KEEP | No change | Preserve as-is |
| TC_039 | Verify reconcile handles zero actual position without crashing | KEEP | No change | Preserve as-is |
| TC_040 | Verify all hedge leg fields written atomically after reconcile | KEEP | No change | Preserve as-is |
| TC_041 | Verify queue_idempotency state updated to succeeded only after full pipeline | KEEP | No change | Preserve as-is |
| TC_042 | Verify bot state version incremented after successful rebalance | KEEP | No change | Preserve as-is |
| TC_043 | Verify circuit opens after three consecutive HL failures | KEEP | No change | Preserve as-is |
| TC_044 | Verify circuit does not open when failures are not consecutive | KEEP | No change | Preserve as-is |
| TC_045 | Verify stop monitoring continues when circuit is open | KEEP | No change | Preserve as-is |
| TC_046 | Verify circuit transitions to half_open when reset timer expires | KEEP | No change | Preserve as-is |
| TC_047 | Verify successful half_open probe closes circuit | KEEP | No change | Preserve as-is |
| TC_048 | Verify failed half_open probe reopens circuit | KEEP | No change | Preserve as-is |
| TC_049 | Verify second probe attempt while in half_open is blocked atomically | KEEP | No change | Preserve as-is |
| TC_050 | Verify circuit breaker state change visible to light-check immediately | KEEP | No change | Preserve as-is |
| TC_051 | Verify failure count not double-incremented on redelivery | KEEP | No change | Preserve as-is |
| TC_052 | Verify bot enters safe mode when HL unreachable past grace period | KEEP | No change | Preserve as-is |
| TC_053 | Verify bot enters safe mode when reconcile detects unexplained size mismatch | KEEP | No change | Preserve as-is |
| TC_054 | Verify bot enters safe mode after two consecutive critical margin readings | KEEP | No change | Preserve as-is |
| TC_055 | Verify all mutations blocked when bot in safe mode | KEEP | No change | Preserve as-is |
| TC_056 | Verify bot exits safe mode automatically when recovery conditions met | KEEP | No change | Preserve as-is |
| TC_057 | Verify safe mode is never a dead end | KEEP | No change | Preserve as-is |
| TC_058 | Verify worker discards hedge-sync when circuit open at execution time | KEEP | No change | Preserve as-is |
| TC_059 | Verify partial fill does NOT increment circuit breaker failure_count | KEEP | No change | Preserve as-is |
| TC_060 | Verify rebalance_attempts.reason equals original payload for stateVersion mismatch | KEEP | No change | Preserve as-is |
| TC_061 | Verify rebalance_attempts.reason equals original payload for delta=0 skip | KEEP | Still valid for delta=0 outcome row — reason field behavior unchanged | Preserve as-is |
| TC_062 | Verify allowHedgeSync returns true only once during half_open | KEEP | No change | Preserve as-is |
| TC_063 | Verify two simultaneous light-check invocations during half_open produce exactly one probe | KEEP | No change | Preserve as-is |
| TC_064 | Verify rebalance_attempts.reason equals original payload for happy-path success | KEEP | No change | Preserve as-is |
| TC_065 | Verify marginSummary fetched AFTER lock; margin_status updated before mutation | KEEP | No change | Preserve as-is |
| TC_066 | Verify extend() called before TTL=90s expiry when HL marginSummary fetch is slow | KEEP | No change | Preserve as-is |
| TC_067 | Verify stateVersion mismatch discards at step 2a without circuit recheck | KEEP | No change | Preserve as-is |
| TC_068 | Verify light-check suppress applies to this tick only | KEEP | No change | Preserve as-is |

---

#### Proposed New Test Cases

| Proposed TC ID | Title | Source of change | TC type | Priority | Note |
|---|---|---|---|---|---|
| TC_069 | Verify delta=0 (no_op_dust) causes Worker to return immediately with no HL call, no reconcile, no stop replacement, and all DB fields unchanged | RD-05-01; AC-12; OQ-EXBOT-013 Closed; TS_006 | Functional | P0 | New operation group needed: place in Section II (delta computation) under II.1. Main no_op_dust positive test |
| TC_070 | BVA: delta exactly 0.000001 ETH (at no_op_dust boundary) — Worker proceeds to adjustShortDelta, not short-circuit | RD-05-01; AC-12; TS_007 | Functional | P0 | Boundary "at": confirms threshold is exclusive (abs < 0.000001 = no_op_dust; abs = 0.000001 → HL order proceeds) |
| TC_071 | BVA: delta 0.0000009 ETH (just below no_op_dust boundary) — Worker returns no_op_dust, does NOT submit HL order | RD-05-01; AC-12; TS_008 | Functional | P0 | Boundary "just below": confirms exclusive `<` semantics of threshold |
| TC_072 | Verify INV-STOP happy path: place-before-cancel sequence with no 0-stop window (verifyStopPlaced between place and cancel) | RD-05-02; AC-10; FR-EXBOT-035; OQ-EXBOT-002 Closed; TS_012 | Functional | P0 | New TC for the confirmed INV-STOP sequence; places in Section III (INV-STOP) under III.1 |
| TC_073 | Verify INV-STOP place failure: new stop cannot be placed on HL — old stop remains active, partial_repair enqueued, Worker does NOT enter SAFE_MODE | RD-05-02; AC-11; FR-EXBOT-035; OQ-EXBOT-002 Closed; TS_013 | Functional | P0 | Failure path for INV-STOP; distinct from stop_replacing_started_at overrun SAFE_MODE (TC_031) |
| TC_074 | BVA: deltaErrorUsd exactly at drift_threshold = max($25, lpValueUsd × 3%) — hedge-sync enqueued when just above, not enqueued when at or below threshold | RD-05-03; AC-15; OQ-EXBOT-011 Closed; TS_024 | Functional | P1 | Tests exclusive boundary of drift trigger in light-check; add to new Section VIII |
| TC_075 | Verify drift_threshold uses $25 floor when lpValueUsd × 3% < $25 — deltaErrorUsd = $25.01 enqueues hedge-sync; $24.99 does not | RD-05-03; AC-15; OQ-EXBOT-011 Closed; TS_025 | Functional | P1 | Tests floor branch of max($25, 3%) formula |
| TC_076 | Verify lpValueUsd formula excludes tokensOwed — only principal (lpEthAmount × uniPoolPrice) + lpUsdcAmount counts toward drift_threshold computation | RD-05-03; AC-15; OQ-EXBOT-011 Closed; TS_026 | Functional | P1 | Tests correct formula operands; ensures tokensOwed_ETH and tokensOwed_USDC are excluded |

---

#### Test Cases Proposed for Retire / Merge

*No TCs proposed for retirement or merge.*

---

#### Open Questions / Items to Confirm

*No open items — all changes are derived from closed requirements (OQ-EXBOT-013, OQ-EXBOT-002, OQ-EXBOT-011 all Closed in v5 audit).*

---

#### Approval Instructions

You can respond in one of the following ways:

- `Approve update report` to apply exactly as described in this report.
- Send additional feedback if the report needs revision before it is applied.
- `Cancel` to stop the workflow; the plan stays in the process-logging folder so you can resume later.
