# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Template rà soát requirement phục vụ thiết kế test**

---

# UC-EXBOT-bot-safe-close Readiness Review Report

---

## Feature Brief - Tóm tắt nghiệp vụ

UC-EXBOT-bot-safe-close là một system-initiated safe close operation dành cho ExBot. Không giống user_redeem (LP-first, investor-initiated), bot_safe_close sử dụng thứ tự hedge-first: đóng HL short trước, sau đó đóng LP position, rồi enqueue HL portion payout vào RedemptionQueue để Operator fulfill FIFO trên on-chain.

**Actor chính:** ExBot System Operator (Close Worker).

**Trigger conditions (5 loại):**
1. Circuit breaker exhausted — `circuit_breakers.state='open'` và `reset_at` đã extend 3 lần không probe thành công
2. Margin critical → SAFE_MODE không có đường auto-recovery
3. 3 stops trong 7 ngày (rolling window)
4. Partial repair exhausted — 3 consecutive repair attempts fail
5. Admin force-close qua `/api/exbot/close`

**Luồng xử lý chính:**
Close Worker thu thập UserLockDO lease, đóng HL short hoàn toàn (size=0), cancel stop qua INV-STOP protocol, reconcile xác nhận size=0, gọi vault call để đóng LP, sau đó `RedemptionQueue.createRequest` enqueue HL portion payout. Operator gọi `fulfillRequest` trả tiền FIFO trên on-chain. Bot chuyển sang `bots.status='closed'`.

**Các luồng thay thế/exception:**
- A1: Hedge close fail → giữ residual_hl_liability, không đụng LP
- A2: LP close revert → retry 3 lần, escalate admin
- A3: fulfillRequest fail → request stays queued, Operator retry
- A4: 3rd trigger trong 7 ngày → proceed bình thường + admin notification

**Quan trọng:** Park/redeploy feature đã bị drop (HLD 2026-06-18). Sau bot_safe_close, lifecycle transition trực tiếp sang `closed`, không có parked/cooldown state.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-safe-close | System-Initiated Safe Close + Auto Re-Entry | v1 (2026-06-18) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-18 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| uc-bot-safe-close.md | 2026-06-18 | UC source | Primary UC |
| us-009.md | 2026-06-18 | Linked User Story | US-EXBOT-009 (bot_safe_close happy path + edge cases) |
| us-010.md | 2026-06-12 | Linked User Story | US-EXBOT-010 (SAFE_MODE + margin triggers) |
| us-012.md | 2026-06-18 | Linked User Story | US-EXBOT-012 (admin force-close + emergencyTransfer) |
| srs/spec.md | 2026-06-29 | SRS baseline | Canonical source of truth for ExBot logic |
| srs/states.md | 2026-06-29 | State diagram | close_operations state machine, lifecycle states |
| srs/flows.md | 2026-06-29 | Flow diagram | F-05 bot_safe_close sequence |
| srs/erd.md | 2026-06-29 | ERD / Schema | close_operations table, queue_idempotency |
| frd.md | 2026-06-29 | FRD | FR-EXBOT-070, 072, 073 |
| message-list.md | 2026-06-26 | Error codes registry | E-EXBOT-* codes |
| common-rules.md | — | BR registry | BR-EXBOT-007 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-bot-safe-close tồn tại để xử lý trường hợp hệ thống cần đóng một ExBot một cách an toàn theo thứ tự hedge-first. Khác với user_redeem (investor-initiated, LP-first), bot_safe_close được trigger bởi các điều kiện hệ thống nghiêm trọng: circuit breaker exhausted, margin critical không recovery được, 3 stops trong 7 ngày, partial repair fail, hoặc admin force-close.

