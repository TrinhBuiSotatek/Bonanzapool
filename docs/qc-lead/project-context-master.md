# Project Context Master: BNZA Ecosystem

**Trạng thái:** Draft  
**Ngày tạo/cập nhật:** 2026-06-30  
**Người chuẩn bị:** QC Context Agent  
**Người review:** QC Lead / Trinh.Bui  
**Mục đích:** Cung cấp bối cảnh tổng quan cấp project để các QC Agent hiểu đúng hệ thống, phạm vi, rule chung, rủi ro và trạng thái tài liệu trước khi review spec, thiết kế scenario/test case, execute hoặc verify bug.

> File này là tài liệu high-level do Agent tổng hợp để QC Lead review và bổ sung.  
> File này không thay thế spec, wireframe, API document, use case detail hoặc các tài liệu chi tiết do BA/BE/Tech Lead cung cấp.  
> File này nên ngắn gọn, chỉ giữ thông tin có ảnh hưởng đến cách QC Agent hiểu dự án, đánh giá impact, review tài liệu hoặc thiết kế kiểm thử.

---

## Sources consolidated

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | intake.md | không có version | Scope / Project overview / NFR / Risks | 2026-06-30 |
| 2 | backbone.md | không có version | Architecture / Feature inventory / Business rules / System constraints | 2026-06-30 |
| 3 | common-rules.md | không có version | Business rules | 2026-06-30 |
| 4 | message-list.md | không có version | Error codes / Messages | 2026-06-30 |
| 5 | feature-map.md | không có version | Feature inventory / Portal registry / Actor registry | 2026-06-30 |
| 6 | project-config.md | v1 | Project config | 2026-06-30 |

---

## 1. Cách các QC Agent sử dụng file này

| Nhóm Agent / Skill | Cách sử dụng project context | Cần đọc thêm file nào |
|---|---|---|
| Site map / dashboard / high-level review | Hiểu 6 portal, 7 actor, cấu trúc 2-line delivery, phạm vi Sotatek vs OOS (Helix) | `feature-map.md`, `backbone.md`, `qc-site-map.md` |
| Spec review - level function | Dùng context tổng quan để kiểm tra spec function đúng scope, role, flow, rule chung | Spec chi tiết module tương ứng (`frd.md`, `srs/spec.md`, UC file) |
| Scenario design | Xác định flow, role, dependency, state machine, risk trước khi thiết kế | `uc-review-report`, `srs/spec.md`, `common-rules.md`, `message-list.md` |
| Test case design | Dùng rule chung, platform, permission, data/state để tránh thiếu expected result | Scenario, spec, `srs/spec.md`, `common-rules.md` |
| Test execute | Hiểu scope, environment, test data, dependency khi execute | Test cases, environment note |
| Bug verify | Hiểu impacted area, expected behavior chung, regression area và rule liên quan | Bug report, spec, test case |

**Quy tắc sử dụng:**  
Nếu thông tin trong file này mâu thuẫn với spec/wireframe/API chi tiết đã approved, Agent phải báo conflict và ưu tiên tài liệu chi tiết đã approved, trừ khi QC Lead có chỉ định khác.

---

## 2. Tóm tắt dự án

| Hạng mục | Nội dung |
|---|---|
| Tên dự án / sản phẩm | BNZA Ecosystem (Bonanzapool) |
| Domain / nghiệp vụ | Blockchain / DeFi — LP bot trên Uniswap V3 + hedge trên Hyperliquid |
| Loại dự án | Enhancement + New build |
| Mục tiêu chính | Tích hợp WL+MLM (Line 1) + xây dựng ExBot — bot tự động hedge LP trên Hyperliquid (Line 2) |
| Người dùng chính | End User (LP), Trader, Admin (zen), WL End User (qua Helix) |
| Release / phase hiện tại | Phase A — ExBot core + WL+MLM Line 1 (Phase 0 gate chưa đủ điều kiện) |
| Trạng thái tổng quan | In development |

