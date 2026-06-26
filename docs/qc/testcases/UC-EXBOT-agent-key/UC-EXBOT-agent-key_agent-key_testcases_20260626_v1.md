# Test Cases — UC-EXBOT-agent-key Submit and Approve HL Agent Key

**Total test cases:** 58 (FUNC: 37, INTG: 15, NFR: 6)
**Scope:** Logic-only (backend / API / bot — no UI)
**Source UC:** docs/qc/uc-read/UC-EXBOT-agent-key/UC-EXBOT-agent-key_agent-key_audited_20260626_v2.md
**Source scenarios:** docs/qc/scenarios/UC-EXBOT-agent-key/UC-EXBOT-agent-key_agent-key_scenarios_20260626_v1.md
**Output language:** English

#### Requirement Traceability Matrix

| AC ID | Acceptance Criteria | Linked Test Cases | Status |
|---|---|---|---|
| AC-01 | Key submitted → only encrypted blobs stored; approval_status='pending'; confirmation returned | TC_001, TC_002, TC_003, TC_004, TC_005 | Covered |
| AC-02 | Admin approves → approval_status='approved', approved_at recorded; investor passes preflight check 3 | TC_010, TC_011, TC_015 | Covered |
| AC-03 | Expired key blocks bot start with E-EXBOT-004; existing row NOT deleted | TC_013, TC_014, TC_054 | Covered |
| AC-04 | Plain DEK and plain key destroyed after signing; no log entry with raw values; D1 row still encrypted | TC_040, TC_041, TC_042 | Covered |
| AC-05 | Rotation: old row superseded AND new row approved atomically; no window with 0 or 2 approved keys | TC_020, TC_021, TC_022, TC_023 | Covered |
| AC-06 | Revoked key mid hedge-sync → SAFE_MODE; no raw key material in logs | TC_030, TC_031, TC_032 | Covered |
| AC-07 | DELETE of revoked row forbidden; row retained for audit | TC_033, TC_034 | Covered |
| AC-08 | Admin reject path | TC_012 (TBD — OQ-EXBOT-016) | Blocked |

---

## I. Operation: Agent Key Submission

### I.1. Functional verification — Agent Key Submission

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_001 | Verify key submission stores only encrypted blobs in D1 with pending status | 1. Investor has a valid HL agent key ready to submit.\n2. ExBot Worker has access to the Master Key in Cloudflare Secrets Store.\n3. No existing key row for this investor (clean state). | 1. Submit the agent key via POST /api/exbot/agent-key. | 1. A new row is inserted into hl_agent_keys with approval_status='pending'. The row contains only encrypted fields (encrypted_secret, wrapped_dek, secret_iv, secret_auth_tag, dek_iv). No plaintext key or plaintext DEK appears in D1. The response confirms the key was received and is awaiting approval. (Reference: FR-EXBOT-080, FR-EXBOT-081 srs; AC-01.) | P0 |
| TC_002 | Verify the per-row DEK is newly generated for each submission (unique IV per row) | 1. Investor submits a second agent key after the first was revoked. | 1. Submit a new agent key via POST /api/exbot/agent-key.\n2. Compare secret_iv and dek_iv of the new row with those of any prior row for this user. | 2. The new row has distinct secret_iv and dek_iv values — IVs are never reused across submissions. The new row has approval_status='pending'; the old row is untouched. (Reference: FR-EXBOT-080 srs; NFR-EXBOT-006.) | P0 |
| TC_003 | Verify submission returns the correct confirmation message | 1. All preconditions for a valid submission are met. | 1. Submit the agent key and read the API response. | 1. The response body contains the message "Agent key received and encrypted. Awaiting approval." The hl_agent_keys row shows approval_status='pending'. (Reference: UC §3 step 7; AC-01.) | P1 |
| TC_004 | Verify plain key and DEK are not present in logs after submission | 1. A valid agent key is submitted. | 1. Submit the agent key and inspect the worker log output produced during the request. | 1. The raw agent key value and the raw DEK value do not appear in any log line produced during or after the submission. The D1 row contains only encrypted blobs. (Reference: FR-EXBOT-080 srs; NFR-EXBOT-006; AC-04.) | P0 |
| TC_005 | Verify Cloudflare Secrets Store unavailability during submission | 1. Cloudflare Secrets Store is unavailable (mocked to fail). | 1. Submit an agent key while the Secrets Store is unreachable. | 1. [TBD — pending BA answer: Issue I-08. Behavior when Cloudflare Secrets Store is unavailable at DEK wrap step is not defined in UC or SRS. Expected: submission fails with an appropriate error; no partial row is inserted into D1.] | P0 |

