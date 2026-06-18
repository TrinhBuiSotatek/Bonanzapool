---
title: UC Readiness Review — UC-EXBOT-agent-key (Submit and Approve HL Agent Key)
uc_id: UC-EXBOT-agent-key
feature: hl-agent-key
type: audited
date: 2026-06-18
author: qc-uc-read-exbot agent
version: v1
---

# Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC-EXBOT-agent-key — Nộp và phê duyệt HL agent key (mã hoá envelope AES-256-GCM)**

> Audit dựa trên SRS baseline 2026-06-18 (HLD decisions: drop park/re-entry; US-EXBOT-012 emergency authority update). UC file `uc-agent-key.md` vẫn dated 2026-06-12 — chưa có changelog update mới theo SRS 2026-06-18.

---

## Bảng mã viết tắt (Reference code glossary)

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case của module ExBot (no-UI). Mỗi UC mô tả một luồng nghiệp vụ logic của bot. | `03_modules/exbot/usecases/` |
| US-EXBOT-* | User Story của module ExBot. UC-EXBOT-agent-key gắn với US-EXBOT-011. | `03_modules/exbot/userstories/` |
| FR-EXBOT-* | Functional Requirement của module ExBot. Tồn tại hai bản không nhất quán: `frd.md` (FR-EXBOT-080 = D1 Architecture, FR-EXBOT-081 = Agent Key Storage, không có 082/083) và `srs/spec.md` (FR-EXBOT-080–083 đều dành cho agent-key). Xem `I-01`. | `frd.md` và `srs/spec.md` |
| BR-EXBOT-* | Business Rule của module ExBot. Toàn bộ rule agent-key nằm inline trong `srs/spec.md §4`. `02_backbone/common-rules.md` không có BR-EXBOT-080..083. Xem `I-05`. | `srs/spec.md §4` (inline) |
| E-EXBOT-* | Error code của module ExBot. Khai báo inline trong `srs/spec.md §5` (E-EXBOT-001..013). Không có trong `02_backbone/message-list.md`. Xem `I-06`. | `srs/spec.md §5` (inline) |
| FM-XB-* | Feature Map của ExBot. FM-XB-01 = D1 Schema; FM-XB-06 = API Endpoints; FM-XB-12 = Envelope Encryption. US-EXBOT-011 chỉ trace FM-XB-01 — bỏ sót FM-XB-12. | `02_backbone/feature-map.md` |
| AES-256-GCM | Advanced Encryption Standard 256-bit, Galois/Counter Mode — mã hoá symmetric có xác thực (AEAD). Agent key mã hoá bằng per-row DEK; `secret_iv` (12 bytes) và `secret_auth_tag` (16 bytes) lưu cùng blob. | (industry term) |
| DEK | Data Encryption Key — khoá 256-bit sinh ngẫu nhiên per-row, dùng mã hoá agent key, sau đó wrap bằng Master Key rồi xoá khỏi RAM. | (industry term) |
| Master Key | Khoá gốc lưu trong Cloudflare Secrets Store. Chỉ dùng để wrap/unwrap DEK. | Cloudflare Secrets Store |
| Envelope encryption | Mã hoá hai tầng: DEK mã hoá dữ liệu, Master Key wrap DEK. Tách quyền truy cập và hỗ trợ rotate Master Key. | (industry term) |
| HL agent key | Hyperliquid agent key — khoá uỷ quyền (delegate) do user tạo trên HL để bot ký lệnh perp thay mặt user. Có `expires_at`, có thể bị revoke. | Hyperliquid documentation |
| SAFE_MODE | Trạng thái khẩn của bot: chặn mọi mutation, chỉ cho phép đọc state + retry HL + alert. `lifecycle_state='safe_mode'`. | `srs/spec.md` FR-EXBOT-050 |
| OPERATOR / Facade | Worker public-facing, expose `/api/exbot/*`, proxy sang ExBot Worker qua CF service binding. | `srs/spec.md` FR-EXBOT-090 |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-agent-key mô tả quy trình NĐT nộp HL agent key để hệ thống lưu trữ an toàn bằng envelope encryption, Admin phê duyệt, và hệ thống sử dụng key đó để ký lệnh trên Hyperliquid thay mặt user. Ba pha chính: (1) NĐT submit qua `POST /api/exbot/agent-key` → ExBot Worker sinh DEK ngẫu nhiên 256-bit, mã hoá AES-256-GCM, wrap DEK bằng Master Key, ghi blob vào `hl_agent_keys` với `approval_status='pending'`. (2) Admin approve → `approval_status='approved'`, `approved_at=now`. (3) Hedge-sync decrypt key trong function scope → ký HL order → destroy ngay. Các luồng phụ: A1 — key hết hạn block bot start (E-EXBOT-004); A2 — rotation (insert row mới, row cũ chuyển trạng thái); A3 — decrypt khi hedge-sync.

**Điểm quan trọng từ SRS baseline 2026-06-18:** (1) `srs/spec.md` FR-EXBOT-080 AC ghi "old row transitions to `status='revoked'`"; FR-EXBOT-083 AC ghi "`status='superseded'` set on old row atomically" — **mâu thuẫn nội bộ trong cùng file SRS**. (2) UC file chưa được cập nhật theo SRS 2026-06-18 (vẫn dated 2026-06-12). (3) US-EXBOT-012 emergency authority đã update (OPERATOR_ROLE only, không multi-sig) — loại bỏ multi-sig consideration khỏi scope UC này.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-agent-key | Submit and Approve HL Agent Key (AES-GCM envelope encryption) | draft (2026-06-12) | Draft — chưa update theo SRS 2026-06-18 |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | UC: 2026-06-12; SRS: 2026-06-18 |

| Artefact đã đọc | Version / ngày | Vai trò | Ghi chú |
|---|---|---|---|
| `03_modules/exbot/usecases/uc-agent-key.md` | 2026-06-12 | UC chính | Chưa có changelog 2026-06-18 |
| `03_modules/exbot/usecases/index.md` | 2026-06-18 | UC index | Confirm Linked Stories + FR Trace |
| `03_modules/exbot/userstories/us-011.md` | 2026-06-12 | User story duy nhất | 4 AC Gherkin; Notes dùng `status='revoked'` |
| `03_modules/exbot/srs/spec.md` | 2026-06-18 | SRS canonical | FR-080 AC: `revoked`; FR-083 AC: `superseded` — mâu thuẫn nội bộ SRS |
| `03_modules/exbot/srs/states.md` | 2026-06-18 | State diagram | `cooldown`/`parked` đã xoá; không có state machine cho `hl_agent_keys` |
| `03_modules/exbot/srs/flows.md` | 2026-06-12 | Sequence flows | Không có flow cho agent-key; F-05 stale (chưa update) |
| `03_modules/exbot/srs/erd.md` | 2026-06-12 | ERD | Schema `hl_agent_keys` đầy đủ; không có `revoked_at`/`superseded_at` |
| `03_modules/exbot/frd.md` | 2026-06-18 | FRD | FR-EXBOT-080 = D1 Arch; FR-EXBOT-081 = Agent Key Storage; không có 082/083 |
| `02_backbone/common-rules.md` | — | Common BR registry | Không có BR-EXBOT-080..083 |
| `02_backbone/message-list.md` | 2026-06-09 | Message registry | Không có E-EXBOT-*; không có disclaimer cho bnza-exbot |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

