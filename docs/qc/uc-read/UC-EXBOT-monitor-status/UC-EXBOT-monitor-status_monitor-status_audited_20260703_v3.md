# Báo cáo rà soát mức độ sẵn sàng — UC-EXBOT-monitor-status

**Tiêu đề tài liệu:** UC Readiness Audit Report — UC-EXBOT-monitor-status  
**Ngày tạo:** 2026-07-03  
**Tác giả / Agent:** QC UC Read Agent  
**Phiên bản:** v3

---

## Reference Code Glossary

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| FR-EXBOT-* | Functional Requirement for the ExBot module — numbered requirements defining bot behavior, API contracts, and state machine rules. Canonical source for all implementation decisions. | `srs/spec.md` |
| BR-EXBOT-* | Business Rule for ExBot — absolute invariants that must never be violated in code or documentation (e.g., SAFE_MODE is never terminal, delta-only hedge adjustment, light-check HL weight = 0). | `srs/spec.md` §4 |
| E-EXBOT-* | API-level error code returned by ExBot Worker through Operator Facade — defines HTTP status code and message content for each error case. | `02_backbone/message-list.md` |
| US-EXBOT-* | User Story for ExBot — acceptance criteria in Given/When/Then format from Investor or Operator perspective. | `userstories/us-*.md` |
| UC-EXBOT-* | Use Case for ExBot — describes system behavior at scenario level, including actors, flows, and FR trace. | `usecases/uc-*.md` |
| OQ-EXBOT-* | Open Question for ExBot — unresolved technical or business question affecting implementation or test design. | `srs/spec.md` §9 |
| D1 | Cloudflare D1 — SQLite-compatible database used to store bot state, positions, hedge legs, and runtime state. Two logical databases: `control_db` (global, cross-shard) and `state_db_shard_xx` (per-shard bot state). | `srs/erd.md`, SRS §1 |
| DO | Durable Object — Cloudflare Workers stateful compute unit; used as distributed lock (UserLockDO), rate limiter (HLRateLimitDO), and market data cache (MarketDataDO). | SRS §1, FR-EXBOT-093 |
| MarketDataDO | Durable Object that caches Uniswap V3 pool slot0 data (sqrtPriceX96, currentTick, blockNumber). Used in this UC to compute rangeState without direct RPC calls from the Worker. | `srs/spec.md` FR-EXBOT-093 |
| SIWE | Sign-In With Ethereum — wallet-based authentication mechanism. Relevant to Investor auth flow through POOL UI. | (industry term) |

---

## Feature Brief

UC-EXBOT-monitor-status describes a read-only query flow that allows an authenticated USDC Investor to monitor the current operational state of their running ExBot. The entire flow is backend-only: POOL UI calls `GET /api/exbot/status` on the Operator Facade, which proxies the request to ExBot Worker via Cloudflare service binding with an internal authentication token. ExBot Worker reads from four D1 tables (`bots`, `positions`, `hedge_legs`, `bot_runtime_state`), queries the current tick from `MarketDataDO`, computes two derived values (rangeState and drift%), then returns a consolidated JSON payload. No data mutation occurs in this flow — all writes are zero.

A secondary actor, Admin, may also call this endpoint and bypasses the wallet ownership check. The auth mechanism uses `X-Wallet-Address` header for the Investor or Admin caller, and `X-Exbot-Internal-Auth` header for the Facade-to-Worker internal leg.

From a testing perspective, this UC is significant because the consolidated status response aggregates data from multiple D1 tables plus a Durable Object query, returns lifecycle state labels that drive UI button visibility (pause, close, emergency close), and is the primary observability surface for both Investor and Operator. The correctness of state labels and derived values (drift%, rangeState) determines whether action buttons in POOL UI are enabled or disabled. Eight alternate flows cover the full lifecycle state space from safe_mode through closed, plus infrastructure-level unavailability.

