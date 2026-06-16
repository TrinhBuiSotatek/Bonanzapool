# Project Context Master: Bonanzapool

**Trạng thái:** Draft  
**Ngày tạo/cập nhật:** 2026-06-15  
**Người chuẩn bị:** QC Context Agent  
**Người review:** QC Lead  
**Mục đích:** Cung cấp bối cảnh tổng quan cấp project để các QC Agent hiểu đúng hệ thống, phạm vi, rule chung, rủi ro và trạng thái tài liệu trước khi review spec, thiết kế scenario/test case, execute hoặc verify bug.

> File này là tài liệu high-level do Agent tổng hợp để QC Lead review và bổ sung.  
> File này không thay thế spec, wireframe, API document, use case detail hoặc các tài liệu chi tiết do BA/BE/Tech Lead cung cấp.  
> File này nên ngắn gọn, chỉ giữ thông tin có ảnh hưởng đến cách QC Agent hiểu dự án, đánh giá impact, review tài liệu hoặc thiết kế kiểm thử.

---

## Sources consolidated

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | Copy of BNZA_EXBOT_Proposal.md | no-version | product or business brief | 2026-06-02 |
| 2 | SPEC_v5.2.6_EN.md | 5.2.6 | architecture / tech overview / integration (replaces v5.2.5) | 2026-06-15 |
| 3 | exbot-implementation-overview.md | no-version | architecture / tech overview / locked decisions / team model | 2026-06-09 |
| 4 | exbot-task-breakdown.md | no-version | feature inventory / WBS / acceptance criteria (SH-/EX-/BT-) | 2026-06-09 |
| 5 | Exbot_Backtest_WBS.xlsx | no-version | WBS backtest (binary — referenced only) | 2026-06-09 |
| 6 | feature-map.md (02_backbone) | no-version | feature inventory / portal matrix / OOS markers / actor list | 2026-06-15 |
| 7 | common-rules.md (02_backbone) | no-version | business rules BR-MOB/EX/PL/ADM/WLA / code namespace | 2026-06-15 |
| 8 | backbone.md (02_backbone) | no-version | delivery structure / permissions / feature map / dependencies / priority | 2026-06-15 |

---

## 1. Cách các QC Agent sử dụng file này

| Nhóm Agent / Skill | Cách sử dụng project context | Cần đọc thêm file nào |
|---|---|---|
| Site map / dashboard / high-level review | Hiểu cấu trúc tổng thể hệ thống, site/module/feature, trạng thái tài liệu và các vùng cần theo dõi | Site map, feature list, qc-dashboard, high-level BA docs |
| Spec review - level function | Dùng context tổng quan để kiểm tra spec function có đúng scope, role, flow, rule chung, data/state và integration không | Spec chi tiết, wireframe, API spec nếu có |
| Scenario design | Xác định flow, role, dependency, risk và regression impact trước khi thiết kế scenario | Spec chi tiết, feature list, site map, business flow |
| Test case design | Dùng rule chung, platform/environment, permission, data/state để tránh thiết kế thiếu expected result hoặc thiếu precondition | Scenario, spec, wireframe, API spec |
| Test execute | Hiểu scope, environment, test data, dependency và các lưu ý chung khi execute | Test cases, test data, environment note, defect workflow |
| Bug verify | Hiểu impacted area, expected behavior chung, regression area và rule liên quan khi verify bug | Bug report, spec, test case, regression note |

**Quy tắc sử dụng:**  
Nếu thông tin trong file này mâu thuẫn với spec/wireframe/API chi tiết đã approved (ví dụ: `SPEC_v5.2.5.md`), Agent phải báo conflict và ưu tiên tài liệu chi tiết đã approved, trừ khi QC Lead có chỉ định khác.

---

## 2. Tóm tắt dự án

| Hạng mục | Nội dung |
|---|---|
| Tên dự án / sản phẩm | Bonanzapool — Hệ sinh thái BNZA (EXBOT là module Line 2) |
| Domain / nghiệp vụ | Blockchain (DeFi Yield / Delta-Hedged LP / WL MLM Distribution) |
| Loại dự án | New build & Integration |
| Mục tiêu chính của dự án/release | **Line 1:** WL+MLM system + POOL/EX portal maintenance. **Line 2:** EXBOT (delta-hedged LP Bot) + Backtest. Mục tiêu: tối ưu LP fee Uniswap V3 và giảm drawdown IL thông qua hedge Hyperliquid. |
| Người dùng chính | End User (LP), WL Partner, WL End User (OOS-Helix), Admin (zen), Trader, OPERATOR (system), WL Operator Admin (OOS-Helix). |
| Release / phase hiện tại | Line 1: WL Launch (P0). Line 2 EXBOT: Phase 0 Gate → Phase A1 (chờ 4 điều kiện gate). |
| Trạng thái tổng quan | In development |

**Tóm tắt ngắn:**  
Dự án Bonanzapool bao gồm 2 delivery line song song. **Line 1** tập trung vào WL+MLM system (wl-admin, wl-mobile do Helix sở hữu — OOS với Sotatek) và duy trì BNZA-POOL / BNZA-EX portal. **Line 2** xây dựng EXBOT — hệ thống bot quản lý thanh khoản tự động (Managed delta-hedged LP Bot) kết hợp LP fee Uniswap V3 (Base + Optimism) với Short Perpetual phòng vệ trên Hyperliquid, kèm Backtest offline. EXBOT bắt đầu sau khi đạt đủ 4 điều kiện Phase 0 Gate (SPEC v5.2.5 §0.3). Mục tiêu cốt lõi: giảm drawdown IL, hướng tới Net positive APR sau phí hedge và 30% performance fee — không bảo đảm hoàn vốn.

