# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tiêu đề:** UC-EXBOT-bot-start — Start ExBot  
**Ngày tạo:** 2026-07-07  
**Tác giả:** QC UC Read Agent (qc-uc-read-exbot)  
**Phiên bản:** v4

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả luồng khởi động ExBot do người dùng chủ động kích hoạt. Sau khi nhà đầu tư (USDC Investor) hoàn thành nạp tiền trên chuỗi, hệ thống tự động cung cấp khóa HL (KMS key-provision — F-03a) mà không cần người dùng thao tác thêm. Khi khóa đã sẵn sàng, nhà đầu tư gọi `POST /api/exbot/start` qua POOL UI để khởi động bot.

ExBot Lambda nhận yêu cầu và chạy 6 kiểm tra tiền quyết (preflight) theo thứ tự: (1) kiểm tra chính sách một bot — không có bot đang hoạt động; (2) kiểm tra số dư vault — `BnzaExVault` balance > 0 cho user; (3) kiểm tra ký quỹ HL — `marginBalance ≥ required × 2.0`; (4) kiểm tra trạng thái khóa — `hl_agent_keys.key_status='active'`; (5) xác nhận builder fee (5bps) trên HL; (6) mô phỏng LP mint. Bất kỳ kiểm tra nào thất bại sẽ chặn toàn bộ quá trình khởi động và trả về mã lỗi tương ứng — không tạo bản ghi bot nào.

Khi tất cả preflight đều qua, hệ thống tạo bản ghi bot (`lifecycle_state='preflight'`) rồi thực hiện tuần tự: mint LP NFT qua `BnzaExVault.vaultMint()` → mở vị thế short IOC trên HL qua Signing Lambda (kms:Sign) → đối soát vị thế thực tế → đặt lệnh stop reduce-only bảo vệ → xác nhận stop → chuyển sang trạng thái `active`. Toàn bộ trình tự trạng thái `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` phải được hoàn thành tuần tự không bỏ bước. Mỗi bước được lưu vào Aurora PostgreSQL một cách nguyên tử trước khi chuyển sang bước tiếp theo.