### I.2. Integration & State verification — Agent Key Submission

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_006 | Verify double-pending behavior when investor submits while a pending row already exists | 1. Investor already has a row with approval_status='pending' in hl_agent_keys. | 1. Submit a new agent key while the existing pending row has not yet been approved or rejected. | 1. [TBD — pending BA answer: Issue I-10. Behavior when investor submits a key while pending row already exists is not defined in UC or SRS. Expected: system either rejects the duplicate submission or replaces the pending row — BA must confirm.] | P1 |
| TC_007 | Verify investor cannot access or read the master private key through any submission response | 1. A valid agent key is submitted. | 1. Inspect the API response and any intermediate outputs during the submission flow. | 1. No API response field contains the Master Key, any DEK value, or any plaintext key material. The Cloudflare Secrets Store Master Key is never exposed outside the worker's secure context. (Reference: FR-EXBOT-080 srs.) | P0 |

### I.3. Non-functional (logic) verification — Agent Key Submission

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_008 | Verify D1 dump of hl_agent_keys contains only encrypted blobs | 1. At least one agent key has been submitted and the row exists in hl_agent_keys. | 1. Read all columns of the hl_agent_keys row directly from D1. | 1. The row contains only encrypted fields: encrypted_secret, wrapped_dek, secret_iv, secret_auth_tag, dek_iv. There is no column containing a plaintext key, no plaintext DEK, and no partial cleartext data. The only way to recover the plaintext key is via the Master Key in Cloudflare Secrets Store. (Reference: FR-EXBOT-080 srs; NFR-EXBOT-006; AC-04.) | P0 |

## II. Operation: Admin Approval