**Tóm tắt ngắn:**  
BNZA Ecosystem là hệ sinh thái DeFi cho phép người dùng tạo LP bot trên Uniswap V3 (Base/OP) và hedge tự động trên Hyperliquid thông qua ExBot. Dự án có 2 luồng song song: Line 1 tích hợp White-label MLM (Helix) với cơ chế chia sẻ doanh thu và Line 2 phát triển ExBot — hệ thống bot chạy trên Cloudflare Workers, xử lý 10,000 bots, tương tác với 10 queue và 3 Durable Object. Client là MEGABUCKS/zen; Vendor là SOTATEK (hợp đồng 8 tuần). WL Admin System (PTL-06) và WL Mobile (PTL-01) là Helix scope — SOTATEK không build hoặc maintain.

---

## 3. Phạm vi tổng thể và ranh giới kiểm thử

### 3.1 In scope cấp project/release

| Area / site / module / capability | Mô tả ngắn | Priority | Ghi chú |
|---|---|---|---|
| BNZA-EXBOT Infrastructure (PTL-04) | Bot tự động hedge LP, 10 queue, 3 DO, cron jobs, HL adapter, API facade | High (P0) | Line 2; Phase 0 gate chưa đủ |
| BNZA-ADMIN (PTL-02) | Quản lý WL partner, PF distribution, IB, bot type config, audit log | High (P0) | Line 1 critical |
| BNZA-OPERATOR WL Backend | DB migrations, Ledger API, Bot API, WlNetSent scanner, reconcilers | High (P0) | Line 1; api.bnza.io |
| WL Smart Contracts (BnzaRouter/BnzaLpBot) | 11 contract changes A-K cho WL integration | High (P0) | SOTATEK builds; zen deploys ExBot contracts |
| BNZA-POOL Steps 7-8 (PTL-05) | Multi-bot grid, plan_specs version management | Medium (P1) | Post-WL |
| BNZA-EX (PTL-03) | TradingView integration, order placement | Low (P2) | Non-blocking |

### 3.2 Out of scope / chưa làm trong phase này

| Area / site / module / capability | Lý do loại trừ / deferred | Ảnh hưởng đến QC |
|---|---|---|
| WL Admin System — PTL-06 (FM-WLA-01→07) | Helix (WL operator) scope — SOTATEK không build | QC chỉ test phía BNZA OPERATOR API mà Helix gọi vào |
| WL Mobile — PTL-01 (FM-MOB-01→11) | Helix scope | QC chỉ test bot operations qua OPERATOR API |
| ExBot contracts (BnzaExVault, BnzaExPositionManager, v.v.) | zen designs & deploys; SOTATEK chỉ integrate | Cần ABI từ zen trước khi test integration |
| Park/redeploy feature | Dropped per HLD 2026-06-18 | Không có CloseDestination enum, FundsParked/Redeployed events |
| BnzaSplitter contract | Removed từ v1 | PF distribution là off-chain (FM-ADM-02) |
| Backtest (Line 2 future) | Post-ExBot Phase A completion | Chưa có spec |

### 3.3 Assumption, dependency, constraint quan trọng

| Loại | Nội dung | Ảnh hưởng đến QC Agent | Cần xác nhận? |
|---|---|---|---|
| Dependency | Phase 0 gate (4 điều kiện): zen approve SPEC v5.2.6 ✅; BnzaExVault deployed (Base+OP); HL agent key encryption confirmed; WL stability gate 7 ngày | ExBot Phase A chưa bắt đầu nếu chưa đủ 4 điều kiện | Yes — trạng thái hiện tại của gate 2-4 |
| Constraint | Dual-chain từ Phase 1: Base (8453) + OP (10) — cả hai từ ngày đầu | Test phải cover cả 2 chains | No |
| Assumption | NV-3 (duplicate reduce-only stop behavior) và NV-12 (pool address, wethIndex) là critical — chưa confirm | Ảnh hưởng §19.5 (stop replacement) và §6.4 (LP calc) | Yes — cần kết quả NV-3/NV-12 |
| Constraint | BnzaRouter unchanged — integrate as-is; "BnzaExVault" (Solidity) ≠ "vaultAddress" (HL subaccount ID) | Tránh nhầm lẫn terminology khi review ExBot spec | No |
| Dependency | WL stability gate: 7 ngày liên tiếp post-launch không có SAFE_MODE + no major incident mới được bắt đầu Phase A | ExBot testing bị block đến khi gate pass | Yes |

---

## 4. Cấu trúc hệ thống và tài liệu high-level liên quan

### 4.1 System / site / portal overview

