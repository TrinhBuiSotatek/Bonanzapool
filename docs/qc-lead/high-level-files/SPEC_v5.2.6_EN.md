# BNZA Ex Bot Integrated Technical Specification v5.2.6 Final Approved

> This English version is authoritative for SOTATEK review.
> Japanese original: SPEC_v5.2.6.md

**Last Updated**: 2026-06-12
**Status**: v5.2.6 Final Approved — v5.2.5 + 3-AI QA reflected (Theme A–F). Phase 0 start OK (the 4 start conditions are in §0.3 / §30, external assumptions in §0.5 NV)
**Target Audience**: For Claude Code implementation / For SOTATEK implementation
**Base**: A direct patch onto v5.2.5. A **design-revision version** reflecting the findings of the 2 validation reports (Claude Code / Codex) (Theme A–F, includes behavioral changes)
**Patch chain**: v5.2 → v5.2.1 (P0 ×11) → v5.2.2 (Codex sync-misses ×5) → v5.2.3 (P1/P2 doc-sync ×3) → v5.2.4 (self-containment) → v5.2.5 (minor notes reflected) → v5.2.6 (3-AI QA reflected / Theme A–F). v5.3 is skipped. The full item summary is completed in §30 patch chain of this SPEC. The complete diff history is retained in git history

> 🚨 v5.2.6 applied (design revisions reflecting the 2 QA reports: Claude Code / Codex, Themes A–F):
> A-1 move §17.1 stop monitoring ahead of the circuit breaker / A-2 unify the stop subsystem on BigDecimal + field names /
> A-3 §19.5 protected stop replacement invariant / A-4 automatic cooldown ladder after stop fires /
> A-5 circuit breaker unification (stored column is canonical + half_open transitions) /
> B-1 §13.10 lp_operations (on-chain success + D1 failure recovery) / B-2 close/redeem state machine + §16.7 closed loop /
> B-3 dust close bypass / B-4 partial reconcile promoted to first-class / B-5 lifecycle enum canonicalization /
> B-6 §13.8 queue idempotency ledger / B-7 one-bot preflight gap fix /
> C-1 margin warning guard / C-2 margin definition fixed + preflight 2.0x / C-3 price 3-way split (uni/mark/oracle) /
> C-4 budget overflow = proportional scale-down ladder / C-5 restore light-check HL-inviolability /
> D-1 D1 write budget + gate / D-2 D1 Free 500MB correction / D-3 tolerance_ratio note /
> D-4 §7.3 canonical note / D-5 connection 6 / margin 33% / bps path notes /
> E dual-chain (Phase 1 = Base + Optimism) / F-1 add §0.5 NV / F-2 version bump.
> Unlike doc-syncs up to v5.2.5, this **includes behavioral changes**. Details in §30 patch chain.
> 🆕 v5.2.6-r1: 4 validation rework items reflected (R-1 §16.5 one-bot query granularity fix / R-2 §13.12 system_config added /
> R-3 §19.2 resize procedure replaced with a note pointing to §19.5 INV-STOP / R-4 §0.5 NV table augmentation NV-13/14 + NV-3/4/6 detail).
> 🆕 v5.2.6-r2: 5 Codex re-validation findings reflected (X-1 unify §17.2 stop cancel/place into §19.5 replaceStopProtected /
> X-2 fully separate §16.4 user_redeem into a LP-first state machine, retire the old Standard Close / X-3 align park accounting with INV-3 +
> §13.13 uninvested_balances + Funds* events / X-4 §7.5 scale-down ladder idempotency + re-expansion policy + hedge_legs columns /
> X-5 fully retire the ethPriceUsd data field → uni/mark/oracle 3-price mapping + X-1b SAFE_MODE on restore failure in the skeleton).
> 🆕 v5.2.6-r3: 4 Codex round-3 findings reflected (Y-1 align §19.5 yaml prose with the r2 skeleton, (b)-path fix, responsibility-boundary note /
> Y-2 reduce §16.6 LP_CLOSING to a §16.4 reference, remove the old hedge-first transition diagram / Y-3 uninvested_balances concurrency control
> (on-chain canonical, additive upsert, lease exclusivity, CAS, event-driven sync) / Y-4 make §7.5 re-expansion a 3-condition AND + change the breach reset condition).
> 🆕 v5.2.6-r4: round-4 cross-validation findings reflected (Z-1 add §15.5.6 vaultClose(dest) / uninvested* functions + required-interface note /
> Z-2 reduce the §16.4 overview transition to an enum list / Z-3 delete the old A-3 comment in §17.2 / Z-4 unify §16.4 (b) restore-success to partial_repair enqueue + failed throw /
> Z-5 wire STOP_REPLACING 60s overrun detection into §19.3/§18.3 / Z-6 resolve the E-11 dead link, §16.3 CLOSED exception note, §15.1 dust alignment, §30 version bump).
> 🆕 v5.2.6-r5: 5 round-5 leftover items reflected (W-1 make §16.7 redeploy reference uninvestedBalanceOf explicitly / W-2 remove (a)/(b) ordering-management wording from §17.2 → §19.5 single execution point /
> W-3 three-point alignment of partial_repair schema/producer×2/consumer (reason required enum + attemptId wiring) / W-4 update §30's old v5.2.5 notation to v5.2.6 and isolate the v5.2.5 final statement as history /
> W-5 move STOP_REPLACING overrun detection forward into §17.1 light-check (primary detection ≤5 min, §19.3 audit as a secondary backstop)).
> 🆕 v5.2.6-r6: round-6 findings reflected (V-1 unify the W-5 follow-up onto partialRepairQueue + extend partial_repair reason to 3 values
> (stop_replacing_overrun) + attemptId nullable + add consumer branch / V-2 remove (a)/(b) wording from the §17.2 step 11 comment).

> 🚨 v5.2.5 applied minor-notes-reflection patch (Codex extracted, zero design changes):
> After Codex's lightweight re-validation of v5.2.4 returned APPROVED with minor notes, 2 findings were reflected: v5.2.5-N1 resolved the staging mismatch between §30 Status / §30.2 next-process, unified to Final Approved / v5.2.5-N2 updated the §16.5 Phase B note's old version-dependent wording to version-neutral "in this SPEC"
> Design content unchanged from v5.2.4.
>
> 🚨 v5.2.4 applied doc-self-containment patch (self-containment, zero design changes):
> Removed external references to the past PATCH_NOTES.md, making this SPEC v5.2.5 self-contained for
> the full patch chain (v5.2 → v5.2.1 → v5.2.2 → v5.2.3 → v5.2.4 → v5.2.5) information.
> Design content unchanged from v5.2.3.
>
> 🚨 v5.2.3 applied P1/P2 (Claude Code extracted, tiny doc-sync ×3):
> v5.2.3-P1-A added a dek pattern to the §21.5.4 sanitize regex + named the columns (security defense-in-depth) /
> v5.2.3-P1-B unified the §10.1 hedge-sync queue / §17.2 function arguments to the canonical RebalanceReason[] type (the last mile of §7.6 P0-11) /
> v5.2.3-P2-A fixed the version staleness of §0.3 start condition 1 (exact match with §30)
>
> Zero structural changes. Design philosophy, API, schema, enum values, Solidity ABI, and operational flow are all unchanged from v5.2.2.
> The summary of all patches (v5.2 → v5.2.1 P0 ×11 / v5.2.1 → v5.2.2 sync-misses ×5 /
>  v5.2.2 → v5.2.3 doc-sync ×3 / v5.2.3 → v5.2.4 self-containment /
>  v5.2.4 → v5.2.5 minor notes reflected) is in
> §30 patch chain. The complete diff history is retained in git history.

---

## 0. Final Review Judgment (added in v5.1)

### 0.1 v5.2 Status

```yaml
v5.0 Status:        "Final Draft for GPT / Codex Validation"
v5.0 validation conclusion: "Strategy/infra direction is sound. After reflecting the 22 required fixes, implementation can start as v5.1"
v5.2 Status:        "Final Candidate — Phase 0 start OK after zen approval"
v5.2.6 Status:      "v5.2.6 Final Approved (v5.2.5 + 3-AI QA reflected, Theme A–F)"  # 🆕 F-2
Fundamental rework: not needed (strategy core / infra core retained. v5.2.6 is a design revision of safety net / state machine / pricing / dual-chain)
```

### 0.2 What changed v5.0 → v5.1 (summary)

```yaml
What was changed (summary of the 22 required fixes):
  - Made strategy wording realistic (removed "net ≥ 0 in all markets", stated no full IL elimination)
  - Made Cloudflare constraint numbers accurate
  - Changed UserLockDO from function-callback to lease-based (implementability)
  - Stated the LP NFT custody / control model in a new section
  - Fixed hedge execution to delta-only adjustment (no full close/open every time)
  - Redefined the Stop / Liquidation model (stop is loss cap, not liquidation avoidance)
  - Countermeasure for stale state after stop trigger (priority audit + crossed marker)
  - Fixed D1 schema inconsistencies (add via ALTER TABLE, no deletion)
  - Stated Security / key handling in a new section
  - Insufficient margin UX (preflight + warning + critical + SAFE_MODE)
  - LP close authority (stated the close flow via BnzaExVault)
  - Realistic subdivision of Phase A (Phase 0 / A1 / A2 / A3) and explicit Defer list
  - Simplified the Funding ledger per phase
  - Analytics Engine high-cardinality warning
  - Stated the One-user one-bot policy (Phase A)
  - LP operation state machine (LP_OPENING / LP_REBALANCING / LP_CLOSING / LP_FAILURE)
  - Fixed backtest ordering (Step 0: PositionAmountCalculator mini first)
  - Made competitive-differentiation wording realistic (removed mathematical-superiority claims vs Panoptic / Neutra)

What was NOT changed:
  - Strategy core: LP fee engine + adaptive hedge overlay (70% short, 3x isolated)
  - Infra core: CF Workers + D1 sharding + Queue fan-out + DO
  - Product lineup: LP / Ex / LP Plus / AI Pro
  - Phase direction: Correctness MVP → 1k → 10k bots
  - Adoption / non-adoption judgment: the carter2099 / Panoptic comparison core
```

### 0.3 Start conditions (the judgment conditions for Phase 0 start OK)

```yaml
🚨 v5.2.1 (P0-7 + P0-10): unified the start conditions to 4 (exact match with §30).
  The old §0.3 had "3 conditions" but contradicted §30's "4 conditions" → unified to 4.

The 4 conditions to start implementation (start Phase 0 once all 4 are met):
  1. zen reads this v5.2.6 and gives approval (document finalized)
     🚨 v5.2.6 (W-4): exact match with §30 (inherits the v5.2.3 P2-A anti-staleness principle).
  2. LP NFT custody integration policy finalized:
     🚨 v5.2.1 finalized (Option C / Section 3.4) — newly develop and newly deploy an
        EXBOT-dedicated BnzaExVault. The current BnzaRouter v2.2.1 / BnzaLpBot v1.1 are
        not modified. Before Phase 0 starts, zen finalizes the deploy address / operator /
        multiSig (Section 15.5.6 zen task)
        🆕 v5.2.6 (E): because Phase 1 = Base + Optimism dual-chain,
        the deploy address / operator / multiSig are finalized as **2 sets for Base + OP**.
  3. The detailed design of the Hyperliquid agent key encrypted-storage method must be
     finalizable at Phase 0 start:
     🚨 v5.2.1 finalized — Phase A default = Cloudflare Secrets Store
        (Section 21.5.2 / 21.5.2.1 runbook, P0-4)
  4. The post-WL-5/15-launch instability gate (🚨 redefined in v5.2.1 P0-10):
     - The WL 5/15 launch has already happened (the old "avoid conflict with 5/15" is void)
     - Incident handling such as Stage 3 rollback (multi-relayer related) has
       settled down
     - Concrete gate: zero SAFE_MODE occurrences over the past 7 days, no major incident
     - The point at which zen judges "the post-POOL-launch instability period is over"

If the 4 conditions are not met, implementation does not start.
In particular, conditions 2 and 3 cause large rework if started in Phase A, so they are pinned before Phase 0 completes.
Condition 4 is a gate to protect POOL operational stability (quality-first policy, deferral allowed).
```

---

## 0.4 Validation request (former Section 0, retained from v5.0)

### 0.4.1 Validation purpose

This specification v5.2 is a version integrating the following:

- **v1-v3 (Claude)**: strategy concept, product design, Marketing
- **v3.1 validation (prior AI)**: mathematical fixes, liquidation calculation, Funding handling
- **v4.1 validation (prior AI)**: infra layer, CF Workers / D1 / Queue design, 10,000 bot scale
- **carter2099 analysis (Claude Code)**: implementation-pattern adoption/non-adoption judgment
- **v5.0 validation report (GPT / Codex integrated version)**: 22 required fixes

### 0.4.2 Points to validate (retained from v5.0, adjusted for v5.2)

```yaml
1. Consistency of the v3.1 strategy layer and v4.1 infra layer (still maintained after v5.1 fixes?)
2. Mathematical validity (Position amount / Hedge / liquidation / Drift)
3. Conformance to Cloudflare constraints (the numbers in Section 5.2)
4. Conformance to Hyperliquid spec (Rate limit / subaccount / native stop / cloid)
5. Feasibility of 10,000 bot scale (Throughput / Sharding / Concurrency)
6. Critical oversights (Edge case / Failure / Recovery)
7. Realism of the Implementation roadmap (Phase subdivision, zen solo)
8. Validity of LP NFT custody / Security / Margin UX / LP state machine added in v5.1
```

---

## 0.5 External assumptions that MUST be verified in Phase 0 (NEEDS-VERIFICATION) (🆕 v5.2.6 / F-1)

```yaml
🚨 v5.2.6 (F-1, transcribing QA Codex NV-1–12): among this SPEC's behavioral specs, the
  assumptions that depend on the real behavior of external systems (Hyperliquid /
  Cloudflare / on-chain) are listed as NV items. Measure and finalize them in Phase 0,
  reflect the results into this SPEC, then enter the implementation body.
  Owner: NV-1–7 (Hyperliquid) = SOTATEK (Phase 0 deliverable, BNZA review)
        NV-8–11 (Cloudflare) = SOTATEK (same)
        NV-12 (pool addresses, both chains) = BNZA (zen)
  🔗 The NV-1 / NV-3 results finalize the §19.5 (A-3) (a)/(b) branch.
```

| NV | Category | What to verify | Affected SPEC location | Owner |
|----|------|----------|--------------------|------|
| NV-1 | HL | the exact API fields of isolated margin (marginBalanceUsd = allocated isolated equity / marginRequiredUsd) and the acceptance spec of reduce-only stop | §18.4 (C-2) / §19.5 (A-3 branch) | SOTATEK |
| NV-2 | HL | whether clearinghouseState returns entryPx / liquidationPx / effectiveLeverage / isolatedMargin | §17.3 / §19.1 | SOTATEK |
| NV-3 | HL | **whether duplicate reduce-only stops are accepted** on the same leg (allowed→A-3(a) / not→A-3(b)). whether a reduce-only stop's size can exceed the current position / cancelByCloid behavior after trigger fire/fill | §19.5 (A-3 branch) / §17.2 | SOTATEK |
| NV-4 | HL | native trigger stop mark-price firing / immediate-trigger rejection / p(orderPx) behavior. whether the trigger source is mark price or oracle price / partial fill behavior of trigger orders | §8.4 / §19.2 / §15.1 (C-3) | SOTATEK |
| NV-5 | HL | behavior on cloid duplication (idempotency). whether a deterministic cloid prevents double submission | §8.5 / §13.8 (B-6) | SOTATEK |
| NV-6 | HL | order / info(clearinghouseState) behavior when subaccount + vaultAddress are specified. order/info behavior on agent key expiry / revocation | §8.3 / §16.5 / §21.5 | SOTATEK |
| NV-7 | HL | measured rate-limit weight (clearinghouseState=2 etc.) and the userRateLimit endpoint | §5.2-3 / §9 | SOTATEK |
| NV-8 | CF | measured Workers subrequest Paid=10,000 / simultaneous open connections=6 | §5.2-1 / §5.2-8 (D-5) | SOTATEK |
| NV-9 | CF | D1 queries Paid=1,000 / single-thread write / write QPS (10k load) | §5.2-2/4 / §5.2.1 (D-1) | SOTATEK |
| NV-10 | CF | Queue throughput 5,000/s / batch 100 / concurrency 250 / wall 15min | §5.2-5 | SOTATEK |
| NV-11 | CF | Durable Object single-thread / lease behavior / Secrets Store binding decrypt round-trip | §11 / §21.5 | SOTATEK |
| NV-12 | Chain | Base + Optimism pool address / token0-token1 order (wethIndex) / BnzaExVault deploy address | §1.3 (E) / §6.4 / §15.5.6 | BNZA (zen) |
| NV-13 | HL | ETH perp min order / min notional / min size. whether there is a means to physically clear dust below the minimum close size (the minimum of market reduce-only, handling of write-off) | §17.2 (B-3) / §16 residual_hl_liability | SOTATEK |
| NV-14 | HL | builder fee 5bps approval flow / billing timing / interaction with agent key/subaccount / whether it applies to stop/trigger fills | §2 / §8 | SOTATEK |

> 🆕 v5.2.6 (r1): NV-5 (cloid idempotency) is a v5.2.6 addition not in the QA original (B-6 dependency). NV-13/14 added from the original cross-check.

```yaml
Reflection flow:
  - In Phase 0, measure each NV → reflect the results into the corresponding SPEC location (finalize constants/branches)
  - In particular, do not implement §19.5 (stop replacement) while NV-1 / NV-3 are unconfirmed
  - Do not implement §6.4 while NV-12 (dual-chain pool/wethIndex) is unconfirmed
```

---

## Part 1: Strategy & Product

## 1. Product Scope

### 1.1 Product Identity

```yaml
Product name: BNZA Ex Bot
Tagline: Managed delta-hedged LP Bot powered by Hyperliquid
Position in BNZA Lineup:
  LP Bot (current):  Pure LP, no hedge        — for DeFi beginners
  Ex Bot (this spec): LP + HL hedge           — intermediate users, aiming to suppress IL drawdown
  LP Plus (Phase 2): LP + Revert Lend       — Capital Efficiency focused (Defer)
  AI Pro (Phase 3): LP + Aave + Hedge       — advanced users, market optimization (Defer)
```

### 1.2 Core Strategy (wording fixed in v5.1)

```yaml
Strategy Concept: LP Fee Engine + Adaptive Hedge Overlay

Primary revenue: Uniswap V3 LP fee
Hedge role:
  - partial hedge of ETH directional exposure
  - aim to "reduce" IL (not full elimination)
  - design goal of overcoming hedge cost with LP fee

Mathematical principle:
  net = LP_fee
        - IL/LVR/gamma_loss
        - hedge_cost
        - funding_cost
        - gas/bridge
        - performance_fee

🚨 wording fixed in v5.1:
  ❌ old (v5.0): "net ≥ 0 in all markets, especially suppressing drawdown vs pure LP in down markets"
  ✅ new (v5.1):
     "Goal: suppress drawdown vs pure LP, and aim for net positive APR in the median scenario.
      However, net ≥ 0 in all markets is NOT guaranteed.
      IL is a reduction target for this Bot, not an elimination target.
      In markets where Hedge cost / funding / gamma loss exceed LP fee (low vol + ranging-out),
      net negative can also occur."

🚨 Non-existence of an IL elimination guarantee (stated in v5.1):
  This Bot is designed to reduce IL (reduce drawdown); it does not have a guarantee to
  eliminate / hedge out IL.
  - LP gamma loss cannot be fully removed by hedging
  - hedge cost (funding / spread / slippage) always occurs
  - the delta of hedge and LP is a discrete adjustment, not continuous hedging
  - within the rebalance threshold, un-hedged delta remains
```

### 1.3 Phase 1 Scope (this spec)

```yaml
Chain: Base + Optimism dual support (🆕 v5.2.6 / Theme E, both chains from Phase 1)
  - current LP Bot integration (3 of 5 Base bots running)
  - Optimism also supported from Phase 1 (the old "go to Phase 2 if backtest beats by >10%" gate is removed)
  - 🆕 the hedge side (HL ETH-USD perp) is **chain-independent**. The dual-chain impact is on the LP side only
    (Uniswap V3 / BnzaExVault / RPC / subgraph / wethIndex) (§6.4 / CC i-5)

LP:
  Pool: USDC/ETH 0.3% (Uniswap V3) — both Base + Optimism pools
  Range: ±5% single (ladder is Phase 2 / Defer)
  Note: the token0/token1 order of USDC/WETH can differ between Base and Optimism.
      wethIndex is verified and stored per chain (§6.4 / §24.2)
  
Hedge:
  Venue: Hyperliquid
  Asset: ETH-USD perpetual short
  Hedge ratio: 70% (Balanced fixed, Phase 1)
  Leverage: 3x configured (effective leverage is dynamic)
  Margin mode: Isolated (absolute)
  Builder fee: 5bps

Risk Management:
  HL native stop: required (loss cap, not liquidation avoidance, see Section 19)
  Reconcile after order: required
  Circuit breaker: stop after 3 consecutive failures within 24h
  Stop trigger crossed marker: required (see Section 19)

User policy:
  Phase A: 1 user = 1 active Ex Bot (see Section 16.5)
  Phase B+: multiple bots per user (isolated by subaccount allocation)
```

---

## 2. Target User & Marketing

### 2.1 Target User

```yaml
Persona:
  - DeFi intermediate user (understands the LP concept)
  - USDC-based thinking
  - wants to reduce the IL risk of pure LP (reduce, not eliminate)
  - prefers drawdown suppression over high APR
  - able to participate at own risk
  - Bot UI is enough; does not want to compute hedges themselves

Expected APR (Net, after 30% PF):
  Best case:    +25-35%
  Median:       +10-20%
  Bad case:     -5% to +5%
  Tail event:   -10% to -20% (when Stop trigger fires / repeated SAFE_MODE)

🚨 v5.1 note:
  The above are model cases. Actual APR can diverge from backtest.
  In particular, "net ≥ 0 in all markets" is not guaranteed (see Section 1.2).
```

### 2.2 Marketing wording rules (re-emphasized in v5.1)

```yaml
✅ OK wording:
  - "a managed LP Bot that makes Uniswap V3 LP fee its primary revenue while partially suppressing ETH directional exposure via a Hyperliquid short"
  - "designed to suppress drawdown vs pure LP (reduction, not elimination)"
  - "automatically hedges ETH directional exposure (partial)"
  - "a managed delta-hedged LP Bot integrated into BNZA POOL"

❌ NG wording (reconfirmed in v5.1):
  - "safe with IL hedging"
  - "principal guaranteed"
  - "no principal loss"
  - "reduces IL by 90%" (a guarantee of a concrete number)
  - "perfect hedge"
  - "completely removes IL / IL elimination"
  - "net positive in all markets"
  - "world first" / "the only implementation"

⚠️ Risk Disclosure (must be stated):
  - LP gamma loss (cannot be fully removed by hedging)
  - loss-realization risk from a Hedge stop trigger (not liquidation, but the loss is realized)
  - HL liquidation risk (the final fallback if the stop is delayed)
  - Funding rate cost (during negative funding periods)
  - HL API failure risk (hedge does not move on SAFE_MODE entry)
  - Bridge / CCTP failure risk
  - USDC depeg risk
  - Operator bug risk
  - return reduction after performance fee
  - hedge-inability / SAFE_MODE-entry risk due to insufficient margin
```

### 2.3 Performance Fee display

```yaml
Fee structure (same as existing):
  Operation fee: 100% BuyBack&Burn on-chain (BNZA token)
  Performance fee: 30% off-chain, up to 10 recipients

Transparent UI display (required):
  Show both to the user:
    - Gross APR (before PF)
    - Net APR (after 30% PF)
  
  Example:
    "Expected Gross APR: 25%"
    "Expected Net APR: 17.5% (after 30% performance fee)"

Monthly report:
  LP fee income: $42
  Funding received/paid: ±$5
  Hedge PnL: -$15
  Hedge adjustment cost: -$8
  Bridge cost: $0
  Gross PnL: $14-24
  Performance fee (30%): -$X
  Net to user: $Y
```

---

## 3. Critical Design Decisions

### 3.1 What to adopt from carter2099/delta_neutral

```yaml
copy:
  - hedge management per asset leg
  - target_short = pool_amount × target_ratio (absolute-value formula)
  - absolute-value formula for tolerance judgment
  - rebalance attempt history
  - 3-failures-in-24h circuit breaker (history-based)
  - nested order error parser
  - the idea of subaccount isolation
  - max() merge of subgraph collected + RPC uncollected
  - per-asset independence
```

### 3.2 What NOT to adopt from carter2099 (including fatal bugs)

```yaml
discard:
  - 🚨 LP amount calc by deposited - withdrawn + collectedFees (breaks on range out)
  - 🚨 calculation without tick / liquidity / sqrtPriceX96 (ignores the Uniswap V3 formula)
  - single subgraph URL (multi-network spoofing)
  - market order only (no stop / TP-SL)
  - no reconcile after order (Atomicity missing)
  - no failed-rebalance notification
  - ambiguous pause that leaves a short with active=false
  - cross margin default (isolated required)
  - processing all hedges sequentially in 1 job (breaks on CF Workers)
  - PnlSnapshot every 1 minute (breaks on D1)
  - 🚨 (added in v5.1) full close → full open every time (subrequest waste + nonce burn)
```

### 3.3 What BNZA newly implements

```yaml
new:
  - PositionAmountCalculator (correct AMM formula)
  - HyperliquidAdapter (integrates rate limit / cloid / nested error / reconcile)
  - HL native reduce-only stop (loss cap, not liquidation avoidance)
  - Reconcile flow (post-order)
  - Funding ledger (per phase — Phase A: daily aggregate only)
  - Queue fan-out (light-check / hedge-sync separation)
  - UserLockDO (lease-based mutation lock — see Section 11)
  - HL global/user rate limiter (HLRateLimitDO)
  - D1 sharding (16 shards for 10,000 bots — introduced in Phase C)
  - MarketData cache (Durable Objects)
  - R2 / Analytics Engine archive (Phase B+)
  - Hedge budget cap (LP fee × 30%)
  - Edge filter (expectedEdge based)
  - 🆕 (v5.1) LP NFT custody model (owned by BnzaExVault, see Section 15.5)
  - 🆕 (v5.1) HL Agent Key envelope encryption (see Section 21.5)
  - 🆕 (v5.1) Delta-only hedge adjustment (see Section 17)
  - 🆕 (v5.1) Stop trigger crossed marker / priority audit (see Section 19)
  - 🆕 (v5.1) Insufficient margin preflight + warning + critical (see Section 18.4)
  - 🆕 (v5.1) LP operation state machine (see Section 16.6)
  - 🆕 (v5.2.1) BnzaExVault (EXBOT-dedicated LP NFT custody contract, see Section 15.5.6)
```

### 3.4 Separation of contract responsibilities (🆕 v5.2.1 — Option C finalized)

The BNZA ecosystem has the following 2 **independent** custody models:

