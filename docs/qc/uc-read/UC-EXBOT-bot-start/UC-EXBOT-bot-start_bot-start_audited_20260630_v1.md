# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tên tài liệu:** UC-EXBOT-bot-start — Audited Readiness Report  
**Ngày tạo:** 2026-06-30  
**Tác giả:** QC UC Read ExBot Agent  
**Phiên bản:** v1

---

## Bảng mã viết tắt

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC | Use Case — mô tả luồng nghiệp vụ cấp cao | `usecases/` |
| US | User Story — mô tả nhu cầu từ góc nhìn người dùng/hệ thống | `userstories/` |
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng của module ExBot | `srs/spec.md`, `frd.md` |
| BR-EXBOT-* | Business Rule — quy tắc nghiệp vụ cố định của module ExBot | `srs/spec.md §4` |
| E-EXBOT-* | Error Code — mã lỗi API-layer trả về từ ExBot Worker qua Operator Facade | `srs/spec.md §5`, `message-list.md` |
| SRS | Software Requirements Specification — tài liệu kỹ thuật chi tiết, nguồn sự thật chính của ExBot | `srs/spec.md`, `srs/states.md`, `srs/flows.md`, `srs/erd.md` |
| FRD | Functional Requirements Document — mô tả yêu cầu chức năng cấp module | `frd.md` |
| KMS | AWS Key Management Service — dịch vụ lưu khóa bí mật; private key KHÔNG bao giờ rời KMS | `srs/spec.md §FR-EXBOT-080` |
| HL | Hyperliquid — sàn giao dịch perp phi tập trung; ExBot mở vị thế short ETH-USD tại đây | (external platform) |
| IOC | Immediate-Or-Cancel — loại lệnh giao dịch: khớp ngay hoặc hủy, không để pending | (industry term) |
| LP | Liquidity Provider — vị thế thanh khoản Uniswap V3; ExBot quản lý LP NFT trong BnzaExVault | (industry term) |
| NFT | Non-Fungible Token — token định danh duy nhất đại diện cho LP position, giữ bởi BnzaExVault | (industry term) |
| D1 | Cloudflare D1 — cơ sở dữ liệu SQLite phân tán của Cloudflare; lưu trạng thái bot, hedge, position | (industry term) |
| DO | Durable Object — Cloudflare primitive cung cấp trạng thái nhất quán; dùng cho UserLockDO, HLRateLimitDO, MarketDataDO | (industry term) |
| cloid | Client Order ID — ID lệnh xác định từ phía client, dùng để dedup lệnh HL | `srs/spec.md §FR-EXBOT-024` |
| SAFE_MODE | Trạng thái an toàn — mọi thao tác mutation bị chặn; chỉ cho phép đọc và cảnh báo | `srs/states.md`, `srs/spec.md §FR-EXBOT-050` |
| BigDecimal | Kiểu số thập phân độ chính xác tùy ý — bắt buộc dùng cho mọi tính toán tài chính, cấm dùng JS float | `srs/spec.md §NFR-EXBOT-008` |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả quá trình **khởi động tự động ExBot** sau khi hệ thống phát hiện giao dịch nạp tiền on-chain của người dùng. Đây là luồng hoàn toàn do hệ thống kích hoạt — người dùng không cần thực hiện thao tác nào ngoài việc nạp USDC vào hợp đồng BnzaExVault trên chain.

Luồng bắt đầu khi Chain Indexer (Fargate) phát hiện sự kiện nạp tiền on-chain và đưa vào hàng đợi `key-provision`. Key-Provision Worker tạo cặp khóa master key + agent key trong AWS KMS (private key không bao giờ rời KMS), đăng ký agent key với Hyperliquid qua `approveAgent`, rồi đưa lệnh khởi động bot vào hàng đợi `bot-start`. ExBot Worker nhận lệnh, chạy kiểm tra tiền đề (preflight), mint LP NFT thông qua hợp đồng BnzaExVault, mở vị thế short ETH IOC trên Hyperliquid qua Signing Lambda, đặt stop market reduce-only, và chuyển bot sang trạng thái `active`.

