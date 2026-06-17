---
title: UC Readiness Review — UC-EXBOT-agent-key (Submit and Approve HL Agent Key)
uc_id: UC-EXBOT-agent-key
feature: hl-agent-key
type: audited
date: 2026-06-17
author: qc-uc-read-exbot agent
version: v1
---

# Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC-EXBOT-agent-key — Nộp và phê duyệt HL agent key (mã hoá envelope AES-256-GCM)**

> Bản audited cho hệ thống logic / backend không UI (ExBot Worker + Admin dashboard). Đối chiếu chéo srs/ làm baseline → UC + user story.

---

## Bảng mã viết tắt (Reference code glossary)

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case của module ExBot (no-UI). Mỗi UC mô tả một luồng nghiệp vụ logic của bot (start / hedge-sync / agent-key / safe-close...). | `03_modules/exbot/usecases/` |
| US-EXBOT-* | User Story của module ExBot. Mỗi story gồm story statement + Gherkin AC. UC-EXBOT-agent-key gắn với US-EXBOT-011. | `03_modules/exbot/userstories/` |
| FR-EXBOT-* | Functional Requirement của module ExBot. Trong dự án này, FR-EXBOT có **hai bản** không trùng nhau (xem mâu thuẫn `IX-01`): `frd.md` chỉ định FR-EXBOT-080 = D1 Architecture, FR-EXBOT-081 = Agent Key Storage, không có 082 / 083; trong khi `srs/spec.md` chỉ định FR-EXBOT-080–083 đều cho agent-key (storage / approval / revocation / expiry). UC trace tới 080–083 theo cách hiểu của `srs/spec.md`. | `03_modules/exbot/frd.md` và `srs/spec.md` |
| BR-EXBOT-* | Business Rule của module ExBot. Trong UC này chỉ ghi nhãn `BR-EXBOT (FR-EXBOT-080, 081, 082, 083)` mà KHÔNG dẫn mã rule cụ thể, và `02_backbone/common-rules.md` không có rule nào prefix BR-EXBOT-080..083. Đây là một traceability gap. | `02_backbone/common-rules.md` |
| E-EXBOT-* | Error / message code của module ExBot, được khai báo **inline** trong `srs/spec.md §5` (E-EXBOT-001..013). **KHÔNG có** trong `02_backbone/message-list.md` — message-list chỉ liệt kê `bnza-ex` (sàn) chứ không đề cập `bnza-exbot`. Bot start với agent key hết hạn dùng `E-EXBOT-004`. | `srs/spec.md §5` (inline) |
| FM-XB-* | Feature Map của ExBot. `FM-XB-01` = D1 Schema (chứa bảng `hl_agent_keys`). `FM-XB-06` = API Endpoints (chứa `/api/exbot/agent-key`). `FM-XB-12` = Envelope Encryption (HL agent keys envelope). US-EXBOT-011 chỉ trace FM-XB-01, **không** trace FM-XB-12 — gap traceability. | `02_backbone/feature-map.md` |
| ACT-* | Actor canonical trong backbone. `ACT-01` = End User (LP) — tương ứng "USDC Investor" trong UC. `ACT-04` = Admin (zen) — tương ứng "ExBot Admin". `ACT-06` = OPERATOR (system) — tương ứng "ExBot Worker". UC không trích ACT-* tường minh. | `02_backbone/backbone.md` |
| AES-256-GCM | Advanced Encryption Standard, khoá 256-bit, chế độ Galois/Counter Mode — mã hoá symmetric có xác thực (AEAD). Trong UC này, agent key của user được mã hoá bằng AES-256-GCM với DEK riêng mỗi row; `secret_iv` (initialization vector) và `secret_auth_tag` (authentication tag chống tampering) lưu cùng `encrypted_secret`. | (industry term) |
| DEK | Data Encryption Key — khoá đối xứng dùng trực tiếp để mã hoá dữ liệu (ở đây là agent key). Trong UC này, DEK sinh ngẫu nhiên 256-bit per-row, mã hoá agent key xong sẽ được wrap bằng Master Key rồi xoá khỏi RAM. | (industry term) |
| Master Key | Khoá gốc lưu trong Cloudflare Secrets Store (KMS Cloudflare). Trong UC này, Master Key chỉ dùng để wrap / unwrap DEK — không trực tiếp chạm vào agent key. ExBot Worker được cấp quyền đọc Master Key qua binding của Cloudflare. | Cloudflare Secrets Store |
| Envelope encryption | Mô hình mã hoá hai tầng: DEK mã hoá data, Master Key (trong KMS) wrap DEK. Tách cấp quyền (access DEK ≠ access Master Key) và hỗ trợ rotate Master Key mà không phải re-encrypt toàn bộ data. UC này áp dụng envelope cho `hl_agent_keys`. | (industry term) |
| HL agent key | Hyperliquid agent key — khoá uỷ quyền (delegate) do user tạo trên HL để bot ký giao dịch perp thay mặt user mà KHÔNG cần master private key. Có thể bị revoke trên HL bất cứ lúc nào, có `expires_at`. | Hyperliquid documentation |
| SAFE_MODE | Trạng thái khẩn của bot: chặn mọi mutation (open / close / rebalance hedge, change leverage, withdraw margin), chỉ cho phép đọc state + retry kết nối HL + alert. Lifecycle state = `safe_mode`. | `srs/spec.md` FR-EXBOT-050 |
| OPERATOR / Facade | Worker public-facing của BNZA, expose `/api/exbot/*` rồi proxy sang ExBot Worker qua Cloudflare service binding (ExBot Worker không trực tiếp accessible từ Internet). | `srs/spec.md` FR-EXBOT-090 |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-agent-key mô tả quy trình **NĐT (USDC Investor) nộp HL agent key của mình cho hệ thống ExBot lưu trữ an toàn, sau đó được Admin phê duyệt trước khi bot có thể chạy**. Mục tiêu chính: ExBot Worker phải có agent key đã được Admin duyệt để ký order trên Hyperliquid thay mặt user, nhưng **không bao giờ được lưu master private key của user** dưới bất kỳ hình thức nào.

Luồng nghiệp vụ chính gồm ba pha: (1) NĐT submit agent key qua POOL UI gọi `POST /api/exbot/agent-key`; ExBot Worker tạo một DEK ngẫu nhiên 256-bit, mã hoá agent key bằng AES-256-GCM, sau đó wrap DEK bằng Master Key trong Cloudflare Secrets Store, lưu chỉ blob đã mã hoá vào bảng `hl_agent_keys` của `control_db` với `approval_status='pending'`; plain DEK và plain key bị destroy ngay sau khi chèn xong row. (2) Admin nhìn thấy key pending trong admin dashboard và bấm approve; ExBot Worker cập nhật `approval_status='approved'`, `approved_at=now`. (3) Sau khi đã approved và `expires_at` chưa qua, key đó sẽ pass được preflight check khi NĐT bấm "Start bot" (preflight check thuộc UC-EXBOT-bot-start, không phải UC này). Các luồng phụ gồm A1 — key hết hạn (block start với message "Agent key expired"), A2 — rotate key (insert row mới + đánh dấu row cũ revoked), A3 — sử dụng key khi hedge-sync (unwrap → decrypt → ký trong function scope → destroy ngay).

