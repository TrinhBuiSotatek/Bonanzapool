---
title: "UC-EXBOT-bot-start — Báo cáo đánh giá sẵn sàng (v4)"
uc_id: UC-EXBOT-bot-start
feature: bot-start
date_created: 2026-06-26
author: qc-uc-read-exbot agent
version: v2
output_language: vi+en
srs_baseline: 2026-06-18
uc_version: 2026-06-20
---

# Báo Cáo Đánh Giá Mức Độ Sẵn Sàng của Use Case

**UC-EXBOT-bot-start — Khởi tạo ExBot: preflight → mint LP → mở hedge HL → đặt stop → active**

> **Ghi chú tái đánh giá (v4):** Đây là lần tái đánh giá thứ hai (v4) đối với UC-EXBOT-bot-start sau khi BA cập nhật tài liệu ngày 2026-06-20. Báo cáo này sử dụng cấu trúc đầy đủ như v1, ghi lại toàn bộ phân tích SRS baseline vs UC/US, bao gồm các phát hiện từ v2 (re-audit 57/100) và xác minh lại trạng thái các vấn đề còn mở.

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + vai trò trong dự án | Defined in |
|---|---|---|
| ExBot | Managed delta-hedged LP Bot — bot quản lý vị thế cung cấp thanh khoản Uniswap V3 trên cặp USDC/WETH kèm vị thế short ETH-USD perpetual trên Hyperliquid để triệt tiêu rủi ro giá ETH. ExBot chạy ở backend Cloudflare Worker `apps/bnza-exbot/`, không có UI riêng. | FRD §1 + SRS spec.md §1 |
| LP | Liquidity Provider — nhà cung cấp thanh khoản Uniswap V3 USDC/WETH. Trong dự án này, LP NFT được mint qua `BnzaExVault.vaultMint()` và luôn được giữ trong vault; `tokenId` được lưu trong bảng `positions`; nhà đầu tư không bao giờ nắm giữ NFT trực tiếp. | (industry term) |
| HL | Hyperliquid — sàn perpetual on-chain dùng để mở vị thế short ETH-USD. ExBot giao tiếp với HL qua REST API có rate-limit (NFR-EXBOT-004). | (proper noun) |
| FR-EXBOT-NNN | Yêu cầu chức năng — module ExBot. **Cảnh báo:** cùng prefix `FR-EXBOT-NNN` xuất hiện ở cả `frd.md` và `srs/spec.md` nhưng trỏ tới hai nội dung khác nhau. Tất cả trace trong báo cáo này đều tham chiếu `srs/spec.md` là nguồn chuẩn. | `srs/spec.md` + `frd.md` |
| BR-EXBOT-NNN | Business Rule của ExBot. Được định nghĩa trong `srs/spec.md §4` (KHÔNG nằm trong `02_backbone/common-rules.md`). | `srs/spec.md §4` |
| E-EXBOT-NNN | Error code của ExBot. Thông báo nguyên văn hiển thị cho người dùng. Định nghĩa trong `srs/spec.md §5` (KHÔNG nằm trong `02_backbone/message-list.md`). | `srs/spec.md §5` |
| OQ-EXBOT-NN | Open Question — câu hỏi thiết kế chưa chốt, theo dõi trong `srs/spec.md §9`. | `srs/spec.md §9` |
| BnzaExVault | Smart contract Solidity custodian LP NFT và xử lý `vaultMint`/`redeem`. SOTATEK chỉ tích hợp qua ABI (ABI cuối cùng chưa confirmed — OQ-EXBOT-08). | FRD §3 + SRS §1.3 |
| Cloid | Client Order ID — chuỗi 128-bit hex deterministic: `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. Dùng để khử trùng lặp lệnh HL. | SRS FR-EXBOT-024 |
| IOC | Immediate-Or-Cancel — loại lệnh HL: khớp ngay nếu có thể, hủy phần còn lại. | (industry term) |
| AES-256-GCM | Thuật toán mã hóa xác thực. Dùng cho envelope encryption agent key HL: DEK mã hóa agent key, master key (Cloudflare Secrets Store) wrap DEK. | NFR-EXBOT-006 + FR-EXBOT-080 |
| DEK | Data Encryption Key — khoá AES per-row dùng để mã hoá agent key. Lưu dạng `wrapped_dek` trong bảng `hl_agent_keys`. | SRS FR-EXBOT-080 |
| BigDecimal | Thư viện tính toán thập phân với độ chính xác tùy ý. Tất cả tính toán tài chính PHẢI dùng BigDecimal (NFR-EXBOT-008). | NFR-EXBOT-008 |
| D1 | Cloudflare D1 — cơ sở dữ liệu edge tương thích SQLite. Dự án tách `control_db` (1 global) và `state_db_shard_xx`. | FRD §4.9 |
| DO | Durable Object — đối tượng trạng thái dài hạn Cloudflare Workers. Dự án có `HLRateLimitDO`, `UserLockDO`, `MarketDataDO`. | FRD §4.10 |
| HLRateLimitDO | DO thi hành rate-limit sliding-window cho tất cả call HL API (ngân sách 800 weight/min). | SRS FR-EXBOT-091 |
| UserLockDO | DO cấp lease 90s chống concurrent HL mutation cho cùng user. | SRS FR-EXBOT-092 |
| MarketDataDO | DO cache giá pool Uniswap V3 (`sqrtPriceX96`, `currentTick`, `blockNumber`). | SRS FR-EXBOT-093 |
| SAFE_MODE | Trạng thái lifecycle cấm mutation nhưng cho phép read/retry/alert. Không phải terminal — phải dẫn đến auto-recovery hoặc `bot_safe_close`. | SRS FR-EXBOT-050; BR-EXBOT-007 |
| Stop / Stop Trigger | Lệnh stop reduce-only đặt trên HL để đóng vị thế hedge khi giá vượt ngưỡng. Tính bằng BigDecimal: `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`. Phase A `stopSafetyFactor = 0.70`. | SRS FR-EXBOT-030 |

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả luồng khởi tạo một con ExBot mới cho nhà đầu tư USDC. ExBot là dịch vụ backend chạy trên Cloudflare Worker, không có UI riêng; nhà đầu tư kích hoạt luồng qua `POST /api/exbot/start` thông qua OPERATOR Facade, OPERATOR forward sang ExBot Worker qua Cloudflare service binding.

Luồng nghiệp vụ chính: ExBot Worker chạy 5 preflight check tuần tự — (1) one-bot-per-user policy; (2) HL isolated margin ≥ required × 2.0; (3) HL agent key đã `approved` và chưa hết hạn; (4) builder fee 5bps đã confirmed; (5) LP mint simulation pass. Nếu mọi check pass, hệ thống tạo bản ghi bot (`lifecycle_state='preflight'`), gọi `BnzaExVault.vaultMint(...)` để mint LP NFT, mở HL short IOC với `targetShortEth = lpEthAmount × hedgeRatio` (Phase A = 0.70), thực hiện post-order reconcile, tính `stop_trigger_px` bằng BigDecimal với `stopSafetyFactor = 0.70`, đặt reduce-only stop market, và chuyển sang `active`. Toàn bộ chuỗi 8 trạng thái được persist nguyên tử vào D1 tại mỗi bước.

Các yếu tố kỹ thuật và nghiệp vụ ảnh hưởng đến thiết kế kiểm thử: (1) BR-EXBOT-001 — Phase A 1 user = 1 active ExBot, tính cả `active/paused/closing/safe_mode/error`; (2) BR-EXBOT-010 — ExBot Worker tách deploy với OPERATOR; (3) NFR-EXBOT-008 — BigDecimal bắt buộc cho mọi tính toán tài chính; (4) FR-EXBOT-050 — lỗi HL dẫn đến `safe_mode`, KHÔNG phải `error`; (5) FR-EXBOT-080 — agent key lưu AES-256-GCM, plain key chỉ tồn tại trong scope hàm. UC liên kết trực tiếp với UC-EXBOT-light-check (bắt đầu giám sát trong 5 phút sau `active`) và UC-EXBOT-bot-safe-close.

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả luồng khởi tạo một con ExBot mới cho nhà đầu tư USDC. ExBot là dịch vụ backend chạy trên Cloudflare Worker, không có UI riêng; nhà đầu tư kích hoạt luồng qua `POST /api/exbot/start` thông qua OPERATOR Facade, OPERATOR forward sang ExBot Worker qua service binding.

Luồng nghiệp vụ chính: ExBot Worker chạy 5 preflight check tuần tự — (1) one-bot-per-user policy; (2) HL isolated margin ≥ required × 2.0; (3) HL agent key `approved` và chưa hết hạn; (4) builder fee 5bps đã confirmed; (5) LP mint simulation pass. Nếu mọi check pass, hệ thống tạo bản ghi bot (`lifecycle_state='preflight'`), gọi `BnzaExVault.vaultMint(...)` để mint LP NFT, mở HL short IOC với `targetShortEth = lpEthAmount × hedgeRatio` (Phase A = 0.70), thực hiện post-order reconcile, tính `stop_trigger_px` bằng BigDecimal với `stopSafetyFactor = 0.70`, đặt reduce-only stop market, và chuyển sang `active`. Chuỗi 8 trạng thái được persist nguyên tử vào D1 tại mỗi bước.

Yếu tố kỹ thuật và nghiệp vụ ảnh hưởng đến thiết kế kiểm thử: BR-EXBOT-001 (1 user = 1 active ExBot, tính cả `active/paused/closing/safe_mode/error`); BR-EXBOT-010 (ExBot Worker tách deploy với OPERATOR); NFR-EXBOT-008 (BigDecimal bắt buộc); FR-EXBOT-050 (lỗi HL → `safe_mode`, KHÔNG phải `error`); FR-EXBOT-080 (agent key lưu AES-256-GCM). UC liên kết với UC-EXBOT-light-check (bắt đầu giám sát trong 5 phút sau `active`) và UC-EXBOT-bot-safe-close.

---

## Tóm tắt đánh giá (Re-audit v2)

| Trường | Giá trị |
|---|---|
| Lần đánh giá trước | v1 (2026-06-17): điểm 52/100, NOT READY |
| UC baseline đánh giá | v1 (2026-06-20) — BA cập nhật thêm A5–A11, đặt tên `hedgeRatio`/`stopSafetyFactor`, xác nhận preconditions on-chain |
| Lần đánh giá này | v4 (2026-06-26) — Re-audit đầy đủ cấu trúc, cross-check SRS vs UC/US |
| Điểm | **57/100** |
| Kết luận | **NOT READY** |
| Blocker | I-01: 4 alternate flow dùng sai terminal state `error` thay vì `safe_mode` |

Điểm cải thiện từ 52 → 57 (tăng 5 điểm) sau khi BA bổ sung 7 alternate flow mới và đặt tên rõ 2 tham số 0.70. Tuy nhiên tồn đọng 1 Blocker và 5 Major issues cản trở thiết kế test đúng.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version UC đang đánh giá | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-start | Start ExBot (preflight + LP mint + hedge open + stop place) | Cập nhật 2026-06-20 bởi BA | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| `@hienduong` | (chưa có) | 2026-06-12 | 2026-06-20 |

| Artefact đã đọc | Version / last updated | Vai trò | Ghi chú |
|---|---|---|---|
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-bot-start.md` | 2026-06-20 | UC chính cần audit | changelog: A5-A11 added, step 7/10 named params, A3 verbatim fix (claimed), on-chain preconditions added |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usercases/index.md` | — | Index UC + FR trace | — |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-001.md` | 2026-06-12 (chưa cập nhật) | US gắn UC | 4 AC: happy + 3 negative; Notes section tham chiếu `cooldown`/`parked` (stale sau HLD-2026-06-18) |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/spec.md` | v5.2.6 / 2026-06-20 | SRS — nguồn truth hành vi bot | changelog 2026-06-20: OQ-EXBOT-13/14/15/16/17 added; 2026-06-18: FR-070/071/073 update, drop park/re-entry |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/states.md` | 2026-06-18 | State machine | `cooldown` và `parked` đã xoá; `bot_safe_close → closed` trực tiếp |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/flows.md` | 2026-06-12 (chưa cập nhật sau HLD) | Sequence flows | F-05 vẫn còn stale text (cần kiểm tra lại) |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/erd.md` | 2026-06-12 | ERD D1 | Cung cấp tên field cụ thể cho bots/positions/hedge_legs |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/frd.md` | v0.1.0 / 2026-06-18 | FRD | changelog 2026-06-18: ACT-M removed; bot_safe_close drop park/re-entry |
| `docs/BA/plans/bnza-sotatek-260519-0000/02_backbone/common-rules.md` | 2026-06-09 | Common Rules registry | KHÔNG chứa BR-EXBOT-* |
| `docs/BA/plans/bnza-sotatek-260519-0000/02_backbone/message-list.md` | 2026-06-09 | Message registry | KHÔNG chứa E-EXBOT-* |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả luồng khởi tạo một con ExBot mới cho nhà đầu tư USDC. ExBot là dịch vụ backend chạy trên Cloudflare Worker, không có UI riêng; nhà đầu tư kích hoạt luồng qua `POST /api/exbot/start` thông qua OPERATOR Facade, OPERATOR forward sang ExBot Worker qua service binding.

Luồng nghiệp vụ chính: ExBot Worker chạy 5 preflight check tuần tự — (1) one-bot-per-user policy; (2) HL isolated margin ≥ required × 2.0; (3) HL agent key `approved` và chưa hết hạn; (4) builder fee 5bps đã confirmed; (5) LP mint simulation pass. Nếu mọi check pass, hệ thống tạo bản ghi bot (`lifecycle_state='preflight'`), gọi `BnzaExVault.vaultMint(...)` để mint LP NFT, mở HL short IOC với `targetShortEth = lpEthAmount × hedgeRatio` (Phase A = 0.70), thực hiện post-order reconcile, tính `stop_trigger_px` bằng BigDecimal với `stopSafetyFactor = 0.70`, đặt reduce-only stop market, và chuyển sang `active`. Chuỗi 8 trạng thái được persist nguyên tử vào D1 tại mỗi bước.

Yếu tố ảnh hưởng thiết kế kiểm thử: BR-EXBOT-001 (1 user = 1 active ExBot, tính cả `active/paused/closing/safe_mode/error`); BR-EXBOT-010 (ExBot Worker tách deploy với OPERATOR); NFR-EXBOT-008 (BigDecimal bắt buộc); FR-EXBOT-050 (lỗi HL → `safe_mode`, KHÔNG phải `error`); FR-EXBOT-080 (agent key AES-256-GCM). UC liên kết với UC-EXBOT-light-check (giám sát trong 5 phút sau `active`) và UC-EXBOT-bot-safe-close.

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này cho phép nhà đầu tư USDC khởi tạo ExBot mới — bot tự động vị thế LP delta-hedged USDC/WETH. Mục tiêu: đặt vốn USDC sinh phí LP Uniswap V3, đồng thời vị thế short ETH-USD perpetual trên HL triệt tiêu rủi ro giá ETH. Kết quả mong đợi: bản ghi bot `lifecycle_state='active'`, LP do BnzaExVault custodian, HL hedge với stop đã đặt.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Endpoint `POST /api/exbot/start` (OPERATOR Facade) | Nhận request từ POOL UI, internal-token auth, forward sang ExBot Worker qua service binding | UC §3.1-3.2; SRS FR-EXBOT-090 |
| Preflight check 1 — one-bot policy | Query `bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')`; count > 0 → reject E-EXBOT-001 | UC §3.3, A1; SRS FR-EXBOT-001 |
| Preflight check 2 — HL margin | Verify `marginBalanceUsd ≥ marginRequired × 2.0` với `marginRequired = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage` | UC §3.3, A2; SRS FR-EXBOT-002 + FR-EXBOT-061 |
| Preflight check 3 — agent key | Check `approval_status='approved'` AND `expires_at > now`; pending → E-EXBOT-003; expired → E-EXBOT-004 | UC §2, A3, A9; SRS FR-EXBOT-081 + FR-EXBOT-083 |
| Preflight check 4 — builder fee | Builder fee 5bps confirmed; chưa → E-EXBOT-005 (cơ chế pending OQ-EXBOT-05) | UC §2, A5; SRS FR-EXBOT-002 step 4 |
| Preflight check 5 — LP mint simulation | Simulate `BnzaExVault.vaultMint`; fail → E-EXBOT-006 | UC §3.3, A6; FRD FR-EXBOT-001 step 5 |
| Tạo bot record `lifecycle_state='preflight'` | Insert `bots`, `bot_registry`; populate `chain`, `wallet_address` | UC §3.4; ERD `bots`, `bot_registry` |
| Vault mint LP NFT | `BnzaExVault.vaultMint(...)` → emit `VaultMinted(user, botId, tokenId, liquidity)` | UC §3.5; SRS flows.md F-03 |
| Populate `positions` row | Insert `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `liquidity`, `pool_address`, `custodian='vault'` | UC §3.6; ERD `positions` |
| Transition `lp_opening → lp_opened` | Atomic D1 write khi event `VaultMinted` được xác nhận | UC §3.6; states.md |
| Open HL short IOC | `targetShortEth = lpEthAmount × hedgeRatio (Phase A=0.70)`; submit `openShortIoc(targetSize, cloid)` | UC §3.7; SRS FR-EXBOT-021 + FR-EXBOT-024 |
| Post-order reconcile | Fetch `clearinghouseState`, verify size, extract `entry_price`, `liquidation_price`, `effective_leverage` | UC §3.8; SRS FR-EXBOT-025 |
| Compute `stop_trigger_px` | BigDecimal: `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`, Phase A `stopSafetyFactor=0.70` | UC §3.10; SRS FR-EXBOT-030 |
| Place reduce-only stop market | `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)`; transition `stop_placing → stop_verified` | UC §3.10-11; SRS FR-EXBOT-031 |
| Transition `stop_verified → active` | Set `lifecycle_state='active'`, `status='active'`; return `{status: active, botId}` | UC §3.11-12; FR-EXBOT-003 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do | Ảnh hưởng đến test |
|---|---|---|
| Logic chiến thuật (PositionCalc, hedge math, stopSafetyFactor tuning) | Zen-proprietary | Tester chỉ verify input/output interface |
| Phát triển contract BnzaExVault | Zen scope; SOTATEK tích hợp qua ABI (pending OQ-EXBOT-08) | Phải dùng deploy thử nghiệm |
| Pause / Resume (FR-EXBOT-005) | UC riêng; index đã ghi nhầm FR-003 vào trace | Test bot-start KHÔNG cover pause/resume |
| Cơ chế confirm builder fee 5bps | Chưa chốt — OQ-EXBOT-05 | Test preflight step 4 phụ thuộc OQ này |
| Nguồn `lpEthAmount` trước mint | UC không nói rõ công thức trước-mint | Không thể verify hedge size đầu-cuối |
| Chain selector trong payload `POST /api/exbot/start` | UC không mô tả request body | Không thể verify Base vs Optimism |
| Slippage tolerance cụ thể | UC nói "passes" không có ngưỡng | Không biết expected result edge case |
| Idempotency cho `POST /api/exbot/start` | UC không đề cập lock/idempotency | Race-condition expected behavior không rõ |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| `USDC Investor` | Primary | Gửi request start qua POOL UI; sở hữu HL account + agent key approved | Phase A: 1 active ExBot per user (BR-EXBOT-001); HL isolated margin ≥ required × 2.0 | UC §1; SRS FR-EXBOT-001 |
| OPERATOR Facade | System (thin proxy) | Nhận `POST /api/exbot/start`, internal-token auth, forward qua service binding | Không sở hữu business logic; chỉ proxy (BR-EXBOT-010) | UC §1; SRS FR-EXBOT-090 |
| ExBot Worker | System (Cloudflare Worker `apps/bnza-exbot/`) | Chạy preflight, gọi Vault, gọi HL, đặt stop, cập nhật D1 | KHÔNG public internet; deploy tách biệt OPERATOR (BR-EXBOT-010) | UC §1; SRS FR-EXBOT-090 |
| BnzaExVault | External (Solidity contract) | Mint LP NFT, custodian LP, emit `VaultMinted` | ABI cuối chưa confirmed (OQ-EXBOT-08) | UC §1; SRS IC-EXBOT-002 |
| Hyperliquid | External | Khớp `openShortIoc`, trả `clearinghouseState`, khớp `placeReduceOnlyStopMarket` | Rate limit 800 weight/min (NFR-EXBOT-004); HL unreachable → SAFE_MODE (FR-EXBOT-050) | UC §1; SRS FR-EXBOT-091 |
| ExBot Admin (zen) | Out-of-scope | Approve agent key tách biệt (precondition) | Không tham gia main flow | FRD ACT-A; UC §2 |

**Nhận xét readiness:**

Actor primary và system actor đã rõ ở mức happy path. Tuy nhiên FRD §4.11 ghi `Actor=Admin` cho cả 5 Operator Facade endpoint, trong khi UC §1 ghi primary actor là `USDC Investor` — mâu thuẫn chưa được BA giải quyết (Q15 từ v1 vẫn Open). Tester không biết ai gọi `/api/exbot/start` trực tiếp, ảnh hưởng test role-based access.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | User KHÔNG có ExBot khác đang `status IN ('active','paused','closing','safe_mode','error')` | Yes | UC §2; SRS BR-EXBOT-001; FR-EXBOT-001 |
| 2 | User có HL account với isolated margin ≥ required × 2.0 | Yes | UC §2; SRS FR-EXBOT-061 |
| 3 | HL agent key `approval_status='approved'` AND `expires_at > now` | Yes | UC §2; SRS FR-EXBOT-081 + FR-EXBOT-083 |
| 4 | HL builder fee 5bps đã confirmed (cơ chế pending OQ-EXBOT-05) | Yes | UC §2; SRS FR-EXBOT-002 step 4 |
| 5 | LP mint simulation pass (ngưỡng slippage cụ thể chưa nêu) | Yes | UC §3.3 preflight step 5 |
| 6 | User đã approve USDC cho BnzaExVault ≥ deposit amount (ERC-20 allowance) | Yes (thêm ở UC 2026-06-20) | UC §2 |
| 7 | User có đủ native ETH để trả gas cho on-chain tx `vaultMint` | Yes (thêm ở UC 2026-06-20) | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau | Nguồn |
|---|---|---|
| Khởi tạo bot thành công (happy path) | `bots.lifecycle_state='active'`, `bots.status='active'`; bản ghi `positions` với `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `custodian='vault'`; bản ghi `hedge_legs` với `entry_price`, `liquidation_price`, `effective_leverage`, `stop_price`, `stop_cloid`, `stop_order_id`, `stop_size`, `stop_distance_pct`, `stop_last_verified_at`; bản ghi `bot_runtime_state` với `last_known_hl_short_size`, `next_light_check_at = now + 5min + jitter(±45s)`; `circuit_breakers.state='closed'`; API trả `{status: active, botId}` | UC §5; SRS FR-EXBOT-003 + FR-EXBOT-025 + FR-EXBOT-013 + FR-EXBOT-040 |
| Fail preflight (A1/A2/A3/A5/A6/A9) | Không tạo bản ghi `bots`; response trả error message tương ứng | UC §4 A1-A3, A5, A6, A9; SRS FR-EXBOT-001 + FR-EXBOT-002 |
| Fail LP mint thực tế sau khi tạo bản ghi (A4) | `bots.lifecycle_state='error'`; cơ chế "return funds" chưa rõ (I-08) | UC §4 A4; states.md `lp_opening → error` |
| HL unreachable giữa hedge open (A7) | UC ghi `error` — **SAI; SRS: `safe_mode`** (I-01) | UC §4 A7; states.md `hedge_pre_open → safe_mode` |
| Stop placement fail (A8) | UC ghi `error` — **SAI; SRS: `safe_mode`** (I-01) | UC §4 A8; states.md `stop_placing → safe_mode` |
| HL IOC reject (A10) | UC ghi `error` — **SAI; SRS: `safe_mode`** (I-01) | UC §4 A10; states.md `hedge_pre_open → safe_mode` |
| Reconcile mismatch (A11) | UC ghi không rõ terminal state + `partial_repair` enqueue (I-09) | UC §4 A11; SRS FR-EXBOT-050 |

