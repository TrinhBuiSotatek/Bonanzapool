# EXBOT Logic Technical Add-on for Test Case Design (Backend / Bot — No UI)

## Purpose

This file is the project-specific add-on for the **BNZA-EXBOT Infrastructure** module (a standalone Cloudflare Worker that manages a delta-hedged LP Bot on Uniswap V3 + Hyperliquid). It is the backend analogue of the per-platform `*-technical.md` add-ons in the UI skill.

Apply this file **on top of** the 5 logic phases in `common-logic-technical.md`. The common file tells you *how* to structure a logic test case; this file tells you *what* must be covered for EXBOT specifically, with the concrete on-chain + off-chain expected results.

Every section below is a reusable test-design checklist. Each checklist item is an intent to cover, not a finished test case — turn it into one or more concrete cases using the logic-only step style (action + condition -> observable effect) and the writing rules in `rules/testcase-instruction-rules.md`.

## Evidence base (cite these in the TC body)

All EXBOT-specific behavior, numbers, and codes below trace to these source files. Cite the relevant FR / BR / E-code / flow in the `Notes` or expected-result of each TC, exactly as the requirement states it.

| Source file | What it provides |
|---|---|
| `srs/states.md` | Bot lifecycle state machine (18 states), circuit-breaker states, margin-status thresholds, `close_operations` states |
| `srs/flows.md` | F-01 queue fan-out, F-02 hedge-sync, F-03 init, F-04 user_redeem, F-05 bot_safe_close + re-entry |
| `srs/spec.md` | FR-EXBOT-001..093, NFR-EXBOT-001..012, BR-EXBOT-001..010, error codes E-EXBOT-001..013, open questions, integration constraints |
| `srs/erd.md` | D1 tables / columns (`bots`, `hedge_legs`, `circuit_breakers`, `close_operations`, `queue_idempotency`, ...) and key invariants |
| `frd.md` | Feature-map framing (FM-XB-01..08) |

> **Numbers are version-pinned.** All thresholds, SLAs, and intervals below are quoted from SPEC v5.2.6 as captured in the SRS. Several are still pending Phase 0 confirmation (`OQ-EXBOT-06` margin thresholds, `OQ-EXBOT-07` stopSafetyFactor, `OQ-EXBOT-04` minimum delta). When you use a number, cite its FR and add a Note that it must be re-confirmed against the latest SPEC version before execution.

---

## A. Bot Lifecycle State Machine (state-transition coverage)

**Evidence:** `srs/states.md` (state diagram + State Registry), `spec.md` FR-EXBOT-003, FR-EXBOT-007 (FM-XB-07).

States to enumerate (stored in `bots.lifecycle_state`, with coarse `bots.status`):
`idle`, `preflight`, `lp_opening`, `lp_opened`, `hedge_pre_open`, `hedge_post_confirmed`, `stop_placing`, `stop_verified`, `active`, `lp_rebalancing`, `hedge_stopped_cooldown`, `lp_closing`, `closed`, `cooldown`, `parked`, `safe_mode`, `error` (plus the `paused` coarse status that keeps `lifecycle_state` at its pre-pause value).

### A1. Valid transitions — one TC per edge (from `states.md` diagram)

For each edge, the TC asserts the `lifecycle_state` value **before -> after** AND the `bots.status` value, plus the event/condition that caused it:

