# Test Cases — UC-EXBOT-bot-safe-close System-Initiated Safe Close

> **Source:** UC-EXBOT-bot-safe-close_bot-safe-close_audited_20260709_v4.md
> **Scenarios:** UC-EXBOT-bot-safe-close_bot-safe-close_scenarios_20260709_v4.md
> **Generated:** 2026-07-02
> **Updated:** 2026-07-09 (v3: **Q4 RESOLVED (BA 2026-07-04)**, Q9 still pending)
> **Language:** Vietnamese (per project global rules)
> **Domain/Architecture:** ExBot Lambda + Hyperliquid + BnzaExVault (on-chain) + RedemptionQueue (on-chain) + Redis Redlock via ElastiCache (User Lock). No UI — logic-only / backend pipeline.

---

## Coverage Summary

| Category | Count |
|---|---:|
| Total Test Cases | 39 |
| High (P0) | 21 |
| Medium (P1) | 18 |

---

## I. Operation: Bot safe close initiation (trigger)

### I.1. Functional verification — Operation: Bot safe close initiation (trigger)

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_001 | Verify trigger is accepted when bot is in valid state (active) | Bot tồn tại với `bots.status='active'`, `bots.lifecycle_state='active'`, `hedge_legs.last_known_hl_short_size > 0`, không có `close_operations` row với `kind='bot_safe_close'` nào tồn tại cho bot này, HL agent key có `key_status='active'` | Kích hoạt bot_safe_close qua một trong 5 trigger conditions (ví dụ: admin force-close qua POST /api/exbot/close) | 1. Quan sát `close_operations` row được tạo: `kind='bot_safe_close'`, `state='requested'`, `idempotency_key` được populate, `trigger_reason` được populate đúng lý do trigger. 2. Quan sát `bots.status` chuyển sang `'closing'`, `bots.lifecycle_state` chuyển sang `'lp_closing'`. | High |
| TC_002 | Verify trigger is rejected when bot is already 'closed' | Bot tồn tại với `bots.status='closed'`, `bots.lifecycle_state='closed'` | Gửi bot_safe_close trigger cho bot đã closed qua bất kỳ trigger source nào trong 5 điều kiện | 1. Hệ thống từ chối trigger. 2. Không có `close_operations` row mới được tạo. 3. API trả về E-EXBOT-012: "Bot {id} is already closed. No action needed." | High |
| TC_003 | Verify duplicate trigger is rejected via idempotency (bot in 'closing' state) | Bot tồn tại với active `close_operations` row (`kind='bot_safe_close'`), `bots.status='closing'` | Gửi bot_safe_close trigger thứ hai cho cùng bot đang trong quá trình đóng | 1. Hệ thống từ chối duplicate trigger qua UNIQUE constraint trên `close_operations.idempotency_key`. 2. Chỉ có đúng một `close_operations` row tồn tại; không có double settlement. **✅ Note:** **Q4 RESOLVED (2026-07-09):** "Close Worker" là ExBot Lambda (architecture component). Trigger mechanism (5 conditions từ workers + admin API) đã được xác nhận. UNIQUE constraint behavior không phụ thuộc vào Q4 answer. | High |
| TC_004 | Verify each of 5 trigger conditions creates close_operations with correct trigger_reason | Bot tồn tại với `bots.status IN ('active', 'safe_mode')`, không có close operation tồn tại | Lần lượt kích hoạt bot_safe_close với từng trigger condition riêng biệt: (1) circuit breaker exhausted, (2) margin critical irrecoverable, (3) 3 stops trong 7 ngày, (4) partial_repair exhausted 3 lần liên tiếp, (5) admin force-close | Mỗi trigger tạo đúng một `close_operations` row với `trigger_reason` được populate đúng theo loại trigger tương ứng; `idempotency_key` UNIQUE được enforce. **⚠️ Note:** Liên quan đến **Q9 (CẦN CONFIRM TỪ BA)** — format cụ thể của `trigger_reason` enum values chưa được định nghĩa. BA cần xác nhận: `circuit_breaker_exhausted`, `margin_critical`, `3_stops_7d`, `partial_repair_exhausted`, `admin_force_close`. ✅ **Q4 RESOLVED** — "Close Worker" là ExBot Lambda (architecture component). 5 trigger conditions đến từ: deep-audit worker, hedge-sync worker, partial_repair worker, light-check/hedge-stopped, HOẶC admin API (`POST /api/exbot/close`). Không có dedicated `bot_safe_close` queue trong 11 queues (FR-EXBOT-010). | Medium |
| TC_005 | Verify admin force-close with missing required fields is rejected | Admin được authenticate với valid OPERATOR facade token | Gọi POST /api/exbot/close với valid botId nhưng thiếu field `reason` | 1. Request bị từ chối với validation error. 2. Không có `close_operations` row được tạo. 3. Audit trail cho thấy reason là bắt buộc | Medium |