Rule quan trọng ảnh hưởng test design: (a) trong DB chỉ tồn tại blob đã mã hoá, dump D1 không thể recover plain key; (b) plain DEK / plain key chỉ tồn tại trong function scope, không log; (c) tối đa 1 row `approval_status='approved'` mỗi user; (d) row revoked không bị DELETE — giữ lại cho audit; (e) decryption fail trong hedge-sync phải đẩy bot vào SAFE_MODE thay vì leak key material. Các UC / module liên quan: UC-EXBOT-bot-start (preflight check 3), UC-EXBOT-hedge-sync (decrypt agent key ngay trước khi ký HL order), FM-XB-12 (Envelope Encryption), `bnza-pool` (POOL UI cung cấp form submit), `admin/bnza-admin` (admin dashboard cung cấp UI approve), Cloudflare Secrets Store (Master Key custody).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-agent-key | Submit and Approve HL Agent Key (AES-GCM envelope encryption) | draft (2026-06-12) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-12 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `03_modules/exbot/usecases/uc-agent-key.md` | 2026-06-12 (draft) | UC chính | Nguồn rà soát |
| `03_modules/exbot/usecases/index.md` | 2026-06-12 | UC index | Confirm Linked Stories + FR Trace |
| `03_modules/exbot/userstories/us-011.md` | 2026-06-12 (draft) | User story duy nhất gắn UC | 4 AC Gherkin |
| `03_modules/exbot/userstories/index.md` | 2026-06-12 | US index | Confirm mapping |
| `03_modules/exbot/srs/spec.md` | 2026-06-12 (v5.2.6) | SRS — baseline canonical (FR-EXBOT-080..083) | Source of truth chính |
| `03_modules/exbot/srs/states.md` | 2026-06-12 | State diagram | Bot lifecycle (không có state machine riêng cho hl_agent_keys) |
| `03_modules/exbot/srs/flows.md` | 2026-06-12 | Sequence flows | Không có flow riêng cho agent-key submit / approve |
| `03_modules/exbot/srs/erd.md` | 2026-06-12 | ERD | Schema `hl_agent_keys` (chi tiết) |
| `03_modules/exbot/frd.md` | (không có frontmatter version) | FRD | FR-EXBOT-080 / 081 mâu thuẫn với SRS (xem `IX-01`) |
| `02_backbone/common-rules.md` | — | Common BR registry | KHÔNG có BR-EXBOT-080..083 |
| `02_backbone/message-list.md` | 2026-06-09 | Message E-code registry | KHÔNG có E-EXBOT-*; chỉ có disclaimer cho `bnza-ex` |
| `02_backbone/feature-map.md` | — | Feature map | FM-XB-01 (D1 Schema), FM-XB-06 (API), FM-XB-12 (Envelope Encryption) |
| `02_backbone/backbone.md` | — | Actor + portal registry | ACT-01 / ACT-04 / ACT-06 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này tồn tại để giải quyết một bài toán bảo mật cốt lõi: **ExBot phải ký được giao dịch perpetual trên Hyperliquid thay mặt user, nhưng tuyệt đối không được phép giữ master private key của user**. Giải pháp là user tạo một "agent key" (khoá uỷ quyền) trên Hyperliquid, nộp khoá này cho hệ thống lưu trữ bằng envelope encryption hai tầng (per-row DEK + Master Key trong Cloudflare Secrets Store), sau đó Admin xác nhận bằng tay rằng đây là khoá hợp lệ trước khi cho phép bot dùng.

Kết quả nghiệp vụ mong đợi: (a) sau khi UC hoàn tất, NĐT có thể pass preflight check khi start bot; (b) dump D1 không thể recover plain agent key; (c) tổn thất tối đa nếu agent key bị lộ chỉ ở phạm vi quyền uỷ quyền trên HL (không lộ master key); (d) audit trail giữ lại lịch sử mọi key (kể cả đã revoked / superseded).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| F1 — Investor submit agent key | NĐT gọi `POST /api/exbot/agent-key` qua POOL UI → OPERATOR forward sang ExBot Worker | UC §3 step 1–2 |
| F2 — Server-side encryption (envelope) | ExBot Worker sinh DEK random 256-bit, mã hoá agent key bằng AES-256-GCM, wrap DEK bằng Master Key, ghi blob mã hoá vào `hl_agent_keys` với `approval_status='pending'` | UC §3 step 3–6; FR-EXBOT-080 (srs); FR-EXBOT-081 (frd) |
| F3 — Trả confirmation cho NĐT | Response "Agent key received and encrypted. Awaiting approval." | UC §3 step 7 |
| F4 — Admin approve key | Admin xem pending key → bấm approve → ExBot Worker set `approval_status='approved'`, `approved_at=now` | UC §3 step 8–9; FR-EXBOT-081 (srs) |
| F5 — Mở khoá preflight cho bot start | Sau khi approved + `expires_at` chưa qua, key dùng được trong preflight check 3 của UC-EXBOT-bot-start | UC §3 step 10; FR-EXBOT-002 (srs) |
| F6 — Key expired block start (A1) | Tại thời điểm preflight, nếu `expires_at < now` → block start với message "Agent key expired" | UC §4 A1; FR-EXBOT-083 (srs) |
| F7 — Key rotation (A2) | Insert row mới (DEK + wrap mới), row cũ chuyển `status='revoked'`, giữ `rotated_from` chain | UC §4 A2; FR-EXBOT-082 (srs) — **xung đột với srs §083 (superseded)**, xem `IX-04` |
| F8 — Decrypt khi hedge-sync (A3) | Unwrap `wrapped_dek` với Master Key → decrypt `encrypted_secret` → dùng plain key trong function scope → destroy ngay; không log | UC §4 A3; FR-EXBOT-080 (srs) |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Quy trình NĐT tạo agent key trên Hyperliquid | UC giả định "Investor has generated an HL agent key" trong precondition, không mô tả thao tác bên phía HL. | Test phải dùng agent key có sẵn (testnet); không thể test luồng tạo key. |
| Form submit agent key trong POOL UI | UC chỉ nhắc tên endpoint POST; module owner là `bnza-pool`. Trong SRS §6, POOL UI (PTL-05) chỉ "render ExBot status data" — không liệt kê tường minh form submit agent key. | Tester FE phải xác nhận với BA của module pool xem form đã specced chưa. |
| Admin dashboard UI approve key | UC chỉ nói "Admin sees pending key in admin dashboard"; module owner là `admin/bnza-admin`. Không cite screen ID nào. | Tester admin dashboard phải tìm spec ở module admin riêng. |
| Master Key rotation procedure | Schema có cột `encryption_key_version` (FR-EXBOT-080) nhưng UC + FRD + SRS không mô tả quy trình rotate Master Key (re-wrap các DEK cũ, ý nghĩa version). | Không thể test scenario rotate Master Key; cần xác nhận có nằm trong scope Phase A không. |
| Multi-sig / emergency approval path cho Admin | US-EXBOT-012 nhắc "emergency multi-sig path" nhưng UC-EXBOT-agent-key không mô tả. | Không thể design test cho multi-sig approval ở UC này. |
| Validation rằng key submit thực sự là agent key hợp lệ trên HL | UC chỉ encrypt và lưu, không nói có challenge ký thử / on-chain check trên HL hay không. | Có thể test happy path nhưng không test được "submit string rác → reject" nếu không có rule validation; xem `IX-08`. |
| Rejection path khi Admin từ chối approve | UC chỉ mô tả "Admin approves"; không nói nếu admin reject thì state là gì. Enum `approval_status` trong ERD chỉ có pending / approved / revoked / superseded. | Không thể design test cho admin reject scenario; xem `IX-12`. |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor (đối chiếu ACT-01 End User / LP) | Primary | Tạo agent key trên HL, submit qua POOL UI; có thể submit lại để rotate. | Có thể submit nhiều lần (mỗi lần insert row mới); chỉ 1 row tại một thời điểm có thể ở `approval_status='approved'`. UC không định nghĩa rate limit / cooldown giữa hai lần submit. | UC §1 + backbone.md `ACT-01` (UC không trích mã ACT) |
| ExBot Admin (đối chiếu ACT-04 Admin zen) | Primary | Approve key pending → chuyển sang approved. | UC không định nghĩa: admin nào được approve, có cần 2 người duyệt không, có rule reject không, ai chịu trách nhiệm. | UC §1 + backbone.md `ACT-04` (UC không trích mã ACT) |
| ExBot Worker | System | Sinh DEK, mã hoá / wrap, ghi DB, set approval_status, decrypt khi hedge-sync. | Chạy như Cloudflare Worker standalone, không lộ HTTP public; chỉ nhận request từ OPERATOR Facade qua service binding (`BR-EXBOT-010`). | UC §1, §3; FR-EXBOT-090 (srs) |
| D1 (control_db) | System | Persistent store cho `hl_agent_keys`. | Chỉ chứa blob đã mã hoá + metadata; không bao giờ chứa plain key. | UC §1; FR-EXBOT-080 (frd) |
| Cloudflare Secrets Store | External | Giữ Master Key; wrap / unwrap DEK. | ExBot Worker có quyền đọc Master Key qua binding. UC không định nghĩa failure mode khi Secrets Store unavailable. | UC §1; FR-EXBOT-080 / 081 (srs) |

