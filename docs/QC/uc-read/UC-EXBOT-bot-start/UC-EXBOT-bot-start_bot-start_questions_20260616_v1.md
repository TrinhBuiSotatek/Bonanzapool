# Question Backlog — UC-EXBOT-bot-start

> Generated: 2026-06-16
> Source files: docs/QC/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260616_v1.md

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | H | uc-bot-start.md §3 | `POST /api/exbot/start` request body schema — what fields, types, constraints? | Tester cannot verify request validation without schema | Open |
| Q2 | H | uc-bot-start.md §3 | Success response schema from `POST /api/exbot/start` — fields, types? | Tester cannot verify happy path response | Open |
| Q3 | M | uc-bot-start.md §3 Step 3 (preflight) | Exact error message when builder fee (5bps) not confirmed? No alternate flow defined for this preflight check. | AC cannot be written as testable Given/When/Then without verbatim message | Open |
| Q4 | M | uc-bot-start.md §3 Step 3 (preflight) | Exact error message when LP mint simulation fails (preflight check 5)? No alternate flow defined for this preflight check. | Needed for negative path AC | Open |
| Q5 | M | uc-bot-start.md §4 A4 | "Return funds" on LP mint failure — which funds, via what mechanism, to where? | Without definition, recovery path cannot be tested | Open |
| Q6 | H | uc-bot-start.md §3 Step 8 | Error flow when post-order reconcile fails — what lifecycle state, is LP unwound? | No alternate flow defined; reconcile-fail test case cannot be written | Open |
| Q7 | H | uc-bot-start.md §3 Step 10 | Error flow when stop placement fails — what lifecycle state, is LP+hedge unwound? | No alternate flow defined; critical path to `active` state | Open |
| Q8 | M | uc-bot-start.md §4 A3 + us-001.md AC-4 | Exact error message when agent key not approved/expired? Both documents use vague wording. | AC-04 cannot be precisely tested | Open |
| Q9 | M | uc-bot-start.md §3 | Behavior if OPERATOR receives duplicate `POST /api/exbot/start` (idempotency)? | No idempotency mechanism described; duplicate submission could create two bot records | Open |
| Q10 | L | spec.md FR-EXBOT-004 | FR-EXBOT-004 (dual-chain) is in spec.md but absent from frd.md §4 — intentional split? | Tester reading only frd.md misses a P0 requirement | Open |
| Q11 | L | spec.md FR-EXBOT-025 vs frd.md FR-EXBOT-023 | Post-order reconcile is "FR-EXBOT-025" in spec.md but "FR-EXBOT-023" in frd.md — which is canonical? | Traceability gap for downstream test case FR references | Open |
| Q12 | H | project-context-master Q-012 | `wethIndex` confirmed values for Base+OP? | Blocks AC-10, LP amount computation, stop price chain | Open |
| Q13 | H | project-context-master Q-011 | HL stop system behavior + stop replacement protocol confirmed? | Blocks Steps 10-11, `stop_verified`→`active` transition, all stop ACs | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
