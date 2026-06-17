# Project Context Master: Bonanzapool (BNZA Ecosystem — SOTATEK Scope)

**Trạng thái:** Draft → Updated (Line scope split)
**Ngày tạo/cập nhật:** 2026-06-16
**Người chuẩn bị:** QC Context Agent (`qc-context-master`)
**Người review:** QC Lead
**Mục đích:** Cung cấp bối cảnh tổng quan cấp project để các QC Agent hiểu đúng hệ thống Bonanzapool (gói SOTATEK 8 tuần, 2026-05-18 → 2026-07-12), phạm vi, rule chung, rủi ro và trạng thái tài liệu trước khi review spec, thiết kế scenario hoặc test case, hỗ trợ test execute hoặc verify bug. **Lưu ý quan trọng:** Line 1 đã hoàn thành, phạm vi QC sắp tới chỉ tập trung vào Line 2 (EXBOT Infra) — xem section "Chỉ thị phạm vi QC hiện tại" ở trên.

> File này là tài liệu high-level do Agent tổng hợp để QC Lead review và bổ sung.
> File này không thay thế spec, wireframe, API document, use case detail hoặc các tài liệu chi tiết do BA/BE/Tech Lead cung cấp.
> File này nên ngắn gọn, chỉ giữ thông tin có ảnh hưởng đến cách QC Agent hiểu dự án, đánh giá impact, review tài liệu hoặc thiết kế kiểm thử.

---

## ⚠️ CHỈ THỊ PHẠM VI QC HIỆN TẠI (BẮT BUỘC ĐỌC TRƯỚC)

> **Cập nhật:** 2026-06-16 — QC Lead xác nhận.

Dự án có **2 line delivery song song**. Trạng thái hiện tại:

| Line | Tên | Phạm vi | Trạng thái QC | Vai trò hiện tại |
|------|-----|---------|---------------|-------------------|
| **Line 1** | WL + MLM System + Maintain Pool/Exchange | PTL-02 BNZA-ADMIN, PTL-03 BNZA-EX, PTL-05 BNZA-POOL Steps 7-8, Smart Contracts (FM-WLC-01), BNZA-OPERATOR WL Backend (FM-OPW-01→07) | ✅ **ĐÃ HOÀN THÀNH** | Chỉ còn là **dependency context** cho Line 2. **KHÔNG cần thực hiện test mới.** |
| **Line 2** | Exchange Bot + Backtest (EXBOT Infra) | PTL-04 BNZA-EXBOT Infra (FM-XB-01→FM-XB-13) | 🔜 **SẮP LÀM** | **Phạm vi QC hoạt động duy nhất** sắp tới. |

**Quy tắc cho tất cả QC Agent downstream:**

1. **KHÔNG** thiết kế test mới, review spec mới, hoặc tạo scenario/test case mới cho bất kỳ feature thuộc Line 1 (FM-ADM-*, FM-EX-*, FM-PL-*, FM-WLC-*, FM-OPW-*).
2. **CHỈ** tập trung vào Line 2: EXBOT Infra (FM-XB-01 → FM-XB-13).
3. Khi đọc context Line 1 trong file này, coi đó là **thông tin tham chiếu dependency** — ví dụ: EXBOT Infra (Line 2) phụ thuộc OPERATOR Queue v2 pattern (Line 1), Router/LPBot contract (Line 1), v.v.
4. Các section về Line 1 bên dưới (portal, actor, flow, rule, integration) vẫn giữ nguyên để Agent hiểu context hệ thống tổng thể, nhưng **không phải là đối tượng test**.

---

## Bảng mã viết tắt

Chỉ liệt kê các tiền tố thực sự xuất hiện trong file này.

| Mã / Tiền tố | Ý nghĩa | Nơi định nghĩa gốc |
|---|---|---|
| `PTL-*` | Portal — vùng sản phẩm tách theo URL/sub-domain (PTL-01 đến PTL-06) | `02_backbone/feature-map.md §1` + `02_backbone/backbone.md §2` |
| `ACT-*` | Actor — vai trò người dùng hoặc tác nhân hệ thống (ACT-01 đến ACT-07) | `02_backbone/feature-map.md §2` + `02_backbone/backbone.md §1` |
| `FM-*` | Feature ID — mã tính năng theo module: `FM-WLA-*` (WL Admin System), `FM-MOB-*` (WL Mobile, tên cũ BNZA-MOBILE), `FM-ADM-*` (BNZA-ADMIN), `FM-EX-*` (BNZA-EX), `FM-XB-*` (BNZA-EXBOT Infra), `FM-PL-*` (BNZA-POOL Steps 7-8) | `02_backbone/feature-map.md §3` |
| `LD-*` | Locked Decision — quyết định khoá scope đã được zen/BA chốt | `01_intake/intake.md §11` |
| `OQ-*` | Open Question — câu hỏi mở do BA ghi nhận trong tài liệu intake/backbone | `01_intake/intake.md §10`, `02_backbone/backbone.md §9` |
| `BR-*` | Business Rule cấp module (`BR-MOB`, `BR-EX`, `BR-PL`, `BR-ADM`, `BR-WLA`) | `02_backbone/common-rules.md` |
| `E-*` | Mã message UI (`E-MOB`, `E-pool`, `E-ADM`, `E-WLA`) | `02_backbone/message-list.md` |
| `T0…T3` | Priority Tier — T0 dành cho WL Launch, T1 Core Dev, T2 Enhancement, T3 Low | `02_backbone/feature-map.md §5` |
| `WL` | White-label MLM operator — khách hàng B2B của BNZA vận hành dưới brand riêng | `02_backbone/backbone.md §8.8.2` |
| `MLM` | Multi-Level Marketing — mô hình chia hoa hồng theo cây giới thiệu nhiều cấp | (thuật ngữ ngành) |
| `SIWE` | Sign-In With Ethereum — chuẩn đăng nhập web bằng chữ ký ví Ethereum (EIP-4361) | `02_backbone/backbone.md §8.1` |
| `HMAC-SHA256` | Hash-based Message Authentication Code dùng SHA-256 — cơ chế ký request server-to-server bằng shared secret | `02_backbone/backbone.md §8.1` |
| `RBAC` | Role-Based Access Control — phân quyền theo role | `02_backbone/backbone.md §8.1` |
| `PWA` | Progressive Web App — ứng dụng web có thể cài đặt và chạy giống app native | `02_backbone/backbone.md §5.0B` (FM-MOB-10) |
| `DO` | Cloudflare Durable Objects — đối tượng có trạng thái bền và xử lý tuần tự trên CF Workers | `02_backbone/backbone.md §2` |
| `CF` | Cloudflare — nền tảng cung cấp Pages, Workers, D1, Queues, Secrets Store | `02_backbone/backbone.md §2` |
| `D1` | Cloudflare D1 — cơ sở dữ liệu SQLite serverless do CF host | `02_backbone/backbone.md §2` |
| `PF` | Performance Fee — phí chia hiệu suất, 30% phần earnings sau khi trừ operating fee | `02_backbone/backbone.md §8.2` |
| `AUM` | Assets Under Management — tổng tài sản đang được hệ thống quản lý | `02_backbone/backbone.md §8.8.2` |
| `TVL` | Total Value Locked — tổng giá trị tài sản đang khoá trong protocol | `02_backbone/backbone.md §8.8.5` |
| `LP` | Liquidity Provider — vị thế cung cấp thanh khoản, ở đây là Uniswap V3 LP NFT | `02_backbone/backbone.md §8.8.1` |
| `HL` | Hyperliquid — sàn giao dịch perpetuals trên Arbitrum (chain 42161) | `02_backbone/backbone.md §2` |
| `OP` | Optimism — mainnet Layer 2 Ethereum (chain ID 10) | `02_backbone/common-rules.md` |
| `NFR` | Non-Functional Requirement — yêu cầu phi chức năng (hiệu năng, bảo mật, khả dụng…) | `01_intake/intake.md §6` |
| `WCAG` | Web Content Accessibility Guidelines — chuẩn tiếp cận web do W3C ban hành | (không xuất hiện cụ thể; mục tham chiếu khi BA bổ sung) |

---

## Sources consolidated

> Bảng này liệt kê các file đã được đọc và tổng hợp ra nội dung phía dưới. Lần chạy update sau sẽ so version trong tên file (`_v<N>`) để biết source có thay đổi hay không.

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | intake.md | không có version | Product brief, scope, stakeholders, assumptions, risks, out of scope, open questions | 2026-06-08 |
| 2 | plan.md | không có version | WBS, plan, phase status | 2026-06-08 |
| 3 | backbone.md | không có version | Architecture, auth model, permissions, dependency, fee model, NFR | 2026-06-08 |
| 4 | feature-map.md | không có version | Feature inventory, portal & actor registry | 2026-06-08 |
| 5 | common-rules.md | không có version | Business rules | 2026-06-08 |
| 6 | message-list.md | không có version | Message catalog | 2026-06-08 |
| 7 | project-config.md | không có version | Project config (overview, environment, account, third-party) | 2026-06-08 |

> **Ghi chú update 2026-06-16:** Lần cập nhật này không do source file thay đổi version mà do QC Lead yêu cầu tách rõ phạm vi Line 1 (đã hoàn thành) và Line 2 (sắp làm) để các downstream Agent không xác định sai scope.

---

