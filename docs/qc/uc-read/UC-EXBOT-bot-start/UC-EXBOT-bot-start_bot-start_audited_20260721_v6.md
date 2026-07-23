# Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC-EXBOT-bot-start — Khởi động ExBot**
**Phiên bản:** v6
**Ngày tạo:** 2026-07-21
**Tác giả:** QC UC Read Agent
**Dựa trên:** uc-bot-start.md (updated 2026-07-20), spec.md (2026-07-20), us-001.md (2026-07-08), frd.md (2026-07-21)

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả luồng người dùng (USDC Investor) kích hoạt ExBot thông qua lệnh gọi `POST /api/exbot/start` sau khi đã hoàn tất nạp tiền on-chain vào `BnzaExVault`. Đây là thao tác người dùng chủ động — không phải luồng tự động sau khi nạp tiền. Luồng cấp phát khóa KMS (`key-provision`) chạy tự động ở sự kiện nạp tiền (F-03a) và phải hoàn tất trước khi người dùng gọi Start.

Khi nhận yêu cầu start, `ExBot Lambda` chạy tuần tự sáu bước kiểm tra preflight: (1) chính sách một-bot, (2) xác nhận số dư vault, (3) ký quỹ Hyperliquid đủ yêu cầu, (4) trạng thái khóa KMS đang active, (5) phí builder đã được xác nhận, (6) mô phỏng LP mint thành công. Nếu bất kỳ bước nào thất bại, toàn bộ yêu cầu bị từ chối ngay lập tức, không tạo bản ghi bot.

Khi preflight vượt qua, luồng khởi tạo tiếp tục theo thứ tự cố định: tạo bản ghi bot (lifecycle_state='preflight') → gọi `BnzaExVault.vaultMint(...)` → mở vị thế short ETH-USD trên Hyperliquid qua Signing Lambda → đặt lệnh stop reduce-only → bot chuyển sang trạng thái `active`. Mỗi bước chuyển trạng thái được ghi nguyên tử vào Aurora PostgreSQL trước khi tiếp tục bước tiếp theo.

Các điểm ảnh hưởng đến test design: thứ tự 6 bước preflight, trạng thái `key_status` bốn giá trị (provisioning/active/superseded/revoked), on-chain transaction lifecycle cho LP mint (có thể revert hoặc timeout → E-EXBOT-028 → `lifecycle_state='error'`), logic IOC hedge open (HL reject → E-EXBOT-026 → safe_mode), công thức stop_trigger_px (BigDecimal), thứ tự các bước trong 8 lifecycle_state khởi tạo.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-start | Khởi động ExBot | uc-bot-start.md updated 2026-07-20 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | QC Lead | 2026-07-09 | 2026-07-21 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| uc-bot-start.md | 2026-07-20 | UC | Đã đọc toàn bộ |
| srs/spec.md | 2026-07-20 | SRS (canonical) | FR-EXBOT-001 đến FR-EXBOT-093 |
| srs/states.md | 2026-07-08 | State diagram | 18 lifecycle_state; 4 key_status |
| srs/flows.md | 2026-07-07 | Flow diagram | F-03a, F-03b |
| srs/erd.md | 2026-07-08 | ERD | bots, positions, hedge_legs, hl_agent_keys |
| frd.md | 2026-07-21 | FRD | FR-EXBOT-001 (6 preflight checks synced) |
| us-001.md | 2026-07-08 | User Story | AC-1..4 |
| message-list.md | 2026-07-09 | Common messages | E-EXBOT-001..029 |
| qc-responses-2026-07-04.md | 2026-07-09 | BA answers | I-11 đến I-18 resolved |
| qc-responses-2026-07-20.md | 2026-07-20 | BA answers | OQ-EXBOT-011 resolved (threshold A11 = exact fill) |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này cho phép một nhà đầu tư USDC đã nạp tiền on-chain khởi động một ExBot quản lý vị thế LP delta-hedged tự động. Bot sẽ: (1) giữ LP NFT trong `BnzaExVault`, (2) duy trì một lệnh short ETH-USD perpetual trên Hyperliquid để triệt tiêu rủi ro định hướng ETH, (3) đặt lệnh stop reduce-only làm lưới an toàn. Mục tiêu: nhà đầu tư kiếm phí LP Uniswap V3 trong khi giảm thiểu thua lỗ do biến động giá ETH.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Preflight — 6 bước kiểm tra | one-bot policy, vault balance, HL margin, key_status='active', builder fee, LP sim | spec.md FR-EXBOT-001, FR-EXBOT-002; frd.md FR-EXBOT-001 |
| Tạo bản ghi bot | INSERT vào bot_registry + bots với lifecycle_state='preflight' | spec.md FR-EXBOT-003; erd.md |
| LP Mint on-chain | Gọi BnzaExVault.vaultMint() → nhận VaultMinted event → lưu positions | flows.md F-03b |
| Hedge open (IOC) | Signing Lambda ký và gửi IOC short order lên HL | spec.md FR-EXBOT-020, FR-EXBOT-021 |
| Post-order reconcile | Fetch clearinghouseState từ HL, verify size, lưu entry_price/liq_price/effective_leverage | spec.md FR-EXBOT-025 |
| Stop placement | Tính stop_trigger_px (BigDecimal, safetyFactor=0.70) → đặt reduce-only stop market | spec.md FR-EXBOT-030, FR-EXBOT-031 |
| Lifecycle state transitions | idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active | states.md; spec.md FR-EXBOT-003 |
| Exception paths | A1–A11 (one-bot fail, margin fail, no vault deposit, LP mint fail, builder fee, LP sim fail, HL unreachable, stop fail, key not provisioned, HL IOC reject, reconcile mismatch) | uc-bot-start.md §4 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| F-03a: Cấp phát khóa KMS on-deposit | Luồng riêng biệt, tự động khi nạp tiền; không phải bot-start | Test key-provision thuộc UC riêng |
| Hedge-sync định kỳ sau khi active | Thuộc UC-EXBOT-light-check + UC-EXBOT-hedge-sync | Không ảnh hưởng test bot-start |
| bot_safe_close khi bot đang closing | Thuộc UC-EXBOT-bot-safe-close | Không ảnh hưởng test bot-start |
| Trading strategy logic (PositionCalc, hedge math) | zen-proprietary; SOTATEK không build | Không test được |
| BnzaExVault contract internals | zen scope; SOTATEK chỉ tích hợp ABI | ABI chưa confirmed (OQ-EXBOT-08) |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Gọi POST /api/exbot/start qua POOL UI | Chỉ được tạo 1 ExBot active mỗi lúc (BR-EXBOT-001); phải có vault balance và HL margin đủ | spec.md BR-EXBOT-001; uc-bot-start.md §1 |
| ExBot Lambda | System | Chạy preflight, tạo bot, điều phối LP mint + hedge open + stop place | Standalone service; không co-deploy với OPERATOR (BR-EXBOT-010) | spec.md FR-EXBOT-090; frd.md §1 |
| BnzaExVault (Solidity) | System / External | Nhận lệnh vaultMint, giữ LP NFT, emit VaultMinted | ABI do zen cung cấp; SOTATEK chỉ tích hợp | frd.md IC-EXBOT-002 |
| Hyperliquid (API) | External | Nhận IOC short order, nhận stop order, cung cấp clearinghouseState | Budget 800 weight/min; HL có thể reject IOC (E-EXBOT-026) | spec.md FR-EXBOT-091 |
| Signing Lambda | System | Ký order payload bằng agent key qua AWS KMS | IAM role kms:Sign duy nhất; private key không rời KMS | spec.md FR-EXBOT-080; NFR-EXBOT-006 |
| AWS KMS | System | Lưu trữ master key + agent key; ký payload | Private key không bao giờ rời KMS HSM | spec.md FR-EXBOT-080 |