| Site / portal / app | Mục đích | Nhóm user chính | Module chính | Ghi chú |
|---|---|---|---|---|
| PTL-01 — wl.bnza.io (TBD) | WL Mobile — SIWE auth, reward display, bot ops | ACT-03 (WL End User) | SIWE, Reward, Claim, Bot ops | **OOS — Helix scope** |
| PTL-02 — ops.bnza.io | BNZA-ADMIN — quản lý WL partner, PF, IB, bots, config | ACT-04 (zen) | WL Mgmt, PF, IB, Bot Config, Audit Log | Sotatek scope |
| PTL-03 — ex.bnza.io | BNZA-EX — TradingView + perpetual trading trực tiếp HL | ACT-05 (Trader) | TradingView, Order, Positions | P2; independent — no OPERATOR |
| PTL-04 — api.bnza.io | BNZA-EXBOT Infrastructure — backend, queue, cron, DO | ACT-06 (OPERATOR System) | ExBot Worker, 10 queues, 3 DOs | Sotatek scope; no UI |
| PTL-05 — pool.bnza.io | BNZA-POOL — multi-bot grid, plan_specs | ACT-01 (End User) | Multi-bot, plan_specs | P1; Vercel deploy |
| PTL-06 — wl-admin.bnza.io (TBD) | WL Admin System — daily MLM distribution ops | ACT-07 (WL Operator Admin) | Distribution, Reward Computation, RewardDistributor | **OOS — Helix scope** |

### 4.2 Các file high-level liên quan

| File | Vai trò | Trạng thái | Ghi chú |
|---|---|---|---|
| `backbone.md` | Kiến trúc tổng thể, feature map inline, system constraints, formulas, key behavioral rules | Reviewed | Nguồn chính cho context cấp project |
| `feature-map.md` | Portal registry, actor registry, feature index đầy đủ (FM-*), priority tiers, cross-deps | In-review | Single source of truth cho FM-* IDs |
| `intake.md` | Scope, deliverables, WBS, NFRs, risks, locked decisions, 8-week contract details | Reviewed | Nguồn scope ban đầu |
| `common-rules.md` | BR-MOB/EX/PL/ADM/EXBOT/WLA business rules | Draft | Cần đọc khi review spec hoặc thiết kế test case |
| `message-list.md` | E-codes cho tất cả module (MOB/POOL/ADM/EXBOT/WLA) | Draft | Cần đọc khi verify error handling |
| `qc-site-map.md` | Cấu trúc site/module/screen/flow | Chưa tạo (sẽ auto-invoke) | Output của qc-site-map |
| `qc-dashboard.md` | Theo dõi spec/scenario/test case từng feature | Chưa tạo | Output của qc-dashboard-sync |
| `project-config.md` | Cấu hình project, domain, target audience | v1 — partial | Mục 2-5 chưa điền |

---

## 5. Users, roles và permission tổng quan

| Role / actor | Mô tả | Workflow chính | Permission / responsibility tổng quan | Ghi chú QC |
|---|---|---|---|---|
| ACT-01 End User (LP) | Người dùng tạo LP bot trên POOL | Tạo bot, start/stop, xem P&L | Wallet connect; max 10 bots/chain | PTL-03 (EX direct) + PTL-05 |
| ACT-02 WL Partner | WL operator — nhận commission từ user activity | Xem earnings, payout history | Chỉ xem qua BNZA-ADMIN (FM-ADM-01) | Sotatek tạo record; Helix operations |
| ACT-03 WL End User | User của Helix — bot ops qua WL Mobile | Bot start/stop, xem reward, claim USDC | SIWE → 24h JWT; tenant by subdomain | **OOS — Helix scope** |
| ACT-04 Admin (zen) | Quản trị hệ thống BNZA | WL onboarding, PF config, bot type config, audit log | Wallet + CF Access (zen@bnza.io); RBAC: super_admin/admin/viewer | super_admin: tạo WL, config hệ thống |
| ACT-05 Trader | Trader trực tiếp trên Hyperliquid qua BNZA-EX | Chart, đặt lệnh perpetual | Wallet connect trực tiếp; không qua OPERATOR | PTL-03 only |
| ACT-06 OPERATOR (System) | Hệ thống backend — ExBot Worker, queues, crons | Queue processing, cron execution, D1 read/write, DO management | Internal service binding | Không có user; bot-to-system |
| ACT-07 WL Operator Admin | Admin của Helix chạy daily MLM ops | Daily distribution, tree management, distributor monitoring | SSO + 2FA TOTP; Super/Operator/Read-only | **OOS — Helix scope** |

