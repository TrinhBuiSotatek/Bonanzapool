# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Tên tài liệu:** UC-EXBOT-bot-start — Audited Readiness Report  
**Ngày tạo:** 2026-07-06  
**Tác giả:** QC UC Read ExBot Agent  
**Phiên bản:** v3

---

## Bảng mã viết tắt

| Mã / Tiền tố | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC | Use Case — mô tả luồng nghiệp vụ cấp cao | `usecases/` |
| US | User Story — mô tả nhu cầu từ góc nhìn người dùng/hệ thống | `userstories/` |
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng của module ExBot | `srs/spec.md`, `frd.md` |
| BR-EXBOT-* | Business Rule — quy tắc nghiệp vụ cố định của module ExBot | `srs/spec.md §4` |
| E-EXBOT-* | Error Code — mã lỗi API-layer trả về từ ExBot Lambda qua Operator Facade | `message-list.md` |
| SRS | Software Requirements Specification — nguồn sự thật chính của ExBot | `srs/spec.md`, `srs/states.md`, `srs/flows.md`, `srs/erd.md` |
| FRD | Functional Requirements Document — mô tả yêu cầu chức năng cấp module | `frd.md` |
| KMS | AWS Key Management Service — dịch vụ lưu khóa bí mật; private key KHÔNG bao giờ rời KMS HSM | `srs/spec.md §FR-EXBOT-080` |
| HL | Hyperliquid — sàn giao dịch perp phi tập trung; ExBot mở vị thế short ETH-USD tại đây | (external platform) |
| IOC | Immediate-Or-Cancel — loại lệnh giao dịch: khớp ngay hoặc hủy, không để pending | (industry term) |
| LP | Liquidity Provider — vị thế thanh khoản Uniswap V3; ExBot quản lý LP NFT trong BnzaExVault | (industry term) |
| NFT | Non-Fungible Token — token định danh duy nhất đại diện cho LP position, giữ bởi BnzaExVault | (industry term) |
| cloid | Client Order ID — ID lệnh xác định từ phía client, dùng để dedup lệnh HL | `srs/spec.md §FR-EXBOT-022` |
| SAFE_MODE | Trạng thái an toàn — mọi thao tác mutation bị chặn; chỉ cho phép đọc và cảnh báo | `srs/states.md`, `srs/spec.md §FR-EXBOT-050` |
| BigDecimal | Kiểu số thập phân độ chính xác tùy ý — bắt buộc dùng cho mọi tính toán tài chính, cấm dùng JS float | `srs/spec.md §NFR-EXBOT-008` |
| HSM | Hardware Security Module — module bảo mật phần cứng bên trong AWS KMS, nơi private key được lưu và không bao giờ xuất ra ngoài | (industry term) |
| IAM | Identity and Access Management — dịch vụ phân quyền của AWS; chỉ Signing Lambda có quyền `kms:Sign` | (AWS term) |
| SQS | Simple Queue Service — dịch vụ hàng đợi tin nhắn của AWS, thay thế Cloudflare Queue (arc-migration 2026-07-04) | (AWS term) |
| Aurora PostgreSQL | Cơ sở dữ liệu quan hệ managed của AWS, thay thế Cloudflare D1 (arc-migration 2026-07-04) | (AWS term) |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả quá trình **khởi động tự động ExBot** sau khi hệ thống phát hiện giao dịch nạp tiền on-chain của người dùng. Đây là luồng hoàn toàn do hệ thống kích hoạt — người dùng không cần thực hiện thao tác nào ngoài việc nạp USDC vào hợp đồng BnzaExVault trên chain. Không có giao diện người dùng (no-UI): toàn bộ luồng được thực thi qua SQS queue, AWS Lambda, và các lời gọi API/on-chain.

Luồng bắt đầu khi Chain Indexer (Fargate) phát hiện sự kiện nạp tiền on-chain và đưa vào hàng đợi `key-provision`. Key-Provision Worker tạo cặp khóa master key + agent key hoàn toàn trong AWS KMS HSM (private key không bao giờ rời KMS), đăng ký agent key với Hyperliquid qua `approveAgent`, ghi `hl_agent_keys.key_status='active'` vào Aurora PostgreSQL, rồi đưa lệnh khởi động bot vào hàng đợi `bot-start`. ExBot Lambda nhận lệnh, chạy 5 kiểm tra tiền đề (preflight) tuần tự: chính sách một-bot → đủ ký quỹ HL → `key_status='active'` → builder fee → mô phỏng mint LP. Sau preflight, ExBot Lambda mint LP NFT qua hợp đồng BnzaExVault trên chain, mở vị thế short ETH IOC trên Hyperliquid qua Signing Lambda (kms:Sign), đặt stop market reduce-only, và chuyển bot sang trạng thái `active`.