**Nhận xét readiness:**
Actor list đã đủ rõ ở mức tên gọi để test design phân biệt được role gọi API nào, nhưng còn **3 gap lớn** ảnh hưởng tới việc thiết kế test theo role: (1) UC không trích mã `ACT-*` chuẩn nên khó cross-link với role matrix backbone — Junior QC mới vào dự án phải tự đoán "USDC Investor = ACT-01"; (2) endpoint `/api/exbot/agent-key` trong `frd.md` §FR-EXBOT-100 đánh dấu actor = "Admin" cho cả POST lẫn GET, mâu thuẫn với UC nói NĐT là người POST submit — không rõ phía OPERATOR có check role không, hay endpoint chấp nhận cả hai role với hành vi khác nhau (xem `IX-02`); (3) định nghĩa "ExBot Admin" chưa rõ là single role hay multi-sig, chưa có rule về quyền reject — Junior QC không biết phải mock account loại nào để test approval / reject (xem `IX-12`, `IX-13`).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | NĐT đã tạo một HL agent key trên Hyperliquid (delegate đã được approve trên HL, không phải master private key). | Yes | UC §2 |
| 2 | ExBot Worker có quyền đọc Master Key trong Cloudflare Secrets Store qua binding. | Yes | UC §2 |
| 3 | Bảng `hl_agent_keys` đã được migrate trong `control_db` (FM-XB-01). | Yes (suy luận từ FRD) | `frd.md` FR-EXBOT-080 |
| 4 | NĐT đã có row trong `users` (cần `users.id` để FK `hl_agent_keys.user_id`). | Yes (suy luận từ ERD) | `srs/erd.md` |
| 5 | Endpoint `/api/exbot/agent-key` đã được expose qua OPERATOR Facade và authenticated. | Yes (suy luận) | `srs/spec.md` FR-EXBOT-090 / `frd.md` FR-EXBOT-100 |
| 6 | NĐT đã set `expires_at` hợp lệ khi submit (hoặc hệ thống tự set theo policy mặc định). | TBD — **UC không nói rõ** | (Thiếu — xem `IX-07`) |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Submit thành công | Row mới trong `hl_agent_keys` với: `encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv` BLOB; `approval_status='pending'`; `approved_at=NULL`. NĐT nhận response "Agent key received and encrypted. Awaiting approval." | UC §3 step 6–7 + US-EXBOT-011 AC-1 |
| Admin approve thành công | Cùng row, `approval_status='approved'`, `approved_at=now`. NĐT có thể pass preflight check 3 khi start bot. | UC §3 step 9–10 + US-EXBOT-011 AC-2 |
| Rotate (A2) | Row mới với DEK + wrap mới, `approval_status='pending'` (hoặc 'approved' — UC không nói rõ, xem `IX-09`); row cũ chuyển `status='revoked'` (UC) hoặc `'superseded'` (srs FR-083) — mâu thuẫn xem `IX-04`; `rotated_from` trỏ tới row cũ. | UC §4 A2 + US-EXBOT-011 Notes + srs FR-082/083 |
| Sử dụng khi hedge-sync (A3) | Plain DEK + plain key chỉ tồn tại trong function scope; không entry log nào chứa plain key / plain DEK; row `hl_agent_keys` không thay đổi. | UC §4 A3 + US-EXBOT-011 AC-4 |
| Bot start với agent key đã expired | Start bị block bởi preflight check, message "Your HL agent key has expired. Please submit a new one." (E-EXBOT-004). Row cũ vẫn còn trong DB, KHÔNG bị xoá. | UC §4 A1 + US-EXBOT-011 AC-3 + `srs/spec.md` §5 E-EXBOT-004 + FR-EXBOT-083 |
| Admin reject (không trong UC) | **TBD — UC không định nghĩa.** Enum `approval_status` không có giá trị `'rejected'`. | (Thiếu — xem `IX-12`) |

**Lưu ý:** UC §6 "Business Rules" chỉ ghi nhãn `BR-EXBOT (FR-EXBOT-080, 081, 082, 083)` nhưng `02_backbone/common-rules.md` KHÔNG có rule nào với prefix `BR-EXBOT-080..083`. Toàn bộ rule định nghĩa nằm inline trong `srs/spec.md` §4 / FR-EXBOT-080..083, không được resolve qua mã BR riêng. Xem `IX-05`.

Message `"Your HL agent key has expired..."` được tham chiếu là `E-EXBOT-004` trong `srs/spec.md §5` (inline). `02_backbone/message-list.md` KHÔNG có E-EXBOT-* nào và cũng không có disclaimer cho `bnza-exbot` (chỉ có cho `bnza-ex`). Xem `IX-06`.

---

## 4 và ## 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Tên chức năng / luồng: F1+F2+F3 — Investor submit + server-side envelope encryption

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | USDC Investor | Submit agent key (form POOL UI) → `POST /api/exbot/agent-key {agent_key, agent_address, expires_at?}` (payload schema UC không định nghĩa rõ — xem `IX-10`) | OPERATOR Facade nhận request, validate auth token | — | Auth fail → 401/403 (UC không định nghĩa code; suy luận từ FR-EXBOT-090) | UC §3 step 1 |
| 2 | OPERATOR Facade | Forward request sang ExBot Worker qua Cloudflare service binding (internal token) | ExBot Worker nhận request | — | Service binding fail → 5xx (UC không định nghĩa) | UC §3 step 2; `srs/spec.md` FR-EXBOT-090 |
| 3 | ExBot Worker | Sinh DEK ngẫu nhiên 256-bit | DEK trong RAM | — | RNG fail → 5xx (UC không định nghĩa; nguồn entropy của Cloudflare Workers `crypto.getRandomValues` thực tế ổn định, nhưng vẫn nên có error path — xem `IX-11`) | UC §3 step 3 |
| 4 | ExBot Worker | `encrypted_secret = AES-256-GCM(plainKey, DEK, IV)`; sinh `secret_iv` (kích cỡ chuẩn 12 bytes — UC không nói rõ, xem `IX-15`), thu `secret_auth_tag` | Blob `encrypted_secret`, `secret_iv`, `secret_auth_tag` trong RAM | — | Encrypt fail → 5xx (UC không định nghĩa) | UC §3 step 4 |
| 5 | ExBot Worker | `wrapped_dek = MasterKey.wrap(DEK, dek_iv)` qua Cloudflare Secrets Store | Blob `wrapped_dek`, `dek_iv` trong RAM | — | Secrets Store unavailable → 5xx, UC không định nghĩa fallback (xem `IX-14`) | UC §3 step 5 |
| 6 | ExBot Worker | INSERT row vào `hl_agent_keys`: chỉ ghi blob mã hoá + metadata; xoá plain DEK + plain key khỏi RAM ngay | Row mới với `approval_status='pending'` | Nếu user đã có row pending khác cho cùng `agent_address` → UC không nói (dedup? overwrite?). Xem `IX-16` | DB INSERT fail → 5xx (UC không định nghĩa) | UC §3 step 6 |
| 7 | ExBot Worker → OPERATOR → NĐT | Response 200 "Agent key received and encrypted. Awaiting approval." | NĐT thấy notification "đang chờ duyệt" | — | — | UC §3 step 7 + US-EXBOT-011 AC-1 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Master private key never stored | Hệ thống tuyệt đối không lưu master private key, chỉ lưu agent key (delegate). | Yes | INSERT row với chỉ blob mã hoá agent key. | (Không có path cho master key — về mặt code phải reject mọi input dạng master key, nhưng UC không có rule validation phân biệt) — xem `IX-08`. | UC §2 + `srs/spec.md` FR-EXBOT-080; NFR-EXBOT-006 |
| Envelope encryption | AES-256-GCM với per-row DEK; DEK wrap bằng Master Key trong Cloudflare Secrets Store. | Yes | Row chứa `encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`. | Encrypt step fail → không INSERT, response 5xx (UC không nói rõ). | UC §3 step 4–6; `srs/spec.md` FR-EXBOT-080; `frd.md` FR-EXBOT-081 |
| Plain key / plain DEK function-scoped | Chỉ tồn tại trong function scope của step encrypt; destroy ngay sau khi INSERT xong. | Yes | Không log entry nào chứa plain key / plain DEK. | (Vi phạm là bug bảo mật — không có UC path cho nó nhưng test bắt buộc phải verify, NFR-EXBOT-006) | UC §3 step 6 + US-EXBOT-011 AC-4 + NFR-EXBOT-006 |
| `approval_status` enum | Chỉ các giá trị `'pending' / 'approved' / 'revoked' / 'superseded'` theo srs FR-082/083. | Yes (suy luận từ srs) | Row mới luôn ở `'pending'` sau submit. | (UC không nói có ràng buộc constraint DB không; ERD không show CHECK constraint cho enum này) | `srs/spec.md` FR-EXBOT-081/082/083; `srs/erd.md` |
| Chỉ 1 key approved mỗi user | DB-level enforced; insert row mới với `approval_status='approved'` khi đã có 1 row approved cho cùng user phải fail. | Yes | UNIQUE constraint reject. | UC không nói rõ tên constraint / message lỗi khi vi phạm. | `srs/spec.md` FR-EXBOT-082 (acceptance criteria) |
| Validate agent key format | UC không có rule. | TBD | — | — | (Thiếu — xem `IX-08`) |
| Rate limit submit | UC không có rule. | TBD | — | — | (Thiếu — xem `IX-17`) |

```text
[Diễn giải rule] Hệ thống chỉ lưu agent key (khoá uỷ quyền của user trên HL) ở dạng đã mã hoá bằng envelope encryption (per-row DEK mã hoá agent key, Master Key trong Cloudflare Secrets Store wrap DEK). Plain DEK / plain agent key chỉ tồn tại trong function scope của lời gọi mã hoá / giải mã, và phải bị destroy ngay sau khi dùng xong. Không bao giờ ghi log plain key. (Nguồn: srs FR-EXBOT-080; frd FR-EXBOT-081; NFR-EXBOT-006; trong UC: §3 step 4–6 + §4 A3. Mã `BR-EXBOT-080..083` được UC §6 nhắc tới nhưng KHÔNG có nội dung gốc trong `02_backbone/common-rules.md` — xem `IX-05`.)
```