**Lưu ý:** `bot_runtime_state` row và `circuit_breakers` row được khởi tạo khi chuyển sang `active` chưa được nêu trong UC §5 Postconditions (I-06).

**BR verbatim được resolve từ `srs/spec.md §4`:**

```text
BR-EXBOT-001: Phase A: 1 user = 1 active ExBot. status IN ('active','paused','closing','safe_mode','error') all count toward the limit.
BR-EXBOT-010: ExBot Worker (apps/bnza-exbot/) must not be co-deployed with OPERATOR (apps/bnza-operator/). They communicate via CF service binding only.
```

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Chức năng: Bot Start (preflight → mint LP → mở hedge → đặt stop → active)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng lỗi | Nguồn |
|---|---|---|---|---|---|
| 1 | USDC Investor | Submit start request qua POOL UI | POOL UI gọi OPERATOR `POST /api/exbot/start` | — | UC §3.1; SRS FR-EXBOT-090 |
| 2 | OPERATOR Facade | Nhận request, internal-token auth, forward qua service binding | Forward tới ExBot Worker | Direct HTTP tới ExBot Worker → 403 | UC §3.2; SRS FR-EXBOT-090 |
| 3 | ExBot Worker | Preflight check 1 — one-bot: query `bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')` | count = 0 → tiếp | count > 0 → A1: E-EXBOT-001 | UC §3.3, A1; SRS FR-EXBOT-001 |
| 4 | ExBot Worker | Preflight check 2 — HL `marginSummary`; compute `marginRequired × 2.0` | Đủ → tiếp | Thiếu → A2: E-EXBOT-002 | UC §3.3, A2; SRS FR-EXBOT-061 |
| 5 | ExBot Worker | Preflight check 3 — `hl_agent_keys.approval_status` + `expires_at` | Approved + not expired → tiếp | Pending → A3: E-EXBOT-003; Expired → A9: E-EXBOT-004 | UC A3, A9; SRS FR-EXBOT-081 + FR-EXBOT-083 |
| 6 | ExBot Worker | Preflight check 4 — builder fee 5bps (cơ chế pending OQ-EXBOT-05) | Confirmed → tiếp | Chưa → A5: E-EXBOT-005 | UC A5; SRS FR-EXBOT-002 step 4 |
| 7 | ExBot Worker | Preflight check 5 — simulate `vaultMint` với `slippageBps` | Pass → tiếp | Fail → A6: E-EXBOT-006 | UC A6; SRS spec.md §5 E-EXBOT-006 |
| 8 | ExBot Worker | Tạo bot record D1: insert `bots` + `bot_registry`, `lifecycle_state='preflight'` | Bản ghi persist nguyên tử | D1 fail → UC không nêu | UC §3.4; ERD `bots` |
| 9 | ExBot Worker | Set `lifecycle_state='lp_opening'`, gọi `BnzaExVault.vaultMint(...)` | Tx submitted; chờ `VaultMinted` | A4: LP mint fails → `error`, "return funds" (cơ chế chưa rõ — I-08) | UC §3.5, A4; states.md |
| 10 | ExBot Worker | Nhận `VaultMinted`; insert `positions`; transition `lp_opening → lp_opened` | `positions` persisted; `lifecycle_state='lp_opened'` | Event watcher lag → UC không nêu | UC §3.6; ERD `positions` |
| 11 | ExBot Worker | Compute `lpEthAmount` từ TickMath; compute `targetShortEth = lpEthAmount × hedgeRatio (Phase A=0.70)`; **transition `lp_opened → hedge_pre_open`** (UC không nêu tên state — I-05) | State persisted | — | UC §3.7; SRS FR-EXBOT-020 + FR-EXBOT-021 |
| 12 | ExBot Worker | Compute deterministic `cloid`; gọi HL `openShortIoc(targetSize, cloid)` | HL ack | A10: HL reject → UC ghi `error` (**SRS: `safe_mode`** — I-01); A7: HL unreachable → UC ghi `error` (**SRS: `safe_mode`** — I-01) | UC §3.7; SRS FR-EXBOT-022 + FR-EXBOT-024 |
| 13 | ExBot Worker | Post-order reconcile: fetch `clearinghouseState`, verify size; transition `hedge_pre_open → hedge_post_confirmed` | Reconcile pass; `hedge_legs` updated | A11: reconcile mismatch → UC không nêu terminal state đúng (**SRS: `safe_mode`** — I-01, I-09) | UC §3.8-9; SRS FR-EXBOT-025 |
| 14 | ExBot Worker | Compute `stop_trigger_px` BigDecimal; `stopSafetyFactor Phase A=0.70` | Tính xong | `effective_leverage > 4.5` → SAFE_MODE (UC không nêu) | UC §3.10; SRS FR-EXBOT-030 |
| 15 | ExBot Worker | **Transition `hedge_post_confirmed → stop_placing`** (UC không nêu — I-05); gọi `placeReduceOnlyStopMarket(...)` | Stop placed; `hedge_legs` cập nhật stop fields | A8: stop fail → UC ghi `error` (**SRS: `safe_mode`** — I-01); E-EXBOT-009 | UC §3.10; SRS FR-EXBOT-031 |
| 16 | ExBot Worker | `stop_placing → stop_verified → active`; set `status='active'`; init `bot_runtime_state` + `circuit_breakers` | Bot `active` | — | UC §3.11; SRS FR-EXBOT-003 + FR-EXBOT-013 + FR-EXBOT-040 |
| 17 | ExBot Worker | Trả `{status: active, botId}` qua service binding | OPERATOR forward về POOL UI | — | UC §3.12; SRS FR-EXBOT-090 |