One high-priority open issue remains: the source of `targetShortEth` in the drift% computation is not confirmed — FR-EXBOT-021 defines it as a computed value (`lpEthAmount × hedgeRatio`), but the ERD shows a `target_short_size` column in `bot_runtime_state`. Until the developer confirms whether ExBot Worker reads this column from D1 or recomputes it on the fly, the expected result for drift% test assertions cannot be fully specified.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-monitor-status | View Active ExBot Status | — (no version field in UC file) | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | — | 2026-06-18 | 2026-07-03 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| `usecases/uc-monitor-status.md` | 2026-07-03 | UC (primary input) | Draft; updated 2026-07-03 by /ba-do resolving I-001 through I-013 |
| `userstories/us-002.md` | 2026-06-18 | US linked to this UC | Draft |
| `srs/spec.md` | 2026-06-29 | SRS baseline — source of truth for all FR | Latest version |
| `srs/states.md` | 2026-07-03 | Lifecycle state machine | Latest version — updated 2026-07-03 (pause clarification) |
| `srs/erd.md` | 2026-06-29 | D1 data model | Latest version |
| `srs/flows.md` | 2026-06-29 | Sequence flow diagrams | Latest version |
| `frd.md` | 2026-06-29 | Functional requirements document | Latest version |
| `usecases/index.md` | 2026-06-29 | UC catalog and FR trace index | Checked |
| `02_backbone/message-list.md` | 2026-06-26 | E-EXBOT-* error code registry | Checked for E-EXBOT-021/022/023 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

This endpoint exists so that a USDC Investor can check at any time whether their ExBot is operating correctly, without needing access to an internal dashboard. It also serves as the signal layer for POOL UI to enable or disable state-changing action buttons (pause, close, emergency close) based on the current lifecycle state and margin health of the bot.

