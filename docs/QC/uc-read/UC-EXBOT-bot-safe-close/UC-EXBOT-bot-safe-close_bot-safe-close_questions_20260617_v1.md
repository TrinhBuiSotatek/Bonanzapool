# Question Backlog — UC-EXBOT-bot-safe-close

> Document Title: UC-EXBOT-bot-safe-close Question Backlog v1
> Generated: 2026-06-17 | Source: UC-EXBOT-bot-safe-close_bot-safe-close_audited_20260617_v1.md | Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | H | NV-3; OQ-EXBOT-02 | INV-STOP §19.5 path for stop cancel (size=0) — path (a) or (b)? | Blocks step 3 stop cancel test | Open |
| Q2 | H | uc-bot-safe-close.md §3 step 5 vs spec FR-EXBOT-073 | UC uses `vaultClose(tokenId, dest=UNINVESTED)`; spec uses `redeem(tokenId)` — canonical LP close method for bot_safe_close? | Canonical LP close method for test ABI call | Open |
| Q3 | H | spec FR-EXBOT-073 | Hedge retry: 3 sequential HL close calls or 3 re-queue cycles? Retry delay between attempts? | AC for retry-before-escalation cannot be written | Open |
| Q4 | M | uc-bot-safe-close.md §3 step 12b | `BnzaExVault.redeploy(botId)` ABI and contract address (Base + OP)? | Blocks re-entry on-chain tests | Open |
| Q5 | M | uc-bot-safe-close.md §3 step 12 | Re-entry "every 60 min" — Cron, CF DO alarm, or queued delay? | Test scheduling for AC-02 | Open |
| Q6 | M | uc-bot-safe-close.md §3 step 12c | CAS update condition for D1 `uninvested_balances`? Concurrency behavior? | Race condition test coverage | Open |
| Q7 | M | uc-bot-safe-close.md §3 step 2, 12a | `UserLockDO.release` absent from both close loop and re-entry loop — `finally` block? | Lock cleanup verification | Open |
| Q8 | L | uc-bot-safe-close.md §4 | DLQ policy for close and re-entry workers? | Worker-failure tests blocked | Open |
| Q9 | L | uc-bot-safe-close.md §4 A1 | Parked state recovery conditions — same as cooldown (7d APR + 2.0×) or different threshold? | Parked recovery test matrix | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