### I.2. Integration & State verification — Operation: Bot safe close initiation (trigger)

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_006 | Verify close_operations state machine progresses sequentially through all valid states | Bot với valid trigger condition, không có existing close operation | Quan sát `close_operations.state` tại mỗi bước của quá trình đóng | `close_operations.state` tiến triển đúng thứ tự: `requested` → `hedge_close_pending` → `hedge_closed` → `lp_closed` → `redemption_queued` → `done`; không có state nào bị skip; không có transition sai thứ tự | High |
| TC_007 | Verify bots.status='closed' only set after fulfillRequest completes — not earlier | Bot đang trong quá trình đóng ở intermediate step | Quan sát `bots.status` khi fulfillRequest chưa được gọi (ví dụ: tại `redemption_queued`) | `bots.status` vẫn giữ giá trị `'closing'` cho đến khi fulfillRequest hoàn tất; không set sớm thành `'closed'` | Medium |

---

## II. Operation: Hedge close operation

### II.1. Functional verification — Operation: Hedge close operation

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_008 | Verify delta computation uses BigDecimal for full hedge close | Bot với existing HL short position (`actualShortEth > 0`) | Kích hoạt bot_safe_close; tính delta = 0 - actualShortEth | 1. Delta được tính đúng cho full close. 2. BigDecimal được sử dụng, không phải float/Number. 3. Precision được duy trì; không có precision loss | High |
| TC_009 | Verify hedge close order submitted with deterministic cloid | Bot với existing HL short position, ExBot Lambda (Close Worker) acquire User Lock (Redis Redlock via ElastiCache) lease | Gọi `closeShortReduceOnlyIoc(size, cloid)` với deterministic cloid = keccak256("bnza:{botId}:{attemptId}:{stage}:{version}") | 1. `closeShortReduceOnlyIoc` được submit với đúng deterministic cloid. 2. HL có thể deduplicate trên cùng cloid; không tạo duplicate order. | Medium |
| TC_010 | Verify stop cancelled via INV-STOP protocol — not direct cancel-then-place | Bot với active reduce-only stop, hedge close đang xử lý | Thực thi bước hedge close yêu cầu cancel stop | 1. `replaceStopProtected(size=0)` được gọi (INV-STOP protocol). 2. KHÔNG sử dụng direct `cancelStop` rồi `placeStop` — đây là architectural violation | High |
| TC_011 | Verify reconcile confirms size=0 AND stop cancelled before advancing to hedge_closed | `closeShortReduceOnlyIoc` đã submit, stop đã cancelled | 1. Fetch clearinghouseState từ HL sau khi hedge close order. 2. Verify actual short size = 0 VÀ stop đã cancelled. 3. Chỉ khi đó mới advance `close_operations.state` sang `hedge_closed` | 1. `close_operations.state` advance sang `hedge_closed` chỉ khi CẢ HAI điều kiện được confirm (size=0 VÀ stop cancelled). 2. Nếu một trong hai không được meet, state không advance | High |
| TC_012 | Verify hedge close failure after 3 retries leads to residual_hl_liability | Bot với existing HL short position, HL API configured để return error | 1. Attempt `closeShortReduceOnlyIoc`. 2. Retry 3 lần, mỗi lần thất bại. 3. Sau 3 lần thất bại, escalate lên A1 path | 1. `close_operations.state='residual_hl_liability'`. 2. `bots.status='safe_mode'`. 3. `bots.lifecycle_state='safe_mode'`. 4. LP KHÔNG được đóng. 5. Admin notification E-EXBOT-018 được gửi: "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability." | High |
| TC_013 | Verify LP close never attempted before hedge_closed confirmed | Bot đang xử lý hedge close, reconcile chưa confirm | Attempt trigger LP close step trước khi `hedge_closed` được confirm | Hệ thống ngăn chặn LP close; LP close chỉ tiến hành sau khi `hedge_closed` được confirm; hedge-first invariant được enforce | High |
| TC_014 | Verify bots.lifecycle_state and bots.status both = 'safe_mode' on SAFE_MODE entry | Bot enter SAFE_MODE qua bất kỳ trigger nào | Quan sát state sau khi bot enter SAFE_MODE | CẢ HAI `bots.lifecycle_state='safe_mode'` VÀ `bots.status='safe_mode'`; hai field không được diverge | Medium |
| TC_015 | Verify bot_safe_close succeeds even when circuit_breakers.state='open' | Bot với `circuit_breakers.state='open'` | Kích hoạt bot_safe_close khi circuit breaker đang open (ví dụ: qua 3rd stop condition) | Close operation thành công; circuit breaker suppress hedge-sync nhưng KHÔNG block close operation | Medium |
| TC_016 | Verify light-check suppressed during bot_safe_close | Bot với `bots.status='closing'`, `bots.lifecycle_state='lp_closing'` | Light-check queue worker chạy | 1. Light-check bị skip cho bot này. 2. Không có HL API call nào được thực hiện cho bot này trong quá trình close | Medium |
| TC_017 | Verify HL API unreachable during hedge close triggers SAFE_MODE with E-EXBOT-008 | bot_safe_close đang xử lý hedge close, HL API configured để fail | Attempt `closeShortReduceOnlyIoc` khi HL API unreachable | 1. Bot enter SAFE_MODE. 2. E-EXBOT-008 được trigger: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | High |
| TC_018 | Verify reconcile mismatch triggers SAFE_MODE with E-EXBOT-011 | `closeShortReduceOnlyIoc` đã submit nhưng reconcile detect actual HL size ≠ 0 | Reconcile (fetch clearinghouseState) phát hiện actual size ≠ expected (0) | 1. Bot enter SAFE_MODE. 2. E-EXBOT-011 được trigger: "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | High |
| TC_019 | Verify HL agent key with key_status='active' required for hedge close signing | Bot với hedge position, HL agent key | 1. Attempt bot_safe_close với `key_status='active'`. 2. Verify signing thành công. 3. Attempt với `key_status='inactive'`. 4. Verify signing thất bại | 1. Active key được yêu cầu; signing thành công khi key active. 2. Signing thất bại khi key không active | Medium |