---

## 3. Phạm vi tổng thể và ranh giới kiểm thử

### 3.0 Cấu trúc delivery và ranh giới OOS

| Line | Scope | Sotatek builds? |
|---|---|---|
| **Line 1** | WL+MLM system development + maintain POOL/EX portal | ✅ Partial (wl-admin + wl-mobile = OOS — Helix sở hữu) |
| **Line 2** | EXBOT + Backtest | ✅ Yes |
| **OOS hoàn toàn** | `wl-admin` (PTL-06) — WL Admin System | ❌ Helix scope |
| **OOS hoàn toàn** | `wl-mobile` (PTL-01) — WL Mobile App | ❌ Helix scope |
| **Integration points** | BNZA-OPERATOR expose endpoint cho Helix gọi (stream 1 Ledger / stream 2 Position / stream 3 Bot Ops) | ✅ BNZA-OPERATOR xây endpoint, Helix consume |

> **Lưu ý QC:** Sotatek kiểm thử toàn bộ phía BNZA (PTL-02 ADMIN, PTL-03 EX, PTL-04 EXBOT Infra, PTL-05 POOL). Không kiểm thử PTL-01 và PTL-06. Chỉ kiểm thử contract giữa BNZA OPERATOR ↔ Helix ở phía endpoint của BNZA.

### 3.1 In scope cấp project/release

| Area / site / module / capability | Mô tả ngắn | Priority | Ghi chú |
|---|---|---|---|
| **Mạng hỗ trợ & Pool** | Dual-chain: Base (8453) + Optimism (10). Pool USDC/ETH 0.3% trên Uniswap V3, range ±5%. | High | **🆕 v5.2.6:** OP support từ Phase 1 — bỏ gate "backtest beats >10%". |
| **Phòng vệ vị thế (Hedge)** | Short Perpetual ETH-USD trên Hyperliquid. Hedge ratio 70%, đòn bẩy 3x Isolated, builder fee 5bps. | High | Hedge side chain-independent (chỉ LP side thay đổi khi dual-chain). |
| **Bộ tính toán vị thế (PositionAmountCalculator)** | Công thức Uniswap V3 chuẩn dựa trên liquidity/tick/sqrtPriceX96. Không dùng deposited−withdrawn+fees. | High | Fix lỗi carter2099. |
| **Bộ kích hoạt Rebalance** | Light-check mỗi 5 phút, 8 triggers: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback, manual_admin/recovery_reconcile. | High | Light-check dùng D1 cache, không gọi HL API. |
| **Cơ chế khớp lệnh phòng vệ** | Delta-only adjustment (chỉ mua/bán phần chênh lệch). Budget cap: chi phí ≤ trailing 7d LP fee × 30%. | High | Không close/open lại toàn bộ. |
| **Quản lý Stop Loss** | HL native reduce-only stop. Stop trigger crossed marker. Priority audit sau khi stop fire. | High | **🆕 v5.2.6:** stop subsystem overhaul (NV-1/NV-3 phải xác nhận trước impl §19.5). |
| **Hợp đồng BnzaExVault** | Solidity mới trên Base + OP custody LP NFT, độc lập BnzaRouter v2.2.1. | High | Cần deploy 2 bộ (Base + OP). Phải audit trước mainnet. |
| **BNZA-ADMIN (PTL-02)** | Quản lý WL partner, member lifecycle, master wallets, PF config, bot type config, EXBOT params, system settings. | High (Line 1 P0) | FM-ADM-01..10 — admin xây xong trước WL launch. |
| **BNZA-POOL Steps 7-8 (PTL-05)** | Multi-bot grid, chain switch, plan_specs version management, force-stop. | Medium (P1) | Step 8 cần deploy đồng bộ POOL + OPERATOR + ADMIN. |
| **BNZA-EX (PTL-03)** | TradingView chart, order placement qua Hyperliquid, position/PnL view. | Low (P2) | Chờ TradingView license (OQ-3 đã resolved: zen funds). |
| **BNZA-EXBOT Infra (PTL-04)** | D1 schema, 10 queues, 3 DOs, cron, HL adapter, API endpoints, lifecycle state machine, close/redeem. | High (Line 2 P0) | Chỉ bắt đầu sau khi đạt 4 Phase 0 Gate conditions. |
| **BNZA-OPERATOR WL Integration** | 3 API streams cho Helix: Ledger (net/user), Position (AUM), Bot Ops (start/stop wl_code). | High (P0) | Expose endpoint, Helix call với HMAC-SHA256. |
| **Backtest offline** | Data crawl + LP/hedge/strategy simulator + reporting. Import exbot-core (shared math). | High (Line 2 P0) | Track 2 chạy song song. |
| **Reconcile & Deep Audit** | Post-order reconcile, 6h deep-audit, hourly metrics-rollup, stop-integrity scan mỗi 6h. | High | Ngăn desync trạng thái. |
| **Kiểm soát Concurrency & Rate Limit** | UserLockDO (lease 90s), HLRateLimitDO (800 wt/min budget), MarketDataDO (slot0 cache). | High | Tránh nonce collision. |
| **Bảo mật Agent Key** | Envelope encryption qua CF Secrets Store. Không lưu raw key ở D1 hay logs. | High | |

### 3.2 Out of scope / chưa làm trong phase này (Deferred / OOS)

