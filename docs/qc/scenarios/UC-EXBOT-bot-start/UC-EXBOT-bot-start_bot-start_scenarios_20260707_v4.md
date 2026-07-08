# Test Scenarios — UC-EXBOT-bot-start: Start ExBot

**Tiêu đề:** UC-EXBOT-bot-start — Start ExBot — Test Scenarios
**Ngày tạo:** 2026-07-07
**Tác giả:** QC Scenario Design Agent (qc-func-scenario-design-exbot)
**Phiên bản:** v4

> Source: docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260707_v4.md
> Generated: 2026-07-07
> Domain/Architecture: ExBot Lambda (AWS) — Aurora PostgreSQL, AWS KMS, SQS queue, Hyperliquid API, BnzaExVault (on-chain Solidity contract)

> **Lưu ý:** UC này có Verdict **NOT READY (58/100)** tại thời điểm tạo scenarios do IS-01 (Blocker: conflict A7/A10 `error` vs `safe_mode`). Scenarios cho A7/A10 được đưa vào Out-of-Scope Flags. Các phần còn lại được thiết kế từ nội dung đã rõ và đầy đủ trong audited v4.

---

## Bảng mã viết tắt

| Code / Prefix | Ý nghĩa + vai trò trong dự án | Định nghĩa tại |
|---|---|---|
| UC-EXBOT-* | Use Case ID cho ExBot module — định danh duy nhất của từng luồng nghiệp vụ ExBot | path-registry.md |
| FR-EXBOT-* | Functional Requirement — yêu cầu chức năng chi tiết của ExBot, được đánh số theo spec.md | srs/spec.md |
| BR-EXBOT-* | Business Rule — quy tắc nghiệp vụ áp dụng cho ExBot | srs/spec.md, common-rules.md |
| E-EXBOT-* | Error message code — mã lỗi chuẩn của ExBot, kèm message text verbatim | srs/spec.md §5 |
| IS-* | Issue — vấn đề hoặc mâu thuẫn được phát hiện trong quá trình audit UC | uc-review-report v4 §10 |
| OQ-EXBOT-* | Open Question — câu hỏi còn mở, chưa có câu trả lời từ BA/zen | uc-review-report §1.3 |
| HL | Hyperliquid — sàn giao dịch perpetual futures, nơi ExBot mở vị thế short hedge | industry term |
| IOC | Immediate-Or-Cancel — loại lệnh giao dịch: khớp ngay nếu có, hủy phần còn lại; dùng cho lệnh short hedge | industry term |
| KMS | AWS Key Management Service — dịch vụ quản lý khóa mã hóa, lưu trữ agent key của bot trong HSM | AWS product |
| DO | Durable Object — Cloudflare primitive cung cấp state có nhất quán mạnh; dùng cho HLRateLimitDO, UserLockDO, MarketDataDO | Cloudflare product |
| SQS | Amazon Simple Queue Service — hàng đợi tin nhắn; dùng cho key-provision queue | AWS product |
| LP | Liquidity Provider / Liquidity Position — vị thế cung cấp thanh khoản trên Uniswap V3; ExBot tạo LP NFT qua BnzaExVault | industry term |
| cloid | Client Order ID — mã lệnh phía client, deterministic theo `keccak256("bnza:{botId}:{attemptId}:{stage}:{version}")`; đảm bảo idempotency khi gửi lại lệnh | srs/spec.md FR-EXBOT-024 |
| INV-STOP | Invariant STOP — bất biến hệ thống: khi HL short non-zero, phải luôn tồn tại verified reduce-only stop | project-context-master.md §7.1 |
| BigDecimal | Kiểu số thập phân chính xác cao — bắt buộc cho mọi tính toán tài chính trong ExBot; cấm dùng float/Number() | srs/spec.md NFR-EXBOT-008 |

---

## UC-EXBOT-bot-start — Start ExBot

### Sub-flow F-03a: Auto Key-Provision on Deposit

---