**Nhận xét readiness:** Actors đủ rõ cho test design. Lưu ý: Signing Lambda là IAM infrastructure component, không phải actor nghiệp vụ (I-01 đã resolved). Actor USDC Investor interact qua POOL UI nhưng ExBot là backend-only — test qua API call trực tiếp, không qua UI.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Người dùng đã hoàn tất nạp tiền on-chain; BnzaExVault balance > 0 | Yes | uc-bot-start.md §2; spec.md FR-EXBOT-002 check #2 |
| 2 | key-provision đã hoàn tất: `hl_agent_keys.key_status='active'` cho user này | Yes | spec.md FR-EXBOT-080; states.md Agent Key Status |
| 3 | Người dùng chưa có ExBot với `status IN ('active','paused','closing','safe_mode','error')` | Yes | spec.md BR-EXBOT-001; spec.md FR-EXBOT-001 |
| 4 | Người dùng có HL isolated margin balance ≥ required_margin × 2.0 | Yes | spec.md FR-EXBOT-061; FR-EXBOT-002 check #3 |
| 5 | Ví người dùng có đủ ETH/native token cho gas giao dịch vault | Yes (inferred) | uc-bot-start.md §2 |
| 6 | Builder fee (5bps) đã được xác nhận trên HL (kiểm tra runtime trong preflight, không phải pre-assumed) | No (runtime check) | uc-bot-start.md changelog 2026-07-09 P2 fix; spec.md FR-EXBOT-002 check #5 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Khởi tạo bot thành công | `bots.lifecycle_state='active'`, `bots.status='active'` | spec.md FR-EXBOT-003; uc-bot-start.md §5 |
| LP NFT | LP NFT được giữ bởi BnzaExVault: `positions.custodian='vault'` | uc-bot-start.md §5 |
| Hedge leg | HL short open với reduce-only stop đã đặt; `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` đã được ghi | spec.md FR-EXBOT-030, FR-EXBOT-031; uc-bot-start.md §5 |
| Aurora PostgreSQL state | `positions` có `tokenId`, `tickLower`, `tickUpper`, `weth_index`; `bot_runtime_state` có `last_known_hl_short_size` | spec.md FR-EXBOT-025; erd.md |
| Trạng thái hiển thị | Bot status visible trong POOL UI tại lần poll tiếp theo (Operator Facade GET /api/exbot/status) | uc-bot-start.md §3 step 11 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Preflight kiểm tra (6 bước)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Investor | POST /api/exbot/start qua POOL UI | ExBot Lambda nhận request; bắt đầu preflight | — | HMAC auth fail → 401 (không thuộc UC scope) | spec.md FR-EXBOT-090; flows.md F-03b |
| 2a | ExBot Lambda | Kiểm tra one-bot policy: SELECT FROM bot_registry WHERE user_id=? AND status IN ('active','paused','closing','safe_mode','error') | Count = 0 → tiếp tục | — | Count > 0 → từ chối với E-EXBOT-001; không tạo bot record | spec.md FR-EXBOT-001; BR-EXBOT-001 |
| 2b | ExBot Lambda | Kiểm tra vault balance > 0 cho user (BnzaExVault) | Balance > 0 → tiếp tục | — | Balance = 0 → từ chối với E-EXBOT-025 "No confirmed deposit found." | spec.md FR-EXBOT-002 check #2; E-EXBOT-025 |
| 2c | ExBot Lambda | Fetch HL marginSummary → kiểm tra margin balance ≥ required_margin × 2.0 | Margin đủ → tiếp tục | — | Margin thiếu → từ chối với E-EXBOT-002 "Required HL margin: $X..." | spec.md FR-EXBOT-061; FR-EXBOT-002 check #3; E-EXBOT-002 |
| 2d | ExBot Lambda | Kiểm tra hl_agent_keys.key_status='active' cho user | key_status='active' → tiếp tục | key_status='provisioning' → block | key_status không có hoặc không phải 'active' → E-EXBOT-017; không tạo bot record | spec.md FR-EXBOT-080; states.md Agent Key Status; E-EXBOT-017 |
| 2e | ExBot Lambda | Kiểm tra builder fee (5bps) xác nhận trên HL | Builder fee confirmed → tiếp tục | — | Chưa xác nhận → E-EXBOT-005; không tạo bot record | spec.md FR-EXBOT-002 check #5; E-EXBOT-005 |
| 2f | ExBot Lambda | Chạy LP mint simulation | Simulation pass → tiếp tục | — | Simulation fail → E-EXBOT-006; không tạo bot record | spec.md FR-EXBOT-002 check #6; E-EXBOT-006 |
| 3 | ExBot Lambda | Tạo bot record: INSERT bots (lifecycle_state='preflight', status='active') | Bot record created | — | DB error → fail request (không thuộc explicit UC scope) | spec.md FR-EXBOT-003 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| One-bot policy (BR-EXBOT-001) | COUNT(bots WHERE status IN active/paused/closing/safe_mode/error) = 0 | Yes | Preflight bước 2a pass | E-EXBOT-001 "You already have an active ExBot. Close or wait for the existing bot to finish." | spec.md BR-EXBOT-001; spec.md FR-EXBOT-001 |
| Vault balance (E-EXBOT-025) | BnzaExVault.balanceOf(user) > 0 | Yes | Preflight bước 2b pass | E-EXBOT-025 "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." | spec.md FR-EXBOT-002 check #2 |
| HL margin buffer (preflight_buffer = 2.0x) | margin_balance ≥ (lpEthAmount × hedgeRatio × hlOraclePrice / leverage) × 2.0 | Yes | Preflight bước 2c pass | E-EXBOT-002 "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | spec.md FR-EXBOT-061; FR-EXBOT-002 check #3 |
| Agent key status | hl_agent_keys.key_status = 'active' (không phải 'provisioning', 'superseded', 'revoked') | Yes | Preflight bước 2d pass | E-EXBOT-017 "Bot cannot start: agent key not yet provisioned." | spec.md FR-EXBOT-080; states.md |
| Builder fee confirmation | HL xác nhận builder fee 5bps | Yes | Preflight bước 2e pass | E-EXBOT-005 "HL builder fee (5bps) approval required before starting ExBot." | spec.md FR-EXBOT-002 check #5; E-EXBOT-005 |
| LP mint simulation | Simulation trong tolerance | Yes | Preflight bước 2f pass | E-EXBOT-006 "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | spec.md FR-EXBOT-002 check #6; E-EXBOT-006 |
| Thứ tự preflight | 6 bước chạy tuần tự: one-bot → vault → margin → key → fee → sim | Yes | Mỗi bước fail dừng ngay, không chạy bước tiếp | Không tạo partial bot record trên bất kỳ failure nào | spec.md FR-EXBOT-002; frd.md FR-EXBOT-001 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| One-bot policy vi phạm | API error response | "You already have an active ExBot. Close or wait for the existing bot to finish." | E-EXBOT-001 (HTTP 409) | message-list.md; spec.md §5 |
| Không có deposit | API error response | "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." | E-EXBOT-025 (HTTP 400) | message-list.md; spec.md §5 |
| HL margin không đủ | API error response | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | E-EXBOT-002 (HTTP 400) | message-list.md; spec.md §5 |
| Agent key chưa provisioned | API error response | "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." | E-EXBOT-017 (HTTP 400) | message-list.md; spec.md §5 |
| Builder fee chưa xác nhận | API error response | "HL builder fee (5bps) approval required before starting ExBot." | E-EXBOT-005 (HTTP 400) | message-list.md; spec.md §5 |
| LP mint simulation fail | API error response | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | E-EXBOT-006 (HTTP 400) | message-list.md; spec.md §5 |