| Area / site / module / capability | Lý do loại trừ / deferred | Ảnh hưởng đến QC |
|---|---|---|
| **WL Admin System (PTL-06)** | OOS — Helix sở hữu, Sotatek không build/maintain. | Không thiết kế test case cho PTL-06. Chỉ test contract endpoint BNZA-OPERATOR phía BNZA. |
| **WL Mobile (PTL-01)** | OOS — Helix sở hữu. | Không test Mobile UI. Chỉ test WL API endpoint mà Helix gọi vào BNZA-OPERATOR. |
| **EXBOT Phase A start** | Chờ đủ 4 điều kiện Phase 0 Gate: (1) zen approve SPEC v5.2.6; (2) BnzaExVault deployed Base+OP; (3) HL agent key encryption confirmed; (4) WL stability gate 7 ngày. | EXBOT Infra chỉ build D1 schema + Queue skeleton trước gate. QC không test HL integration cho đến khi gate pass. |
| **Nhiều bot/user (Phase B+)** | Phase A: 1 user = 1 active Ex Bot. | Test constraint single-active-bot nghiêm ngặt. |
| **LP Range Ladder (nhiều dải)** | Phase 2 deferred. | Chỉ test single range ±5%. |
| **D1 Sharding (16 shards)** | Phase C deferred; Phase A dùng 1 shard. | Test với 1 shard. |
| **R2/Analytics Engine archive** | Phase B+ deferred. | Không test archiving. |

### 3.3 Assumption, dependency, constraint quan trọng

| Loại | Nội dung | Ảnh hưởng đến QC Agent | Cần xác nhận? |
|---|---|---|---|
| Dependency | Địa chỉ deploy BnzaExVault, Operator, và cấu hình Multi-sig cần được xác định từ trước W3. | Không có contract deploy và cấu hình thì không thể thực hiện kiểm thử tích hợp. | Yes |
| Constraint | Giới hạn rate limit của Hyperliquid REST API (1200 weight/phút/IP). | QC cần giả lập các tình huống rate limit bị vượt quá để kiểm chứng HLRateLimitDO hoạt động tốt. | No |
| Assumption | Phí tổn thất vô thường (IL) chỉ được giảm thiểu chứ không thể bị xóa bỏ hoàn toàn bởi chiến lược hedge. | Cần lưu ý khi thiết kế kịch bản nghiệm thu PnL, không được kỳ vọng rủi ro IL về 0. | No |

---

## 4. Cấu trúc hệ thống và tài liệu high-level liên quan

### 4.1 System / site / portal overview

| Portal ID | Site / portal / app | Mục đích | Tech Stack | Hosting | Nhóm user | Sotatek builds? |
|---|---|---|---|---|---|---|
| PTL-01 **[OOS — Helix]** | wl.bnza.io — WL Mobile | WL End User mobile PWA: SIWE auth, reward display, claim USDC, bot ops | Vite+React 19+Zustand+Tailwind 4+Reown AppKit+PWA | CF Pages | ACT-03 WL End User | ❌ |
| PTL-02 | ops.bnza.io — BNZA-ADMIN | Admin portal: WL partner mgmt, member lifecycle, PF config, bot type config, dashboard | React 19.2+Vite 8.0+TS 5.9+shadcn/ui+React Router 7 | CF Pages | ACT-04 Admin (zen) | ✅ |
| PTL-03 | ex.bnza.io — BNZA-EX | Perps trading UI (Hyperliquid direct) + TradingView charts | React 18.3+Vite 6.0+JS (no TS)+Wagmi 3.6+@nktkas/hyperliquid | CF Pages | ACT-01, ACT-05 | ✅ |
| PTL-04 | api.bnza.io/exbot — BNZA-EXBOT Infra | Backend bot engine: queues, DOs, D1, HL adapter, lifecycle state machine | CF Workers+D1+8 Queues+3 DOs (HLRateLimitDO, UserLockDO, MarketDataDO) | CF Workers | ACT-06 OPERATOR | ✅ |
| PTL-05 | pool.bnza.io — BNZA-POOL | LP bot management Steps 7-8: multi-bot grid, plan_specs, chain switch | Next.js 16.2+React 19.2+TS 5.9+Wagmi 2.19+TanStack Query | Vercel | ACT-01, ACT-04 | ✅ |
| PTL-06 **[OOS — Helix]** | wl-admin.bnza.io — WL Admin System | WL ops: daily reward distribution, MLM computation, on-chain payout, reconciliation | CF Pages+CF Workers+CF D1 (25 tables)+CF Queues | CF Pages+CF Workers | ACT-07 WL Operator Admin | ❌ |

**Actors (7):**
- ACT-01: End User (LP) — wallet connect
- ACT-02: WL Partner — wallet + WL invite code
- ACT-03: WL End User **[OOS-Helix]** — SIWE JWT 24h
- ACT-04: Admin (zen) — wallet + CF Access
- ACT-05: Trader — wallet direct HL
- ACT-06: OPERATOR (System) — internal no user auth
- ACT-07: WL Operator Admin **[OOS-Helix]** — SSO+2FA TOTP

**Data store boundary:**
- `bnza-operator D1` (control_db): users, bot_registry, shard_registry, hl_agent_keys, wl_members, wl_master_wallets, wl_activation_status.
- `bnza-exbot-db` (DEDICATED state_db): bots, positions, hedge_legs, bot_runtime_state, rebalance_attempts, circuit_breakers, funding_daily_metrics, queue_idempotency, close_operations, lp_operations, hourly/daily_bot_metrics.
- `wl-admin D1` (OOS-Helix): 25 tables riêng biệt cho MLM distribution, reward computation, on-chain payout.

### 4.2 Các file high-level liên quan