## 1. Cách các QC Agent sử dụng file này

| Nhóm Agent / Skill | Cách sử dụng project context | Cần đọc thêm file nào |
|---|---|---|
| Site map / dashboard / high-level review (`qc-site-map`, `qc-dashboard-sync`) | Hiểu cấu trúc 6 portal (PTL-01 đến PTL-06), 7 actor (ACT-01 đến ACT-07), 42 feature ID (`FM-*`) và 2 line delivery. **Line 1 đã hoàn thành — chỉ còn là dependency context. Line 2 (EXBOT Infra) là phạm vi QC hoạt động duy nhất.** | `02_backbone/feature-map.md`, `02_backbone/backbone.md §2 đến §5`, `03_modules/exbot/`. |
| Spec review cấp function (`qc-uc-smoke`, `qc-uc-read`) | **Chỉ áp dụng cho Line 2 (FM-XB-*).** Dùng context tổng quan để kiểm spec có đúng EXBOT architecture (D1, Queue, DO, HL adapter), đúng auth model (internal system, không có user auth), và không vi phạm pattern Queue v2 hiện hữu. | `03_modules/exbot/frd.md`, `02_backbone/backbone.md §8.7`. |
| Scenario design (`qc-func-scenario-design`) | **Chỉ áp dụng cho Line 2 (FM-XB-*).** Xác định dependency của EXBOT với OPERATOR Queue v2 (Line 1 dependency), Hyperliquid API, và 4 gate conditions Phase 0. | `03_modules/exbot/frd.md`, `02_backbone/backbone.md §6`, `02_backbone/feature-map.md §4`. |
| Test case design (`qc-func-tc-design`) | **Chỉ áp dụng cho Line 2 (FM-XB-*).** Vận dụng architecture constraints của EXBOT (Queue pattern, D1 hot+R2 archive, RelayerLockDO, 10k bot scale) và Hyperliquid rate limit (1200 req/min) để có expected result chính xác. | `03_modules/exbot/frd.md`, scenarios, EXBOT SPEC v5.2.5 interface. |
| Test execute | Hiểu môi trường triển khai (CF Workers chạy chung với OPERATOR), Hyperliquid testnet cho Phase A1. **Chỉ execute test cho Line 2.** | `project-config.md`, deployment guide. |
| Bug verify | **Chỉ verify bug thuộc Line 2 (EXBOT Infra).** Hiểu vùng impact dựa trên dependency với OPERATOR (Line 1 — dependency context), các gate conditions, và HL adapter. | Bug report, spec `FM-XB-*` liên quan. |

**Quy tắc sử dụng:**
Nếu thông tin trong file này mâu thuẫn với spec, wireframe hoặc API chi tiết đã approved (ví dụ FRD theo module, SPEC v5.2.5 của EXBOT), Agent phải báo conflict và ưu tiên tài liệu chi tiết đã approved, trừ khi QC Lead có chỉ định khác. Tất cả thay đổi scope hoặc architecture đều được BA chú thích bằng tag `[SCOPE CHANGE]` hoặc `[NEW]` ngay trong source — đọc kèm để biết phiên bản nào đang hiệu lực.

---

## 2. Tóm tắt dự án

| Hạng mục | Nội dung |
|---|---|
| Tên dự án / sản phẩm | Bonanzapool — BNZA Ecosystem, gói SOTATEK 8 tuần. |
| Domain / nghiệp vụ | DeFi / CeDeFi — Automated Liquidity Provisioning (bot tự động cung cấp thanh khoản Uniswap V3) kết hợp Perpetuals trading (sàn Hyperliquid) và nền tảng White-label MLM. |
| Loại dự án | Hỗn hợp: New build (WL Admin System, WL Mobile, EXBOT Infra) + Enhancement (BNZA-ADMIN chuyển từ mock sang real, BNZA-POOL Step 7-8, BNZA-EX nâng cấp TradingView Advanced Charts) + Maintenance (bug fix POOL/EX). |
| Mục tiêu chính của dự án/release | (1) Đưa hệ thống WL+MLM go-live ngày 2026-06-02 dùng LPBot, theo quyết định khoá `LD-8` (WL launch product là MLM + LPBot, không phải EXBOT); (2) Hoàn thiện BNZA-ADMIN phục vụ WL launch, gồm WL Management và PF Distribution; (3) Xây EXBOT Infra (hoãn khoảng 6 tuần sau WL launch); (4) Hoàn tất BNZA-POOL Step 7-8 và nâng cấp BNZA-EX TradingView (sau WL launch). |
| Người dùng chính | (a) End User retail tự tạo LP Bot hoặc trade (`ACT-01`, `ACT-05`); (b) WL Partner và WL End User trong cây MLM (`ACT-02`, `ACT-03`); (c) Admin nội bộ zen (`ACT-04`) và WL Operator Admin (`ACT-07`); (d) OPERATOR — tác nhân backend tự động (`ACT-06`). |
| Release / phase hiện tại | **Line 1 (WL+MLM + maintain Pool/EX): ĐÃ HOÀN THÀNH.** Line 2 (EXBOT Infra): sắp bắt đầu, chờ gate conditions. |
| Trạng thái tổng quan | **Line 1 hoàn thành** — QC đã done cho BNZA-ADMIN, BNZA-EX, BNZA-POOL, WL Contracts, OPERATOR WL Backend. **Line 2 chưa bắt đầu** — EXBOT Infra (FM-XB-01→FM-XB-13) là phạm vi QC hoạt động duy nhất sắp tới; bị chặn bởi 4 gate conditions Phase 0 (xem §3.3). |

**Tóm tắt ngắn:**
Bonanzapool là hệ sinh thái DeFi/CeDeFi của MEGABUCKS, Inc., với 5 sản phẩm chính: BNZA-POOL (LP Bot retail), BNZA-EX (giao dịch Hyperliquid), BNZA-ADMIN (dashboard nội bộ), BNZA-EXBOT (LP Bot có hedge để giảm rủi ro biến động giá) và WL Mobile. Gói SOTATEK chia thành 2 line delivery: **Line 1** (WL+MLM + maintain Pool/EX) và **Line 2** (EXBOT Infra + Backtest). **Line 1 đã hoàn thành** — WL go-live ngày 2026-06-02 với MLM + LPBot (theo `LD-8`), QC cho Line 1 đã done. **Line 2 là phạm vi QC hoạt động duy nhất sắp tới** — EXBOT Infra (FM-XB-01→FM-XB-13) trên PTL-04, bị chặn bởi 4 gate conditions Phase 0 và chờ zen cung cấp interface specs (`Q-001`). Line 1 chỉ còn vai trò dependency context cho Line 2 (ví dụ: OPERATOR Queue v2 pattern, Router/LPBot contract, D1 schema hiện có).

---

## 3. Phạm vi tổng thể và ranh giới kiểm thử

### 3.1 In scope cấp project/release

| Area / site / module / capability | Mô tả ngắn | Priority | Line | Trạng thái QC | Ghi chú |
|---|---|---|---|---|---|
| WL Admin System (PTL-06) | Layer B của WL+MLM. | High (T0/T1) | Line 1 | ✅ Done (OOS — Helix scope) | Không thuộc scope test SOTATEK. Chỉ là interface context. |
| WL Mobile = BNZA-MOBILE (PTL-01) | Layer C, SIWE auth, reward display, bot ops, PWA. | High (T0/T1) | Line 1 | ✅ Done (OOS — Helix scope) | Không thuộc scope test SOTATEK. Chỉ là interface context. |
| BNZA-ADMIN (PTL-02) | Dashboard quản lý nội bộ cho zen. | High (T0) đến Low (T3) | **Line 1** | ✅ **Done** | QC đã hoàn thành. Chỉ còn là dependency context cho Line 2. |
| BNZA-EX (PTL-03) | Nâng cấp TradingView Advanced Charts. | Medium (T2) | **Line 1** | ✅ **Done** | QC đã hoàn thành. Tách biệt, không ảnh hưởng Line 2. |
| BNZA-EXBOT Infra (PTL-04) | Backend hạ tầng cho EXBOT: D1, Queue, DO, cron, HL adapter, API. | High (T0) đến Medium (T2) | **Line 2** | 🔜 **PHẠM VI QC HOẠT ĐỘNG DUY NHẤT SẮP TỚI** | Bị chặn bởi 4 gate conditions Phase 0. Chờ zen cung cấp interface specs (`Q-001`). |
| BNZA-POOL Steps 7-8 (PTL-05) | Step 7 multi-bot UI, Step 8 plan_specs version. | Medium (T1/T2) | **Line 1** | ✅ **Done** | QC đã hoàn thành. |
| WL Smart Contracts (FM-WLC-01) | Router + LPBot WL changes A–K. | High (T0) | **Line 1** | ✅ **Done** | QC đã hoàn thành. |
| BNZA-OPERATOR WL Backend (FM-OPW-01→07) | DB migrations, Ledger API, Bot API, scanner, reconcilers. | High (T0/T1) | **Line 1** | ✅ **Done** | QC đã hoàn thành. Là dependency chính của Line 2 (EXBOT dùng chung OPERATOR codebase). |

### 3.2 Out of scope / chưa làm trong phase này