Mục tiêu nghiệp vụ: đảm bảo investor nhận lại tiền qua RedemptionQueue FIFO trên on-chain, với hedge được đóng trước để giảm rủi ro cho hệ thống.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Trigger detection | 5 trigger conditions (circuit/margin/stops/repair/admin) tạo close_operations row | FR-EXBOT-072, SRS Flows F-05 |
| Hedge close | Close Worker acquire UserLockDO → full close HL short → cancel stop → reconcile | FR-EXBOT-073, SRS states.md close_operations |
| LP close | vault call đóng LP position | FR-EXBOT-073, SRS states.md |
| RedemptionQueue | createRequest → fulfillRequest FIFO → user receives funds on-chain | FR-EXBOT-070, 073 |
| State tracking | close_operations state machine: requested → hedge_close_pending → hedge_closed → lp_closed → redemption_queued → done | SRS states.md close_operations |
| Alternate flows | A1 (hedge fail), A2 (LP revert), A3 (fulfillRequest fail), A4 (3rd trigger in 7 days) | UC §4 |
| Idempotency | close_operations.idempotency_key UNIQUE prevents double settlement | FR-EXBOT-070, SRS erd.md |
| Admin force-close | POST /api/exbot/close trigger | US-EXBOT-012, FR-EXBOT-090 |
| Emergency transfer | emergencyTransfer(user, botId) khi contract paused | US-EXBOT-012 AC-012-3 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Trading strategy logic (PositionCalc, hedge formula) | zen-proprietary | Không ảnh hưởng test bot_safe_close |
| BnzaExVault Solidity contract internal logic | zen-develops, SOTATEK integrates via ABI | Cần xác nhận executeStrategy ABI cuối cùng |
| VaultMinted event watcher / chain indexer | Không thuộc bot_safe_close flow | Không ảnh hưởng |
| Park/redeploy feature | Đã bị drop HLD 2026-06-18 | Cần đảm bảo không còn trace trong documents |
| RedemptionQueue contract internal logic | zen-develops | Cần xác nhận fulfillRequest ABI |
| Multi-bot per user (Phase B+) | Phase A chỉ hỗ trợ 1 bot/user | Không ảnh hưởng |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| ExBot System Operator (Close Worker) | Primary | Thu thập UserLockDO, thực hiện hedge close, LP close, RedemptionQueue createRequest | Không được đụng LP khi hedge chưa đóng xong | UC §1, SRS flows.md F-05 |
| Hyperliquid (HL) | System / External | Nhận closeShortReduceOnlyIoc, place/cancel stop orders | Không có quyền hạn riêng | UC §1, FR-EXBOT-073 |
| BnzaExVault | System / External | Nhận vault call từ worker | Contract do zen phát triển | UC step 5, FR-EXBOT-070, IC-EXBOT-002 |
| BnzaExPositionManager | System / External | Xử lý RedeemStrategyV1, emit PositionClosed event | Contract do zen phát triển | UC step 6 |
| RedemptionQueue | System / External | Nhận createRequest, chờ fulfillRequest từ Operator | FIFO queue on-chain | UC step 8, FR-EXBOT-070 |
| Operator (role) | System | Gọi fulfillRequest tokens/amounts, thực hiện safeTransferFrom on-chain | Operator có quyền OPERATOR_ROLE | UC step 10 |
| ExBot Admin (zen) | Primary (qua API) | Trigger force-close qua POST /api/exbot/close | Không được force-close bot đã closed | US-EXBOT-012 AC-012-4, E-EXBOT-012 |
| Investor | Beneficiary | Nhận notification và funds | Không trigger bot_safe_close trực tiếp | UC step 12 |
| D1 Database | System | Lưu close_operations, bots, hedge_legs state | Source of truth off-chain | FR-EXBOT-073, SRS erd.md |
| UserLockDO | System / Durable Object | Cung cấp lease-based mutex cho HL mutations | TTL=90s, heartbeat supported | FR-EXBOT-026, 092 |