| File | Vai trò | Trạng thái | Ghi chú |
|---|---|---|---|
| **project-config.md** | Cấu hình thông tin tổng quan dự án, các link tài liệu, cấu hình môi trường, tài khoản test và APIs bên thứ ba. | Approved (v4) | Chứa các thông tin cơ sở cho toàn dự án. |
| **path-registry.md** | Khai báo toàn bộ đường dẫn logic (logical names) của các artifact dùng chung cho các AI Agent. | Approved | Đảm bảo tính nhất quán của cấu trúc thư mục. |
| **project-context-master.md** | File tổng hợp tri thức dự án (chính là tài liệu này), cung cấp bối cảnh tổng quan cho các QC Agent. | Draft (Đang cập nhật) | Đầu ra của skill `qc-context-master`. |
| **SPEC_v5.2.6_EN.md** | Tài liệu đặc tả kỹ thuật đầy đủ — luồng nghiệp vụ, tính toán, API, hợp đồng, NFR. **Version mới nhất (thay thế v5.2.5)**. | Approved (v5.2.6) | Nguồn tham chiếu chính cho spec review và scenario design. Có 14 NV items cần xác nhận ở Phase 0 (§0.5). |
| **backbone.md** | Requirements backbone cho toàn BNZA ecosystem: portal matrix, actor list, permissions, feature map, dependency graph, priority. | In-review | Nguồn canonical cho scope, OOS markers, và cross-project dependencies. |
| **feature-map.md** | Feature index đầy đủ 6 portals: PTL-01..06, 7 actors, FM-WLA/MOB/ADM/XB/PL/WLC/OPW với priority tiers T0-T3. | In-review | Dùng để đối chiếu scope và OOS markers. |
| **common-rules.md** | Business rules registry: BR-MOB-001..010, BR-EX-01..09, BR-PL-01..25, BR-ADM-001..034, BR-WLA-001..035. Code namespace MSG/CR. | Draft (2026-06-09) | Canonical source cho tất cả BRs — không define inline trong screen files. |
| **exbot-implementation-overview.md** | Tổng quan triển khai: quyết định đã khóa, kiến trúc component, mô hình đội nhóm (track), cấu trúc source. | Approved (no-version) | Giúp QC Agent hiểu ranh giới package và trách nhiệm từng track. |
| **exbot-task-breakdown.md** | Phân rã task chi tiết theo SH-/EX-/BT- với acceptance criteria và trạng thái (☐/◐/☑). | Approved (no-version) | Nguồn chính để lập Feature Inventory và đánh giá scope kiểm thử. |
| **Exbot_Backtest_WBS.xlsx** | WBS cho backtest track (Excel). | Approved (no-version) | Binary — tham chiếu bổ sung cho Track 2 Backtest. |
| **qc-dashboard.md** | Dashboard theo dõi trạng thái thiết kế và kiểm thử của từng feature theo từng usecase. | Missing / TBD | Sẽ được bootstrap sau khi chạy xong `qc-site-map`. |
| **agent-work-log.md** | Nhật ký ghi nhận các phiên chạy của các AI Agent trên từng thiết bị làm việc. | In use | Tự động tổng hợp từ các file JSONL trong thư mục `agent-work-log.local/`. |

---

## 5. Users, roles và permission tổng quan

| Role / actor | Mô tả | Workflow chính | Permission / responsibility tổng quan | Ghi chú QC |
|---|---|---|---|---|
| **ACT-01 End User (LP)** | Chủ sở hữu vị thế đầu tư. Cung cấp vốn, thụ hưởng lợi nhuận ròng. | Tạo/quản lý LP Bot, xem earnings, deposit/withdraw | Full access PTL-03 EX, PTL-05 POOL. Không trực tiếp ký lệnh HL (qua Agent Key). | Phase A: tối đa 1 active Ex Bot. |
| **ACT-02 WL Partner** | Institutional broker dùng branded MLM platform. | Xem earnings của own users | View earnings PTL-01 (OOS). Không test. | OOS phần WL Mobile. |
| **ACT-03 WL End User** **[OOS — Helix]** | MLM participant dưới WL operator. | SIWE auth, reward, claim, bot ops | Full PTL-01 WL Mobile. | Không test — Helix scope. |
| **ACT-04 Admin (zen)** | Sys admin, full access ADMIN portal. | Quản lý WL partner, config, emergency | Full PTL-02 ADMIN. Config PTL-04 EXBOT (API endpoints). Full PTL-05 POOL. | Test toàn bộ ADMIN portal FM-ADM-01..10. |
| **ACT-05 Trader** | Perps trader trên BNZA-EX. | Đặt lệnh perpetual qua Hyperliquid | Full PTL-03 EX. Direct HL — không qua OPERATOR. | Test FM-EX-01..03 (P2). |
| **ACT-06 OPERATOR (System)** | Backend automation — cron, relayers, queue consumers. | Cron light-check, hedge-sync, reconcile, deep-audit | Full PTL-04 EXBOT Infra (system level). KHÔNG có quyền transfer tài sản user ra ngoài BnzaExVault. | Cần test constraint: Operator chỉ rebalance/close/collect fees — không rút tiền về ví hệ thống. |
| **ACT-07 WL Operator Admin** **[OOS — Helix]** | WL ops team — monitor daily reward, manage referral tree. | Distribution job, tree mgmt, reconciliation | Full PTL-06 WL Admin. | Không test — Helix scope. |

---

## 6. Business flow, module relationship và impact area

### 6.1 Flow chính cấp project