| Product | Custody Contract | Deploy status | LP NFT holder |
|---|---|---|---|
| BNZA POOL (current) | BnzaRouter v2.2.1 | Running on Optimism + Base | user (user-owned NFT) |
| EXBOT (this SPEC's target) | BnzaExVault (new dev) | Not deployed | Vault contract |

```yaml
🚨 v5.2.1 zen decision (Option C):
  EXBOT newly develops and newly deploys a Solidity contract suite independent of
  BNZA POOL. When this SPEC says "Vault" / "BnzaExVault" it means an
  EXBOT-dedicated new contract; it does not modify the current BnzaRouter v2.2.1.

Responsibility-separation principle:
  - BnzaRouter v2.2.1 / BnzaLpBot v1.1: BNZA POOL only, no modification, continued operation
  - BnzaExVault: EXBOT only, new, spec'd in this SPEC §15.5.6
  - The two are non-interfering at the contract level (Section 15.5.4 INV-5)
  - Shared are only BNZAToken (BuyBack&Burn) and the Uniswap V3 NFPM

⚠️ Caution on terminology collision (important):
  Solidity's "BnzaExVault / Vault" and Hyperliquid's "vaultAddress
  (subaccount address)" are **completely unrelated**. In this SPEC:
    - "BnzaExVault" / "Vault custody" = EXBOT LP NFT custody contract
    - "vaultAddress" / "subaccount" = a subaccount identifier on Hyperliquid
  Do not confuse them.
```

---

## Part 2: Technical Architecture

## 4. High-Level Architecture

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  BNZA POOL UI (Next.js / Vercel)             │
│        - Bot start / stop / status display                  │
│        - HL margin balance check / Onboarding               │
│        - Margin warning / Critical / SAFE_MODE display      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│            BNZA OPERATOR (Cloudflare Workers)                │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Cron Scheduler Worker (every 1 minute)              │   │
│  │   shard window scan / enqueue only                  │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Queue: bot-scan → light-check → hedge-sync          │   │
│  │         → reconcile → deep-audit → stop-audit       │   │
│  └────────┬──────────────────────┬─────────────────────┘   │
│           │ rebalance candidate  │ priority audit          │
│           ▼                      ▼                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ UserLockDO (lease-based) + HLRateLimitDO            │   │
│  │   + HyperliquidAdapter                              │   │
│  │   - per-user mutation serialization (lease lock)    │   │
│  │   - global/user token bucket                        │   │
│  │   - delta-only hedge adjustment (Section 17)        │   │
│  │   - reconcile after order                           │   │
│  └────────┬────────────────────────────────────────────┘   │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│ D1 (shard count/phase)  │  │ R2 / Analytics Engine        │
│   - Phase A: 1 shard    │  │   - raw logs (Phase B+)      │
│   - Phase B: 4 shards   │  │   - old attempts (>90d)      │
│   - Phase C: 16 shards  │  │   - low-cardinality metrics  │
│   - hot state           │  │   ❌ do not use bot_id /     │
│   - rebalance attempts  │  │      user_id as a dimension  │
│   - circuit breakers    │  │                              │
│   - hl_agent_keys       │  │                              │
│   - hourly/daily metrics│  │                              │
└─────────────────────────┘  └──────────────────────────────┘

External:
  - Hyperliquid API (orders, info, trigger orders)
  - Uniswap V3 (Base / OP)
  - The Graph (subgraph per chain)
  - On-chain RPC (per chain)
  - Across / CCTP (bridge, executed on the user side)
  - 🆕 BnzaExVault (Solidity, LP NFT custody — Section 15.5)
```

### 4.2 Key Architectural Principles

```yaml
1. Separation of Light-check and Hedge-sync
   Light-check: does not touch HL, every 5 min, all bots
   Hedge-sync: HL mutation only, only when needed, event-driven
   Hedge-sync is a delta-only adjustment (see Section 17)

2. Per-user mutation serialization (lease-based)
   Serialize the same user's HL operations with UserLockDO
   acquire / release lock on a Lease (TTL) basis
   The function-callback approach (v5.0) is retired (see Section 11)

3. Shared market cache
   Share pool slot0 as a cache in MarketDataDO
   Bots do not RPC-fetch individually

4. Sharded state (per phase)
   Phase A: 1 shard / Phase B: 4 shards / Phase C: 16 shards
   shard determined by bot_id hash

5. Hot state only in D1
   History to R2 (Phase B+), metrics to Analytics Engine (Phase B+)
   minimize D1 row count

6. Idempotent mutations
   Cloid (deterministic) prevents duplicates
   Retry safe

7. Post-order reconcile
   Separate order submission from success recording
   Update DB after confirming the real position

8. 🆕 Delta-only hedge adjustment (v5.1)
   full close → full open every time is forbidden
   adjust only the delta of targetSize - actualSize
   Full close is for target=0 / emergency / manual reset only

9. 🆕 LP NFT custody by BnzaExVault (v5.1)
   The LP NFT is held by BnzaExVault, not the user wallet
   Details: Section 15.5

10. 🆕 Security: do not hold the master private key (v5.1)
    Store only the Agent key with envelope encryption in D1 / KMS-like
    Details: Section 21.5
```

---

## 5. 10,000 Bot Throughput Model

### 5.1 Required Throughput

```
10,000 bots / 5 minutes light-check
= 10,000 / 300 sec
= 33.3 bots/sec
= 2,000 bots/min
```

### 5.2 Bottleneck Analysis (Cloudflare numbers made accurate in v5.1)

```yaml
🚨 v5.1 note: the following corrects the "Cloudflare constraint number errors" flagged in v5.0 validation.
                Adopts numbers matching the official docs.
                (Cloudflare plan names can change, so re-confirm at Phase 0 start is recommended.
                 ⚠️ Verification needed (zen task): at Phase 0 start, confirm the latest values in the
                  Cloudflare official docs and update the table if stale)

1. Cloudflare Workers subrequest limit (per invocation):
   Free plan:        50 subrequests / invocation
   Paid (Standard):  10,000 subrequests / invocation (the old v5.0 "Paid 50" was wrong)
   1 hedge sync = 6-10 fetches (close + open + stop + reconcile, 4-8 even delta-only)
   → on the Paid plan there is plenty of headroom to batch multiple hedges in 1 invocation
   → but HL rate limit is a separate bottleneck, so fan-out is still needed

2. D1 queries per Worker invocation:
   Free plan:        50 queries / invocation
   Paid:             1,000 queries / invocation
   within 1 invocation, a single DO / Worker can issue multiple D1 queries
   → ~5-10 queries for 1 light-check
   → even processing 100 bots sequentially in 1 invocation stays under the limit
   → but to suppress queue lag / retry risk, fan-out is still needed

3. Hyperliquid REST rate limit:
   Official hard limit: 1,200 weight/min/IP
   clearinghouseState weight: 2
   polling all bots every 5 min = 4,000 weight/min
   → exceeds the limit by 3.3x, impossible
   → a design where light-check does not touch HL is mandatory

4. D1 constraints:
   Free:     500 MB / DB (🆕 v5.2.6 D-2 correction: 5 GB is "account total storage",
                          not per DB. The official value is Free 500 MB / DB)
   Paid:     10 GB / DB
   Paid:     50,000 DB / account (theoretical; in practice 16-32 shards assumed)
   Single-threaded per DB (concurrent writes are serialized)
   → sharding required (the Phase C 16-shard design is retained)
   → the design assumes Workers Paid (for the subrequest/CPU limits). Paid 10 GB/DB matters.

5. Queue constraints:
   Per-queue throughput: 5,000 msg/sec
   Batch size: max 100
   Push consumer concurrency: 250
   Wall time: 15 min
   → sufficient for fan-out

6. Same-user mutation collision:
   1 user's HL nonce is monotonically increasing
   parallel mutations collide
   → per-user lock in a DO (lease-based, Section 11)

7. Execution time:
   Workers Paid CPU time: up to 5 min
   Queue consumer wall clock duration: 15 min
   Design target:
     1 hedge-sync should normally complete well below 30 sec
     to reduce queue lag and retry risk.

8. Workers simultaneous open connection limit (🆕 v5.2.6 D-5, QA CC i-3):
   outbound connections that can simultaneously await a response per invocation = 6 (Free/Paid common).
   → in the 1 message = 1 bot fan-out design, simultaneous fetches per invocation are few, so no real harm.
     If an implementation fetches multiple bots in parallel in 1 invocation, limit it to 6 concurrent.
```

### 5.2.1 D1 write budget (🆕 v5.2.6 / D-1, QA Codex M-6)

```yaml
🚨 v5.2.6 (D-1): at 10,000 bots, D1 is single-threaded/shard. Budget the write QPS.

Write-reduction rules:
  - Write bot_runtime_state **only on change** (no-op detection: do not write if there is no diff from the latest persisted value).
    Forbid an unconditional UPDATE per light-check (§17.1 updateRuntimeState writes only on diff).
  - Separate scan cursor / next_light_check_at updates from per-bot writes and
    update in batch (1 statement per shard) (jitter is value computation only; writes are aggregated).

10,000-bot write QPS estimate (16 shards, Phase C):
  | Type                      | Frequency      | QPS per shard      | Note                       |
  |---------------------------|----------------|--------------------|----------------------------|
  | runtime_state (on diff)   | only changes   | << full count      | greatly reduced by no-op detection |
  | next_light_check (batch)  | every 5 min/agg| ~ (625/300) agg    | eliminates per-bot individual writes |
  | rebalance_attempts        | only on event  | low                | only on mutation           |
  | metrics rollup            | hourly/daily   | low                | aggregated                 |
  → confirm numerically that it does not jam even single-thread/shard before proceeding to Phase C.

🚨 gate: before transitioning to Phase C (16 shards / 10,000-bot equivalent),
  make **passing a 10k-equivalent load benchmark** a mandatory condition (added to §26).
```

### 5.3 Solution: Shared cache + Light-check + Event-driven

```yaml
Light-check (does not touch HL):
  source:
    - D1 hot state (last_known_short_size)
    - MarketDataDO (sqrtPriceX96, currentTick)
    - Local TickMath (LP amount calculation)
  weight on HL: 0
  
Hedge-sync (mutation candidates only, delta-only):
  trigger conditions:
    # 🚨 v5.2.1 (P0-11): references the canonical RebalanceReason (§7.6).
    #   The same set as §7.3 / §13.4 / §17.1. Do not create custom aliases / alternate sets.
    - drift_threshold / drift_relative   (detected in light-check)
    - range_out / range_boundary_near
    - margin_warning                     (§18.4; margin_critical is SAFE_MODE)
    - funding_alert / time_fallback
    - manual_admin / recovery_reconcile  (deep audit mismatch / repair flow)
  excluded (not a hedge-sync reason):
    - stop_trigger_crossed_at marker set / near-stop
      → route to priority stop-audit/reconcile (Section 19.3 / §17.1)
  weight on HL: 4-8 weight/hedge (HL rate-limit weight, reduced by delta-only)
    ※ a different unit from CF subrequest count (for subrequests see §5.2-1, P1)
  
Deep audit (periodic reconcile):
  cadence: 6h normal / 1h high-risk
  full HL clearinghouseState fetch
  distribute all bots (spread over time)

Stop integrity audit:
  cadence: 6h normal
  trigger:
    - near-stop (price ±2% to stop)
    - 🆕 (v5.1) ETH price >= stop_price (priority audit, immediate enqueue)
    - 🆕 (v5.1) stop_trigger_crossed_at marker set

Forbidden at scale:
  ❌ clearinghouseState fetch for all bots every 5 min
  ❌ openOrders fetch for all bots every 5 min
  ❌ userFunding fetch for all bots every 5 min
  ❌ (v5.1) full close → full open per hedge-sync
```

---

## 6. Position Amount Calculation

### 6.1 Fundamental Rule

```yaml
Hedge size MUST be based on current Uniswap V3 position amount.

❌ DO NOT USE (carter2099's bug):
  amount = depositedToken - withdrawnToken + collectedFees
  
✅ USE (the correct AMM formula):
  liquidity (from NFT)
  tickLower (from NFT)
  tickUpper (from NFT)
  sqrtPriceX96 (from pool)
  currentTick (from pool)
```

### 6.2 Mathematical Foundation

```
S = sqrt(P) (sqrt of the current price)
A = sqrt(P_lower) (sqrt of the range lower bound)
B = sqrt(P_upper) (sqrt of the range upper bound)
L = liquidity

Range states:
  current_tick < tick_lower:
    amount0 = L * (1/A - 1/B)
    amount1 = 0
  
  tick_lower <= current_tick < tick_upper:
    amount0 = L * (1/S - 1/B) = L * (B - S) / (S * B)
    amount1 = L * (S - A)
  
  current_tick >= tick_upper:
    amount0 = 0
    amount1 = L * (B - A)
```

### 6.3 Data Sources

```yaml
Static data (saved at LP open / rebalance):
  NonfungiblePositionManager.positions(tokenId):
    - token0
    - token1
    - fee
    - tickLower
    - tickUpper
    - liquidity (re-readable)
  
  Pool:
    - poolAddress
    - token0
    - token1
    - fee
  
  ERC20:
    - token0_decimals
    - token1_decimals

Dynamic data (from MarketDataDO):
  Pool.slot0:
    - sqrtPriceX96
    - currentTick
    - blockNumber
    - updatedAt
```

### 6.4 PositionAmountCalculator Interface

```typescript
export type PositionAmountResult = {
  positionId: string;
  token0: Address;
  token1: Address;
  wethIndex: 0 | 1;
  currentTick: number;
  tickLower: number;
  tickUpper: number;
  sqrtPriceX96: string;
  amount0Raw: string;
  amount1Raw: string;
  amount0Human: string;
  amount1Human: string;
  lpEthAmount: string;
  rangeState: "below" | "in" | "above";
};

async function calculatePositionAmount(
  position: PositionStatic,
  market: PoolMarketState,
): Promise<PositionAmountResult> {
  const sqrtA = TickMath.getSqrtRatioAtTick(position.tickLower);
  const sqrtB = TickMath.getSqrtRatioAtTick(position.tickUpper);
  
  const [amount0Raw, amount1Raw] = LiquidityAmounts.getAmountsForLiquidity(
    BigInt(market.sqrtPriceX96),
    sqrtA,
    sqrtB,
    BigInt(position.liquidity),
  );
  
  const amount0Human = formatUnits(amount0Raw, position.token0Decimals);
  const amount1Human = formatUnits(amount1Raw, position.token1Decimals);
  const lpEthAmount = position.wethIndex === 0 ? amount0Human : amount1Human;
  
  const rangeState =
    market.currentTick < position.tickLower ? "below" :
    market.currentTick >= position.tickUpper ? "above" :
    "in";
  
  return {
    positionId: position.id,
    token0: position.token0,
    token1: position.token1,
    wethIndex: position.wethIndex,
    currentTick: market.currentTick,
    tickLower: position.tickLower,
    tickUpper: position.tickUpper,
    sqrtPriceX96: market.sqrtPriceX96,
    amount0Raw: amount0Raw.toString(),
    amount1Raw: amount1Raw.toString(),
    amount0Human,
    amount1Human,
    lpEthAmount,
    rangeState,
  };
}
```

### 6.5 Required Test Cases

```yaml
test_cases:
  - in range: amount0 > 0, amount1 > 0
  - below lower: amount0 = full, amount1 = 0
  - above upper: amount0 = 0, amount1 = full
  - WETH is token0
  - WETH is token1
  - negative tick (low ETH price)
  - zero liquidity
  - very small liquidity (precision)
  - decimals 18 (WETH) / 6 (USDC)
  - currentTick == tickLower (boundary)
  - currentTick == tickUpper (boundary)
  - currentTick == tickLower - 1 (just outside)
  - currentTick == tickUpper - 1 (just inside upper)
```

---

## 7. Hedge Math

### 7.1 Target Short Calculation

```typescript
// conceptual formula:
targetShortEth = lpEthAmount × hedgeRatio
```

🚨 v5.2.1 (P0-6): the implementation does not go through float. Normalize `hedgeRatio` as a bps integer
(`target_ratio_bps`) and compute ETH amounts in BigDecimal.
For the canonical rule and the normalization function see **§7.6** (unified with §13.4 / §15.3 / §17).

### 7.2 Hedge Ratio Modes (Phase 1)

```yaml
Phase 1: Balanced 70% fixed (simplified)

Considered for addition in Phase 2 (Defer):
  Conservative: hedgeRatio = 0.50
  Balanced:     hedgeRatio = 0.70 (default)
  Aggressive:   disabled in Phase 1-2 (considered in Phase 3)
```

### 7.3 Rebalance Trigger

> 🆕 v5.2.6 (D-4, QA CC i-1): this section is the conceptual formula. **The canonical implementation is §17.1** light-check.
> If this section and §17.1 disagree, §17.1 takes precedence (to prevent dual-implementation divergence).

```typescript
// 🚨 v5.2.1 (P0-6): compute in BigDecimal. Raw Math.abs / JS float arithmetic is forbidden.
const deltaErrorEth = BigDecimal(targetShortEth).sub(lastKnownShortEth).abs();
const deltaErrorUsd = deltaErrorEth.mul(uniPoolPrice); // 🆕 X-5: LP drift valuation uses uniPoolPrice (§15.1 3-way split)
const lpValueUsd = BigDecimal(/* bot_runtime_state.lp_value_usd */);
const relativeDrift =
  BigDecimal(targetShortEth).gt(minSizeEth)
    ? deltaErrorEth.div(targetShortEth)
    : BigDecimal(0);

// 🚨 v5.2.1 (P0-11): the rebalance reason is unified to the §7.6 canonical RebalanceReason.
//   §5.3 / §13.4 / §17.1 all reference this set (do not create aliases / alternate sets).
const reasons: RebalanceReason[] = [];
// 🚨 v5.2.2 (P0-1): going through float is forbidden. Unify toNumber()/Math.max to BigDecimal comparison.
//   Keep constants as strings via BigDecimal('...').
const driftThreshold = BigDecimal.max(BigDecimal('25'), lpValueUsd.mul('0.03'));
if (deltaErrorUsd.gt(driftThreshold))                             reasons.push('drift_threshold');
if (relativeDrift.gt(BigDecimal('0.15')))                         reasons.push('drift_relative');
if (rangeOut)                                                     reasons.push('range_out');
if (rangeBoundaryNear)                                            reasons.push('range_boundary_near'); // 90% to upper/lower
if (marginStatus === 'warning')                                   reasons.push('margin_warning');
if (fundingAlert)                                                 reasons.push('funding_alert');       // 7d funding < -15% APR
if (timeFallback)                                                 reasons.push('time_fallback');       // 4h since last adjustment
const shouldRebalance = reasons.length > 0;

// stopTriggerCrossed / near-stop is not a normal hedge-sync reason.
// route only to priority stop-audit/reconcile (Section 19.3 / §17.1).
// margin_critical routes to the §18.4.3 SAFE_MODE path (not emitted by hedge-sync).
```

```yaml
relative drift:
  Use:
    abs(targetShort - actualShort) / targetShort
  If targetShort <= minSize:
    relativeDrift = 0
  Do not use:
    abs(targetShort - actualShort) / initialHedgeEth
```

### 7.4 The judgment difference between Light-check and Hedge-sync

```yaml
light-check:
  source: lastKnownShortEth from D1 (cached)
  purpose: drift judgment only
  HL fetch: none
  
hedge-sync:
  source: actual HL position (fresh fetch)
  purpose: execute delta-only mutation (see Section 17)
  HL fetch: yes
  
success record:
  not created in light-check
  created only after hedge-sync post-order reconcile
```

### 7.5 Hedge Budget Cap

```yaml
Hedge cost ≤ trailing 7d LP fee × 30%

Cold start (first 7d):
  budget = expected_LP_fee_APR × LP_capital × 7d × 30%
  example: 30% × $850 × (7/365) × 30% = $1.47/week

After 7d:
  budget = realized_trailing_7d_fee × 30%

🚨 v5.2.6 (C-4, QA Codex M-4 / decision ②): on overflow, instead of "lowering the hedge ratio",
  **scale down LP and hedge at the same ratio** (drop only the size while keeping delta-neutrality).
  Do not change the hedge ratio (target_ratio).
  L1 proportional scale-down ladder (current size → 50% → 25% = system_config: l1_steps "100,50,25"):
    - each step = execute decreaseLiquidity (LP) + short reduction (HL) in the **same adjustment cycle**
      (scale LP/HL by the same ratio. do not break delta by scaling only one side)
    - step firing: while the trailing 7d budget overflow continues, lower by one step at a time

  🚨 v5.2.6 (X-4) idempotency (structurally prevent applying twice on queue redelivery):
    - hold the step in hedge_legs.scale_step_pct (§13.2) as an **absolute value** (100/50/25).
    - scale down/up is an idempotent operation applying "the target step's absolute value". If the current scale_step_pct
      and the target are the same, **no-op** (apply by target, not diff = prevent double application).
    - take scale_baseline_lp_usd (the full size when entering L1) as the invariant base, and
      each step targets baseline × (scale_step_pct/100).
    - update last_scale_change_at on step change. set budget_breach_since when the budget overflow starts.

  Re-expansion policy (🆕 v5.2.6 X-4 / Y-4, design decision = allowed. **AND of 3 conditions**):
    ① 7d funding APR > reentry_funding_apr_floor (-15%, shared with system_config)
    ② at least scale_up_min_hold_hours (=24h, §13.12) elapsed since last_scale_change_at
    ③ 🆕 v5.2.6 (Y-4): **the 7d estimated hedge cost recomputed at the next step's (one up) size**
       fits within budget (= 30% of trailing 7d LP fee income)
    - when the above ①∧②∧③ are satisfied, raise by **only 1 step** per judgment (25 → 50 → 100).
      update scale_step_pct and last_scale_change_at at each step.
    - 🆕 v5.2.6 (Y-4) change the budget_breach_since reset condition:
        reset not "when re-expansion happens" but "**when the 7d hedge cost at the current step is back within budget**".
        While the overflow continues, do not stop the breach clock even if the step goes up
        (to maintain L2-judgment continuity).

  L2 (evacuation):
    - scale_step_pct=25 and **7 days continuous** from budget_breach_since → L2 = bot_safe_close
      (§16.4 B) → to the §16.7 cooldown closed loop.

  Immediate alert (preemptive scale-down without waiting for the 7d metric):
    - if 24h funding annualized < -40% (system_config: funding_24h_apr_immediate_l1),
      immediately lower L1 by one step (following the idempotency rule above)
  Phase A trailing 7d source (🆕 C-4 / CC m-6):
    - 7d funding APR is aggregated from the latest 7 rows of funding_daily_metrics
      (funding_rolling_metrics is Phase B+. §13.6)
  notification: notify the user on each step's scale-down / re-expansion / L2 evacuation (acknowledge only)
```

### 7.6 Canonical: RebalanceReason enum + target_ratio bps rule (🆕 v5.2.1 / P0-6 + P0-11)

```typescript
// 🚨 CANONICAL rebalance reason enum (P0-11)
// §5.3 / §7.3 / §13.4 / §17.1 all reference only this type.
// Do not create aliases / alternate sets (custom expressions like trigger / cause / reason).
type RebalanceReason =
  | 'drift_threshold'      // deltaErrorUsd > max($25, lpValueUsd * 3%)
  | 'drift_relative'       // |target - actual| / target > 0.15
  | 'range_out'            // rangeState != 'in'
  | 'range_boundary_near'  // price 90% to range upper/lower
  | 'margin_warning'       // hedge_legs.margin_status == 'warning' (§18.4)
  | 'margin_critical'      // §18.4.3 SAFE_MODE path only (not emitted by hedge-sync)
  | 'funding_alert'        // 7d funding < -15% APR
  | 'time_fallback'        // 4h since last adjustment
  | 'manual_admin'         // admin invoked
  | 'recovery_reconcile';  // reconcile/repair flow

// Note: stop_trigger_crossed / near-stop is not a RebalanceReason.
//     route to priority stop-audit (§19.3 / §17.1).
```

```typescript
// 🚨 CANONICAL target_ratio implementation rule (P0-6)
// D1 schema: hedge_legs.target_ratio TEXT '0.7' is kept for display/backward compat.
// internal computation must always normalize to a bps integer (bigint); going through float is forbidden.
//   0.70 -> 7000n,  0.50 -> 5000n,  1.00 -> 10000n
function normalizeTargetRatioBps(targetRatioText: string): bigint {
  // turn the string "0.70" into a 10^4-scale integer. Number(x) * 10000 is forbidden
  // (because float error like 0.73 * 10000 = 7300.0000001 makes BigInt() throw).
  const [intPart, fracRaw = ''] = targetRatioText.trim().split('.');
  const frac = (fracRaw + '0000').slice(0, 4);          // padding/truncate to 4 digits (bps)
  const bps = BigInt(intPart) * 10000n + BigInt(frac);
  if (bps < 0n || bps > 10000n) throw new Error(`invalid target_ratio: ${targetRatioText}`);
  return bps;                                            // e.g. "0.70" -> 7000n
}

// Usage example (matches §17.1 / §17.2):
//   const targetRatioBps = normalizeTargetRatioBps(data.hedge.targetRatio);
//   const targetShort = BigDecimal(amount.lpEthAmount).mul(targetRatioBps).div(10000);
```

```yaml
If adding hedge ratio modes in Phase 2 (Defer):
  - ALTER ADD a target_ratio_bps INTEGER to D1 (Section 13.0 principle: ADD only)
  - keep target_ratio TEXT for display/backward compat (do not DROP/RENAME)
  - all normalization goes through normalizeTargetRatioBps() (never create any float path)
```

---

## 8. Hyperliquid Adapter

### 8.1 Adapter Responsibility

HyperliquidAdapter is not a thin wrapper. It owns the following:

```yaml
Responsibilities:
  - HL rate limit reservation
  - Agent key decryption (see Section 21.5)
  - Order payload creation
  - Cloid generation (deterministic)
  - Nested error parsing
  - Order submission
  - Post-order reconciliation
  - Error classification
  - Safe logging (sanitize private key etc., see Section 21.5)
  - 🆕 (v5.1) Delta-only adjustment helper (see Section 17)
```

### 8.2 Interface

```typescript
export interface HyperliquidAdapter {
  // Read operations
  getPositions(account: HlAccountRef): Promise<HlPosition[]>;
  getPosition(account: HlAccountRef, asset: string): Promise<HlPosition | null>;
  getOpenOrders(account: HlAccountRef): Promise<HlOpenOrder[]>;
  getUserFunding(account: HlAccountRef, startTime?: number, endTime?: number): Promise<HlFundingEntry[]>;
  getUserRateLimit(userAddress: Address): Promise<HlUserRateLimit>;
  getMarginSummary(account: HlAccountRef): Promise<HlMarginSummary>;  // 🆕 (v5.1)
  
  // Mutations (delta-only adjustment helper added in Section 17)
  placeIocOrder(input: PlaceIocOrderInput): Promise<HlOrderResult>;
  openShortIoc(input: OpenShortInput): Promise<HlOrderResult>;
  closeShortReduceOnlyIoc(input: CloseShortInput): Promise<HlOrderResult | null>;
  adjustShortDelta(input: AdjustShortDeltaInput): Promise<HlOrderResult>;  // 🆕 (v5.1)
  placeReduceOnlyStopMarket(input: PlaceStopMarketInput): Promise<HlOrderResult>;
  cancelByOid(account: HlAccountRef, assetIndex: number, oid: number): Promise<void>;
  cancelByCloid(account: HlAccountRef, assetIndex: number, cloid: `0x${string}`): Promise<void>;
  updateLeverage(account: HlAccountRef, assetIndex: number, leverage: number, isCross: boolean): Promise<void>;
  updateIsolatedMargin(account: HlAccountRef, assetIndex: number, isBuy: boolean, ntli: number): Promise<void>;
  
  // Reconcile
  reconcilePosition(account: HlAccountRef, asset: string, expectedAbsSize: string): Promise<ReconcileResult>;
}
```

### 8.3 Account Reference

```typescript
export type HlAccountRef = {
  userAddress: Address;        // master account (NOT agent address)
  agentKeyId: string;          // encrypted approved agent key reference (Section 21.5)
  vaultAddress?: Address | null; // subaccount/vault if applicable
};
```

```yaml
🚨 Critical:
  - userAddress is the master account's address
  - using the agent address as userAddress makes info queries empty (HL spec)
  - if it has a vaultAddress, operate the subaccount by specifying vaultAddress at order time
  - 🆕 (v5.1) BNZA never stores the user's master private key (Section 21.5)
  - 🆕 (v5.1) the agent key is stored in D1 (hl_agent_keys) with envelope encryption
```

### 8.4 Native Stop Implementation

```typescript
await exchange.order({
  orders: [{
    a: ethAssetIndex,      // ETH's asset index
    b: true,                // buy = close short
    p: orderPx,             // fallback/aggressive price (slippage tolerance)
    s: size,                // close size
    r: true,                // reduce-only
    t: {
      trigger: {
        isMarket: true,
        triggerPx: stopTriggerPx,  // 🆕 (v5.1) dynamically computed based on liquidationPx (Section 19)
        tpsl: "sl",                // Stop Loss
      },
    },
    c: cloid,               // deterministic client order id
  }],
  grouping: "na",
  vaultAddress: account.vaultAddress ?? undefined,
});
```

### 8.5 Cloid Generation (Idempotency)

```typescript
function makeCloid(input: {
  botId: string;
  attemptId: string;
  stage: "close" | "open" | "stop" | "cancel" | "adjust";  // 🆕 (v5.1) "adjust"
  version: number;
}): `0x${string}` {
  return first128BitsHex(
    keccak256(`bnza:${input.botId}:${input.attemptId}:${input.stage}:${input.version}`)
  );
}

Rules:
  same retry: same cloid
  payload changed: increment version
  duplicate cloid detected: do not blindly retry, reconcile first
```

### 8.6 Nested Error Parser

The HL SDK can include an error in a nested status even when `status: "ok"`.

```typescript
export function parseOrderResponse(result: any): HlOrderResult[] {
  const statuses = result?.response?.data?.statuses ?? [];
  const errors = statuses
    .map((s: any) => typeof s === "object" ? s.error : undefined)
    .filter(Boolean);
  
  if (errors.length > 0) {
    throw new HlOrderRejectedError(errors.join("; "), {
      errors,
      raw: sanitize(result),  // exclude private key / nonce / secret (Section 21.5)
    });
  }
  
  return statuses.map(parseStatus);
}
```

---

## 9. Hyperliquid Rate Limiting

### 9.1 Rate Limit Policy

```yaml
HLGlobalRateLimitDO:
  official hard limit: 1,200 weight/min/IP
  BNZA operating budget: 700-800 weight/min (🆕 v5.2.6 D-5 correction: 33% margin / 800÷1,200 = 67% used)
  excess handling: queue + delay

HLUserRateLimitDO:
  per-user/address action budget
  informed by userRateLimit endpoint
  
UserLockDO:
  same-user mutation serialization (lease-based, Section 11)
```

### 9.2 API Class & Usage

```yaml
info.position (clearinghouseState):
  weight: 2
  use only for:
    - mutation candidate (just before hedge-sync)
    - post-order reconcile
    - deep audit
    - priority audit when the stop_trigger_crossed marker is set (v5.1)
  forbidden:
    - polling all bots every 5 min

info.history (funding/fills):
  low frequency only
  daily aggregation recommended

info.marginSummary:
  - preflight margin check (Section 18.4)
  - margin warning / critical evaluation
  - SAFE_MODE entry judgment

exchange.order:
  mutation only
  rate limit reservation required
  delta-only adjustment is the default (Section 17)

light-check:
  weight: 0 (does not touch HL)
```

### 9.3 Forbidden at Scale

```yaml
🚨 Forbidden to run the following for all bots / every 5 min:
  - clearinghouseState
  - openOrders
  - userFunding
  - userRateLimit
  - stop cancel/recreate (recreating every light-check is wasteful)
```

---

## 10. Queue Architecture

### 10.1 Queue List

```yaml
bot-scan:
  purpose: shard/window scan
  producer: cron worker (1 min)
  consumer: scan worker
  message: { shardId, cursor, limit, now }

light-check:
  purpose: 1 message = 1 bot light check
  producer: scan worker
  consumer: light-check worker
  message: { botId, userId, shardId }

hedge-sync:
  purpose: delta-only mutation candidate
  producer: light-check worker
  consumer: hedge-sync worker
  message: { botId, reasons: RebalanceReason[], expectedTargetSize, stateVersion }
    // 🚨 v5.2.3 (P1-B): unified to RebalanceReason[] (canonical, §7.6).
    //   the old reason (a singular string) is not used.
    //   the producer §17.1 emits the canonical array, ensuring consistency.

reconcile:
  purpose: post-order reconciliation
  producer: hedge-sync worker
  consumer: reconcile worker
  message: { botId, attemptId, expectedAbsSize, hedgeLegId }

deep-audit:
  purpose: distributed full audit
  producer: cron worker (6h)
  consumer: deep-audit worker
  message: { botId, urgency }

price-near-stop-audit:
  purpose: stop/range boundary priority audit
  producer: light-check worker (price near stop / >= stop detected)
  consumer: stop-audit worker
  message: { botId, markPriceUsd, stopPriceUsd, crossed, staleMark? }  # 🆕 X-5: unify the price field to markPriceUsd (stop judgment=hlMarkPrice; on stale, uniPool fallback + staleMark)

partial_repair:                  # 🆕 v5.2.6 (B-4 / W-3 / V-1)
  purpose: partial reconcile / after stop replacement failure / after STOP_REPLACING overrun repair (priority)
  producer: hedge-sync worker (§17.2 B-4 on partial detection / §19.5 after stop restore / §17.1 W-5 after overrun detection)
  consumer: partial-repair worker
  message: { botId, hedgeLegId, attemptId: string | null, expectedSize, actualSize,
             reason: 'partial_reconcile' | 'stop_replace_failed_restored' | 'stop_replacing_overrun' }
             # 🆕 V-1: reason is 3 values / attemptId is nullable because of the crash path (stop_replacing_overrun)
  consumer branch (🆕 W-3 / V-1):
    - reason='partial_reconcile'            → size re-adjustment (existing handling, §17.2 B-4)
    - reason='stop_replace_failed_restored' → re-place the stop for the current position size
        via §19.5 replaceStopProtected (direct cancel/place is an INV-STOP violation)
    - reason='stop_replacing_overrun'       → reconcile the actual HL position to determine the size, then
        re-place the stop for that size via §19.5 replaceStopProtected
        (the same repair action as stop_replace_failed_restored, only the cause label differs)
  note: SAFE_MODE after 3 failures (§17.2 B-4)

user_redeem:                     # 🆕 v5.2.6 (B-2 / X-2) highest priority
  purpose: hedge close for a user's instant redemption (triggered by a redeem event). SLA 5 min from detection
  producer: redeem event watcher (the LP is already liquidated by the redeem tx; the LP-portion USDC is already returned in the same tx)
  consumer: redeem worker (LP-first: redeem tx already complete → close the hedge immediately → send the HL-portion USDC, §16.4 A)
  message: { botId, redeemTxHash, userAddress }
  note: LP repayment is already done by the redeem tx. This queue handles hedge close only (X-2, does not depend on LP)

notification:
  purpose: user/admin alert
  producer: any worker
  consumer: notification worker

metrics-rollup:
  purpose: hourly/daily aggregation
  producer: cron worker (hourly)
  consumer: rollup worker

dead-letter:
  purpose: poison messages
  producer: any queue
  consumer: admin review
```

```yaml
🚨 v5.2.6 (B-6) consumer idempotency protocol (common to all queues):
  - every consumer INSERTs message_id with state='started' into queue_idempotency at the start of
    processing. UNIQUE conflict = duplicate delivery → return immediately (structurally prevents double execution, §13.8).
  - on completion update state='succeeded' / on failure update to 'failed'|'retryable'.
  - derive the cloid from the queue message's deterministic ID, not from a "re-fetched state"
    (§8.5. forbid creating a new attempt from a re-fetched state).
  - reconcile / partial_repair are designed idempotently so they can no-op by looking at terminal state.
  - responsibility separation: UserLockDO lease (§11) = mutual exclusion of a single user's mutations / queue_idempotency
    (§13.8) = idempotency of a single message. The two are separate layers.
```

### 10.2 Cron Worker

```typescript
// 🚨 v5.2.2 (P0-4): common chunking helper. Cloudflare Queues sendBatch is
//   max 100 per call. All producers in this SPEC go through this helper
//   (§10.2 cron / §10.3 scan / deep-audit / notification etc., no exceptions).
const SEND_BATCH_MAX = 100; // Cloudflare Queues hard limit per sendBatch

async function chunkSendBatch<T>(
  queue: Queue<T>,
  messages: { body: T }[],
): Promise<void> {
  for (let i = 0; i < messages.length; i += SEND_BATCH_MAX) {
    await queue.sendBatch(messages.slice(i, i + SEND_BATCH_MAX));
  }
}

export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    const shardWindows = dueShardWindows(Date.now());

    const messages = shardWindows.map((w) => ({
      body: {
        shardId: w.shardId,
        cursor: w.cursor,
        limit: 500,
        now: Date.now(),
      },
    }));

    await chunkSendBatch(env.BOT_SCAN_QUEUE, messages); // via the §10.2 common helper
  },
};
```

### 10.3 Scan Worker

```typescript
async function scanDueBots(msg: BotScanMessage, env: Env) {
  const db = shardDb(env, msg.shardId);
  
  const bots = await db.prepare(`
    SELECT id, user_id, shard_id
    FROM bots
    WHERE status = 'active'
      AND next_light_check_at <= ?
    ORDER BY next_light_check_at
    LIMIT ?
  `).bind(nowIso(), msg.limit).all();
  
  // 🚨 v5.2.1 (P0-3) / v5.2.2 (P0-4): go through the common helper chunkSendBatch (defined in §10.2).
  //   even passing the scan limit (msg.limit, e.g. 500) as-is, the helper sends in chunks of 100.
  const messages = bots.results.map((bot) => ({
    body: { botId: bot.id, userId: bot.user_id, shardId: bot.shard_id },
  }));
  await chunkSendBatch(env.LIGHT_CHECK_QUEUE, messages); // via the §10.2 common helper

  await jitterNextCheckForBots(db, bots.results);
}
```

```yaml
🚨 v5.2.1 (P0-3) / v5.2.2 (P0-4) sendBatch chunking rule:
  - the scan SELECT LIMIT (msg.limit) may stay at 500
  - but every *.sendBatch() must go through the §10.2 common helper chunkSendBatch()
    (SEND_BATCH_MAX=100). Directly calling raw queue.sendBatch() is forbidden
  - scope: cron worker (§10.2), scan worker (§10.3), deep-audit producer,
    notification producer, metrics-rollup producer, i.e. all producers (no exceptions)
  - consistent with §5.2-5 "Batch size: max 100"