ExBot phải ký được giao dịch perpetual trên Hyperliquid thay mặt user mà tuyệt đối không được giữ master private key. Giải pháp: user tạo agent key (khoá uỷ quyền) trên HL, nộp cho hệ thống lưu bằng envelope encryption hai tầng, Admin xác nhận hợp lệ trước khi cho phép bot dùng. Kết quả mong đợi: (a) dump D1 không thể recover plain key; (b) tổn thất tối đa nếu agent key lộ chỉ ở phạm vi uỷ quyền HL; (c) audit trail giữ lại lịch sử mọi key.

### 1.2 Phạm vi trong use case

| Hạng mục | Mô tả | Nguồn |
|---|---|---|
| F1 — Investor submit agent key | NĐT gọi `POST /api/exbot/agent-key` qua POOL UI → OPERATOR forward sang ExBot Worker | UC §3 step 1–2 |
| F2 — Server-side envelope encryption | Sinh DEK 256-bit → AES-256-GCM encrypt → wrap DEK bằng Master Key → ghi blob vào `hl_agent_keys`, `approval_status='pending'` | UC §3 step 3–6; FR-EXBOT-080 (srs); FR-EXBOT-081 (frd) |
| F3 — Confirmation response | HTTP 200 "Agent key received and encrypted. Awaiting approval." | UC §3 step 7 |
| F4 — Admin approve key | Admin approve qua dashboard → `approval_status='approved'`, `approved_at=now` | UC §3 step 8–9; FR-EXBOT-081 (srs) |
| F5 — Mở khoá preflight bot start | Sau khi approved + `expires_at` chưa qua → pass preflight check 3 của UC-EXBOT-bot-start | UC §3 step 10; FR-EXBOT-002 (srs) |
| F6 — Key expired block start (A1) | `expires_at < now` → block với E-EXBOT-004 | UC §4 A1; FR-EXBOT-083 (srs) |
| F7 — Key rotation (A2) | Insert row mới; row cũ → `revoked` (UC/US) hoặc `superseded` (srs FR-083) — **mâu thuẫn nội bộ SRS** | UC §4 A2; FR-EXBOT-082/083 (srs) |
| F8 — Decrypt khi hedge-sync (A3) | Unwrap DEK → decrypt → ký HL order → destroy plain key ngay; không log | UC §4 A3; FR-EXBOT-080 (srs) |

### 1.3 Ngoài phạm vi

| Hạng mục | Lý do | Ảnh hưởng test |
|---|---|---|
| NĐT tạo agent key trên Hyperliquid | UC giả định user đã có key (precondition). | Test dùng key testnet có sẵn. |
| POOL UI form submit | Module `bnza-pool` — ngoài scope ExBot. | Tester FE xác nhận với BA pool. |
| Admin dashboard UI approve | Module `admin/bnza-admin` — ngoài scope. | Tester admin xác nhận với BA admin. |
| Master Key rotation procedure | `encryption_key_version` có trong ERD nhưng procedure chưa spec. Xem `I-21`. | Cần xác nhận Phase A scope. |
| Validation agent key hợp lệ trên HL | UC không có rule challenge/on-chain check. Xem `I-08`. | Không thể test "submit string rác → reject". |
| Admin reject path | Enum không có `rejected`; UC không mô tả. Xem `I-12`. | Không thể test admin reject scenario. |

---

## 2. Actor, vai trò và quyền hạn

| Actor | Loại | Vai trò | Quyền hạn / giới hạn | Nguồn |
|---|---|---|---|---|
| USDC Investor (ACT-01) | Primary | Submit + rotate agent key | Có thể submit nhiều lần; chỉ 1 row `approved` tại một thời điểm; UC không định nghĩa rate limit. | UC §1; backbone ACT-01 |
| ExBot Admin (ACT-04) | Primary | Approve key pending | UC không định nghĩa rule reject, SLA approve, approver identity audit. Xem `I-12`, `I-13`. | UC §1; backbone ACT-04 |
| ExBot Worker | System | Sinh DEK, mã hoá/wrap, ghi DB, decrypt khi hedge-sync | Chạy qua CF service binding, không HTTP public (FR-EXBOT-090). | UC §1; FR-EXBOT-090 |
| D1 (control_db) | System | Lưu `hl_agent_keys` — chỉ blob mã hoá | Không bao giờ chứa plain key. | UC §1; FR-EXBOT-080 |
| Cloudflare Secrets Store | External | Giữ Master Key; wrap/unwrap DEK | Failure mode khi unavailable chưa có spec. Xem `I-14`. | UC §1; FR-EXBOT-080/081 |

**Nhận xét:** `frd.md` §FR-EXBOT-100 đánh nhãn actor=Admin cho cả POST lẫn GET endpoint `/api/exbot/agent-key`, trong khi UC nói NĐT POST submit. Xem `I-02`.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | NĐT đã tạo HL agent key trên Hyperliquid (delegate, không phải master key). | Yes | UC §2 |
| 2 | ExBot Worker có quyền đọc Master Key trong Cloudflare Secrets Store. | Yes | UC §2 |
| 3 | Bảng `hl_agent_keys` đã migrate trong `control_db`. | Yes (suy luận ERD) | `srs/erd.md` |
| 4 | NĐT đã có row trong `users` (FK `user_id`). | Yes (suy luận ERD) | `srs/erd.md` |
| 5 | Endpoint `/api/exbot/agent-key` exposed qua OPERATOR Facade và authenticated. | Yes (suy luận) | FR-EXBOT-090; FR-EXBOT-100 (frd) |
| 6 | Policy `expires_at` khi submit (user nhập hay hệ thống tự set). | TBD | (Thiếu — xem `I-07`) |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống sau | Nguồn |
|---|---|---|
| Submit thành công | Row mới `hl_agent_keys`: blob mã hoá, `approval_status='pending'`, `approved_at=NULL`. Response 200. | UC §3 step 6–7; US-011 AC-1 |
| Admin approve | `approval_status='approved'`, `approved_at=now`. NĐT pass preflight check 3. | UC §3 step 9–10; US-011 AC-2 |
| Rotation (A2) | Row mới; row cũ → `revoked` (UC/US) hoặc `superseded` (srs FR-083). **Mâu thuẫn** — xem `I-04`. `rotated_from` chain preserved. | UC §4 A2; srs FR-082/083 |
| Decrypt hedge-sync (A3) | Plain DEK + plain key chỉ tồn tại function scope; không log; row không thay đổi. | UC §4 A3; US-011 AC-4 |
| Key expired — bot start | Start bị block với E-EXBOT-004. Row KHÔNG bị xoá. | UC §4 A1; srs FR-083; US-011 AC-3 |
| Admin reject | **TBD — UC không định nghĩa.** Enum không có `rejected`. | (Thiếu — xem `I-12`) |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### §F.1 — Inventory