---

### 6.2 Khởi tạo bot — LP Mint

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 4 | ExBot Lambda | Gọi BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps) | BnzaExVault emit VaultMinted(user, botId, tokenId, liquidity) | — | On-chain tx revert hoặc timeout → E-EXBOT-028; lifecycle_state='error'; không có tiền nào di chuyển (A4) | flows.md F-03b; spec.md E-EXBOT-028 |
| 5 | ExBot Lambda | Nhận VaultMinted event, cập nhật Aurora PostgreSQL | positions: tokenId, tickLower, tickUpper, weth_index; lifecycle_state='lp_opened' | — | DB write fail → giữ ở lp_opening (retry path) | uc-bot-start.md §3 step 5; erd.md positions |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| weth_index per chain | Giá trị 0 hoặc 1 (WETH là token0 hay token1); xác nhận per-chain và lưu vào positions.weth_index tại LP open | Yes | weth_index được lưu chính xác | LP amount tính sai nếu weth_index sai → hedge size sai | spec.md FR-EXBOT-004 |
| LP mint on-chain lifecycle | idle → lp_opening (trước khi gọi vault); lp_opened (sau VaultMinted confirmed) | Yes | Transition đúng thứ tự | LP mint fail → lifecycle_state='error' (A4); không phải safe_mode | states.md; spec.md E-EXBOT-028 |
| VaultMinted event | ExBot Lambda đọc tokenId từ VaultMinted event (không thể hardcode) | Yes | positions.token_id được lưu từ event | Token ID sai → reconcile fail | flows.md F-03b |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| LP mint on-chain revert hoặc timeout | API error + lifecycle_state change | "Bot startup failed: LP mint transaction did not complete. No funds were moved. Please try again or contact support." | E-EXBOT-028 (HTTP 502); lifecycle_state='error' | message-list.md; spec.md §5; states.md (lp_opening → error) |

