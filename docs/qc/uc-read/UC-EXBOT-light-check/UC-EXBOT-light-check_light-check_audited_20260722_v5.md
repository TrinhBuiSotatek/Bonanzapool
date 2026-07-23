# Báo cáo rà soát mức độ sẵn sàng của Use Case

**UC-EXBOT-light-check — Execute Periodic Light-Check**
**Ngày tạo:** 2026-07-22
**Tác giả:** QC UC Read Agent (qc-uc-read-exbot)
**Version:** v5

---

## Feature Brief - Tóm tắt nghiệp vụ

UC-EXBOT-light-check mô tả luồng tự động kiểm tra định kỳ (mỗi 5 phút) cho tất cả các bot ExBot đang hoạt động. Luồng này hoạt động hoàn toàn trên backend AWS (Lambda + Aurora PostgreSQL + ElastiCache Redis) mà **không thực hiện bất kỳ lệnh gọi nào tới Hyperliquid API** — đây là bất biến cốt lõi được ràng buộc bởi `BR-EXBOT-003` (HL weight = 0).

Mỗi lượt light-check có trách nhiệm: (1) đọc trạng thái LP hiện tại từ Pool Slot0 Cache (ElastiCache Redis) và Aurora PostgreSQL; (2) tính toán `lpEthAmount` bằng TickMath + LiquidityAmounts cục bộ; (3) đánh giá xem bot có cần điều chỉnh hedge hay không dựa trên bảy lý do kích hoạt trong `RebalanceReason[]`; (4) giám sát stop trigger bằng cách đọc `markPriceUsd` từ HL Mark Price Cache (ElastiCache Redis) thay vì gọi HL trực tiếp; và (5) kiểm tra tình huống overrun (`stop_replacing_started_at` bị kẹt > 60 giây) để chuyển bot sang `safe_mode` kịp thời.

Use case này liên kết chặt chẽ với: `US-EXBOT-005` (light-check không gọi HL), `US-EXBOT-006` (delta-only hedge adjustment), `US-EXBOT-007` (LP range rebalance trigger), `US-EXBOT-008` (circuit breaker management). Điều quan trọng cần nắm để thiết kế test là: light-check **chỉ ra quyết định và enqueue message** — quá trình thực thi hedge và LP rebalance xảy ra ở worker riêng biệt (hedge-sync, partial_repair). Light-check KHÔNG tự set `lifecycle_state='lp_rebalancing'`.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
| UC-EXBOT-light-check | Execute Periodic Light-Check | updated 2026-07-20 | Draft |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
| @hienduong | QC UC Read Agent | 2026-06-12 | 2026-07-20 |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
| usecases/uc-light-check.md | 2026-07-20 | UC | 2 fixes: lp_value_usd formula + stale threshold 120s |
| userstories/us-005.md | latest | US | Light-check without HL calls |
| userstories/us-006.md | latest | US | Delta-only hedge adjustment |
| userstories/us-007.md | 2026-07-14 | US | LP range rebalance trigger |
| userstories/us-008.md | latest | US | Circuit breaker management |
| srs/spec.md | 2026-07-20 | SRS | Source of truth cho formulas, OQ closed |
| srs/states.md | 2026-07-14 | SRS — State diagram | 18 lifecycle states |
| srs/flows.md | 2026-07-14 | SRS — Flow diagram | F-01 fan-out flow |
| srs/erd.md | 2026-07-20 | ERD | funding_rolling_metrics, safe_mode_tier v1 gap |
| frd.md | 2026-07-21 | FRD | FR-EXBOT-011..040, RebalanceReason[] enum |
| common-rules.md | latest | Common rule | BR-EXBOT-003, BR-EXBOT-005 |
| message-list.md | latest | Messages | E-EXBOT-019, E-EXBOT-020 |
| UC-EXBOT-light-check_light-check_questions_20260714_v2.md | 2026-07-22 | Question backlog | All questions Answered |
| scoring-rubric.md | latest | Scoring rubric | 100 points, 5 areas |

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| BR-EXBOT-* | Business Rule — ràng buộc nghiệp vụ bắt buộc của module ExBot; không thể bị bỏ qua ở bất kỳ worker nào | common-rules.md |
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng cụ thể cần implement | frd.md |
| E-EXBOT-* | Error Code — mã lỗi hệ thống ExBot; xác định message lỗi cụ thể kèm điều kiện kích hoạt | message-list.md |
| UC | Use Case — tài liệu mô tả luồng nghiệp vụ chính và alternate flows | usecases/ |
| US | User Story — yêu cầu từ góc độ người dùng, kèm Acceptance Criteria | userstories/ |
| SRS | Software Requirements Specification — baseline kỹ thuật, bao gồm spec.md, states.md, flows.md, erd.md | srs/ |
| HL | Hyperliquid — sàn giao dịch phái sinh phi tập trung nơi ExBot đặt lệnh short hedge | (platform name) |
| LP | Liquidity Provider — vị thế thanh khoản Uniswap V3 do bot quản lý; ETH-USDC pool trên Base/Optimism | (industry term) |
| SAFE_MODE | Trạng thái bot bị tạm ngừng mutations khi phát hiện tình huống bất thường nghiêm trọng; không phải trạng thái cuối (BR-EXBOT-007) | common-rules.md |
| INV-STOP | Invariant: place-before-cancel stop replacement — không bao giờ có khoảng thời gian 0 stop | srs/spec.md §19.5 |
| RebalanceReason[] | Enum 7 lý do kích hoạt điều chỉnh hedge: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback | frd.md FR-EXBOT-011 |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

