# Test Scenarios — UC-EXBOT-agent-key (Submit and Approve HL Agent Key)

> Source: `docs/qc/uc-read/UC-EXBOT-agent-key/UC-EXBOT-agent-key_agent-key_audited_20260626_v2.md`
> Generated: 2026-06-26
> Author: qc-func-scenario-design-exbot agent (Trinh.Bui)
> Version: v1
> Domain/Architecture: Cloudflare Workers + D1 + Cloudflare Secrets Store; no UI — all operations via API endpoint `POST /api/exbot/agent-key` and admin dashboard calls; queue/cron/Durable-Object pipeline for hedge-sync integration.
>
> **NOTE:** UC-EXBOT-agent-key has verdict NOT READY (57/100) due to primary blocker OQ-EXBOT-016 (admin reject path undefined) and multiple open gaps (I-01..I-14). Per user direction, scenarios for blocked areas are included with `[TBD — pending BA answer: <issue ref>]` in the Description field so tester can fill in expected results once BA resolves the gaps.

---

## UC-EXBOT-agent-key — Submit and Approve HL Agent Key

### Scenario ID: TS_UC-EXBOT-AKEY_001
**Scenario Title:** Happy path — investor submits agent key, system stores only encrypted blobs
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §3 steps 1-7; FR-EXBOT-080 srs
**Test Type:** Functional
**Description:** An investor submits a valid HL agent key via `POST /api/exbot/agent-key`. The system must generate a per-row DEK, encrypt the key with AES-256-GCM, wrap the DEK using Cloudflare Secrets Store Master Key, insert a row into `hl_agent_keys` with `approval_status='pending'`, and return a confirmation response. The D1 row must contain only encrypted blobs (`encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`) — no plaintext key or plaintext DEK.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_002
**Scenario Title:** Submission success response contains confirmation message
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §3 step 7; FR-EXBOT-080 srs
**Test Type:** Functional
**Description:** After a valid submission, the system returns a confirmation response indicating the key was received and is awaiting approval. The response must not contain any plaintext key material. [TBD — exact response schema pending BA answer: I-06]
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_003
**Scenario Title:** Admin views pending key in dashboard, then approves it
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §3 steps 8-10; FR-EXBOT-081 srs
**Test Type:** Functional
**Description:** An ExBot Admin fetches the pending key for a user via the admin dashboard. Admin approves the key. The system must update `hl_agent_keys.approval_status` to `'approved'` and record `approved_at=now`. After approval, the investor must pass bot-start preflight check 3 (FR-EXBOT-002).
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_004
**Scenario Title:** Approved key enables bot-start preflight to pass
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §3 step 10; FR-EXBOT-002 srs; FR-EXBOT-081 srs
**Test Type:** Integration
**Description:** With `hl_agent_keys.approval_status='approved'` and `expires_at > now` for the investor, trigger a bot-start preflight check. The preflight check 3 (agent key check) must pass and must not block bot start due to key status.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-AKEY_005
**Scenario Title:** Bot-start blocked when agent key is in pending status (E-EXBOT-003)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A1; FR-EXBOT-081 srs; E-EXBOT-003 srs
**Test Type:** Functional
**Description:** When `hl_agent_keys.approval_status='pending'` for an investor, trigger a bot-start preflight. The system must block the start and return error E-EXBOT-003: "Agent key is awaiting approval. Please complete the approval process before starting." (HTTP 400).
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-AKEY_006
**Scenario Title:** Bot-start blocked when agent key is revoked (E-EXBOT-003 or equivalent)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A1; FR-EXBOT-081 srs; FR-EXBOT-082 srs
**Test Type:** Functional
**Description:** When `hl_agent_keys.approval_status='revoked'` for an investor, trigger a bot-start preflight. The system must block the start. [TBD — exact error code/message for revoked status pending BA answer: I-13]
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-AKEY_007
**Scenario Title:** Bot-start blocked when agent key has expired (E-EXBOT-004)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A1; FR-EXBOT-083 srs; E-EXBOT-004 srs
**Test Type:** Functional
**Description:** When `hl_agent_keys.expires_at < now` for an investor (regardless of `approval_status`), trigger a bot-start preflight. The system must block the start and return error E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." (HTTP 400). The expired row must NOT be deleted.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-AKEY_009
**Scenario Title:** Rotation — investor submits new key while approved key exists; old key remains active during pending window
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A2; FR-EXBOT-083 srs AC
**Test Type:** Data/State
**Description:** An investor who already has `approval_status='approved'` submits a new agent key. The system must insert a new row with `approval_status='pending'` and a new DEK. The existing `approved` row must remain untouched and active. During the window between the new submission and admin approval, hedge-sync must continue to use the old approved key without interruption.
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-AKEY_010
**Scenario Title:** Rotation — admin approves new key, old row transitions to `superseded` atomically
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A2; FR-EXBOT-083 srs AC
**Test Type:** Data/State
**Description:** After an investor submits a rotation key, an admin approves the new key. The system must atomically set the new row to `approval_status='approved'` AND the old row to `approval_status='superseded'` in the same D1 transaction. At no point should there be 0 approved keys or 2 approved keys simultaneously for the same user. The `rotated_from` FK on the new row must point to the old row's ID.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_011
**Scenario Title:** Rotation — superseded is distinct from revoked; superseded row is set only by rotation, not by explicit revocation
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A2; FR-EXBOT-082 srs; FR-EXBOT-083 srs AC
**Test Type:** Data/State
**Description:** After a rotation is approved, verify that the old row has `approval_status='superseded'` (not `'revoked'`). Then, separately trigger an explicit admin revocation on an approved key and verify it transitions to `'revoked'` (not `'superseded'`). The two enum values must be distinct and assigned by distinct operations.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_012
**Scenario Title:** Rotation — hedge-sync in-flight during rotation window uses old approved key without error
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A2; FR-EXBOT-083 srs AC
**Test Type:** Integration
**Description:** While a rotation is pending (new key submitted, not yet approved), trigger a hedge-sync cycle. The worker must fetch and use the existing `approved` key (not the `pending` rotation key) to sign the HL order. The hedge-sync must complete without error. The new `pending` key must not be used until it is approved.
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-AKEY_013
**Scenario Title:** Decrypt at hedge-sync — DEK unwrap and key decrypt are function-scoped; nothing persisted
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A3; FR-EXBOT-080 srs; NFR-EXBOT-006
**Test Type:** Functional
**Description:** During a hedge-sync cycle, the worker must unwrap the DEK from `wrapped_dek` via Cloudflare Secrets Store, decrypt `encrypted_secret` using the DEK, sign the HL order with the plain key, then immediately destroy both the plain DEK and plain key. After the operation, no log entry must contain the plaintext key or plaintext DEK. The `hl_agent_keys` D1 row must still contain only encrypted blobs.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_014
**Scenario Title:** Decrypt at hedge-sync — key revoked mid-flight triggers SAFE_MODE
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A3; FR-EXBOT-082 srs
**Test Type:** Functional
**Description:** During a hedge-sync cycle's decrypt step (between DEK unwrap and HL order submission), admin revokes the key (`approval_status='revoked'`). The worker must detect the revocation failure, abort the signing operation, and trigger SAFE_MODE for the bot. No raw key material must appear in logs.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-AKEY_015
**Scenario Title:** Admin reject path — [TBD pending OQ-EXBOT-016]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A4 (missing); OQ-EXBOT-016
**Test Type:** Functional
**Description:** Admin rejects a `pending` key via the admin dashboard. [TBD — entire reject path (enum value, message to investor, resubmit eligibility) pending BA+zen decision on OQ-EXBOT-016. Issue I-03 Blocker.]
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-AKEY_016
**Scenario Title:** State transition: pending → approved (valid)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-081 srs; UC-EXBOT-agent-key §3 steps 8-9
**Test Type:** Data/State
**Description:** Submit a new agent key (row enters `pending`). Admin approves. Verify `approval_status` transitions from `'pending'` to `'approved'` and `approved_at` is recorded.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_017
**Scenario Title:** State transition: approved → superseded (via rotation approval)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-083 srs AC; UC-EXBOT-agent-key §4 A2
**Test Type:** Data/State
**Description:** With an existing `approved` row, submit a rotation key and have admin approve the new key. Verify the old row transitions from `'approved'` to `'superseded'`. This transition must happen atomically with the new row becoming `'approved'`.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_018
**Scenario Title:** State transition: approved → revoked (explicit admin revocation)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-082 srs
**Test Type:** Data/State
**Description:** Admin explicitly revokes an `approved` key. Verify `approval_status` transitions from `'approved'` to `'revoked'` and `revoked_at` is recorded. [TBD — `revoked_at` field absent in ERD; verify field exists or gap persists: Issue I-07]
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_019
**Scenario Title:** State transition: pending → rejected/deleted (admin reject) — [TBD]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** OQ-EXBOT-016; UC-EXBOT-agent-key §4 A4 (missing)
**Test Type:** Data/State
**Description:** Admin rejects a `pending` key. Verify the row's final state. [TBD — target state (`rejected`? deleted? other?) pending OQ-EXBOT-016. Issue I-03 Blocker. Also verify state diagram in states.md is updated after BA resolves OQ-EXBOT-016.]
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_020
**Scenario Title:** Invalid state transition: attempt to INSERT second approved row for same user — DB rejects
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-082 srs
**Test Type:** Data/State
**Description:** Attempt to INSERT a second row with `approval_status='approved'` for the same user without first superseding/revoking the existing `approved` row. The D1 UNIQUE constraint must reject the operation. Only 1 `approved` row per user must exist at any time.
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_021
**Scenario Title:** Business rule: plain key and plain DEK never appear in D1 or logs
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-080 srs; NFR-EXBOT-006; UC-EXBOT-agent-key §3 steps 4-6
**Test Type:** Functional
**Description:** After a key submission, inspect the `hl_agent_keys` D1 row. Verify that only `encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv` are stored. After a hedge-sync decrypt cycle, inspect all log output from the worker. No log entry must contain the plaintext key value or plaintext DEK value.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_022
**Scenario Title:** Business rule: DELETE of a revoked row is forbidden
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-082 srs
**Test Type:** Functional
**Description:** After a key is explicitly revoked (`approval_status='revoked'`), attempt to DELETE the row from `hl_agent_keys`. The database must reject the DELETE operation. The row must be retained for audit purposes. This applies regardless of which actor attempts the delete.
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-AKEY_023
**Scenario Title:** Business rule: exactly 1 approved key per user at all times
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-082 srs
**Test Type:** Data/State
**Description:** At any given point in time, verify that a user has at most 1 row with `approval_status='approved'` in `hl_agent_keys`. After rotation approval, verify the count remains 1 (old row is `superseded`, new row is `approved`). After revocation, the count drops to 0 (no `approved` row).
**Test Focus:** State transition