| Flow ID | Flow name | Actor chính | Module/site liên quan | Trigger | Kết quả chính | Ghi chú impact/regression |
|---|---|---|---|---|---|---|
| **FLOW-001** | Khởi tạo Bot & Ký gửi Tài sản | ACT-01 End User, ACT-06 OPERATOR | BnzaExVault, D1, Hyperliquid, UI | User start bot, nạp LP NFT. | Bot `idle→preflight→lp_opening→lp_opened→hedge_pre_open→active`. NFT custody trong Vault. | Lỗi ở đây làm bot kẹt trạng thái hoặc NFT vào vault nhưng hedge không mở. |
| **FLOW-002** | Light-check & Rebalance tự động | ACT-06 OPERATOR | D1, MarketDataDO, UserLockDO, Hyperliquid | Cron 5 phút hoặc event trigger | Đánh giá 8 điều kiện rebalance. Nếu thỏa mãn + budget cap < 30%, thực hiện delta-only adjustment. | Chạy liên tục. Sai tính toán vị thế → sai khối lượng hedge → lỗ user. |
| **FLOW-003** | Khớp Stop Loss & Đóng Vị thế | Hyperliquid, ACT-06 OPERATOR | Hyperliquid, BnzaExVault, Queue, D1 | Giá ETH chạm stop_price trên HL | Stop fire → ghi `stop_trigger_crossed_at` → đóng LP trên Uniswap → bot `closed`. | **🆕 v5.2.6:** stop system overhaul. NV-1/NV-3 phải xác nhận trước impl. |
| **FLOW-004** | Reconcile & Deep Audit | ACT-06 OPERATOR | D1, Hyperliquid, Uniswap, RPC | Định kỳ 6h (1h nếu risk) | Phát hiện và fix lệch trạng thái D1 ↔ HL/Uniswap. | Đảm bảo atomicity. Nếu bỏ qua lệch vị thế → lỗi lặp lệnh sai. |
| **FLOW-005** | WL Member Lifecycle | ACT-04 Admin (zen), ACT-06 OPERATOR | BNZA-ADMIN (PTL-02), wl_members D1 | Admin thực hiện register/leave/suspend WL member | Member state: active → leaving → left. Bot delivery suspend khi pending_unset. | Two-phase leave (không instant NULL). `membership_epoch++` khi rejoin. |
| **FLOW-006** | WL Bot Activation (setBotWlMaster) | ACT-04 Admin, ACT-06 OPERATOR | BNZA-ADMIN, OPERATOR API, on-chain Relayer | Admin trigger set/unset wl master | Bot activation state: NULL → pending_set → active (6 states). | Two-phase force-normalize nếu bot stuck failed_set >48h. |
| **FLOW-007** | Bot User Redeem (LP-first) | ACT-01 End User | BnzaExVault, Queue (user_redeem), Hyperliquid | User yêu cầu close bot | LP close trước (on-chain guarantee). Hedge close SLA 5 phút. | Highest priority queue. close_operations idempotency ledger ngăn double settlement. |

### 6.2 Quan hệ giữa module / data / integration

| Area A | Liên quan đến Area B | Kiểu liên quan | Ảnh hưởng QC |
|---|---|---|---|
| **Tính toán vị thế LP (Uniswap)** | **Khối lượng Hedge (Hyperliquid)** | Data dependency | Mọi sự sai lệch trong tính toán lượng WETH thực tế của LP NFT trên Uniswap (do giá trượt, tick thay đổi) sẽ ảnh hưởng trực tiếp đến khối lượng vị thế Short cần mở trên HL. QC cần test kỹ các biên giá (out of range, boundary). |
| **Tài khoản phụ (Subaccount)** | **Khóa ghi UserLockDO** | Permission / Concurrency | Hyperliquid sử dụng cơ chế tăng nonce tuần tự cho mỗi giao dịch của subaccount. Do đó, UserLockDO phải đảm bảo không có 2 tiến trình ghi nào cùng thực thi lệnh trên một subaccount tại một thời điểm để tránh lỗi đè nonce (nonce collision). |
| **Tích lũy Phí LP (Uniswap)** | **Hedge Budget Cap (Hyperliquid)** | Integration | Phí thu được từ Uniswap LP (thu thập qua subgraph/RPC) được dùng để tính toán budget cap 30% cho chi phí rebalance. Nếu phí được lấy sai hoặc trễ, hệ thống có thể chặn rebalance sai hoặc cho phép rebalance quá tay làm hao hụt vốn. |

---

## 7. Rule chung, data/state và integration cần nhớ

### 7.1 Rule chung áp dụng nhiều function

**EXBOT Core Rules:**

| Rule | Áp dụng cho | Ảnh hưởng đến review/spec/scenario/test case |
|---|---|---|
| **Hedge Budget Cap** | Rebalance | Chi phí rebalance ≤ trailing 7d LP fee × 30%. Test case: LP fee thấp → hệ thống phải block/giảm tần suất rebalance. |
| **Delta-only Adjustment** | Khớp lệnh Hedge | Chỉ mua/bán phần chênh lệch `targetSize − actualSize`. Nghiêm cấm close toàn bộ rồi mở lại (trừ khi full redeem). Verify khối lượng order thực tế = delta tính toán. |
| **Circuit Breaker** | Bot state | 3 lần rebalance thất bại liên tiếp trong 24h → bot vào `SAFE_MODE` hoặc error state + alert. Test: giả lập 3 lỗi HL liên tiếp. |
| **1-User 1-Bot (Phase A)** | Bot creation | Mỗi user tối đa 1 active Ex Bot. Kiểm tra block tạo bot thứ 2 khi bot 1 active. |
| **Hedge Ratio & Leverage cố định** | Giao dịch | 70% (Balanced), 3x Isolated. Không thay đổi trong vòng đời bot Phase A. |
| **No Float** | Toàn bộ logic tính toán (exbot-core, D1, config) | Tất cả ratios/amounts dùng bigint hoặc decimal-string. Nghiêm cấm JS float cho phép tính tài chính. Test vector biên SH-02/03/04. |
| **No Plaintext Key** | Agent Key, Logging | HL Agent Key không lưu raw ở D1 hay logs. Test log sanitization EX-45, EX-07. |
| **EXBOT không public internet** | Kiến trúc / Transport | `apps/bnza-exbot` chỉ gọi qua CF service binding từ OPERATOR — không public endpoint. |
| **Dual-chain wethIndex** | LP calc, BnzaExVault, RPC | **🆕 v5.2.6:** token0/token1 order của USDC/WETH khác nhau giữa Base và OP. `wethIndex` phải được verify và lưu per-chain (§6.4). NV-12 là blocker. |
| **Price 3-way split** | Pricing | **🆕 v5.2.6:** Giá ETH dùng 3 nguồn: Uniswap price (LP math), Mark price (hedge target), Oracle price (stop placement). Không được dùng lẫn lộn. |
| **Stop không impl khi NV-1/NV-3 chưa xong** | Stop system | **🆕 v5.2.6:** §19.5 stop replacement KHÔNG được implement khi NV-1 (isolated margin fields) và NV-3 (duplicate reduce-only stop) chưa được SOTATEK confirm với HL. |