**Thay đổi quan trọng so với v2 (arc-migration 2026-07-04):** Toàn bộ primitive Cloudflare đã được thay thế bằng tương đương AWS: D1 → Aurora PostgreSQL, ExBot Worker → ExBot Lambda, Cloudflare Queue → SQS/BullMQ. Tài liệu SRS, UC, FRD đã cập nhật ngày 2026-07-04. **I-11 vẫn còn mở:** UC §4 A7/A10 ghi trạng thái đích là `error` nhưng `srs/states.md` xác nhận `hedge_pre_open → safe_mode` (không phải `error`) khi HL order thất bại. I-06 đã giải quyết (v2): `stop_placing → safe_mode`. Phát hiện mới trong v3: FR trace không đầy đủ và ERD `hl_agent_keys` cần làm rõ thêm sau arc-migration.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-start | Start ExBot — tự động khởi động sau deposit + key provisioning | 2026-07-04 (changelog) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-07-04 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-bot-start.md` | 2026-07-04 | UC | Tài liệu chính được review |
| `userstories/us-001.md` | 2026-07-04 | US | Linked story duy nhất |
| `srs/spec.md` | 2026-07-04 | SRS (nguồn sự thật) | Canonical source |
| `srs/states.md` | 2026-07-04 | State diagram | Lifecycle state machine + key_status 3-state |
| `srs/flows.md` | 2026-07-04 | Flow diagram | F-03: Bot Initialization Flow (rewritten 2026-06-29) |
| `srs/erd.md` | 2026-07-04 | ERD | Aurora PostgreSQL schema; hl_agent_keys RETIRED fields |
| `frd.md` | 2026-07-04 | FRD | FR-EXBOT-001..031, FR-EXBOT-080..091 |
| `02_backbone/message-list.md` | 2026-07-01 | Common messages | E-EXBOT-001..018; E-EXBOT-003/004 deprecated |
| `02_backbone/common-rules.md` | 2026-06-26 | Common rules | BR-EXBOT-001..014 |


---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC-EXBOT-bot-start tồn tại để tự động hóa toàn bộ quá trình khởi động một bot quản lý vị thế LP delta-hedged trên USDC/ETH cho nhà đầu tư, từ thời điểm hệ thống phát hiện giao dịch nạp tiền on-chain cho đến khi bot ở trạng thái `active` với LP NFT được giữ bởi BnzaExVault, vị thế short ETH trên Hyperliquid đã xác nhận, và lệnh stop reduce-only đã được đặt. Mục tiêu: LP của nhà đầu tư được bảo vệ bởi hedge ngay khi nạp tiền, không cần thao tác thủ công từ phía người dùng hoặc admin.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Key-Provision | Chain Indexer phát hiện deposit on-chain → Key-Provision Worker tạo master key + agent key trong KMS HSM → HL `approveAgent` → `key_status='active'` → enqueue bot-start job | SRS F-03, FR-EXBOT-081 |
| Preflight checks | ExBot Lambda chạy 5 kiểm tra tuần tự: (1) chính sách một-bot, (2) đủ ký quỹ HL, (3) `key_status='active'`, (4) builder fee (5bps) đã xác nhận, (5) mô phỏng mint LP; bất kỳ lỗi nào dừng luồng | FR-EXBOT-001, UC §3 step 3 |
| LP mint | ExBot Lambda gọi `BnzaExVault.vaultMint(...)` on-chain → nhận `VaultMinted` event với `tokenId` → cập nhật Aurora PostgreSQL `positions` | FR-EXBOT-020, UC §3 step 5 |
| Hedge open | ExBot Lambda yêu cầu Signing Lambda mở short IOC trên HL (targetShortEth = lpEthAmount × 0.70) → reconcile actual position → ghi `hedge_legs` | FR-EXBOT-030, FR-EXBOT-023, UC §3 step 7-9 |
| Stop placement | ExBot Lambda tính `stop_trigger_px` (BigDecimal, safetyFactor=0.70) → yêu cầu Signing Lambda đặt reduce-only stop market → xác nhận → `lifecycle_state='stop_verified' → 'active'` | FR-EXBOT-030, UC §3 step 10-11 |
| Alternate flows | A1 (one-bot fail), A2 (margin fail), A4 (LP mint fail → `error`), A5 (builder fee fail), A6 (LP sim fail), A7 (HL unreachable), A8 (stop fail → `safe_mode`), A10 (HL IOC reject), A11 (reconcile mismatch) | UC §4 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Giao diện người dùng | ExBot không có UI; bot-start được kích hoạt tự động | Không có test UI |
| Quy trình nạp tiền on-chain | Thuộc phạm vi chain indexer / vault smart contract | Test bot-start giả định deposit đã xảy ra |
| Key rotation (superseded → new active) | Thuộc FR-EXBOT-081 nhưng không có trong UC bot-start | Cần UC riêng |
| Close / redeem flow | UC bot-close / F-04 / F-05 riêng biệt | Out of scope UC này |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| Chain Indexer (Fargate) | System | Phát hiện sự kiện nạp tiền on-chain, enqueue `key-provision` job | Chỉ ghi queue; không gọi API HL | SRS F-03 |
| Key-Provision Worker | System | Tạo key trong KMS, gọi HL `approveAgent`, ghi `hl_agent_keys`, enqueue `bot-start` | IAM: `kms:GenerateKeyPair`; HL: `approveAgent` | FR-EXBOT-081, SRS F-03 |
| ExBot Lambda | System | Nhận bot-start job, chạy preflight, điều phối LP mint + hedge open + stop placement | Không gọi KMS trực tiếp; dùng Signing Lambda cho kms:Sign | FR-EXBOT-001, 002, 030, UC §1 |
| BnzaExVault (Solidity) | System (on-chain) | Mint LP NFT, giữ `tokenId`; emit `VaultMinted` event | Smart contract; không có admin override | FR-EXBOT-020, UC §3 step 5 |
| Hyperliquid | External | Nhận lệnh short IOC, xác nhận position; nhận lệnh stop reduce-only | HL API rate limit 800 weight/min (FR-EXBOT-090) | FR-EXBOT-030, UC §1 |
| AWS KMS | System (external) | Giữ private key trong HSM; thực hiện `kms:Sign` khi Signing Lambda yêu cầu | Private key không bao giờ rời KMS | FR-EXBOT-081 |
| Signing Lambda | System | Ký payload lệnh HL bằng agent key (kms:Sign); không có quyền `kms:GenerateKeyPair` | Chỉ IAM `kms:Sign`; không thể tạo key | FR-EXBOT-081, SRS F-03 |
| USDC Investor | Khởi phát (gián tiếp) | Kích hoạt luồng bằng hành động nạp tiền on-chain | Không có quyền can thiệp vào luồng bot-start | US-EXBOT-001 |

**Nhận xét readiness:** Actor đã đủ rõ cho test. Sự phân chia trách nhiệm giữa Key-Provision Worker, ExBot Lambda, và Signing Lambda được mô tả rõ trong SRS F-03. Không cần phân quyền admin trong UC này (bot-start là fully automated).

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Người dùng không có ExBot hiện tại với `status IN ('active','paused','closing','safe_mode','error')` | Yes | UC §2, BR-EXBOT-001 |
| 2 | Số dư ký quỹ HL isolated ≥ required × 2.0 | Yes | UC §2, FR-EXBOT-001 |
| 3 | `hl_agent_keys.key_status='active'` đã được key-provision worker tạo sau khi deposit on-chain | Yes | UC §2, FR-EXBOT-001, FR-EXBOT-081 |
| 4 | Builder fee (5bps) đã được xác nhận trên HL | Yes | UC §2, FR-EXBOT-001 |
| 5 | Người dùng đã approve BnzaExVault chi tiêu USDC ≥ deposit amount (ERC-20 allowance) | Yes | UC §2 |
| 6 | Người dùng giữ đủ ETH/native token cho gas giao dịch vault | Yes | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Khởi tạo bot thành công | `bots.lifecycle_state='active'`, `bots.status='active'` | UC §5, FR-EXBOT-003 |
| LP position | LP NFT giữ bởi BnzaExVault (`positions.custodian='vault'`); `tokenId`, `tickLower`, `tickUpper`, `wethIndex` đã ghi vào Aurora PostgreSQL | UC §5 |
| Hedge | HL short open với size = lpEthAmount × 0.70; `hedge_legs.entry_price`, `liquidation_price`, `effective_leverage` đã ghi | UC §5, FR-EXBOT-023 |
| Stop | Reduce-only stop market đặt trên HL; `hedge_legs.stop_cloid`, `stop_price`, `stop_size` đã ghi | UC §5, FR-EXBOT-030 |


---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Luồng: Key Provisioning (Chain Indexer → KMS → HL → Bot-Start Queue)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | Chain Indexer | Phát hiện sự kiện nạp tiền on-chain | Enqueue `key-provision` job `{userId, depositAmount, txHash}` vào SQS | — | — | SRS F-03 |
| 2 | Key-Provision Worker | Nhận job từ SQS | Gọi AWS KMS `GenerateKeyPair` (master key) → nhận `hl_user_address` (public only) | — | KMS không phản hồi: retry tối đa 3 lần; nếu vẫn thất bại → thông báo admin | FR-EXBOT-081 |
| 3 | Key-Provision Worker | Tiếp tục | Gọi KMS `GenerateKeyPair` (agent key) → nhận `agent_address` (public only) | — | Xem lỗi bước 2 | FR-EXBOT-081 |
| 4 | Key-Provision Worker | Gọi HL `approveAgent` | HL xác nhận agent được đăng ký là delegate của master key | — | HL `approveAgent` thất bại: key vẫn `key_status='provisioning'`; retry qua queue; thông báo admin nếu vượt SLA | FR-EXBOT-081 |
| 5 | Key-Provision Worker | Ghi vào Aurora PostgreSQL | INSERT `hl_agent_keys` với `key_status='active'`, `agent_address`, `hl_user_address` | — | DB INSERT thất bại: retry | FR-EXBOT-081, ERD |
| 6 | Key-Provision Worker | Enqueue bot-start | SQS `bot-start` nhận job `{userId}` | — | — | SRS F-03 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Private key (master + agent) | Không bao giờ rời KMS HSM | Yes | Lưu trong KMS; public address ghi vào Aurora PostgreSQL | Vi phạm bảo mật — không được phép | FR-EXBOT-081, NFR-EXBOT-006 |
| HL `approveAgent` trước khi `key_status='active'` | `approveAgent` phải thành công trước khi set `active` | Yes | `key_status='active'` | `key_status='provisioning'`; không enqueue bot-start | FR-EXBOT-081 |
| Chỉ một row `key_status='active'` mỗi user | Constraint ở cấp database | Yes | Duy nhất row active | DB constraint violation | BR-EXBOT-012, spec.md §4 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| KMS GenerateKeyPair thất bại sau 3 lần retry | Admin notification | (nội dung message chưa được định nghĩa trong tài liệu hiện tại) | — | FR-EXBOT-081 |
| HL `approveAgent` thất bại, vượt SLA | Admin notification | (nội dung message chưa được định nghĩa) | — | FR-EXBOT-081 |

---

### 6.2 Luồng: Preflight Checks

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Lambda | Nhận job từ SQS `bot-start` | Kiểm tra idempotency: INSERT `queue_idempotency` với `message_id='started'`; UNIQUE conflict → thoát im lặng | — | UNIQUE conflict (duplicate delivery) → thoát không xử lý | FR-EXBOT-011 |
| 2 | ExBot Lambda | Check one-bot policy | Không có bot nào có `status IN ('active','paused','closing','safe_mode','error')` → pass | A1: Có bot đang tồn tại → reject với E-EXBOT-001 | — | FR-EXBOT-001, BR-EXBOT-001 |
| 3 | ExBot Lambda | Check margin | HL `getMarginSummary` → balance ≥ required × 2.0 → pass | A2: balance không đủ → block với E-EXBOT-002 | — | FR-EXBOT-001, UC §3 |
| 4 | ExBot Lambda | Check `key_status` | `hl_agent_keys.key_status='active'` → pass | — | `key_status` không phải `active` → block với E-EXBOT-017 | FR-EXBOT-001, UC §3 step 3 |
| 5 | ExBot Lambda | Check builder fee | Builder fee (5bps) đã xác nhận trên HL → pass | A5: chưa xác nhận → block với E-EXBOT-005 | — | FR-EXBOT-001, UC §4 A5 |
| 6 | ExBot Lambda | LP mint simulation | Mô phỏng mint LP → thành công → pass | A6: simulation thất bại → block với E-EXBOT-006 | — | FR-EXBOT-001, UC §4 A6 |
| 7 | ExBot Lambda | Tạo bot record | CREATE `bots` với `lifecycle_state='preflight'` | — | — | UC §3 step 4, FR-EXBOT-003 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| One-bot policy | `status NOT IN ('active','paused','closing','safe_mode','error')` | Yes | Preflight tiếp tục | E-EXBOT-001: "You already have an active ExBot. Close or wait for the existing bot to finish." | BR-EXBOT-001, FR-EXBOT-001 |
| Margin buffer | `balance ≥ required × 2.0` | Yes | Preflight tiếp tục | E-EXBOT-002: "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | FR-EXBOT-001 |
| key_status active | `hl_agent_keys.key_status='active'` | Yes | Preflight tiếp tục | E-EXBOT-017: "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." | FR-EXBOT-001, FR-EXBOT-081 |
| Builder fee | 5bps đã xác nhận trên HL | Yes | Preflight tiếp tục | E-EXBOT-005: "HL builder fee (5bps) approval required before starting ExBot." | FR-EXBOT-001, UC §4 A5 |
| Preflight thứ tự kiểm tra | one-bot → margin → key_status → builder fee → LP sim; không được đảo thứ tự | Yes | Kiểm tra tuần tự | Nếu đảo thứ tự → hành vi không xác định | FR-EXBOT-001 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| One-bot policy fail | API error response (409) | "You already have an active ExBot. Close or wait for the existing bot to finish." | E-EXBOT-001 | message-list.md |
| Margin không đủ | API error response (400) | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | E-EXBOT-002 | message-list.md |
| key_status không active | API error response (400) | "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." | E-EXBOT-017 | message-list.md |
| Builder fee chưa xác nhận | API error response (400) | "HL builder fee (5bps) approval required before starting ExBot." | E-EXBOT-005 | message-list.md |
| LP simulation thất bại | API error response (400) | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | E-EXBOT-006 | message-list.md |


---

### 6.3 Luồng: LP Mint (BnzaExVault)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Lambda | Gọi `BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` | Hợp đồng emit `VaultMinted(user, botId, tokenId, liquidity)` | — | A4: LP mint thất bại → `lifecycle_state='error'`; hoàn trả tiền | UC §4 A4, states.md |
| 2 | ExBot Lambda | Nhận `VaultMinted` event | Cập nhật Aurora PostgreSQL `positions`: `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `lifecycle_state='lp_opened'` | — | — | UC §3 step 6, FR-EXBOT-020 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `wethIndex` | 0 hoặc 1 tùy theo chain (Base vs Optimism); phải verify và lưu vào `positions.weth_index` tại thời điểm LP open | Yes | `weth_index` chính xác cho tính toán `lpEthAmount` | Sai `weth_index` → tính toán hedge sai → lỗi nghiêm trọng | FR-EXBOT-004, FR-EXBOT-020 |
| `lpEthAmount` | Tính từ `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick` bằng Uniswap V3 TickMath + LiquidityAmounts; KHÔNG dùng formula `depositedToken - withdrawnToken` | Yes | Giá trị chính xác | Nếu dùng formula sai → hedge ratio sai | frd.md §FR-EXBOT-021 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| LP mint thành công | State transition + on-chain event | `lifecycle_state` → `lp_opened`; `VaultMinted` event với `tokenId` | — | UC §3 step 6 |
| LP mint thất bại | State transition + hoàn tiền | `lifecycle_state` → `error`; hoàn trả tiền | UC §4 A4 | uc-bot-start.md §4 A4 |