Use case này tồn tại để đảm bảo mỗi bot ExBot đang hoạt động được giám sát liên tục, phát hiện kịp thời khi vị thế LP lệch khỏi trạng thái an toàn, và kích hoạt hành động điều chỉnh mà không cần tương tác trực tiếp với Hyperliquid. Nếu không có light-check, bot sẽ không biết khi nào cần điều chỉnh hedge, khi nào stop trigger bị kích hoạt, hoặc khi nào overrun xảy ra — dẫn đến tổn thất tài chính không được kiểm soát.

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
| Bot scan và fan-out | EventBridge Scheduler → Scan Worker query Aurora PostgreSQL → enqueue per-bot light-check messages | UC §3 steps 1-4; FR-EXBOT-011 |
| Idempotency check | Light-Check Worker insert message_id vào queue_idempotency; UNIQUE conflict → skip | UC §3 step 5; FR-EXBOT-011 |
| Pool Slot0 Cache read | Đọc sqrtPriceX96, currentTick từ ElastiCache Redis; fail-fast nếu stale > 120s | UC §3 step 7; FR-EXBOT-093 |
| LP amount calculation | Tính lpEthAmount từ liquidity, tickLower, tickUpper, sqrtPriceX96 bằng TickMath + LiquidityAmounts cục bộ | UC §3 step 8; FR-EXBOT-021 |
| RebalanceReason[] evaluation | Đánh giá 7 lý do: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback | UC §3 step 9; FR-EXBOT-011 |
| Hedge-sync enqueue | Enqueue 1 hedge-sync với decision.reason[] nếu action=REBALANCE và circuit không open | UC §3 step 10; FR-EXBOT-011 |
| Stop monitoring | Đọc markPriceUsd từ HL Mark Price Cache; set stop_trigger_crossed_at; enqueue price-near-stop-audit | UC §3 step 11; FR-EXBOT-031, FR-EXBOT-032 |
| Overrun check | Kiểm tra stop_replacing_started_at bị kẹt > 60s → SAFE_MODE + partial_repair | UC §3 step 12; FR-EXBOT-033 |
| Circuit breaker integration | Suppress / probe hedge-sync khi circuit open / half_open; stop monitoring vẫn chạy | UC §4 A2, A3; FR-EXBOT-040 |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
| Hedge execution | Hedge-sync worker xử lý; light-check chỉ enqueue | Test hedge execution thuộc UC-EXBOT-hedge-sync |
| LP rebalance execution | Hedge-sync / partial_repair worker xử lý; light-check không set lifecycle_state='lp_rebalancing' | Test LP rebalance execution thuộc UC-EXBOT-hedge-sync |
| Stop replacement execution | price-near-stop-audit / partial_repair worker xử lý | Test stop replacement thuộc UC riêng |
| deep-audit | 6h cron riêng biệt; không liên quan light-check | Test deep-audit thuộc UC riêng |
| UI / Admin dashboard | ExBot là backend-only, không có UI trong scope | N/A |
| funding_rolling_metrics population | bnza-market-cron worker chưa deploy ở v1 | funding_alert AC-LC-09 chỉ test được từ v1.1 |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
| EventBridge Scheduler | System | Kích hoạt bot-scan queue mỗi 1 phút | Không có quyền hạn người dùng; chỉ enqueue | FR-EXBOT-010; UC §1 |
| Scan Worker (Lambda) | System | Query Aurora PostgreSQL, update next_light_check_at, enqueue per-bot light-check | Đọc/ghi Aurora PostgreSQL; ghi SQS | UC §3 steps 1-4 |
| Light-Check Worker (Lambda) | System — Primary | Xử lý toàn bộ logic light-check; không gọi HL | Đọc Aurora PG + Redis; ghi Aurora PG + SQS | UC §3 steps 5-13 |
| Aurora PostgreSQL (state_db_shard) | System | Lưu trữ trạng thái bot, hedge_legs, circuit_breakers, queue_idempotency | Source of truth cho hot state | UC §1; ERD |
| Pool Slot0 Cache (ElastiCache Redis) | System | Cung cấp sqrtPriceX96, currentTick cho LP calculation | Stale > 120s → fail-fast | UC §1, step 7; FR-EXBOT-093 |
| HL Mark Price Cache (ElastiCache Redis) | System | Cung cấp markPriceUsd cho stop trigger detection | Không phải HL API call; stale → band widening + freeze hedge-sync | UC §3 step 11 |