Luồng này ảnh hưởng trực tiếp đến thiết kế test vì: (1) toàn bộ là logic backend không có UI — tester quan sát qua API status và trạng thái D1; (2) có 5 bước preflight phải vượt qua theo thứ tự cố định; (3) có 9 trạng thái `lifecycle_state` liên tiếp không được bỏ qua; (4) tích hợp với 3 hệ thống ngoài (AWS KMS, Hyperliquid, BnzaExVault Solidity contract) mỗi hệ thống có đường lỗi riêng; (5) security critical — private key không được lưu ngoài KMS, không xuất hiện trong log hoặc database.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-start | Start ExBot — tự động khởi động sau deposit + key provisioning | 2026-06-29 (changelog) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-06-29 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-bot-start.md` | 2026-06-29 | UC | Tài liệu chính được review |
| `userstories/us-001.md` | 2026-06-29 | US | Linked story duy nhất |
| `srs/spec.md` | 2026-06-29 | SRS (nguồn sự thật) | Canonical source, SPEC v5.2.6 |
| `srs/states.md` | 2026-06-29 | State diagram | Lifecycle state machine |
| `srs/flows.md` | 2026-06-29 | Flow diagram | F-03: Bot Initialization Flow |
| `srs/erd.md` | 2026-06-29 | ERD | D1 schema |
| `frd.md` | 2026-06-29 | FRD | FR-EXBOT-001–004, 020, 030–031 |
| `02_backbone/message-list.md` | 2026-06-26 | Common messages | E-EXBOT-001..017 |
| `02_backbone/common-rules.md` | 2026-06-26 | Common rules | BR-EXBOT-001..014 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-bot-start tồn tại để tự động hóa toàn bộ quá trình khởi động một bot delta-hedge LP cho nhà đầu tư USDC, từ thời điểm hệ thống phát hiện giao dịch nạp tiền on-chain cho đến khi bot ở trạng thái `active` với LP position, vị thế short, và stop order đều đã được xác nhận. Mục tiêu nghiệp vụ: đảm bảo LP của nhà đầu tư được bảo vệ bởi hedge ngay khi nạp tiền, không cần thao tác thủ công.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Key-Provision | Chain Indexer phát hiện deposit → KMS tạo master key + agent key → HL `approveAgent` → `key_status='active'` → enqueue bot-start | SRS F-03, FR-EXBOT-080 |
| Preflight checks (5 bước) | One-bot check → margin check → key_status check → builder fee check → LP mint simulation | UC §3 step 3, FR-EXBOT-002 |
| Tạo bot record | `lifecycle_state='preflight'` ghi vào D1 sau khi preflight qua | UC §3 step 4, FR-EXBOT-003 |
| LP Mint | `BnzaExVault.vaultMint(...)` → nhận sự kiện `VaultMinted` → cập nhật `positions` với `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'` | UC §3 step 5–6, FR-EXBOT-004 |
| Mở vị thế hedge | ExBot Worker gửi lệnh short IOC qua Signing Lambda → KMS ký bằng agent key → HL nhận lệnh đã ký | UC §3 step 7, FR-EXBOT-020 |
| Reconcile sau hedge | Lấy actual position từ HL, trích xuất `entry_price`, `liquidation_price`, `effective_leverage`, cập nhật `hedge_legs` | UC §3 step 8–9, FR-EXBOT-025 |
| Đặt stop order | Tính `stop_trigger_px` bằng BigDecimal (safetyFactor=0.70) → đặt reduce-only stop market qua Signing Lambda → xác nhận → `lifecycle_state='stop_verified'→'active'` | UC §3 step 10–11, FR-EXBOT-030, FR-EXBOT-031 |
| Alternate flows | A1–A11 bao gồm: one-bot policy fail, margin fail, LP mint fail, builder fee fail, simulation fail, HL unreachable, stop fail, HL rejection, reconcile mismatch | UC §4 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Trading strategy logic (hedge ratio, stop safety factor formula) | Zen-proprietary, SOTATEK chỉ tích hợp — FR-EXBOT-030 ghi Phase A `stopSafetyFactor=0.70` là hằng số | Tester chỉ verify giá trị được dùng đúng, không verify logic tính toán |
| BnzaExVault Solidity contract nội bộ | Zen phát triển; SOTATEK tích hợp qua ABI (IC-EXBOT-002 — OQ-EXBOT-08 vẫn mở) | ABI chưa finalize → stub; test integration cần ABI confirm trước |
| UI screens cho ExBot | Thuộc module bnza-pool (PTL-05), ngoài phạm vi ExBot backend | Tester quan sát kết quả qua status API, không qua UI |
| Key rotation / revocation sau khi bot active | Thuộc UC khác (nếu có); UC này chỉ cover provisioning lần đầu | Không ảnh hưởng test UC này |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| System — Chain Indexer (Fargate) | System | Phát hiện sự kiện nạp tiền on-chain, enqueue job `key-provision` | Chỉ đọc on-chain events; không thực hiện thao tác tài chính | SRS F-03, FRD §2 ACT-O |
| System — Key-Provision Worker | System | Tạo cặp khóa KMS, đăng ký agent key với HL, enqueue bot-start | Chỉ gọi KMS GenerateKeyPair và HL approveAgent; không ký lệnh giao dịch | SRS F-03, FR-EXBOT-080 |
| System — ExBot Worker | System | Chạy preflight, tạo bot record, orchestrate LP mint + hedge open + stop placement | Không trực tiếp accessible từ internet; giao tiếp qua CF service binding | SRS F-03, BR-EXBOT-010 |
| System — BnzaExVault (Solidity) | External | Nhận lệnh `vaultMint`, mint LP NFT, giữ custody LP | Hợp đồng on-chain do zen phát triển; SOTATEK tích hợp qua ABI | UC §1, IC-EXBOT-002 |
| System — Hyperliquid | External | Nhận lệnh short IOC đã ký, xác nhận vị thế, nhận lệnh stop market | Sàn giao dịch ngoài; rate limit 800 weight/min (FR-EXBOT-091) | UC §1, FR-EXBOT-091 |
| System — AWS KMS | External | Tạo và lưu giữ private key; ký lệnh theo yêu cầu Signing Lambda | Private key không bao giờ rời KMS; chỉ Signing Lambda IAM có quyền `kms:Sign` | FR-EXBOT-080, NFR-EXBOT-006 |
| System — Signing Lambda | System | Nhận yêu cầu ký từ ExBot Worker, gọi KMS, gửi lệnh đã ký lên HL | Là thực thể duy nhất có IAM permission `kms:Sign` | SRS F-03, FR-EXBOT-080 |
| USDC Investor | Primary (gián tiếp) | Thực hiện giao dịch nạp tiền on-chain — trigger toàn bộ luồng | Không có thao tác trực tiếp trong UC này sau khi đã nạp tiền | UC §1, FRD ACT-I |

**Nhận xét readiness:** Actor đã đủ rõ để thiết kế test theo role. Lưu ý: UC không nêu rõ Signing Lambda như một actor riêng trong phần §1 Actors — chỉ liệt kê trong phần trigger và step 7/10 — nhưng SRS F-03 flow diagram đã hiện thị đầy đủ. Không gây nhầm lẫn nhưng nên bổ sung vào UC §1 để nhất quán. (Issue I-01)

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Người dùng không có ExBot nào với `status IN ('active','paused','closing','safe_mode','error')` | Yes | UC §2, BR-EXBOT-001: "Phase A: 1 user = 1 active ExBot. `status IN ('active','paused','closing','safe_mode','error')` all count toward the limit." |
| 2 | Người dùng có tài khoản HL với isolated margin balance ≥ required × 2.0 | Yes | UC §2, FR-EXBOT-061 |
| 3 | `hl_agent_keys.key_status='active'` cho người dùng này (được key-provision worker tạo sau khi deposit) | Yes | UC §2, FR-EXBOT-080, FR-EXBOT-002 bước 3 |
| 4 | Builder fee (5bps) đã được xác nhận trên HL | Yes | UC §2, FR-EXBOT-002 bước 4 |
| 5 | ERC-20 allowance: người dùng đã approve BnzaExVault chi USDC ≥ deposit amount | Yes | UC §2 |
| 6 | Người dùng có đủ ETH/native token để trả gas cho vault tx | Yes | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Bot khởi động thành công | `bots.lifecycle_state='active'`, `bots.status='active'` | UC §5, FR-EXBOT-003 |
| LP NFT | LP NFT đang được giữ bởi BnzaExVault (`positions.custodian='vault'`) | UC §5 |
| Hedge | Vị thế short HL đang mở với reduce-only stop đã đặt | UC §5 |
| Dữ liệu hedge | `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` đã được ghi vào D1 | UC §5, FR-EXBOT-031 |

---

---

## §F.1 Inventory — Hàm/Operation, Data Object, State, Event, Message

### F.1.1 Operations / Triggers