| Area / site / module / capability | Lý do loại trừ / deferred | Ảnh hưởng đến QC |
|---|---|---|
| EXBOT trading strategy logic (PositionCalc, hedge math, stop strategy, edge filter) | Là tài sản độc quyền của zen, không công khai cho SOTATEK. | QC không có visibility vào logic nên chỉ test được interface contract. |
| Thay đổi smart contract Router/LPBot (trừ phần upgrade phục vụ WL) | On-chain đã stable và đã deploy bản v2.2.2-fix-2 + v1.2. | Coi như behavior chuẩn; QC chỉ test integration. |
| Sửa contract TOKEN, contract Buy & Burn | Không thuộc gói SOTATEK. | Chỉ test UI mock nếu QC Lead xác nhận giữ pass. |
| BnzaSplitter on-chain contract | Loại khỏi v1 theo `WL_SPEC_SOTATEK_EN_v1.0 §1.2`; PF chảy thẳng về `pfCollector` EOA (Externally Owned Account — ví đơn không phải contract). | Loại khỏi test path; cần verify `FM-ADM-02` PF Distribution chỉ chạy off-chain. |
| MLM reward computation, referral tree, RewardDistributor payout (Layer B) | Helix/WL build theo `01_intake/intake.md §9`. | Cần QC Lead làm rõ phạm vi test PTL-06 — xem `Q-014` ở §10. |
| Multi-region deployment (Phase 3), Enterprise SLA features, marketing/community | Thuộc roadmap dài hạn ngoài 8 tuần SOTATEK. | Không nằm trong test plan release này. |
| Các tính năng core POOL ngoài Step 7-8 | Đã chạy ổn định. | Chỉ regression nhẹ. |
| OPERATOR Queue v2 core implementation | Đã có sẵn; EXBOT chỉ tích hợp vào. | Test integration EXBOT phải tôn trọng pattern hiện hữu, không xây lại. |

### 3.3 Assumption, dependency, constraint quan trọng

| Loại | Nội dung | Ảnh hưởng đến QC Agent | Cần xác nhận? |
|---|---|---|---|
| Assumption | Zen sẽ cung cấp EXBOT interface specs (schema D1, topology queue, contract API) trước khi SOTATEK bắt đầu làm EXBOT. (Mã tham chiếu: `01_intake/intake.md §7` assumption 1.) | Test design EXBOT bị block đến khi specs về tay QC. | Yes — gắn với open question `Q-001` (gốc `OQ-2` trong `intake.md §10`). |
| Assumption | Router v2.2.2-fix-2 và LPBot v1.2 đã deploy ổn định, ABI mới đã được sử dụng (hàm `closeForUser` nhận 7 tham số, struct `startBot` 11 field, thêm cờ `convertToUsdc`). (Mã tham chiếu: `01_intake/intake.md §7` assumption 5.) | Test integration phải bám ABI mới này. | No — đã resolved bởi zen. |
| Assumption | License TradingView Advanced Charts đã được zen fund, không phải blocker. | EX integration test có thể lên kế hoạch, chỉ chờ license thực tế. | No — `OQ-3` đã resolved. |
| Assumption | EXBOT Phase A bị chặn cho đến khi 4 gate sau cùng đạt: (a) zen approve SPEC v5.2.5; (b) contract `BnzaExVault` đã deploy và confirm; (c) cơ chế mã hoá HL agent key đã confirm; (d) WL ổn định 7 ngày liên tục post-launch và không vào `SAFE_MODE` (chế độ khẩn tạm dừng giao dịch). (Mã tham chiếu: `01_intake/intake.md §7` assumption 11.) | QC không có test target Hyperliquid thật trước khi gate mở; chỉ test infra và dry-run. | Yes (phụ thuộc trạng thái thực). |
| Dependency | 19 endpoint OPERATOR hiện có phải giữ ổn định trong suốt sprint SOTATEK. (Mã tham chiếu: `01_intake/intake.md §7` assumption 4.) | API contract freeze — nếu thay đổi sẽ gây regression nhiều module. | No (cam kết của zen). |
| Dependency | WL Mobile phụ thuộc API của Helix-built admin system (`/api/mobile/*` SIWE/JWT) cho toàn bộ dữ liệu hiển thị. | Mobile test cần mock hoặc endpoint Helix thật. | Yes — cần làm rõ chế độ stub hay live trước khi viết test. |
| Constraint | NFR scale 10.000 bot ngay từ ngày đầu đang chờ Daniel review (giới hạn concurrent worker của CF). | Performance/scale test target chưa chốt, chờ report (`Q-009`). | Yes. |
| Constraint | Rủi ro migration mainnet với khoảng 8 user và 250k USD fund; Andrew chuẩn bị plan validation. | Cần regression plan cho production cutover (`Q-010`). | Yes. |
| Constraint | Project tổ chức monorepo với `apps/bnza-{pool,operator,admin,ex,ecosystem,mobile}`, `contracts/bnza-{router,lpbot,contracts}` và `packages/shared-{types,utils}`, theo quyết định khoá `LD-7`. | QC điều hướng codebase theo layout này. | No (locked). |
| Constraint | Sản phẩm cho WL launch là MLM + LPBot (KHÔNG phải EXBOT) theo quyết định khoá `LD-8`. EXBOT chỉ migrate vào WL sau khi Phase A hoàn tất. | QC plan M1 không bao gồm EXBOT path. | No (locked). |

---

## 4. Cấu trúc hệ thống và tài liệu high-level liên quan

### 4.1 System / site / portal overview

| Site / portal / app | Mục đích | Nhóm user chính | Module chính | Ghi chú |
|---|---|---|---|---|
| PTL-01 — WL Mobile (BNZA-MOBILE), URL `wl.bnza.io` (TBD) | App PWA cho WL End User xem reward sau khi đã allocation, claim USDC, vận hành LP Bot, xem community và referral. | `ACT-03` WL End User; `ACT-02` WL Partner (chỉ xem earning). | `apps/bnza-mobile/` — Vite, React 19, TypeScript 5.9, Zustand, Tailwind 4, shadcn/ui, Reown AppKit, PWA. | Hosting CF Pages; auth SIWE → JWT thời hạn 24 giờ; chain Base + OP; tenant theo subdomain. |
| PTL-02 — BNZA-ADMIN, URL `ops.bnza.io` | Dashboard nội bộ cho zen quản lý bot, plan_specs, user, RBAC, tài khoản WL partner, cấu hình PF, IB, system settings, relayer, reports. | `ACT-04` Admin (zen). | `apps/bnza-admin/` — React 19.2, Vite 8.0, TypeScript 5.9, Tailwind 4.2, shadcn/ui, React Router 7.14, TanStack Query 5.100. | Hosting CF Pages; auth Wallet + Cloudflare Access (`zen@bnza.io`) + RBAC; 16 page đã scaffold. |
| PTL-03 — BNZA-EX, URL `ex.bnza.io` | Frontend trading perpetuals Hyperliquid, nâng cấp lên TradingView Advanced Charts. | `ACT-01` End User, `ACT-05` Trader. | `apps/bnza-ex/` — React 18.3, Vite 6.0, plain JavaScript, Wagmi 3.6, `@nktkas/hyperliquid` 0.32. | Chain Arbitrum 42161; trade trực tiếp Hyperliquid, không đi qua OPERATOR. Plain JavaScript (không TypeScript). |
| PTL-04 — BNZA-EXBOT Infra, URL `api.bnza.io` | Backend EXBOT trên CF Workers (chung deploy với OPERATOR): D1, Queue, DO, cron, HL adapter, các API endpoint. | `ACT-06` OPERATOR (system); `ACT-04` Admin cho phần cấu hình. | `apps/bnza-operator/` — CF Workers, Hono 4.12, D1 (22 migrations), Queues (3 queue đã defined), DO (2 active), KV. | Trading logic do zen độc quyền; SOTATEK chỉ xây hạ tầng. |
| PTL-05 — BNZA-POOL, URL `pool.bnza.io` | Frontend LP Bot retail — Step 7 multi-bot UI và Step 8 quản lý version `plan_specs`. | `ACT-01` End User; `ACT-04` Admin (chỉ xem). | `apps/bnza-pool/` — Next.js 16.2, React 19.2, TypeScript 5.9, Tailwind 4, shadcn/ui, Wagmi 2.19, TanStack Query 5.94. | Hosting Vercel (tách khỏi monorepo deploy CF). Chain Base + OP. |
| PTL-06 — WL Admin System, URL `wl-admin.bnza.io` (TBD) | Tool nội bộ cho WL Operator Admin chạy distribution pipeline daily, reward computation, RewardDistributor, admin console 7 page, multi-tenant config, reconciliation. | `ACT-07` WL Operator Admin với 3 role: Super, Operator, Read-only. | `apps/bnza-wl-admin/` — CF Pages (frontend) + CF Workers (backend và cron) + CF D1 (25 bảng) + CF Queues. | Auth SSO qua Cloudflare Access + 2FA TOTP (Time-based One-Time Password). **Phạm vi build:** `01_intake/intake.md §9` ghi Layer B là Helix build chứ không phải SOTATEK; cần QC Lead chốt phạm vi test — xem `Q-014` ở §10. |

### 4.2 Các file high-level liên quan

