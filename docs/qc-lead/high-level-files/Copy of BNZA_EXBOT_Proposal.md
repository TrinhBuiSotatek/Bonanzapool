# BNZA EXBOT — Implementation & Backtesting Proposal

| To | Zen-san, MEGABUCKS, Inc. |
| :---- | :---- |
| **From** | Carter — Blockchain Division, SOTATEK |
| **Date** | 2026-05-26 |
| **Re** | EXBOT implementation \+ backtesting in parallel (W1–W8), then PnL validation (W9–W10) |
| **Basis** | BNZA Ex Bot 統合技術仕様書 **v5.2.5 Final Approved** (spec-exbot.md) |

---

## 1\. Objective & Approach

SOTATEK will implement EXBOT per **SPEC v5.2.5** and validate it via a backtesting system, over **10 weeks**:

- **W1–W8 — Parallel build**: Track 1 implements the EXBOT core engine (strategy logic \+ backend infrastructure \+ `BnzaExVault` contract) to dry-run-ready (A1); Track 2 builds the backtesting system.  
- **W9–W10 — Validation**: use the backtest to measure EXBOT's effectiveness, produce the PnL report across ETH price scenarios (with rebalance analysis), run the single-user dry-run (via API), and make the Go/No-Go decision. If PnL targets are not met, a spec-parameter update loop follows.

The spec is "Phase 0 着手 OK" (3-AI approved \+ zen approved). This engagement executes Phase 0 \+ Phase A1 from the spec's roadmap.

**Out of scope (follow-on phase):** Mobile UI and Admin/config UI. This engagement delivers the **server-side engine \+ contract**, configured and operated via API/direct config. UI layers are required before a public WL launch and are quoted separately.

**Why build in parallel**: the strategy parameters (range ±5%, hedge ratio 70%, leverage 3x, rebalance thresholds) are configurable values defined in the spec — the engine is built to *accept* them. Backtesting determines whether those values meet the PnL target and the go-live decision; it does not change the architecture. Both tracks share the `PositionAmountCalculator` (spec §6) and converge at W7–W10.

---

## 2\. Implementation Basis & Confidentiality

The strategy **and** the architecture are fully specified in SPEC v5.2.5. SOTATEK implements per the spec; there is no withheld "black box." SOTATEK treats the spec as zen's confidential IP (under NDA) and will not redistribute it.

| Area | Defined in spec | Implemented by |
| :---- | :---- | :---- |
| Strategy: PositionAmountCalculator (AMM math, §6), hedge math (§7, 70%/3x), rebalance triggers (§7.3/§7.6), delta-only adjustment (§17), native stop (§8.4/§19), edge filter / hedge budget cap (§7.5) | Yes | SOTATEK |
| Architecture: CF Workers, D1 schema (§13), Queue fan-out (§10), Durable Objects (§11), HyperliquidAdapter (§8), reconcile (§9) | Yes | SOTATEK |
| Contract: `BnzaExVault` LP NFT custody (§3.4 Option C, §15.5) | Yes | SOTATEK |
| Final parameter tuning \+ go-live decision | Spec defaults; tuned via backtest | zen (approves spec changes) |

**Custody (resolved in spec §3.4):** EXBOT uses a **new** `BnzaExVault` contract (Option C). The existing `BnzaRouter v2.2.1` / `BnzaLpBot v1.1` are **not** modified — they continue running BNZA POOL. The two custody models are non-interfering.

---

## 3\. Scope of Work

### Track 1 — EXBOT Core Engine (W1–W8, A1 / dry-run-ready, per SPEC v5.2.5)

**Strategy logic (per spec)**

- `PositionAmountCalculator` — correct Uniswap V3 AMM math (§6); shared with the backtest (Track 2\)  
    
- Hedge math — `targetShort = lpEthAmount × hedgeRatio` (§7); 70% Balanced fixed, 3x isolated, builder fee 5bps  
    
- **Rebalance trigger engine** — implement the canonical `RebalanceReason` set (§7.3/§7.6). Triggers are evaluated in light-check (cached D1 \+ MarketDataDO, no HL fetch) and executed in hedge-sync (delta-only). All thresholds are config-driven (backtest-tunable):