### Scenario ID: TS_UC-EXBOT-bot-start_001
**Scenario Title:** Key-provision hoàn tất thành công sau khi on-chain deposit được phát hiện
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-080, UC §6.1 F-03a step 1–6
**Test Type:** Functional
**Description:** Sau khi Chain Indexer phát hiện sự kiện nạp tiền on-chain của người dùng và enqueue message `{userId, depositAmount, txHash}` vào key-provision SQS, Key-Provision Worker thực hiện tuần tự: tạo master key qua KMS GenerateKeyPair, tạo agent key qua KMS GenerateKeyPair, gọi HL `approveAgent`, sau đó INSERT bản ghi vào `hl_agent_keys` với `key_status='active'`. Kết quả cuối: một row `hl_agent_keys` tồn tại với `key_status='active'` cho userId đó; không có raw private key material trong DB.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_002
**Scenario Title:** Chỉ tồn tại một row `key_status='active'` per user tại mọi thời điểm (BR-EXBOT-012)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** BR-EXBOT-012, FR-EXBOT-080, UC §6.1 F-03a §B
**Test Type:** Data/State
**Description:** Trong bất kỳ trạng thái nào của hệ thống (sau key-provision, sau key rotation), khi kiểm tra bảng `hl_agent_keys` cho một `user_id` bất kỳ, chỉ có đúng một row với `key_status='active'`. DB-level UNIQUE constraint phải ngăn chặn trường hợp có hai row `active` cùng tồn tại cho cùng một user. Nếu key rotation đang diễn ra, hệ thống phải thực hiện nguyên tử: old row chuyển sang `superseded` và new row chuyển sang `active` trong cùng một transaction — không có window nào mà cả hai đều `active` hoặc không có row nào `active`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_003
**Scenario Title:** KMS GenerateKeyPair thất bại — retry với exponential backoff, tối đa 3 lần
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-080, UC §6.1 F-03a step 2–3
**Test Type:** Functional
**Description:** Khi KMS trả về `ThrottlingException` hoặc không khả dụng tại bước GenerateKeyPair (master key hoặc agent key), Key-Provision Worker thực hiện retry với exponential backoff. Sau tối đa 3 lần thất bại liên tiếp, hệ thống gửi admin alert; `key_status` không được set thành `active`; không tạo row `hl_agent_keys` với `active` status.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_004
**Scenario Title:** HL `approveAgent` thất bại — retry qua key-provision queue, admin alert khi vượt SLA
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-080, UC §6.1 F-03a step 5
**Test Type:** Functional
**Description:** Khi HL từ chối hoặc không phản hồi lệnh `approveAgent(hl_user_address, agent_address)`, Key-Provision Worker không được set `key_status='active'`; thay vào đó, message được đưa vào retry queue. Nếu tổng thời gian thử lại vượt SLA, hệ thống gửi admin alert. `key_status` phải giữ trạng thái không phải `active` cho đến khi HL xác nhận.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_005
**Scenario Title:** Redelivery cùng key-provision message không tạo duplicate row `hl_agent_keys`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-011, NFR-EXBOT-007, UC §6.1 F-03a §B
**Test Type:** Data/State
**Description:** Khi SQS tái phân phối cùng một key-provision message (cùng `message_id`) cho Key-Provision Worker, worker phát hiện `message_id` đã tồn tại trong `queue_idempotency` với `state='started'` hoặc `state='succeeded'`, và return ngay lập tức mà không tạo thêm row `hl_agent_keys`. Sau khi xử lý, tổng số row `hl_agent_keys` cho user này không tăng thêm so với trước khi redelivery xảy ra.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_006
**Scenario Title:** Private key không bao giờ rời KMS HSM — không có raw key trong DB, log, memory
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** NFR-EXBOT-006, FR-EXBOT-080, UC §6.1 F-03a §B, AC-08
**Test Type:** Functional
**Description:** Sau khi key-provision hoàn tất, kiểm tra bảng `hl_agent_keys` chỉ chứa `hl_user_address` và `agent_address` (public key dạng địa chỉ ví) — không có trường nào chứa raw private key material, private key bytes, hoặc encrypted private key. Log hệ thống trong quá trình provisioning không expose bất kỳ private key material nào.
**Test Focus:** Error/Exception

---

### Sub-flow F-03b: User-Triggered Bot Start — Preflight

---