**Lưu ý permission chung:**  
- `X-Wallet-Address` header (không signature) là primary auth cho POOL và BNZA-ADMIN → OPERATOR.  
- BNZA-ADMIN có thêm Cloudflare Access (zen@bnza.io) + wallet connect.  
- Helix server gọi BNZA OPERATOR qua HMAC-SHA256 (server-to-server) cho `/api/wl/*` và bot start/stop webhooks.  
- ExBot KHÔNG có public API — tất cả gọi qua OPERATOR service binding (PTL-04 → PTL-02 facade).

---

## 6. Business flow, module relationship và impact area

### 6.1 Flow chính cấp project

| Flow ID | Flow name | Actor chính | Module/site liên quan | Trigger | Kết quả chính | Ghi chú impact/regression |
|---|---|---|---|---|---|---|
| FLOW-001 | LP Bot Start (ExBot) | ACT-01/ACT-04 | POOL → OPERATOR → ExBot Worker | Admin gọi `/api/exbot/start` | Bot tạo Uniswap LP + hedge trên HL; `lifecycle_state = active` | Ảnh hưởng preflight, HL adapter, DO lock |
| FLOW-002 | Hedge Sync | ACT-06 (queue) | ExBot Worker → HL API | `hedge-sync` queue message | Điều chỉnh short ETH theo LP drift; delta-only | Light-check KHÔNG fetch HL; margin status từ D1 |
| FLOW-003 | User Redeem (LP-first) | ACT-01 (on-chain) | BnzaExVault → ExBot Worker | `BnzaExVault.redeem(tokenId)` on-chain TX | LP USDC trả về user trong cùng TX; HL hedge close async (SLA 5 phút) | BR-EXBOT-006: LP repayment unconditional — hedge fail KHÔNG block |
| FLOW-004 | Bot Safe Close (hedge-first) | ACT-06 / ACT-04 | ExBot Worker → HL → BnzaExVault → RedemptionQueue | Admin close hoặc auto (3 stops/7 ngày) | Close HL → LP close → RedemptionQueue FIFO pay user | Không có park/redeploy loop |
| FLOW-005 | WL MLM Distribution | ACT-07 (Helix) | WL Admin → BNZA OPERATOR Ledger API → RewardDistributor | Daily cron (Helix-side) | Tính và phân phối reward USDC cho WL users | OOS nhưng BNZA OPERATOR Ledger API là dependency |
| FLOW-006 | WL Partner Onboarding | ACT-04 | BNZA-ADMIN → OPERATOR API | Admin tạo WL partner record | `wl_code` active; Helix có thể pull Ledger API | Ảnh hưởng wl_members, wl_master_wallets, on-chain setBotWlMaster |

### 6.2 Quan hệ giữa module / data / integration

| Area A | Liên quan đến Area B | Kiểu liên quan | Ảnh hưởng QC |
|---|---|---|---|
| ExBot Worker (PTL-04) | Hyperliquid API (external) | Integration — trading API, rate limit 1,200 wt/min (BNZA budget 800) | Phải test rate limit, cloid idempotency, error parsing |
| ExBot Worker | OPERATOR API (PTL-04) | Service binding (Worker-to-Worker) — không public | Test ExBot qua OPERATOR facade `/api/exbot/*` |
| BNZA-ADMIN (PTL-02) | OPERATOR API | REST API (admin role) | WL mgmt, PF config, bot type config đều qua OPERATOR |
| POOL (PTL-05) | OPERATOR API | REST API | `bot-positions` API, plan_specs endpoints |
| WL Admin (PTL-06) | BNZA OPERATOR Ledger/Position/Bot APIs | HMAC-SHA256 server-to-server PULL | OOS nhưng SOTATEK phải đảm bảo API contract đúng |
| ExBot hedge-sync | D1 state_db | Data dependency — `bots`, `hedge_legs`, `bot_runtime_state` | State phải nhất quán sau mỗi operation |
| User redeem | BnzaExVault (on-chain) + `close_operations` D1 table | On-chain event → off-chain state machine | `close_operations` là idempotency ledger — prevent double settlement |

---

## 7. Rule chung, data/state và integration cần nhớ