#### C. Thông báo, lỗi và phản hồi hệ thống (API response / state change / event / message)

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Submit thành công | API response + state change | HTTP 200, body "Agent key received and encrypted. Awaiting approval."; state: row mới `approval_status='pending'` | (UC không gắn mã E-code cho thông điệp thành công) | UC §3 step 7 |
| Auth fail (OPERATOR Facade) | API error response | HTTP 401/403 (UC không định nghĩa code chính xác) | (Thiếu — xem `IX-10`) | Suy luận từ `srs/spec.md` FR-EXBOT-090 |
| Encryption / Secrets Store fail | API error response | HTTP 5xx; nội dung message UC không định nghĩa | (Thiếu — xem `IX-14`) | (Thiếu — xem `IX-14`) |
| User đã có row pending khác (duplicate) | UC không nói | (Thiếu) | (Thiếu — xem `IX-16`) | (Thiếu) |
| Validation fail (key sai format) | UC không nói | (Thiếu) | (Thiếu — xem `IX-08`) | (Thiếu) |

Nguyên tắc:
- Tester KHÔNG được suy ra error message cho các case "UC không nói"; phải để slot `(Thiếu)` cho BA confirm.
- Khi có mã E-code, phải resolve ra nội dung gốc. Trong UC này, message `"Your HL agent key has expired. Please submit a new one."` được mã hoá là `E-EXBOT-004` trong `srs/spec.md §5` — không có trong `02_backbone/message-list.md` (xem `IX-06`).

---

### 6.2 Tên chức năng / luồng: F4 — Admin approve key

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Admin | Mở admin dashboard, xem danh sách pending key | Dashboard list các row `approval_status='pending'`. (UI thuộc module admin riêng, không trong scope UC). | — | — | UC §3 step 8 |
| 2 | ExBot Admin | Bấm Approve một row pending | Dashboard gửi action approve sang OPERATOR Facade `/api/exbot/agent-key` (cách gọi cụ thể: method, payload — UC không nói rõ, xem `IX-02`) | Admin có thể bỏ qua / không approve → key giữ `pending` indefinitely (UC không định nghĩa SLA approve) — xem `IX-13` | OPERATOR forward fail → 5xx (UC không định nghĩa) | UC §3 step 9 |
| 3 | OPERATOR Facade | Forward sang ExBot Worker | ExBot Worker nhận lệnh approve | — | — | UC §3 step 9 (suy luận theo FR-EXBOT-090) |
| 4 | ExBot Worker | UPDATE row: `approval_status='approved'`, `approved_at=now()`. | Row cập nhật. | UC không định nghĩa rule "phải check key chưa expired tại thời điểm approve" — nếu admin approve một key có `expires_at < now`, hệ thống cho phép gì? (Xem `IX-18`) | Constraint vi phạm (đã có row approved khác cho cùng user) → UPDATE fail (UC không định nghĩa message lỗi) | UC §3 step 9; `srs/spec.md` FR-EXBOT-081 / 082 |
| 5 | Hệ thống | NĐT có thể pass preflight check 3 trong UC-EXBOT-bot-start | — | — | — | UC §3 step 10; `srs/spec.md` FR-EXBOT-002 / FR-EXBOT-081 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Chỉ 1 key approved / user | DB enforce. | Yes | Approve row mới → cần demote row cũ trước (UC §4 A2 nói row cũ chuyển 'revoked'; srs FR-083 nói 'superseded'). | UPDATE fail nếu cố approve 2 row cùng lúc cho cùng user (UC không có message). | `srs/spec.md` FR-EXBOT-082 |
| Approve key đã expired | UC không định nghĩa rule. | TBD | — | — | (Thiếu — xem `IX-18`) |
| Approver identity audit | ERD `hl_agent_keys` không có cột `approved_by`. | (gap) | — | — | (Thiếu — xem `IX-13`) |
| Reject action | UC + ERD không có. | (gap) | — | — | (Thiếu — xem `IX-12`) |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Approve thành công | State change | `approval_status` chuyển pending → approved; `approved_at=now`. (UC không định nghĩa response body cho admin). | (Thiếu) | UC §3 step 9 |
| Approve fail (vi phạm constraint 1-approved-per-user) | API error response | UC không định nghĩa. | (Thiếu) | (Thiếu) |
| Notification cho NĐT khi key được approve | UC không nói. | (Thiếu) | (Thiếu — xem `IX-19`) | (Thiếu) |

---

### 6.3 Tên chức năng / luồng: F6 — Key expired block preflight (A1)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | USDC Investor | Bấm start bot (UC-EXBOT-bot-start) | Preflight check 3: hệ thống đọc `hl_agent_keys WHERE user_id=? AND approval_status='approved'`, kiểm tra `expires_at >= now`. | — | — | UC §4 A1; `srs/spec.md` FR-EXBOT-002 / FR-EXBOT-083 |
| 2 | Hệ thống | Nếu `expires_at < now` → block start. | Trả message `E-EXBOT-004` "Your HL agent key has expired. Please submit a new one." HTTP 400. Row cũ KHÔNG bị xoá (US-EXBOT-011 AC-3). | — | — | UC §4 A1; `srs/spec.md` §5 E-EXBOT-004; FR-EXBOT-083 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `expires_at` check | `expires_at >= now` mới cho phép pass preflight. | Yes | Pass preflight 3. | Block start với E-EXBOT-004. | UC §4 A1; FR-EXBOT-083 |
| `expires_at` source | Cách đặt `expires_at`: user nhập, hay hệ thống tự set theo policy? UC không nói. | TBD | — | — | (Thiếu — xem `IX-07`) |
| Notification 7d trước hết hạn | FR-EXBOT-083 srs định nghĩa: deep-audit gửi notification khi `expires_at - now <= 7 days`. UC KHÔNG mô tả. | Yes (theo srs) | Notification "Your HL agent key expires in {N} days..." gửi qua `notification` queue. | — | UC (thiếu); `srs/spec.md` FR-EXBOT-083 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Key expired tại preflight | API error response + state | HTTP 400, "Your HL agent key has expired. Please submit a new one." | E-EXBOT-004 (inline trong `srs/spec.md` §5; KHÔNG trong `02_backbone/message-list.md`) | UC §4 A1; `srs/spec.md` §5 |
| Notification trước hết hạn (7d) | Notification queue | "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." | (Không có E-code) | `srs/spec.md` FR-EXBOT-083 |

---

### 6.4 Tên chức năng / luồng: F7 — Key rotation (A2)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | USDC Investor | Submit key mới qua POST endpoint | Như F1+F2+F3 (insert row mới `approval_status='pending'`). | — | — | UC §4 A2 |
| 2 | ExBot Admin | Approve key mới | Row mới chuyển `approved`. **Đồng thời** row cũ phải chuyển — UC nói `status='revoked'`; srs FR-EXBOT-083 nói `status='superseded'` (atomically với row mới approved). MÂU THUẪN — xem `IX-04`. | — | — | UC §4 A2 + US-011 Notes; `srs/spec.md` FR-EXBOT-082 / FR-EXBOT-083 |
| 3 | ExBot Worker | Set `rotated_from` của row mới trỏ tới row cũ (chain preserved). | Chain audit giữ lại. | — | — | UC §4 A2; `srs/erd.md` `hl_agent_keys.rotated_from` |
| 4 | Hệ thống | Trong window giữa submit và approve, key cũ vẫn active để bot không bị gián đoạn (theo srs FR-EXBOT-083). UC không nói rõ điểm này. | Bot tiếp tục dùng key cũ cho hedge-sync. | UC §4 A2 chỉ ghi "old row set to status='revoked'" mà không tách rõ "khi nào" — trước hay sau khi admin approve. | — | UC §4 A2 (mập mờ); `srs/spec.md` FR-EXBOT-083 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Old row status sau rotate | UC: `'revoked'`; srs FR-083: `'superseded'`. | (mâu thuẫn) | — | — | (Mâu thuẫn — xem `IX-04`) |
| Old row vẫn hoạt động trong window pending → approved | srs: có. UC: không nói. | (UC thiếu) | — | — | (Thiếu — xem `IX-09`) |
| DELETE row revoked / superseded | srs FR-082: FORBIDDEN (audit). | Yes | Row giữ lại. | DELETE bị reject. | `srs/spec.md` FR-EXBOT-082 |

#### C. Thông báo

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Rotate thành công | State change | Hai row tồn tại: row cũ revoked/superseded, row mới approved. | (Thiếu message cụ thể) | UC §4 A2 |

