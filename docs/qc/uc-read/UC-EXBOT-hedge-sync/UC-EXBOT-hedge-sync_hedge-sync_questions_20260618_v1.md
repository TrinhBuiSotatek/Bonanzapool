# Question Backlog

> UC ID: UC-EXBOT-hedge-sync
> Generated: 2026-06-18
> Source files: `docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260618_v1.md`
> Author: QC QnA Agent
> Version: v1

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-001 | H | UC §6 `BR-EXBOT-004`; `02_backbone/common-rules.md` | `BR-EXBOT-004` được cite trong UC nhưng không tồn tại trong `02_backbone/common-rules.md` (chỉ có trong `srs/spec.md` §4). BA vui lòng xác nhận: BR-EXBOT-* được định nghĩa ở đâu là canonical? Cần bổ sung BR-EXBOT-004 vào common-rules.md không? | Tester không thể resolve BR-EXBOT-004 qua đường dẫn canonical — nguy cơ miss update khi spec thay đổi mà UC không cập nhật. | Open |
| I-002 | H | `srs/spec.md` §5; `02_backbone/message-list.md` | Tất cả `E-EXBOT-*` codes (E-EXBOT-007, E-EXBOT-008, E-EXBOT-011, v.v.) không có trong `message-list.md` backbone. BA vui lòng bổ sung section `## EXBOT` vào `message-list.md` với đầy đủ E-EXBOT-001 đến E-EXBOT-013. | Tester phải tra spec.md thay vì message-list.md — không có nguồn canonical thống nhất cho error messages của hedge-sync. | Open |
| I-003 | H | UC §4 A3; FR-EXBOT-040 | UC mô tả AF-A3 "HL order rejection → enqueue notification" nhưng không nêu: (1) notification gửi qua queue nào (implied `notification` queue nhưng không explicit); (2) content notification cho investor là gì (E-EXBOT-007 có phải message đúng không?); (3) INV-STOP (stop replacement) có được bỏ qua khi delta order bị reject, hay vẫn execute? BA vui lòng xác nhận cả 3 điểm. | Tester không thể viết expected result đầy đủ cho AF-A3: không biết queue name, message content, và INV-STOP behavior khi order fail. | Open |
| I-004 | H | UC §3 (missing step); FR-EXBOT-060; `frd.md` §4.7 | FR-EXBOT-060 nêu rõ "Margin status shall be updated only during hedge-sync preflight (HL `marginSummary` fetch)." Tuy nhiên bước fetch `marginSummary` hoàn toàn vắng mặt trong UC §3 Main Success Scenario lẫn §4 Alternate Flows. BA vui lòng: (1) thêm bước fetch `marginSummary` vào UC §3 với vị trí chính xác trong flow; (2) mô tả nhánh khi `margin_status='warning'` (lệnh tăng size bị block — ở bước nào?); (3) mô tả nhánh khi `margin_status='critical'` tại preflight hedge-sync. | Tester không thể thiết kế test case cho margin warning/critical trong hedge-sync flow — không biết bước nào bị block và response là gì. | Open |
| I-005 | H | UC §3 step 4; FR-EXBOT-091 | UC không có alternate flow khi `HLRateLimitDO` trả về `{allowed: false, retryAfterMs}` trước khi fetch `clearinghouseState`. FR-EXBOT-091 nêu caller phải không proceed với HL call và phải re-queue. BA vui lòng bổ sung alternate flow: "HLRateLimitDO returns allowed=false → worker re-queues message với retryAfterMs delay; không submit HL call." | Tester không biết expected behavior khi HL rate limit bị vượt ngưỡng giữa hedge-sync — cần alternate flow rõ ràng để thiết kế test. | Open |
| I-006 | M | UC §3 step 8; FR-EXBOT-035; OQ-EXBOT-02 | INV-STOP protocol (§19.5 SPEC v5.2.6) có 2 path: (a) place-before-cancel và (b) cancel-then-place, tùy kết quả NV-3 (OQ-EXBOT-02 — Open). UC chỉ cite "§19.5" mà không nêu path nào. BA vui lòng cập nhật UC sau khi OQ-EXBOT-02 (NV-3) được verify. | Tester không thể verify sequence cụ thể của INV-STOP (cancel trước hay place trước) cho đến khi OQ-EXBOT-02 resolved. | Open |
| I-007 | M | UC §3 step 3; FR-EXBOT-026 | UC không mô tả điều kiện kích hoạt `UserLockDO.heartbeat()`. FR-EXBOT-026 nêu: "If work exceeds 30 seconds, the worker extends the lease via `heartbeat()`." Không có step hay alternate flow nào đề cập trigger condition và failure handling cho heartbeat. BA vui lòng bổ sung note vào UC §3. | Tester không biết khi nào heartbeat được gọi và test case nào cần cover (ví dụ: work > 30s → heartbeat called, heartbeat fails → lease lost). | Open |
| I-008 | M | UC §2 Preconditions; FR-EXBOT-080; FR-EXBOT-082 | UC không có precondition hay exception flow cho trường hợp HL agent key bị revoke trong khi hedge-sync đang chạy. FR-EXBOT-082 nêu: "decryption failure → log the error, and enter SAFE_MODE." BA vui lòng bổ sung exception flow: "Agent key decryption fails (revoked/expired mid-flight) → SAFE_MODE entry; log error without key material." | Tester không có flow để test trường hợp key bị revoke giữa chừng — expected behavior (SAFE_MODE) chưa documented trong UC. | Open |
| I-009 | M | UC §4 A4; FR-EXBOT-036 | UC dùng cụm "partial mismatch" trong AF-A4 nhưng không định nghĩa ngưỡng cụ thể. FR-EXBOT-036 dùng `\|actual - target\| > drift_threshold`. BA vui lòng xác nhận: ngưỡng trigger partial repair trong reconcile là `\|actual - target\| > drift_threshold` (giống light-check threshold), hay một ngưỡng riêng dành cho reconcile? | Tester không biết khi nào reconcile mismatch đủ nhỏ được bỏ qua, và khi nào đủ lớn để trigger partial repair. | Open |
| I-010 | H | UC §7 FR Trace; `usecases/index.md` FR Trace | FR Trace trong UC body §7 (`FR-EXBOT-022, 024, 025, 026, 027, 036`) khác với FR Trace trong `usecases/index.md` (`FR-020, 021, 022, 024, 025, 026, 027, 035`). Cụ thể: UC body thiếu FR-020 (Delta-Only — P0), FR-021 (BigDecimal — P0), FR-035 (INV-STOP — P0); index thiếu FR-036. BA vui lòng reconcile FR Trace giữa UC body §7 và index: thêm FR-020, FR-021, FR-035 vào UC §7; xác nhận FR-036 có đúng scope không. | Tester dùng FR Trace để xác định scope test — nếu không nhất quán, coverage sẽ bị hổng (bỏ sót FR-020, FR-021, FR-035 là 3 FR P0 critical). | Open |
| I-011 | M | UC §3 step 13; FR-EXBOT-030; FR-EXBOT-035 | UC step 13 "Recompute `stop_trigger_px`; record new `stop_cloid`, `stop_price` in `hedge_legs`" tạo ambiguity: stop đã được placed ở step 8 (INV-STOP), vậy step 13 có place lệnh stop mới không, hay chỉ update D1 record với data từ lệnh stop đã placed? BA vui lòng làm rõ: step 8 = place stop; step 13 = chỉ recompute giá trigger và update D1 record (không place lệnh mới). | Tester không biết expected behavior của step 13: nếu step 13 place lệnh mới → có 2 lệnh stop trên HL; nếu chỉ update D1 → cần verify D1 consistency sau step 8. | Open |
| I-012 | H | UC §3 step 5-6; FR-EXBOT-022; OQ-EXBOT-04 | UC không có alternate flow khi `\|delta\| < minimum_order_size`. OQ-EXBOT-04 (NV-13 — Open): "HL ETH-USD perp minimum order size / dust handling rules — Blocks FR-EXBOT-022." Không có xử lý dust delta trong UC. BA vui lòng bổ sung alternate flow sau khi OQ-EXBOT-04 resolved: "If \|delta\| < minimumOrderSize → skip order submission; record `rebalance_attempts.status='skipped'`; không increment circuit breaker." | Tester không thể thiết kế boundary test cho "delta quá nhỏ" — nếu hệ thống submit delta dust, HL sẽ reject → circuit breaker increment không cần thiết, gây false positive. | Open |

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