### Scenario ID: TS_UC-EXBOT-bot-start_007
**Scenario Title:** One-bot policy — từ chối start khi user đang có bot ở trạng thái `active`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, UC §6.2 F-03b step 2a, AC-02
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đã có một bot với `status='active'` trong `bot_registry`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không có bot record mới nào được tạo trong DB.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_008
**Scenario Title:** One-bot policy — từ chối start khi user đang có bot ở trạng thái `paused`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, UC §6.2 F-03b step 2a
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='paused'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_009
**Scenario Title:** One-bot policy — từ chối start khi user có bot ở trạng thái `closing`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, UC §6.2 F-03b step 2a
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='closing'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_010
**Scenario Title:** One-bot policy — từ chối start khi user có bot ở trạng thái `safe_mode`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, UC §6.2 F-03b step 2a
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='safe_mode'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_011
**Scenario Title:** One-bot policy — từ chối start khi user có bot ở trạng thái `error`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, UC §6.2 F-03b step 2a
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='error'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_012
**Scenario Title:** One-bot policy — cho phép start khi user không có bot nào đang tồn tại
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-001, BR-EXBOT-001, UC §6.2 F-03b step 2a
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và user này không có bất kỳ bot nào trong `bot_registry` (không có row với userId đó ở trạng thái `active`, `paused`, `closing`, `safe_mode`, hoặc `error`), preflight step 1 pass; hệ thống tiếp tục sang step 2.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_013
**Scenario Title:** Vault balance = 0 — từ chối start với E-EXBOT-025
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 2, E-EXBOT-025, UC §6.2 F-03b step 2b, AC-03
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và BnzaExVault balance của user này bằng 0 (chưa nạp tiền on-chain), ExBot Lambda trả về HTTP 400 với message "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_014
**Scenario Title:** Vault balance > 0 — preflight step 2 pass
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 2, UC §6.2 F-03b step 2b
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và BnzaExVault balance của user > 0 (đã hoàn tất on-chain deposit), preflight step 2 pass; hệ thống tiếp tục sang step 3 (HL margin check).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_015
**Scenario Title:** HL margin = required × 2.0 chính xác — preflight step 3 pass (boundary: đúng ngưỡng)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 3, FR-EXBOT-061, UC §6.2 F-03b step 2c
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `marginBalance` trên HL bằng đúng `required_margin × 2.0` (tính bằng BigDecimal: `required_margin = lpEthAmount × hedgeRatio × hlOraclePrice / leverage`), preflight step 3 pass; hệ thống tiếp tục sang step 4.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_016
**Scenario Title:** HL margin = required × 2.0 − epsilon — từ chối start với E-EXBOT-002 (boundary: dưới ngưỡng)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 3, FR-EXBOT-061, E-EXBOT-002, UC §6.2 F-03b step 2c, AC-04
**Test Type:** Functional
**Description:** Khi `marginBalance` nhỏ hơn `required_margin × 2.0` (dù chỉ nhỏ hơn một lượng rất nhỏ), ExBot Lambda trả về HTTP 400 với message "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." trong đó X là required, Y là current balance, Z là shortfall. Không tạo bot record.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_017
**Scenario Title:** HL margin > required × 2.0 — preflight step 3 pass (boundary: trên ngưỡng)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 3, FR-EXBOT-061, UC §6.2 F-03b step 2c
**Test Type:** Functional
**Description:** Khi `marginBalance` lớn hơn `required_margin × 2.0`, preflight step 3 pass; hệ thống tiếp tục sang step 4.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_018
**Scenario Title:** `key_status` không phải `active` — từ chối start với E-EXBOT-017
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 4, E-EXBOT-017, UC §6.2 F-03b step 2d, AC-05
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `hl_agent_keys.key_status` của user không phải `active` (ví dụ không có row tồn tại, hoặc row có `key_status='superseded'` hoặc `key_status='revoked'`), ExBot Lambda trả về HTTP 400 với message "Bot cannot start: agent key not yet provisioned. Please wait for deposit processing to complete." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_019
**Scenario Title:** `key_status='active'` — preflight step 4 pass
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 4, UC §6.2 F-03b step 2d
**Test Type:** Functional
**Description:** Khi `hl_agent_keys.key_status='active'` tồn tại cho user, preflight step 4 pass; hệ thống tiếp tục sang step 5 (builder fee check).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_020
**Scenario Title:** Builder fee 5bps chưa được confirm trên HL — từ chối start với E-EXBOT-005
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 5, E-EXBOT-005, UC §6.2 F-03b step 2e
**Test Type:** Functional
**Description:** Khi builder fee 5bps chưa được approve trên HL cho account của user, ExBot Lambda trả về HTTP 400 với message "HL builder fee (5bps) approval required before starting ExBot." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_021
**Scenario Title:** LP mint simulation thất bại — từ chối start với E-EXBOT-006
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002 step 6, E-EXBOT-006, UC §6.2 F-03b step 2f
**Test Type:** Functional
**Description:** Khi LP mint simulation thất bại (ví dụ: pool liquidity không đủ, hoặc slippage tolerance bị vi phạm), ExBot Lambda trả về HTTP 400 với message "LP mint simulation failed. Check pool liquidity or adjust deposit amount." Không tạo bot record; không có lời gọi `BnzaExVault.vaultMint()` thực tế nào được thực hiện.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_022
**Scenario Title:** 6 preflight checks thực hiện tuần tự — fail bất kỳ bước nào thì dừng ngay, không tạo bot record
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002, UC §6.2 F-03b §B
**Test Type:** Functional
**Description:** Khi preflight fail tại bước N (bất kỳ bước nào từ 2a đến 2f), hệ thống không tiếp tục thực hiện các bước sau bước N, không tạo bot record trong DB, và trả về lỗi tương ứng. Ví dụ: nếu step 2b (vault balance) fail, step 2c đến 2f không được thực hiện.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_023
**Scenario Title:** HL weight bị tính vào quota 800/min ngay cả khi preflight fail ở bước sau margin check
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-091, UC §6.2 F-03b §B, I-09 (Answered)
**Test Type:** Integration
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và preflight step 3 (HL margin check) thực hiện thành công (HL API trả về marginSummary, tốn 2 weight đơn vị), nhưng preflight thất bại tại bước 4 hoặc 5, ElastiCache Redis token bucket vẫn ghi nhận và trừ đi 2 weight đơn vị từ quota 800/min. Weight bị tính không bị hoàn trả dù preflight không hoàn thành.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_024
**Scenario Title:** Preflight order thứ tự đúng: one-bot → vault balance → HL margin → key_status → builder fee → LP sim
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-002, UC §6.2 F-03b step 2a–2f
**Test Type:** Functional
**Description:** Khi gọi `POST /api/exbot/start` với user vừa vi phạm one-bot policy (step 1) vừa thiếu vault balance (step 2), hệ thống trả về E-EXBOT-001 (one-bot, HTTP 409) chứ không phải E-EXBOT-025 (vault balance). Điều này xác nhận thứ tự thực hiện preflight đúng theo spec.md FR-EXBOT-002.
**Test Focus:** Alternative flow

