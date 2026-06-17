# UC Readiness Review — UC-EXBOT-agent-key
> Document Title: UC-EXBOT-agent-key Readiness Review v1
> Date Created: 2026-06-17 | Author/Agent: qc-uc-read (run-20260617-143500-udemysen) | Version: v1

---

## Feature Brief

UC-EXBOT-agent-key-approval covers the secure ingestion and governance of the HL agent key (delegated signing key). The investor submits the key via POOL UI → `POST /api/exbot/agent-key`. The ExBot Worker generates a per-row DEK (AES-256), encrypts the key (AES-256-GCM), wraps the DEK with the Master Key (Cloudflare Secrets Store), and stores only the encrypted blobs in `hl_agent_keys` (`encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`). Admin approves via dashboard, transitioning `approval_status` to `approved`. The system enforces: only ONE approved key per user (UNIQUE constraint); pending/revoked keys block preflight; expired keys block preflight with E-EXBOT-004. At hedge-sync time, decryption is function-scoped — plain DEK and plain key are never persisted or logged.

---

## Readiness Verdict

| Overall Score | Verdict |
|---|---|
| **71.5 / 100** | ⚠️ **CONDITIONALLY READY** |

**No hard blockers.** Key gaps: `revoked` vs `superseded` state naming conflict, proactive 7d expiry notification absent from UC, `users.hl_agent_key_id` update step missing from main flow, `POST /api/exbot/agent-key` schema undefined.

---

## 0. Document Metadata

| UC-ID | Feature Name | Version | Status |
|---|---|---|---|
| UC-EXBOT-agent-key | Submit + Encrypt + Approve HL Agent Key (AES-GCM envelope) | v1 | Draft |

> Note: UC title in file is `UC-EXBOT-agent-key-approval`; dashboard Folder ID is `UC-EXBOT-agent-key`. Dashboard ID used as canonical.

| Author / BA | Date Created | Last Updated |
|---|---|---|
| @hienduong (BA) | 2026-06-12 | 2026-06-17 |

---

## 1. Objective & Scope

### 1.1 Objective
Enable the ExBot system to execute HL trades on behalf of the investor without ever storing the investor's master private key. Only the approved HL agent key (a delegated signing key) is stored, using AES-256-GCM envelope encryption, with admin approval required before use.

### 1.2 In Scope
- Investor submitting agent key via POOL UI → `POST /api/exbot/agent-key`
- Per-row DEK generation + AES-256-GCM encryption + DEK wrap with Master Key
- `hl_agent_keys` INSERT with only encrypted blobs
- Admin approval flow: `approval_status` → `approved`
- Preflight checks: pending/revoked/expired key blocks bot start
- Key rotation: new row INSERT + old row → `superseded/revoked`
- Decryption at hedge-sync: function-scope only, immediate destruction
- Proactive expiry warning (7d before `expires_at`) via deep-audit (FR-EXBOT-083)

### 1.3 Out of Scope
- Master private key — system never stores or handles it
- HL API calls themselves (covered by `UC-EXBOT-hedge-sync`)
- Bot start preflight in full (covered by `UC-EXBOT-bot-start`)

---

## 2. Actors & Stakeholders

| Actor | Type | Role |
|---|---|---|
| USDC Investor | Primary | Generates and submits HL agent key via POOL UI |
| ExBot Admin | Primary | Approves pending key via admin dashboard |
| ExBot Worker | System | Handles encryption, storage, decryption |
| D1 control_db | System | Stores `hl_agent_keys` table |
| Cloudflare Secrets Store | System | Holds Master Key; wraps/unwraps DEK |
| OPERATOR Facade | System | Receives `POST /api/exbot/agent-key`; forwards to ExBot Worker |
| Notification Queue | System | Receives 7d expiry warning notification (FR-EXBOT-083) |

---

## 3. Preconditions & Postconditions

### 3.1 Preconditions
- Investor has generated an HL agent key (approved delegate, NOT master private key)
- ExBot Worker has access to Master Key in Cloudflare Secrets Store
- *(Inferred from FR-EXBOT-082)* No other approved key exists for this user — or if one exists, it must be transitioned to `superseded/revoked` atomically with new approval

### 3.2 Postconditions

| Outcome | System State |
|---|---|
| Happy path (submit) | `hl_agent_keys` row with `approval_status='pending'`; no plaintext persisted |
| Happy path (approve) | `approval_status='approved'`; `approved_at` set; investor can pass preflight |
| A1 (expired at preflight) | Bot start blocked; E-EXBOT-004; encrypted row retained |
| A2 (rotation) | New row `approved`; old row `superseded`; `rotated_from` chain preserved |
| A3 (hedge-sync decryption) | Plain key used and destroyed; nothing logged |

