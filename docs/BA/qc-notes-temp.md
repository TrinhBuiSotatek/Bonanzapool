## UC-EXBOT-bot-safe-close

| # | Câu hỏi | Trả lời | Note |
|---|---------|---------|------|
| Q1 | LP close method conflict: FR-EXBOT-073 step 4 ghi `BnzaExVault.redeem(tokenId)`, UC step 5 và US-EXBOT-009 AC-009-1 ghi `vault.executeStrategy(RedeemStrategyV1, ...)` — cái nào đúng? | `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` là đúng. FR-EXBOT-073 step 4 đã được sửa: LP close qua BnzaExPositionManager, fees routed via LpFeeOps, PositionClosed event emitted. | ✅ Confirmed |
| Q2 | US-EXBOT-012 AC-012-1 vẫn còn ghi `BnzaExVault.vaultClose` và USDC parked vào `uninvested_balances` — park/redeploy đã bị drop theo HLD 2026-06-18. | AC-012-1 đã được cập nhật: bỏ dòng vaultClose/park, thêm `vault.executeStrategy(RedeemStrategyV1)` + `RedemptionQueue.createRequest` + `fulfillRequest`. | ✅ Confirmed |
| Q3 | UC §2 Preconditions chưa nêu rõ `bots.status` prerequisite — bot phải ở status nào mới trigger được `bot_safe_close`? Trigger trên bot đã `closed` có bị reject không? | Trigger chỉ hợp lệ khi `bots.status NOT IN ('closed', 'closing')`. Reject được enforce ở DB level bởi UNIQUE constraint trên `close_operations.idempotency_key` (FR-EXBOT-072). UC §2 Preconditions đã được update. | ✅ Confirmed |
| Q4 | Close Worker được trigger qua queue message hay direct call? Không có dedicated `bot_safe_close` queue trong FR-EXBOT-010. F-05 diagram quá simplified. | Nhờ chị Trinh check với dev team. | ⏳ Pending Tech Lead |
| Q5 | UC A1 nói "admin escalation notification sent" khi hedge fail nhưng không define message content, không có E-code. | Thêm E-EXBOT-018: "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability." — internal alert. UC A1 và message-list.md đã được update. | ✅ Confirmed |
| Q6 | `bots.status='closing'` được set ở bước nào — step 2 hay step 8? | Set tại **step 1** — ngay khi trigger fires và `close_operations` row được tạo. `lifecycle_state='lp_closing'` set đồng thời. Giữ đến step 11 khi `fulfillRequest` hoàn tất → chuyển sang `'closed'`. UC step 1 đã được update. | ✅ Confirmed |
| Q7 | Close Worker có cần acquire `UserLockDO` không? UC step 2 mention nhưng không nói bắt buộc. FR-EXBOT-026/092 chỉ specify cho hedge-sync. | Nhờ Tech Lead xác nhận. | ⏳ Pending Tech Lead |
| Q8 | FR-EXBOT-073 step 3 nói "stop cancelled" nhưng `states.md` close_operations không có state `stop_canceled` — là action hay state? | `stop cancelled` là **action**, không phải state riêng. `closeShortReduceOnlyIoc` và `replaceStopProtected(size=0)` đều là actions trong step 2 (`hedge_close_pending`). `close_operations.state` chỉ advance lên `hedge_closed` sau khi reconcile confirm HL size = 0 AND stop đã cancel. FR-EXBOT-073 đã được update. | ✅ Confirmed |
| Q11 | Khi hedge fail → SAFE_MODE, AC-009-2 nói `bots.status='safe_mode'` nhưng không specify `bots.lifecycle_state`. | Cả hai đều chuyển sang `'safe_mode'` — `lifecycle_state` và `status` có cùng giá trị per `states.md`. AC-009-2 đã được update để ghi rõ `lifecycle_state='safe_mode'`. | ✅ Confirmed |

---

## UC-EXBOT-bot-start

| # | Câu hỏi | Trả lời | Note |
|---|---------|---------|------|
| I-02 | Threshold deviation cụ thể cho A11 (reconcile mismatch) là bao nhiêu? FR-EXBOT-025 không nêu, FR-EXBOT-036 đề cập `lpValueUsd × 3%` nhưng OQ-EXBOT-011 chưa confirm. | `drift_threshold = lp_value_usd × 3%`. Behavior logic của A11 (mismatch → enqueue `partial_repair` + alert) đã confirmed. Test boundary của A11 deferred đến khi OQ-EXBOT-011 được closed. | ⏳ Pending khách (zen) — OQ-EXBOT-011 |
| I-06 | Khi stop placement fails (A8), trạng thái đích là `error` (theo UC) hay `safe_mode` (theo states.md)? Recovery là auto hay manual? | `safe_mode` là đúng per `states.md` (`stop_placing → safe_mode`). UC A8 đã được fix. Auto-recovery per FR-EXBOT-050: retry khi HL responsive + 3 reconciles succeed; nếu irrecoverable → `bot_safe_close`. | ✅ Confirmed |

