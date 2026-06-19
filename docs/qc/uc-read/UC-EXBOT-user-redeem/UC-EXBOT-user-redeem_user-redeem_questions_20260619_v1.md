# Question Backlog — UC-EXBOT-user-redeem

> Generated: 2026-06-19  
> Source files: `docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260619_v1.md`

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-01 | High | UC §3 bước 7; states.md §close_operations | UC §3 bước 7 ghi `state='lp_closed→funds_returned'` như thể hai trạng thái xảy ra đồng thời trong một bước. Tuy nhiên states.md định nghĩa `lp_closed` và `funds_returned` là hai state riêng biệt trong close_operations của user_redeem. Không rõ: (a) worker update `state='lp_closed'` trước, sau đó update `state='funds_returned'` ngay sau khi tạo row? Hay (b) cả hai được set trong cùng một D1 transaction? (c) Khi worker crash giữa `lp_closed` và `funds_returned`, resume flow là gì? BA/Tech Lead vui lòng làm rõ: `state='lp_closed'` và `state='funds_returned'` là hai update riêng biệt hay một transaction? Nếu riêng biệt, resume strategy khi worker crash tại `lp_closed` là gì? | Tester không thể viết test case cho crash recovery giữa hai state mà không biết thứ tự và atomicity | Open |
| I-02 | High | UC §A2; states.md §lifecycle; SRS FR-EXBOT-070 | UC §A2 mô tả khi hedge close thất bại thì `close_operations.state='residual_hl_liability'`, nhưng không định nghĩa `bots.lifecycle_state` trong trường hợp này. States.md mô tả `lp_closing → closed` khi close complete, nhưng nếu hedge close fail và ghi `residual_hl_liability`, bot `lifecycle_state` là gì? `closed` hay vẫn `lp_closing`? UC §5 Postconditions liệt kê `close_operations.state='done' or 'residual_hl_liability'` nhưng không nói lifecycle_state tương ứng khi `residual_hl_liability`. BA/Tech Lead vui lòng xác nhận: khi `close_operations.state='residual_hl_liability'`, `bots.lifecycle_state` là gì? | Tester cần biết `lifecycle_state` sau hedge fail để viết expected result cho A2; nếu bot vẫn ở `lp_closing`, các worker khác có skip nó không? | Open |
| I-03 | High | UC §3 bước 5; states.md §lifecycle | UC không mô tả bước chuyển `bots.lifecycle_state` từ `active`/`paused`/`safe_mode` sang `lp_closing`. States.md §lifecycle chỉ rõ transition `active → lp_closing` xảy ra khi "close request". Không rõ: (a) Worker nào/bước nào set `lifecycle_state='lp_closing'`? (b) Khi nào set — khi tạo close_operations row hay khi receive queue message? (c) Nếu Worker set `lp_closing` sau khi LP đã đóng on-chain, khoảng thời gian giữa `BnzaExVault.redeem()` và Worker arrive có thể có trạng thái không nhất quán. BA/Tech Lead vui lòng xác nhận: `bots.lifecycle_state='lp_closing'` được set ở bước nào trong user_redeem worker? | Tester không thể kiểm tra `lp_closing` được set đúng thời điểm mà không biết bước nào set nó; light-check skip bots trong `lp_closing` (SRS) | Open |
| I-04 | High | UC §7 FR Trace; SRS spec.md | UC §7 FR Trace liệt kê `FR-EXBOT-070, FR-EXBOT-071` nhưng `FR-EXBOT-071` không tồn tại như một section riêng trong spec.md (spec nhảy từ FR-EXBOT-070 sang FR-EXBOT-072). FRD cũng không có entry FR-EXBOT-071. Không rõ: (a) FR-EXBOT-071 có phải là typo của FR-EXBOT-070 không? (b) Hay FR-EXBOT-071 là một FR đã bị xóa/merged vào FR-EXBOT-070? BA vui lòng xác nhận: FR-EXBOT-071 có phải typo? Nếu không, FR-EXBOT-071 được định nghĩa ở đâu? Cập nhật FR Trace để chính xác. | Tester không thể verify compliance với FR-EXBOT-071 vì nó không tồn tại trong spec/FRD; traceability bị gián đoạn | Open |
| I-05 | Medium | UC §3; SRS FR-EXBOT-091 | UC §3 không đề cập đến `HLRateLimitDO` trước khi gọi HL full close (`closeShortReduceOnlyIoc`). Theo SRS FR-EXBOT-091, mọi HL API call phải khai báo weight và nhận `{allowed: boolean, retryAfterMs}`. Khi `HLRateLimitDO` trả `allowed=false` và worker đang giữ `UserLockDO` lease (TTL=90s), không rõ worker có release lock trước re-queue không. BA/Tech Lead xác nhận: khi `HLRateLimitDO` từ chối trong user_redeem, worker release `UserLockDO` trước re-queue không? Re-queue strategy là gì? | Thiếu test case quan trọng về rate limit behavior trong user_redeem; nếu lock không được release có thể block concurrent operations | Open |
| I-06 | Medium | UC §3; SRS FR-EXBOT-080, FR-EXBOT-082 | UC §3 không đề cập bước giải mã HL agent key (AES-GCM decrypt từ `hl_agent_keys.encrypted_key`) trước khi ký lệnh HL. Đây là bước bắt buộc theo SRS FR-EXBOT-080. Trong user_redeem: (a) nếu agent key đã bị revoke (`revoked_at IS NOT NULL`) thì worker xử lý thế nào — vào SAFE_MODE hay ghi `residual_hl_liability`? (b) Nếu `expires_at` đã qua thì sao? BA/Tech Lead xác nhận: trong user_redeem, nếu agent key bị revoke hoặc expired, hành vi là gì? | Tester cần failure path của agent key decryption để thiết kế test case bảo mật; user_redeem là P0 flow | Open |
| I-07 | Medium | UC §3 bước 13; SRS FR-EXBOT-070; erd.md | UC §3 bước 13 ghi "Send HL-portion USDC to investor (tracked in RedemptionQueue ledger)" nhưng không định nghĩa cơ chế gửi: worker gọi contract function nào? SRS FR-EXBOT-070 mô tả user_redeem không dùng `RedemptionQueue.createRequest/fulfillRequest` (đó là bot_safe_close), nhưng UC §3 bước 13 vẫn nói "tracked in RedemptionQueue ledger" — có thể mâu thuẫn. BA/Tech Lead làm rõ: user_redeem gửi HL-portion USDC bằng cách nào? Contract function nào được gọi? "RedemptionQueue ledger" ở đây có nghĩa là gì? | Tester không thể test bước transfer HL-portion mà không biết cơ chế; nếu dùng fulfillRequest phải include Operator action trong test | Open |
| I-08 | Low | UC §5 Postconditions; UC §3 | UC có hai mục `## Postconditions` — mục §5 có nội dung đúng và đầy đủ. Mục thứ hai (ngay sau §5) là placeholder template chưa xóa: "System state reflects the completed operation", "Relevant audit log entries recorded (NFR-ADM-005)", "Affected bot state transitions persisted in D1". NFR-ADM-005 là NFR của module Admin, không phải ExBot. BA vui lòng xóa phần placeholder Postconditions thứ hai. | Gây nhầm lẫn; Tester có thể hiểu nhầm NFR-ADM-005 áp dụng cho ExBot | Open |
| I-09 | Low | UC §Trigger; SRS flows.md F-04 | UC §Trigger ghi: "User navigates to the relevant screen or initiates the described action." — placeholder template chưa cập nhật. Trigger thực tế là: nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` on-chain, `RedemptionEvent` phát, Redeem Event Watcher detect và enqueue vào `user_redeem` queue. BA vui lòng cập nhật §Trigger mô tả đúng trigger on-chain. | Tester có thể nhầm đây là UC có UI trigger thay vì on-chain event trigger | Open |
| I-10 | Medium | UC §3 bước 9; SRS FR-EXBOT-070 | UC §3 bước 9 ghi `closeShortReduceOnlyIoc` nhưng không định nghĩa behavior khi partial fill: worker có re-submit với size còn lại không? Giới hạn retry là gì? Partial fill có thể khiến reconcile (bước 11) fail và trigger A2 sai cách. BA/Tech Lead xác nhận: khi `closeShortReduceOnlyIoc` chỉ partial fill, worker xử lý thế nào? Re-submit hay count as failure? | Tester cần partial fill behavior để thiết kế test hedge close không hoàn chỉnh | Open |

Priority: High = blocks test design, Medium = affects scope/coverage, Low = cleanup/traceability  
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|

_(No answered questions yet.)_

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|

_(No deferred questions.)_