**Nhận xét readiness:**
Các actor đã được xác định rõ. Tuy nhiên, cần lưu ý:
- Không có Actor cho "Queue idempotency" mechanism — Close Worker message được consume với idempotency check, nhưng UC không đề cập rõ Close Worker là queue consumer.
- "Chain indexer / deposit watcher" không phải actor của bot_safe_close — đây là actor của bot-start.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Một trong 5 trigger conditions phải được met: circuit breaker exhausted, margin critical + irrecoverable, 3 stops in 7 days, partial_repair exhausted, admin force-close | Yes | UC §2, FR-EXBOT-072 |
| 2 | Không có close_operations row tồn tại cho bot này với `kind='bot_safe_close'` (idempotency_key UNIQUE prevents duplicate) | Yes (enforced by DB) | FR-EXBOT-070, SRS erd.md |
| 3 | HL agent key phải có `key_status='active'` cho HL signing operations (nếu hedge cần sign) | Yes | FR-EXBOT-080 (applies to hedge close signing) |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Happy path hoàn tất | `bots.status='closed'`, `bots.lifecycle_state='closed'`, `close_operations.state='done'`, HL short size=0, LP NFT burned, RedemptionQueue request created and fulfilled, user notification sent | UC §5, FR-EXBOT-073 |
| Happy path notification | Investor receives: "Bot safely closed. Funds have been returned to your wallet." | UC step 12, US-EXBOT-009 AC-009-1 |
| Hedge fail (A1) | `close_operations.state='residual_hl_liability'`, `bots.status='safe_mode'`, LP NOT closed, admin notification | UC A1, FR-EXBOT-073, US-EXBOT-009 AC-009-2 |
| LP close revert (A2) | `close_operations.state='lp_closed'`, retry up to 3 times, escalate to admin on failure | UC A2, FR-EXBOT-073 |
| fulfillRequest pending (A3) | `close_operations.state='redemption_queued'`, request stays in queue, `bots.status='closing'` | UC A3, US-EXBOT-009 AC-009-4 |
| 3rd trigger in 7 days (A4) | Hoàn tất bình thường + admin notification đồng thời | UC A4, US-EXBOT-009 AC-009-3 |

---

## 4 và ## 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 bot_safe_close Trigger & Initiation

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| T1 | System (deep-audit/hedge-sync/partial_repair/admin) | Trigger condition met (5 loại) | Tạo `close_operations` row với `kind='bot_safe_close'`, `state='requested'`, `idempotency_key`, `trigger_reason` populated | A4: Nếu là 3rd trigger trong 7 ngày → proceed bình thường + admin notification | — | FR-EXBOT-072, FR-EXBOT-073 |
| T2 | System (auto hoặc admin API) | Admin gọi POST /api/exbot/close HOẶC system trigger auto | OperatorFacade forward via CF service binding → ExBot Worker | — | E-EXBOT-012 nếu bot đã closed (admin path) | FR-EXBOT-090, US-EXBOT-012 AC-012-4 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| close_operations.idempotency_key | UNIQUE constraint trên DB | Yes | Row được tạo thành công | Duplicate trigger → UNIQUE constraint violation → reject, no double settlement | FR-EXBOT-070 |
| close_operations.trigger_reason | Phải được populate cho tất cả 5 trigger types | Yes | Traceable audit trail | (no explicit error in UC) | FR-EXBOT-072 |
| close_operations.kind | Phải = 'bot_safe_close' | Yes | Phân biệt với user_redeem | Không áp dụng | FR-EXBOT-070 |
| Trigger conditions (5 loại) | Phải match: circuit breaker exhausted / margin critical irrecoverable / 3 stops in 7 days / partial_repair exhausted / admin force-close | Yes | Trigger được accept | Invalid trigger → không tạo row | FR-EXBOT-072 |

#### C. Thông báo, lỗi và phản hồi hệ thống (API response / state change / event / message)

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Trigger accept (admin API) | API response | "Close request queued. Funds will be returned after FIFO processing." | — | UC step 12 note, FR-EXBOT-073 |
| Admin force-close trên closed bot | API error | "Bot {id} is already closed. No action needed." | E-EXBOT-012 | US-EXBOT-012 AC-012-4, message-list.md |
| 3rd trigger in 7 days | Admin notification | Admin escalation notification | — | UC A4 |
| close_operations row created | DB state | `state='requested'` | FR-EXBOT-073 | FR-EXBOT-073 |

---