### II.1. Functional verification — Admin Approval

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_010 | Verify admin approval sets approval_status to approved and records approved_at | 1. A row exists in hl_agent_keys with approval_status='pending' for the target investor.\n2. The actor is ExBot Admin. | 1. Admin approves the pending key via the admin dashboard endpoint.\n2. Read the hl_agent_keys row after approval. | 2. The row's approval_status changes from 'pending' to 'approved'. approved_at is set to the current timestamp. The investor can now pass bot-start preflight check 3. (Reference: FR-EXBOT-081 srs; UC §3 steps 9-10; AC-02.) | P0 |
| TC_011 | Verify bot start is unblocked after key is approved | 1. Investor key was pending; admin has just approved it (approval_status='approved', expires_at in future).\n2. All other bot-start preflight checks pass. | 1. Trigger bot start preflight for the investor. | 1. Preflight check 3 (agent key) passes. The bot start proceeds to the next preflight check without returning E-EXBOT-003 or E-EXBOT-004. (Reference: FR-EXBOT-002 step 3; FR-EXBOT-081 srs; AC-02.) | P0 |
| TC_012 | Verify admin reject path (blocked — OQ-EXBOT-016) | 1. A row exists with approval_status='pending'.\n2. Admin decides to reject rather than approve. | 1. Admin rejects the pending key. | 1. [TBD — pending BA answer: Issue I-03 / OQ-EXBOT-016. Admin reject path is entirely undefined. Expected: row transitions to a defined rejected state; investor is notified; resubmission is allowed or disallowed per BA decision.] | P0 |
| TC_013 | Verify bot start is blocked when key is still pending (E-EXBOT-003) | 1. The investor hl_agent_keys row has approval_status='pending'.\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Bot start is blocked. The response returns error code E-EXBOT-003 with message "Agent key is awaiting approval. Please complete the approval process before starting." (HTTP 400). No bot record is created in D1. (Reference: FR-EXBOT-002 step 3; FR-EXBOT-081 srs; E-EXBOT-003 spec §5.) | P0 |
| TC_014 | Verify bot start is blocked when key is expired (E-EXBOT-004) | 1. The investor hl_agent_keys row has approval_status='approved' but expires_at < now.\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Bot start is blocked. The response returns error code E-EXBOT-004 with message "Your HL agent key has expired. Please submit a new one." (HTTP 400). The expired row is NOT deleted from D1. No bot record is created. (Reference: FR-EXBOT-081 srs; FR-EXBOT-083 srs; E-EXBOT-004 spec §5; AC-03.) | P0 |
| TC_015 | Verify bot start passes when key is approved and not expired | 1. The investor hl_agent_keys row has approval_status='approved' and expires_at > now.\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Preflight check 3 passes. Bot start proceeds. No error code E-EXBOT-003 or E-EXBOT-004 is returned. (Reference: FR-EXBOT-002 step 3; FR-EXBOT-081 srs.) | P0 |
| TC_016 | Verify bot start is blocked when key is revoked (E-EXBOT-003) | 1. The investor hl_agent_keys row has approval_status='revoked'.\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Bot start is blocked. The response returns E-EXBOT-003 with message "Agent key is awaiting approval. Please complete the approval process before starting." (HTTP 400). No bot record is created. (Reference: FR-EXBOT-081 srs; E-EXBOT-003 spec §5.) | P0 |

### II.2. Integration & State verification — Admin Approval

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_017 | Verify investor (non-admin) cannot approve a key via the agent-key endpoint | 1. A pending row exists for investor A.\n2. The caller is investor A (not admin). | 1. Investor A calls the approve action on the agent-key endpoint. | 1. [TBD — pending BA answer: Issue I-01. frd.md FR-EXBOT-100 lists Admin as actor for all /api/exbot/agent-key methods including POST; UC defines POST as investor action. Expected: approval action returns 403 Forbidden for a non-admin caller.] | P0 |
| TC_018 | Verify admin cannot approve a key when expires_at has already passed at approval time | 1. A pending row exists; expires_at was set to a date in the past.\n2. Admin attempts to approve the row. | 1. Admin approves the key whose expires_at < now. | 1. [TBD — pending BA answer: Issue I-12. Behavior when admin approves an already-expired key is not defined. Expected: either approval is rejected with a validation error, or approval succeeds but the key immediately fails preflight — BA must confirm.] | P1 |

### II.3. Non-functional (logic) verification — Admin Approval

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_019 | Verify only one approved key per user is enforced at the DB level | 1. Investor already has a row with approval_status='approved'.\n2. A second pending row is also present for the same investor (rotation scenario). | 1. Attempt to approve the second pending row without atomically setting the first row to superseded. | 1. The D1 hl_agent_keys table rejects the second 'approved' row for the same user via the UNIQUE constraint — two rows for the same user cannot both have approval_status='approved' simultaneously. (Reference: FR-EXBOT-082 srs; AC-05.) | P0 |

## III. Operation: Key Rotation

