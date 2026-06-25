# BA Response to QC UC Audit — ExBot 4 UCs
**Date:** 2026-06-20  
**Scope:** UC-EXBOT-agent-key, UC-EXBOT-bot-start, UC-EXBOT-light-check, UC-EXBOT-hedge-sync

---

## Part 1 — Fixed Items

### Already fixed before audit was read (commits 2026-06-20)

| QC Issue | File | What was done |
|---|---|---|
| agent-key I-04: `revoked` vs `superseded` conflict | `uc-agent-key.md` | A2 updated to `superseded` for rotation; `revoked` reserved for explicit admin action only. `spec.md` FR-080/083 aligned. |
| bot-start I-22: `flows.md` F-05 stale (park/re-entry) | `srs/flows.md` | F-05 rewritten to reflect direct `bot_safe_close → closed`. No cooldown/parked/re-entry. |
| bot-start I-04: missing alt flows | `uc-bot-start.md` | Added A5 (builder fee), A6 (LP sim fail), A7 (HL unreachable), A8 (stop fail), A9 (key expired), A10 (HL rejection), A11 (reconcile mismatch) with E-codes. |
| bot-start I-08: `0.70` ambiguity | `uc-bot-start.md` | Step 7 → `hedgeRatio (Phase A = 0.70)`, step 10 → `stopSafetyFactor (Phase A = 0.70)`. Separate names, same value. |
| bot-start I-16: E-EXBOT-003 verbatim mismatch | `uc-bot-start.md` | A3 updated to exact verbatim from `spec.md §5`. |
| light-check I-001: `stop_replacing_started_at` overrun missing from §3 | `uc-light-check.md` | Step 12 added: check overrun > 60s → enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE. |
| light-check I-002: `range_boundary_near` routing ambiguous | `uc-light-check.md` | A4 corrected: `range_boundary_near` → `hedge-sync` (it is a `RebalanceReason[]`). `price-near-stop-audit` is for `stop_trigger_crossed` only. |
| light-check I-005: `hedge_stopped_cooldown` missing | `uc-light-check.md` | §2 note added: these bots are NOT skipped; light-check runs, hedge-sync suppressed only. |
| light-check I-016: LP rebalance path missing from §3 | `uc-light-check.md` | Step 10 split: `range_out` → `lp_rebalancing` + `partial_repair`. Other reasons → `hedge-sync`. |
| light-check I-017: `flows.md` F-05 stale | `srs/flows.md` | Same fix as bot-start I-22 above. |
| hedge-sync I-02: A5 cites deep-audit as primary detector | `uc-hedge-sync.md` | A5 rewritten: light-check is primary (≤5 min, FR-EXBOT-033); deep-audit is secondary backstop only. |
| hedge-sync I-07: duplicate Postconditions + NFR-ADM-005 | `uc-hedge-sync.md` | Template artifact removed. |
| hedge-sync I-08: Trigger section is placeholder | `uc-hedge-sync.md` | Trigger updated to describe actual queue-based trigger. |

### Fixed in this session (2026-06-20)

| QC Issue | File | What was done |
|---|---|---|
| agent-key: A5 expiry notification scope unclear | `uc-agent-key.md` | Added A5: OOS, handled by UC-EXBOT-deep-audit, cross-ref FR-083. |
| agent-key: OQ-016 referenced in UC but missing from OQ table | `srs/spec.md §9` | OQ-EXBOT-016 added: admin reject path, options A/B/C, owner BA+zen. |
| agent-key + bot-start: FR dual numbering undocumented | `uc-agent-key.md`, `uc-bot-start.md` | FR Trace §7 in both UCs now has note: `frd.md` = implementation grouping, `srs/spec.md` = canonical behavior. Trace always refers `srs/spec.md`. |
| bot-start: on-chain preconditions (ERC-20, gas) missing | `uc-bot-start.md` | §2 already had these added in earlier session (ERC-20 allowance + native gas). Confirmed present. |
| light-check: `hlMarkPrice` source undefined in zero-HL-calls context | `uc-light-check.md` | Step 11 note added: TBD pending OQ-EXBOT-017; candidate `bot_runtime_state.eth_price_usd`. |
| light-check: OQ-017 did not exist | `srs/spec.md §9` | OQ-EXBOT-017 added: data source + staleness policy, owner Tech Lead. |
| light-check: stale template Postconditions + NFR-ADM-005 | `uc-light-check.md` | Template block removed. |
| hedge-sync I-01: delta=0 behavior undefined | `uc-hedge-sync.md` | Step 6 note added: no HL order if delta=0; behavior pending OQ-EXBOT-013. |
| hedge-sync I-03: "consecutive failures" definition unclear | `uc-hedge-sync.md` | §6 BR clarified: rolling 24h window, no intervening success. Source: FR-EXBOT-040 AC. |