### II.2. Integration & State verification — Operation: Hedge close operation

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_020 | Verify duplicate trigger via redelivery is rejected (idempotency) | bot_safe_close trigger đã được xử lý thành công | 1. Trigger được redeliver (cùng idempotency_key, ví dụ: consumer ack failure, worker crash before ack). 2. Quan sát hệ thống response | 1. Duplicate bị reject qua UNIQUE constraint. 2. Đúng một `close_operations` row tồn tại; operation không bị double-apply. **✅ Note:** **Q4 RESOLVED (2026-07-09):** "Close Worker" là ExBot Lambda (architecture component). 5 trigger conditions đã được xác nhận trong UC. UNIQUE constraint idempotency không phụ thuộc vào Q4 answer. | High |
| TC_021 | Verify same cloid resubmission does not create duplicate HL orders | `closeShortReduceOnlyIoc` đã submit với deterministic cloid | 1. Submit `closeShortReduceOnlyIoc(size, cloid)`. 2. Resubmit với cùng cloid (network retry) | 1. HL deduplicates — chỉ một order được tạo. 2. Không có double-apply của hedge close | Medium |

---

## III. Operation: LP close operation

### III.1. Functional verification — Operation: LP close operation

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_022 | Verify LP close via vault.executeStrategy emits PositionClosed event | `close_operations.state='hedge_closed'`, hedge đã được confirm đóng | 1. Gọi `vault.executeStrategy(RedeemStrategyV1, user, botId, params)` để đóng LP. 2. Quan sát on-chain: BnzaExPositionManager xử lý strategy. 3. Verify PositionClosed event emitted. 4. Verify fees routed via LpFeeOps (op fee + perf fee). 5. Verify principal returned in pair currency | 1. PositionClosed event emitted on-chain. 2. Fees routed đúng qua LpFeeOps. 3. `close_operations.state` chỉ advance sang `lp_closed` sau khi PositionClosed event được nhận | High |
| TC_023 | Verify LP close revert retry 3 times then escalate to admin | `close_operations.state='hedge_closed'`, vault call configured để revert | 1. Attempt `vault.executeStrategy` — revert. 2. Retry lên đến 3 lần. 3. Sau 3 lần thất bại, escalate lên admin | 1. `close_operations.state` giữ tại `lp_closed`. 2. Admin được escalate sau 3 lần thất bại. 3. LP position không được đóng | High |

---

## IV. Operation: RedemptionQueue operation

