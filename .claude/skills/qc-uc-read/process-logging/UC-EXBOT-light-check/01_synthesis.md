# Phase 1 Synthesis — UC-EXBOT-light-check

## Working notes
- UC-ID: UC-EXBOT-light-check / Name: Execute Periodic Light-Check
- Input language: English
- Source files: uc-light-check.md (2026-06-12), us-005.md, us-006.md, frd.md (FR-EXBOT-011/012/013/014/015/016/023/032/033), spec.md (FR-EXBOT-012/013/014/015/016/023/032/033/093 + BR table + OQ table)
- Blocked/missing artefacts: No design/prototype/ASCII screen (LOGIC-only backend UC — expected). No HTML prototype. No image designs.
- Generated at 2026-06-17T17:10:00+07:00 by qc-uc-read · first-audit · Phase 1

---

## §A. Project & site-map context

### A.1 Project context (scoped to this UC)
- **Platform:** PTL-04 BNZA-EXBOT — Cloudflare Workers-only backend. No UI. Tested through API and DB state.
- **Feature scope:** Line 2 (EXBOT Infra) — the only active QC scope.
- **Domain:** Delta-hedged LP bot system. ExBot Worker runs on CF Workers; communicates with OPERATOR via CF service binding. D1 (SQLite) is the state store. Queue topology: 10 queues, all via `chunkSendBatch()`.
- **Key constraint:** HL rate limit = 1,200 weight/min; BNZA budget = 800 weight/min. Light-check MUST consume 0 HL weight.
- **Scale target:** 10,000 active bots in a 5-minute window.
- **OQ-EXBOT-10/11/12:** Three open questions from BA that directly affect light-check evaluation logic — all unconfirmed by zen.

### A.2 Site-map context
- No `qc-site-map.md` entries for PTL-04 backend UCs (site-map covers UI screens only).
- light-check is triggered by: Cron Worker (1 min) → `bot-scan` queue → Scan Worker → `light-check` queue → Light-Check Worker.
- Downstream: Light-Check Worker may enqueue `hedge-sync` or `price-near-stop-audit`.

---

## §B. UC identity & raw reference list

- UC ID: UC-EXBOT-light-check
- UC name: Execute Periodic Light-Check
- Input language: English
- Source UC file: `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-light-check.md`
- Related feature/module: PTL-04 EXBOT, FM-XB-02 (Queue Topology), FM-XB-07 (Lifecycle State Machine)
- Linked user stories: US-EXBOT-005, US-EXBOT-006
- Referenced FRs: FR-EXBOT-013, 014, 015, 016, 023, 032 (UC §7); FR-EXBOT-011/012 (frd.md — light-check core); FR-EXBOT-033 (frd.md — stop_replacing detection)
- Referenced BRs: BR-EXBOT-003 (HL weight = 0), BR-EXBOT-005 (stop_trigger_crossed_at write-once)
- Referenced OQs: OQ-EXBOT-10 (range_boundary_near formula), OQ-EXBOT-11 (lpValueUsd formula), OQ-EXBOT-12 (7d APR formula)
- Referenced DOs: MarketDataDO (sqrtPriceX96 cache)
- Referenced tables: `bots`, `bot_runtime_state`, `hedge_legs`, `queue_idempotency`, `circuit_breakers`
- No design artefacts (backend-only UC)

---

## §C. Resolved common rules & messages (Sub-agent A)