**Nhận xét readiness:** Actor/role đầy đủ và rõ ràng cho test design. Light-Check Worker là primary actor. Không có actor người dùng (investor/admin) tham gia trực tiếp vào luồng này.

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 | Bot `status='active'` và `next_light_check_at <= now` | Yes | UC §2; FR-EXBOT-011 |
| 2 | `lifecycle_state NOT IN ('lp_rebalancing', 'lp_closing')` | Yes | UC §2; FR-EXBOT-011 |
| 3 | `status != 'paused'` | Yes | UC §2; FR-EXBOT-003 |
| 4 | Bot ở `lifecycle_state='hedge_stopped_cooldown'` KHÔNG bị skip — light-check vẫn chạy bình thường; chỉ hedge-sync bị suppress | Yes | UC §2 note; FR-EXBOT-011 |
| 5 | Pool Slot0 Cache phải accessible và không stale > 120s — nếu không, tick bị skip hoàn toàn | Yes (fail-fast) | UC §3 step 7; FR-EXBOT-093 |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Happy path (không cần hành động) | `queue_idempotency.state='succeeded'`; `next_light_check_at` đã được update ở step 4; không có message nào được enqueue | UC §5; UC §3 step 13 |
| Phát hiện cần điều chỉnh hedge | 1 hedge-sync message được enqueue với `{botId, reasons[], stateVersion}`; `queue_idempotency.state='succeeded'` | UC §5; UC §3 step 10 |
| Phát hiện stop trigger crossed | `stop_trigger_crossed_at` được set (write-once); 1 `price-near-stop-audit` message được enqueue | UC §3 step 11; FR-EXBOT-031 |
| Phát hiện stop overrun | `bots.status='safe_mode'` VÀ `bots.lifecycle_state='safe_mode'` được set atomically; 1 `partial_repair(reason='stop_replacing_overrun')` được enqueue | UC §3 step 12; FR-EXBOT-033 |
| Pool Slot0 Cache stale / unreachable | Tick bị skip hoàn toàn; không có evaluation; `next_light_check_at` vẫn đã được update ở step 4 | UC §4 A1 |
| Message duplicate (idempotency) | UNIQUE conflict → return ngay; không xử lý tiếp | UC §3 step 5; FR-EXBOT-011 |

**Lưu ý:** `next_light_check_at` luôn được update bởi Scan Worker tại step 4 cho **mọi** eligible bot (kể cả bot ở `lp_rebalancing`, `lp_closing`) — trước khi Light-Check Worker xử lý. Bots bị skip sau đó vẫn được reschedule đúng (tránh flood khi recovery).

---

## 6. Phân rã nghiệp vụ và luồng xử lý

### 6.1 Bot Scan và Fan-Out (EventBridge → Scan Worker)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 | EventBridge Scheduler | Kích hoạt mỗi 1 phút → gọi `chunkSendBatch` | Bot-scan message được enqueue | N/A | N/A | UC §3 step 1 |
| 2 | Scan Worker | Query Aurora PostgreSQL: `SELECT * FROM bots WHERE status='active' AND next_light_check_at <= now ORDER BY next_light_check_at LIMIT 500` | Trả về danh sách ≤ 500 bots eligible | Shard có > 500 bots: các bot vượt LIMIT được xử lý ở tick tiếp theo, oldest first | N/A | UC §3 step 2 |
| 3 | Scan Worker | Gửi per-bot messages đến `light-check` queue qua `chunkSendBatch` | Mỗi bot nhận 1 light-check message | N/A | N/A | UC §3 step 3 |
| 4 | Scan Worker | Update `next_light_check_at = now + 5min + jitter(±45s)` cho **mọi** eligible bot trong batch | Tất cả bots (kể cả sẽ bị skip) được reschedule | N/A | N/A | UC §3 step 4; FR-EXBOT-012 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| LIMIT 500 per tick | By design — jitter ±45s phân tán bots đều trong 5 phút ở steady state | Yes | Tất cả eligible bots được xử lý trong 1-2 ticks | Bots vượt LIMIT được xử lý ở tick tiếp theo | UC §3 step 2 |
| Jitter formula | `next_light_check_at = now + 5min + random(−45s, +45s)` — `hash(botId)` deterministic | Yes | Bots được phân tán đều; không clustering tại :00/:05 | N/A | FR-EXBOT-012 |
| `chunkSendBatch` bắt buộc | Direct `queue.sendBatch()` bị forbidden; SQS max 10/call | Yes | Batch được gửi đúng | N/A | FR-EXBOT-010 |
| next_light_check_at update scope | Cả bots ở `lp_rebalancing`, `lp_closing` cũng được update (dù Light-Check Worker sau đó skip chúng) | Yes | Tránh flood message khi bot recovery | N/A | UC §3 step 4 |