---

### 6.3 Hedge Open và Reconcile

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 6 | ExBot Lambda → Signing Lambda → HL | ExBot tính targetShortEth = lpEthAmount × hedgeRatio (0.70); gọi Signing Lambda để ký IOC short order; Signing Lambda gọi kms:Sign; HL nhận lệnh | HL fills IOC order | — | HL unreachable → safe_mode; auto-recovery per FR-EXBOT-050 (A7). HL reject IOC → E-EXBOT-026 → safe_mode (A10). | spec.md FR-EXBOT-020, FR-EXBOT-021; E-EXBOT-026; states.md hedge_pre_open → safe_mode |
| 7 | ExBot Lambda | Fetch clearinghouseState từ HL; verify actual size = targetShortEth | Lưu entry_price, liquidation_price, effective_leverage vào hedge_legs; lifecycle_state='hedge_post_confirmed' | — | Actual size lệch (any partial fill, exact fill required — no tolerance per spec.md FR-EXBOT-025 updated 2026-07-20) → enqueue partial_repair; alert operator (A11). drift_threshold = max($25, lpValueUsd × 3%) where lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount (principal only, exclude tokensOwed) belongs to light-check rebalance trigger, not this reconcile step. | spec.md FR-EXBOT-025; uc-bot-start.md A11 (updated 2026-07-20) |
| 8 | ExBot Lambda | Cập nhật Aurora PostgreSQL: hedge_legs (entry_price, liq_price, effective_leverage), lifecycle_state='hedge_post_confirmed' | DB updated | — | — | uc-bot-start.md §3 step 8; erd.md hedge_legs |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Tính hedge size (BigDecimal) | targetShortEth = lpEthAmount × hedgeRatio; tất cả phép tính dùng BigDecimal (cấm float) | Yes | Hedge size chính xác | Float arithmetic → sai lệch tài chính | spec.md FR-EXBOT-021; NFR-EXBOT-008 |
| lpEthAmount calculation | Tính từ liquidity, tickLower, tickUpper, sqrtPriceX96, currentTick qua TickMath + LiquidityAmounts; cấm dùng depositedToken - withdrawnToken + collectedFees | Yes | LP amount chính xác | Hedge size sai → rủi ro delta | spec.md FR-EXBOT-020 |
| Cloid deterministic | cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}")); retry dùng cloid giống; payload đổi → tăng version | Yes | HL dedup đúng | Cloid không deterministic → double submission | spec.md FR-EXBOT-024 |
| Reconcile exact fill | rebalance_attempts.status='success' chỉ được ghi SAU KHI reconcile xác nhận actual size = target size (exact fill — no tolerance); any partial fill → reconcile_partial → partial_repair flow | Yes | Reconcile chính xác | Ghi success sai → bỏ sót mismatch | spec.md FR-EXBOT-025 (updated 2026-07-20) |
| Transition hedge_pre_open → safe_mode | Khi HL order fail (unreachable hoặc reject IOC) tại hedge open | Yes | safe_mode; auto-recovery per FR-EXBOT-050 | error state (không đúng per states.md) | states.md; BA confirmed I-11 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| HL unreachable tại hedge open (A7) | State transition + internal alert | lifecycle_state → safe_mode; auto-recovery theo FR-EXBOT-050 | E-EXBOT-008 "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | states.md hedge_pre_open → safe_mode; spec.md FR-EXBOT-050; BA confirmed I-11 |
| HL reject IOC order (A10) | State transition + internal alert | lifecycle_state → safe_mode; E-EXBOT-026 | E-EXBOT-026 "Hedge order rejected by Hyperliquid. Bot entered Safe Mode." — internal alert | message-list.md; spec.md §5 E-EXBOT-026; BA confirmed I-11/I-12 |
| Reconcile mismatch (A11) | Queue message + alert | partial_repair enqueued; alert operator | E-EXBOT-011 "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | message-list.md; uc-bot-start.md A11 (updated 2026-07-20); spec.md FR-EXBOT-025 |