### III.1. Functional verification — Key Rotation

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_020 | Verify key rotation atomically sets old row to superseded and new row to approved | 1. Investor has an existing approved row in hl_agent_keys.\n2. Investor submitted a new key (new row with approval_status='pending'). | 1. Admin approves the new pending key.\n2. Read both rows from hl_agent_keys immediately after approval. | 2. In a single D1 transaction: the old row approval_status changes to 'superseded' AND the new row approval_status changes to 'approved'. There is no moment between the two updates where either 0 approved keys or 2 approved keys exist for this user. rotated_from FK on the new row points to the old row's ID. (Reference: FR-EXBOT-083 srs AC; UC §4 A2; AC-05.) | P0 |
| TC_021 | Verify existing approved key stays active during the pending window before rotation is approved | 1. Investor has an existing approved row.\n2. Investor has submitted a new key (new row is pending); admin has not yet approved it. | 1. Check which key passes bot-start preflight check 3. | 1. The existing approved row (not expired) passes preflight check 3. The new pending row does not block the existing approved key from being used. No interruption to hedge-sync operations that use the approved key. (Reference: FR-EXBOT-083 srs; UC §4 A2; AC-05.) | P0 |
| TC_022 | Verify superseded row is NOT treated as revoked — only rotation sets superseded | 1. A rotation has been completed: old row is superseded, new row is approved. | 1. Check whether the superseded row is treated as revoked for preflight or hedge-sync purposes. | 1. The superseded row is treated as inactive for signing and preflight — it cannot be used to pass preflight check 3. However, it is NOT the same as revoked: revoked is set only by explicit admin action, not by rotation. The superseded row is retained in D1 with the rotated_from chain intact for audit. (Reference: FR-EXBOT-082 srs; FR-EXBOT-083 srs; UC §4 A2 note.) | P1 |
| TC_023 | Verify the rotated_from chain is preserved after multiple rotations | 1. Investor has gone through two rotations: key A superseded, key B superseded, key C is current approved. | 1. Read all hl_agent_keys rows for the investor. | 1. Row C has rotated_from pointing to row B; row B has rotated_from pointing to row A. All three rows remain in D1 — no row is deleted. Rows A and B are superseded; row C is approved. (Reference: FR-EXBOT-083 srs AC; FR-EXBOT-082 srs — no destructive delete.) | P1 |

### III.2. Integration & State verification — Key Rotation

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_024 | Verify in-flight hedge-sync continues with old approved key during rotation pending window | 1. Investor has approved key A; has submitted new pending key B; hedge-sync is in progress using key A. | 1. Observe the hedge-sync execution while the rotation is pending. | 1. Hedge-sync uses the approved key A for signing without interruption. Key B pending status does not interfere with key A usage. (Reference: FR-EXBOT-083 srs; UC §4 A2.) | P0 |
| TC_025 | Verify hedge-sync uses new approved key after rotation completes | 1. Rotation has completed: key A is superseded, key B is approved. | 1. Trigger a hedge-sync that requires agent key decryption. | 1. Worker fetches the row with approval_status='approved' (key B) for decryption. Key A (superseded) is not selected for signing. (Reference: FR-EXBOT-082 srs; FR-EXBOT-083 srs.) | P0 |


## IV. Operation: Key Revocation