| File | Vai trò | Trạng thái | Ghi chú |
|---|---|---|---|
| `01_intake/intake.md` | Project context, 2 line delivery, stakeholders, scope theo module, dependency cross-module, NFR, risk, 11 Locked Decision, 8 Open Question. | In-review (cập nhật 2026-06-04). | Tài liệu self-contained — đã absorb 22 source document client; QC không cần đọc external. |
| `01_intake/plan.md` | Trạng thái 7 phase BA artifact, milestone scope M1 đến M4, pending reports. | In-progress (cập nhật 2026-05-27). | Theo dõi tiến độ artifact, không phải tiến độ code. |
| `02_backbone/backbone.md` | Shared actor và portal matrix, permission matrix per portal, dependency graph, fee model, auth model, kiến trúc 3 layer WL+MLM, kiến trúc contract EXBOT. | In-review (cập nhật 2026-06-04). | Là source canonical cho rule cross-module; FRD theo module derive từ đây. |
| `02_backbone/feature-map.md` | Single source of truth cho 42 mã `FM-*`, registry portal và actor, priority tier T0 đến T3, dependency cross-feature. | In-review (cập nhật 2026-06-03). | Mọi `FR-*`, `UC-*`, `US-*` trong module artifact phải trace về ít nhất 1 `FM-*`. |
| `02_backbone/common-rules.md` | Registry business rule cấp module: `BR-MOB`, `BR-EX`, `BR-PL`, `BR-ADM`, `BR-WLA`. | Draft (cập nhật 2026-06-02). | Là input chính cho QC khi viết expected result và precondition. |
| `02_backbone/message-list.md` | Registry message UI: `E-MOB`, `E-pool`, `E-ADM`, `E-WLA`. | Draft (cập nhật 2026-06-02). | QC dùng để verify hiển thị message và label original-language. |
| Site map | Cung cấp cấu trúc site/module/screen tổng thể. | Missing | Sẽ được tạo bởi `qc-site-map` trong chain top-down. |
| Feature list | Danh sách feature/use case để đánh giá scope, impact, regression. | Reviewed (đã có trong `feature-map.md`). | QC Agent dùng trực tiếp; không tạo lại trong file này. |
| `qc-dashboard.md` | Theo dõi trạng thái spec, wireframe, scenario, test case, execute theo từng feature. | Missing | Sẽ được bootstrap bởi `qc-dashboard-sync` sau `qc-site-map`. |
| `docs/qc-lead/project-config.md` | Cấu hình project — overview, link, environment, account, third-party. | Draft (v2, cập nhật 2026-05-10). | Phần lớn ô vẫn là placeholder ("`[company]`", `[e.g., Stripe]`); cần QC Lead hoặc DevOps điền giá trị thực. |
| `docs/bnza-docs/`, `docs/bnza-exbot/docs/SPEC_v5.2.5.md`, `docs/wl/OVERVIEW.{en,ja}.md` | Tham chiếu bổ sung (ECOSYSTEM_OVERVIEW, README/SPEC theo module, WL Overview). | Available — nhưng chưa được register vào `High-level-files` của `path-registry.md`. | Đã được absorb vào intake/backbone; chỉ tra cứu khi cần verify một chi tiết kỹ thuật. |

---

## 5. Users, roles và permission tổng quan

| Role / actor | Mô tả | Workflow chính | Permission / responsibility tổng quan | Ghi chú QC |
|---|---|---|---|---|
| `ACT-01` End User (LP) | User retail tự tạo và quản lý LP Bot, xem earning, deposit/withdraw. | Trên PTL-05 POOL: tạo bot, start/stop bằng ví. Trên PTL-03 EX: trade perpetuals Hyperliquid. | Truy cập đầy đủ PTL-03 và PTL-05. Auth qua header `X-Wallet-Address`. | Khi start bot cần USDC approve + `setApprovalForAll` + `zapMint`; khi stop có deadline +1200 giây (`BR-PL-07`). UI giới hạn tối đa 10 bot/chain (`BR-PL-11`). |
| `ACT-02` WL Partner | Institutional broker — đại lý tổ chức xem earning và quản lý end user của mình qua WL Mobile. | Trên PTL-01: xem earning của user thuộc WL mình quản lý. | Read-only earning view. Auth Wallet + WL invite code. | Test: chỉ được xem dữ liệu user thuộc WL của mình, không được rò sang WL khác. |
| `ACT-03` WL End User | Người tham gia MLM dưới một WL operator. | Trên PTL-01: SIWE sign-in, xem reward, claim USDC, vận hành LP Bot, xem community. | Toàn quyền trên PTL-01. Auth SIWE → JWT 24h, tenant được giải bởi server từ subdomain + signature domain (`BR-MOB-003`). | UI không bao giờ hiện raw uncollected fees của LP NFT (`BR-MOB-004`); bot ops bắt buộc cờ `convertToUsdc=true` và `autoCompound=false` (`BR-MOB-005`); khi JWT hết hạn → silent re-sign, không hiện banner (`BR-MOB-002`). |
| `ACT-04` Admin (zen) | Administrator hệ thống của BNZA, full quyền trên ADMIN. | Trên PTL-02: WL Partner onboarding (members, master wallet, suspend), cấu hình PF off-chain, IB, bot config, system settings, relayer monitor, WL Bot Lifecycle Monitor. | Full PTL-02; Config PTL-04; Full PTL-05. Auth Wallet + Cloudflare Access + RBAC với 3 role `super_admin`, `admin`, `viewer`. | Test: chỉ `super_admin` mới được tạo/sửa/disable WL partner (`BR-ADM-002`). Suspend WL khoá toàn bộ delivery (`BR-ADM-014`). |
| `ACT-05` Trader | Trader perpetuals trên BNZA-EX (Hyperliquid). | Trên PTL-03: view chart, đặt lệnh bằng agent key. | Toàn quyền trên PTL-03. Auth Wallet trực tiếp Hyperliquid, không đi qua OPERATOR (`BR-EX-06`). | Chain duy nhất là Arbitrum 42161 (`BR-EX-01`); lệnh được ký bằng agent key (`BR-EX-04`). |
| `ACT-06` OPERATOR (System) | Tác nhân backend tự động — cron, relayer, queue consumer. | Trên PTL-04: xử lý queue, chạy cron, đọc/ghi D1, quản lý DO, gọi HL adapter. | Toàn quyền PTL-04 ở mức system. Không có user auth. | Ưu tiên integration test cho queue và HL API, mô tả ở `02_backbone/backbone.md §8.6`. |
| `ACT-07` WL Operator Admin | Đội vận hành WL — theo dõi và khôi phục distribution daily, quản lý referral tree, xử lý incident. | Trên PTL-06: distribution job recovery, referral tree, distributor refill, reward settings, admin & auth management. | 3 role: Super (toàn quyền), Operator (vận hành + tree + refill, không vào settings), Read-only (chỉ xem). Auth SSO qua Cloudflare Access + 2FA TOTP bắt buộc. | Mọi write op đòi reason note và Slack audit mirror, mô tả ở `02_backbone/backbone.md §5.0`. |

**Lưu ý:**
Chỉ ghi permission tổng quan và rule dùng chung ở đây. Permission chi tiết theo từng action nằm trong `02_backbone/backbone.md §4.1` đến `§4.7` và FRD của từng module — không lặp lại trong file này.

---

## 6. Business flow, module relationship và impact area

### 6.1 Flow chính cấp project

