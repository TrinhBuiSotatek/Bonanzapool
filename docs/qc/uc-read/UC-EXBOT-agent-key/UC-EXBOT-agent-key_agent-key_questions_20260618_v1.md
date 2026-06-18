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
| I-01 | H | `frd.md` FR-EXBOT-080; `srs/spec.md` FR-EXBOT-080–083 | `frd.md` và `srs/spec.md` dùng cùng số FR-EXBOT-080 để chỉ hai nội dung khác nhau. `frd.md` không có FR-EXBOT-082, FR-EXBOT-083 trong khi `srs/spec.md` có cả 4 FR (080–083) dành cho agent-key. BA cần đồng bộ bộ số FR; hoặc xác nhận `srs/spec.md` là nguồn duy nhất và `frd.md` chỉ trace nhóm D1/API/NFR. | Tester không có nguồn chính thức để trace test case → FR trace bị lơ lửng. Mọi test case liên quan đến agent-key storage, revocation, expiry đều không trace được FR. | Open |
| I-02 | H | `frd.md` FR-EXBOT-100; UC §3 step 1, step 8 | `frd.md` FR-EXBOT-100 gán Admin là actor của POST /api/exbot/agent-key, trong khi UC định nghĩa NĐT gọi POST để nộp key và Admin chỉ gọi GET. BA cần cập nhật `frd.md` FR-EXBOT-100: POST do NĐT, GET do Admin; hoặc giải thích tại sao frd thiết kế khác UC. | Test case kiểm soát truy cập và luồng submit sẽ fail ngay nếu dùng nhầm actor. | Open |
| I-03 | L | `uc-agent-key.md` header; UC body title | UC file chưa có changelog entry cho ngày 2026-06-18 dù SRS đã có HLD decision làm thay đổi enum rotation. UC title trong body là "UC-EXBOT-agent-key-approval" nhưng file name và index dùng "UC-EXBOT-agent-key". BA cần update `updated: 2026-06-18`, thêm changelog entry, thống nhất tên UC. | Tester không biết UC có áp dụng SRS mới nhất không; inconsistent UC title gây khó tra cứu. | Open |
| I-04 | H | `srs/spec.md` FR-EXBOT-080 AC; `srs/spec.md` FR-EXBOT-083 AC; UC §4 A2; `us-011.md` Notes | Trong cùng một file `srs/spec.md`, FR-EXBOT-080 ghi trạng thái cũ chuyển thành `revoked` khi rotation, nhưng FR-EXBOT-083 ghi trạng thái cũ chuyển thành `superseded`. UC và US-011 theo FR-080 (`revoked`). BA cần chốt một enum value cho rotation cũ-row và cập nhật toàn bộ `srs/spec.md`, UC §4 A2, US-011 Notes về cùng giá trị. | Test case rotation không thể viết vì không biết expected state là `revoked` hay `superseded`. Nếu DB enforce enum, một trong hai AC sẽ fail. | Open |
| I-05 | H | UC §6; `02_backbone/common-rules.md` | UC §6 tham chiếu BR-EXBOT nhưng các rule này không tồn tại trong `common-rules.md` — chúng chỉ nằm inline trong `srs/spec.md §4`. BA cần tạo BR-EXBOT-080..083 trong `common-rules.md` hoặc xác nhận rằng inline srs là nguồn duy nhất và update UC §6 để dẫn đúng nguồn. | Test case liên quan đến BR validation (ví dụ: 1 approved/user, DELETE forbidden, expiry) không có nguồn chính thức để trace. | Open |
| I-06 | H | `srs/spec.md §5`; `02_backbone/message-list.md` | E-EXBOT-004 "Your HL agent key has expired. Please submit a new one." được khai báo trong `srs/spec.md §5` nhưng không đăng ký trong `message-list.md`. BA cần thêm E-EXBOT-001..013 vào `message-list.md` hoặc tạo section ExBot riêng trong registry và thêm disclaimer. | Test case kiểm tra error message E-EXBOT-004 không có nguồn master để compare. | Open |
| I-07 | H | `srs/spec.md` FR-EXBOT-083; `srs/erd.md` `expires_at TEXT`; UC §3 step 1 | Không có tài liệu nào định nghĩa: (a) ai set `expires_at` — user gửi hay hệ thống tự tính? (b) thời hạn tối đa / mặc định; (c) có validate khi submit không (ví dụ: không cho phép expires_at trong quá khứ). BA cần chốt: ai set `expires_at`, rule validation (min/max), và nếu user gửi thì format/constraint ra sao. | Tester không biết expected giá trị `expires_at` khi submit, không thể viết test case cho boundary của trường này. | Open |
| I-08 | H | FR-EXBOT-080 (srs); UC §2 | Không có validation rule nào phân biệt agent key với master key để từ chối trường hợp user vô tình nộp master private key. Format / length / prefix của agent key không được định nghĩa. BA cần định nghĩa format hợp lệ của agent key (ví dụ: length, prefix, checksum) và rule từ chối nếu không đúng format. | Test case negative: "nộp master key bị reject" không viết được vì không có expected validation behavior. | Open |
| I-09 | H | `srs/spec.md` FR-EXBOT-083; UC §4 A2 | Thời điểm chính xác khi row cũ chuyển trạng thái khi rotation chưa rõ: cùng transaction với approve-new, hay sau khi approve-new commit, hay trong một cron job? Thiếu mô tả atomicity / transaction boundary. BA cần bổ sung vào UC §4 A2: hành động cụ thể khi admin approve new key (atomic DB update, transaction boundary) và hành vi của hedge-sync trong window. | Test case rotation không thể verify "hedge-sync không bị interrupt trong window" vì không biết exact timing chuyển state. | Open |
| I-10 | H | UC §3 step 1; `frd.md` FR-EXBOT-100 | Không có tài liệu nào định nghĩa schema của payload POST /api/exbot/agent-key (field name, type, required/optional, ví dụ giá trị) và schema của response. BA / Dev cần publish API contract cho `/api/exbot/agent-key` với đầy đủ request schema, response schema, và HTTP status codes. | Không thể thiết kế test case submit hợp lệ, test negative validation, hoặc verify error response format. | Open |
| I-11 | H | `srs/spec.md` FR-EXBOT-083; UC (thiếu) | Luồng cron deep-audit scan `expires_at <= now + 7d` và enqueue expiry notification không được mô tả trong UC-EXBOT-agent-key. BA cần thêm vào UC §4 một alternate flow cho expiry notification hoặc xác nhận đây thuộc UC-EXBOT-deep-audit và thêm cross-reference. | Test case cron / expiry notification không có trong scope UC — tester có thể bỏ sót. | Open |
| I-12 | H | UC §3 step 8–9; `approval_status` enum | Không có alternate flow khi Admin không approve (reject) một key pending. Không có enum value `rejected`. BA cần định nghĩa admin-reject path: enum value mới (`rejected`?), message gửi NĐT, hành vi với row rejected (giữ hay delete). | Test case "Admin reject" không viết được. | Open |
| I-13 | H | `srs/erd.md` `hl_agent_keys`; UC §3 step 9 | Không có cách audit ai đã approve một agent key (thiếu trường `approved_by`). Không có SLA từ `pending` → `approved`. BA cần thêm `approved_by` vào ERD hoặc giải thích tại sao không cần; định nghĩa SLA approve (nếu có). | Audit trail test case không viết được; SLA test không có baseline. | Open |
| I-14 | H | FR-EXBOT-080 (srs); UC §3 step 5; UC §4 A3 | Không có tài liệu nào định nghĩa hành vi khi Cloudflare Secrets Store không available: (a) lúc wrap DEK khi submit; (b) lúc unwrap DEK khi hedge-sync. BA cần bổ sung failure handling cho Secrets Store unavailability vào UC §3 (submit) và UC §4 A3 (decrypt). | Test case dependency failure (Secrets Store down) không viết được. | Open |
| I-15 | M | FR-EXBOT-080 (srs) `IV 12 bytes` | Không có rule yêu cầu IV phải unique per row (chống nonce reuse). AES-GCM với IV tái dùng là lỗ hổng bảo mật nghiêm trọng, nhưng UC không đề cập. BA / Dev cần xác nhận IV được sinh ngẫu nhiên (CSPRNG) per row và không tái dùng — nếu đã đảm bảo ở code level, cần note vào NFR. | Test case kiểm tra IV uniqueness không có trong scope. | Closed |
| I-16 | M | UC §4 A2; UC §3 (thiếu) | Không định nghĩa hành vi khi NĐT submit key mới trong khi đã có row `pending` (ví dụ: bị reject vì chỉ 1 pending/user? overwrite? INSERT thêm row?). BA cần bổ sung UC §4 alt flow hoặc constraint rõ ràng. | Test case "submit khi pending đã tồn tại" không có expected result. | Open |
| I-17 | M | UC (thiếu); `frd.md` (thiếu NFR rate limit) | POST /api/exbot/agent-key không có rate limit được định nghĩa. BA cần xác nhận rate limit policy cho endpoint này (nếu có). | Test case rate limit không viết được. | Open |
| I-18 | M | UC §3 step 9 (thiếu edge case) | Nếu Admin xử lý chậm và key đã hết hạn trước khi approve, hành vi là gì: approve vẫn được (row `approved` nhưng sẽ fail preflight ngay) hay system reject approve? BA cần định nghĩa: hệ thống có validate `expires_at` khi admin approve không? | Test case edge case này không có expected result. | Open |
| I-19 | M | UC §4 A2; srs FR-EXBOT-082 | UC không nói rõ DELETE revoked rows có bị cấm hay không, mặc dù srs FR-082 ghi "DELETE of revoked rows is forbidden". BA cần cross-reference FR-EXBOT-082 srs vào UC §6 Business Rules để tester trace được. | Tester cần biết để viết negative test case "xoá row revoked bị block". | Open |
| I-20 | M | `srs/spec.md §5`; UC (thiếu) | UC không có section liệt kê toàn bộ error codes ảnh hưởng đến luồng agent-key (ngoài E-EXBOT-004). BA cần thêm bảng E-* liên quan vào UC §6 hoặc §10. | Coverage error cases bị bỏ sót. | Open |
| I-21 | L | UC Mermaid diagram (placeholder) | UC có chứa Mermaid diagram nhưng chỉ là placeholder "User->>System: Trigger action" — không có sequence diagram thực tế cho submit/approve/decrypt flow. BA nên thêm sequence diagram thực tế hoặc xoá placeholder. | Không ảnh hưởng test case nhưng giảm khả năng hiểu của reviewer mới. | Closed |
| I-22 | L | `us-011.md` FR Trace | US-011 chỉ trace FM-XB-01 nhưng bỏ qua FM-XB-12 (Envelope Encryption) mặc dù AC-4 về plain key destruction liên quan trực tiếp đến FM-XB-12. BA cần thêm FM-XB-12 vào FR Trace của US-011. | Feature map coverage cho encryption feature bị thiếu. | Open |
| I-23 | L | `srs/states.md` 2026-06-18 | `srs/states.md` chỉ có state machine cho `bots.lifecycle_state`. Không có diagram trạng thái cho `hl_agent_keys.approval_status` (pending → approved → revoked/superseded). BA nên thêm state machine cho `hl_agent_keys.approval_status` vào `srs/states.md`. | State transition test case cần tự construct enum, tăng rủi ro bỏ sót transition. | Open |
| I-24 | L | UC §4 A3 step 1 | UC không định nghĩa: fetch row mỗi hedge-sync cycle hay có caching? Cache invalidation khi key bị revoke giữa chừng? BA / Dev cần clarify caching strategy cho hl_agent_keys lookup trong hedge-sync. | Nếu có cache, hedge-sync có thể dùng revoked key. Test case cần bao gồm revoke-mid-cycle nếu caching tồn tại. | Closed |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred Until | Status |
|----|----------|-----|----------|-----------------|----------------|--------|