| UC mention | Common file | Section | Verbatim content |
|---|---|---|---|
| BR-EXBOT-003 | spec.md BR table (line 550) | §BR | "Light-check HL weight = 0. Any HL API call introduced into light-check is an architectural violation." |
| BR-EXBOT-005 | spec.md BR table (line 552) | §BR | "`stop_trigger_crossed_at` is write-once per stop event (guarded: only set if currently NULL). This prevents the 30-min SAFE_MODE detection from being defeated by repeated light-check overwrites." |
| FR-EXBOT-013 (spec) | spec.md line 163 | §FR-EXBOT-013 | "`next_light_check_at` shall be set to `now + 5min + random(−45s, +45s)`. The jitter is computed per-bot as a value, but the D1 write is batched (1 UPDATE statement per shard, not a per-bot individual write)." |
| FR-EXBOT-014 (spec) | spec.md line 173 | §FR-EXBOT-014 | "Stop monitoring (`price-near-stop-audit` enqueue) shall continue at all times — including when `circuit_breakers.state='open'`. Light-check shall suppress `hedge-sync` when circuit is open, but shall never suppress stop price evaluation or `price-near-stop-audit` enqueue." |
| FR-EXBOT-015 (spec) | spec.md line 183 | §FR-EXBOT-015 | "When light-check detects `rangeState != 'in'` (range_out condition), the system shall transition `bots.lifecycle_state` to `lp_rebalancing` and enqueue an LP rebalance operation via the `partial_repair` queue." |
| FR-EXBOT-016 (spec) | spec.md line 193 | §FR-EXBOT-016 | "The system shall run a full HL state reconcile for every active and paused bot every 6 hours via the `deep-audit` queue. In high-risk mode...the interval reduces to 1 hour." |
| FR-EXBOT-023 (spec) | spec.md line 233 | §FR-EXBOT-023 | "Rebalance triggers shall use only the canonical `RebalanceReason[]` enum values: `drift_threshold`, `drift_relative`, `range_out`, `range_boundary_near`, `margin_warning`, `funding_alert`, `time_fallback`, `manual_admin`, `recovery_reconcile`. No aliases or alternate naming are permitted. `stop_trigger_crossed` is not a `RebalanceReason`; it routes to `price-near-stop-audit`." |
| FR-EXBOT-032 (spec) | spec.md line 303 | §FR-EXBOT-032 | "When light-check detects `markPrice >= stop_price`, the worker shall set `hedge_legs.stop_trigger_crossed_at` only if it is currently NULL (guarded write). It shall enqueue a `price-near-stop-audit` message. It shall NOT enqueue a `hedge-sync` message for this trigger." |
| FR-EXBOT-011 (frd) | frd.md line 149 | §FR-EXBOT-011 | Light-Check core logic: RebalanceReason[] evaluation, 3-way price source split, skip conditions. (See §F.3 for full synthesis) |
| FR-EXBOT-012 (frd) | frd.md line 182 | §FR-EXBOT-012 | "`next_light_check_at = now + 5min + random(−45s, +45s)`. Prevents bot clustering." — NOTE: In spec.md this is FR-EXBOT-013. frd/spec numbering diverges. |
| OQ-EXBOT-10 | spec.md line 638 | §OQ | "`range_boundary_near` exact computation: is '90% to upper/lower' measured in tick distance or price distance?... Owner: zen/SOTATEK to confirm." |
| OQ-EXBOT-11 | spec.md line 639 | §OQ | "`lpValueUsd` formula: how is `bot_runtime_state.lp_value_usd` computed and updated?... Blocks FR-EXBOT-012 `drift_threshold` (lpValueUsd × 3% term)." |
| OQ-EXBOT-12 | spec.md line 640 | §OQ | "7d funding APR aggregation formula... exact annualization formula not specified. Owner: zen to confirm." |

---

## §D. HTML prototype UI evidence
Not applicable — no HTML prototype provided. UC is a backend logic UC (no UI).

## §E. Image design UI evidence
Not applicable — no image design provided. UC is a backend logic UC (no UI).

## §E2. ASCII screen UI evidence
Not applicable — no ASCII screen provided. UC is a backend logic UC (no UI).

---

## §F.1 Function/Operation Inventory & Source Mapping

> **Note:** This is a LOGIC-only UC. §F.1 replaces UI element inventory with function/operation/state-object inventory per the backend-UC variant.