---

### 6.5 Tên chức năng / luồng: F8 — Decrypt khi hedge-sync (A3)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Worker (hedge-sync worker) | Đến bước ký HL order, fetch row `hl_agent_keys` của user theo `users.hl_agent_key_id` | Có blob mã hoá. | Row đã chuyển `revoked` / `superseded` / expired → decrypt sẽ fail policy → SAFE_MODE (srs FR-082). UC §4 A3 không nói rõ. | — | UC §4 A3; `srs/erd.md`; `srs/spec.md` FR-EXBOT-082 |
| 2 | ExBot Worker | Unwrap `wrapped_dek` bằng Master Key | Plain DEK trong RAM (function scope). | — | Cloudflare Secrets Store unavailable → fail (UC không có path); srs FR-082 nói decryption failure trong hedge-sync → SAFE_MODE. | UC §4 A3; `srs/spec.md` FR-EXBOT-082 |
| 3 | ExBot Worker | AES-256-GCM decrypt `encrypted_secret` với DEK + IV + auth tag → plain agent key | Plain agent key trong RAM. | Auth tag mismatch (data corruption / tampering) → decryption fail → SAFE_MODE. UC không nói. | — | UC §4 A3; `srs/spec.md` FR-EXBOT-082 |
| 4 | ExBot Worker | Dùng plain agent key để ký HL order | HL nhận order. | — | — | UC §4 A3 (gián tiếp); UC-EXBOT-hedge-sync (UC riêng) |
| 5 | ExBot Worker | Destroy plain DEK + plain agent key khỏi memory ngay sau khi dùng | Không log entry nào chứa plain key. | — | — | UC §4 A3; US-011 AC-4; NFR-EXBOT-006 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Plain key function-scoped | Plain key + DEK destroy ngay sau khi ký. | Yes | Không log / persist plain key. | (Vi phạm là bug bảo mật) | UC §4 A3; NFR-EXBOT-006 |
| Decryption fail handling | srs FR-082: SAFE_MODE. UC không nói. | Yes (theo srs) | Hedge-sync abort, bot vào SAFE_MODE, log error KHÔNG chứa key material. | — | `srs/spec.md` FR-EXBOT-082 |
| Audit tag verification | UC không nói. | (Thiếu) | — | — | (Thiếu — xem `IX-15`) |

#### C. Thông báo

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Decryption fail | State change + log | Bot chuyển `lifecycle_state='safe_mode'`; log không chứa key material; UC không định nghĩa message cụ thể cho NĐT/admin. | (Thiếu) | `srs/spec.md` FR-EXBOT-082 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Submit + approve agent key (UC-EXBOT-agent-key) | UC-EXBOT-bot-start preflight check 3 | Nếu không có key approved + chưa hết hạn, bot KHÔNG start được. | `bots` row mới chỉ tạo khi preflight pass — không có partial bot record nếu fail preflight (`srs/spec.md` FR-EXBOT-002 AC). Cross-check: `users.hl_agent_key_id` phải trỏ tới đúng row approved hiện tại của user. | UC §3 step 10; `srs/spec.md` FR-EXBOT-002 / 081 |
| Decrypt agent key (A3) | UC-EXBOT-hedge-sync (mọi HL mutation) | Mọi lần hedge-sync phải decrypt key để ký order. Decryption fail → bot vào SAFE_MODE (srs FR-082). | `hl_agent_keys.approval_status` không bị mutate bởi hedge-sync. State bot chuyển sang `safe_mode` qua `bots.lifecycle_state`. | UC §4 A3; `srs/spec.md` FR-EXBOT-082; flows.md F-02 |
| Rotate key (A2) | UC-EXBOT-hedge-sync trong window submit → approve | srs FR-083: trong window này, key cũ vẫn active để bot không gián đoạn. UC §4 A2 không nói rõ — gây mơ hồ về thời điểm `revoked`. | Cross-check: tại mọi thời điểm chỉ có ≤1 row approved cho cùng user (DB constraint). | UC §4 A2; `srs/spec.md` FR-EXBOT-082 / 083 |
| Key expired + notification 7d | UC-EXBOT-light-check (không) / `deep-audit` cron | Deep-audit cron (mỗi 6h hoặc 1h ở high-risk) scan `hl_agent_keys.expires_at`, gửi notification qua `notification` queue khi còn ≤7 ngày. UC không mô tả luồng này. | Cross-check: notification queue có message với template "expires in {N} days". | `srs/spec.md` FR-EXBOT-083 |
| Decrypt fail → SAFE_MODE | UC-EXBOT-hedge-sync, circuit_breakers, deep-audit | Bot dừng mọi mutation; light-check (no HL) tiếp tục; auto-recovery khi HL responsive + 3 reconcile pass + margin ok (`srs/spec.md` FR-EXBOT-050). Nếu không recover được → `bot_safe_close` → cooldown re-entry loop. | Cross-check: `bots.status='safe_mode'`, `bots.lifecycle_state='safe_mode'`; circuit không bắt buộc open. | `srs/spec.md` FR-EXBOT-050 / 082 |
| Admin force-close (UC-EXBOT-bot-safe-close) | hl_agent_keys không bị ảnh hưởng | Force-close không revoke key. | Row `hl_agent_keys` giữ nguyên — key còn dùng được nếu user re-start bot sau cooldown. | `srs/spec.md` FR-EXBOT-072 |

Gợi ý phân tích bổ sung:
- Dữ liệu được tạo trong UC này (row `hl_agent_keys`) được đọc bởi: preflight check (FR-EXBOT-002 / 081), hedge-sync worker (decrypt), deep-audit cron (expiry scan). Tất cả phải được test khi `approval_status` thay đổi.
- Trạng thái `revoked` / `superseded` ảnh hưởng tới quyền start bot — phải verify cross-link giữa `hl_agent_keys.approval_status` và `users.hl_agent_key_id`.
- Bot đang chạy mà key chủ động bị revoke (UC §4 A2) → hedge-sync kế tiếp decrypt key đã revoke → SAFE_MODE. Luồng này UC không vẽ explicit nhưng srs FR-082 acceptance criteria có.

---

## 8. Acceptance Criteria

Nguồn AC chính lấy từ US-EXBOT-011. Mỗi AC dưới là format Given/When/Then có thể test được; AC suy luận đánh dấu `Suy luận cần xác nhận`.