| Flow ID | Flow name | Actor chính | Module/site liên quan | Trigger | Kết quả chính | Ghi chú impact/regression |
|---|---|---|---|---|---|---|
| FLOW-001 | LP Bot lifecycle (retail thông thường) | `ACT-01` End User | PTL-05 POOL → Router/LPBot on-chain → OPERATOR | User bấm Start Bot trên PTL-05. | LP Bot được tạo on-chain; OPERATOR ghi nhận; user nhận earning sau khi trừ operating fee và PF. | Regression khi đổi ABI Router/LPBot hoặc đổi fee model. Liên quan `FM-PL-01`, `FM-PL-02`. |
| FLOW-002 | WL Bot lifecycle (đường đi MLM) | `ACT-03` WL End User | PTL-01 MOBILE → Helix WL backend → BNZA OPERATOR → Router/LPBot | User bấm Start Bot trên PTL-01; Helix forward sang BNZA. | Net của bot WL chảy đến `wlMaster[tokenId]` (master account per WL). Phần principal vẫn về user. | Regression khi đổi state machine 6 trạng thái của `wlMaster` (`NULL` / `pending_set` / `active` / `failed_set` / `pending_unset` / `needs_repair`). Liên quan `FM-MOB-04`, `FM-ADM-10`. |
| FLOW-003 | Daily MLM reward distribution | `ACT-07` WL Operator Admin | PTL-06 WL-ADMIN → BNZA OPERATOR (Ledger/Position/Bot API) → RewardDistributor on-chain → PTL-01 MOBILE | Cron daily 06:00 UTC khởi chạy job distribution. | State machine chạy từ `BOT_SYNC` đến `COMPLETED`; user nhận reward Push (khi reward ≥ `minPayout`) hoặc giữ ở dạng Claim (dưới ngưỡng). | Toàn bộ `FM-WLA-01` đến `FM-WLA-07` và `FM-MOB-02`/`FM-MOB-03`; reconciliation 6 điểm báo strong alert nếu lệch. |
| FLOW-004 | PF distribution off-chain | `ACT-04` Admin (zen) | PTL-02 ADMIN → OPERATOR D1 (bảng `fee_distributions`) | Admin cấu hình recipient và share; cron daily-collector tổng hợp PF. | PF thực tế chảy đến `pfCollector` EOA; UI chỉ track off-chain ai chia bao nhiêu. | Contract `BnzaSplitter` đã loại khỏi v1 nên test path không có Splitter tx on-chain. `OQ-6` mở. |
| FLOW-005 | Trading perpetuals trên Hyperliquid | `ACT-05` Trader | PTL-03 EX → Hyperliquid trực tiếp | User connect ví → setup agent key (`BR-EX-02`, `BR-EX-03`, `BR-EX-04`) → đặt lệnh. | Order match trên Hyperliquid; PnL hiển thị qua TradingView. | Không đi qua OPERATOR; regression chỉ ở tầng adapter `chartingLibraryAdapter.js`. |
| FLOW-006 | EXBOT lifecycle (Phase A1 dry-run) | `ACT-04` Admin (zen) + `ACT-06` OPERATOR | PTL-04 EXBOT Infra → contract BnzaExVault (do zen quản) + Hyperliquid testnet | Admin trigger start qua API; OPERATOR chạy queue và cron. | Bot tạo subaccount Hyperliquid; logic hedge do zen tính; SOTATEK monitor hạ tầng qua reconcile và circuit breaker (cơ chế tự ngắt khi phát hiện bất thường). | Bị chặn bởi 4 gate của EXBOT Phase 0, mô tả ở `01_intake/intake.md §7` assumption 11. |
| FLOW-007 | WL partner onboarding | `ACT-04` Admin (zen) | PTL-02 ADMIN | Admin tạo WL partner: name, logo (lưu CF R2), `referral_code` 8 ký tự uppercase alphanumeric unique, deposit tier (1k/5k/10k USD), main wallet, languages. | Tạo record `wl_partners` và `wl_code`; cấu hình members lifecycle, master wallet rotation, suspend/resume. | Ranh giới: BNZA-ADMIN tạo partner, daily ops chạy ở PTL-06 (`BR-ADM-008`). |
| FLOW-008 | Bot plan_specs version management (Step 8) | `ACT-04` Admin (zen) | PTL-02 ADMIN ↔ PTL-05 POOL ↔ OPERATOR | Admin publish version mới; POOL refresh từ OPERATOR API; bot tạo mới được snapshot vào version. | `plan_specs` immutable; BotCard hiện cảnh báo outdated khi `currentVersion ≠ bot_configs.plan_specs_version`. | Yêu cầu deploy đồng thời POOL, OPERATOR và OPS. |

### 6.2 Quan hệ giữa module / data / integration

| Area A | Liên quan đến Area B | Kiểu liên quan | Ảnh hưởng QC |
|---|---|---|---|
| WL Mobile (PTL-01) | WL Admin Backend (PTL-06) | Data dependency (read-only) + Integration | Mọi dữ liệu hiển thị mobile đến từ `/api/mobile/*` (SIWE/JWT). Mock hay live ảnh hưởng cách viết test. |
| WL Mobile (PTL-01) | BNZA OPERATOR (PTL-04) | Integration (bot start/stop) | Helix server gọi BNZA `/api/bot-configs/atomic-start` và `:id/stop` qua HMAC-SHA256 (đã finalize ở v1.1 §4.4). Anti-spoofing dựa trên `tx_hash` và NPM `ownerOf`. |
| WL Admin Backend | BNZA OPERATOR | Integration — 3 stream HMAC-SHA256 PULL: Ledger API, Position API, Bot Operations API | Reward computation phụ thuộc 3 stream — test phải cover failure mode (HMAC sai, nonce replay). |
| BNZA-ADMIN (PTL-02) | OPERATOR | Permission, Workflow + Integration | Toàn bộ feature chuyển từ mock sang real đi qua OPERATOR; thay đổi endpoint sẽ gây regression nhiều feature. ADMIN còn là control plane cho state machine `wl_activation_status`. |
| BNZA-ADMIN → OPERATOR (WL bot lifecycle) | Router + Relayer | Integration on-chain | Hàm `setBotWlMaster` và `unsetBotWlMaster` được trigger qua OPERATOR Relayer — regression khi đổi Router. |
| EXBOT Infra (PTL-04) | OPERATOR Queue v2 | Workflow (cùng codebase) | EXBOT phải reuse pattern (`RelayerLockDO`, tách producer và consumer). Test integration không được duplicate logic. |
| EXBOT Infra | Hyperliquid (testnet → mainnet) | Integration external | Phase A1 dry-run trước, A2 live 1k USD bằng fund của zen, A3 closed beta 5 đến 10 WL user. |
| BNZA-POOL Step 8 | BNZA-ADMIN + OPERATOR | Workflow + Reporting | Phải deploy đồng thời 3 hệ; cập nhật CORS cho `ops.bnza.io`. |
| BNZA-EX (PTL-03) | Hyperliquid trực tiếp | Integration external | Tách biệt — regression không lan đến module khác. |
| Router v2.2.2-fix-2 + LPBot v1.2 | Tất cả module dùng bot on-chain | Integration on-chain | Address mới: trên OP là `0xe4E8…16B8D`, trên Base là `0xc70c…f8f2130`; ABI có breaking change (`closeForUser` 7 tham số, `startBot` 11 field, thêm cờ `convertToUsdc`). Mọi integration test phải dùng version mới. |
| Reown AppKit | MOBILE + ADMIN + POOL | Shared infra | Wallet connect; lỗi ở 1 chỗ ảnh hưởng 3 module. |
| `wl_code` ↔ `wl_members` ↔ `wl_master_wallets` | BNZA-ADMIN D1 ↔ WL-ADMIN tenant config | Data dependency | `BR-WLA-022`: `wl_code` trong WL-ADMIN phải khớp record ở BNZA-ADMIN. Test cross-system consistency. |

---

## 7. Rule chung, data/state và integration cần nhớ

### 7.1 Rule chung áp dụng nhiều function