| # | Function / Operation | Type | Source | Notes |
|---|---|---|---|---|
| F1-01 | Cron Worker fires every 1 min, calls `chunkSendBatch` to `bot-scan` queue | Trigger | UC §3 Step 1; spec FR-EXBOT-012 AC | Entry point of entire light-check chain |
| F1-02 | Scan Worker queries D1: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now LIMIT 500` | Query | UC §3 Step 2 | Per-shard batch read |
| F1-03 | Scan Worker sends per-bot messages to `light-check` queue via `chunkSendBatch` | Queue produce | UC §3 Step 3; spec FR-EXBOT-012 | Fan-out to Light-Check Workers |
| F1-04 | Scan Worker batch-updates `next_light_check_at = now + 5min + jitter(±45s)` (1 stmt per shard) | D1 write | UC §3 Step 4; frd FR-EXBOT-012; spec FR-EXBOT-013 | MUST be batch (1 stmt/shard), not per-bot write |
| F1-05 | Light-Check Worker inserts `message_id` into `queue_idempotency` (state='started'); UNIQUE conflict → skip | Idempotency guard | UC §3 Step 5; spec FR-EXBOT-007 | De-dup on redelivery |
| F1-06 | Light-Check Worker reads D1: `bot_runtime_state`, `hedge_legs` (stop_price, margin_status, circuit_state), `lifecycle_state` | D1 read | UC §3 Step 6 | Zero HL API calls |
| F1-07 | Light-Check Worker reads MarketDataDO: `sqrtPriceX96`, `currentTick` | DO read | UC §3 Step 7; spec FR-EXBOT-093 | Shared cache — 0 RPC per worker |
| F1-08 | Compute `lpEthAmount` via TickMath + LiquidityAmounts (local, no RPC) | Computation | UC §3 Step 8; frd FR-EXBOT-011 | MUST use `liquidity`, `sqrtPriceX96`, `currentTick`; AMM formula forbidden to replace with deposit-based approx |
| F1-09 | Evaluate `RebalanceReason[]` using D1 + MarketDataDO state | Evaluation | UC §3 Step 9; frd FR-EXBOT-011; spec FR-EXBOT-023 | 7 canonical reasons: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback |
| F1-10 | If reasons found AND circuit != open: enqueue `hedge-sync` with {botId, reasons, stateVersion} | Queue produce | UC §3 Step 10; spec FR-EXBOT-012/014 | circuit=half_open: allow 1 probe (atomic claim) |
| F1-11 | If `markPrice >= stop_price`: set `stop_trigger_crossed_at` (guarded write — NULL only); enqueue `price-near-stop-audit` | State write + Queue produce | UC §3 Step 11; spec FR-EXBOT-032; BR-EXBOT-005 | NEVER also enqueue hedge-sync for this trigger |
| F1-12 | Update `queue_idempotency.state='succeeded'` | D1 write | UC §3 Step 12 | Terminal idempotency update |
| F1-13 | If `stop_replacing_started_at IS NOT NULL AND age > 60s`: enqueue `partial_repair` + trigger SAFE_MODE | Safety check | frd FR-EXBOT-011 (extra pass); spec FR-EXBOT-033 | **MISSING from UC §3 main flow** — only in frd |
| F1-14 | Skip light-check entirely for `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'` | Guard | UC §2 Preconditions; frd FR-EXBOT-011 | |
| F1-15 | Alternate A2: circuit half_open — atomically claim `half_open_probe_used`; enqueue one probe hedge-sync | Atomic claim | UC §4 A2; spec FR-EXBOT-028 AC | atomic 0→1 claim required |

**Key data objects:**
| Object | Fields accessed | Source |
|---|---|---|
| `bots` | `status`, `lifecycle_state`, `next_light_check_at` | UC §3 Steps 2,4,6 |
| `bot_runtime_state` | `last_known_hl_short_size`, `lifecycle_state` | UC §3 Step 6 |
| `hedge_legs` | `stop_price`, `margin_status`, `stop_trigger_crossed_at`, `stop_replacing_started_at` | UC §3 Step 6; frd FR-EXBOT-011 |
| `circuit_breakers` | `state` (`closed`/`open`/`half_open`), `half_open_probe_used` | UC §3 Step 10; §4 A1/A2 |
| `queue_idempotency` | `message_id`, `state` | UC §3 Steps 5,12 |
| `MarketDataDO` | `sqrtPriceX96`, `currentTick` | UC §3 Step 7 |