### 6.2 Light-Check Worker — Idempotency và State Read

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 5 | Light-Check Worker | Insert `message_id` vào `queue_idempotency` (state='started', expires_at=now+1min) | Insert thành công | UNIQUE conflict → skip toàn bộ tick (duplicate delivery) | N/A | UC §3 step 5; FR-EXBOT-011 |
| 6 | Light-Check Worker | Đọc từ Aurora PG: `bot_runtime_state.last_known_hl_short_size`, `lifecycle_state`, `hedge_legs` (stop_price, margin_status, circuit_state) | Dữ liệu hot state được load | N/A | N/A | UC §3 step 6 |
| 7 | Light-Check Worker | Đọc Pool Slot0 Cache: `sqrtPriceX96`, `currentTick`; kiểm tra staleness | Cache fresh (≤ 120s) → tiếp tục | Cache stale (> 120s) hoặc unreachable → A1: skip tick hoàn toàn | N/A | UC §3 step 7; FR-EXBOT-093 |
| 8 | Light-Check Worker | Tính `lpEthAmount` từ `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96` bằng TickMath + LiquidityAmounts (không RPC) | lpEthAmount được tính cục bộ | N/A | N/A | UC §3 step 8; FR-EXBOT-021 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| Pool Slot0 Cache stale threshold | `snapshot age > 2× refresh interval`; provisional: `> 120s` (refresh interval = 60s, zen confirmed, config-driven) | Yes | Tiếp tục evaluation | Fail-fast: skip tick hoàn toàn; không có trigger evaluation | UC §3 step 7; FR-EXBOT-093; OQ-EXBOT-09 closed |
| queue_idempotency expires_at | Luôn set TTL = 1 phút khi insert | Yes | N/A | Bảng tích lũy vô hạn | UC §3 step 5 note |
| EventBridge cron purge | Cron job mỗi 1 giờ: `DELETE FROM queue_idempotency WHERE expires_at < now` | Yes | Bảng được dọn sạch định kỳ | N/A | UC §3 step 5 note; FR-EXBOT-011 AC |
| BR-EXBOT-003 (HL weight = 0) | Light-Check Worker KHÔNG được thực hiện bất kỳ lệnh gọi HL API nào | Yes | N/A | Vi phạm bất biến cốt lõi của hệ thống | common-rules.md; BR-EXBOT-003: "HL API call count MUST be 0 during light-check execution" |

### 6.3 RebalanceReason[] Evaluation (Strategy Engine)

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 9 | Light-Check Worker | Đánh giá 7 lý do kích hoạt điều chỉnh; gom kết quả vào `decision.reason[]` | Một hoặc nhiều reason bị fired, hoặc rỗng | N/A | N/A | UC §3 step 9; FR-EXBOT-011 |
| 10 | Light-Check Worker | Nếu `action=REBALANCE` VÀ `circuit_state != 'open'`: enqueue **1** hedge-sync với `{botId, reasons[], stateVersion}` | 1 message được enqueue; `range_out` được đưa vào reasons[] như mọi trigger khác | A2: circuit open → suppress hedge-sync; A3: half_open → 1 probe hedge-sync | N/A | UC §3 step 10; UC §4 A2, A3 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| `drift_threshold` | `deltaErrorUsd > max($25, lpValueUsd × 3%)` — `deltaErrorUsd = \|targetShortEth − actualShortEth\| × uniPoolPrice`; `lpValueUsd = (lpEthAmount × uniPoolPrice) + lpUsdcAmount` (principal only, exclude tokensOwed; price = Uniswap pool slot0) | Yes | drift_threshold added to reason[] | N/A | UC step 9; FR-EXBOT-011; OQ-EXBOT-11 closed (zen) |
| `drift_relative` | `\|target - actual\| / target > 0.15` | Yes | drift_relative added to reason[] | N/A | FR-EXBOT-011 |
| `range_out` | `rangeState != 'in'` | Yes | range_out added to reason[]; light-check KHÔNG set lifecycle_state='lp_rebalancing' | N/A | UC step 9; FR-EXBOT-011; US-EXBOT-007 AC-007-1 fix |
| `range_boundary_near` | `min(distToLower, distToUpper) / halfRange <= rangeBoundaryFraction (default 0.9)` | Yes | range_boundary_near added to reason[] | N/A | UC step 9; FR-EXBOT-011; OQ-EXBOT-10 closed |
| `margin_warning` | `hedge_legs.margin_status == 'warning'` (đọc từ Aurora PG — không gọi HL) | Yes | margin_warning added to reason[] | N/A | FR-EXBOT-011 |
| `funding_alert` | 7d funding APR < −15%; primary source: `fundingApr7dPct` từ `funding_rolling_metrics`; fallback: `fundingRate × 8760`; nếu < 7 rows: `× 365/n` | Yes | funding_alert added to reason[] | v1 gap: bnza-market-cron chưa deploy → bảng trống → fallback luôn được dùng ở v1 | UC step 9; FR-EXBOT-011; OQ-EXBOT-12 closed (zen) |
| `time_fallback` | 4h kể từ lần adjustment cuối | Yes | time_fallback added to reason[] | N/A | FR-EXBOT-011 |
| light-check KHÔNG set `lifecycle_state='lp_rebalancing'` | Hedge-sync worker mới là người set; light-check chỉ enqueue | Yes | N/A | Conflict với US-EXBOT-007 AC-007-1 cũ (đã được BA fix 2026-07-14) | UC step 10; US-EXBOT-007 AC-007-1 (fixed) |
| 1 hedge-sync duy nhất | Dù có nhiều reason[] fired cùng lúc, chỉ enqueue 1 message | Yes | Tránh xử lý trùng lặp | N/A | UC step 10; I-05 confirmed |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| circuit open | State read | Suppress hedge-sync; stop monitoring vẫn chạy bình thường | FR-EXBOT-040 | UC §4 A2 |
| circuit half_open | State + SQS | Atomically claim `half_open_probe_used`; enqueue 1 probe hedge-sync | FR-EXBOT-040 | UC §4 A3 |