| # | Item | Loại | Trigger | Input | Output | Nguồn |
|---|---|---|---|---|---|---|
| F1.1 | POST /api/exbot/agent-key — submit | API operation | NĐT gọi qua POOL UI | agent key payload (schema TBD — xem `I-10`) | Row `hl_agent_keys` inserted; 200 confirmation | UC §3 step 1; FR-EXBOT-081 (frd); FR-EXBOT-090 |
| F1.2 | Generate per-row DEK | Crypto operation | Internally triggered | — | DEK 256-bit trong RAM (function scope) | UC §3 step 3; FR-EXBOT-080 (srs) |
| F1.3 | AES-256-GCM encrypt agent key | Crypto operation | After DEK generated | plainKey, DEK, IV (12 bytes) | `encrypted_secret`, `secret_iv`, `secret_auth_tag` | UC §3 step 4; FR-EXBOT-080 (srs) |
| F1.4 | Wrap DEK với Master Key | Crypto — Cloudflare Secrets Store | After encrypt | DEK, `dek_iv` | `wrapped_dek`, `dek_iv` | UC §3 step 5; FR-EXBOT-080 (srs) |
| F1.5 | INSERT hl_agent_keys | D1 write | After wrap success | blob fields + metadata | Row created; plain DEK/key destroyed | UC §3 step 6; `srs/erd.md` |
| F1.6 | GET /api/exbot/agent-key — admin list pending | API operation | Admin opens dashboard | — | List rows `approval_status='pending'` | UC §3 step 8; FR-EXBOT-100 (frd) |
| F1.7 | Admin approve key | API operation | Admin approves row | row id (payload TBD — xem `I-02`) | `approval_status='approved'`, `approved_at=now` | UC §3 step 9; FR-EXBOT-081 (srs) |
| F1.8 | Preflight check 3 — agent key | Validation | Bot start triggered | `users.hl_agent_key_id` | Pass / block E-EXBOT-004 nếu expired | UC §3 step 10; FR-EXBOT-002; FR-EXBOT-083 |
| F1.9 | Unwrap DEK + decrypt key (hedge-sync) | Crypto operation | Hedge-sync worker trước khi ký HL | `wrapped_dek`, `dek_iv`, `encrypted_secret`, `secret_iv`, `secret_auth_tag` | plain key trong function scope; destroy ngay | UC §4 A3; FR-EXBOT-080 (srs) |
| F1.10 | Key rotation — insert new row | API operation | NĐT submit key mới | new agent key payload | New row `pending`; old row → `revoked`/`superseded` (mâu thuẫn) | UC §4 A2; FR-EXBOT-082/083 (srs) |
| F1.11 | Expiry notification (7 days) | Cron — deep-audit | `expires_at - now <= 7 days` | `hl_agent_keys.expires_at` | Notification enqueued | FR-EXBOT-083 (srs); **UC không mô tả** |
| D1.1–D1.16 | hl_agent_keys fields | Data object | — | — | id, user_id, hl_user_address, agent_address, encrypted_secret, secret_iv, secret_auth_tag, wrapped_dek, dek_iv, encryption_key_version, approval_status, approved_at, expires_at, rotated_from, created_at, updated_at | `srs/erd.md`; FR-EXBOT-080 |
| S1.1 | approval_status = 'pending' | State | After INSERT | — | Bot start blocked at preflight | FR-EXBOT-081 (srs) |
| S1.2 | approval_status = 'approved' | State | After admin approve | — | Bot start preflight passes | FR-EXBOT-081 (srs) |
| S1.3 | approval_status = 'revoked' | State | Key revoked / rotation (UC/US wording) | — | Bot start blocked; hedge-sync → SAFE_MODE | FR-EXBOT-082 (srs); UC §4 A2 |
| S1.4 | approval_status = 'superseded' | State | Rotation — old row khi admin approves replacement (srs FR-083 wording) | — | Same as revoked | FR-EXBOT-083 (srs); **conflict với UC/US** — xem `I-04` |
| M1.1 | E-EXBOT-004 | Message | expires_at < now at preflight | — | "Your HL agent key has expired. Please submit a new one." HTTP 400 | `srs/spec.md §5`; **NOT in message-list.md** — xem `I-06` |
| M1.2 | Success response submit | Message | Submit thành công | — | "Agent key received and encrypted. Awaiting approval." HTTP 200 | UC §3 step 7; US-011 AC-1 |
| M1.3 | Expiry warning | Message | Deep-audit: expires_at - now <= 7 days | — | "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." | FR-EXBOT-083 (srs); **UC không mô tả** |

---

### §F.2 — Business Rules, Validations, States, Messages per Item

| # | Item | State / Precondition | Validation / Business Rule | Kết quả hợp lệ | Kết quả không hợp lệ | Resolved message | Nguồn |
|---|---|---|---|---|---|---|---|
| F2.1 | Submit (F1.1) | user_id tồn tại; auth token hợp lệ | Payload phải chứa agent key material; format chưa defined — xem `I-10` | INSERT row `pending` | Auth fail → 401/403; format invalid → TBD | — | UC §3 step 1; FR-EXBOT-090 |
| F2.2 | Master private key forbidden | Always | Chỉ lưu agent key (delegate), không bao giờ lưu master key. Không có validation rule phân biệt — xem `I-08`. | Chỉ blob agent key trong DB. | (Không có rejection path cho master key — xem `I-08`) | — | UC §2; FR-EXBOT-080; NFR-EXBOT-006 |
| F2.3 | AES-256-GCM encrypt (F1.3) | DEK đã sinh; plainKey trong RAM | IV = 12 bytes; auth_tag = 16 bytes; IV uniqueness per encryption — xem `I-15` | blob trong RAM | Encrypt fail → INSERT blocked → 5xx (UC không định nghĩa) | — | UC §3 step 4; FR-EXBOT-080 |
| F2.4 | Wrap DEK (F1.4) | Master Key accessible | Cloudflare Secrets Store phải available; failure mode chưa spec — xem `I-14` | `wrapped_dek`, `dek_iv` | Secrets Store down → INSERT blocked → 5xx (UC không định nghĩa) | — | UC §3 step 5; FR-EXBOT-080 |
| F2.5 | Plain key/DEK scope | Sau mỗi encrypt/decrypt | Plain DEK + plain key PHẢI bị destroy ngay. Không log bất kỳ giá trị raw. | Không tồn tại plain key ngoài function scope. | (Security bug — NFR-EXBOT-006) | — | UC §3 step 6; UC §4 A3; US-011 AC-4; NFR-EXBOT-006 |
| F2.6 | 1 key approved / user | At any time | DB-level UNIQUE: không có 2 row `approved` cho cùng user. | Constraint enforce. | UPDATE bị reject hoặc old row phải chuyển trước. | — | srs FR-EXBOT-082 |
| F2.7 | Admin approve (F1.7) | Row ở `pending` | UPDATE `approval_status='approved'`, `approved_at=now`. `approved_by` không có trong ERD — xem `I-13`. | Row chuyển `approved`. | Constraint fail → message TBD. | — | UC §3 step 9; FR-EXBOT-081 (srs) |
| F2.8 | Preflight check 3 (F1.8) | Bot start triggered | CHECK: `approval_status='approved'` AND `expires_at >= now`. `pending` hoặc `revoked` → block. | Pass preflight. | `approval_status` != 'approved' → block. `expires_at < now` → E-EXBOT-004. | E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." (srs §5; NOT in message-list.md) | UC §4 A1; FR-EXBOT-081/083 |
| F2.9 | Rotation old row status (F1.10) | User submit key mới | **Mâu thuẫn nội bộ SRS:** FR-EXBOT-080 AC → `revoked`; FR-EXBOT-083 AC → `superseded`. UC §4 A2 + US-011 Notes → `revoked`. | — | — | — | UC §4 A2; US-011 Notes; srs FR-080 AC; srs FR-083 AC — xem `I-04` |
| F2.10 | Rotation window submit→approve | Row mới `pending`, row cũ `approved` | srs FR-083: "existing approved key remains active until admin approves". UC §4 A2 không nói rõ thời điểm — xem `I-09`. | Bot tiếp tục dùng key cũ trong window. | Old key bị revoke sớm → SAFE_MODE không mong muốn. | — | srs FR-083; UC §4 A2 (thiếu) |
| F2.11 | Revoked row — no DELETE | After revocation | srs FR-082: "DELETE of revoked rows is forbidden." | Row tồn tại lâu dài. | DELETE bị reject. | — | srs FR-EXBOT-082 |
| F2.12 | Decrypt fail → SAFE_MODE (F1.9) | Hedge-sync thử decrypt row revoked / data corruption / Secrets Store down | srs FR-082: decryption failure → log error (không log key material) → SAFE_MODE. UC §4 A3 không nói path này. | — | `lifecycle_state='safe_mode'` | — | srs FR-EXBOT-082; UC §4 A3 (thiếu) |
| F2.13 | Expiry notification (F1.11) | Deep-audit | srs FR-083: scan `expires_at - now <= 7 days` → enqueue notification. UC không mô tả. | Message enqueued vào `notification` queue. | — | "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." | srs FR-083; UC (thiếu) |
| F2.14 | Rate limit submit | Per request | UC không có rule — xem `I-17`. | — | — | — | (Thiếu) |
| F2.15 | Duplicate submit while pending | Row `pending` đã tồn tại | UC không định nghĩa: insert thứ 2, reject, hay overwrite — xem `I-16`. | — | — | — | (Thiếu) |