### IV.1. Functional verification — Key Revocation

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_030 | Verify explicit revocation sets approval_status to revoked and revoked_at to now | 1. Investor has an approved key row.\n2. Admin explicitly revokes the key. | 1. Admin revokes the key via the admin dashboard.\n2. Read the hl_agent_keys row. | 2. The row's approval_status changes to 'revoked'. revoked_at is set to the current timestamp. The row remains in D1 — it is NOT deleted. (Reference: FR-EXBOT-082 srs; AC-06.) | P0 |
| TC_031 | Verify bot start is blocked immediately after key is revoked (E-EXBOT-003) | 1. Investor's key has been revoked (approval_status='revoked').\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Bot start is blocked with E-EXBOT-003: "Agent key is awaiting approval. Please complete the approval process before starting." (HTTP 400). No bot record is created. (Reference: FR-EXBOT-081 srs; E-EXBOT-003 spec §5.) | P0 |
| TC_032 | Verify hedge-sync that decrypts a revoked key fails safely and enters SAFE_MODE | 1. Investor's bot is running (status='active').\n2. Admin revokes the investor's agent key (approval_status='revoked') while a hedge-sync is in progress at the decrypt step. | 1. Observe the hedge-sync execution when key revocation occurs mid-flight. | 1. The worker receives a decryption failure. The bot transitions to safe_mode (bots.lifecycle_state='safe_mode', bots.status='safe_mode'). No raw key material or DEK appears in any log line. The hedge-sync does not complete partially — no HL order is submitted after the failure. (Reference: FR-EXBOT-082 srs; AC-06.) | P0 |
| TC_033 | Verify DELETE of a revoked row is forbidden | 1. A row exists with approval_status='revoked'. | 1. Attempt to DELETE the revoked row from hl_agent_keys. | 1. The DELETE is rejected. The row remains in D1 for audit purposes. (Reference: FR-EXBOT-082 srs; AC-07.) | P0 |
| TC_034 | Verify DELETE of any hl_agent_keys row (regardless of status) is forbidden | 1. Rows with various statuses (pending, approved, superseded, revoked) exist in hl_agent_keys. | 1. Attempt to DELETE each row type from hl_agent_keys. | 1. All DELETE attempts are rejected. All rows are retained in D1 for audit. No status type is exempt from the delete prohibition. (Reference: FR-EXBOT-082 srs; AC-07.) | P0 |

### IV.2. Integration & State verification — Key Revocation

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_035 | Verify no two approved rows exist for the same user after revocation + new submission | 1. Investor A's existing key was revoked.\n2. Investor A submits a new key (now pending).\n3. Admin approves the new key. | 1. Read all hl_agent_keys rows for investor A. | 1. Exactly one row has approval_status='approved'. The previously revoked row has approval_status='revoked' and remains. No two rows are simultaneously approved. (Reference: FR-EXBOT-082 srs.) | P0 |
| TC_036 | Verify Cloudflare Secrets Store unavailability at hedge-sync DEK unwrap step | 1. Investor has an approved, non-expired key.\n2. A hedge-sync is triggered.\n3. Cloudflare Secrets Store is unavailable (mocked to fail) at the DEK unwrap step. | 1. Let hedge-sync attempt to unwrap the DEK. | 1. [TBD — pending BA answer: Issue I-08. Behavior when Cloudflare Secrets Store is unavailable at DEK unwrap during hedge-sync is not defined. Expected: decryption failure → bot enters SAFE_MODE; no raw key material in logs.] | P0 |


## V. Operation: Key Decrypt at Hedge-Sync

### V.1. Functional verification — Key Decrypt at Hedge-Sync

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_040 | Verify hedge-sync decrypts approved key in function scope and destroys it immediately | 1. Investor has approval_status='approved' and expires_at > now key.\n2. Hedge-sync is triggered. | 1. Execute a hedge-sync that requires HL signing.\n2. Inspect logs and D1 after the signing completes. | 2. The HL order is signed and submitted. After the signing operation, the plain DEK and plain key are destroyed (function-scoped). No log line contains the raw key or DEK. The hl_agent_keys D1 row still contains only encrypted blobs — it is not modified during the decrypt operation. (Reference: FR-EXBOT-080 srs; NFR-EXBOT-006; AC-04.) | P0 |
| TC_041 | Verify hedge-sync decryption uses the correct fields for AES-256-GCM decrypt | 1. An approved key row exists with all five encrypted fields populated. | 1. Execute hedge-sync and trace the decrypt sequence. | 1. Worker fetches the approved row; performs MasterKey.unwrap(wrapped_dek, dek_iv) to get plain DEK; then performs AES-256-GCM.decrypt(encrypted_secret, DEK, secret_iv, secret_auth_tag) to get the plain key. All five fields (encrypted_secret, wrapped_dek, secret_iv, secret_auth_tag, dek_iv) are consumed correctly. (Reference: FR-EXBOT-080 srs; UC §4 A3.) | P0 |
| TC_042 | Verify plain key and DEK are not in logs during hedge-sync signing | 1. Hedge-sync executes and successfully signs an HL order. | 1. Inspect all worker log output produced during the hedge-sync signing operation. | 1. Neither the raw agent key value nor the raw DEK value appears in any log line. Logs may record that signing was attempted and succeeded, but must contain no key material. (Reference: FR-EXBOT-080 srs; NFR-EXBOT-006; AC-04.) | P0 |
| TC_043 | Verify hedge-sync does not fetch or use a superseded key row for signing | 1. Investor has a superseded row (old key after rotation) and an approved row (new key). | 1. Execute a hedge-sync and observe which row is fetched for decryption. | 1. Worker fetches only the row with approval_status='approved'. The superseded row is not selected for decryption or signing. (Reference: FR-EXBOT-082 srs; FR-EXBOT-083 srs.) | P1 |