| Trigger | Condition | Default threshold | Category |
| :---- | :---- | :---- | :---- |
| `drift_threshold` | deltaError USD \> max($25, lpValue × 3%) | hybrid abs+relative | Delta drift |
| `drift_relative` | |target − actual| / target \> 0.15 | 15% | Delta drift |
| `range_out` | rangeState ≠ 'in' | price exits ±5% | LP range |
| `range_boundary_near` | price at 90% to upper/lower bound | 90% | LP range (proactive) |
| `margin_warning` | hedge margin\_status \== warning (§18.4) | warning level | Risk |
| `funding_alert` | 7d funding \< −15% APR | −15% APR | Economic |
| `time_fallback` | 4h since last adjustment | 4h | Maintenance |
| `manual_admin` / `recovery_reconcile` | admin / repair flow | — | Operational |


  **Routing exceptions (not hedge-sync):** `stop_trigger_crossed` / near-stop → priority stop-audit (§19.3); `margin_critical` → SAFE\_MODE (§18.4.3). Routine rebalance is kept separate from emergency handling.


  **Economic gate (§7.5):** all triggers are subject to the hedge budget cap — if a rebalance would push hedge cost above trailing-7d LP fee × 30%, the engine pauses/reduces instead of rebalancing.


- Delta-only hedge adjustment (§17) — no full close/open each cycle  
    
- HL native reduce-only stop \+ crossed marker / priority audit (§8.4/§19)  
    
- Hedge budget cap (LP fee × 30%, §7.5); insufficient-margin preflight \+ SAFE\_MODE (§18.4)

**Backend infrastructure (per spec)**

- D1 schema (§13): bots (+lifecycle\_state), positions (custodian=vault), hedge\_legs, bot\_runtime\_state, rebalance\_attempts, circuit\_breakers (hedge\_leg PK), funding\_daily\_metrics, queue\_idempotency, hl\_agent\_keys (envelope-encrypted)  
- Queue fan-out \+ DLQ (§10): bot-scan, light-check, hedge-sync, reconcile, deep-audit, stop-audit, notification, metrics-rollup  
- Durable Objects (§11): UserLockDO (lease-based), HLRateLimitDO, MarketDataDO  
- Cron scan \+ jitter (§10.4); HyperliquidAdapter (§8: rate limit, cloid, nested-error parser, reconcile); post-order reconcile (§9)  
- HL agent-key envelope encryption — Cloudflare Secrets Store (§21.5, per Phase 0 condition 3\)

**Smart contract**

- `BnzaExVault` (new, Option C, §15.5.6): LP NFT custody; rebalance/close/collect/burn (Operator-only); emergency multi-sig; Foundry tests; audit prep

**Not included:** Mobile UI, Admin/config UI. Config (hedge ratio, leverage, stop) via direct config/API in this phase.

**Track 1 outcome (W8):** EXBOT engine \+ `BnzaExVault` ready for single-user dry-run (API-driven), one-user-one-bot per spec §16.5.

### Track 2 — Backtesting System (W1–W8)

- **Data pipeline**: Uniswap V3 USDC/ETH 0.3% (swap/tick/liquidity) \+ Hyperliquid (funding, mark price, depth) \+ gas \+ reference price, cleaned & UTC-aligned  
- **Simulation engine** built on the spec's `PositionAmountCalculator` (spec backtest Step 0 \= PositionAmountCalculator mini): LP value, fee accrual, hedge PnL, rebalance & stop per spec logic  
- **Reporting framework**: produces the PnL report in §4

