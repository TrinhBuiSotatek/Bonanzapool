# Question Backlog — UC-EXBOT-user-redeem

> Document Title: UC-EXBOT-user-redeem Question Backlog v1
> Generated: 2026-06-17 | Source: UC-EXBOT-user-redeem_user-redeem_audited_20260617_v1.md | Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | H | NV-3; OQ-EXBOT-02 | INV-STOP §19.5 path for stop cancel during close — place-before-cancel (a) or cancel-then-place (b)? | Blocks step 10 test; stop cancel is required before HL close | Open |
| Q2 | H | OQ-EXBOT-08 | BnzaExVault final ABI and contract address (Base + Optimism)? | Blocks all on-chain redeem tests | Open |
| Q3 | H | uc-user-redeem.md §3 step 7 vs spec FR-EXBOT-073 | `close_operations` state machine mismatch: UC uses `lp_closed→funds_returned` but spec uses `requested→hedge_close_pending→hedge_closed→lp_closed→funds_parked→done` — which is correct? | Tester cannot write state machine AC without canonical definition | Open |
| Q4 | H | uc-user-redeem.md §3 | SLA 5-min timer: when does the clock start (event detection by watcher, or worker start)? How is breach detected and escalated? | AC-02 cannot be tested without timer mechanism | Open |
| Q5 | M | uc-user-redeem.md §3 step 8 | `UserLockDO.release` is absent from main flow steps — is it called? In a `finally` block? | Tester cannot verify lock cleanup | Open |
| Q6 | M | uc-user-redeem.md §3 step 13 | HL-portion USDC send mechanism — direct transfer, via what wallet/account? Tracked in `RedemptionQueue` only? | AC for HL-portion delivery cannot be written | Open |
| Q7 | M | uc-user-redeem.md §2 Preconditions | Does the same flow apply when `status='paused'` or `status='safe_mode'`? Any state-specific differences? | Test matrix depends on which states allow redeem | Open |
| Q8 | L | uc-user-redeem.md §4 | DLQ policy for `user_redeem` queue? Given highest priority + SLA-bound, what happens on 3 failures? | Queue reliability tests blocked | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