```

### 10.4 Jitter Strategy

```typescript
next_light_check_at = now + 5m + random(-45s, +45s)

Reason:
  prevent all bots from clustering at 00:00, 00:05, ...
  ease HL rate limit / D1 write spikes
```

---

## 11. User-Level Concurrency Control (implementation model changed in v5.1)

### 11.1 Required Invariant

```yaml
Do not run the same user's Hyperliquid mutations concurrently.
Reason:
  - HL nonce is monotonically increasing
  - parallel mutations cause nonce collision
  - Rate limit is shared

🚨 v5.2.6 (B-6) responsibility separation: the UserLockDO lease handles "mutual exclusion of a single user's mutations".
  "absorbing duplicate delivery of the same message (idempotency)" is handled by the queue_idempotency ledger (§13.8).
  The two are separate layers, and either one alone is insufficient (exclusion ≠ idempotency).
```

### 11.2 Implementation: UserLockDO (Lease-based, rewritten in v5.1)

```yaml
🚨 v5.1 fix:
  v5.0's "function-callback approach" (passing work() to the DO to execute) cannot be
  directly implemented given Cloudflare Durable Object RPC design
  (function objects cannot be passed cross-DO).
  v5.1 changes to a lease-based lock pattern.

Design policy:
  - the DO provides only the acquire / release / heartbeat API
  - the caller (hedge-sync worker) acquires a lease, runs the work itself, and
    calls release on completion
  - the Lease carries a TTL (90s) and a holderToken (UUID)
  - a release whose holderToken does not match is a noop / error
  - after the TTL expires, another holder can acquire (stale lock auto-release)
```

```typescript
// Durable Object: UserLockDO:userId
// Single-threaded per instance

export type LeaseAcquireInput = {
  holderToken: string;       // UUID v4 (caller-generated)
  ttlMs: number;             // recommended: 90_000
  idempotencyKey?: string;   // optional, for replay-safe behaviors
};

export type LeaseAcquireResult =
  | { acquired: true; expiresAt: number; idempotentReplay: false }
  | { acquired: false; currentHolderExpiresAt: number; reason: "held" }
  | { acquired: true; expiresAt: number; idempotentReplay: true; cachedResult?: unknown };

export class UserLockDO {
  // Acquire (or replay) a lease.
  async acquire(input: LeaseAcquireInput): Promise<LeaseAcquireResult> {
    const now = Date.now();

    // 1. Idempotency replay check (cached results from prior completed work)
    if (input.idempotencyKey) {
      const cached = await this.state.storage.get<{ result: unknown; recordedAt: number }>(
        `idem:${input.idempotencyKey}`,
      );
      if (cached) {
        return {
          acquired: true,
          expiresAt: now,             // already finished — no new lease needed
          idempotentReplay: true,
          cachedResult: cached.result,
        };
      }
    }

    // 2. Existing lease check
    const existing = await this.state.storage.get<{ holderToken: string; expiresAt: number }>("lease");
    if (existing && existing.expiresAt > now && existing.holderToken !== input.holderToken) {
      return { acquired: false, currentHolderExpiresAt: existing.expiresAt, reason: "held" };
    }

    // 3. Acquire (fresh or re-acquire by same holder)
    const expiresAt = now + input.ttlMs;
    await this.state.storage.put("lease", { holderToken: input.holderToken, expiresAt });
    return { acquired: true, expiresAt, idempotentReplay: false };
  }

  // Heartbeat to extend the lease while still holding it
  async heartbeat(input: { holderToken: string; ttlMs: number }): Promise<{ ok: boolean; expiresAt?: number }> {
    const existing = await this.state.storage.get<{ holderToken: string; expiresAt: number }>("lease");
    if (!existing || existing.holderToken !== input.holderToken) return { ok: false };
    const expiresAt = Date.now() + input.ttlMs;
    await this.state.storage.put("lease", { holderToken: input.holderToken, expiresAt });
    return { ok: true, expiresAt };
  }

  // Release. holderToken mismatch is a noop (stale releaser).
  // If idempotencyKey provided, cache the result for replay-safe behavior.
  async release(input: { holderToken: string; idempotencyKey?: string; result?: unknown }): Promise<{ released: boolean }> {
    const existing = await this.state.storage.get<{ holderToken: string; expiresAt: number }>("lease");
    if (!existing || existing.holderToken !== input.holderToken) {
      return { released: false };
    }
    await this.state.storage.delete("lease");
    if (input.idempotencyKey) {
      await this.state.storage.put(`idem:${input.idempotencyKey}`, {
        result: input.result ?? null,
        recordedAt: Date.now(),
      });
      // optional: delete after 24-72h via alarm()
    }
    return { released: true };
  }
}
```

### 11.3 Caller-side Usage (acquire / release pattern)

```typescript
import { randomUUID } from "node:crypto";

async function withUserLock<T>(args: {
  userId: string;
  ttlMs: number;
  idempotencyKey?: string;
  work: () => Promise<T>;
  env: Env;
}): Promise<T> {
  const stub = args.env.USER_LOCK_DO.get(args.env.USER_LOCK_DO.idFromName(args.userId));
  const holderToken = randomUUID();

  // 1. acquire
  const acq = await stub.fetch("/acquire", {
    method: "POST",
    body: JSON.stringify({ holderToken, ttlMs: args.ttlMs, idempotencyKey: args.idempotencyKey }),
  }).then(r => r.json() as Promise<LeaseAcquireResult>);

  if ("idempotentReplay" in acq && acq.idempotentReplay) {
    return acq.cachedResult as T;  // already executed, replay cached result
  }
  if (!acq.acquired) {
    throw new UserLockHeldError(args.userId, acq.currentHolderExpiresAt);
  }

  // 2. execute work in caller (NOT inside DO)
  let result: T;
  try {
    result = await args.work();
  } catch (e) {
    // best-effort release on failure (no idempotency cache needed)
    await stub.fetch("/release", {
      method: "POST",
      body: JSON.stringify({ holderToken }),
    });
    throw e;
  }

  // 3. release with optional idempotency caching
  await stub.fetch("/release", {
    method: "POST",
    body: JSON.stringify({ holderToken, idempotencyKey: args.idempotencyKey, result }),
  });

  return result;
}

// Usage at hedge-sync worker
const result = await withUserLock({
  env,
  userId: data.user.id,
  ttlMs: 90_000,
  idempotencyKey: `hedge-sync:${botId}:${stateVersion}`,
  work: async () => await hedgeSyncInner(data, reasons),
});
```

```yaml
🚨 Notes:
  - the holderToken is generated by the caller (UUID v4)
  - after acquiring the lease, if work does not complete within 30s wall time, extend with heartbeat()
  - if the Worker times out during work(), the lease is auto-released after the TTL expires
  - idempotencyKey prevents duplicate execution of the same stateVersion
  - by caching the result on release(), a duplicate call can replay it

reconcile after a lock holder crash:
  - lease expires automatically
  - next worker must not assume previous operation succeeded
  - next worker must fetch and reconcile actual Hyperliquid state before any mutation
  - if state mismatch is detected, enter SAFE_MODE or run repair flow
```

---

## 12. D1 Architecture

### 12.1 Database Layout

```yaml
control_db (1):
  - users
  - bot_registry
  - shard_registry
  - billing
  - global config
  - hl_agent_keys (🆕 v5.1, see Section 13.9 / 21.5)

state_db_shard_xx (per phase):
  Phase A: 1 shard
  Phase B: 4 shards
  Phase C: 16 shards (Defer to Phase C)
  Phase D: 32 shards
  
  tables:
  - bots
  - positions
  - hedge_legs
  - bot_runtime_state
  - circuit_breakers
  - rebalance_attempts
  - hourly_bot_metrics
  - daily_bot_metrics
  - funding_daily_metrics (🆕 v5.1, simplified per phase, Section 13.6)
  - queue_idempotency

archive (R2, Phase B+):
  - raw logs
  - old rebalance_attempts (>90d)
  - raw HL/RPC response samples
  - JSONL gzip by day/shard

observability (Analytics Engine, Phase B+):
  - queue lag
  - worker latency
  - error counters (low cardinality only)
  - RPC cache hit rate
  - HL token usage
  - D1 shard latency
  ❌ do not use bot_id / user_id as a dimension (Section 14.3)
```

### 12.2 Shard Plan

```yaml
Phase A (1-100 bot):     1 shard
Phase B (1,000 bot):     4 shards
Phase C (10,000 bot):    16 shards (Defer until Phase B is stable)
Phase D (10,000+ bot):   32 shards (resharding)

shard_id = hash(bot_id) % shard_count

Reason:
  - bot_id based (not user_id)
  - handles skew in the number of bots per user
  - the user-level lock is implemented separately in a DO (lease-based)
```

---

## 13. D1 Schema (ALTER TABLE additions in v5.1 — DROP forbidden)

### 13.0 Schema change principles (v5.1)

```yaml
🚨 Principles:
  - keep the CREATE TABLE defined in v5.0
  - add fields needed in v5.1 via ALTER TABLE ADD COLUMN
  - DROP / RENAME of existing columns is forbidden (post-implementation migration compatibility)
  - new tables (hl_agent_keys, funding_daily_metrics) are added via CREATE TABLE
  - if a PRIMARY KEY change is needed (circuit_breakers), do a new table + view migration
    (this spec includes the DDL example in Section 13.7)
```

### 13.1 Control DB

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  wallet_address TEXT,
  hl_user_address TEXT,
  hl_agent_key_id TEXT,         -- references hl_agent_keys.id (v5.1)
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE bot_registry (
  bot_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  shard_id INTEGER NOT NULL,
  status TEXT NOT NULL,          -- active, paused, closing, closed, safe_mode, error
  chain TEXT NOT NULL,           -- 'base' | 'optimism'
  bot_type TEXT NOT NULL,        -- 'lp' | 'ex'
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_bot_registry_user ON bot_registry(user_id);
CREATE INDEX idx_bot_registry_shard_status ON bot_registry(shard_id, status);

CREATE TABLE shard_registry (
  shard_id INTEGER PRIMARY KEY,
  db_binding_name TEXT NOT NULL,
  status TEXT NOT NULL,           -- active, draining, readonly
  bot_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
```

### 13.2 State Shard DB

```sql
CREATE TABLE bots (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  status TEXT NOT NULL,           -- coarse-grained: active, paused, closing, closed, safe_mode, error
  -- 🆕 v5.2.1 (P0-8): fine-grained lifecycle. Expresses the §16.1/§16.6 state machine.
  --   status stays coarse-grained; the state machine transitions are tracked in lifecycle_state.
  -- 🚨 v5.2.6 (B-5): the canonical persisted strings are this enum. The §16.1 flow diagram,
  --   §16.1 mapping table, and all pseudocode use only these words (the old uppercase aliases
  --   hedge_pre_open / hedge_post_confirmed are forbidden). Added hedge_stopped_cooldown / cooldown / parked (A-4 / B-2).
  --   values: idle | preflight | lp_opening | lp_opened | hedge_pre_open |
  --       hedge_post_confirmed | stop_placing | stop_verified | active |
  --       lp_rebalancing | lp_closing | closed | safe_mode | error |
  --       hedge_stopped_cooldown | cooldown | parked
  lifecycle_state TEXT NOT NULL DEFAULT 'idle',
  chain TEXT NOT NULL,
  wallet_address TEXT NOT NULL,
  position_id TEXT NOT NULL,
  hedge_leg_id TEXT NOT NULL,
  next_light_check_at TEXT NOT NULL,
  next_deep_audit_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
-- v5.2.1 ALTER (for existing environments; for a new DB the CREATE TABLE above is fine)
-- ALTER TABLE bots ADD COLUMN lifecycle_state TEXT NOT NULL DEFAULT 'idle';
CREATE INDEX idx_bots_due_light ON bots(status, next_light_check_at);
CREATE INDEX idx_bots_due_audit ON bots(status, next_deep_audit_at);
CREATE INDEX idx_bots_user ON bots(user_id);
CREATE INDEX idx_bots_lifecycle ON bots(lifecycle_state);

CREATE TABLE positions (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL UNIQUE,
  token_id TEXT NOT NULL,         -- Uniswap V3 NFT token id
  pool_address TEXT NOT NULL,
  token0 TEXT NOT NULL,
  token1 TEXT NOT NULL,
  fee INTEGER NOT NULL,
  tick_lower INTEGER NOT NULL,
  tick_upper INTEGER NOT NULL,
  liquidity TEXT NOT NULL,        -- BigInt string
  weth_index INTEGER NOT NULL,    -- 0 or 1
  token0_decimals INTEGER NOT NULL,
  token1_decimals INTEGER NOT NULL,
  -- 🆕 v5.1: LP NFT custody (see Section 15.5)
  custodian TEXT NOT NULL DEFAULT 'vault',   -- 'vault' | 'user' (EXBOT Phase A is fixed to 'vault', v5.2.1)
  custodian_address TEXT NOT NULL,           -- BnzaExVault address (per chain)
  updated_at TEXT NOT NULL
);

-- v5.1 ALTER (for existing environments; for a new DB the CREATE TABLE above is fine)
-- ALTER TABLE positions ADD COLUMN custodian TEXT NOT NULL DEFAULT 'vault';
-- ALTER TABLE positions ADD COLUMN custodian_address TEXT NOT NULL DEFAULT '';

CREATE TABLE hedge_legs (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL UNIQUE,
  hl_asset TEXT NOT NULL,         -- 'ETH'
  target_ratio TEXT NOT NULL,     -- '0.7' (Phase 1 fixed)
  tolerance_ratio TEXT NOT NULL,  -- '0.10' or similar. 🆕 v5.2.6 (D-3): display/future use.
                                  -- not used for rebalance judgment (judgment uses only the §7.3/§17.1 thresholds). Keep the column.
  leverage INTEGER NOT NULL DEFAULT 3,
  margin_mode TEXT NOT NULL DEFAULT 'isolated',  -- 🚨 isolated required
  hl_account_address TEXT,        -- subaccount address if applicable
  stop_order_id TEXT,
  stop_cloid TEXT,
  stop_price TEXT,
  stop_size TEXT,
  stop_last_verified_at TEXT,
  circuit_state TEXT NOT NULL DEFAULT 'closed',  -- closed | open | half_open
  -- 🆕 v5.1: Stop / Liquidation model redefinition (Section 19)
  entry_price TEXT,
  liquidation_price TEXT,
  effective_leverage TEXT,         -- notional / isolatedMargin based
  isolated_margin_usd TEXT,
  stop_distance_pct TEXT,          -- (stop_price - entry_price) / entry_price
  -- 🆕 v5.1: stale state countermeasure after stop trigger (Section 19)
  last_stop_audit_at TEXT,
  stop_trigger_crossed_at TEXT,    -- timestamp when ETH price >= stop_price is observed
  -- 🆕 v5.1: Margin status (Section 18.4)
  margin_status TEXT NOT NULL DEFAULT 'ok',  -- ok | warning | critical | safe_mode
  margin_balance_usd TEXT,
  margin_required_usd TEXT,
  -- 🆕 v5.2.6 (A-3): start time of the protected stop replacement critical section (§19.5)
  stop_replacing_started_at TEXT,  -- STOP_REPLACING start time. exceeding the 60s limit is escalation
  -- 🆕 v5.2.6 (X-4): budget scale-down ladder idempotency + re-expansion policy (§7.5)
  scale_step_pct INTEGER NOT NULL DEFAULT 100,  -- current step's absolute value (100/50/25)
  scale_baseline_lp_usd TEXT,      -- the scale-down base size = the full size when entering L1
  last_scale_change_at TEXT,       -- the most recent step-change time (for the re-expansion minimum-hold check)
  budget_breach_since TEXT,        -- the time the budget overflow started (L2 judgment / anti-oscillation)
  updated_at TEXT NOT NULL
);

-- v5.1 ALTER (for existing environments)
-- ALTER TABLE hedge_legs ADD COLUMN entry_price TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN liquidation_price TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN effective_leverage TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN isolated_margin_usd TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN stop_distance_pct TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN last_stop_audit_at TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN stop_trigger_crossed_at TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN margin_status TEXT NOT NULL DEFAULT 'ok';
-- ALTER TABLE hedge_legs ADD COLUMN margin_balance_usd TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN margin_required_usd TEXT;
-- v5.2.6 ALTER (A-3)
-- ALTER TABLE hedge_legs ADD COLUMN stop_replacing_started_at TEXT;
-- v5.2.6 ALTER (X-4)
-- ALTER TABLE hedge_legs ADD COLUMN scale_step_pct INTEGER NOT NULL DEFAULT 100;
-- ALTER TABLE hedge_legs ADD COLUMN scale_baseline_lp_usd TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN last_scale_change_at TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN budget_breach_since TEXT;
```

### 13.3 Runtime State (Hot)

```sql
CREATE TABLE bot_runtime_state (
  bot_id TEXT PRIMARY KEY,
  state_version INTEGER NOT NULL DEFAULT 0,
  current_tick INTEGER,
  sqrt_price_x96 TEXT,
  lp_amount0_raw TEXT,
  lp_amount1_raw TEXT,
  lp_eth_amount TEXT,             -- WETH amount (for a USDC pair)
  -- 🆕 v5.1: needed for drift computation (Section 7.3)
  eth_price_usd TEXT,
  lp_value_usd TEXT,
  target_short_size TEXT,
  last_known_hl_short_size TEXT,
  last_hl_reconcile_at TEXT,
  last_light_check_at TEXT,
  last_deep_audit_at TEXT,
  last_rebalance_attempt_id TEXT,
  health_status TEXT NOT NULL DEFAULT 'ok',  -- ok | warning | critical
  updated_at TEXT NOT NULL
);

-- v5.1 ALTER
-- ALTER TABLE bot_runtime_state ADD COLUMN eth_price_usd TEXT;
-- ALTER TABLE bot_runtime_state ADD COLUMN lp_value_usd TEXT;
```

### 13.4 Rebalance Attempts

```sql
CREATE TABLE rebalance_attempts (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  -- 🆕 v5.1: tracking of leg / asset / version
  hedge_leg_id TEXT NOT NULL,
  asset TEXT NOT NULL,            -- 'ETH'
  state_version INTEGER NOT NULL, -- for confirming a match with bot_runtime_state.state_version
  status TEXT NOT NULL,           -- success, failed, partial, skipped
  reason TEXT,                    -- 🚨 v5.2.1 (P0-11): canonical RebalanceReason (§7.6).
                                  --   values: drift_threshold | drift_relative | range_out |
                                  --       range_boundary_near | margin_warning | margin_critical |
                                  --       funding_alert | time_fallback | manual_admin |
                                  --       recovery_reconcile
                                  --   for multiple reasons[] use CSV (canonical values only, aliases forbidden)
  old_short_size TEXT,
  target_short_size TEXT,
  reconciled_short_size TEXT,     -- 🚨 the actual size after reconcile
  -- 🆕 v5.1: cloid for delta-only adjustment
  adjust_cloid TEXT,              -- cloid for delta-only adjust
  close_cloid TEXT,               -- only for target=0 / emergency / manual reset
  open_cloid TEXT,                -- same as above
  stop_cloid TEXT,
  close_order_id TEXT,
  open_order_id TEXT,
  adjust_order_id TEXT,
  error_code TEXT,
  error_message TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT
);
CREATE INDEX idx_attempts_bot_time ON rebalance_attempts(bot_id, started_at);
CREATE INDEX idx_attempts_status_time ON rebalance_attempts(status, started_at);
CREATE INDEX idx_attempts_leg ON rebalance_attempts(hedge_leg_id, started_at);

-- v5.1 ALTER
-- ALTER TABLE rebalance_attempts ADD COLUMN hedge_leg_id TEXT NOT NULL DEFAULT '';
-- ALTER TABLE rebalance_attempts ADD COLUMN asset TEXT NOT NULL DEFAULT 'ETH';
-- ALTER TABLE rebalance_attempts ADD COLUMN state_version INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE rebalance_attempts ADD COLUMN adjust_cloid TEXT;
-- ALTER TABLE rebalance_attempts ADD COLUMN adjust_order_id TEXT;
-- CREATE INDEX idx_attempts_leg ON rebalance_attempts(hedge_leg_id, started_at);
```

### 13.5 Metrics

```sql
CREATE TABLE hourly_bot_metrics (
  bot_id TEXT NOT NULL,
  bucket_hour TEXT NOT NULL,
  checks_count INTEGER NOT NULL,
  rebalance_count INTEGER NOT NULL,
  failure_count INTEGER NOT NULL,
  max_abs_drift_bps INTEGER,
  last_lp_eth_amount TEXT,
  funding_received_usd TEXT,
  funding_paid_usd TEXT,
  hedge_pnl_usd TEXT,
  PRIMARY KEY (bot_id, bucket_hour)
);

CREATE TABLE daily_bot_metrics (
  bot_id TEXT NOT NULL,
  bucket_day TEXT NOT NULL,
  checks_count INTEGER NOT NULL,
  rebalance_count INTEGER NOT NULL,
  failure_count INTEGER NOT NULL,
  max_abs_drift_bps INTEGER,
  total_lp_fee_usd TEXT,
  total_il_realized_usd TEXT,
  total_funding_usd TEXT,
  total_hedge_cost_usd TEXT,
  net_pnl_usd TEXT,
  PRIMARY KEY (bot_id, bucket_day)
);
```

### 13.6 Funding Ledger (simplified per phase in v5.1)

```yaml
🚨 v5.1 fix:
  v5.0's funding_history (per-record raw entry) is over-engineered for Phase A.
  Change the storage granularity per phase.

Phase A (10-100 bot):
  do not store raw funding events in D1
  → store only daily aggregate (funding_daily_metrics)

Phase B (1,000 bot):
  + store 24h / 7d / 30d realized aggregate (rolling)

Phase C (10,000 bot):
  + archive raw funding events to R2 (JSONL gzip)
  D1 still keeps only the daily / rolling aggregate
```

```sql
-- 🆕 v5.1 (used from Phase A)
CREATE TABLE funding_daily_metrics (
  bot_id TEXT NOT NULL,
  bucket_day TEXT NOT NULL,
  funding_paid_usd TEXT NOT NULL DEFAULT '0',
  funding_received_usd TEXT NOT NULL DEFAULT '0',
  funding_net_usd TEXT NOT NULL DEFAULT '0',
  events_count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (bot_id, bucket_day)
);
CREATE INDEX idx_funding_daily_day ON funding_daily_metrics(bucket_day);

-- 🆕 v5.1 (Phase B+)
CREATE TABLE funding_rolling_metrics (
  bot_id TEXT PRIMARY KEY,
  funding_24h_usd TEXT,
  funding_7d_usd TEXT,
  funding_30d_usd TEXT,
  funding_apr_24h_pct TEXT,
  funding_apr_7d_pct TEXT,
  funding_apr_30d_pct TEXT,
  computed_at TEXT NOT NULL
);

-- v5.0's funding_history (per-record) is to be retired
-- keep the existing LP Bot's funding_history (compat), do not use it for Ex Bot
-- do not DROP but also do not INSERT. archive (R2) at the Phase B transition.
```

### 13.7 Circuit Breaker (PK changed in v5.1)

```yaml
🚨 v5.1 fix:
  v5.0 used PRIMARY KEY (id TEXT) with bot_id, asset as separate columns, but
  managing the circuit per hedge_leg is correct (1 leg = 1 circuit).
  Change the PK to be hedge_leg_id based.

DDL representation:
  if an existing DB already exists, DROP is not possible, so
  do a view-based migration:
    1. create a new table circuit_breakers_v2 with hedge_leg_id PK
    2. copy from the existing circuit_breakers
    3. rename the existing table to _legacy (do not DROP)
    4. rename v2 to circuit_breakers
  
  ⚠️ Verification needed (zen task): prepare a migration script separately at Phase 0 start.
                          this spec describes only the new schema.

🚨 v5.2.6 (A-5) circuit breaker canonical source and transitions (history computation retired):
  - the canonical source is the stored column circuit_breakers.state. Dynamic computation from
    rebalance_attempts history is retired (§18.2 checkCircuitBreaker is rewritten to read the stored column. §17.1 also references the stored column).
  - transitions (made explicit):
      closed
        ──(3 consecutive failures within 24h)──▶ open  (opened_at=now, reset_at=now+1h)
      open
        ──(light-check detects reset_at reached)──▶ half_open
      half_open
        ──(a probe hedge-sync succeeds once)──▶ closed
        ──(probe fails)──▶ open  (reset_at reset to now+1h)
  - during half_open, allow hedge-sync **only once** (probe).
    §17.1's light-check suppresses the hedge-sync enqueue only when state==='open', and
    during half_open lets one probe through (consistent with A-1: stop monitoring continues at all times).
  - reset only on success (A-5). do not reset on partial / failed (§17.2 / B-4).
  - failure_count / last_failure_at / reset_at are used to drive these transitions.
```

```sql
-- 🆕 v5.1 (a new environment uses this) / 🆕 v5.2.6 (A-5): added half_open_probe_used
CREATE TABLE circuit_breakers (
  hedge_leg_id TEXT PRIMARY KEY,        -- 🆕 v5.1: 1 leg = 1 circuit
  bot_id TEXT NOT NULL,
  asset TEXT NOT NULL,
  state TEXT NOT NULL,            -- closed | open | half_open
  opened_at TEXT,
  reason TEXT,
  failure_count INTEGER NOT NULL DEFAULT 0,
  last_failure_at TEXT,
  reset_at TEXT,                  -- 🆕 v5.2.6 (A-5): the open→half_open unlock time (now+1h)
  half_open_probe_used INTEGER NOT NULL DEFAULT 0,  -- 🆕 v5.2.6 (A-5): flag that the half_open one-time probe is used
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_breaker_bot ON circuit_breakers(bot_id);

-- v5.2.6 ALTER (A-5, for existing environments)
-- ALTER TABLE circuit_breakers ADD COLUMN half_open_probe_used INTEGER NOT NULL DEFAULT 0;
```

### 13.8 Queue Idempotency (🆕 turned into a ledger in v5.2.6 / B-6)

```yaml
🚨 v5.2.6 (B-6) idempotency ledger responsibilities:
  - every consumer INSERTs message_id with state='started' at the start of processing.
    UNIQUE constraint conflict = duplicate delivery → return immediately (structurally prevents double execution).
  - derive the cloid **from the queue message's deterministic ID**, not from a "re-fetched state"
    (§8.5 makeCloid's attemptId should be a deterministic value derived from the message).
  - design reconcile / repair messages idempotently so they can no-op by looking at terminal state (succeeded/failed).
  - responsibility separation: the UserLockDO lease is "mutual exclusion of a single user's mutations"; this ledger is "idempotency
    of a single message (absorbing duplicate delivery)". The two are separate layers (§11).
```

```sql
-- 🆕 v5.2.6 (B-6): extended to a per-message idempotency ledger (per the §13.0 principle, ADD without DROP/RENAME).
CREATE TABLE queue_idempotency (
  key TEXT PRIMARY KEY,            -- existing: an arbitrary idempotency key (backward compat). New consumers put message_id here
  message_id TEXT,                 -- 🆕 B-6: the queue message's deterministic ID (UNIQUE, duplicate-delivery detection)
  kind TEXT,                       -- 🆕 B-6: consumer type (light-check|hedge-sync|reconcile|partial_repair|...)
  state TEXT,                      -- 🆕 B-6: started | succeeded | failed | retryable
  attempt INTEGER NOT NULL DEFAULT 0,  -- 🆕 B-6: redelivery count
  bot_id TEXT,
  result_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT,                 -- 🆕 B-6
  expires_at TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_idempotency_message ON queue_idempotency(message_id);
CREATE INDEX idx_idempotency_expires ON queue_idempotency(expires_at);

-- v5.2.6 ALTER (B-6, for existing environments)
-- ALTER TABLE queue_idempotency ADD COLUMN message_id TEXT;
-- ALTER TABLE queue_idempotency ADD COLUMN kind TEXT;
-- ALTER TABLE queue_idempotency ADD COLUMN state TEXT;
-- ALTER TABLE queue_idempotency ADD COLUMN attempt INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE queue_idempotency ADD COLUMN updated_at TEXT;
-- CREATE UNIQUE INDEX idx_idempotency_message ON queue_idempotency(message_id);
```
### 13.9 HL Agent Keys (🆕 v5.1, see Section 21.5)

```sql
-- newly added to control_db
-- 🚨 v5.2.2 (P0-2 / Option A): make envelope fields independent BLOB columns.
--   fully synced with the §21.5.2 / §21.5.2.1 runbook (1 agent key row = 1 DEK).
CREATE TABLE hl_agent_keys (
  id TEXT PRIMARY KEY,                  -- agent_key_id (UUID)
  user_id TEXT NOT NULL,
  hl_user_address TEXT NOT NULL,        -- master account
  agent_address TEXT NOT NULL,          -- agent (signing) address
  encrypted_secret BLOB NOT NULL,       -- agent key, AES-256-GCM, encrypted with a per-row DEK
  secret_iv BLOB NOT NULL,              -- 🆕 v5.2.2: IV used for encrypted_secret
  secret_auth_tag BLOB NOT NULL,        -- 🆕 v5.2.2: AES-GCM auth tag for encrypted_secret
  wrapped_dek BLOB NOT NULL,            -- 🆕 v5.2.2: DEK wrapped with the Master Key (Secrets Store)
  dek_iv BLOB NOT NULL,                 -- 🆕 v5.2.2: IV used for wrapped_dek
  encryption_key_version INTEGER NOT NULL,  -- Master Key version (rotation chain)
  approval_status TEXT NOT NULL,        -- 'pending' | 'approved' | 'revoked' | 'expired'
  approved_at TEXT,
  expires_at TEXT,                      -- HL agent key expiry
  rotated_from TEXT,                    -- previous hl_agent_keys.id (rotation chain)
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_hl_agent_keys_user ON hl_agent_keys(user_id);
CREATE INDEX idx_hl_agent_keys_status ON hl_agent_keys(approval_status, expires_at);

-- v5.2.2 ALTER (for existing environments; for a new DB the CREATE TABLE above is fine)
-- ALTER TABLE hl_agent_keys ADD COLUMN secret_iv BLOB NOT NULL DEFAULT x'';
-- ALTER TABLE hl_agent_keys ADD COLUMN secret_auth_tag BLOB NOT NULL DEFAULT x'';
-- ALTER TABLE hl_agent_keys ADD COLUMN wrapped_dek BLOB NOT NULL DEFAULT x'';
-- ALTER TABLE hl_agent_keys ADD COLUMN dek_iv BLOB NOT NULL DEFAULT x'';
```

```yaml
🚨 Handling (fully synced with §21.5.2 / §21.5.2.1 in v5.2.2 / P0-2):
  - 1 agent key row = 1 DEK. The DEK is wrapped with the Master Key (Cloudflare Secrets Store)
    and stored in wrapped_dek. The agent key is encrypted with the per-row DEK and stored in
    encrypted_secret (AES-256-GCM, secret_iv / secret_auth_tag)
  - the raw secret / raw DEK does not appear even in a DB dump
  - decryption only inside the OPERATOR Worker. For the decrypt flow see §21.5.2
    (unwrap wrapped_dek with the Master Key → decrypt encrypted_secret with the DEK)
  - the post-decrypt plain DEK / plain agent key is function-scope only, destroyed immediately after use
  - on rotation, insert a new row (new DEK + new wrap); the old row becomes status='revoked'
  - do not use keys with approval_status = 'pending'
```

### 13.10 LP Operations (🆕 v5.2.6 / B-1, QA Codex C-3)