| Rule | Áp dụng cho | Ảnh hưởng đến review/spec/scenario/test case |
|---|---|---|
| Header `X-Wallet-Address` là layer auth chính cho POOL và BNZA-ADMIN khi gọi OPERATOR. (Mã tham chiếu: `02_backbone/backbone.md §8.1`.) | PTL-02, PTL-05 → PTL-04 | Test: thiếu header → reject; mọi endpoint cần covert. |
| BNZA-ADMIN có thêm layer 2 là Cloudflare Access (`zen@bnza.io`) cộng RBAC 3 role (`super_admin`, `admin`, `viewer`). | PTL-02 | Test: truy cập ngoài Cloudflare Access → 403; thiếu role → 403. |
| WL Admin System dùng SSO qua Cloudflare Access kèm 2FA TOTP bắt buộc; role gồm Super, Operator, Read-only. | PTL-06 | Test: thiếu 2FA → block; permission per action theo `02_backbone/backbone.md §4.7`. |
| WL Mobile dùng SIWE để sign-in rồi đổi sang JWT thời hạn 24 giờ; tenant được server giải dựa trên subdomain và signature domain. (Mã tham chiếu: `BR-MOB-001`, `BR-MOB-002`, `BR-MOB-003`.) | PTL-01 | Test: hết JWT → silent re-sign (không hiện banner); frontend không được override tenant. |
| Đường WL post-record (`/api/bot-configs/atomic-start`, `:id/stop`) dùng HMAC-SHA256 server-to-server (Helix gọi BNZA), starter wallet truyền explicit; anti-spoofing bằng `tx_hash`, kiểm `ownerOf` NPM, decode event. | OPERATOR API (đường WL) | Test: HMAC sai hoặc nonce replay → reject; `ownerOf` không khớp → reject. |
| Chain support cấp project — Base (8453) và OP (10) cho LP/MLM; Arbitrum (42161) chỉ cho EX. (Mã tham chiếu: `BR-MOB-006`, `BR-MOB-009`, `BR-PL-01`, `BR-EX-01`.) | MOBILE, POOL, ADMIN, EX | Test: bot ops chỉ chạy trên Base/OP; EX chỉ trên Arbitrum; UI phải nhắc switch chain khi sai. |
| Fee model — 0.5% swap + 0.5% operating fee + 30% PF (Router v2.2.2). PF chảy về `pfCollector` EOA (1 account duy nhất). WL split 70/30 thực hiện off-chain ở Layer B do BNZA tính. (Mã tham chiếu: `02_backbone/backbone.md §8.2`.) | All module dùng fee | Test: khi `convert_to_usdc=1` → PF ratio 0.2970075; khi `=0` → 0.2985. UI hiển thị USDC. |
| Mobile data isolation — không bao giờ đọc trực tiếp LP NFT; mọi số liệu hiển thị đến từ Admin System API (post-allocation). (Mã tham chiếu: `BR-MOB-004`, `02_backbone/backbone.md §8.8.8`.) | PTL-01 | Test: không có request RPC LP từ mobile; UI không hiện raw uncollected fees. |
| WL bot constraint — cờ `autoCompound=false` và `convertToUsdc=true` được Router enforce on-chain. (Mã tham chiếu: `BR-MOB-005`.) | PTL-01 + Router | Test: bot WL bắt buộc gửi USDC; mọi flow phải tôn trọng. |
| Cơ chế Push vs Claim — Push tự động khi reward ≥ `minPayout` (gas do WL trả); Claim user manual cho phần fraction dưới ngưỡng (gas do user trả). Khi distributor pause: Claim disable, UI hiện message `E-MOB-007` "Receiving is currently paused". (Mã tham chiếu: `BR-MOB-007`, `BR-MOB-008`.) | PTL-01 + PTL-06 | Test: dưới ngưỡng → tích vào claimable; khi pause → claim UI disable. |
| WL partner constraint — `referral_code` unique 8 ký tự uppercase alphanumeric; `wl_code` immutable sau khi set; chỉ `super_admin` được create/update/disable. (Mã tham chiếu: `BR-ADM-001`, `BR-ADM-002`, `BR-ADM-006`, `BR-ADM-007`.) | PTL-02 | Test: duplicate code → 409 với message `E-ADM-001`; non-super-admin → 403. |
| WL member lifecycle — một ví chỉ ở trạng thái `active` hoặc `leaving` tại đúng 1 WL trong cùng một thời điểm; leave theo two-phase `initiate-leave` → `confirm-leave`; rejoin tăng `membership_epoch`. (Mã tham chiếu: `BR-ADM-009`, `BR-ADM-010`, `BR-ADM-011`, `BR-ADM-012`.) | PTL-02 + OPERATOR | Test: đang ở trạng thái `leaving` thì bot start mới phải bị reject; khi rejoin, epoch tăng và phải xuất hiện trong response Ledger API gửi cho Helix. |
| WL master wallet — 1 master per WL per chain; rotation theo two-phase; suspend (`wl_codes.status='suspended'`) dừng toàn bộ delivery, cron OPERATOR sẽ chuyển bot sang `pending_unset`. (Mã tham chiếu: `BR-ADM-013`, `BR-ADM-014`.) | PTL-02 + OPERATOR | Test: rotation phải dừng delivery; suspend → toàn bộ daily và rebalance dừng. |
| Cấu hình `fee_distributions` — chính xác 1 row có `is_remainder=true`; tổng share của non-remainder phải nhỏ hơn 1.0; tối đa 10 entries; chỉ off-chain. (Mã tham chiếu: `BR-ADM-015` đến `BR-ADM-019`.) | PTL-02 | Test: vi phạm bất kỳ điều kiện nào → reject kèm audit log. |
| WL Bot Lifecycle force-normalize — two-phase: OPERATOR phải fire `unsetBotWlMaster` on-chain và confirm `wlMaster[tokenId]==0` trước khi set DB `wl_code=NULL`. Nếu `failed_set` stuck 48 giờ → auto force-normalize. (Mã tham chiếu: `BR-ADM-031`, `BR-ADM-032`, `BR-ADM-033`.) | PTL-02 + OPERATOR + Router | Test: chỉ set DB không đủ; phải verify on-chain trước. |
| Trên POOL, cờ `auto_compound` cố định ở 0 và `convert_to_usdc` immutable sau khi bot start. (Mã tham chiếu: `BR-PL-18`, `BR-PL-19`.) | PTL-05 | Test: cố edit sau start → reject. |
| POOL stop tolerance — `already_stopped` trả từ API được coi là success; OPERATOR fail sau khi on-chain đã success vẫn coi là success. (Mã tham chiếu: `BR-PL-09`, `BR-PL-14`.) | PTL-05 | Test: chuỗi nghiệp vụ tiếp tục đi đúng dù gặp các trường hợp trên. |
| Plan specs — `plan_specs` immutable, version mới tạo row mới; cache localStorage TTL 5 phút; BotCard hiện cảnh báo outdated khi version lệch. (Mã tham chiếu: `BR-PL-17`.) | PTL-05 + PTL-02 + OPERATOR | Test: cố edit version cũ → reject; bot tạo mới phải snapshot version đang current. |
| EX agent key — private key của ví agent lưu trong browser storage và phải khớp với ví user connect; mọi action Hyperliquid ký bằng agent key (không pop-up MetaMask). (Mã tham chiếu: `BR-EX-02`, `BR-EX-04`.) | PTL-03 | Test: agent key mismatch → reject. |
| i18n — POOL hỗ trợ 5 ngôn ngữ (en/ja/zh/ko/vi). MOBILE tối thiểu ja + en cộng `supported_languages` per tenant. EX hỗ trợ 8 ngôn ngữ (ja/en/ko/zh/vi…). | All frontend | Test: label gốc giữ nguyên (theo `qc-writting-rules.md §2A3`); chỉ chú thích bản dịch. |
| Message catalog — không viết text inline trong screen; phải reference `E-*` từ `message-list.md`. | All frontend | Test: verify đúng `E-ID` hiển thị theo trigger. |

### 7.2 Data object / state quan trọng cấp project

| Object / entity | Mô tả | State / lifecycle chính | Ghi chú QC |
|---|---|---|---|
| `wl_partners` (BNZA-ADMIN D1) | Hồ sơ WL partner gồm name, logo, `referral_code`, `wl_code`, deposit tier, main wallet, languages, status. | `active` / `disabled` / `suspended`. | `BR-ADM-001` đến `BR-ADM-008`. |
| `wl_members` (BNZA-ADMIN D1) | Mapping wallet ↔ membership WL: mỗi WL user là 1 row, có `membership_epoch`. | `active` → `leaving` → `left` → (rejoin) `active` với epoch tăng. | `BR-ADM-009` đến `BR-ADM-012`. |
| `wl_master_wallets` (BNZA-ADMIN D1) | Master account nhận net per WL per chain. | Rotation theo two-phase: unset old → set new on-chain. | `BR-ADM-013`. |
| `wl_activation_status` (OPERATOR) | State machine WL bot activation gồm 6 trạng thái. | `NULL` / `pending_set` / `active` / `failed_set` / `pending_unset` / `needs_repair`. Auto force-normalize sau 48 giờ ở `failed_set`. | `BR-ADM-031` đến `BR-ADM-033`; UI hiển thị ở `FM-ADM-10`. |
| `fee_distributions` (BNZA-ADMIN D1) | Cấu hình recipient PF off-chain. | CRUD; chính xác 1 row `is_remainder=true`; tổng share non-remainder phải nhỏ hơn 1.0; tối đa 10 entries. | `BR-ADM-015` đến `BR-ADM-020`. |
| `tenants` (WL-ADMIN D1) | Cấu hình tenant per WL operator: branding, chain, ví, `rank_table`, `title_table`, `referral_levels`, `reward_settings`, `reown_project_id`. | `active` / `suspended`. | Schema chi tiết trong `02_backbone/backbone.md §8.8.6`. |
| Distribution Job (WL-ADMIN D1) | Job daily tính và payout MLM reward. | `PENDING` → `BOT_SYNC` → `LEDGER_FETCH` → `PENDING_SNAPSHOT` → `SNAPSHOT` → `UPLINE` → `COMPUTED` → `ENQUEUED` → `ONCHAIN` → `VALIDATED` → `COMPLETED`; nhánh lỗi `BLOCKED` / `ABANDONED` / `paused_waiting`. | `02_backbone/backbone.md §8.8.7`. |
| RewardDistributor on-chain (Base + OP) | Smart contract chia USDC reward (Push) và cho phép user claim (Claim). | `unpaused` / `paused` (PAUSER hot wallet — Unpause qua multisig). | `BR-MOB-008`, `E-MOB-007`. |
| `bot_configs` + `bot_positions` (OPERATOR D1) | Cấu hình bot retail và bot WL. | Lifecycle start/stop/rebalance; `convert_to_usdc` và `auto_compound` immutable sau start. | `BR-PL-18`, `BR-PL-19`. |
| `plan_specs` + `plan_specs_history` (OPERATOR D1) | Các phiên bản plan_specs. | Immutable; version mới là row mới; có `system_config.plan_specs_current_version`. | `BR-PL-17` + Step 8. |
| EXBOT D1 (9 bảng) | `hl_agent_keys`, `subaccount_mappings`, `lp_positions`, `hedge_positions`, `funding_ledger`, `rebalance_attempts`, `circuit_breakers`, `stop_triggers`, `reconcile_log`. | Migration mới sẽ được tạo khi zen cung cấp specs (`Q-001`). | `hl_agent_keys` cần envelope encryption — mã hoá theo lớp, key cấp ngoài bảo vệ key dữ liệu (`FM-XB-12`). |

### 7.3 Integration / API / job / notification quan trọng

