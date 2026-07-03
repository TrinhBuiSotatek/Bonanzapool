# Question Backlog — UC-EXBOT-monitor-status

> **UC ID:** UC-EXBOT-monitor-status  
> **Feature:** View Active ExBot Status  
> **Generated:** 2026-07-01  
> **Source files:** `UC-EXBOT-monitor-status_monitor-status_audited_20260630_v1.md`  
> **Version:** v3 → v4 (cập nhật 2026-07-03: I-001, I-002, I-004, I-005, I-006, I-009, I-010, I-011, I-013 → Answered per `qc-responses-2026-07-03.md` @hienduong)

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)  
Status: Open | Answered | Deferred

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-003 | H | UC §3 step 3 và step 6 vs SRS ERD bảng `bot_runtime_state` + SRS FR-EXBOT-021 | UC step 6 tính drift % nhưng chỉ liệt kê một trong hai giá trị đầu vào cần thiết ở step 3. Cụ thể: `last_known_hl_short_size` đã có trong danh sách D1 reads, nhưng `target_short_size` — giá trị còn lại để tính drift — **hoàn toàn không được đề cập**. Theo SRS ERD, bảng `bot_runtime_state` có cột `target_short_size`. Tuy nhiên SRS FR-EXBOT-021 định nghĩa `targetShortEth = lpEthAmount × hedgeRatio` — tức là giá trị này được *tính lại* từ công thức, không phải đọc thẳng từ D1. Chưa rõ: Worker đọc `bot_runtime_state.target_short_size` đã lưu sẵn, hay tính lại từ `lpEthAmount × hedgeRatio` (cần thêm `lp_eth_amount` và `hedge_legs.target_ratio` vào danh sách reads). Ngoài ra, nếu giá trị mẫu số bằng 0, phép tính sẽ chia cho 0 — UC không định nghĩa hệ thống xử lý trường hợp này như thế nào. BA hoặc Tech Lead vui lòng xác nhận: (a) nguồn dữ liệu chính xác cho `targetShortEth` trong status response là gì; (b) bổ sung vào danh sách D1 reads ở UC step 3; (c) định nghĩa hành vi khi giá trị mẫu số bằng 0. | Nếu Worker dùng sai nguồn hoặc giá trị không cập nhật, drift % trên màn hình sẽ hiển thị sai — nhà đầu tư thấy thông tin lệch so với thực tế. Tester không biết phải kiểm tra giá trị nào là đúng để viết assertion, và không thể thiết kế test case cho trường hợp chia cho 0. | Open |

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-001 | H | UC §A3 vs `srs/states.md` (note 2026-06-18) + SRS FR-EXBOT-070 | UC Alternate Flow A3 mô tả `lifecycle_state='cooldown'` và message "USDC parked. Re-entry will be attempted automatically." Tuy nhiên cả hai đã bị loại bỏ trong HLD 2026-06-18. BA vui lòng viết lại A3 để mô tả behavior khi `lifecycle_state='closed'` sau `bot_safe_close`. | A3 đã được viết lại — `cooldown` removed. Thay bằng 2 cases: `lp_closing`: "Bot close is in progress. Please wait." (E-EXBOT-021); `closed`: "Bot safely closed. Funds have been returned to your wallet." (E-EXBOT-022). | @hienduong | 2026-07-03 | Answered |
| I-002 | H | UC §1 Actors vs FRD §4.11 FR-EXBOT-100 | UC định nghĩa primary actor là "USDC Investor (read-only)". FRD §4.11 FR-EXBOT-100 liệt kê Actor là "Admin". BA vui lòng xác nhận actor đúng: chỉ Investor, chỉ Admin, hay cả hai? | Actor đúng là **cả Investor lẫn Admin**. Auth: `X-Wallet-Address` header qua `accessControl` middleware. Admin bypass wallet ownership check; Investor phải match `bot.user_wallet_address` (403 nếu không match). Response schema giống nhau cho cả hai. UC §1 Actors cần update thêm Admin. | @hienduong | 2026-07-03 | Answered |
| I-004 | H | UC §3 step 3 vs UC §3 step 9 vs SRS ERD `bots` + `bot_runtime_state` | UC step 3 đọc `next_light_check_at` (tương lai) nhưng step 9 gắn nhãn "Last light-check timestamp" (quá khứ) — mâu thuẫn trực tiếp. BA vui lòng xác nhận timestamp nào cần trả về. | Đã fix — step 3 đọc `bot_runtime_state.last_light_check_at` (quá khứ). Bỏ `bots.next_light_check_at`. Label "Last light-check timestamp" ở step 9 giữ nguyên — đã đúng. | @hienduong | 2026-07-03 | Answered |
| I-005 | H | UC §4 Alternate Flows vs `srs/states.md` State Registry (15 active states) | UC chỉ mô tả response cho 3 lifecycle states trong số 15 states. Các states còn thiếu: `lp_rebalancing`, `lp_closing`, `error`, `closed`. UC không định nghĩa `closed` bot trả về 404 hay JSON. | Step 9: bổ sung đủ tất cả states. **A3a**: `lp_closing` (E-EXBOT-021). **A3b**: `closed` (E-EXBOT-022). **A6 mới**: `lp_rebalancing` — buttons disabled. **A7 mới**: `error` — chỉ enable Close Bot emergency. A4: `closed` ≠ 404; 404 chỉ khi không có bot record. | @hienduong | 2026-07-03 | Answered |
| I-006 | H | UC §3 steps 7–8 vs SRS FR-EXBOT-090 | Không có JSON response schema HTTP 200 nào được định nghĩa. BA/Tech Lead vui lòng định nghĩa đầy đủ schema: field names, types, optionality, null-handling. | Schema đã chốt: `{ "tick_lower": number\|null, "tick_upper": number\|null, "current_tick": number\|null, "range_state": "in"\|"out"\|null, "actual_short_eth": string\|null, "target_short_eth": string\|null, "drift_pct": number\|null, "margin_status": "ok"\|"warning"\|"critical"\|null, "last_light_check_at": string\|null, "safe_mode_reason": string\|null, "cooldown_end_at": string\|null }` | @hienduong | 2026-07-03 | Answered |
| I-007 | M | FRD §4.10 vs SRS §2 FR-EXBOT-090 | Trong FRD, FR-EXBOT-090 trỏ đến "HLRateLimitDO" (§4.10). Trong SRS, FR-EXBOT-090 trỏ đến "Operator Facade API". Cùng một FR number được gán cho hai requirements khác nhau. | **Xác nhận mâu thuẫn từ tài liệu.** Identifier đúng cho Operator Facade trong FRD là `FR-EXBOT-100` (§4.11). **Hành động cần làm:** BA căn chỉnh FR numbering giữa FRD và SRS; UC trace cần cập nhật sau khi căn chỉnh xong. | QC (đọc `frd.md` §4.10 + `spec.md` FR-EXBOT-090) | 2026-07-01 | Answered |
| I-008 | M | UC §FR Trace vs US-EXBOT-002 §Trace | FR-EXBOT-050 (SAFE_MODE Entry Conditions) liên quan trực tiếp đến Alternate Flow A1 nhưng thiếu trong UC FR trace. | **Xác nhận thiếu sót.** US-EXBOT-002 đã trace đúng đến `FR-EXBOT-050`. **Hành động cần làm:** BA thêm `FR-EXBOT-050` vào UC §FR Trace. | QC (đọc `spec.md` FR-EXBOT-050 + `us-002.md` §Trace) | 2026-07-01 | Answered |
| I-009 | M | UC §A4 vs `02_backbone/message-list.md` EXBOT section | A4 (no active bot) trả về HTTP 404 nhưng không có E-EXBOT-* code nào được đăng ký trong `message-list.md`. BA vui lòng đăng ký code và reference trong A4. | E-EXBOT-023 đã được đăng ký trong `message-list.md`; A4 đã reference code. | @hienduong | 2026-07-03 | Answered |
| I-010 | M | UC §A5 vs `02_backbone/message-list.md` EXBOT section | A5 (Operator Facade unavailable) trả về HTTP 503. Message chưa được đăng ký. BA vui lòng đăng ký hoặc xác nhận là generic Cloudflare response. | 503 là Cloudflare/infra-level response — không phải application error, không cần E-EXBOT code. Tester verify HTTP 503 status code; không cần verify message body. | @hienduong | 2026-07-03 | Answered |
| I-011 | M | UC §2 Preconditions, §3 step 2 vs SRS FR-EXBOT-090 | Cơ chế xác thực không được chỉ định: (a) POOL UI → Operator Facade; (b) Operator Facade → ExBot Worker. | **Đoạn 1:** `X-Wallet-Address` header. Thiếu header → 401; bị block → 403; ngoài whitelist → 403; Admin bypass whitelist. **Đoạn 2:** `X-Exbot-Internal-Auth` header với shared secret từ env var `EXBOT_INTERNAL_AUTH_TOKEN`. Thiếu/sai → 401 `UNAUTHORIZED_INTERNAL_CALL`. | @hienduong | 2026-07-03 | Answered |
| I-012 | M | UC §3 step 5 vs SRS FR-EXBOT-012 | Công thức rangeState không định nghĩa điều kiện biên inclusive/exclusive. | **Trả lời một phần từ tài liệu.** SRS FR-EXBOT-020 AC ngụ ý convention `tickLower <= currentTick < tickUpper`. `range_boundary_near` là `RebalanceReason` trong light-check worker, không xuất hiện trong status response. **Hành động cần làm:** BA xác nhận tường minh convention trong UC step 5. | QC (đọc `spec.md` FR-EXBOT-020 AC + FR-EXBOT-012) | 2026-07-01 | Answered |
| I-013 | M | UC §3 step 4 vs SRS FR-EXBOT-093 | UC không mô tả behavior khi `MarketDataDO` unavailable hoặc stale. BA/Tech Lead vui lòng tài liệu hóa fallback behavior. | Khi `MarketDataDO` unavailable hoặc stale: `current_tick: null`, `range_state: null` — response vẫn HTTP 200 với các fields còn lại bình thường. Không block, không retry, không 503. UI hiển thị "—" cho range state indicator. | @hienduong | 2026-07-03 | Answered |
| I-014 | L | UC §FR Trace vs FRD §4.1 vs SRS §2 | FR number được dùng cho hai nội dung khác nhau giữa FRD và SRS (FR-EXBOT-002, FR-EXBOT-003). | **Xác nhận mâu thuẫn từ tài liệu.** Đây là vấn đề format và numbering nhất quán, không phải mâu thuẫn logic nghiêm trọng. **Hành động cần làm:** BA clean up trong một pass riêng về FR numbering alignment — không block test design. | QC (đọc `spec.md` §FR-EXBOT-002/003 + `frd.md` §4.1) | 2026-07-01 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason for Deferral | Status |
|----|----------|-----|----------|---------------------|--------|
| _(No deferred questions.)_ | | | | | |