| AC # | Scenario | Given — điều kiện | When — hành động | Then — kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — agent key submit + lưu mã hoá | NĐT đã có agent key trên HL; user_id tồn tại; bảng `hl_agent_keys` đã migrate | NĐT submit key qua `POST /api/exbot/agent-key` | Row mới chèn vào `hl_agent_keys` với chỉ blob mã hoá (`encrypted_secret`, `wrapped_dek`, `secret_iv`, `secret_auth_tag`, `dek_iv`); `approval_status='pending'`; response 200 "Agent key received and encrypted. Awaiting approval." | US-EXBOT-011 AC-1 |
| AC-02 | Happy path — admin approve unlock bot start | Row pending tồn tại cho user X | Admin approve key qua admin dashboard | `approval_status='approved'`, `approved_at=now`. NĐT pass được preflight check 3 khi start bot (sang luồng UC-EXBOT-bot-start). | US-EXBOT-011 AC-2 |
| AC-03 | Edge — key hết hạn block start | Row approved của user X có `expires_at < now` | Preflight check chạy khi NĐT bấm start | Start bị block với message "Your HL agent key has expired. Please submit a new one." (mã `E-EXBOT-004` theo `srs/spec.md §5`). Row KHÔNG bị xoá. | US-EXBOT-011 AC-3 |
| AC-04 | Negative — plain key không xuất hiện trong log / DB | Worker decrypt agent key để ký HL order | Signing operation hoàn tất | Plain DEK + plain agent key bị destroy (function scope only); không entry log nào chứa raw key / raw DEK; row `hl_agent_keys` vẫn chỉ chứa blob mã hoá. | US-EXBOT-011 AC-4; NFR-EXBOT-006 |
| AC-05 | Suy luận cần xác nhận — chỉ 1 key approved / user | User X đã có 1 row `approval_status='approved'`. | Admin approve một row khác cho cùng user X | UPDATE bị reject bởi DB constraint; OR row cũ phải chuyển `'revoked'` (UC) hoặc `'superseded'` (srs) atomically. **Mâu thuẫn UC vs srs — Suy luận cần xác nhận, xem `IX-04`.** | UC §4 A2; `srs/spec.md` FR-EXBOT-082 / 083 |
| AC-06 | Suy luận cần xác nhận — rotate (A2) giữ chain | User X submit key mới khi đã có 1 key approved | Submit + admin approve | Row mới `approval_status='approved'`, `rotated_from` trỏ tới row cũ; row cũ chuyển `revoked` / `superseded` (xem `IX-04`); KHÔNG được DELETE row cũ (srs FR-082). | UC §4 A2; US-011 Notes; `srs/spec.md` FR-EXBOT-082 |
| AC-07 | Suy luận cần xác nhận — decrypt fail trong hedge-sync → SAFE_MODE | Hedge-sync chạy nhưng row đã revoked / data corruption / Secrets Store unavailable | Worker thử decrypt | Decryption fail; bot chuyển `lifecycle_state='safe_mode'`; log error nhưng không chứa key material. **Suy luận từ `srs/spec.md` FR-EXBOT-082 — UC §4 A3 KHÔNG nói rõ.** | `srs/spec.md` FR-EXBOT-082 |
| AC-08 | Suy luận cần xác nhận — notification 7d trước hết hạn | Deep-audit cron scan `hl_agent_keys.expires_at` và phát hiện `expires_at - now <= 7 days` | Cron tick | Message "Your HL agent key expires in {N} days. Submit a new key to avoid bot interruption." được enqueue vào `notification` queue. **Suy luận từ `srs/spec.md` FR-EXBOT-083 — UC KHÔNG nói.** | `srs/spec.md` FR-EXBOT-083 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | UC không định nghĩa SLA cho submit / approve. (Có thể suy luận theo NFR-EXBOT-002 ≤30s, nhưng NFR này dành cho hedge-sync, không phải agent-key.) | Không có ngưỡng cụ thể để test performance — đặt câu hỏi cho BA. (Xem `IX-20`) | UC (thiếu); `srs/spec.md` NFR-EXBOT-002 |
| Security | Master private key never stored. Agent key AES-256-GCM envelope (per-row DEK + Master Key trong Cloudflare Secrets Store). Plain key function-scope only, không log. | Bắt buộc test: dump D1 không có plain key; log audit không có plain key; rotate Master Key không break các DEK cũ (procedure UC không định nghĩa — xem `IX-21`). | `srs/spec.md` FR-EXBOT-080 / NFR-EXBOT-006 |
| Reliability / Resilience | Cloudflare Secrets Store unavailability handling chưa có. Decryption fail → SAFE_MODE (srs FR-082) nhưng UC không nói. | Test resilience scenarios bị thiếu input. | (Thiếu — xem `IX-14`) |
| Audit / Logging | UC §3 step 6 nói "nothing logged" cho plain key. Nhưng UC không nói có audit log riêng cho hành vi (submit / approve / revoke / rotate) hay không. ERD `hl_agent_keys` không có cột `approved_by`. | Tester không biết có audit trail không — không thể design test traceability. | UC §3 (thiếu); `srs/erd.md` (xem `IX-13`) |
| Privacy / Compliance | Master private key never stored. Revoked row giữ lại cho audit (srs FR-082). | Verify DELETE bị reject. | `srs/spec.md` FR-EXBOT-082 |
| Compatibility / Integration | OPERATOR Facade ↔ ExBot Worker qua Cloudflare service binding (internal token). ExBot Worker không HTTP public (FR-EXBOT-090). | Test: direct HTTP request tới ExBot Worker phải 403. | `srs/spec.md` FR-EXBOT-090 |

