---
source_skill: qc-site-map
handoff_type: site-map-feature-coverage
mode: initialization
generated_at: 2026-06-15T00:00:00+07:00
---

# Site Map Handoff for qc-dashboard-sync

Site map vừa được tạo lần đầu (`docs/qc-lead/qc-site-map.md`) — Bonanzapool BNZA Ecosystem.  
Handoff này chứa thông tin cấp **feature/UC** để `qc-dashboard-sync` tạo dashboard rows (top-down Initialization).  
**Không** ghi đè vào cột `UC review stt`, `Scenario design stt`, `TC design stt`, `Execute stt` khi các cột đó đã có giá trị.

---

## Feature-level site map coverage

| Feature ID | Feature name | Site / Portal | Module | Mapped screen(s) | Folder alias(es) | In scope? | Site map status | Notes |
|---|---|---|---|---|---|---|---|---|
| FM-ADM-01 | WL Partner Onboarding | PTL-02 ADMIN | WL Partners | SCR-ADM-02, SCR-ADM-02a, SCR-ADM-02b, SCR-ADM-02c | | Yes | Partial | Wireframe chưa có. Screen tree Derived từ nav schema. Regression: Member Lifecycle (2-phase leave), Master Wallets (rotation). |
| FM-ADM-02 | PF Distribution | PTL-02 ADMIN | PF Distribution | SCR-ADM-04 | | Yes | Partial | Wireframe chưa có. |
| FM-ADM-03 | IB Management | PTL-02 ADMIN | IB Management | SCR-ADM-05 | | Yes | Partial | Wireframe chưa có. Real D1 data (replace mockIBs). |
| FM-ADM-04 | Bot Type Config | PTL-02 ADMIN | Bot Config | SCR-ADM-06 | | Yes | Partial | Wireframe chưa có. Regression: zen-provided EXBOT params (hedge_ratio, leverage, stop_safety_factor). |
| FM-ADM-05 | Dashboard (Admin) | PTL-02 ADMIN | Dashboard | SCR-ADM-01 | | Yes | Partial | KPI list từ OPERATOR /api/admin/stats. KV cache 5min TTL. |
| FM-ADM-06 | Reports | PTL-02 ADMIN | Reports | SCR-ADM-11 | | Yes | Partial | Date-range query schema cần confirm. |
| FM-ADM-07 | TOKEN Management | PTL-02 ADMIN | TOKEN | SCR-ADM-08 | | Yes | Partial | Mock data only. Low priority (T3). |
| FM-ADM-08 | System Settings | PTL-02 ADMIN | System | SCR-ADM-09 | | Yes | Partial | Regression: global_bot_enabled kill switch (BR-ADM-028). safe_mode requires zen approval (BR-ADM-029). |
| FM-ADM-09 | Relayer Monitor | PTL-02 ADMIN | System | SCR-ADM-10 | | Yes | Partial | Balance threshold alert. Wireframe chưa có. |
| FM-ADM-10 | WL Bot Lifecycle Monitor | PTL-02 ADMIN | WL Partners | SCR-ADM-03 | | Yes | Partial | Regression: force-normalize 2-phase (BR-ADM-031). Auto-normalize >48h (BR-ADM-033). |
| FM-ADM-11 | User Management | PTL-02 ADMIN | Users | SCR-ADM-07 | | Yes | Partial | RBAC-based. Read-only Phase A. |
| FM-EX-01 | TradingView Integration | PTL-03 EX | Trading | SCR-EX-01 | | Yes | Partial | TradingView license cần confirm. chartingLibraryAdapter.js. |
| FM-EX-02 | Chart Data Feed | PTL-03 EX | Trading | SCR-EX-01 | | Yes | Partial | HL WebSocket data feed. |
| FM-EX-03 | Order Placement | PTL-03 EX | Trading | SCR-EX-02, SCR-EX-03, SCR-EX-04 | | Yes | Partial | Regression: agent key ký (no MetaMask popup — BR-EX-04). Builder fee approval required (BR-EX-03). |
| FM-EX-04 | i18n (BNZA-EX) | PTL-03 EX | Trading | SCR-EX-01..04 (shared) | | Yes | Partial | 5 languages. No TypeScript (BR-EX-08). |
| FM-XB-01 | D1 Schema | PTL-04 EXBOT | Backend | — (backend-only) | | Yes | Mapped | 9 tables. No UI. |
| FM-XB-02 | Queue Topology | PTL-04 EXBOT | Backend | QUE-XB-01..10 | | Yes | Mapped | 10 queues confirmed. Regression: user_redeem highest prio SLA 5min. light-check zero HL calls. |
| FM-XB-03 | Durable Objects | PTL-04 EXBOT | Backend | DO-XB-01, DO-XB-02, DO-XB-03 | | Yes | Mapped | Regression: HLRateLimitDO 800wt/min sliding window. UserLockDO lease 90s prevents nonce collision. |
| FM-XB-04 | Cron Jobs | PTL-04 EXBOT | Backend | QUE-XB-05 (deep-audit) | | Yes | Mapped | deep-audit 6h interval. Hourly metrics-rollup. 6h stop-integrity check. |
| FM-XB-05 | HL Adapter | PTL-04 EXBOT | Backend | QUE-XB-03, QUE-XB-04 | | Yes | Mapped | Delta-only. cloid idempotency (NV-5 Q-013). Reconcile. |
| FM-XB-06 | OPERATOR Facade API | PTL-04 EXBOT | Backend | API-XB-01..05 | | Yes | Mapped | 5 endpoints confirmed from SRS. |
| FM-XB-07 | Lifecycle State Machine | PTL-04 EXBOT | Backend | API-XB-01, QUE-XB-01, QUE-XB-02 | | Yes | Mapped | 18 states (FR-EXBOT-003). Regression: all state transitions. NV-1/NV-3 gate for §19.5 stop impl. |
| FM-XB-08 | Close/Redeem Operations | PTL-04 EXBOT | Backend | API-XB-03, QUE-XB-08 | | Yes | Mapped | Regression: LP-first, SLA 5min, idempotency (close_operations ledger). |
| FM-XB-09 | Phase A1 Dry Run | PTL-04 EXBOT | Backend | API-XB-01..05 | | Yes | Mapped | Blocked on Phase 0 Gate (4 conditions). Cannot test HL integration until gate passes. |
| FM-XB-12 | Envelope Encryption | PTL-04 EXBOT | Backend | API-XB-04 | | Yes | Mapped | Regression: no raw key in D1/logs. AES-GCM confirmed. |
| FM-PL-01 | Step 7 Multi-Bot | PTL-05 POOL | AI Bot | SCR-POOL-01, SCR-POOL-02, SCR-POOL-02a, SCR-POOL-02b, SCR-POOL-03, SCR-POOL-04 | | Yes | Partial | Nav schema confirmed. Wireframe chi tiết cần BA. Regression: invested_amount immutable (BR-PL-24). P&L = Evaluation − invested_amount. atomic-start 3 retry (BR-PL-16). |
| FM-PL-02 | Step 8 plan_specs | PTL-05 POOL | OPS (Admin) | SCR-POOL-05 | | Yes | Partial | Simultaneous deploy POOL+OPERATOR+ADMIN. Version immutability. |
| FM-OPW-01 | DB Migrations 0024–0027 | PTL-04 EXBOT (backend) | Backend | — (backend-only) | | Yes | Mapped | DB migrations. No UI. |
| FM-OPW-02 | Ledger API | PTL-04 EXBOT (backend) | Backend | — (API) | | Yes | Mapped | GET /wl/ledger/* HMAC-SHA256 auth. Schema cần full SRS. |
| FM-OPW-03 | Bot API | PTL-04 EXBOT (backend) | Backend | — (API) | | Yes | Mapped | POST /wl/bot/* two-phase commits. |
| FM-OPW-04 | Post-Record Webhook | PTL-04 EXBOT (backend) | Backend | — (API) | | Yes | Mapped | POST to tenant wl_codes.post_record_url. |
| FM-OPW-05 | WlNetSent Scanner | PTL-04 EXBOT (backend) | Backend | — (Cron/Queue) | | Yes | Mapped | Scan WlNetSent events 5min. |
| FM-OPW-06 | Reconcilers | PTL-04 EXBOT (backend) | Backend | — (Cron) | | Yes | Mapped | setBotWlMaster reconciler + wlMaster invariant. |
| FM-OPW-07 | fee_collections Exclusion | PTL-04 EXBOT (backend) | Backend | — (code change) | | Yes | Mapped | 7 OPERATOR files. |
| FM-WLC-01 | WL Contract Upgrades (A–K) | Smart Contract | Blockchain | — (Smart Contract) | | Yes | Mapped | 11 contract changes. Phase 2. Blocked until Phase 1 stable. |
| FM-WLA-01 | WL Admin — Module 1 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. Không tạo test cases. |
| FM-WLA-02 | WL Admin — Module 2 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-WLA-03 | WL Admin — Module 3 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-WLA-04 | WL Admin — Module 4 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-WLA-05 | WL Admin — Module 5 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-WLA-06 | WL Admin — Module 6 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-WLA-07 | WL Admin — Module 7 | PTL-06 WL Admin [OOS] | WL Admin OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-01 | WL Mobile — Module 1 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. Không tạo test cases. |
| FM-MOB-02 | WL Mobile — Module 2 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-03 | WL Mobile — Module 3 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-04 | WL Mobile — Module 4 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-05 | WL Mobile — Module 5 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-06 | WL Mobile — Module 6 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-07 | WL Mobile — Module 7 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-08 | WL Mobile — Module 8 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-09 | WL Mobile — Module 9 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-10 | WL Mobile — Module 10 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |
| FM-MOB-11 | WL Mobile — Module 11 | PTL-01 WL Mobile [OOS] | WL Mobile OOS | [OOS — Helix] | | No | Missing | OOS — Helix scope. |

---

## Feature-level gaps

| Feature ID | Feature name | Gap | Impact to QC | Owner | Priority |
|---|---|---|---|---|---|
| FM-ADM-* (all 11) | BNZA-ADMIN module | Không có SRS/module doc. Chỉ có feature-map.md mô tả ngắn. | Không thể viết scenario chi tiết cho ADMIN trước khi có SRS. | BA | High |
| FM-PL-01/02 | POOL Steps 7-8 | Wireframe chi tiết Step 7-8 chưa có. | BotCard edge cases, Create Bot flow detail cần confirm. | BA | Medium |
| FM-XB-09 | Phase A1 Dry Run | Phase 0 Gate chưa pass. | QC không test HL integration. D1 schema + Queue skeleton only. | zen / SOTATEK | High |
| FM-XB-07 | Lifecycle + Stop §19.5 | NV-1/NV-3 chưa confirm (Q-011). | §19.5 stop impl blocked. Scenario cho stop cases chưa design được. | SOTATEK | High |
| FM-PL-01 + FM-XB-07 | Dual-chain wethIndex | NV-12 chưa confirm (Q-012). Pool address Base+OP + wethIndex chưa xác nhận. | Chain switch test + LP calc test bị block. | zen (BNZA) | High |

---

## Unmapped screens

Không có. Tất cả screens đều map được tới ít nhất 1 Feature ID.

---

## Handoff notes for qc-dashboard-sync

- **In scope = Yes:** 35 features (toàn bộ Sotatek builds).
- **In scope = No:** 18 OOS features (FM-WLA-01..07 + FM-MOB-01..11).
- **EXBOT Phase 0 Gate chưa pass:** FM-XB-09 bị block — đánh dấu rõ trong dashboard.
- **NV-1/NV-3 + NV-12 chưa confirm:** Ảnh hưởng FM-XB-07 + FM-PL-01. Xem Q-011/Q-012 trong project-context-master.md.
- **Không có qc-dashboard.md hiện tại** — đây là Initialization, tạo fresh từ handoff này.