**BNZA-POOL Rules (BR-PL):**

| Rule | Nội dung ngắn | Ghi chú QC |
|---|---|---|
| BR-PL-01 | Chỉ OP (10) + Base (8453). | Test chain switch. |
| BR-PL-02 | Pool address từ `Factory.getPool` on-chain — không từ DB. | Test: DB cũ ≠ on-chain. |
| BR-PL-08 | PF ratio: `convert_to_usdc=1` → 0.2970075, else 0.2985. | Test 2 nhánh PF ratio. |
| BR-PL-11 | Max 10 bots/chain — UI enforcement only. | Test đúng UI limit. |
| BR-PL-14 | `already_stopped` error = success. | Test idempotency stop. |
| BR-PL-16 | `atomic-start` retry 3 lần (2s/4s/6s backoff); full fail = fatal modal. | Test retry exhaustion. |
| BR-PL-23/24 | Evaluation = Σ(liquidityUSD + unclaimedFeesUSD) active positions. P&L = Evaluation − invested_amount (immutable). | Test PnL display. |

**BNZA-ADMIN Rules (BR-ADM, chọn lọc quan trọng):**

| Rule | Nội dung ngắn | Ghi chú QC |
|---|---|---|
| BR-ADM-009 | 1 wallet chỉ active/leaving ở 1 WL cùng lúc. | Test duplicate WL membership. |
| BR-ADM-010 | Wallet đang `leaving` → reject new bot start. | Test bot creation gate. |
| BR-ADM-011 | Leave 2-phase: `initiate-leave` → `leaving` → confirm after on-chain unset. | Test flow leave + revert. |
| BR-ADM-013 | 1 master wallet per WL per chain. Rotation 2-phase; bot delivery suspend during rotation. | Test rotation flow. |
| BR-ADM-028 | `global_bot_enabled=false` → dừng toàn bộ bot processing ngay lập tức. | Test emergency switch. |
| BR-ADM-031 | Force-normalize 2-phase: unset on-chain confirmed + `wlMaster[tokenId]==0` read → set `wl_code=NULL`. | Test 2-phase constraint. |
| BR-ADM-033 | `failed_set` bots stuck >48h → auto-force-normalized bởi OPERATOR cron. | Test SLA alert + auto-normalize. |

### 7.2 Data object / state quan trọng cấp project

| Object / entity | Mô tả | State / lifecycle chính | Ghi chú QC |
|---|---|---|---|
| **Ex Bot (Bot State)** | Đối tượng bot đại diện cho vị thế đầu tư của user. Lưu trong D1 database. | `LP_OPENING` -> `LP_OPEN` <br> `LP_REBALANCING` <br> `LP_CLOSING` -> `LP_CLOSED` <br> `LP_FAILURE` (khi ngắt hoặc cắn stop loss) | QC cần thiết kế ma trận chuyển trạng thái (State Transition Matrix) để test đầy đủ các trường hợp chuyển đổi hợp lệ và không hợp lệ. |
| **Hedge Leg (Vị thế Hedge)** | Ghi nhận vị thế phòng vệ trên Hyperliquid tương ứng với Bot. | `Active` (đang hedge)<br> `Rebalancing` (đang khớp delta)<br> `Closed` (đã đóng vị thế) | Cần đối chiếu chính xác trạng thái của Hedge Leg trong DB D1 với vị thế thực tế trên sàn Hyperliquid. |
| **Circuit Breaker Log** | Nhật ký lỗi phục vụ tự ngắt bot. | `Open` (bình thường) -> `Tripped` (đã kích hoạt tự ngắt) | QC kiểm tra cơ chế ghi log lỗi và reset log sau 24h hoặc sau khi Admin can thiệp. |

### 7.3 Integration / API / job / notification quan trọng

| Item | Loại | Module liên quan | Ghi chú QC / risk |
|---|---|---|---|
| **Hyperliquid REST/WS API** | API tích hợp | HyperliquidAdapter, Hedge-sync, Audit | Rủi ro: Nghẽn mạng, lỗi rate limit (1200 weight/phút). Cần kiểm thử cơ chế retry bất đồng bộ với exponential backoff. |
| **Uniswap V3 Subgraph & RPC** | API tích hợp | MarketDataDO, PositionAmountCalculator | Rủi ro: Subgraph bị đồng bộ chậm (stale block). Hệ thống cần lấy giá trị max() giữa dữ liệu subgraph và dữ liệu RPC trực tiếp của node. |
| **Cloudflare Secrets Store** | API bảo mật | Key Management, Authentication | Mã hóa Agent Key bằng khóa KMS/Envelope. QC cần đảm bảo private key của ví user và admin không bao giờ bị ghi log thô (raw print). |