### 7.1 Rule chung áp dụng nhiều function

| Rule | Áp dụng cho | Ảnh hưởng đến review/spec/scenario/test case |
|---|---|---|
| INV-STOP: khi HL short non-zero, phải luôn tồn tại verified reduce-only stop. Ngoại lệ duy nhất: bên trong `replaceStopProtected` critical section (max 60s) | Tất cả operations liên quan HL hedge | Stop phải được kiểm chứng trước khi mark bất kỳ hedge operation nào là hoàn thành |
| Light-check HL weight = 0: KHÔNG fetch HL dưới bất kỳ hình thức nào trong light-check (kể cả margin) | `light-check` queue worker | Margin status chỉ đọc từ D1 `hedge_legs.margin_status`; KHÔNG từ HL API |
| Delta-only hedge: `adjustShortDelta(target − actual)` là mặc định. Full close→open chỉ khi: target=0 (close), emergency reset, manual reset | hedge-sync, preflight | Test case phải kiểm tra delta calculation đúng, không full-replace |
| BigDecimal: tất cả hedge/stop calculation PHẢI dùng BigDecimal. KHÔNG dùng `Number()` cho hedge ratio, stop price, margin | Tất cả formula trong ExBot | Bug nếu dùng floating point |
| Budget overflow = scale-down ladder: 100% → 50% → 25% (scale LP + hedge proportionally). KHÔNG thay đổi hedgeRatio | hedge-sync, preflight margin check | Test boundary: budget vừa đủ, overflow nhẹ, overflow nhiều |
| Queue idempotency: UNIQUE constraint trên `message_id` trong `queue_idempotency`; `started → succeeded`; duplicate → return immediately | Tất cả queue workers | Test case phải kiểm tra re-delivery không double-apply |
| cloid deterministic: client order ID cho HL orders phải deterministic theo bot_id + operation_type | HL adapter, stop placement, hedge order | Idempotent re-submission test |
| BR-EXBOT-006 (LP-first close): LP USDC repayment là unconditional — hedge close failure KHÔNG ĐƯỢC block hoặc reverse LP repayment | user_redeem flow | Critical test case: hedge close fail → LP đã trả → residual_hl_liability |
| user_redeem SLA: 5 phút kể từ khi phát hiện RedemptionEvent (NFR-EXBOT-003) | user_redeem worker | Performance test OOS nhưng functional SLA trace phải check |
| Dual-chain: Base (8453) + OP (10) cả hai từ Phase 1. `wethIndex` phải verify per chain khi mở LP | LP operations | Test phải cover cả 2 chains; wethIndex không hardcode |

### 7.2 Data object / state quan trọng cấp project

| Object / entity | Mô tả | State / lifecycle chính | Ghi chú QC |
|---|---|---|---|
| `bots.lifecycle_state` | Trạng thái bot | idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active; runtime: hedge_stopped_cooldown, lp_rebalancing, lp_closing, closed, safe_mode, error | `cooldown` và `parked` states đã bị xóa (HLD 2026-06-18). Test transition hợp lệ và bất hợp lệ |
| `close_operations` | Idempotency ledger cho close/redeem operations | `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done | residual_hl_liability` | Prevent double settlement; test state machine đầy đủ |
| `UserLockDO` | Distributed lock per user — TTL 90s | acquired → released (hoặc expired) | Phải acquire trước bất kỳ HL operation nào; test TTL expiry, contention |
| `HLRateLimitDO` | Sliding-window rate limiter — 800 wt/min budget | allowed / retryAfterMs | Test rate limit exceeded path; backoff behavior |
| `MarketDataDO` | Cache sqrtPriceX96/tick từ Uniswap pool | cached / stale | Dùng cho LP amount calculation (`uniPoolPrice`) |
| `wl_activation_status` | Trạng thái WL activation per bot | NULL → pending_set → active → failed_set / pending_unset → needs_repair | 6-state machine; failed_set > 48h → auto force-normalize |
| `wl_members.state` | Trạng thái WL membership | (none) → active → leaving → left → active (rejoin, epoch++) | One-wallet-one-WL constraint |
| `wl_codes.status` | Trạng thái WL code | active ↔ suspended | Suspend dừng toàn bộ delivery |

### 7.3 Integration / API / job / notification quan trọng