| # | Operation | Trigger | Actor | Nguồn |
|---|---|---|---|---|
| OP-01 | Chain Indexer phát hiện on-chain deposit | On-chain event (deposit confirmed) | Chain Indexer (Fargate) | SRS F-03 |
| OP-02 | Enqueue `key-provision` job | Sau OP-01 | Chain Indexer | SRS F-03 |
| OP-03 | KMS GenerateKeyPair — master key | Queue message `key-provision` | Key-Provision Worker | SRS F-03, FR-EXBOT-080 |
| OP-04 | KMS GenerateKeyPair — agent key | Sau OP-03 | Key-Provision Worker | SRS F-03, FR-EXBOT-080 |
| OP-05 | HL `approveAgent(hl_user_address, agent_address)` | Sau OP-04 | Key-Provision Worker | SRS F-03, FR-EXBOT-080 |
| OP-06 | INSERT `hl_agent_keys` với `key_status='active'` | Sau HL confirm agent registration | Key-Provision Worker | SRS F-03, FR-EXBOT-080 |
| OP-07 | Enqueue `bot-start` job | Sau OP-06 | Key-Provision Worker | SRS F-03 |
| OP-08 | Preflight — one-bot policy check | Queue message `bot-start` | ExBot Worker | UC §3 step 3, FR-EXBOT-001 |
| OP-09 | Preflight — HL margin sufficiency check | Sau OP-08 pass | ExBot Worker | UC §3 step 3, FR-EXBOT-002, FR-EXBOT-061 |
| OP-10 | Preflight — `hl_agent_keys.key_status='active'` check | Sau OP-09 pass | ExBot Worker | UC §3 step 3, FR-EXBOT-002 |
| OP-11 | Preflight — builder fee check | Sau OP-10 pass | ExBot Worker | UC §3 step 3, FR-EXBOT-002 |
| OP-12 | Preflight — LP mint simulation | Sau OP-11 pass | ExBot Worker | UC §3 step 3, FR-EXBOT-002 |
| OP-13 | CREATE bot record `lifecycle_state='preflight'` trong D1 | Sau tất cả preflight pass | ExBot Worker | UC §3 step 4, FR-EXBOT-003 |
| OP-14 | `BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` | Sau OP-13 | ExBot Worker → BnzaExVault | UC §3 step 5, FR-EXBOT-004 |
| OP-15 | Nhận sự kiện `VaultMinted(user, botId, tokenId, liquidity)` | Sau OP-14 succeed | ExBot Worker | UC §3 step 5 |
| OP-16 | UPDATE D1 `positions`: `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'` | Sau OP-15 | ExBot Worker | UC §3 step 6, FR-EXBOT-004 |
| OP-17 | Tính `targetShortEth = lpEthAmount × hedgeRatio (0.70)` bằng BigDecimal | Sau OP-16 | ExBot Worker | UC §3 step 7, FR-EXBOT-020, FR-EXBOT-021 |
| OP-18 | Signing Lambda: `openShortIoc(targetSize, cloid, hl_user_address)` | Sau OP-17 | ExBot Worker → Signing Lambda → KMS → HL | UC §3 step 7, SRS F-03 |
| OP-19 | KMS `kms:Sign` ký payload lệnh short qua agent key | Trong OP-18 | Signing Lambda | SRS F-03, FR-EXBOT-080 |
| OP-20 | Reconcile: lấy actual HL position via `clearinghouseState` | Sau OP-18 | ExBot Worker | UC §3 step 8, FR-EXBOT-025 |
| OP-21 | UPDATE D1 `hedge_legs`: `entry_price`, `liq_price`, `effective_leverage`, `lifecycle_state='hedge_post_confirmed'` | Sau OP-20 | ExBot Worker | UC §3 step 9, FR-EXBOT-025 |
| OP-22 | Tính `stop_trigger_px` bằng BigDecimal (`stopSafetyFactor=0.70`) | Sau OP-21 | ExBot Worker | UC §3 step 10, FR-EXBOT-030 |
| OP-23 | Signing Lambda: `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)` | Sau OP-22 | ExBot Worker → Signing Lambda → KMS → HL | UC §3 step 10, SRS F-03, FR-EXBOT-031 |
| OP-24 | UPDATE D1 `hedge_legs`: `stop_cloid`, `stop_price`; `lifecycle_state='stop_verified'→'active'` | Sau stop confirmed | ExBot Worker | UC §3 step 11, FR-EXBOT-031 |

### F.1.2 Data Objects & Fields

| # | Data Object | Field | Kiểu | Ghi chú / Source of Truth | Nguồn |
|---|---|---|---|---|---|
| DO-01 | `hl_agent_keys` | `id` | TEXT PK | | SRS ERD |
| DO-02 | `hl_agent_keys` | `user_id` | TEXT FK | | SRS ERD |
| DO-03 | `hl_agent_keys` | `hl_user_address` | TEXT | Public address của master key; private key ở KMS | SRS ERD, FR-EXBOT-080 |
| DO-04 | `hl_agent_keys` | `agent_address` | TEXT | Public address của agent key; private key ở KMS | SRS ERD, FR-EXBOT-080 |
| DO-05 | `hl_agent_keys` | `key_status` | TEXT | Enum: `active` / `superseded` / `revoked` | SRS states.md §Agent Key Status |
| DO-06 | `bot_registry` | `bot_id` | TEXT PK | | SRS ERD |
| DO-07 | `bot_registry` | `user_id` | TEXT FK | | SRS ERD |
| DO-08 | `bot_registry` | `status` | TEXT | Coarse: `active`/`paused`/`closing`/`closed`/`safe_mode`/`error` | SRS ERD, FR-EXBOT-003 |
| DO-09 | `bots` | `lifecycle_state` | TEXT | Fine-grained: 18 states — xem §F.1.4 | SRS states.md, FR-EXBOT-003 |
| DO-10 | `positions` | `token_id` | TEXT | LP NFT tokenId từ `VaultMinted` event | SRS ERD |
| DO-11 | `positions` | `tick_lower` | INTEGER | | SRS ERD |
| DO-12 | `positions` | `tick_upper` | INTEGER | | SRS ERD |
| DO-13 | `positions` | `weth_index` | INTEGER | 0 hoặc 1 — WETH là token0 hay token1; per-chain | SRS ERD, FR-EXBOT-004 |
| DO-14 | `positions` | `custodian` | TEXT | `'vault'` sau khi LP mint thành công | SRS ERD |
| DO-15 | `hedge_legs` | `entry_price` | TEXT | BigDecimal string; từ HL reconcile | SRS ERD, FR-EXBOT-025 |
| DO-16 | `hedge_legs` | `liquidation_price` | TEXT | BigDecimal string; từ HL reconcile | SRS ERD |
| DO-17 | `hedge_legs` | `effective_leverage` | TEXT | BigDecimal string; từ HL reconcile | SRS ERD |
| DO-18 | `hedge_legs` | `stop_price` | TEXT | BigDecimal string; tính bằng FR-EXBOT-030 | SRS ERD |
| DO-19 | `hedge_legs` | `stop_cloid` | TEXT | Deterministic cloid theo FR-EXBOT-024 | SRS ERD |

### F.1.3 Lifecycle States — `bots.lifecycle_state` (chỉ các state trong UC này)

