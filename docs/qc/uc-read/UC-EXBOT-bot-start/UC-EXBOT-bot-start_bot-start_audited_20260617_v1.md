---
title: "UC-EXBOT-bot-start — Audited Readiness Review (v1)"
uc_id: UC-EXBOT-bot-start
feature: bot-start
date_created: 2026-06-17
last_updated: 2026-06-18
author: qc-uc-read-exbot agent
version: v1
output_language: vi+en
hld_baseline: 2026-06-18
---

# UC Readiness Review Report / Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC-EXBOT-bot-start — Bot Initialization: preflight → LP mint → HL hedge open → stop place → active**
**UC-EXBOT-bot-start — Khởi tạo ExBot: preflight → mint LP → mở hedge HL → đặt stop → active**

> **Re-audit note (2026-06-18):** Updated in-place against HLD decisions published 2026-06-18 — `cooldown`/`parked` states removed; park/re-entry loop dropped; `bot_safe_close` now transitions directly to `closed`; `emergencyTransfer` authority updated (OPERATOR_ROLE only, no recipient param, emits `EmergencyRecovery`). New issue I-22 added. File paths corrected to `docs/BA/`. Both English and Vietnamese content integrated per global-rules.

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| ExBot | Managed delta-hedged LP Bot — bot quản lý vị thế cung cấp thanh khoản Uniswap V3 trên cặp USDC/WETH kèm vị thế short ETH-USD perpetual trên Hyperliquid để triệt tiêu phần lớn rủi ro giá ETH. Trong dự án này, ExBot chạy ở backend Cloudflare Worker `apps/bnza-exbot/`, không có UI riêng. | FRD §1 + SRS spec.md §1 |
| LP | Liquidity Provider — bên cấp thanh khoản trên Uniswap V3. Trong UC này, phía LP của ExBot được mint NFT thanh khoản và lưu ký bên trong contract BnzaExVault. | (industry term) |
| HL | Hyperliquid — sàn perpetual on-chain dùng để mở vị thế short ETH-USD nhằm hedge LP. ExBot gọi HL qua REST API có rate-limit (NFR-EXBOT-004). | (proper noun) |
| FRD | Functional Requirement Document — tài liệu yêu cầu chức năng. Trong dự án này, FRD `03_modules/exbot/frd.md` đánh số `FR-EXBOT-001..110` theo nhóm chức năng. | (industry term) |
| SRS | Software Requirement Specification — tài liệu spec hệ thống. Trong dự án này, SRS gồm `srs/spec.md` + `srs/states.md` + `srs/flows.md` + `srs/erd.md`; `srs/spec.md` cũng đánh số `FR-EXBOT-*` nhưng theo cách khác với FRD (xem §10.1 issue I-01). | (industry term) |
| FR-EXBOT-NNN | Functional Requirement của ExBot. **Cảnh báo:** cùng một mã FR-EXBOT-NNN xuất hiện ở cả `frd.md` và `srs/spec.md` nhưng trỏ tới hai nội dung khác nhau (ví dụ FR-EXBOT-001 trong FRD = "Bot Initialization Preflight"; trong SRS = "One-Bot-Per-User Policy"). | `frd.md` §4 + `srs/spec.md` §2 |
| BR-EXBOT-NNN | Business Rule của ExBot. Trong dự án này được định nghĩa trong `srs/spec.md` §4 (không nằm trong `02_backbone/common-rules.md` như cấu trúc tham chiếu mặc định). | `srs/spec.md` §4 |
| E-EXBOT-NNN | Error code trả về cho API hoặc internal alert của ExBot. Định nghĩa trong `srs/spec.md` §5; không xuất hiện trong `02_backbone/message-list.md`. | `srs/spec.md` §5 |
| OQ-EXBOT-NN | Open Question — câu hỏi mở chưa chốt, liệt kê trong `srs/spec.md` §9 và `frd.md` §7. Trong UC này có nhiều OQ ảnh hưởng trực tiếp đến preflight (OQ-EXBOT-05 builder fee) và LP open (OQ-EXBOT-03 pool/wethIndex). | `srs/spec.md` §9 + `frd.md` §7 |
| BnzaExVault | Smart contract Solidity do zen sở hữu, đóng vai trò custodian của LP NFT và xử lý `vaultMint` / `redeem` / lưu ký USDC `uninvested_balances`. SOTATEK chỉ tích hợp qua ABI, không phát triển contract. | FRD §3 + SRS §1.3 |
| Cloid | Client Order ID — chuỗi 128-bit hex deterministic gửi kèm mỗi lệnh HL để khử trùng lặp. Trong dự án này, `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`. | SRS FR-EXBOT-024 |
| TickMath | Thuật toán toán học của Uniswap V3 dùng để chuyển đổi giữa `tick`, `sqrtPriceX96` và amount. Trong dự án này dùng để tính `lpEthAmount` mà không cần gọi HL API. | (industry term) |
| sqrtPriceX96 | Giá pool Uniswap V3 ở định dạng Q64.96 fixed-point. Trong dự án này được cache trong `MarketDataDO` để mọi light-check worker đọc chung, tránh mỗi bot tự gọi RPC. | (industry term) |
| wethIndex | Vị trí của WETH trong cặp pool Uniswap V3 (0 hoặc 1). Trong dự án này phải xác minh per-chain ở thời điểm LP open (FR-EXBOT-004) vì Base và Optimism có thể khác thứ tự token0/token1. | SRS FR-EXBOT-004 |
| AES-256-GCM | Authenticated encryption with associated data (AEAD) algorithm. Trong dự án này dùng cho envelope encryption agent key HL: data key (DEK) mã hoá agent key, master key (Cloudflare Secrets Store) wrap DEK. | NFR-EXBOT-006 + FR-EXBOT-080 |
| DEK | Data Encryption Key — khoá AES per-row dùng để mã hoá agent key. Trong dự án này lưu dạng `wrapped_dek` trong bảng `hl_agent_keys`. | SRS FR-EXBOT-080 |
| KMS | Key Management Service — dịch vụ quản lý khoá. Trong dự án này dùng Cloudflare Secrets Store làm Master Key store để wrap DEK. | (industry term) |
| Stop / Stop Trigger | Lệnh stop reduce-only đặt trên HL để đóng vị thế hedge khi giá vượt ngưỡng. Trong dự án này tính bằng BigDecimal theo công thức `stop_trigger_px = entry_price × (1 + liq_distance_pct × stopSafetyFactor)`, Phase A `stopSafetyFactor = 0.70`. | SRS FR-EXBOT-030 |
| INV-STOP | Invariant về stop replacement: cấm cancel-then-place trực tiếp khi resize stop; phải dùng protected protocol §19.5 của SPEC. Không áp dụng trực tiếp ở UC này (start) nhưng được nhắc trong cooldown / hedge-sync. | SRS FR-EXBOT-035 |
| IOC | Immediate-Or-Cancel — kiểu lệnh khớp ngay phần có thể, hủy phần còn lại. UC này mở hedge bằng HL short IOC. | (industry term) |
| Builder fee 5bps | Phí builder 5 basis points (0.05%) mà người dùng phải approve cho HL trước khi ExBot có thể vận hành. UC yêu cầu confirmed trước start nhưng cơ chế approve còn pending OQ-EXBOT-05. | SRS FR-EXBOT-002 + OQ-EXBOT-05 |
| BigDecimal | Kiểu số chính xác cao dùng cho mọi tính toán tài chính (hedge size, stop price, margin). Trong dự án này forbidden mọi phép cộng/nhân `Number()` trên giá trị tài chính (NFR-EXBOT-008). | NFR-EXBOT-008 |
| D1 | Cơ sở dữ liệu SQLite-as-a-service của Cloudflare. Trong dự án này tách `control_db` (1 global) và `state_db_shard_xx` (1 shard Phase A). | FRD §4.9 |
| Durable Object (DO) | Đối tượng có trạng thái dài hạn trên Cloudflare Workers, dùng làm lock / cache / rate-limit ở quy mô region. Dự án này có `HLRateLimitDO`, `UserLockDO`, `MarketDataDO`. | FRD §4.10 |
| HLRateLimitDO | Durable Object thi hành rate-limit sliding-window cho mọi call HL API (NV ngân sách 800 weight/min). Mọi outbound HL call ở mọi giai đoạn của UC này (margin check, hedge open, reconcile, stop place) đều phải đi qua DO này. | SRS FR-EXBOT-091 |
| UserLockDO | Durable Object cấp lease 90s để chống concurrent HL mutation cho cùng một user. UC này không đề cập rõ có dùng UserLockDO ở giai đoạn start hay không. | SRS FR-EXBOT-092 |
| MarketDataDO | Durable Object cache giá pool Uniswap V3 (`sqrtPriceX96`, `currentTick`, `blockNumber`). UC này nhiều khả năng phải đọc DO để tính `lpEthAmount` trước khi mint, nhưng UC không nói rõ. | SRS FR-EXBOT-093 |
| Service binding | Cơ chế gọi nội bộ giữa hai Cloudflare Worker mà không đi qua internet. UC này dùng service binding giữa OPERATOR Facade và ExBot Worker. | SRS §1.1 |
| Reconcile | Bước đối soát trạng thái thực tế HL với trạng thái mong đợi sau mỗi mutation. UC này thực hiện reconcile sau khi mở hedge short. | SRS FR-EXBOT-025 |
| SAFE_MODE | Trạng thái lifecycle cấm mọi mutation nhưng vẫn cho phép read state, retry, alert. UC này hiện không xử lý trường hợp rơi vào SAFE_MODE giữa luồng start. | SRS FR-EXBOT-050 |

---

## Feature Brief — Tóm tắt nghiệp vụ

UC-EXBOT-bot-start mô tả luồng khởi tạo một con ExBot mới cho một nhà đầu tư USDC. ExBot là dịch vụ backend chạy trên Cloudflare Worker, không có UI riêng; nhà đầu tư bấm "Start" trên POOL UI, request đi qua OPERATOR Facade `POST /api/exbot/start`, OPERATOR forward sang ExBot Worker qua Cloudflare service binding. ExBot Worker là phía thực sự chạy nghiệp vụ.

Luồng nghiệp vụ chính: ExBot Worker chạy 5 preflight check tuần tự (one-bot-per-user; HL isolated margin ≥ required × 2.0; HL agent key đã approved và chưa hết hạn; builder fee 5bps đã confirmed; LP mint simulation pass). Nếu mọi check pass, hệ thống tạo bản ghi bot (`lifecycle_state='preflight'`), gọi `BnzaExVault.vaultMint(...)` để mint LP NFT (chuyển sang `lp_opening` → `lp_opened` khi nhận event `VaultMinted`), mở HL short IOC với target size `lpEthAmount × hedgeRatio` (Phase A `hedgeRatio` được hardcode trong UC là 0.70 nhưng văn bản UC không đặt tên tham số rõ ràng — xem §10.1 issue I-08), reconcile vị thế thực, đặt reduce-only stop market với `stop_trigger_px` tính bằng BigDecimal, và cuối cùng chuyển sang `active`. Toàn bộ chuỗi state transition này được lưu nguyên tử vào D1 ở mỗi bước.

