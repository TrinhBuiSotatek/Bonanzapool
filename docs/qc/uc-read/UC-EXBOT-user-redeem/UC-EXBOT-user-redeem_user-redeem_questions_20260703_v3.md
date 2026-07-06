# Question Backlog

| UC ID | UC-EXBOT-user-redeem |
|-------|----------------------|
| Ngày tạo | 2026-07-01 |
| Ngày cập nhật | 2026-07-03 |
| Người tạo | QC UC Read ExBot Agent |
| Version | v3 |
| Nguồn audited | UC-EXBOT-user-redeem_user-redeem_audited_20260703_v2.md |
| Nguồn câu trả lời | docs/BA/qc-responses-2026-07-03.md (owner: @hienduong) |

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-02 | High | uc-user-redeem.md §3 step 12-14; flows.md F-04 | UC mô tả Worker "gửi HL-portion USDC về nhà đầu tư qua RedemptionQueue ledger" nhưng không định nghĩa: (a) HL-portion được tính như thế nào (tổng số tiền từ HL closing position minus fees? minus funding?); (b) ai thực sự là người thực hiện on-chain transfer USDC (Worker gọi trực tiếp hay qua Operator Facade?); (c) transaction hash của HL-portion transfer có được lưu vào `close_operations.hedge_close_tx` không? | Không có công thức hoặc mô tả source of truth cho HL-portion amount → tester không thể verify số tiền nhà đầu tư nhận đúng không. | Outdated vs AWS arc — HL-portion transfer mechanism changed. Pending Tech Lead for updated flow details. |
| I-03 | Medium | uc-user-redeem.md §3 step 8; spec.md FR-EXBOT-026; flows.md F-04 | UC step 8 xác nhận Redeem Worker có acquire `UserLockDO` lease — vấn đề không phải là "có lock hay không". Sau khi cross-check tài liệu, câu hỏi được thu hẹp còn 2 điểm chưa rõ: **(a) Behavior khi acquired=false:** UC step 8 chỉ ghi "acquires UserLockDO lease" nhưng không mô tả behavior khi lock đang bị giữ bởi hedge-sync worker. spec.md FR-EXBOT-026 định nghĩa pattern cho hedge-sync: `acquired=false → re-queue với delay`. User_redeem có dùng cùng pattern không, hay chờ spin-wait, hay fail ngay? Với user_redeem có SLA 5 phút, re-queue với delay có thể vi phạm SLA. **(b) flows.md F-04 không hiển thị UserLockDO:** Sequence diagram F-04 không có participant UserLockDO (trong khi F-02 hedge-sync hiển thị rõ). Đây là lỗi thiếu trong diagram hay user_redeem dùng cơ chế khác? | Behavior khi lock contention xảy ra ảnh hưởng trực tiếp đến test case SLA. | Outdated vs AWS arc — UserLockDO replaced by Postgres advisory lock + SQS FIFO. Lock behavior details pending Tech Lead confirmation under new arc. |
| I-N1 | Medium | uc-user-redeem.md §2 Preconditions (v2, updated 2026-07-03); states.md State Registry | UC §2 v2 mở rộng precondition: "Bot `status='active'` (or paused/safe_mode — user may redeem from any non-closed state)". Thông tin này mới so với v1 và **chưa được phản ánh trong states.md** State Registry. Cụ thể cần xác nhận: (a) Bot ở `hedge_stopped_cooldown` có thể được redeem không? (b) Bot ở `lp_rebalancing` có thể được redeem không? (c) Bot ở `error` có thể được redeem không? states.md chỉ liệt kê `lp_closing` như là bước chuyển tiếp khi có close request, nhưng không nói rõ các trạng thái nào được phép khởi tạo close request. | Tester cần biết chính xác các trạng thái bắt đầu hợp lệ để thiết kế pre-condition cho test case. Nếu precondition sai → test case fail vì lý do sai, không phải vì lỗi thực. | Open — cần BA confirm và update states.md |
| I-N2 | Low | uc-user-redeem.md §3 step 9 | UC step 9 chỉ nói "retries up to 3 times on reject/timeout" nhưng không mô tả: (a) Retry strategy: trong cùng Worker invocation hay re-queue message? (b) Có backoff delay giữa các lần retry không? Nếu re-queue với delay, tổng thời gian 3 retries có thể vượt SLA 5 phút. | Ảnh hưởng thiết kế test case simulate HL partial failure và timing. Không block happy path design nhưng cần biết để test retry behavior chính xác. | Open — Minor, thông tin phụ trợ |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-01 | High | UC §7 FR Trace vs frd.md; US-EXBOT-009 Trace | UC §7 FR Trace liệt kê "FR-EXBOT-070, FR-EXBOT-071". FR-EXBOT-071 không tồn tại trong frd.md. Câu hỏi: (a) FR-EXBOT-071 có phải là FR bị thiếu cần tạo mới? hay (b) đây là lỗi copy-paste từ US-009 sang UC user-redeem? | FR-EXBOT-071 does not exist in frd.md. Citation error — FR-071 belongs to `uc-bot-safe-close`, not in scope of user-redeem. UC §7 FR Trace updated — only `FR-EXBOT-070` retained. | @hienduong | 2026-07-03 | Answered |
| I-04 | High | uc-user-redeem.md §3 step 7; flows.md F-04 line 162; states.md close_operations table; spec.md FR-EXBOT-073 | Conflict về initial state khi Worker tạo `close_operations` row. UC step 7 và flows.md F-04 dùng notation `lp_closed→funds_returned` không hợp lệ. (a) Initial state là `'requested'` hay `'funds_returned'`? (b) `lp_closed→funds_returned` là lỗi notation hay bỏ qua state `requested` và `lp_closed`? | (a) Initial state = `requested`. (b) `lp_closed→funds_returned` là lỗi notation — Worker insert row tại `requested`, sau đó update ngay sang `lp_closed` rồi `funds_returned` (được bảo đảm on-chain từ step 2-3). Không skip state nào. (c) Full transition `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done` có thể test được. UC doc đã được cập nhật. | @hienduong | 2026-07-03 | Answered |
| I-05 | Medium | uc-user-redeem.md §4 A2; flows.md F-04; message-list.md | Khi hedge close thất bại và `close_operations.state='residual_hl_liability'`, UC A2 nói "admin notified with amount" nhưng không cite message code. BA vui lòng cung cấp message code và nội dung verbatim. | Đã đăng ký **E-EXBOT-024**: "User redemption hedge close failed. Manual intervention required." — internal admin alert. UC A2 đã cập nhật để cite E-EXBOT-024. | @hienduong | 2026-07-03 | Answered |
| I-06 | Medium | uc-user-redeem.md §4 A2; states.md | Khi `close_operations.state='residual_hl_liability'` (A2 flow), `bots.lifecycle_state` và `bots.status` chuyển sang giá trị gì? UC §5 không mô tả postconditions cho A2. | A2 → `bots.lifecycle_state='error'`, `bots.status='error'`. LP đã được hoàn trả (on-chain, không đảo ngược). Admin phải đóng thủ công residual HL position. UC §5 đã cập nhật với A2 postconditions. | @hienduong | 2026-07-03 | Answered |
| I-08 | Medium | uc-user-redeem.md §3 step 11; flows.md F-04 | Sau bước reconcile, nếu reconcile thất bại (HL position ≠ 0 sau closeShortReduceOnlyIoc), UC không mô tả behavior. SAFE_MODE có áp dụng không? | Reconcile failure in user_redeem = same outcome as A2: `residual_hl_liability` → `bots.lifecycle_state='error'` → admin notified (E-EXBOT-024). SAFE_MODE does NOT apply — LP đã thanh lý, không còn gì để bảo vệ. UC A2 đã cập nhật để bao gồm cả hedge close failure và reconcile mismatch. | @hienduong | 2026-07-03 | Answered |
| I-09 | Medium | uc-user-redeem.md §5 (Postconditions) | UC có hai phần Postconditions trùng lặp với nội dung khác nhau về `lifecycle_state`. | Phần Postconditions dư (tham chiếu D1, NFR-ADM-005) đã bị xóa vì là boilerplate cũ và mâu thuẫn với §5. §5 hiện là nguồn duy nhất, bao gồm happy path và A2 postconditions. | @hienduong | 2026-07-03 | Answered |
| I-10 | Medium | flows.md F-05 vs uc-user-redeem.md | flows.md F-05 (bot_safe_close) hiển thị luồng cũ, có thể đã outdated sau HLD 2026-06-18. | Outdated vs AWS arc — F-05 will be rewritten during arc migration. Logic issue (missing hedge-first step) will also be corrected in the same pass. | @hienduong | 2026-07-03 | Answered |
| I-11 | Low | uc-user-redeem.md §3 step 9; flows.md F-04; frd.md FR-EXBOT-022 | Khi `closeShortReduceOnlyIoc` bị HL reject, Worker retry bao nhiêu lần trước khi chuyển sang `residual_hl_liability`? | `closeShortReduceOnlyIoc` thử lại tối đa 3 lần khi HL reject/timeout. Sau 3 lần thất bại: `close_operations.state='residual_hl_liability'`, `bots.lifecycle_state='error'`, admin nhận thông báo (E-EXBOT-024). Retry count thống nhất với bot_safe_close. UC step 9 và A2 đã cập nhật. | @hienduong | 2026-07-03 | Answered |
| I-05-B | Medium | erd.md close_operations | `close_operations.residual_amount TEXT` là field lưu outstanding liability amount khi hedge close thất bại (`state='residual_hl_liability'`). | ERD xác nhận. | QC UC Read Agent | 2026-07-01 | Answered |
| I-11-A | Low | spec.md line 246; frd.md FR-EXBOT-022 | Cloid cho `closeShortReduceOnlyIoc` trong user_redeem có áp dụng công thức FR-EXBOT-022 không? | Có — FR-EXBOT-022 áp dụng cho mọi hedge mutation. Công thức: `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. spec.md line 226 xác nhận full close (target=0) được phép trong "bot close path". | QC UC Read Agent | 2026-07-01 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Status |
|----|----------|-----|----------|-----------------|--------|
| I-12 | Low | uc-user-redeem.md §3 step 3 "enqueue ... [highest priority queue]" | UC dùng notation "[highest priority queue]" (trong ngoặc vuông) — không rõ đây là tên queue hay chú thích độ ưu tiên. | frd.md FR-EXBOT-010 và flows.md F-04 đã xác nhận đây là `user_redeem` queue — tester có thể resolve từ frd.md mà không cần BA xác nhận thêm. | Deferred |

---

Priority: H = High (chặn thiết kế), M = Medium (ảnh hưởng scope), L = Low (cần biết thêm)
Status: Open | Answered | Deferred | Outdated vs AWS arc