Một số NFR canonical liên quan (đã trích từ `srs/spec.md` §3):
- NFR-EXBOT-006: Master private key never stored. Agent key AES-256-GCM envelope. Plain key function-scope only, never logged. (P0)
- NFR-EXBOT-011: Max 6 simultaneous outbound connections per CF Worker invocation. (Áp dụng nếu hedge-sync decrypt phải gọi Cloudflare Secrets Store cùng với HL — cần xác nhận.)

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| IX-01 | High | CROSS_SOURCE_CONFLICT | UC §7 "FR Trace: FR-EXBOT-080–083"; `frd.md` §FR-EXBOT-080 (D1 Architecture) / FR-EXBOT-081 (Agent Key Storage), KHÔNG có 082 / 083; `srs/spec.md` FR-EXBOT-080–083 (đều agent-key) | Bảng mã FR-EXBOT trong `frd.md` và `srs/spec.md` KHÔNG khớp về nội dung. UC trace tới 080–083 nhưng nếu tester mở `frd.md` đúng các mã này họ sẽ thấy D1 Architecture và Agent Key Storage (chỉ 2 mã), không thấy revocation / expiry. BA vui lòng xác nhận: bản nào là canonical, có cần re-number FR trong `frd.md` cho khớp `srs/spec.md` không, hoặc UC cần đổi FR Trace? | Tester không thể trace test cases về một bộ FR ổn định; risk thiết kế test sót Revocation (FR-082 srs) và Expiry handling (FR-083 srs) vì không có trong FRD. | BA + Tech Lead | Open |
| IX-02 | High | UNCLEAR_INFO + CROSS_SOURCE_CONFLICT | UC §3 step 1 (NĐT POST submit); `frd.md` §FR-EXBOT-100 (`/api/exbot/agent-key` actor = Admin); `srs/spec.md` §FR-EXBOT-090 (cùng endpoint, không phân biệt role); UC §3 step 9 (Admin approve) | Endpoint `/api/exbot/agent-key` được dùng cho cả NĐT submit (POST) và Admin approve. `frd.md` đánh nhãn actor = Admin cho cả endpoint, mâu thuẫn với UC nói NĐT POST. BA vui lòng xác nhận: (a) endpoint này có RBAC tách hai sub-action (submit / approve) không, hay phải tách hai endpoint khác nhau; (b) payload schema submit (chứa gì), payload approve (chứa gì); (c) HTTP code khi user gọi sai sub-action / sai role. | Tester FE và BE cần payload schema rõ ràng để mock; tester admin cần biết RBAC để design negative test (NĐT cố gọi approve). | BA + Tech Lead | Open |
| IX-03 | Medium | MISSING_INFO | UC §1 + §3; `02_backbone/backbone.md` ACT-01 / ACT-04 | UC không trích mã `ACT-*` chuẩn cho "USDC Investor" và "ExBot Admin"; Junior QC phải tự đoán mapping. BA vui lòng cập nhật UC §1 trích mã ACT canonical (ACT-01 / ACT-04) hoặc xác nhận mapping khác. | Mapping role thiếu rõ → test plan theo role có thể chọn nhầm account / permission. | BA | Open |
| IX-04 | High | INTERNAL_INCONSISTENCY | UC §4 A2 ("old row set to status='revoked'") + US-011 Notes (cùng wording); `srs/spec.md` FR-EXBOT-083 ("old approved row transitions to status='superseded'") | Hai nguồn dùng hai giá trị enum khác nhau cho row cũ sau rotation: UC + US dùng `'revoked'`, srs FR-083 dùng `'superseded'`. ERD `hl_agent_keys.approval_status` không khai enum rõ ràng. BA vui lòng chốt: enum chính xác là gì, ý nghĩa `revoked` vs `superseded` (theo srs FR-082 `revoked` là user request / admin action; `superseded` chỉ dành cho rotation). UC + US cần cập nhật theo? | Tester không biết expected value để verify post-condition; auto test sẽ fail vì DB schema có thể CHECK constraint khác wording. | BA + Tech Lead | Open |
| IX-05 | High | MISSING_INFO (traceability) | UC §6 "BR-EXBOT (FR-EXBOT-080, 081, 082, 083)"; `02_backbone/common-rules.md` (không có BR-EXBOT-080..083) | UC chỉ ghi nhãn `BR-EXBOT (FR-...)` mà KHÔNG cite mã BR cụ thể, và `02_backbone/common-rules.md` không có rule nào prefix BR-EXBOT-080..083. Toàn bộ rule chỉ tồn tại inline trong `srs/spec.md`. BA vui lòng xác nhận: (a) module ExBot có dùng BR-EXBOT-* registry không, hay rule được inline trong SRS; (b) nếu có, đăng ký BR-EXBOT-080..083 vào `common-rules.md` để cite được. | Tester không thể resolve BR-EXBOT-* để biết wording chính thức; mọi rule phải đọc bằng tay trong SRS spec — tốn thời gian + risk hiểu sai. | BA | Open |
| IX-06 | High | MISSING_INFO (traceability) | `srs/spec.md` §5 (E-EXBOT-001..013 inline); `02_backbone/message-list.md` (không có E-EXBOT-*); message-list disclaimer chỉ cho `bnza-ex` | E-EXBOT-* codes được khai báo inline trong `srs/spec.md §5` nhưng KHÔNG có trong `02_backbone/message-list.md`, và message-list không có disclaimer cho `bnza-exbot`. BA vui lòng xác nhận: (a) E-EXBOT-* có cần register vào `message-list.md` không (đồng nhất với MOB / POOL / ADM / WLA); (b) hoặc thêm disclaimer "bnza-exbot dùng inline matrix tại `srs/spec.md §5`" như đã làm với `bnza-ex`. | Tester không tìm thấy message wording khi search message-list; risk dùng sai message / sót message. | BA | Open |
| IX-07 | High | MISSING_INFO | UC §3 step 1 (payload UC không liệt kê); `srs/erd.md` `hl_agent_keys.expires_at`; `srs/spec.md` FR-EXBOT-083 | UC không định nghĩa **nguồn của `expires_at`**: user nhập tay khi submit? Hệ thống tự set theo policy (ví dụ now + 90 days)? Lấy từ HL (HL agent key có expiry on-chain)? BA vui lòng xác nhận policy + format. | Không biết policy thì không design được test cho A1 (expired block), test rotation, và test notification 7d. | BA + Tech Lead | Open |
| IX-08 | High | MISSING_INFO | UC §3 step 4 (mã hoá "plainKey" — không nói plainKey là gì) | UC không định nghĩa **quy trình validate agent key trước khi mã hoá**: (a) format string của HL agent key (length, prefix, base64 / hex / 0x-prefixed bytes); (b) check on-chain trên HL xem key có thực sự là delegate đã active của user không; (c) check không phải master private key (UC §2 nói "approved delegate, not master private key" nhưng không có rule reject). BA vui lòng định nghĩa validation rule + message lỗi khi sai format. | Submit string rác sẽ được encrypt và lưu, sau đó decryption thành công nhưng HL reject signing → tốn round-trip + bot vào SAFE_MODE. Tester không design được negative test cho input invalid. | BA + Tech Lead | Open |
| IX-09 | Medium | UNCLEAR_INFO | UC §4 A2 ("New row inserted (new DEK + new wrap); old row set to status='revoked'") | UC §4 A2 không nói rõ **thời điểm** old row chuyển sang revoked: ngay khi row mới submit (`pending`) hay phải đợi admin approve row mới? srs FR-EXBOT-083 nói rõ "the existing approved key remains active... until admin approves the replacement", thì UC §4 A2 phải cập nhật theo. BA vui lòng làm rõ. | Window submit→approve có dài (admin tay), nếu old key bị revoke ngay khi user submit thì bot đang chạy sẽ vào SAFE_MODE — hành vi không mong muốn. Tester cần biết để test. | BA | Open |
| IX-10 | High | MISSING_INFO | UC §3 step 1 (chỉ tên endpoint, không có payload spec) | UC không định nghĩa **API contract** cho `POST /api/exbot/agent-key`: request schema (required / optional fields), response schema cho success / lỗi, HTTP status code cho từng case. BA vui lòng cung cấp hoặc trỏ tới file API contract canonical. | Tester BE và Tester FE không có nguồn ground truth để test → phải đoán dựa trên code, dễ sai. | BA + Tech Lead | Open |
| IX-11 | Low | MISSING_INFO | UC §3 step 3 ("generates a per-row DEK (random, AES-256)") | UC không nói rõ **nguồn entropy** của DEK random. Cloudflare Workers cung cấp `crypto.getRandomValues` đạt cryptographic strength — nên xác nhận đây là API được dùng và document trong UC. | Tester security cần biết để có check trong code review (không dùng `Math.random()`). | Tech Lead | Open |
| IX-12 | High | MISSING_INFO | UC §3 step 8–9 (chỉ approve); `srs/erd.md` enum `approval_status` (không có `'rejected'`) | UC không định nghĩa **luồng admin reject** khi xem pending key thấy có vấn đề (ví dụ key không hợp lệ, user submit nhầm). Enum hiện tại không có `'rejected'`. BA vui lòng xác nhận: (a) có hỗ trợ reject không; (b) nếu có, state transition + message cho NĐT; (c) nếu không, lý do (admin chỉ approve hoặc bỏ qua đến khi user re-submit?). | Tester không design được test admin reject; nếu sau này code thêm `rejected` state sẽ không có spec để verify. | BA + Tech Lead | Open |
| IX-13 | High | MISSING_INFO (audit) | `srs/erd.md` `hl_agent_keys` (không có `approved_by`); UC §3 step 9 | UC + ERD không có cột `approved_by` để biết Admin nào đã approve, cũng không nói thời gian Admin được expect approve trong bao lâu (SLA). BA vui lòng xác nhận: (a) cần audit trail approver_id không (compliance); (b) SLA approve để có notify nếu trễ. | Không thể trace ai đã approve nếu sau này có vấn đề bảo mật — risk compliance. | BA | Open |
| IX-14 | High | MISSING_INFO | UC §3 step 5 (wrap qua Cloudflare Secrets Store); UC §4 A3 | UC không định nghĩa **failure mode khi Cloudflare Secrets Store unavailable**: (a) lúc submit (encrypt fail) → HTTP code và message; (b) lúc hedge-sync (decrypt fail) → srs FR-082 nói SAFE_MODE nhưng UC không nói rõ. BA vui lòng định nghĩa hành vi để test resilience. | Resilience test thiếu spec → tester phải tự đoán. Risk: production fail Secrets Store sẽ không có expected behavior để verify. | BA + Tech Lead | Open |
| IX-15 | Medium | UNCLEAR_INFO | UC §3 step 4 (chỉ "AES-256-GCM(plainKey, DEK, IV)"); `srs/erd.md` `secret_iv` BLOB | UC không định nghĩa: (a) IV length (chuẩn AES-GCM là 12 bytes — phải confirm); (b) IV uniqueness policy (mỗi mã hoá phải có IV mới — verify code không reuse); (c) `secret_auth_tag` length (16 bytes mặc định). BA / Tech Lead vui lòng xác nhận để tester security verify đúng. | IV reuse trong AES-GCM phá vỡ bảo mật — phải test verify; nếu spec không có, tester không biết expected. | Tech Lead | Open |
| IX-16 | Medium | MISSING_INFO | UC §3 step 6 | UC không định nghĩa hành vi khi **user đã có row `approval_status='pending'`** mà submit thêm lần nữa: (a) insert row pending thứ hai; (b) reject với "đang chờ duyệt rồi"; (c) overwrite. Cũng không có rule rate-limit. BA vui lòng xác nhận. | Risk bot bị spam submit → admin dashboard ngập row pending; tester cần spec để verify. | BA | Open |
| IX-17 | Medium | MISSING_INFO | UC §3 step 1 (không có rate limit) | UC không định nghĩa **rate limit / brute force protection** cho endpoint submit. BA vui lòng xác nhận: (a) có rate limit per user / per IP không; (b) ngưỡng. | Security test (DoS / abuse) thiếu spec; risk endpoint bị abuse. | BA + Tech Lead | Open |
| IX-18 | Medium | MISSING_INFO | UC §3 step 9 (admin approve) | UC không định nghĩa **rule khi admin approve key đã expired**: cho phép approve (key vô dụng từ đầu) hay reject? BA vui lòng xác nhận. | Test admin approve flow thiếu negative case. | BA | Open |
| IX-19 | Low | MISSING_INFO | UC §3 step 9 (không có notification) | UC không định nghĩa **notification cho NĐT khi key được approve**. NĐT phải tự refresh dashboard hay nhận thông báo proactive? BA vui lòng xác nhận. | UX gap — tester UX không có expected để verify. | BA | Open |
| IX-20 | Low | MISSING_INFO | UC §9 (UC không có section 9 trong template ExBot); `srs/spec.md` NFR-EXBOT-* | UC không định nghĩa **SLA cho submit + admin approve**: thời gian response của API submit, thời gian từ pending → approved (admin SLA). BA vui lòng xác nhận. | Test performance + SLA thiếu ngưỡng. | BA | Open |
| IX-21 | Medium | MISSING_INFO | `frd.md` FR-EXBOT-080 (cột `encryption_key_version`); UC + srs không có procedure | Schema có `hl_agent_keys.encryption_key_version` nhưng UC + FRD + SRS không định nghĩa **quy trình rotate Master Key**: re-wrap các DEK cũ với Master Key mới? Version semantics? BA / Tech Lead vui lòng xác nhận có nằm trong Phase A scope không. | Nếu Phase A scope thì cần thêm test cases; nếu không, phải document rõ là Phase B+. | Tech Lead | Open |
| IX-22 | Low | MISSING_INFO (traceability) | US-EXBOT-011 frontmatter `source_backbone_ids: [FM-XB-01]`; `feature-map.md` FM-XB-12 (Envelope Encryption) | US-EXBOT-011 chỉ trace FM-XB-01 (D1 Schema), bỏ sót FM-XB-12 (Envelope Encryption) — feature trọng tâm của UC này. BA vui lòng cập nhật trace. | Traceability matrix sai lệch — risk test coverage không gắn được với feature canonical. | BA | Open |
| IX-23 | Medium | MISSING_INFO | UC §4 A3 + `srs/spec.md` FR-EXBOT-082 | UC không định nghĩa **expiry handling notification cho NĐT trong UC này**. Toàn bộ logic notification 7d trước hết hạn nằm trong srs FR-EXBOT-083 — UC §4 chỉ có A1 (block start khi đã hết hạn) chứ không có proactive warning. BA vui lòng bổ sung vào UC để testers thấy được scope đầy đủ. | Coverage gap — tester có thể bỏ qua test notification 7d nếu chỉ đọc UC. | BA | Open |
| IX-24 | Low | INTERNAL_INCONSISTENCY | UC tiêu đề "UC-EXBOT-agent-key-approval"; index + filename "UC-EXBOT-agent-key" | Filename + index dùng `UC-EXBOT-agent-key` nhưng heading body dùng `UC-EXBOT-agent-key-approval`. BA vui lòng đồng nhất một ID duy nhất. | Nhỏ — gây nhầm lẫn trace. | BA | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| Cloudflare Secrets Store (Master Key custody) | Integration | Toàn bộ submit (wrap) + hedge-sync (unwrap) phụ thuộc; downtime → submit / hedge-sync fail. | Tech Lead / Cloudflare ops | Open |
| `bnza-pool` module — POOL UI form submit agent key | UC / Module | UC nói "via POOL UI" nhưng form chưa được chỉ định trong SRS POOL hay không — cần xác nhận với BA module pool. | BA module pool | Open |
| `admin/bnza-admin` module — admin dashboard approve UI | UC / Module | UC nói "admin dashboard" nhưng không cite screen ID — cần xác nhận với BA admin module. | BA module admin | Open |
| `02_backbone/common-rules.md` — BR-EXBOT-* registration | Common rule | Hiện chưa có BR-EXBOT-080..083; cần đăng ký để cite được. (Xem `IX-05`.) | BA | Open |
| `02_backbone/message-list.md` — E-EXBOT-* registration | Common rule | Hiện chưa có E-EXBOT-* hoặc disclaimer; cần đăng ký. (Xem `IX-06`.) | BA | Open |
| `frd.md` ↔ `srs/spec.md` FR-EXBOT-080..083 alignment | Cross-source | Hai bộ FR mâu thuẫn — cần re-number hoặc thống nhất nguồn canonical. (Xem `IX-01`.) | BA + Tech Lead | Open |
| API contract canonical cho `/api/exbot/agent-key` | Integration | Chưa có schema rõ ràng. (Xem `IX-02`, `IX-10`.) | Tech Lead | Open |
| HL agent key generation flow on user side | External | UC giả định user đã có key — không nằm trong scope BNZA test. | Hyperliquid documentation | — |