| State | bots.status | Ý nghĩa | Chuyển sang | Trigger | Nguồn |
|---|---|---|---|---|---|
| `idle` | (pre-create) | Chưa khởi động | `preflight` | start request + one-bot check pass | SRS states.md |
| `preflight` | (transitional) | Đang chạy preflight checks | `lp_opening` hoặc kết thúc nếu fail | All preflight pass / any fail | SRS states.md |
| `lp_opening` | (transitional) | Đang mint LP | `lp_opened` hoặc `error` | VaultMinted / LP mint fails | SRS states.md |
| `lp_opened` | (transitional) | LP mint xong, hedge chưa mở | `hedge_pre_open` | LP confirmed | SRS states.md |
| `hedge_pre_open` | (transitional) | Đang mở HL short | `hedge_post_confirmed` hoặc `safe_mode` | IOC filled + reconcile / HL order fails | SRS states.md |
| `hedge_post_confirmed` | (transitional) | Short confirmed, stop chưa đặt | `stop_placing` | reconcile verified | SRS states.md |
| `stop_placing` | (transitional) | Đang đặt stop | `stop_verified` hoặc `safe_mode` | stop placed / stop placement fails | SRS states.md |
| `stop_verified` | (transitional) | Stop confirmed | `active` | bot fully initialized | SRS states.md |
| `active` | active | Bot hoạt động bình thường | nhiều state khác | light-check / hedge-sync / events | SRS states.md |
| `error` | error | Cần admin xử lý | — | critical bug / LP NFT anomaly | SRS states.md |
| `safe_mode` | safe_mode | Mọi mutation bị chặn | `active` (auto-recovery) hoặc `closed` | SAFE_MODE triggers | SRS states.md |

### F.1.4 Emitted Events & Messages

| # | Event / Message | Loại | Trigger | Nguồn |
|---|---|---|---|---|
| EV-01 | `VaultMinted(user, botId, tokenId, liquidity)` | On-chain event từ BnzaExVault | LP mint thành công | UC §3 step 5, SRS F-03 |
| MSG-01 | E-EXBOT-001: "You already have an active ExBot. Close or wait for the existing bot to finish." | API error 409 | One-bot policy fail | message-list.md, FR-EXBOT-001 |
| MSG-02 | E-EXBOT-002: "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | API error 400 | Margin insufficient | message-list.md, FR-EXBOT-002 |
| MSG-03 | E-EXBOT-017: "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." | API error 400 | `key_status` not active | message-list.md, FR-EXBOT-002 |
| MSG-04 | E-EXBOT-005: "HL builder fee (5bps) approval required before starting ExBot." | API error 400 | Builder fee not confirmed | message-list.md |
| MSG-05 | E-EXBOT-006: "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | API error 400 | LP simulation fail | message-list.md |
| MSG-06 | E-EXBOT-008: "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | API error 503 | HL unreachable (step 5 or 7) | message-list.md |
| MSG-07 | E-EXBOT-009: "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | API error 502 | Stop placement failed | message-list.md |

---

## §F.2 Trạng thái, điều kiện, validation và business rules theo từng operation

| Operation | Precondition | Validation / Business Rule | Dependency | Resolved Message |
|---|---|---|---|---|
| OP-08 (One-bot check) | ExBot Worker nhận bot-start job | `SELECT count(*) FROM bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')` — nếu > 0 → reject | D1 control_db | E-EXBOT-001 |
| OP-09 (Margin check) | One-bot check pass | `marginBalance >= (lpEthAmount × hedgeRatio × hlOraclePrice / leverage) × 2.0`. Dùng `hlOraclePrice` (không phải mark/pool price). | HL getMarginSummary; OQ-EXBOT-01 (field names pending) | E-EXBOT-002 |
| OP-10 (Key status check) | Margin check pass | `hl_agent_keys.key_status='active'` cho user này. Nếu không có row active → block. | D1 control_db `hl_agent_keys` | E-EXBOT-017 |
| OP-11 (Builder fee check) | Key status check pass | Builder fee 5bps confirmed trên HL. Cơ chế check: on-chain tx hay API call — OQ-EXBOT-05 vẫn mở. | HL (mechanism unclear — OQ-EXBOT-05) | E-EXBOT-005 |
| OP-12 (LP simulation) | Builder fee check pass | Mint simulation pass (slippage trong tolerance). Chưa gọi on-chain vault. | BnzaExVault ABI (OQ-EXBOT-08) | E-EXBOT-006 |
| OP-13 (Create bot record) | All 5 preflight pass | `lifecycle_state='preflight'` được ghi nguyên tử vào D1 trước khi gọi vault. BR-EXBOT-010: ExBot Worker độc lập với OPERATOR. | D1 state_db_shard | — |
| OP-14 (vaultMint) | Bot record created | `BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)`. ERC-20 allowance đã approve. Native gas đủ. | BnzaExVault on-chain; ABI pending OQ-EXBOT-08 | — (on-chain reverts nếu fail) |
| OP-16 (Update positions) | VaultMinted event nhận được | `wethIndex` (0 hoặc 1) phải được verify per-chain theo FR-EXBOT-004. Pool address và wethIndex per chain: OQ-EXBOT-03 vẫn mở. | D1 positions table; OQ-EXBOT-03 | — |
| OP-17 (Compute targetShortEth) | lp_opened confirmed | `targetShortEth = lpEthAmount × hedgeRatio`. Bắt buộc dùng BigDecimal. Phase A hedgeRatio = 0.70. Nguồn hedgeRatio từ config — BR-EXBOT-021 quy định admin config. | D1 bot config / `hedge_legs.target_ratio` | — |
| OP-18 (openShortIoc) | targetShortEth computed | Signing Lambda nhận request → KMS `kms:Sign` bằng agent key → gửi lệnh IOC đã ký lên HL. Minimum order size: OQ-EXBOT-04. | Signing Lambda, KMS, HL; OQ-EXBOT-04 | E-EXBOT-008 (HL unreachable), A10 (HL rejection) |
| OP-20 (Reconcile) | IOC order sent | Fetch `clearinghouseState`, verify actual size vs expected. Nếu sai lệch vượt ngưỡng → A11 `partial_repair`. Ngưỡng deviation chưa được nêu rõ trong UC — Issue I-02. | HL clearinghouseState; weight=2 (SRS F-03) | E-EXBOT-011 (internal) |
| OP-22 (Compute stop) | hedge_post_confirmed | `liq_distance_pct = (liq_price − entry_price) / entry_price`. `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)`. Bắt buộc BigDecimal. Fallback khi `liquidationPx` không có: `1/effective_leverage`. | hedge_legs data từ OP-21 | — |
| OP-23 (placeReduceOnlyStop) | stop_trigger_px computed | Signing Lambda ký payload stop order → HL. INV-STOP protocol (FR-EXBOT-035) không áp dụng ở bước này (đây là đặt stop lần đầu, không phải replace). | Signing Lambda, KMS, HL | E-EXBOT-009 (stop placement failed) |


---

## §F.3 Phân rã luồng xử lý — Happy path, Alternate, Exception

### F.3.1 Luồng chính: Key-Provision → Bot-Start → Active

