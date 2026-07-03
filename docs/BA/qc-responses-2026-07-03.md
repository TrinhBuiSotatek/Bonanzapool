---
type: qc-response
module: exbot
status: draft
created: 2026-07-03
updated: 2026-07-03
owner: "@hienduong"
---

# QC Responses — ExBot Module (2026-07-03)

---

## EXBOT on AWS — Architecture Reference

> Context lưu từ 3 diagrams do Lead cung cấp (2026-07-03). Dùng để check "câu hỏi này có bị outdated so với arc mới không" trước khi trả lời QnA.

### Diagram 1 — Target Architecture (tổng quan)

**Entry point:**
- OPERATOR vẫn là Cloudflare Worker, chỉ làm nhiệm vụ create/close bot → API Gateway

**AWS infrastructure (ap-southeast-1 · CloudTrail + Config):**
- API Gateway (HTTP API) → Lambda Authorizer (HMAC token)
- EventBridge (cron 1m / 5m) → Queue (SQS / Redis BullMQ)

**Compute — 2 layer:**
- **AWS Lambda** (event/API): Ingress (start/close) · Queue Consumers (scan · light · hedge · reconcile) · Signing (KMS · nonce)
- **ECS Fargate ×1** (long-running): HL WS Poller + Chain Indexer

**Storage/State:**
- **Aurora PostgreSQL Serverless v2** — advisory lock · state · idempotency
- **ElastiCache Redis** — rate-limit · price cache
- **AWS KMS** — operator + master/agent keys
- **Secrets Manager** — config

**External:**
- Hyperliquid (perp hedge + funding)
- EVM Chains — OP/Arb · vault + logs
- Uniswap V3 — WETH/USDC LP

---

### Diagram 2 — Bot Lifecycle & Event Pipeline

**Queue pipeline (triggered bởi EventBridge):**
EventBridge → bot-scan (enqueue active) → light-check (8 triggers · cached) → [if trigger] → hedge-sync (serial · lock · order) → reconcile (read HL · write)

**Exception routing:**
- stop / margin critical → stop-audit (pre-liquidation)
- → SAFE_MODE (warn/restrict/freeze)

**Data flows:**
- bot-scan + light-check → Aurora PostgreSQL (acquire lock · write state)
- light-check → ElastiCache Redis (read cache — price)
- hedge-sync → Signing Lambda → KMS (sign) → Hyperliquid (place/reduce)
- reconcile → Aurora PostgreSQL (write state)

**Per-bot state machine (high-level):**
IDLE → LP_OPENING → ACTIVE → CLOSING → CLOSED

**Key points:**
- Không còn ExBot Worker monolith — tất cả là Lambda functions
- hedge-sync đảm bảo serial exactly-one-per-bot qua SQS FIFO + Postgres advisory lock
- Signing tách riêng thành Signing Lambda → KMS

---

### Diagram 3 — KMS Custody Signing

**AWS KMS — HSM (secp256k1), 3 loại key:**

| Key | Scope | Signs what |
|-----|-------|-----------|
| Operator key (1 key · role-based) | System-wide | vault executeStrategy (open / rebalance / redeem / collect) → EVM Chains |
| Per-user MASTER key (withdraw authority) | Per user | withdraw3 + HL approveAgent |
| Per-user AGENT key (trade-only) | Per user | HL trades (place / reduce) |

**Signing Lambda** là trung gian duy nhất:
- re-validate · per-wallet nonce lock · kms:Sign only
- Private key **never leaves KMS** — chỉ signing-Lambda IAM role được gọi kms:Sign
- Output: broadcast → EVM Chains (vault executeStrategy) + Hyperliquid (approveAgent · place/reduce)

---

### Cloudflare → AWS Mapping (what replaced what)

| Cloudflare (cũ — trong doc hiện tại) | AWS (mới — arc thực tế) |
|---------------------------------------|------------------------|
| ExBot Worker (monolith) | Lambda: Ingress + Queue Consumers + Signing |
| Redeem Event Watcher | Chain Indexer (ECS Fargate) |
| UserLockDO | Postgres advisory lock + SQS FIFO MsgGroup=botId |
| MarketDataDO / HlMarkDO | ElastiCache Redis (rate-limit · price cache) |
| D1 database | Aurora PostgreSQL Serverless v2 |
| Cloudflare Queues | SQS / Redis BullMQ |
| Cloudflare Cron | EventBridge Scheduler (cron 1m / 5m) |
| Cloudflare Secrets Store | AWS Secrets Manager + KMS |