### Scenario ID: TS_UC-EXBOT-AKEY_024
**Scenario Title:** Boundary: key expires exactly at `expires_at` timestamp — preflight blocks
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-083 srs; E-EXBOT-004 srs
**Test Type:** Functional
**Description:** Set `expires_at` to exactly `now` (boundary value). Trigger bot-start preflight. The system must block the start with E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." [TBD — `expires_at` owner (investor or system) and format pending BA answer: Issue I-04]
**Test Focus:** Boundary

### Scenario ID: TS_UC-EXBOT-AKEY_025
**Scenario Title:** Boundary: key has `expires_at` 1 second in the future — preflight passes
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-083 srs
**Test Type:** Functional
**Description:** Set `expires_at` to `now + 1 second`. Trigger bot-start preflight. The preflight agent key check must pass (key is not yet expired). [TBD — `expires_at` owner and format pending BA answer: Issue I-04]
**Test Focus:** Boundary

### Scenario ID: TS_UC-EXBOT-AKEY_026
**Scenario Title:** Double-pending: investor submits while a pending row already exists — [TBD]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 (missing behavior); Issue I-10
**Test Type:** Functional
**Description:** An investor submits a key while their existing row has `approval_status='pending'`. [TBD — behavior (reject? overwrite? insert second row?) pending BA answer: Issue I-10]
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-AKEY_027
**Scenario Title:** Integration: expiry warning condition (`expires_at - now ≤ 7d`) is detectable by deep-audit cron
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §4 A5; FR-EXBOT-083 srs
**Test Type:** Integration
**Description:** Set `hl_agent_keys.expires_at` to `now + 6 days` for a user with `approval_status='approved'`. Run a deep-audit cron cycle. Verify the cron detects `expires_at - now ≤ 7d` and enqueues an expiry notification for the investor. This scenario verifies the integration contract from the agent-key data side (owned by UC-EXBOT-deep-audit for full coverage).
**Test Focus:** Integration

