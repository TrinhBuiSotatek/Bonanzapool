# Question Backlog — UC-EXBOT-agent-key

> Document Title: UC-EXBOT-agent-key Question Backlog v1
> Generated: 2026-06-17 | Source: UC-EXBOT-agent-key_agent-key_audited_20260617_v1.md | Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q1 | H | uc-agent-key.md A2 vs spec FR-EXBOT-083 | UC A2 uses `status='revoked'` for rotation; spec FR-EXBOT-083 uses `status='superseded'` — are these distinct states? When is each applied? | Canonical state machine for rotation test cases | Open |
| Q2 | H | FR-EXBOT-082 | In-flight hedge-sync decrypting a `revoked` key → SAFE_MODE: triggered at status check (before decrypt) or decryption failure (after decrypt attempt)? | Security test case trigger mechanism | Open |
| Q3 | M | uc-agent-key.md §5 Postconditions | `users.hl_agent_key_id` update: after admin approval or after first preflight pass? | AC-02 step coverage | Open |
| Q4 | M | uc-agent-key.md §3 step 1 | `POST /api/exbot/agent-key` request schema — fields, required validation, max key length, format? | Input validation test coverage | Open |
| Q5 | M | FR-EXBOT-083 | Proactive 7d expiry warning: which deep-audit event fires it? Deep-audit run frequency? | Notification scheduling test | Open |
| Q6 | M | uc-agent-key.md §3 step 5 | Cloudflare Secrets Store unavailability: error path if `MasterKey.wrap` fails? | Submission failure test coverage | Open |
| Q7 | L | FR-EXBOT-082 | UNIQUE on `(user_id, approval_status='approved')` enforced at DB level or application level? | Race condition and DB schema tests | Open |
| Q8 | L | uc-agent-key.md §3 step 9 | Admin approval endpoint name — `PUT /api/exbot/agent-key/{id}/approve` or another path? | Admin AC test requires concrete endpoint | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