---

### 6.4 Stop Placement

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống — happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 9a | ExBot Lambda | Tính stop_trigger_px (BigDecimal): liq_distance_pct = (liquidation_price − entry_price) / entry_price; stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70) | stop_trigger_px computed | Fallback: dùng 1/effective_leverage nếu liquidation_price không có | — | spec.md FR-EXBOT-030 |
| 9b | ExBot Lambda → Signing Lambda → HL | Gọi Signing Lambda ký reduce-only stop market order với stop_trigger_px; HL nhận lệnh | Stop placed; HL xác nhận stop_order_id | — | Stop placement fail → safe_mode (A8); lifecycle_state='stop_placing' → 'safe_mode' | spec.md FR-EXBOT-031; states.md stop_placing → safe_mode |
| 10 | ExBot Lambda | Xác nhận stop đã đặt; cập nhật Aurora PostgreSQL: hedge_legs (stop_cloid, stop_order_id, stop_price, stop_size, stop_distance_pct); lifecycle_state='stop_verified' → 'active' | lifecycle_state='active'; bot fully initialized | — | — | spec.md FR-EXBOT-031; uc-bot-start.md §3 step 10 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Stop price (BigDecimal) | Tất cả tính toán stop_trigger_px dùng BigDecimal (cấm Number() conversion) | Yes | Stop price chính xác | Float → sai stop price → rủi ro liquidation | spec.md FR-EXBOT-030; NFR-EXBOT-008 |
| stopSafetyFactor Phase A = 0.70 | stop_distance_pct = liq_distance_pct × 0.70; stop fires trước liquidation price với buffer ≥ 30% | Yes | Stop bảo vệ đúng | safetyFactor sai → stop quá gần liquidation | spec.md FR-EXBOT-030 |
| Bot không được chuyển sang active khi chưa có stop | lifecycle_state='stop_verified' chỉ khi stop đã confirmed; 'active' chỉ sau 'stop_verified' | Yes | Bot có stop đã đặt khi active | Bot active không có stop → rủi ro không giới hạn | spec.md FR-EXBOT-031 |
| stop_placing → safe_mode (không phải error) | Khi stop placement fail | Yes | safe_mode với auto-recovery path | Chuyển sang error state (không đúng per states.md) | states.md; spec.md FR-EXBOT-033 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Stop placement fail (A8) | State transition + internal alert | lifecycle_state='stop_placing' → 'safe_mode'; alert operator | E-EXBOT-009 "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." (HTTP 502) | message-list.md; states.md stop_placing → safe_mode |
| Bot started thành công | API success response + state | lifecycle_state='active', status='active'; POOL UI hiển thị bot "Active" | (Success — không có E-code riêng; POOL UI dùng MSG-SUC-01 "Bot started successfully!") | us-001.md AC-1; message-list.md MSG-POOL |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Bot chuyển sang lifecycle_state='active' | UC-EXBOT-light-check | Scan Worker bắt đầu enqueue light-check messages sau khi bot active; next_light_check_at được tính khi first light-check cycle | Nếu lifecycle_state không đúng 'active' → bot không được scan | spec.md FR-EXBOT-012; FR-EXBOT-013 |
| positions.weth_index được lưu tại LP open | UC-EXBOT-light-check; UC-EXBOT-hedge-sync | lpEthAmount tính từ weth_index → hedge size; sai weth_index → hedge sai từ đầu | weth_index phải được verify per-chain; không hardcode | spec.md FR-EXBOT-004; FR-EXBOT-020 |
| hedge_legs.stop_price được lưu sau stop placement | UC-EXBOT-light-check (stop trigger detection) | Light-check dùng stop_price để phát hiện markPrice >= stop_price → enqueue price-near-stop-audit | Nếu stop_price = NULL → stop trigger detection không hoạt động | spec.md FR-EXBOT-031; FR-EXBOT-032 |
| bot_runtime_state.last_known_hl_short_size được khởi tạo | UC-EXBOT-light-check; UC-EXBOT-hedge-sync | Light-check đọc giá trị này thay vì gọi HL API; hedge-sync dùng để tính delta | Phải được ghi sau reconcile tại bot-start; nếu thiếu → light-check delta calculation sai | spec.md FR-EXBOT-025; FR-EXBOT-012 |
| F-03a key-provision phải hoàn tất trước bot-start | UC-EXBOT-bot-start (precondition) | Preflight check #4 fail nếu key_status != 'active' → bot không thể start | hl_agent_keys.key_status='active' là dependency bắt buộc | spec.md FR-EXBOT-080; flows.md F-03a |
| LP mint on-chain (BnzaExVault.vaultMint) | BnzaExVault Solidity (zen scope) | VaultMinted event là on-chain source of truth cho tokenId; ExBot Lambda lưu off-chain sau event | Nếu event listener miss event → positions không có tokenId → hedge-sync fail sau | flows.md F-03b; spec.md IC-EXBOT-002 |
| safe_mode entry (A7, A8, A10) | UC-EXBOT-bot-safe-close (nếu irrecoverable) | Bot vào safe_mode → auto-recovery thử FR-EXBOT-050; nếu irrecoverable → bot_safe_close | Safe_mode không bao giờ là terminal state (BR-EXBOT-007); phải có recovery path hoặc close | spec.md FR-EXBOT-050; BR-EXBOT-007 |
| error state (A4 — LP mint fail) | Admin intervention required (E-EXBOT-029) | lifecycle_state='error'; không có tiền di chuyển; admin cần can thiệp | Verify: positions không có tokenId khi error; không có hedge_legs record; không có close_operations record | spec.md E-EXBOT-028; E-EXBOT-029; states.md lp_opening → error |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given — điều kiện | When — hành động | Then — kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — preflight pass, bot active | Investor có vault balance > 0; key_status='active'; HL margin ≥ required × 2.0; builder fee confirmed; LP sim pass; không có bot active | POST /api/exbot/start | lifecycle_state='active'; bots.status='active'; hedge_legs.stop_price populated; positions.weth_index populated; last_known_hl_short_size populated | us-001.md AC-1; spec.md FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-025, FR-EXBOT-031 |
| AC-02 | One-bot policy — từ chối start khi đã có bot active | Investor có ExBot với status='active' | POST /api/exbot/start | HTTP 409; message "You already have an active ExBot. Close or wait for the existing bot to finish."; không tạo bot record mới | us-001.md AC-2; E-EXBOT-001 |
| AC-03 | One-bot policy — từ chối start khi bot ở trạng thái safe_mode | Investor có ExBot với status='safe_mode' | POST /api/exbot/start | HTTP 409; E-EXBOT-001 same message; không tạo bot record mới | spec.md FR-EXBOT-001 (status IN ... safe_mode) |
| AC-04 | Vault balance = 0 — block | Investor chưa deposit on-chain | POST /api/exbot/start | HTTP 400; E-EXBOT-025 "No confirmed deposit found." | us-001.md AC-4; E-EXBOT-025 |
| AC-05 | HL margin thiếu — block | HL margin balance < required × 2.0 | POST /api/exbot/start | HTTP 400; E-EXBOT-002 với giá trị $X, $Y, $Z chính xác | us-001.md AC-3; E-EXBOT-002 |
| AC-06 | key_status='provisioning' — block | hl_agent_keys.key_status='provisioning' | POST /api/exbot/start | HTTP 400; E-EXBOT-017 "Bot cannot start: agent key not yet provisioned." | spec.md FR-EXBOT-080; states.md |
| AC-07 | Builder fee chưa xác nhận — block | HL builder fee chưa confirmed | POST /api/exbot/start | HTTP 400; E-EXBOT-005 | E-EXBOT-005 |
| AC-08 | LP mint simulation fail — block | Pool liquidity không đủ hoặc slippage quá lớn | POST /api/exbot/start | HTTP 400; E-EXBOT-006 | E-EXBOT-006 |
| AC-09 | LP mint on-chain revert/timeout | Preflight pass; vaultMint tx revert hoặc timeout | POST /api/exbot/start | HTTP 502; E-EXBOT-028; lifecycle_state='error'; không có tiền di chuyển | E-EXBOT-028; states.md lp_opening → error |
| AC-10 | HL unreachable tại hedge open (A7) | Preflight pass; LP mint success; HL API unreachable | ExBot Lambda cố gọi HL short IOC | lifecycle_state='hedge_pre_open' → 'safe_mode'; auto-recovery per FR-EXBOT-050 được enqueue | states.md; spec.md FR-EXBOT-050; BA confirmed I-11 |
| AC-11 | HL reject IOC (A10) | Preflight pass; LP mint success; HL reject IOC order | ExBot Lambda gửi IOC qua Signing Lambda | lifecycle_state → safe_mode; E-EXBOT-026 logged; auto-recovery per FR-EXBOT-050 | states.md; E-EXBOT-026; BA confirmed I-12 |
| AC-12 | Stop placement fail (A8) | Preflight + hedge open + reconcile pass; stop placement fail | ExBot Lambda đặt stop | lifecycle_state='stop_placing' → 'safe_mode'; E-EXBOT-009 logged; auto-recovery per FR-EXBOT-050 | states.md stop_placing → safe_mode |
| AC-13 | Thứ tự preflight đúng | Investor thiếu vault balance VÀ thiếu key_status (cả 2 fail) | POST /api/exbot/start | Chỉ trả về lỗi vault balance (E-EXBOT-025) — dừng tại bước 2b, không chạy tiếp bước 2d | spec.md FR-EXBOT-002 (tuần tự) |
| AC-14 | Không tạo partial bot record khi preflight fail | Bất kỳ preflight bước nào fail | POST /api/exbot/start | Aurora PostgreSQL: không có bản ghi bots/positions/hedge_legs được tạo | spec.md FR-EXBOT-002 "no partial bot record is left" |
| AC-15 | stop_price populated sau bot active | Happy path | POST /api/exbot/start | hedge_legs.stop_price != NULL; stop_price tính bằng BigDecimal với safetyFactor=0.70 | spec.md FR-EXBOT-030, FR-EXBOT-031 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Precision | Tất cả tính toán hedge, stop, margin dùng BigDecimal; cấm float/number arithmetic | Test: verify stop_price và hedge_size không dùng JS Number; không có sai lệch tài chính | spec.md NFR-EXBOT-008 |
| Security | Master key + agent key trong AWS KMS; private key không bao giờ rời KMS; chỉ Signing Lambda có IAM kms:Sign | Test: log audit không có raw key; DB hl_agent_keys không có plaintext private key | spec.md NFR-EXBOT-006 |
| Idempotency | queue_idempotency.message_id UNIQUE; cloid deterministic | Test: gửi same message 2 lần → chỉ 1 execution; same retry → same cloid | spec.md NFR-EXBOT-007 |
| Rate limit | HL API weight ≤ 800/min; preflight margin check tiêu thụ weight ngay cả khi fail ở bước sau | Test: nhiều start request liên tiếp có thể tiêu thụ HL weight | spec.md NFR-EXBOT-004; FR-EXBOT-091 |
| Multi-chain | Base + Optimism supported; weth_index verify per chain tại LP open | Test: bot trên Base và Optimism có weth_index đúng; không hardcode | spec.md NFR-EXBOT-009 |
| Architecture | ExBot Lambda không co-deploy với OPERATOR; giao tiếp qua API Gateway + HMAC | Test: gọi trực tiếp ExBot Lambda bị 403 | spec.md NFR-EXBOT-006; BR-EXBOT-010 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận (Issue Register)

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| V5-01 | High | UNCLEAR_INFO | uc-bot-start.md A11; spec.md FR-EXBOT-025; OQ-EXBOT-011 | Threshold reconcile mismatch tại A11 được UC ghi là "actual size deviates > threshold" với ghi chú threshold = `drift_threshold = lp_value_usd × 3%` nhưng OQ-EXBOT-011 vẫn Open — zen chưa xác nhận formula tính `lpValueUsd`. Tester không thể thiết kế boundary test cho A11 cho đến khi OQ-EXBOT-011 Closed. | Blocker cho test reconcile mismatch (AC-test của A11 không đủ cụ thể) | zen / BA | Resolved (2026-07-20). Resolution: Threshold = exact fill. No percentage tolerance. Any partial fill results in reconcile_partial status → partial_repair flow. drift_threshold = max($25, lpValueUsd × 3%) where lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount (principal only, exclude tokensOwed, price = Uniswap pool slot0) belongs to light-check rebalance trigger only, not this reconcile step. OQ-EXBOT-011 Closed (zen confirmed). Source: qc-responses-2026-07-20.md |
| V5-02 | Medium | UNCLEAR_INFO | flows.md F-03a vs spec.md FR-EXBOT-080 | F-03a (flows.md) mô tả Key-Provision Worker INSERT `hl_agent_keys` row với `key_status='active'` SAU KHI HL `approveAgent` confirms (bỏ qua bước `provisioning`). Trong khi đó spec.md FR-EXBOT-080 step 4 ghi rõ: row được tạo với `key_status='provisioning'` SAU KHI KMS generate keys thành công — VÀ HL approveAgent CHƯA được gọi. F-03a không reflect đúng trình tự: thiếu bước INSERT với key_status='provisioning' trước HL approveAgent. Đây là bất nhất nội bộ giữa flows.md và spec.md. | Tester đọc flows.md sẽ không test được path key_status='provisioning' tại bot-start preflight (E-EXBOT-017 khi key đang provisioning) | BA | Open — Minor (spec.md là canonical; flows.md cần update) |
| V5-03 | Low | MISSING_INFO | uc-bot-start.md A7; spec.md FR-EXBOT-050; E-EXBOT-008 | UC A7 mô tả "HL unreachable tại bước hedge → enter safe_mode". Nhưng UC A7 áp dụng cho "Step 4 or 6" — step 4 là LP mint (BnzaExVault), không phải HL call. Nếu HL unreachable ở step 4, điều này không logic. Câu hỏi: A7 chỉ áp dụng cho step 6 (hedge open), hay cũng áp dụng cho một scenario khác ở step 4? | Tester có thể nhầm thiết kế test "HL unreachable at step 4" trong khi step 4 không gọi HL | BA | Open |
| V5-04 | Low | MISSING_INFO | spec.md FR-EXBOT-002; B5 checklist | Preflight check #5 (builder fee) và check #6 (LP mint simulation) không có HL API call weight rõ ràng. Builder fee check gọi HL endpoint nào? Weight bao nhiêu? OQ-EXBOT-05 (NV-14) vẫn Open. Ảnh hưởng test design: không thể verify rate limit consumption cho preflight đầy đủ. | Test rate limit cho preflight flow bị block cho đến khi OQ-EXBOT-05 Closed | BA / Tech Lead (OQ-EXBOT-05) | Deferred (OQ-EXBOT-05) |
| V5-05 | Low | MISSING_INFO | uc-bot-start.md §5 Postconditions | Postconditions không đề cập đến `bot_runtime_state.last_known_hl_short_size` được khởi tạo sau reconcile. Đây là field quan trọng cho light-check và hedge-sync sau này đọc. Nếu field này = NULL sau bot-start, light-check sẽ tính delta sai. | Test design cần verify field này populated sau bot-start | BA | Open — Note |
| V5-06 | Note | MISSING_INFO | B3 blockchain checklist | UC không đề cập chainId, testnet vs mainnet behavior, wrong-chain behavior cho vault tx. ExBot hỗ trợ Base + Optimism (FR-EXBOT-004) nhưng UC không mô tả expected behavior khi user wallet trên wrong chain. | Không block test design cho happy path; test multi-chain behavior cần clarify | BA | Open — Note |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-08 — BnzaExVault final ABI | Integration | Blocker cho test LP mint (A4, A5 actual on-chain behavior); vault call stubbed cho đến khi ABI confirmed | zen | Open |
| OQ-EXBOT-05 — Builder fee check endpoint | Spec | Block chi tiết test preflight step 5 (rate limit weight, HL endpoint) | Tech Lead / zen | Open |
| OQ-EXBOT-03 — Pool addresses + wethIndex per chain | Spec | Block test weth_index per chain tại LP open | zen / SOTATEK | Open |
| flows.md F-03a update (V5-02) | Documentation | flows.md cần thêm bước INSERT key_status='provisioning' để consistent với spec.md FR-EXBOT-080 | BA | Open — Minor |