### V.2. Integration & State verification — Key Decrypt at Hedge-Sync

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_044 | Verify hedge-sync enters SAFE_MODE when no approved key exists at signing time | 1. Investor's bot is running.\n2. No row with approval_status='approved' exists (e.g., key was revoked between preflight and hedge-sync execution). | 1. Hedge-sync worker attempts to fetch an approved key for decryption. | 1. Worker cannot find an approved key row. The hedge-sync fails safely. The bot transitions to safe_mode. No HL order is submitted. No key material is logged. (Reference: FR-EXBOT-082 srs; AC-06.) | P0 |
| TC_045 | Verify hedge-sync SAFE_MODE entry does not expose key material in error logs | 1. Hedge-sync fails during decryption due to key revocation. | 1. Inspect error logs generated by the SAFE_MODE entry. | 1. Error logs record the failure reason (e.g., decryption failed, key revoked) without including any raw key bytes, DEK bytes, or encrypted blob contents. (Reference: FR-EXBOT-082 srs; NFR-EXBOT-006; AC-06.) | P0 |


## VI. Operation: Expiry Handling & Preflight Enforcement

### VI.1. Functional verification — Expiry Handling

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_050 | Verify bot start is blocked exactly when expires_at < now (boundary: expired by one second) | 1. hl_agent_keys row has approval_status='approved' and expires_at = now - 1 second.\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Bot start is blocked with E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." (HTTP 400). The expired row is NOT deleted. (Reference: FR-EXBOT-083 srs; E-EXBOT-004 spec §5; AC-03.) | P0 |
| TC_051 | Verify bot start passes when expires_at is exactly one second in the future (boundary) | 1. hl_agent_keys row has approval_status='approved' and expires_at = now + 1 second.\n2. All other preflight checks pass. | 1. Trigger bot start preflight. | 1. Preflight check 3 passes. The bot start is not blocked by E-EXBOT-004. (Reference: FR-EXBOT-083 srs.) | P0 |
| TC_052 | Verify deep-audit enqueues expiry notification when key expires within 7 days | 1. hl_agent_keys row has approval_status='approved' and expires_at = now + 5 days (within 7-day window).\n2. Deep-audit cron runs. | 1. Execute a deep-audit cycle. | 1. The system enqueues a notification message to the investor via the notification queue. The message states "Your HL agent key expires in 5 days. Submit a new key to avoid bot interruption." (Reference: FR-EXBOT-083 srs; UC §4 A5.) | P1 |
| TC_053 | Verify deep-audit does NOT enqueue notification when key expires more than 7 days out | 1. hl_agent_keys row has approval_status='approved' and expires_at = now + 8 days.\n2. Deep-audit cron runs. | 1. Execute a deep-audit cycle. | 1. No expiry notification is enqueued for this investor. The 7-day threshold is not exceeded. (Reference: FR-EXBOT-083 srs.) | P1 |
| TC_054 | Verify expired row is not deleted after bot start is blocked by E-EXBOT-004 | 1. hl_agent_keys row has approval_status='approved' and expires_at < now. | 1. Trigger bot start preflight and confirm E-EXBOT-004 is returned.\n2. Read the hl_agent_keys row after the blocked start. | 2. The expired row remains in D1 with its original values unchanged. No automated deletion occurs as a result of the preflight check. (Reference: FR-EXBOT-083 srs; AC-03.) | P0 |