UC này liên quan chặt chẽ với: F-03a (auto key-provision on deposit), FR-EXBOT-080 (KMS provisioning), FR-EXBOT-030/031 (stop trigger price + placement), FR-EXBOT-025 (post-order reconcile), BR-EXBOT-010 (ExBot Lambda standalone), BR-EXBOT-012 (chỉ 1 key_status='active' per user).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-start | Start ExBot | v4 (audit) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | QC Lead | 2026-07-07 | 2026-07-07 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-bot-start.md` | 2026-07-07 | UC | Updated: trigger user-initiated; vault balance preflight added |
| `userstories/us-001.md` | 2026-07-07 | User Story | AC updated: vault balance Given added; user-initiated trigger |
| `srs/spec.md` | 2026-07-04 | SRS | Canonical: FR-EXBOT-001–004, 020, 030, 031, 080, 091, 092 |
| `srs/states.md` | 2026-07-03 | State Diagram | Bot lifecycle + agent key states (3-state) |
| `srs/flows.md` | 2026-07-07 | Flow Diagram | F-03a (key-provision) + F-03b (user-triggered bot start) |
| `srs/erd.md` | 2026-07-04 | ERD | Aurora PostgreSQL schema; hl_agent_keys retired fields noted |
| `frd.md` | 2026-07-04 | FRD | FR-EXBOT-001 (5 checks — no vault balance); FR-EXBOT-081 (KMS) |
| `usecases/index.md` | 2026-06-29 | Index | UC-EXBOT-bot-start entry confirmed |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này cung cấp cho nhà đầu tư USDC khả năng tự khởi động một ExBot delta-hedged LP. Mục tiêu: vốn của nhà đầu tư kiếm phí từ vị thế LP Uniswap V3 trong khi leg hedge trên Hyperliquid triệt tiêu rủi ro giá ETH một chiều. UC cũng bao gồm luồng tự động cung cấp khóa HL (key-provision) được kích hoạt bởi sự kiện nạp tiền on-chain, diễn ra trước khi người dùng gọi start.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Preflight check (6 bước) | Kiểm tra onebot policy, vault balance, HL margin, key_status, builder fee, LP simulation | `spec.md` FR-EXBOT-002 |
| Tạo bản ghi bot | INSERT bot với `lifecycle_state='preflight'` sau khi tất cả preflight pass | `spec.md` FR-EXBOT-003 |
| LP mint (on-chain) | Gọi `BnzaExVault.vaultMint()` → nhận `VaultMinted` event → lưu tokenId, wethIndex | `spec.md` FR-EXBOT-003, `flows.md` F-03b |
| Mở vị thế short IOC trên HL | Qua Signing Lambda (kms:Sign) → cloid deterministic | `spec.md` FR-EXBOT-080, FR-EXBOT-024 |
| Post-order reconcile | Fetch `clearinghouseState`, verify actual size, extract entry_price/liq_price/leverage | `spec.md` FR-EXBOT-025 |
| Tính stop_trigger_px | BigDecimal, formula: `entry_price × (1 + liq_distance_pct × 0.70)` | `spec.md` FR-EXBOT-030 |
| Đặt lệnh stop reduce-only | Qua Signing Lambda, verify stop confirmed | `spec.md` FR-EXBOT-031 |
| Lifecycle state tracking | Chuỗi 8 trạng thái `idle→…→active`, mỗi bước nguyên tử trong Aurora PostgreSQL | `spec.md` FR-EXBOT-003, `states.md` |
| Key-provision flow (F-03a) | Chain Indexer → key-provision SQS → KMS GenerateKeyPair ×2 → HL approveAgent → `key_status='active'` | `spec.md` FR-EXBOT-080, `flows.md` F-03a |
| Rate limiter (HL) | Tất cả HL API calls trong preflight + hedge open + reconcile + stop phải đi qua ElastiCache Redis token bucket | `spec.md` FR-EXBOT-091 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Chi tiết thuật toán LP mint (PositionCalc, tick range) | Zen-proprietary — SOTATEK integrate via ABI | Test chỉ verify event/state output, không verify nội bộ tính toán tick |
| BnzaExVault ABI chi tiết | IC-EXBOT-002: ABI chưa confirmed (OQ-EXBOT-08 Open) | Test A4 (LP mint fail) cần deferred |
| Pool address + wethIndex per chain | OQ-EXBOT-03 Open | Test dual-chain wethIndex cần deferred |
| Builder fee API endpoint/weight | OQ-EXBOT-05 Open | Test builder fee check cần deferred (I-07) |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Gọi `POST /api/exbot/start` sau khi đã nạp tiền on-chain | Chỉ có thể start bot nếu không có bot nào đang active/paused/closing/safe_mode/error. Không thể có 2 bot đồng thời (Phase A). | `spec.md` BR-EXBOT-001, FR-EXBOT-001 |
| ExBot Lambda | System | Nhận request, chạy preflight, điều phối toàn bộ luồng khởi động | Standalone service, không co-deployed với OPERATOR. Chỉ nhận request qua API Gateway + HMAC Lambda Authorizer. | `spec.md` BR-EXBOT-010 |
| BnzaExVault (Solidity) | External | Nhận `vaultMint()` call, emit `VaultMinted` event | SOTATEK integrates via ABI only. ABI confirmed by zen at Phase 0. | IC-EXBOT-002 |
| Hyperliquid API | External | Nhận lệnh short IOC + lệnh stop reduce-only, cung cấp marginSummary | Giới hạn rate: 800 weight/min (FR-EXBOT-091). Phải đi qua Signing Lambda. | `spec.md` IC-EXBOT-001 |
| Signing Lambda | System | Ký lệnh HL bằng agent key qua kms:Sign | Chỉ IAM role của Signing Lambda được phép kms:Sign. Private key không rời KMS. | `spec.md` FR-EXBOT-080, NFR-EXBOT-006 |
| AWS KMS | System | Lưu master key + agent key, thực hiện ký khi được Signing Lambda yêu cầu | Private keys không bao giờ rời KMS HSM. Failure → SAFE_MODE hoặc abort provisioning. | `spec.md` FR-EXBOT-080, IC-EXBOT-005 |
| Chain Indexer (Fargate) | System | Phát hiện on-chain deposit event, enqueue key-provision job | Kích hoạt F-03a tự động. Không liên quan đến start request của user. | `flows.md` F-03a |
| Key-Provision Worker | System | Chạy KMS GenerateKeyPair ×2, gọi HL approveAgent, set key_status='active' | Chạy tự động khi có deposit event. Không cần user action. | `spec.md` FR-EXBOT-080 |

**Nhận xét readiness:** Actors đủ rõ để thiết kế test theo role. Signing Lambda được liệt kê trong UC §1 (updated 2026-07-07). Phân biệt `BnzaExVault` (LP custody contract) và `vaultAddress/subaccount` (HL subaccount) được nêu rõ trong BR-EXBOT-008 — tester cần lưu ý.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | User đã nạp tiền on-chain; `BnzaExVault` balance > 0 cho user này | Yes | UC §2, `spec.md` FR-EXBOT-002 (step 2) |
| 2 | Key-provision đã hoàn tất: `hl_agent_keys.key_status='active'` cho user này | Yes | UC §2, `spec.md` FR-EXBOT-002 (step 4), FR-EXBOT-080 |
| 3 | User không có ExBot nào đang active/paused/closing/safe_mode/error | Yes | UC §2, `spec.md` FR-EXBOT-001, BR-EXBOT-001 |
| 4 | User có tài khoản HL với isolated margin balance ≥ required × 2.0 | Yes | UC §2, `spec.md` FR-EXBOT-002 (step 3), FR-EXBOT-061 |
| 5 | Builder fee (5bps) đã được confirm trên HL | Yes | UC §2, `spec.md` FR-EXBOT-002 (step 5) |
| 6 | User wallet có đủ ETH/native token cho gas phí vault transaction | Yes | UC §2 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 F-03a: Auto Key-Provision on Deposit

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Chain Indexer (Fargate) | Phát hiện on-chain deposit event của user | Enqueue job `{userId, depositAmount, txHash}` vào key-provision SQS | — | — | `flows.md` F-03a |
| 2 | Key-Provision Worker | Nhận message từ SQS | Gọi KMS GenerateKeyPair để tạo master key | KMS ThrottlingException → backoff + retry (max 3) | Abort provisioning, enqueue retry; sau max retry: admin alert; `key_status` giữ `provisioning` | `spec.md` FR-EXBOT-080 |
| 3 | AWS KMS | Nhận GenerateKeyPair request (master key) | Trả về `hl_user_address` (public only); private key stays in HSM | — | KMS unavailable → abort step 2 | `spec.md` FR-EXBOT-080 |
| 4 | Key-Provision Worker | Gọi KMS GenerateKeyPair lần 2 (agent key) | Trả về `agent_address` (public only) | — | Tương tự step 2 | `spec.md` FR-EXBOT-080 |
| 5 | Key-Provision Worker | Gọi HL `approveAgent(hl_user_address, agent_address)` | HL xác nhận agent được đăng ký là delegate | — | `approveAgent` fail → `key_status='provisioning'`; retry via key-provision queue; admin alert on SLA breach | `spec.md` FR-EXBOT-080 |
| 6 | Key-Provision Worker | INSERT `hl_agent_keys` | `key_status='active'`; 1 row per user có thể là `active` tại một thời điểm (BR-EXBOT-012) | — | Nếu HL chưa confirm → không set `active` | `spec.md` FR-EXBOT-080, BR-EXBOT-012 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `hl_agent_keys.key_status` | Chỉ 1 row per user được phép là `'active'` tại bất kỳ thời điểm nào. DB-level constraint. | Yes | Bản ghi active duy nhất tồn tại | UNIQUE constraint violation | `spec.md` BR-EXBOT-012 |
| Private key | Private keys không bao giờ rời KMS HSM — không lưu trong DB, app memory, hoặc log | Yes | Key chỉ là public address trong DB | Security violation | `spec.md` NFR-EXBOT-006, FR-EXBOT-080 |
| KMS failure retry | Max 3 attempts với exponential backoff khi KMS unavailable | Yes | Key provision thành công | Sau 3 lần fail: admin alert; `key_status` không set `active` | `spec.md` FR-EXBOT-080, IC-EXBOT-005 |
| Agent key states | Chỉ có 3 trạng thái: `active` / `superseded` / `revoked`. Không có trạng thái `provisioning` trong state machine của `states.md`. Tuy nhiên spec.md FR-EXBOT-080 đề cập `key_status='provisioning'` trong failure path. | ⚠️ Partial | — | Xem I-17 mới | `states.md`, `spec.md` FR-EXBOT-080 |
| Idempotency — queue consumer | Key-provision worker insert `message_id` vào `queue_idempotency` với `state='started'` tại đầu xử lý. UNIQUE conflict = duplicate delivery → return immediately. | Yes | Mỗi message chỉ được xử lý một lần | Xử lý lặp lại bị ngăn chặn | `spec.md` FR-EXBOT-011 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| KMS failure sau max retry | Admin notification | Không có message verbatim trong spec — xem I-15 (Low, open) | `spec.md` FR-EXBOT-080 | `spec.md` FR-EXBOT-080 |
| HL approveAgent fail | Internal — retry + admin alert on SLA breach | Không có message verbatim | `spec.md` FR-EXBOT-080 | `spec.md` FR-EXBOT-080 |
| Key provision hoàn tất | State transition | `hl_agent_keys.key_status='active'`; bot start có thể tiến hành | — | `spec.md` FR-EXBOT-080 |

---

### 6.2 F-03b: User-Triggered Bot Start — Preflight

#### A. Luồng xử lý preflight

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | USDC Investor | Gọi `POST /api/exbot/start` qua POOL UI | ExBot Lambda nhận request | — | — | UC §3 step 1 |
| 2a | ExBot Lambda | One-bot policy check: SELECT bot_registry WHERE user_id=? AND status IN ('active','paused','closing','safe_mode','error') | Count = 0 → pass | — | Count > 0 → reject E-EXBOT-001 "You already have an active ExBot. Close or wait for the existing bot to finish." HTTP 409; no bot record created | `spec.md` FR-EXBOT-001, E-EXBOT-001 |
| 2b | ExBot Lambda | Vault balance check: kiểm tra BnzaExVault balance > 0 cho user | Balance > 0 → pass | — | Balance = 0 → block E-EXBOT-025 "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." HTTP 400 | `spec.md` FR-EXBOT-002 step 2, E-EXBOT-025 |
| 2c | ExBot Lambda | HL margin check: fetch `marginSummary`, verify ≥ required × 2.0 | Margin đủ → pass | — | Insufficient → block "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." HTTP 400 (E-EXBOT-002) | `spec.md` FR-EXBOT-002 step 3, FR-EXBOT-061, E-EXBOT-002 |
| 2d | ExBot Lambda | Key status check: verify `hl_agent_keys.key_status='active'` | key_status='active' → pass | — | Not active → block E-EXBOT-017 "Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete." HTTP 400 | `spec.md` FR-EXBOT-002 step 4, E-EXBOT-017 |
| 2e | ExBot Lambda | Builder fee check: confirm 5bps builder fee trên HL | Fee confirmed → pass | — | Fee not confirmed → block E-EXBOT-005 "HL builder fee (5bps) approval required before starting ExBot." HTTP 400 | `spec.md` FR-EXBOT-002 step 5, E-EXBOT-005 |
| 2f | ExBot Lambda | LP mint simulation | Simulation pass → pass | — | Simulation fail → block E-EXBOT-006 "LP mint simulation failed. Check pool liquidity or adjust deposit amount." HTTP 400 | `spec.md` FR-EXBOT-002 step 6, E-EXBOT-006 |

#### B. Business rules và validation — preflight

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| One-bot policy (Phase A) | `status IN ('active','paused','closing','safe_mode','error')` đều tính vào giới hạn 1 bot | Yes | Pass preflight step 1 | E-EXBOT-001, HTTP 409 | `spec.md` BR-EXBOT-001, FR-EXBOT-001 |
| Vault balance | `BnzaExVault` on-chain balance > 0 là điều kiện bắt buộc trước khi start — đây là preflight step 2 | Yes | Pass preflight step 2 | E-EXBOT-025, HTTP 400 | `spec.md` FR-EXBOT-002, E-EXBOT-025 |
| HL margin buffer | `required_margin = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`; cần balance ≥ required × 2.0 | Yes | Pass preflight step 3 | E-EXBOT-002, HTTP 400 | `spec.md` FR-EXBOT-061 |
| Preflight thứ tự tuần tự | Bất kỳ check nào fail thì dừng; không tạo bot record | Yes | Tất cả 6 check pass → tạo bot record | Bot record không được tạo khi fail | `spec.md` FR-EXBOT-002 |
| HL rate limit tại preflight | Margin check (step 3) tiêu thụ HL weight bất kể kết quả. Weight bị tính vào quota 800/min ngay tại thời điểm gọi API. | Yes | Weight được tính | Weight vẫn bị tính dù fail ở bước sau | `spec.md` FR-EXBOT-091, I-09 (Answered) |

#### C. Thông báo, lỗi và phản hồi hệ thống — preflight

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| One-bot policy fail | API error response HTTP 409 | "You already have an active ExBot. Close or wait for the existing bot to finish." | E-EXBOT-001 | `spec.md` §5 |
| Vault balance = 0 | API error response HTTP 400 | "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." | E-EXBOT-025 | `spec.md` §5 |
| HL margin insufficient | API error response HTTP 400 | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | E-EXBOT-002 | `spec.md` §5 |
| Key not provisioned | API error response HTTP 400 | "Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete." | E-EXBOT-017 | `spec.md` §5 |
| Builder fee not confirmed | API error response HTTP 400 | "HL builder fee (5bps) approval required before starting ExBot." | E-EXBOT-005 | `spec.md` §5 |
| LP mint simulation fail | API error response HTTP 400 | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | E-EXBOT-006 | `spec.md` §5 |

---

### 6.3 F-03b: User-Triggered Bot Start — Execution (Post-Preflight)

#### A. Luồng xử lý execution

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 3 | ExBot Lambda | Tạo bot record | INSERT vào `bots` với `lifecycle_state='preflight'` | — | — | UC §3 step 3, `spec.md` FR-EXBOT-003 |
| 4 | ExBot Lambda → BnzaExVault | Gọi `vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` | `VaultMinted(user, botId, tokenId, liquidity)` event emitted | — | LP mint fail → `lifecycle_state='error'`; A4 deferred pending OQ-EXBOT-08 | UC §3 step 4, `flows.md` F-03b |
| 5 | ExBot Lambda | Nhận VaultMinted event, UPDATE Aurora PostgreSQL | `positions.tokenId`, `tickLower`, `tickUpper`, `wethIndex` updated; `lifecycle_state='lp_opened'` | — | — | UC §3 step 5, `spec.md` FR-EXBOT-003 |
| 6 | ExBot Lambda → Signing Lambda → HL | Mở short IOC: `targetShortEth = lpEthAmount × hedgeRatio (0.70)`; tạo cloid deterministic | Lệnh IOC submitted qua Signing Lambda (kms:Sign) | — | HL unreachable / IOC reject → xem I-11 (High, open) — UC A7/A10 ghi `error` nhưng `states.md` chỉ có `hedge_pre_open → safe_mode` | UC §3 step 6, `spec.md` FR-EXBOT-024, FR-EXBOT-080 |
| 7 | ExBot Lambda | Post-order reconcile: fetch `clearinghouseState` | Verify actual size matches expected; extract `entry_price`, `liquidation_price`, `effective_leverage` | A11: actual size deviates > threshold → enqueue `partial_repair`; alert operator | Reconcile mismatch > threshold → enqueue partial_repair; `drift_threshold` = `lpValueUsd × 3%` (pending OQ-EXBOT-11) | UC §3 step 7, `spec.md` FR-EXBOT-025 |
| 8 | ExBot Lambda | Cập nhật hedge_legs | `lifecycle_state='hedge_post_confirmed'`; `hedge_legs.entry_price`, `liq_price`, `effective_leverage` updated | — | — | UC §3 step 8, `spec.md` FR-EXBOT-003 |
| 9 | ExBot Lambda | Tính `stop_trigger_px` (BigDecimal) | `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)` | — | — | UC §3 step 9, `spec.md` FR-EXBOT-030 |
| 9b | ExBot Lambda → Signing Lambda → HL | Đặt reduce-only stop market với `stop_trigger_px` | Stop placed và confirmed trên HL | — | Stop placement fail → `lifecycle_state='safe_mode'` (UC A8, confirmed I-06 Answered); auto-recovery per FR-EXBOT-050 | UC §3 step 9, UC §4 A8, `states.md` `stop_placing → safe_mode` |
| 10 | ExBot Lambda | Update hedge_legs + lifecycle | Record `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size`, `stop_distance_pct`; `lifecycle_state='stop_verified' → 'active'` | — | — | UC §3 step 10, `spec.md` FR-EXBOT-031 |
| 11 | ExBot Lambda → POOL UI | Bot active; status visible on next poll | `bots.lifecycle_state='active'`, `bots.status='active'` | — | — | UC §3 step 11 |

#### B. Business rules và validation — execution

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Lifecycle state sequence | `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` — không được bỏ bước | Yes | Bot đạt `active` | — | `spec.md` FR-EXBOT-003, `states.md` |
| Mỗi state transition nguyên tử | Mỗi transition được lưu vào Aurora PostgreSQL trước khi chuyển bước | Yes | Consistency đảm bảo | Partial state trên crash | `spec.md` FR-EXBOT-003 |
| cloid deterministic | `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | Yes | Same retry → same cloid | Duplicate submission → reconcile first, không retry mù | `spec.md` FR-EXBOT-024 |
| stop_trigger_px BigDecimal | `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`. `liq_distance_pct = (liq_price - entry_price) / entry_price`; fallback: `1 / effective_leverage`. Phase A stopSafetyFactor = 0.70. Không được dùng float/number. | Yes | Stop được đặt đúng | Precision error → sai giá stop | `spec.md` FR-EXBOT-030 |
| Stop bắt buộc trước khi active | Bot không được chuyển sang `stop_verified` cho đến khi stop confirmed. Bot không thể reach `active` nếu chưa có stop confirmed. | Yes | `hedge_legs.stop_price` populated khi `lifecycle_state='active'` | Stop fail → `safe_mode`, không phải `active` | `spec.md` FR-EXBOT-031 |
| wethIndex per chain | `wethIndex` (0 hoặc 1) phải được verify và lưu vào `positions.weth_index` tại LP open. Không hardcode. | Yes | Dual-chain LP amount tính đúng | Tính sai LP ETH amount → hedge size sai | `spec.md` FR-EXBOT-004 |
| Post-reconcile trước khi ghi success | `rebalance_attempts.status='success'` không được ghi trước khi reconcile xác nhận actual state | Yes | Audit trail đúng | Sai status trong rebalance_attempts | `spec.md` FR-EXBOT-025 |
| hedge_legs.stop_price bắt buộc | `hedge_legs.stop_price` phải được điền khi `lifecycle_state='active'` | Yes | Stop monitoring có giá tham chiếu | Missing stop_price → stop monitoring không hoạt động | `spec.md` FR-EXBOT-031 |