- `idle -> preflight` (start request + one-bot check passes).
- `preflight -> lp_opening` (all 5 preflight checks pass) and `preflight -> [*]` (any preflight fails -> **no bot record created**; verify `bots`/`bot_registry` has no new row).
- `lp_opening -> lp_opened` (`VaultMinted` event confirmed) and `lp_opening -> error` (LP mint fails).
- `lp_opened -> hedge_pre_open` -> `hedge_post_confirmed` (HL short IOC filled + reconcile) and `hedge_pre_open -> safe_mode` (HL order fails).
- `hedge_post_confirmed -> stop_placing -> stop_verified` (stop placed + confirmed) and `stop_placing -> safe_mode` (stop placement fails).
- `stop_verified -> active` (fully initialized — see FR-EXBOT-003: no step may be skipped).
- `active -> lp_rebalancing -> active` (range_out -> rebalance complete) and `lp_rebalancing -> safe_mode` (rebalance fails).
- `active -> hedge_stopped_cooldown -> active` (stop trigger fired -> re-hedge success after 4h cooldown) and `hedge_stopped_cooldown -> safe_mode` (re-hedge fails).
- `active -> lp_closing -> closed` (user_redeem path) and `lp_closing -> cooldown` (bot_safe_close path).
- `cooldown -> active` (re-entry conditions met) and `cooldown -> parked` (3rd bot_safe_close within 7 days).
- `parked -> active` (re-entry met at 24h interval).
- `active -> safe_mode -> active` (auto-recovery: 3 reconciles + margin ok) and `safe_mode -> cooldown` (irrecoverable -> bot_safe_close).
- `active -> error` (critical bug / LP NFT anomaly) and `error -> [*]` (admin resolution required).

**Expected result pattern for each:** `bots.lifecycle_state` changes from `<X>` to `<Y>` and is persisted atomically to D1 before the next step (FR-EXBOT-003 AC); `bots.status` reflects the State Registry mapping (e.g. `lp_closing -> status=closing`, `safe_mode -> status=safe_mode`). For on-chain-triggering edges (LP mint, hedge open, stop, close), also assert the on-chain effect (see Add-on B sections below).

### A2. Invalid / blocked transitions — representative cases

- An operation requested from a state where the State Registry marks it `skip`/`blocked` is rejected with no side effect. Examples: hedge-sync requested while `lifecycle_state IN ('lp_rebalancing','lp_closing')` -> skipped (FR-EXBOT-012); any mutation requested in `safe_mode` -> rejected (FR-EXBOT-050); a second initialization step requested out of order (e.g. `placeStop` before `hedge_post_confirmed`) -> blocked, bot cannot reach `active` without a confirmed stop (FR-EXBOT-031 AC).
- A `paused` bot: light-check and hedge-sync suppressed, but deep-audit continues every 6h (FR-EXBOT-005); `lifecycle_state` stays at the pre-pause value.

---

## B. Preflight & Initialization — Operation `uc-bot-start` (F-03)

**Evidence:** `flows.md` F-03; `spec.md` FR-EXBOT-001, 002, 003, 020, 030, 031, 061; error codes E-EXBOT-001..006, 009; BR-EXBOT-001.

### B1. One-bot policy (FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001)

- Start with an existing bot whose `status IN ('active','paused','closing','safe_mode','error')` -> rejected with `E-EXBOT-001` ("You already have an active ExBot..."), HTTP 409, **no new bot record** created.
- Start with no existing counted bot -> policy check passes, proceeds to margin preflight.
- Boundary: a bot in `closed` status does NOT count toward the limit -> a new start is allowed (only the 5 statuses above count, per BR-EXBOT-001).

### B2. Preflight checks in sequence (FR-EXBOT-002, FR-EXBOT-061)

Cover the 5 sequential checks; each single failure blocks start with its distinct message and leaves **no partial bot record**:
1. one-bot policy (B1).
2. HL isolated margin balance `>= required margin x 2.0` (`getMarginSummary`). Boundary cases (FR-EXBOT-061 AC): exactly the minimum (no buffer) -> blocked with `E-EXBOT-002`; exactly `2.0x` -> passes. The shortfall `$Z` in the message is accurate to the nearest dollar.
3. HL agent key `approval_status='approved'` AND `expires_at` not reached. `pending` -> `E-EXBOT-003`; expired -> `E-EXBOT-004` (see Add-on M).
4. builder fee (5bps) confirmed on HL -> not approved -> `E-EXBOT-005`.
5. LP mint simulation passes -> fails -> `E-EXBOT-006`.