### 6.4 Stop Monitoring

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 11 | Light-Check Worker | Đọc `markPriceUsd` từ HL Mark Price Cache (ElastiCache Redis) | markPriceUsd fresh → đánh giá stop trigger | Cache stale (updatedAt > 120s): `audit hl_mark_price_stale`; widen band 2%→4%; freeze routine hedge-sync sau stop check; fallback sang `bot_runtime_state.eth_price_usd` | N/A | UC §3 step 11; FR-EXBOT-031 |
| 11b | Light-Check Worker | Nếu `markPrice >= stop_price`: set `stop_trigger_crossed_at` (write-once guard); enqueue `price-near-stop-audit` | stop_trigger_crossed_at được set; PSAQ message được enqueue | A4: `stop_trigger_crossed_at` đã có giá trị → KHÔNG overwrite; vẫn enqueue price-near-stop-audit | N/A | UC §3 step 11; UC §4 A4; FR-EXBOT-031; BR-EXBOT-005 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| BR-EXBOT-005 (stop_trigger_crossed_at write-once) | Field được set một lần, không bao giờ bị overwrite khi đã có giá trị | Yes | N/A | Mất thông tin thời điểm đầu tiên stop bị trigger | common-rules.md; BR-EXBOT-005 |
| 3-way price split (MUST NOT interchange) | uniPoolPrice: LP drift; hlMarkPrice: stop trigger; hlOraclePrice: margin calculation | Yes | Mỗi metric dùng đúng nguồn giá | Tính drift_threshold bằng hlMarkPrice → sai; tính stop bằng uniPoolPrice → sai | FR-EXBOT-011; SRS spec.md X-5 |
| Stop monitoring bất kể circuit state | Stop monitoring chạy ngay cả khi `circuit_state='open'` | Yes | N/A | Bỏ lỡ stop trigger khi circuit open | UC §4 A2; FR-EXBOT-011 |
| HL Mark Price Cache fallback | Cache stale → fallback sang `bot_runtime_state.eth_price_usd` (last-known từ light-check trước) | Yes | N/A | N/A | UC §3 step 11 |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| stop_trigger_crossed_at kẹt > 30 phút | State transition → SAFE_MODE | Không có message UI; log sự kiện; partial_repair được enqueue | E-EXBOT-019 | message-list.md; FR-EXBOT-031 |

### 6.5 Overrun Check và SAFE_MODE

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 12 | Light-Check Worker | Kiểm tra `stop_replacing_started_at IS NOT NULL AND age > 60s` | Nếu không overrun: tiếp tục bình thường | Overrun detected: atomically set `bots.status='safe_mode'` VÀ `bots.lifecycle_state='safe_mode'` trong 1 UPDATE; sau đó enqueue `partial_repair(reason='stop_replacing_overrun')` | N/A | UC §3 step 12; FR-EXBOT-033 |
| 13 | Light-Check Worker | Update `queue_idempotency.state='succeeded'` | Tick hoàn thành | N/A | N/A | UC §3 step 13 |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
| SAFE_MODE atomicity | `bots.status` VÀ `bots.lifecycle_state` phải được set trong **1 single UPDATE statement** | Yes | State nhất quán | Tình trạng race condition giữa 2 UPDATE | UC §3 step 12; I-07 confirmed |
| Status → SAFE_MODE trước khi enqueue | State change phải xảy ra **trước** khi partial_repair message được đưa vào queue | Yes | Không có race condition nếu worker crash sau enqueue | Nếu enqueue trước, worker có thể đọc status cũ | UC §3 step 12 |
| SAFE_MODE không phải terminal state (BR-EXBOT-007) | Bot ở safe_mode có thể được repair và restore về active | Yes | partial_repair xử lý recovery | N/A | common-rules.md (BR-EXBOT-007, chưa được trace rõ trong UC §6) |

#### C. Thông báo, lỗi và phản hồi hệ thống