---

## UC-EXBOT-deep-audit

| # | Câu hỏi | Trả lời | Note |
|---|---------|---------|------|
| Q-DA-01 | Thiếu message content và E-code cho 2 stuck marker notifications (`stop_trigger_crossed_at > 30min` và `stop_replacing_started_at > 60s`). | Đã thêm E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." và E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required." vào message-list.md. UC A4 đã updated để reference cả 2 E-code. Cả 2 là internal alert. | ✅ Confirmed |
| Q-DA-02 | Deep-audit có check stuck markers trên **paused bot** không? Edge case: bot active → stop fires → user pause → marker stuck > 30min. | Confirmed — deep-audit chạy stuck marker detection (steps 4–5) cho cả paused bots. Nếu triggered, bot chuyển `paused → safe_mode`. UC A2 và states.md đã được update. Source: FR-EXBOT-016 acceptance criteria. | ✅ Confirmed |
| Q-DA-03 | Deep-audit worker đọc bots theo cách nào — scan tất cả shards hay cron per shard? Ảnh hưởng test design cho Phase B (4 shards). | Đây là implementation architecture decision của worker — BA không đủ context về D1 sharding setup và Cloudflare Worker limits. Behavior nghiệp vụ không thay đổi dù theo cách nào. | ⏳ Pending Tech Lead |
| Q-DA-04 | Khi cadence switch 6h → 1h, worker có update `bots.next_deep_audit_at` không, hay cron tự handle? | Pending Tech Lead xác nhận. | ⏳ Pending Tech Lead |

---

## UC-EXBOT-hedge-sync

| # | Câu hỏi | Trả lời | Note |
|---|---------|---------|------|
| Q1 | delta=0 → skip HL order rồi làm gì với stop replacement? | Pending OQ-EXBOT-013. | ⏳ Pending khách (zen) — OQ-EXBOT-013 |
| Q2 | INV-STOP protocol: place trước cancel, hay cancel trước place? | Pending OQ-EXBOT-002 — cần verify HL support place-before-cancel. | ⏳ Pending khách (zen) — OQ-EXBOT-002 |
| Q3 | `marginSummary` fetch: trước hay sau khi acquire `UserLockDO`? | Pending OQ-EXBOT-014. | ⏳ Pending Tech Lead — OQ-EXBOT-014 |
| Q5 | Partial fill có tăng `failure_count` trong circuit breaker không? | Partial fill **không tăng** `failure_count`. Routes sang `partial_repair` queue (FR-EXBOT-036) — repair path riêng, không phải failure path. Chỉ `status='failed'` (A3) mới gọi `incrementCircuitBreaker`. UC A4 đã được update. | ✅ Confirmed |
| Q6 | `lpValueUsd` formula chưa confirm — OQ-EXBOT-011 còn Open. | `partial_repair` dùng cùng `drift_threshold = max($25, lpValueUsd × 3%)` với light-check (FR-EXBOT-036). Test boundary deferred đến khi OQ-EXBOT-011 closed. | ⏳ Pending khách (zen) — OQ-EXBOT-011 |
| Q7 | delta=0, không gửi lệnh HL → `entry_price` / `liq_price` có được update không? | Deferred — blocked bởi Q1 (OQ-EXBOT-013). Sẽ update khi Q1 được closed. | ⏳ Pending khách (zen) — OQ-EXBOT-013 |
| Q8 | FR Trace trong UC vs SRS §7 UC Inventory không khớp — thiếu FR-020/021/035, thừa FR-036. | UC §7 thêm FR-020/021/035. SRS §7 UC Inventory thêm FR-036 cho `uc-hedge-sync`. Đã fix. | ✅ Confirmed |
| Q9 | Race condition: circuit chuyển `open` giữa enqueue và execute. | Worker recheck `circuit_breakers.state` tại execution time (step 2) — nếu `open` thì discard (status='skipped'), không gửi lệnh HL. UC step 2 đã được update. Ordering chi tiết (trước/sau UserLockDO) là Tech Lead decision. | ✅ Confirmed |
| Q10 | `rebalance_attempts.reason` ghi giá trị gì cho A2 (stateVersion mismatch) và A6 (delta=0)? | Cả hai = original RebalanceReason[] từ message payload. Không thêm enum value mới — canonical enum giữ nguyên per FR-EXBOT-023. UC A2 và A6 đã được update. | ✅ Confirmed |