Admin actors can query the same endpoint to inspect any bot without ownership restriction, supporting operational monitoring and incident response.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| `GET /api/exbot/status` — primary status query | Operator Facade proxies request to ExBot Worker via CF service binding; Worker reads D1 and MarketDataDO, computes derived values, returns consolidated JSON | UC §3, FR-EXBOT-090 |
| Multi-table D1 read | Reads `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.last_light_check_at`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status` | UC §3 step 3 |
| MarketDataDO query | Fetches `currentTick` from `MarketDataDO` shared cache (no direct RPC from Worker) | UC §3 step 4, FR-EXBOT-093 |
| rangeState computation | Compares `currentTick` with `tickLower`/`tickUpper` using half-open interval (`tickLower <= currentTick < tickUpper`); null if currentTick unavailable | UC §3 step 5 |
| drift% computation | `(\|actualShortEth - targetShortEth\| / targetShortEth) × 100` using BigDecimal | UC §3 step 6, FR-EXBOT-021 |
| JSON response schema | Two-part schema: Implemented fields (immediately available) + Pending implementation fields (null until implemented) | UC §3 step 7 |
| Alternate flows A1–A8 | Covers safe_mode, hedge_stopped_cooldown, lp_closing, closed, lp_rebalancing, error, MarketDataDO unavailable, no bot record | UC §4 |
| Auth: Investor path | `X-Wallet-Address` header; `wallet_address` must match `bot.user_wallet_address`; mismatch → 403 | UC §2 |
| Auth: Admin path | `X-Wallet-Address` header; bypasses ownership check | UC §2 |
| Auth: Facade→Worker | `X-Exbot-Internal-Auth` header (shared secret from env var `EXBOT_INTERNAL_AUTH_TOKEN`) | UC §2 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| POOL UI rendering logic | UI component behavior is POOL module scope; UC covers the API response payload only | Test scenarios for this UC focus on the API response; UI rendering tests are out of scope |
| Margin status update logic | Margin status is computed during hedge-sync preflight and deep-audit (FR-EXBOT-060), not during status read | Test must use pre-seeded D1 data with known margin_status values; real-time margin update is not triggered by this UC |
| Historical status data / audit trail | UC returns current snapshot only; no history query is in scope | N/A |
| Pause/resume mutation | Pause is a separate UC; status endpoint is read-only | N/A |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| USDC Investor | Primary | Initiates status query from POOL UI; views current bot state, LP range, hedge size, margin health, and lifecycle label | Can only query their own bot (`wallet_address` must match `bot.user_wallet_address`); read-only — no mutations | UC §1 Actors |
| Admin | Secondary | Can query any bot's status without ownership check | Bypasses `wallet_address == bot.user_wallet_address` check; read-only | UC §1 Actors, UC §2 Preconditions |
| Operator Facade Worker | System | Receives `GET /api/exbot/status` from POOL UI; validates `X-Wallet-Address` header (401/403 on failure); proxies to ExBot Worker with `X-Exbot-Internal-Auth` | Does not own ExBot business logic; passthrough only | UC §1 Actors, FR-EXBOT-090 |
| ExBot Worker | System | Reads D1 + MarketDataDO; computes rangeState and drift%; composes and returns JSON status response | Internet-inaccessible; only reachable via Facade CF service binding | UC §1 Actors, FR-EXBOT-090 |
| D1 (state_db_shard) | System | Source of bots, positions, hedge_legs, bot_runtime_state records | Read-only in this UC | UC §3, ERD |
| MarketDataDO | System | Shared cache for Uniswap V3 pool slot0 currentTick | Read-only; if unavailable or stale, `current_tick: null` returned without blocking | UC §3 step 4, FR-EXBOT-093 |

**Readiness assessment:** Actors are well-defined and sufficient for test design by role. The Investor ownership check (wallet mismatch → 403) is listed in preconditions but has no corresponding alternate flow entry, creating a minor test design gap (see N-002 in §10.1). Admin bypass is explicitly documented.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Caller sends `X-Wallet-Address` header; missing header → 401 from Operator Facade | Yes | UC §2 |
| 2 | Investor: `wallet_address` in header matches `bot.user_wallet_address` in D1; mismatch → 403 | Yes (Investor path) | UC §2 |
| 3 | Admin: `X-Wallet-Address` header present; ownership check bypassed | Yes (Admin path) | UC §2 |
| 4 | Operator Facade validates caller is not blocked; blocked → 403 | Yes | UC §2 |
| 5 | When `access_mode=whitelist`: caller wallet address must be in whitelist; not in whitelist → 403 | Conditional | UC §2 |
| 6 | Operator Facade forwards to ExBot Worker with `X-Exbot-Internal-Auth` (from env var `EXBOT_INTERNAL_AUTH_TOKEN`); missing/wrong → 401 | Yes | UC §2 |
| 7 | CF service binding from Operator Facade to ExBot Worker is configured and available | Yes | UC §2 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Status query (happy path) | Investor receives 200 JSON response with current `status`, `lifecycle_state`, LP range, hedge size, drift%, margin_status, and last_light_check_at. No D1 data is mutated. | UC §3 steps 7–10 |
| Status query with MarketDataDO unavailable | 200 JSON response returned with `current_tick: null` and `range_state: null`; all other fields populated normally. No error thrown, no retry. | UC §4 A8, FR-EXBOT-093 |
| Status query for closed bot | 200 JSON response with `lifecycle_state='closed'`; bot record retained in D1. Not a 404. | UC §4 A3b |
| Status query for nonexistent bot | 404 response with E-EXBOT-023; UI shows "No active bot found for this account." | UC §4 A4 |
| Operator Facade unavailable | 503 Service Unavailable from Cloudflare infra layer; no application-level E-EXBOT code; UI shows error banner | UC §4 A5 |

---

## 4 và 5 bị loại bỏ do scope không có UI.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 GET /api/exbot/status — ExBot Status Query

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | POOL UI | Calls `GET /api/exbot/status` with `X-Wallet-Address` header | Operator Facade receives request | — | Missing header → 401 | UC §3.1, §2 |
| 2 | Operator Facade | Validates `X-Wallet-Address`; proxies to ExBot Worker via CF service binding with `X-Exbot-Internal-Auth` | ExBot Worker receives forwarded request | — | Blocked wallet → 403; not in whitelist → 403; wrong internal auth → 401; Facade unavailable → 503 (infra, A5) | UC §2, §3.2, FR-EXBOT-090 |
| 3 | ExBot Worker | Reads from D1: `bots.status`, `bots.lifecycle_state`, `bot_runtime_state.last_known_hl_short_size`, `bot_runtime_state.last_light_check_at`, `positions.tickLower`, `positions.tickUpper`, `hedge_legs.margin_status` | D1 record returned | — | No bot record → 404 E-EXBOT-023 (A4); `lifecycle_state='lp_closing'` → 200 with E-EXBOT-021 (A3a); `lifecycle_state='closed'` → 200 with E-EXBOT-022 (A3b) | UC §3.3, §4 |
| 4 | ExBot Worker | Queries `currentTick` from MarketDataDO | `currentTick` value returned | MarketDataDO unavailable or stale → `current_tick: null`, `range_state: null` (A8); all other fields returned normally | — | UC §3.4, FR-EXBOT-093 |
| 5 | ExBot Worker | Computes `rangeState`: `tickLower <= currentTick < tickUpper` → `"in"`; else `"out"` | `range_state` populated | `current_tick = null` → skip computation, `range_state: null` | — | UC §3.5 |
| 6 | ExBot Worker | Computes `drift%`: `(\|last_known_hl_short_size - targetShortEth\| / targetShortEth) × 100` using BigDecimal | `drift_pct` populated | `bots.status='safe_mode'` → A1; `lifecycle_state='hedge_stopped_cooldown'` → A2; `lifecycle_state='lp_rebalancing'` → A6; `status='error'` → A7 | — | UC §3.6, FR-EXBOT-021 |
| 7 | ExBot Worker | Composes JSON status response (Implemented fields + Pending implementation fields) | Full JSON payload assembled; Pending fields return `null` if not yet available | — | — | UC §3.7 |
| 8 | Operator Facade | Returns JSON response to POOL UI | 200 OK with status payload | — | — | UC §3.8 |
| 9 | POOL UI | Renders status panel | Investor sees status label, LP range, tick, hedge size, drift%, margin status, last light-check time | — | — | UC §3.9–10 |

**Alternate flows:**

| Flow | Trigger condition | System response | UI behavior |
|---|---|---|---|
| A1 — safe_mode | `bots.status='safe_mode'` | 200 with `safe_mode_reason` in response | "Safe Mode — No new actions" banner; all mutation buttons disabled except "Close Bot (emergency)" |
| A2 — hedge_stopped_cooldown | `bots.lifecycle_state='hedge_stopped_cooldown'` | 200 with `cooldown_end_at` timestamp in response | "Stop Fired — Cooldown (Xh remaining)"; mutation buttons disabled |
| A3a — lp_closing | `bots.lifecycle_state='lp_closing'` | 200 with `lifecycle_state='lp_closing'`; E-EXBOT-021 message | "Bot close is in progress. Please wait."; all mutation buttons disabled |
| A3b — closed | `bots.lifecycle_state='closed'` | 200 with `lifecycle_state='closed'`; E-EXBOT-022 message; record retained in D1 | "Bot safely closed. Funds have been returned to your wallet."; all mutation buttons disabled |
| A4 — no bot record | No bot record in D1 for botId | 404 E-EXBOT-023 | "No active bot found for this account." Note: `closed` bots return 200, not 404 |
| A5 — Facade unavailable | CF infra-level failure | 503 Service Unavailable; no E-EXBOT code | "Status service temporarily unavailable" banner |
| A6 — lp_rebalancing | `bots.lifecycle_state='lp_rebalancing'` | 200 with `lifecycle_state='lp_rebalancing'` | "Rebalancing in progress"; all mutation buttons disabled |
| A7 — error | `bots.status='error'` | 200 with `status='error'` | "Bot error — admin intervention required"; only "Close Bot (emergency)" enabled |
| A8 — MarketDataDO null | MarketDataDO unavailable or snapshot stale | 200; `current_tick: null`, `range_state: null`; all other fields normal | "—" displayed for range state indicator |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `bots.lifecycle_state` | Must be one of the 18 canonical states defined in SRS | Yes | Correct lifecycle label returned in response | Not applicable (D1 integrity issue — out of scope for this UC) | FR-EXBOT-003, `srs/states.md` |
| rangeState computation | Half-open interval: `tickLower <= currentTick < tickUpper` | Yes | `range_state: "in"` or `"out"` | If `current_tick = null` → `range_state: null` | UC §3 step 5 |
| drift% computation | BigDecimal arithmetic; no float/number for financial values | Yes | Accurate `drift_pct` value | Float arithmetic is an architectural violation per NFR-EXBOT-008 | FR-EXBOT-021, NFR-EXBOT-008 |
| `margin_status` | One of: `ok`, `warning`, `critical` (thresholds: ok < 0.55, warning 0.55–0.75, critical ≥ 0.75) | Yes | Correct margin label returned | Stale value possible (updated only at hedge-sync preflight + deep-audit per FR-EXBOT-060, not during status read) | FR-EXBOT-060, `srs/states.md` |
| BR-EXBOT-007 — SAFE_MODE is not terminal | SAFE_MODE bot must still respond to status queries; must eventually reach auto-recovery or bot_safe_close | Yes | 200 response with safe_mode data | N/A | BR-EXBOT-007 |
| Investor wallet ownership check | `X-Wallet-Address` must equal `bot.user_wallet_address` for Investor | Yes (Investor path) | 200 status response | 403 Forbidden | UC §2 |
| `X-Exbot-Internal-Auth` validation | Internal token must match `EXBOT_INTERNAL_AUTH_TOKEN` env var | Yes | Request forwarded | 401 from ExBot Worker | UC §2 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| Missing `X-Wallet-Address` header | API error response | 401 Unauthorized | Operator Facade auth check | UC §2 |
| Caller wallet blocked by Operator Facade | API error response | 403 Forbidden | Operator Facade auth check | UC §2 |
| Investor wallet does not match `bot.user_wallet_address` | API error response | 403 Forbidden | Ownership check in Preconditions | UC §2 |
| Missing or wrong `X-Exbot-Internal-Auth` | API error response | 401 from ExBot Worker | Internal auth check | UC §2 |
| No bot record found for botId | API error response | 404 Not Found — "No active bot found for this account." | E-EXBOT-023 | UC §4 A4 |
| Bot in `lp_closing` lifecycle state | API response (200) | "Bot close is in progress. Please wait." | E-EXBOT-021 | UC §4 A3a |
| Bot in `closed` lifecycle state | API response (200) | "Bot safely closed. Funds have been returned to your wallet." | E-EXBOT-022 | UC §4 A3b |
| Operator Facade infrastructure failure | Infra-level response | 503 Service Unavailable — "Status service temporarily unavailable" | No E-EXBOT code (infra-level, not application-defined) | UC §4 A5 |
| MarketDataDO unavailable or stale | Field-level null in 200 response | `current_tick: null`, `range_state: null`; other fields populated normally | No error code | UC §4 A8, FR-EXBOT-093 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Status read reads `hedge_legs.margin_status` | FR-EXBOT-060, hedge-sync preflight, deep-audit | The `margin_status` value is written by hedge-sync preflight and deep-audit, not by this UC. The value returned here may be stale if no hedge-sync or deep-audit has run recently. Test must verify the value matches what was last written by hedge-sync or deep-audit. | Confirm `margin_status` in response matches D1 value at time of query | FR-EXBOT-060, srs/states.md Margin Status table |
| Status read reads `bot_runtime_state.last_light_check_at` | UC-EXBOT-light-check | The timestamp reflects the last completed light-check. Test scenarios for light-check should verify this timestamp is updated correctly; status UC reads the result. | Confirm `last_light_check_at` in response matches D1 value at time of query | UC §3 step 3, srs/erd.md |
| `lifecycle_state` returned in response drives POOL UI button state | POOL module (UI buttons) | Incorrect lifecycle label in response → incorrect button enable/disable state in UI → potential user action on a bot that should not accept mutations. Critical for safety: wrong label on `lp_closing` could allow redundant close requests. | Verify all 8 lifecycle states covered in alternate flows produce correct labels | UC §4 A1–A8, srs/states.md |
| `range_state` returned in response | POOL UI indicator | A stale or null `range_state` affects the range indicator display. MarketDataDO staleness directly propagates to the investor's visibility of LP range health. | Verify null fallback path (A8) does not produce error or missing other fields | UC §4 A8, FR-EXBOT-093 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 | Happy path — active bot | Bot with `lifecycle_state='active'`, `status='active'` in D1; MarketDataDO has valid `currentTick`; Investor wallet matches `bot.user_wallet_address` | Investor calls `GET /api/exbot/status` | 200 response with all Implemented fields populated; `range_state` computed as "in" or "out"; `drift_pct` computed using BigDecimal; `margin_status` one of ok/warning/critical | UC §3, FR-EXBOT-003 |
| AC-02 | safe_mode state | Bot with `bots.status='safe_mode'` | Investor calls `GET /api/exbot/status` | 200 response includes `safe_mode_reason`; `status='safe_mode'` in response | UC §4 A1, BR-EXBOT-007 |
| AC-03 | hedge_stopped_cooldown state | Bot with `lifecycle_state='hedge_stopped_cooldown'` | Investor calls `GET /api/exbot/status` | 200 response includes `cooldown_end_at` timestamp | UC §4 A2 |
| AC-04 | lp_closing state | Bot with `lifecycle_state='lp_closing'` | Investor calls `GET /api/exbot/status` | 200 response with `lifecycle_state='lp_closing'`; response body includes E-EXBOT-021 message "Bot close is in progress. Please wait." | UC §4 A3a |
| AC-05 | closed state — record retained | Bot with `lifecycle_state='closed'`; record still exists in D1 | Investor calls `GET /api/exbot/status` | 200 response with `lifecycle_state='closed'`; NOT 404; response body includes E-EXBOT-022 message "Bot safely closed. Funds have been returned to your wallet." | UC §4 A3b |
| AC-06 | No bot record found | No record in D1 for the given botId | Investor calls `GET /api/exbot/status` | 404 response; E-EXBOT-023 triggered; response message "No active bot found for this account." | UC §4 A4 |
| AC-07 | MarketDataDO unavailable | Bot active; MarketDataDO returns null or stale snapshot | Investor calls `GET /api/exbot/status` | 200 response with `current_tick: null`, `range_state: null`; all other fields populated; no 503, no retry | UC §4 A8, FR-EXBOT-093 |
| AC-08 | lp_rebalancing state | Bot with `lifecycle_state='lp_rebalancing'` | Investor calls `GET /api/exbot/status` | 200 response with `lifecycle_state='lp_rebalancing'` | UC §4 A6 |
| AC-09 | error state | Bot with `bots.status='error'` | Investor calls `GET /api/exbot/status` | 200 response with `status='error'` | UC §4 A7 |
| AC-10 | Investor wallet mismatch | Investor wallet_address in header does NOT match `bot.user_wallet_address` in D1 | Investor calls `GET /api/exbot/status` | 403 Forbidden | UC §2 Preconditions — Suy luận cần xác nhận (no alternate flow defined; sourced from precondition only) |
| AC-11 | Admin bypasses ownership check | Admin actor sends `X-Wallet-Address` for another user's bot | Admin calls `GET /api/exbot/status` | 200 response with bot status; ownership check bypassed | UC §2 |
| AC-12 | Missing X-Wallet-Address | No `X-Wallet-Address` header in request | Any caller calls `GET /api/exbot/status` | 401 from Operator Facade | UC §2 |
| AC-13 | Wrong internal auth token | `X-Exbot-Internal-Auth` value does not match `EXBOT_INTERNAL_AUTH_TOKEN` | Facade forwards with wrong token | 401 from ExBot Worker | UC §2 |
| AC-14 | drift% uses BigDecimal precision | Bot active; known actualShortEth and targetShortEth values | Investor calls `GET /api/exbot/status` | `drift_pct` computed with BigDecimal; result matches expected value without floating-point rounding error | FR-EXBOT-021, NFR-EXBOT-008 — Suy luận cần xác nhận (targetShortEth source unconfirmed per I-003) |
| AC-15 | Pending fields return null | Bot active; "Pending implementation" fields not yet implemented | Investor calls `GET /api/exbot/status` | All Pending fields return `null` in response; no error | UC §3 step 7 null-handling note |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | No explicit latency SLA defined for `GET /api/exbot/status` in this UC. General SRS NFR-EXBOT-002 states hedge-sync should complete within 30s; not directly applicable. | Test may verify response time under normal conditions as a smoke check; no hard SLA to assert | NFR-EXBOT-002 (hedge-sync, not status) — not directly applicable |
| Security | `X-Exbot-Internal-Auth` token must be sourced from env var `EXBOT_INTERNAL_AUTH_TOKEN`; never hardcoded. ExBot Worker is not internet-accessible (direct calls return 403). | Test must verify 401 on missing/wrong internal auth; verify ExBot Worker is not directly callable without Facade | UC §2, FR-EXBOT-090, NFR-EXBOT-006 |
| Reliability / Resilience | MarketDataDO unavailability must not block the status response — system must degrade gracefully to `current_tick: null` (A8). Operator Facade unavailability produces infra-level 503 (A5). | Test A8 fallback path is a required test case; verify 503 behavior when Facade is unavailable | UC §4 A8, A5, FR-EXBOT-093 |
| Audit / Logging | FR-EXBOT-090: Operator Facade logs show service binding calls for each proxied request | Test environment should confirm logging is active; not a functional assertion but relevant for observability validation | FR-EXBOT-090 |
| Privacy / Compliance | N/A — no PII mutation in this UC. Response contains bot state and financial data visible only to the authenticated caller. | N/A |  |
| Compatibility / Integration | Base + Optimism dual-chain: `positions.tickLower`, `positions.tickUpper`, and `wethIndex` are chain-specific values stored in D1 at LP open. Status endpoint reads these values; chain ID is implicit in bot record. | Test should cover bots on both Base and Optimism to verify chain-specific LP range values are read correctly | FR-EXBOT-004, srs/erd.md |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| I-003 | High | MISSING_INFO | UC §3 step 6; FR-EXBOT-021; `srs/erd.md` `bot_runtime_state` table | The source of `targetShortEth` used in the drift% formula is not confirmed. FR-EXBOT-021 defines `targetShortEth = lpEthAmount × hedgeRatio` as a computed value at hedge-sync time. However, the ERD shows a `target_short_size` TEXT column in `bot_runtime_state`, which could be a cached value written at hedge-sync. The UC step 6 formula is present but does not specify whether ExBot Worker reads `target_short_size` from D1 or recomputes the value on the fly using `lpEthAmount × hedgeRatio` from `hedge_legs`. If the column is read from D1: test must seed `target_short_size` and assert the formula result against it. If the value is recomputed: test must seed `hedge_legs.target_ratio` and LP amount, and verify the computation. These are different test setups and different expected results. Please confirm which approach the implementation uses. | Without this confirmation, test assertions for drift% (AC-14) cannot be fully specified. The tester cannot determine which D1 column(s) to seed or what expected value to assert. | Tech Lead / Dev | Open |
| N-001 | Minor | INTERNAL_INCONSISTENCY | UC §3 step 7 JSON schema | The UC response schema splits fields into "Implemented fields" and "Pending implementation (BA-defined)". This split implies partial implementation but does not define which fields are guaranteed to be available at a given deployment version vs conditionally null. The null-handling note partially addresses this ("all pending fields return null when not yet available") but the "Pending" section label may cause testers to skip assertions on those fields entirely, rather than asserting they return null. Recommendation: UC should clarify that "Pending" fields must always return null (not missing from response) until implementation is complete, and add a note that tests MUST assert null for these fields. | Testers may omit assertions for "Pending" fields, creating a coverage gap. A field that returns null correctly vs a field that is absent from the response JSON are different behaviors. | BA / QC Lead | Open |
| N-002 | Minor | MISSING_INFO | UC §2 Preconditions; UC §4 Alternate flows | The UC lists Investor wallet mismatch → 403 in the Preconditions section but does not define it as a named alternate flow (e.g., A9). The 403 case is therefore not an explicitly testable path in the flow structure. Testers reading only the alternate flows section would not find this path. | Test design completeness: without a named alternate flow, this 403 case may be omitted from scenario design. It is a security-relevant path (unauthorized read of another user's bot) and must be tested explicitly. | BA | Open |
| N-003 | Note | MISSING_INFO | UC §6 FR Trace; `srs/spec.md` | The FR Trace in the UC lists only FR-EXBOT-002, FR-EXBOT-003, FR-EXBOT-090. Missing from the trace: FR-EXBOT-060 (margin status thresholds — the source of the ok/warning/critical computation used in the response), FR-EXBOT-093 (MarketDataDO — the source of currentTick used for rangeState), FR-EXBOT-050 (SAFE_MODE entry conditions — relevant to A1 behavior). Incomplete FR trace reduces traceability between test cases and requirements. | Test cases trace to FR for coverage reporting; missing FRs will appear as uncovered by this UC even though they are tested implicitly. | BA | Open (not a blocker) |

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| I-003: `targetShortEth` source confirmation | Data / Implementation | Blocks full test case design for drift% assertion (AC-14) | Tech Lead / Dev | Open |
| OQ-EXBOT-06: Margin thresholds (0.55/0.75) pending Phase 0 backtest finalization | Business Rule / Data | If thresholds change, test data for ok/warning/critical margin_status tests must be recalibrated | zen (backtest owner) | Open (tracked in spec.md §9) |
| OQ-EXBOT-09: MarketDataDO cache refresh interval pending Phase 0 NV-12 verification | Integration / Configuration | Affects test setup for A8 (how to trigger a stale DO snapshot in test environment) | Tech Lead / Phase 0 | Open (tracked in spec.md §9) |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-23 | QC UC Read Agent | Initial audited report; score 51/100 NOT READY; 13 open issues identified |
| v2 | 2026-06-30 | QC UC Read Agent | Re-audit after BA updates; translated to Vietnamese; score 51/100 NOT READY; issues I-001 through I-013 documented |
| v3 | 2026-07-03 | QC UC Read Agent | Re-audit after BA resolved I-001/I-002/I-004/I-005/I-006/I-009/I-010/I-011/I-013; score updated to 78/100 CONDITIONALLY READY; I-003 remains open; new observations N-001/N-002/N-003 added |

---

## 10.3 Audit Summary — Readiness Score and Verdict

### Scoring Table

| Area | Description | Max Pts | Score | Notes |
|---|---|---|---|---|
| 1 | Function/Operation & Data Object Inventory | 20 | 17 | Response schema now fully defined; all 18 lifecycle states listed; enum sets complete; `target_short_size` not explicitly listed in D1 reads section of UC (only `last_known_hl_short_size` appears), contributing to I-003 ambiguity |
| 2 | Data Object/State Attributes, Business Rules, Validations & Messages | 25 | 20 | Margin thresholds documented (FR-EXBOT-060); auth rules fully defined; MarketDataDO null fallback specified; error codes E-EXBOT-021/022/023 registered; deduction: no alternate flow for Investor wallet mismatch 403 path (N-002); "Pending" split ambiguity in response schema (N-001) |
| 3 | Functional Logic & Workflow Decomposition | 25 | 18 | All lifecycle state alternate flows A1–A8 now covered; computation formulas present; deduction: I-003 unresolved (targetShortEth source unknown → drift% test assertions cannot be fully specified); wallet mismatch 403 missing as named alternate flow |
| 4 | Functional Integration & Data Consistency | 15 | 12 | D1 field reads clearly listed; MarketDataDO integration specified; Facade passthrough defined; deduction: no explicit note on eventual consistency behavior of `margin_status` (updated at hedge-sync/deep-audit, potentially stale when status is read) |
| 5 | UC/Spec Documentation Quality Issues | 15 | 11 | Major structural gaps resolved in this revision; deduction: "Pending implementation" label creates test design ambiguity (N-001); FR trace incomplete — FR-EXBOT-060, FR-EXBOT-093, FR-EXBOT-050 missing (N-003) |
| **Total** | | **100** | **78** | **CONDITIONALLY READY** |

### Verdict: CONDITIONALLY READY (78/100)

This UC has been substantially improved from v2 (51/100) through the BA's 2026-07-03 revision. The following previously blocking issues are now resolved: alternate flow for A3 (lp_closing + closed with E-EXBOT-021/022), actor definition (Investor + Admin, auth mechanism), field name confirmation (last_light_check_at), alternate flows A6/A7, JSON response schema definition, E-EXBOT-023 registration, A5 infra-level note, auth mechanism documentation, and MarketDataDO null fallback (A8).

**One remaining blocker (I-003):** The source of `targetShortEth` in the drift% formula has not been confirmed by the developer. FR-EXBOT-021 defines it as a computed value (`lpEthAmount × hedgeRatio`), but the ERD contains a `target_short_size` column in `bot_runtime_state` that may serve as a cached version of this value. This ambiguity means test cases for drift% (AC-14) cannot be fully specified — the test data setup and expected result depend on whether the Worker reads from D1 or recomputes. This issue must be resolved by the Tech Lead or Dev before test case design for drift% can be finalized.

**Recommendation:** Proceed with test scenario design for all flows except the drift% assertion path. Scenarios for A1–A8, auth paths, null fallback, and response schema validation can be designed immediately. Draft the drift% test case as a placeholder with the formula and mark it pending I-003 resolution. Once I-003 is confirmed, finalize the drift% test assertion and complete the test case set.