```yaml
🚨 v5.2.6 (B-1): a recovery ledger for "on-chain success + D1 failure".
  Tracks each on-chain operation of vaultMint / vaultRebalance / vaultClose idempotently, so that
  the tokenId can be re-determined even if the tx succeeded but the worker died before reflecting it in D1.
  - the Vault must always emit VaultRebalanced(user, botId, oldTokenId, newTokenId, liquidity, amounts)
    as an indexed event (§15.5.6). open/close emit similar indexed events.
  - recovery procedure (on restart/retry):
      find lp_operations with status='submitted' → get the tx receipt → decode the event →
      determine the new tokenId → update D1 positions / lp_operations (status='recovered').
      Until then, hedge adjustments for that bot are forbidden entirely (keep lifecycle_state in one of
      lp_opening/lp_rebalancing/lp_closing and skip §17.1 light-check).
```

```sql
CREATE TABLE lp_operations (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL,
  op_type TEXT NOT NULL,            -- open | rebalance | close
  idempotency_key TEXT NOT NULL UNIQUE,  -- deterministic key (prevent double submission, consistent with §B-6)
  tx_hash TEXT,
  pre_token_id TEXT,
  post_token_id TEXT,
  status TEXT NOT NULL,             -- submitted | confirmed | d1_failed_recovering | recovered
  submitted_at TEXT NOT NULL,
  confirmed_at TEXT
);
CREATE INDEX idx_lp_ops_bot ON lp_operations(bot_id, submitted_at);
CREATE INDEX idx_lp_ops_status ON lp_operations(status);
```

### 13.11 Close Operations (🆕 v5.2.6 / B-2, QA Codex C-4)

```yaml
🚨 v5.2.6 (B-2): turn the close/redeem state machine into a ledger, structurally preventing double repayment / double settlement.
  - kind=user_redeem: the redeem tx instantly liquidates the LP and returns the LP-portion USDC to the user in the same tx
    (on-chain guarantee = formally adopt the HLD RedemptionQueue design). The HL-portion USDC is sent after hedge close.
  - kind=bot_safe_close: full settlement in the order hedge → LP. USDC is parked into the Vault's uninvested balance
    (the user's withdraw right is always valid). After completion, to the §16.7 closed loop.
  - residual_hl_liability: the explicit state when hedge close is impossible (escalation). LP-side repayment is not stopped.
```

```sql
CREATE TABLE close_operations (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL,
  kind TEXT NOT NULL,               -- user_redeem | bot_safe_close
  state TEXT NOT NULL,              -- requested | lp_closed | hedge_close_pending |
                                    -- hedge_closed | funds_returned | funds_parked |
                                    -- residual_hl_liability | done
  idempotency_key TEXT NOT NULL UNIQUE,  -- structural prevention of double repayment/double settlement
  requested_at TEXT NOT NULL,
  lp_closed_at TEXT,
  hedge_closed_at TEXT,
  funds_settled_at TEXT,
  residual_usd TEXT,                -- the amount recorded on residual_hl_liability
  done_at TEXT
);
CREATE INDEX idx_close_ops_bot ON close_operations(bot_id, requested_at);
CREATE INDEX idx_close_ops_state ON close_operations(state);
```

### 13.12 System Config (🆕 v5.2.6 / r1, the ruling on confirmation-item #2)

```yaml
🚨 v5.2.6 (r1): the canonical table for tunables.
  Code falls back to the default values below, and operational overrides happen in this table.
  The tunables of §16.7 / §19.5 / §7.5 / §18.4 / §18.4.1 all take this table's keys as canonical.
  Place it in control_db (a shard-independent global setting. Concretizes the §12.1 global config in this table).
```

```sql
-- newly added to control_db
CREATE TABLE system_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

```yaml
Default value list (code fallback values; overridable in operation):
  cooldown_minutes                  = 60     # §16.7 cooldown → re-entry judgment interval (A-4/B-2)
  reentry_funding_apr_floor         = -15    # §16.7 re-entry condition (7d funding APR > -15%)
  reentry_check_interval_minutes    = 60     # §16.7 re-entry judgment interval
  parked_interval_hours             = 24     # §16.7 judgment interval while parked
  safe_close_limit_7d               = 3      # §16.7 bot_safe_close limit within 7 days → parked
  hedge_stopped_cooldown_hours      = 4      # §19.3/§17.1 the length of hedge_stopped_cooldown (A-4)
  funding_24h_apr_immediate_l1      = -40    # §7.5 if 24h funding annualized < -40%, immediately L1 by one step (C-4)
  l1_steps                          = 100,50,25  # §7.5 proportional scale-down ladder (% of size, C-4)
  preflight_buffer                  = 2.0    # §18.4.1 preflight margin buffer (C-2)
  stop_replacing_deadline_seconds   = 60     # §19.5 STOP_REPLACING limit (A-3)
  user_redeem_hedge_close_sla_minutes = 5    # §16.4 user_redeem hedge close SLA (B-2)
  scale_up_min_hold_hours           = 24     # §7.5 minimum hold time before re-expansion from a scale-down step (X-4)
```

### 13.13 Uninvested Balances (🆕 v5.2.6 / X-3, QA Codex round-2)

```yaml
🚨 v5.2.6 (X-3): the ledger of USDC parked by bot_safe_close (the HLD unspent capital model).
  Tracks funds parked in the Vault's uninvested balance per user/bot/chain.
  ・ on park, FundsParked event + INSERT into this table (source='bot_safe_close').
  ・ §16.7 re-entry **fully consumes** this balance for that bot (FundsRedeployed).
  ・ the user's withdraw is always possible (FundsWithdrawn, consistent with the INV-3 revision).
  ・ no new contract is needed. Reuse the existing withdraw path.