**Expected result:** the failing check returns its specific `E-EXBOT-00X` message and HTTP code (per spec section 5); the off-chain assertion is that `bots`/`bot_registry` contain no row for this attempt (preflight-fail => no bot created, FR-EXBOT-002 AC).

### B3. Initialization happy path (F-03, fixed sequence)

One end-to-end TC plus per-step TCs asserting the exact sequence `idle -> preflight -> lp_opening -> lp_opened -> hedge_pre_open -> hedge_post_confirmed -> stop_placing -> stop_verified -> active` (no step skipped):
- create bot record (`lifecycle_state=preflight`).
- `vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` -> on-chain `VaultMinted(user, botId, tokenId, liquidity)` emitted; off-chain `positions` row written with `token_id`, `tick_lower/upper`, `weth_index`, `lifecycle_state=lp_opened`.
- `openShortIoc(targetSize, cloid)` then `reconcilePosition` -> off-chain `hedge_legs` row written with `entry_price`, `liquidation_price`, `effective_leverage`, `lifecycle_state=hedge_post_confirmed`.
- `computeStopTriggerPx` (BigDecimal, `safetyFactor=0.70`, FR-EXBOT-030) then `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)` -> off-chain `hedge_legs.stop_cloid`, `stop_price` written, `lifecycle_state=stop_verified -> active`; bot returns `{status: active, botId}`.

**On-chain + off-chain rule:** the `vaultMint`, `openShortIoc`, and `placeReduceOnlyStopMarket` cases each state BOTH the on-chain effect (event / position size / stop order placed) AND the D1 effect (`positions` / `hedge_legs` columns).

---

## C. Queue Fan-Out — Operation `uc-light-check` (F-01)

**Evidence:** `flows.md` F-01; `spec.md` FR-EXBOT-010, 012, 013, 014, 032; BR-EXBOT-003, 005.

- Cron (1 min) -> `bot-scan` queue via `chunkSendBatch` (<=100 msgs/call, FR-EXBOT-010): direct `sendBatch` without the helper is forbidden; batch > 100 is auto-chunked.
- Scan worker selects `bots WHERE status='active' AND next_light_check_at <= now LIMIT 500`, fans out one `light-check` message per bot, and batch-updates `next_light_check_at = now + 5min + random(-45s,+45s)` (FR-EXBOT-013) with **1 UPDATE statement per shard** (no per-bot D1 write — NFR-EXBOT-005).
- Light-check computes rebalance need from D1 `bot_runtime_state` + `MarketDataDO` (`sqrtPriceX96`, `currentTick`) + local TickMath only — **zero HL API calls** (BR-EXBOT-003; FR-EXBOT-012 AC: a 10,000-bot cycle consumes 0 HL weight). A TC must assert HL weight = 0 for the light-check path.
- Three-way price split (FR-EXBOT-012): `uniPoolPrice` (pool slot0) for `deltaErrorUsd`; `hlMarkPrice` only for stop trigger; `hlOraclePrice` only for margin. A case verifies these are not interchanged.
- Fan-out branches:
  - rebalance needed AND circuit NOT open -> enqueue `hedge-sync` `{botId, reasons, stateVersion}`.
  - stop trigger detected (`markPrice >= stop_price`) -> set `hedge_legs.stop_trigger_crossed_at` **only if currently NULL** (guarded write, BR-EXBOT-005 / FR-EXBOT-032) -> enqueue `price-near-stop-audit`; do **NOT** enqueue `hedge-sync` for this trigger.
  - circuit `open` -> suppress `hedge-sync`, but **stop monitoring continues** (FR-EXBOT-014: with circuit open, a bot at `markPrice >= stop_price` still gets a `price-near-stop-audit` message; no `hedge-sync` enqueued).
- Skip rule: light-check skipped entirely for `lifecycle_state IN ('lp_rebalancing','lp_closing')` or `status='paused'` (FR-EXBOT-012).
- Guarded-write idempotency: repeated light-checks before the audit resolves set `stop_trigger_crossed_at` **exactly once** (FR-EXBOT-032 AC).