### IV.1. Functional verification — Operation: RedemptionQueue operation

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_024 | Verify fulfillRequest pending — request stays enqueued, bots.status remains 'closing' | `close_operations.state='redemption_queued'`, `RedemptionQueue.createRequest` đã được gọi | 1. Quan sát `bots.status` khi Operator chưa gọi `fulfillRequest`. 2. Verify request vẫn trong queue | 1. Request vẫn enqueued trên on-chain; không bị mất. 2. `bots.status` vẫn giữ giá trị `'closing'`. 3. User funds vẫn safe trên on-chain | Medium |
| TC_025 | Verify fulfillRequest failure keeps request in queue | `close_operations.state='redemption_queued'`, fulfillRequest configured để fail | 1. Gọi `fulfillRequest` — fail (ví dụ: insufficient operator balance). 2. Quan sát queue state | 1. Request vẫn trong queue; không bị dropped. 2. Operator có thể retry | Medium |
| TC_026 | Verify RequestFulfilled event advances close_operations to done and bots.status='closed' | `close_operations.state='redemption_queued'`, fulfillRequest đã được gọi | 1. Quan sát `RequestFulfilled` event on-chain. 2. Verify state transitions | 1. `close_operations.state` advance sang `done`. 2. `bots.status` chuyển sang `'closed'`. 3. `bots.lifecycle_state` chuyển sang `'closed'` | High |

### IV.2. Integration & State verification — Operation: RedemptionQueue operation

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_027 | Verify RedemptionQueue.createRequest enqueues HL portion payout | `close_operations.state='lp_closed'`, LP position đã đóng | Gọi `RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId)` | 1. Request được enqueue on-chain, RequestCreated event emitted. 2. `close_operations.state` advance sang `redemption_queued` | High |
| TC_028 | Verify fulfillRequest pops FIFO — oldest request served first | Nhiều redemption requests tồn tại trong queue từ các bot khác nhau | Gọi `RedemptionQueue.fulfillRequest(tokens, amounts)` | 1. Request oldest (được tạo trước) được fulfill trước (FIFO). 2. Out-of-order fulfillment không xảy ra; FIFO invariant được enforce | High |

---

## V. Operation: Admin force-close

### V.1. Functional verification — Operation: Admin force-close

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_029 | Verify admin force-close initiates full bot_safe_close flow | Admin được authenticate, bot với `bots.status='active'` | 1. Admin gọi POST /api/exbot/close với valid botId và reason. 2. Verify request forwarded qua OperatorFacade → API Gateway + HMAC Lambda Authorizer → ExBot Lambda. 3. Verify `bots.status='closing'`. 4. Verify full flow executes (hedge → LP → RedemptionQueue) | 1. bot_safe_close được khởi tạo. 2. Investor notified: "Your ExBot was administratively closed. USDC is available for withdrawal." | High |
| TC_030 | Verify force-close on already-closed bot returns E-EXBOT-012 | Bot với `lifecycle_state='closed'` | Admin gọi POST /api/exbot/close cho bot đã closed | 1. Hệ thống trả về E-EXBOT-012: "Bot {id} is already closed. No action needed." (HTTP 409). 2. Không có `close_operations` row được tạo | High |
| TC_031 | Verify force-close reason is logged in close_operations for audit trail | Admin được authenticate, valid botId | Admin gọi POST /api/exbot/close với reason | `close_operations.trigger_reason` được populate với admin-provided reason; audit trail đầy đủ | Medium |
| TC_032 | Verify force-close on SAFE_MODE bot proceeds with existing hedge state | Bot với `bots.status='safe_mode'` | Admin initiate force-close trên SAFE_MODE bot | 1. System proceed với bot_safe_close sử dụng existing hedge state. 2. Nếu hedge không đóng được (irrecoverable), `residual_hl_liability` được ghi nhận và admin notified | Medium |
| TC_033 | Verify investor receives correct notification on admin force-close | Admin force-close hoàn tất thành công | Quan sát investor notification sau khi fulfillRequest hoàn tất | Investor nhận đúng message: "Your ExBot was administratively closed. USDC is available for withdrawal." (khác với happy-path message) | Medium |
| TC_034 | Verify 3rd trigger within 7 days executes normally with admin notification | Bot với 2 prior bot_safe_close events trong 7 ngày rolling window | 3rd trigger condition met trong 7 ngày | 1. Close flow execute bình thường (không bị block). 2. Admin notification được gửi đồng thời. 3. Bot đạt `closed` | Medium |
| TC_035 | Verify admin receives E-EXBOT-018 notification on hedge failure | Hedge close fails sau 3 retries | Quan sát admin notification sau khi hedge fail | Admin notification E-EXBOT-018: "Bot safe close failed: HL hedge could not be closed after 3 attempts. Manual intervention required. Bot held at residual_hl_liability." | Medium |