---

### §F.3 — Functional Logic & Workflow

#### F3.1 — Submit + Encrypt + Confirm

| Path | Trigger | Actor | Input | Hành động | Output / State | Nguồn |
|---|---|---|---|---|---|---|
| Happy | NĐT gọi POST | USDC Investor | agent key payload | OPERATOR auth → ExBot Worker sinh DEK → AES-GCM encrypt → wrap DEK → INSERT `pending` → destroy plain | HTTP 200; row `pending` | UC §3 step 1–7 |
| Alt — Secrets Store down | Step wrap DEK | ExBot Worker | — | Wrap fail | INSERT blocked; 5xx; plain DEK cần destroy (UC không nói) | xem `I-14` |
| Alt — Duplicate pending | Submit khi đã có row `pending` | USDC Investor | — | UC không định nghĩa | TBD — xem `I-16` | (Thiếu) |
| Exception — Auth fail | OPERATOR auth | — | Invalid token | OPERATOR reject | HTTP 401/403 | FR-EXBOT-090 |

#### F3.2 — Admin Approve Key

| Path | Trigger | Actor | Input | Hành động | Output / State | Nguồn |
|---|---|---|---|---|---|---|
| Happy | Admin bấm approve | ExBot Admin | row id (payload TBD — xem `I-02`) | UPDATE `approval_status='approved'`, `approved_at=now` | Row `approved`; NĐT pass preflight | UC §3 step 8–9; FR-EXBOT-081 |
| Alt — Approve expired key | Admin approve key có `expires_at < now` | ExBot Admin | — | UC không định nghĩa — xem `I-18` | TBD | (Thiếu) |
| Alt — Constraint vi phạm | Admin approve khi user đã có row `approved` | ExBot Admin | — | DB reject hoặc demote old row trước | Error (message TBD); xem `I-04` | srs FR-082 |
| Missing — Admin reject | Admin không approve | ExBot Admin | — | UC không định nghĩa | Enum không có `rejected` — xem `I-12` | (Thiếu) |

#### F3.3 — Preflight Check 3 (A1)

| Path | Trigger | Actor | Input | Hành động | Output / State | Nguồn |
|---|---|---|---|---|---|---|
| Happy — pass | Bot start | ExBot Worker | `hl_agent_keys WHERE user_id=?` | Check `approved` AND `expires_at >= now` | Pass preflight 3 | FR-EXBOT-002; FR-EXBOT-081 |
| Block — expired | Preflight; `expires_at < now` | ExBot Worker | — | Reject với E-EXBOT-004 | HTTP 400; row NOT deleted | UC §4 A1; srs FR-083 |
| Block — pending/revoked | Preflight; key không `approved` | ExBot Worker | — | Reject (message TBD cho case này) | HTTP 400 | srs FR-081 |

#### F3.4 — Key Rotation (A2)

| Path | Trigger | Actor | Input | Hành động | Output / State | Nguồn |
|---|---|---|---|---|---|---|
| Submit new key | NĐT submit khi có key cũ `approved` | USDC Investor | new payload | INSERT row mới `pending`; old row KHÔNG revoke ngay (srs FR-083) | Row mới `pending`; old row vẫn `approved` | srs FR-083; UC §4 A2 (thiếu timing) |
| Admin approves new row | Admin approve | ExBot Admin | — | Row mới → `approved`; old row → `revoked` (UC) hoặc `superseded` (srs FR-083) atomically | Mâu thuẫn — xem `I-04` | UC §4 A2; srs FR-082/083 |
| Hedge-sync trong window | Worker decrypt old key | ExBot Worker | — | Decrypt thành công (old key vẫn `approved`) | Bot không interrupt | srs FR-083 |

#### F3.5 — Decrypt khi Hedge-sync (A3)

| Path | Trigger | Actor | Input | Hành động | Output / State | Nguồn |
|---|---|---|---|---|---|---|
| Happy | Hedge-sync worker cần ký HL | ExBot Worker | fetch row `hl_agent_keys` | Unwrap DEK → decrypt → ký HL → destroy plain key ngay | HL order signed; row không thay đổi; không log plain key | UC §4 A3; US-011 AC-4; FR-EXBOT-080 |
| Exception — Decrypt fail | Row revoked / data corruption | ExBot Worker | — | Fail → log error (không log key material) → SAFE_MODE | `bots.lifecycle_state='safe_mode'` | srs FR-082; **UC không nói** |
| Exception — Secrets Store down | Unwrap fail | ExBot Worker | — | Decrypt blocked → SAFE_MODE (suy luận FR-082) | `bots.lifecycle_state='safe_mode'` | srs FR-082 (suy luận); xem `I-14` |

---

### §F.4 — Functional Integration & Data Consistency

| Trigger | UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán | Nguồn |
|---|---|---|---|---|
| Submit + approve agent key | UC-EXBOT-bot-start preflight check 3 | Không có key `approved` chưa expired → bot không start. | `users.hl_agent_key_id` trỏ đúng row `approved`; không partial bot record nếu preflight fail. | FR-EXBOT-002/081 |
| Decrypt key (A3) | UC-EXBOT-hedge-sync | Mỗi hedge-sync cần decrypt để ký; fail → SAFE_MODE. | `hl_agent_keys.approval_status` không bị mutate bởi hedge-sync; `bots.lifecycle_state` → `safe_mode` nếu fail. | srs FR-082; flows F-02 |
| Rotation A2 (window) | UC-EXBOT-hedge-sync | Old key active trong window; bot không interrupt. | ≤1 row `approved` per user (DB); `rotated_from` chain. | srs FR-083 |
| Expiry notification | UC-EXBOT-deep-audit (cron) | Deep-audit scan, enqueue notification ≤7 ngày. | Notification đúng template; `approval_status` không thay đổi. | srs FR-083 |
| Decrypt fail → SAFE_MODE | UC-EXBOT-hedge-sync, deep-audit | Bot dừng mutation; auto-recovery hoặc `bot_safe_close`. | `bots.status='safe_mode'`; key material không trong log. | srs FR-050/082 |
| Admin force-close | UC-EXBOT-bot-safe-close | Force-close không revoke key. | Row `hl_agent_keys` giữ nguyên sau close. | srs FR-072 |

---

### §F.5 — AC Candidates