| Trường hợp | Loại phản hồi | Nội dung phản hồi / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
| stop_replacing_started_at kẹt > 60s | State transition + SQS enqueue | `bots.status='safe_mode'`; `bots.lifecycle_state='safe_mode'`; partial_repair enqueued | E-EXBOT-020 | message-list.md; FR-EXBOT-033; UC §3 step 12 |

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
| Enqueue hedge-sync | UC-EXBOT-hedge-sync | Hedge-sync worker nhận message, thực hiện delta-only adjustment, set lifecycle_state='lp_rebalancing' nếu cần | reasons[] trong message phải khớp với evaluation ở step 9 | UC step 10; FR-EXBOT-010 |
| Enqueue price-near-stop-audit | UC riêng (stop-audit worker) | Stop-audit worker kiểm tra tình trạng stop và thực hiện stop replacement nếu cần | stop_trigger_crossed_at phải có giá trị trước khi message được enqueue | UC step 11; FR-EXBOT-031 |
| Enqueue partial_repair(stop_replacing_overrun) | UC riêng (repair worker) | Repair worker xử lý recovery stop replacement bị kẹt | bots.status='safe_mode' phải được set trước khi partial_repair message được xử lý | UC step 12; FR-EXBOT-033 |
| next_light_check_at update | Scan Worker (tick tiếp theo) | Scan Worker dùng next_light_check_at để quyết định bot nào eligible ở tick tiếp theo | Batch update per shard — 1 statement, không per-bot | UC step 4; FR-EXBOT-012 |
| stop_trigger_crossed_at set | deep-audit (6h) và partial_repair | Deep-audit phát hiện stuck > 30 min → SAFE_MODE (backstop thứ hai); primary detection là light-check ≤5 min | stop_trigger_crossed_at write-once: không bao giờ bị overwrite | E-EXBOT-019; FR-EXBOT-033 |
| circuit_state thay đổi | Circuit_breakers table | Sau khi circuit open → light-check tiếp theo suppress hedge-sync | circuit_breakers.state cần được update đúng trước next light-check tick | FR-EXBOT-040; US-EXBOT-008 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-LC-01 | Happy path: bot active, không trigger | Bot status='active', lifecycle_state='active', next_light_check_at <= now; Pool Slot0 Cache fresh; tất cả reasons[] = false | Light-Check Worker xử lý bot | queue_idempotency.state='succeeded'; không có hedge-sync, PSAQ, partial_repair nào được enqueue | UC main flow; US-EXBOT-005 AC-005-1 |
| AC-LC-02 | Skip bot ở lp_rebalancing | Bot lifecycle_state='lp_rebalancing' | Scan Worker enqueue; Light-Check Worker dequeue | Tick bị skip; next_light_check_at đã được update bởi Scan Worker ở step 4 | UC §2; FR-EXBOT-011 |
| AC-LC-03 | Skip bot ở lp_closing | Bot lifecycle_state='lp_closing' | Scan Worker enqueue; Light-Check Worker dequeue | Tick bị skip; next_light_check_at đã được update bởi Scan Worker ở step 4 | UC §2; FR-EXBOT-011 |
| AC-LC-04 | Skip bot status='paused' | Bot status='paused' | Scan Worker gặp bot này | Bot không được query (status != 'active' nên không vào LIMIT 500 scan) | UC §2; FR-EXBOT-003 |
| AC-LC-05 | Idempotency: message duplicate | message_id đã tồn tại trong queue_idempotency | Light-Check Worker nhận duplicate message | UNIQUE conflict → return ngay; không xử lý tiếp; không có side effect | UC §3 step 5 |
| AC-LC-06 | Pool Slot0 Cache stale | Cache.updatedAt > 120s | Light-Check Worker đọc cache | Fail-fast: tick bị skip hoàn toàn; không có trigger evaluation; không có enqueue | UC §4 A1; FR-EXBOT-093 |
| AC-LC-07 | drift_threshold kích hoạt | `\|targetShortEth − actualShortEth\| × uniPoolPrice > max($25, (lpEthAmount × uniPoolPrice + lpUsdcAmount) × 3%)`; circuit_state='closed' | Light-Check Worker đánh giá | drift_threshold added to reason[]; hedge-sync được enqueue với reason=['drift_threshold'] | UC step 9; FR-EXBOT-011; OQ-EXBOT-11 closed |
| AC-LC-08 | range_out kích hoạt — light-check không set lp_rebalancing | rangeState != 'in'; circuit_state='closed' | Light-Check Worker đánh giá | range_out added to reason[]; hedge-sync enqueued; light-check KHÔNG set lifecycle_state='lp_rebalancing' | UC step 9-10; US-EXBOT-007 AC-007-1 |
| AC-LC-09 | funding_alert kích hoạt (v1: fallback path) | fundingApr7dPct = fundingRate × 8760 < −0.15 (vì funding_rolling_metrics trống ở v1) | Light-Check Worker đánh giá | funding_alert added to reason[]; hedge-sync enqueued | UC step 9; OQ-EXBOT-12 closed; v1 gap: bnza-market-cron chưa deploy |
| AC-LC-10 | circuit open — suppress hedge-sync, stop vẫn chạy | circuit_state='open'; drift_threshold fired | Light-Check Worker step 10 | hedge-sync NOT enqueued; stop monitoring tiếp tục bình thường ở step 11 | UC §4 A2; US-EXBOT-005 AC-005-3 |
| AC-LC-11 | circuit half_open — 1 probe | circuit_state='half_open'; drift_threshold fired | Light-Check Worker step 10 | half_open_probe_used claimed atomically; 1 probe hedge-sync enqueued | UC §4 A3; US-EXBOT-008 AC-008-2 |
| AC-LC-12 | Stop trigger crossed | markPriceUsd >= stop_price; stop_trigger_crossed_at IS NULL | Light-Check Worker step 11 | stop_trigger_crossed_at được set; price-near-stop-audit enqueued; hedge-sync KHÔNG được enqueue cho stop path | UC step 11; FR-EXBOT-031; BR-EXBOT-005 |
| AC-LC-13 | Stop trigger already crossed (write-once) | markPriceUsd >= stop_price; stop_trigger_crossed_at IS NOT NULL | Light-Check Worker step 11 | stop_trigger_crossed_at KHÔNG bị overwrite; price-near-stop-audit vẫn được enqueue | UC §4 A4; BR-EXBOT-005 |
| AC-LC-14 | HL Mark Price Cache stale | HL Mark Price Cache.updatedAt > 120s | Light-Check Worker step 11 | Audit `hl_mark_price_stale`; near-stop band widened 2%→4%; routine hedge-sync frozen sau stop check; fallback sang bot_runtime_state.eth_price_usd | UC step 11 |
| AC-LC-15 | Stop overrun → SAFE_MODE | stop_replacing_started_at IS NOT NULL AND age > 60s | Light-Check Worker step 12 | bots.status='safe_mode' VÀ bots.lifecycle_state='safe_mode' set atomically trong 1 UPDATE; partial_repair(reason='stop_replacing_overrun') enqueued SAU state change | UC step 12; FR-EXBOT-033; E-EXBOT-020 |
| AC-LC-16 | Jitter phân tán bots | Bot shard có 200 bots eligible | Scan Worker xử lý | next_light_check_at của mỗi bot = now + 5min + hash(botId) deterministic jitter(±45s); không clustering | FR-EXBOT-012 |

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance | Scan Worker LIMIT 500 per tick; jitter ±45s giảm Aurora PostgreSQL write spike | Test boundary: shard có đúng 500 và 501 bots; verify bots vượt LIMIT được xử lý ở tick tiếp theo | FR-EXBOT-012; UC step 2 |
| Performance | Aurora PostgreSQL batch update `next_light_check_at` per shard (1 statement), không per-bot | Test: verify không có N×1 queries khi shard có nhiều bots | UC step 4 |
| Reliability | Idempotency via queue_idempotency — duplicate delivery phải skip | Test: gửi duplicate SQS message → verify không có double processing | UC step 5; FR-EXBOT-011 |
| Reliability | Fail-fast khi Pool Slot0 Cache stale — tick bị skip, không có partial evaluation | Test: mock cache stale → verify KHÔNG có trigger evaluation nào xảy ra | UC §4 A1; FR-EXBOT-093 |
| Reliability | queue_idempotency TTL cleanup via EventBridge cron 1h | Test: verify bảng không tích lũy vô hạn sau nhiều ticks (integration test) | UC step 5 note |
| Correctness | Tất cả tính toán tài chính PHẢI dùng BigDecimal, không dùng JS float | Test: boundary values với số thập phân ETH nhỏ; verify không có floating point error | FR-EXBOT-021 (implied) |
| Security | BR-EXBOT-003: HL API call count = 0 trong toàn bộ light-check | Test: mock/spy tất cả HL adapter calls → verify count = 0 trong mọi scenario | BR-EXBOT-003; US-EXBOT-005 |
| Audit / Logging | E-EXBOT-019: log khi stop_trigger_crossed_at kẹt > 30 phút | Test: verify log event được emit với đúng message sau 30 phút | E-EXBOT-019; message-list.md |
| Audit / Logging | E-EXBOT-020: log khi stop_replacing_started_at kẹt > 60s | Test: verify log event được emit và SAFE_MODE transition xảy ra | E-EXBOT-020; message-list.md |

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| v5-I-01 | Medium | MISSING_INFO | UC step 9 vs FRD FR-EXBOT-011 | UC step 9 liệt kê 5 trong 7 RebalanceReason, nhưng **thiếu `drift_relative`** (ngưỡng: `\|target - actual\| / target > 0.15`) và **`time_fallback`** (điều kiện: 4h kể từ lần adjustment cuối). FRD FR-EXBOT-011 liệt kê đầy đủ 7 lý do. Tester không biết hai lý do này có tồn tại và hoạt động theo ngưỡng nào nếu chỉ đọc UC. BA vui lòng bổ sung `drift_relative` và `time_fallback` vào UC step 9 với điều kiện kích hoạt rõ ràng. | Tester thiếu 2 trong 7 trigger conditions → không thể thiết kế test case đầy đủ cho RebalanceReason[] evaluation. | BA | Open |
| v5-I-02 | Low | MISSING_INFO | UC §6 vs common-rules.md BR-EXBOT-004, BR-EXBOT-007 | UC §6 (Business Rules) chỉ trace `BR-EXBOT-003` và `BR-EXBOT-005` nhưng **thiếu BR-EXBOT-004** (Delta-only hedge adjustment invariant: full close/open bị forbidden) và **BR-EXBOT-007** (SAFE_MODE is never a terminal state). Cả 2 BR áp dụng trực tiếp cho các luồng trong UC này (SAFE_MODE transition ở step 12; delta-only constraint ở step 10 enqueue). | Low risk — tester vẫn có thể thiết kế test dựa trên UC steps, nhưng BR trace không đầy đủ ảnh hưởng đến traceability. | BA | Open |