| Item | Loại | Module liên quan | Ghi chú QC / risk |
|---|---|---|---|
| BNZA Ledger API (`/api/wl/ledger`) | API — HMAC-SHA256 + nonce, PULL | OPERATOR ↔ WL-ADMIN | Stream 1 — net per user per chain. HMAC sai hoặc replay nonce phải bị reject. |
| BNZA Position API (`/api/wl/portfolio`) | API — HMAC-SHA256 + nonce, PULL | OPERATOR ↔ WL-ADMIN | Stream 2 — AUM phục vụ rank và Cap. |
| BNZA Bot Operations API (`/internal/bot/sync`) | API internal | OPERATOR ↔ WL-ADMIN | Stream 3 — sync `bot_positions_mirror` cho phase `BOT_SYNC`. |
| BNZA OPERATOR `/api/bot-configs/atomic-start`, `:id/stop` (đường WL) | API — HMAC-SHA256 server-to-server | Helix WL backend → OPERATOR | Anti-spoofing dùng `tx_hash`, kiểm `ownerOf` NPM, decode event `BotStarted`/`ZapMintFor` (v1.1 §4.4). |
| RewardDistributor (Base + OP) | Smart contract on-chain | WL-ADMIN ↔ User | Push + Claim hybrid; hàm `addRewards` dùng `clientNonce` để idempotency. Pause/Unpause qua multisig (trừ PAUSER hot wallet — pause khẩn). |
| Router v2.2.2-fix-2 (Base + OP) | Smart contract on-chain | POOL + MOBILE + ADMIN + đường WL Bot | Address mới: trên OP là `0xe4E873DCef553dAb821B03a3caC36B84C5f16B8D`, trên Base là `0xc70cDE10aE7b7630FBF0778D23A04a84B8f82130`. `wlMaster[tokenId]` enforce net recipient. |
| LPBot v1.2 (Base + OP) | Smart contract on-chain | POOL + MOBILE | Address mới: trên OP là `0xeFA6036307bb4A781bdB27e4Cbf314c9386F9572`, trên Base là `0xAA42Bb3408Af361013352998FB6A046A790DA814`. Struct `startBot` 11 field. |
| OPERATOR Queue v2 (3 queue hiện hữu) | Cloudflare Queues | OPERATOR + EXBOT Infra | Gồm `bnza-daily-collect-queue`, `bnza-bot-check-queue`, `bnza-rule-check-queue`. Max batch 100, timeout 30 giây, concurrency 1, retries 3. |
| 6 queue EXBOT mới | Cloudflare Queues | EXBOT Infra | bot-scan, light-check, hedge-sync, reconcile, deep-audit, stop-audit. Đang chờ `FM-XB-02`. |
| Cron daily distribution (UTC chưa chốt giờ) | Cron (WL-ADMIN) | WL-ADMIN | Khởi chạy state machine từ `BOT_SYNC` đến `COMPLETED`. |
| Cron daily reconciliation (UTC 06:00) | Cron (WL-ADMIN) | WL-ADMIN | Reconciliation 6 điểm; strong alert khi có delta. |
| Cron daily PF collector | Cron (OPERATOR) | OPERATOR + ADMIN | Tổng hợp PF; cơ chế WL split 70/30 cho remittance daily chưa rõ (`Q-002`). |
| Hàm on-chain `setBotWlMaster` / `unsetBotWlMaster` | Operator-only function trên Router | ADMIN → OPERATOR → Router | Trigger từ `FM-ADM-10` (retry-set và force-normalize). Force-normalize phải confirm on-chain `wlMaster[tokenId]==0` trước khi set DB `wl_code=NULL`. |
| Reown AppKit (wallet connect + SIWE) | SDK | MOBILE + ADMIN + POOL | Per-tenant `reown_project_id` (MOBILE). Tech debt `BR-EX-07`: EX dùng sai metadata URL — fix priority P2. |
| Hyperliquid API | External | EX + EXBOT | EX dùng `@nktkas/hyperliquid 0.32.1` trực tiếp. EXBOT chạy testnet trước rồi mainnet từ Phase A2. Rate limit 1200 req/phút. |
| Cloudflare R2 | Storage | ADMIN | Upload logo WL partner (`BR-ADM-005`). |
| Cloudflare Secrets Store | Secret management | EXBOT | Lưu master encryption key bảo vệ HL agent key (`FM-XB-12`). |
| Notifications polling 30 giây | Polling (UI) | POOL | `BR-PL-20`. |

---

## 8. Platform, environment, device và NFR/ràng buộc

### 8.1 Platform và environment tổng quan

| Hạng mục | Nội dung | Ghi chú QC |
|---|---|---|
| Platform type | Hỗn hợp: PWA mobile-hybrid (MOBILE), web-responsive desktop-first (ADMIN, POOL, EX), API-only backend (EXBOT Infra). | Test plan phải tách viewport mobile khỏi viewport desktop. |
| Browser / OS / device cần quan tâm | MOBILE: iOS Safari và Android Chrome (cần PWA, manifest + service worker, layout `100dvh` + safe-area). ADMIN: desktop modern browser (Chrome/Edge/Firefox), tối thiểu width 1280px (cho WL-ADMIN). POOL/EX: desktop modern browser. | Test: 60 fps trên MOBILE (NFR); PWA install path; offline shell (`FM-MOB-10`). |
| Test environment | DEV / QA (STG) / UAT / PROD theo template — **chưa được điền URL hoặc DB thật trong `project-config.md`**. URL production đã biết: `pool.bnza.io`, `ops.bnza.io`, `ex.bnza.io`, `api.bnza.io`. URL WL `wl.bnza.io` và `wl-admin.bnza.io` đều TBD. | Tester cần QC Lead hoặc DevOps điền giá trị thật trước khi execute (`Q-012`). Staging environment chưa có (`Q-003`). |
| Integration mode | Mock + sandbox + real service xen kẽ. Hyperliquid testnet cho EXBOT Phase A1; mainnet (Base/OP) cho POOL/MOBILE/ADMIN sau khi gate đạt. | Test: tách rõ mock path khỏi live path; với Helix backend, cần xác nhận đang dùng stub hay endpoint thật. |
| Test data / account tổng quan | Tài khoản template (Admin / Standard User / Vendor / Test Card) chưa điền giá trị thật. Account thật cho QA hoặc UAT cần được cấp riêng (wallet test có sẵn USDC trên Base/OP testnet hoặc forked mainnet). | Cần test wallet có USDC kèm ETH gas trên Base và OP để cover bot start. |

### 8.2 NFR, security, compliance, legal, audit

| Loại ràng buộc | Nội dung đã biết | Ảnh hưởng QC |
|---|---|---|
| Performance | Bot-check latency target dưới 100 ms; API latency p95 dưới 100 ms (`02_backbone/backbone.md §8.3`); MOBILE phải đạt 60 fps (`01_intake/intake.md §6`). | Performance test target — chờ Daniel report (`Q-009`) trước khi cố định. |
| Availability | SLA uptime 99.9% (theo roadmap M3). | Cần SLA monitoring + downtime tracking. |
| Scale | Mục tiêu 10.000 bot ngay từ ngày đầu (Queue v2). **Đang dưới review** — giới hạn concurrent worker của CF. | Scale test target chưa chốt; chờ Daniel report. |
| Security | Audit OWASP Top 10 (roadmap M3). Envelope encryption cho HL agent key (`FM-XB-12`). HMAC-SHA256 cho 3 stream và WL post-record. Cloudflare Access + 2FA TOTP cho admin. | Test: secret không lộ; HMAC nonce replay; rate limit báo message `E-MOB-003` "Too many attempts." |
| Privacy / Legal | Quy định pháp lý quan trọng: principal trả thẳng cho user, không qua WL pool — không bị xem là money handling của WL (`02_backbone/backbone.md §8.8.1`). | Test: khi stop bot WL → principal đi đến user, net đi đến `wlMaster`. |
| Audit | Mọi write ở WL-ADMIN cần reason note và Slack audit mirror (`02_backbone/backbone.md §5.0`). BNZA-ADMIN cần audit log cho mỗi CRUD `fee_distributions` (`BR-ADM-019`). | Test: audit log entry chứa actor, action, before/after, timestamp. |
| Accessibility | Chưa có cam kết WCAG cụ thể (mức AA hay AAA). Mobile theo dark theme + responsive PWA. | QC Lead nên xác nhận target WCAG nếu cần (chưa có trong source). |
| Logging | LP Bot path có notification poll 30 giây (`BR-PL-20`); EXBOT có bảng `reconcile_log`; reconciliation 6 điểm chạy daily. | Test: log phải đầy đủ trường để trace incident. |
| i18n / Localization | POOL: 5 ngôn ngữ (en/ja/zh/ko/vi). MOBILE: tối thiểu ja + en + tenant `supported_languages`. EX: 8 ngôn ngữ (ja/en/ko/zh/vi…). | Test: label giữ nguyên gốc, chú thích bản dịch (theo `qc-writting-rules.md §2A3`). |
| Testing standards (theo `02_backbone/backbone.md §8.6`) | MOBILE/ADMIN/POOL: unit + E2E critical flow đạt 80% trở lên. EX: unit 80% trở lên. EXBOT Infra: integration test queue và HL API. | QC plan phải tách layer test theo bảng này. |
| Build / Deploy | pnpm 10.11 + Turbo 2.5.4 monorepo; CF Workers (OPERATOR), Vercel (POOL — tách repo), CF Pages (ADMIN/EX/MOBILE/WL-ADMIN). | Deploy sequencing có ràng buộc (Step 8 cần POOL, OPERATOR và OPS deploy đồng thời). |

---

## 9. Đánh giá mức độ đủ context cấp project