#### C. Thông báo, lỗi và phản hồi hệ thống — execution

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| LP mint fail | State transition: `lifecycle_state='error'`; refund behavior pending OQ-EXBOT-08 | — | UC §4 A4 | UC §4 A4, deferred I-05 |
| HL unreachable trong hedge open | State transition: I-11 Open — UC A7 ghi `error`, `states.md` chỉ có `→ safe_mode` | Xem I-11 | UC §4 A7 | I-11 (High, Open) |
| HL reject IOC order | State transition: I-11 Open — UC A10 ghi `error`, `states.md` chỉ có `→ safe_mode` | Xem I-11 và I-12 | UC §4 A10 | I-11/I-12 (High/Medium, Open) |
| Stop placement fail | State transition: `lifecycle_state='safe_mode'` (confirmed I-06); return "HL service unavailable, please retry." | E-EXBOT-008 (xem I-12 về IOC) | UC §4 A8, `states.md` | `states.md`, I-06 (Answered) |
| Reconcile mismatch | Internal: enqueue `partial_repair`; alert operator | E-EXBOT-011 "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | E-EXBOT-011 | `spec.md` §5 |
| Bot start success | API success response + State transition | `{status: 'active', botId, lifecycle_state: 'active'}` | — | UC §3 step 11, `spec.md` FR-EXBOT-003 |