### VI.2. Integration & State verification — Expiry Handling

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_055 | Verify boundary: deep-audit notification threshold is exactly 7 days (not less, not more) | 1. Investor A: expires_at = now + 7 days (exactly at boundary).\n2. Investor B: expires_at = now + 7 days + 1 second (just outside boundary). | 1. Execute a deep-audit cycle. | 1. Investor A receives a notification (7-day window satisfied: expires_at - now <= 7 days). Investor B does NOT receive a notification. (Reference: FR-EXBOT-083 srs.) | P1 |

## VII. Operation: Access Control & Permission Enforcement

### VII.1. Functional verification — Access Control

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_060 | Verify investor cannot approve their own key (actor conflict TBD) | 1. Investor A has a pending key row.\n2. Investor A calls the approval endpoint. | 1. Investor A attempts to approve their own key. | 1. [TBD — pending BA answer: Issue I-01. Actor conflict between frd.md FR-EXBOT-100 (Admin owns all agent-key endpoints) and UC (investor submits via POST). Expected: investor is rejected (403 Forbidden) for the approval action — only Admin can approve.] | P0 |
| TC_061 | Verify ExBot Worker is only reachable via OPERATOR facade CF service binding | 1. A direct HTTP request to the ExBot Worker endpoint is made without going through the OPERATOR facade. | 1. Attempt to call POST /api/exbot/agent-key directly on the ExBot Worker URL, bypassing OPERATOR. | 1. The direct request is rejected (HTTP 403). The ExBot Worker is not internet-accessible; all calls must go through the OPERATOR facade via CF service binding with an internal token. (Reference: FR-EXBOT-090; BR-EXBOT-010.) | P0 |

### VII.2. Integration & State verification — Access Control

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_062 | Verify admin cannot revoke a key that does not exist for the target user | 1. No hl_agent_keys row exists for investor B. | 1. Admin attempts to revoke investor B's key. | 1. The request fails with an appropriate error (key not found / no row to revoke). No new rows are inserted. (Reference: FR-EXBOT-082 srs.) | P1 |


## VIII. State Machine — approval_status Transitions

### VIII.1. Functional verification — State Transitions

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_070 | Verify valid transition: pending → approved (admin approval) | 1. Row has approval_status='pending'. | 1. Admin approves the key. | 1. approval_status transitions from pending to approved. approved_at is set. (Reference: FR-EXBOT-081 srs.) | P0 |
| TC_071 | Verify valid transition: approved → superseded (via rotation approval) | 1. Investor has an approved row and a new pending row. | 1. Admin approves the new pending row. | 1. The old approved row transitions to superseded atomically as the new row transitions to approved. (Reference: FR-EXBOT-083 srs AC.) | P0 |
| TC_072 | Verify valid transition: approved → revoked (admin explicit revocation) | 1. Row has approval_status='approved'. | 1. Admin explicitly revokes the key. | 1. approval_status transitions to revoked. revoked_at is set. (Reference: FR-EXBOT-082 srs.) | P0 |
| TC_073 | Verify valid transition: pending → rejected (blocked — OQ-EXBOT-016) | 1. Row has approval_status='pending'. | 1. Admin rejects the key. | 1. [TBD — pending BA answer: Issue I-03 / OQ-EXBOT-016. The pending → rejected transition is entirely undefined. Expected: row transitions to a new rejected status or is deleted per the chosen option — BA must confirm.] | P0 |
| TC_074 | Verify invalid transition: superseded → approved is blocked | 1. Row has approval_status='superseded' (old key after rotation). | 1. Attempt to approve the superseded row directly. | 1. The approval attempt is rejected. A superseded row cannot transition back to approved. The system does not allow re-activation of superseded keys. (Reference: FR-EXBOT-082 srs; FR-EXBOT-083 srs.) | P1 |
| TC_075 | Verify invalid transition: revoked → approved is blocked | 1. Row has approval_status='revoked'. | 1. Attempt to approve the revoked row directly. | 1. The approval attempt is rejected. A revoked row cannot transition to approved. A new submission is required. (Reference: FR-EXBOT-082 srs.) | P1 |