### Scenario ID: TS_UC-EXBOT-AKEY_028
**Scenario Title:** Admin approves key after `expires_at` already passed — [TBD]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §3 step 9; FR-EXBOT-083 srs; Issue I-12
**Test Type:** Functional
**Description:** Admin processes a `pending` key after `expires_at` has already passed. [TBD — behavior (approve is allowed but key fails preflight immediately, or system blocks the approval entirely) pending BA answer: Issue I-12]
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-AKEY_029
**Scenario Title:** Permission: investor cannot approve own key
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §1 Actors; FR-EXBOT-081 srs
**Test Type:** Functional
**Description:** An investor calls the admin approval endpoint for their own pending key. The system must reject the action and return an authorization error. Only ExBot Admin (zen) may approve keys.
**Test Focus:** Permission/Role

### Scenario ID: TS_UC-EXBOT-AKEY_030
**Scenario Title:** Permission: actor conflict on POST endpoint — investor vs admin [TBD per I-01]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** UC-EXBOT-agent-key §1 Actors; `frd.md` FR-EXBOT-100; Issue I-01
**Test Type:** Functional
**Description:** Call `POST /api/exbot/agent-key` as an admin (not an investor). [TBD — UC says POST is investor-only, but `frd.md` FR-EXBOT-100 lists Admin as actor for POST. Expected access control behavior depends on BA resolving Issue I-01.]
**Test Focus:** Permission/Role