*Ghi chú: Tất cả câu hỏi từ v3 (v3-I-03, v3-I-04, v3-I-06) và từ các audit trước đó (I-01 đến I-13) đã được Answered và không còn Open. Issue Register ở v5 chỉ có 2 issue mới được phát hiện sau khi đối chiếu UC (2026-07-20) với FRD.*

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| `bnza-market-cron` worker chưa deploy ở v1 | Environment / Feature gap | `funding_rolling_metrics` trống ở v1; `funding_alert` (AC-LC-09) chỉ test được primary path từ v1.1. Fallback path (`fundingRate × 8760`) có thể test ở v1 | BA / Tech Lead | Open — v1 gap, planned v1.1 |
| Pool Slot0 Cache refresh interval = 60s (provisional) | Configuration | Stale threshold = 120s; giá trị có thể thay đổi sau Phase 0 NV-12 RPC verification | BA / Tech Lead | Open — provisional; confirmed zen 2026-07-20 |
| `safe_mode_tier` column chưa có trong v1 DB | ERD v1 gap | Column `bot_runtime_state.safe_mode_tier` thêm vào v1.1; các scenario phân nhánh theo tier chỉ test được từ v1.1 | BA / Tech Lead | Open — v1 gap |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-30 | QC UC Read Agent | Tạo báo cáo audited lần đầu |
| v2 | 2026-07-03 | QC UC Read Agent | Cập nhật sau khi BA confirm I-01 đến I-12 |
| v3 | 2026-07-06 | QC UC Read Agent | Re-audit: phát hiện v3-I-01 đến v3-I-08 |
| v4 | 2026-07-14 | QC UC Read Agent | Re-audit sau arc-migration; v3-I-01, v3-I-02, v3-I-07, v3-I-08 closed; v3-I-03, v3-I-04, v3-I-06 vẫn pending BA confirm |
| v5 | 2026-07-22 | QC UC Read Agent | Re-audit với câu trả lời mới nhất từ BA responses 2026-07-20. v3-I-03 (funding formula), v3-I-04 (stale threshold 120s), v3-I-06 (lp_value_usd formula) tất cả đã Closed. UC (2026-07-20) đã update tương ứng. Phát hiện v5-I-01 (UC thiếu drift_relative + time_fallback) và v5-I-02 (UC §6 thiếu BR-EXBOT-004 + BR-EXBOT-007 trace). Score tăng từ v4 do các gap cũ đã được đóng. |