| Bước | Actor | Trigger / Hành động | Phản hồi hệ thống — happy path | Alternate flow | Exception / Error | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Chain Indexer | On-chain deposit event detected | Enqueue `key-provision` job `{userId, depositAmount, txHash}` | — | Deposit watcher offline: không enqueue | SRS F-03 |
| 2 | Key-Provision Worker | Nhận message từ `key-provision` queue | `queue_idempotency` INSERT `state='started'`; UNIQUE conflict → skip | — | KMS ThrottlingException → retry max 3; admin alert on final fail | SRS F-03, FR-EXBOT-080, FR-EXBOT-011 |
| 3 | Key-Provision Worker | KMS GenerateKeyPair (master key) | KMS trả public address `hl_user_address`; private key ở KMS HSM | — | KMS fail → abort provisioning; retry via queue | FR-EXBOT-080 |
| 4 | Key-Provision Worker | KMS GenerateKeyPair (agent key) | KMS trả public address `agent_address`; private key ở KMS HSM | — | KMS fail → như bước 3 | FR-EXBOT-080 |
| 5 | Key-Provision Worker | HL `approveAgent(hl_user_address, agent_address)` | HL xác nhận agent đã đăng ký | — | HL call fail → `key_status='provisioning'`; retry; admin alert on SLA breach | FR-EXBOT-080 |
| 6 | Key-Provision Worker | INSERT `hl_agent_keys` với `key_status='active'` | Row được ghi vào D1 control_db | — | DB write fail → retry | FR-EXBOT-080 |
| 7 | Key-Provision Worker | Enqueue `bot-start` job `{userId}` | Job được đưa vào `bot-start` queue | — | Queue send fail → retry | SRS F-03 |
| 8 | ExBot Worker | Nhận message từ `bot-start` queue | `queue_idempotency` INSERT; UNIQUE conflict → skip | — | — | FR-EXBOT-011 |
| 9 | ExBot Worker | Preflight bước 1: one-bot check | `bot_registry` query trả về count=0 | **A1**: count > 0 → reject E-EXBOT-001; không tạo bot record | — | UC §3, FR-EXBOT-001 |
| 10 | ExBot Worker | Preflight bước 2: HL margin check | `marginBalance >= required × 2.0` → pass | **A2**: margin thiếu → block E-EXBOT-002 với số tiền cụ thể | HL API fail → chưa rõ trong UC (Issue I-03) | UC §3, FR-EXBOT-061 |
| 11 | ExBot Worker | Preflight bước 3: `key_status` check | `hl_agent_keys.key_status='active'` → pass | — | key không active → block E-EXBOT-017 | UC §3 step 3, FR-EXBOT-002 |
| 12 | ExBot Worker | Preflight bước 4: builder fee check | Builder fee 5bps confirmed → pass | **A5**: fee not confirmed → block E-EXBOT-005 | Cơ chế check chưa rõ (OQ-EXBOT-05) | UC §3, FR-EXBOT-002 |
| 13 | ExBot Worker | Preflight bước 5: LP mint simulation | Simulation pass (slippage OK) | **A6**: simulation fail → block E-EXBOT-006 | ABI pending (OQ-EXBOT-08) | UC §3, FR-EXBOT-002 |
| 14 | ExBot Worker | CREATE bot record `lifecycle_state='preflight'` | D1 INSERT nguyên tử; record được tạo | — | DB fail → không có partial record | UC §3 step 4, FR-EXBOT-003 |
| 15 | ExBot Worker | `BnzaExVault.vaultMint(...)` on-chain | Nhận `VaultMinted` event; `lifecycle_state='lp_opening'→'lp_opened'` | **A4**: LP mint fail → `error` state, return funds | **A7**: HL unreachable ở bước này → `error` state | UC §3 step 5–6, FR-EXBOT-004 |
| 16 | ExBot Worker | UPDATE `positions`: tokenId, tickLower, tickUpper, wethIndex | D1 positions row cập nhật đủ fields | — | wethIndex sai → tính lpEthAmount sai (Issue I-04) | UC §3 step 6, FR-EXBOT-004 |
| 17 | ExBot Worker → Signing Lambda | `openShortIoc(targetShortEth, cloid, hl_user_address)` | Signing Lambda gọi KMS Sign → gửi lệnh đã ký lên HL | — | **A7**: HL unreachable → `error`; **A10**: HL rejection → `error` | UC §3 step 7, SRS F-03 |
| 18 | ExBot Worker | Reconcile: fetch `clearinghouseState` từ HL | Actual size khớp expected; `lifecycle_state='hedge_post_confirmed'` | **A11**: sai lệch > threshold → enqueue `partial_repair`; alert operator | — | UC §3 step 8–9, FR-EXBOT-025 |
| 19 | ExBot Worker | Tính `stop_trigger_px` bằng BigDecimal | `stop_trigger_px` computed; không có intermediate float conversion | — | `liquidationPx` không có từ HL → fallback `1/effective_leverage` | UC §3 step 10, FR-EXBOT-030 |
| 20 | ExBot Worker → Signing Lambda | `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)` | KMS Sign → HL nhận stop order đã ký; stop confirmed | **A8**: stop placement fail → `error`; alert operator | — | UC §3 step 10–11, FR-EXBOT-031 |
| 21 | ExBot Worker | UPDATE `hedge_legs`: stop_cloid, stop_price; `lifecycle_state='stop_verified'→'active'` | D1 cập nhật nguyên tử; bot ở trạng thái `active` | — | — | UC §3 step 11, FR-EXBOT-031 |

### F.3.2 Alternate Flows chi tiết

| Flow ID | Trigger | Bước xảy ra | Hành động hệ thống | Error/Message | Nguồn |
|---|---|---|---|---|---|
| A1 | One-bot policy: count > 0 | Step 3 (preflight) | Reject; không tạo bot record | E-EXBOT-001 | UC §4 A1, FR-EXBOT-001 |
| A2 | Margin insufficient | Step 3 (preflight) | Block với số tiền thiếu cụ thể | E-EXBOT-002 | UC §4 A2, FR-EXBOT-061 |
| A4 | LP mint on-chain fails | Step 5 (vaultMint) | `lifecycle_state='error'`; return funds | — (on-chain event / revert) | UC §4 A4 |
| A5 | Builder fee not confirmed | Step 3 (preflight) | Block | E-EXBOT-005 | UC §4 A5 |
| A6 | LP mint simulation fail | Step 3 (preflight) | Block với simulation error details | E-EXBOT-006 | UC §4 A6 |
| A7 | HL unreachable | Step 5 hoặc 7 | `lifecycle_state='error'` | E-EXBOT-008 | UC §4 A7 |
| A8 | Stop placement fail | Step 10 | `lifecycle_state='error'`; HL short đang mở nhưng stop chưa có; alert operator | E-EXBOT-009 | UC §4 A8 |
| A10 | HL rejects IOC order | Step 7 | `lifecycle_state='error'`; HL rejection reason trả về | — (HL response) | UC §4 A10 |
| A11 | Reconcile mismatch | Step 8 | Actual size sai lệch > threshold → enqueue `partial_repair`; alert operator | E-EXBOT-011 (internal) | UC §4 A11 |