### Rule check: câu hỏi có bị outdated không?

- Câu hỏi về **business logic** (state machine, SLA, business rules, idempotency behavior): **không bị outdated** — arc thay đổi infra, không thay đổi behavior
- Câu hỏi đề cập **tên component cụ thể** (Worker, UserLockDO, D1, MarketDataDO, Redeem Event Watcher): **bị outdated** — cần map sang tên AWS tương đương
- Câu hỏi về **cơ chế locking / serialization**: UserLockDO → Postgres advisory lock + SQS FIFO
- Câu hỏi về **price/market data cache**: MarketDataDO → ElastiCache Redis

---

> Câu trả lời cho các câu hỏi QC audit ngày 2026-07-03.
> Source: `UC-EXBOT-monitor-status` và `UC-EXBOT-pause-resume`

---

## UC-EXBOT-monitor-status

| ID | Priority | Ref | Question | Why It Matters | Status | Ans |
| --- | --- | --- | --- | --- | --- | --- |
| I-001 | H | UC §A3 vs `srs/states.md` (note 2026-06-18) + SRS FR-EXBOT-070 | UC Alternate Flow A3 mô tả `lifecycle_state='cooldown'` và message "USDC parked. Re-entry will be attempted automatically." Tuy nhiên cả hai đã bị loại bỏ trong HLD 2026-06-18 (`cooldown` và `parked` states đã bị xóa; vòng lặp park/re-entry đã bị bỏ). Sau `bot_safe_close`, system chuyển thẳng sang `closed`. Message đúng theo SRS FR-EXBOT-070/073 là "Bot safely closed. Funds have been returned to your wallet." BA vui lòng viết lại A3 để mô tả behavior khi `lifecycle_state='closed'` sau `bot_safe_close`, thay thế state reference và message text cho đúng. | Tester sẽ thiết kế test case cho một lifecycle state không tồn tại và một message đã bị retire. Test execution sẽ luôn fail vì hệ thống không bao giờ vào `lifecycle_state='cooldown'`. Đây là Blocker — làm cho UC không sẵn sàng cho test design. | Open | A3 đã được viết lại — `cooldown` removed. Thay bằng 2 cases:`lp_closing`: "Bot close is in progress. Please wait." (E-EXBOT-021)`closed`: "Bot safely closed. Funds have been returned to your wallet." (E-EXBOT-022) |
| I-002 | H | UC §1 Actors vs FRD §4.11 FR-EXBOT-100 | UC định nghĩa primary actor là "USDC Investor (read-only)". FRD §4.11 FR-EXBOT-100 liệt kê Actor cho `GET /api/exbot/status` là "Admin". US-EXBOT-002 xác nhận rõ đây là use case của Investor. Hai tài liệu có thẩm quyền mâu thuẫn nhau về việc ai gọi endpoint này. BA vui lòng xác nhận actor đúng cho `GET /api/exbot/status`: chỉ Investor, chỉ Admin, hay cả hai? Nếu cả hai, cần xác định cơ chế xác thực cho từng actor và liệu response có khác nhau theo role không. | Các test case xác thực phụ thuộc vào điều này: POOL UI xác thực là Investor (SIWE / user JWT) hay Admin (admin session)? Nếu cả hai có thể gọi endpoint, các auth paths và authorization rules của response là khác nhau và cần test riêng. | Open | Actor đúng là **cả Investor lẫn Admin**. Auth mechanism: `X-Wallet-Address` header qua `accessControl` middleware. Admin bypass wallet ownership check; Investor phải match `bot.user_wallet_address` (403 nếu không match). Response schema giống nhau cho cả hai — không có role-based response difference. UC §1 Actors cần update thêm Admin. |
| I-003 | H | UC §3 step 3 và step 6 vs SRS ERD bảng `bot_runtime_state` + SRS FR-EXBOT-021 | UC step 6 tính drift % nhưng chỉ liệt kê một trong hai giá trị đầu vào cần thiết ở step 3. Cụ thể: `last_known_hl_short_size` đã có trong danh sách D1 reads, nhưng `target_short_size` — giá trị còn lại để tính drift — **hoàn toàn không được đề cập**. Theo SRS ERD, bảng `bot_runtime_state` có cột `target_short_size`. Tuy nhiên SRS FR-EXBOT-021 định nghĩa `targetShortEth = lpEthAmount × hedgeRatio` — tức là giá trị này được *tính lại* từ công thức, không phải đọc thẳng từ D1. Chưa rõ: Worker đọc `bot_runtime_state.target_short_size` đã lưu sẵn, hay tính lại từ `lpEthAmount × hedgeRatio` (cần thêm `lp_eth_amount` và `hedge_legs.target_ratio` vào danh sách reads). Ngoài ra, nếu giá trị mẫu số bằng 0, phép tính sẽ chia cho 0 — UC không định nghĩa hệ thống xử lý trường hợp này như thế nào. BA hoặc Tech Lead vui lòng xác nhận: (a) nguồn dữ liệu chính xác cho `targetShortEth` trong status response là gì; (b) bổ sung vào danh sách D1 reads ở UC step 3; (c) định nghĩa hành vi khi giá trị mẫu số bằng 0. | Nếu Worker dùng sai nguồn hoặc giá trị không cập nhật, drift % trên màn hình sẽ hiển thị sai — nhà đầu tư thấy thông tin lệch so với thực tế. Tester không biết phải kiểm tra giá trị nào là đúng để viết assertion, và không thể thiết kế test case cho trường hợp chia cho 0. | Open | **Cần anh em dev hỗ trợ câu này.** |
| I-004 | H | UC §3 step 3 vs UC §3 step 9 vs SRS ERD `bots` + `bot_runtime_state` | `bots.next_light_check_at` = thời điểm light-check **tiếp theo** được lên lịch (tương lai). `bot_runtime_state.last_light_check_at` = thời điểm light-check lần **cuối** đã hoàn tất (quá khứ). Đây là hai fields khác nhau. UC step 3 đọc `next_light_check_at` (tương lai) nhưng step 9 gắn nhãn hiển thị là "Last light-check timestamp" (quá khứ) — mâu thuẫn trực tiếp. Cả hai cột đều tồn tại trong ERD (xác nhận qua `srs/erd.md`). BA vui lòng xác nhận: status response nên bao gồm timestamp nào — lần check đã hoàn tất (`bot_runtime_state.last_light_check_at`) hay lần check tiếp theo được lên lịch (`bots.next_light_check_at`)? Cập nhật step 3 đọc đúng field và step 9 gắn nhãn chính xác. | Test assertion không thể viết được: giá trị timestamp hiển thị là lần check đã qua hay lần tiếp theo? Hai giá trị này có thể chênh nhau 5+ phút (FR-EXBOT-013: `next_light_check_at = now + 5min + jitter`). | Open | Đã fix — step 3 đọc `bot_runtime_state.last_light_check_at` (quá khứ, lần check đã hoàn tất). Bỏ `bots.next_light_check_at` (tương lai). Label "Last light-check timestamp" ở step 9 giữ nguyên — đã đúng. |
| I-005 | H | UC §4 Alternate Flows vs `srs/states.md` State Registry (15 active states) | UC chỉ mô tả status response cho 3 lifecycle states (active, safe_mode, hedge_stopped_cooldown) trong số 15 states được định nghĩa trong `states.md`. Các states còn thiếu: `lp_rebalancing` (đang rebalance LP range, light-check bị skip), `lp_closing` (close operation đang chạy), `error` (cần admin can thiệp), và `closed` (bot đã đóng hoàn toàn nhưng status endpoint vẫn được gọi). UC dùng 404 cho "no active bot" (A4) nhưng không định nghĩa `closed` bot trả về 404 hay response JSON có `lifecycle_state='closed'`. BA vui lòng thêm alternate flows cho các lifecycle states còn thiếu, hoặc xác nhận rõ: "status endpoint luôn trả về cùng field set cho mọi lifecycle state, với `lifecycle_state` value xác định state hiện tại, và mọi mutation buttons trên POOL UI đều bị disabled cho non-active states." | Test cases cho bots trong trạng thái `lp_rebalancing`, `lp_closing`, `error`, và `closed` không thể thiết kế được. Edge case: investor check status ngay sau bot_safe_close trong khi `lifecycle_state='lp_closing'` — expected response không xác định. | Open | Step 9: bỏ "Cooldown" label, thêm đủ tất cả states. A3a/A3b: giữ nguyên, bỏ note "after bot_safe_close" vì lp_closing/closed có thể từ user_redeem cũng như bot_safe_close. **A6 mới**: `lp_rebalancing` — rebalancing in progress, buttons disabled. **A7 mới**: `error` — admin intervention required, chỉ enable Close Bot emergency. A4: clarify rõ `closed` ≠ 404, 404 chỉ khi không có bot record |
| I-006 | H | UC §3 steps 7–8 vs SRS FR-EXBOT-090 | Không có JSON response schema HTTP 200 nào được định nghĩa trong UC, SRS, hay FRD. Các derived fields (`rangeState`, `drift_pct`) được tính bởi ExBot Worker nhưng JSON key names không được chỉ định. Chưa rõ: `lifecycle_state` và `status` có đều được trả về không; key name cho `last_known_hl_short_size` trong response là gì; các computed và raw fields có cùng tên với D1 columns không. BA hoặc Tech Lead vui lòng định nghĩa đầy đủ JSON response schema cho `GET /api/exbot/status` HTTP 200: tất cả field names, types, optionality, và null-handling rules. | Test không thể assert field names của response. API-level integration test sẽ phải đoán field names. UC không thể test được ở cấp độ API contract nếu không có schema. | Open | `{ "tick_lower": "number \| null", "tick_upper": "number \| null", "current_tick": "number \| null", "range_state": "\"in\" \| \"out\" \| null", "actual_short_eth": "string \| null", "target_short_eth": "string \| null", "drift_pct": "number \| null", "margin_status": "\"ok\" \| \"warning\" \| \"critical\" \| null", "last_light_check_at": "string \| null", "safe_mode_reason": "string \| null", "cooldown_end_at": "string \| null" }` |
| I-009 | M | UC §A4 vs `02_backbone/message-list.md` EXBOT section | Alternate Flow A4 (no active bot for user) trả về HTTP 404 với POOL UI hiển thị "No active bot" empty state. Không có E-EXBOT-* error code nào được đăng ký trong `message-list.md` cho trường hợp 404 này. Tất cả các ExBot error cases khác đều có E-EXBOT codes đã đăng ký (E-EXBOT-001 đến E-EXBOT-016). BA vui lòng đăng ký một E-EXBOT code cho "no active bot / user has no running ExBot" trong `message-list.md`, và bao gồm code này trong mô tả UC A4. | Test không thể verify nội dung API-level error response body cho 404 (ví dụ: có `code` hay `message` field không, và giá trị của chúng là gì?). | Open | E-EXBOT-023 đã đăng ký trong message-list.md và A4 đã reference code. |
| I-010 | M | UC §A5 vs `02_backbone/message-list.md` EXBOT section | Alternate Flow A5 (Operator Facade unavailable) trả về HTTP 503 với message "Status service temporarily unavailable". Message này không được đăng ký trong `message-list.md`. BA vui lòng đăng ký message này dưới dạng E-EXBOT code trong `message-list.md`, hoặc xác nhận đây là generic Cloudflare / OPERATOR-level response không cần đăng ký. | Test không thể verify nội dung message text chính xác của 503 response. | Open | UC A5: "503 là Cloudflare/infra-level response, không phải application error." Không cần E-EXBOT code. Tester verify HTTP 503 status code, không cần verify message body. |
| I-011 | M | UC §2 Preconditions, §3 step 2 vs SRS FR-EXBOT-090 | Cơ chế xác thực không được chỉ định trong UC: (a) POOL UI xác thực Investor với Operator Facade bằng cơ chế gì (SIWE JWT? API key? Session token?)? (b) "Internal auth token" giữa Operator Facade và ExBot Worker là gì, và ExBot Worker validate nó như thế nào? BA vui lòng tài liệu hóa cơ chế xác thực cho cả hai segment: POOL UI → Facade và Facade → ExBot Worker. | Các test case authentication-path (valid auth, expired auth, missing auth header) không thể thiết kế được khi không biết cơ chế auth. | Open | **Đoạn 1 (POOL UI → Operator Facade):** `X-Wallet-Address` header. Thiếu header → 401. Địa chỉ bị block → 403. Không trong whitelist (khi `access_mode=whitelist`) → 403. Admin wallet bypass whitelist check. **Đoạn 2 (Operator Facade → ExBot Worker):** `X-Exbot-Internal-Auth` header với shared secret từ env var `EXBOT_INTERNAL_AUTH_TOKEN`. Thiếu hoặc sai → 401 `UNAUTHORIZED_INTERNAL_CALL` |
| I-013 | M | UC §3 step 4 vs SRS FR-EXBOT-093 | UC step 4 nêu ExBot Worker query `currentTick` từ `MarketDataDO`. SRS FR-EXBOT-093 ghi nhận cache TTL của `MarketDataDO` được xác định bởi kết quả Phase 0 NV-12 (OQ-EXBOT-09 — Open). Nếu DO cache bị stale quá 2× refresh interval, DO sẽ thực hiện forced refresh. UC không mô tả behavior của status endpoint khi MarketDataDO unavailable hoặc trả về giá trị stale. BA hoặc Tech Lead vui lòng tài liệu hóa fallback behavior cho status endpoint khi `MarketDataDO` unavailable hoặc cache TTL đã hết hạn (ví dụ: trả về last-known value với staleness flag, trả về null cho `currentTick`, hay block và retry). | Test scenario: MarketDataDO đang forced refresh khi status được gọi — `currentTick` là null, stale, hay call bị block? Response behavior trong trường hợp này không xác định. | Open | Khi MarketDataDO unavailable hoặc stale: `current_tick: null`, `range_state: null` — response vẫn trả về 200 với các fields còn lại bình thường. Không block, không retry, không 503. UI hiển thị "—" cho range state indicator. Behavior này consistent với null-handling rules của status endpoint (display-only, không trigger action). |