---

## 10.3 Audit Summary — Điểm số và kết luận

### Bảng điểm

| Khu vực | Max | Điểm | Ghi chú |
|---|---|---|---|
| **Area 1: Inventory — Functions/Operations, States, Data Objects** | 20 | 19 | Đầy đủ 13 steps, 5 alternate flows, state machine, ERD. Trừ 1 điểm: UC step 9 thiếu drift_relative và time_fallback (v5-I-01) |
| **Area 2: Data/BR/Validations — Fields, Types, Business Rules** | 25 | 23 | 3-way price split rõ ràng; lp_value_usd formula confirmed (OQ-EXBOT-11 closed); stale threshold 120s confirmed (OQ-EXBOT-09 closed); funding formula confirmed (OQ-EXBOT-12 closed). Trừ 2 điểm: UC §6 thiếu BR-EXBOT-004 và BR-EXBOT-007 trace (v5-I-02) |
| **Area 3: Functional Logic — Happy/Alternate/Exception Paths** | 25 | 25 | Tất cả 5 alternate flows rõ ràng; circuit breaker states đầy đủ; SAFE_MODE atomicity confirmed; idempotency đủ rõ. Không có gap mới. |
| **Area 4: Integration — Queue/Cron/External Effects** | 15 | 15 | Fan-out topology rõ ràng (11 queues); hedge-sync/PSAQ/partial_repair routing đúng; next_light_check_at batch update per shard documented. |
| **Area 5: Doc Quality — Clarity, Testability, Traceability** | 15 | 13 | FR Trace bổ sung đầy đủ sau v3-I-01 fix. Trừ 2 điểm: UC step 9 thiếu 2 reasons làm tester không thể thiết kế test case đầy đủ mà không đọc FRD. |
| **TỔNG** | **100** | **95** | |

### Điều kiện auto-fail

- Không có khu vực nào = 0 điểm ✅
- Không có Blocker unresolved ✅

### Verdict: **READY (95/100)**

### Blockers và issues chính

Không có Blocker. Hai issues còn lại ở v5 là Minor:

1. **v5-I-01 (Medium)** — UC step 9 thiếu `drift_relative` và `time_fallback`. Tester cần đọc FRD FR-EXBOT-011 để thiết kế test case đầy đủ. Đề nghị BA bổ sung 2 lý do này vào UC step 9 ở version tiếp theo.

2. **v5-I-02 (Low)** — UC §6 thiếu BR-EXBOT-004 và BR-EXBOT-007 trong trace. Ảnh hưởng traceability, không ảnh hưởng test execution.

### Khuyến nghị cho team

Use case UC-EXBOT-light-check đã đạt mức **sẵn sàng để thiết kế test case**. Các câu trả lời từ BA ngày 2026-07-20 đã giải quyết tất cả 3 câu hỏi còn mở từ audit v4 (lp_value_usd formula, stale threshold 120s, funding formula 7d APR). Tester có thể bắt đầu thiết kế test cases cho 15 AC từ AC-LC-01 đến AC-LC-15, với lưu ý:

- **AC-LC-09** (funding_alert primary path): chỉ test được từ v1.1 sau khi `bnza-market-cron` deploy. Ở v1, test fallback path (`fundingRate × 8760`).
- **drift_relative và time_fallback**: cần đọc FRD FR-EXBOT-011 để biết ngưỡng cụ thể (0.15 và 4h) — pending BA update UC step 9 theo v5-I-01.
- **3-way price split** là điểm dễ mắc lỗi nhất — test case cần verify từng loại giá được dùng đúng metric (uniPoolPrice cho drift, hlMarkPrice cho stop, hlOraclePrice cho margin).