Quy tắc, exception và integration ảnh hưởng đến thiết kế test: (1) BR-EXBOT-001 (Phase A 1 user = 1 active ExBot, tính cả các status `active/paused/closing/safe_mode/error`); (2) BR-EXBOT-010 (ExBot Worker phải tách deploy với OPERATOR — chỉ giao tiếp qua service binding); (3) NFR-EXBOT-008 (mọi tính toán tài chính phải dùng BigDecimal); (4) NFR-EXBOT-009 (Base + Optimism từ Phase 1, `wethIndex` xác minh per-chain); (5) FR-EXBOT-080 (agent key lưu envelope AES-256-GCM, plain key chỉ tồn tại trong scope hàm). UC liên quan trực tiếp tới UC-EXBOT-hedge-sync (kế thừa cloid scheme + reconcile pattern), UC-EXBOT-bot-safe-close (gỡ trạng thái nếu start fail giữa chừng), và UC-EXBOT-agent-key (key phải approved trước start).

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-bot-start | Start ExBot (preflight + LP mint + hedge open + stop place) | initial draft 2026-06-12 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| `@hienduong` | (chưa có) | 2026-06-12 | 2026-06-12 |

| Artefact read / Artefact đã đọc | Version / last updated | Role / Vai trò | Notes / Ghi chú |
|---|---|---|---|
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-bot-start.md` | draft 2026-06-12 (unchanged) | UC chính cần audit | — |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/index.md` | **2026-06-18** | Index UC + FR trace | Updated on 2026-06-18; UC-EXBOT-bot-start row unchanged |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/userstories/us-001.md` | draft 2026-06-12 (unchanged) | US gắn UC (AC duy nhất hỗ trợ) | 4 AC: happy + 3 negative; Notes section still mentions `cooldown`/`parked` → stale after HLD-2026-06-18 |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/spec.md` | **v5.2.6 / 2026-06-18** | SRS — nguồn truth hành vi bot | HLD-2026-06-18: FM-XB-08 scope updated (park/redeploy dropped); FR-EXBOT-070/073/090 updated; IC-EXBOT-002 updated (uninvestedBalanceOf removed from integration surface) |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/states.md` | **draft 2026-06-18** | State machine — 16 lifecycle states (post-HLD) | `cooldown` và `parked` đã bị xoá khỏi State Registry; `close_operations` không còn `funds_parked`; bot_safe_close → closed trực tiếp |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/flows.md` | draft **2026-06-12** (NOT updated) | Sequence flows | ⚠️ F-05 still contains stale park/re-entry loop — see I-22 |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/srs/erd.md` | draft 2026-06-12 | ERD D1 | Cung cấp tên field cụ thể cho bots/positions/hedge_legs |
| `docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/frd.md` | **v0.1.0 / 2026-06-18** | FRD — nguồn yêu cầu chức năng | HLD-2026-06-18: ACT-M removed; bot_safe_close drop park/re-entry; lifecycle states cooldown/parked removed; emergencyTransfer authority updated |
| `docs/BA/plans/bnza-sotatek-260519-0000/02_backbone/common-rules.md` | draft 2026-06-09 | Common Rules registry | KHÔNG chứa BR-EXBOT-* (BR-EXBOT-* nằm trong SRS spec.md §4) |
| `docs/BA/plans/bnza-sotatek-260519-0000/02_backbone/message-list.md` | draft 2026-06-09 | Message registry | KHÔNG chứa E-EXBOT-* (E-EXBOT-* nằm trong SRS spec.md §5) |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

UC này tồn tại để cho phép một nhà đầu tư USDC khởi tạo một con ExBot mới — một bot tự động hoá vị thế LP delta-hedged trên cặp USDC/WETH. Mục tiêu nghiệp vụ là: nhà đầu tư đặt vốn USDC sinh phí LP Uniswap V3, đồng thời vị thế short ETH-USD perpetual trên Hyperliquid sẽ triệt tiêu phần lớn rủi ro giá ETH. Kết quả mong đợi của UC là một bản ghi bot mới với `lifecycle_state='active'`, vị thế LP do BnzaExVault custodian, và vị thế hedge HL đã đặt kèm reduce-only stop. UC này phục vụ nhóm `USDC Investor` ở Phase A (Base + Optimism, 1 active ExBot per user).

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Endpoint `POST /api/exbot/start` (Operator Facade) | Nhận request từ POOL UI, internal-token auth, forward sang ExBot Worker qua service binding | UC §3.1-3.2; SRS FR-EXBOT-090 |
| Preflight check 1 — one-bot policy | Query `bot_registry` với điều kiện `user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')`; nếu count > 0 → reject E-EXBOT-001 | UC §3.3, A1; SRS FR-EXBOT-001; FRD FR-EXBOT-001 step 1 |
| Preflight check 2 — HL margin sufficiency | Verify `marginBalanceUsd ≥ required_margin × 2.0` với `required_margin = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage` | UC §3.3, A2; SRS FR-EXBOT-002 + FR-EXBOT-061; FRD FR-EXBOT-001 step 2 |
| Preflight check 3 — agent key approved + not expired | Check `hl_agent_keys.approval_status='approved'` AND `expires_at > now`; nếu pending → E-EXBOT-003; nếu expired → E-EXBOT-004 | UC §2 + §3.3, A3; SRS FR-EXBOT-081 + FR-EXBOT-083 |
| Preflight check 4 — builder fee 5bps confirmed | Confirm HL builder fee đã approved (cơ chế chính xác chưa chốt — OQ-EXBOT-05); nếu chưa → E-EXBOT-005 | UC §2; SRS FR-EXBOT-002 step 4; OQ-EXBOT-05 |
| Preflight check 5 — LP mint simulation | Simulate `BnzaExVault.vaultMint` với slippage tolerance; nếu fail → E-EXBOT-006 | UC §3.3 (step 5 trong preflight); FRD FR-EXBOT-001 step 5 |
| Create bot record `(lifecycle_state='preflight')` | Insert vào `bots`, `bot_registry`, shard registry; populate `chain`, `wallet_address`, `next_light_check_at` | UC §3.4; ERD `bots`, `bot_registry` |
| Vault mint LP NFT | `BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` → emit `VaultMinted(user, botId, tokenId, liquidity)` | UC §3.5; SRS flows.md F-03 |
| Populate `positions` row | Insert `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `liquidity`, `pool_address`, `token0_decimals`, `token1_decimals`, `custodian='vault'` | UC §3.6; ERD `positions` |
| Transition `lp_opening → lp_opened` | Atomic D1 write của `bots.lifecycle_state` khi event `VaultMinted` được xác nhận | UC §3.6; states.md transition `lp_opening → lp_opened` |
| Open HL short IOC | Compute `targetShortEth = lpEthAmount × hedgeRatio` (Phase A 0.70 — xem I-08), submit `openShortIoc(targetSize, cloid)` với cloid deterministic | UC §3.7; SRS FR-EXBOT-021 + FR-EXBOT-024 |
| Post-order reconcile hedge | Fetch `clearinghouseState`, verify actual size = target ± tolerance, extract `entry_price`, `liquidation_price`, `effective_leverage` | UC §3.8; SRS FR-EXBOT-025 |
| Populate `hedge_legs` row + transition `hedge_post_confirmed` | Insert `hl_asset`, `target_ratio`, `leverage`, `margin_mode`, `entry_price`, `liquidation_price`, `effective_leverage`, `isolated_margin_usd` | UC §3.9; ERD `hedge_legs` |
| Compute `stop_trigger_px` | BigDecimal: `liq_distance_pct = (liquidation_price − entry_price) / entry_price`; `stop_distance_pct = liq_distance_pct × stopSafetyFactor`; `stop_trigger_px = entry_price × (1 + stop_distance_pct)`; Phase A `stopSafetyFactor=0.70` | UC §3.10; SRS FR-EXBOT-030 |
| Place reduce-only stop market trên HL | `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)`; transition `stop_placing → stop_verified` | UC §3.10-11; SRS FR-EXBOT-031 |
| Persist stop metadata vào `hedge_legs` | Lưu `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size`, `stop_distance_pct`, `stop_last_verified_at` | UC §3.10-11; ERD `hedge_legs` |
| Transition `stop_verified → active` + response | Set `bots.lifecycle_state='active'`, `bots.status='active'`; return `{status: active, botId}` lên OPERATOR rồi về POOL UI | UC §3.11-12; FR-EXBOT-003 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Logic chiến thuật giao dịch (PositionCalc, hedgeRatio tuning, stopSafetyFactor tuning) | Zen-proprietary (FRD §3 / SRS §1.3) | Tester không phải verify công thức math của zen; chỉ verify input/output của các interface mà SOTATEK build |
| Phát triển contract BnzaExVault | Zen scope; SOTATEK chỉ tích hợp qua ABI (IC-EXBOT-002) | Phải mock hoặc dùng deploy thử nghiệm BnzaExVault để test path Vault; ABI chưa final (OQ-EXBOT-08) |
| Pause / Resume (FRD FR-EXBOT-003) | Index `usecases/index.md` ghi nhầm FR-003 vào trace của bot-start; nhưng đây thuộc UC riêng (xem I-02) | Test bot-start KHÔNG cần cover pause/resume; cần xác nhận trace đúng |
| Wireframe / UI screens của POOL | ExBot là module backend; POOL UI thuộc module bnza-pool (SRS §6) | Không penalty UC vì thiếu wireframe; verify text trả về và status response |
| Cơ chế chính xác để confirm builder fee 5bps | Chưa chốt — OQ-EXBOT-05 (on-chain tx hay API call?) | Test step 4 preflight phụ thuộc OQ-EXBOT-05; cần clarify trước test design chi tiết |
| Cơ chế chính xác để compute `lpEthAmount` trước khi mint (chưa có liquidity) | UC không nói nguồn; không có spec rõ ràng — xem I-07 | Tester không thể tự suy ra công thức trước-mint chỉ từ TickMath chuẩn (cần `liquidity`) |
| Cách user / hệ thống chọn chain (Base hay Optimism) ở thời điểm start | UC không nói; payload `POST /api/exbot/start` chưa được mô tả — xem I-12 | Không thể verify Base bot vs Optimism bot tách biệt nếu không biết chain selector |
| Slippage tolerance cụ thể cho LP mint simulation | UC nói "passes" nhưng không có ngưỡng — xem I-11 | Tester không biết expected result của edge case slippage |
| Concurrency / double-click protection ở Facade endpoint | UC không đề cập idempotency cho `POST /api/exbot/start` — xem I-14 | Tester không biết race-condition expected (1 user 2 request đồng thời) |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| `USDC Investor` | Primary | Gửi request start qua POOL UI; sở hữu HL account + agent key approved | Phase A: 1 active ExBot per user (BR-EXBOT-001); HL isolated margin ≥ required × 2.0 | UC §1; SRS FR-EXBOT-001; FRD ACT-I |
| OPERATOR Facade | System (thin proxy) | Nhận `POST /api/exbot/start`, internal-token auth, forward qua service binding tới ExBot Worker | Không sở hữu business logic; chỉ proxy (BR-EXBOT-010) | UC §1; SRS FR-EXBOT-090; FRD ACT-O |
| ExBot Worker | System (Cloudflare Worker, `apps/bnza-exbot/`) | Chạy preflight, gọi Vault, gọi HL, đặt stop, cập nhật D1 | KHÔNG public internet (chỉ accessible qua service binding); deploy tách biệt OPERATOR (BR-EXBOT-010) | UC §1; SRS FR-EXBOT-090; FRD §3 |
| BnzaExVault | External (Solidity contract) | Mint LP NFT, custodian LP, emit `VaultMinted` event | ABI cuối cùng chưa confirmed (OQ-EXBOT-08); contract address inject qua Cloudflare Secrets Store | UC §1; SRS IC-EXBOT-002 |
| Hyperliquid | External | Khớp `openShortIoc`, trả `clearinghouseState`, khớp `placeReduceOnlyStopMarket` | Rate limit 1,200 weight/min hard; BNZA budget 800 weight/min (NFR-EXBOT-004); api unreachable >5 min → SAFE_MODE | UC §1; SRS FR-EXBOT-091; IC-EXBOT-001 |
| ExBot Admin (zen) | (Không tham gia luồng start chính) | Approve agent key tách biệt (UC-EXBOT-agent-key) — precondition của bot-start | Không xuất hiện trong main flow; xuất hiện trong A3 (agent key chưa approve) | FRD ACT-A; UC §2 |

**Nhận xét readiness:**

Actor primary (`USDC Investor`) và các system actor đã rõ ràng và đủ để thiết kế test ở mức happy path. Tuy nhiên tài liệu thiếu mô tả role/permission ở lớp Facade: OPERATOR mở endpoint `/api/exbot/start` cho ai? FRD §4.11 ghi cột `Actor = Admin` cho cả 5 endpoint Operator Facade, nhưng UC §1 ghi primary actor là `USDC Investor`. Mâu thuẫn này (xem I-15) tạo rủi ro test sai role: tester không biết end-user investor gọi trực tiếp hay phải thông qua Admin. Cần BA xác nhận role/permission chính xác để thiết kế test theo role.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | User KHÔNG có ExBot khác đang `status IN ('active','paused','closing','safe_mode','error')` | Yes | UC §2; SRS BR-EXBOT-001; FR-EXBOT-001 |
| 2 | User có HL account với isolated margin balance ≥ required margin × 2.0 (preflight buffer 2.0x) | Yes | UC §2; SRS FR-EXBOT-061; FRD FR-EXBOT-001 step 2 |
| 3 | HL agent key của user `approval_status='approved'` và `expires_at > now` | Yes | UC §2; SRS FR-EXBOT-081 + FR-EXBOT-083 |
| 4 | HL builder fee 5bps đã confirmed cho user | Yes (cơ chế chưa rõ — OQ-EXBOT-05) | UC §2; SRS FR-EXBOT-002 step 4 |
| 5 | LP mint simulation pass (slippage trong tolerance — ngưỡng cụ thể chưa nêu) | Yes | UC §3.3 (preflight step 5); FRD FR-EXBOT-001 step 5 |
| 6 (suy luận) | User đã approve token USDC cho BnzaExVault (ERC-20 allowance) đủ amount LP planned | Chưa nêu trong UC (xem I-09) | (Suy luận cần xác nhận) |
| 7 (suy luận) | User có đủ native ETH để trả gas cho on-chain tx `vaultMint` | Chưa nêu trong UC (xem I-09) | (Suy luận cần xác nhận) |
| 8 (suy luận) | Pool USDC/WETH 0.3% trên chain đã chọn có đủ thanh khoản để mint range theo tickLower/tickUpper user request | Chưa nêu trong UC (xem I-13) | (Suy luận cần xác nhận) |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Khởi tạo bot thành công (happy path) | `bots.lifecycle_state='active'`, `bots.status='active'`; bản ghi `positions` với `tokenId`, `tickLower`, `tickUpper`, `wethIndex`, `custodian='vault'`, `pool_address` populated; bản ghi `hedge_legs` với `entry_price`, `liquidation_price`, `effective_leverage`, `stop_price`, `stop_cloid`, `stop_order_id`, `stop_size`, `stop_distance_pct`, `stop_last_verified_at`, `circuit_state='closed'`, `margin_status='ok'`; bản ghi `bot_runtime_state` với `last_known_hl_short_size`, `last_hl_reconcile_at`, `next_light_check_at = now + 5min + jitter(±45s)`; API trả `{status: active, botId}` cho POOL UI | UC §5; SRS FR-EXBOT-003 + FR-EXBOT-025 + FR-EXBOT-013; ERD |
| Fail preflight (A1/A2/A3) | Không tạo bản ghi `bots` (FR-EXBOT-001 + FR-EXBOT-002 đảm bảo "no partial bot record"); response trả error message tương ứng E-EXBOT-001/002/003/004/005/006 | UC §4 A1-A3; SRS FR-EXBOT-001 + FR-EXBOT-002 |
| Fail LP mint thực tế sau khi bản ghi đã tạo (A4) | `bots.lifecycle_state='error'`; UC ghi "return funds" nhưng KHÔNG nêu cơ chế hoàn USDC vì NFT chưa mint thành công (xem I-04) | UC §4 A4; states.md transition `lp_opening → error` |
| Fail hedge open (chưa có alt flow trong UC) | UC KHÔNG nêu (xem I-04 + I-05); SRS FR-EXBOT-050 ngụ ý nếu HL API unreachable hoặc reconcile mismatch → enter SAFE_MODE | (gap UC) |
| Fail stop placement (chưa có alt flow trong UC) | UC KHÔNG nêu (xem I-04 + I-05); SRS states.md transition `stop_placing → safe_mode : stop placement fails` | (gap UC) |
| bot_safe_close downstream (sau active) | Sau HLD-2026-06-18: lifecycle chuyển thẳng `lp_closing → closed`; KHÔNG còn `cooldown`/`parked` state hay re-entry loop. `bot_safe_close` dùng `executeStrategy(RedeemStrategyV1)` → `RedemptionQueue.createRequest` → Operator `fulfillRequest` FIFO on-chain. | SRS states.md Note HLD-2026-06-18; frd.md changelog 2026-06-18 |

**Lưu ý:** UC §2 và §5 tham chiếu BR-EXBOT-001 và BR-EXBOT-010. Nội dung verbatim của hai rule này được resolve trong `srs/spec.md` §4 (KHÔNG nằm trong `02_backbone/common-rules.md` như cấu trúc tham chiếu mặc định — xem I-10):

```text
BR-EXBOT-001: Phase A: 1 user = 1 active ExBot. `status IN ('active','paused','closing','safe_mode','error')` all count toward the limit. (Nguồn: srs/spec.md §4)