🚨 v5.2.6 (Y-3) concurrency control (design decision):
  - the canonical source is **on-chain (the Vault's unspent balance)**. uninvested_balances is a mirror (cache).
  - 🚨 on-chain-priority reconciliation principle (🆕 Z-6, defined in this section): **the divergence between D1 and on-chain
    is always corrected toward the on-chain side** (align D1 to the real balance. never the reverse).
  - park repetition (additive upsert):
      INSERT INTO uninvested_balances (...) VALUES (...)
      ON CONFLICT (user_address, bot_id, chain_id)
      DO UPDATE SET amount_usdc = amount_usdc + excluded.amount_usdc,
                    parked_at = excluded.parked_at;
  - withdraw: the scanner detects the FundsWithdrawn event and subtracts from the D1 balance (event-driven sync).
  - for the canonical redeploy (§16.7 re-entry) procedure see §16.7 (mutual exclusion with the withdraw API via the UserLockDO
    lease → read on-chain balance → tx → update D1 to 0 with CAS).
```

```sql
-- state shard DB
CREATE TABLE uninvested_balances (
  user_address TEXT NOT NULL,
  bot_id TEXT NOT NULL,
  chain_id INTEGER NOT NULL,
  amount_usdc TEXT NOT NULL,          -- BigDecimal string
  parked_at TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'bot_safe_close',
  PRIMARY KEY (user_address, bot_id, chain_id)
);
CREATE INDEX idx_uninvested_bot ON uninvested_balances(bot_id);
```

---

## 14. Retention Policy

### 14.1 Keep in D1

```yaml
bot_runtime_state:
  permanent, 1 row per bot

rebalance_attempts:
  90 days

hourly_bot_metrics:
  30 days

daily_bot_metrics:
  365 days

queue_idempotency:
  24-72h

funding_daily_metrics (v5.1):
  365 days (Phase A)

funding_rolling_metrics (v5.1):
  permanent, 1 row per bot (Phase B+)

circuit_breakers:
  permanent (1 row per hedge_leg)

hl_agent_keys (v5.1):
  permanent (kept even after revoked as an audit trail)
```

### 14.2 Forbidden in D1

```yaml
🚨 do not store in D1:
  - 5-minute snapshot for all bots
  - raw RPC responses
  - raw HL responses
  - high-cardinality logs
  - full execution traces
  - 🆕 (v5.1) raw funding events (Phase A is funding_daily_metrics only,
                                   Phase C+ goes to R2)

Reason:
  10,000 bot × 288 checks/day = 2.88M rows/day
  30 days: 86.4M rows
  → exceeds the D1 constraint (10GB / 1 DB)
```

### 14.3 Archive (Analytics Engine warning strengthened in v5.1)

```yaml
R2 (Phase B+):
  - raw logs (JSONL gzip by day/shard)
  - rebalance_attempts > 90d
  - HL/RPC response samples (sanitized — Section 21.5)
  - debug traces
  - raw funding events (Phase C+)

Analytics Engine (Phase B+):
  Allowed dimensions (low cardinality):
    - shard_id
    - chain
    - queue_name
    - error_code (enumerated)
    - phase / env
    - hl_action_type ('order' | 'cancel' | 'info')
  
  🚨 Forbidden dimensions (high cardinality):
    ❌ bot_id
    ❌ user_id
    ❌ hl_user_address
    ❌ position_id
    ❌ tx_hash
    ❌ cloid
    ❌ order_id
  
  Reason:
    Analytics Engine explodes in cost / latency on high-cardinality dimensions.
    Per-bot / per-user metrics are stored only as D1 (hourly_bot_metrics / daily_bot_metrics)
    aggregates.
  
  When per-bot detail is needed:
    - D1 aggregate (hourly / daily)
    - R2 raw logs (offline analysis)
```

---

## 15. MarketData Cache

### 15.1 Pool State Cache

```yaml
Durable Object: MarketDataDO
key format: chain:poolAddress

stored:
  - sqrtPriceX96
  - currentTick
  - blockNumber
  - updatedAt
  # 🆕 v5.2.6 (C-3, QA Codex M-5): split the price source 3 ways.
  - uniPoolPrice     (from slot0. **LP-math only** = calculatePositionAmount / drift)
  - hlMarkPrice      (HL mark. **stop judgment / near-stop / hedge size basis (incl. dust)**, Z-6)
  - hlOraclePrice    (HL oracle. **margin evaluation only**)
  - hlMarkUpdatedAt  (the fetch time of hlMarkPrice. for staleness judgment)

🚨 v5.2.6 (A-2 / C-3) type and field-name discipline:
  - hold all prices as BigDecimal-compatible strings. The reader must receive them via BigDecimal(...)
    for comparison/arithmetic (JS float / Number() / raw >= are forbidden).
  - the old-name current-price alias field does not exist. 🆕 v5.2.6 (X-5): the old single
    "eth price" data field (camelCase name) is fully retired from code / queue message / schema,
    split into 3 prices per use (the DB column bot_runtime_state.eth_price_usd keeps only the column name per §13.0,
    its value is uniPoolPrice):
      LP math (calculatePositionAmount / drift / lpValueUsd) → uniPoolPrice
      stop-cross / near-stop (§17.1 / §19.3)              → hlMarkPrice
      margin evaluation (§18.4 evaluateMargin)            → hlOraclePrice
      the price field name of the stop-audit queue message → markPriceUsd
  - a fetch method compatible with weight 0: a shared HlMarkDO fetches HL mark/oracle once
    every 60 seconds (global +1–2 weight/min, not proportional to bot count). light-check
    only reads that cache and does not touch HL (consistent with NN#3 / §5.3 / §9.2).
  - staleness: when the hlMarkPrice used for stop judgment is >120 seconds stale, treat it as **undecidable**:
      ・freeze hedge-sync
      ・continue stop monitoring as a substitute with uniPoolPrice + 2× near-stop margin
      ・escalation (priority stop-audit / admin alert)
```

### 15.2 Refresh Policy

```yaml
maxAge:
  normal volatility:    15-30 sec
  high volatility:      5-10 sec
  fallback:             🆕 v5.2.6 (E): Phase 1 has at least 1 RPC per chain (Base/OP 1 endpoint each).
                        multi-RPC failover is Phase C (single-RPC means "1 per chain")

refresh trigger:
  - on read if updatedAt > maxAge
  - background refresh (proactive) for high-traffic pools
  - manual on rebalance attempt
```

### 15.3 Light-check Usage (an example use of MarketDataDO)

```yaml
🚨 v5.2.1 fix (P0-2 / canonical unification):
  the canonical implementation of light-check is unified into **Section 17.1**.
  This §15.3 is reduced to an "example use" explanation of MarketDataDO; the pseudocode body
  references Section 17.1 (preventing recurrence of the divergence / NN#14-invalidation bug from dual definition).

  the following problems that existed in the old §15.3 pseudocode are resolved in the §17.1 canonical version:
    - it re-marked the stop_trigger_crossed marker unconditionally
      → in §17.1 it is guarded: if already set, it does not overwrite stop_trigger_crossed_at.
        This makes the §18.3 / NN#14 "marker stuck > 30 min → SAFE_MODE" fire correctly
        (the timestamp does not roll back to now on every light-check).
    - it computed targetShort in float (`*`)
      → in §17.1 it is BigDecimal, and targetRatio is bps-integerized (§7.6 / P0-6).

The role MarketDataDO plays in this flow (key points as an example use):
  - light-check reads only the MarketDataDO shared pool cache
    (sqrtPriceX96 / currentTick / uniPoolPrice / hlMarkPrice / hlOraclePrice)  # 🆕 X-5: price 3-way split (§15.1)
  - it fetches nothing from HL (weight 0, NN#3)
  - calculatePositionAmount is a pure function per §6.4 (no HL/RPC fetch)
  - the real flow (stop-crossed guarded detection / drift trigger / hot state update /
    hedge-sync enqueue) takes Section 17.1 as the only norm
```

---

## 15.5 LP NFT Custody / Control Model (🆕 v5.1)

### 15.5.1 Design policy (v5.2.1: Option C finalized)

```yaml
🚨 newly added in v5.1 / Option C finalized in v5.2.1:
  in v5.0 the owner of the LP NFT was implicit (≒ assumed user wallet), but
  in EXBOT the LP NFT is held by a dedicated custody contract BnzaExVault.

🚨 v5.2.1 finalized (zen decision — Option C):
  EXBOT newly develops and newly deploys an EXBOT-dedicated Solidity contract suite (BnzaExVault).
  The current BNZA POOL's BnzaRouter v2.2.1 / BnzaLpBot v1.1 are
  not modified (responsibility separation. For details see Section 3.4).
  - EXBOT custody = BnzaExVault (new, not deployed, spec'd in this SPEC §15.5.6)
  - BNZA POOL custody = BnzaRouter v2.2.1 (current, running on Optimism+Base, unchanged)

Reason:
  - rebalance / close can be called from the Operator trustlessly and atomically
  - eliminates the risk of a user accidentally transferring the NFT or revoking the approve
  - by putting the subaccount + LP NFT together under BNZA management, failure modes are consolidated
  - by isolating EXBOT and POOL as completely separate products / separate contracts,
    EXBOT development has zero impact on POOL's post-WL-launch operational stability

Phase A custody policy:
  custodian: 'vault' (fixed in Phase A, EXBOT is BnzaExVault custody)
  custodian_address: BnzaExVault address (per chain, Optimism + Base)
  invariant: NFPM.ownerOf(tokenId) == BnzaExVault address
  representation of the user's share: a BnzaExVault internal ledger (mapping(user => positionId))
                     or a receipt token issued by BnzaExVault
  
  Completely non-interfering at the contract level with the existing BNZA-LPBOT (BnzaLpBot.sol) / BnzaRouter v2.2.1
  (Section 15.5.4 / Section 3.4).
```

### 15.5.2 Authority Matrix

```yaml
| Role            | Read  | Mint  | Increase | Decrease | Collect | Burn  | Transfer |
|-----------------|-------|-------|----------|----------|---------|-------|----------|
| Operator (BNZA) |  ✅   |  ✅   |   ✅     |   ✅     |   ✅    |  ✅   |    ❌    |
| User            |  ✅   |  ❌   |   ❌     |   ❌     |   ❌    |  ❌   |    ❌    |
| Emergency Admin |  ✅   |  ❌   |   ❌     |   ✅(*)  |   ✅    |  ❌   |    ✅(*) |
| External        |  ✅   |  ❌   |   ❌     |   ❌     |   ❌    |  ❌   |    ❌    |

(*) Emergency Admin only via multi-sig. The BnzaExVault emergency path spec is in this SPEC §15.5.6.

Operator authority:
  - LP rebalance (Decrease + Increase)
  - LP close (Decrease 100% + Burn)
  - Fee collect (event-based, Section 21)
  - drives the Bot state machine (Section 16)

User rights (Phase A):
  - Bot start / stop (start / pause / close request)
  - Position view (read-only)
  - Withdraw request (triggers the flow up to LP close → USDC return)
  - HL agent key approval (Section 21.5)

User does NOT have:
  - LP NFT direct transfer
  - LP NFT direct burn
  - HL master private key (not stored at BNZA, Section 21.5)

Emergency permissions:
  - LP forced close (multi-sig + admin)
  - LP NFT recovery (in case of operator failure)
  - User funds rescue path
```

### 15.5.3 LP Operation Flow and authority relationships

```yaml
LP Open (on Bot start) — 🆕 v5.2.2 (P0-3-2): function names unified to the §15.5.6 ABI:
  1. user → POOL UI: deposit USDC + start Ex Bot
  2. UI → Operator → BnzaExVault.vaultMint(user, MintParams)
  3. BnzaExVault.vaultMint: USDC → swap → NFPM.mint (Uniswap V3)
  4. BnzaExVault: BnzaExVault itself holds the LP NFT (returns tokenId)
  5. BnzaExVault: record positionOwner[tokenId] = user
  6. Operator: record into the positions table custodian='vault', custodian_address=BnzaExVault,
     token_id=returned tokenId

LP Rebalance (Operator driven):
  1. the Operator judges a rebalance is needed (range out etc.)
  2. Operator → BnzaExVault.vaultRebalance(tokenId, newTickLower, newTickUpper, slippageBps)
  3. BnzaExVault (msg.sender == authorizedOperator check) executes if so
  4. BnzaExVault.vaultRebalance: NFPM decreaseLiquidity 100% → collect → swap
     → NFPM.mint new range (burn old tokenId) → returns newTokenId
  5. Operator: update the D1 positions row with new tickLower/tickUpper + token_id=newTokenId

LP Close (Operator or User initiated):
  see Section 16.4 (LP close authority) and Section 16.6 (LP_CLOSING)
```

### 15.5.4 Non-interference with existing BNZA POOL contracts (v5.2.1: Option C)

```yaml
🚨 v5.2.1 finalized: EXBOT newly develops a new contract suite (BnzaExVault).
  It does not modify the current BNZA POOL contracts at all (Option C / Section 3.4).

Existing BNZA POOL contracts (unchanged, reference only):
  ~/Desktop/BNZA-LPBOT/src/BnzaLpBot.sol      -- for POOL, not modified
  ~/Desktop/BNZA-LPBOT/docs/SPEC.md           -- design pattern reference only
  ~/Desktop/BNZA-ROUTER/src/BnzaRouter.sol    -- for POOL v2.2.1, not modified
  ~/Desktop/BNZA-ROUTER/docs/SPEC.md          -- design pattern reference only
  ~/Desktop/BNZA-ROUTER/docs/SPEC_V2.md       -- design pattern reference only
  ~/Desktop/bnza-contracts/src/BNZAToken.sol  -- BuyBack&Burn target, shared

New EXBOT contract (spec'd in this SPEC):
  BnzaExVault.sol           -- new development, API/invariants spec'd in §15.5.6
  planned deploy: Optimism + Base (same chains as BnzaRouter v2.2.1, different addresses)

Non-interference guarantees (zen confirms before Phase 0 starts):
  1. BnzaExVault never calls / changes the storage / function / authority of
     BnzaRouter v2.2.1 / BnzaLpBot v1.1
  2. the only shared thing is BNZAToken (the BuyBack&Burn destination), which is read/transfer only
  3. NFPM (Uniswap V3 NonfungiblePositionManager) is shared infra but
     positions are independent per tokenId and do not collide
  4. the Operator key / multi-sig is separated for EXBOT only (§21.5.5)
  5. EXBOT development/deploy must not affect POOL's post-WL-launch operation
     (cron / relayer / Stage 3 rollback situation)

Design-pattern reuse policy:
  the existing BnzaRouter/BnzaLpBot custody patterns (internal ledger / operator
  authority / emergency multi-sig) are used as a reference for the BnzaExVault design.
  But there is no code sharing; it is newly implemented for EXBOT only (responsibility separation).
```

### 15.5.5 Failure Modes

```yaml
If the Operator is compromised:
  - rotate the Operator key
  - SAFE_MODE / forced close all Bots via the Emergency Admin (multi-sig)

BnzaExVault contract bug:
  - Pause feature (implemented in BnzaExVault itself)
  - LP NFT recovery via the Emergency Admin
  - a fast return path to User funds

If a User attempts abuse:
  - the User cannot call anything but BnzaExVault's public functions
  - they can only touch the LP via Bot start/stop/withdraw

If the LP NFT is unexpectedly transferred:
  - the Operator detects the NFPM.ownerOf anomaly at the next light-check
  - transition bot.status to 'error', admin alert
  - designed so User funds are protected up to the LP value
```

### 15.5.6 BnzaExVault Solidity spec (🆕 v5.2.1, new contract)

```yaml
🚨 BnzaExVault is an EXBOT-dedicated new Solidity contract.
  Since this SPEC is the whole-EXBOT spec, the Solidity-side API / invariants are also
  centrally managed here (not split into a separate SPEC, for consistency management).
  Deploy: Optimism + Base (a separate contract / separate address from BnzaRouter v2.2.1).
```

```solidity
// Invariants — always hold:
//  INV-1: for every managed tokenId, NFPM.ownerOf(tokenId) == address(this)
//  INV-2: positionOwner[tokenId] points to a single user (1 LP NFT = 1 user)
//  INV-3 (🆕 v5.2.6 X-3 revised): USDC in the user_redeem path stays only within the same tx
//          (as before, returned to the user in 1 tx). Only the bot_safe_close path is an exception,
//          allowing a park into the Vault's **uninvested balance**. The park is
//          ledger-recorded (uninvested_balances, §13.13) + has an indexed event, and
//          the user's withdraw right is always valid. This is the same concept as HLD's
//          unspent capital model, and no new contract is needed (reuse the existing withdraw path).
//  INV-4: operator functions are authorizedOperator only; emergency is multiSig only
//  INV-5: do not call the storage/function of BnzaRouter v2.2.1 / BnzaLpBot v1.1

interface IBnzaExVault {
  // --- Events (🆕 v5.2.6 / B-1): required for tokenId re-determination on D1 failure. All indexed. ---
  event VaultMinted(address indexed user, bytes32 indexed botId, uint256 indexed tokenId,
                    uint128 liquidity, uint256 amount0, uint256 amount1);
  event VaultRebalanced(address indexed user, bytes32 indexed botId,
                        uint256 oldTokenId, uint256 indexed newTokenId,
                        uint128 liquidity, uint256 amount0, uint256 amount1);
  event VaultClosed(address indexed user, bytes32 indexed botId, uint256 indexed tokenId,
                    uint256 token0Amount, uint256 token1Amount);
  // 🆕 v5.2.6 (X-3 / Y-3): bot_safe_close park accounting (the unspent capital model). All indexed.
  //   🚨 the Vault's unspent balance is the **canonical source** of the park balance. redeploy / withdraw
  //   enforce the on-chain balance (a tx that loses a concurrent race reverts = a structural backstop).
  //   D1.uninvested_balances (§13.13) is a mirror synced by these events; divergence is always
  //   corrected toward the on-chain side (§16.7 redeploy procedure / the on-chain-priority reconciliation principle §13.13).
  event FundsParked(address indexed user, bytes32 indexed botId, uint256 amountUsdc, uint256 chainId);
  event FundsRedeployed(address indexed user, bytes32 indexed botId, uint256 amountUsdc, uint256 chainId);
  event FundsWithdrawn(address indexed user, bytes32 indexed botId, uint256 amountUsdc, uint256 chainId);

  // --- Operator authority (authorizedOperator only) ---
  function vaultMint(
    address user,
    MintParams calldata params      // pool, tickLower, tickUpper, amounts, slippage
  ) external returns (uint256 tokenId);
  // effect: receive USDC → swap → NFPM.mint → this contract holds the NFT
  //       positionOwner[tokenId] = user
  //       🆕 v5.2.6 (B-1): emit VaultMinted (so the Operator can re-determine the tokenId into D1)

  function vaultRebalance(
    uint256 tokenId,
    int24 newTickLower,
    int24 newTickUpper,
    uint256 slippageBps
  ) external returns (uint256 newTokenId);   // 🆕 v5.2.2 (P0-3-1)
  // effect: decreaseLiquidity 100% → collect → swap → mint new range
  //       burn the old tokenId, this contract holds the new tokenId, carry over the ledger
  //       return newTokenId so the Operator can update D1 positions.token_id
  //       🆕 v5.2.6 (B-1): always emit VaultRebalanced(user, botId, oldTokenId, newTokenId, ...) as an
  //       indexed event (on D1 failure, re-determine newTokenId via receipt→decode)

  // 🆕 v5.2.6 (Z-1 / Codex M1): make the close destination an enum branch (a mapping to the HLD unspent capital model).
  //   the fund destination is always confined to "the user themselves or the user's own unspent" (third-party destinations are structurally impossible thanks to the enum).
  enum CloseDestination { USER, UNINVESTED }
  function vaultClose(bytes32 botId, CloseDestination dest) external;
  // effect: decreaseLiquidity 100% → collect → WETH→USDC swap → branch on dest:
  //   dest=USER       : return the liquidation USDC to the user in the same tx (user_redeem path). emit VaultClosed
  //   dest=UNINVESTED : add to that user's unspent balance (bot_safe_close path). emit FundsParked
  // authority: dest=USER is user_redeem (the user themselves / with their own signature verification),
  //       dest=UNINVESTED is onlyOperator (bot_safe_close).

  function uninvestedBalanceOf(address user, bytes32 botId) external view returns (uint256);
  // the concrete "read on-chain balance" before §16.7 redeploy (this, not D1, is the canonical source)

  function redeployUninvested(bytes32 botId /*, MintParams */) external; // onlyOperator
  // re-invest only from the unspent of the same user・same bot. Insufficient balance reverts (structural backstop). emit FundsRedeployed

  function withdrawUninvested(bytes32 botId, uint256 amount) external; // the user themselves only
  // always executable (the concrete of the INV-3 revision). emit FundsWithdrawn

  function collectFees(uint256 tokenId) external; // event/threshold-based (§21)

  // --- Emergency (multiSig only) ---
  function emergencyTransfer(uint256 tokenId, address recipient) external;
  // multiSig only. transfer the LP NFT directly to the user wallet on operator failure

  function pause() external;   // multiSig / guardian
  function unpause() external;

  function rotateOperator(     // 🆕 v5.2.2 (P0-3-3) — consistent with §21.5.5 / §21.5.6
    address oldOperator,
    address newOperator
  ) external;
  // effect: update authorizedOperator. Executable via multiSig only.
  //       does not affect in-flight txs (guarantees transaction-level atomicity).

  // --- Read ---
  function ownerOfPosition(uint256 tokenId) external view returns (address);
  function isAuthorizedOperator(address a) external view returns (bool);
}
```

```yaml
Authority (consistent with Section 15.5.2):
  authorizedOperator:
    - vaultMint / vaultRebalance / vaultClose(dest=UNINVESTED) / redeployUninvested / collectFees
    - require msg.sender == authorizedOperator
    - the operator key is EXBOT-dedicated (§21.5.5), a different key from POOL's operator
  multiSig (Emergency Admin):
    - emergencyTransfer / pause / unpause / rotateOperator
  User (themselves only, 🆕 Z-1):
    - vaultClose(dest=USER) (user_redeem, themselves / with own signature verification) / withdrawUninvested
    - otherwise they touch the LP only via POOL UI → Operator API
  Transfer forbidden:
    - the operator cannot transfer the LP NFT (maintains INV-1)
    - only emergencyTransfer is an exception, via multiSig

🚨 v5.2.6 (Z-1): this ABI is a **required interface (normative)**. The function names/signatures are
  finalized in SOTATEK's contract design (HLD §5). However, the following are **mandatory requirements**:
    - the vaultClose dest branch (USER / UNINVESTED)
    - on-chain balance enforcement for redeploy / withdraw (insufficient reverts = structural backstop)
    - the 3 events (FundsParked / FundsRedeployed / FundsWithdrawn)
    - the authority constraints (dest=USER is the user themselves, dest=UNINVESTED and redeploy are onlyOperator, withdraw is the user themselves)

Non-interference (INV-5, Section 15.5.4 / Section 3.4):
  - BnzaExVault does not import / delegatecall / call BnzaRouter v2.2.1
  - the only shared things are BNZAToken (BuyBack&Burn) and NFPM (independent per tokenId)

zen tasks finalized in Phase 0:
  - the BnzaExVault deploy address per chain
  - the authorizedOperator address (EXBOT-dedicated)
  - the multiSig signer set / threshold
  - the performance fee distribution logic (up to 10 recipients, consistent with §2.3)
  - the final ABI, referencing the existing BnzaRouter/BnzaLpBot custody patterns
```

---

## 16. Bot Lifecycle State Machine

### 16.1 Initialization States

```yaml
🚨 v5.2.1 (P0-8): the fine-grained states below are stored in bots.lifecycle_state
  (§13.2). bots.status stays the coarse-grained 6 values (active/paused/closing/closed/
  safe_mode/error). The mapping between them:
    lifecycle_state                | status
    -------------------------------|------------------
    idle/preflight/lp_opening/     | (status is the coarse-grained value before/after the transition)
      lp_opened/hedge_pre_open/    |
      hedge_post_confirmed/        |
      stop_placing/stop_verified   |
    active                         | active
    hedge_stopped_cooldown         | active   (🆕 A-4: cooldown after stop fires. hedge-sync suppressed)
    cooldown                       | active   (🆕 B-2: re-entry judgment in progress after bot_safe_close)
    parked                         | active   (🆕 B-2: slow the judgment to a 24h interval on repeated safe_close)
    lp_rebalancing                 | active   (light-check skips per §17.1 P0-9)
    lp_closing                     | closing
    closed                         | closed
    safe_mode                      | safe_mode
    error                          | error
    (keep the value just before pause) | paused   (🆕 B-5: paused is expressed at the status level only.
                                              lifecycle_state keeps and does not change the pre-pause value)
  🚨 v5.2.6 (B-5): the lifecycle_state strings in the table above are canonical. The flow diagram below and all pseudocode
    use the same words (the old uppercase aliases hedge_pre_open / hedge_post_confirmed are retired).
  Places where old descriptions assigned a fine-grained value into status, like "bot.status='lp_opened'",
  are all to be read as assignment into lifecycle_state.
```

```
# 🆕 v5.2.6 (B-5): each box name is unified to the canonical string of the §13.2 lifecycle_state enum.
idle
  ↓
preflight
  - user HL margin check (sufficient? — Section 18.4)
  - agent approval check (approved? — Section 21.5)
  - builder fee approval check (approved?)
  - LP mint simulation (will succeed?)
  - one-bot policy check (Phase A, Section 16.5)
  ↓
lp_opening (detailed in Section 16.6)
  ↓
lp_opened
  ↓
hedge_pre_open
  - HL short open (IOC)
  ↓
hedge_post_confirmed
  - 🚨 must reconcile actual position
  ↓
stop_placing
  - HL native reduce-only stop market (Section 19)
  ↓
stop_verified
  ↓
active
```

### 16.2 Runtime States

```yaml
ACTIVE:
  description: normal monitoring
  light-check: every 5 min
  hedge-sync: event-driven (delta-only adjustment, Section 17)
  deep-audit: every 6h

PAUSED:
  description: no new adjustments, existing hedge remains
  UI display: clearly show "Paused"
  light-check: skip
  hedge-sync: skip
  deep-audit: every 6h (still verify state)
  🚨 the hedge is not closed (different from carter2099)

CLOSING:
  description: closing LP and hedge
  detail: Section 16.6 LP_CLOSING flow

CLOSED:
  description: fully closed
  no further actions

SAFE_MODE:
  trigger:
    - HL API unreachable > 5 min
    - reconcile mismatch
    - suspicious state detected
    - margin critical (Section 18.4)
  behavior:
    - no new mutations
    - keep existing stop in place
    - continue monitoring price
    - alert user/admin
    - retry every 1 min
  recovery:
    - auto: when HL responsive + reconcile matches + margin recovered
    - manual: admin intervention
    - 🆕 v5.2.6 (B-2): on irrecoverable/limit-reached, bot_safe_close → to the §16.7 closed loop (do not make it a one-way ticket)

ERROR:
  description: admin intervention required
  trigger:
    - critical bug
    - data corruption
    - irrecoverable state
    - LP NFT ownership unexpected (Section 15.5)
  behavior: pause all activity, alert admin
```

### 16.3 Pause vs Close Semantics (important)

```yaml
🚨 Required: PAUSED ≠ CLOSED

PAUSED:
  - the hedge is maintained
  - the LP is also maintained
  - only new mutations are stopped
  - user intent: "pause for now, resume later"

CLOSED:
  - hedge closed
  - LP closed
  - full USDC return (via BnzaExVault, Section 16.4)
    🆕 v5.2.6 (Z-6): this is the user_redeem path description. In the bot_safe_close path, USDC is
    parked into uninvested_balances (§16.4 B / §16.7), and the return is at withdraw time (FundsWithdrawn).
  - user intent: "complete termination"

Clearly distinguish in the UI:
  Pause button: "Pause Bot (hedge is maintained)"
  Close button: "Close Bot (close everything, return USDC)"
```

### 16.4 LP Close Authority (🆕 v5.1 / 🆕 v5.2.6 B-2 split into 2 close/redeem systems)

```yaml
Since the LP NFT custodian = BnzaExVault (Section 15.5),
LP close can only be executed via Operator → BnzaExVault.

🚨 v5.2.6 (B-2 / Z-2): close has 2 systems. State is tracked in the close_operations ledger (§13.11),
  structurally preventing double repayment / double settlement (idempotency_key UNIQUE).
  The possible values of close_operations.state:
    requested / lp_closed / hedge_close_pending / hedge_closed /
    funds_returned / funds_parked / residual_hl_liability / done
  The **transition order is per kind**, and the canonical sources are the A (user_redeem = LP-first) / B (bot_safe_close =
  hedge-first) flows below (the single linear transition sequence is retired, because A's funds_returned position and
  B's lp_closed position differ).

  (A) user_redeem (user-initiated instant redemption):
      - the redeem tx instantly liquidates the LP and returns the LP-portion USDC to the user in the same tx
        (on-chain guarantee = formally adopt the HLD RedemptionQueue design).
      - the Worker processes the redeem event in the **highest-priority queue** and closes the hedge immediately
        (SLA: 5 min from detection = system_config: user_redeem_hedge_close_sla_minutes. overrun is escalation).
      - the HL-portion USDC is sent after hedge liquidation, tracked in the RedemptionQueue ledger.
  (B) bot_safe_close (system/Operator-initiated safe close):
      - full settlement in order hedge → LP. USDC is **parked into the Vault's uninvested balance**
        (redeployable. the user's withdraw right is always valid).
      - after completion, joins the §16.7 automatic re-entry closed loop.

— Below are the detailed flows of each system (🚨 v5.2.6 X-2: A / B fully separated.
  the old hedge-first "Standard Close Flow" is **retired**. user_redeem is LP-first) —

A. user_redeem (User initiated, LP instant liquidation first):
  state transition (close_operations.kind='user_redeem'):
    requested
      → lp_closed        : redeem tx confirmed. the LP-portion USDC goes **to the user in the same tx**
                           (BnzaExVault redeem, on-chain guarantee = HLD RedemptionQueue)
      → funds_returned   : LP-portion repayment complete (the user receives the LP value immediately)
      → hedge_close_pending : process the redeem event in the **highest-priority queue (user_redeem)**.
                             close the hedge immediately (SLA 5 min = system_config:
                             user_redeem_hedge_close_sla_minutes, overrun is escalation)
      → hedge_closed     : HL short reconciled = 0, the stop is cancel-only via §19.5
      → done             : send the HL-portion USDC to the user (tracked in the RedemptionQueue ledger)
    on failure:
      → residual_hl_liability : hedge close impossible. record the amount + escalation.
                                **do not stop the LP-portion repayment** (already funds_returned).
  key point: the LP repayment **does not depend on** hedge close (LP-first). user fund protection is the top priority.

B. bot_safe_close (System/Operator initiated, hedge first):
  Trigger:
    - Circuit breaker open + retry exhausted / Margin critical (SAFE_MODE recovery impossible)
    - hedge size > 0 after stop trigger fires (anomaly)
    - 3 stops within 7 days (A-4) / partial_repair exhausted (B-4) / SAFE_MODE terminus (§18.3)
    - Compliance / admin force close
  state transition (close_operations.kind='bot_safe_close'):
    requested → hedge_close_pending → hedge_closed (the stop is cancel-only via §19.5)
             → lp_closed → funds_parked (park USDC into the Vault's uninvested balance = uninvested_balances,
               §16.7 / X-3) → done → to the §16.7 automatic re-entry closed loop
    on failure: hedge close impossible → residual_hl_liability + SAFE_MODE (do not touch the LP)
  User notification required (acknowledge only, no action needed).

Emergency Close Path:
  Trigger:
    - emergency stop by Multi-sig admin
    - BnzaExVault contract bug detected
    - User wallet compromised (emergency withdraw from the User)
  Flow:
    1. Multi-sig approval
    2. BnzaExVault emergency function (a close path that works even in paused state)
    3. transfer the LP NFT directly from BnzaExVault to the user wallet
       (BNZA does not intermediate; the user can resolve the V3 NFT themselves)
    4. the Operator sets bot status = 'error'
    5. the HL hedge is closed separately by the user or by an admin
       (admin close is possible if the HL agent key is valid, Section 21.5)

USDC return authority relationships (🆕 v5.2.6 X-3, consistent with the INV-3 revision):
  - user_redeem path: the period BnzaExVault holds the post-close USDC is very short (within 1 tx).
    The transfer to the User wallet executes in the same tx. BNZA does not store USDC (custody risk eliminated).
  - bot_safe_close path (exception): the USDC is **parked** into the Vault's uninvested balance (uninvested_balances, §13.13).
    This is not custody but the unspent capital model (the same concept as HLD):
      ・the park is ledger-recorded + has a FundsParked event. The user's withdraw right is always valid
        (can be withdrawn anytime via FundsWithdrawn).
      ・it is re-invested as FundsRedeployed at §16.7 re-entry.
    → "BNZA does not store USDC" is the principle of the user_redeem path; the bot_safe_close
      park is an exception explicitly allowed by the INV-3 revision (ledger + event + always withdrawable).

  The performance fee is paid separately by BnzaExVault at close via the operator address
  (operation_fee → BNZA Token BuyBack&Burn, performance_fee → 10 recipients)
```

### 16.5 One-User One-Bot Policy (🆕 v5.1)

```yaml
Phase A:
  1 user = 1 active Ex Bot

  Reason:
    - complete the HL hedge with a single subaccount (concentrated margin / nonce management)
    - consolidate failure modes for debugging efficiency
    - simplify the LP NFT custody mapping to 1:1
  
  Implementation:
    - at bot start PREFLIGHT
       SELECT count(*) FROM bot_registry
        WHERE user_id = ? AND bot_type = 'ex'
          -- 🆕 v5.2.6 (B-7 / r1): include 'error' in the 1-bot isolation target (it can hold an unresolved position/hedge).
          --   cooldown / parked are lifecycle_state values, and those bots' status stays 'active', so
          --   they are already covered by this filter (§16.7). Therefore they are not listed in status IN.
          AND status IN ('active','paused','closing','safe_mode','error')
      if not 0, reject the start
    - UI: if an active Ex Bot already exists, disable "new start" and guide via the display

Phase B+:
  multiple bots per user unlocked

  🚨 v5.2.1 (P0-5) / v5.2.2 (P0-5): a realistic structure aligned with the Hyperliquid subaccount limit.
    **Unified to 1 bot = 1 subaccount** (resolves an internal contradiction).
    HL subaccount limits (official):
      - initial: 10 subaccounts per master account
      - max: 50 subaccounts (released in stages conditioned on trading volume)
    → expressions assuming the unlimited like a "pre-created subaccount pool" are retired.

  Implementation policy (realistic structure, unified to 1 bot = 1 subaccount in v5.2.2):
    - 1 user = N bots (N limited by plan, e.g. 3 / 10)
    - each bot is isolated in a separate HL subaccount (avoid nonce collision / margin contention)
    - **fixed at 1 bot = 1 subaccount**
      (the old "1 user 1 subaccount basis" expression is retired. the matrix is per bot)
    - master account capacity calculation:
       - 1 master account = max 50 subaccounts (HL limit, volume conditioned)
       - if exceeding 50 subaccounts, add a master account
         (the operator manages multiple master accounts, designed together with master/IP distribution)
    - example per-plan bot-count caps (a hard cap based on master capacity):
       - Basic plan:      1 user 1 bot  (= 1 subaccount)
       - Pro plan:        1 user 3 bots (= 3 subaccounts)
       - Enterprise plan: 1 user 10 bots (= 10 subaccounts)
       - ※ the unlimited plan is removed (does not align with the HL subaccount limit)
    - allocate a free subaccount at bot start (if insufficient, wait for a master expansion)
    - subaccount shortage blocks onboarding (capacity check in preflight)
    - UserLockDO is per user_id. The lock granularity is re-designed at Phase B start
      for subaccount parallelism (a known defer, §30.1)

  ⚠️ Verification needed (zen task): at Phase B start, spec out separately the master account
       expansion policy / subaccount allocation detail / master・IP distribution.
       Phase B detail is out of scope for this SPEC
       (only the fact of the HL limit was reflected in the v5.2.2 patch cycle; later patches keep it out of scope).
```

### 16.6 LP Operation State Machine (🆕 v5.1)

```yaml
LP_OPENING (after passing PREFLIGHT):
  states:
    LP_OPEN_REQUESTED → LP_OPEN_SWAPPING → LP_OPEN_MINTING → LP_OPENED
  
  detailed flow:
    1. LP_OPEN_REQUESTED:
       - user wallet → BnzaExVault: deposit USDC
       - BnzaExVault: confirm the receive event
    2. LP_OPEN_SWAPPING:
       - BnzaExVault: half USDC → WETH (V3 swap)
       - on failure: revert (USDC stays in the user wallet)
    3. LP_OPEN_MINTING:
       - BnzaExVault: NonfungiblePositionManager.mint(tickLower, tickUpper, USDC, WETH)
       - BnzaExVault itself receives the NFT
       - on failure: return USDC + WETH to the user wallet
    4. LP_OPENED:
       - Operator: create a row in D1 positions (custodian='vault')
       - Operator: set bots.lifecycle_state to 'lp_opened' (P0-8. status stays coarse-grained)
       - next, transition to hedge_pre_open (B-5: canonical lifecycle_state name)
  
  failure handling (LP_FAILURE):
    - LP_OPEN_SWAPPING failed → bot.status='error', user funds returned
    - LP_OPEN_MINTING failed → bot.status='error', user funds returned
    - if the Hedge open fails after this, walk back through Section 16.6 LP_CLOSING

LP_REBALANCING (range out etc.):
  trigger:
    - rangeState != 'in' in light-check
    - manual reset
    - Operator policy change (range pct change etc.)

  🚨 v5.2.1 (P0-9): on entry, set bots.lifecycle_state='lp_rebalancing'.
    while lifecycle_state=='lp_rebalancing':
      - the §17.1 canonical light-check skips via early-return
        (does not fire a normal range_out hedge-sync)
      - the hedge is controlled only by this state machine's "defensive partial pre-hedge"
      - at LP_REBAL_DONE, return lifecycle_state='active' and resume light-check
    This makes the §16.6 hedge policy "do not blindly move the hedge before confirmation"
    consistent with the execution path (light-check) (the old v5.2 did not change status, so
    light-check could fire a range_out hedge-sync even during rebalance).

  states:
    LP_REBAL_REQUESTED → LP_REBAL_DECREASING → LP_REBAL_SWAPPING → LP_REBAL_MINTING
                      → LP_REBAL_HEDGING → LP_REBAL_DONE
  
  hedge policy:
    - Do not blindly move hedge to future target before LP rebalance is confirmed.
    - Pre-hedge is allowed only as defensive partial adjustment.
    - Final hedge must be based on confirmed post-rebalance LP amount.

  recommended flow:
    1. Compute expected post-rebalance LP ETH amount.
    2. If current hedge is dangerously under-hedged, perform partial defensive
       delta-only hedge adjustment only.
    3. Operator → BnzaExVault.vaultRebalance(tokenId, newTickLower,
       newTickUpper, slippageBps)   // 🆕 v5.2.2 (P0-3-2): §15.5.6 ABI
    4. BnzaExVault.vaultRebalance internal: NFPM decreaseLiquidity 100% on old position
    5. BnzaExVault.vaultRebalance internal: collect fees
    6. BnzaExVault.vaultRebalance internal: swap (if needed)
    7. BnzaExVault.vaultRebalance internal: NFPM.mint new range
       → burn old tokenId, returns newTokenId
    8. After LP rebalance is confirmed onchain, recompute actual LP ETH amount.
    9. Operator: D1 positions update (token_id=newTokenId, tickLower,
       tickUpper, liquidity, ...)
    10. Run hedge-sync to final target from confirmed actual LP amount.
    11. LP_REBAL_DONE → return to ACTIVE

  if LP rebalance fails:
    - do not assume new LP state
    - enter SAFE_MODE
    - reconcile hedge against current confirmed LP state
    - alert admin/user

LP_CLOSING (🆕 v5.2.6 Y-2: the procedure canonical is unified into §16.4. This section is reduced to lifecycle definition only):
  trigger:
    - user close request        (→ §16.4 A: user_redeem = LP-first)
    - Operator force close       (→ §16.4 B: bot_safe_close = hedge-first)

  🚨 the canonical of the LP close execution order / state transitions is §16.4:
       A: user_redeem    = LP-first  (LP instant liquidation → LP-portion repayment → hedge close)
       B: bot_safe_close = hedge-first (hedge → LP → funds_parked → §16.7)
     Since A and B differ in order, the old single transition diagram "HEDGE_CLOSING first" is **retired** (Y-2).
     The internal stages of vaultClose (decreaseLiquidity → collect → swap → return/park) reference
     the §15.5.6 ABI / §16.4.

  This section (§16.6) specifies only the following:
    - the definition of lifecycle_state='lp_closing' (corresponds to bot.status='closing', P0-8/P0-9)
    - the §17.1 canonical light-check early-return skips for lifecycle_state in ('lp_closing','lp_rebalancing')
      (the concurrency control is on the state machine side)
    - the correspondence with close_operations (§13.11): each state transition takes the §16.4 A/B
      close_operations.state as canonical, and this section references it
      (requested → … → done / funds_parked / residual_hl_liability).

LP_FAILURE handling:
  invariants:
    - do not allow the LP NFT to float (not linked to any bot)
    - 🆕 v5.2.6 (X-3 / consistent with the INV-3 revision): do not allow "un-ledgered, un-authorized retention" of User funds.
      the user_redeem path returns within 1 tx. Only the bot_safe_close park is allowed as an exception, but
      always with the uninvested_balances ledger (§13.13) + a FundsParked event, and the withdraw right is always valid.
    - on failure, always admin alert + bot.status='error'
  
  representative failure modes:
    - swap slippage > tolerance → revert + retry with relaxed slippage
    - mint failed (gas / liquidity) → revert + return user funds
    - decrease failed (V3 contract issue) → admin manual recovery
    - WETH→USDC swap failed → bot.status='error', return WETH to the user
    - hedge close failed → enter SAFE_MODE (do not touch the LP)
  
  recovery:
    - can re-attempt from the admin manual flow
    - transfer the LP NFT directly to the user wallet via emergency multi-sig
```

### 16.7 Automatic re-entry (closed loop) (🆕 v5.2.6 / B-2, QA Codex C-4 / i-1)

```yaml
🚨 v5.2.6 (B-2): do not make SAFE_MODE / bot_safe_close a "one-way ticket". The terminus of the stop subsystem
  always joins this closed loop, and human intervention is only escalation handling (autonomous recovery).

States and transitions (lifecycle_state, §13.2 B-5):
  bot_safe_close completes
    → lifecycle_state='cooldown' (60 min. via system_config)
    → thereafter, re-entry judgment at a 60-min interval (system_config: reentry_check_interval_minutes):
         condition: 7d funding APR > -15% (system_config: reentry_funding_apr_floor,
               C-4: aggregate the latest 7 rows of funding_daily_metrics) and preflight pass
               (2.0x buffer = system_config: preflight_buffer, C-2)
         pass → automatically re-run the open flow (§16.1) → return to active
                funding source (🆕 X-3): **fully consume** that bot's uninvested_balances (§13.13)
                (FundsRedeployed). If there is no/insufficient park balance, abort the re-entry and
                **carry over to the next judgment** (not an escalation. wait for the balance to return or a manual deposit).
                redeploy canonical procedure (🆕 v5.2.6 Y-3, concurrency control):
                  1. acquire the UserLockDO bot lease (mutual exclusion with the withdraw API)
                  2. **read the on-chain balance via uninvestedBalanceOf(user, botId) (§15.5.6)**
                     (not D1). If insufficient, correct D1 to the real balance and abort re-entry (carry over to the next judgment)
                  3. send the redeploy tx. Since the Vault enforces the on-chain balance,
                     if it loses to a concurrent withdraw the tx reverts = a structural backstop
                  4. after the FundsRedeployed event confirms, update D1 to 0 (CAS:
                     UPDATE uninvested_balances SET amount_usdc='0'
                     WHERE user_address=? AND bot_id=? AND chain_id=? AND amount_usdc=:expected.
                     if it does not match, delegate to event-driven re-sync)
                  ※ the divergence between D1 and on-chain is always corrected toward on-chain (the on-chain-priority reconciliation principle, §13.13)
         fail → keep cooldown (re-judge at the next interval)
    → on the 3rd bot_safe_close within 7 days (system_config: safe_close_limit_7d):
         lifecycle_state='parked' (slow the judgment interval to 24h = system_config: parked_interval_hours)
         + admin escalation
    → recovery from parked is also an automatic judgment under the same conditions (human intervention is escalation handling only)

SAFE_MODE terminus (consistent with §18.3):
  - SAFE_MODE recovery impossible / limit reached → bot_safe_close (B-2) → joins this §16.7 cooldown
  - this eradicates the "stopped and nobody touches it" state

Notification:
  - notify the user on cooldown entry / re-entry success / parked transition (acknowledge only)

tunable (the canonical is §13.12 system_config. Below are the keys and defaults):
  - cooldown_minutes                = 60   (cooldown → the re-entry judgment interval)
  - reentry_check_interval_minutes  = 60   (the repeat interval of the re-entry judgment)
  - reentry_funding_apr_floor       = -15  (same value as C-4)
  - parked_interval_hours           = 24
  - safe_close_limit_7d             = 3    (bot_safe_close limit within 7 days)
  - hedge_stopped_cooldown_hours    = 4    (A-4)
```

---

## 17. Hedge Execution Flow (made delta-only in v5.1)

### 17.0 Summary of the v5.1 fix

```yaml
🚨 v5.1 fix:
  v5.0 designed hedge-sync to do a full close/open ("close existing → open new")
  every time. Change this to a delta-only adjustment.

Reason:
  - full close/open every time wastes subrequests (HL rate limit, CF subrequest)
  - extra fill cost / spread / funding discontinuity occurs when a partial adjustment would suffice
  - cloid / nonce advance wastefully
  - monitoring / reconcile is also redundant

New policy:
  delta = targetSize - actualSize
  
  if (|delta| <= dust)         → no-op
  if (delta > 0)                → additional short open IOC (size = delta)
  if (delta < 0 && targetSize>0) → reduce-only IOC (size = |delta|)
  if (delta < 0 && targetSize=0) → reduce-only full close + stop cancel
  
  Full close/open is allowed only for:
    - target size = 0 (= bot close / pause-for-full-close selected)
    - emergency reset (admin)
    - manual reset (on state corruption recovery)
```

### 17.1 Light Check Flow (does not touch HL) — 🚨 CANONICAL light-check implementation (v5.2.1)

```yaml
🚨 v5.2.1 (P0-2): this §17.1 is the only canonical implementation of light-check.
  §15.3 is reduced to an explanation of an example use of MarketDataDO and has no pseudocode body.
  the reason references the §7.6 RebalanceReason enum (P0-11).
  targetRatio is bps-integerized, going through float is forbidden (§7.6 / P0-6).
  while the LP operation state machine (§16.6) is in progress, light-check is suppressed (P0-9).
```

```typescript
// the rebalance reason uses the canonical RebalanceReason type of §7.6 (P0-11)
async function lightCheck(botId: string) {
  const data = await repo.getBotWithPositionAndState(botId);

  // P0-9: status / lifecycle_state guard.
  //   while the LP operation state machine (§16.6) is in progress, suppress light-check / hedge-sync.
  //   skip not only LP_CLOSING but also LP_REBALANCING (concurrency control is on the state machine side).
  if (data.bot.status !== 'active') return;            // paused/closing/safe_mode/etc
  if (data.bot.lifecycleState === 'lp_closing' ||
      data.bot.lifecycleState === 'lp_rebalancing') {
    return; // LP operation in progress (§16.6); the hedge is controlled by the state machine
  }

  // 🆕 v5.2.6 (A-1): fetch market first. The read-only safety monitoring
  //   (stop-crossed / near-stop / marker management) runs at all times, regardless of the
  //   circuit breaker state. The breaker only suppresses the hedge-sync enqueue later.
  const market = await marketData.getPoolState(data.position.poolAddress);
  const amount = calculatePositionAmount(data.position, market); // §6.4 pure function, no HL fetch

  // P0-6: bps-integerize targetRatio and compute in BigDecimal. Going through float (* 10000) is forbidden.
  const targetRatioBps = normalizeTargetRatioBps(data.hedge.targetRatio); // bigint, §7.6
  const targetShort = BigDecimal(amount.lpEthAmount).mul(targetRatioBps).div(10000);
  const currentShort = data.runtime.lastKnownHlShortSize;
  const drift = calculateDrift(targetShort, currentShort);

  // 🆕 v5.2.6 (D-1): no-op detection. Do not write if there is no diff from the latest persisted value (§5.2.1 write budget).
  await repo.updateRuntimeState(botId, {
    lpEthAmount: amount.lpEthAmount,
    targetShortSize: targetShort.toString(),
    currentTick: amount.currentTick,
    sqrtPriceX96: amount.sqrtPriceX96,
    uniPoolPrice: market.uniPoolPrice.toString(), // 🆕 X-5: the value is uniPoolPrice. The persisted column is bot_runtime_state.eth_price_usd (column name unchanged per §13.0)
    lpValueUsd: drift.lpValueUsd.toString(),
    healthStatus: drift.health,
    lastLightCheckAt: nowIso(),
  });

  // 🆕 v5.1 / v5.2.1 (P0-2): stop trigger crossed marker — GUARDED.
  //   if the marker is already set, do not overwrite stop_trigger_crossed_at.
  //   overwriting makes the §18.3 / NN#14 "marker stuck > 30 min → SAFE_MODE" never fire
  //   (because the timestamp would roll back to now on every light-check).
  //   crossed is not a normal hedge-sync reason; route it only to priority stop-audit
  //   (§19.3 / §7.3).
  // 🆕 v5.2.6 (A-2 / C-3): the comparison is byte-identical BigDecimal to §19.3, the price source is hlMarkPrice.
  //   going through float / Number() is forbidden. If hlMarkPrice is >120s stale, treat as undecidable (C-3 staleness).
  if (isStale(market.hlMarkUpdatedAt, 120)) {
    // C-3 staleness: stop undecidable → freeze hedge-sync, substitute-monitor with uniPoolPrice + 2× near-stop margin
    await stopAuditQueue.send({
      botId, markPriceUsd: market.uniPoolPrice.toString(), stopPriceUsd: data.hedge.stopPrice, // 🆕 X-5: on stale, uniPool fallback
      crossed: false, priority: "high", staleMark: true,
    }, { delaySeconds: 0 });
    return;
  }
  if (data.hedge.stopPrice && market.hlMarkPrice.gte(data.hedge.stopPrice)) {
    if (!data.hedge.stopTriggerCrossedAt) {
      await repo.markStopTriggerCrossed(data.hedge.id, nowIso()); // guarded: set once
    }
    await stopAuditQueue.send({
      botId,
      markPriceUsd: market.hlMarkPrice.toString(), // 🆕 X-5: stop judgment price = hlMarkPrice
      stopPriceUsd: data.hedge.stopPrice,
      crossed: true,
      priority: "high",
    }, { delaySeconds: 0 });
    return; // freeze hedge-sync until stop-audit reconciles the actual HL state
  }

  // near-stop (price within 2% of stop) is also not a normal hedge-sync reason;
  // route it to priority stop-audit (§19.3 urgent audit / §7.3).
  // 🆕 v5.2.6 (A-2 / C-3): near-stop uses hlMarkPrice. priceNearStop is BigDecimal.
  if (priceNearStop(market.hlMarkPrice, data.hedge.stopPrice)) {
    await stopAuditQueue.send({
      botId,
      markPriceUsd: market.hlMarkPrice.toString(), // 🆕 X-5: stop judgment price = hlMarkPrice
      stopPriceUsd: data.hedge.stopPrice,
      crossed: false,
      priority: "high",
    }, { delaySeconds: 0 });
    return;
  }

  // 🆕 v5.2.6 (W-5): primary detection of a STOP_REPLACING overrun (D1 read only, no HL call = weight 0).
  //   detects, at the light-check period (max 5 min), the case where a worker crash left an unprotected
  //   window because §19.5 finally's clearStopReplacing did not run (without waiting for the §19.3 audit's 6h). The §19.3 audit is
  //   kept as a secondary backstop. The detection is read-only, so place it before the breaker (run at all times).
  if (data.hedge.stopReplacingStartedAt &&
      secondsSince(data.hedge.stopReplacingStartedAt) > cfg.stop_replacing_deadline_seconds) { // §13.12 (60s)
    // the primary safety action holds independent of the message via enterSafeMode (W-5). The message below
    // only handles the follow-up repair routing (🆕 V-1: unify priority repair onto partialRepairQueue).
    await enterSafeMode(data, { reason: 'stop_replacing_overrun' });           // SAFE_MODE + admin alert (§18.3)
    await partialRepairQueue.send(makePartialRepairMessage(data.hedge, {
      reason: 'stop_replacing_overrun',
      attemptId: null,                       // attempt unknown because it is crash-originated
      expectedSize: data.hedge.size,         // the current size on the ledger (best known)
      actualSize: data.hedge.size,           // the consumer determines the real size via reconcile
    }), { priority: 'high' });
    return; // possibly unprotected → freeze mutation
  }

  // ── mutation suppression gate (after the read-only safety monitoring) ──────────────────
  // 🆕 v5.2.6 (A-1): the circuit breaker is a suppression device for mutation (hedge-sync).
  //   it must not gate the read-only safety monitoring above (stop-crossed / near-stop / marker / STOP_REPLACING overrun).
  //   it is precisely while the breaker is open that stop monitoring continues.
  const breaker = await getCircuitBreaker(data.hedge.id);
  if (breaker.state === 'open') return; // suppress only the hedge-sync enqueue (A-5: half_open allows a probe)

  // 🆕 v5.2.6 (A-4): during the automatic cooldown after a stop fires, stop the drift-driven
  //   automatic re-hedge (to prevent stop spamming). The LP/price update is done above. Do not emit hedge-sync.
  if (data.bot.lifecycleState === 'hedge_stopped_cooldown') return;

  // Canonical rebalance reasons (§7.6 RebalanceReason / P0-11).
  // because light-check does not touch HL, margin/funding are judged from the D1 persisted values.
  const reasons: RebalanceReason[] = [];
  // 🚨 v5.2.2 (P0-1): drift.* is BigDecimal. Math.max/float comparison is forbidden.
  //   constants are strings via BigDecimal('...'). calculateDrift returns BigDecimal.
  const driftThreshold = BigDecimal.max(BigDecimal('25'), drift.lpValueUsd.mul('0.03'));
  if (drift.usd.gt(driftThreshold))                       reasons.push('drift_threshold');
  if (drift.relative.gt(BigDecimal('0.15')))              reasons.push('drift_relative');
  if (amount.rangeState !== 'in')                         reasons.push('range_out');
  if (drift.rangeBoundaryNear)                            reasons.push('range_boundary_near');
  if (data.hedge.marginStatus === 'warning')              reasons.push('margin_warning');
  if (data.funding.alert7dAprLtMinus15Pct)                reasons.push('funding_alert');
  if (sinceLastAdjustmentHours(data) > 4)                 reasons.push('time_fallback');
  // Note: margin_critical routes to the §18.4.3 SAFE_MODE path, not hedge-sync
  //     (it is in the RebalanceReason enum but is not emitted from light-check).

  if (reasons.length > 0) {
    // 🆕 v5.2.6 (A-5): during half_open, let a probe through only once.
    //   enqueue only if half_open_probe_used could be atomically set 0→1 (§18.2 / §13.7).
    if (breaker.state === 'half_open') {
      const probeClaimed = await repo.tryClaimHalfOpenProbe(data.hedge.id);
      if (!probeClaimed) return; // probe already used → do not emit hedge-sync until the next reset
    }
    await hedgeSyncQueue.send({
      botId,
      reasons,                                   // canonical RebalanceReason[]
      expectedTargetSize: targetShort.toString(),
      stateVersion: data.runtime.stateVersion,
    });
  }
}
```

### 17.2 Hedge Sync Flow — Delta-only adjustment (has mutation)

```typescript
async function hedgeSync(
  botId: string,
  reasons: RebalanceReason[],   // 🚨 v5.2.3 (P1-B): use the canonical type (§7.6)
  stateVersion: number,
) {
  const data = await repo.getBotWithEverything(botId);
  
  // 0. Stale message guard
  if (data.runtime.stateVersion !== stateVersion) {
    return; // newer state already applied
  }
  
  // 1. Acquire UserLockDO (lease-based, Section 11)
  return await withUserLock({
    env,
    userId: data.user.id,
    ttlMs: 90_000,
    idempotencyKey: `hedge-sync:${botId}:${stateVersion}`,
    work: async () => await hedgeSyncInner(data, reasons),
  });
}

async function hedgeSyncInner(data: BotData, reasons: RebalanceReason[]) {
  // 🚨 v5.2.3 (P1-B): use the canonical type (§7.6)
  // 2. Reserve HL rate limit
  await hlRateLimit.reserve({ weight: 8, userAddress: data.user.hlUserAddress });
  
  // 3. Fetch actual HL position
  const account = {
    userAddress: data.user.hlUserAddress,
    vaultAddress: data.hedge.hlAccountAddress,
    agentKeyId: data.user.hlAgentKeyId,
  };
  const actualPosition = await hl.getPosition(account, 'ETH');
  const actualSize = BigDecimal(actualPosition?.size ?? '0');
  
  // 4. Recompute target from fresh market cache
  const market = await marketData.getPoolState(data.position.poolAddress);
  const amount = calculatePositionAmount(data.position, market);
  // 🚨 v5.2.2 (P0-1): go through the canonical bps path (§7.6).
  //   do not pass data.hedge.targetRatio directly into BigDecimal (going through float is forbidden).
  const targetRatioBps = normalizeTargetRatioBps(data.hedge.targetRatio); // bigint, §7.6
  const targetSize = BigDecimal(amount.lpEthAmount).mul(targetRatioBps).div(10000);
  
  // 5. Margin preflight (Section 18.4)
  const margin = await hl.getMarginSummary(account);
  const marginCheck = evaluateMargin(margin, targetSize, market.hlOraclePrice); // 🆕 C-3: margin uses hlOraclePrice
  if (marginCheck.status === 'critical') {
    await enterSafeMode(data, marginCheck);
    return;
  }
  // 🆕 v5.2.6 (C-1, QA CC M-6 / Codex M-3): during warning, forbid the size-increase direction (delta>0) and
  //   allow only reduction. If an increase is needed, record skipped_margin_warning and re-evaluate next tick.
  const marginWarning = marginCheck.status === 'warning';
  
  // 6. Compute delta
  const delta = targetSize.sub(actualSize);
  // 🆕 v5.2.6 (B-3): when targetSize=0 (close cases), bypass the dust check and
  //   reduce-only close the entire HL-recognized remainder (do not allow leaving dust). Remainder that cannot be
  //   cleared below the minimum close size is amount-recorded into close_operations.state='residual_hl_liability' for
  //   escalation and excluded from active hedge math (§16.2 / B-2).
  const dust = computeDust(market.hlMarkPrice);  // e.g. $5 worth in ETH (🆕 C-3: hedge size basis = hlMarkPrice)
  if (!targetSize.eq(0) && delta.abs().lt(dust)) {
    return; // no-op (normal delta-only only. close cases with targetSize=0 are excluded)
  }

  // 🆕 v5.2.6 (C-1): do not execute when margin warning and the size-increase direction (delta>0).
  //   skip before stop cancel / attempt creation, so neither an unprotected window nor a wasted attempt is created.
  //   the reduction direction (delta<0) and close (targetSize=0) are executed even during warning.
  if (marginWarning && delta.gt(0)) {
    await repo.recordSkippedMarginWarning(data.bot.id, data.hedge.id); // re-evaluate next tick
    return;
  }
  
  // 7. Create rebalance_attempt
  const attemptId = await repo.createAttempt(data.bot.id, {
    hedgeLegId: data.hedge.id,
    asset: 'ETH',
    stateVersion: data.runtime.stateVersion,
    oldSize: actualSize.toString(),
    targetSize: targetSize.toString(),
    // 🚨 v5.2.3 (P1-B): reasons is RebalanceReason[] (canonical, §7.6).
    //   .join(',') works like string[], so no runtime change.
    reason: reasons.join(','),
  });
  
  try {
    // 🚨 v5.2.6 (X-1 / W-2 / INV-STOP): calling stop cancel/place directly outside §19.5 is forbidden.
    //   responsibility for the execution/order of stop replacement is held by §19.5 replaceStopProtected (single execution point).
    //   §17.2 calls it once at step 11 (Y-1 responsibility boundary).
    //   the old stop is maintained even during delta adjust (INV-STOP); §19.5 atomically replaces it after reconcile.
    // 8. (deleted) — stop cancel is integrated into §19.5 replaceStopProtected (step 11)
    
    // 9. Delta-only adjustment (v5.1 core change)
    if (targetSize.eq(0)) {
      // target = 0: full close (only allowed exit path for size=0)
      if (actualSize.gt(0)) {
        const closeCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'close', version: 1 });
        await hl.closeShortReduceOnlyIoc({
          account, asset: 'ETH', size: actualSize.toString(), cloid: closeCloid,
        });
      }
    } else if (delta.gt(0)) {
      // target > actual: open additional short
      const adjustCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'adjust', version: 1 });
      await hl.adjustShortDelta({
        account, asset: 'ETH', deltaSize: delta.toString(), direction: 'increase', cloid: adjustCloid,
      });
    } else {
      // target < actual: reduce short (reduce-only IOC)
      const adjustCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'adjust', version: 1 });
      await hl.adjustShortDelta({
        account, asset: 'ETH', deltaSize: delta.abs().toString(), direction: 'decrease', cloid: adjustCloid,
      });
    }
    
    // 10. Reconcile actual position
    await sleep(2000); // wait for HL to settle
    const reconciled = await hl.reconcilePosition(account, 'ETH', targetSize.toString());
    
    // 11. Stop replacement/cancel — unified into §19.5 protected (X-1). Do not call cancel/place individually.
    if (BigDecimal(reconciled.actualSize).gt(0)) {
      const newStopParams = {
        size: reconciled.actualSize,
        triggerPx: computeStopTriggerPx({
          entryPrice: reconciled.entryPrice,
          liquidationPrice: reconciled.liquidationPrice,
          effectiveLeverage: reconciled.effectiveLeverage, // see Section 19.1
        }).toString(),
        cloid: makeCloid({ botId: data.bot.id, attemptId, stage: 'stop', version: 1 }),
        attemptId, // 🆕 W-3: used by §19.5 when enqueuing partial_repair (stop_replace_failed_restored)
      };
      // §19.5 chooses the stop replacement procedure inside replaceStopProtected based on the NV-3 result.
      await replaceStopProtected(env, data.hedge, newStopParams, NV3_STRATEGY);
    } else {
      // targetSize=0 / full close: a new stop is not needed. The old stop is cancelled only via §19.5.
      await replaceStopProtected(env, data.hedge, null, NV3_STRATEGY); // null = cancel-only
    }
    
    // 12. Mark success/partial/failed
    if (reconciled.match) {
      await repo.markAttemptSuccess(attemptId, reconciled.actualSize);
      await repo.updateRuntimeState(data.bot.id, {
        lastKnownHlShortSize: reconciled.actualSize,
        lastHlReconcileAt: nowIso(),
        stateVersion: data.runtime.stateVersion + 1,
      });
      // 🆕 v5.2.6 (A-5): reset the circuit breaker only on success.
      //   the stored column circuit_breakers.state is canonical (§13.7 / §18.2). do not reset on partial / failed.
      await resetCircuitBreaker(data.hedge.id);
    } else {
      // 🆕 v5.2.6 (B-4): partial is an unsafe state. Treat it as a first-class citizen (consistent with A-5).
      // ① immediately persist reconciled.actualSize to D1 (do not leave it stale)
      await repo.markAttemptPartial(attemptId, reconciled.actualSize, reconciled.expectedSize);
      await repo.updateRuntimeState(data.bot.id, {
        lastKnownHlShortSize: reconciled.actualSize,
        lastHlReconcileAt: nowIso(),
        stateVersion: data.runtime.stateVersion + 1,
      });
      // ② do not reset the circuit breaker (A-5). the consecutive count of partials is handled by the ④ repair count
      // ③ verify/restore the stop's existence/size for actualSize (§19.5 INV-STOP protected replacement)
      if (BigDecimal(reconciled.actualSize).gt(0)) {
        await ensureStopForSize(data, account, reconciled); // §19.5
      }
      // ④ to the partial_repair priority queue. SAFE_MODE after 3 retries
      const repairAttempts = await repo.countRecentPartialRepairs(data.hedge.id);
      if (repairAttempts >= 3) {
        await enterSafeMode(data, { reason: 'partial_repair_exhausted' });
      } else {
        await partialRepairQueue.send(
          { botId: data.bot.id, hedgeLegId: data.hedge.id, attemptId,
            expectedSize: reconciled.expectedSize, actualSize: reconciled.actualSize,
            reason: 'partial_reconcile' }, // 🆕 W-3: conforms to the §10.1 schema
          { priority: 'high' },
        );
      }
    }

  } catch (e) {
    await repo.markAttemptFailed(attemptId, e);
    await incrementCircuitBreaker(data.hedge.id, e);
    await notifyFailedRebalance(data.user, attemptId, e);
    throw e;
  }
}
```

### 17.3 Reconcile Flow (important)

```yaml
🚨 important: success ≠ order submitted
🚨 important: success = actual position confirmed

Reconcile steps:
  1. after order submission, wait 2 seconds (HL internal settlement)
  2. clearinghouseState fetch
  3. compare expected size and actual size
  4. success if within tolerance
  5. if there is divergence, partial, consider retry

🆕 v5.1:
  extract entry_price / liquidation_price / effective_leverage from the reconcile result and
  save to the hedge_legs table (used for the stop computation in Section 19)
```

### 17.4 Cases where Full Close/Open is allowed (v5.1)

```yaml
In v5.1 it is delta-only in principle. Full close/open is allowed only for:

1. target size = 0:
   - bot close path (Section 16.6 LP_CLOSING)
   - emergency stop (admin force)
   → a single close, open is not needed

2. emergency reset (admin invoked):
   - state corruption recovery
   - circuit breaker manual reset
   - reconcile HL state vs DB consistency
   → close → open (with new cloid version) to clear everything

3. manual reset (user invoked, Phase B+):
   - range change (if making range pct changeable in Phase B+)
   - hedge ratio change
   - subaccount migration
   → close → open

All other cases (drift / range out / near stop / time fallback / stop crossed) are
all delta-only adjustment.
```

---

## 18. Failure Handling

### 18.1 Error Classification

```yaml
| Error                          | Retry? | Circuit | Action                     |
|-------------------------------|--------|---------|----------------------------|
| Network timeout               | yes    | no      | retry with jitter          |
| HL 429 rate limit             | delayed| no      | route through rate limiter |
| Min order / min notional      | no     | yes     | pause leg, notify          |
| Insufficient margin           | no     | yes     | user action required (18.4)|
| Unauthorized agent            | no     | yes     | re-approval required (21.5)|
| Duplicate cloid               | no     | no      | reconcile first            |
| Reduce-only rejected          | maybe  | maybe   | reconcile state            |
| Stop would immediately trigger| no     | maybe   | recompute / alert          |
| Open failed after close       | controlled | maybe | reconcile first         |
| Partial fill mismatch         | yes    | no      | repair job                 |
| HL API unreachable            | yes    | no      | enter SAFE_MODE            |
| RPC unreachable               | yes    | no      | failover provider (Phase C)|
| LP NFT ownerOf mismatch       | no     | yes     | bot.status='error', alert  |
```
### 18.2 Circuit Breaker Logic (PK = hedge_leg_id)

```typescript
// 🆕 v5.2.6 (A-5): the canonical source is the stored column circuit_breakers.state. Dynamic computation from history is retired.
//   incrementCircuitBreaker accrues the failure count in the stored column and transitions to open after 3 in a row.
//   here we judge "may hedge-sync go through" from the stored column (consistent with the §13.7 transitions).
async function getCircuitBreaker(hedgeLegId: string): Promise<{ state: 'closed'|'open'|'half_open' }> {
  let cb = await repo.getBreaker(hedgeLegId); // the stored circuit_breakers row
  if (!cb) return { state: 'closed' };

  // open and reset_at reached → unlock to half_open (allow 1 probe)
  if (cb.state === 'open' && cb.resetAt && nowIso() >= cb.resetAt) {
    await repo.setBreaker(hedgeLegId, { state: 'half_open', halfOpenProbeUsed: 0 });
    cb = { ...cb, state: 'half_open', halfOpenProbeUsed: 0 };
  }
  return { state: cb.state };
}

// whether to let hedge-sync through (called from §17.1). half_open is true for only 1 probe.
async function allowHedgeSync(hedgeLegId: string): Promise<boolean> {
  const cb = await getCircuitBreaker(hedgeLegId);
  if (cb.state === 'closed')   return true;
  if (cb.state === 'open')     return false;          // suppress hedge-sync (stop monitoring continues in §17.1)
  // half_open: let a probe through only once (atomically set half_open_probe_used 0→1)
  const claimed = await repo.tryClaimHalfOpenProbe(hedgeLegId); // true only once
  return claimed;
}

Open conditions:
  - 3 failed attempts within 24h (failure_count managed in the stored column. open at 3, reset_at=now+1h)
  - permanent validation error
  - unauthorized agent
  - insufficient margin (repeated)

State transitions (§13.7 canonical):
  - closed →(3 consecutive failures)→ open(reset_at=now+1h)
  - open →(reset_at reached)→ half_open(allow 1 probe)
  - half_open →(probe success)→ closed /(probe fail)→ open(reset_at re-set)

Reset conditions (back to closed):
  - the half_open probe hedge-sync succeeds (A-5: reset only on success)
  - manual reset (admin)
  - config changed (target ratio etc)
  ※ do not reset on partial / failed (§17.2 / B-4).
```

### 18.3 SAFE_MODE Behavior

```yaml
trigger conditions:
  - HL API unreachable > 5 min
  - reconcile mismatch (actual ≠ expected)
  - suspicious state detected
  - 🆕 (v5.1) margin status = 'critical' (Section 18.4)
  - 🆕 (v5.1) stop_trigger_crossed_at marker stuck > 30 min
  - 🆕 v5.2.6 (Z-5) stop_replacing_started_at stuck > 60s (a catcher for when a worker abnormal exit
    did not run finally's clearStopReplacing. detection is in the §19.3 / §20.2 audit, the predicate is in §19.3)

🚨 v5.2.1 (P0-2) — guarantee that marker-stuck detection fires correctly:
  predicate: now - hedge_legs.stop_trigger_crossed_at > 30 min
  premise: stop_trigger_crossed_at is set GUARDED by the §17.1 canonical light-check
        (if already non-NULL, do not overwrite).
        This means the timestamp does not roll back to now on every 5-minute light-check,
        so the 30-minute lapse can be detected reliably.
        (with the old v5.2 §15.3 unconditional re-mark, this condition never
         fired — fixed in P0-2 / NN#14).
  resolve path: the priority stop-audit either resolves the marker in one of cases A-D
        or transitions to this SAFE_MODE (§19.3).

forbidden in SAFE_MODE:
  ❌ cancel existing stops
  ❌ open new positions
  ❌ rebalance hedge
  ❌ rebalance LP
  ❌ change leverage
  ❌ withdraw margin

allowed in SAFE_MODE:
  ✅ read state
  ✅ retry HL connectivity
  ✅ alert user/admin
  ✅ continue light-check (the non-HL part)
  ✅ deep audit (when HL recovers)
  ✅ priority stop audit (when stop_trigger_crossed flagged)

recovery:
  auto: HL responsive + 3 successful reconciles + margin status returned to 'ok'
  manual: admin intervention via dashboard
  # 🆕 v5.2.6 (B-2): do not make SAFE_MODE a one-way ticket.
  terminus: when irrecoverable / limit reached by either auto/manual, start bot_safe_close (§16.4 B)
            and join the §16.7 cooldown closed loop (eradicate stuck-stopped states).
```

### 18.4 Insufficient Margin UX (🆕 v5.1)

```yaml
Handle margin in 3 levels:
  ok       → normal operation
  warning  → notify user, continue light-check, hedge-sync carefully
  critical → enter SAFE_MODE

Definitions:
  # 🆕 v5.2.6 (C-2, QA CC M-4 / Codex M-3): fix the margin terminology.
  marginRequiredUsd = initial margin = the assumed short notional ÷ leverage
                      (notional = lpEthAmount × hedgeRatio × hlOraclePrice, then ÷ leverage  # 🆕 X-5: margin evaluation uses hlOraclePrice)
  marginBalanceUsd  = the isolated equity allocated to that position
                      (the exact HL API field is finalized in §0.5 NV-1)
  marginUsage = marginRequiredUsd / marginBalanceUsd
              (= equivalent to 1 - (marginBalanceUsd - marginRequiredUsd) / marginBalanceUsd)

  ok:        marginUsage < 0.55
  warning:   0.55 <= marginUsage < 0.75
  critical:  marginUsage >= 0.75

  The thresholds above are finalized via Phase 0 backtest (⚠️ Verification needed (zen task))
```

#### 18.4.1 Preflight Margin Check (at Bot start)

```yaml
Run in PREFLIGHT:
  1. fetch the user's HL margin balance
  2. compute the expected target hedge notional
     notional = lpEthAmount × hedgeRatio × hlOraclePrice  # 🆕 X-5: margin evaluation uses hlOraclePrice (§15.1)
  2.5. 🆕 v5.2.6 (D-5, QA CC i-4): the hedgeRatio of notional goes through the canonical bps path
       (§7.6 normalizeTargetRatioBps) (direct float multiplication is forbidden).
  3. required margin = notional / leverage   (= marginRequiredUsd, §18.4 C-2)
  4. 🆕 v5.2.6 (C-2): the bot cannot start unless expected post-deposit margin balance >= required margin × 2.0
     (100% buffer = system_config: preflight_buffer).
     → marginUsage right after start = required / (2.0 × required) = 0.50 = falls in the ok band
       (with the old ×1.5 there was an inconsistency where marginUsage was 0.667 = the warning band right after start).
     example: notional = 0.5 ETH × 0.7 × $3000 = $1050, required = $1050 / 3 = $350,
         required balance = $350 × 2.0 = $700
  5. UI display:
     "Required HL margin: $X (with 100% buffer)
      Current HL margin: $Y
      Status: [Sufficient / Insufficient — please deposit $Z to HL]"

When insufficient:
  - block the bot start
  - guide "please deposit an additional $Z to HL and then start again"
  - explain the HL deposit procedure in the UI (via CCTP / Across, executed on the user side)
```

#### 18.4.2 Margin Warning / Critical while Active

```yaml
# 🆕 v5.2.6 (C-5, QA CC M-2): light-check does not touch HL at all (restores the weight 0 invariant).
#   the old "fetch margin inside light-check once every 30 minutes (weight 2)" contradicted the
#   "light-check does not touch HL" of §4.2/§5.3/§9.2/§17.1, so it is deleted.
where margin status is updated (HL marginSummary fetch is only here):
  - just before hedge-sync (Section 17.2 step 5)
  - deep-audit (Section 20.2)
  ❌ margin fetch inside light-check is forbidden. light-check only reads the D1
     hedge_legs.margin_status (it does not update it).

transitions of hedge_legs.margin_status:
  ok → warning:
    - push an alert to the user (POOL UI banner + email; Phase A is UI banner only)
    - disable size-increase-direction adjustments in hedge-sync (allow size reduction only)
    - the Bot stays active
  
  warning → critical:
    - enter SAFE_MODE (Section 18.3)
    - alert the admin too
    - guide the User "you need an additional deposit to HL"
  
  critical → warning:
    - auto-transition when margin recovers (the user adds a deposit)
    - part of the SAFE_MODE recovery condition
  
  warning → ok:
    - auto-transition when margin recovers further
    - lift the hedge-sync constraint
```

#### 18.4.3 SAFE_MODE entry conditions (margin perspective, reorganized in v5.1)

```yaml
margin-originated conditions to enter SAFE_MODE:
  1. margin_status = 'critical' detected twice in a row (false-positive prevention)
  2. a hedge-sync failure where HL returned an insufficient margin error
  3. effective_leverage > 4.5 (exceeded the 3x configured = a dangerous level)
     ※ effective_leverage is computed as notional_usd / isolated_margin_usd
  4. liquidation_price within 5% of the current ETH price (🆕 C-3: hlMarkPrice)
```

---

## 19. Native Stop Lifecycle (redefined in v5.1)

### 19.0 Redefinition of the meaning of Stop (important)

```yaml
🚨 v5.1 fix:
  v5.0 described the stop as "insurance to avoid liquidation", but
  precisely the stop is a loss cap, a separate thing from liquidation avoidance.

  - liquidation is HL's automatic execution (on margin shortage)
  - the stop is an intentional loss realization (close reduce-only when price exceeds the trigger)
  
  in reality:
    a stop being triggered ≒ loss realization + position size going to 0 + delta imbalance with the LP
  
  v5.1 makes the following explicit:
  
  - the stop is a device to "suppress" loss, designed to fire before liquidation
  - but even when the stop fires, the loss at that point is realized
  - 🆕 v5.2.6 (A-4): after the stop fires, the bot keeps the LP and rides an automatic ladder.
    the operation "the user decides to rebuild the hedge / close the LP" is retired, and it
    autonomously recovers via hedge_stopped_cooldown → automatic re-hedge → (on repeats) bot_safe_close → §16.7 closed loop
    (details in §19.3 / §16.7). User operations are only acknowledging the notification and optional redeem.
  - the stop is not a mechanism to save the LP side (the LP-side IL occurs separately)
```

### 19.1 Dynamic computation of stopTriggerPx (v5.1)

```yaml
v5.0 used a fixed stopTriggerPx = entry × 1.10, but
v5.1 prefers the actual liquidationPx and dynamically computes via an
effective_leverage-based fallback approximation only when it cannot be obtained.

Inputs (obtained from HL reconcile, saved to hedge_legs):
  entry_price        = position.entryPx
  liquidation_price  = position.liquidationPx (always prefer when obtainable)
  notional_usd       = abs(position_size_eth) × entry_price
  effective_leverage = notional_usd / isolated_margin_usd
  not:
    isolated_margin_usd / notional_usd
	  
Formula (short position, ETH-USD short):
  if liquidation_price is available:
    liq_distance_pct = (liquidation_price - entry_price) / entry_price
  else:
    liq_distance_pct ≒ 1 / effective_leverage
    ※ fallback approximation only

  Actual liquidation shifts due to changes in maintenance margin / funding / mark-oracle price /
  isolated margin. The distance from effective_leverage is a
  safety estimate and does not replace the HL position's liquidationPx.
  
  stop_distance_pct = liq_distance_pct × stopSafetyFactor
  
  stopSafetyFactor:
    Phase A:  0.70  (stop at the 70% point before liquidation)
    Phase B+: tuned via backtest (⚠️ Verification needed (zen task))
  
  stop_trigger_px = entry_price × (1 + stop_distance_pct)
  
example: entry $3000, effective_leverage = 3.1x
  liq_distance_pct ≒ 32.3%
  stop_distance_pct = 32.3% × 0.70 = 22.6%
  stop_trigger_px = $3000 × 1.226 = $3678
  
  This secures more buffer to liquidation than v5.0's "entry × 1.10",
  and avoids a too-early stop (= unnecessary loss realization).
```

```typescript
// 🆕 v5.2.6 (A-2): fully BigDecimal-ized. The formula is unchanged (per the cross-checked formula of §19.1).
//   the stop trigger price is a safety-critical value that determines the loss cap. Going through float / number is forbidden.
function computeStopTriggerPx(input: {
  entryPrice: Decimal;
  liquidationPrice?: Decimal;
  effectiveLeverage: Decimal;
  safetyFactor?: Decimal;  // default 0.70 (Phase A)
}): Decimal {
  const safety = input.safetyFactor ?? BigDecimal('0.70');
  const liqDistancePct = input.liquidationPrice
    ? input.liquidationPrice.sub(input.entryPrice).div(input.entryPrice)
    : BigDecimal('1').div(input.effectiveLeverage); // fallback approximation only
  const stopDistancePct = liqDistancePct.mul(safety);
  return input.entryPrice.mul(BigDecimal('1').add(stopDistancePct));
}

function computeEffectiveLeverage(input: {
  sizeEth: Decimal;
  entryPrice: Decimal;
  isolatedMarginUsd: Decimal;
}): Decimal {
  const notionalUsd = input.sizeEth.abs().mul(input.entryPrice);
  if (input.isolatedMarginUsd.lte(0)) {
    throw new Error("invalid isolated margin");
  }
  return notionalUsd.div(input.isolatedMarginUsd);
}
```

### 19.2 Stop Placement (coordination with delta-only)

```yaml
on hedge open (size 0 → > 0):
  1. open short (IOC)
  2. wait for fill
  3. reconcile actual size
  4. extract entry_price / liquidation_price / effective_leverage
  5. save to hedge_legs (Section 13.2)
  6. compute stop_trigger_px (Section 19.1)
  7. place reduce-only stop with computed trigger
  8. verify stop placed (single confirmation)
  9. record stop_cloid, stop_order_id, stop_price, stop_size, stop_distance_pct in DB

on hedge resize (delta-only adjustment):
  🚨 v5.2.6 (A-3): this v5.0/v5.1 procedure was replaced by §19.5 INV-STOP.
    The canonical execution order is §19.5 (the NV-3 result finalizes whether it is (a) place-before-cancel or
    (b) protected cancel→place). Reference the Steps A–G below
    only as the step detail of the (b) path.
  v5.0: cancel old stop → close diff → place new stop
  v5.1: cancel old stop → adjust delta → reconcile → place new stop
  
  Stop placement order (v5.1 → the detail of the §19.5 (b) path):
    Step A: cancel old stop (by cloid)
    Step B: delta adjust (open additional / reduce-only)
    Step C: reconcile new size
    Step D: extract updated entry_price / liquidation_price (HL updates via a weighted average)
    Step E: re-compute stop_trigger_px
    Step F: place new stop with new cloid (version + 1)
    Step G: verify

on hedge close (size > 0 → 0):
  1. cancel stop
  2. close position
  3. reconcile (size = 0)
  4. clear stop_cloid / stop_price / stop_distance_pct in DB

Hyperliquid Stop Direction Live Test:
  Short position close requires buy reduce-only trigger.
  Confirm on testnet/live-small:
    - side: buy for short close
    - reduce-only flag
    - triggerPx direction
    - tpsl value
    - mark-price trigger behavior
    - immediate-trigger rejection
    - p/orderPx behavior for trigger market
    - vaultAddress + agent key compatibility
    - cancelByCloid behavior
```
### 19.3 Stop Audit (priority audit added in v5.1)

```yaml
periodic audit:
  cadence: 6h normal
  scope: distribute across all bots (avoid burst)
  check:
    - stop exists in HL openOrders?
    - stop size matches DB?
    - stop side correct (buy)?
    - stop reduce-only?
    - stop trigger based on mark price?
    - 🆕 v5.1: hedge_legs.last_stop_audit_at update
    - 🆕 v5.2.6 (Z-5 / W-5): the catcher for a STOP_REPLACING 60s overrun.
        🚨 the primary detection is §17.1 light-check (max 5-min period, weight 0). This audit is the **secondary backstop**.
        predicate: hedge_legs.stop_replacing_started_at IS NOT NULL AND
                now - stop_replacing_started_at > stop_replacing_deadline_seconds (60s, §13.12)
        → SAFE_MODE + priority repair + admin alert
        (the catcher for when a worker abnormal exit did not run §19.5 finally's clearStopReplacing.
         consistent with §17.1 primary detection / §18.3 trigger / §19.5 finally)

urgent audit triggers (priority):
  - ETH price within 2% of stop trigger
  - 🆕 v5.1: ETH price >= stop_price (immediate enqueue, stop_trigger_crossed_at marker)
  - HL API/order error detected
  - reconcile mismatch
  - bot status change

Stop trigger crossed (v5.1 detail):
  when light-check observes ETH price >= stop_price,
    1. mark hedge_legs.stop_trigger_crossed_at = now
    2. priority-enqueue to the stop-audit queue (delaySeconds=0)
    3. do not enqueue normal hedge-sync
    4. freeze normal hedge adjustment until stop-audit reconciles the actual HL state
    5. treat lastKnownHlShortSize as stale until reconciliation completes
  
  stop-audit worker:
    - HL clearinghouseState fetch
    - confirm whether the native stop has fired
    - reconcile the actual short size
       case A: stop triggered + position size = 0
              → update DB consistency (lastKnownHlShortSize = 0, clear stop_cloid)
              → resolve stop_trigger_crossed_at
              → 🆕 v5.2.6 (A-4): transition bots.lifecycleState = 'hedge_stopped_cooldown'
                (keep the LP. the new hedge is rebuilt by the automatic ladder, not user judgment)
              → notify the user (acknowledge only. no action needed)
       case B: stop is still pending (a price spike but not filled in the market)
              → wait and see (re-check at the next audit cycle)
       case C: stop missing / mismatch (cloid not found, size/side mismatch)
              → enter SAFE_MODE + admin alert
       case D: position size > 0 but stop is triggered (= partial fill anomaly)
              → enter SAFE_MODE + admin alert
    - stop order missing / partial / mismatch is SAFE_MODE
    - stop_trigger_crossed_at is either resolved or transitions to SAFE_MODE

  🆕 v5.2.6 (A-4) automatic policy after the stop fires (the ladder after case A. no user judgment needed):
    1. after case A, transition bots.lifecycleState='hedge_stopped_cooldown'
       - light-check only does LP/price update (§17.1). hedge-sync enqueue is forbidden
       - reason: prevent stop spamming from drift-driven automatic re-hedge
    2. after cooldown elapses (cooldown = 4h, via system_config):
       - automatically rebuild the hedge based on the current LP delta (open flow → return to ACTIVE)
    3. 3 stop fires within 7 days:
       - start bot_safe_close (B-2) → join the §16.7 closed loop
    4. notify the user on each transition (acknowledge only, no action needed)

  related states (added in §13.2 lifecycle_state / B-5):
    hedge_stopped_cooldown / cooldown / parked

  light-check pseudocode:
    // 🚨 v5.2.1 (P0-2): the canonical implementation is §17.1. This is an excerpt from the §19.3 perspective.
    //   markStopTriggerCrossed is GUARDED (if already set, do not overwrite the
    //   timestamp). overwriting invalidates the §18.3 / NN#14 stuck>30min detection.
    //   it must be completely identical logic to the canonical.
    // 🆕 v5.2.6 (A-2 / C-3): the price source is hlMarkPrice, BigDecimal comparison (byte-identical to §17.1).
    if (data.hedge.stopPrice && market.hlMarkPrice.gte(data.hedge.stopPrice)) {
      if (!data.hedge.stopTriggerCrossedAt) {
        await repo.markStopTriggerCrossed(data.hedge.id, nowIso()); // guarded: set once
      }
      await stopAuditQueue.send({
        botId,
        markPriceUsd: market.hlMarkPrice.toString(), // 🆕 X-5: stop judgment price = hlMarkPrice
        stopPriceUsd: data.hedge.stopPrice,
        crossed: true,
        priority: "high",
      }, { delaySeconds: 0 });

      // Important:
      // Do not run normal hedge-sync until stop-audit reconciles actual HL state.
      return;
    }

🚨 forbidden:
  ❌ check every stop for every bot every 5 min (exceeds the subrequest limit)
  ❌ leaving the stop_trigger_crossed marker set for more than 30 min
     (after set, always resolve it via the priority audit path)
```

### 19.4 Relationship of Stop and Liquidation (made explicit)

```yaml
Intent of stop placement:
  - stop_trigger_px is before liquidation_price
  - if the stop is triggered, liquidation is not reached (ideal)
  - but the stop is a market order, so the fill price may be bad due to slippage
  - because it is mark-price based, it fires on the oracle / book mid, not your own last trade

Cases where liquidation occurs:
  - a sharp price move while stop cancel/replace is impossible due to an HL API failure
  - the stop cannot be filled due to market liquidity drying up (= the liquidation engine picks it up)
  - margin decreases unexpectedly (funding payment / loss on another leg)
  - the stop had been removed by the user's manual operation (needs audit)

Make explicit to the User:
  "the stop is a mechanism to cap loss; it does not completely prevent liquidation.
   In particular, the stop may not be in time during a flash crash or API failure."
```

### 19.5 Protected stop replacement (🆕 v5.2.6 / A-3, QA Codex C-1)

```yaml
🚨 Invariant (INV-STOP):
  while the HL short is non-zero, a verified reduce-only stop must always exist.
  The exception is only during the STOP_REPLACING critical section
  (limit 60 seconds = system_config: stop_replacing_deadline_seconds, record the start time in D1).

🚨 Responsibility boundary (🆕 v5.2.6 Y-1):
  this function replaceStopProtected handles **only stop replacement**. delta adjustment / reconcile are
  the responsibility of the §17.2 side and are not included in this function (it receives the post-reconcile confirmed size as an argument).
  the call from §17.2 is **only the single execution point** of replaceStopProtected (it does not call cancel/place directly).

STOP_REPLACING critical section:
  - on start, record hedge_legs.stop_replacing_started_at = now (D1)
  - limit 60 seconds. overrun is escalation (priority repair + admin alert)
  - this section runs only inside the §17.2 step 11 replaceStopProtected

procedure branch (🆕 v5.2.6 Y-1: matches the r2 skeleton (this section's typescript). the §0.5 NV-3 result finalizes (a)/(b)):
  (a) if HL allows duplicate reduce-only stops on the same leg:
      1. place the new stop for the new size first
      2. verify the new stop's existence with verifyStopPlaced (cloid in openOrders)
      3. cancel the old stop after verification
      → zero unprotected window (always at least 1 valid stop exists)
  (b) if not allowed:
      1. snapshot the old stop (prev) then cancel it
      2. place the new stop → verifyStopPlaced (within the 60-second limit)
      3. on place / verify failure: prioritize immediate restore of the old stop (prev) (🆕 Z-4: do both)
         - restore success → enqueue partial_repair (B-4) **and** treat the attempt as failed (subject to circuit breaker accrual)
           reason: the position is the new size and the stop is the old size, a mismatch state, so it is a B-4 repair target.
                 at the same time, let the breaker detect repeated replacement failures.
         - restore also fails (including a restore throw) → enter SAFE_MODE (reason='stop_restore_failed')
           + priority stop-audit/repair + admin alert (matches the X-1b double guard)
  cancel-only (newStop = null, targetSize=0 / full close path):
      - cancel the old stop and clear the stop in the DB (do not place a new stop)

STOP_REPLACING 60-second overrun:
  - escalation: SAFE_MODE + priority repair queue + admin alert
  - light-check's near-stop / stop-crossed monitoring continues per §17.1 (consistent with A-1)

References:
  - §17.2 step 11 (the only call site of this function. X-1 unified cancel/place into this function)
  - §0.5 NV-1 (HL acceptance spec of reduce-only stop) / NV-3 (whether duplicate stops are allowed)
  - §13.2 hedge_legs.stop_replacing_started_at (the start time of this section)
```

```typescript
// 🚨 v5.2.6 (X-1): stop cancel/place is called only from this function (INV-STOP).
//   §17.2 only references this function and does not call hl.cancelByCloid / hl.placeReduceOnlyStopMarket directly.
//   newStop === null means "cancel only" (targetSize=0 / full close path).
//   NV3_STRATEGY is finalized to 'a' (duplicate allowed) / 'b' (duplicate not allowed) by the §0.5 NV-3 measurement.
async function replaceStopProtected(
  env: Env,
  leg: HedgeLeg,
  newStop: { size: string; triggerPx: string; cloid: `0x${string}`; attemptId: string } | null, // 🆕 W-3: attemptId
  strategy: 'a' | 'b',
): Promise<void> {
  const account = hlAccountOf(leg);
  await repo.markStopReplacingStarted(leg.id, nowIso()); // limit stop_replacing_deadline_seconds (§13.12)
  try {
    if (newStop === null) {
      // cancel-only: the position went to 0, so cancel the old stop
      if (leg.stopCloid) await hl.cancelByCloid(account, ETH_ASSET_INDEX, leg.stopCloid);
      await repo.clearStop(leg.id);
      return;
    }
    if (strategy === 'a') {
      // (a) HL allows duplicate reduce-only stops: place new stop first → verify → cancel old stop
      await hl.placeReduceOnlyStopMarket({ account, asset: 'ETH', ...newStop });
      await verifyStopPlaced(account, newStop.cloid);            // confirm existence in openOrders
      if (leg.stopCloid) await hl.cancelByCloid(account, ETH_ASSET_INDEX, leg.stopCloid);
    } else {
      // (b) not allowed: cancel old stop → place new stop (within deadline). On place failure, prioritize immediate restore of the old stop
      const prev = leg.stopCloid ? await snapshotStop(account, leg.stopCloid) : null;
      if (leg.stopCloid) await hl.cancelByCloid(account, ETH_ASSET_INDEX, leg.stopCloid);
      try {
        await hl.placeReduceOnlyStopMarket({ account, asset: 'ETH', ...newStop });
        await verifyStopPlaced(account, newStop.cloid);
      } catch (e) {
        // 🆕 v5.2.6 (X-1b / Z-4): restore success → enqueue partial_repair + failed throw / restore fail → SAFE_MODE
        try {
          if (prev) {
            await hl.placeReduceOnlyStopMarket({ account, asset: 'ETH', ...prev }); // immediate restore
            await verifyStopPlaced(account, prev.cloid);
            // Z-4 / W-3: the position (new size) and the stop (old size) mismatch → enqueue as a B-4 repair target.
            //   makePartialRepairMessage generates conforming to all §10.1 schema fields:
            //     reason='stop_replace_failed_restored', attemptId=newStop.attemptId (the ID of that hedge-sync attempt),
            //     expectedSize=the new target stop size (newStop.size),
            //     actualSize=the restored old stop size (prev.size)
            await partialRepairQueue.send(
              makePartialRepairMessage(leg, {
                attemptId: newStop.attemptId, expectedSize: newStop.size, actualSize: prev.size,
                reason: 'stop_replace_failed_restored',
              }),
              { priority: 'high' },
            );
          } else {
            await enterSafeMode(legBot(leg), { reason: 'stop_restore_failed' });
          }
        } catch (_restoreErr) {
          await enterSafeMode(legBot(leg), { reason: 'stop_restore_failed' });
        }
        throw e; // the attempt is treated as failed → markAttemptFailed + breaker accrual in the §17.2 outer catch
      }
    }
    await repo.saveStop(leg.id, newStop);
  } finally {
    await repo.clearStopReplacing(leg.id); // even if this line does not run on a worker abnormal exit, the primary detection §17.1 light-check (max 5 min, W-5) + the secondary backstop §19.3 (Z-5) audit detect the deadline overrun and escalate to SAFE_MODE
  }
}
```

---

## 20. Deep Audit

### 20.1 Cadence

```yaml
normal bots:
  every 6h
  
high-risk bots (recent failures, low margin):
  every 1h

recent rebalance bots:
  5 min, 30 min, 2h follow-up
  
near-stop bots:
  immediate (price within 2% of stop)
  
🆕 v5.1: stop_trigger_crossed bots:
  immediate priority (Section 19.3)
  
ladder for SAFE_MODE recovery:
  1 min initially, exponential backoff
```

### 20.2 Audit Work

```yaml
per-bot audit:
  1. NFPM.positions refresh (liquidity, ticks)
  2. NFPM.ownerOf check (custodian == BnzaExVault?)  -- 🆕 v5.1
  3. pool.slot0 refresh
  4. HL clearinghouseState fetch
  5. actual short size reconcile
  6. stop order existence check
  7. funding/fills low-frequency sync (Phase A is daily aggregate)
  8. HL marginSummary fetch (Section 18.4)
  9. update bot_runtime_state (incl. eth_price_usd, lp_value_usd)
  10. hedge_legs update (entry_price, liquidation_price, effective_leverage,
                       isolated_margin_usd, stop_distance_pct, last_stop_audit_at)
  11. mark next_deep_audit_at

work splitting:
  - 1 audit message = 1 bot
  - parallel consumers process queue
  - HL rate limit shared
```

---

## 21. Fee Collection

### 21.1 Retire Daily Fee Collect

```yaml
🚨 a lesson learned from carter2099:
  daily collect increases gas/operation cost
  daily at 10,000 bots = a huge number of txs → high cost

New policy:
  threshold-based + event-based
```

### 21.2 Collection Triggers

```yaml
collect fee when:
  - LP rebalance (range out)
  - Bot close
  - uncollected fee > threshold (e.g. $10)
  - weekly scheduled claim
  - user manual claim

display:
  - estimated/static-call fee data
  - actual collect is threshold/event based
  
do not:
  ❌ collect for all bots daily
  ❌ swap fee → USDC every collect (maintain the token balance)
```

---

## 21.5 Security / Secret Handling (🆕 v5.1)

### 21.5.1 Grand principles

```yaml
🚨 stated in v5.1:

1. BNZA does not hold / receive the user's HL master private key
   - the user manages the master account in the HL official UI / wallet
   - only the agent key (approved by the master) is sent to BNZA
   - no feature to paste the master private key into the BNZA UI / API is provided

2. BNZA does not hold the user's wallet private key (Base / OP)
   - the user wallet connects via metamask / WalletConnect
   - the user wallet signs:
       - initial start / deposit request
       - approvals where applicable
       - user-requested close confirmation if UI requires explicit confirmation
       - agent / builder fee approval flows where applicable

3. Operator signs BnzaExVault operational tx
   - BnzaExVault operational rebalance
   - BnzaExVault fee collect
   - BnzaExVault LP close after authorized user/admin trigger
   - emergency actions, if authorized by contract role
   - to align with the LP NFT custody model (Section 15.5),
     it does not define "the user signs all onchain tx"

4. What BNZA must never store
   - user EVM wallet private key
   - user HL master private key

5. What BNZA may store
   - encrypted HL approved agent key
   - operator key, separately managed and rotated

6. The Agent key (HL signing key) is stored with envelope encryption
   - encrypted storage (envelope encryption)
   - decryption only when needed inside the OPERATOR Worker
   - do not emit plaintext to log / DB dump / Analytics

7. Any secret (API key, webhook secret, etc.) is also envelope-encrypted similarly
```

### 21.5.2 Envelope Encryption Model (Agent Key)

```yaml
Hierarchy:
  - Master Key (Phase A default finalized: 🚨 v5.2.1 / P0-4):
       the Phase A default is finalized to **Cloudflare Secrets Store** (zen decision).
         a) Cloudflare Secrets Store + Worker bindings  ← Phase A finalized
         b) HashiCorp Vault Cloud / AWS KMS via internal proxy ← considered from Phase B onward
         c) self-managed (HSM)  ← from Phase D onward
       whether to migrate to an external KMS (AWS/GCP KMS) is evaluated in Phase B.
       In Phase 0, finalize the a) DEK generate/store/rotation runbook (§21.5.2.1).
  
  - Holding the Master Key (🚨 v5.2.2 / P0-2 resolved the DEK lifecycle contradiction):
       the Master Key is held in memory via the Cloudflare Secrets Store binding at Worker startup
       (account-level secret, memory-only).
       ※ the old description "decrypt the DEK and hold memory-only at Worker startup" was wrong and is deleted.
         the DEK is not touched at startup.

  - Data Encryption Key (DEK) — per agent key row:
       1 DEK per hl_agent_keys row (not per bot/hedge_leg).
       each time the agent key is used, read wrapped_dek from D1 and
       unwrap it with the Master Key into memory (function scope only, destroyed immediately after use).
       generate a new DEK and a new wrap on each agent key rotation.

  - Agent Key (encrypted) — stored in D1.hl_agent_keys (Option A columns):
       encrypted_secret (AES-256-GCM ciphertext)
       secret_iv / secret_auth_tag (per-record random IV + GCM tag)
       wrapped_dek / dek_iv (the DEK wrapped with the Master Key + IV)
       encryption_key_version (Master Key version, rotation chain)

Decrypt flow (exactly matches the §13.9 Option A schema):
  1. the hedge-sync worker needs the agent key
  2. read {wrapped_dek, dek_iv, encrypted_secret, secret_iv,
     secret_auth_tag, encryption_key_version} from D1
  3. obtain the Master Key from the Secrets Store binding (memory cache at Worker startup)
  4. unwrap wrapped_dek with Master Key + dek_iv → plaintext DEK (memory)
  5. decrypt encrypted_secret with DEK + secret_iv + secret_auth_tag via AES-256-GCM
  6. hold the plaintext agent key in memory (function scope only)
  7. after signing the HL order, destroy the plaintext DEK / plaintext agent key
  8. never include them in log / error output (§21.5.4 sanitize)
```

#### 21.5.2.1 Phase A Default Runbook: Cloudflare Secrets Store (🆕 v5.2.1 / P0-4)

```yaml
🚨 v5.2.1 finalized: Phase A envelope encryption uses Cloudflare Secrets Store.

Master Key:
  - stored as an account-level secret in Cloudflare Secrets Store
  - referenceable only by the OPERATOR Worker via Worker bindings
  - plaintext is memory-only, not emitted to D1/disk/log (§21.5.4)

DEK (Data Encryption Key) — 🚨 v5.2.2 (P0-2): per agent key row:
  - generate 1 DEK per hl_agent_keys row (32-byte random for AES-256-GCM).
    not per bot/hedge_leg (resolves the DEK lifecycle contradiction)
  - wrap it with the Master Key and store in D1.hl_agent_keys.wrapped_dek
    (dek_iv / encryption_key_version in the same row)
  - the Agent Key itself is encrypted with the per-row DEK (encrypted_secret, secret_iv,
    secret_auth_tag)

Generation (at agent key approval / rotation. 1 row = 1 DEK):
  1. generate the DEK with crypto.getRandomValues (memory-only)
  2. wrap the DEK with the Master Key (Secrets Store) → {wrapped_dek, dek_iv}
  3. encrypt the agent key with the DEK via AES-256-GCM → {encrypted_secret,
     secret_iv, secret_auth_tag}
  4. save into each §13.9 Option A column:
     {encrypted_secret, secret_iv, secret_auth_tag, wrapped_dek, dek_iv,
      encryption_key_version}. destroy the plaintext DEK / agent key immediately

Decryption (at hedge-sync):
  follow the §21.5.2 decrypt flow (Master Key→unwrap DEK→decrypt agent key→
  function scope only→destroy after signing)

Rotation:
  - monthly automatic (consistent with §21.5.3). bump the Master Key version,
    existing rows are decryptable via the old version chain, new rows are wrapped with the new version
  - no downtime during rotation (key version chain, §21.5.3)

External KMS migration:
  - evaluate an AWS/GCP KMS proxy from Phase B onward (replacing this runbook)
  - Phase A freezes on this runbook (satisfies start condition 3, §0.3 / §30)
```

### 21.5.3 Key Versioning / Rotation

```yaml
encryption_key_version:
  - managed in hl_agent_keys.encryption_key_version
  - on Master Key rotation, assign a new key version
  - rows encrypted with the old version are still decryptable (key version chain)

agent key rotation:
  trigger:
    - HL agent key expiry (HL-spec expiry)
    - the user's intent (after a security event)
    - periodic rotation (90 days recommended)
  flow:
    1. request re-approval from the user
    2. generate a new agent key (browser / wallet side)
    3. the user approve-signs on the HL master
    4. BNZA envelope-encrypts the new key and INSERTs it
    5. the old row's approval_status='revoked', rotated_from=new.id
    6. hedge-sync uses the new key

leave an audit trail via the rotated_from chain.
do not DROP.
```

### 21.5.4 Logging / Sanitization

# 🚨 v5.2.3 (P1-A): extend the sanitize regex to also redact envelope encryption fields (wrapped_dek /
#   dek_iv / secret_iv / secret_auth_tag).
#   fully align the regex with the §21.5.4 body "never write DEK / Master Key to log".
```yaml
Never write to log:
  - private keys (plaintext agent key)
  - master account private key (not received in principle, but just in case)
  - the signature part of the signed payload
  - DEK / Master Key
  - wrapped_dek (already Master-Key-encrypted, but do not emit to log just in case)
  - dek_iv (the IV for DEK decryption; does not weaken the ciphertext, but do not emit to log)
  - secret_iv (the IV for agent key decryption, same as above)
  - secret_auth_tag (the AES-GCM auth tag, same as above)
  - cloudflare secrets binding contents
  - any string containing "secret" / "auth" / "key" / "token"

sanitize function:
  the HL response raw object may contain an agent key / signature
  → always pass it through sanitize() before parseOrderResponse / R2 archive
  also redact envelope-encryption-related fields (wrapped_dek / dek_iv /
  secret_iv / secret_auth_tag) with the same function.
  
  function sanitize(obj: unknown): unknown {
    // recursively redact keys matching:
    // 🚨 v5.2.3 (P1-A): add the dek / master.*key pattern
    // /private|secret|signature|agent.*key|auth|dek|master.*key/i
    // also mask long hex values (>= 64 bytes)
  }

R2 archive:
  - sanitized JSON only
  - if a sanitize miss is discovered, delete and regenerate that date's archive

Analytics Engine:
  - unconditionally exclude sensitive dimensions (Section 14.3)
```

### 21.5.5 Operator Key Management

```yaml
Operator (the authority to call BnzaExVault operator functions):
  - the private key of the operator address held by Cloudflare Workers
  - this is also managed with envelope encryption (§21.X Phase A default = Cloudflare Secrets Store)
  - rotatable (implement a rotateOperator function on the BnzaExVault contract side)
  
  🚨 v5.2.1 finalized (Option C / Section 3.4):
    EXBOT's Operator key is separated for EXBOT only.
    It is a separate key / separate rotation lifecycle from the current BNZA POOL
    BnzaRouter v2.2.1 operator key, and they do not affect each other.
    BnzaExVault.rotateOperator is callable only by the EXBOT multiSig.
    The operator address / multiSig signer set per chain is
    finalized by zen before Phase 0 starts (synced with the §15.5.6 zen task).
```

### 21.5.6 Compromise Response

```yaml
agent key compromise (suspected):
  1. Operator: immediately SAFE_MODE that user's bot
  2. notify the user
  3. request re-approval from the user
  4. move the old key to revoked
  5. the user also executes agent revoke on the HL side (HL UI)

operator key compromise:
  1. pause all bots
  2. operator key rotation
  3. impact investigation
  4. notify users of the resumption

KMS / Master Key compromise (severe):
  1. revoke all hl_agent_keys
  2. request re-approval from all users
  3. KMS rotation + service restart
  4. re-encrypt past DB dumps / or discard old dumps
```

---

## Part 3: Implementation Roadmap

## 22. Pre-Launch Process (Phase subdivision + Backtest ordering fix in v5.1)

### 22.0 Summary of the v5.1 fix

```yaml
🚨 v5.1 fix:
  v5.0's Phase 1 = "4-6 weeks" is too optimistic.
  v5.1 subdivides Phases into Phase 0 / A1 / A2 / A3 and presents a realistic Total.
  (🚨 v5.2.1 P0-7: the old notation "A0" is the same as the real-roadmap "Phase 0". Naming unified)
  
  Phase 0 (Backtest + PositionCalculator + HL testnet validation):  4-6 weeks
  Phase A1 (single-user dry-run):                                     3-4 weeks
  Phase A2 (live $1k):                                                3-4 weeks
  Phase A3 (closed beta):                                             4 weeks
  Total Phase 0+A:                                                    14-18 weeks (4-5 months)

  Defer list (not implemented in Phase A):
  - 16 D1 shards (Phase A is 1 shard)
  - Analytics Engine (Phase A is D1 aggregation only, introduced in Phase B+)
  - R2 raw log archive (Phase A is basically D1, logs in CF Logs / Tail)
  - DLQ operator UI (Phase A is admins querying D1 directly)
  - Multi-RPC failover (🆕 v5.2.6 E: Phase 1 has at least 1 RPC per chain = Base/OP 1 each.
                        multi-RPC failover itself is Phase C)
  - LP range ladder (Phase A is ±5% single)
  - Revert Lend integration (LP Plus)
  - AI Pro (dynamic leverage / Aave integration)
  - Multiple bots per user (Phase A is 1 user 1 bot, Section 16.5)
```

### 22.1 Phase 0: Backtest + Mini-implementation (Step ordering fix)

```yaml
duration: 4-6 weeks
tool: zelos-research/Demeter (Python OSS) + custom HL module
goal: finalize parameters + verify PositionAmountCalculator accuracy + confirm HL testnet operation

🚨 v5.1 fix: Step ordering
  v5.0 was "data → simulation → parameter sweep → choose".
  v5.1 makes the PositionAmountCalculator (mini) first as Step 0.
  reason: the backtest simulator uses the same AMM formula, so
        the computation logic can be shared between the real implementation and the backtest.

Step 0: PositionAmountCalculator mini implementation (Week 1)
  - implement TickMath / LiquidityAmounts in TypeScript (the same as used in the real OPERATOR)
  - embed a Python wrapper or equivalent logic into Demeter
  - pass all test cases (Section 6.5)
  - confirm both WETH token0/token1 cases
  - confirm boundary tick behavior
  - output: PositionAmountCalculator package + test suite (used as-is in Phase A1)

Step 1: Data preparation (Week 1-2)
  # 🆕 v5.2.6 (E): obtain both Base + Optimism pool data and evaluate the parameter sweep
  #   on both chains (Phase 1 = both chains).
  - Base USDC/ETH 0.3% pool: 6-12 months historical
    - slot0, liquidity, ticks, swap events
  - Optimism USDC/ETH 0.3% pool: 6-12 months historical (same, sweep on both chains)
  - HL ETH funding history (fundingHistory API)
  - HL ETH mark/oracle price
  - estimated orderbook impact

Step 2: Simulator (Week 2-3)
  - an LP simulator based on Demeter
  - embed the Step 0 PositionAmountCalculator
  - HL hedge module (incl. funding / spread / stop trigger)
  - reproduce the Phase 1 strategy (70% short, 3x isolated, ±5% range, threshold trigger)

Step 3: Parameter sweep (Week 3-4)
  range: ±3%, ±5%, ±8%, ±12%
  hedge ratio: 50%, 70%, 90%
  leverage: 2x, 3x
  trigger threshold: delta error 10%, 15%, 25%
  cooldown: 30min, 60min, 120min
  stopSafetyFactor: 0.60, 0.70, 0.80   -- 🆕 v5.1 (Section 19.1)

Step 4: Metrics evaluation (Week 4-5)
  metrics:
    - net APR (after PF, gas, fees)
    - max drawdown
    - liquidation distance min
    - out-of-range time
    - rebalance count (assuming delta-only adjustment)
    - hedge turnover
    - funding paid/received
    - worst 1d / 7d loss
    - Sharpe ratio
    - 🆕 stop trigger fire count / average stop loss size

Step 5: Decision + HL testnet validation (Week 5-6)
  parameter set adoption criteria:
    ✅ net positive APR (median scenario)
    ✅ max drawdown < 20%
    ✅ worst 7d loss < 10%
    ✅ avg liquidation distance > 5%
    ✅ Sharpe ratio > 1.5
    ✅ stop trigger fire count / month < 1 (median scenario)
  
  HL testnet validation (part of the mini-implementation):
    - create an agent key on Hyperliquid testnet + the envelope encryption round-trip
    - IOC short open / reduce-only close / native stop on testnet
    - cloid / nested error / reconcile behavior
    - subaccount + vaultAddress behavior
```

### 22.2 Phase A1: Single-User Dry-Run (3-4 weeks)

```yaml
duration: 3-4 weeks
goal: confirm implementation operation + verify the full flow in dry-run mode
funds: $0 (no real orders)

scope:
  - PositionAmountCalculator (adopt the Phase 0 Step 0 as-is)
  - HyperliquidAdapter (testnet → production, but in dry-run mode)
  - D1 hot state (1 shard, Phase A default)
  - Cron + Queue fan-out (light-check only, hedge-sync is dry-run)
  - UserLockDO (lease-based)
  - HL native stop placement (testnet)
  - Reconcile after order
  - PREFLIGHT margin check (Section 18.4)
  - Bot lifecycle state machine (Section 16)
  - LP NFT custody (Section 15.5, confirm BnzaExVault integration)
  - 1 user / 1 bot policy (Section 16.5)

forbidden in A1:
  ❌ live HL mutation
  ❌ live LP open / close
  ❌ live USDC transfer
  ❌ Multi-shard
  ❌ R2 / Analytics Engine
  ❌ Multi-RPC failover

completion criteria:
  - PREFLIGHT reliably blocks in patterns that should be blocked
  - the lp_opening / hedge_pre_open / stop_placing simulation succeeds (B-5: canonical lifecycle_state names)
  - light-check fires as expected
  - hedge-sync's delta-only logic outputs the correct size (no real orders)
  - SAFE_MODE entry conditions are as expected
  - the whole Cron / Queue completes within wall time
```

### 22.3 Phase A2: Live $1,000 Test (3-4 weeks)

```yaml
duration: 3-4 weeks
goal: real-fund operation, stability verification under production conditions
funds: zen's own $1,000 (1 bot)
user: zen only (1 user 1 bot policy)

scope:
  - run all A1 features in live mode
  - real LP open (Base USDC/ETH 0.3%, ±5%)
    # 🆕 v5.2.6 (E): the $1k body runs on Base. In parallel, also verify a small
    #   real open/close once on Optimism, confirming OP's wethIndex / RPC / subgraph / Vault
  - real HL hedge (70% short, 3x isolated)
  - real stop placement
  - real reconcile
  - real fee collect (event-based, Section 21)
  - real close path (try a close midway, also verify re-open)
  - detailed log of all metrics
  - daily results review
  - confirm margin warning / critical triggering (intentionally cause it with low margin)

pass criteria:
  - Net APR within ±30% of the backtest assumption
  - no Stop trigger fire, or normal operation when fired (Section 19.3 case A)
  - Reconcile 100% match
  - zero Critical bugs
  - HL native stop placement / cancel / re-place as expected
  - delta-only adjustment does not consume more subrequests than full close/open
  - LP NFT custody (inside BnzaExVault) is verifiable (NFPM.ownerOf == BnzaExVault)
```

### 22.4 Phase A3: Closed Beta (4 weeks)

```yaml
duration: 4 weeks
goal: operation with multiple users, UX / Onboarding verification
users: 5-10 WL members, $1,000-5,000 each, up to 1 bot per user (Section 16.5)
total AUM: $5,000-50,000

process:
  - operate with real users
  - weekly user feedback collection
  - Weekly metric review
  - evaluate Phase B transition feasibility weekly

pass criteria:
  - zero Critical bugs
  - User satisfaction (survey average 4/5 or above)
  - divergence from backtest < 30%
  - no Critical SAFE_MODE occurrence
  - Operator-initiated close is 0 or only expected patterns
  - the Stop trigger crossed marker resolves normally (Section 19.3)
  - Onboarding (HL agent approval / margin deposit) succeeds for all 5 users
```

### 22.5 Phase A → Phase B transition conditions (before Public Launch)

```yaml
prerequisites:
  - Phase A3 complete + all pass criteria achieved
  - Conservative marketing prepared
  - Risk disclosure complete
  - Customer support structure
  - Legal / compliance review (Terms / Risk Disclosure)

launch path:
  - Public Open at Phase A scope (10-100 bots assumed)
  - staged invitation (Whitelist → Public)
  - Phase B features (multi-shard, multi-bot per user, R2 archive, etc.)
    are added after Public Launch
```

### 22.6 Total Timeline (v5.1 finalized values)

```yaml
Phase 0 (Backtest + PositionCalculator + HL testnet):  4-6 weeks
Phase A1 (single-user dry-run):                         3-4 weeks
Phase A2 (live $1k):                                    3-4 weeks
Phase A3 (closed beta):                                 4 weeks
Total:                                                  14-18 weeks (4-5 months)

An estimate assuming zen solo + Claude Code.
With parallel work (BnzaExVault new development / BNZA-LPBOT・BnzaRouter v2.2.1 non-interference confirmation),
add a buffer of about +2–4 weeks (because BnzaExVault is new Solidity).

⚠️ Verification needed (zen task) — start condition 4 (redefined in v5.2.1, synced with §0.3 / §30):
  the WL 5/15 launch has already happened. The Phase 0 start date is the point at which zen judges
  "the post-POOL-launch instability period is over". For the concrete gate see start condition 4 of §0.3 / §30
  (zero SAFE_MODE over the past 7 days, no major incident).
```

---

## 23. Implementation Phases (Technical) — Defer made explicit in v5.1

### 23.1 Phase A: Correctness MVP (the sum of Phase A1+A2+A3)

```yaml
cap: 1-100 bots
duration: about 10-12 weeks (the whole Phase A excluding Phase 0)

must_have (Phase A):
  ✅ PositionAmountCalculator (correct AMM formula, established in Phase 0)
  ✅ HyperliquidAdapter (cloid, nested error, reconcile, delta-only adjust)
  ✅ HL native reduce-only stop (dynamic stopTriggerPx, Section 19)
  ✅ Reconcile after order
  ✅ D1 hot state (1 shard)
  ✅ Queue fan-out (light-check, hedge-sync, reconcile, stop-audit)
  ✅ UserLockDO (lease-based)
  ✅ Circuit breaker (history-based, hedge_leg_id PK)
  ✅ Failure notification (POOL UI banner + email)
  ✅ MarketDataDO
  ✅ LP NFT custody via BnzaExVault (Section 15.5)
  ✅ HL agent key envelope encryption (Section 21.5)
  ✅ Margin status (ok / warning / critical / safe_mode, Section 18.4)
  ✅ Stop trigger crossed marker + priority audit (Section 19.3)
  ✅ One user one bot policy (Section 16.5)
  ✅ Funding daily metrics (Section 13.6 Phase A simplified version)

forbidden in Phase A (Defer list):
  ❌ D1 sharding (16 shards is Phase C)
  ❌ R2 raw log archive (Phase B+)
  ❌ Analytics Engine (Phase B+)
  ❌ DLQ operator UI (Phase B+)
  ❌ Multi-RPC failover (Phase C)
  ❌ LP range ladder (Phase 2 / Defer)
  ❌ Revert Lend (LP Plus, Defer)
  ❌ AI Pro (Defer)
  ❌ Multiple bots per user (Phase B+)
  ❌ D1 snapshots (1 min granularity)
  ❌ HL poll for all bots every 5 min
  ❌ Per-bot RPC fetch in light-check
  ❌ Per-record funding ledger (Phase A is daily aggregate only)
```

### 23.2 Phase B: 1,000 Bot Readiness

```yaml
trigger: stable Phase A operation + user growth
duration: 2-3 weeks
add:
  - 4 D1 shards
  - MarketDataDO (strengthened shared pool cache)
  - HLRateLimitDO (token bucket)
  - Stop audit queue strengthening
  - Deep audit queue (distributed)
  - Dead-letter queue + admin UI
  - Metrics rollup (hourly/daily)
  - Funding rolling metrics (24h/7d/30d, Section 13.6)
  - R2 raw log archive
  - Analytics Engine (low-cardinality dimensions only, Section 14.3)
  - Hedge ratio 2 modes (Conservative 50% / Balanced 70%)
  - Multiple bots per user (subaccount allocation, Section 16.5)
  # 🚨 v5.2.1/v5.2.2 (P0-5): unified to 1 bot = 1 subaccount. Aligned with the HL subaccount limit
  #   (initial 10 / max 50, volume-conditioned). max ~50 subaccounts per master account
  #   (= ~50 bots), add a master on overflow. Plans are Basic 1 /
  #   Pro 3 / Enterprise 10 bot (unlimited retired). The master/IP distribution policy is
  #   spec'd separately at Phase B start (§16.5 zen task).
```

### 23.3 Phase C: 10,000 Bot Readiness

```yaml
trigger: stable 1,000-bot operation
duration: 3-4 weeks
add:
  - 16 D1 shards
  - Shard-aware scheduler
  - Adaptive audit priority
  - R2 archive (incl. raw funding events)
  - Multi-RPC provider failover
  - Queue lag backpressure
  - Operator dashboard
```

### 23.4 Phase D: 10,000+ / Enterprise

```yaml
trigger: stable 10,000-bot operation + further scale demand
add:
  - 32 shards
  - Online resharding tool
  - Per-chain worker split
  - Multiple RPC providers per chain
  - Stronger observability
  - LP Plus Bot (Revert Lend leveraged)
  - AI Pro Bot (Aave + dynamic optimization)
```

---

## 24. Live Test Checklist

### 24.1 Hyperliquid

```yaml
must_test:
  □ agent key can place order without main private key
  □ agent key + vaultAddress works correctly
  □ clearinghouseState with vaultAddress returns subaccount position
  □ clearinghouseState with master returns master position only
  □ IOC sell opens short
  □ IOC buy reduce-only closes short
  □ the correct delta is submitted to the market on delta-only adjust (size increase / decrease) (v5.1)
  □ updateLeverage works (3x)
  □ isolated margin update works
  □ trigger stop market accepted
  □ stop triggers on mark price
  □ openOrders contains cloid / reduceOnly flags
  □ cancelByCloid works
  □ duplicate cloid behavior understood
  □ nested min-notional error parsed correctly
  □ userRateLimit endpoint usable
  □ funding query bounded by time works
  □ subaccount creation works
  □ subaccount transfer works
  □ marginSummary includes effective_leverage / liquidation_price (v5.1)
  □ the envelope-encrypted agent key decrypt → sign → log sanitize flow works (v5.1)
```

### 24.2 Uniswap

```yaml
must_test:
  □ Base WETH/USDC 0.3% pool: WETH is token0
  □ 🆕 v5.2.6 (E): Optimism WETH/USDC 0.3% pool: verify the token0/token1 order individually
                   (the USDC/WETH address order can differ between Base and OP → finalize and store
                    wethIndex per chain, §6.4)
  □ Pool where WETH is token1 (verify)
  □ in range: amount0 > 0, amount1 > 0
  □ below lower: all token0
  □ above upper: all token1
  □ negative tick handling
  □ currentTick == tickLower (boundary)
  □ currentTick == tickUpper (boundary)
  □ zero liquidity case
  □ decimals 18/6 correct conversion
  □ NFPM.collect static call works
  □ Subgraph indexing lag observed (🆕 E: wire and verify the Base / OP subgraph on separate endpoints)
  □ NFPM.ownerOf returns BnzaExVault (Phase A custody check, v5.1) — both Base / OP Vault
  □ BnzaExVault rebalance / decreaseLiquidity / collect / mint authority (v5.1) — Base / OP
```

### 24.3 Cloudflare

```yaml
must_test:
  □ Queue fan-out correctness (no message loss)
  □ Queue idempotency (no duplicate execution)
  □ D1 shard routing (correct shard selected)
  □ UserLockDO lease acquire/release (no concurrent mutation, v5.1)
  □ UserLockDO heartbeat extends lease (v5.1)
  □ UserLockDO auto-releases a stale lock on TTL overrun (v5.1)
  □ HLRateLimitDO backpressure (within budget)
  □ DLQ handling (poison messages quarantined)
  □ MarketDataDO cache consistency
  □ Subrequest count under plan limit (Free 50 / Paid 10,000, Section 5.2)
  □ D1 query count under plan limit (Free 50 / Paid 1,000 per invocation, Section 5.2)
  □ Master Key decrypt round-trip via KMS / Secrets (v5.1)
```

### 24.4 BnzaExVault (🆕 v5.1)

```yaml
must_test (Phase 0 / Phase A1):
  □ BnzaExVault LP open (USDC deposit → mint NFT, custody = BnzaExVault)
  □ BnzaExVault LP rebalance (decrease 100% → mint new range)
  □ BnzaExVault LP close (decrease 100% → collect → swap → return USDC)
  □ BnzaExVault emergency NFT recovery (via multi-sig, v5.1)
  □ Operator authority check (msg.sender check)
  □ BnzaExVault pause / unpause
  □ User receipt token / internal ledger (which one was adopted)
  □ compatibility with the existing BNZA-LPBOT (BnzaLpBot.sol) (zen task)
```

---

## 25. Must-Fix Before 1,000 Bots

```yaml
🚨 mandatory before the 1,000-bot scale (before the Phase A → Phase B transition):
  1. Correct Uniswap V3 amount calculation (PositionAmountCalculator)
  2. Queue fan-out (no cron direct processing)
  3. No HL fetch in light check
  4. User-level mutation lock (UserLockDO lease-based, v5.1)
  5. Order idempotency (cloid)
  6. Post-order reconcile
  7. D1 hot state only (no snapshots)
  8. MarketDataDO cache
  9. Circuit breaker (history-based, hedge_leg_id PK, v5.1)
  10. HL native reduce-only stop (dynamic stopTriggerPx, v5.1)
  11. Failed rebalance notification
  12. Bridge state machine (LP first, atomicity)
  13. 🆕 v5.1: LP NFT custody via BnzaExVault (Section 15.5)
  14. 🆕 v5.1: Agent key envelope encryption + sanitize logging (Section 21.5)
  15. 🆕 v5.1: Delta-only hedge adjustment (Section 17)
  16. 🆕 v5.1: Margin status + insufficient margin UX (Section 18.4)
  17. 🆕 v5.1: Stop trigger crossed marker + priority audit (Section 19.3)
  18. 🆕 v5.1: LP operation state machine (Section 16.6)
```

---

## 26. Must-Fix Before 10,000 Bots

```yaml
🚨 mandatory before the 10,000-bot scale (before the Phase B → Phase C transition):
  1. 16 D1 shards
  2. Shard-aware scanner
  3. HL global/user token bucket (HLRateLimitDO)
  4. Distributed deep audit
  5. Distributed stop audit
  6. R2 / Analytics Engine offload (low-cardinality dimensions only, Section 14.3)
  7. DLQ operator UI
  8. Queue lag backpressure
  9. Per-pool MarketDataDO monitoring
  10. RPC provider failover (multi-RPC)
  11. Daily collect removal (event-based only, already from Phase A)
  12. Snapshot ban (D1 row count management, already from Phase A)
  13. 🆕 v5.1: R2 archive of per-bot funding raw events (Section 13.6)
  14. 🆕 v5.1: Master Key rotation drill (Section 21.5)
  15. 🆕 v5.2.6 (D-1): pass a 10k-equivalent load benchmark (D1 write QPS gate, §5.2.1).
      do not proceed to Phase C (16 shards / 10,000 bots) unless it passes.
```

---

## Part 4: Conclusion

## 27. Final Technical Conclusion

### 27.1 Non-Negotiable Rules (updated in v5.1)

```yaml
🚨 absolutely observe (violations cause scale collapse / trust collapse):

1. Do not fork carter2099/delta_neutral.
   → re-implement in TypeScript in the BNZA OPERATOR

2. Do not copy carter2099 LP amount calculation.
   → implement with the correct AMM formula

3. Do not poll Hyperliquid for every bot every 5 minutes.
   → light-check does not touch HL

4. Do not store 5-minute snapshots in D1.
   → hot state only, history to R2 (Phase B+)

5. Do not process all bots inside cron worker.
   → cron is a dispatcher only, fan-out via queue

6. Do not record success before reconcile.
   → post-order reconcile required

7. Do not use cross margin by default.
   → isolated required (Phase 1)

8. Do not keep pause/close semantics ambiguous.
   → make PAUSED ≠ CLOSED clear in UI/code

9. 🆕 v5.1: Do not full-close → full-open every hedge-sync.
   → delta-only adjustment is the default (Section 17)

10. 🆕 v5.1: Do not store HL master private key, ever.
    → agent key only, envelope-encrypted (Section 21.5)

11. 🆕 v5.1: Do not log raw HL responses without sanitize().
    → they can contain secret / signature (Section 21.5)

12. 🆕 v5.1: Do not promise "net positive in all markets" or "IL elimination".
    → designed to aim for drawdown suppression, not a guarantee (Section 1.2)

13. 🆕 v5.1: Do not use bot_id / user_id as Analytics Engine dimension.
    → low-cardinality only (Section 14.3)

14. 🆕 v5.1: Do not let stop_trigger_crossed_at marker stuck > 30 min.
    → always resolve via the priority audit (Section 19.3)
    → 🆕 v5.2.1 (P0-2): the marker must be set GUARDED in the §17.1 canonical light-check
      (if already set, overwriting is forbidden). An unconditional re-mark like §15.3
      rolls the timestamp back to now every time and invalidates this NN's stuck detection
      (§18.3), so it is strictly forbidden. The canonical light-check is only §17.1.
```

### 27.2 Implementation Model Summary

```
TypeScript rewrite
+ Correct Uniswap V3 position math (LiquidityAmounts)
+ Shared pool market cache (MarketDataDO)
+ Lightweight 5m checks (no HL fetch)
+ Event-driven HL execution (hedge-sync queue)
+ Delta-only adjustment (v5.1 — full close/open is target=0/emergency only)
+ Native reduce-only stops with dynamic trigger (v5.1)
+ Post-order reconciliation (mandatory)
+ Per-phase D1 sharding (Phase A: 1 / Phase B: 4 / Phase C: 16)
+ R2 / Analytics Engine archive (Phase B+, low-cardinality only)
+ Queue fan-out (no direct cron processing)
+ Lease-based Durable Object user lock (v5.1 — not function-callback)
+ Hyperliquid rate limiter (HLRateLimitDO)
+ LP NFT custody by BnzaExVault (v5.1)
+ HL agent key envelope encryption (v5.1)
+ Margin status state machine (v5.1)
+ Stop trigger crossed priority audit (v5.1)
+ One user one bot policy (Phase A, v5.1)
+ LP operation state machine (v5.1)
```

### 27.3 Scaling Path

```
Phase 0 (4-6w):          Backtest + PositionCalc + HL testnet (parameters fixed)
Phase A1 (3-4w):         Single-user dry-run (1 shard, no live mutation)
Phase A2 (3-4w):         Live $1k test (1 user, 1 bot)
Phase A3 (4w):           Closed beta (5-10 users, 1 bot each)
Phase B (2-3w + ongoing):4 shards + R2 + Analytics + multiple bot per user
Phase C (3-4w):          16 shards + multi-RPC + full distributed audit
Phase D (ongoing):       32 shards + online resharding + LP Plus / AI Pro
```

### 27.4 BNZA Differentiation vs Competitors (wording fixed in v5.1)

```yaml
🚨 v5.1 fix:
  remove the "mathematical superiority" claim against Panoptic / Neutra.
  BNZA's differentiation is narrowed to (a) existing BNZA POOL UI integration (b) HL liquidity usage
  (c) the BNZA Token BuyBack&Burn fee structure (d) operational simplicity.
  the comparison with carter2099 (OSS) keeps the v5.0 wording.

vs carter2099/delta_neutral (OSS):
  ✅ Multi-tenant SaaS
  ✅ BNZA POOL UI integration
  ✅ HL builder revenue share
  ✅ Performance fee model
  ✅ HL native stop (delta-only adjustment + dynamic stop trigger)
  ✅ Funding rate management
  ✅ Multi-chain (with implementation)
  ✅ Atomicity (post-order reconcile)
  ✅ accurate LP amount calculation with the AMM formula

vs Panoptic (commercial option-based):
  ✅ HL liquidity usage (within what the perpetual mechanism can achieve)
  ✅ a simple perpetual hedge (no option pricing needed)
  ✅ integration with the existing BNZA POOL / LP Bot
  ❌ do not claim "mathematically superior" (a different approach, each with trade-offs)

vs Neutra Finance / Orange Finance (Aave + Uniswap):
  ✅ HL hedge (Phase 1) — a simpler hedge venue
  ✅ Optimism / Base dual support (🆕 v5.2.6 E: both chains from Phase 1)
  ✅ Aave also integrable in Phase 2 (AI Pro, Defer)
  ❌ do not claim "a better hedge" (just a different hedge venue)

vs Arrakis / Gamma (LP only):
  ✅ designed to suppress IL drawdown with an optional hedge overlay
  ❌ do not claim IL elimination (Section 1.2)
```

---

## 28. Appendix: critical points confirmed in validation

### A.1 Points fixed v1 (early Claude) → v3.1

```yaml
1. the mathematical contradiction of ±2% range / ±3% threshold
   → fixed to ±5% range / delta error trigger

2. insufficient safety margin of 5x leverage + Auto Close +15%
   → fixed to 3x leverage + HL native stop + reconcile

3. the mathematical inaccuracy of the "reduce IL by 90%" expression
   → fixed to "70% directional exposure hedge"

4. simulation that did not account for the Performance fee
   → Gross/Net split display

5. accident risk of internal Bridge Bot execution
   → fixed to a user-prepare-in-advance model

6. optimism of Funding +3-10% expectation
   → treated as bonus/cost, not as a revenue premise

7. an Auto Close liquidation calculation error (3x +14.7% is wrong, +30.7% is correct)
   → dynamic computation (effective leverage based)

8. State machine LP first vs Hedge first
   → LP_OPEN → HEDGE_OPEN → STOP_PLACE is correct

9. close impossible when HL API unreachable
   → enter SAFE_MODE, do not attempt close

10. confusion of expression for Agent wallet vs main private key
    → only the user-approved agent key is stored at BNZA
```

### A.2 Points added v3.1 → v4.1

```yaml
1. reorganization of CF Workers / D1 constraints
   → at v4.1 subrequest 50 was treated as a conservative premise, but
      v5.2 fixed it to the current official values.
      Workers Paid subrequests: 10,000/request
      D1 queries per invocation: 1,000 on Workers Paid
      the main bottlenecks are HL rate limit / D1 single-thread / queue orchestration.

2. accurate calculation of the HL rate limit
   → 1,200 weight/min/IP, polling all bots is impossible

3. D1 row count constraints
   → a 1-min snapshot breaks at 10,000 bots

4. carter2099's hidden bug
   → LP amount calc by cumulative diffs breaks on range out

5. BNZA differentiation points not in carter2099
   → HL native stop, funding monitor, atomicity, multi-tenant

6. conformance to Cloudflare constraints
   → Queue + DO + sharding is mandatory

7. the 10,000-bot scale throughput model
   → light-check + event-driven + shared cache

8. Cloid idempotency
   → deterministic, retry-safe, version-aware

9. rejection of carter2099's cross margin default
   → BNZA requires isolated default

10. Pause vs Close semantics
    → eliminate carter2099's ambiguity, distinguish clearly
```

### A.3 Points added v4.1 → v5.0 → v5.1 (🆕)

```yaml
1. UserLockDO implementability
   → function-callback approach is impossible, fixed to lease-based (Section 11)

2. LP NFT custody was implicit
   → an explicit model held by BnzaExVault (Section 15.5)

3. subrequest / nonce waste from full close/open every Hedge
   → made delta-only adjustment (Section 17)

4. stopTriggerPx was fixed at 1.10
   → liquidationPx-based dynamic computation (Section 19.1)

5. the misconception that Stop = liquidation avoidance
   → make explicit that Stop is a loss cap, not liquidation avoidance (Section 19.0)

6. risk of leaving stale state after a Stop trigger
   → stop_trigger_crossed_at marker + priority audit (Section 19.3)

7. Schema inconsistencies (eth_price_usd / lp_value_usd etc.)
   → add via ALTER TABLE, do not DROP (Section 13)

8. circuit_breakers PK was bot_id based
   → changed to hedge_leg_id based (1 leg = 1 circuit, Section 13.7)

9. the HL agent key encryption method was undefined
   → envelope encryption + KMS-like + key versioning (Section 21.5)

10. risk of secret contamination in raw logs
    → make sanitize() mandatory, Analytics low-cardinality only

11. the Insufficient margin UX flow was undefined
    → Preflight + warning / critical / SAFE_MODE three levels (Section 18.4)

12. LP close authority was undefined
    → via BnzaExVault, the emergency multi-sig path made explicit (Section 16.4)

13. Phase A scope was optimistic (4-6 weeks)
    → subdivided into Phase 0 / A1 / A2 / A3, Total 14-18 weeks (Section 22.6)
      (🚨 v5.2.1 P0-7: unify the old "A0" notation to "Phase 0")

14. the Funding ledger was over-engineered
    → simplified per phase (Phase A: daily aggregate only, Section 13.6)

15. Analytics Engine high-cardinality risk
    → do not use bot_id / user_id as a dimension (Section 14.3)

16. one-user one-bot vs multi-bot was undefined
    → Phase A: 1 user 1 bot, Phase B+: multiplied via subaccount (Section 16.5)

17. the LP operation state machine was implicit
    → make LP_OPENING / LP_REBALANCING / LP_CLOSING / LP_FAILURE explicit (Section 16.6)

18. the Backtest order was "data → simulation → ..."
    → make the PositionAmountCalculator mini first as Step 0 (Section 22.1)

19. mathematical superiority claims against competitors
    → do not claim against Panoptic / Neutra (Section 27.4)

20. the Cloudflare Workers Paid subrequest number error
    → fixed to Free 50 / Paid 10,000 (Section 5.2, ⚠️ re-confirm in Phase 0)

21. the strategy expression "net ≥ 0 in all markets"
    → removed, changed to aiming for net positive in the median scenario (Section 1.2)

22. the non-existence of an IL elimination guarantee was not stated
    → make explicit "IL is a reduction target, not an elimination target" (Section 1.2)
```

---

## 29. Final points to validate (for the final review after the v5.1 fixes)

```yaml
1. whether the fusion of the v3 strategy layer and v4.1 infra layer (this v5.2) is not broken
   - whether the strategy (Phase 1: 70% hedge, 3x leverage) and
     the technology (10,000-bot scale architecture) are consistent

2. mathematical accuracy of the Position amount calculation
   - the LiquidityAmounts.getAmountsForLiquidity formula
   - boundary condition behavior (currentTick == tickLower)
   - Negative tick handling

3. conformance to Cloudflare constraints (updated in v5.1)
   - Subrequest Free 50 / Paid 10,000 / 1 invocation
   - D1 query Free 50 / Paid 1,000 / 1 invocation
   - D1 10GB / shard, single-threaded
   - Queue 5,000 msg/sec, 250 concurrency
   - DO single-threaded per instance
   - UserLockDO lease pattern (v5.1)

4. conformance to the Hyperliquid spec
   - Rate limit 1,200 weight/min/IP
   - correct use of Subaccount + vault_address
   - Native stop trigger order spec (dynamic stopTriggerPx, v5.1)
   - Cloid + idempotency
   - Agent key envelope encryption flow (v5.1)

5. gaps in the state machine
   - SAFE_MODE transition conditions (incl. margin critical)
   - PAUSED → ACTIVE/CLOSED transition
   - behavior on Reconcile mismatch
   - each step of LP_OPENING / LP_REBALANCING / LP_CLOSING (v5.1)

6. completeness of failure handling
   - Network timeout, rate limit, validation error
   - behavior on HL/RPC failure
   - Circuit breaker reset conditions
   - error transition on LP NFT ownerOf mismatch (v5.1)

7. realism of the Pre-launch process (re-estimated in v5.1)
   - whether 4-6 weeks is enough for Phase 0
   - whether 10-12 weeks is enough for Phase A1 + A2 + A3
   - whether Total 14-18 weeks is enough

8. validity of the Phase A scope (defer made explicit in v5.1)
   - whether it is completable by zen solo + Claude Code
   - whether there are gaps in the Defer list

9. critical oversights
   - Edge case
   - Security risk (whether Section 21.5 covers it)
   - Operational risk (margin critical / stop crossed)

10. validity of the competitive differentiation (wording fixed in v5.1)
    - against carter2099 / Panoptic / Neutra
    - whether the wording is realistic (no exaggeration)

11. 🆕 validity of the LP NFT custody model added in v5.1
    - integration feasibility with the existing BNZA-LPBOT (Solidity) (zen task)
    - validity of the Operator authority / Emergency multi-sig

12. 🆕 validity of the envelope encryption / KMS-like added in v5.1
    - whether a KMS candidate can be finalized before Phase 0 starts
    - whether the rotation flow is implementable
```

---

## 30. Document Status (updated in v5.2)

```yaml
Version: v5.2.6   # 🆕 W-4: the current version. v5.2.6 includes the r1–r5 behavioral changes (see the top changelog)
Status: Final Approved — 3 AI APPROVED (Codex / GPT / Claude Code) + zen approval finalized + round-1–5 cross-validation reflected (v5.2.6-r5). Phase 0 start OK (see §0.3 / §30 for the 4 start conditions)
Authors:
  - Strategy: Claude (BNZA Technical Advisor)
  - Math/Risk: validation AI #1 (Code Review)
  - Infrastructure: validation AI #2 (Scale Architecture)
  - Implementation Reference: Claude Code (carter2099 analysis)
  - v5.0 → v5.1 fixes: GPT / Codex validation reports integrated (22 required fixes)
  - v5.1 → v5.2 lightweight patch: final sanity corrections
  - v5.2 → v5.2.1 patch: Codex/GPT/Claude Code integrated P0 ×11 (applied by Claude Code)
  - v5.2.1 → v5.2.2 patch: 5 Codex re-validation findings / P0 sync-misses (applied by Claude Code)
  - v5.2.2 → v5.2.3 patch: Claude Code extracted P1/P2 / tiny doc-sync ×3 (applied by Claude Code)
  - v5.2.3 → v5.2.4 patch: doc-self-containment / removal of external PATCH_NOTES references (applied by Claude Code)
  - v5.2.4 → v5.2.5 patch: 2 Codex-extracted minor notes reflected / Final Approved finalized (applied by Codex)
  - Approval: zen (BNZA Founder)

v5.1 → v5.2 lightweight patch:
  - fixed effective_leverage definition
  - replaced initialHedgeEth drift denominator with targetShort-based relative drift
  - stop_trigger_crossed now routes to priority stop-audit/reconcile only, not normal hedge-sync
  - aligned security/onchain signing text with Router/Vault custody model
  - weakened LP_REBALANCING hedge-first into defensive partial pre-hedge + final post-confirm hedge
  - added Hyperliquid stop direction live-test requirement
  - added UserLockDO crash/reconcile rule

v5.2 → v5.2.1 patch (3-AI integrated P0 ×11, applied directly by Claude Code):
  - P0-1  Option C: separate EXBOT custody into a new BnzaExVault (the current BnzaRouter
          v2.2.1 / BnzaLpBot v1.1 are unmodified). Router term replacement + §3.4 responsibility separation +
          §15.5.6 BnzaExVault Solidity spec + a terminology-collision note with HL vaultAddress
  - P0-2  reduce §15.3 to an example and unify the canonical light-check into §17.1.
          make markStopTriggerCrossed guarded → make the NN#14 / §18.3
          "marker stuck > 30 min → SAFE_MODE" effective (safety-net repair)
  - P0-3  chunk every sendBatch to 100 (Cloudflare Queues limit, §10.3)
  - P0-4  finalize envelope encryption Phase A default = Cloudflare Secrets Store
          + runbook (§21.5.2 / §21.5.2.1)
  - P0-5  align with the HL subaccount limit (initial 10/max 50), make the subaccount pool
          expression a realistic structure (§16.5 / §23.2)
  - P0-6  rule target_ratio as a bps integer, forbid going through float (§7.6 canonical)
  - P0-7  unify Phase naming to "Phase 0 / A1 / A2 / A3" (retire the A0 notation)
  - P0-8  add the bots.lifecycle_state column, consistent with the §16 fine-grained state machine
  - P0-9  suppress §17.1 light-check during LP_REBALANCING (same pattern as LP_CLOSING)
  - P0-10 redefine the Phase 0 start condition 4 (5/15 done → instability gate),
          exact match of §0.3 and §30 on the 4 conditions
  - P0-11 unify the RebalanceReason enum to canonical
          (defined in §7.6, referenced by §5.3/§7.3/§13.4/§17.1)

v5.2.1 → v5.2.2 patch (Codex re-validation, 5 P0-integration sync-misses, applied directly by Claude Code):
  - v5.2.2-P0-1 move §17.2 hedge-sync onto the canonical bps path
                (normalizeTargetRatioBps). unify §7.3/§17.1's toNumber()/Math.max/
                float comparison to BigDecimal comparison (constants are string BigDecimal)
  - v5.2.2-P0-2 add envelope fields to the hl_agent_keys DDL (Option A:
                secret_iv/secret_auth_tag/wrapped_dek/dek_iv). Resolve the DEK lifecycle
                contradiction (per agent key row, §13.9/§21.5.2/§21.5.2.1 synced)
  - v5.2.2-P0-3 BnzaExVault ABI alignment: vaultRebalance returns newTokenId /
                unify §15.5.3·§16.4·§16.6 to vaultMint/vaultRebalance/vaultClose /
                add rotateOperator to the interface (§15.5.6)
  - v5.2.2-P0-4 define the common helper chunkSendBatch in §10.2. §10.2 cron /
                §10.3 scan go through the helper. Direct raw sendBatch calls forbidden
  - v5.2.2-P0-5 unify §16.5 to 1 bot = 1 subaccount, remove the unlimited plan,
                make the master capacity calculation explicit. sync §23.2

v5.2.2 → v5.2.3 patch (Claude Code extracted, 3 tiny P1/P2 doc-sync, applied directly by Claude Code):
  - v5.2.3-P1-A add the dek/master.*key pattern to the §21.5.4 sanitize regex +
                state wrapped_dek / dek_iv / secret_iv / secret_auth_tag in the "never write to log"
                list (security defense-in-depth).
                fully consistent with the §21.5.4 body "never write DEK / Master Key to log"
  - v5.2.3-P1-B unify the §10.1 hedge-sync queue message reason (singular string) to
                reasons: RebalanceReason[] (canonical, §7.6).
                also unify the §17.2 hedgeSync / hedgeSyncInner function arguments to the same type.
                the last-mile propagation of the §7.6 P0-11 canonical enum
  - v5.2.3-P2-A fix the version of §0.3 start condition 1 to "approval of this v5.2.3".
                exact match with §30 (a self-introduced staleness fix missed in the v5.2.2 patch)

v5.2.3 → v5.2.4 patch (doc-self-containment, applied directly by Claude Code):
  - up to SPEC v5.2.3, the precise diffs of past patches were split into a separate PATCH_NOTES.md
    (SPEC_v5.2_to_v5.2.1_PATCH_NOTES.md /
     SPEC_v5.2.1_to_v5.2.2_PATCH_NOTES.md /
     SPEC_v5.2.2_to_v5.2.3_PATCH_NOTES.md)
  - v5.2.4 removes these external references and makes this SPEC's §30 patch chain (above) the
    canonical source of the patch summary, achieving a self-contained state for SPEC_v5.2.4.md alone
  - the precise diff of each patch is fully retained in git history (the deleted
    PATCH_NOTES.md is also recoverable via git log / git show)
  - the design content (strategy, Phase structure, API, schema, enum, Solidity ABI, operational flow,
    the 4 start conditions, all NN rules) is completely unchanged from v5.2.3
  - achieved a state where SPEC_v5.2.4.md alone completes the full implementation norm of BNZA Ex Bot

v5.2.4 → v5.2.5 patch (2 Codex-extracted minor notes reflected / Final Approved finalized, applied directly by Codex):
  - v5.2.5-N1 resolve the staging mismatch between §30 Status and §30.2 next-process. After Codex's lightweight re-validation of v5.2.4 returned APPROVED with minor notes, the use of "Final" vs "Final Approved" was ambiguous. In this v5.2.5 unify to "Final Approved" and remove the staged expression "Codex lightweight re-validation → become Final Approved" from §30.2 next-process. Tidied into a canonical SPEC where an implementer can read the state mechanically in one word.
  - v5.2.5-N2 rewrite the §16.5 Phase B+ note's old version-dependent wording into a version-neutral current-SPEC-scope declaration.
              the old wording looks stale to a reader of the v5.2.4 canonical (it is read as a current SPEC scope declaration, not a record of a patch-cycle decision).
              retains the history in parentheses as "only the fact of the HL limit was reflected in the v5.2.2 patch cycle; later patches keep it out of scope".
  - the design content (strategy, Phase structure, API, schema, enum, Solidity ABI, operational flow,
    the 4 start conditions, all NN rules) is completely unchanged from v5.2.4
  - Codex applied this patch directly as its own raised fix (no re-re-validation needed)
  - with this v5.2.5, the SPEC v5.2.x series is finalized as Final Approved

Implementation may start ONLY AFTER 4 conditions are all met
(🚨 v5.2.1: unified to exactly match §0.3 — P0-7/P0-10):
  1. zen reads this v5.2.6 and gives approval (document finalized)  # 🆕 W-4: exact match with §0.3 (v5.2.6)
  2. LP NFT custody integration policy finalized = Option C finalized (BnzaExVault new development,
     Section 3.4 / 15.5.6). zen finalizes the deploy address / operator /
     multiSig before Phase 0 starts (🆕 v5.2.6 E: 2 sets for Base + OP)
  3. Hyperliquid agent key encryption method = Phase A default Cloudflare Secrets
     Store finalized (Section 21.5.2 / 21.5.2.1 runbook, P0-4)
  4. the post-WL-5/15-launch instability gate (redefined in P0-10, identical to §0.3):
     5/15 is done. zero SAFE_MODE over the past 7 days, no major incident, and
     the point at which zen judges "the post-POOL-launch instability period is over"
     (see Section 22.6 / §0.3)

Review process (retained from v5.0):
  1. v5.0 → GPT / Codex validation (complete)
  2. Final corrections incorporated → v5.1 (this doc, complete)
  3. v5.1 final sanity corrections → v5.2 Final Candidate (this doc, complete)
  4. zen approval → start Phase 0
  5. start Phase 0 (Backtest + PositionCalculator + HL testnet)

Implementation start: TBD (zen finalizes the Phase 0 start date)
Phase A1 start estimate: 1-2 weeks after Phase 0 completes (estimate)
Public Launch (Phase B transition): 14-18 weeks later (Q3-Q4 2026 assumed, Section 22.6)
```

### 30.1 Defer List Summary (v5.1 summary)

```yaml
Not implemented in Phase A (Defer):
  - 16 D1 shards         → Phase C
  - Analytics Engine     → Phase B
  - R2 raw log archive   → Phase B (debug log in CF Logs / Tail)
  - DLQ operator UI      → Phase B (substituted by admins querying D1 directly)
  - Multi-RPC failover   → Phase C (🆕 v5.2.6 E: Phase 1 has at least 1 RPC per chain = Base/OP 1 each,
                           multi-RPC failover is Phase C, with a fallback alert if needed)
  - LP range ladder      → Phase 2 (Defer)
  - Revert Lend (LP Plus)→ Defer (Phase 3)
  - AI Pro               → Defer (Phase 3)
  - Multiple bots per user→ Phase B+ (Section 16.5)
  - Per-record funding ledger → Phase C (Phase A is daily aggregate)
  - Aggressive hedge mode (90%+) → Phase 3 (Defer)
```

### 30.2 v5.2.5 Final Approved Statement

```yaml
v5.1 maintained the v5.0 strategy/infra direction and reflected the 22 required fixes.
v5.2 is minor final-sanity-check corrections only.
v5.2.1 directly patched the 11 P0 items from the integrated result of the 3-AI Final approval validation.

🚨 v5.2.2: directly patched onto v5.2.1 the 5 sync-misses discovered in Codex's re-validation (2026-05-19) that
"the canonicalization of P0 fixes did not reach some sections". Not a design-philosophy problem but a propagation-scope sync. No structural change /
fundamental rework was done.
  - the strategy core / infra core are unchanged from v5.2
  - v5.2.2-P0-1–5 all fully propagated the canonical rules (bps / chunking helper /
    vaultXxx ABI / envelope schema / 1 bot=1 subaccount) across the whole SPEC (§30 patch list)
  - propagation across all sections verified grep-based (see the execution report)

🚨 v5.2.3: against v5.2.2 (3 AI: Codex / GPT / Claude Code all
APPROVED), only the 3 items extracted by Claude Code that are not Final
blockers but resolve internal SPEC contradictions were doc-synced.
Zero structural change. Design philosophy・API・schema・enum values・Solidity ABI・operational
flow are all unchanged from v5.2.2.
  - v5.2.3-P1-A make the §21.5.4 sanitize regex also redact envelope encryption fields
    (dek/master.*key pattern + column names stated, defense-in-depth)
  - v5.2.3-P1-B type-unify the §10.1 hedge-sync queue / §17.2 hedgeSync function arguments to
    canonical RebalanceReason[] (§7.6 P0-11) (runtime unchanged)
  - v5.2.3-P2-A fix the version staleness of §0.3 start condition 1 (exact match with §30)
  - obtained APPROVED in Codex's lightweight re-validation (today)

🚨 v5.2.4: up to v5.2.3, the precise diffs of past patches were split into a separate
PATCH_NOTES.md (SPEC_v5.2_to_v5.2.1_PATCH_NOTES.md /
SPEC_v5.2.1_to_v5.2.2_PATCH_NOTES.md /
SPEC_v5.2.2_to_v5.2.3_PATCH_NOTES.md). v5.2.4 removes
these external references and makes this SPEC's §30 patch chain the
canonical source of the patch summary, achieving a self-contained state for
SPEC_v5.2.4.md alone. The design content (strategy・infra core・API・schema・enum・Solidity
ABI・operational flow・start conditions・all NN rules) is completely unchanged from v5.2.3.
The precise diffs of the past PATCH_NOTES.md are saved in git history and
recoverable via git log / git show.

🚨 (history) v5.2.5 patch: After Codex's lightweight re-validation of v5.2.4 returned "APPROVED with minor notes", the 2 raised minor notes were reflected. There was no problem blocking finalization, but per zen's "no compromise, prevent recurrence" principle, a tiny patch was applied to raise the completeness as a canonical SPEC.
  - v5.2.5-N1 unify the §30 Status from "Final" to "Final Approved".
              remove the staged expression "Codex lightweight re-validation → finalize as Final Approved" from §30.2 next-process, tidied into a form readable mechanically in one word.
  - v5.2.5-N2 rewrite the §16.5 Phase B+ note to version-neutral "in this SPEC",
              retaining the v5.2.2 patch-cycle history in parentheses.
The design content is completely unchanged from v5.2.4 (the description as of the v5.2.5 patch).
🆕 W-4: the above is the description that, **(history) as of v5.2.5**, "finalized the v5.2.x series as Final Approved".
The current version is **v5.2.6** (cross-validation including behavioral changes reflected in r1–r5. the top changelog is canonical).
For the Phase 0 start conditions see §0.3 / §30.

Next process: this v5.2.6 is finalized as Final Approved (🆕 Z-6: version bump). Of the 4 Phase 0 start conditions (§0.3 / §30), after the zen side finalizes condition 2 (BnzaExVault deploy address / operator / multiSig, 2 sets for Base + OP) and condition 4 (post-WL-5/15 instability gate / zero SAFE_MODE over the past 7 days, no major incident), start Phase 0.
(history) as of v5.2.5: since there was zero structural change, the GPT / Claude Code / Codex v5.2.5 re-validation was deemed unnecessary (the mathematical-validity / SPEC-integration / implementability perspectives obtained up to v5.2.4 as APPROVED remain valid as-is, and the Codex-extracted minor notes are reflected in v5.2.5).
🆕 W-4: unlike v5.2.5, v5.2.6 **includes behavioral changes** and has reflected the Codex / Claude Code cross-validation across round-1–5 (see the top changelog).

Start conditions (4 items, exact match between §0.3 / §30):
  1. zen's v5.2.6 approval (after finalizing through the r1–r5 reflection)  # 🆕 W-4: updated the old "v5.2.5 approval"
  2. Option C (BnzaExVault new development) — deploy/operator/multiSig finalized
  3. Cloudflare Secrets Store KMS design freeze
  4. the post-WL-5/15 instability gate (zero SAFE_MODE over the past 7 days, no incident)
Full item summary: 22 items = §28.A.3 / P0 ×11 + sync-misses ×5 +
doc-sync ×3 + self-containment ×1 + minor notes reflected ×2 = the whole §30 patch chain.
```

---

End of Document.