---

### 6.4 Luồng: Hedge Open (HL Short IOC qua Signing Lambda)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Lambda | Tính `targetShortEth = lpEthAmount × hedgeRatio (Phase A = 0.70)` | Giá trị targetShortEth bằng BigDecimal | — | — | FR-EXBOT-020, UC §3 step 7 |
| 2 | ExBot Lambda | Yêu cầu Signing Lambda `openShortIoc(targetSize, cloid, hl_user_address)` | Signing Lambda gọi KMS `kms:Sign` → ký payload → gửi lệnh IOC lên HL | A7: HL unreachable — **I-11 OPEN** | A10: HL reject IOC — **I-11 OPEN** | UC §3 step 7, FR-EXBOT-081 |
| 3 | ExBot Lambda | Post-order reconcile: `fetchActualHLPosition(clearinghouseState)` | Lấy `entry_price`, `liquidation_price`, `effective_leverage`; verify size = target | A11: size lệch > `drift_threshold` → enqueue `partial_repair`; thông báo admin | — | FR-EXBOT-023, UC §3 step 8 |
| 4 | ExBot Lambda | Cập nhật Aurora PostgreSQL | `lifecycle_state='hedge_post_confirmed'`; ghi `hedge_legs.entry_price`, `liq_price`, `effective_leverage` | — | — | UC §3 step 9, FR-EXBOT-023 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| cloid idempotency | `cloid = first128BitsHex(keccak256('bnza:{botId}:{attemptId}:{stage}:{version}'))` — cùng retry = cùng cloid; payload thay đổi → increment version | Yes | Không retry trùng lệnh | Gửi lệnh trùng lặp | FR-EXBOT-022 |
| Reconcile trước khi ghi success | Không ghi success trước khi reconcile xác nhận kích thước thực tế | Yes | `hedge_legs` chính xác | Ghi sai kích thước hedge | FR-EXBOT-023 |
| hedgeRatio Phase A | 0.70 (cứng) | Yes | Mở 70% ETH LP value | — | UC §3 step 7 |
| drift_threshold | `deltaErrorUsd > max($25, lpValueUsd × 3%)` — nếu vượt → `partial_repair` | Yes | Hedge khớp target | Enqueue partial_repair + thông báo admin | FR-EXBOT-012 (OQ-EXBOT-11 OPEN: công thức `lpValueUsd` chưa được chốt) |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| HL unreachable (A7) | State transition (trạng thái đích chưa xác nhận — **I-11 OPEN**) | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | E-EXBOT-008 | message-list.md; UC §4 A7 ghi `error` nhưng states.md ghi `safe_mode` |
| HL IOC reject (A10) | State transition (trạng thái đích chưa xác nhận — **I-11 OPEN**) | (Nội dung message chưa được định nghĩa rõ trong tài liệu cho trường hợp này) | UC §4 A10 | uc-bot-start.md §4 A10 |
| Reconcile mismatch (A11) | Queue message + admin notification | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | E-EXBOT-011 | message-list.md, UC §4 A11 |