## IX. Non-Functional & Security (Logic-Accessible)

### IX.1. Functional verification — Non-Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_080 | Verify no raw key or DEK appears in any log across the full lifecycle (submission → approval → signing → revocation) | 1. A complete key lifecycle is executed: submission, admin approval, hedge-sync signing, revocation. | 1. Execute the full lifecycle and collect all worker log output. | 1. A full-text search of all log output for the raw key value and raw DEK value returns no matches. Logs may record operational events (key approved, key revoked, signing attempted) but must contain no cryptographic material. (Reference: FR-EXBOT-080 srs; NFR-EXBOT-006; AC-04.) | P0 |
| TC_081 | Verify audit trail is preserved: superseded and revoked rows not deleted | 1. Investor has gone through one rotation (key A → superseded, key B → approved) and key B was later revoked. | 1. Read all hl_agent_keys rows for the investor. | 1. All historical rows (A: superseded, B: revoked) remain in D1. No automated or admin-triggered cleanup removes old rows. The complete rotated_from chain is intact. (Reference: FR-EXBOT-082 srs; FR-EXBOT-083 srs; AC-07.) | P0 |

### IX.2. Integration & State verification — Non-Functional

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_082 | Verify concurrent approve attempts for the same pending key produce exactly one approved row | 1. One pending row exists.\n2. Two admin processes simultaneously attempt to approve the same row. | 1. Trigger two concurrent approval requests for the same pending key. | 1. Exactly one approval succeeds. The resulting state has exactly one approved row and the row is not double-approved or corrupted. The second concurrent attempt either succeeds (idempotent) or fails with an appropriate conflict error — the end state is exactly one approved row. (Reference: FR-EXBOT-082 srs — single approved invariant.) | P1 |
| TC_083 | Verify concurrent hedge-sync workers both correctly identify the single approved key | 1. Investor has exactly one approved key.\n2. Two hedge-sync workers execute simultaneously and both need to decrypt the agent key. | 1. Let both workers execute the decrypt step concurrently. | 1. Both workers fetch the same approved row and each performs its own local decrypt in function scope. Neither worker stores the decrypted key across requests. No concurrency issue causes one worker to see a stale or missing approved row. (Reference: FR-EXBOT-080 srs; FR-EXBOT-082 srs.) | P1 |

### IX.3. Non-functional (logic) verification — Security & Audit

| TC ID | Title | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_084 | Verify error messages during decryption failure do not expose key material | 1. Hedge-sync decryption fails (e.g., Secrets Store unavailable, key revoked mid-flight). | 1. Trigger a decryption failure and inspect the error response and log output. | 1. The error message (internal or API-level) describes the failure without including any raw key bytes, DEK bytes, IV values, or auth tag values. The error is useful for diagnosis (failure type, timestamp, botId) without leaking cryptographic material. (Reference: FR-EXBOT-080 srs; FR-EXBOT-082 srs; NFR-EXBOT-006.) | P0 |
| TC_085 | Verify the OPERATOR facade enforces the internal token for all agent-key calls | 1. A request is made to /api/exbot/agent-key without the required internal CF service binding token. | 1. Call the agent-key endpoint without a valid internal token. | 1. The request is rejected (HTTP 403). The ExBot Worker is not directly accessible without the OPERATOR facade's service binding token. (Reference: FR-EXBOT-090; BR-EXBOT-010.) | P0 |