---

## 11. Scoring — Đánh giá mức độ sẵn sàng

### Issue Register Summary

| Issue ID | Type | Severity | Scoring Area | Finding |
|---|---|---|---|---|
| V5-01 | UNCLEAR_INFO | Major → Resolved | Area 3 (logic), Area 5 (doc quality) | Threshold A11 confirmed exact fill (OQ-EXBOT-011 Closed 2026-07-20) — boundary test A11 now unblocked |
| V5-02 | INTERNAL_INCONSISTENCY | Minor | Area 4 (integration), Area 5 | flows.md F-03a không reflect provisioning step — bất nhất với spec.md FR-EXBOT-080 |
| V5-03 | UNCLEAR_INFO | Minor | Area 3 | UC A7 reference "Step 4 or 6" — step 4 là vault call (không phải HL call); có thể gây nhầm lẫn |
| V5-04 | MISSING_INFO | Minor | Area 1 (inventory) | Builder fee HL endpoint và weight không rõ (OQ-EXBOT-05 deferred) |
| V5-05 | MISSING_INFO | Note | Area 2 (data attributes) | Postconditions thiếu last_known_hl_short_size |
| V5-06 | MISSING_INFO | Note | B3 checklist | Chain ID / wrong-chain behavior không được mô tả |

### Scoring Table

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 18 | ✅ Clear | 6 bước preflight, 8 lifecycle states, full error code inventory đầy đủ. Trừ 2: builder fee weight (OQ-EXBOT-05) chưa có trong inventory |
| 2 | Data Object / State Attributes, BR, Validations & Messages | 25 | 22 | ✅ Clear | key_status 4 states, stop formula, BigDecimal constraint, all E-codes resolved. Trừ 3: last_known_hl_short_size thiếu trong postconditions (V5-05); provisioning path F-03a không đồng bộ (V5-02) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 25 | ✅ Clear | Happy path + 11 alternate flows rõ. threshold A11 confirmed exact fill; OQ-EXBOT-011 Closed — boundary test A11 fully designable |
| 4 | Functional Integration & Data Consistency | 15 | 13 | ✅ Clear | On-chain ↔ off-chain event flow (VaultMinted), key-provision dependency, light-check downstream. Trừ 2: flows.md F-03a bất nhất (V5-02) |
| 5 | UC / Spec Documentation Quality | 15 | 14 | ✅ Clear | UC v6 nhất quán tốt sau khi BA resolved I-11..I-18 và OQ-EXBOT-011. V5-01 resolved; V5-02 minor inconsistency flows.md still open |