**Lưu ý quan trọng về A4 và A8:**
- A4: LP mint on-chain fail → bot enter `error` state và "return funds". UC không mô tả cơ chế return funds cụ thể khi vault tx reverts — liệu BnzaExVault tự hoàn tiền on-chain (revert) hay cần hành động riêng? (Issue I-05)
- A8: Stop placement fail → HL short đang mở nhưng không có stop. UC ghi "alert operator" nhưng không nêu message cụ thể gửi cho operator và không mô tả flow recovery (close HL short thủ công? bot_safe_close tự động?). (Issue I-06)

---

## §F.4 Tích hợp, hàng đợi và nhất quán dữ liệu

| Hành động kích hoạt | Hệ thống / UC / Service bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Nhất quán dữ liệu cần kiểm tra | Nguồn |
|---|---|---|---|---|
| Bot đạt `lifecycle_state='active'` | UC-EXBOT-light-check, UC-EXBOT-hedge-sync | Light-check cron bắt đầu scan bot này sau `next_light_check_at`; hedge-sync có thể được enqueue | `bots.status='active'`, `next_light_check_at` được set | SRS states.md, FR-EXBOT-012 |
| Bot đạt `lifecycle_state='active'` | UC-EXBOT-deep-audit | Deep-audit cron lên lịch cho bot này trong 6h tới | `bots.next_deep_audit_at` cần được set | FR-EXBOT-016 |
| Bot đạt `lifecycle_state='active'` | UC-EXBOT-monitor-status | POOL UI có thể lấy status qua Operator Facade GET `/api/exbot/status` | API phải trả `{status: 'active', botId, ...}` | UC §3 step 12, FR-EXBOT-090 |
| `hl_agent_keys` row được tạo với `key_status='active'` | Tất cả UC ExBot dùng HL signing | Mọi lệnh HL đều cần agent key active. Nếu key bị superseded/revoked sau khi bot active → UC-EXBOT-hedge-sync cần xử lý | BR-EXBOT-012: chỉ 1 row `active` per user bất kỳ lúc nào | FR-EXBOT-080, BR-EXBOT-012 |
| LP NFT được giữ bởi BnzaExVault (`positions.custodian='vault'`) | UC-EXBOT-user-redeem, UC-EXBOT-bot-safe-close | Khi close, `BnzaExVault.redeem(tokenId)` cần tokenId chính xác từ `positions` | `positions.token_id` phải match on-chain | FR-EXBOT-070 |
| KMS failure trong lúc hedge-sync signing | UC-EXBOT-hedge-sync | Bot vào SAFE_MODE; admin được cảnh báo | `bots.lifecycle_state` → `safe_mode` | FR-EXBOT-080, IC-EXBOT-005 |
| `bot-start` job được enqueue nhưng `bot_registry` đã có entry (race condition: 2 deposits) | UC-EXBOT-bot-start (concurrent) | One-bot check (`queue_idempotency`) ngăn 2 bot cùng khởi động | `queue_idempotency.message_id` UNIQUE; `bot_registry` count check | FR-EXBOT-011, FR-EXBOT-001 |

---

## §F.5 Acceptance Criteria candidates

| AC # | Scenario | Given | When | Then | Nguồn / Ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — bot khởi động thành công | Không có ExBot active; margin đủ (≥2.0×); `key_status='active'`; builder fee confirmed; simulation pass | Hệ thống nhận bot-start job sau deposit | Bot record tạo với từng trạng thái liên tiếp: `preflight→lp_opening→lp_opened→hedge_pre_open→hedge_post_confirmed→stop_placing→stop_verified→active`; `hedge_legs.stop_price` populated; `positions.custodian='vault'` | UC §3, US-EXBOT-001 AC-1; từ SRS |
| AC-02 | One-bot policy block | User đã có 1 ExBot với `status='active'` | Hệ thống nhận bot-start job thứ 2 sau deposit mới | Reject với E-EXBOT-001; không tạo bot record mới | FR-EXBOT-001; US-EXBOT-001 AC-2 |
| AC-03 | Margin insufficient | `marginBalance = $300`; required (×2.0) = $700 | Hệ thống chạy preflight bước 2 | Block với E-EXBOT-002; hiển thị số tiền cần nạp thêm ($400); không tạo bot record | FR-EXBOT-061; US-EXBOT-001 AC-3 |
| AC-04 | Agent key not provisioned | `hl_agent_keys` không có row với `key_status='active'` cho user | Hệ thống chạy preflight bước 3 | Block với E-EXBOT-017; không tạo bot record | FR-EXBOT-002 bước 3 |
| AC-05 | Builder fee not confirmed | Builder fee 5bps chưa approved trên HL | Hệ thống chạy preflight bước 4 | Block với E-EXBOT-005; không tạo bot record | FR-EXBOT-002 bước 4; OQ-EXBOT-05 cần resolve |
| AC-06 | LP simulation fail | Pool liquidity thấp hoặc deposit amount không phù hợp | Hệ thống chạy preflight bước 5 | Block với E-EXBOT-006; không tạo bot record | FR-EXBOT-002 bước 5 |
| AC-07 | HL unreachable during hedge open | HL API down tại thời điểm ExBot Worker gửi short IOC | ExBot Worker thực thi bước mở hedge (step 7) | `lifecycle_state='error'`; E-EXBOT-008; không partial state remaining | UC §4 A7 |
| AC-08 | Stop placement fails | HL nhận short nhưng reject lệnh stop market | ExBot Worker thực thi bước đặt stop (step 10) | `lifecycle_state='error'`; E-EXBOT-009; operator alert; HL short đang mở (A8) | UC §4 A8; **Suy luận cần xác nhận**: recovery flow chưa rõ |
| AC-09 | HL IOC order rejected | HL reject lệnh short IOC (vd: margin không đủ trên HL lúc order) | ExBot Worker gửi short IOC qua Signing Lambda | `lifecycle_state='error'`; HL rejection reason trả về | UC §4 A10 |
| AC-10 | Reconcile mismatch | Actual HL position size sai lệch vượt threshold | Post-hedge reconcile (step 8) | Enqueue `partial_repair`; operator alert; E-EXBOT-011 | UC §4 A11; **Suy luận cần xác nhận**: threshold chưa được nêu rõ |
| AC-11 | Private key security | Bot start thành công | Sau khi bot active | `hl_agent_keys` không chứa plaintext private key; log không chứa key material | FR-EXBOT-080, NFR-EXBOT-006 |
| AC-12 | wethIndex per chain | Bot start trên Base và Optimism | Sau LP mint | `positions.weth_index` khác nhau cho mỗi chain (nếu token ordering khác); không hardcode | FR-EXBOT-004; OQ-EXBOT-03 cần resolve trước |
| AC-13 | BigDecimal cho stop price | Bot start thành công | Sau stop placement | `hedge_legs.stop_price` < `hedge_legs.liquidation_price`; khoảng cách ≥ 30% (stopSafetyFactor=0.70) cho 3x leverage position | FR-EXBOT-030; Suy luận cần xác nhận |
| AC-14 | Idempotency — duplicate bot-start message | `bot-start` message được deliver lần 2 (do queue retry) | ExBot Worker nhận duplicate message | `queue_idempotency` UNIQUE conflict → skip; không tạo bot record thứ 2 | FR-EXBOT-011 |