---

## 8. Platform, environment, device và NFR/ràng buộc

### 8.1 Platform và environment tổng quan

| Hạng mục | Nội dung | Ghi chú QC |
|---|---|---|
| Platform type | API-only / backend-job (Phase A1) <br> Web-responsive (Next.js - Phase B+) | Hầu hết công việc kiểm thử ở Phase A1 sẽ chạy trên backend/API. Giao diện người dùng sẽ được kiểm thử ở phase sau. |
| Browser / OS / device cần quan tâm | API Clients (Postman/Curl), Linux/macOS CLI | Môi trường triển khai production của bot là Cloudflare Workers (V8 runtime). |
| Test environment | **Base Sepolia Testnet** (cho Smart Contract & Uniswap V3) <br> **Hyperliquid Testnet** (cho vị thế Hedge) | QC cần chuẩn bị faucet ETH trên Base Sepolia và tài khoản Testnet có USDC trên Hyperliquid để thực hiện test. |
| Integration mode | Real Testnet Sandbox | Kết nối trực tiếp đến testnet thực của Uniswap V3 (Base Sepolia) và Hyperliquid Testnet API. |
| Test data / account tổng quan | Cấu hình tài khoản test được lưu trữ và mô tả trong `project-config.md`. | Chỉ sử dụng các tài khoản và Agent Keys thử nghiệm, tuyệt đối không dùng khóa có chứa tài sản thực (Mainnet). |

### 8.2 NFR, security, compliance, legal, audit

| Loại ràng buộc | Nội dung đã biết | Ảnh hưởng QC |
|---|---|---|
| **Bảo mật (Security)** | Agent Key phải được mã hóa phong bì (envelope encryption) thông qua Cloudflare Secrets Store. Hệ thống không lưu trữ Master Private Key của người dùng. | QC cần kiểm tra tính bảo mật trong log: đảm bảo không có API keys hay private keys nào bị hiển thị dưới dạng raw text trong Cloudflare Logs hay D1 database. |
| **Hiệu năng (Performance)** | - Thời gian thực thi cron light-check: < 50ms CPU time.<br>- Thời gian hoàn thành 1 phiên rebalance (hedge-sync): < 30 giây để tránh nghẽn hàng đợi (Queue lag). | QC cần thực hiện kiểm thử tải (Load test) hoặc đo đạc latency của tiến trình hedge-sync trong điều kiện mạng lag để đảm bảo không bị quá 15 phút timeout của Queue consumer. |
| **Tuân thủ & Kiểm toán (Audit)** | Hợp đồng thông minh `BnzaExVault` bắt buộc phải được audit độc lập bởi bên thứ 3 (chi phí dự kiến 8.000$ - 25.000$) trước khi triển khai Mainnet. | QC cần rà soát mã nguồn contract dựa trên các file test Foundry đi kèm trước khi bàn giao cho bên audit. |
| **Pháp lý (Legal / Risk Disclosure)** | UI hiển thị minh bạch 2 mức APR: Gross APR (trước phí) và Net APR (sau khi trừ 30% phí hiệu suất). Cảnh báo rõ ràng về việc không bảo lãnh hoàn vốn và rủi ro trượt giá Stop Loss. | QC cần rà soát kỹ các nhãn hiển thị thông tin APR và cảnh báo rủi ro trên UI ở các phase sau. |

---

## 9. Đánh giá mức độ đủ context cấp project

| Nhóm context | Trạng thái | Độ tin cậy | Ảnh hưởng nếu thiếu/sai | Cần QC Lead bổ sung gì |
|---|---|---:|---|---|
| **Project goal & scope (full ecosystem)** | Ready | High | Nhầm scope EXBOT-only → bỏ sót Line 1 testing | Xác nhận priority phân công QC theo Line 1 vs Line 2. |
| **OOS boundaries (Helix)** | Ready | High | Test nhầm PTL-01/PTL-06 thuộc Helix | N/A — đã rõ. |
| **System/site/portal overview (6 portals)** | Ready | High | Hiểu sai kiến trúc portal → thiết kế test sai module | N/A |
| **EXBOT feature/use case inventory** | Ready | High | Bỏ sót SH-/EX-/BT- khi lập test plan | Rà soát scope theo Phase 0 Gate → A1 → A2. |
| **WL+MLM feature inventory (Line 1)** | Partial | Medium | Thiếu test cho FM-ADM/FM-PL/FM-EX | Cần đọc UC files từ `03_modules/` sau khi có. |
| **Users/roles/permission overview** | Ready | High | Test sai phân quyền → lỗ hổng bảo mật | N/A |
| **Business flows & module relationship** | Ready | High | Thiếu cross-portal test cases | N/A |
| **Common rules/data/state/integration** | Ready | High | Bỏ sót BR-PL/ADM rules → missed acceptance criteria | N/A |
| **Platform/environment/device/NFR** | Partial | Medium | Gặp rate limit RPC hoặc hết CF resource | Xác nhận RPC endpoints dự phòng và CF Paid plan. |
| **SPEC v5.2.6 NV items (Phase 0 gate)** | Partial | Medium | Implement §19.5 stop khi NV-1/NV-3 chưa xác nhận → sai spec | Theo dõi tiến độ SOTATEK confirm NV-1..14 với HL/CF. |
| **Document status tracking** | Partial | Medium | Khó theo dõi tiến độ thiết kế và thực thi | Chạy `qc-site-map` để khởi tạo dashboard. |