---

## D. Hedge-Sync Delta Logic — Operation `uc-hedge-sync` (F-02)

**Evidence:** `flows.md` F-02; `spec.md` FR-EXBOT-020, 021, 022, 024, 025, 026, 027, 035; NFR-EXBOT-002, 007, 008; BR-EXBOT-004; ERD `hedge_legs`, `rebalance_attempts`, `bot_runtime_state`.

- StateVersion optimistic-concurrency guard (FR-EXBOT-027): message `stateVersion` < current `bot_runtime_state.state_version` -> **abort/skip**, record `rebalance_attempts.status='skipped'`, **no HL order submitted**.
- `UserLockDO` lease (FR-EXBOT-026, 092): acquire with `holderToken`, `ttl=90s`, `idempotencyKey=hedge-sync:{botId}:{stateVersion}`. If `acquired=false` (lease held by another worker) -> re-queue with delay, do not run the mutation. Work runs in the caller, not the DO. TTL expiry auto-releases; the next worker reconciles before any new mutation. `heartbeat` by the wrong `holderToken` is a no-op. Lease released in `finally`.
- Delta-only adjustment (FR-EXBOT-022, BR-EXBOT-004): `delta = targetShortEth - actualShortEth` (BigDecimal). A drift-triggered sync submits **only** `adjustShortDelta(delta)` via a deterministic `cloid` — **never** full close -> full open. Full close/open allowed only for target size = 0 (close path), emergency reset (admin), or manual reset (Phase B+).
- Target computation (FR-EXBOT-021): `targetShortEth = lpEthAmount x hedgeRatio`; `target_ratio_bps` via `normalizeTargetRatioBps("0.70") -> 7000n`. Assert BigDecimal throughout; `Number(...) * 10000` forbidden (NFR-EXBOT-008).
- Deterministic cloid (FR-EXBOT-024): same `{botId, attemptId, stage, version}` -> same cloid; on duplicate-cloid detection, reconcile actual HL state **before** any retry — never blind resubmit.
- INV-STOP protocol (FR-EXBOT-035): stop resize uses the protected protocol (section 19.5); direct `cancelStop` then `placeStop` is forbidden; `stop_replacing_started_at` set at the start of the critical section and cleared in `finally`.
- Post-order reconcile (FR-EXBOT-025): after the mutation, fetch actual HL position, verify size matches expected, write `hedge_legs` (`entry_price`, `liq_price`, `effective_leverage`, `stop_price`), update `bot_runtime_state.last_known_hl_short_size`, and **only then** insert `rebalance_attempts.status='success'` (never before reconcile). Cover `success` / `failed` / `partial`.
- Latency: one hedge-sync should complete within 30s under normal conditions (NFR-EXBOT-002).
- Idempotency on redelivery (FR-EXBOT-011, NFR-EXBOT-007): re-delivering the same `hedge-sync` message (same `message_id` / same `idempotencyKey`) -> exactly one effect; the second delivery exits immediately on the `queue_idempotency.message_id` UNIQUE conflict.

---

## E. Circuit Breaker — `circuit_breakers.state` (closed / open / half_open)

**Evidence:** `states.md` (circuit diagram + table); `spec.md` FR-EXBOT-040; stop-monitoring invariant via FR-EXBOT-014.

- `closed -> open`: 3 consecutive hedge-sync failures within 24h -> `state='open'`, `reset_at = now + 1h`. Partial and failed-but-not-3-in-a-row results do NOT open.
- `open -> half_open`: when `reset_at` is reached.
- `half_open -> closed`: a single probe hedge-sync succeeds (atomic `half_open_probe_used` 0->1 claim — only one probe allowed).
- `half_open -> open`: probe fails -> re-open with a new `reset_at = now + 1h`.
- Reset to `closed` happens **only** on probe success; partial/failed do not reset.
- Stop-monitoring invariant: in `open` and `half_open`, **stop monitoring is ALWAYS on** (FR-EXBOT-014); only `hedge-sync` is suppressed. A TC asserts that with circuit `open`, a stop-crossing bot still gets `price-near-stop-audit`.