---

## 6. Phân rã nghiệp vụ và luồng xử lý

> Đã được tổng hợp trong §F.3 (chi tiết hơn format template gốc). Phần này tham chiếu đến §F.3.

N/A — Luồng nghiệp vụ chi tiết đã được trình bày đầy đủ tại §F.3.1 (happy path) và §F.3.2 (alternate flows). Không duplicate để tránh inconsistency.

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

> Đã được tổng hợp trong §F.4. Tham chiếu đến §F.4.

N/A — Phân tích tích hợp và nhất quán dữ liệu đã được trình bày tại §F.4.

---

## 8. Acceptance Criteria

> Đã được tổng hợp trong §F.5. Tham chiếu đến §F.5.

N/A — AC candidates đã được liệt kê tại §F.5 (AC-01 đến AC-14).

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Security | Private key (master + agent) không bao giờ rời KMS; không xuất hiện trong log, memory, DB. Chỉ Signing Lambda IAM có `kms:Sign`. | Test: dump D1 `hl_agent_keys` — không có plaintext key material; log audit không có raw key values | FR-EXBOT-080, NFR-EXBOT-006 |
| Security | ExBot Worker không trực tiếp accessible từ internet (chỉ qua CF service binding + internal token) | Test: direct HTTP request đến ExBot Worker phải return 403 | FR-EXBOT-090, BR-EXBOT-010 |
| Precision | Tất cả tính toán hedge, stop, margin phải dùng BigDecimal. Cấm dùng JS float/Number cho giá trị tài chính. | Test: verify stop_price, entry_price trong D1 là TEXT (BigDecimal string), không phải number; verify không có intermediate float | NFR-EXBOT-008, FR-EXBOT-030 |
| Idempotency | Duplicate queue message → chỉ execute 1 lần (UNIQUE trên `queue_idempotency.message_id`) | Test: redelivery cùng message_id không tạo thêm bot record | NFR-EXBOT-007, FR-EXBOT-011 |
| Availability | KMS failure → retry tối đa 3 lần, sau đó admin alert; `key_status` không được set 'active' nếu provisioning chưa hoàn tất | Test: mock KMS failure → verify retry + admin notification; verify không có partial active row | FR-EXBOT-080, IC-EXBOT-005 |
| Multi-chain | Base và Optimism đều phải chạy được; `weth_index` verify per chain | Test: bot trên Base và Optimism cùng user (nếu Phase B), weth_index đúng mỗi chain | NFR-EXBOT-009, FR-EXBOT-004; OQ-EXBOT-03 |
| Rate limit | HL API: ≤ 800 weight/min. Bước preflight margin check (weight=2 theo SRS F-03) và reconcile đều consume weight. | Test: monitor HL weight consumption trong bot-start flow | NFR-EXBOT-004, FR-EXBOT-091 |


---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận (Issue Register)

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Ảnh hưởng đến tester | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 | Low | UNCLEAR_INFO | UC §1 Actors vs SRS F-03 | UC §1 Actors không liệt kê "Signing Lambda" dù SRS F-03 và UC step 7/10 đều đề cập. Đề xuất: thêm Signing Lambda vào UC §1 Actors để nhất quán. | Minor — tester có thể suy luận từ flow; không block | BA | Open |
| I-02 | High | MISSING_INFO | UC §4 A11 vs FR-EXBOT-025 | UC mô tả A11 (reconcile mismatch) là "actual size deviates > threshold" nhưng không định nghĩa threshold cụ thể là bao nhiêu. FR-EXBOT-025 cũng không nêu threshold. Tester cần biết ngưỡng deviation cụ thể để thiết kế test case kiểm tra boundary. | Blocker cho test reconcile mismatch | Tech Lead | Open |
| I-03 | Medium | MISSING_INFO | UC §3 step 3 (preflight bước 2) | Preflight bước 2 yêu cầu fetch HL `marginSummary` để kiểm tra margin. UC không mô tả hành vi khi HL API không phản hồi trong lúc preflight (khác với A7 xảy ra sau preflight). Nếu HL down tại bước preflight margin check → bot có enter `error` state hay retry sau đó? | Cần biết để test alternate flow HL timeout tại preflight | Tech Lead | Open |
| I-04 | High | CROSS_SOURCE_CONFLICT | UC §3 step 6 vs OQ-EXBOT-03 | UC nêu `wethIndex` được lưu vào `positions` sau LP mint, nhưng pool address + `wethIndex` cho USDC/WETH 0.3% trên Base và Optimism chưa được xác nhận (OQ-EXBOT-03 vẫn Open). Nếu wethIndex sai → `lpEthAmount` tính sai → hedge size sai. Test case kiểm tra wethIndex per chain bị block cho đến khi OQ-EXBOT-03 resolved. | Blocker cho test dual-chain LP open | BA / zen | Open |
| I-05 | High | UNCLEAR_INFO | UC §4 A4 | A4 ghi "enter `error` state, return funds" khi LP mint on-chain fails. Cơ chế "return funds" không được mô tả: BnzaExVault tự hoàn tiền qua on-chain revert, hay ExBot Worker cần gọi hàm riêng? Nếu là revert — USDC đã approve nhưng chưa transfer thì không cần return. Nếu cần hành động riêng — flow bị thiếu. | Cần biết để verify postcondition của test case A4 | BA / zen (BnzaExVault owner) | Open |
| I-06 | High | MISSING_INFO | UC §4 A8 | A8 ghi "enter `error` state; HL short open but stop not confirmed; alert operator". UC không nêu: (1) message cụ thể gửi cho operator; (2) recovery flow — operator phải làm gì tiếp theo? Đặt stop thủ công? Bot tự thử lại? `bot_safe_close` tự động? Trạng thái không có stop là rủi ro nghiệp vụ cao. | Cần biết để test expected result sau A8; alert message không thể verify nếu không có spec | Tech Lead / BA | Open |
| I-07 | Medium | MISSING_INFO | OQ-EXBOT-05 | Preflight bước 4 kiểm tra "builder fee (5bps) confirmed on HL" — nhưng cơ chế check không được mô tả: gọi HL API endpoint nào? Dùng weight bao nhiêu? Đây là OQ-EXBOT-05 trong SRS (Open). Tester cần biết để test bước này một cách độc lập. | Block test case cho preflight builder fee check | Tech Lead | Open |
| I-08 | Medium | CROSS_SOURCE_CONFLICT | message-list.md vs srs/spec.md §5 | message-list.md còn có E-EXBOT-003 ("Agent key awaiting approval") và E-EXBOT-004 ("Agent key expired"), E-EXBOT-014, E-EXBOT-015, E-EXBOT-016 — đây là các message từ luồng manual agent key cũ đã bị bỏ (UC-EXBOT-agent-key retired, OQ-EXBOT-16 Closed). SRS spec.md §5 không còn liệt kê E-003/004. Có nguy cơ tester thiết kế test case sai dựa trên các E-code đã obsolete này. | Cần BA xác nhận E-003/004/014/015/016 có được xóa khỏi message-list.md không | BA | Open |
| I-09 | Low | MISSING_INFO | UC §3 step 3 — thứ tự preflight | UC nêu 5 bước preflight "run in sequence" nhưng không nêu rõ khi nào bot record được tạo vs khi nào từng check được chạy. SRS FR-EXBOT-002 ghi rõ: chỉ tạo bot record SAU KHI tất cả 5 preflight pass. UC step 4 cũng nhất quán. Tuy nhiên UC không nêu khi preflight fail ở bước 3/4/5 thì check trước đó đã "consume" HL API weight chưa (margin check = weight 2). Không phải conflict nhưng cần clarify cho test design. | Ảnh hưởng test HL rate limit trong preflight | Tech Lead | Open |
| I-10 | High | MISSING_INFO | SRS FR-EXBOT-002 vs UC §3 step 3 | FR-EXBOT-002 (SRS spec.md) và UC ghi "builder fee (5bps) confirmed on HL" là bước preflight. Tuy nhiên precondition UC §2 cũng ghi "Builder fee (5bps) confirmed on HL". Câu hỏi: builder fee check trong preflight là RE-CHECK hay lần check duy nhất? Nếu re-check — điều gì xảy ra nếu builder fee đã được confirm trước đây nhưng bị revoke sau đó? | Cần biết để design test case cho edge case fee revoke | BA / Tech Lead | Open |