#### B. Business rules và validation

| Rule | Điều kiện | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|
| BR-EXBOT-001 — one-bot | `COUNT(bot_registry WHERE user_id=? AND bot_type='ex' AND status IN (...))` = 0 | Cho phép tạo | Reject E-EXBOT-001 | SRS §4 BR-EXBOT-001 |
| BR-EXBOT-010 — Worker isolation | ExBot Worker không co-deploy với OPERATOR | Architecture hợp lệ | Direct HTTP → 403 | SRS §4 BR-EXBOT-010 |
| HL margin buffer 2.0x | `marginBalanceUsd ≥ marginRequired × 2.0` | Pass preflight 2 | Block E-EXBOT-002 | SRS FR-EXBOT-061 |
| Agent key approved + not expired | `approval_status='approved'` AND `expires_at > now` | Pass preflight 3 | Pending: E-EXBOT-003; Expired: E-EXBOT-004 | SRS FR-EXBOT-081 + FR-EXBOT-083 |
| Builder fee 5bps | Confirmed (mechanism pending OQ-EXBOT-05) | Pass preflight 4 | Block E-EXBOT-005 | SRS FR-EXBOT-002 step 4 |
| BigDecimal invariant | Tất cả tính `targetShortEth`, `stop_trigger_px`, `marginRequired` phải BigDecimal | Precision đúng | Bug runtime không có thông báo | NFR-EXBOT-008 |
| `wethIndex` per-chain | Verify và lưu tại LP open; KHÔNG hardcode | LP ETH calc đúng | LP amount sai → hedge sai | SRS FR-EXBOT-004 |
| Cloid deterministic | `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | HL dedup; retry an toàn | Double-order risk | SRS FR-EXBOT-024 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung (verbatim từ spec.md §5) | Mã | Nguồn |
|---|---|---|---|---|
| One-bot policy fail | API error 409 | "You already have an active ExBot. Close or wait for the existing bot to finish." | E-EXBOT-001 | SRS spec.md §5 |
| HL margin không đủ | API error 400 | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | E-EXBOT-002 | SRS spec.md §5 |
| Agent key pending | API error 400 | "Agent key is awaiting approval. Please complete the approval process before starting." | E-EXBOT-003 | SRS spec.md §5. UC A3 ghi sai verbatim (I-03) |
| Agent key expired | API error 400 | "Your HL agent key has expired. Please submit a new one." | E-EXBOT-004 | SRS spec.md §5. UC A9 cite E-EXBOT-003 (sai code — I-02) |
| Builder fee chưa approved | API error 400 | "HL builder fee (5bps) approval required before starting ExBot." | E-EXBOT-005 | SRS spec.md §5. UC A5 ghi sai verbatim (I-04) |
| LP mint simulation fail | API error 400 | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | E-EXBOT-006 | SRS spec.md §5 |
| HL IOC reject | API error 502 | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." | E-EXBOT-007 | SRS spec.md §5. UC A10 ghi `error` (SRS: `safe_mode`) |
| HL unreachable | API error 503 + SAFE_MODE | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | E-EXBOT-008 | SRS spec.md §5; FR-EXBOT-050. UC A7 ghi `error` (SRS: `safe_mode`) |
| Stop placement fail | API error 502 + SAFE_MODE | "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | E-EXBOT-009 | SRS spec.md §5; states.md `stop_placing → safe_mode`. UC A8 ghi `error` (SRS: `safe_mode`) |
| Reconcile mismatch | Internal alert + SAFE_MODE | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | E-EXBOT-011 | SRS spec.md §5; FR-EXBOT-050. UC A11 không nêu terminal state (I-01, I-09) |
| Happy path | API 200 + `active` | `{status: active, botId}` | — | UC §3.12; SRS FR-EXBOT-003 |
| VaultMinted event | On-chain event | `VaultMinted(user, botId, tokenId, liquidity)` | — | UC §3.5; SRS flows.md F-03 |
| State transitions D1 | Atomic D1 write | `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` | — | SRS FR-EXBOT-003; states.md |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / action kích hoạt | Module / UC bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Bot chuyển `active` | UC-EXBOT-light-check | Cron `bot-scan` (1 phút) pick bot mới khi `next_light_check_at <= now` | Verify `next_light_check_at` = `now + 5min + jitter(±45s)` | SRS FR-EXBOT-012 + FR-EXBOT-013 |
| `hedge_legs.stop_price` populated | UC-EXBOT-light-check (stop monitoring) + UC-EXBOT-bot-safe-close | Light-check check `markPrice >= stop_price`; stop monitoring chạy kể cả khi circuit open | Verify `stop_price` BigDecimal, `stop_cloid` khớp HL response | SRS FR-EXBOT-014 + FR-EXBOT-032 |
| Agent key decrypt để sign HL order | UC-EXBOT-agent-key | Plain DEK + agent key chỉ tồn tại trong scope function; revoked key giữa luồng → SAFE_MODE | Verify log không chứa plain key | SRS FR-EXBOT-080 + FR-EXBOT-082 |
| Gọi HL `marginSummary`, `openShortIoc`, `clearinghouseState`, `placeReduceOnlyStopMarket` | HLRateLimitDO | Tổng weight ≤ 800/min; nếu DO trả `{allowed:false}` → worker phải re-queue | UC không đề cập DO interaction (Q17 Open) | SRS FR-EXBOT-091 |
| Compute `lpEthAmount` trước hedge open | MarketDataDO | Đọc `sqrtPriceX96`, `currentTick` từ DO cache | UC không đề cập (Q17 Open); nguồn `lpEthAmount` pre-mint chưa rõ (Q7 Open) | SRS FR-EXBOT-093 |
| Multiple workers cùng start cho 1 user | UserLockDO | UC không nêu có lease ở `/api/exbot/start` | UC không đề cập (Q14 Open) | SRS FR-EXBOT-092 |
| A4 LP mint fail | UC-EXBOT-bot-safe-close | UC ghi "return funds" nhưng không nêu cleanup `bots` record hay rollback ERC-20 | UC không đề cập (I-08, Q5 Open) | UC §4 A4; states.md `lp_opening → error` |
| Bot mới ảnh hưởng `bot_registry` count | UC-EXBOT-bot-start (chính nó) | Sau `active`, mọi start mới của cùng user phải reject; sau `closed`, count giảm | Verify race: 2 request song song (Q14 Open) | UC §4 A1; SRS FR-EXBOT-001 |

---

## 8. Acceptance Criteria

> UC trace tới US-EXBOT-001 (us-001.md) — 4 AC. Bổ sung AC suy luận từ SRS.

| AC # | Scenario | Given | When | Then | Nguồn |
|---|---|---|---|---|---|
| AC-01 | Happy path — preflight pass, bot đi qua đủ 8 lifecycle state → `active` | User chưa có ExBot active; margin đủ; key approved + not expired; builder fee approved; LP sim pass | Investor submit `/api/exbot/start` | `lifecycle_state` tuần tự `preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`; `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` populated; `bot_runtime_state.next_light_check_at` set; `circuit_breakers.state='closed'`; response `{status:active, botId}` | US-EXBOT-001 AC-EXBOT-001-1 |
| AC-02 | One-bot policy block | User đã có 1 ExBot `status='active'` | Submit `/api/exbot/start` | Reject E-EXBOT-001 verbatim; không tạo bot record mới | US-EXBOT-001 AC-EXBOT-001-2 |
| AC-03 | Insufficient HL margin | `marginBalanceUsd = $300`; `marginRequired × 2.0 = $700` | Submit `/api/exbot/start` | Block E-EXBOT-002: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit an additional $400 to HL." | US-EXBOT-001 AC-EXBOT-001-3 |
| AC-04 | Agent key pending | `hl_agent_keys.approval_status='pending'` | Submit `/api/exbot/start` | Block E-EXBOT-003 verbatim: "Agent key is awaiting approval. Please complete the approval process before starting." | US-EXBOT-001 AC-EXBOT-001-4 (UC A3 ghi sai verbatim — I-03) |
| AC-05 | Agent key expired (Suy luận cần xác nhận) | `approval_status='approved'` AND `expires_at < now` | Submit `/api/exbot/start` | Block E-EXBOT-004: "Your HL agent key has expired. Please submit a new one." | Suy luận từ SRS FR-EXBOT-083; UC A9 cite sai code |
| AC-06 | Builder fee chưa approved (Suy luận) | Builder fee 5bps chưa confirmed | Submit `/api/exbot/start` | Block E-EXBOT-005 verbatim | Suy luận từ SRS spec.md §5 E-EXBOT-005; UC A5 ghi sai verbatim |
| AC-07 | LP mint simulation fail (Suy luận) | Slippage > tolerance | Submit `/api/exbot/start` | Block E-EXBOT-006; không tạo bot record | Suy luận; ngưỡng slippage chưa nêu (Q11) |
| AC-08 | LP mint thực tế fail (Suy luận) | Preflight pass; tx `vaultMint` revert | ExBot Worker submit tx | `lifecycle_state='error'`; "return funds" — cơ chế chưa rõ (I-08) | Suy luận từ states.md `lp_opening → error` |
| AC-09 | HL unreachable (Suy luận) | Preflight pass; LP minted; HL down > 5 min | ExBot Worker gọi `openShortIoc` | `lifecycle_state='safe_mode'` (SRS); E-EXBOT-008 | Suy luận; UC A7 ghi sai `error` (I-01) |
| AC-10 | Stop placement fail (Suy luận) | Preflight pass; LP minted; hedge open + reconcile pass; HL từ chối `placeReduceOnlyStopMarket` | ExBot Worker submit stop | `lifecycle_state='safe_mode'` (SRS); E-EXBOT-009; bot KHÔNG đạt `active` | Suy luận; UC A8 ghi sai `error` (I-01) |
| AC-11 | Reconcile mismatch (Suy luận) | Preflight pass; LP minted; HL ack nhưng `clearinghouseState` báo size khác target | ExBot Worker reconcile | `lifecycle_state='safe_mode'` (SRS); E-EXBOT-011 | Suy luận; UC A11 không nêu terminal state (I-01, I-09) |
| AC-12 | Direct internet access tới ExBot Worker (security, Suy luận) | Attacker gọi trực tiếp ExBot Worker URL | HTTP request | Trả 403 | Suy luận từ SRS FR-EXBOT-090 + BR-EXBOT-010 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Throughput | NFR-EXBOT-001: scan 10,000 bots / 5-min cycle | Bot mới phải được pick bởi scan → init đúng `next_light_check_at` | SRS NFR §3 |
| Latency | NFR-EXBOT-002: 1 hedge-sync < 30s | Bot-start chứa hedge open + reconcile + stop place — tổng latency mong đợi? (Q18 Open) | SRS NFR §3 |
| Rate Limit | NFR-EXBOT-004: HL API ≤ 800 weight/min | Preflight + hedge open + reconcile + stop = nhiều HL calls; phải qua HLRateLimitDO; UC không đề cập (Q17) | SRS FR-EXBOT-091 |
| Security | NFR-EXBOT-006: agent key AES-GCM; plain key function-scope; never logged | Verify log không chứa plain key; revoked key giữa luồng → SAFE_MODE | NFR §3; FR-EXBOT-080 |
| Precision | NFR-EXBOT-008: BigDecimal bắt buộc | Mọi test math phải verify không có `Number()` conversion | SRS NFR §3 |
| Multi-chain | NFR-EXBOT-009: Base + Optimism; `wethIndex` per-chain | Test phải có 2 chain; pool address + wethIndex chưa chốt (OQ-EXBOT-03) | SRS NFR §3 |
| Availability | NFR-EXBOT-010: SAFE_MODE không phải terminal — autonomous recovery | Bot fail vào SAFE_MODE phải có path recovery | SRS NFR §3; FR-EXBOT-050 |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng vấn đề (Issue Register — Re-audit v2)

Các vấn đề được đánh số từ v2 audit; mỗi vấn đề vẫn còn mở sau UC update 2026-06-20.

| Issue ID | Loại | Mức độ | Khu vực | Nguồn tham chiếu | Phát hiện | Ảnh hưởng đến tester | Đề xuất sửa | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| I-01 | CROSS_SOURCE_CONFLICT | **Blocker** | Alternate flow A7, A8, A10, A11 | UC §4 A7/A8/A10/A11 vs `srs/states.md` `hedge_pre_open → safe_mode`, `stop_placing → safe_mode`; SRS FR-EXBOT-050 | Cả bốn alternate flow mới (A7 = HL unreachable, A8 = stop fail, A10 = HL IOC reject, A11 = reconcile mismatch) đều ghi terminal state là **`'error'`**. SRS `states.md` ánh xạ tường minh cả bốn trường hợp sang **`safe_mode`**. Trạng thái `error` chỉ dành cho lỗi không thể phục hồi cần admin (FR-EXBOT-050). | Tester assert `bots.lifecycle_state = 'error'` trong khi hệ thống chuyển sang `'safe_mode'`. Test 4 đường thất bại này sẽ fail hoặc pass sai. Không thể thiết kế kịch bản recovery safe-mode đúng. | Thay `'error'` bằng `'safe_mode'` trong A7, A8, A10, A11. Thêm ghi chú §3 phân biệt `error` vs `safe_mode`. | **Open** |
| I-02 | CROSS_SOURCE_CONFLICT | **Major** | Alternate flow A9 | UC §4 A9 vs SRS spec.md §5 E-EXBOT-003 và E-EXBOT-004 | A9 cite E-EXBOT-003 nhưng trích dẫn nội dung của E-EXBOT-004 (expired key). E-EXBOT-003 là "Agent key is awaiting approval..." (pending key). | Tester assert `E-EXBOT-003` trong path key expired nhưng hệ thống phát `E-EXBOT-004`. | Đổi A9 từ E-EXBOT-003 → E-EXBOT-004. | **Open** |
| I-03 | CROSS_SOURCE_CONFLICT | **Major** | Alternate flow A3 | UC §4 A3 vs SRS spec.md §5 E-EXBOT-003 verbatim | UC A3: "Agent key not approved. Please submit and get approval before starting." — KHÔNG khớp E-EXBOT-003 verbatim: "Agent key is awaiting approval. Please complete the approval process before starting." | Test assertion message sẽ fail. | Cập nhật A3 theo nguyên văn E-EXBOT-003. | **Open** |
| I-04 | CROSS_SOURCE_CONFLICT | **Major** | Alternate flow A5 | UC §4 A5 vs SRS spec.md §5 E-EXBOT-005 verbatim | UC A5: "Builder fee (5bps) must be confirmed on HL before starting." — KHÔNG khớp E-EXBOT-005: "HL builder fee (5bps) approval required before starting ExBot." | Ảnh hưởng tương tự I-03. | Cập nhật A5 theo nguyên văn E-EXBOT-005. | **Open** |
| I-05 | MISSING_INFO | **Major** | Main flow bước 7–9 | UC §3.7–3.9 vs `srs/states.md` `hedge_pre_open`, `stop_placing`; SRS FR-EXBOT-003 | UC main flow không đặt tên các trạng thái trung gian `hedge_pre_open` (bước 7) và `stop_placing` (bước 10). Tường thuật nhảy `lp_opened → hedge_post_confirmed` và `stop_verified → active`, tạo cảm giác hai state này không tồn tại. Light-check xử lý khác khi bot đang ở state transitional (FR-EXBOT-013). | Tester không thể test chuyển trạng thái `lp_opened → hedge_pre_open` hay `hedge_post_confirmed → stop_placing`. Kịch bản "light-check skip khi state là `hedge_pre_open`/`stop_placing`" không thể suy ra. | Thêm tên state tường minh tại §3.7 (`→ hedge_pre_open`) và §3.10 (`→ stop_placing`). | **Open** |
| I-06 | MISSING_INFO | **Major** | §5 Postconditions | UC §3.11, §5 vs SRS FR-EXBOT-013, FR-EXBOT-040; ERD `bot_runtime_state`, `circuit_breakers` | Sau khi `lifecycle_state='active'`, UC không đề cập: (1) insert `bot_runtime_state` với `next_light_check_at = now + 5 min + jitter(±45s)`; (2) init `circuit_breakers.state='closed'`; (3) populate `last_known_hl_short_size`. Thiếu các bước này → bot mới không được cron light-check nhận diện. | Tester bỏ sót assertion post-condition `bot_runtime_state` và `circuit_breakers` trong happy path. | Thêm vào §5 Postconditions: `bot_runtime_state` với `next_light_check_at`, `circuit_breakers.state='closed'`. | **Open** |
| I-07 | MISSING_INFO | **Minor** | §7 FR Trace | UC §7 vs SRS FR-EXBOT-003, FR-EXBOT-061, FR-EXBOT-081 | FR Trace liệt kê `FR-EXBOT-001, 002, 004, 020, 030, 031`. Thiếu: FR-EXBOT-003 (chuỗi 8 trạng thái), FR-EXBOT-061 (margin check), FR-EXBOT-081 (agent key check). | RTM coverage report sai — FRs này hiện thị là chưa test dù bot-start triển khai chúng. | Thêm FR-EXBOT-003, FR-EXBOT-061, FR-EXBOT-081 vào §7. | **Open** |
| I-08 | UNCLEAR_INFO | **Major** | Alternate flow A4 | UC §4 A4 vs `srs/states.md` `lp_opening → error` | A4 gộp chung: (a) LP mint simulation fail (preflight, chưa có D1 record) với (b) `vaultMint` tx revert (D1 record tại `lp_opening`). Hai trường hợp có cleanup requirements khác nhau. "Return funds" không rõ: auto-revert on-chain hay explicit Worker action? | Tester không biết A4 áp dụng trước hay sau D1 record tạo. Không thể viết precondition hoặc post-condition cleanup assertions. | Tách A4 thành A4a (sim fail, không có D1 record) và A4b (tx revert, D1 tại `lp_opening → error`). Chỉ định cơ chế "return funds". | **Open** |
| I-09 | UNCLEAR_INFO | **Minor** | Alternate flow A11 | UC §4 A11 vs SRS FR-EXBOT-025, FR-EXBOT-028, FR-EXBOT-050 | A11 không nêu terminal state (chỉ "enqueue `partial_repair`; alert operator"). FR-EXBOT-028 định nghĩa `partial_repair` cho hedge-sync partial fill và LP rebalance failures — KHÔNG phải cho initialization reconcile mismatch. Không có FR nào map trigger này tới queue đó. | Tester nhận thông tin mâu thuẫn: SAFE_MODE vs `partial_repair` enqueue không có trong spec. | Sửa (1): ghi `safe_mode` là terminal state. Sửa (2): BA xác nhận `partial_repair` enqueue lúc init mismatch có chủ ý không và thêm FR, hoặc xóa. | **Open** |

### 10.2 Câu hỏi mở carry-forward từ v1 (vẫn Open)

| ID | Mức ưu tiên | Blocking |
|---|---|---|
| Q2 / Q3 | M | FR trace sync giữa `usecases/index.md` và UC body §7; FR-003 discrepancy |
| Q5 | M | A4 "return funds" mechanism — simulation fail vs on-chain revert (trùng I-08) |
| Q6 | M | `hedge_pre_open` và `stop_placing` không nêu trong UC main flow (trùng I-05) |
| Q7 | H | Nguồn `lpEthAmount` trước LP mint (formula inputs `liquidity, tickLower, tickUpper, sqrtPriceX96, currentTick` chỉ available post-mint) |
| Q10 | M | BR-EXBOT-* / E-EXBOT-* định nghĩa chỉ trong module-local `spec.md`, không trong backbone common files |
| Q11 | M | Slippage tolerance threshold cho LP mint simulation — giá trị cụ thể chưa nêu |
| Q12 | M | Request payload `POST /api/exbot/start` chưa được mô tả (chain, tick range, deposit amount) |
| Q14 | M | Idempotency / lock cho concurrent start requests (double-submit race) |
| Q15 | M | Actor discrepancy: FRD §4.11 ghi Admin; UC §1 ghi USDC Investor |
| Q17 | M | UC không đề cập 3 Durable Objects (HLRateLimitDO, MarketDataDO, UserLockDO) |
| Q18 | L | Expected latency / SLA cho toàn bộ bot-start sequence |
| Q19 | M | Behavior khi agent key status là `revoked` hoặc `superseded` trong key rotation |
| Q20 | L | Post-active init: `bot_runtime_state` và `circuit_breakers` không trong UC §5 (trùng I-06) |
| Q21 | L | Audit log requirements cho `POST /api/exbot/start` |

### 10.3 Audit Summary

**Bảng điểm (per `references/scoring-rubric.md`):**

| # | Scoring Area | Max | Score | Ghi chú |
|---|---|---|---|---|
| 1 | Completeness of functional scope | 25 | 15 | Main flow cover 8-state sequence ở mức cao (+). Thiếu `hedge_pre_open`/`stop_placing` state names (I-05, −4). Thiếu post-active init postconditions (I-06, −4). A4 gộp chung sim fail vs tx revert (I-08, −2). |
| 2 | Consistency with SRS / cross-source integrity | 25 | 10 | 4 alternate flow dùng sai terminal state `error` vs `safe_mode` (I-01, −8 Blocker). A9 cite sai E-EXBOT-003 vs E-EXBOT-004 (I-02, −3). A3 message verbatim sai (I-03, −2). A5 message verbatim sai (I-04, −2). |
| 3 | Clarity and testability | 20 | 13 | Happy path narrative cải thiện. `hedgeRatio`/`stopSafetyFactor` đặt tên rõ (+4). A4 "return funds" vẫn mơ hồ (I-08, −3). A11 `partial_repair` không có FR (I-09, −2). `lpEthAmount` source chưa rõ (Q7, −2). |
| 4 | Traceability (FR/BR/E codes) | 15 | 9 | E codes cited trong A1–A11 (+). 3 FR thiếu trong trace (I-07, −3). FR-003 index mismatch (Q2/Q3, −2). BR-EXBOT-* không trong backbone (Q10, −1). |
| 5 | Preconditions, postconditions, actors | 15 | 10 | On-chain preconditions thêm vào (+3). Post-active init thiếu §5 (I-06, −3). Actor discrepancy chưa giải quyết (Q15, −2). |
| **Tổng** | | **100** | **57** | |

**Verdict: NOT READY (57/100)**

Điểm tăng từ 52 → 57 so với v1. BA đã giải quyết các blocker quan trọng nhất từ v1 (thiếu alternate flows, ambiguity tên tham số 0.70). Tuy nhiên, cluster mới Blocker/Major: 4 alternate flow dùng sai terminal state (`error` thay vì `safe_mode`), 2 alternate flow có sai E-code hoặc non-verbatim message, main flow thiếu 2 intermediate lifecycle states quan trọng.

Auto-fail: không trigger. Blocker cap: Area 2 score 10/25 (dưới 40% = 10/25) cap không trigger riêng nhưng Blocker I-01 đủ để NOT READY.

---

## 11. Khuyến nghị

UC-EXBOT-bot-start hiện ở trạng thái **NOT READY (57/100)**. BA cần xử lý các mục sau trước lần audit tiếp:

**Blocker (bắt buộc sửa):**
- **I-01:** Thay `'error'` bằng `'safe_mode'` trong alternate flow A7, A8, A10, A11. Thêm ghi chú §3 phân biệt ngữ nghĩa `error` vs `safe_mode` theo FR-EXBOT-050.

**Major (nên sửa trong cùng lần):**
- **I-02:** Sửa A9 cite E-EXBOT-004 (expired key), không phải E-EXBOT-003.
- **I-03:** Cập nhật A3 theo đúng nguyên văn E-EXBOT-003: "Agent key is awaiting approval. Please complete the approval process before starting."
- **I-04:** Cập nhật A5 theo đúng nguyên văn E-EXBOT-005: "HL builder fee (5bps) approval required before starting ExBot."
- **I-05:** Đặt tên tường minh `hedge_pre_open` tại §3.7 và `stop_placing` tại §3.10 trong main flow.
- **I-06:** Thêm vào §5 Postconditions: `bot_runtime_state` row tạo với `next_light_check_at`; `circuit_breakers.state='closed'` init.
- **I-08:** Tách A4 thành A4a (preflight sim fail) và A4b (on-chain tx revert). Rõ cơ chế "return funds".

**Minor:**
- **I-07:** Thêm FR-EXBOT-003, FR-EXBOT-061, FR-EXBOT-081 vào §7 FR Trace.
- **I-09:** Rõ terminal state A11 là `safe_mode`; BA xác nhận `partial_repair` enqueue có FR support không.

Sau các sửa chữa này, v5 re-audit có thể đạt 75+ (Conditionally Ready). 14 câu hỏi Open từ §10.2 không block riêng lẻ cho happy path, nhưng Q7 (hedge size formula) và Q14 (double-submit idempotency) nên ưu tiên giải quyết.

---

## 12. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read-exbot agent | Tạo báo cáo lần đầu. Score 52/100, NOT READY. |
| v1 (re-audit) | 2026-06-18 | qc-uc-read-exbot agent | Re-audit theo HLD-2026-06-18: xóa cooldown/parked/re-entry; sửa paths; thêm I-22 (flows.md F-05 stale). |
| v2 | 2026-06-26 | qc-uc-read-exbot agent | Tái đánh giá đầy đủ cấu trúc như v1. Cross-check SRS baseline vs UC/US update 2026-06-20. Score 57/100, NOT READY. |