**Expected result:** `circuit_breakers.state` value before -> after, `reset_at` and `half_open_probe_used` column values, plus the suppression/monitoring side effects on the queues.

---

## F. Margin Status & SAFE_MODE

**Evidence:** `states.md` (margin table); `spec.md` FR-EXBOT-050, 060, 061; BR-EXBOT-007; error codes E-EXBOT-007, 008, 011.

### F1. Margin status thresholds (FR-EXBOT-060)

`marginUsage = marginRequiredUsd / marginBalanceUsd`. Thresholds (BVA at the boundaries — cite `OQ-EXBOT-06`, values pending Phase 0):
- `ok` when `< 0.55`; `warning` when `0.55 <= usage < 0.75`; `critical` when `>= 0.75`.
- `warning`: size-increase hedge adjustments disabled + investor alert.
- `critical` (x2 consecutive) -> SAFE_MODE entry + investor **and** admin alert.
- Margin status updated only during hedge-sync preflight (HL `marginSummary`) and deep-audit; **never** during light-check (HL weight stays 0).

### F2. SAFE_MODE entry & behavior (FR-EXBOT-050, BR-EXBOT-007)

- Entry triggers (cover each): HL API unreachable > 5 min (`E-EXBOT-008`); reconcile mismatch (actual != expected, `E-EXBOT-011`); `margin_status='critical'` x2; `effective_leverage > 4.5`; `liquidation_price` within 5% of `hlMarkPrice`; `stop_trigger_crossed_at` stuck > 30 min; `stop_replacing_started_at` stuck > 60s.
- In `safe_mode`: forbidden — cancel stops, open positions, rebalance hedge/LP, change leverage, withdraw margin (each rejected with no side effect). Allowed — read state, retry HL connectivity, alert, light-check (non-HL part), deep-audit when HL recovers.
- Auto-recovery: HL responsive + **3 consecutive reconciles succeed** + `margin_status='ok'` -> `safe_mode -> active`. If recovery impossible -> `bot_safe_close` (BR-EXBOT-007: SAFE_MODE is never terminal). A TC asserts that no SAFE_MODE path is a dead-end.

---

## G. Close Flows — `uc-user-redeem` (F-04) and `uc-bot-safe-close` (F-05)

**Evidence:** `flows.md` F-04, F-05; `states.md` (`close_operations` states); `spec.md` FR-EXBOT-070, 071, 072, 073; NFR-EXBOT-003; BR-EXBOT-006; error codes E-EXBOT-010, 012.

### G1. user_redeem — LP-first (F-04, FR-EXBOT-070)

Sequence with on-chain + off-chain assertions at each step:
- `BnzaExVault.redeem(tokenId)` on-chain -> LP liquidated and **LP-portion USDC returned to the investor in the same transaction** (on-chain guarantee). Off-chain `close_operations` row `kind=user_redeem`, state `lp_closed -> funds_returned`.
- `RedemptionEvent` -> enqueue `user_redeem` (highest priority); SLA **5 min** from detection (NFR-EXBOT-003).
- `closeShortReduceOnlyIoc` (full close, cloid) -> `cancelStop` (replaceStopProtected size=0) -> `reconcilePosition` verify **size=0** -> `close_operations.state=hedge_closed`.
- send HL-portion USDC to user (RedemptionQueue ledger) -> `state=done`, `lifecycle_state=closed`.
- **Failure branch (BR-EXBOT-006):** if hedge close fails -> `close_operations.state=residual_hl_liability`; enqueue admin notification with outstanding amount; **LP-portion repayment is NOT reverted** (a TC must assert the LP USDC stays with the user regardless of hedge outcome). SLA breach -> `E-EXBOT-010` admin escalation, "LP funds already returned".
- Close on an already-closed bot -> `E-EXBOT-012` (HTTP 409), no action.

