# Question Backlog — UC-EXBOT-hedge-sync

> Generated: 2026-06-17
> Source files: docs/QC/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260617_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | H | NV-3; OQ-EXBOT-02 | Does HL support place-before-cancel stop replacement (§19.5 path a)? Or cancel-then-place (path b)? | Blocks all stop-replacement AC; INV-STOP path unconfirmed | Open |
| Q2 | H | NV-13; OQ-EXBOT-04 | HL ETH-USD perp minimum order size and dust handling threshold? | Blocks minimum delta threshold; FR-EXBOT-022 implementation unverifiable | Open |
| Q3 | H | uc-hedge-sync.md §3 Step 3 | Is heartbeat() required in hedge-sync when work exceeds 30s? Under what condition? | Lease renewal path untestable | Open |
| Q4 | M | uc-hedge-sync.md §4 A3 | Bot lifecycle state after HL rejection + circuit breaker increment? | AC-04 cannot verify final state | Open |
| Q5 | M | uc-hedge-sync.md §3 | Behavior when `hedge-sync` arrives while `circuit_breakers.state='open'`? | Circuit-open suppression path undefined | Open |
| Q6 | M | uc-hedge-sync.md §3/§4 | DLQ policy for hedge-sync, reconcile, partial_repair queues? | Queue-failure tests undefined | Open |
| Q7 | L | spec.md §9 vs uc-hedge-sync.md §7 | FR trace mismatch (UC lists FR-036; spec §9 lists FR-020/021/035) — which is authoritative? | Traceability gap | Open |
| Q8 | H | NV-12; OQ-EXBOT-03 | `wethIndex` for Base+OP confirmed? | Upstream dependency for targetShortEth | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