BR-EXBOT-010: ExBot Worker (`apps/bnza-exbot/`) must not be co-deployed with OPERATOR (`apps/bnza-operator/`). They communicate via CF service binding only. (Nguồn: srs/spec.md §4)
```

---

## 4 và ## 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Chức năng: Bot Start (preflight → mint LP → mở hedge → đặt stop → active)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | USDC Investor | Submit start request qua POOL UI | POOL UI gọi OPERATOR `POST /api/exbot/start` | — | — | UC §3.1; SRS FR-EXBOT-090 |
| 2 | OPERATOR Facade | Nhận `POST /api/exbot/start`, internal-token auth, forward qua service binding | Forward request tới ExBot Worker | — | Nếu request đến trực tiếp ExBot Worker từ internet → 403 (FR-EXBOT-090) | UC §3.2; SRS FR-EXBOT-090 |
| 3 | ExBot Worker | Chạy preflight check 1 — one-bot policy: `SELECT count(*) FROM bot_registry WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')` | Nếu count = 0 → tiếp tục check 2 | — | Nếu count > 0 → A1 reject với E-EXBOT-001 ("You already have an active ExBot. Close or wait for the existing bot to finish.") | UC §3.3, §4 A1; SRS FR-EXBOT-001; spec.md §5 E-EXBOT-001 |
| 4 | ExBot Worker | Preflight check 2 — fetch HL `marginSummary`, compute `marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage`, verify `marginBalanceUsd ≥ marginRequiredUsd × 2.0` | Nếu đủ → tiếp tục check 3 | — | Nếu thiếu → A2 block với E-EXBOT-002 ("Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL.") | UC §3.3, §4 A2; SRS FR-EXBOT-002 + FR-EXBOT-061; spec.md §5 E-EXBOT-002 |
| 5 | ExBot Worker | Preflight check 3 — query `hl_agent_keys` cho user, verify `approval_status='approved'` AND `expires_at > now` | Nếu approved + not expired → tiếp tục check 4 | — | (a) Pending → E-EXBOT-003; (b) Expired → E-EXBOT-004; (c) Revoked / superseded → UC KHÔNG nêu (xem I-04) | UC §3.3, §4 A3; SRS FR-EXBOT-081 + FR-EXBOT-082 + FR-EXBOT-083 |
| 6 | ExBot Worker | Preflight check 4 — confirm builder fee 5bps đã approved trên HL (cơ chế chính xác chưa chốt — OQ-EXBOT-05) | Nếu confirmed → tiếp tục check 5 | — | Nếu chưa → E-EXBOT-005 ("HL builder fee (5bps) approval required before starting ExBot."); UC KHÔNG có alt flow tường minh (xem I-04) | UC §2 + §3.3; SRS FR-EXBOT-002 step 4; OQ-EXBOT-05 |
| 7 | ExBot Worker | Preflight check 5 — simulate `BnzaExVault.vaultMint(...)` với `slippageBps` planned | Nếu pass → tiếp tục step 8 | — | Nếu fail → E-EXBOT-006 ("LP mint simulation failed. Check pool liquidity or adjust deposit amount."); UC KHÔNG có alt flow tường minh (xem I-04) | UC §3.3 (preflight step 5); SRS spec.md §5 E-EXBOT-006 |
| 8 | ExBot Worker | Tạo bot record vào D1: insert `bot_registry` (control_db) + `bots` (state_db_shard), set `lifecycle_state='preflight'`, populate `shard_id = hash(bot_id) % shard_count`, `chain`, `wallet_address` | Bản ghi `bots` được persist nguyên tử | — | Nếu D1 insert fail → UC KHÔNG nêu (xem I-04) | UC §3.4; ERD `bots`, `bot_registry`; SRS FR-EXBOT-003 |
| 9 | ExBot Worker | Set `lifecycle_state='lp_opening'`, gọi `BnzaExVault.vaultMint(user, tickLower, tickUpper, amount0, amount1, slippageBps)` on-chain | Tx được submit; chờ event `VaultMinted(user, botId, tokenId, liquidity)` | — | A4: LP mint fails → `lifecycle_state='error'`, "return funds"; UC KHÔNG nêu cụ thể cách hoàn USDC (xem I-04 + I-09) | UC §3.5, §4 A4; SRS flows.md F-03; states.md `lp_opening → error` |
| 10 | ExBot Worker | Nhận event `VaultMinted`; insert `positions` row với `tokenId`, `pool_address`, `token0`, `token1`, `fee`, `tickLower`, `tickUpper`, `liquidity`, `wethIndex`, `token0_decimals`, `token1_decimals`, `custodian='vault'`, `custodian_address`; transition `lp_opening → lp_opened` | `positions` row persisted; `bots.lifecycle_state='lp_opened'` | — | Nếu event watcher mất kết nối / lag → UC KHÔNG nêu (xem I-13) | UC §3.6; ERD `positions`; states.md transition |
| 11 | ExBot Worker | Compute `lpEthAmount` từ `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick` qua TickMath + LiquidityAmounts; compute `targetShortEth = lpEthAmount × hedgeRatio` (Phase A 0.70 — xem I-08); transition `lp_opened → hedge_pre_open` | Transition state persisted | — | — | UC §3.7; SRS FR-EXBOT-020 + FR-EXBOT-021; states.md transition; UC KHÔNG đề cập state trung gian `hedge_pre_open` — xem I-06 |
| 12 | ExBot Worker | Compute deterministic `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))`; gọi HL `openShortIoc(targetSize, cloid)` | HL ack lệnh IOC | — | (a) HL trả error reject (insufficient margin trong sync) → E-EXBOT-007; (b) HL unreachable → E-EXBOT-008 + SAFE_MODE; UC KHÔNG nêu (xem I-04) | UC §3.7; SRS FR-EXBOT-022 + FR-EXBOT-024; spec.md §5 |
| 13 | ExBot Worker | Post-order reconcile: fetch `clearinghouseState`, verify actual short size = target ± tolerance, extract `entry_price`, `liquidation_price`, `effective_leverage` | Reconcile pass; values lưu vào `hedge_legs`; transition `hedge_pre_open → hedge_post_confirmed` | — | Reconcile mismatch (actual ≠ expected) → SAFE_MODE (E-EXBOT-011); UC KHÔNG nêu (xem I-04) | UC §3.8-9; SRS FR-EXBOT-025; FR-EXBOT-050 trigger |
| 14 | ExBot Worker | Compute `liq_distance_pct = (liquidation_price − entry_price) / entry_price` (fallback `1 / effective_leverage` nếu HL không trả `liquidationPx`); `stop_distance_pct = liq_distance_pct × stopSafetyFactor` (Phase A `stopSafetyFactor = 0.70`); `stop_trigger_px = entry_price × (1 + stop_distance_pct)` — toàn bộ BigDecimal | `stop_trigger_px` tính xong | — | Nếu `effective_leverage > 4.5` → SAFE_MODE (FR-EXBOT-050); UC KHÔNG nêu | UC §3.10; SRS FR-EXBOT-030 |
| 15 | ExBot Worker | Transition `hedge_post_confirmed → stop_placing`; gọi HL `placeReduceOnlyStopMarket(stopTriggerPx, size, cloid)` | Stop được place; lưu `stop_cloid`, `stop_order_id`, `stop_price`, `stop_size`, `stop_distance_pct`, `stop_last_verified_at` vào `hedge_legs` | — | Stop placement fail → E-EXBOT-009 ("Failed to place native stop on Hyperliquid. Bot cannot activate without a stop.") → `stop_placing → safe_mode`; UC KHÔNG nêu (xem I-04 + I-06: state `stop_placing` không xuất hiện trong UC) | UC §3.10; SRS FR-EXBOT-031; spec.md §5; states.md `stop_placing → safe_mode`. **Note HLD-2026-06-18:** frd.md FR-EXBOT-031 còn chứa text cũ "3 stops within 7 days → bot_safe_close → §16.7 cooldown closed loop" — §16.7 re-entry loop đã bị drop; xem I-22. |
| 16 | ExBot Worker | Sau khi stop confirmed → transition `stop_placing → stop_verified → active`; set `bots.status='active'`; init `bot_runtime_state` với `next_light_check_at = now + 5min + jitter(±45s)`; init `circuit_breakers` với `state='closed'` | Bot ở trạng thái `active` | — | — | UC §3.11; SRS FR-EXBOT-003 + FR-EXBOT-013 + FR-EXBOT-040; ERD |
| 17 | ExBot Worker | Trả response `{status: active, botId}` qua service binding | OPERATOR forward về POOL UI | — | — | UC §3.12; SRS FR-EXBOT-090 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| BR-EXBOT-001 — one-bot policy | `COUNT(bot_registry) WHERE user_id=? AND bot_type='ex' AND status IN ('active','paused','closing','safe_mode','error')` = 0 | Yes | Cho phép tạo bot mới | Reject với E-EXBOT-001, không insert bot record | UC §6; SRS §4 BR-EXBOT-001; FR-EXBOT-001 |
| BR-EXBOT-010 — Worker tách deploy | ExBot Worker `apps/bnza-exbot/` không co-deploy với OPERATOR; chỉ giao tiếp qua CF service binding | Yes | Architecture hợp lệ | Direct HTTP tới ExBot Worker bị 403 | UC §6; SRS §4 BR-EXBOT-010; FR-EXBOT-090 |
| HL margin buffer 2.0x | `marginBalanceUsd ≥ marginRequiredUsd × 2.0` với `marginRequiredUsd = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage` | Yes | Pass preflight check 2 | Block với E-EXBOT-002 + display required deposit | SRS FR-EXBOT-061; FRD FR-EXBOT-001 step 2 |
| Agent key approval | `hl_agent_keys.approval_status='approved'` AND `expires_at > now` | Yes | Pass preflight check 3 | Block: pending → E-EXBOT-003; expired → E-EXBOT-004 | SRS FR-EXBOT-081 + FR-EXBOT-083 |
| Builder fee 5bps | Builder fee đã approved trên HL (cơ chế chưa chốt — OQ-EXBOT-05) | Yes | Pass preflight check 4 | Block với E-EXBOT-005 | SRS FR-EXBOT-002 step 4; OQ-EXBOT-05 |
| LP mint simulation | Simulation `vaultMint` pass với slippage tolerance (ngưỡng cụ thể chưa nêu — xem I-11) | Yes | Pass preflight check 5 | Block với E-EXBOT-006 | FRD FR-EXBOT-001 step 5 |
| BigDecimal cho tài chính | Mọi tính `targetShortEth`, `stop_trigger_px`, `marginRequiredUsd` phải BigDecimal; cấm `Number()` trên giá trị tài chính | Yes (invariant NFR) | Tính đúng tới precision | Bug nghiệp vụ — không có thông báo runtime | NFR-EXBOT-008; SRS FR-EXBOT-021 + FR-EXBOT-030 |
| `wethIndex` per-chain | Phải verify `wethIndex` (0 hay 1) per chain và lưu vào `positions.weth_index` ở thời điểm LP open; KHÔNG hardcode | Yes | LP ETH amount calc đúng | LP amount sai → hedge sai → drift / SAFE_MODE; nguồn pool address + wethIndex Phase 0 chưa chốt (OQ-EXBOT-03) | SRS FR-EXBOT-004; NFR-EXBOT-009 |
| Cloid deterministic | `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | Yes | HL khử trùng lặp lệnh; retry an toàn | Double-order risk; mismatch retry path | SRS FR-EXBOT-024 |
| Atomic D1 transition | Mỗi transition lifecycle persist vào D1 trước khi tiến tới bước sau | Yes | Crash giữa chừng vẫn recover được | UC không nêu rõ recovery path nếu Worker crash giữa lp_opened và hedge_pre_open (xem I-04) | SRS FR-EXBOT-003 |
| Operator Facade auth | Direct HTTP tới ExBot Worker phải 403; chỉ chấp nhận service binding với internal token | Yes | Bảo vệ surface | Internet access → bypass auth | SRS FR-EXBOT-090; BR-EXBOT-010 |

Diễn giải các rule được tham chiếu bằng mã:

```text
BR-EXBOT-001: Phase A: 1 user = 1 active ExBot. `status IN ('active','paused','closing','safe_mode','error')` all count toward the limit. (Nguồn: srs/spec.md §4 — KHÔNG có trong common-rules.md)