### G2. bot_safe_close — hedge-first (F-05, FR-EXBOT-072, 073)

- Trigger conditions (FR-EXBOT-072 — one TC each, each creating exactly one `close_operations` row, `idempotency_key UNIQUE`, `trigger_reason` populated): (1) circuit exhausted (`open` + `reset_at` extended >=3x without probe success); (2) margin `critical` x2 -> SAFE_MODE with no recovery; (3) 3rd `hedge_stopped_cooldown` within 7 days; (4) partial_repair fails 3 consecutive attempts; (5) admin force-close via `/api/exbot/close`. Duplicate trigger (e.g. two concurrent admin calls) -> rejected by the UNIQUE constraint.
- Execution sequence (FR-EXBOT-073, fixed, no step skipped): `requested -> hedge_close_pending -> hedge_closed (stop cancelled) -> lp_closed (BnzaExVault.redeem, LP NFT burned) -> funds_parked (USDC -> uninvested_balances, accessible via uninvestedBalanceOf) -> done (lifecycle_state=cooldown)`. **LP close is never attempted before `hedge_closed`.** Hedge close failure -> retry up to 3x then escalate to admin and hold at `hedge_close_pending` (does not silently advance). On-chain assertion: `vaultClose(tokenId, dest=UNINVESTED)` -> `FundsParked` event; off-chain: `close_operations` state column transitions.

### G3. close_operations state coverage (`states.md`)

Cover the full state set and which close kind reaches it: `requested`, `lp_closed`, `funds_returned` (user_redeem only), `hedge_close_pending` (bot_safe_close first step / user_redeem after funds_returned), `hedge_closed`, `funds_parked` (bot_safe_close only), `residual_hl_liability` (either, on hedge-close failure), `done`. UNIQUE `idempotency_key` prevents double settlement (FR-EXBOT-070 AC).

---

## H. Automatic Re-Entry & Parked Loop (F-05, FR-EXBOT-071)

**Evidence:** `flows.md` F-05 re-entry loop; `states.md` (`cooldown`, `parked`); `spec.md` FR-EXBOT-071; `funding_daily_metrics` in ERD.

- After `bot_safe_close` done -> `lifecycle_state=cooldown` (60 min). Re-entry judgment **every 60 min**: read 7-day funding APR (`funding_daily_metrics`) AND on-chain `uninvestedBalanceOf(user, botId)` (**on-chain is canonical** for the capital check, not D1, FR-EXBOT-071 AC).
- Re-entry condition: `funding APR > -15%` AND preflight (2.0x buffer) passes AND on-chain `balance > 0` -> `redeploy(botId)` -> `FundsRedeployed` event, set `uninvested_balances=0`, run the open flow (`preflight -> ... -> active`). Else stay `cooldown`.
- Boundary BVA: APR exactly `-15%` (not `>`) -> stay cooldown; balance exactly 0 -> stay cooldown.
- 3rd `bot_safe_close` within a 7-day rolling window -> `lifecycle_state=parked` (24h interval) + admin escalation notification. Recovery from `parked -> active` is autonomous under the same conditions (24h cadence).
- Notifications: user notified on cooldown entry, re-entry success, and parked transition.

---

## I. Reconciliation & Deep-Audit (FR-EXBOT-016, 025)

**Evidence:** `spec.md` FR-EXBOT-016, 025, 033; `states.md` (deep-audit cadence).

- Deep-audit every 6h (active + paused); reduces to 1h in high-risk mode (`circuit != closed` OR `margin_status IN ('warning','critical')`).
- Per cycle: fetch `clearinghouseState`; verify actual short size matches `hedge_legs.last_known_hl_short_size` (mismatch -> SAFE_MODE / repair routing); detect `stop_trigger_crossed_at` stuck > 30 min -> SAFE_MODE; detect `stop_replacing_started_at` stuck > 60s -> SAFE_MODE (secondary backstop to the light-check primary, FR-EXBOT-033); update `margin_status` from fresh `marginSummary`.
- Reconcile success is recorded only after actual state confirms expected (no optimistic "success" before reconcile).