---

### 6.5 Luồng: Stop Placement

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | ExBot Lambda | Tính `stop_trigger_px` | `liq_distance_pct = (liquidation_price − entry_price) / entry_price`; `stop_distance_pct = liq_distance_pct × 0.70`; `stop_trigger_px = entry_price × (1 + stop_distance_pct)` — BigDecimal bắt buộc | — | — | FR-EXBOT-030 |
| 2 | ExBot Lambda | Yêu cầu Signing Lambda `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)` | Signing Lambda ký → HL nhận lệnh stop | — | A8: stop fail → `lifecycle_state='safe_mode'`; short mở nhưng stop chưa xác nhận; thông báo operator; auto-recovery per FR-EXBOT-050 | UC §4 A8, states.md |
| 3 | ExBot Lambda | Xác nhận stop | Ghi `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size` vào Aurora PostgreSQL | — | — | FR-EXBOT-030 |
| 4 | ExBot Lambda | Cập nhật trạng thái | `lifecycle_state='stop_verified'` → `'active'` | — | — | UC §3 step 11 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| BigDecimal bắt buộc | `stop_trigger_px` PHẢI dùng BigDecimal (không được dùng JS float) | Yes | Tính toán chính xác | Lỗi làm tròn → stop price sai → rủi ro tài chính | FR-EXBOT-030 |
| stopSafetyFactor | Phase A = 0.70 | Yes | Stop đặt ở 70% khoảng cách liquidation | — | FR-EXBOT-030 |
| Stop fail → safe_mode | `stop_placing → safe_mode` khi đặt stop thất bại; KHÔNG phải `error` | Yes | Bot vào `safe_mode`; auto-recovery per FR-EXBOT-050 | — | states.md (I-06 resolved) |
| Stop fail: SAFE_MODE action | Trong `safe_mode`: forbid cancel stop, open position, rebalance; allow: read state, retry HL, alert user/admin | Yes | Bảo vệ vị thế | — | FR-EXBOT-050 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Stop placement thất bại (A8) | State transition + admin notification | "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | E-EXBOT-009 | message-list.md, UC §4 A8 |
| Stop verified, bot active | State transition | `lifecycle_state='stop_verified' → 'active'`; `bots.status='active'` | — | UC §3 step 11 |