---

## §F.1 — Inventory (Functions, Operations, Triggers, Data Objects, States, Events, Messages)

| # | Item | Type | Description | Source |
|---|---|---|---|---|
| F1-01 | `POST /api/exbot/start` | API Endpoint (trigger) | User-initiated bot start. Received by ExBot Lambda via API Gateway + HMAC Lambda Authorizer. | `spec.md` FR-EXBOT-090, `flows.md` F-03b |
| F1-02 | Preflight check — one-bot policy | Operation | SELECT bot_registry WHERE user_id + status IN ('active','paused','closing','safe_mode','error'). Fail → reject E-EXBOT-001. | `spec.md` FR-EXBOT-001 |
| F1-03 | Preflight check — vault balance | Operation | Check BnzaExVault on-chain balance > 0 for user. Fail → E-EXBOT-025. | `spec.md` FR-EXBOT-002 step 2 |
| F1-04 | Preflight check — HL margin | Operation | Fetch marginSummary (HL weight = 2); verify balance ≥ required × 2.0. Fail → E-EXBOT-002. | `spec.md` FR-EXBOT-002 step 3, FR-EXBOT-061 |
| F1-05 | Preflight check — key_status | Operation | Verify hl_agent_keys.key_status='active'. Fail → E-EXBOT-017. | `spec.md` FR-EXBOT-002 step 4 |
| F1-06 | Preflight check — builder fee | Operation | Confirm 5bps builder fee on HL. Fail → E-EXBOT-005. OQ-EXBOT-05 Open (API endpoint unknown). | `spec.md` FR-EXBOT-002 step 5 |
| F1-07 | Preflight check — LP mint simulation | Operation | Simulate LP mint with slippage tolerance. Fail → E-EXBOT-006. | `spec.md` FR-EXBOT-002 step 6 |
| F1-08 | Bot record creation | Data write | INSERT bots (lifecycle_state='preflight') after all 6 preflight pass. | `spec.md` FR-EXBOT-003 |
| F1-09 | `BnzaExVault.vaultMint()` | On-chain transaction | LP NFT minted on-chain; VaultMinted event emitted. | `flows.md` F-03b |
| F1-10 | VaultMinted event | On-chain event | (user, botId, tokenId, liquidity) — triggers update of positions table. | `flows.md` F-03b |
| F1-11 | Aurora PostgreSQL positions update | Data write | UPDATE positions with tokenId, tickLower, tickUpper, wethIndex, lifecycle_state='lp_opened'. | `spec.md` FR-EXBOT-003 |
| F1-12 | Short IOC order via Signing Lambda | HL operation | targetShortEth = lpEthAmount × hedgeRatio (0.70). Signing Lambda → kms:Sign → HL. Cloid: `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. | `spec.md` FR-EXBOT-024, FR-EXBOT-080 |
| F1-13 | Post-order reconcile | Operation | Fetch clearinghouseState; verify actual size = expected; extract entry_price/liq_price/leverage. | `spec.md` FR-EXBOT-025 |
| F1-14 | stop_trigger_px computation | Calculation | BigDecimal only. Formula: `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)`. `liq_distance_pct = (liq_price - entry_price) / entry_price`; fallback: `1 / effective_leverage`. | `spec.md` FR-EXBOT-030 |
| F1-15 | Stop reduce-only order | HL operation | Reduce-only stop market at stop_trigger_px via Signing Lambda. | `spec.md` FR-EXBOT-031 |
| F1-16 | Lifecycle state transitions (bot start sequence) | State machine | `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`. 8 steps, none skippable. | `spec.md` FR-EXBOT-003, `states.md` |
| F1-17 | bots table | Data object | `id`, `user_id`, `status` (coarse), `lifecycle_state` (fine), `chain`, etc. | `srs/erd.md` |
| F1-18 | positions table | Data object | `bot_id`, `tokenId`, `tickLower`, `tickUpper`, `liquidity`, `weth_index`, `custodian`, `custodian_address`. | `srs/erd.md` |
| F1-19 | hedge_legs table | Data object | `bot_id`, `hl_asset`, `target_ratio`, `leverage`, `hl_account_address`, `stop_order_id`, `stop_cloid`, `stop_price`, `stop_size`, `entry_price`, `liquidation_price`, `effective_leverage`, `stop_distance_pct`, `margin_status`, etc. | `srs/erd.md` |
| F1-20 | hl_agent_keys table | Data object | `user_id`, `hl_user_address`, `agent_address`, `key_status` ('active'/'superseded'/'revoked'). 9 fields RETIRED (legacy manual-approval flow). | `srs/erd.md` |
| F1-21 | queue_idempotency table | Data object | `key`, `message_id`, `kind`, `state` ('started'/'succeeded'/'failed'/'retryable'), `bot_id`, etc. | `srs/erd.md` |
| F1-22 | key-provision SQS queue | Queue (trigger) | Produced by Chain Indexer (Fargate); consumed by Key-Provision Worker. | `spec.md` FR-EXBOT-010 |
| F1-23 | Key-Provision Worker | Worker | Generates KMS keys + HL approveAgent + set key_status='active'. Triggered by key-provision queue message. | `spec.md` FR-EXBOT-080 |
| F1-24 | E-EXBOT-001 | Error message | "You already have an active ExBot. Close or wait for the existing bot to finish." HTTP 409. | `spec.md` §5 |
| F1-25 | E-EXBOT-002 | Error message | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." HTTP 400. | `spec.md` §5 |
| F1-26 | E-EXBOT-005 | Error message | "HL builder fee (5bps) approval required before starting ExBot." HTTP 400. | `spec.md` §5 |
| F1-27 | E-EXBOT-006 | Error message | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." HTTP 400. | `spec.md` §5 |
| F1-28 | E-EXBOT-008 | Error message | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." HTTP 503. | `spec.md` §5 |
| F1-29 | E-EXBOT-017 | Error message | "Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete." HTTP 400. | `spec.md` §5 |
| F1-30 | E-EXBOT-025 | Error message (new) | "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." HTTP 400. | `spec.md` §5 |
| F1-31 | E-EXBOT-011 | Error message (internal) | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." (internal alert). | `spec.md` §5 |
| F1-32 | agent key states | Enum (3-state) | `active` / `superseded` / `revoked`. No `provisioning` in states.md — spec.md FR-EXBOT-080 mentions `provisioning` in failure path (conflict, see Issue IS-04). | `states.md`, `spec.md` FR-EXBOT-080 |
| F1-33 | lifecycle_state enum (bot init) | Enum | `idle`, `preflight`, `lp_opening`, `lp_opened`, `hedge_pre_open`, `hedge_post_confirmed`, `stop_placing`, `stop_verified`, `active` (+ runtime states). | `states.md`, `spec.md` FR-EXBOT-003 |
| F1-34 | hedgeRatio (Phase A) | Parameter | 0.70 (zen-proprietary). targetShortEth = lpEthAmount × 0.70. | `spec.md` FR-EXBOT-021 |
| F1-35 | stopSafetyFactor (Phase A) | Parameter | 0.70 (pending Phase 0 backtest — OQ-EXBOT-07). | `spec.md` FR-EXBOT-030 |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations & Messages

| Item | States / Preconditions | Validations / Business Rules | Dependencies | Resolved Messages | Source |
|---|---|---|---|---|---|
| `hl_agent_keys.key_status` | `active` / `superseded` / `revoked`. Chỉ 1 `active` per user (DB constraint). Không có `provisioning` trong states.md — xem IS-04. | BR-EXBOT-012: DB-level UNIQUE constraint trên (user_id, key_status='active'). BR-EXBOT-013: rows immutable after write. BR-EXBOT-014: rotation nguyên tử (old→superseded + new→active trong same tx). | key-provision worker, AWS KMS, HL approveAgent | E-EXBOT-017 khi preflight fail | `states.md`, `spec.md` BR-EXBOT-012–014 |
| `bots.lifecycle_state` (bot start sequence) | Sequence: idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active. Mỗi bước nguyên tử. | FR-EXBOT-003: không được bỏ bước; mỗi transition persist trước khi proceed. | Aurora PostgreSQL | — | `spec.md` FR-EXBOT-003, `states.md` |
| `bots.status` (coarse) | `active` / `paused` / `closing` / `closed` / `safe_mode` / `error`. Sau start: `active`. | Coarse status phản chiếu `lifecycle_state`. | — | — | `spec.md` FR-EXBOT-003 |
| Preflight margin computation | Precondition: phải có HL Oracle price. | `required_margin = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`; buffer factor = 2.0. Tất cả BigDecimal. | HL marginSummary (weight = 2) | E-EXBOT-002 | `spec.md` FR-EXBOT-061 |
| stop_trigger_px | Precondition: entry_price và liquidation_price phải được reconcile trước. | BigDecimal only: `entry_price × (1 + liq_distance_pct × 0.70)`. Fallback khi liq_price unavailable: `liq_distance_pct = 1/effective_leverage`. | hedge_legs.entry_price, liq_price, effective_leverage | — | `spec.md` FR-EXBOT-030 |
| cloid | Deterministic per (botId, attemptId, stage, version). | `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Same retry → same cloid. Payload changed → increment version. Dup cloid → reconcile first, không retry. | — | — | `spec.md` FR-EXBOT-024 |
| `positions.weth_index` | Phải được set tại LP open. 0 hoặc 1 (WETH là token0 hay token1). | Verify per chain; không hardcode. OQ-EXBOT-03 (Open) cung cấp pool address + wethIndex. | OQ-EXBOT-03 | — | `spec.md` FR-EXBOT-004 |
| `queue_idempotency` | State: `started` → `succeeded` / `failed` / `retryable`. | UNIQUE on message_id. Conflict = duplicate → return immediately without processing. reportBatchItemFailures cho Lambda SQS. | Aurora PostgreSQL | — | `spec.md` FR-EXBOT-011 |
| `hedge_legs.stop_price` | Phải populated khi `lifecycle_state='active'`. | Bot không thể reach `active` nếu chưa có stop_price. | stop placement confirmed | — | `spec.md` FR-EXBOT-031 |
| `rebalance_attempts.status` | `success` / `failed` / `partial` / `skipped`. | `success` KHÔNG được ghi trước khi reconcile xác nhận actual state. | clearinghouseState fetch | — | `spec.md` FR-EXBOT-025 |