### 6.2 Hedge Close Operation

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| H1 | Close Worker | Acquire UserLockDO lease (TTL=90s, holderToken UUID, idempotencyKey) | Lease acquired → proceed | Lock busy → re-queue message với delay | FR-EXBOT-026, 092 |
| H2 | Close Worker | Compute delta = 0 - actualShortEth (BigDecimal) | delta = full close size | — | — | FR-EXBOT-022 |
| H3 | Close Worker + Signing Lambda | Gọi `closeShortReduceOnlyIoc(size)` với deterministic cloid | HL order submitted | A1: Order fails after 3 retries → `residual_hl_liability`, SAFE_MODE, no LP close | FR-EXBOT-073, FR-EXBOT-022 |
| H4 | Close Worker | Cancel stop via INV-STOP protocol với size=0 | Stop cancelled | — | Stop cancel fails → hold, retry | FR-EXBOT-073, FR-EXBOT-035 |
| H5 | Close Worker | Reconcile: fetch clearinghouseState, verify size = 0 | Size confirmed = 0 → `close_operations.state='hedge_closed'` | A1: Size != 0 → retry hoặc residual_hl_liability | FR-EXBOT-025, FR-EXBOT-073 |
| H6 | Close Worker | Update `close_operations.hedge_close_tx` với tx hash | `hedge_close_tx` populated | — | — | FR-EXBOT-073 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Delta computation | Phải dùng BigDecimal, delta = 0 - actualShortEth | Yes | Correct full close size | Float arithmetic → precision loss → BLOCKED | FR-EXBOT-021, NFR-EXBOT-008 |
| Cloid | Deterministic: keccak256("bnza:{botId}:{attemptId}:{stage}:{version}") | Yes | HL deduplicates on same cloid | — | FR-EXBOT-024 |
| Stop cancel | Phải qua INV-STOP protocol (§19.5), không được direct cancel-then-place | Yes | Protected replacement | Direct cancel → architectural violation | FR-EXBOT-035 |
| Reconcile | Phải verify size = 0 trước khi advance state | Yes | Confirmed → proceed | Size mismatch → retry hoặc residual_hl_liability | FR-EXBOT-025, FR-EXBOT-073 |
| Retry on hedge close fail | Retry up to 3 times trước khi escalate | Yes | Final failure → A1 | Admin escalation after 3 fails | FR-EXBOT-073 |
| LP close ordering | LP close KHÔNG được attempt trước khi hedge_closed confirmed | Yes (business rule) | Hedge-first invariant maintained | LP đóng trước hedge → BLOCKED | FR-EXBOT-073 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Hedge close fail (A1) | State change | `close_operations.state='residual_hl_liability'`, `bots.status='safe_mode'` | — | UC A1, FR-EXBOT-073 |
| A1 admin notification | Admin notification | Có, nội dung not specified trong UC | — | UC A1 |
| HL API unreachable | State change | Bot enters SAFE_MODE | E-EXBOT-008 | message-list.md |
| Reconcile mismatch | State change | Bot enters SAFE_MODE | E-EXBOT-011 | message-list.md |

---

### 6.3 LP Close Operation

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| L1 | Close Worker | Gọi vault call đóng LP | Contract executes strategy | A2: Revert after 3 retries → escalate admin | FR-EXBOT-073, IC-EXBOT-002 |
| L2 | BnzaExPositionManager | Xử lý strategy | Earned fees routed via LpFeeOps (op fee + perf fee), principal returned in pair currency | — | — | UC step 6 |
| L3 | Close Worker | Theo dõi PositionClosed event | Event received → `close_operations.state='lp_closed'`, `close_operations.lp_close_tx` populated | — | — | FR-EXBOT-073 |

---

### 6.4 RedemptionQueue Operation

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| R1 | Close Worker | Gọi `RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId)` | Request enqueued → `close_operations.state='redemption_queued'`, `RequestCreated` event emitted | — | — | FR-EXBOT-073, UC step 8-9 |
| R2 | Operator | Gọi `RedemptionQueue.fulfillRequest(tokens, amounts)` | FIFO pop from queue, `safeTransferFrom(operator, user, amount)` on-chain | A3: fulfillRequest fails → request stays queued, Operator retries | — | FR-EXBOT-070, UC step 10 |
| R3 | Close Worker / System | Theo dõi `RequestFulfilled` event | Event received → `close_operations.state='done'`, `bots.status='closed'` | — | — | FR-EXBOT-073, UC step 11 |
| R4 | System | Gửi investor notification | Investor receives: "Bot safely closed. Funds have been returned to your wallet." | — | — | UC step 12, US-EXBOT-009 AC-009-1 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| FIFO order | fulfillRequest phải pop theo FIFO | Yes (business rule) | Oldest request served first | Out-of-order → user fund loss risk | FR-EXBOT-070 |
| Request not lost on fulfillRequest fail | Request stays enqueued khi fulfillRequest fails | Yes (business rule) | User funds safe | Request dropped → BLOCKED | UC A3, US-EXBOT-009 AC-009-4 |
| bots.status transition timing | `bots.status='closed'` chỉ set khi fulfillRequest complete | Yes | Correct terminal state | Status set too early → misleading | FR-EXBOT-073 |

