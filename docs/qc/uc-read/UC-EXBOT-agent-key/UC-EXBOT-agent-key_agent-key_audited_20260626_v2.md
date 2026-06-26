---
title: UC Readiness Review — UC-EXBOT-agent-key (Submit and Approve HL Agent Key)
date: 2026-06-26
author: qc-uc-read-exbot agent (Trinh.Bui)
version: v2
uc_id: UC-EXBOT-agent-key
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-agent-key.md
---

# UC Readiness Review — UC-EXBOT-agent-key

## Feature Brief

UC-EXBOT-agent-key describes the process by which a USDC Investor submits a Hyperliquid (HL) agent key — a delegated signing key, never the master private key — for secure encrypted storage, and an ExBot Admin approves it before the key can be used to authorize HL trades on the investor's behalf.

The system never stores the plaintext key. Instead, the key is encrypted at rest using AES-256-GCM envelope encryption: the key is encrypted with a per-row DEK (Data Encryption Key), and the DEK is wrapped using the Master Key stored in Cloudflare Secrets Store. Only encrypted blobs (`encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`) are persisted in D1. At hedge-sync time, the worker unwraps the DEK, decrypts the key in function scope, uses it to sign the HL order, then destroys both the plain DEK and plain key immediately.

Key approval is a prerequisite for starting an ExBot (FR-EXBOT-002 preflight check 3). The UC also covers key rotation (new row inserted, old row becomes `superseded`), explicit revocation (old row becomes `revoked`), and expiry handling. A critical path — what happens when Admin rejects a pending key — remains blocked on OQ-EXBOT-016 (pending BA + zen scope decision) and is the primary reason this UC is Not Ready.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-agent-key | Submit and Approve HL Agent Key | updated 2026-06-20 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-20 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-agent-key.md` | 2026-06-20 | UC | Primary review target |
| `userstories/us-011.md` | 2026-06-12 | US | Linked story |
| `srs/spec.md` | 2026-06-20 | SRS | Canonical source — FR-EXBOT-080..083 |
| `srs/erd.md` | 2026-06-12 | ERD | `hl_agent_keys` schema |
| `srs/states.md` | 2026-06-18 | State diagram | No `hl_agent_keys` state machine |
| `frd.md` | 2026-06-24 | FRD | FR-EXBOT-081, FR-EXBOT-100 (actor conflict) |
| `02_backbone/common-rules.md` | 2026-06-17 | Common rule | No ExBot section — BR-EXBOT-* absent |
| `02_backbone/message-list.md` | 2026-06-09 | Message list | No ExBot section — E-EXBOT-* absent |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

The UC exists to satisfy the security requirement that HL trades be signed by a delegated agent key rather than the user's master private key. It enables: (1) secure submission and storage of the agent key, (2) admin-gated approval before the key can be used, (3) key rotation and revocation lifecycle management, (4) expiry notification and preflight enforcement. Without an approved, non-expired agent key, an investor cannot start an ExBot (FR-EXBOT-002).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Agent key submission | Investor submits key via POOL UI → `POST /api/exbot/agent-key` → AES-256-GCM envelope encryption → D1 insert with `approval_status='pending'` | UC §3; FR-EXBOT-080 srs |
| DEK + Master Key wrap | Per-row DEK generated, key encrypted, DEK wrapped with Cloudflare Secrets Store Master Key | UC §3 steps 3-6; FR-EXBOT-080 srs |
| Admin approval | Admin approves pending key in admin dashboard → `approval_status='approved'`, `approved_at=now` | UC §3 steps 8-10; FR-EXBOT-081 srs |
| Preflight enforcement | `approval_status IN ('pending','revoked')` or `expires_at < now` blocks bot start | UC §4 A1; FR-EXBOT-081/083 srs |
| Key rotation | New key submitted → new row + new DEK; old approved row → `superseded` (atomic D1 transaction) | UC §4 A2; FR-EXBOT-083 srs AC |
| Key revocation | Admin explicit revocation → `approval_status='revoked'`, `revoked_at=now`; hedge-sync → SAFE_MODE | UC §4 A2 note; FR-EXBOT-082 srs |
| Decrypt at hedge-sync | Unwrap DEK → decrypt key in function scope → sign HL order → destroy immediately | UC §4 A3; FR-EXBOT-080 srs |
| Expiry notification | Deep-audit cron: `expires_at - now ≤ 7d` → enqueue notification | UC §4 A5 (OOS, cross-ref deep-audit); FR-EXBOT-083 srs |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Admin reject path | OQ-EXBOT-016 pending BA+zen scope decision (options A/B/C) | Cannot test admin reject flow; A4 missing from UC |
| Expiry notification (detail) | Owned by UC-EXBOT-deep-audit; UC §4 A5 marks it OOS | Test for expiry notification should be in deep-audit UC |
| Master key protection logic | No format validation defined for agent key vs master key | Cannot test "submit master key is rejected" |
| Cloudflare Secrets Store failure handling | Not defined in UC or SRS | Cannot test DEK wrap/unwrap failure path |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Submits agent key via POOL UI → `POST /api/exbot/agent-key` | Can submit and rotate own key; cannot approve own key | UC §1 Actors; FR-EXBOT-081 srs |
| ExBot Admin (zen) | Primary | Approves/rejects pending key via admin dashboard | Can approve, reject (path undefined), revoke keys | UC §1 Actors; FR-EXBOT-082 srs |
| ExBot Worker | System | Encrypts key on submission; decrypts at hedge-sync time | Function-scope only access to plain key; no logging | UC §1 Actors; FR-EXBOT-080 srs |
| Cloudflare Secrets Store | External | Holds Master Key used to wrap/unwrap DEK | Not accessible to investor; failure behavior undefined | UC §3 steps 4-5; FR-EXBOT-080 srs |
| D1 (control_db: hl_agent_keys) | System | Persistent storage for encrypted blobs and approval state | Only encrypted blobs stored; plain key never reaches D1 | UC §1 Actors; FR-EXBOT-080 srs |

**Nhận xét readiness:** Actor split between investor (POST) and admin (GET/approve) is clearly defined in UC but conflicts with `frd.md` FR-EXBOT-100, which lists "Admin" as the actor for all `/api/exbot/agent-key` methods including POST. This actor conflict (Issue I-01) creates test design risk for access control tests.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Investor has generated an HL agent key (approved delegate key, not master private key) | Yes | UC §2 |
| 2 | ExBot Worker has access to Master Key in Cloudflare Secrets Store | Yes | UC §2 |
| 3 | For admin approval: a `pending` row exists in `hl_agent_keys` for the target user | Yes | UC §3 step 8; FR-EXBOT-081 srs |
| 4 | For decrypt at hedge-sync: `hl_agent_keys.approval_status='approved'` and `expires_at > now` | Yes | UC §4 A3; FR-EXBOT-082 srs |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Submission | New row in `hl_agent_keys` with `approval_status='pending'`; only encrypted blobs stored; plain key and DEK destroyed | UC §3 steps 6-7; FR-EXBOT-080 srs |
| Admin approval | `hl_agent_keys.approval_status='approved'`, `approved_at=now`; investor can pass bot-start preflight | UC §3 steps 9-10; FR-EXBOT-081 srs |
| Rotation (new key approved) | New row `approved`; old row `superseded` — set atomically in same D1 transaction | UC §4 A2; FR-EXBOT-083 srs AC |
| Explicit revocation | Row `approval_status='revoked'`, `revoked_at=now`; row retained in D1 (DELETE forbidden); hedge-sync → SAFE_MODE if key used mid-flight | FR-EXBOT-082 srs |
| Decrypt (hedge-sync) | Plain DEK and plain key are function-scoped; destroyed after signing; no log entry with raw values | UC §4 A3; FR-EXBOT-080 srs |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Agent Key Submission (NĐT nộp key)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Investor | Submits HL agent key via POOL UI → `POST /api/exbot/agent-key` | OPERATOR forwards to ExBot Worker via CF service binding | — | — | UC §3 step 1 |
| 2 | ExBot Worker | Generates per-row DEK (random AES-256) | DEK generated in memory only | — | Secrets Store unavailable → behavior undefined (Issue I-08) | UC §3 step 3 |
| 3 | ExBot Worker | Encrypts agent key: `encrypted_secret = AES-256-GCM(plainKey, DEK, IV)` | Stores `encrypted_secret`, `secret_iv`, `secret_auth_tag` | — | — | UC §3 step 4; FR-EXBOT-080 srs |
| 4 | ExBot Worker | Wraps DEK: `wrapped_dek = MasterKey.wrap(DEK, dek_iv)` via Cloudflare Secrets Store | Stores `wrapped_dek`, `dek_iv` | — | Secrets Store unavailable → behavior undefined (Issue I-08) | UC §3 step 5; FR-EXBOT-080 srs |
| 5 | ExBot Worker | INSERTs row into `hl_agent_keys` with `approval_status='pending'`; plain DEK and plain key destroyed immediately | Row created; no plaintext stored anywhere | — | — | UC §3 step 6; FR-EXBOT-080 srs |
| 6 | ExBot Worker | Returns HTTP response to POOL UI | "Agent key received and encrypted. Awaiting approval." | — | — | UC §3 step 7 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `hl_agent_keys.approval_status` initial | Must be `pending` on INSERT | Yes | Row created with `pending` | — | FR-EXBOT-081 srs |
| Plain key / plain DEK | Must be function-scope only; never persisted or logged | Yes | Destroyed after use | Security violation if logged | FR-EXBOT-080 srs; NFR-EXBOT-006 |
| Master key | Never stored in D1 | Yes | Stored only in Cloudflare Secrets Store | Security violation | FR-EXBOT-080 srs |
| Agent key format | Not defined in any document | TBD | — | Cannot reject master key by format (Issue I-05) | NOT_FOUND |
| `expires_at` owner | Not defined — who sets it: investor or system? | TBD | — | Cannot test boundary (Issue I-04) | NOT_FOUND |
| Double-pending | Behavior when investor submits while row already `pending` | TBD | — | Cannot test (Issue I-10) | NOT_FOUND |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Submission success | API response | "Agent key received and encrypted. Awaiting approval." | — | UC §3 step 7 |
| Bot start: key pending | API error response | "Agent key is awaiting approval. Please complete the approval process before starting." (HTTP 400) | E-EXBOT-003 | srs/spec.md §5 |
| Bot start: key expired | API error response | "Your HL agent key has expired. Please submit a new one." (HTTP 400) | E-EXBOT-004 | srs/spec.md §5 |
| E-EXBOT-001..013 | N/A | E-EXBOT-* codes defined in srs/spec.md §5 but NOT registered in message-list.md | — | Issue I-09 |

---

### 6.2 Admin Approval Flow

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Admin | Views pending key in admin dashboard | `hl_agent_keys` row with `approval_status='pending'` shown | — | — | UC §3 step 8 |
| 2 | ExBot Admin | Approves key | ExBot Worker updates `approval_status='approved'`, `approved_at=now` | A4: Admin rejects → **path undefined** (OQ-EXBOT-016 — Blocker Issue I-03) | — | UC §3 step 9; FR-EXBOT-081 srs |
| 3 | System | Investor can now pass bot-start preflight agent key check | Bot start unblocked | — | — | UC §3 step 10 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Only 1 approved key per user | DB-enforced UNIQUE constraint | Yes | New `approved` row allowed only after old row `superseded`/`revoked` | DB rejects second `approved` row | FR-EXBOT-082 srs |
| `approved_by` field | Not present in ERD `hl_agent_keys` | TBD | — | Audit trail test cannot verify who approved (Issue I-07) | NOT_FOUND in erd.md |
| `revoked_at` field | FR-EXBOT-082 srs references `revoked_at=now` but field absent in ERD | TBD | — | ERD-SRS inconsistency | Issue I-07 |
| SLA `pending → approved` | Not defined | TBD | — | Cannot write SLA test | NOT_FOUND |
| Admin reject path | Not defined in UC or SRS; OQ-EXBOT-016 pending | TBD — Blocker | — | Entire reject flow untestable | Issue I-03 |

---

### 6.3 Key Rotation (A2)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống | Luồng thay thế | Nguồn |
|---|---|---|---|---|---|
| 1 | Investor | Submits new agent key (existing approved row present) | New row inserted with `approval_status='pending'`, new DEK + wrap | — | UC §4 A2 |
| 2 | ExBot Admin | Approves new key | New row → `approved`; old row → `superseded`; set atomically in same D1 transaction | — | UC §4 A2; FR-EXBOT-083 srs AC |
| 3 | System | Window between submission and approval | Existing approved key remains active (unless expired) | — | FR-EXBOT-083 srs AC |

**Key rule:** `superseded` = old row when rotation; `revoked` = explicit admin action only. (Source: FR-EXBOT-083 srs; BA response 2026-06-20)

---

### 6.4 Key Decrypt at Hedge-Sync (A3)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống | Nguồn |
|---|---|---|---|---|
| 1 | ExBot Worker | Hedge-sync requires HL signing | Worker fetches `hl_agent_keys` row with `approval_status='approved'` | UC §4 A3 |
| 2 | ExBot Worker | Unwraps DEK: `MasterKey.unwrap(wrapped_dek, dek_iv)` | Plain DEK in function scope | FR-EXBOT-080 srs |
| 3 | ExBot Worker | Decrypts agent key: `AES-256-GCM.decrypt(encrypted_secret, DEK, secret_iv, secret_auth_tag)` | Plain agent key in function scope | FR-EXBOT-080 srs |
| 4 | ExBot Worker | Signs HL order using plain key | HL order signed and submitted | UC §4 A3 |
| 5 | ExBot Worker | Destroys plain DEK and plain key immediately after signing | Nothing persisted; no log entry with raw values | FR-EXBOT-080 srs; NFR-EXBOT-006 |
| — | System | Key is `revoked` mid-flight during step 2-4 | Decryption failure → SAFE_MODE (FR-EXBOT-082 srs) | FR-EXBOT-082 srs |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Key `approved` | UC-EXBOT-bot-start (preflight check 3) | Bot start unblocked for investor | `hl_agent_keys.approval_status='approved'` AND `expires_at > now` | FR-EXBOT-002 srs; UC §3 step 10 |
| Key `revoked` mid hedge-sync | UC-EXBOT-hedge-sync | Worker decryption failure → SAFE_MODE | `hl_agent_keys.approval_status='revoked'` detected at decrypt time | FR-EXBOT-082 srs |
| Key `expires_at ≤ now + 7d` | UC-EXBOT-deep-audit (cron) | Expiry notification enqueued to investor | `hl_agent_keys.expires_at` checked per deep-audit cycle | FR-EXBOT-083 srs; UC §4 A5 |
| Key `expires_at < now` | UC-EXBOT-bot-start (preflight) | Bot start blocked with E-EXBOT-004 | `expires_at` evaluated at preflight time | FR-EXBOT-083 srs; E-EXBOT-004 |
| Rotation approved | UC-EXBOT-hedge-sync (in-flight window) | Old key remains active until new key approved; no interrupt | `hl_agent_keys`: exactly 1 `approved` row per user at all times | FR-EXBOT-083 srs AC |
| New key submission | D1 `hl_agent_keys` | New `pending` row inserted; existing `approved` row untouched until admin approves replacement | No two `approved` rows for same user simultaneously | FR-EXBOT-082 srs; FR-EXBOT-083 srs |
| Rotation approved | D1 `hl_agent_keys` | New `approved` row inserted; old `approved` → `superseded` atomically | `rotated_from` FK chain preserved in new row | FR-EXBOT-083 srs AC |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — key submitted and stored securely | Investor provides HL agent key via POOL UI | Investor calls `POST /api/exbot/agent-key` | System stores only encrypted blobs; `approval_status='pending'`; returns confirmation message | US-011 AC-1; UC §3 |
| AC-02 | Happy path — key approved, bot start unlocked | `hl_agent_keys.approval_status='pending'` for user | Admin approves via dashboard | `approval_status='approved'`, `approved_at` recorded; investor passes preflight check 3 | US-011 AC-2; UC §3 steps 9-10 |
| AC-03 | Expired key blocks bot start | `hl_agent_keys.expires_at < now` | Preflight runs for new bot start | Start blocked with E-EXBOT-004: "Your HL agent key has expired. Please submit a new one."; existing row NOT deleted | US-011 AC-3; FR-EXBOT-083 srs |
| AC-04 | Plain key never in logs or DB | Worker decrypts agent key to sign HL order | Signing operation completes | Plain DEK and plain key destroyed (function-scope); no log entry with raw values; D1 row still contains only encrypted blobs | US-011 AC-4; FR-EXBOT-080 srs |
| AC-05 | Rotation atomicity | User has `approved` key; submits new key; admin approves | Admin approves new key row | Old row → `superseded` AND new row → `approved` in same D1 transaction; no window with 0 or 2 approved keys | FR-EXBOT-083 srs AC — Suy luận cần xác nhận |
| AC-06 | Revoked key mid hedge-sync → SAFE_MODE | Approved key exists; hedge-sync in progress | Admin revokes key during signing step | Worker receives decryption failure; bot enters SAFE_MODE; no raw key material in logs | FR-EXBOT-082 srs — Suy luận cần xác nhận |
| AC-07 | DELETE of revoked row forbidden | `approval_status='revoked'` row exists | Any actor attempts DELETE | Database rejects DELETE; row retained for audit | FR-EXBOT-082 srs — Suy luận cần xác nhận |
| AC-08 | Admin reject path | Admin rejects a `pending` key | Admin rejects via dashboard | ??? — blocked on OQ-EXBOT-016 | NOT TESTABLE until OQ-EXBOT-016 resolved |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Security | Master private key never stored; only agent key (approved delegate) with AES-256-GCM envelope encryption | Test: D1 dump contains only encrypted blobs; no plaintext key recoverable without Master Key | NFR-EXBOT-006; FR-EXBOT-080 srs |
| Security | Plain DEK and plain key are function-scoped only; destroyed immediately after use | Test: Log audit shows no raw key/DEK values after any operation | FR-EXBOT-080 srs |
| Security | Only 1 `approved` key per user at any time — DB-enforced | Test: Attempt to approve second key without revoking/superseding first → DB rejects | FR-EXBOT-082 srs |
| Reliability | Cloudflare Secrets Store unavailability handling: undefined in UC and SRS | Cannot design failure test — gap (Issue I-08) | NOT_FOUND |
| Audit / Logging | No log entry may contain raw key or raw DEK | Test: Search log output for plaintext key pattern after submission and hedge-sync signing | FR-EXBOT-080 srs |
| Idempotency | Double-submit behavior when `pending` row already exists: undefined | Cannot test double-submit scenario (Issue I-10) | NOT_FOUND |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 | High | CROSS_SOURCE_CONFLICT | `frd.md` FR-EXBOT-100; UC §1 Actors, §3 step 1 | `frd.md` FR-EXBOT-100 liệt kê "Admin" là actor cho cả POST và GET `/api/exbot/agent-key`. UC định nghĩa POST do NĐT thực hiện (nộp key), Admin chỉ gọi GET (xem dashboard) và approve. Hai nguồn mâu thuẫn về actor của POST. BA cần cập nhật `frd.md` FR-EXBOT-100 để phân rõ: POST = NĐT, GET/approve = Admin; hoặc giải thích lý do thiết kế khác UC. | Test case kiểm soát truy cập sẽ fail nếu dùng nhầm actor. | BA | Open |
| I-02 | Low | INTERNAL_INCONSISTENCY | `uc-agent-key.md` header; UC body title; UC §Trigger | UC title trong body là "UC-EXBOT-agent-key-approval" nhưng file name và index dùng "UC-EXBOT-agent-key". UC §Trigger vẫn là placeholder "User navigates to the relevant screen..." — không mô tả trigger thực tế (investor submits key via POOL UI). BA cần thống nhất tên UC và cập nhật Trigger. | Gây nhầm lẫn khi trace; tester không biết trigger thực tế. | BA | Open |
| I-03 | High | MISSING_INFO | UC §4; OQ-EXBOT-016; `srs/spec.md` §9 | UC không có A4 cho admin reject path. OQ-EXBOT-016 đã tạo với 3 options (A/B/C) nhưng chưa được chốt. Khi admin reject một key `pending`: trạng thái row là gì (`rejected`? bị xóa?), message gửi NĐT là gì, NĐT có thể resubmit không? | Toàn bộ admin-reject flow không thể test được cho đến khi OQ-EXBOT-016 được chốt. **Blocker.** | BA + zen | Open |
| I-04 | High | MISSING_INFO | `srs/spec.md` FR-EXBOT-083; `srs/erd.md` `expires_at TEXT`; UC §3 step 1 | Không tài liệu nào định nghĩa: (a) ai set `expires_at` — NĐT gửi hay hệ thống tự tính? (b) thời hạn tối đa/mặc định; (c) có validate khi submit không (ví dụ: từ chối `expires_at` trong quá khứ). | Tester không biết expected value của `expires_at` khi submit; không thể viết test case boundary. | BA | Open |
| I-05 | High | MISSING_INFO | FR-EXBOT-080 srs; UC §2 Preconditions | Không có validation rule nào phân biệt agent key với master key để từ chối trường hợp NĐT vô tình nộp master private key. Format/length/prefix hợp lệ của agent key không được định nghĩa ở bất kỳ đâu. | Test case negative "nộp master key bị reject" không viết được vì không có expected validation behavior. | BA | Open |
| I-06 | High | MISSING_INFO | UC §3 step 1; `frd.md` FR-EXBOT-100 | Không có tài liệu nào định nghĩa request schema của `POST /api/exbot/agent-key` (field names, types, required/optional) và response schema (body, HTTP status codes cho từng trường hợp). | Không thể thiết kế test case submit hợp lệ, negative validation, hoặc verify error response format. | BA / Dev | Open |
| I-07 | High | MISSING_INFO | `srs/erd.md` `hl_agent_keys`; FR-EXBOT-082 srs | ERD thiếu trường `approved_by` — không có cách audit ai đã approve key. FR-EXBOT-082 srs đề cập `revoked_at=now` nhưng trường `revoked_at` không có trong ERD. Không có SLA được định nghĩa cho `pending → approved`. | Audit trail test không viết được; SLA test không có baseline; ERD-SRS inconsistency. | BA | Open |
| I-08 | High | MISSING_INFO | FR-EXBOT-080 srs; UC §3 steps 4-5; UC §4 A3 | Không tài liệu nào định nghĩa behavior khi Cloudflare Secrets Store không available: (a) lúc wrap DEK khi submit, (b) lúc unwrap DEK khi hedge-sync. | Test case "Secrets Store down" không viết được. | BA | Open |
| I-09 | High | MISSING_INFO | UC §6 BR; `02_backbone/common-rules.md`; `02_backbone/message-list.md` | UC §6 tham chiếu "BR-EXBOT (FR-EXBOT-080, 081, 082, 083)" nhưng BR-EXBOT-* không tồn tại trong `common-rules.md`. E-EXBOT-001..013 được định nghĩa trong `srs/spec.md §5` nhưng không đăng ký trong `message-list.md`. | Test case cần nguồn master để trace BR và E-code; không có nguồn chính thức để compare. | BA | Open |
| I-10 | Medium | MISSING_INFO | UC §4; UC §3 | Không định nghĩa behavior khi NĐT submit key mới trong khi đã có row `pending` (bị reject? overwrite? INSERT thêm row?). | Test case "submit khi pending đã tồn tại" không có expected result. | BA | Open |
| I-11 | Medium | MISSING_INFO | UC (thiếu); `frd.md` FR-EXBOT-100 | POST `/api/exbot/agent-key` không có rate limit được định nghĩa. | Test case rate limit không viết được nếu policy không được xác định. | BA | Open |
| I-12 | Medium | MISSING_INFO | UC §3 step 9; FR-EXBOT-083 srs | Nếu Admin xử lý chậm và key `expires_at` đã qua trước khi approve: hệ thống có validate `expires_at` tại thời điểm admin approve không? Hay approve vẫn được nhưng key sẽ fail preflight ngay? | Test case edge case này không có expected result. | BA | Open |
| I-13 | Medium | MISSING_INFO | `srs/spec.md §5`; UC §6 | UC không liệt kê đầy đủ E-code liên quan đến luồng agent-key. Chỉ E-EXBOT-003 và E-EXBOT-004 được đề cập implicitly; E-EXBOT-001..013 không có trong UC. | Coverage error cases bị bỏ sót; tester không biết expected error codes cho từng failure path. | BA | Open |
| I-14 | Low | MISSING_INFO | `us-011.md` FR Trace; `srs/spec.md §1.2` | US-011 FR Trace tham chiếu FM-XB-12 (Envelope Encryption) nhưng FM-XB-12 không tồn tại trong SRS §1.2 Feature Map (FM-XB-01..08 only). | FM-XB-12 là dangling reference; không thể trace feature map coverage cho encryption. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-016: Admin reject path (options A/B/C) | UC / Common rule | Blocks UC A4; blocks AC-08; blocks test design cho admin reject flow | BA + zen | Open |
| `common-rules.md` ExBot section | Common rule | BR-EXBOT-* cần được đăng ký để có nguồn trace chính thức | BA | Open |
| `message-list.md` ExBot section | Common rule | E-EXBOT-001..013 cần được đăng ký để test case có nguồn compare | BA | Open |
| API contract `/api/exbot/agent-key` | API | Request/response schema cần được publish trước khi thiết kế test case API | BA / Dev | Open |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v2 | 2026-06-26 | qc-uc-read-exbot agent (Trinh.Bui) | Re-audit sau khi BA cập nhật UC (2026-06-20): A5 OOS added, A2 superseded/revoked split, FR trace note. So sánh với SRS spec.md 2026-06-20. Issues I-01..I-14 được cập nhật theo trạng thái hiện tại. Score: 57/100 Not Ready. |
| v1 | 2026-06-18 | qc-uc-read-exbot agent (Trinh.Bui) | Tạo báo cáo audited lần đầu. Score: 61/100 Not Ready. |

---

## 10.3 Audit Summary

### Scoring

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 15 | ⚠️ Partial | Inventory đầy đủ hơn v1 (A5, A2 rotation, A3 decrypt). Còn thiếu `revoked_at` trong ERD; `approved_by` absent; `expires_at` owner undefined. |
| 2 | Data Object / State Attributes, BR, Validations & Messages | 25 | 14 | ⚠️ Partial | BR-EXBOT-* không resolve từ common-rules.md; E-EXBOT-* không trong message-list.md; Secrets Store failure undefined; `expires_at` validation undefined. |
| 3 | Functional Logic & Workflow Decomposition | 25 | 10 | ❌ Weak | A4 admin reject path = Blocker (OQ-EXBOT-016). Agent key format validation undefined. Blocker cap 40% applied → max 10/25. |
| 4 | Functional Integration & Data Consistency | 15 | 10 | ⚠️ Partial | Rotation atomicity documented; window behavior documented; hedge-sync decrypt path present. Double-pending và rate limit missing. |
| 5 | UC / Spec Documentation Quality | 15 | 8 | ⚠️ Partial | Trigger placeholder; title mismatch; frd.md actor conflict (CROSS_SOURCE_CONFLICT); FM-XB-12 dangling reference. |
| **Total** | | **100** | **57** | | |

**Verdict: Not Ready**

Auto-fail triggered: Blocker I-03 (admin reject path — A4 missing, OQ-EXBOT-016 unresolved) prevents reliable test design for a required flow. Area 3 capped at 40% per rubric.

### Blockers (1)

| ID | Finding |
|---|---|
| I-03 | Admin reject path hoàn toàn undefined. OQ-EXBOT-016 chưa được chốt. Không thể test flow admin từ chối key `pending`. |

### Major issues (7)

| ID | Finding |
|---|---|
| I-01 | `frd.md` FR-EXBOT-100 gán Admin là actor của POST — mâu thuẫn với UC (NĐT gọi POST). |
| I-04 | `expires_at` owner và validation rules không được định nghĩa. |
| I-05 | Agent key format/length/prefix không được định nghĩa; không thể phân biệt agent key với master key. |
| I-06 | API contract `/api/exbot/agent-key` (request/response schema) chưa được publish. |
| I-07 | `approved_by` và `revoked_at` vắng mặt trong ERD; không có SLA `pending → approved`. |
| I-08 | Cloudflare Secrets Store unavailability handling không được định nghĩa. |
| I-09 | BR-EXBOT-* không có trong `common-rules.md`; E-EXBOT-* không có trong `message-list.md`. |

### Recommendation

UC-EXBOT-agent-key đã được cải thiện đáng kể so với v1 (BA đã fix rotation enum conflict, thêm A5, bổ sung FR trace note). Tuy nhiên vẫn Not Ready vì: (1) OQ-EXBOT-016 chưa chốt → A4 admin reject path hoàn toàn thiếu, (2) API contract chưa được publish, (3) BR-EXBOT-* và E-EXBOT-* chưa đăng ký vào registry chính thức. Đề xuất: ưu tiên chốt OQ-EXBOT-016, publish API contract, sau đó BA update UC A4 và đăng ký E-code/BR vào backbone files — lúc đó có thể re-audit lần 3 và dự kiến đạt Conditionally Ready.