| AC # | Scenario | Given | When | Then | Nguồn |
|---|---|---|---|---|---|
| AC-01 | Happy — submit + store encrypted | NĐT có agent key; user_id tồn tại | Submit qua POST | Row `pending` với blob; HTTP 200 "Agent key received and encrypted. Awaiting approval." | US-011 AC-1 |
| AC-02 | Happy — admin approve | Row `pending` | Admin approve | `approval_status='approved'`, `approved_at=now`; pass preflight 3. | US-011 AC-2 |
| AC-03 | Edge — expired key blocks | `expires_at < now` | Preflight check | Block với E-EXBOT-004; row NOT deleted. | US-011 AC-3; srs FR-083 |
| AC-04 | Negative — plain key không trong log | Worker decrypt để ký | Signing complete | Plain DEK/key destroyed; không log; row vẫn chỉ blob. | US-011 AC-4; NFR-EXBOT-006 |
| AC-05 | Suy luận cần xác nhận — 1 approved / user | User X có row `approved` | Admin approve row khác | Reject hoặc old row → `revoked`/`superseded` atomically. **Mâu thuẫn — xem `I-04`.** | srs FR-082/083 |
| AC-06 | Suy luận cần xác nhận — rotation giữ chain | User X submit key mới | Submit + approve | Row mới `approved`; old row `revoked`/`superseded`; `rotated_from` chain; old row NOT deleted. | UC §4 A2; srs FR-082 |
| AC-07 | Suy luận cần xác nhận — decrypt fail → SAFE_MODE | Hedge-sync với row `revoked` / Secrets Store down | Worker decrypt | Bot → `safe_mode`; log không chứa key material. | srs FR-082 |
| AC-08 | Suy luận cần xác nhận — notification 7d | `expires_at - now <= 7 days` | Deep-audit cron tick | "Your HL agent key expires in {N} days..." enqueued vào `notification` queue. | srs FR-083 |


---

## 7. Phân tích liên chức năng (Cross-Function Analysis)

### 7.1 Điểm giao cắt giữa UC-EXBOT-agent-key và các UC khác

| Điểm giao | UC / module | Mô tả phụ thuộc | Vấn đề cần chú ý |
|---|---|---|---|
| Preflight check 3 | UC-EXBOT-bot-start | Bot-start chặn nếu không có agent key `approved` chưa expired. `users.hl_agent_key_id` phải trỏ đúng row sau khi admin approve. | Nếu `users.hl_agent_key_id` không được cập nhật sau approve, preflight check 3 sẽ fail ngay cả khi row `approved`. (Source: FR-EXBOT-002 / UC §3 step 10) |
| Hedge-sync decrypt | UC-EXBOT-hedge-sync (F-02) | Mỗi chu kỳ hedge-sync cần fetch `hl_agent_keys`, unwrap DEK, decrypt, ký HL, destroy ngay. | Decrypt fail → SAFE_MODE; UC-EXBOT-agent-key không định nghĩa path này. Xem `I-07` (expires_at policy), `I-14` (Secrets Store failure). |
| SAFE_MODE trigger | UC-EXBOT-bot-safe-close / UC-EXBOT-deep-audit | Decrypt fail có thể trigger SAFE_MODE → safe-close cascade. | srs FR-082 ghi "log error, no key material", nhưng UC-EXBOT-agent-key không tham chiếu path này. |
| Emergency recovery | US-EXBOT-012 | Emergency authority = OPERATOR_ROLE only; không có recipient param. UC-EXBOT-agent-key không bị ảnh hưởng trực tiếp nhưng đây là context của HLD 2026-06-18. | N/A cho UC này. |
| Deep-audit cron | UC-EXBOT-deep-audit | Scan `expires_at - now <= 7 days` → enqueue notification. | UC-EXBOT-agent-key không mô tả luồng này mặc dù srs FR-083 yêu cầu. Xem `I-11`. |
| Rotation window | UC-EXBOT-hedge-sync | Trong window submit-mới→approve-mới, hedge-sync phải dùng key cũ (còn `approved`). | Thời điểm chuyển row cũ sang `revoked`/`superseded` chưa rõ trong UC. Xem `I-04`, `I-09`. |

### 7.2 Nhất quán dữ liệu sau các sự kiện chính

| Sự kiện | Bảng bị ảnh hưởng | State sau sự kiện | Kiểm tra nhất quán bắt buộc |
|---|---|---|---|
| Submit thành công | `hl_agent_keys` | Row mới, `approval_status='pending'` | `user_id` tồn tại; chỉ 1 row `pending` per user (chưa có constraint trong ERD — xem `I-16`) |
| Admin approve | `hl_agent_keys` | Row → `approved`, `approved_at=now` | `approved_by` không có trong ERD (`I-13`); DB constraint 1 approved/user giữ nguyên |
| Rotation — admin approves mới | `hl_agent_keys` (2 rows) | Row mới → `approved`; old row → `revoked`/`superseded` (mâu thuẫn) | Atomicity? srs FR-083 ghi "atomically" nhưng không mô tả transaction boundary (`I-09`) |
| Expiry block | `bots` | Bot không start; `hl_agent_keys` không thay đổi | `hl_agent_keys.expires_at` không bị xoá khi expired |
| Decrypt fail | `bots` | `lifecycle_state='safe_mode'` | `hl_agent_keys` KHÔNG mutate; log không chứa key material |

---

## 8. Acceptance Criteria (cross-check với §F.5)

| AC # | Scope | Given | When | Then | Trạng thái | Nguồn |
|---|---|---|---|---|---|---|
| AC-01 | Submit thành công | NĐT đã đăng nhập; user_id hợp lệ | Gọi POST /api/exbot/agent-key với payload hợp lệ | HTTP 200 "Agent key received and encrypted. Awaiting approval."; row `hl_agent_keys` tồn tại với `approval_status='pending'`; plain key KHÔNG trong log | ✅ Có trong US-011 AC-1 | US-011 AC-1; UC §3 step 7 |
| AC-02 | Admin approve | Row `pending` tồn tại | Admin approve qua dashboard | `approval_status='approved'`, `approved_at` được ghi; NĐT pass preflight check 3 | ✅ Có trong US-011 AC-2 | US-011 AC-2; FR-EXBOT-081 |
| AC-03 | Expired key blocks | `expires_at < now`; bot start trigger | Preflight check 3 | HTTP 400 với E-EXBOT-004 "Your HL agent key has expired. Please submit a new one."; row NOT deleted | ✅ Có trong US-011 AC-3 | US-011 AC-3; srs FR-083 |
| AC-04 | Plain key không log | Worker decrypt để ký | Signing done | Plain DEK/key không xuất hiện trong log hoặc error message; row `hl_agent_keys` chỉ chứa blob | ✅ Có trong US-011 AC-4 | US-011 AC-4; NFR-EXBOT-006 |
| AC-05 | 1 approved/user | User X đã có row `approved` | Admin approve row khác cho user X | Constraint enforce: old row → `revoked`/`superseded`; không có 2 row `approved` cùng user | ❌ Thiếu AC; mâu thuẫn `I-04` | srs FR-082/083 |
| AC-06 | Rotation chain | User X submit key mới khi đang có `approved` | Submit + admin approve mới | `rotated_from` FK tồn tại; old row NOT deleted; `rotation window` hedge-sync không bị interrupt | ❌ Thiếu AC; timing chưa rõ `I-09` | UC §4 A2; srs FR-083 |
| AC-07 | Decrypt fail → SAFE_MODE | Hedge-sync với row `revoked` hoặc Secrets Store down | Worker thực hiện decrypt | Bot → `lifecycle_state='safe_mode'`; log error không chứa key material | ❌ Thiếu trong UC; chỉ có trong srs FR-082 | srs FR-082 |
| AC-08 | Expiry notification 7d | `expires_at - now <= 7 days` | Deep-audit cron tick | Notification "Your HL agent key expires in {N} days. Submit a new key..." enqueued | ❌ Thiếu trong UC | srs FR-083 |

---

## 9. Non-Functional Requirements (NFR) liên quan