---

## §F.2 Object Attributes, Behavior, Rules & Validations

| # | Object / State | Rule / Behavior | Source | Issues |
|---|---|---|---|---|
| F2-01 | `circuit_breakers.state='open'` | SUPPRESS hedge-sync enqueue; CONTINUE stop monitoring | UC §4 A1; spec FR-EXBOT-014 | Clear |
| F2-02 | `circuit_breakers.state='half_open'` | Allow EXACTLY ONE probe hedge-sync via atomic `half_open_probe_used` 0→1 claim | UC §4 A2; spec FR-EXBOT-028 | ⚠️ UC says "atomically claim" but does NOT specify the atomic mechanism (DB transaction? DO? CAS?) |
| F2-03 | `stop_trigger_crossed_at` | Write-once per event — set ONLY if currently NULL (guarded) | UC §4 A3; BR-EXBOT-005 | Clear |
| F2-04 | `range_boundary_near` | Price 90% to range upper/lower | frd FR-EXBOT-011; UC §4 A4 | ⚠️ OQ-EXBOT-10: tick distance vs price distance — formula NOT confirmed by zen |
| F2-05 | `drift_threshold` | `deltaErrorUsd > max($25, lpValueUsd × 3%)` where `deltaErrorUsd = |targetShortEth − actualShortEth| × uniPoolPrice` | frd FR-EXBOT-011 | ⚠️ OQ-EXBOT-11: `lpValueUsd` formula undefined — blocks this threshold |
| F2-06 | `funding_alert` | 7d funding APR < −15% | frd FR-EXBOT-011 | ⚠️ OQ-EXBOT-12: exact APR aggregation formula undefined |
| F2-07 | Price source 3-way split | `uniPoolPrice` → drift; `hlMarkPrice` → stop trigger; `hlOraclePrice` → margin. MUST NOT interchange. | frd FR-EXBOT-011; spec FR-EXBOT-012 AC | ⚠️ UC §3 Step 7 only mentions `sqrtPriceX96, currentTick` from MarketDataDO — does NOT explicitly state hlMarkPrice source for stop trigger detection. How does light-check get hlMarkPrice without an HL API call? |
| F2-08 | `RebalanceReason[]` enum | Exactly 9 canonical values; no aliases; `stop_trigger_crossed` NOT a reason | spec FR-EXBOT-023 | Clear |
| F2-09 | `next_light_check_at` batch write | 1 D1 UPDATE statement per shard (not per-bot) | frd FR-EXBOT-012; spec FR-EXBOT-013 | Clear |
| F2-10 | `stop_replacing_started_at` overrun | If IS NOT NULL AND age > 60s → enqueue `partial_repair` + SAFE_MODE | frd FR-EXBOT-011; spec FR-EXBOT-033 | ⚠️ Completely absent from UC §3 main flow (only in frd/spec) |
| F2-11 | `queue_idempotency` UNIQUE conflict | Return immediately on duplicate delivery without processing | UC §3 Step 5; spec FR-EXBOT-007 | Clear |
| F2-12 | `lpEthAmount` computation | MUST use TickMath + LiquidityAmounts with `liquidity`, `sqrtPriceX96`, `currentTick`. Forbidden: `depositedToken − withdrawnToken + collectedFees` approximation. | spec FR-EXBOT-017 AC | Clear |

---

## §F.3 Functional Logic & Workflow Decomposition