### Scenario ID: TS_UC-EXBOT-AKEY_031
**Scenario Title:** Each submission produces unique encrypted blobs even for the same plaintext key (random IV per row)
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-080 srs (IV 12 bytes random per row)
**Test Type:** Functional
**Description:** An investor submits the same agent key value twice (second submission allowed assuming first was superseded or no pending exists). Because the IV is generated randomly per row, the two `encrypted_secret` and `secret_iv` values in D1 must differ, confirming no IV reuse. [TBD — double-submit behavior when pending already exists: Issue I-10]
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-AKEY_032
**Scenario Title:** Concurrency: two admins approve same pending key simultaneously — exactly 1 approved row result
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-081 srs; FR-EXBOT-082 srs
**Test Type:** Data/State
**Description:** Two admin sessions concurrently attempt to approve the same `pending` key for the same user. The system must accept exactly one approval. After both operations complete, exactly 1 `approved` row must exist for the user — no duplicate `approved` rows.
**Test Focus:** Idempotency/Concurrency

### Scenario ID: TS_UC-EXBOT-AKEY_033
**Scenario Title:** AC-01: key submission stores only encrypted blobs, status is pending
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** US-011 AC-1; UC-EXBOT-agent-key §3; FR-EXBOT-080 srs
**Test Type:** Acceptance
**Description:** Submit a valid agent key. Verify D1 row has `approval_status='pending'` and contains only encrypted fields (`encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`). No plaintext key in D1 or in any log.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_034
**Scenario Title:** AC-02: admin approval sets status to approved and records approved_at
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** US-011 AC-2; UC-EXBOT-agent-key §3 steps 9-10; FR-EXBOT-081 srs
**Test Type:** Acceptance
**Description:** Admin approves a `pending` key. Verify `hl_agent_keys.approval_status='approved'` and `approved_at` is set. The investor must subsequently pass bot-start preflight check 3.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_035
**Scenario Title:** AC-03: expired key blocks bot start with E-EXBOT-004; row not deleted
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** US-011 AC-3; FR-EXBOT-083 srs; E-EXBOT-004 srs
**Test Type:** Acceptance
**Description:** With `hl_agent_keys.expires_at < now` for an investor, trigger a bot-start preflight. The system must block with E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." The expired row must remain in D1 (not deleted).
**Test Focus:** Alternative flow