### V.2. Non-functional (logic) verification — Operation: Admin force-close

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_036 | Verify force-close requires valid admin authentication | Request không có valid OPERATOR facade token | Gọi POST /api/exbot/close mà không có valid auth token | 1. Request bị reject tại facade level. 2. Trả về 403 Forbidden. 3. Request không được forward đến ExBot Lambda | High |
| TC_037 | Verify all state-changing operations write audit records | bot_safe_close được trigger | Execute bot_safe_close | 1. Audit log entry được tạo với: actor, action, timestamp, target (botId), result. 2. Logs không chứa PII hoặc secrets | Medium |

---

## VI. Operation: Emergency transfer

### VI.1. Functional verification — Operation: Emergency transfer

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_038 | Verify emergencyTransfer transfers funds to user's own address only — no recipient parameter | BnzaExVault contract is paused | 1. Operator gọi `emergencyTransfer(user, botId)`. 2. Verify không có recipient parameter tồn tại. 3. Verify funds transferred to user's own address. 4. Verify EmergencyRecovery event emitted | 1. User's USDC và LP NFTs được transfer đến user's own address. 2. EmergencyRecovery event emitted on-chain. 3. Multi-sig KHÔNG required cho operation này | High |

---

## VII. Operation: Happy path notification

### VII.1. Functional verification — Operation: Happy path notification

| TC ID | Test Title/Summary of test cases | Pre-conditions | Test Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC_039 | Verify investor receives notification after fulfillRequest completes | bot_safe_close hoàn tất thành công (fulfillRequest đã được gọi, RequestFulfilled event đã được nhận) | Quan sát investor notification sau khi bot_safe_close hoàn tất | Investor nhận đúng message: "Bot safely closed. Funds have been returned to your wallet." | Medium |

---

## Coverage Breakdown by Phase (5-Phase Framework)

| Phase | Count |
|---|---:|
| Phase 1: Preconditions & Initial State | 4 |
| Phase 2: Input & Contract Validation | 2 |
| Phase 3: Core Functional Logic | 24 |
| Phase 4: Integration & Data Consistency | 7 |
| Phase 5: Non-Functional (logic) | 2 |
| **Total** | **39** |

---

## Priority Summary

| Priority | Count |
|---|---:|
| High | 21 |
| Medium | 18 |
| **Total** | **39** |

---

## ⚠️ Out-of-Scope Flags

| Area | Reason | Recommended Action | Related TCs |
|---|---|---|---|
| `idempotency_key` và `trigger_reason` format (**Q9 — CẦN CONFIRM TỪ BA**) | FR-EXBOT-072 nói "idempotency_key UNIQUE enforced" và "trigger_reason populated" nhưng không định nghĩa format/value cụ thể. BA cần bổ sung: (1) format của `idempotency_key` (ví dụ: `{botId}:{kind}:{trigger_timestamp}`), (2) enum values của `trigger_reason` (`circuit_breaker_exhausted`, `margin_critical`, `3_stops_7d`, `partial_repair_exhausted`, `admin_force_close`). | **Chờ Q9 answer từ BA** | TC_004 |
| BnzaExVault Solidity contract internal logic | zen develops; SOTATEK integrates via ABI | Integration tests depend on ABI (OQ-EXBOT-08) | — |
| RedemptionQueue contract internal logic | zen develops; SOTATEK integrates via ABI | Integration tests depend on ABI (OQ-EXBOT-08) | — |
| SPEC §19.5 INV-STOP protocol implementation | Pending HL confirmation (OQ-EXBOT-02) | Wait for OQ-EXBOT-02 | — |
| HL API field names for marginSummary | Pending HL API docs (OQ-EXBOT-01) | Integration tests depend on API confirmation | — |
| Performance / load testing (NFR-EXBOT-003: 5-minute SLA) | Performance testing out of scope | Defer to performance testing | — |
| Security: private key never leaves KMS | Security audit out of scope | Defer to security audit | — |
| EmergencyTransfer contract-level enforcement | Cannot be tested via integration | Defer to contract security review | — |

---

✅ **Q4 RESOLVED (2026-07-09):** "Close Worker" trong UC §1 là label cho ExBot Lambda — architecture component, không phải actor độc lập. 5 trigger conditions đã được xác nhận trong UC §1/FR-EXBOT-072. Actor list convention giữ nguyên.

---

*Generated by qc-func-tc-design-exbot skill — logic-only, no UI*