| NFR ID | Nội dung | Kiểm tra được không | Ghi chú |
|---|---|---|---|
| NFR-EXBOT-006 | Plain DEK/key function-scoped; không bao giờ log raw secret | ✅ Có thể verify qua log audit | Core security requirement; test case cần verify không có plain key trong Cloudflare log |
| NFR-EXBOT-007 | AES-256-GCM; IV 12 bytes; auth_tag 16 bytes | ✅ Verify qua blob analysis | IV uniqueness per row chưa có rule — xem `I-15` |
| NFR-EXBOT-008 | Master Key trong Cloudflare Secrets Store; không hardcode | ✅ Code review / secrets audit | Secrets Store down → failure path chưa spec — xem `I-14` |
| (Chưa có NFR ID) | Rate limit cho POST /api/exbot/agent-key | ❌ Chưa có NFR | Xem `I-17` |
| (Chưa có NFR ID) | expires_at policy: kỳ hạn tối đa, tối thiểu | ❌ Chưa có NFR | Xem `I-07` |
| (Chưa có NFR ID) | SLA Admin approve: thời hạn từ `pending` → `approved` | ❌ Chưa có NFR | Xem `I-13` |

---

## 10. Issue Register, Dependencies & Audit Summary

### §10.1 — Issue Register

| Issue ID | Type | Severity | Khu vực ảnh hưởng | Source trace | Vấn đề phát hiện | Ảnh hưởng đến tester | Câu hỏi / đề xuất fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-01 | CROSS_SOURCE_CONFLICT | Blocker | Area 1 (Inventory) | `frd.md` FR-EXBOT-080 = D1 Architecture; `srs/spec.md` FR-EXBOT-080 = Agent Key Storage; `srs/spec.md` FR-EXBOT-082 và FR-EXBOT-083 không tồn tại trong `frd.md` | `frd.md` và `srs/spec.md` dùng cùng số FR-EXBOT-080 để chỉ hai nội dung khác nhau. `frd.md` không có FR-EXBOT-082, FR-EXBOT-083 trong khi `srs/spec.md` có cả 4 FR (080–083) dành cho agent-key. Tester không biết nên dùng bộ FR nào làm nguồn chính. | Không thể trace test case về đúng FR — mọi test case liên quan đến agent-key storage, revocation, expiry đều bị lơ lửng. | BA cần đồng bộ `frd.md` và `srs/spec.md` về cùng bộ số FR; hoặc chính thức tuyên bố `srs/spec.md` là nguồn duy nhất cho FR agent-key và `frd.md` chỉ trace nhóm D1/API/NFR. | Open |
| I-02 | CROSS_SOURCE_CONFLICT | Major | Area 1 (Inventory); Area 4 (Integration) | `frd.md` FR-EXBOT-100: actor = "Admin" cho cả GET và POST `/api/exbot/agent-key`; UC §3 step 1: NĐT gọi POST; UC §3 step 8: Admin gọi GET | `frd.md` FR-EXBOT-100 gán Admin là actor của POST /api/exbot/agent-key, trong khi UC định nghĩa NĐT gọi POST để nộp key và Admin chỉ gọi GET để xem danh sách pending. Tester không biết endpoint nào dành cho ai. | Test case kiểm soát truy cập và luồng submit sẽ fail ngay nếu dùng nhầm actor. | BA cần cập nhật `frd.md` FR-EXBOT-100: POST do NĐT, GET do Admin; hoặc giải thích tại sao frd thiết kế khác UC. | Open |
| I-03 | MISSING_INFO | Minor | Area 5 (Doc Quality) | `uc-agent-key.md` header: `updated: 2026-06-12`; `srs/spec.md` updated 2026-06-18 | UC file chưa có changelog entry cho ngày 2026-06-18 dù SRS đã có HLD decision làm thay đổi enum rotation. UC title trong body là "UC-EXBOT-agent-key-approval" nhưng file name và index dùng "UC-EXBOT-agent-key". | Tester không biết UC có áp dụng SRS mới nhất không; inconsistent UC title gây khó tra cứu. | BA update `updated: 2026-06-18`, thêm changelog entry, thống nhất tên UC. | Open |
| I-04 | INTERNAL_INCONSISTENCY | Blocker | Area 2 (Rules/States/Messages) | `srs/spec.md` FR-EXBOT-080 AC: "old row transitions to `status='revoked'`"; `srs/spec.md` FR-EXBOT-083 AC: "`status='superseded'` is set on the old row atomically"; UC §4 A2: "old row set to `status='revoked'`"; `userstories/us-011.md` Notes: `status='revoked'` | Trong cùng một file `srs/spec.md`, FR-EXBOT-080 ghi trạng thái cũ chuyển thành `revoked` khi rotation, nhưng FR-EXBOT-083 ghi trạng thái cũ chuyển thành `superseded`. Đây là mâu thuẫn nội bộ SRS. UC và US-011 theo FR-080 (`revoked`). Nếu DB enforce enum, một trong hai AC sẽ fail. | Test case rotation không thể viết vì không biết expected state là `revoked` hay `superseded`. | BA cần chốt một enum value cho rotation cũ-row và cập nhật toàn bộ `srs/spec.md`, UC §4 A2, US-011 Notes về cùng giá trị. | Open |
| I-05 | MISSING_INFO | Major | Area 2 (Rules/States/Messages) | UC §6: "BR-EXBOT (FR-EXBOT-080, 081, 082, 083)"; `02_backbone/common-rules.md`: không có BR-EXBOT-080..083 | UC §6 tham chiếu BR-EXBOT nhưng các rule này không tồn tại trong `common-rules.md` — chúng chỉ nằm inline trong `srs/spec.md §4`. Tester không thể xác minh nội dung BR bằng cách tra `common-rules.md`. | Test case liên quan đến BR validation (ví dụ: 1 approved/user, DELETE forbidden, expiry) không có nguồn chính thức để trace. | BA cần tạo BR-EXBOT-080..083 trong `common-rules.md` hoặc xác nhận rằng inline srs là nguồn duy nhất và update UC §6 để dẫn đúng nguồn. | Open |
| I-06 | MISSING_INFO | Major | Area 2 (Rules/States/Messages) | `srs/spec.md §5`: E-EXBOT-004 khai báo inline; `02_backbone/message-list.md`: không có mục nào cho E-EXBOT-*, không có disclaimer cho bnza-exbot | E-EXBOT-004 "Your HL agent key has expired. Please submit a new one." được khai báo trong `srs/spec.md §5` nhưng không đăng ký trong `message-list.md`. Tester không biết văn bản chính thức của message này và không thể verify bằng message registry. | Test case kiểm tra error message E-EXBOT-004 không có nguồn master để compare. | BA cần thêm E-EXBOT-001..013 vào `message-list.md` hoặc tạo section ExBot riêng trong registry và thêm disclaimer. | Open |
| I-07 | MISSING_INFO | Major | Area 2 (Rules/States/Messages) | `srs/spec.md` FR-EXBOT-083: "key has an `expires_at` field"; `srs/erd.md`: `expires_at TEXT`; UC §3 step 1: không định nghĩa expires_at | Không có tài liệu nào định nghĩa: (a) ai set `expires_at` — user gửi hay hệ thống tự tính? (b) thời hạn tối đa / mặc định; (c) có validate khi submit không (ví dụ: không cho phép expires_at trong quá khứ). | Tester không biết expected giá trị `expires_at` khi submit, không thể viết test case cho boundary của trường này. | BA cần chốt: ai set `expires_at`, rule validation (min/max), và nếu user gửi thì format/constraint ra sao. | Open |
| I-08 | MISSING_INFO | Major | Area 2 (Rules/States/Messages) | FR-EXBOT-080 (srs): "stores the agent's delegate key"; UC §2: "Chỉ agent key (delegate), không phải master key"; không có validation rule | Không có validation rule nào phân biệt agent key với master key để từ chối trường hợp user vô tình nộp master private key. Format / length / prefix của agent key không được định nghĩa. | Test case negative: "nộp master key bị reject" không viết được vì không có expected validation behavior. | BA cần định nghĩa format hợp lệ của agent key (ví dụ: length, prefix, checksum) và rule từ chối nếu không đúng format. | Open |
| I-09 | AMBIGUOUS_WORDING | Major | Area 3 (Workflow) | `srs/spec.md` FR-EXBOT-083: "existing approved key remains active until admin approves the replacement"; UC §4 A2 không mô tả timing hay atomicity | Thời điểm chính xác khi row cũ chuyển trạng thái khi rotation chưa rõ: cùng transaction với approve-new, hay sau khi approve-new commit, hay trong một cron job? Thiếu mô tả atomicity / transaction boundary. | Test case rotation không thể verify "hedge-sync không bị interrupt trong window" vì không biết exact timing chuyển state. | BA cần bổ sung vào UC §4 A2: hành động cụ thể khi admin approve new key (atomic DB update, transaction boundary) và hành vi của hedge-sync trong window. | Open |
| I-10 | BLOCKED_EVIDENCE | Blocker | Area 4 (Integration) | UC §3 step 1: "NĐT gọi POST /api/exbot/agent-key"; `frd.md` FR-EXBOT-100: endpoint có tên nhưng không có schema; không có file API contract | Không có tài liệu nào định nghĩa schema của payload POST /api/exbot/agent-key (field name, type, required/optional, ví dụ giá trị) và schema của response. Tester không có contract để viết test case submit. | Không thể thiết kế test case submit hợp lệ, test negative validation, hoặc verify error response format. | BA / Dev cần publish API contract cho `/api/exbot/agent-key` với đầy đủ request schema, response schema, và HTTP status codes. | Open |
| I-11 | MISSING_INFO | Major | Area 3 (Workflow) | `srs/spec.md` FR-EXBOT-083: "deep-audit should scan expires_at"; UC không có section nào mô tả deep-audit trigger / cron / notification | Luồng cron deep-audit scan `expires_at <= now + 7d` và enqueue expiry notification không được mô tả trong UC-EXBOT-agent-key. Tester không biết UC này có yêu cầu coverage cho notification hay không. | Test case cron / expiry notification không có trong scope UC — tester có thể bỏ sót. | BA cần thêm vào UC §4 một alternate flow cho expiry notification hoặc xác nhận đây thuộc UC-EXBOT-deep-audit và thêm cross-reference. | Open |
| I-12 | MISSING_INFO | Major | Area 3 (Workflow) | UC §3 step 8–9: chỉ có path approve; `approval_status` enum: pending/approved/revoked/superseded; không có `rejected` | Không có alternate flow khi Admin không approve (reject) một key pending. Không có enum value `rejected`. Tester không biết hành vi hệ thống khi Admin từ chối, message trả về là gì, NĐT có được thông báo không. | Test case "Admin reject" không viết được. | BA cần định nghĩa admin-reject path: enum value mới (`rejected`?), message gửi NĐT, hành vi với row rejected (giữ hay delete). | Open |
| I-13 | MISSING_INFO | Major | Area 4 (Integration) | `srs/erd.md` `hl_agent_keys`: không có trường `approved_by`; UC §3 step 9: không định nghĩa SLA approve | Không có cách audit ai đã approve một agent key (thiếu trường `approved_by`). Không có SLA từ `pending` → `approved` (ví dụ: bot không start được bao lâu nếu admin không xử lý?). | Audit trail test case không viết được; SLA test không có baseline. | BA cần thêm `approved_by` vào ERD hoặc giải thích tại sao không cần; định nghĩa SLA approve (nếu có). | Open |
| I-14 | MISSING_INFO | Major | Area 3 (Workflow); Area 4 (Integration) | FR-EXBOT-080 (srs): wrap DEK via Cloudflare Secrets Store; không có failure handling spec | Không có tài liệu nào định nghĩa hành vi khi Cloudflare Secrets Store không available: (a) lúc wrap DEK khi submit; (b) lúc unwrap DEK khi hedge-sync. Nếu wrap fail lúc submit, INSERT có bị block không? Plain DEK có bị destroy đúng cách không? | Test case dependency failure (Secrets Store down) không viết được. | BA cần bổ sung failure handling cho Secrets Store unavailability vào UC §3 (submit) và UC §4 A3 (decrypt). | Open |
| I-15 | AMBIGUOUS_WORDING | Minor | Area 2 (Rules/States/Messages) | FR-EXBOT-080 (srs): "AES-256-GCM; IV 12 bytes"; không có rule về IV uniqueness | Không có rule yêu cầu IV phải unique per row (chống nonce reuse). AES-GCM với IV tái dùng là lỗ hổng bảo mật nghiêm trọng, nhưng UC không đề cập. | Test case kiểm tra IV uniqueness không có trong scope. | BA / Dev cần xác nhận IV được sinh ngẫu nhiên (CSPRNG) per row và không tái dùng — nếu đã đảm bảo ở code level, cần note vào NFR. | Closed |
| I-16 | MISSING_INFO | Minor | Area 3 (Workflow) | UC §4 A2: mô tả rotation khi đã có key cũ; không có flow khi submit khi đang có pending | Không định nghĩa hành vi khi NĐT submit key mới trong khi đã có row `pending` (ví dụ: bị reject vì chỉ 1 pending/user? overwrite? INSERT thêm row?). | Test case "submit khi pending đã tồn tại" không có expected result. | BA cần bổ sung UC §4 alt flow hoặc constraint rõ ràng. | Open |
| I-17 | MISSING_INFO | Minor | Area 2 (Rules/States/Messages) | UC không có rate limit rule; `frd.md` không có NFR rate limit cho endpoint này | POST /api/exbot/agent-key không có rate limit được định nghĩa. Tester không biết endpoint này có giới hạn request per user per time window không. | Test case rate limit không viết được. | BA cần xác nhận rate limit policy cho endpoint này (nếu có). | Open |
| I-18 | MISSING_INFO | Minor | Area 3 (Workflow) | UC không định nghĩa hành vi Admin approve key đã expired (`expires_at < now`) | Nếu Admin xử lý chậm và key đã hết hạn trước khi approve, hành vi là gì: approve vẫn được (row `approved` nhưng sẽ fail preflight ngay) hay system reject approve? | Test case edge case này không có expected result. | BA cần định nghĩa: hệ thống có validate `expires_at` khi admin approve không? | Open |
| I-19 | MISSING_INFO | Minor | Area 1 (Inventory) | UC §4 A2: "old row set to `status='revoked'`"; UC không mô tả có được phép DELETE revoked rows không | UC không nói rõ DELETE revoked rows có bị cấm hay không, mặc dù srs FR-082 ghi "DELETE of revoked rows is forbidden". | Tester cần biết để viết negative test case "xoá row revoked bị block". | BA cần cross-reference FR-EXBOT-082 srs vào UC §6 Business Rules để tester trace được. | Open |
| I-20 | MISSING_INFO | Minor | Area 1 (Inventory) | `srs/spec.md §5`: E-EXBOT-001..013 khai báo inline; UC không list đầy đủ error codes liên quan | UC không có section liệt kê toàn bộ error codes ảnh hưởng đến luồng agent-key (ngoài E-EXBOT-004). Tester không biết có error code nào khác cần cover không. | Coverage error cases bị bỏ sót. | BA cần thêm bảng E-* liên quan vào UC §6 hoặc §10. | Open |
| I-21 | MISSING_INFO | Note | Area 5 (Doc Quality) | UC Mermaid diagram: "User->>System: Trigger action" (placeholder) | UC có chứa Mermaid diagram nhưng chỉ là placeholder — không có sequence diagram thực tế cho submit/approve/decrypt flow. | Không ảnh hưởng test case nhưng giảm khả năng hiểu của reviewer mới. | BA nên thêm sequence diagram thực tế hoặc xoá placeholder. | Closed |
| I-22 | MISSING_INFO | Note | Area 1 (Inventory) | `userstories/us-011.md` FR Trace: chỉ có FM-XB-01 (D1 Schema); thiếu FM-XB-12 (Envelope Encryption) | US-011 chỉ trace FM-XB-01 nhưng bỏ qua FM-XB-12 (Envelope Encryption) mặc dù AC-4 về plain key destruction liên quan trực tiếp đến FM-XB-12. | Feature map coverage cho encryption feature bị thiếu. | BA cần thêm FM-XB-12 vào FR Trace của US-011. | Open |
| I-23 | MISSING_INFO | Note | Area 2 (Rules/States/Messages) | `srs/states.md` 2026-06-18: không có state machine cho `hl_agent_keys.approval_status` | `srs/states.md` chỉ có state machine cho `bots.lifecycle_state`. Không có diagram trạng thái cho `hl_agent_keys.approval_status` (pending → approved → revoked/superseded). Tester cần tự suy luận từ AC. | State transition test case cần tự construct enum, tăng rủi ro bỏ sót transition. | BA nên thêm state machine cho `hl_agent_keys.approval_status` vào `srs/states.md`. | Open |
| I-24 | MISSING_INFO | Note | Area 3 (Workflow) | UC §4 A3 step 1: "ExBot Worker fetches hl_agent_keys row"; không mô tả caching hay lookup strategy | UC không định nghĩa: fetch row mỗi hedge-sync cycle hay có caching? Cache invalidation khi key bị revoke giữa chừng? | Nếu có cache, hedge-sync có thể dùng revoked key. Test case cần bao gồm revoke-mid-cycle nếu caching tồn tại. | BA / Dev cần clarify caching strategy cho hl_agent_keys lookup trong hedge-sync. | Closed |


