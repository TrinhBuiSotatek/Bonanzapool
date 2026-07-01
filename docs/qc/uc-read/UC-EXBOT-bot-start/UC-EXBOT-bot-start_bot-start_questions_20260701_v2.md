# Question Backlog — UC-EXBOT-bot-start

> **UC ID:** UC-EXBOT-bot-start  
> **Ngày tạo:** 2026-06-30  
> **Cập nhật:** 2026-07-01  
> **Nguồn:** `UC-EXBOT-bot-start_bot-start_audited_20260630_v1.md` §10.1  
> **Phiên bản:** v2 — I-01, I-03, I-08, I-09, I-10 chuyển Answered; I-04, I-05, I-07 chuyển Deferred

Priority: High = block test design, Medium = ảnh hưởng scope/coverage, Low = nice-to-know  
Status: Open | Answered | Deferred

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-02 | High | UC §4 A11 vs FR-EXBOT-025 | UC mô tả A11 (reconcile mismatch) là "actual size deviates > threshold" nhưng không định nghĩa threshold cụ thể là bao nhiêu. FR-EXBOT-025 cũng không nêu threshold. FR-EXBOT-036 có nhắc `drift_threshold` và OQ-EXBOT-11 đề cập `lpValueUsd × 3%` nhưng đây là ứng viên chưa được zen xác nhận (OQ-EXBOT-11 vẫn Open). Tester cần biết ngưỡng deviation cụ thể để thiết kế test case kiểm tra boundary. | Blocker cho test reconcile mismatch | Open |
| I-06 | High | UC §4 A8 vs states.md | A8 ghi "enter `error` state; HL short open but stop not confirmed; alert operator". Nhưng states.md state diagram cho thấy `stop_placing → safe_mode` (không phải `error`). (1) Trạng thái đích thực khi stop placement fails là `error` hay `safe_mode`? (2) Recovery flow là auto-recovery theo SAFE_MODE path (FR-EXBOT-050) hay cần operator can thiệp thủ công? E-EXBOT-009 xác nhận message alert ("Failed to place native stop on Hyperliquid. Bot cannot activate without a stop.") nhưng trạng thái và recovery vẫn mâu thuẫn giữa UC và states.md. | Blocker — trạng thái đích và recovery flow không nhất quán; cần BA/zen xác nhận states.md hay UC đúng | Open |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-01 | Low | UC §1 Actors vs SRS F-03 | UC §1 Actors không liệt kê "Signing Lambda" dù SRS F-03 và UC step 7/10 đề cập. | Signing Lambda là **internal infrastructure component** (không phải actor nghiệp vụ). Theo FR-EXBOT-080, Signing Lambda là IAM role — nó không khởi tạo hay nhận yêu cầu từ user, nó chỉ ký lệnh theo yêu cầu từ ExBot Worker. Actor trong UC §1 chỉ liệt kê các tác nhân có hành động nghiệp vụ trực tiếp. Thiếu này không gây lỗi test — tester đọc flow step là đủ. | SRS spec.md FR-EXBOT-080, IC-EXBOT-005 | 2026-07-01 | Answered |
| I-03 | Medium | UC §3 step 3 (preflight bước 2) | Hành vi khi HL API không phản hồi trong lúc preflight margin check? | **Bot không enter error state và không retry sau preflight.** Theo FR-EXBOT-050, HL API unreachable > 5 phút là điều kiện kích hoạt SAFE_MODE — nhưng điều này áp dụng cho bot đang hoạt động (active). Trong preflight, nếu HL API không phản hồi khi fetch `marginSummary`, toàn bộ start request **fail ngay lập tức với E-EXBOT-008** ("Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically."). Preflight không có retry loop — mọi failure đều block start với một error code cụ thể (FR-EXBOT-002). Không có partial bot record nào được tạo. | SRS spec.md FR-EXBOT-002, E-EXBOT-008, FR-EXBOT-050 | 2026-07-01 | Answered |
| I-08 | Medium | message-list.md vs srs/spec.md §5 | E-EXBOT-003/004/014/015/016 có được xóa khỏi message-list.md không? | **Có — đã xóa.** Theo changelog spec.md (2026-06-29): "remove E-003/004/014/015/016; add E-017". Các mã này thuộc luồng manual agent key cũ (UC-EXBOT-agent-key) đã bị retired. spec.md §5 hiện chỉ có 13 error code từ E-001 đến E-017 (không có E-003/004/014/015/016). Tester **không được** thiết kế test case dựa vào các mã này. E-EXBOT-017 là mã thay thế cho trường hợp agent key chưa được provisioned. | SRS spec.md §5 changelog 2026-06-29, OQ-EXBOT-16 (Closed) | 2026-07-01 | Answered |
| I-09 | Low | UC §3 step 3 — thứ tự preflight | HL API call trong preflight (margin check = weight 2) có consume HL rate limit weight khi preflight fail ở bước sau không? | **Có — weight bị consume bất kể kết quả.** Theo FR-EXBOT-091, `HLRateLimitDO` sliding-window kế toán: caller khai báo weight **trước khi** gọi API, weight bị trừ bất kể downstream success/failure. Trong preflight, margin check (bước 2) gọi HL `marginSummary` — weight được declare và consume ngay tại bước đó. Nếu preflight fail ở bước 3, 4 hoặc 5 sau đó, weight từ bước 2 vẫn đã bị tính vào quota 800/min. Điều này có nghĩa: nhiều start request liên tiếp thất bại ở bước 3+ đều tốn HL weight. Tester cần lưu ý khi thiết kế test phối hợp start + rate limit. | SRS spec.md FR-EXBOT-091, FR-EXBOT-002 | 2026-07-01 | Answered |
| I-10 | High | SRS FR-EXBOT-002 vs UC §3 step 3 | Builder fee check trong preflight là re-check hay lần check duy nhất? Nếu builder fee bị revoke sau khi đã confirm → điều gì xảy ra? | **Builder fee check trong preflight là kiểm tra tại thời điểm start** — không phải re-check định kỳ sau đó. Theo FR-EXBOT-002, đây là bước preflight độc lập (bước 4/5). Nếu builder fee bị revoke sau khi bot đã `active`, không có preflight nào chạy lại để phát hiện → hedge-sync có thể thất bại do HL từ chối lệnh vì fee không còn valid. Trong trường hợp đó, hedge-sync failure sẽ activate circuit breaker theo FR-EXBOT-040 (3 consecutive failures → open). Spec không định nghĩa cơ chế monitoring builder fee status định kỳ — đây là edge case chưa được cover. Tuy nhiên với test design cho UC-EXBOT-bot-start: chỉ cần test (a) fee confirmed → pass, (b) fee not confirmed → E-EXBOT-005. Trường hợp fee revoke sau start thuộc scope UC-EXBOT-hedge-sync. | SRS spec.md FR-EXBOT-002, E-EXBOT-005, FR-EXBOT-040 | 2026-07-01 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred By | Date | Status |
|----|----------|-----|----------|-----------------|-------------|------|--------|
| I-04 | High | UC §3 step 6 vs OQ-EXBOT-03 | Pool address + `wethIndex` cho USDC/WETH 0.3% trên Base và Optimism chưa được xác nhận (OQ-EXBOT-03 vẫn Open). Test case kiểm tra wethIndex per chain bị block. | OQ-EXBOT-03 là Phase 0 NV-12 verification task — zen/SOTATEK phải xác nhận pool address trước khi test có thể chạy. Deferred đến khi OQ-EXBOT-03 Closed. | Claude / QC agent | 2026-07-01 | Deferred |
| I-05 | High | UC §4 A4 | Cơ chế "return funds" khi LP mint fails: on-chain revert tự động hay ExBot Worker cần gọi hàm riêng? | IC-EXBOT-002 xác nhận BnzaExVault ABI chưa được zen confirm (OQ-EXBOT-08 Open). Không thể xác định postcondition của A4 cho đến khi ABI confirmed. Deferred đến khi OQ-EXBOT-08 Closed. | Claude / QC agent | 2026-07-01 | Deferred |
| I-07 | Medium | OQ-EXBOT-05 | Preflight bước 4 — builder fee check: gọi HL API endpoint nào? Weight bao nhiêu? | OQ-EXBOT-05 (NV-14: HL builder fee 5bps approval flow) vẫn Open trong SRS §9. Không thể thiết kế test case độc lập cho bước này cho đến khi OQ-EXBOT-05 được BA/zen resolved. | Claude / QC agent | 2026-07-01 | Deferred |