---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| `key_status='active'` được ghi vào Aurora PostgreSQL | Preflight check bước 3 của bot-start | Nếu key-provision ghi sai trạng thái → bot-start bị chặn với E-EXBOT-017 | Aurora PostgreSQL `hl_agent_keys.key_status` phải nhất quán giữa key-provision worker và ExBot Lambda | FR-EXBOT-081, UC §3 step 3 |
| `VaultMinted` event on-chain | Aurora PostgreSQL `positions` | `tokenId`, `tickLower`, `tickUpper`, `wethIndex` phải được ghi ngay sau event; nếu Lambda crash trước khi ghi → `lp_opening` state bị kẹt | `queue_idempotency` ngăn duplicate processing; nhưng nếu Lambda crash AFTER on-chain tx BEFORE DB write → trạng thái không nhất quán | FR-EXBOT-011, FR-EXBOT-020 |
| Hedge open thành công → `hedge_post_confirmed` | `hedge_legs` table, `bot_runtime_state` | `entry_price`, `liq_price`, `effective_leverage` được dùng bởi light-check cho margin monitoring | `bot_runtime_state.last_known_hl_short_size` phải cập nhật sau reconcile | FR-EXBOT-023, FR-EXBOT-060 |
| Stop placement thành công → `active` | light-check, hedge-sync bắt đầu chạy | Bot chuyển sang `status='active'` → light-check scan sẽ bao gồm bot này sau 5 phút | `bots.status='active'` phải nhất quán với `bot_registry` trong `control_db` | FR-EXBOT-003, FR-EXBOT-012 |
| Stop placement thất bại → `safe_mode` | FR-EXBOT-050 SAFE_MODE recovery flow | Auto-recovery: HL responsive + 3 successful reconciles + margin_status='ok' → `active` | Nếu recovery thất bại → `bot_safe_close` → `close_operations` được tạo | FR-EXBOT-050, UC §4 A8 |
| Reconcile mismatch (A11) → `partial_repair` enqueued | `partial_repair` queue consumer | Worker tính toán remaining delta, resubmit `adjustShortDelta`; tối đa 3 lần; nếu vẫn thất bại → `bot_safe_close` | `queue_idempotency` row cho mỗi repair attempt; UNIQUE trên `message_id` | FR-EXBOT-023, spec.md §partial_repair |
| Bot active → status visible on POOL UI | Operator API `/api/exbot/status` | Admin có thể query trạng thái bot qua Operator Facade | `bots.status` trong Aurora PostgreSQL là nguồn sự thật; UI chỉ poll | FR-EXBOT-100 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — bot khởi động thành công | User không có ExBot đang tồn tại; HL margin ≥ required × 2.0; `key_status='active'`; builder fee xác nhận | Hệ thống enqueue bot-start sau khi key-provision hoàn tất | `bots.lifecycle_state='active'`; LP NFT giữ bởi BnzaExVault; HL short open; stop placed; Operator API trả về status 'Active' | US-EXBOT-001 AC-1, UC §3, UC §5 |
| AC-02 | One-bot policy chặn bot thứ hai | User đã có ExBot với `status='active'` | Hệ thống cố gắng start bot mới sau deposit | Hệ thống reject với E-EXBOT-001; không tạo bot record mới | US-EXBOT-001 AC-2, BR-EXBOT-001 |
| AC-03 | Margin không đủ chặn bot start | HL margin balance < required × 2.0 | Hệ thống trigger bot-start | Hệ thống block với E-EXBOT-002 với số tiền cụ thể; không tạo bot record | US-EXBOT-001 AC-3, FR-EXBOT-001 |
| AC-04 | key_status không active chặn bot start | `hl_agent_keys.key_status != 'active'` | Hệ thống chạy preflight | Block với E-EXBOT-017; không tạo bot record | UC §3 step 3, FR-EXBOT-081 |
| AC-05 | LP mint thất bại → error state | Preflight pass nhưng `vaultMint` thất bại on-chain | Hợp đồng revert hoặc không emit `VaultMinted` | `lifecycle_state='error'`; tiền được hoàn trả | UC §4 A4, states.md |
| AC-06 | Stop thất bại → safe_mode với auto-recovery | LP minted, hedge open thành công, nhưng stop placement thất bại | Signing Lambda không đặt được stop trên HL | `lifecycle_state='safe_mode'`; operator được thông báo; auto-recovery bắt đầu per FR-EXBOT-050 | UC §4 A8, states.md (I-06 resolved) |
| AC-07 | HL unreachable tại bước hedge → trạng thái đích | Hedge bước đang mở short nhưng HL không phản hồi | HL API timeout/unreachable | **Trạng thái đích chưa xác nhận (I-11 OPEN):** UC §4 A7 ghi `error`; states.md ghi `hedge_pre_open → safe_mode`. Cần BA xác nhận | UC §4 A7 vs states.md |
| AC-08 | Reconcile mismatch → partial_repair | Hedge open thành công nhưng actual size lệch > drift_threshold | Post-order reconcile phát hiện mismatch | `partial_repair` job được enqueue; operator được thông báo; E-EXBOT-011 | UC §4 A11, FR-EXBOT-023 |
| AC-09 | HL IOC reject → trạng thái đích | HL từ chối lệnh IOC (ví dụ: insufficient margin) | Signing Lambda gửi IOC nhưng HL reject | **Trạng thái đích chưa xác nhận (I-11 OPEN):** UC §4 A10 ghi `error`; states.md không có transition `hedge_pre_open → error` cho trường hợp này. Cần BA xác nhận | UC §4 A10 vs states.md |
| AC-10 | Idempotency: duplicate bot-start message | SQS redelivers bot-start message | ExBot Lambda xử lý message lần 2 | Consumer detect UNIQUE conflict trên `queue_idempotency.message_id` → thoát im lặng; không tạo duplicate bot | FR-EXBOT-011 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Throughput: 10,000 bots / 5-min scan = 33.3 bots/sec (cho light-check phase); bot-start latency không được định nghĩa riêng trong tài liệu | Bot-start không trực tiếp ảnh hưởng; nhưng DB write throughput cần đủ cho scale | FR-EXBOT-110, NFR-EXBOT-001 |
| Latency | 1 hedge-sync < 30s (FR-EXBOT-002); không có SLA cho bot-start initialization | Kiểm tra xem bot có vào `active` trong thời gian chấp nhận được không | NFR-EXBOT-002 |
| Security | Private key không bao giờ rời KMS HSM; chỉ Signing Lambda có IAM `kms:Sign`; không có key material trong memory/logs | Kiểm tra log không chứa private key; Signing Lambda request phải đi qua IAM role đúng | NFR-EXBOT-006, FR-EXBOT-081 |
| Reliability / Resilience | KMS retry max 3 lần; HL approveAgent retry qua queue; SQS consumer idempotency (FR-EXBOT-011); `partial_repair` max 3 lần sau đó bot_safe_close | Test failure-recovery cho từng step; test duplicate delivery handling | FR-EXBOT-011, FR-EXBOT-081 |
| Audit / Logging | `queue_idempotency` row cho mỗi message; `rebalance_attempts` cho reconcile; `hl_agent_keys` rows là immutable (không xóa, không overwrite) | Kiểm tra audit trail đầy đủ sau mỗi bước | BR-EXBOT-013, FR-EXBOT-011 |
| Privacy / Compliance | Private key không bao giờ xuất ra (NFR-EXBOT-006); key rotation immutable audit log | Test không thể trích xuất private key qua API | NFR-EXBOT-006, BR-EXBOT-013 |
| Compatibility / Integration | HL API rate limit: 800 weight/min (67% của 1200 hard limit); KMS rate limit: backoff on ThrottlingException | Kiểm tra rate limiter hoạt động đúng khi nhiều bot start song song | FR-EXBOT-090, FR-EXBOT-081 |