**Track 2 outcome (W8):** backtest system validated (reproduces a known historical LP's returns), ready to run EXBOT scenarios.

### Validation (W9–W10)

- Run the backtest with the spec strategy across the §4 scenarios; produce the **PnL report**  
- Run the **single-user dry-run** of the live engine (via API); **Go/No-Go** for production  
- If PnL below target, enter the parameter/strategy update loop (§5)

---

## 4\. Backtest Deliverable — PnL Report (W9–W10)

For each scenario, the report quantifies net PnL **and** the rebalance dynamics that drive it.

### 4.1 Price scenarios

| Scenario | Description |
| :---- | :---- |
| **ETH up** | Trending up; price may break the upper range bound |
| **ETH down** | Trending down; price may break the lower range bound |
| **In-range ±5%** | Price oscillates within the LP range (ideal fee-harvesting case) |

### 4.2 Metrics per scenario

- **Net PnL / APR** after: LP fee − IL/LVR − hedge cost (funding) − rebalance cost − gas/bridge − performance fee (30%)  
- **Number of rebalances** triggered, **broken down by `RebalanceReason`** (drift / range / margin / funding / time)  
- **Cost per rebalance** (gas \+ slippage \+ realized IL)  
- **Total rebalance cost** and its **impact on net PnL** (before vs after rebalance drag)  
- **Hedge budget utilization** — does rebalance cost breach the 30%-of-fee cap (§7.5) in any scenario?

### 4.3 Expected insight

Rebalance frequency links the scenarios: **in-range ±5%** → few rebalances → low cost → best net PnL; **trending (up/down)** → frequent range breaks → many rebalances → eroded net PnL. The report identifies the rebalance-threshold sweet spot balancing health-factor safety against net PnL.

Reference (spec §2.1 expected net APR, after 30% PF): best \+25–35%, median \+10–20%, bad −5% to \+5%, tail −10% to −20%.

**Caveat (per spec §1.2)**: the strategy does not guarantee net ≥ 0 in all regimes; IL is reduced, not eliminated. Backtests of delta-hedged LP also tend to be optimistic vs live — discount results \~20–30%.

---

## 5\. Parameter / Strategy Update Loop (if PnL below target)

If the W9–W10 report shows net PnL below target:

1. **Identify shortfall** — which scenario fails and why (e.g., rebalance cost eats fees in trending markets; negative funding; range too tight).  
2. **Revise spec parameters** — range width, hedge ratio, rebalance threshold, leverage, stop distance (spec-defined; zen approves spec changes).  
3. **Re-run** — the engine and harness are parameter-driven (spec §7.6 normalizes target\_ratio to bps), so new parameters are tested without rebuilding. Iterate until target met or strategy deemed unviable.  
4. **Engine adjustments (if needed)** — e.g., adaptive rebalance threshold, funding-aware gating (spec §7.3 already includes funding\_alert) — implemented per a spec patch.

Because the same `PositionAmountCalculator` and hedge logic power both the backtest and the live engine, parameter changes are validated and deployed through one codebase.

---

## 6\. Timeline (10 weeks)

```
        W1   W2   W3   W4   W5   W6   W7   W8   W9   W10
Track 1 — EXBOT Core Engine (strategy + backend + BnzaExVault, A1)
        [env+schema][--- engine + adapter + vault ---][integrate]
                                                   └ dry-run support →[dry-run]

Track 2 — Backtesting System
        [data pipeline][--- sim engine (shared PositionCalc) ---][validate]
                                                   └ ready →[run + PnL report]

Validation (W9-W10): run backtest → PnL report (§4) + API dry-run + Go/No-Go.
Gate (end W10): Go/No-Go for production go-live (real user funds).
```

- **W1–W2**: env \+ D1 schema \+ PositionAmountCalculator (T1); data pipeline (T2)  
- **W3–W6**: HyperliquidAdapter \+ hedge engine \+ BnzaExVault (T1); simulation engine on shared PositionCalc (T2)  
- **W7–W8**: reconcile \+ stop \+ integration (T1); engine validation vs known LP returns (T2)  
- **W9–W10**: API dry-run (T1); run backtest → PnL report → Go/No-Go (T2)

**Follow-on (not in this scope):** Mobile UI \+ Admin UI; A3 production hardening (full reconcile at scale, multi-sig finalization, third-party audit, load test, closed beta). Quoted separately after the W10 decision.

---

## 7\. Team, Effort & Cost

Pricing unit: 1 man-month (mm) \= 4 weeks of 1 FTE. Figures in USD. 10-week engagement.

| Role | Scope | Man-months |
| :---- | :---- | :---- |
| PM/BA | Both (W1–W10) | 2 |
| Data Engineer | Backtest data pipeline | 2.25 |
| BE (strategy logic \+ infra) | Engine | 4.5 |
| SC (BnzaExVault \+ HL testnet) | Engine | 1.0 |
| QC | Both (integration \+ validate) | 2.0 |
| DevOps | Engine (env, CI/CD, monitoring) | 1.0 |
| **TOTAL** |  | **12.75** |

**Efficiency note:** the complete spec removes design uncertainty, and `PositionAmountCalculator` is built once and shared between the engine (Track 1\) and the backtest (Track 2).

**Excluded (client-owned):** third-party `BnzaExVault` audit (\~$8,000–25,000, pre-mainnet, separate); Cloudflare/D1/R2/Queue, RPC, HL builder account; production gas.

**Note:** this 10-week scope delivers **A1 dry-run-ready engine \+ validated PnL report**, via API. Mobile UI, Admin UI, and A3 production hardening are follow-on phases required before public WL launch.

---

## 8\. Dependencies on zen (Phase 0 着手 conditions \+ critical path)

Spec §0.3 lists 4 conditions to start Phase 0; status and remaining items:

| \# | Item | Status / Needed by |
| :---- | :---- | :---- |
| 1 | SPEC v5.2.5 approval | ✅ Done (3-AI \+ zen approved) |
| 2 | `BnzaExVault` deploy address / operator / multiSig (§15.5.6 zen task) | Needed by W3 (before contract integration) |
| 3 | HL agent-key encryption method (Cloudflare Secrets Store, §21.5) | ✅ Decided in spec |
| 4 | WL post-launch stability gate (7d no SAFE\_MODE / no major incident) | zen confirms before kickoff |
| 5 | GitHub access \+ `BnzaRouter` reference source; HL testnet credentials | W1–W2 |
| 6 | Backtest methodology \+ PnL target (success criteria) | W1 |
| 7 | Confirm Base vs Ethereum mainnet proxy for backtest history; HL funding data source | W1 |

---

## 9\. Key Risks

| Risk | Severity | Mitigation |
| :---- | :---- | :---- |
| `BnzaExVault` deploy params (operator/multiSig) late | High | Lock by W3 (dependency §8.2) |
| Data quality & alignment (backtest) | High | W1–W2 buffer; validate engine vs known LP before W9–W10 run |
| Backtest overfitting / optimistic vs live | Medium | Out-of-sample check; discount \~20–30% (spec §1.2 caveat) |
| `BnzaExVault` holds user funds | High | Mandatory third-party audit before mainnet (follow-on) |
| Spec is large (v5.2.5, many sections) → implementation breadth | Medium | Detailed spec reduces design risk; phase to A1 first, A3 follow-on |
| AMM-math skill (PositionAmountCalculator / Quant) | Medium | Shared component, single owner; short ramp-up if needed |
| 10 weeks reaches A1 only, not production | Medium | Set expectation: A3 hardening is a follow-on |
| No UI → dry-run API-driven only | Low | Acceptable for technical dry-run; UI is a follow-on |

---

## 10\. Open Questions

1. PnL target threshold for the Go/No-Go gate — defined by zen?  
2. Base-only data or Ethereum mainnet proxy for longer regime history (Base pool data starts \~Aug 2023)?  
3. `BnzaExVault` deploy params (operator / multiSig signers) — timeline for zen to finalize (§15.5.6)?  
4. Accountability / triage model for production incidents (engine vs strategy-parameter)?  
5. Commercial model: milestone-based fixed price or time-and-materials?  
6. Timing for the follow-on Mobile/Admin UI phase — immediately after W10, or later?  
7. WL stability gate (§0.3 condition 4\) — is the 7-day no-SAFE\_MODE window currently met?

---

## 11\. Next Steps

1. zen confirms scope, PnL target, commercial model, and Phase 0 condition 4 (stability gate).  
2. Finalize `BnzaExVault` deploy params (§15.5.6); confirm backtest data source (§8.7).  
3. Grant GitHub access \+ HL testnet credentials.  
4. Kick off W1: both tracks start (env \+ D1 \+ PositionAmountCalculator; data pipeline); backtest run \+ PnL report in W9–W10.

---

*This plan implements EXBOT per SPEC v5.2.5 — strategy logic and infrastructure both defined in the spec — alongside a backtesting system over W1–W8, then uses the backtest in W9–W10 to validate effectiveness and the rebalance-cost dynamics that drive net return, with go-live gated on the results. Mobile and Admin UI are follow-on phases.*

**Carter — Blockchain Division, SOTATEK**  