### Main Flow (Happy Path — no rebalance needed)
1. Cron (1 min) → chunkSendBatch → `bot-scan` queue
2. Scan Worker: SELECT active bots WHERE `next_light_check_at <= now` (LIMIT 500/shard)
3. Scan Worker: chunkSendBatch → `light-check` queue (one msg/bot)
4. Scan Worker: batch-UPDATE `next_light_check_at = now + 5min + jitter(±45s)` (1 stmt/shard)
5. Light-Check Worker: INSERT `queue_idempotency` (message_id, state='started') — UNIQUE guard
6. Light-Check Worker: READ D1 (bot_runtime_state, hedge_legs, circuit_breakers)
7. Light-Check Worker: READ MarketDataDO (sqrtPriceX96, currentTick)
8. Light-Check Worker: COMPUTE lpEthAmount via TickMath + LiquidityAmounts
9. Light-Check Worker: EVALUATE RebalanceReason[] — result: empty array
10. Step 10: circuit check → no hedge-sync needed
11. Step 11: markPrice < stop_price → no price-near-stop-audit
12. UPDATE queue_idempotency.state='succeeded'
→ No queue messages produced

### Alternate Flows
**A1 — circuit open:** Step 10 → suppress hedge-sync. Steps 11-12 continue normally.
**A2 — circuit half_open:** Step 10 → atomically claim `half_open_probe_used` 0→1; if claim succeeds, enqueue ONE probe hedge-sync. Mechanism for atomic claim not specified.
**A3 — stop trigger crossed_at already set:** Step 11 → guard prevents overwrite. price-near-stop-audit still enqueued.
**A4 — range_boundary_near 90%:** Step 9 → reason added; Step 10 → hedge-sync enqueued with reason.

### Exception / Error Flows
**E1 — Duplicate message delivery:** Step 5 UNIQUE conflict → return immediately (idempotency).
**E2 — Bot in lp_rebalancing or lp_closing:** UC §2 precondition → skip entire light-check.
**E3 — status='paused':** UC §2 precondition → skip entire light-check.
**E4 — stop_replacing_started_at overrun (>60s):** frd FR-EXBOT-011 → enqueue partial_repair + SAFE_MODE. **Not in UC main flow.**
**E5 — MarketDataDO cache stale (>2× refresh interval):** spec FR-EXBOT-093 → DO logs warning, forces refresh. UC does not define worker behavior on stale cache read.

### Business Rules synthesized
| Rule | Verbatim | Source |
|---|---|---|
| BR-EXBOT-003 | "Light-check HL weight = 0. Any HL API call is an architectural violation." | spec.md BR table |
| BR-EXBOT-005 | "`stop_trigger_crossed_at` write-once per stop event." | spec.md BR table |
| FR-EXBOT-023 | Only 9 canonical RebalanceReason values; `stop_trigger_crossed` NOT a reason. | spec.md |

---

## §F.4 Functional Integration & Data Consistency

| Trigger | Downstream Effect | Consistency concern |
|---|---|---|
| Cron → bot-scan → light-check queue | Per-bot light-check workers are fan-out via queue | `chunkSendBatch` enforces max 100/batch (spec FR-EXBOT-010). Direct `sendBatch` forbidden. |
| Light-check → hedge-sync enqueued | hedge-sync worker acquires UserLockDO, executes delta adjustment | `stateVersion` in queue message must match D1 at consumption time — stale messages discarded (spec FR-EXBOT-025 AC) |
| Light-check → price-near-stop-audit enqueued | Stop-audit worker monitors stop trigger resolution | `stop_trigger_crossed_at` set once by light-check; SAFE_MODE if stuck > 30 min (deep-audit backstop) |
| Light-check → partial_repair enqueued (stop_replacing overrun) | Repair worker handles stop replacement failure + SAFE_MODE entry | **Gap: UC §3 main flow does not include this path.** Only in frd FR-EXBOT-011. |
| light-check + deep-audit for stop_replacing_started_at detection | Primary: light-check ≤5 min; Secondary: deep-audit 6h/1h backstop | Both systems must detect same condition; duplication is intentional (safety net) |
| MarketDataDO cache | All light-check workers share one DO instance per CF region — 0 RPC per worker | Cache TTL not yet defined (OQ-EXBOT-09 / NV-12). If TTL is too large, stale pool price → wrong drift/stop evaluation. |
| D1 write on next_light_check_at | Batch per shard, not per bot | NFR-EXBOT-005: no unconditional per-bot UPDATE permitted. `bot_runtime_state` written on change only. |