---

### 6.5 Admin Force-Close & Emergency Transfer

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| F1 | Admin (zen) | Chọn bot trên admin dashboard, click "Force Close", confirm with reason | System initiates bot_safe_close flow | AC-012-2: SAFE_MODE bot → proceed với existing hedge state | AC-012-4: Already closed → reject | US-EXBOT-012, FR-EXBOT-090 |
| F2 | System | Đóng hedge → đóng LP → RedemptionQueue (same as happy path T1-L4) | Full close flow | F2b: SAFE_MODE bot với irrecoverable hedge | F2c: Already closed | US-EXBOT-012 AC-012-1/2, FR-EXBOT-073 |
| F3 | System | Gửi investor notification | "Your ExBot was administratively closed. USDC is available for withdrawal." | — | — | US-EXBOT-012 AC-012-1 |
| E1 | Operator | Contract paused + gọi `emergencyTransfer(user, botId)` | User's USDC + LP NFTs transferred to user's own address (no recipient param) | — | Only when contract paused | US-EXBOT-012 AC-012-3, FRD §2 ACT-M |
| E2 | System | Emit `EmergencyRecovery` event on-chain | Event enables indexer/alert detection | — | — | US-EXBOT-012 AC-012-3 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Force-close reason | Phải logged trong close_operations | Yes | Audit trail complete | Missing → not traceable | US-EXBOT-012 Notes |
| emergencyTransfer recipient | Không có recipient parameter — funds always go to user's own address | Yes (security) | No fund redirection risk | Recipient param exists → security issue | US-EXBOT-012 AC-012-3 |
| Multi-sig for emergency | NOT required | Yes (simplified) | Faster response | Multi-sig required → slow | US-EXBOT-012 AC-012-3 |
| Already closed rejection | E-EXBOT-012 returned | Yes | No duplicate close | No rejection → double settlement risk | US-EXBOT-012 AC-012-4, message-list.md |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| bot_safe_close triggered | `bots.lifecycle_state` → `lp_closing` → `closed` | Lifecycle state machine transition | Verify state progression: `active`/`safe_mode` → `lp_closing` → `closed` | SRS states.md, UC §3 |
| Hedge close completes | `hedge_legs.last_known_hl_short_size` → 0 | Hedge leg becomes zero | Verify D1 value = 0 after reconcile | FR-EXBOT-025, FR-EXBOT-073 |
| Hedge fail → A1 | `close_operations.state='residual_hl_liability'`, SAFE_MODE | LP stays open, user funds at risk until hedge resolved | Verify LP NFT still in user's wallet/positions | UC A1, FR-EXBOT-073 |
| LP close completes | `positions.tokenId` marked as burned, `lp_operations` row created | LP position removed | Verify tokenId no longer in user's wallet | FR-EXBOT-073, SRS erd.md |
| RedemptionQueue request | `close_operations` row with `redemption_queued` state | HL portion tracked in queue | Verify request exists in on-chain queue | FR-EXBOT-070, FR-EXBOT-073 |
| fulfillRequest completes | `bots.status='closed'`, `close_operations.state='done'` | User receives funds, bot terminal state | Verify user wallet balance increased | FR-EXBOT-073, UC §5 |
| Circuit breaker state | Circuit breaker remains open during close (CB doesn't block close) | hedge-sync suppressed, but close still allowed | Verify close succeeds even when circuit open | FR-EXBOT-040, FR-EXBOT-073 |
| Deep-audit detection | SAFE_MODE entry → bot_safe_close trigger (margin critical irrecoverable path) | Auto-triggered from deep-audit | Verify deep-audit creates close_operations | FR-EXBOT-016, FR-EXBOT-072 |
| Partial repair fail | 3 consecutive repair failures → bot_safe_close trigger | Auto-triggered from partial_repair worker | Verify partial_repair worker creates close_operations | FR-EXBOT-036, FR-EXBOT-072 |
| Light-check / hedge-stopped | 3 stops in 7 days → bot_safe_close trigger | Auto-triggered from hedge-stopped cooldown | Verify cooldown counter increments and triggers | FR-EXBOT-034, FR-EXBOT-072 |
| Admin force-close | POST /api/exbot/close → ExBot Worker via CF service binding | Admin can close any bot | Verify service binding proxy works | FR-EXBOT-090, US-EXBOT-012 |
| Emergency transfer | Contract paused → emergencyTransfer | User recovers funds when vault paused | Verify no recipient parameter, EmergencyRecovery event emitted | US-EXBOT-012 AC-012-3 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — bot_safe_close completes | Bot ở `safe_mode` hoặc `active` với trigger condition met | Close Worker initiates bot_safe_close | HL short fully closed (size=0 confirmed via reconcile); LP closed; RedemptionQueue.createRequest enqueued; Operator fulfillRequest FIFO; bots.status='closed'; investor notified "Bot safely closed. Funds have been returned to your wallet." | US-EXBOT-009 AC-009-1, FR-EXBOT-070, 073 |
| AC-02 | Happy path — state progression | Trigger condition met | close_operations row created | `state='requested'` → `hedge_close_pending` → `hedge_closed` → `lp_closed` → `redemption_queued` → `done` (sequential, no skip) | FR-EXBOT-073, SRS states.md |
| AC-03 | Hedge close fail — LP not touched (A1) | bot_safe_close triggered | HL short close fails after 3 retries | `close_operations.state='residual_hl_liability'`; `bots.status='safe_mode'`; LP NOT closed; admin notification sent | UC A1, US-EXBOT-009 AC-009-2 |
| AC-04 | LP close revert — retry 3x then escalate (A2) | Hedge closed successfully | vault call reverts | Retry up to 3 times; after 3rd failure → escalate to admin, hold at `lp_closed` pending | UC A2, FR-EXBOT-073 |
| AC-05 | fulfillRequest pending (A3) | `close_operations.state='redemption_queued'` | Operator has not yet called fulfillRequest | Request stays enqueued (not lost); `bots.status='closing'`; user funds safe on-chain | US-EXBOT-009 AC-009-4 |
| AC-06 | 3rd trigger in 7 days (A4) | Bot đã có 2 bot_safe_close events trong 7 ngày | 3rd trigger condition met | Close flow executes normally; admin notification sent concurrently; bots.status='closed' after fulfillRequest | UC A4, US-EXBOT-009 AC-009-3 |
| AC-07 | Idempotency — duplicate trigger rejected | Close operation đang active cho bot X | New trigger received for same bot X | UNIQUE constraint on idempotency_key → reject duplicate; exactly one close_operations row created | FR-EXBOT-070, SRS erd.md |
| AC-08 | Admin force-close happy path | Admin selects active bot | Admin confirms force-close with reason | bot_safe_close initiated; bots.status='closing'; hedge → LP → RedemptionQueue; investor notified "Your ExBot was administratively closed. USDC is available for withdrawal." | US-EXBOT-012 AC-012-1 |
| AC-09 | Admin force-close on SAFE_MODE bot | Admin selects bot with `status='safe_mode'` | Admin initiates force close | System proceeds with bot_safe_close using existing hedge state; if hedge cannot close → residual_hl_liability record; admin notified of outstanding liability | US-EXBOT-012 AC-012-2 |
| AC-10 | Emergency transfer when paused | BnzaExVault contract is paused | Operator calls emergencyTransfer(user, botId) | User's USDC + LP NFTs transferred to user's own address (no recipient param); EmergencyRecovery event emitted; bots.status='error'; multi-sig NOT required | US-EXBOT-012 AC-012-3 |
| AC-11 | Force-close on already-closed bot rejected | Bot has `lifecycle_state='closed'` | Admin attempts force-close | E-EXBOT-012: "Bot {id} is already closed. No action needed."; no close_operations row created | US-EXBOT-012 AC-012-4, E-EXBOT-012 |
| AC-12 | Bot enters lp_closing state | bot_safe_close triggered | Close Worker starts operation | `bots.lifecycle_state` transitions to `lp_closing`; light-check suppressed during close | SRS states.md, FR-EXBOT-015 |
| AC-13 | Bot terminates at closed state | fulfillRequest completes successfully | Bot close operation finalizes | `bots.status='closed'`, `bots.lifecycle_state='closed'`, `close_operations.state='done'` | FR-EXBOT-073, UC §5 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Security | Private keys never leave KMS; all HL signing via Signing Lambda (kms:Sign only); no key material in app memory/logs | Verify hedge close signing uses Signing Lambda, not direct key access | NFR-EXBOT-006, FR-EXBOT-080 |
| Security | emergencyTransfer có no recipient param — funds always go to user's own address | Verify contract-level enforcement (cannot be tested via integration) | US-EXBOT-012 AC-012-3 |
| Reliability / Resilience | SAFE_MODE not a terminal state — every SAFE_MODE leads to auto-recovery or bot_safe_close | Verify A1 path: hedge fail → SAFE_MODE + residual_hl_liability, không stuck forever | BR-EXBOT-007, FR-EXBOT-050 |
| Reliability / Resilience | Circuit breaker suppresses hedge-sync but does NOT block close operation | Verify bot_safe_close succeeds even when circuit_breakers.state='open' | FR-EXBOT-040, FR-EXBOT-073 |
| Idempotency | close_operations.idempotency_key UNIQUE prevents double settlement | Verify duplicate trigger → UNIQUE constraint rejection | NFR-EXBOT-007, FR-EXBOT-070 |
| Precision | All hedge/stop/margin computations: BigDecimal only (float/number forbidden) | Verify delta computation in hedge close uses BigDecimal | NFR-EXBOT-008, FR-EXBOT-021 |
| Availability | SAFE_MODE and bot_safe_close lead to autonomous recovery — neither is terminal state | Verify bot eventually reaches `closed` from SAFE_MODE via bot_safe_close | BR-EXBOT-007, NFR-EXBOT-010 |
| Integration | BnzaExVault + RedemptionQueue ABI chưa finalized (OQ-EXBOT-08) | ExecuteStrategy/fulfillRequest ABI cần confirm trước khi test integration | IC-EXBOT-002, OQ-EXBOT-08 |
| Integration | HL API reachable for hedge close operations (SAFE_MODE không block close) | Verify hedge close works even when SAFE_MODE | FR-EXBOT-050, FR-EXBOT-073 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q1 | Major | CROSS_SOURCE_CONFLICT | FR-EXBOT-073 step 4 vs UC step 5 | LP close method conflict: FR-EXBOT-073 step 4 nói "Call `BnzaExVault.redeem(tokenId)`" trong khi UC step 5 nói "Call `vault.executeStrategy(RedeemStrategyV1, user, botId, params)`". US-EXBOT-009 AC-009-1 cũng nói `executeStrategy`. Không có document nào xác nhận cái nào đúng. | Affects test steps: LP close operation khác nhau hoàn toàn về ABI call | BA / Tech Lead | Open |
| Q2 | Major | OUTDATED_CONTENT | US-EXBOT-012 AC-012-1 | US-EXBOT-012 AC-012-1 vẫn nói "BnzaExVault.vaultClose is called, USDC parked into uninvested_balances" — đây là park/redeploy feature đã bị drop theo HLD 2026-06-18. FR-EXBOT-070 xác nhận "No park/redeploy loop (dropped HLD 2026-06-18)". | AC không reflect feature đã drop — tester sẽ design test sai | BA | Open |
| Q3 | Major | MISSING_INFO | UC §3 (preconditions) | UC §3 preconditions chỉ nói "Trigger condition met" nhưng không specify rằng bot phải có `bots.status IN ('active','safe_mode','paused')` (không phải 'closed'). Không có document nào explicit về điều này. | Tester cần biết trigger trên closed bot có được accept không | BA | Open |
| Q4 | Medium | MISSING_INFO | UC §1, SRS flows.md F-05 | UC không đề cập queue idempotency cho Close Worker. Close Worker được trigger như thế nào — via queue message hay direct call? flows.md F-05 diagram rất simplified. Không có document nào mô tả trigger mechanism. | Tester cần biết trigger mechanism để design test cho duplicate scenario | Tech Lead | Open |
| Q5 | Medium | MISSING_INFO | UC A1, US-EXBOT-009 AC-009-2 | UC A1 nói "admin escalation notification sent" nhưng không specify nội dung message. US-EXBOT-009 cũng không define. Không có E-* code cho residual_hl_liability scenario. Không có document nào định nghĩa message content. | Expected result không rõ → test không thể verify message content | BA | Open |
| Q6 | Medium | MISSING_INFO | UC §4 A3 vs US-EXBOT-009 AC-009-4 | AC-009-4 nói "bots.status remains 'closing' until fulfillRequest completes" nhưng không có document nào nói rõ khi nào `bots.status='closing'` được set. Sau step 2 (hedge_close_pending) hay step 8 (redemption_queued)? | Lifecycle state timing cần rõ để test đúng | BA | Open |
| Q7 | Medium | MISSING_INFO | UC §3 vs FR-EXBOT-072 | UC §3 preconditions không đề cập UserLockDO requirement. FR-EXBOT-026, 092 specify acquire UserLockDO cho hedge-sync, nhưng không có document nào xác nhận điều này có apply cho Close Worker không. UC step 2 mention UserLockDO nhưng không nói rõ đây có bắt buộc không. | Tester cần biết close operation có cần lock không | Tech Lead | Open |
| Q8 | Medium | INTERNAL_INCONSISTENCY | FR-EXBOT-073 vs SRS states.md | FR-EXBOT-073 step 3 nói "stop cancelled" nhưng close_operations states table (states.md) không có `stop_canceled` state. Không có document nào giải thích đây là action hay state. | Documentation inconsistency | BA | Open |
| Q9 | Minor | MISSING_INFO | FR-EXBOT-072, UC §3 | FR-EXBOT-072 nói "idempotency_key UNIQUE enforced" và "trigger_reason populated" nhưng không có document nào định nghĩa format/value cụ thể. | Test case cần verify these fields được set đúng | QC Lead | Deferred |
| Q10 | Minor | OUTDATED_CONTENT | SRS flows.md F-05 | flows.md F-05 diagram rất simplified — không reflect executeStrategy, idempotency_key, state progressionchi tiết. | Tester có thể bỏ sót steps khi follow diagram | BA | Deferred |
| Q11 | Minor | UNCLEAR_INFO | US-EXBOT-009 AC-EXBOT-009-2 | AC-009-2 nói "bots.status transitions to 'safe_mode'" sau hedge fail nhưng không specify `bots.lifecycle_state`. states.md cho thấy SAFE_MODE có thể là cả hai, nhưng không rõ khi nào thì nào. | Affects test assertion | BA / Tech Lead | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| BnzaExVault final ABI (executeStrategy, redeem function) | Integration | Affects LP close test steps | zen | Open (OQ-EXBOT-08) |
| RedemptionQueue ABI (createRequest, fulfillRequest signatures) | Integration | Affects RedemptionQueue test steps | zen | Open (OQ-EXBOT-08) |
| SPEC v5.2.6 §19.5 INV-STOP protocol details | Common rule | Affects stop cancel test steps | zen | Open (OQ-EXBOT-02) |
| HL API field names for marginSummary (marginBalanceUsd) | API contract | Affects reconcile verification | HL API docs | Open (OQ-EXBOT-01) |
| Vault contract address (Base + Optimism) via CF Secrets Store | Environment | Affects integration test connectivity | SOTATEK | Open |
| park/redeploy removal verification (to ensure no remaining traces) | Documentation | Ensure no misleading content in UC/FR/SRS | BA | Open |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Agent | Tạo báo cáo audited lần đầu |

---

## Scoring Summary

| Area | Max | Score | Status | Summary |
|---:|---:|---:|---|---|
| 1. Function/Operation & Data Object Inventory | 20 | 12 | ⚠️ Partial | Conflict Q1 (LP close method), missing trigger mechanism (Q4), Q9 (idempotency_key format) |
| 2. Data Object / State Attributes, BR & Messages | 25 | 15 | ⚠️ Partial | Q5 (message content), Q7 (UserLockDO), Q8 (stop_canceled conflict) |
| 3. Functional Logic & Workflow Decomposition | 25 | 15 | ⚠️ Partial | Q1 (LP close), Q2 (AC outdated), Q6 (status timing) |
| 4. Functional Integration & Data Consistency | 15 | 8 | ⚠️ Partial | Multiple missing details affecting integration test |
| 5. UC / Spec Documentation Quality | 15 | 6 | ⚠️ Partial | Q1, Q2, Q8 major conflicts; Q3-Q7, Q11 missing/unclear info |
| **Total** | **100** | **56** | **Not Ready** | |

**Verdict: Not Ready (56/100)**

Critical issues to resolve: Q1 (LP close method conflict), Q2 (outdated US-EXBOT-012 AC).

---

*UC Readiness Review Report - QC-UC-READ-EXBOT skill - Vietnamese output*