---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận (Issue Register)

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-11 | High | CROSS_SOURCE_CONFLICT (Blocker) | UC §4 A7 vs `srs/states.md` dòng `hedge_pre_open → safe_mode`; UC §4 A10 cùng conflict | UC §4 A7 mô tả "HL unreachable tại bước hedge → enter `error` state". UC §4 A10 mô tả "HL reject IOC → enter `error` state". Nhưng `srs/states.md` chỉ định nghĩa transition hợp lệ là `hedge_pre_open → safe_mode` khi "HL order fails" — không có transition `hedge_pre_open → error` trong state machine. Tài liệu UC đã được cập nhật 2026-07-04 nhưng conflict vẫn còn. BA vui lòng xác nhận: khi HL unreachable hoặc IOC bị reject tại bước hedge open, trạng thái đích chính xác là `error` hay `safe_mode`? | Tester không thể viết expected result cho AC-07, AC-09. Nếu dùng sai state → test case pass/fail sai → rủi ro bỏ sót lỗi production | BA (@hienduong) | Open |
| I-12 | Medium | MISSING_INFO | UC §4 A7 ("enter `error` state; return 'HL service unavailable, please retry'"); UC §4 A10 ("enter `error` state; return HL rejection reason") | Message content cho A10 chưa được resolve thành mã lỗi cụ thể từ `message-list.md`. E-EXBOT-008 cover A7 ("HL unreachable → safe_mode"), nhưng không có error code nào cover trường hợp "HL IOC order rejected" riêng biệt trong `message-list.md`. Nếu destination state là `safe_mode` (sau khi I-11 giải quyết), E-EXBOT-008 có phù hợp không? | Test case không thể verify đúng message code khi HL reject IOC | BA (@hienduong) | Open |
| I-13 | Medium | MISSING_INFO | UC §7 FR Trace; `srs/spec.md` | UC §7 FR Trace chỉ liệt kê FR-EXBOT-001, 002, 004, 020, 030, 031. Các FR sau không được trace mặc dù trực tiếp liên quan đến bot-start flow: (1) FR-EXBOT-003 — state tracking (khởi tạo sequence idle→preflight→...→active); (2) FR-EXBOT-011 — queue consumer idempotency (dedup message bot-start); (3) FR-EXBOT-081 — KMS key provisioning (toàn bộ key-provision worker); (4) FR-EXBOT-091 — HL rate limiter (áp dụng cho hedge open). FR trace không đầy đủ khiến tester bỏ sót các yêu cầu quan trọng khi cross-check. | Không block test design nhưng làm tăng rủi ro bỏ sót coverage | BA (@hienduong) | Open |
| I-14 | Low | UNCLEAR_INFO | `srs/erd.md` dòng `hl_agent_keys` (updated 2026-07-04) | ERD `hl_agent_keys` sau arc-migration (2026-07-04) annotate 9 trường là RETIRED, giữ lại `expires_at` và `rotated_from`. Nhưng trường `key_status` — trường quan trọng nhất của table (3-state: `active`/`superseded`/`revoked`) — không được liệt kê rõ ràng trong danh sách active fields của ERD. Note cuối ERD nói "Table holds per-user key metadata and `key_status` only" nhưng không có định nghĩa field type/constraint trong ERD format (như các trường khác). BA vui lòng xác nhận `key_status` vẫn là `TEXT` NOT NULL với UNIQUE constraint `active` per user (BR-EXBOT-012), và mô tả đầy đủ trong ERD. | Nếu `key_status` definition bị mơ hồ → test case về preflight check không thể verify schema constraint đúng | BA (@hienduong) | Open |
| I-15 | Low | UNCLEAR_INFO | `srs/spec.md §FR-EXBOT-081`; UC §4 A7 | FR-EXBOT-081 mô tả "KMS failure during key generation → abort, retry max 3, admin alert". Nhưng không định nghĩa: (1) Nội dung message thông báo admin là gì? (2) Admin được alert qua kênh nào (notification queue? webhook? email?)? (3) Sau khi max retry hết → bot-start có bao giờ được tự động retry hay user phải deposit lại? | Thiếu thông tin này không block test design chính nhưng ảnh hưởng đến coverage của negative path KMS failure | BA / Tech Lead | Open |
| I-16 | Low | INTERNAL_INCONSISTENCY | `userstories/us-001.md` Notes section vs `srs/states.md` | US-EXBOT-001 Notes ghi: "`cooldown` and `parked` lifecycle states map to `status='active'`". Nhưng `srs/states.md` (updated 2026-06-18) đã remove `cooldown` và `parked` states khỏi state machine hoàn toàn. US-001 Notes chưa được cập nhật tương ứng. Mặc dù không block bot-start testing, nhưng gây hiểu nhầm về scope of one-bot policy (US-001 AC-2 mentions `status IN ('active','paused','closing','safe_mode','error')` — đúng, nhưng Notes vẫn đề cập states đã bị xóa). | Có thể gây hiểu nhầm cho tester mới; cần cleanup | BA (@hienduong) | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-11: công thức `lpValueUsd` | Requirement gap | Ảnh hưởng `drift_threshold = max($25, lpValueUsd × 3%)` trong reconcile mismatch detection (AC-08) | BA / Tech Lead | Open (chưa đóng theo spec.md) |
| Nội dung admin alert message cho KMS failure | Missing info | Ảnh hưởng test case cho KMS unavailable path (I-15) | BA | Open |
| Xác nhận I-11: `hedge_pre_open → error` hay `safe_mode` | Cross-source conflict | Blocks AC-07, AC-09 test design | BA (@hienduong) | Open |

