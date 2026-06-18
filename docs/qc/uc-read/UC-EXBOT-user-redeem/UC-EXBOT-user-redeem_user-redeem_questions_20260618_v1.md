# Question Backlog

> UC ID: UC-EXBOT-user-redeem
> Generated: 2026-06-18
> Source files: `docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260618_v1.md`
> Author: QC QnA Agent
> Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-001 | H | US-EXBOT-004 AC-1; UC §3 step 1 | US-EXBOT-004 AC-1 mô tả "system triggers on-chain `BnzaExVault.redeem(tokenId)`" — nhưng UC §3 step 1 xác định investor chủ động gọi `BnzaExVault.redeem(tokenId)` on-chain. BA vui lòng xác nhận: ai là actor khởi tạo giao dịch on-chain — investor hay system backend? Cập nhật US-EXBOT-004 AC-1 cho nhất quán với UC §3. | Tester không biết scope test cho bước on-chain initiation: nếu system trigger → cần test backend call; nếu investor trigger → không cần. Sai actor = sai toàn bộ test scenario. | Open |
| I-002 | H | UC §3 step 7; srs/states.md close_operations; srs/flows.md F-04 | UC §3 step 7 dùng `state='lp_closed→funds_returned'` (notation mũi tên). SRS states.md định nghĩa đây là 2 trạng thái riêng biệt: `lp_closed` và `funds_returned`. Hơn nữa, SRS flow F-04 bắt đầu bằng `close_operations(state='requested')` nhưng UC §3 step 7 bỏ qua `requested` hoàn toàn. BA vui lòng: (1) xác nhận trạng thái D1 đúng là: `requested` → `lp_closed` → `funds_returned` → ...; (2) cập nhật UC §3 step 7 dùng tên trạng thái chính xác, không dùng ký hiệu mũi tên. | Tester không thể viết D1 state assertion đúng cho test case. Nếu implement dùng string `'lp_closed→funds_returned'` → automation test sẽ fail vì không khớp SRS. | Open |
| I-003 | H | UC §4 A2; srs/states.md (`funds_parked`, `residual_hl_liability`) | UC §4 A2 nêu "hedge close fails → `residual_hl_liability`" nhưng không mô tả: (a) điều kiện cụ thể kích hoạt A2 — fail sau bao nhiêu retry? circuit breaker open?; (b) trạng thái `funds_parked` có trong SRS states.md nhưng không xuất hiện trong UC. BA vui lòng: (1) mô tả retry logic và điều kiện vào `residual_hl_liability`; (2) xác nhận `funds_parked` có thuộc user_redeem flow không. | Tester không thể thiết kế test case cho nhánh "hedge close fail" — không biết retry count, circuit breaker involvement, hay sự tồn tại của `funds_parked` state. | Open |
| I-004 | H | UC §3; FR-EXBOT-091 | UC không có alternate flow khi `HLRateLimitDO` trả về `{allowed: false, retryAfterMs}` trước khi gửi `closeShortReduceOnlyIoc`. FR-EXBOT-091 yêu cầu caller không proceed với HL call và phải re-queue. BA vui lòng bổ sung alternate flow: "HLRateLimitDO returns `allowed=false` → worker re-queues message với `retryAfterMs` delay; không submit HL call; SLA timer tiếp tục chạy." | Rate limit vượt ngưỡng + SLA 5 phút là tổ hợp nguy hiểm — nếu không có expected behavior rõ ràng, tester không thể test scenario này và dev có thể implement sai (submit HL call dù bị chặn). | Open |
| I-005 | H | UC §3 step 13; srs/erd.md | UC §3 step 13 cite "RedemptionQueue ledger" để theo dõi HL-portion USDC transfer cho investor, nhưng `srs/erd.md` không có bảng `redemption_queue`. Không có schema, không có `message_id` dedup, không có `state` tracking cho bước này. BA vui lòng xác nhận: (a) "RedemptionQueue ledger" là bảng D1 chưa được thêm vào ERD, hay là một cơ chế khác (Cloudflare Queue với idempotency riêng)? (b) Bổ sung vào `srs/erd.md` nếu là D1 table. | Tester không thể verify D1 state sau HL-portion transfer vì không có bảng canonical. Nếu transfer fail → không rõ retry mechanism và idempotency đảm bảo thế nào. | Open |
| I-006 | M | UC §4 A1; NFR-EXBOT-003 | UC §4 A1 mô tả SLA breach → alert admin, nhưng không nêu cơ chế đo thời gian 5 phút: timer nằm trong worker? cron job độc lập? dựa vào `close_operations.created_at`? Không rõ T0 (khi nào đồng hồ bắt đầu). BA vui lòng bổ sung vào UC §4 A1: T0 = timestamp khi [Event Watcher enqueue / on-chain tx confirmed]; SLA monitor là [component nào]; timeout xử lý bởi [worker / cron / alarm]. | Tester không thể viết test case "SLA breach at T+5min" nếu không biết T0 được lưu ở đâu và component nào chịu trách nhiệm detect breach. | Open |
| I-007 | M | UC index FR Trace; srs/spec.md FR-EXBOT-071 | `usecases/index.md` FR Trace cho UC-EXBOT-user-redeem bao gồm FR-EXBOT-071 (automatic re-entry). Tuy nhiên, FR-EXBOT-071 chỉ áp dụng cho bot_safe_close (lifecycle_state='cooldown' → 'active'). user_redeem kết thúc ở `lifecycle_state='closed'`, không có re-entry. BA vui lòng: loại bỏ FR-EXBOT-071 khỏi FR Trace của UC-EXBOT-user-redeem trong index, hoặc thêm ghi chú tường minh lý do FR-EXBOT-071 được liệt kê. | Tester có thể test sai scope: thiết kế test case cho re-entry trong user_redeem khi thực tế re-entry không xảy ra. | Open |
| I-008 | M | UC §3 step 8; FR-EXBOT-026 | UC §3 step 8 mô tả "acquire UserLockDO" nhưng không có alternate flow khi: (a) lock đã bị giữ bởi process khác (hedge-sync đang chạy); (b) heartbeat fail khi work > 30s (FR-EXBOT-026: nếu work > 30s, worker phải gọi heartbeat để gia hạn lease). BA vui lòng bổ sung: (1) alternate flow khi lock đang bị giữ; (2) note về heartbeat condition (FR-EXBOT-026) vào UC §3. | Tester không biết expected behavior khi UserLockDO bị giữ bởi hedge-sync Worker — deadlock/delay scenario chưa có test case. | Open |
| I-009 | L | UC §3 step 7 | UC §3 step 7 dùng ký hiệu `state='lp_closed→funds_returned'` không nhất quán với chuẩn notation D1 field value. BA vui lòng thay thế bằng notation rõ ràng: nếu là transition → "state chuyển từ `lp_closed` sang `funds_returned`"; nếu là 2 bước riêng → mô tả 2 dòng. | Tester có thể interpret sai D1 field value, dẫn đến assertion sai trong automation test. | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

| ID | Priority | Ref | Question | Defer Reason | Status |
|----|----------|-----|----------|--------------|--------|