### 10.3 Audit Summary

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---:|---:|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 13 | ⚠️ Partial | Functions / data object / fields được liệt kê tương đối đầy đủ (UC + srs ERD). Trừ điểm vì: (a) `IX-10` thiếu API contract canonical → operations underspecified; (b) `IX-08` thiếu validation rule cho input; (c) enum `approval_status` không liệt kê đầy đủ trong UC (chỉ rõ trong srs FR-082/083). |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 11 | ⚠️ Partial | Trừ mạnh do auto-cap (xem dưới): (a) `IX-01` cross-source conflict FR numbering — wording rules / acceptance criteria khác nhau giữa FRD và SRS, cap §10.b ("UC có unresolved contradiction across sources" → Area 2 ≤70% = 17.5, kết hợp với gap cá nhân kéo xuống); (b) `IX-04` enum revoked vs superseded; (c) `IX-05` BR-EXBOT không có trong common-rules.md; (d) `IX-06` E-EXBOT không có trong message-list.md; (e) `IX-12` thiếu rejection state. Blockchain checklist B1 (key states + messages) — partial: states có nhưng wording mâu thuẫn; B8 (resolved messages) — fail (E-codes inline không resolve được qua registry chuẩn). |
| 3 | Functional Logic & Workflow Decomposition | 25 | 14 | ⚠️ Partial | Happy path rõ; thiếu nhiều exception path đáng kể: `IX-14` (Secrets Store unavailable), `IX-16` (duplicate submit), `IX-12` (admin reject), A3 decryption-fail path UC không nói (srs FR-082 mới có) → cap §10 ("F.3 covers happy path only and omits important alternative / exception paths" → Area 3 ≤18). Blockchain B4 (transaction lifecycle) — N/A vì agent-key không phải on-chain tx; B6 (mid-flow events) — partial (rotation trong khi hedge-sync chạy chưa rõ). |
| 4 | Functional Integration & Data Consistency | 15 | 8 | ⚠️ Partial | Có nêu liên kết tới UC-EXBOT-bot-start (preflight), UC-EXBOT-hedge-sync (decrypt), deep-audit cron (expiry notification). Thiếu cụ thể: `IX-23` (UC không mô tả notification 7d), tương tác với rotation A2 trong hedge-sync chưa rõ (`IX-09`), consistency `users.hl_agent_key_id` ↔ `hl_agent_keys` không nêu rõ. Blockchain B7 (on-chain↔off-chain consistency) — N/A vì hl_agent_keys là off-chain only. |
| 5 | UC / Spec Documentation Quality Issues | 15 | 7 | ⚠️ Partial | Cap §10: (a) "UC có unresolved contradiction across sources" → Area 5 ≤8 (do `IX-01` FR numbering mismatch + `IX-04` enum mismatch). (b) "Phase 1 adds behavior not traceable to source and does not mark it as inferred" không áp dụng (đã đánh dấu `Suy luận cần xác nhận` cho AC-05..AC-08). (c) Nhiều ambiguous wording (`IX-09` thời điểm revoked) và missing pieces nhưng không lặp lại quá rộng → giữ ≤8. |
| **Tổng** | | **100** | **53** | ❌ Not Ready | — |

**Verdict: Not Ready (53/100, < 70 = Not Ready).**

Reasons:
- Hai mâu thuẫn nguồn quan trọng (`IX-01` FR numbering FRD vs SRS, `IX-04` enum revoked vs superseded) buộc auto-cap.
- Hai gap traceability đáng kể (`IX-05` BR-EXBOT chưa register, `IX-06` E-EXBOT chưa register) ngăn không resolve được rule / message qua registry chuẩn.
- Nhiều luồng exception thiết yếu cho hệ thống mã hoá / Admin approval không có spec (Secrets Store unavailable `IX-14`, admin reject `IX-12`, duplicate submit `IX-16`, validate input `IX-08`).
- API contract canonical cho `/api/exbot/agent-key` thiếu (`IX-02`, `IX-10`) → BE/FE đều không có ground truth để test.

Blockers còn lại:
- `IX-01` FR numbering conflict (block FR Trace cho test plan).
- `IX-04` enum revoked / superseded conflict (block expected post-condition cho rotate test).
- `IX-10` API contract thiếu (block thiết kế test API).

Major issues còn lại: `IX-02`, `IX-05`, `IX-06`, `IX-08`, `IX-12`, `IX-13`, `IX-14`. Minor: `IX-03`, `IX-11`, `IX-15`, `IX-16`, `IX-17`, `IX-18`, `IX-19`, `IX-20`, `IX-21`, `IX-22`, `IX-23`, `IX-24`.

Recommendation (1 đoạn):
UC-EXBOT-agent-key chưa sẵn sàng để bước vào pha thiết kế test một cách đầy đủ. BA cần ưu tiên xử lý **3 blocker** trước: (1) thống nhất bảng FR-EXBOT-080..083 giữa `frd.md` và `srs/spec.md` (re-number hoặc bổ sung FR-082/083 vào FRD), (2) chốt enum row cũ sau rotation là `revoked` hay `superseded` rồi cập nhật UC + US + ERD CHECK constraint cho khớp, (3) cung cấp API contract canonical cho `/api/exbot/agent-key` (payload submit, payload approve, response, role-based access). Sau khi 3 blocker được giải quyết, có thể proceed với 70% test coverage (happy path + key expired + decrypt fail + rotation); các luồng còn lại (admin reject `IX-12`, duplicate submit `IX-16`, Secrets Store unavailable `IX-14`, validate input `IX-08`) sẽ block khoảng 30% test coverage còn lại, cần BA bổ sung trong vòng kế tiếp.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-17 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu cho UC-EXBOT-agent-key (Submit and Approve HL Agent Key). Đối chiếu chéo `srs/` baseline (FR-EXBOT-080..083, ERD `hl_agent_keys`, flows + states không có entry riêng cho agent-key) với UC + US-EXBOT-011 + `frd.md` + common files. Issue Register §10.1 ghi nhận 24 issue (IX-01..IX-24). Verdict: Not Ready (53/100). |

---

*Báo cáo audited UC readiness — qc-uc-read-exbot skill — output English skill metadata + Vietnamese body theo `qc-writting-rules.md` §2B.*