---

## 4. API / Queue / State Interface Inventory

> UC §2 = 2 preconditions only. Auto-cap applied: KA #5 max 8/15.

**API:**

| # | Endpoint | Notes |
|---|---|---|
| 1 | `POST /api/exbot/agent-key` | ⚠️ Request/response schema undefined in UC |
| 2 | Admin approval endpoint (implicit) | ⚠️ Endpoint name undefined — `PUT .../approve`? |

**Cloudflare Secrets Store:**

| # | Method | Notes |
|---|---|---|
| 3 | `MasterKey.wrap(DEK, dek_iv)` | DEK wrapping at submission |
| 4 | `MasterKey.unwrap(wrapped_dek)` | DEK unwrapping at hedge-sync decrypt |

**D1 (control_db):**

| # | Table | Operation | Notes |
|---|---|---|---|
| 5 | `hl_agent_keys` INSERT | Submission: encrypted blobs only; `approval_status='pending'` | |
| 6 | `hl_agent_keys` UPDATE | Approval: `approval_status='approved'`, `approved_at` | |
| 7 | `hl_agent_keys` UPDATE | Rotation: old → `superseded`; ⚠️ UC uses `revoked` not `superseded` |
| 8 | `hl_agent_keys` READ | At preflight: check `approval_status` + `expires_at` | |
| 9 | `users.hl_agent_key_id` UPDATE | After approval; ⚠️ timing not in main flow |

**Notification:**

| # | Trigger | Notes |
|---|---|---|
| 10 | 7d expiry warning | During deep-audit; ⚠️ entirely absent from UC scope |

---

## 5. System State Model

**`hl_agent_keys.approval_status`:**

| State | Trigger | Notes |
|---|---|---|
| `pending` | INSERT after submission | Default |
| `approved` | Admin approves | Preflight passes |
| `revoked` | Admin revokes (FR-EXBOT-082) OR rotation (UC A2) | Non-destructive; row retained for audit |
| `superseded` | Key rotation: replaced by newer approved key (FR-EXBOT-083) | ⚠️ UC A2 uses `revoked` for this case — conflict |

**Invariants (from spec):**

| Rule | Source |
|---|---|
| Only ONE `approved` row per user | FR-EXBOT-082 — DB UNIQUE constraint; ⚠️ not stated in UC |
| `DELETE` of rows forbidden | FR-EXBOT-082 |
| Plain DEK / plain key: function-scope only | FR-EXBOT-080 |

---

## 6. Functional Logic & Workflow Decomposition

### 6.1 Main Flow — Key Submission + Admin Approval (10 Steps)

| Step | Actor | Action | FR Ref | Gap |
|---|---|---|---|---|
| 1 | Investor | Submits agent key via POOL UI → `POST /api/exbot/agent-key` | FR-EXBOT-081 | ⚠️ Request schema undefined |
| 2 | OPERATOR | Forwards to ExBot Worker via CF service binding | FR-EXBOT-081 | |
| 3 | ExBot Worker | Generates per-row DEK (random AES-256) | FR-EXBOT-080 | ⚠️ DEK generation source unspecified |
| 4 | ExBot Worker | Encrypts: `AES-256-GCM(plainKey, DEK, IV)` → `encrypted_secret`, `secret_iv`, `secret_auth_tag` | FR-EXBOT-080 | ✅ Matches spec |
| 5 | ExBot Worker | Wraps DEK: `MasterKey.wrap(DEK, dek_iv)` → `wrapped_dek` | FR-EXBOT-080 | ⚠️ Error path if Secrets Store unavailable undefined |
| 6 | ExBot Worker | INSERTs `hl_agent_keys` row; plain DEK and plain key destroyed immediately | FR-EXBOT-080 | ✅ |
| 7 | ExBot Worker | Returns "Agent key received and encrypted. Awaiting approval." | FR-EXBOT-081 | |
| 8 | Admin | Views pending key in admin dashboard | FR-EXBOT-081 | ⚠️ Dashboard view content not specified |
| 9 | Admin | Approves → `approval_status='approved'`, `approved_at=now` | FR-EXBOT-081 | |
| 10 | System | Investor can now pass agent key preflight check | FR-EXBOT-081 | ⚠️ `users.hl_agent_key_id` update not in this step |

### 6.2 Alternate Flows

