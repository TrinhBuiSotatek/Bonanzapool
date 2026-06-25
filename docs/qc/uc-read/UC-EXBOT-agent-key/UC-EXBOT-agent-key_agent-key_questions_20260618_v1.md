---
title: Question Backlog — UC-EXBOT-agent-key (Submit and Approve HL Agent Key)
uc_id: UC-EXBOT-agent-key
feature: hl-agent-key
type: questions
date: 2026-06-18
author: qc-qna agent (Trinh.Bui)
version: v1
source_report: UC-EXBOT-agent-key_hl-agent-key_audited_20260618_v1.md
---

# Question Backlog — UC-EXBOT-agent-key

> Generated: 2026-06-18
> Source file: `docs/qc/uc-read/UC-EXBOT-agent-key/UC-EXBOT-agent-key_hl-agent-key_audited_20260618_v1.md`

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-02 | H | `frd.md` FR-EXBOT-100; UC §3 step 1, step 8 | `frd.md` FR-EXBOT-100 gán Admin là actor của POST /api/exbot/agent-key, trong khi UC định nghĩa NĐT gọi POST để nộp key và Admin chỉ gọi GET. BA cần cập nhật `frd.md` FR-EXBOT-100: POST do NĐT, GET do Admin; hoặc giải thích tại sao frd thiết kế khác UC. | Test case kiểm soát truy cập và luồng submit sẽ fail ngay nếu dùng nhầm actor. | Open |
| I-03 | L | `uc-agent-key.md` header; UC body title | UC file chưa có changelog entry cho ngày 2026-06-18 dù SRS đã có HLD decision làm thay đổi enum rotation. UC title trong body là "UC-EXBOT-agent-key-approval" nhưng file name và index dùng "UC-EXBOT-agent-key". BA cần update `updated: 2026-06-18`, thêm changelog entry, thống nhất tên UC. | Tester không biết UC có áp dụng SRS mới nhất không; inconsistent UC title gây khó tra cứu. | Open |
| I-05 | H | UC §6; `02_backbone/common-rules.md` | UC §6 tham chiếu BR-EXBOT nhưng các rule này không tồn tại trong `common-rules.md` — chúng chỉ nằm inline trong `srs/spec.md §4`. BA cần tạo BR-EXBOT-080..083 trong `common-rules.md` hoặc xác nhận rằng inline srs là nguồn duy nhất và update UC §6 để dẫn đúng nguồn. | Test case liên quan đến BR validation (ví dụ: 1 approved/user, DELETE forbidden, expiry) không có nguồn chính thức để trace. | Open |
| I-06 | H | `srs/spec.md §5`; `02_backbone/message-list.md` | E-EXBOT-004 "Your HL agent key has expired. Please submit a new one." được khai báo trong `srs/spec.md §5` nhưng không đăng ký trong `message-list.md`. BA cần thêm E-EXBOT-001..013 vào `message-list.md` hoặc tạo section ExBot riêng trong registry và thêm disclaimer. | Test case kiểm tra error message E-EXBOT-004 không có nguồn master để compare. | Open |
| I-07 | H | `srs/spec.md` FR-EXBOT-083; `srs/erd.md` `expires_at TEXT`; UC §3 step 1 | Không có tài liệu nào định nghĩa: (a) ai set `expires_at` — user gửi hay hệ thống tự tính? (b) thời hạn tối đa / mặc định; (c) có validate khi submit không (ví dụ: không cho phép expires_at trong quá khứ). BA cần chốt: ai set `expires_at`, rule validation (min/max), và nếu user gửi thì format/constraint ra sao. | Tester không biết expected giá trị `expires_at` khi submit, không thể viết test case cho boundary của trường này. | Open |
| I-08 | H | FR-EXBOT-080 (srs); UC §2 | Không có validation rule nào phân biệt agent key với master key để từ chối trường hợp user vô tình nộp master private key. Format / length / prefix của agent key không được định nghĩa. BA cần định nghĩa format hợp lệ của agent key (ví dụ: length, prefix, checksum) và rule từ chối nếu không đúng format. | Test case negative: "nộp master key bị reject" không viết được vì không có expected validation behavior. | Open |
| I-10 | H | UC §3 step 1; `frd.md` FR-EXBOT-100 | Không có tài liệu nào định nghĩa schema của payload POST /api/exbot/agent-key (field name, type, required/optional, ví dụ giá trị) và schema của response. BA / Dev cần publish API contract cho `/api/exbot/agent-key` với đầy đủ request schema, response schema, và HTTP status codes. | Không thể thiết kế test case submit hợp lệ, test negative validation, hoặc verify error response format. | Open |
| I-13 | H | `srs/erd.md` `hl_agent_keys`; UC §3 step 9 | Không có cách audit ai đã approve một agent key (thiếu trường `approved_by`). Không có SLA từ `pending` → `approved`. BA cần thêm `approved_by` vào ERD hoặc giải thích tại sao không cần; định nghĩa SLA approve (nếu có). | Audit trail test case không viết được; SLA test không có baseline. | Open |
| I-14 | H | FR-EXBOT-080 (srs); UC §3 step 5; UC §4 A3 | Không có tài liệu nào định nghĩa hành vi khi Cloudflare Secrets Store không available: (a) lúc wrap DEK khi submit; (b) lúc unwrap DEK khi hedge-sync. BA cần bổ sung failure handling cho Secrets Store unavailability vào UC §3 (submit) và UC §4 A3 (decrypt). | Test case dependency failure (Secrets Store down) không viết được. | Open |
| I-16 | M | UC §4 A2; UC §3 (thiếu) | Không định nghĩa hành vi khi NĐT submit key mới trong khi đã có row `pending` (ví dụ: bị reject vì chỉ 1 pending/user? overwrite? INSERT thêm row?). BA cần bổ sung UC §4 alt flow hoặc constraint rõ ràng. | Test case "submit khi pending đã tồn tại" không có expected result. | Open |
| I-17 | M | UC (thiếu); `frd.md` (thiếu NFR rate limit) | POST /api/exbot/agent-key không có rate limit được định nghĩa. BA cần xác nhận rate limit policy cho endpoint này (nếu có). | Test case rate limit không viết được. | Open |
| I-18 | M | UC §3 step 9 (thiếu edge case) | Nếu Admin xử lý chậm và key đã hết hạn trước khi approve, hành vi là gì: approve vẫn được (row `approved` nhưng sẽ fail preflight ngay) hay system reject approve? BA cần định nghĩa: hệ thống có validate `expires_at` khi admin approve không? | Test case edge case này không có expected result. | Open |
| I-20 | M | `srs/spec.md §5`; UC (thiếu) | UC không có section liệt kê toàn bộ error codes ảnh hưởng đến luồng agent-key (ngoài E-EXBOT-004). BA cần thêm bảng E-* liên quan vào UC §6 hoặc §10. | Coverage error cases bị bỏ sót. | Open |
| I-22 | L | `us-011.md` FR Trace | US-011 chỉ trace FM-XB-01 nhưng bỏ qua FM-XB-12 (Envelope Encryption) mặc dù AC-4 về plain key destruction liên quan trực tiếp đến FM-XB-12. BA cần thêm FM-XB-12 vào FR Trace của US-011. | Feature map coverage cho encryption feature bị thiếu. | Open |
| I-23 | L | `srs/states.md` 2026-06-18; OQ-EXBOT-016 | `srs/states.md` không có diagram trạng thái cho `hl_agent_keys.approval_status`. Từ FR-EXBOT-081/082/083, 3 transitions đã có đủ tài liệu: `pending→approved`, `approved→superseded` (rotation), `approved→revoked` (explicit revocation). Chỉ còn thiếu 1 transition: khi admin **reject** một key pending, trạng thái row là gì? BA cần bổ sung vào `states.md` transition `pending→???` (rejected/deleted) sau khi OQ-EXBOT-016 được chốt. | Tester có thể viết test case cho 3 transitions đã rõ; chỉ bị block ở reject path. | Open |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-01 | H | `frd.md` FR-EXBOT-080; `srs/spec.md` FR-EXBOT-080–083 | `frd.md` và `srs/spec.md` dùng cùng số FR-EXBOT-080 để chỉ hai nội dung khác nhau. `frd.md` không có FR-EXBOT-082, FR-EXBOT-083 trong khi `srs/spec.md` có cả 4 FR (080–083) dành cho agent-key. BA cần đồng bộ bộ số FR; hoặc xác nhận `srs/spec.md` là nguồn duy nhất. | Hai hệ thống đánh số là quyết định có chủ ý: `frd.md` dùng nhóm số riêng phục vụ implementation grouping (D1/API/NFR), `srs/spec.md` là nguồn chính thức (canonical). UC §7 FR Trace đã được thêm note: "`frd.md` = implementation grouping, `srs/spec.md` = canonical behavior. Trace luôn tham chiếu `srs/spec.md`." Tester dùng `srs/spec.md` để trace test case. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-04 | H | `srs/spec.md` FR-EXBOT-080 AC; `srs/spec.md` FR-EXBOT-083 AC; UC §4 A2; `us-011.md` Notes | Trong cùng một file `srs/spec.md`, FR-EXBOT-080 ghi trạng thái cũ chuyển thành `revoked` khi rotation, nhưng FR-EXBOT-083 ghi trạng thái cũ chuyển thành `superseded`. UC và US-011 theo FR-080 (`revoked`). BA cần chốt một enum value cho rotation cũ-row. | `superseded` là enum value đúng cho row cũ khi rotation (admin approve key mới → row cũ chuyển sang `superseded`). `revoked` chỉ dùng khi admin thu hồi key chủ động (explicit revocation). `spec.md` FR-080 và FR-083 đã được align về giá trị này. UC §4 A2 đã update sang `superseded`. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-11 | H | `srs/spec.md` FR-EXBOT-083; UC (thiếu) | Luồng cron deep-audit scan `expires_at <= now + 7d` và enqueue expiry notification không được mô tả trong UC-EXBOT-agent-key. BA cần thêm vào UC §4 một alternate flow cho expiry notification hoặc xác nhận đây thuộc UC-EXBOT-deep-audit và thêm cross-reference. | Luồng expiry notification là Out-of-Scope cho UC-EXBOT-agent-key. Scope này thuộc UC-EXBOT-deep-audit, cross-reference FR-083. UC đã thêm A5 ghi rõ OOS và cross-ref đến UC-EXBOT-deep-audit. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-09 | H | UC §4 A2; `srs/spec.md` FR-EXBOT-083 | Thời điểm chính xác khi row cũ chuyển trạng thái khi rotation chưa rõ: cùng transaction với approve-new, hay sau khi approve-new commit, hay trong một cron job? Thiếu mô tả atomicity / transaction boundary. Hành vi của hedge-sync trong window giữa submission và admin approval là gì? | FR-EXBOT-083 AC xác nhận: (1) **Atomicity** — `status='superseded'` trên row cũ được set **cùng transaction** với `status='approved'` trên row mới, không có window không nhất quán. (2) **Window behavior** — "During the window between submission and admin approval, the existing approved key remains active (unless it has expired)." → Hedge-sync tiếp tục dùng key cũ bình thường trong toàn bộ thời gian chờ approve. | `srs/spec.md` FR-EXBOT-083 AC | 2026-06-25 | Answered |
| I-19 | M | UC §4 A2; `srs/spec.md` FR-EXBOT-082 | UC không nói rõ DELETE revoked rows có bị cấm hay không, mặc dù srs FR-082 ghi "DELETE of revoked rows is forbidden". BA cần cross-reference FR-EXBOT-082 srs vào UC §6 Business Rules để tester trace được. | FR-EXBOT-082 quy định rõ: "Revoked rows remain in D1 for audit purposes — DELETE of revoked rows is forbidden." UC §6 đã tham chiếu FR-EXBOT-082 qua chuỗi "BR-EXBOT (FR-EXBOT-080, 081, 082, 083)". Tester có thể trace rule này từ UC §6 → spec.md FR-082 mà không cần BA bổ sung thêm. | `srs/spec.md` FR-EXBOT-082 | 2026-06-25 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred Until | Status |
|----|----------|-----|----------|-----------------|----------------|--------|
| I-12 | H | UC §3 step 8–9; `approval_status` enum | Không có alternate flow khi Admin không approve (reject) một key pending. Không có enum value `rejected`. BA cần định nghĩa admin-reject path: enum value mới (`rejected`?), message gửi NĐT, hành vi với row rejected (giữ hay delete). | OQ-EXBOT-016 đã được tạo trong `spec.md §9` với 3 options (A/B/C) cho admin reject path. Blocked on BA + zen scope decision. | Pending OQ-EXBOT-016 resolution | Deferred |
| I-15 | M | FR-EXBOT-080 (srs) `IV 12 bytes` | Không có rule yêu cầu IV phải unique per row (chống nonce reuse). AES-GCM với IV tái dùng là lỗ hổng bảo mật nghiêm trọng, nhưng UC không đề cập. BA / Dev cần xác nhận IV được sinh ngẫu nhiên (CSPRNG) per row và không tái dùng — nếu đã đảm bảo ở code level, cần note vào NFR. | Đã được đảm bảo ở code level (xác nhận trước đó). Không cần thêm vào UC; chỉ cần note vào NFR nếu muốn trace được. | — | Deferred |
| I-21 | L | UC Mermaid diagram (placeholder) | UC có chứa Mermaid diagram nhưng chỉ là placeholder "User->>System: Trigger action" — không có sequence diagram thực tế cho submit/approve/decrypt flow. BA nên thêm sequence diagram thực tế hoặc xoá placeholder. | Không ảnh hưởng test case. Để BA quyết định có thêm diagram hay không. | — | Deferred |
| I-24 | L | UC §4 A3 step 1 | UC không định nghĩa: fetch row mỗi hedge-sync cycle hay có caching? Cache invalidation khi key bị revoke giữa chừng? BA / Dev cần clarify caching strategy cho hl_agent_keys lookup trong hedge-sync. | Nếu có cache, hedge-sync có thể dùng revoked key. | — | Deferred |