| Item | Loại | Module liên quan | Ghi chú QC / risk |
|---|---|---|---|
| Hyperliquid API (external) | Integration | ExBot Worker | Rate limit 1,200 wt/min; cloid idempotency; NV-1→7 chưa confirm đủ |
| BnzaExVault (on-chain) | Integration | user_redeem, bot_safe_close | zen deploys; SOTATEK integrate against ABI; address chưa confirm (NV-12) |
| RedemptionQueue (on-chain) | Integration | bot_safe_close | FIFO fulfill; operator-only `fulfillRequest` |
| BNZA OPERATOR Ledger API (`/api/wl/ledger`) | API | WL distribution (Helix pulls) | HMAC-SHA256; range cap 90 ngày; min disclosure rules |
| Queue workers (10 queues) | Job | ExBot Worker | user_redeem: highest priority, SLA 5 phút; hedge-sync: delta-only |
| Cron jobs | Job | ExBot Worker | deep-audit `*/360`; hourly metrics-rollup; 6h stop-integrity scan |
| Notification queue | Notification | ExBot Worker | E-EXBOT-010 (hedge close exceeded SLA) → admin escalation |
| WlNetSent event (on-chain) | Integration | BNZA OPERATOR WL Backend | Scanner mỗi 5 phút; holds-first; unattributed retry max 288 |
| setBotWlMaster/unsetBotWlMaster (on-chain) | Integration | BNZA-ADMIN → OPERATOR → Relayer | Two-phase commit; on-chain tx via Relayer; reconciler backoff |

---

## 8. Platform, environment, device và NFR/ràng buộc

### 8.1 Platform và environment tổng quan

| Hạng mục | Nội dung | Ghi chú QC |
|---|---|---|
| Platform type | PTL-04 (ExBot): API-only / backend-job; PTL-02/03/05 (Admin/EX/Pool): web-desktop; PTL-01 (Mobile): PWA mobile | ExBot tests: logic-only, no UI |
| Deploy | ExBot: Cloudflare Workers (`apps/bnza-exbot/`); Admin/Mobile/EX: CF Pages; Pool: Vercel | KHÔNG co-deploy ExBot với OPERATOR |
| Chains supported | Base (8453) + OP (10). Arbitrum (42161): chỉ cho EX (Hyperliquid direct) | Test phải verify cả Base và OP cho ExBot/Pool/Mobile |
| Test environment | DEV / QA (TBD) — staging environment chưa confirm (OQ-8 trong backbone) | TBD — cần QC Lead xác nhận |
| Integration mode | Hyperliquid: testnet trước, sau đó mainnet | ExBot Phase A1 = testnet |
| Test data | HL agent key encryption method chưa confirm (NV-3); BnzaExVault address chưa deploy | Test data phụ thuộc Phase 0 gate |
| D1 Database | 2 DBs: `control_db` (users, bot_registry, hl_agent_keys) + `state_db_shard_xx` (bots, hedge_legs, close_operations, queue_idempotency, v.v.) | Phase A: 1 shard |

### 8.2 NFR, security, compliance, legal, audit

| Loại ràng buộc | Nội dung đã biết | Ảnh hưởng QC |
|---|---|---|
| Performance | Bot-check latency <100ms; API latency <100ms p95; Uptime 99.9%; 10,000 bots scale (feasibility under review) | Functional test; load test OOS cho QC này |
| Security | HL agent key: master key in CF Secrets Store, per-bot key encrypted in D1 (FM-XB-12) | Test key decryption path; KHÔNG log/expose key |
| Audit | Tất cả writes BNZA-ADMIN require reason note + Slack audit mirror | Test audit trail cho Admin actions |
| Queue idempotency | UNIQUE constraint `message_id`; prevent double settlement qua `close_operations` table | Test tất cả mutation operations có idempotency |
| Blockchain security | MultiSig KHÔNG required cho emergencyTransfer (Operator-only when paused, HLD 2026-06-18) | Test emergency path không cần multisig |
| Privacy | HMAC secret KHÔNG stored trong D1; KHÔNG returned bởi bất kỳ endpoint nào | Test API response không expose secret |
| WL Min disclosure | Ledger API: không expose position_id/pool/token symbols cho Helix | Test disclosure rules cho `/api/wl/ledger` |

---

## 9. Đánh giá mức độ đủ context cấp project