| ID | Trigger | Outcome |
|----|---------|---------|
| A1 (key expired) | Preflight: `expires_at < now` | Block start: "Agent key expired. Please submit a new one." Encrypted row retained. E-EXBOT-004 |
| A2 (key rotation) | Investor submits new key | New row inserted (new DEK + wrap); old → `status='revoked'` (⚠️ should be `superseded`?); `rotated_from` chain preserved |
| A3 (hedge-sync decryption) | Worker needs to sign HL order | Unwrap DEK → decrypt → use in function scope → destroy immediately; nothing logged |

---

## 7. Functional Integration Analysis

| Integration Point | Cross-Op Impact | Check |
|---|---|---|
| Envelope encryption at submission | Plain key NEVER leaves step 4 scope; DEK NEVER leaves step 5 scope | ✅ Explicitly enforced in UC steps 3–6 |
| UNIQUE constraint (`approved` per user) | New approval must atomically supersede old | ⚠️ Atomicity of supersede+approve not described in UC |
| Preflight check (UC-EXBOT-bot-start) | Blocked for `pending`/`revoked`/expired keys | AC-03 covers expired; pending/revoked coverage needs explicit test in bot-start UC |
| `revoked` key at hedge-sync | FR-EXBOT-082: decryption failure → SAFE_MODE | ⚠️ Absent from UC — critical security path untested |
| 7d expiry notification | Triggered during deep-audit (not covered in UC) | ⚠️ Tester unaware; notification test requires deep-audit trigger knowledge |
| Secrets Store unavailability | If `MasterKey.wrap` fails — no path defined | ⚠️ Submission error scenario untestable |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then |
|---|---|---|---|---|
| AC-01 | Happy submit | Investor provides valid HL agent key | `POST /api/exbot/agent-key` submitted | AES-256-GCM encrypted; DEK wrapped; only blobs in D1; `approval_status='pending'`; confirmation returned |
| AC-02 | Admin approval | `approval_status='pending'` for user | Admin approves via dashboard | `approval_status='approved'`; `approved_at` set; bot start preflight passes |
| AC-03 | Expired key blocks start | `expires_at` has passed | Preflight runs | Start blocked: "Agent key expired"; existing row retained; E-EXBOT-004 |
| AC-04 | Plain key never persisted | Worker decrypts key for hedge-sync signing | Signing completes | D1 dump has only blobs; no log contains raw key or raw DEK |
| AC-05 | D1 data integrity | Any point in time | D1 dump of `hl_agent_keys` | No plaintext key recoverable without Master Key; `hl_agent_keys` rows never deleted |
| AC-06 | UNIQUE approved-per-user | User already has approved key | Admin approves new key for same user | Old key transitions to `superseded/revoked`; only ONE approved row per user |
| AC-07 | Revoked key at hedge-sync | `hl_agent_keys.approval_status='revoked'` | Hedge-sync attempts decrypt | Decryption fails safely; enters SAFE_MODE; no key material in logs |

---

## 9. Non-functional Requirements

| Category | Requirement | Source |
|---|---|---|
| Security | AES-256-GCM envelope encryption; plain key/DEK function-scope + immediate destroy | FR-EXBOT-080 |
| Data integrity | `DELETE` of `hl_agent_keys` rows forbidden; non-destructive revocation | FR-EXBOT-082 |
| Uniqueness | Only ONE `approved` row per user at any time | FR-EXBOT-082 |
| Audit | `hl_agent_keys` row retained for revoked/superseded keys for audit purposes | FR-EXBOT-082 |
| Proactive expiry | 7d before `expires_at`: notification sent during deep-audit | FR-EXBOT-083 |
| ⚠️ Audit log retention | Retention period for `hl_agent_keys` audit rows not stated | — |
| ⚠️ DEK source | DEK randomness source and strength not specified in UC | FR-EXBOT-080 |

---

## 10. Open Questions & Dependencies