---

## §F.3 — Functional Logic & Workflow Decomposition

### F.3.1 Happy Path — Bot Start thành công

**Trigger:** Investor gọi `POST /api/exbot/start`  
**Điều kiện:** Tất cả 6 preflight pass  
**Actor:** USDC Investor → ExBot Lambda → BnzaExVault → Signing Lambda → AWS KMS → Hyperliquid → Aurora PostgreSQL

| Bước | Input | System action | Output / State |
|---|---|---|---|
| Preflight (1–6) | POST body (userId), HL marginSummary, BnzaExVault balance, hl_agent_keys | 6 checks in sequence; any fail → return error, no bot record | All pass → proceed |
| Create bot record | userId, chain | INSERT bots (`lifecycle_state='preflight'`) | `bots.id` created |
| LP mint | vaultMint params (tickLower, tickUpper, amount0, amount1, slippageBps) | BnzaExVault.vaultMint() on-chain | VaultMinted(user, botId, tokenId, liquidity); `lifecycle_state='lp_opened'` |
| Short IOC | targetShortEth, cloid, hl_user_address | Signing Lambda → kms:Sign → HL | Short position opened |
| Post-reconcile | clearinghouseState | Verify actual size; extract entry_price, liq_price, leverage | `hedge_legs` updated; `lifecycle_state='hedge_post_confirmed'` |
| Compute stop price | entry_price, liq_price, leverage | BigDecimal formula: `entry_price × (1 + liq_distance_pct × 0.70)` | stop_trigger_px computed |
| Place stop | stop_trigger_px, size | Signing Lambda → kms:Sign → HL reduce-only stop market | Stop confirmed; `lifecycle_state='stop_verified'` → `'active'` |