---

## §F.5 Acceptance Criteria Candidates for User Confirmation

| # | AC Candidate | Type | Trace | Source status | Confirmation |
|---|---|---|---|---|---|
| AC-01 | A 10,000-bot light-check cycle consumes 0 HL API rate limit weight | Functional/NFR | §F.3 main flow, BR-EXBOT-003, spec FR-EXBOT-012 AC | Verbatim from spec | Confirmed in spec |
| AC-02 | `deltaErrorUsd` computation uses `uniPoolPrice` (pool slot0), NOT hlMarkPrice or hlOraclePrice | Functional | §F.2 F2-07, frd FR-EXBOT-011 3-way split | Verbatim from frd | Confirmed in frd/spec |
| AC-03 | `stop_trigger_crossed_at` is set exactly once per stop event regardless of how many subsequent light-checks run | Functional | §F.2 F2-03, BR-EXBOT-005, spec FR-EXBOT-032 AC | Verbatim from spec | Confirmed in spec |
| AC-04 | Bot in `lp_rebalancing` or `status='paused'` produces no queue messages from light-check | Functional | §F.3 E2/E3, UC §2, frd FR-EXBOT-011 | Verbatim from UC | Confirmed in UC |
| AC-05 | Duplicate queue message delivery exits after UNIQUE constraint conflict (no double processing) | Functional | §F.2 F2-11, UC §3 Step 5, spec FR-EXBOT-007 | Verbatim from UC/spec | Confirmed |
| AC-06 | `next_light_check_at` updated via 1 D1 batch statement per shard, not per-bot individual write | NFR | §F.1 F1-04, NFR-EXBOT-005, frd FR-EXBOT-012 | Verbatim from spec | Confirmed |
| AC-07 | A bot with circuit='open' still receives `price-near-stop-audit` if stop criteria met | Functional | §F.3 A1, UC §4 A1, spec FR-EXBOT-014 | Verbatim from UC/spec | Confirmed |
| AC-08 | With circuit='half_open', exactly one probe hedge-sync is enqueued (atomic claim) | Functional | §F.3 A2, UC §4 A2, spec FR-EXBOT-028 AC | Verbatim from UC | ⚠️ Atomic mechanism not specified — needs BA confirmation |
| AC-09 | If `stop_replacing_started_at` is set and age > 60s, a `partial_repair` message is enqueued and SAFE_MODE entered within next light-check cycle | Functional | §F.2 F2-10, frd FR-EXBOT-011/033 | In frd/spec, NOT in UC §3 | ⚠️ Needs BA to add to UC main flow |
| AC-10 | `range_boundary_near` evaluation uses confirmed formula (tick-based or price-based) | Functional | §F.2 F2-04, OQ-EXBOT-10 | OQ open — formula undefined | ⚠️ Blocked: OQ-EXBOT-10 unresolved |
| AC-11 | `drift_threshold` evaluation uses confirmed `lpValueUsd` formula | Functional | §F.2 F2-05, OQ-EXBOT-11 | OQ open — formula undefined | ⚠️ Blocked: OQ-EXBOT-11 unresolved |
| AC-12 | `funding_alert` evaluation uses confirmed 7d APR formula | Functional | §F.2 F2-06, OQ-EXBOT-12 | OQ open — formula undefined | ⚠️ Blocked: OQ-EXBOT-12 unresolved |
| AC-13 | hlMarkPrice used for stop trigger detection is sourced without an HL API call (source mechanism confirmed) | Functional | §F.2 F2-07 — gap | UC/frd/spec conflict — how hlMarkPrice reaches light-check without HL call is undefined | ⚠️ Needs BA clarification |

---