| Nhóm context | Trạng thái | Độ tin cậy | Ảnh hưởng nếu thiếu/sai | Cần QC Lead bổ sung gì |
|---|---|---|---|---|
| Project goal & scope | Ready | High | — | Không |
| System/site/module overview | Ready | High | — | Không |
| Feature/use case inventory | Ready | High | — | Không |
| Users/roles/permission overview | Ready | High | — | Không |
| Business flows & module relationship | Ready | High | — | Không |
| Common rules/data/state/integration | Ready | High | — | Không |
| Platform/environment/device/NFR | Partial | Medium | Test environment chưa rõ → không biết test ở đâu | Xác nhận staging environment, HL testnet access, test accounts |
| Document status tracking | Partial | Medium | qc-site-map và qc-dashboard chưa tồn tại | sẽ được tạo qua qc-site-map (auto-invoke) |

**Kết luận:**  
Context cấp project đã đủ để QC Agent hiểu tổng quan hệ thống, scope, actors, flows và common rules. Phần còn thiếu là thông tin cụ thể về test environment/accounts (cần QC Lead cung cấp) và site-map/dashboard (sẽ được tạo tự động). Phase 0 gate của ExBot chưa đủ điều kiện — test ExBot Phase A phụ thuộc vào tiến độ của zen.

---

## 10. Open questions và việc cần QC Lead xác nhận

| ID | Câu hỏi / thông tin cần xác nhận | Vì sao quan trọng | Ảnh hưởng nếu chưa rõ | Priority | Owner | Status |
|---|---|---|---|---|---|---|
| Q-001 | Staging/QA environment cho ExBot đã được setup chưa? Domain? Wrangler config? | Cần environment để test ExBot queue, cron, DO | Không thể test ExBot nếu chưa có environment | High | QC Lead / Ops | Open |
| Q-002 | Trạng thái Phase 0 gate hiện tại: (2) BnzaExVault deployed chưa? (3) HL agent key encryption confirmed chưa? (4) WL stability gate passed chưa? | Gate 2-4 quyết định ExBot Phase A có thể bắt đầu không | Không thể test integration thực nếu gate chưa pass | High | QC Lead / zen | Open |
| Q-003 | NV-3 kết quả: HL có accept duplicate reduce-only stops không? → quyết định §19.5 INV-STOP implementation path (a) hay (b) | Ảnh hưởng trực tiếp đến test case thiết kế cho stop replacement | Không thể thiết kế test case đầy đủ cho INV-STOP | High | SOTATEK (verify với HL) | Open |
| Q-004 | NV-12 kết quả: Base + OP pool addresses, wethIndex per chain đã confirm chưa? | Cần để test LP position calculation đúng per chain | LP amount test case có thể sai nếu wethIndex chưa rõ | High | zen | Open |
| Q-005 | Test accounts: HL testnet agent key, BnzaExVault testnet address, USDC testnet faucet | Cần test data thực để run integration tests | Không test được ExBot end-to-end | Medium | QC Lead / zen | Open |
| Q-006 | Mục 2-5 của `project-config.md` (Associated Links, Environments, Accounts, Third-party APIs) chưa được điền | Downstream skills cần thông tin này | Site-map và dashboard sync có thể bị thiếu context | Medium | QC Lead | Open |
| Q-007 | FM-ADM-13 (Escalations Dashboard), FM-ADM-14 (Holds Review), FM-ADM-15 (Attribution History): FR/UC/US đang được authoring — trạng thái hiện tại? | QC cần biết khi nào spec sẵn sàng để lên lịch review | Delay spec review nếu chưa rõ timeline | Low | BA (hien.duong) | Open |

---

## Phụ lục A. Nguyên tắc giữ file gọn

- Chỉ ghi thông tin cấp project hoặc thông tin dùng chung cho nhiều Agent/skill.
- Không copy toàn bộ nội dung từ spec, wireframe, API document hoặc use case detail.
- Không ghi test case chi tiết trong file này.
- Không lặp lại danh sách feature dài nếu đã có `feature list` hoặc `qc-dashboard`.
- Nếu thông tin đã có ở file khác, chỉ tóm tắt vai trò và dẫn Agent đọc file đó.
- Nếu một thông tin chỉ ảnh hưởng một function cụ thể, đưa vào function-level context/spec review, không đưa vào file này.