**Số lượng Open issues: 10**
**Blocker issues (I-02, I-04, I-05, I-06): 4**

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-03: Pool address + wethIndex cho USDC/WETH 0.3% trên Base + Optimism | Integration / Data | Block test case dual-chain wethIndex; block AC-12 | zen / SOTATEK NV-12 | Open |
| OQ-EXBOT-05: Builder fee 5bps — on-chain tx hay API call? | Integration | Block test case preflight builder fee (AC-05) | Tech Lead | Open |
| OQ-EXBOT-08: BnzaExVault final ABI | Integration | Block integration test LP mint + redeem; AC-01, AC-08, AC-10 dùng stub đến khi ABI confirmed | zen | Open |
| OQ-EXBOT-01: HL marginSummary field names (marginBalanceUsd) | Integration | Block implementation FR-EXBOT-060; ảnh hưởng test preflight margin check | NV-1 (zen/SOTATEK) | Open |
| Signing Lambda IAM + KMS integration | Environment | Test security (AC-11) cần environment có real KMS | Ops / zen | Open |

---

## 10.3 Audit Summary — Đánh giá tổng thể và điểm số sẵn sàng

### Scoring Table

| # | Khu vực đánh giá | Điểm tối đa | Điểm đạt | Trạng thái | Lý do chính |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 16 | ⚠️ Partial | Operation, data objects, state enum, messages được liệt kê đầy đủ và nguyên tử. Trừ điểm: reconcile threshold (F.1 không thể điền giá trị cụ thể — I-02); wethIndex per chain chưa có giá trị confirm (OQ-EXBOT-03). Blockchain checklist B1–B9 phần lớn covered; B3 (chainId per chain) chưa rõ trong UC; B6 (mid-flow agent-key change) không có trong UC. |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 18 | ⚠️ Partial | State machine 9 trạng thái initialization rõ ràng. BR-EXBOT-001, 010, 012 được resolve verbatim. E-EXBOT-001/002/005/006/008/009/017 có đầy đủ message text. Trừ điểm: threshold reconcile mismatch missing (I-02); A8 không có operator message spec (I-06); builder fee check mechanism unclear (I-07). Không áp dụng §F.2 cap 15/25 (coverage >80% của F.1 elements). |
| 3 | Functional Logic & Workflow Decomposition | 25 | 18 | ⚠️ Partial | Happy path 24 operation steps đầy đủ; alternate flows A1–A11 có. Trừ điểm: HL API fail tại preflight margin check chưa xử lý (I-03); A4 return funds mechanism unclear (I-05); A8 recovery flow undefined (I-06). Cap F.3 18/25 áp dụng (A8 exception path thiếu recovery). |
| 4 | Functional Integration & Data Consistency | 15 | 11 | ⚠️ Partial | Cross-service effects (light-check, deep-audit, monitor-status) được identify. On-chain↔off-chain source of truth rõ. Trừ điểm: wethIndex dependency chưa confirm (I-04/OQ-EXBOT-03); BnzaExVault ABI stub (OQ-EXBOT-08). |
| 5 | UC / Spec Documentation Quality Issues | 15 | 10 | ⚠️ Partial | UC được viết rõ ràng, cấu trúc tốt. Trừ điểm: I-01 Signing Lambda thiếu trong §1 Actors; I-08 obsolete E-codes trong message-list; I-09/I-10 minor ambiguity về builder fee và HL weight. |

**Tổng điểm: 73 / 100**

### Kết luận và khuyến nghị

**Verdict: Conditionally Ready (Sẵn sàng có điều kiện)**

UC-EXBOT-bot-start có chất lượng tổng thể tốt — luồng chính được mô tả đầy đủ và nhất quán với SRS, state machine initialization 9 bước rõ ràng không bỏ qua bước nào, security model (KMS/Signing Lambda) được mô tả chính xác, và hầu hết alternate flows có error message cụ thể.

**Có thể tiến hành thiết kế test ngay** cho: happy path (AC-01), one-bot policy (AC-02), margin check (AC-03), key not provisioned (AC-04), simulation fail (AC-06), HL unreachable (AC-07), HL rejection (AC-10), security/idempotency (AC-11, AC-14).

**Cần resolve trước khi test đầy đủ:**
1. **I-02** (High): Xác nhận ngưỡng deviation cho reconcile mismatch (A11) — block AC-10 boundary test.
2. **I-05** (High): Xác nhận cơ chế "return funds" trong A4 (LP mint fail) — block AC postcondition verification.
3. **I-06** (High): Xác nhận operator alert message và recovery flow trong A8 (stop placement fail) — block AC-08 expected result.
4. **I-04 / OQ-EXBOT-03** (High): Confirm pool address + wethIndex per chain — block dual-chain test (AC-12).

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu — SRS-first cross-check |