**Kết luận:**  
Context cấp project đã được mở rộng từ EXBOT-only sang full Bonanzapool ecosystem (6 portals, 2 delivery lines). Context đủ để QC Agent hiểu toàn bộ hệ thống và phân chia test plan theo Line 1 / Line 2. Rủi ro cao nhất còn lại: NV items SPEC v5.2.6 (đặc biệt NV-1/NV-3 cho stop system, NV-12 cho dual-chain pool address), địa chỉ deploy BnzaExVault, và xác nhận pool 0.3% đủ thanh khoản cho backtest.

---

## 10. Open questions và việc cần QC Lead xác nhận

| ID | Câu hỏi / thông tin cần xác nhận | Vì sao quan trọng | Ảnh hưởng nếu chưa rõ | Priority | Owner | Status |
|---|---|---|---|---|---|---|
| Q-001 | Địa chỉ deploy BnzaExVault, Operator address, và danh sách ví Multi-sig signers (Base + OP)? | Cần để cấu hình môi trường test tích hợp. | Không thể chạy test tích hợp A2 Live $1k. | High | QC Lead / zen | Open |
| Q-002 | Quy trình ký và phối hợp Multi-sig khi Circuit Breaker bị kích hoạt? | Đảm bảo recovery time khi bot sự cố. | Khó thiết lập kịch bản test recovery flow. | Low | Tech Lead | Open |
| Q-003 | Cách giả lập stop loss trigger trên HL Testnet để test luồng tự động đóng LP? | Stop loss là safety tối thượng bảo vệ user. | Không thể test đầy đủ luồng đóng vị thế khẩn cấp. | Medium | Tech Lead / QC Lead | Open |
| Q-004 | RPC endpoint dự phòng cho Base Sepolia và OP Sepolia Testnet? | Tránh gián đoạn test suite do rate limit RPC. | Test suite fail ngẫu nhiên do lỗi RPC. | Low | Tech Lead | Open |
| Q-005 | Xác nhận Cloudflare Paid plan sẽ dùng cho môi trường test và deploy thật? | Kiểm chứng giới hạn CPU time và subrequest limit (NV-8/NV-9). | Phát hiện muộn lỗi resource limit của CF Workers. | Medium | QC Lead / zen | Open |
| Q-006 | OPERATOR có duy trì minimal status mirror của EXBOT hay luôn query live EXBOT status? (Quyết định EX-43) | Quyết định kiến trúc ảnh hưởng test path: cache vs live-query. | QC không xác định đúng test design cho EX-43. | Medium | Tech Lead | Open |
| Q-007 | Ai có quyền điều chỉnh strategy params (hedge ratio, drift threshold) khi live khác backtest? | Xác định người ký duyệt thay đổi config. | Không rõ quyền → không test được luồng thay đổi params. | Medium | PM / Tech Lead | Open |
| Q-008 | API key của The Graph Studio (subgraph Uniswap V3 trên Base) đã procurement chưa? | Không có API key → block BT-01. | Backtest Track 2 bị block hoàn toàn. | High | Ops / Tech Lead | Open |
| Q-009 | Pool USDC/WETH 0.3% trên Base có đủ thanh khoản/volume đại diện (so với 0.05%)? | Nếu pool quá mỏng → fallback archive-RPC. | Backtest không representative. | Medium | Tech Lead | Open |
| Q-010 | Ngày freeze final ABI của BnzaExVault là khi nào? | Track 1 (EX-23) cần ABI đóng để code song song SC track. | ABI thay đổi muộn → Track 1 rework vault-client. | High | SC team | Open |
| Q-011 | Tiến độ xác nhận NV-1 và NV-3 với Hyperliquid (isolated margin fields, duplicate reduce-only stop behavior)? | **SPEC v5.2.6 §0.5:** §19.5 stop replacement KHÔNG được impl trước khi xác nhận NV-1/NV-3. | Block impl stop system (§19.5) và ảnh hưởng test plan FLOW-003. | High | SOTATEK (Phase 0 deliverable) | Open |
| Q-012 | NV-12: Địa chỉ pool Base + OP và `wethIndex` (token0/token1 order) cho USDC/WETH 0.3% đã được BNZA (zen) xác nhận chưa? | **SPEC v5.2.6 §1.3, §6.4:** dual-chain LP calc dùng `wethIndex` per-chain. Sai index → sai toàn bộ LP amount calculation. | Block impl dual-chain (§6.4). Block test dual-chain POOL. | High | BNZA (zen) | Open |
| Q-013 | NV-5 (cloid idempotency) đã được verify với HL testnet chưa? Cloid deterministic có ngăn double submission không? | **SPEC v5.2.6 §8.5, §13.8 (B-6):** Nếu HL không idempotent với cloid → cần workaround khác. | Ảnh hưởng thiết kế HL adapter và test case cloid collision. | Medium | SOTATEK | Open |

---

## Phụ lục A. Nguyên tắc giữ file gọn

- Chỉ ghi thông tin cấp project hoặc thông tin dùng chung cho nhiều Agent/skill.
- Không copy toàn bộ nội dung từ spec, wireframe, API document hoặc use case detail.
- Không ghi test case chi tiết trong file này.
- Không lặp lại danh sách feature dài nếu đã có `feature list` hoặc `qc-dashboard`.
- Nếu thông tin đã có ở file khác, chỉ tóm tắt vai trò và dẫn Agent đọc file đó.
- Nếu một thông tin chỉ ảnh hưởng một function cụ thể, đưa vào function-level context/spec review, không đưa vào file này.