---

### §10.2 — Dependencies

| # | Phụ thuộc | Loại | Ảnh hưởng | Status |
|---|---|---|---|---|
| D-01 | API contract POST/GET `/api/exbot/agent-key` | External doc | Blocker — không viết test case submit/read nếu thiếu schema | Thiếu — xem `I-10` |
| D-02 | Cloudflare Secrets Store (Master Key) | Infrastructure | Major — failure path cần spec để test | Thiếu failure handling — xem `I-14` |
| D-03 | `02_backbone/common-rules.md` — BR-EXBOT-080..083 | Common registry | Major — tester cần tra BR để trace | Thiếu — xem `I-05` |
| D-04 | `02_backbone/message-list.md` — E-EXBOT-001..013 | Message registry | Major — tester cần tra message text | Thiếu — xem `I-06` |
| D-05 | `srs/states.md` — state machine cho `hl_agent_keys` | SRS diagram | Minor | Thiếu — xem `I-23` |
| D-06 | UC-EXBOT-bot-start — preflight check 3 definition | Cross-UC | Informational — test integration | Có (srs FR-EXBOT-002); UC-EXBOT-bot-start cần review riêng |
| D-07 | UC-EXBOT-deep-audit — expiry notification cron | Cross-UC | Major — cần scope clarity | Thiếu cross-reference — xem `I-11` |