**Output cuối:** `{lifecycle_state: 'active', status: 'active', botId}`. `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` đầy đủ. LP NFT giữ bởi vault.

### F.3.2 Alternative Paths

| Path | Trigger | System response | State outcome |
|---|---|---|---|
| A1 — One-bot policy fail | Có bot đang active/paused/closing/safe_mode/error | Reject E-EXBOT-001 HTTP 409; no bot record | No state change |
| A2 — Margin insufficient | marginBalance < required × 2.0 | Block E-EXBOT-002 HTTP 400 với required/current/shortfall amounts | No state change |
| A3 — No vault deposit | BnzaExVault balance = 0 | Block E-EXBOT-025 HTTP 400 | No state change |
| A5 — Builder fee not confirmed | Builder fee check fail | Block E-EXBOT-005 HTTP 400 | No state change |
| A6 — LP simulation fail | LP mint simulation fail | Block E-EXBOT-006 HTTP 400; no vault call | No state change |
| A9 — Key not provisioned | key_status ≠ 'active' | Block E-EXBOT-017 HTTP 400 | No state change |

### F.3.3 Exception Paths

| Path | Trigger | System response | State outcome |
|---|---|---|---|
| A4 — LP mint fail | vaultMint() transaction reverts | `lifecycle_state='error'`; return funds (mechanism pending OQ-EXBOT-08) | `lifecycle_state='error'` |
| A7 — HL unreachable (hedge step) | HL API unreachable tại step 6 | **I-11 Open**: UC A7 → `error`; `states.md` → `safe_mode` (conflict) | Conflict — xem I-11 |
| A8 — Stop placement fail | HL stop order không được confirm | `lifecycle_state='safe_mode'`; alert operator; auto-recovery per FR-EXBOT-050 | `lifecycle_state='safe_mode'` (confirmed I-06) |
| A10 — HL IOC reject | HL từ chối IOC order (ví dụ insufficient margin during order) | **I-11 Open**: UC A10 → `error`; `states.md` → `safe_mode` (conflict) | Conflict — xem I-11 |
| A11 — Reconcile mismatch | actual size deviates > drift_threshold | Enqueue `partial_repair`; alert operator | Bot stays at `hedge_post_confirmed`; repair queued |

---

## §F.4 — Functional Integration & Data Consistency

| Hành động | Downstream effect | Data consistency check | Source |
|---|---|---|---|
| On-chain deposit (F-03a trigger) | Chain Indexer phát hiện → enqueue key-provision SQS → Key-Provision Worker → KMS → HL approveAgent → `key_status='active'` | Nếu `approveAgent` fail → `key_status` không được set 'active'; bot start bị block bởi E-EXBOT-017 | `spec.md` FR-EXBOT-080, `flows.md` F-03a |
| `POST /api/exbot/start` → preflight | 6 preflight checks đều tiêu thụ resource (HL weight từ margin check) | Margin check weight bị tính vào quota 800/min ngay cả khi fail ở bước sau | `spec.md` FR-EXBOT-091, I-09 (Answered) |
| vaultMint() → VaultMinted event | Aurora PostgreSQL positions updated; lifecycle_state='lp_opened' | tokenId, wethIndex phải được set đúng per chain. OQ-EXBOT-03 cần xác nhận pool address + wethIndex | `spec.md` FR-EXBOT-003, FR-EXBOT-004 |
| Short IOC → reconcile | hedge_legs.entry_price, liq_price, effective_leverage updated; stop_trigger_px computed | rebalance_attempts.status='success' không được ghi trước reconcile | `spec.md` FR-EXBOT-025 |
| Stop placement → lifecycle 'active' | hedge_legs.stop_price, stop_cloid, stop_size, stop_distance_pct phải populated | Bot không thể reach 'active' nếu stop_price chưa được set | `spec.md` FR-EXBOT-031 |
| Bot 'active' → light-check scheduling | next_light_check_at = now + 5min + random(−45s, +45s) — batch update per shard | Aurora PostgreSQL write budget: 1 UPDATE per shard, không per-bot | `spec.md` FR-EXBOT-013 |
| key_status='active' (rotation/revoke) | Key rotation: old row → 'superseded' + new row → 'active' trong same tx. Revoke: row → 'revoked'. | BR-EXBOT-014: không có window khi cả hai đều 'active' hoặc không có 'active' nào | `spec.md` BR-EXBOT-012–014 |

---

## §F.5 — Acceptance Criteria Candidates