### 10.1 Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | uc-agent-key.md A2 vs spec FR-EXBOT-083 | UC A2 uses `status='revoked'` for rotation; spec FR-EXBOT-083 uses `status='superseded'` — are these two distinct states? When is each used? | Canonical state machine for rotation test cases | Open |
| Q2 | H | FR-EXBOT-082 | In-flight hedge-sync decrypting a `revoked` key → SAFE_MODE: triggered at status check (before decrypt) or decryption failure (after decrypt attempt)? | Security test case trigger mechanism | Open |
| Q3 | M | uc-agent-key.md §5 Postconditions | `users.hl_agent_key_id` update: after admin approval or after first preflight pass? | AC-02 step coverage | Open |
| Q4 | M | uc-agent-key.md §3 step 1 | `POST /api/exbot/agent-key` request schema — fields, required validation, max key length, format? | Input validation test coverage | Open |
| Q5 | M | FR-EXBOT-083 | Proactive 7d expiry warning: fired during which deep-audit event? Deep-audit run frequency? | Notification scheduling test | Open |
| Q6 | M | uc-agent-key.md §3 step 5 | Cloudflare Secrets Store unavailability: what is the error path if `MasterKey.wrap` fails? | Submission failure test coverage | Open |
| Q7 | L | FR-EXBOT-082 | UNIQUE on `(user_id, approval_status='approved')` enforced at DB level or application level? | Race condition and DB schema tests | Open |
| Q8 | L | uc-agent-key.md §3 step 9 | Admin approval endpoint — `PUT /api/exbot/agent-key/{id}/approve` or another path? | Admin AC test requires concrete endpoint | Open |

### 10.2 Dependencies

| Dependency | Notes |
|---|---|
| UC-EXBOT-bot-start | Agent key preflight check is part of bot-start preflight (already audited Conditionally Ready 70.8/100) |
| UC-EXBOT-hedge-sync | Decryption at hedge-sync is A3 in this UC |
| Cloudflare Secrets Store | Master Key availability required for all submission and decryption operations |

---

## 11. Change Log

| Version | Date | Author | Summary |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read (run-20260617-143500-udemysen) | Initial first-audit |

---

## Audit Summary

### Score Breakdown

| # | Knowledge Area | Max | Score | Status |
|---|---|---|---|---|
| 1 | Feature Identity | 5 | 5 | ✅ |
| 2 | Objective & Scope | 5 | 4 | ✅ |
| 3 | Actors & User Roles | 10 | 9 | ✅ |
| 4 | Preconditions & Postconditions | 10 | 7 | ⚠️ |
| 5 | API/Queue/State Interface | 15 | 8 | ⚠️ AUTO-CAP |
| 6 | System State Model | 20 | 14 | ✅ |
| 7 | Functional Logic | 20 | 14 | ✅ |
| 8 | Integration Analysis | 20 | 13 | ✅ |
| 9 | Acceptance Criteria | 20 | 15 | ✅ |
| 10 | NFRs | 5 | 4 | ✅ |
| **TOTAL** | | **130** | **93** | |

**Raw: 93/130 → Final: 71.5/100 → ⚠️ CONDITIONALLY READY**

### Blockers
None. No critical KA = 0. No blocking unresolved NV applies.

### Strengths
- AES-256-GCM envelope encryption fully described with all 5 stored fields
- Function-scope plaintext destruction explicitly stated in UC main flow AND alt flows
- 4 well-formed Gherkin ACs cover happy path, approval, expired, log-safety
- Non-destructive revocation + `DELETE` forbidden both stated

### Recommendation
Test design may begin for the core encryption/approval flow. Resolve W1 (revoked vs superseded), W2 (proactive 7d notification), and W7 (revoked key → SAFE_MODE path) before writing security test cases and edge case state machine tests.

### 📋 Unified Gap & Question Report

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | H | uc-agent-key.md A2 vs spec FR-EXBOT-083 | UC A2 uses `status='revoked'` for rotation; spec uses `status='superseded'` — are these distinct states? When is each applied? | Canonical state machine for rotation test cases | Open |
| Q2 | H | FR-EXBOT-082 | In-flight hedge-sync on `revoked` key → SAFE_MODE: triggered at status check or decryption failure? | Security test case trigger mechanism | Open |
| Q3 | M | uc-agent-key.md §5 Postconditions | `users.hl_agent_key_id` update: after admin approval or first preflight pass? | AC-02 step coverage | Open |
| Q4 | M | uc-agent-key.md §3 step 1 | `POST /api/exbot/agent-key` request schema — fields, validation, max key length? | Input validation test coverage | Open |
| Q5 | M | FR-EXBOT-083 | Proactive 7d expiry warning: which deep-audit event? Deep-audit run frequency? | Notification scheduling test | Open |
| Q6 | M | uc-agent-key.md §3 step 5 | Cloudflare Secrets Store unavailability: error path if `MasterKey.wrap` fails? | Submission failure test coverage | Open |
| Q7 | L | FR-EXBOT-082 | UNIQUE on `(user_id, approval_status='approved')` at DB level or application level? | Race condition and schema tests | Open |
| Q8 | L | uc-agent-key.md §3 step 9 | Admin approval endpoint name? | Admin AC test requires concrete endpoint | Open |