---

### §10.3 — Audit Summary

#### Kết quả chấm điểm

| Khu vực đánh giá | Max điểm | Điểm đạt | Lý do trừ điểm |
|---|---|---|---|
| Area 1 — Inventory (functions, data, states, messages) | 20 | 13 | FR numbering conflict (I-01) gây không xác định được nguồn chính (−4); API contract thiếu (I-10) gây không trace được I/O (−3) |
| Area 2 — Rules, States, Messages | 25 | 10 | SRS internal enum conflict (I-04) là Blocker (−5); BR-EXBOT không trong common-rules (I-05) (−4); E-EXBOT không trong message-list (I-06) (−3); expires_at policy undefined (I-07) (−2); agent key format undefined (I-08) (−1) |
| Area 3 — Workflow (happy/alt/exception paths) | 25 | 13 | Admin reject path missing (I-12) (−4); deep-audit cron missing (I-11) (−3); Secrets Store failure (I-14) (−2); rotation timing (I-09) (−2); duplicate pending (I-16) (−1) |
| Area 4 — Integration & Data Consistency | 15 | 9 | API contract blocker (I-10) (−4); approved_by missing/SLA (I-13) (−2) |
| Area 5 — Documentation Quality | 15 | 6 | UC không update per SRS 2026-06-18 (I-03) (−3); placeholder diagram (I-21) (−2); UC title inconsistency (I-03) (−2); FM trace thiếu (I-22) (−2) |
| **Tổng** | **100** | **51** | |

**Verdict: ❌ NOT READY (51/100)**

Ngưỡng Conditionally Ready = 70. UC hiện đạt 51 — không đủ điều kiện.

#### Blockers (không thể bắt đầu test design cho đến khi resolved)

| # | Issue | Lý do block |
|---|---|---|
| B-01 | I-01: FR numbering conflict frd.md vs srs/spec.md | Tester không có nguồn chính thức để trace test case → FR trace bị lơ lửng |
| B-02 | I-04: SRS internal enum conflict revoked vs superseded | Expected state sau rotation chưa xác định → AC rotation không viết được |
| B-03 | I-10: API contract POST /api/exbot/agent-key thiếu | Không có schema → không viết được test case submit |

#### Major Issues (cần resolve trước Test Design pass 2)

I-02 (actor conflict frd vs UC), I-05 (BR không có trong common-rules), I-06 (E-EXBOT không có trong message-list), I-07 (expires_at policy undefined), I-08 (agent key format undefined), I-09 (rotation timing unclear), I-11 (expiry notification flow missing), I-12 (admin reject path missing), I-13 (approved_by/SLA missing), I-14 (Secrets Store failure path missing).

#### Khuyến nghị

UC-EXBOT-agent-key cần BA giải quyết 3 Blocker trước khi QC có thể bắt đầu viết test case. Ưu tiên: (1) Đồng bộ bộ số FR giữa `frd.md` và `srs/spec.md` (I-01); (2) Chốt enum value cho rotation old-row — `revoked` hay `superseded` — và cập nhật toàn bộ tài liệu liên quan (I-04); (3) Publish API contract cho `/api/exbot/agent-key` (I-10). Song song, BA nên đăng ký BR-EXBOT-080..083 vào `common-rules.md` và E-EXBOT-001..013 vào `message-list.md` để tester có nguồn tra cứu độc lập. UC cũng cần được cập nhật changelog theo SRS 2026-06-18 để đảm bảo nhất quán với HLD decision đã chốt.

---

## 11. Changelog

| Ngày | Version | Người tạo | Nội dung |
|---|---|---|---|
| 2026-06-18 | v1 | qc-uc-read-exbot agent (Trinh.Bui) | Initial audit dựa trên SRS baseline 2026-06-18. 24 issues (3 Blocker, 10 Major, 8 Minor, 3 Note). Score: 51/100 Not Ready. |