---

## J. Durable Objects & Rate Limit (integration preconditions)

**Evidence:** `spec.md` FR-EXBOT-091, 092, 093; NFR-EXBOT-004, 011.

- `HLRateLimitDO` (FR-EXBOT-091, NFR-EXBOT-004): total HL weight in any 60s window <= 800 (67% of the 1,200 hard limit). A caller receiving `{allowed: false, retryAfterMs}` must NOT proceed — it re-queues with the delay. Weight accounting covers all 5 endpoint categories. Window resets every 60s; single DO instance per region.
- `UserLockDO` (FR-EXBOT-092): see Add-on D (lease semantics, idempotencyKey result caching).
- `MarketDataDO` (FR-EXBOT-093): all light-check workers read pool slot0 from the DO, not individual RPC calls (10,000 workers -> <=1 RPC/refresh interval). Stale cache (2x refresh interval) -> forced refresh + warning log; `blockNumber` must monotonically increase (a lower value is treated as cache regression and re-fetched).
- Concurrency cap (NFR-EXBOT-011): <=6 simultaneous outbound connections per Worker invocation; <=6 parallel HL fetches within one invocation.

---

## K. Idempotency, Determinism & Precision (cross-cutting)

**Evidence:** `spec.md` FR-EXBOT-011, 024, 027, 030, 021; NFR-EXBOT-007, 008; ERD key invariants.

- `queue_idempotency.message_id` UNIQUE -> redelivery produces exactly one execution; second exits on UNIQUE conflict (FR-EXBOT-011).
- Deterministic `cloid` for every HL order; `idempotencyKey=hedge-sync:{botId}:{stateVersion}` for the lock; `stateVersion` guard before any mutation; guarded NULL-only write for `stop_trigger_crossed_at`.
- Precision: all hedge / stop / margin math in BigDecimal; wei<->token unit conversion exact (no float rounding loss); `stopSafetyFactor=0.70` (Phase A, `OQ-EXBOT-07` for Phase B+). No float storage — all financial amounts are TEXT BigDecimal strings (ERD invariant).
- Key D1 invariants to test as guards: `positions.bot_id UNIQUE` (1 bot : 1 position), `hedge_legs.bot_id UNIQUE` (1 bot : 1 hedge leg), `close_operations.idempotency_key UNIQUE`, `lp_operations.idempotency_key UNIQUE`.

---

## L. Dependencies & Environment (logic preconditions, not UI)

**Evidence:** `spec.md` FR-EXBOT-090; integration constraints IC-EXBOT-001..004; BR-EXBOT-010, BR-EXBOT-008.

- Operator Facade (FR-EXBOT-090, BR-EXBOT-010): ExBot Worker reached only via the OPERATOR facade `/api/exbot/*` over a CF **service binding** with an internal token. A direct HTTP request to ExBot Worker returns 403 (not internet-accessible). Five endpoints: `start`, `status`, `close`, `agent-key`, `margin`. OPERATOR owns no business logic — it forwards only. `POST /api/exbot/start` is the entry to F-03.
- Agent-key lifecycle (FR-EXBOT-080..083 — Add-on M): provisioning, approval, expiry, revocation, rotation.
- BnzaExVault contract (IC-EXBOT-002): integrated via ABI only; contract address injected via Cloudflare Secrets Store (not hardcoded); `redeem()` / `uninvestedBalanceOf()` stubbed until ABI confirmed (`OQ-EXBOT-08`). The bot type config (`hedge_ratio`, `leverage`, `stop_safety_factor`) is interface-only, supplied by zen via Admin (BR-ADM-021).
- Chain/network gate (IC-EXBOT-003, FR-EXBOT-004): Base + Optimism dual-chain; `wethIndex` verified per chain and stored in `positions.weth_index` at LP open (not hardcoded). Hyperliquid testnet vs mainnet must be gated for the hedge leg.
- Naming guard (BR-EXBOT-008): "BnzaExVault/Vault" (LP NFT custody contract) must never be conflated with "vaultAddress/subaccount" (HL subaccount). A TC reviewing config must keep these distinct.