**Tổng điểm: 92 / 100**

**Verdict: ✅ Ready** — All major test paths unblocked. Boundary test A11 now fully designable (exact fill = 0 tolerance). Only outstanding issues are minor/notes.

### §10.3 Audit Summary

**Điểm mạnh:** So với v5, UC v6 đã resolve issue V5-01 (OQ-EXBOT-011 Closed): threshold reconcile mismatch tại A11 đã được zen xác nhận là exact fill — không có percentage tolerance. Boundary test cho A11 hiện đã có thể thiết kế hoàn chỉnh. drift_threshold = max($25, lpValueUsd × 3%) đã được làm rõ là thuộc light-check rebalance trigger, không liên quan đến reconcile step. Score tăng từ 85 lên 92/100.

**Điểm cần theo dõi:** (1) flows.md F-03a vẫn chưa được cập nhật để reflect provisioning step (V5-02, minor — spec.md là canonical). (2) UC A7 reference "Step 4 or 6" cần làm rõ — step 4 là vault call (V5-03). (3) OQ-EXBOT-05 (builder fee endpoint) và OQ-EXBOT-08 (vault ABI) vẫn open nhưng không block test design cho happy path và phần lớn exception paths.

**Khuyến nghị:** Tiến hành thiết kế test case đầy đủ bao gồm cả boundary test A11 (exact fill = any partial fill triggers reconcile_partial → partial_repair). Confirm với BA về V5-02 (flows.md update) và V5-03 (A7 step reference). Defer test chi tiết rate limit preflight step 5 cho đến khi OQ-EXBOT-05 Closed.

---

## 12. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v5 | 2026-07-09 | QC UC Read Agent | Re-audit với câu trả lời BA mới nhất (I-11 đến I-18 resolved); cập nhật theo spec.md 2026-07-09, uc-bot-start.md 2026-07-09; score 85/100 Conditionally Ready |
| v6 | 2026-07-21 | QC UC Read Agent | Re-audit với BA answer qc-responses-2026-07-20.md: V5-01 resolved (threshold A11 = exact fill, OQ-EXBOT-011 Closed); score 85→92/100; verdict Conditionally Ready→Ready |