---

## Part 2 — QC Findings We Disagree With

### Blockers that are not blockers

| QC Issue | Why we disagree |
|---|---|
| bot-start I-01 (FR numbering = Blocker) | `frd.md` and `srs/spec.md` intentionally use separate numbering schemes. This is a known structural decision, not a conflict. `srs/spec.md` is declared canonical in both documents. Added a clarifying note to UC §7 — no renumbering needed. |
| bot-start I-13 (OQ-EXBOT-03 pool address = Blocker) | This is a dependency on zen (Phase 0 NV-12), not a BA doc gap. UC correctly notes it as blocked external input. Not a BA action item. |
| light-check I-012 (frd.md FR-032 vs srs FR-033 = Blocker) | `srs/spec.md` is canonical ("SPEC v5.2.6 prevails" stated in both files). A tester reading both documents knows to use SRS. `frd.md` FR-032 should be updated but it does not block test design — it is medium severity, not a blocker. |

### Items that are BA non-scope / implementation detail

| QC Issue | Why it is not a BA UC item |
|---|---|
| bot-start I-17: missing HLRateLimitDO / MarketDataDO / UserLockDO interaction | UC describes behavior, not internal implementation. Which Durable Objects are called is a dev-level detail. Not required in BA UC. |
| hedge-sync I-04: `marginSummary` fetch step missing | FR-EXBOT-060 "during hedge-sync preflight" is an implementation ordering question for dev. UC references `hedge_legs.margin_status` in §F.2. Step-level ordering is covered by OQ-EXBOT-014 (already exists). |
| hedge-sync I-05: HLRateLimitDO missing from UC flow | Same rationale — implementation detail. OQ-EXBOT-015 already captures the interaction question. |
| hedge-sync I-06: agent key decrypt step | UC §3 step 4 already documents this (added in prior session). If QC is reading an older snapshot, the current file has this. |
| light-check I-004/008/009 (OQ formulas) | These are OQ items owned by zen — not BA documentation gaps. OQ-010/011/012 already exist in `spec.md §9` with owner and options. BA cannot resolve these unilaterally. |

### Items already resolved before QC audit baseline

| QC Issue | Note |
|---|---|
| agent-key I-04 (revoked vs superseded = Blocker) | Already fixed on 2026-06-20 before audit was read. Not a current gap. |
| light-check I-017 + bot-start I-22 (flows.md stale = Blocker/Major) | Already fixed on 2026-06-20. Not a current gap. |

---

## Open Items Awaiting External Input

These remain open and are correctly blocked on non-BA owners:

| OQ | Owner | Blocks |
|---|---|---|
| OQ-EXBOT-016 | BA + zen (scope decision) | UC-agent-key A4 admin reject enum |
| OQ-EXBOT-017 | Tech Lead | light-check step 11 markPrice source |
| OQ-EXBOT-013 | Tech Lead | hedge-sync delta=0 behavior |
| OQ-EXBOT-014 | Tech Lead | hedge-sync marginSummary fetch order |
| OQ-EXBOT-015 | Tech Lead | hedge-sync RateLimitDO + LockDO interaction |
| OQ-EXBOT-08 | zen | US-007 vaultRebalance() vs FR-015 redeem()+mint — pending ABI |
| OQ-EXBOT-05 | zen | builder fee 5bps approval mechanism |
| OQ-EXBOT-10/11/12 | zen | range_boundary_near formula, lpValueUsd, 7d APR |
| OQ-EXBOT-03 | zen / Phase 0 NV-12 | pool address + wethIndex dual-chain |