| Nhóm context | Trạng thái | Độ tin cậy | Ảnh hưởng nếu thiếu/sai | Cần QC Lead bổ sung gì |
|---|---|---:|---|---|
| Project goal & scope | Ready | High | Đã có scope SOTATEK lock, 2 line delivery rõ ràng. **Line 1 done, Line 2 là phạm vi QC duy nhất.** | — |
| System/site/module overview | Ready | High | Portal matrix 6 portal cộng actor matrix 7 actor đầy đủ. | — |
| Feature/use case inventory | Ready | High | 42 mã `FM-*` đều có ID. **Line 2 scope: FM-XB-01→FM-XB-13.** | — |
| Users/roles/permission overview | Ready | High | Permission matrix cấp portal đầy đủ. Line 2 chủ yếu ACT-06 (OPERATOR system) + ACT-04 (Admin config). | — |
| Business flows & module relationship | Ready | High | Dependency EXBOT → OPERATOR Queue v2 → Hyperliquid đã rõ. | — |
| Common rules/data/state/integration | Partial | Medium | EXBOT cần zen interface specs (D1 schema, Queue topology, API contracts) — `Q-001` vẫn Open. | Đợi zen chốt `Q-001`. |
| Platform/environment/device/NFR | Partial | Medium | CF Workers deployment rõ; NFR scale 10k bot đang review; `project-config.md` còn placeholder. | Điền `project-config.md` (`Q-012`); chờ `Q-009`. |
| Document status tracking | Partial | Medium | Line 1 features đã tracked. Line 2 (EXBOT) chưa có dashboard row. | Chạy `qc-site-map` rồi `qc-dashboard-sync` để cập nhật. |

**Kết luận:**
**Tạm đủ cho Line 2 (EXBOT Infra) ở mức context tổng quan.** Line 1 đã hoàn thành và chỉ còn là dependency context — Agent không cần test thêm. Với Line 2, context cấp project đã đủ để hiểu EXBOT architecture, dependency với OPERATOR, và gate conditions. **Chưa đủ** để thiết kế test chi tiết cho EXBOT vì: (1) `Q-001` — zen chưa cung cấp đầy đủ EXBOT interface specs (D1 schema, Queue topology, API contracts); (2) 4 gate conditions Phase 0 chưa đạt; (3) `project-config.md` chưa điền môi trường thật.

---

## 10. Open questions và việc cần QC Lead xác nhận

| ID | Câu hỏi / thông tin cần xác nhận | Vì sao quan trọng | Ảnh hưởng nếu chưa rõ | Priority | Owner | Status |
|---|---|---|---|---|---|---|
| Q-001 | Khi nào zen cung cấp đầy đủ EXBOT interface specs (schema D1, topology queue, contract API)? | Là blocker chính của Line 2 EXBOT (`FM-XB-01` đến `FM-XB-06`). | Không thiết kế được scenario hoặc test case cho family `FM-XB-*`; trễ gate Phase A1. (Mã tham chiếu: `OQ-2` trong `01_intake/intake.md §10`.) | High | zen (BA escalate) | Open |
| Q-002 | Cơ chế daily remittance WL 70/30 cho `FM-ADM-02` PF Distribution là gì? | PF Distribution là feature P0 cho WL launch; cron daily-collector đã tồn tại nhưng phần WL-specific 70/30 chưa rõ. | Không xác định được expected result cho remittance flow, ảnh hưởng test case `FM-ADM-02`. (Mã tham chiếu: `OQ-6` trong `01_intake/intake.md §10`.) | High | BA / Tech Lead | Open |
| Q-003 | Staging environment (URL, DB, scope dữ liệu) sẽ được dựng ở đâu, lúc nào? | Quyết định milestone M3 (Staging) và toàn bộ kế hoạch UAT/E2E. | Không lên được test environment plan; `project-config.md` vẫn để placeholder. (Mã tham chiếu: `OQ-8` trong `01_intake/intake.md §10`.) | Medium | DevOps / PM | Open |
| Q-004 | Same-rank bonus eligibility — dùng "cùng title" hay "cùng rank"? Chia đều hay weighted? | Logic chia thưởng MLM cho `FM-WLA-02` Reward Computation Engine. | Test case reward engine không có expected result chuẩn. (Mã tham chiếu: open question trong `01_intake/intake.md §3 Module 1A`.) | High | WL operator (BA escalate) | Open |
| Q-005 | Leader airdrop token (V4+) — công thức tính và điều kiện ra sao (`leader_bonus_json`)? | Quyết định luồng airdrop `bonus_airdrops` cho `FM-WLA-02` và `FM-MOB-02`. | Không thể test display leader perk và logic phân phối. (Mã tham chiếu: open question trong `01_intake/intake.md §3 Module 1A`.) | High | WL operator (BA escalate) | Open |
| Q-006 | Cap policy — forfeit hay carry-over? Có bật ngay từ launch hay không? | Ảnh hưởng `FM-WLA-02` (Cap double-check trước phase `ONCHAIN`) và `FM-MOB-02` (Cap status display). | Test case Cap reach và overflow không có expected result xác định. (Mã tham chiếu: open question trong `01_intake/intake.md §3 Module 1A`.) | High | WL operator (BA escalate) | Open |
| Q-007 | Xử lý trường hợp `AUM=0` hoặc dưới rank thấp nhất — không trả fee reward hay vẫn giữ ở rank starter? | Ảnh hưởng edge case rank assignment cho `FM-WLA-02`. | Test case edge value (`AUM=0`, `AUM < starter min`) không có expected result. (Mã tham chiếu: open question trong `01_intake/intake.md §3 Module 1A`.) | Medium | WL operator (BA escalate) | Open |
| Q-008 | Cross-chain claimable UX — claim theo từng chain riêng hay gộp về 1 chain đại diện? | Ảnh hưởng `FM-MOB-03` Claim USDC (Base + OP) và `FM-WLA-03`. | Test case multi-chain claim không có flow chuẩn. (Mã tham chiếu: open question trong `01_intake/intake.md §3 Module 1A`.) | Medium | WL operator (BA escalate) | Open |
| Q-009 | Khi nào báo cáo CF infrastructure feasibility cho mục tiêu 10.000 bot (Daniel) hoàn thành? | Ảnh hưởng target NFR scale và quyết định kiến trúc EXBOT. | Không cố định được performance hoặc scale test target. (Mã tham chiếu: `01_intake/plan.md` — Pending Reports.) | Medium | Daniel | Open |
| Q-010 | Khi nào kế hoạch mainnet data migration (khoảng 8 user, 250k USD fund) — Andrew hoàn thành? | Ảnh hưởng QA gate cho deploy sequencing trên monorepo. | Không lên được regression plan cho production cutover. (Mã tham chiếu: `01_intake/plan.md` — Pending Reports.) | Medium | Andrew | Open |
| Q-011 | `FM-ADM-07` TOKEN Management — có cần QC pass ở phase này, hay giữ mock và bỏ qua test? | Quyết định scope test BNZA-ADMIN. | Nếu không xác nhận, có thể tốn effort QA cho feature ngoài scope. (Mã tham chiếu: `02_backbone/feature-map.md §3.2` — Tier T3.) | Low | QC Lead / zen | Open |
| Q-012 | `docs/qc-lead/project-config.md` (URL DEV/QA/UAT/PROD, DB, account, link Jira/Confluence/Figma/Git/CI) khi nào sẽ được điền? | QC Lead cần để chuẩn bị môi trường thực thi. | Tester không vào được môi trường thật để execute. (Mã tham chiếu: `docs/qc-lead/project-config.md`.) | High | QC Lead / DevOps | Open |
| Q-013 | Target tuân thủ WCAG (mức AA hay AAA) cho các frontend (MOBILE/ADMIN/POOL/EX/WL-ADMIN) là gì? | Mức tuân thủ chuẩn tiếp cận web (WCAG — Web Content Accessibility Guidelines) chưa được nêu trong intake hoặc backbone. | Không thiết kế được accessibility test target (tương phản, ngôn ngữ, điều hướng, ARIA). | Low | BA / QC Lead | Open |
| Q-014 | Phạm vi build và test PTL-06 WL-ADMIN cho SOTATEK — `01_intake/intake.md §9 Out of Scope` viết "MLM reward computation, referral tree management, RewardDistributor payout (Layer B) — Helix/WL build, not SOTATEK scope", trong khi `02_backbone/feature-map.md §3.0` vẫn liệt kê đầy đủ `FM-WLA-01` đến `FM-WLA-07` trong feature map dự án. SOTATEK có cần QC pass toàn bộ Layer B hay chỉ kiểm tra interface contract giữa BNZA và Helix? | Quyết định toàn bộ effort QC cho PTL-06 và việc có chạy `qc-site-map` cho folder `03_modules/admin/wl-admin/` hay không. | Nếu Helix build mà SOTATEK vẫn QC, lãng phí effort; nếu Helix build mà QC bỏ qua, có thể thiếu test integration. (Mã tham chiếu: `01_intake/intake.md §9` so với `02_backbone/feature-map.md §3.0`.) | High | QC Lead / BA / zen | Open |

---

## Phụ lục A. Nguyên tắc giữ file gọn

- Chỉ ghi thông tin cấp project hoặc thông tin dùng chung cho nhiều Agent/skill.
- Không copy toàn bộ nội dung từ spec, wireframe, API document hoặc use case detail.
- Không ghi test case chi tiết trong file này.
- Không lặp lại danh sách feature dài nếu đã có `feature-map.md` hoặc `qc-dashboard.md`.
- Nếu thông tin đã có ở file khác, chỉ tóm tắt vai trò và dẫn Agent đọc file đó (đặc biệt là `02_backbone/backbone.md` cho rule cross-module, `02_backbone/common-rules.md` cho business rule, `02_backbone/message-list.md` cho message catalog).
- Nếu một thông tin chỉ ảnh hưởng một function cụ thể, đưa vào function-level context/spec review, không đưa vào file này.