---

### Sub-flow F-03b: User-Triggered Bot Start — Execution (Post-Preflight)

---

### Scenario ID: TS_UC-EXBOT-bot-start_025
**Scenario Title:** Happy path — bot start hoàn toàn thành công, đạt `lifecycle_state='active'`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-003, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-030, FR-EXBOT-031, FR-EXBOT-080, UC §F.3.1, AC-01
**Test Type:** Functional
**Description:** Khi tất cả 6 preflight checks pass, ExBot Lambda tạo bot record (`lifecycle_state='preflight'`), gọi `BnzaExVault.vaultMint()` thành công, nhận `VaultMinted` event, mở short IOC qua Signing Lambda với `targetShortEth = lpEthAmount × 0.70`, thực hiện post-order reconcile, tính `stop_trigger_px` bằng BigDecimal, đặt reduce-only stop và nhận xác nhận. Kết quả cuối: `bots.lifecycle_state='active'`, `bots.status='active'`, `hedge_legs.stop_price` được điền, `hedge_legs.entry_price`, `liq_price`, `effective_leverage` đầy đủ, LP NFT được giữ trong `BnzaExVault` (`positions.custodian='vault'`).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_026
**Scenario Title:** Lifecycle state sequence đúng thứ tự — không bỏ bước
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-003, UC §6.3 F-03b §B, F1-16
**Test Type:** Data/State
**Description:** Trong quá trình bot start thành công, chuỗi `lifecycle_state` trong Aurora PostgreSQL phải tuần tự đúng thứ tự: `idle → preflight → lp_opening → lp_opened → hedge_pre_open → hedge_post_confirmed → stop_placing → stop_verified → active`. Mỗi transition phải được persist vào Aurora PostgreSQL nguyên tử trước khi bước tiếp theo bắt đầu. Không được bỏ qua bất kỳ bước trung gian nào.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_027
**Scenario Title:** Mỗi lifecycle state transition được lưu nguyên tử trước khi proceed
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-003, UC §6.3 F-03b §B
**Test Type:** Data/State
**Description:** Nếu quá trình bot start bị gián đoạn (ví dụ: Lambda timeout, crash) sau khi một state transition đã được persist nhưng trước khi bước tiếp theo hoàn thành, khi hệ thống kiểm tra bảng `bots`, `lifecycle_state` phản ánh đúng trạng thái cuối cùng đã được commit — không bị mất hay rollback về state trước đó. Không có "partial state" có thể gây inconsistency.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_028
**Scenario Title:** cloid deterministic — cùng (botId, attemptId, stage, version) luôn cho cùng cloid
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-024, UC §F.2 cloid
**Test Type:** Data/State
**Description:** Với cùng bộ (botId, attemptId, stage, version), hàm tính cloid `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` luôn trả về cùng một giá trị. Nếu lệnh IOC được gửi lại do retry (cùng attemptId, cùng stage, cùng version), cloid gửi lên HL là như nhau — hệ thống không thực hiện retry mù mà phải reconcile trước.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_029
**Scenario Title:** Post-order reconcile — `rebalance_attempts.status='success'` không được ghi trước khi reconcile xác nhận
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-025, UC §6.3 F-03b step 7, §F.2
**Test Type:** Data/State
**Description:** Sau khi lệnh short IOC được submit lên HL, ExBot Lambda phải fetch `clearinghouseState` và xác nhận actual size trước khi ghi `rebalance_attempts.status='success'`. Nếu `clearinghouseState` chưa được fetch hoặc reconcile chưa xác nhận, `status='success'` không được xuất hiện trong bảng `rebalance_attempts`.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_030
**Scenario Title:** Post-order reconcile — actual size khớp expected; `hedge_legs` được cập nhật đầy đủ
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-025, UC §6.3 F-03b step 7–8, AC-07
**Test Type:** Integration
**Description:** Sau khi lệnh short IOC khớp trên HL, ExBot Lambda fetch `clearinghouseState` và xác nhận actual size bằng expected (`targetShortEth`). `hedge_legs` được cập nhật với `entry_price`, `liquidation_price`, `effective_leverage` từ `clearinghouseState`; `lifecycle_state` chuyển thành `hedge_post_confirmed`.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_031
**Scenario Title:** Post-order reconcile — actual size lệch > drift_threshold: enqueue partial_repair, alert operator
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-025, UC §6.3 F-03b step 7, UC §F.3.3 A11, AC-07
**Test Type:** Integration
**Description:** Sau khi lệnh short IOC khớp, ExBot Lambda phát hiện actual size lệch khỏi expected size quá ngưỡng `drift_threshold`. Hệ thống enqueue một message `partial_repair`, gửi alert cho operator, và bot giữ nguyên tại `lifecycle_state='hedge_post_confirmed'` — không tiếp tục sang bước tính stop. (Lưu ý: giá trị `drift_threshold` cụ thể bị blocked bởi OQ-EXBOT-11 — xem Out-of-Scope Flags.)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_032
**Scenario Title:** stop_trigger_px tính bằng BigDecimal — không có float error
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-030, NFR-EXBOT-008, UC §6.3 F-03b step 9, AC-11
**Test Type:** Functional
**Description:** Với `entry_price = $3,000`, `liq_price = $3,300`, `leverage = 3x`: `liq_distance_pct = (3300 - 3000) / 3000 = 0.10`; `stop_trigger_px = 3000 × (1 + 0.10 × 0.70) = 3000 × 1.07 = $3,210.00`. Kết quả phải chính xác bằng $3,210.00, không có sai số floating point trung gian. Toàn bộ tính toán dùng BigDecimal, không dùng `Number()` hay `parseFloat()`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_033
**Scenario Title:** stop_trigger_px — fallback khi liq_price không có: dùng `1 / effective_leverage`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-030, UC §F.2 stop_trigger_px
**Test Type:** Functional
**Description:** Khi `liquidation_price` không khả dụng từ `clearinghouseState` (ví dụ: HL không trả về giá trị này), ExBot Lambda dùng fallback: `liq_distance_pct = 1 / effective_leverage`. Ví dụ với leverage 3x: `liq_distance_pct = 0.3333...`; `stop_trigger_px = entry_price × (1 + 0.3333 × 0.70)`. Tính toán vẫn dùng BigDecimal.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_034
**Scenario Title:** Stop placement fail — bot chuyển sang `safe_mode`, không phải `active`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-031, FR-EXBOT-050, UC §6.3 F-03b step 9b, UC §F.3.3 A8, AC-06
**Test Type:** Data/State
**Description:** Sau khi LP mint và hedge short mở thành công, khi lệnh đặt reduce-only stop không được HL confirm (stop placement fail), `lifecycle_state` chuyển thành `'safe_mode'` — không phải `'active'`. Operator alert được gửi. Auto-recovery theo FR-EXBOT-050 bắt đầu. `hedge_legs.stop_price` chưa được điền vì stop chưa confirmed.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_035
**Scenario Title:** Bot không thể reach `active` nếu `hedge_legs.stop_price` chưa được điền
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-031, UC §6.3 F-03b step 10, §F.2 hedge_legs.stop_price
**Test Type:** Data/State
**Description:** Khi `lifecycle_state='stop_verified'`, phải có `hedge_legs.stop_price` được điền trước khi hệ thống cho phép transition sang `active`. Không có trường hợp nào bot đạt `lifecycle_state='active'` mà `hedge_legs.stop_price` là NULL. INV-STOP invariant phải được thỏa mãn.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_036
**Scenario Title:** `hedge_legs` sau bot start — đầy đủ các trường bắt buộc khi `lifecycle_state='active'`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-031, FR-EXBOT-025, UC §6.3 F-03b step 10, UC §F.3.1
**Test Type:** Data/State
**Description:** Sau khi bot start thành công và đạt `lifecycle_state='active'`, bảng `hedge_legs` phải có đầy đủ: `stop_price`, `stop_cloid`, `stop_order_id`, `stop_size`, `stop_distance_pct`, `entry_price`, `liquidation_price`, `effective_leverage`, `hl_account_address`. Không được có giá trị NULL trong các trường này.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_037
**Scenario Title:** `positions.weth_index` được set đúng tại LP open trên Base (chain 8453)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-004, UC §6.3 F-03b step 5, §F.2 positions.weth_index
**Test Type:** Integration
**Description:** Khi `vaultMint()` được thực hiện trên Base (chainId 8453), giá trị `wethIndex` cho pool tương ứng trên Base được lấy đúng (0 hoặc 1, tùy WETH là token0 hay token1 trong pool), và `positions.weth_index` được set với giá trị đó. Không được hardcode `wethIndex`. (Lưu ý: test cụ thể với pool address xác định cần deferred đến khi OQ-EXBOT-03 được giải quyết — xem Out-of-Scope Flags.)
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_038
**Scenario Title:** `positions.weth_index` được set đúng tại LP open trên Optimism (chain 10)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-004, NFR-EXBOT-009, UC §6.3 F-03b step 5
**Test Type:** Integration
**Description:** Khi `vaultMint()` được thực hiện trên Optimism (chainId 10), giá trị `wethIndex` cho pool tương ứng trên OP được lấy đúng và `positions.weth_index` được set với giá trị đó — không dùng cùng giá trị hardcode với Base. (Lưu ý: test cụ thể cần deferred đến khi OQ-EXBOT-03 được giải quyết.)
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_039
**Scenario Title:** targetShortEth = lpEthAmount × hedgeRatio (0.70) — tính toán hedge size đúng
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-021, FR-EXBOT-024, UC §6.3 F-03b step 6, F1-34
**Test Type:** Functional
**Description:** Sau khi LP mint thành công và `lpEthAmount` được xác định từ `VaultMinted` event, ExBot Lambda tính `targetShortEth = lpEthAmount × 0.70` (hedgeRatio Phase A) bằng BigDecimal. Lệnh short IOC gửi lên HL có size đúng bằng `targetShortEth`, không làm tròn bằng float.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-bot-start_040
**Scenario Title:** LP mint fail — `lifecycle_state` chuyển sang `error`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-003, UC §F.3.3 A4
**Test Type:** Data/State
**Description:** Khi `BnzaExVault.vaultMint()` transaction revert trên chain (ví dụ: slippage vượt tolerance, contract reverts), `lifecycle_state` trong `bots` chuyển thành `'error'`. Cơ chế refund (return funds cho user) là thông tin deferred pending OQ-EXBOT-08 — xem Out-of-Scope Flags. Bot không được tiếp tục sang bước mở short hedge.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_041
**Scenario Title:** Sau bot start thành công — light-check được lên lịch với jitter 5 phút
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-013, UC §F.4
**Test Type:** Integration
**Description:** Ngay sau khi `lifecycle_state='active'`, hệ thống tính và lưu `bots.next_light_check_at = now + 5min + random(−45s, +45s)`. Update này được thực hiện theo batch per shard (1 UPDATE per shard, không per-bot). `next_light_check_at` phải nằm trong khoảng từ `now + 4m15s` đến `now + 5m45s`.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_042
**Scenario Title:** LP NFT sau bot start — được giữ bởi `BnzaExVault` (`positions.custodian='vault'`)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-070, UC §F.4, UC §F.3.1
**Test Type:** Data/State
**Description:** Sau khi bot start thành công và LP NFT được mint, `positions.custodian='vault'` và `positions.custodian_address` trỏ đến địa chỉ `BnzaExVault` contract đúng trên chain tương ứng. NFT không nằm trong ví của user hay của ExBot Lambda.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_043
**Scenario Title:** stop_trigger_px — bot không được set `active` với stop ở giá cao hơn `liq_price`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-030, FR-EXBOT-031, UC §F.2 stop_trigger_px
**Test Type:** Data/State
**Description:** Công thức `stop_trigger_px = entry_price × (1 + liq_distance_pct × 0.70)` với `stopSafetyFactor = 0.70` đảm bảo stop được kích hoạt khi giá còn 30% buffer trước khi đến `liq_price`. Kiểm tra: `stop_trigger_px` phải nhỏ hơn `liquidation_price` — nếu stop bằng hoặc lớn hơn `liq_price`, đây là lỗi tính toán.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_044
**Scenario Title:** HL margin check tính đúng `required_margin` theo công thức BigDecimal
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-061, FR-EXBOT-002 step 3, UC §F.2 preflight margin computation
**Test Type:** Functional
**Description:** Tại bước preflight margin check, ExBot Lambda tính `required_margin = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage` bằng BigDecimal. Với ví dụ: `lpEthAmount = 10 ETH`, `hedgeRatio = 0.70`, `hlOraclePrice = $3,000`, `leverage = 3x`: `required_margin = (10 × 0.70 × 3000) / 3 = $7,000`. Buffer factor 2.0: cần `marginBalance ≥ $14,000`. Nếu sai công thức hoặc dùng float, kết quả sẽ sai.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-bot-start_045
**Scenario Title:** Bot start với ExBot Lambda riêng biệt, không co-deployed với OPERATOR (BR-EXBOT-010)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** BR-EXBOT-010, UC §2 ExBot Lambda actor
**Test Type:** Integration
**Description:** `POST /api/exbot/start` phải đi qua ExBot Lambda riêng biệt (không phải OPERATOR service). Xác nhận request không được xử lý bởi OPERATOR Worker — ExBot Lambda là standalone service nhận request qua API Gateway + HMAC Lambda Authorizer. Các log và tracing phải chỉ ra ExBot Lambda riêng biệt với OPERATOR.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_046
**Scenario Title:** Acceptance Criteria AC-01 — bot start end-to-end: tất cả postconditions được thỏa mãn
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** UC §F.5 AC-01, FR-EXBOT-003, FR-EXBOT-031, FR-EXBOT-025
**Test Type:** Acceptance
**Description:** Với precondition đầy đủ (không có bot active, vault balance > 0, margin đủ, key_status='active', builder fee confirmed), khi gọi `POST /api/exbot/start`, tất cả postconditions sau phải đúng: (1) `lifecycle_state='active'`; (2) `stop_price` được điền trong `hedge_legs`; (3) LP NFT trong BnzaExVault (`positions.custodian='vault'`); (4) `hedge_legs.entry_price`, `liq_price`, `effective_leverage` không NULL; (5) API response trả về `{status: 'active', botId, lifecycle_state: 'active'}`.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_047
**Scenario Title:** Acceptance Criteria AC-08 — KMS key isolation: không có raw private key trong DB
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** UC §F.5 AC-08, NFR-EXBOT-006
**Test Type:** Acceptance
**Description:** Sau khi key-provision hoàn tất và `key_status='active'`, kiểm tra tất cả fields trong `hl_agent_keys` cho user vừa provision — không có trường nào chứa raw private key bytes, hex private key, hay bất kỳ material nào có thể reconstruct private key. Chỉ có public address (`hl_user_address`, `agent_address`) và metadata được lưu.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_048
**Scenario Title:** Acceptance Criteria AC-09 deferred — HL IOC reject: expected state `error` hay `safe_mode`?
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** UC §F.5 AC-09, UC §F.3.3 A10
**Test Type:** Acceptance
**Description:** Khi HL từ chối lệnh short IOC (ví dụ: insufficient margin during order placement, hoặc HL service down), expected `lifecycle_state` cần được xác nhận: UC §4 A10 mô tả → `error`; `states.md` chỉ định nghĩa transition `hedge_pre_open → safe_mode`. Scenario này bị blocked bởi IS-01 (I-11) — không thể thiết kế expected result cho đến khi BA xác nhận. (Xem Out-of-Scope Flags.)
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_049
**Scenario Title:** Acceptance Criteria AC-11 — stop_trigger_px chính xác BigDecimal, fire trước liq_price với buffer 30%
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** UC §F.5 AC-11, FR-EXBOT-030, NFR-EXBOT-008
**Test Type:** Acceptance
**Description:** Với `entry_price = $3,000`, `liq_price = $3,300`, `leverage = 3x`: `stop_trigger_px` phải chính xác bằng `$3,210.00` (không có float error). Stop này sẽ kích hoạt ở $3,210 — còn $90 (30% của $300 `liq_distance`) trước khi chạm `liq_price = $3,300`. Xác nhận không có intermediate float operation.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_050
**Scenario Title:** VaultMinted event — `tokenId`, `tickLower`, `tickUpper`, `liquidity` được lưu đúng vào Aurora PostgreSQL
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** FR-EXBOT-003, UC §6.3 F-03b step 5, F1-10, F1-11
**Test Type:** On-chain↔off-chain consistency
**Description:** Sau khi `BnzaExVault.vaultMint()` emit `VaultMinted(user, botId, tokenId, liquidity)` event, ExBot Lambda xử lý event và UPDATE bảng `positions` với: `tokenId` từ event, `tickLower`, `tickUpper` từ params, `liquidity` từ event, `wethIndex` đúng per chain. `lifecycle_state` chuyển thành `lp_opened`. Tất cả 4 trường phải được set từ event thực tế, không hardcode.
**Test Focus:** On-chain↔off-chain consistency

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Lý do | Hành động đề nghị |
|---|---|---|
| A7 — HL unreachable tại bước hedge open (UC §F.3.3 A7) | **BLOCKED: IS-01 (I-11)** — mâu thuẫn giữa UC §4 A7 (`error`) và `states.md` (`hedge_pre_open → safe_mode`). Không thể thiết kế expected result. | Resolve via qc-qna: BA xác nhận target state là `error` hay `safe_mode`; sau đó re-audit + re-gen scenarios |
| A10 — HL reject IOC order (UC §F.3.3 A10) | **BLOCKED: IS-01 (I-11)** — tương tự A7. UC §4 A10 → `error`; `states.md` chỉ có `hedge_pre_open → safe_mode`. | Resolve via qc-qna: BA xác nhận; sau đó re-audit + re-gen scenarios |
| A4 — LP mint fail: cơ chế refund chi tiết (UC §F.3.3 A4) | **BLOCKED: OQ-EXBOT-08** — ABI BnzaExVault chưa confirmed; cơ chế refund khi `vaultMint()` revert chưa được xác định. TS_UC-EXBOT-bot-start_040 đã cover state transition sang `error` từ thông tin hiện có. | Chờ zen xác nhận OQ-EXBOT-08 (BnzaExVault ABI + refund mechanism) |
| Builder fee preflight (step 5) chi tiết (UC §6.2 F-03b step 2e) | **BLOCKED: OQ-EXBOT-05** — API endpoint và weight để check builder fee trên HL chưa được xác nhận. TS_UC-EXBOT-bot-start_020 đã cover happy/error flow từ thông tin hiện có. | Chờ zen xác nhận OQ-EXBOT-05 |
| Dual-chain wethIndex test với pool address cụ thể | **BLOCKED: OQ-EXBOT-03** — Pool addresses trên Base và OP chưa được confirm; `wethIndex` per chain chưa được xác nhận chính xác. TS_UC-EXBOT-bot-start_037/038 cover intent-level. | Chờ zen xác nhận OQ-EXBOT-03 rồi expand thành test case cụ thể |
| Reconcile mismatch boundary: giá trị `drift_threshold` cụ thể | **BLOCKED: OQ-EXBOT-11 (IS-02)** — `drift_threshold` chưa confirmed (ứng viên `lpValueUsd × 3%` nhưng chưa approved). TS_UC-EXBOT-bot-start_031 cover scenario nhưng không thể set boundary value cụ thể. | Chờ zen/BA confirm OQ-EXBOT-11 |
| IS-03 — `provisioning` state trong hl_agent_keys | **BLOCKED: IS-03** — Mâu thuẫn giữa spec.md (đề cập `provisioning` trong failure path) và `states.md` (chỉ có `active/superseded/revoked`). Không rõ `provisioning` có phải state chính thức cần test. | BA confirm: `provisioning` có phải state chính thức? Nếu có thì cần add vào `states.md` và thiết kế thêm scenario |
| Performance / load testing | NFR: ngoài phạm vi chức năng. Bot-check latency <100ms, 10,000 bots scale — cần specialist | Defer sang load testing specialist sau khi Phase A test environment sẵn sàng |