BR-EXBOT-010: ExBot Worker (`apps/bnza-exbot/`) must not be co-deployed with OPERATOR (`apps/bnza-operator/`). They communicate via CF service binding only. (Nguồn: srs/spec.md §4)
```

#### C. Thông báo, lỗi và phản hồi hệ thống (API response / state change / event / message)

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| One-bot policy fail | API error 409 | "You already have an active ExBot. Close or wait for the existing bot to finish." | E-EXBOT-001 | SRS spec.md §5 |
| HL margin không đủ ở preflight | API error 400 | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | E-EXBOT-002 | SRS spec.md §5; FR-EXBOT-061 |
| Agent key pending | API error 400 | "Agent key is awaiting approval. Please complete the approval process before starting." | E-EXBOT-003 | SRS spec.md §5. UC §4 A3 ghi "Agent key must be approved first" — KHÔNG khớp verbatim (xem I-16) |
| Agent key expired | API error 400 | "Your HL agent key has expired. Please submit a new one." | E-EXBOT-004 | SRS spec.md §5; FR-EXBOT-083. UC KHÔNG có alt flow riêng cho expired (gộp vào "pending" — xem I-04) |
| Builder fee chưa approved | API error 400 | "HL builder fee (5bps) approval required before starting ExBot." | E-EXBOT-005 | SRS spec.md §5. UC KHÔNG có alt flow tường minh (xem I-04) |
| LP mint simulation fail | API error 400 | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | E-EXBOT-006 | SRS spec.md §5. UC KHÔNG có alt flow tường minh (xem I-04) |
| HL từ chối hedge open IOC (insufficient margin during sync) | API error 502 | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." | E-EXBOT-007 | SRS spec.md §5. UC KHÔNG có alt flow (xem I-04) |
| HL API unreachable giữa hedge open | API error 503 + state change SAFE_MODE | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | E-EXBOT-008 | SRS spec.md §5; FR-EXBOT-050. UC KHÔNG nêu (xem I-04) |
| Stop placement fail | API error 502 + state change SAFE_MODE | "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | E-EXBOT-009 | SRS spec.md §5; states.md `stop_placing → safe_mode`. UC KHÔNG nêu (xem I-04) |
| Reconcile mismatch sau hedge open | Internal alert + state change SAFE_MODE | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | E-EXBOT-011 | SRS spec.md §5; FR-EXBOT-050. UC KHÔNG nêu (xem I-04) |
| Happy path completion | API 200 + state change `active` | `{status: active, botId}` | (không có E-code) | UC §3.12; SRS FR-EXBOT-003 |
| Event chain on-chain | Emitted event | `VaultMinted(user, botId, tokenId, liquidity)` | BnzaExVault ABI (OQ-EXBOT-08 — final ABI pending) | UC §3.5; SRS flows.md F-03 |
| State transition logging | D1 atomic write | `bots.lifecycle_state` chuyển qua 8 giá trị: `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active` | (không có message) | SRS FR-EXBOT-003; states.md |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Khi bot chuyển `active` ở step 17 | UC-EXBOT-light-check | Cron `bot-scan` (1 phút) sẽ pick bot mới khi `next_light_check_at <= now`; light-check sẽ bắt đầu monitor drift/range/margin | Verify bản ghi mới có `next_light_check_at` đặt đúng `now + 5min + jitter(±45s)`; light-check không gọi HL (NFR HL weight 0) | SRS FR-EXBOT-012 + FR-EXBOT-013; flows.md F-01 |
| Khi `hedge_legs.stop_price` populated | UC-EXBOT-light-check (stop monitoring) + UC-EXBOT-bot-safe-close | Light-check sẽ check `markPrice >= stop_price`; stop monitoring chạy ngay cả khi circuit open. **HLD-2026-06-18:** nếu stop trigger dẫn đến `bot_safe_close`, lifecycle chuyển thẳng `lp_closing → closed` (không còn `cooldown`/`parked`/re-entry loop). | Verify `stop_price` BigDecimal, `stop_cloid` khớp HL `placeReduceOnlyStopMarket` response | SRS FR-EXBOT-014 + FR-EXBOT-032; states.md HLD-2026-06-18 note |
| Khi `hl_agent_keys` được decrypt để sign HL order | UC-EXBOT-agent-key | Plain DEK + plain agent key chỉ tồn tại trong scope function; sau use phải destroy; revoked / superseded key giữa luồng start sẽ gây fail | Verify log không chứa plain key; verify in-flight decrypt với revoked key → SAFE_MODE | SRS FR-EXBOT-080 + FR-EXBOT-082; NFR-EXBOT-006 |
| Khi gọi HL `marginSummary`, `openShortIoc`, `clearinghouseState`, `placeReduceOnlyStopMarket` | HLRateLimitDO (FR-EXBOT-091) | Tổng weight tiêu thụ phải ≤ 800/min; nếu DO trả `{allowed:false, retryAfterMs}` thì worker phải re-queue | UC KHÔNG đề cập việc tương tác với HLRateLimitDO ở giai đoạn start (xem I-17) | SRS FR-EXBOT-091; NFR-EXBOT-004 |
| Khi tính `lpEthAmount` trước hedge open | MarketDataDO (FR-EXBOT-093) | Phải đọc `sqrtPriceX96`, `currentTick` từ DO cache, không gọi RPC trực tiếp | UC KHÔNG đề cập (xem I-17); thiếu nguồn cho `liquidity` ở thời điểm trước-mint vs sau-mint (xem I-07) | SRS FR-EXBOT-093 |
| Khi multiple workers cùng start cho 1 user | UserLockDO (FR-EXBOT-092) | UC KHÔNG nêu có lease ở `/api/exbot/start`; rủi ro race-condition double-submit | UC KHÔNG đề cập (xem I-14 + I-17) | SRS FR-EXBOT-092 + FR-EXBOT-026 |
| Khi tx `vaultMint` đã submit nhưng event watcher chưa thấy `VaultMinted` | Event watcher / reconcile | UC KHÔNG nêu timeout / replay nếu event lag → state stuck ở `lp_opening` | (gap UC — xem I-13) | states.md `lp_opening` |
| Khi A4 LP mint fail giữa luồng | UC-EXBOT-bot-safe-close (terminus path?) | UC ghi "return funds" nhưng không nêu cơ chế: cleanup `bots` record? rollback ERC-20 approval? refund USDC (chưa transfer)? | UC KHÔNG đề cập (xem I-04 + I-09) | UC §4 A4; states.md `lp_opening → error` |
| Bot mới ảnh hưởng `bot_registry` count cho one-bot policy của user | UC-EXBOT-bot-start (chính nó) + UC-EXBOT-bot-safe-close | Sau khi bot `active`, mọi start mới của cùng user phải reject; sau khi bot `closed`, count phải giảm | Verify race: 2 request `/api/exbot/start` song song của cùng user — UC không nói (xem I-14) | UC §4 A1; SRS FR-EXBOT-001 |
| Mỗi step transition persist vào D1 | UC chính | Crash giữa step → state stuck; resume strategy chưa nêu | Verify recovery: sau crash ở `hedge_pre_open`, bot làm gì? (gap UC — xem I-04) | SRS FR-EXBOT-003 |
| Endpoint `POST /api/exbot/start` mở ở OPERATOR Facade | FRD §4.11 trace FR-EXBOT-100 (Actor=Admin) vs UC §1 (Actor=USDC Investor) | Vai trò gọi endpoint chưa thống nhất (xem I-15) | Verify request từ investor đi trực tiếp hay phải qua Admin | FRD §4.11; UC §1 |

---

## 8. Acceptance Criteria

> UC trace tới US-EXBOT-001 (us-001.md) — 4 AC. Bổ sung từ phân tích UC + SRS các AC suy luận (đánh dấu `Suy luận cần xác nhận`).

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — preflight pass, bot đi qua đủ 8 lifecycle state và chuyển `active` | User chưa có ExBot `active/paused/closing/safe_mode/error`; HL margin balance ≥ required × 2.0; agent key approved + not expired; builder fee approved; LP mint sim pass | Investor submit `/api/exbot/start` | Bot record được tạo với `lifecycle_state='preflight'` rồi tuần tự `lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`; `hedge_legs.stop_price`, `stop_cloid`, `entry_price`, `effective_leverage` đều populated; response trả `{status:active, botId}` | US-EXBOT-001 AC-EXBOT-001-1 |
| AC-02 | One-bot policy block — user đã có 1 ExBot active | User đã có 1 ExBot `status='active'` | Investor submit `/api/exbot/start` | Reject với E-EXBOT-001 verbatim; không tạo bot record mới; bản ghi cũ giữ nguyên | US-EXBOT-001 AC-EXBOT-001-2 |
| AC-03 | Insufficient HL margin — block ở preflight check 2 | `marginBalanceUsd = $300`; `marginRequiredUsd × 2.0 = $700` | Investor submit `/api/exbot/start` | Block với E-EXBOT-002: "Required HL margin: $700 (with 100% buffer). Current: $300. Please deposit an additional $400 to HL."; không tạo bot record | US-EXBOT-001 AC-EXBOT-001-3 |
| AC-04 | Agent key chưa approved — block ở preflight check 3 | `hl_agent_keys.approval_status='pending'` | Investor submit `/api/exbot/start` | Block với E-EXBOT-003: "Agent key is awaiting approval. Please complete the approval process before starting."; không tạo bot record | US-EXBOT-001 AC-EXBOT-001-4 (lưu ý UC §4 A3 ghi message khác — xem I-16) |
| AC-05 | Agent key expired — block ở preflight check 3 (Suy luận cần xác nhận) | `hl_agent_keys.approval_status='approved'` AND `expires_at < now` | Investor submit `/api/exbot/start` | Block với E-EXBOT-004: "Your HL agent key has expired. Please submit a new one."; không tạo bot record | Suy luận từ SRS FR-EXBOT-083; UC + US chưa có AC cho expired |
| AC-06 | Builder fee chưa approved — block ở preflight check 4 (Suy luận cần xác nhận) | Builder fee 5bps chưa confirmed | Investor submit `/api/exbot/start` | Block với E-EXBOT-005; không tạo bot record | Suy luận từ SRS spec.md §5 E-EXBOT-005; cơ chế confirm còn pending OQ-EXBOT-05 |
| AC-07 | LP mint simulation fail (Suy luận cần xác nhận) | Slippage > tolerance (ngưỡng cụ thể chưa nêu — I-11) | Investor submit `/api/exbot/start` | Block với E-EXBOT-006; không tạo bot record | Suy luận; UC + US chưa nêu |
| AC-08 | LP mint thực tế fail (A4) — bot rơi `error` (Suy luận cần xác nhận) | Preflight pass; tx `vaultMint` revert on-chain | ExBot Worker submit tx | `bots.lifecycle_state='error'`; UC §4 A4 ghi "return funds" nhưng cơ chế hoàn tiền chưa định nghĩa (I-09); state `error` yêu cầu admin resolution | Suy luận từ states.md `lp_opening → error`; UC mô tả mơ hồ |
| AC-09 | HL hedge open IOC reject — insufficient margin during sync (Suy luận cần xác nhận) | Preflight pass; LP minted; HL trả error khi `openShortIoc` | ExBot Worker submit short IOC | Bot transition về SAFE_MODE; E-EXBOT-007 alert; LP NFT đã mint phải được rollback hoặc giữ tới reconcile/admin (UC không nêu) | Suy luận; UC + SRS chưa định nghĩa rollback LP khi hedge fail (I-04) |
| AC-10 | HL API unreachable giữa hedge open (Suy luận cần xác nhận) | HL down > 5 min giữa luồng start | ExBot Worker gọi `openShortIoc` | SAFE_MODE entry; E-EXBOT-008; bot không transition `active`; recovery khi HL response + 3 reconcile pass | Suy luận từ SRS FR-EXBOT-050; UC chưa cover |
| AC-11 | Stop placement fail (Suy luận cần xác nhận) | Preflight pass; LP minted; hedge open + reconcile pass; HL từ chối `placeReduceOnlyStopMarket` | ExBot Worker submit stop | `lifecycle_state` transition `stop_placing → safe_mode`; E-EXBOT-009; bot KHÔNG đạt `active` | Suy luận từ states.md `stop_placing → safe_mode`; SRS FR-EXBOT-031; UC chưa cover |
| AC-12 | Reconcile mismatch sau hedge open (Suy luận cần xác nhận) | Preflight pass; LP minted; HL `openShortIoc` ack nhưng `clearinghouseState` báo size khác target | ExBot Worker reconcile | SAFE_MODE entry; E-EXBOT-011; KHÔNG ghi success vào `rebalance_attempts` | Suy luận từ SRS FR-EXBOT-025 + FR-EXBOT-050; UC chưa cover |
| AC-13 | Direct internet access tới ExBot Worker (security) (Suy luận cần xác nhận) | Attacker gọi trực tiếp ExBot Worker URL | HTTP request bất kỳ | Trả 403; OPERATOR-side log không show service binding event | Suy luận từ SRS FR-EXBOT-090 + BR-EXBOT-010; UC chưa cover |
| AC-14 | Double-submit `/api/exbot/start` cho cùng 1 user (concurrency) (Suy luận cần xác nhận) | User submit 2 request song song; 0 bot active hiện có | ExBot Worker xử lý concurrent | Đúng 1 bot được tạo; request thứ 2 reject với E-EXBOT-001 hoặc lock-based skip | Suy luận; UC + SRS chưa nêu cơ chế idempotency / lease ở Facade (I-14) |
| AC-15 | Base bot + Optimism bot cho 2 user khác nhau chạy song song (dual-chain) (Suy luận cần xác nhận) | User A start trên Base; user B start trên Optimism; pool address + wethIndex per-chain valid | Cả 2 submit start song song | Cả 2 bot reach `active`; `positions.weth_index` populated đúng per chain; KHÔNG hardcoded | Suy luận từ SRS FR-EXBOT-004 + NFR-EXBOT-009; phụ thuộc OQ-EXBOT-03 |

Nguyên tắc:
- Mọi AC suy luận trên đây đều ghi `Suy luận cần xác nhận` để BA / QC Lead review.
- AC-01..04 trace verbatim US-EXBOT-001; AC-05..15 mở rộng để cover các đường dẫn lỗi mà UC body không ghi rõ.

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | NFR-EXBOT-001: scan 10,000 bots / 5-min cycle = 33.3 bots/sec sustained | UC bot-start không trực tiếp test scale này nhưng bot mới phải được pick bởi scan (next_light_check_at), nên init đúng `next_light_check_at` ảnh hưởng phân bố scan | SRS NFR §3 |
| Performance | NFR-EXBOT-002: 1 hedge-sync < 30s under normal conditions | UC bot-start chứa 1 hedge open IOC + reconcile + stop place — tổng latency mong đợi? UC KHÔNG nêu ngưỡng tổng (xem I-18) | SRS NFR §3 |
| Rate Limit | NFR-EXBOT-004: HL API ≤ 800 weight/min (67% của 1,200 hard) | Preflight check 2 (`marginSummary`) + reconcile (`clearinghouseState`) + `openShortIoc` + `placeReduceOnlyStopMarket` = nhiều HL call; phải đi qua HLRateLimitDO; UC KHÔNG đề cập (xem I-17) | SRS FR-EXBOT-091; IC-EXBOT-001 |
| Security | NFR-EXBOT-006: master private key never stored; agent key AES-GCM envelope; plain key function-scope only, never logged | UC dùng agent key để sign HL orders; cần verify: log không chứa plain key, key destroyed sau use, revoked/superseded key bị reject giữa luồng | NFR §3; FR-EXBOT-080..083 |
| Reliability / Resilience | NFR-EXBOT-010: SAFE_MODE và bot_safe_close không phải terminal — autonomous recovery | UC bot-start nếu fail vào SAFE_MODE giữa luồng phải có path recovery; UC không nêu (xem I-04) | SRS NFR §3; FR-EXBOT-050 |
| Idempotency | NFR-EXBOT-007: queue consumers UNIQUE idempotency ledger | `/api/exbot/start` không phải queue consumer; UC không nêu idempotency mechanism cho REST API (xem I-14) | SRS NFR §3 |
| Precision | NFR-EXBOT-008: BigDecimal cho mọi tính toán hedge/stop/margin; cấm float | Mọi test math (margin, stopTriggerPx, targetShortEth) phải verify không có Number() conversion intermediate | SRS NFR §3 |
| Compatibility / Integration | NFR-EXBOT-009: dual-chain Base + Optimism từ Phase 1; `wethIndex` per chain verify | Test phải có 2 chain; nhưng pool address + wethIndex chưa chốt (OQ-EXBOT-03 — I-13) | SRS NFR §3 |
| Audit / Logging | (chưa có NFR explicit cho audit log) | UC KHÔNG nêu yêu cầu log audit trail của các transition `bots.lifecycle_state` — cần BA xác nhận policy | (gap) |
| Privacy / Compliance | (chưa có NFR cho data privacy của hl_user_address, wallet_address) | UC KHÔNG nêu PII handling / GDPR; cần BA xác nhận nếu áp dụng | (gap) |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-01 (Q1) | High (Blocker) | CROSS_SOURCE_CONFLICT | `frd.md` §4.1-4.4 vs `srs/spec.md` §2; UC §7 FR Trace | Cùng prefix `FR-EXBOT-NNN` xuất hiện ở cả `frd.md` và `srs/spec.md` nhưng trỏ tới hai nội dung khác nhau. Ví dụ: FR-EXBOT-001 trong FRD = "Bot Initialization (PREFLIGHT)"; trong SRS = "One-Bot-Per-User Policy". FR-EXBOT-030 trong FRD = "Stop Placement" (compute + place); trong SRS = "Stop Trigger Price Computation". FR-EXBOT-031 trong FRD = "Stop-Trigger Crossed Handling"; trong SRS = "Stop Placement After Hedge Open". UC §7 ghi "FR-EXBOT-001, 002, 004, 020, 030, 031" mà KHÔNG nói đang trace tới văn bản nào. Tester đọc UC không thể biết phải mở FRD hay SRS để verify. Yêu cầu BA: thống nhất một sơ đồ đánh số (hoặc đánh dấu prefix `FR-EXBOT-FRD-NNN` vs `FR-EXBOT-SRS-NNN`, hoặc rebase SRS theo FRD), và update UC trace tương ứng. | Mọi test step trace lại FR đều mơ hồ; ảnh hưởng toàn bộ Issue Register; cũng cản đường nhánh UC khác. | BA + QC Lead | Open |
| I-02 (Q2) | Medium | INTERNAL_INCONSISTENCY | `usecases/index.md` row UC-EXBOT-bot-start vs UC §7 | Index ghi `FR Trace = FR-001,002,003,004,020,030,031` (7 FR — có FR-003); UC body §7 ghi `FR-EXBOT-001, 002, 004, 020, 030, 031` (6 FR — không có FR-003). FR-EXBOT-003 trong FRD là "Pause/Resume" — KHÔNG liên quan UC bot-start. Cần thống nhất bỏ FR-003 khỏi index. | Sai trace có thể khiến tester thiết kế nhầm test pause/resume vào UC bot-start. | BA | Open |
| I-03 (Q3) | Medium | INTERNAL_INCONSISTENCY | `usecases/index.md` row UC-EXBOT-bot-start vs UC body §7 | Index row UC-EXBOT-bot-start liệt kê thêm `FR-003` so với UC body — và UC body cũng KHÔNG bao gồm FR-EXBOT-003 (Bot Lifecycle State Tracking — trong SRS) dù chính bản UC body mô tả đầy đủ 8-state initialization sequence (`idle → preflight → ... → active`). FR trace có nên thêm FR-EXBOT-003 (SRS) không, hay bỏ hoàn toàn? | Ảnh hưởng đến RTM (Requirement Traceability Matrix); nếu test cover lifecycle nhưng requirement không trace thì coverage report bị sai. | BA | Open |
| I-04 (Q4) | High (Blocker) | MISSING_INFO | UC §4 (Alternate Flows) | UC chỉ liệt kê 4 alt flow: A1 one-bot fail, A2 margin insufficient, A3 agent key pending, A4 LP mint fails. UC THIẾU các alt/exception flow quan trọng đã có E-code và state transition trong SRS: (a) agent key expired (E-EXBOT-004); (b) builder fee chưa approved (E-EXBOT-005); (c) LP mint simulation fail (E-EXBOT-006) — KHÁC với A4 (mint thực tế fail); (d) HL hedge IOC reject (E-EXBOT-007); (e) HL API unreachable giữa luồng (E-EXBOT-008 + SAFE_MODE); (f) stop placement fail (E-EXBOT-009 + transition `stop_placing → safe_mode`); (g) reconcile mismatch sau hedge open (E-EXBOT-011 + SAFE_MODE); (h) D1 insert fail; (i) event watcher mất event `VaultMinted`; (j) worker crash giữa transition. Tester không thể thiết kế test cho các nhánh này từ UC. | Mất hơn nửa số test path; vi phạm scoring rule "Area 3 covers happy path only and omits important alternative / exception paths" → Area 3 capped. | BA | Open |
| I-05 (Q5) | Medium | UNCLEAR_INFO | UC §4 A4 vs states.md `lp_opening → error` | A4 ghi "LP mint fails: enter `error` state, return funds". KHÔNG rõ: (a) "LP mint fails" là sim fail (preflight check 5) hay tx thực tế revert? (b) "return funds" là rollback USDC ERC-20 transfer hay refund USDC từ wallet? Tx `vaultMint` consume USDC từ user wallet (suy luận) — nếu revert thì on-chain tự rollback, nhưng nếu Worker mất event sau khi tx success thì sao? | Phân biệt sim fail vs tx fail dẫn đến hai test path khác nhau; "return funds" mechanism ảnh hưởng on-chain test. | BA + Dev (zen cho contract refund logic) | Open |
| I-06 (Q6) | Medium | INTERNAL_INCONSISTENCY | UC §3 main flow vs states.md | UC main flow steps 7-11 KHÔNG đề cập tới các state trung gian `hedge_pre_open` và `stop_placing`, dù states.md liệt kê chúng và phân biệt rõ behavior (light-check skip ở các state này). UC body chỉ ghi `lp_opened → hedge_post_confirmed` và `stop_verified → active`, làm tester có thể tưởng `hedge_pre_open` và `stop_placing` không tồn tại. | Test coverage cho behavior "light-check skip ở state transitional" sẽ bị thiếu nếu UC không nhắc tên state. | BA | Open |
| I-07 (Q7) | High | MISSING_INFO | UC §3.7 + SRS FR-EXBOT-020 | UC §3.7 dùng `lpEthAmount` để compute `targetShortEth` TRƯỚC hedge open. SRS FR-EXBOT-020 ghi `lpEthAmount` được tính từ `liquidity, tickLower, tickUpper, sqrtPriceX96, currentTick`. NHƯNG ở thời điểm trước-mint, `liquidity` chưa tồn tại (LP NFT chưa mint). UC không nói nguồn của `lpEthAmount` ở giai đoạn này — có thể là từ deposit amount + planned tick range, nhưng KHÔNG có công thức rõ. | Tester không thể test happy path đầu-đến-cuối nếu không biết nguồn input của hedge size. Ảnh hưởng AC-15 dual-chain. | BA + zen (PositionCalc owner) | Open |
| I-08 (Q8) | High | AMBIGUOUS_WORDING | UC §3.7 + §3.10 | UC §3.7 ghi `targetShortEth = lpEthAmount × 0.70` (hardcode 0.70 — đáng lẽ phải là tên tham số `hedgeRatio`). UC §3.10 ghi `(BigDecimal, safetyFactor=0.70)` — hardcode 0.70 — là `stopSafetyFactor`. Hai `0.70` này TRÙNG GIÁ TRỊ NHƯNG KHÁC Ý NGHĨA: `hedgeRatio` quyết định kích thước hedge; `stopSafetyFactor` quyết định khoảng cách stop. SRS FR-EXBOT-021 đặt tên `hedgeRatio`; SRS FR-EXBOT-030 đặt tên `stopSafetyFactor`. UC làm tester nhầm chúng là cùng 1 tham số. Đề nghị UC ghi rõ tên tham số (`× hedgeRatio (Phase A = 0.70)` và `safetyFactor=stopSafetyFactor (Phase A = 0.70)`). | Tester có thể viết test sai (chỉ change 1 giá trị nhưng thay vào lại nhầm sang giá trị khác). Cũng làm rule resolution mơ hồ. | BA | Open |
| I-09 (Q9) | Medium | MISSING_INFO | UC §2 preconditions; B5 trong blockchain checklist | UC §2 preconditions không nêu các điều kiện on-chain bắt buộc trước khi gọi `vaultMint`: (a) user đã approve token USDC cho BnzaExVault với amount đủ; (b) user có đủ native ETH (Base / OP) để trả gas; (c) nonce / chain id verify; (d) approval mechanism (signed-data matches displayed data). Cũng không nêu xử lý khi gas estimation fail hoặc tx pending lâu. | Tester thiếu precondition on-chain dẫn tới test sai expectation; thiếu coverage cho path edge case ERC-20 approve insufficient. | BA + zen (cho ERC-20 flow) | Open |
| I-10 (Q10) | Medium | CROSS_SOURCE_CONFLICT | `input-files-format.md` §3 vs reality | Per skill spec: `BR-<MOD>-<NNN>` phải resolve verbatim từ `02_backbone/common-rules.md` và `E-<MOD>-<NNN>` từ `02_backbone/message-list.md`. Thực tế: `02_backbone/common-rules.md` chỉ chứa BR-MOB, BR-EX, BR-PL, BR-ADM, BR-WLA — KHÔNG có BR-EXBOT-*. `02_backbone/message-list.md` chỉ chứa E-MOB, E-pool, E-ADM, E-WLA — KHÔNG có E-EXBOT-*. Tất cả BR-EXBOT-* và E-EXBOT-* hiện chỉ định nghĩa trong `03_modules/exbot/srs/spec.md` §4 và §5. Đề nghị BA: hoặc copy BR-EXBOT/E-EXBOT vào common-rules/message-list (giữ pattern thống nhất với các module khác), hoặc cập nhật skill registry (path-registry.md / input-files-format.md) để chấp nhận module-local resolution. | Mọi resolve verbatim của BR/E hiện phải đi đường vòng; tester không follow được pattern chuẩn. | BA + QC Lead (registry update) | Open |
| I-11 (Q11) | Medium | UNCLEAR_INFO | FRD FR-EXBOT-001 step 5; UC §3.3 | "LP mint simulation passes (slippage within tolerance)" — KHÔNG có giá trị slippage tolerance cụ thể (basis point). Phase A default? Cấu hình per-bot? Khi nào fail? | Tester không thể design AC-07 (LP mint sim fail) nếu không biết ngưỡng. | BA + zen | Open |
| I-12 (Q12) | Medium | MISSING_INFO | UC §3 + SRS FR-EXBOT-004 + FR-EXBOT-090 | UC KHÔNG mô tả payload của `POST /api/exbot/start` (request body). Chain (Base/Optimism) chọn ở đâu? Tick range chọn ở đâu (user input hay auto)? Deposit amount? Slippage? Nếu Base bot và Optimism bot đều xài cùng endpoint thì điều kiện switch là gì? | Tester không thể design test request payload; AC-15 (dual-chain) không verify được. | BA | Open |
| I-13 (Q13) | High | BLOCKED_EVIDENCE | OQ-EXBOT-03 (NV-12) | Pool addresses + `wethIndex` cho USDC/WETH 0.3% trên Base + Optimism chưa chốt (Phase 0 NV-12). Cho tới khi chốt, không thể test LP open thực tế trên 2 chain. UC tham chiếu FR-EXBOT-004 nhưng FR-EXBOT-004 phụ thuộc OQ này. | Test dual-chain bị block tới Phase 0; ảnh hưởng AC-15 và toàn bộ verify on-chain. | BA + zen | Open |
| I-14 (Q14) | Medium | MISSING_INFO | UC §3 + SRS FR-EXBOT-092 (UserLockDO) | UC KHÔNG nêu cơ chế idempotency / lock cho `POST /api/exbot/start`. Nếu user double-click hoặc retry, hai request có thể chạy concurrent. SRS FR-EXBOT-092 UserLockDO là cho hedge-sync, không nói về start endpoint. Cần BA xác nhận: dùng UserLockDO ở start cũng? Idempotency-Key header? Hay rely trên D1 UNIQUE constraint của `bot_registry`? | AC-14 (double-submit) không thể design AC chính xác; rủi ro race condition tạo 2 bot. | BA + Dev | Open |
| I-15 (Q15) | Medium | CROSS_SOURCE_CONFLICT | FRD §4.11 vs UC §1 | FRD §4.11 bảng Operator Facade Endpoints ghi Actor=Admin cho cả 5 endpoint. UC §1 ghi Primary Actor = USDC Investor (qua POOL UI → OPERATOR → ExBot Worker). Vậy `/api/exbot/start` do investor gọi trực tiếp hay phải qua Admin? Có 2 lớp endpoint khác nhau (investor-facing và admin-facing)? | Test role-based access bị mơ hồ; có thể vô tình verify wrong-role flow. | BA | Open |
| I-16 (Q16) | Low | INTERNAL_INCONSISTENCY | UC §4 A3 vs SRS E-EXBOT-003 | UC §4 A3 ghi message "Agent key must be approved first" và US-EXBOT-001 AC-EXBOT-001-4 ghi "message indicating the agent key must be approved before starting". E-EXBOT-003 verbatim ghi "Agent key is awaiting approval. Please complete the approval process before starting." Cần thống nhất chính xác wording. | Test assertion text mismatch sẽ fail; tester không biết bản verbatim nào đúng. | BA | Open |
| I-17 (Q17) | Medium | MISSING_INFO | UC §3 + SRS FR-EXBOT-091/092/093 | UC KHÔNG đề cập tương tác với 3 Durable Object: (a) HLRateLimitDO khi gọi mọi HL endpoint (margin, position, openShort, placeStop); (b) MarketDataDO khi đọc `sqrtPriceX96`/`currentTick` để compute `lpEthAmount`; (c) UserLockDO (nếu áp dụng — xem I-14). Tester có thể nghĩ ExBot gọi HL trực tiếp hoặc gọi RPC trực tiếp. | Test integration mismatch architecture; rate-limit budget verify không được. | BA | Open |
| I-18 (Q18) | Low | MISSING_INFO | NFR §3 vs UC §3 | NFR-EXBOT-002 nêu 1 hedge-sync < 30s. UC bot-start gồm preflight (HL margin fetch) + LP mint on-chain (block confirmation time) + hedge open + reconcile + stop place. Tổng latency expected cho UC bot-start? Khác nhau theo chain (Base ~2s blocktime vs Optimism ~2s blocktime nhưng L1 finality khác)? | Performance test cho start không có expected SLA. | BA | Open |
| I-19 (Q19) | Medium | MISSING_INFO | UC §2 preconditions vs SRS FR-EXBOT-083 (key rotation) | UC §2 nói "key approved + not expired" nhưng không nêu trường hợp: (a) key vừa được rotated (status đang `superseded`); (b) key đang `revoked`; (c) key mới `pending` trong khi key cũ vẫn `approved` thì lấy key nào để sign? FR-EXBOT-083 ghi "existing approved key remains active until admin approves replacement" — UC không trace tới rule này. | Ảnh hưởng test agent-key rotation cross-feature. | BA | Open |
| I-20 (Q20) | Low | UNTRACEABLE_SYNTHESIS | UC §3.11 vs SRS FR-EXBOT-013 | UC §3.11 nói chuyển sang `'active'` nhưng KHÔNG nêu các init action ở thời điểm `active`: set `next_light_check_at = now + 5min + jitter(±45s)`; init `circuit_breakers.state='closed'`; init `bot_runtime_state` row. Test "happy path → active" thiếu các verify post-condition này. | Test thiếu coverage cho init state. | BA | Open |
| I-21 (Q21) | Low | MISSING_INFO | UC §3 + NFR audit/logging | UC KHÔNG đề cập audit log: ai gọi start, khi nào, từ IP nào, log retention. Phase A có yêu cầu compliance log không? | Test audit trail không có scope; có thể là requirement của bnza-admin. | BA | Open |
| I-22 (Q22) | Major | CROSS_SOURCE_CONFLICT | `srs/flows.md` F-05 (updated: 2026-06-12, NOT 2026-06-18) vs `srs/spec.md` + `srs/states.md` + `frd.md` (all updated: 2026-06-18) | **EN:** `srs/flows.md` F-05 "bot_safe_close + Automatic Re-Entry" was NOT updated on 2026-06-18 and still contains the entire park/re-entry loop that was dropped by HLD decisions: `vaultClose(tokenId, dest=UNINVESTED)`, `FundsParked` event, `lifecycle_state=cooldown (60 min)`, `uninvestedBalanceOf(user, botId)`, `parked` state, and the `REENTRY` worker loop. All of this contradicts `srs/states.md` HLD-2026-06-18 note ("cooldown and parked lifecycle states removed — park/redeploy feature dropped. After bot_safe_close, lifecycle transitions directly to `closed`"), `srs/spec.md` FR-EXBOT-070/073 (updated), and `frd.md` changelog 2026-06-18 (ACT-M removed; bot_safe_close flow updated — drop park/re-entry). Also: `frd.md` FR-EXBOT-031 still contains text referencing "§16.7 cooldown closed loop". **VI:** `srs/flows.md` F-05 chưa được cập nhật theo HLD-2026-06-18 và còn toàn bộ nội dung park/re-entry đã bị drop: `vaultClose(tokenId, dest=UNINVESTED)`, event `FundsParked`, `lifecycle_state=cooldown (60 min)`, `uninvestedBalanceOf(user, botId)`, state `parked`, và `REENTRY` worker loop. Tất cả mâu thuẫn với `srs/states.md` (HLD-2026-06-18 note), `srs/spec.md` FR-EXBOT-070/073, và `frd.md` changelog 2026-06-18. Ngoài ra `frd.md` FR-EXBOT-031 còn tham chiếu "§16.7 cooldown closed loop". **Yêu cầu BA:** update `flows.md` F-05 để phản ánh `bot_safe_close → closed` trực tiếp; update FR-EXBOT-031 trong frd.md bỏ tham chiếu §16.7. | **Impact (EN):** Any tester reading `flows.md` F-05 gets a contradictory picture of `bot_safe_close` downstream behavior. Test design for UC-EXBOT-bot-safe-close is blocked until F-05 is aligned. Also misleads integration tests that check for `cooldown`/`parked` states or `uninvestedBalanceOf` — both are no longer in scope. **Impact (VI):** Tester đọc flows.md F-05 sẽ thiết kế test dựa trên cooldown/re-entry loop đã bị drop; test UC-EXBOT-bot-safe-close bị block cho tới khi F-05 được đồng bộ với HLD-2026-06-18. | BA (`@hienduong`) | Open |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| OQ-EXBOT-01 NV-1 HL `marginSummary` API field names | API contract / Integration | Preflight check 2 dùng `marginBalanceUsd` — chưa rõ tên field chính xác từ HL | zen / SOTATEK | Open |
| OQ-EXBOT-03 NV-12 Pool address + wethIndex (Base + Optimism) | Integration / Environment | LP open + dual-chain test bị block | zen / BNZA | Open |
| OQ-EXBOT-04 NV-13 HL ETH-USD perp min order size / dust | API contract | Có thể ảnh hưởng hedge open IOC ở edge case amount nhỏ | zen / SOTATEK | Open |
| OQ-EXBOT-05 NV-14 Builder fee 5bps approval flow (on-chain tx hay API call?) | Integration | Preflight check 4 cơ chế chưa rõ → AC-06 không design được | zen / SOTATEK | Open |
| OQ-EXBOT-08 BnzaExVault final ABI | Integration | Mọi call `vaultMint`, `redeem`, event `VaultMinted` đều phụ thuộc ABI cuối | zen | Open |
| OQ-EXBOT-09 MarketDataDO cache refresh interval | Integration | Ảnh hưởng độ tươi của `sqrtPriceX96` khi compute `lpEthAmount` | zen / SOTATEK | Open |
| OQ-EXBOT-11 `lpValueUsd` formula | API contract | (Light-check thresholds — không trực tiếp block UC start, nhưng post-active behavior) | zen | Open |
| Common-rules registry inclusion of BR-EXBOT-* | Documentation | Ảnh hưởng cách resolve BR verbatim trong test docs | BA + QC Lead | Open |
| Message-list registry inclusion of E-EXBOT-* | Documentation | Ảnh hưởng cách resolve E verbatim | BA + QC Lead | Open |
| FR numbering unification (FRD vs SRS) | Documentation (I-01) | Ảnh hưởng trace của mọi UC trong ExBot module | BA | Open |

### 10.3 Audit Summary

**Bảng điểm theo `references/scoring-rubric.md` (updated 2026-06-18):**

| # | Scoring Area | Max | Score | Status | Ghi chú |
|---|---|---|---|---|---|
| 1 | Function / Operation & Data Object Inventory | 20 | 12 | ⚠️ Partial | Inventory cấu trúc rõ (15 hạng mục §1.2) nhưng còn thiếu atomic mapping cho payload request, các state trung gian `hedge_pre_open` / `stop_placing` không xuất hiện trong main flow (I-06), nguồn `lpEthAmount` pre-mint chưa rõ (I-07). |
| 2 | Data Object / State Attributes, Business Rules, Validations & Messages | 25 | 13 | ⚠️ Partial | Cap 70% × 25 = 17.5 do CROSS_SOURCE_CONFLICT FR numbering (I-01). BR-EXBOT-001/010 cited; nhưng BR/E codes nằm trong spec.md không phải common-rules/message-list (I-10); message verbatim mismatch (I-16); state transitions trung gian bị skip (I-06). |
| 3 | Functional Logic & Workflow Decomposition | 25 | 13 | ⚠️ Partial | Cap 18/25 do happy path rõ nhưng alt/exception path thiếu nhiều (I-04: 10 nhánh thiếu); cap thêm 70% × 25 = 17.5 do contradiction. Lấy mức thấp hơn = 17. Trừ thêm vì A4 mơ hồ (I-05) và payload request thiếu (I-12). |
| 4 | Functional Integration & Data Consistency | 15 | 7 | ⚠️ Partial | Đề cập service binding + Vault + HL ở mức cao; KHÔNG đề cập HLRateLimitDO / MarketDataDO / UserLockDO interaction (I-17); thiếu phân tích on-chain ↔ off-chain consistency cho `VaultMinted` event watcher (I-13); concurrency ở Facade chưa rõ (I-14). |
| 5 | UC / Spec Documentation Quality Issues | 15 | 7 | ⚠️ Weak | Cap 8/15 áp dụng do CROSS_SOURCE_CONFLICT FR numbering (I-01) + ambiguous wording `0.70` (I-08). Index ≠ body FR trace (I-02-I-03), message verbatim mismatch (I-16), role conflict FRD-vs-UC (I-15). **I-22 (HLD-2026-06-18):** `flows.md` F-05 stale với toàn bộ park/re-entry loop — thêm CROSS_SOURCE_CONFLICT Major vào Area 5; cap đã đạt, không giảm thêm điểm nhưng tăng độ nghiêm trọng của Area 5. |
| **Tổng** | — | **100** | **52** | — | I-22 là Major CROSS_SOURCE_CONFLICT mới; Area 5 cap đã bị hit từ I-01, nên điểm tổng giữ nguyên 52/100. |

**Blockchain readiness checklist (§6b — UC này blockchain-dependent):**

| # | Trạng thái | Ghi chú |
|---|---|---|
| B1 Wallet/agent-key states & messages | ⚠️ Partial | UC nêu `approved + not expired`; thiếu xử lý `revoked` / `superseded` / `rotation in-progress` (I-19) |
| B2 Signing behavior | ❌ Missing | UC KHÔNG mô tả signing: agent key được decrypt khi nào, sign lệnh HL nào, replay/expiry handling (I-17) |
| B3 Required network/chain | ❌ Missing | Chain selector ở payload chưa nêu (I-12); pool address per-chain chờ NV-12 (I-13) |
| B4 Transaction lifecycle | ⚠️ Partial | `VaultMinted` event được nhắc; HL order pending/confirmed/dropped không nêu; timeout/replay event watcher chưa rõ (I-13) |
| B5 Pre-flight on-chain | ❌ Missing | Thiếu gas check, ERC-20 allowance check, decimals (I-09) |
| B6 Mid-flow events | ⚠️ Partial | Agent-key rotation / circuit-breaker open giữa start chưa nêu (I-19); SAFE_MODE giữa luồng chưa cover (I-04) |
| B7 On-chain ↔ off-chain consistency | ❌ Missing | Source of truth cho `tokenId` (Vault hay D1?), event watcher lag chưa rõ (I-13) |
| B8 Error/success messages verbatim | ⚠️ Partial | Có E-codes trong spec.md nhưng UC paraphrase (I-16) |
| B9 Security | ⚠️ Partial | NFR-006 quy định không lưu master key; UC không re-trace; signed-data match displayed data chưa nêu (I-17) |

**Blockers (Major) phải gỡ trước khi UC sang test-design giai đoạn chi tiết:**

1. **I-01 (CROSS_SOURCE_CONFLICT FR numbering)** — Mọi trace UC tới FR đều mơ hồ giữa FRD và SRS. BA + QC Lead cần thống nhất một sơ đồ đánh số duy nhất hoặc dùng prefix `FR-EXBOT-FRD-*` / `FR-EXBOT-SRS-*`.
2. **I-04 (MISSING_INFO alt/exception flows)** — UC chỉ có 4 alt flow trong khi SRS đã định nghĩa ít nhất 10 nhánh lỗi với E-code và state transition (E-EXBOT-004 đến E-EXBOT-011 + reconcile mismatch + worker crash recovery). UC bổ sung các alt flow này.
3. **I-13 (BLOCKED_EVIDENCE OQ-EXBOT-03 pool address + wethIndex)** — Test thực tế trên 2 chain bị block tới Phase 0 NV-12 hoàn tất.

**Major issues khác (không Blocker nhưng cần xử lý):**

- I-07 nguồn `lpEthAmount` pre-mint (UNCLEAR / MISSING).
- I-08 `0.70` ambiguity giữa `hedgeRatio` và `stopSafetyFactor` (AMBIGUOUS_WORDING).
- I-10 BR/E codes không nằm trong registry chuẩn (CROSS_SOURCE_CONFLICT về architecture tài liệu).
- I-12 payload request `POST /api/exbot/start` chưa được mô tả (MISSING_INFO).
- I-14 concurrency / idempotency cho start endpoint (MISSING_INFO).
- I-15 role/permission OPERATOR vs Investor mâu thuẫn FRD-vs-UC (CROSS_SOURCE_CONFLICT).
- I-17 không đề cập 3 Durable Object integrations (MISSING_INFO).
- **I-22 (NEW — HLD-2026-06-18):** `srs/flows.md` F-05 stale — toàn bộ park/re-entry loop chưa được xoá; mâu thuẫn với spec.md + states.md + frd.md đã cập nhật 2026-06-18. Tester đọc flows.md sẽ thiết kế test sai cho UC-EXBOT-bot-safe-close.

**Khuyến nghị kết luận / Conclusion (EN + VI):**

**EN:** UC-EXBOT-bot-start is **Not Ready** (score 52/100, below the 70-point threshold). The report was re-audited against HLD baseline 2026-06-18. Key changes from that baseline: `cooldown` and `parked` lifecycle states are removed; `bot_safe_close` transitions directly to `closed`; `uninvestedBalanceOf()` is no longer an integration surface; `emergencyTransfer` is now OPERATOR_ROLE only with no recipient parameter. A new cross-source conflict I-22 is added: `srs/flows.md` F-05 was not updated and still describes the dropped park/re-entry loop, contradicting spec.md, states.md, and frd.md (all updated 2026-06-18). The three original Blockers remain: FR numbering conflict (I-01), missing alt/exception flows (I-04), and blocked dual-chain evidence (I-13). Before proceeding to detailed test-case design, BA must resolve at minimum I-01, I-04, I-08, I-22, and clarify I-13 status.

**VI:** UC-EXBOT-bot-start hiện ở trạng thái **Not Ready** (tổng điểm 52/100, dưới ngưỡng 70). Báo cáo được re-audit theo HLD baseline 2026-06-18: các state `cooldown`/`parked` đã bị xoá; `bot_safe_close` chuyển thẳng sang `closed`; `uninvestedBalanceOf()` không còn trong integration surface; `emergencyTransfer` là OPERATOR_ROLE only, không có recipient param. Issue mới I-22 được thêm: `srs/flows.md` F-05 chưa được cập nhật và còn toàn bộ park/re-entry loop đã bị drop — mâu thuẫn trực tiếp với spec.md, states.md, và frd.md (cả 3 đã update 2026-06-18). Ba Blocker gốc vẫn còn: xung đột đánh số FR (I-01), thiếu alt/exception flows (I-04), và evidence dual-chain bị block (I-13). Trước khi thiết kế test cases chi tiết, BA cần xử lý tối thiểu I-01, I-04, I-08, I-22 và xác nhận trạng thái I-13.

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-17 | qc-uc-read-exbot agent | Tạo báo cáo audited lần đầu cho UC-EXBOT-bot-start |
| v1 (re-audit) | 2026-06-18 | qc-uc-read-exbot agent | Re-audit against HLD-2026-06-18: removed all cooldown/parked/re-entry references; corrected file paths docs/ba/ → docs/BA/; added new issue I-22 (flows.md F-05 stale); updated §3.2 postconditions, §6.1 step 15 note, §7 integration table; updated §10.3 Audit Summary scoring note and conclusion; added bilingual header and conclusion. Score unchanged 52/100. |