---

## UC-EXBOT-pause-resume

| ID | Priority | Ref | Question | Why It Matters | Status | Ans |
| --- | --- | --- | --- | --- | --- | --- |
| Q2 | Blocker | FR-EXBOT-010; UC §1, §3 | **"Status Update Worker" không tồn tại trong queue topology.** FR-EXBOT-010 định nghĩa đúng 11 queues. UC gọi worker xử lý pause/resume là "Status update worker" nhưng worker này không được ánh xạ vào queue nào trong SRS. Nó có phải là phần của ExBot Worker (xử lý trực tiếp API request mà không qua queue), hay là một queue consumer chưa được định nghĩa? Tech Lead vui lòng xác nhận kiến trúc worker: ExBot Worker xử lý pause/resume đồng bộ (không queue), hay cần một queue riêng (tên gì)? | Tester không biết worker xử lý pause/resume hoạt động như thế nào → không thể test idempotency, retry behavior | Open | "Status Update Worker" không phải là một worker riêng biệt. Pause/resume được xử lý trực tiếp bởi ExBot Worker dưới dạng synchronous HTTP POST handler (`/pause`, `/resume`). Không có queue consumer nào liên quan. Tên "Status Update Worker" trong UC sẽ được chuẩn hóa thành "ExBot Worker" cho rõ ràng. |
| Q3 | Major | FR-EXBOT-011; UC §3–5; SRS spec.md §FR-EXBOT-011 | **Không có idempotency mechanism cho pause/resume.** FR-EXBOT-011 bắt buộc mọi queue consumer phải insert `message_id` vào `queue_idempotency` table. UC §5 A3 mô tả idempotent response nhưng không nêu cơ chế implement. Tech Lead vui lòng xác nhận: (1) pause/resume có qua queue không? (2) nếu có, idempotency key là gì? (3) nếu không qua queue, cơ chế chống race condition là gì? | Không có idempotency → không thể test race condition scenarios | Open | Pause/resume không qua queue — là synchronous HTTP handler, FR-EXBOT-011 không áp dụng. Race condition được ngăn bởi DB conditional UPDATE (`WHERE status='active'` cho pause, `WHERE status='paused'` cho resume) — chỉ 1 request thắng, request còn lại nhận idempotent response (A2/A3). UC sẽ bổ sung note này. |
| Q7 | Major | UC §2, §4; SRS states.md | **Valid `lifecycle_state` values cho pause/resume không được định nghĩa rõ ràng.** UC §2 pause precondition chỉ nêu `lifecycle_state='active'` được pause. Tuy nhiên states.md state registry row `(pre-pause value) \| paused` ngụ ý mọi giá trị `lifecycle_state` đều có thể pause (không chỉ `'active'`). BA vui lòng chốt: những giá trị `lifecycle_state` nào được phép pause/resume? Chỉ `'active'` hay `'hedge_stopped_cooldown'` và `'lp_rebalancing'` cũng được? | Tester không biết valid/invalid pause/resume scenarios theo lifecycle_state | Open | BA chốt: chỉ `lifecycle_state='active'` được phép pause. `hedge_stopped_cooldown` và `lp_rebalancing` không được pause — 2 state này đang trong quá trình xử lý tự động, pause vào giữa tạo edge case không xác định (cooldown timer, rebalance dở). states.md đã cập nhật. |
| Q8 | Major | UC §3–5; SRS spec.md §6 | **"UI confirmation" gây nhầm lẫn scope giữa ExBot và POOL UI.** spec.md §6 khẳng định ExBot là backend-only module, không sở hữu UI. UC nói "Investor receives UI confirmation" nhưng ExBot không có màn hình. BA vui lòng xác nhận: "UI confirmation" nằm trong ExBot scope hay POOL UI (PTL-05)? Nếu ExBot scope dừng ở API response, tester chỉ verify API response — không cần test POOL UI rendering. | Tester không biết test scope — chỉ API hay cả UI rendering | Open | ExBot scope dừng ở API response: `{status: "paused/active", message: "..."}`. Phần "Investor receives UI confirmation" thuộc POOL UI (PTL-05) — nằm ngoài ExBot scope. Tester chỉ cần verify API response, không cần test POOL UI rendering. UC sẽ được sửa để tách rõ boundary. |
| Q9 | Major | UC §3 step 7, §4 step 6; UC §5 A2, A3; message-list.md | **Success messages không có message code để trace.** UC §3 step 7 trả về message nhưng không có mã E-code. message-list.md chỉ có E-EXBOT-* error codes. BA vui lòng xác nhận: (1) success messages có cần đăng ký message code không? (2) nếu có, mã là gì? (3) nếu không, tester verify text content của response? | Không có message code → khó trace API contract trong test | Open | Success messages đã được đăng ký: **MSG-SUC-81** (pause): "Bot paused. Hedge and LP are maintained." — **MSG-SUC-82** (resume): "Bot resumed. Monitoring will resume shortly." Đăng ký trong `message-list.md` §MSG-EXBOT. Tester verify theo message code. |