---

## M. Agent-Key Lifecycle (backend, no human popup)

**Evidence:** `spec.md` FR-EXBOT-080, 081, 082, 083; NFR-EXBOT-006; error codes E-EXBOT-003, 004; ERD `hl_agent_keys`.

- Storage (FR-EXBOT-080): master private key **never** stored; only the approved agent key, AES-256-GCM envelope-encrypted (per-row DEK wrapped by Master Key in Secrets Store; columns `encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`). A D1 dump of `hl_agent_keys` contains only encrypted blobs. During decrypt, plain DEK + plain key are function-scoped and destroyed after signing; **no log contains the raw key or DEK** (NFR-EXBOT-006).
- Approval (FR-EXBOT-081): new key `approval_status='pending'`; admin approves via `/api/exbot/agent-key`. `pending`/`revoked` -> rejected at preflight (`E-EXBOT-003`); `expires_at < now` -> rejected (`E-EXBOT-004`).
- Revocation (FR-EXBOT-082): non-destructive — old row -> `approval_status='revoked'`, `revoked_at=now`; new submission inserts a new row; never two `approved` rows per user (DB-enforced); `DELETE` of revoked rows forbidden (audit). An in-flight hedge-sync decrypting a revoked key -> decryption failure -> log error (no key material) -> SAFE_MODE.
- Expiry & rotation (FR-EXBOT-083): deep-audit checks `expires_at`; if `<= 7 days` -> `notification` to user; re-submission flow keeps the existing approved key active until admin approves the replacement, then old row -> `status='superseded'` atomically with new -> `approved`. Rotation chain is retained via `rotated_from` (audit; no destructive delete).

---

## N. Out of Scope — DO NOT design test cases for these (flag instead)

**Evidence:** `spec.md` section 1.3 In/Out of Scope, section 4 BR list, section 9 open questions.

Do not write functional TCs for the following — they are owned by zen / contract dev / audit, not by this infrastructure module. Flag them as out-of-scope in the chat report (per `SKILL.md` -> Step C):

- EXBOT proprietary trading-strategy math: PositionCalc, hedge math formula, stop safety-factor tuning (section 1.3 out of scope; the *integration* of these is testable, the *math correctness* is not).
- BnzaExVault Solidity contract internal logic / contract development (IC-EXBOT-002 — integrate via ABI only).
- Gas optimization and on-chain security audit of the contract.
- Phase 0 verification tasks (NV-1..NV-14) and any value still pending an Open Question (`OQ-EXBOT-01..12`) — design the case structure but mark the concrete number as "pending Phase 0 confirmation; re-confirm against latest SPEC".
- POOL UI / ADMIN UI screens (section 6 Screen Inventory: EXBOT is backend-only; UI is owned by `bnza-pool` / `bnza-admin`).

---

## Output principle (EXBOT)

A good EXBOT logic suite combines, per operation:

```text
Common 5 logic phases (common-logic-technical.md)
+ This EXBOT add-on (lifecycle A, init B, fan-out C, hedge-sync D, circuit E, margin/SAFE_MODE F, close G, re-entry H, reconcile I, DO/rate-limit J, idempotency/precision K, dependencies L, agent-key M)
+ Blockchain (Chain + Signer) add-on from common-logic-technical.md WHEN the operation touches vault / HL signer / on-chain read
+ Business rules BR-EXBOT-001..010 and error codes E-EXBOT-001..013 as expected results
+ Both on-chain AND off-chain (D1) expected results for every on-chain operation
```

Never produce a suite that merely lists endpoints or queue names — every case must state an observable, measurable effect and trace to a cited FR / BR / E-code / flow.