| AC # | Scenario | Given | When | Then | Source / Note |
|---|---|---|---|---|---|
| AC-01 | Happy path — bot start thành công | Không có bot active; vault balance > 0; margin đủ; key_status='active'; builder fee confirmed | Investor gọi POST /api/exbot/start | lifecycle_state='active'; stop_price populated; LP NFT trong vault; hedge_legs.entry_price, liq_price, effective_leverage đầy đủ | UC §3, US-001 AC-1 |
| AC-02 | One-bot policy — reject | Bot đang active tồn tại | Investor gọi POST /api/exbot/start | HTTP 409, E-EXBOT-001 message. Không tạo bot record. | `spec.md` FR-EXBOT-001 |
| AC-03 | Vault balance = 0 | Không có on-chain deposit | Investor gọi POST /api/exbot/start | HTTP 400, E-EXBOT-025 message | `spec.md` FR-EXBOT-002, E-EXBOT-025 |
| AC-04 | Margin insufficient | marginBalance < required × 2.0 | Investor gọi POST /api/exbot/start | HTTP 400, E-EXBOT-002 với required/current/shortfall amounts | US-001 AC-3 |
| AC-05 | Key not provisioned | key_status ≠ 'active' | Investor gọi POST /api/exbot/start | HTTP 400, E-EXBOT-017 message | `spec.md` FR-EXBOT-002 step 4 |
| AC-06 | Stop fail → safe_mode | Stop placement fail | ExBot Lambda hoàn thành LP mint + hedge open | lifecycle_state='safe_mode'; operator alert; auto-recovery bắt đầu | `states.md` (confirmed I-06) |
| AC-07 | Reconcile mismatch | actual size ≠ expected sau IOC | Post-order reconcile | partial_repair enqueued; operator alerted | `spec.md` FR-EXBOT-025 |
| AC-08 | KMS key — private key isolation | Key-provision flow complete | DB dump hl_agent_keys | Không có raw private key material trong bất kỳ field nào | `spec.md` NFR-EXBOT-006 |
| AC-09 | HL IOC reject → ? | HL từ chối IOC order | ExBot Lambda gọi short IOC | Suy luận cần xác nhận — phụ thuộc I-11: 'error' hay 'safe_mode'? | I-11 (High, Open) |
| AC-10 | wethIndex per chain | LP mint trên Base và Optimism | VaultMinted event xử lý | positions.weth_index populated đúng per chain; không hardcode | `spec.md` FR-EXBOT-004; deferred OQ-EXBOT-03 |
| AC-11 | stop_trigger_px BigDecimal | entry_price = $3,000; liq_price = $3,300; leverage 3x | computeStopTriggerPx() | stop_trigger_px = $3,000 × (1 + 0.10 × 0.70) = $3,210.00; không có float error; stop fires trước liq_price với 30% buffer | `spec.md` FR-EXBOT-030 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Bot 'active' → scheduled light-check | UC-EXBOT-light-check | Light-check worker bắt đầu evaluate rebalance reasons mỗi ~5 phút | `bots.lifecycle_state='active'` là tiền quyết cho light-check | `spec.md` FR-EXBOT-012, `states.md` |
| Bot 'active' → deep-audit scheduling | FR-EXBOT-016 | Deep-audit chạy mỗi 6h cho tất cả active + paused bots | `margin_status` được update qua deep-audit, không qua light-check | `spec.md` FR-EXBOT-016 |
| LP NFT được giữ bởi BnzaExVault | UC-EXBOT-user-redeem | User chỉ có thể redeem LP bằng cách gọi `BnzaExVault.redeem(tokenId)` on-chain | `positions.custodian='vault'` là postcondition của bot start | `spec.md` FR-EXBOT-070 |
| hedge_legs.stop_price populated | UC-EXBOT-light-check (stop monitoring) | Light-check evaluate `markPrice >= stop_price` để detect stop trigger | `hedge_legs.stop_price` PHẢI có sau bot start | `spec.md` FR-EXBOT-032 |
| key_status='active' phụ thuộc F-03a | UC-EXBOT-bot-start (precondition) | Bot start bị block E-EXBOT-017 nếu F-03a chưa hoàn tất | F-03a phải xảy ra trước F-03b | `spec.md` FR-EXBOT-080 |
| hedge_legs.entry_price / liq_price | FR-EXBOT-030, FR-EXBOT-060 | stop_trigger_px và margin thresholds phụ thuộc vào entry_price + liq_price từ reconcile | Phải được set đúng ngay sau reconcile | `spec.md` FR-EXBOT-025, FR-EXBOT-030 |
| BR-EXBOT-008 — BnzaExVault vs vaultAddress | Tất cả code integration | `BnzaExVault` (LP NFT custody contract) KHÔNG phải là `vaultAddress/subaccount` (HL subaccount). Nhầm lẫn gây bug nghiêm trọng. | Tester cần phân biệt rõ hai khái niệm này | `spec.md` BR-EXBOT-008 |

---

## 8. Acceptance Criteria

> Xem §F.5 ở trên — AC candidates đã được tổng hợp chi tiết.

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Security | Private keys không bao giờ rời KMS HSM. Chỉ Signing Lambda IAM role có kms:Sign. Không có key material trong DB, app memory, logs. | Test: DB dump hl_agent_keys không chứa raw private key. Log audit không expose key. | `spec.md` NFR-EXBOT-006, FR-EXBOT-080 |
| Precision | Tất cả hedge, stop, margin computations dùng BigDecimal. Float/number arithmetic bị cấm cho financial values. | Test: stop_trigger_px, targetShortEth, marginRequired không có float intermediate. | `spec.md` NFR-EXBOT-008 |
| Rate Limit (HL) | HL API: ≤ 800 weight/min. Margin check trong preflight = weight 2. Tất cả calls qua ElastiCache Redis rate limiter. | Test: nhiều start requests liên tiếp fail ở step 3+ vẫn tốn HL weight. | `spec.md` NFR-EXBOT-004, FR-EXBOT-091 |
| Idempotency | queue_idempotency.message_id UNIQUE prevents double execution. Cloid deterministic prevents double HL order. | Test: redelivery cùng key-provision message không tạo duplicate hl_agent_keys row. | `spec.md` NFR-EXBOT-007, FR-EXBOT-024 |
| Reliability | SAFE_MODE không phải terminal state. Auto-recovery path phải tồn tại. | Test: A8 (stop fail) → safe_mode → auto-recovery khi HL responsive + 3 reconciles | `spec.md` NFR-EXBOT-010, FR-EXBOT-050 |
| Multi-Chain | Base + Optimism từ Phase 1. wethIndex verified per chain tại LP open. | Test dual-chain deferred pending OQ-EXBOT-03. | `spec.md` NFR-EXBOT-009 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Issue Register

| ID | Severity | Type | Ref | Finding | Impact | Suggested fix / Question | Status |
|---|---|---|---|---|---|---|---|
| IS-01 | Blocker | CROSS_SOURCE_CONFLICT | UC §4 A7/A10 vs `states.md` (hedge_pre_open → safe_mode) | UC §4 A7 mô tả "HL unreachable → enter `error` state"; UC §4 A10 mô tả "HL reject IOC → enter `error` state". Nhưng `states.md` chỉ định nghĩa transition hợp lệ từ `hedge_pre_open` là `hedge_pre_open → safe_mode` — không có `hedge_pre_open → error`. Conflict tồn tại qua cả v3 (2026-07-04) và v4 (2026-07-07) sau khi UC được update. | Blocker cho AC-09. Tester không thể viết expected result cho 2 exception path quan trọng nhất của hedge open. | BA xác nhận: khi HL unreachable hoặc IOC bị reject tại hedge open, trạng thái đích là `error` hay `safe_mode`? Nếu là `safe_mode`, cần update UC §4 A7/A10. | Open (existing I-11) |
| IS-02 | Major | MISSING_INFO | UC §4 A11 vs `spec.md` FR-EXBOT-025 | `drift_threshold` (reconcile mismatch threshold) được nhắc trong A11 nhưng không được định nghĩa trong UC. FR-EXBOT-036 nêu `drift_threshold` và OQ-EXBOT-11 đề cập `lpValueUsd × 3%` nhưng là ứng viên chưa xác nhận (OQ-EXBOT-11 Open). | Blocker cho test reconcile mismatch boundary. | Xem I-02 (existing). BA/zen confirm OQ-EXBOT-11. | Open (existing I-02) |
| IS-03 | Minor | CROSS_SOURCE_CONFLICT | `spec.md` FR-EXBOT-080 KMS failure path vs `states.md` agent key states | `spec.md` FR-EXBOT-080 đề cập `key_status='provisioning'` trong failure path ("key remains key_status='provisioning'"). Nhưng `states.md` chỉ định nghĩa 3 states: `active`, `superseded`, `revoked` — không có `provisioning`. Không rõ `provisioning` là trạng thái transient hay trạng thái chính thức cần test. | Minor: không block test design chính nhưng gây nhầm lẫn cho tester thiết kế negative path. | BA confirm: `provisioning` có phải state chính thức trong `hl_agent_keys.key_status` không? Nếu có, cần add vào `states.md`. | Open (new IS-03) |
| IS-04 | Major | CROSS_SOURCE_CONFLICT | `frd.md` FR-EXBOT-001 (5 preflight checks) vs `spec.md` FR-EXBOT-002 (6 preflight checks) | `frd.md` FR-EXBOT-001 liệt kê 5 preflight checks (one-bot → margin → key_status → builder fee → LP sim) — không có vault balance check. `spec.md` FR-EXBOT-002 liệt kê 6 checks với vault balance là step 2, margin là step 3. `spec.md` canonical nhưng FRD chưa được sync. Thứ tự step 2 (vault) vs step 3 (margin) theo spec.md cũng khác với flow F-03b diagram. | Major: Tester thiết kế test dựa vào FRD sẽ bỏ sót vault balance check hoàn toàn. FRD chưa sync với spec.md sau update 2026-07-07. | BA update FRD FR-EXBOT-001 để phản ánh 6 preflight checks theo spec.md FR-EXBOT-002. Đây là FRD stale issue — spec.md đã được update nhưng FRD chưa được update. | Open (new IS-04) |
| IS-05 | Minor | INTERNAL_INCONSISTENCY | `userstories/us-001.md` Notes vs `states.md` | US-001 Notes: "`cooldown` and `parked` lifecycle states map to `status='active'`". Nhưng `states.md` (2026-06-18) đã remove `cooldown` và `parked` hoàn toàn. Notes section stale. | Minor: gây nhầm lẫn cho tester mới. AC-2 của US-001 đúng (không bao gồm cooldown/parked). | BA cleanup Notes section của US-001. | Open (existing I-16) |
| IS-06 | Note | MISSING_INFO | UC §7 FR Trace | FR trace chỉ liệt kê FR-001, 002, 004, 020, 030, 031. Thiếu: FR-EXBOT-003 (state tracking), FR-EXBOT-011 (queue idempotency), FR-EXBOT-080 (KMS), FR-EXBOT-091 (HL rate limiter). | Low: không block test design nhưng tăng rủi ro bỏ sót coverage. | BA bổ sung FR trace vào UC §7. | Open (existing I-13) |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-08 — BnzaExVault ABI | Integration | Test A4 (LP mint fail / refund mechanism) bị deferred | zen | Open |
| OQ-EXBOT-03 — Pool address + wethIndex | Data | Test dual-chain wethIndex + LP open per chain bị deferred | zen/SOTATEK | Open |
| OQ-EXBOT-05 — Builder fee API | Integration | Test builder fee preflight (step 5) bị deferred | zen | Open |
| OQ-EXBOT-11 — lpValueUsd formula | Calculation | Test reconcile mismatch boundary bị block | zen | Open |
| I-11 — A7/A10 state conflict | UC spec | Test HL unreachable / IOC reject expected state | BA | Open |