---

## UC-EXBOT-user-redeem

| ID | Priority | Ref | Question | Why It Matters | Status | Ans |
| --- | --- | --- | --- | --- | --- | --- |
| I-01 | High | UC §7 FR Trace vs frd.md; US-EXBOT-009 Trace | UC §7 FR Trace liệt kê "FR-EXBOT-070, FR-EXBOT-071". FR-EXBOT-070 tồn tại trong frd.md (§4.8) và mô tả cả hai close systems. **FR-EXBOT-071 không tồn tại trong frd.md** — sau FR-EXBOT-070 nhảy thẳng đến FR-EXBOT-080; không có định nghĩa nào cho FR-EXBOT-071 trong toàn bộ tài liệu. Phân tích bổ sung: US-EXBOT-009 (`bot_safe_close`) cũng cite "FR-EXBOT-070, FR-EXBOT-071" trong phần Trace, gợi ý FR-EXBOT-071 có thể là FR dự kiến tách riêng chi tiết `bot_safe_close` (RedemptionQueue mechanics, fulfillRequest flow) ra khỏi FR-EXBOT-070, nhưng **chưa được viết**. Câu hỏi cần BA xác nhận: (a) FR-EXBOT-071 có phải là FR bị thiếu cần tạo mới (nếu vậy nội dung sẽ là gì)? hay (b) đây là lỗi copy-paste từ US-009 sang UC user-redeem (FR Trace của UC user-redeem chỉ nên cite FR-EXBOT-070 mục A)? | FR-EXBOT-071 được cite trong UC như một yêu cầu của user_redeem. Nếu FR này chưa được viết, coverage UC bị thiếu. Nếu là lỗi copy-paste, FR Trace của UC cần sửa để tránh tester trace nhầm test case vào FR của bot_safe_close. | Open | FR-EXBOT-071 does not exist in frd.md. Citation error — FR-071 belongs to `uc-bot-safe-close`, not in scope of user-redeem. UC §7 FR Trace updated — only `FR-EXBOT-070` retained. |
| I-02 | High | uc-user-redeem.md §3 step 12-14; flows.md F-04 | UC mô tả Worker "gửi HL-portion USDC về nhà đầu tư qua RedemptionQueue ledger" nhưng không định nghĩa: (a) HL-portion được tính như thế nào (tổng số tiền từ HL closing position minus fees? minus funding?); (b) ai thực sự là người thực hiện on-chain transfer USDC (Worker gọi trực tiếp hay qua Operator Facade?); (c) transaction hash của HL-portion transfer có được lưu vào `close_operations.hedge_close_tx` không? | Không có công thức hoặc mô tả source of truth cho HL-portion amount → tester không thể verify số tiền nhà đầu tư nhận đúng không. | Open | Outdated vs AWS arc — HL-portion transfer mechanism changed. Pending Tech Lead for updated flow details. |
| I-03 | Medium | uc-user-redeem.md §3 step 8; spec.md FR-EXBOT-026; flows.md F-04 | UC step 8 xác nhận Redeem Worker có acquire `UserLockDO` lease — vấn đề không phải là "có lock hay không". Sau khi cross-check tài liệu, câu hỏi được thu hẹp còn 2 điểm chưa rõ: **(a) Behavior khi acquired=false:** UC step 8 chỉ ghi "acquires UserLockDO lease" nhưng không mô tả behavior khi lock đang bị giữ bởi hedge-sync worker. spec.md FR-EXBOT-026 định nghĩa pattern cho hedge-sync: `acquired=false → re-queue với delay`. User_redeem có dùng cùng pattern không, hay chờ spin-wait, hay fail ngay? Với user_redeem có SLA 5 phút, re-queue với delay có thể vi phạm SLA. **(b) flows.md F-04 không hiển thị UserLockDO:** Sequence diagram F-04 không có participant UserLockDO (trong khi F-02 hedge-sync hiển thị rõ). Đây là lỗi thiếu trong diagram hay user_redeem dùng cơ chế khác? | Behavior khi lock contention xảy ra ảnh hưởng trực tiếp đến test case SLA. | Open | Outdated vs AWS arc — UserLockDO replaced by Postgres advisory lock + SQS FIFO. Lock behavior details pending Tech Lead confirmation under new arc. |
| I-04 | High | uc-user-redeem.md §3 step 7; flows.md F-04 line 162; states.md close_operations table; spec.md FR-EXBOT-073 | Có conflict về initial state khi Worker tạo `close_operations` row. **UC step 7 và flows.md F-04** cùng ghi: `create close_operations (kind=user_redeem, state=lp_closed→funds_returned)` — dùng mũi tên (`→`) trong một field TEXT, không hợp lệ về mặt data model (ERD định nghĩa `close_operations.state` là `TEXT`, không thể lưu hai giá trị). **states.md** liệt kê sequence đầy đủ cho user_redeem: `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done` — trong đó `requested` là state đầu tiên (✓). **spec.md FR-EXBOT-073** mô tả bot_safe_close bắt đầu ở `requested` rõ ràng, nhưng không có spec tương đương cho user_redeem. Câu hỏi: (a) Khi Worker tạo `close_operations` row ở step 7, initial state là `'requested'` (như bot_safe_close) hay `'funds_returned'` (vì LP-portion đã về user rồi)? (b) UC/flows notation `lp_closed→funds_returned` là lỗi notation hay worker thực sự bỏ qua state `requested` và `lp_closed` trong user_redeem path? (c) Nếu skip `requested`, tester không thể viết test case verify state transition `requested → lp_closed`. | Initial state xác định expected result của test case verify `close_operations` record được tạo đúng. | Open | (a) Initial state = `requested`. (b) `lp_closed→funds_returned` is a notation error — Worker inserts row at `requested`, then immediately updates to `lp_closed` then `funds_returned` (on-chain guarantee from step 2-3). No states skipped. (c) Full transition `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done` is testable. UC doc updated. |
| I-05 | Medium | uc-user-redeem.md §4 A2; flows.md F-04; message-list.md | Khi hedge close thất bại hoàn toàn và `close_operations.state='residual_hl_liability'`, UC A2 và flows.md F-04 đều nói "admin notified with amount" nhưng không cite message code. `message-list.md` chỉ có `E-EXBOT-010` cho SLA breach, không có message nào cho hedge close failure hoàn toàn. BA vui lòng cung cấp message code và nội dung verbatim của admin notification cho trường hợp này. | Tester không thể verify expected result của admin notification trong test case A2 nếu không có message code và nội dung chính xác. | Open | Registered **E-EXBOT-024**: "User redemption hedge close failed. Manual intervention required." — internal admin alert. UC A2 updated to cite E-EXBOT-024. |
| I-06 | Medium | uc-user-redeem.md §4 A2; states.md | Khi `close_operations.state = 'residual_hl_liability'` (A2 flow), `bots.lifecycle_state` và `bots.status` chuyển sang giá trị gì? UC §5 Postconditions (phần đầu) mô tả happy path. §5 không mô tả postconditions cho A2. states.md không có state `residual_hl_liability` trong `bots.lifecycle_state` enum. | Tester không biết bot ở trạng thái nào sau A2 — không thể verify state transition của `bots` table. | Open | A2 → `bots.lifecycle_state='error'`, `bots.status='error'`. LP already returned (on-chain, not reversed). Admin must manually close residual HL position. UC §5 updated with A2 postconditions. |
| I-08 | Medium | uc-user-redeem.md §3 step 11; flows.md F-04 | Sau bước reconcile (verify HL position = 0), nếu reconcile thất bại (HL position ≠ 0 sau closeShortReduceOnlyIoc), UC không mô tả behavior. Trong hedge-sync, reconcile mismatch → SAFE_MODE. Trong user_redeem context (LP đã thanh lý), SAFE_MODE có được áp dụng không? | Không có expected behavior cho reconcile failure trong user_redeem → tester không thiết kế được test case cho trường hợp này. | Open | Reconcile failure in user_redeem = same outcome as A2: `residual_hl_liability` → `bots.lifecycle_state='error'` → admin notified (E-EXBOT-024). SAFE_MODE does NOT apply — LP already liquidated, nothing to protect. UC A2 updated to cover both hedge close failure and reconcile mismatch. |
| I-09 | Medium | uc-user-redeem.md §5 (Postconditions) | UC có hai phần Postconditions: phần đầu (§5 chính thức) và một phần không có header §5 lặp lại ở phía dưới. Hai phần này có nội dung khác nhau về `lifecycle_state` sau khi hoàn tất. Đây là lỗi cấu trúc tài liệu. | Gây nhầm lẫn cho tester về expected postcondition. BA cần merge hoặc xóa một phần. | Open | Duplicate Postconditions section removed. The boilerplate section (referencing D1, NFR-ADM-005) was stale and conflicted with §5. §5 is now the single source of truth with happy path and A2 postconditions. |
| I-10 | Medium | flows.md F-05 vs uc-user-redeem.md | flows.md F-05 (bot_safe_close) vẫn hiển thị luồng cũ với `OperatorFacade → ExBotWorker → RedemptionQueue → Operator fulfillRequest` (hedge-first qua API, không phải qua on-chain event watcher). Tuy nhiên HLD 2026-06-18 ghi nhận "drop park/re-entry" và frd.md FR-EXBOT-070(B) mô tả bot_safe_close khác. F-05 có thể đã outdated sau HLD decision. | Nếu tester đọc F-05 để so sánh hai close systems, họ sẽ hiểu sai bot_safe_close. | Open | Outdated vs AWS arc — F-05 will be rewritten during arc migration. Logic issue (missing hedge-first step) will also be corrected in the same pass. |
| I-11 | Low | uc-user-redeem.md §3 step 9; flows.md F-04; frd.md FR-EXBOT-022 | UC step 9 gọi `closeShortReduceOnlyIoc` với `cloid` nhưng không mô tả behavior khi HL từ chối lệnh (ví dụ: lệnh bị reject vì lý do không xác định, partial fill, hay HL API timeout). BA vui lòng xác nhận: khi `closeShortReduceOnlyIoc` bị HL reject, Worker retry bao nhiêu lần trước khi chuyển sang `residual_hl_liability`? | Ảnh hưởng test case cho edge case HL reject close order — tester cần biết retry count để thiết kế đúng expected behavior. | Open | `closeShortReduceOnlyIoc` retries up to 3 times on HL reject/timeout. After 3 failed attempts, `close_operations.state='residual_hl_liability'`, `bots.lifecycle_state='error'`, admin notified (E-EXBOT-024). Retry count aligned with bot_safe_close. UC step 9 and A2 updated. |