---

## 10.3 Audit Summary và Kết quả điểm

### Scoring Table

| # | Khu vực đánh giá | Điểm tối đa | Trạng thái | Vấn đề | Điểm đạt |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | ⚠️ Partial | FR trace trong UC không đầy đủ (I-13): thiếu FR-EXBOT-003, FR-EXBOT-011, FR-EXBOT-081, FR-EXBOT-091. ERD `key_status` field không được mô tả rõ ràng sau arc-migration (I-14). Nhưng SRS (spec.md, states.md, flows.md, erd.md) cung cấp đủ thông tin để lập inventory. | 15/20 |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | ⚠️ Partial | I-11 (Blocker): trạng thái đích `hedge_pre_open` khi HL fails là `error` (UC) hay `safe_mode` (states.md)? Conflict chưa giải quyết ảnh hưởng 2 AC. I-12: message code cho IOC reject (A10) chưa được resolve. Phần còn lại (preflight rules, stop formula, idempotency, SAFE_MODE triggers) được mô tả đầy đủ trong SRS. Cap: Blocker → affected area max 40%. | 15/25 |
| 3 | Functional Logic & Workflow Decomposition | 25 | ⚠️ Partial | Happy path và hầu hết alt/exception paths có tài liệu đầy đủ. I-11 làm 2 exception paths (A7, A10) chưa hoàn chỉnh. Admin alert mechanism (KMS failure, I-15) và message content (IOC reject, I-12) chưa rõ. Cap: Blocker → max 40%. | 17/25 |
| 4 | Functional Integration & Data Consistency | 15 | ⚠️ Partial | Các on-chain↔off-chain effects (VaultMinted→DB, reconcile→hedge_legs) được mô tả tốt. Tiềm năng inconsistency nếu Lambda crash giữa on-chain tx và DB write chưa được UC đề cập (nhưng FR-EXBOT-011 cover idempotency ở level queue). Dependency OQ-EXBOT-11 ảnh hưởng `drift_threshold` computation. | 11/15 |
| 5 | UC / Spec Documentation Quality Issues | 15 | ⚠️ Partial | I-11 (Blocker conflict), I-13 (FR trace thiếu), I-16 (stale US Notes). Nhưng UC được viết rõ ràng, cấu trúc tốt, ngôn ngữ không ambiguous (ngoại trừ conflict I-11). Cap: unresolved contradiction → max 8/15. | 7/15 |
| **Tổng** | | **100** | | | **65/100** |