---

### 10.3 Audit Summary

#### Scoring Table

| # | Scoring Area | Max | Score | Status | Key Issues |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 17 | ✅ Clear | F1 inventory đầy đủ 35 items. Thiếu FR-003/011/080/091 trong UC §7 trace (IS-06, Minor). |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 18 | ⚠️ Partial | IS-03 (provisioning state conflict Minor), IS-01 (A7/A10 → error vs safe_mode Blocker). Phần lớn BRs đầy đủ. |
| 3 | Functional Logic & Workflow Decomposition | 25 | 16 | ⚠️ Partial | IS-01 Blocker: 2 exception paths (A7, A10) không có expected state rõ ràng. IS-04 (FRD stale, vault balance missing). Preflight logic 4/6 checks clear; 2 paths blocked. |
| 4 | Functional Integration & Data Consistency | 15 | 12 | ✅ Clear | On-chain ↔ off-chain flows đầy đủ. Deferred items documented (OQ-EXBOT-03/08). |
| 5 | UC / Spec Documentation Quality Issues | 15 | 9 | ⚠️ Partial | IS-01 Blocker tồn tại qua v3 → v4. IS-04 FRD stale (Major). IS-05 US-001 Notes stale (Minor). IS-03 states.md vs FR-EXBOT-080 conflict (Minor). |

**Auto-cap applied:**
- IS-01 là Blocker → Affected areas (Area 2, 3) max 40% of max. Area 3 bị cap tại 10/25. Area 2 bị cap tại 10/25.

**Điểm thực tế sau cap:**

| # | Scoring Area | Max | Raw | Cap | Final |
|---|---|---|---|---|---|
| 1 | Inventory | 20 | 17 | — | 17 |
| 2 | Data/State/BR/Messages | 25 | 18 | Cap 40% = 10 | 10 |
| 3 | Functional Logic & Workflow | 25 | 16 | Cap 40% = 10 | 10 |
| 4 | Integration & Data Consistency | 15 | 12 | — | 12 |
| 5 | Documentation Quality | 15 | 9 | — | 9 |
| **TOTAL** | | **100** | **72** | | **58** |

**Verdict: NOT READY (58/100)**

#### Blockers tồn tại

1. **IS-01 (I-11)**: Conflict giữa UC §4 A7/A10 (`error`) và `states.md` (`safe_mode`) cho hedge open failure. Tester không thể viết expected result cho 2 exception paths quan trọng nhất.

#### Major issues

2. **IS-04**: FRD FR-EXBOT-001 không bao gồm vault balance preflight check (step 2 theo spec.md FR-EXBOT-002). FRD stale sau update 2026-07-07. Tester dùng FRD sẽ bỏ sót hoàn toàn E-EXBOT-025 test path.
3. **IS-02 (I-02)**: `drift_threshold` chưa được xác nhận (OQ-EXBOT-11 Open) — block test reconcile mismatch boundary.

#### Khuyến nghị

Ưu tiên giải quyết IS-01 (I-11): BA xác nhận `hedge_pre_open` failure state là `error` hay `safe_mode`. Đây là blocker đơn giản cần 1 quyết định — nên resolve trong sprint hiện tại. Sau khi IS-01 resolved và FRD được sync (IS-04), audit có thể đạt 75–80 điểm và verdict Conditionally Ready. Hiện tại test cases cho A7 và A10 không được thiết kế cho đến khi I-11 có câu trả lời.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-17 | QC UC Read Agent | Tạo báo cáo audited lần đầu |
| v2 | 2026-07-01 | QC UC Read Agent | Re-audit: thêm I-01 đến I-10; cập nhật F.1–F.4 theo SRS mới |
| v3 | 2026-07-06 | QC UC Read Agent | Re-audit sau arc-migration 2026-07-04: update terminology (D1→Aurora PostgreSQL, ExBot Worker→ExBot Lambda, CF→AWS); thêm I-11/I-12/I-13/I-14/I-15/I-16; cập nhật E-EXBOT-017/025; 6 preflight checks |
| v4 | 2026-07-07 | QC UC Read Agent | Re-audit toàn bộ sau update UC 2026-07-07 (user-initiated trigger; vault balance preflight mới; US-001 updated). Thêm IS-03 (provisioning state conflict), IS-04 (FRD stale — thiếu vault balance check). Cập nhật F.1–F.5 đầy đủ. Score: 58/100, NOT READY. |






| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Khởi động bot thành công | `bots.lifecycle_state='active'`, `bots.status='active'` | UC §5, `spec.md` FR-EXBOT-003 |
| LP NFT custody | LP NFT được giữ bởi BnzaExVault (`positions.custodian='vault'`) | UC §5 |
| Vị thế hedge | HL short open với reduce-only stop đã đặt và confirmed | UC §5 |
| Dữ liệu hedge leg | `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` được điền đầy đủ | UC §5, `spec.md` FR-EXBOT-031 |


