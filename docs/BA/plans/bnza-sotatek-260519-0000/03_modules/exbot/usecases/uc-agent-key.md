---
type: use-case
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-12
owner: "@hienduong"
linked_stories: [US-EXBOT-011]
changelog:
  - 2026-06-12 | /ba-start srs | initial draft
---

# UC-EXBOT-agent-key-approval: Submit and Approve HL Agent Key

## 1. Actors
- **Primary:** USDC Investor (key submission), ExBot Admin (key approval)
- **System:** ExBot Worker, D1 (control_db: hl_agent_keys), Cloudflare Secrets Store

## 2. Preconditions
- Investor has generated an HL agent key (approved delegate, not master private key)
- ExBot Worker has access to Master Key in Cloudflare Secrets Store

## 3. Main Success Scenario — Key Submission
1. Investor submits agent key via POOL UI → `POST /api/exbot/agent-key`
2. OPERATOR forwards to ExBot Worker via service binding
3. ExBot Worker generates a per-row DEK (random, AES-256)
4. Encrypts agent key: `encrypted_secret = AES-256-GCM(plainKey, DEK, IV)` → stores `encrypted_secret`, `secret_iv`, `secret_auth_tag`
5. Wraps DEK with Master Key (Cloudflare Secrets Store): `wrapped_dek = MasterKey.wrap(DEK, dek_iv)`
6. Inserts row into `hl_agent_keys`: only encrypted blobs stored; plain DEK and plain key destroyed immediately
7. Returns confirmation: "Agent key received and encrypted. Awaiting approval."

**Admin Approval Flow:**
8. Admin sees pending key in admin dashboard
9. Admin approves → ExBot Worker updates `approval_status='approved'`, `approved_at=now`
10. Investor can now pass agent key preflight check when starting ExBot

## 4. Alternate Flows
- **A1 (key expired):** At preflight time — `expires_at < now` → block start: "Agent key expired. Please submit a new one."
- **A2 (key rotation):** New row inserted (new DEK + new wrap); old row set to `status='revoked'`, `rotated_from` chain preserved
- **A3 (decryption during hedge-sync):** Unwrap `wrapped_dek` with Master Key → decrypt `encrypted_secret` → use plain key in function scope → destroy immediately; nothing logged

## 5. Postconditions
- `hl_agent_keys.approval_status='approved'`
- No plain key or plain DEK persisted anywhere
- `users.hl_agent_key_id` references the approved key row

## 6. Business Rules
- BR-EXBOT (FR-EXBOT-080, 081, 082, 083)

## 7. FR Trace
FR-EXBOT-080, FR-EXBOT-081, FR-EXBOT-082, FR-EXBOT-083