**Áp dụng auto-cap:** I-11 là Blocker trong Area 2 và 3 (unresolved contradiction affects critical function behavior). Cap Area 2 ≤ 40% = 10/25; Area 3 ≤ 40% = 10/25. Area 5 ≤ 8/15 (unresolved contradiction across sources).

| # | Khu vực | Max | Điểm sau cap |
|---|---|---|---|
| 1 | Inventory | 20 | 15 |
| 2 | Data/State/Rules | 25 | 10 (capped at 40%) |
| 3 | Logic/Workflow | 25 | 10 (capped at 40%) |
| 4 | Integration/Consistency | 15 | 11 |
| 5 | Documentation Quality | 15 | 7 (capped) |
| **Tổng** | | **100** | **53/100** |

### Blockchain UC Readiness Checklist (§6b)

| # | Tiêu chí | Trạng thái | Ghi chú |
|---|---|---|---|
| B1 | Agent key states & messages | ⚠️ Partial | 3-state key_status được mô tả đầy đủ trong states.md; E-EXBOT-017 resolved. Nhưng ERD thiếu explicit field definition cho `key_status` (I-14). |
| B2 | Signing behavior | ✅ Clear | SRS F-03 + FR-EXBOT-081 mô tả rõ Signing Lambda, kms:Sign, cloid idempotency. |
| B3 | Required network/chain | ✅ Clear | FR-EXBOT-004: Base + Optimism, `wethIndex` per chain. |
| B4 | Transaction lifecycle | ⚠️ Partial | Happy path rõ; A7/A10 destination state chưa xác nhận (I-11). |
| B5 | Pre-flight rules (gas, allowance) | ✅ Clear | UC §2 liệt kê ERC-20 allowance và native gas. |
| B6 | Mid-flow events (key change, circuit breaker) | ⚠️ Partial | FR-EXBOT-050 SAFE_MODE triggers đầy đủ; nhưng không có explicit mid-flow key change scenario trong UC. |
| B7 | On-chain ↔ off-chain consistency | ✅ Clear | VaultMinted → DB write được mô tả; reconcile protocol (FR-EXBOT-023) đầy đủ. |
| B8 | Error/success messages | ⚠️ Partial | Hầu hết messages resolved; I-12 (IOC reject message) chưa resolve. |
| B9 | Security expectations | ✅ Clear | NFR-EXBOT-006 + FR-EXBOT-081 mô tả rõ: không có key material ngoài KMS. |

### Verdict

| Điểm | Verdict |
|---|---|
| **53/100** | **NOT READY** |

**Lý do NOT READY:** I-11 là Blocker chưa được giải quyết — UC A7/A10 khai báo `error` state nhưng state machine (`srs/states.md`) chỉ định nghĩa `hedge_pre_open → safe_mode`. Conflict này ảnh hưởng trực tiếp đến 2 AC quan trọng (hedge fail scenarios) và triggers auto-cap cho các khu vực điểm liên quan. Khi I-11 được giải quyết, score ước tính sẽ tăng lên khoảng 70-75/100 (Conditionally Ready).

**Các blockers cần giải quyết trước khi proceed:**
1. **I-11 (Critical):** BA xác nhận trạng thái đích khi HL fails tại `hedge_pre_open`: `error` hay `safe_mode`? Cập nhật UC §4 A7/A10 cho nhất quán với `srs/states.md`.
2. **I-12 (Supporting):** Sau khi I-11 giải quyết, xác định error code và message content cho IOC reject scenario.

**Recommendation:** Sau khi BA cập nhật UC §4 A7/A10 theo kết quả I-11, agent có thể proceed với scenario design và test case design cho phần còn lại (happy path, preflight failures, stop_placing→safe_mode). Không nên đợi I-11 để test các path khác — chỉ các case về hedge failure cần tạm thời đánh dấu blocked.


---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read ExBot Agent | Tạo báo cáo audited lần đầu |
| v2 | 2026-07-02 | QC UC Read ExBot Agent | I-06 resolved (stop_placing → safe_mode); I-03 resolved; I-11 mới phát hiện (hedge_pre_open destination state conflict) |
| v3 | 2026-07-06 | QC UC Read ExBot Agent | Re-audit với tài liệu mới nhất (arc-migration 2026-07-04): toàn bộ SRS/UC/FRD đã cập nhật AWS primitives. I-11 vẫn open. Phát hiện thêm I-12 (IOC reject message), I-13 (FR trace thiếu), I-14 (ERD key_status), I-15 (KMS alert message), I-16 (US stale notes). Verdict: NOT READY (53/100, I-11 Blocker). |

