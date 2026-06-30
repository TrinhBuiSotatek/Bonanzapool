# Question Backlog — UC-EXBOT-bot-start

> **UC ID:** UC-EXBOT-bot-start  
> **Ngày tạo:** 2026-06-30  
> **Nguồn:** `UC-EXBOT-bot-start_bot-start_audited_20260630_v1.md` §10.1  
> **Phiên bản:** v1

Priority: High = block test design, Medium = ảnh hưởng scope/coverage, Low = nice-to-know  
Status: Open | Answered | Deferred

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-01 | Low | UC §1 Actors vs SRS F-03 | UC §1 Actors không liệt kê "Signing Lambda" dù SRS F-03 và UC step 7/10 đều đề cập. Đề xuất: thêm Signing Lambda vào UC §1 Actors để nhất quán. | Minor — tester có thể suy luận từ flow; không block | Open |
| I-02 | High | UC §4 A11 vs FR-EXBOT-025 | UC mô tả A11 (reconcile mismatch) là "actual size deviates > threshold" nhưng không định nghĩa threshold cụ thể là bao nhiêu. FR-EXBOT-025 cũng không nêu threshold. Tester cần biết ngưỡng deviation cụ thể để thiết kế test case kiểm tra boundary. | Blocker cho test reconcile mismatch | Open |
| I-03 | Medium | UC §3 step 3 (preflight bước 2) | Preflight bước 2 yêu cầu fetch HL `marginSummary` để kiểm tra margin. UC không mô tả hành vi khi HL API không phản hồi trong lúc preflight (khác với A7 xảy ra sau preflight). Nếu HL down tại bước preflight margin check → bot có enter `error` state hay retry sau đó? | Cần biết để test alternate flow HL timeout tại preflight | Open |
| I-04 | High | UC §3 step 6 vs OQ-EXBOT-03 | UC nêu `wethIndex` được lưu vào `positions` sau LP mint, nhưng pool address + `wethIndex` cho USDC/WETH 0.3% trên Base và Optimism chưa được xác nhận (OQ-EXBOT-03 vẫn Open). Nếu wethIndex sai → `lpEthAmount` tính sai → hedge size sai. Test case kiểm tra wethIndex per chain bị block cho đến khi OQ-EXBOT-03 resolved. | Blocker cho test dual-chain LP open | Open |
| I-05 | High | UC §4 A4 | A4 ghi "enter `error` state, return funds" khi LP mint on-chain fails. Cơ chế "return funds" không được mô tả: BnzaExVault tự hoàn tiền qua on-chain revert, hay ExBot Worker cần gọi hàm riêng? Nếu là revert — USDC đã approve nhưng chưa transfer thì không cần return. Nếu cần hành động riêng — flow bị thiếu. | Cần biết để verify postcondition của test case A4 | Open |
| I-06 | High | UC §4 A8 | A8 ghi "enter `error` state; HL short open but stop not confirmed; alert operator". UC không nêu: (1) message cụ thể gửi cho operator; (2) recovery flow — operator phải làm gì tiếp theo? Đặt stop thủ công? Bot tự thử lại? `bot_safe_close` tự động? Trạng thái không có stop là rủi ro nghiệp vụ cao. | Cần biết để test expected result sau A8; alert message không thể verify nếu không có spec | Open |
| I-07 | Medium | OQ-EXBOT-05 | Preflight bước 4 kiểm tra "builder fee (5bps) confirmed on HL" — nhưng cơ chế check không được mô tả: gọi HL API endpoint nào? Dùng weight bao nhiêu? Đây là OQ-EXBOT-05 trong SRS (Open). Tester cần biết để test bước này một cách độc lập. | Block test case cho preflight builder fee check | Open |
| I-08 | Medium | message-list.md vs srs/spec.md §5 | message-list.md còn có E-EXBOT-003 ("Agent key awaiting approval") và E-EXBOT-004 ("Agent key expired"), E-EXBOT-014, E-EXBOT-015, E-EXBOT-016 — đây là các message từ luồng manual agent key cũ đã bị bỏ (UC-EXBOT-agent-key retired, OQ-EXBOT-16 Closed). SRS spec.md §5 không còn liệt kê E-003/004. Có nguy cơ tester thiết kế test case sai dựa trên các E-code đã obsolete này. Cần BA xác nhận E-003/004/014/015/016 có được xóa khỏi message-list.md không. | Tránh test dựa trên E-code đã obsolete | Open |
| I-09 | Low | UC §3 step 3 — thứ tự preflight | UC nêu 5 bước preflight "run in sequence" nhưng không nêu rõ khi nào từng check được chạy và liệu các HL API call trong preflight (margin check = weight 2) đã "consume" HL rate limit weight khi preflight fail ở bước sau. | Ảnh hưởng test HL rate limit trong preflight | Open |
| I-10 | High | SRS FR-EXBOT-002 vs UC §3 step 3 | FR-EXBOT-002 và UC ghi "builder fee (5bps) confirmed on HL" là bước preflight. Câu hỏi: builder fee check trong preflight là re-check hay lần check duy nhất? Nếu re-check — điều gì xảy ra nếu builder fee đã được confirm trước đây nhưng bị revoke sau đó? | Cần biết để design test case cho edge case fee revoke | Open |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|