### Scenario ID: TS_UC-EXBOT-AKEY_036
**Scenario Title:** AC-04: no plaintext key recoverable from D1 dump or log output
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** US-011 AC-4; FR-EXBOT-080 srs; NFR-EXBOT-006
**Test Type:** Acceptance
**Description:** After submitting and using a key for hedge-sync signing, dump the `hl_agent_keys` D1 table and inspect all worker logs. The plaintext agent key must not be recoverable from either source. Only encrypted blobs exist in D1; no log line contains the raw key value.
**Test Focus:** Happy path

### Scenario ID: TS_UC-EXBOT-AKEY_037
**Scenario Title:** Cloudflare Secrets Store unavailable at DEK wrap time (submission) — [TBD]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-080 srs; UC-EXBOT-agent-key §3 step 5; Issue I-08
**Test Type:** Functional
**Description:** Cloudflare Secrets Store is unavailable when the worker attempts to wrap the DEK during a key submission. [TBD — error behavior (rollback? retry? specific error response?) pending BA answer: Issue I-08]
**Test Focus:** Error/Exception

### Scenario ID: TS_UC-EXBOT-AKEY_038
**Scenario Title:** Cloudflare Secrets Store unavailable at DEK unwrap time (hedge-sync) — [TBD]
**UC Reference:** UC-EXBOT-agent-key — Submit and Approve HL Agent Key
**Req-ID:** FR-EXBOT-080 srs; UC-EXBOT-agent-key §4 A3; Issue I-08
**Test Type:** Functional
**Description:** Cloudflare Secrets Store is unavailable when the worker attempts to unwrap the DEK during a hedge-sync signing step. [TBD — error behavior (SAFE_MODE? retry? specific log event?) pending BA answer: Issue I-08]
**Test Focus:** Error/Exception

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| Admin reject path (full flow) | BLOCKED: OQ-EXBOT-016 unresolved — enum value, message, resubmit eligibility all undefined. Issue I-03 (Blocker). Scenarios TS_015 and TS_019 included with TBD. | Resolve OQ-EXBOT-016 (BA + zen), then complete TS_015 and TS_019. |
| Agent key format validation (reject master key) | BLOCKED: No format/length/prefix defined for valid agent key. Issue I-05. | BA to define format rule; add new scenario for negative case. |
| `POST /api/exbot/agent-key` request/response schema | BLOCKED: API contract not published. Issue I-06. | BA/Dev to publish API contract; update TS_001 and TS_002 with concrete assertions. |
| `expires_at` boundary (exact values) | BLOCKED: Owner and format of `expires_at` undefined. Issue I-04. TS_024 and TS_025 included with TBD. | BA to define; complete TS_024/TS_025. |
| Double-pending behavior | BLOCKED: Expected behavior undefined. Issue I-10. TS_026 included with TBD. | BA to define; complete TS_026. |
| Cloudflare Secrets Store failure handling | BLOCKED: Neither UC nor SRS defines error behavior. Issue I-08. TS_037 and TS_038 included with TBD. | BA to define; complete TS_037/TS_038. |
| Approved-at-expiry edge case | BLOCKED: Behavior undefined. Issue I-12. TS_028 included with TBD. | BA to define; complete TS_028. |
| Actor conflict on POST (investor vs admin) | BLOCKED: FRD conflicts with UC. Issue I-01. TS_030 included with TBD. | BA to resolve in FRD; complete TS_030. |
| Rate limit on POST endpoint | BLOCKED: No rate limit policy defined. Issue I-11. | BA to define; add new scenario. |
| `approved_by` audit trail | BLOCKED: Field absent from ERD. Issue I-07. | BA to add field to ERD; add audit trail scenario. |
| Expiry notification (full) | OOS: Owned by UC-EXBOT-deep-audit per UC §4 A5. TS_027 covers integration contract only. | Design full expiry notification scenarios under UC-EXBOT-deep-audit. |
| Performance / load testing | NFR: Out of scope for functional scenario design. | Defer to performance test phase. |
| Security penetration testing | NFR: Beyond functional auth scope. | Defer to security specialist. |
