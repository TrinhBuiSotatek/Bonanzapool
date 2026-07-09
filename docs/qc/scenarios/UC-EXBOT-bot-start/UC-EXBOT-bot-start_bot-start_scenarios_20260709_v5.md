# Test Scenarios — UC-EXBOT-bot-start: Khởi động ExBot

> **Source:** `docs/qc/uc-read/UC-EXBOT-bot-start/UC-EXBOT-bot-start_bot-start_audited_20260709_v5.md`
> **Generated:** 2026-07-09
> **Domain/Architecture:** AWS Lambda (ExBot Lambda standalone, BR-EXBOT-010) + Aurora PostgreSQL + BnzaExVault (Solidity, Base/Optimism) + Hyperliquid (perpetual DEX) + AWS KMS (Signing Lambda) + SQS queue
> **Version:** v5 (re-gen từ audit v5; v4 marked NOT READY 58/100; v5 audit 85/100 Conditionally Ready)

---

## UC-EXBOT-bot-start — Khởi động ExBot

---

## Sub-flow F-03a: Auto Key-Provision on Deposit

---

### Scenario ID: TS_UC-EXBOT-bot-start_001
**Scenario Title:** Key-provision hoàn tất thành công — `key_status` chuyển từ `provisioning` sang `active`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-080, states.md Agent Key Status, BA confirmed I-17
**Test Type:** Data/State
**Description:** Khi Chain Indexer phát hiện sự kiện nạp tiền on-chain của người dùng, Key-Provision Worker khởi động luồng F-03a: gọi KMS GenerateKeyPair (master key + agent key) thành công, INSERT một row vào `hl_agent_keys` với `key_status='provisioning'`, sau đó gọi HL `approveAgent`. Khi HL xác nhận `approveAgent`, `key_status` được UPDATE thành `'active'`. Xác nhận: (1) row với `key_status='provisioning'` tồn tại SAU KHI KMS thành công và TRƯỚC KHI HL `approveAgent` được gọi; (2) row chuyển thành `key_status='active'` sau khi HL xác nhận; (3) không có row trùng lặp nào được tạo.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_002
**Scenario Title:** Lifecycle state F-03a — INSERT `hl_agent_keys` với `key_status='provisioning'` trước HL `approveAgent` (spec.md là canonical)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-080 step 4, states.md Agent Key Status, V5-02 (flows.md bất nhất — spec.md là canonical)
**Test Type:** Data/State
**Description:** Trong luồng F-03a, xác nhận rằng thứ tự thực hiện đúng như spec.md FR-EXBOT-080 (không như flows.md F-03a vốn bỏ qua bước provisioning): bước 1 — KMS GenerateKeyPair; bước 2 — INSERT `hl_agent_keys` row với `key_status='provisioning'`; bước 3 — gọi HL `approveAgent`; bước 4 — UPDATE `key_status='active'`. Nếu message bị lost sau bước 2 nhưng trước bước 3, worker có thể retry bắt đầu từ bước 3 mà không cần tạo key pair mới (idempotency recovery).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_003
**Scenario Title:** KMS GenerateKeyPair thất bại — retry với exponential backoff, tối đa 3 lần; `key_status` không chuyển sang `provisioning`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-080, spec.md FR-EXBOT-081, BA confirmed I-15
**Test Type:** Functional
**Description:** Khi KMS trả về `ThrottlingException` hoặc không khả dụng tại bước GenerateKeyPair, Key-Provision Worker thực hiện retry với exponential backoff. Sau tối đa 3 lần thất bại liên tiếp, hệ thống gửi admin alert qua notification queue với message E-EXBOT-027 "Key-provision failed for user {wallet_address} after 3 retries. Manual re-trigger required via admin panel." `hl_agent_keys` không có row nào được INSERT (vì KMS chưa thành công — INSERT chỉ xảy ra SAU KHI KMS succeed, trước HL). Tiền của user vẫn còn trong `BnzaExVault` — không cần deposit lại.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_004
**Scenario Title:** HL `approveAgent` thất bại — row `hl_agent_keys` với `key_status='provisioning'` tồn tại; retry qua queue; không tạo duplicate row
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-080, states.md Agent Key Status
**Test Type:** Functional
**Description:** Khi HL từ chối hoặc không phản hồi lệnh `approveAgent(hl_user_address, agent_address)`, Key-Provision Worker đã có một row `hl_agent_keys` với `key_status='provisioning'` (đã INSERT sau khi KMS succeed). Worker không UPDATE row này thành `active`; message được đưa vào retry queue. Khi retry: worker phát hiện row `provisioning` đã tồn tại (via `message_id` idempotency hoặc user_id check), tái sử dụng key pair đã generate, chỉ retry bước HL `approveAgent` — không gọi KMS lại, không tạo thêm row.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_005
**Scenario Title:** Redelivery cùng key-provision message — không tạo duplicate row `hl_agent_keys`; không tạo duplicate key pair
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-011, NFR-EXBOT-007
**Test Type:** Data/State
**Description:** Khi SQS tái phân phối cùng một key-provision message (cùng `message_id`) cho Key-Provision Worker, worker phát hiện `message_id` đã tồn tại trong `queue_idempotency` với `state='started'` hoặc `state='succeeded'`, và return ngay lập tức mà không tạo thêm row `hl_agent_keys` hoặc gọi KMS lần nữa. Tổng số row `hl_agent_keys` cho user này không tăng so với trước redelivery.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_006
**Scenario Title:** Private key không bao giờ rời KMS HSM — không có raw key material trong DB, log, hoặc memory
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** NFR-EXBOT-006, spec.md FR-EXBOT-080
**Test Type:** Functional
**Description:** Sau khi key-provision hoàn tất và `key_status='active'`, kiểm tra bảng `hl_agent_keys` chỉ chứa `hl_user_address` và `agent_address` (public key dạng địa chỉ ví) — không có trường nào chứa raw private key material, private key bytes, hoặc encrypted private key. Log hệ thống trong quá trình provisioning không expose bất kỳ private key material nào. 9 trường legacy (encrypted_secret, secret_iv, v.v.) đã được annotate RETIRED trong ERD và phải hoàn toàn NULL/không có giá trị.
**Test Focus:** Error/Exception

---

## Sub-flow F-03b: User-Triggered Bot Start — Preflight

---

### Scenario ID: TS_UC-EXBOT-bot-start_007
**Scenario Title:** One-bot policy — từ chối start khi user đang có bot ở trạng thái `active`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, AC-02
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đã có một bot với `status='active'` trong `bot_registry`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không có bot record mới nào được tạo trong DB.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_008
**Scenario Title:** One-bot policy — từ chối start khi user đang có bot ở trạng thái `paused`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='paused'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_009
**Scenario Title:** One-bot policy — từ chối start khi user có bot ở trạng thái `closing`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='closing'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_010
**Scenario Title:** One-bot policy — từ chối start khi user có bot ở trạng thái `safe_mode`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001, AC-03
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='safe_mode'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_011
**Scenario Title:** One-bot policy — từ chối start khi user có bot ở trạng thái `error`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-001, BR-EXBOT-001, E-EXBOT-001
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` trong khi user này đang có bot với `status='error'`, ExBot Lambda trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish before starting a new one." Không tạo bot record mới.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_012
**Scenario Title:** One-bot policy — cho phép start khi user không có bot nào đang tồn tại
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-001, BR-EXBOT-001
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và user này không có bất kỳ bot nào trong `bot_registry` với `status IN ('active','paused','closing','safe_mode','error')`, preflight step 1 pass; hệ thống tiếp tục sang step 2 (vault balance check).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_013
**Scenario Title:** Vault balance = 0 — từ chối start với E-EXBOT-025
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #2, E-EXBOT-025, AC-04
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `BnzaExVault` balance của user này bằng 0 (chưa nạp tiền on-chain), ExBot Lambda trả về HTTP 400 với message "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_014
**Scenario Title:** Vault balance > 0 — preflight step 2 pass
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #2
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `BnzaExVault` balance của user > 0 (đã hoàn tất on-chain deposit), preflight step 2 pass; hệ thống tiếp tục sang step 3 (HL margin check).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_015
**Scenario Title:** HL margin = required × 2.0 chính xác — preflight step 3 pass (boundary: đúng ngưỡng)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-061, FR-EXBOT-002 check #3
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `marginBalance` trên HL bằng đúng `required_margin × 2.0` (tính bằng BigDecimal: `required_margin = lpEthAmount × hedgeRatio × hlOraclePrice / leverage`), preflight step 3 pass; hệ thống tiếp tục sang step 4.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_016
**Scenario Title:** HL margin = required × 2.0 − epsilon — từ chối start với E-EXBOT-002 (boundary: dưới ngưỡng)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-061, FR-EXBOT-002 check #3, E-EXBOT-002, AC-05
**Test Type:** Functional
**Description:** Khi `marginBalance` nhỏ hơn `required_margin × 2.0` (dù chỉ nhỏ hơn một lượng rất nhỏ epsilon), ExBot Lambda trả về HTTP 400 với message "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." trong đó X là required×2.0, Y là current balance, Z là shortfall. Không tạo bot record.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_017
**Scenario Title:** HL margin > required × 2.0 — preflight step 3 pass (boundary: trên ngưỡng)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-061, FR-EXBOT-002 check #3
**Test Type:** Functional
**Description:** Khi `marginBalance` lớn hơn `required_margin × 2.0`, preflight step 3 pass; hệ thống tiếp tục sang step 4.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_018
**Scenario Title:** HL margin check tính đúng `required_margin` theo công thức BigDecimal
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-061, FR-EXBOT-002 check #3, NFR-EXBOT-008
**Test Type:** Functional
**Description:** Tại bước preflight margin check, ExBot Lambda tính `required_margin = (lpEthAmount × hedgeRatio × hlOraclePrice) / leverage` bằng BigDecimal. Ví dụ cụ thể: `lpEthAmount = 10 ETH`, `hedgeRatio = 0.70`, `hlOraclePrice = $3,000`, `leverage = 3x` → `required_margin = (10 × 0.70 × 3,000) / 3 = $7,000` → cần `marginBalance ≥ $14,000`. Kết quả phải chính xác $14,000.00 — không có sai số floating point.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-bot-start_019
**Scenario Title:** `key_status='provisioning'` — từ chối start với E-EXBOT-017 (trạng thái đang provisioning)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #4, FR-EXBOT-080, E-EXBOT-017, BA confirmed I-17, AC-06
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `hl_agent_keys.key_status='provisioning'` (KMS đã generate keys, HL `approveAgent` chưa confirm), ExBot Lambda trả về HTTP 400 với message "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." Không tạo bot record. Đây là trạng thái DB chính thức (BA confirmed I-17) — không phải transient in-progress.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_020
**Scenario Title:** `key_status='superseded'` — từ chối start với E-EXBOT-017
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #4, E-EXBOT-017, states.md Agent Key Status
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `hl_agent_keys.key_status='superseded'` (khóa cũ đã bị thay thế bởi khóa mới), ExBot Lambda trả về HTTP 400 với message "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_021
**Scenario Title:** `key_status='revoked'` — từ chối start với E-EXBOT-017
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #4, E-EXBOT-017, states.md Agent Key Status
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và `hl_agent_keys.key_status='revoked'` (khóa bị thu hồi), ExBot Lambda trả về HTTP 400 với message "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_022
**Scenario Title:** Không có row `hl_agent_keys` cho user — từ chối start với E-EXBOT-017
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #4, E-EXBOT-017
**Test Type:** Functional
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và không có row nào trong `hl_agent_keys` cho user này (chưa deposit lần nào, hoặc key-provision chưa chạy), ExBot Lambda trả về HTTP 400 với message "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_023
**Scenario Title:** `key_status='active'` — preflight step 4 pass
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #4
**Test Type:** Functional
**Description:** Khi `hl_agent_keys.key_status='active'` tồn tại cho user, preflight step 4 pass; hệ thống tiếp tục sang step 5 (builder fee check).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_024
**Scenario Title:** Builder fee 5bps chưa được confirm trên HL — từ chối start với E-EXBOT-005
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #5, E-EXBOT-005, AC-07
**Test Type:** Functional
**Description:** Khi builder fee 5bps chưa được approve trên HL cho account của user, ExBot Lambda trả về HTTP 400 với message "HL builder fee (5bps) approval required before starting ExBot." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_025
**Scenario Title:** LP mint simulation thất bại — từ chối start với E-EXBOT-006
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 check #6, E-EXBOT-006, AC-08
**Test Type:** Functional
**Description:** Khi LP mint simulation thất bại (ví dụ: pool liquidity không đủ, hoặc slippage tolerance bị vi phạm), ExBot Lambda trả về HTTP 400 với message "LP mint simulation failed. Check pool liquidity or adjust deposit amount." Không tạo bot record; không có lời gọi `BnzaExVault.vaultMint()` thực tế nào được thực hiện.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_026
**Scenario Title:** Preflight thứ tự đúng — vault balance fail trước key_status fail: trả về E-EXBOT-025, không phải E-EXBOT-017
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 (tuần tự check #1→#6), AC-13
**Test Type:** Functional
**Description:** Khi user vừa thiếu vault balance (step 2) vừa có `key_status` không phải `active` (step 4), ExBot Lambda chỉ trả về lỗi vault balance (E-EXBOT-025, HTTP 400) — dừng tại bước 2, không chạy tiếp bước 4. Điều này xác nhận thứ tự tuần tự 6 bước preflight: one-bot → vault → margin → key → fee → sim.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_027
**Scenario Title:** Preflight thứ tự đúng — one-bot fail trước vault fail: trả về E-EXBOT-001, không phải E-EXBOT-025
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002 (tuần tự check #1→#6)
**Test Type:** Functional
**Description:** Khi user vừa vi phạm one-bot policy (step 1) vừa thiếu vault balance (step 2), ExBot Lambda trả về E-EXBOT-001 (HTTP 409) chứ không phải E-EXBOT-025. Xác nhận: step 1 được thực hiện trước step 2; fail tại step 1 ngăn chặn các bước tiếp theo.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_028
**Scenario Title:** Không tạo partial bot record khi bất kỳ preflight bước nào fail
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002, AC-14
**Test Type:** Functional
**Description:** Khi preflight fail tại bất kỳ bước nào (one-bot fail, vault fail, margin fail, key_status fail, builder fee fail, sim fail), không có bản ghi nào được tạo trong `bots`, `positions`, `hedge_legs`, `bot_runtime_state`. Aurora PostgreSQL phải sạch — không có partial bot record.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_029
**Scenario Title:** HL weight bị tính vào quota 800/min ngay cả khi preflight fail ở bước sau margin check
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-091, FR-EXBOT-002, BA confirmed I-09
**Test Type:** Integration
**Description:** Khi USDC Investor gọi `POST /api/exbot/start` và preflight step 3 (HL margin check) thực hiện thành công (HL API trả về `marginSummary`, tiêu thụ 2 weight đơn vị), nhưng preflight thất bại tại bước 4 hoặc 5, ElastiCache Redis token bucket vẫn ghi nhận và trừ đi 2 weight đơn vị từ quota 800/min. Weight bị tính không bị hoàn trả dù preflight không hoàn thành.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_030
**Scenario Title:** 6 preflight checks thực hiện tuần tự — fail bất kỳ bước nào thì dừng ngay
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-002
**Test Type:** Functional
**Description:** Khi preflight fail tại bước N (bất kỳ bước nào từ 1 đến 6), hệ thống không tiếp tục thực hiện các bước sau bước N và không gọi bất kỳ API bên ngoài (HL, KMS) nào của các bước chưa thực hiện. Ví dụ: nếu step 2 (vault balance) fail, step 3 đến 6 không được thực hiện — không có HL API call nào được gửi.
**Test Focus:** Alternative flow

---


## Sub-flow F-03b: User-Triggered Bot Start — Khởi tạo Bot (Post-Preflight)

---

### Scenario ID: TS_UC-EXBOT-bot-start_031
**Scenario Title:** Happy path — bot start hoàn toàn thành công, đạt `lifecycle_state='active'`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-003, FR-EXBOT-025, FR-EXBOT-030, FR-EXBOT-031, AC-01
**Test Type:** Functional
**Description:** Khi tất cả 6 preflight checks pass, ExBot Lambda tạo bot record (`lifecycle_state='preflight'`), gọi `BnzaExVault.vaultMint()` thành công, nhận `VaultMinted` event, mở short IOC qua Signing Lambda với `targetShortEth = lpEthAmount x 0.70`, thực hiện post-order reconcile, tính `stop_trigger_px` bằng BigDecimal với `safetyFactor = 0.70`, đặt reduce-only stop và nhận xác nhận. Kết quả cuối: `bots.lifecycle_state='active'`, `bots.status='active'`, `hedge_legs.stop_price` được điền, `hedge_legs.entry_price`, `liq_price`, `effective_leverage` đầy đủ, `bot_runtime_state.last_known_hl_short_size` populated, LP NFT được giữ trong `BnzaExVault` (`positions.custodian='vault'`).
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_032
**Scenario Title:** Lifecycle state sequence đúng thứ tự — 8 bước khởi tạo tuần tự, không bỏ bước
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-003, states.md
**Test Type:** Data/State
**Description:** Trong quá trình bot start thành công, chuỗi `lifecycle_state` trong Aurora PostgreSQL phải tuần tự đúng: `idle => preflight => lp_opening => lp_opened => hedge_pre_open => hedge_post_confirmed => stop_placing => stop_verified => active`. Mỗi transition phải được persist nguyên tử trước khi bước tiếp theo bắt đầu. Không được bỏ qua bất kỳ bước trung gian nào.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_033
**Scenario Title:** Mỗi lifecycle state transition được lưu nguyên tử — crash sau persist giữ đúng trạng thái cuối
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-003
**Test Type:** Data/State
**Description:** Nếu ExBot Lambda crash sau khi một state transition đã được persist vào Aurora PostgreSQL nhưng trước khi bước tiếp theo hoàn thành, `bots.lifecycle_state` phản ánh đúng trạng thái cuối cùng đã commit — không bị rollback về state trước. Không có "partial state" nào gây inconsistency giữa `bots`, `positions`, `hedge_legs`.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_034
**Scenario Title:** LP mint on-chain revert — `lifecycle_state='error'`, HTTP 502, không có tiền di chuyển
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md E-EXBOT-028, states.md (lp_opening -> error), AC-09
**Test Type:** Data/State
**Description:** Khi `BnzaExVault.vaultMint()` transaction revert on-chain (slippage vượt tolerance, contract revert), ExBot Lambda không nhận `VaultMinted` event. `lifecycle_state` chuyển thành `'error'`. Trả về HTTP 502 với message "Bot startup failed: LP mint transaction did not complete. No funds were moved. Please try again or contact support." Không có row `positions`, `hedge_legs` nào được tạo. `BnzaExVault` balance của user không thay đổi.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_035
**Scenario Title:** LP mint on-chain timeout — `lifecycle_state='error'`, không phải `safe_mode`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md E-EXBOT-028, states.md (lp_opening -> error)
**Test Type:** Data/State
**Description:** Khi `BnzaExVault.vaultMint()` transaction timeout (không nhận được `VaultMinted` event trong khoảng thời gian tối đa), ExBot Lambda ghi `lifecycle_state='error'` (không phải `safe_mode` — LP mint fail không đi qua hedge layer). Message E-EXBOT-028 được phát ra. Không có tiền di chuyển.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_036
**Scenario Title:** `VaultMinted` event — `tokenId`, `tickLower`, `tickUpper`, `liquidity` được lưu đúng vào Aurora PostgreSQL
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-003, flows.md F-03b
**Test Type:** On-chain<->off-chain consistency
**Description:** Sau khi `BnzaExVault.vaultMint()` emit `VaultMinted(user, botId, tokenId, liquidity)` event, ExBot Lambda xử lý event và UPDATE bảng `positions` với: `tokenId` từ event (không hardcode), `tickLower`, `tickUpper` từ params, `liquidity` từ event, `weth_index` đúng per chain, `lifecycle_state='lp_opened'`. Tất cả 4 trường phải được set từ event thực tế.
**Test Focus:** On-chain<->off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_037
**Scenario Title:** `positions.weth_index` được set đúng tại LP open trên Base (chainId 8453)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-004, NFR-EXBOT-009
**Test Type:** Integration
**Description:** Khi `vaultMint()` được thực hiện trên Base (chainId 8453), giá trị `wethIndex` cho pool tương ứng được lấy đúng (0 hoặc 1, tùy WETH là token0 hay token1 trong pool) và `positions.weth_index` được set với giá trị đó. Không được hardcode `wethIndex`. (Ghi chú: test với pool address cụ thể deferred đến khi OQ-EXBOT-03 Closed.)
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_038
**Scenario Title:** `positions.weth_index` được set đúng tại LP open trên Optimism (chainId 10)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-004, NFR-EXBOT-009
**Test Type:** Integration
**Description:** Khi `vaultMint()` được thực hiện trên Optimism (chainId 10), giá trị `wethIndex` cho pool tương ứng được lấy đúng và `positions.weth_index` được set với giá trị đó — không dùng cùng giá trị hardcode với Base. (Ghi chú: deferred đến khi OQ-EXBOT-03 Closed.)
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_039
**Scenario Title:** `lpEthAmount` tính từ TickMath + LiquidityAmounts — không dùng `depositedToken - withdrawnToken + collectedFees`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-020
**Test Type:** Functional
**Description:** Giá trị `lpEthAmount` dùng để tính `targetShortEth` phải được tính từ `liquidity`, `tickLower`, `tickUpper`, `sqrtPriceX96`, `currentTick` qua TickMath + LiquidityAmounts. Không được tính bằng `depositedToken - withdrawnToken + collectedFees`. Với cùng LP position, kết quả từ hai phương pháp phải nhất quán — nếu khác nhau, TickMath là canonical.
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-bot-start_040
**Scenario Title:** `targetShortEth = lpEthAmount x 0.70` — tính toán hedge size đúng bằng BigDecimal
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-021, NFR-EXBOT-008
**Test Type:** Functional
**Description:** Sau khi LP mint thành công và `lpEthAmount` được xác định từ `VaultMinted` event, ExBot Lambda tính `targetShortEth = lpEthAmount x 0.70` (hedgeRatio Phase A = 0.70) bằng BigDecimal. Ví dụ: `lpEthAmount = 5.123456789 ETH` thì `targetShortEth = 3.586419752 ETH` (BigDecimal, không làm tròn sai).
**Test Focus:** Functional

---

### Scenario ID: TS_UC-EXBOT-bot-start_041
**Scenario Title:** Cloid deterministic — cùng `(botId, attemptId, stage, version)` luôn cho cùng cloid
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-024
**Test Type:** Data/State
**Description:** Với cùng bộ `(botId, attemptId, stage, version)`, hàm tính cloid `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` luôn trả về cùng giá trị hexadecimal. Nếu lệnh IOC được gửi lại do retry (cùng attemptId, cùng stage, cùng version), cloid gửi lên HL là như nhau — HL dedup để tránh double submission.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-bot-start_042
**Scenario Title:** HL unreachable tại bước hedge open — `lifecycle_state` chuyển sang `safe_mode`, không phải `error`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-050, states.md (hedge_pre_open -> safe_mode), BA confirmed I-11, AC-10
**Test Type:** Data/State
**Description:** Khi ExBot Lambda gửi IOC short order qua Signing Lambda đến HL nhưng HL API không phản hồi (network unreachable, timeout), `lifecycle_state` chuyển từ `hedge_pre_open` sang `safe_mode`. Operator alert E-EXBOT-008 "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." Auto-recovery theo FR-EXBOT-050 được enqueue. `lifecycle_state` KHÔNG chuyển sang `error`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_043
**Scenario Title:** HL reject IOC order — `lifecycle_state` chuyển sang `safe_mode`, E-EXBOT-026
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-050, E-EXBOT-026, states.md (hedge_pre_open -> safe_mode), BA confirmed I-11/I-12, AC-11
**Test Type:** Data/State
**Description:** Khi HL nhận được IOC order nhưng từ chối thực hiện, `lifecycle_state` chuyển từ `hedge_pre_open` sang `safe_mode`. E-EXBOT-026 "Hedge order rejected by Hyperliquid. Bot entered Safe Mode." được ghi dưới dạng internal alert. Auto-recovery per FR-EXBOT-050 được enqueue. Không dùng E-EXBOT-008 (HL vẫn reachable).
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_044
**Scenario Title:** Transition `hedge_pre_open -> error` là KHÔNG HỢP LỆ theo state machine
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** states.md (hedge_pre_open -> safe_mode ONLY), BA confirmed I-11
**Test Type:** Data/State
**Description:** Xác nhận rằng từ `lifecycle_state='hedge_pre_open'`, không có transition hợp lệ nào đến `error`. Bất kể loại lỗi nào xảy ra tại bước hedge open (HL unreachable, IOC rejected), `lifecycle_state` phải chuyển sang `safe_mode` — không bao giờ chuyển sang `error` từ `hedge_pre_open`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_045
**Scenario Title:** Post-order reconcile — `rebalance_attempts.status='success'` không được ghi trước khi reconcile xác nhận
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-025
**Test Type:** Data/State
**Description:** Sau khi lệnh short IOC được submit lên HL, ExBot Lambda phải fetch `clearinghouseState` và xác nhận actual size trước khi ghi `rebalance_attempts.status='success'`. Nếu `clearinghouseState` chưa được fetch hoặc reconcile chưa xác nhận, `status='success'` không được xuất hiện trong bảng `rebalance_attempts`.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_046
**Scenario Title:** Post-order reconcile — actual size khớp expected; `hedge_legs` được cập nhật đầy đủ
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-025
**Test Type:** Integration
**Description:** Sau khi lệnh short IOC khớp trên HL, ExBot Lambda fetch `clearinghouseState` và xác nhận actual size bằng expected (`targetShortEth`). `hedge_legs` được cập nhật với `entry_price`, `liquidation_price`, `effective_leverage` từ `clearinghouseState`. `lifecycle_state` chuyển thành `hedge_post_confirmed`. `bot_runtime_state.last_known_hl_short_size` được populate với actual size.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_047
**Scenario Title:** Post-order reconcile — actual size lệch > drift_threshold: enqueue `partial_repair`, alert operator
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-025, uc-bot-start.md A11
**Test Type:** Integration
**Description:** Sau khi lệnh short IOC khớp, ExBot Lambda phát hiện actual size lệch khỏi `targetShortEth` quá `drift_threshold` (formula: `lpValueUsd x 3%` — pending OQ-EXBOT-011, xem Out-of-Scope Flags). Hệ thống enqueue message `partial_repair`, gửi alert operator E-EXBOT-011 "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." Bot giữ nguyên tại `lifecycle_state='hedge_post_confirmed'`.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_048
**Scenario Title:** `bot_runtime_state.last_known_hl_short_size` được populate sau reconcile — không NULL khi bot active
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-025, v5 audit V5-05
**Test Type:** Data/State
**Description:** Sau khi post-order reconcile thành công và `lifecycle_state='hedge_post_confirmed'`, `bot_runtime_state.last_known_hl_short_size` phải được ghi với actual size từ `clearinghouseState`. Khi bot đạt `lifecycle_state='active'`, field này không được NULL — light-check và hedge-sync đọc giá trị này thay vì gọi HL API.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_049
**Scenario Title:** Stop placement fail — `lifecycle_state` chuyển sang `safe_mode`, không phải `active`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-031, FR-EXBOT-050, states.md (stop_placing -> safe_mode), AC-12
**Test Type:** Data/State
**Description:** Sau khi LP mint và hedge short mở thành công, khi lệnh đặt reduce-only stop không được HL confirm, `lifecycle_state` chuyển thành `'safe_mode'` — không phải `'active'`. E-EXBOT-009 "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." được ghi dưới dạng internal alert. Auto-recovery theo FR-EXBOT-050 bắt đầu.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_050
**Scenario Title:** Transition `stop_placing -> error` là KHÔNG HỢP LỆ — chỉ có `stop_placing -> safe_mode`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** states.md (stop_placing -> safe_mode ONLY)
**Test Type:** Data/State
**Description:** Xác nhận rằng từ `lifecycle_state='stop_placing'`, không có transition hợp lệ nào đến `error`. Khi stop placement fail, `lifecycle_state` phải chuyển sang `safe_mode` — không bao giờ chuyển sang `error` từ `stop_placing`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_051
**Scenario Title:** Bot không thể reach `active` nếu `hedge_legs.stop_price` chưa được điền
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-031, states.md (stop_verified -> active)
**Test Type:** Data/State
**Description:** `lifecycle_state='stop_verified'` chỉ được set khi stop đã confirmed và `hedge_legs.stop_price` đã được ghi. Không có trường hợp nào bot đạt `lifecycle_state='active'` mà `hedge_legs.stop_price` là NULL.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-bot-start_052
**Scenario Title:** `stop_trigger_px` — công thức BigDecimal đúng: `entry_price x (1 + liq_distance_pct x 0.70)`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-030, NFR-EXBOT-008, AC-15
**Test Type:** Functional
**Description:** Với `entry_price = $3,000`, `liquidation_price = $3,300`: `liq_distance_pct = (3300 - 3000) / 3000 = 0.10`; `stop_trigger_px = 3000 x (1 + 0.10 x 0.70) = $3,210.00`. Kết quả phải chính xác $3,210.00, không có sai số floating point. Toàn bộ tính toán dùng BigDecimal, không dùng `Number()` hay `parseFloat()`.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_053
**Scenario Title:** `stop_trigger_px` — fallback khi `liquidation_price` không có: dùng `1 / effective_leverage`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-030
**Test Type:** Functional
**Description:** Khi `liquidation_price` không khả dụng từ `clearinghouseState`, ExBot Lambda dùng fallback: `liq_distance_pct = 1 / effective_leverage`. Ví dụ với `leverage = 3x`: `liq_distance_pct = 0.3333...`; `stop_trigger_px = entry_price x (1 + 0.3333... x 0.70)`. Tính toán vẫn dùng BigDecimal.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-bot-start_054
**Scenario Title:** `stop_trigger_px` phải nhỏ hơn `liquidation_price` — stop fire trước khi chạm liquidation
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-030, stopSafetyFactor = 0.70
**Test Type:** Boundary
**Description:** Với `safetyFactor = 0.70`, `stop_trigger_px` phải nhỏ hơn `liquidation_price` ít nhất 30% `liq_distance`. Nếu `stop_trigger_px >= liquidation_price`, đây là lỗi tính toán nghiêm trọng (position bị liquidated trước khi stop kích hoạt).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-bot-start_055
**Scenario Title:** `hedge_legs` sau bot start — đầy đủ các trường bắt buộc khi `lifecycle_state='active'`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-031, FR-EXBOT-025
**Test Type:** Data/State
**Description:** Sau khi bot start thành công và đạt `lifecycle_state='active'`, bảng `hedge_legs` phải có đầy đủ: `stop_price`, `stop_cloid`, `stop_order_id`, `stop_size`, `stop_distance_pct`, `entry_price`, `liquidation_price`, `effective_leverage`, `hl_account_address`. Không được có giá trị NULL trong các trường này.
**Test Focus:** Data/State

---

### Scenario ID: TS_UC-EXBOT-bot-start_056
**Scenario Title:** LP NFT sau bot start — được giữ bởi `BnzaExVault` (`positions.custodian='vault'`)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-070, uc-bot-start.md Postconditions
**Test Type:** Data/State
**Description:** Sau khi bot start thành công và LP NFT được mint, `positions.custodian='vault'` và `positions.custodian_address` trỏ đến địa chỉ `BnzaExVault` contract đúng trên chain tương ứng. NFT không nằm trong ví của user hay của ExBot Lambda.
**Test Focus:** On-chain<->off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-bot-start_057
**Scenario Title:** Sau bot start thành công — downstream dependency: bot được đưa vào scan queue cho light-check
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-012, FR-EXBOT-013, v5 audit §7
**Test Type:** Integration
**Description:** Ngay sau khi `lifecycle_state='active'`, bot được đưa vào scan queue cho light-check worker. `bots.next_light_check_at` được ghi với timestamp phù hợp (now + interval + jitter). Nếu `next_light_check_at` là NULL sau khi bot active, light-check sẽ không scan bot này.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_058
**Scenario Title:** Sau bot start — `hedge_legs.stop_price` non-NULL là điều kiện bắt buộc cho light-check stop trigger detection
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md FR-EXBOT-031, FR-EXBOT-032, v5 audit §7
**Test Type:** Integration
**Description:** `hedge_legs.stop_price` được ghi sau stop placement thành công. Light-check worker dùng giá trị này để phát hiện `markPrice >= stop_price` (trigger stop monitoring). Nếu `stop_price = NULL` sau bot-start (do stop placement chưa confirmed), light-check sẽ không detect stop trigger — đây là regression path cần verify sau mỗi bot-start.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-bot-start_059
**Scenario Title:** ExBot Lambda standalone — không co-deploy với OPERATOR (BR-EXBOT-010)
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** spec.md BR-EXBOT-010
**Test Type:** Integration
**Description:** `POST /api/exbot/start` phải được xử lý bởi ExBot Lambda riêng biệt (không phải OPERATOR service). Xác nhận: request không được xử lý bởi OPERATOR Worker; ExBot Lambda là standalone service nhận request qua API Gateway + HMAC Lambda Authorizer. Log và tracing phải chỉ ra ExBot Lambda riêng biệt với OPERATOR.
**Test Focus:** Integration

---


### Scenario ID: TS_UC-EXBOT-bot-start_060
**Scenario Title:** Acceptance Criteria AC-01 — bot start end-to-end: tất cả postconditions được thỏa mãn
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-01, spec.md FR-EXBOT-003, FR-EXBOT-031, FR-EXBOT-025
**Test Type:** Acceptance
**Description:** Với precondition đầy đủ (không có bot active, vault balance > 0, margin đủ, key_status='active', builder fee confirmed, LP sim pass), khi gọi `POST /api/exbot/start`, tất cả postconditions sau phải đúng: (1) `lifecycle_state='active'`; (2) `stop_price` được điền trong `hedge_legs`; (3) LP NFT trong BnzaExVault (`positions.custodian='vault'`); (4) `hedge_legs.entry_price`, `liq_price`, `effective_leverage` không NULL; (5) `bot_runtime_state.last_known_hl_short_size` không NULL.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-bot-start_061
**Scenario Title:** Acceptance Criteria AC-02 — one-bot policy với bot ở trạng thái `active`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-02, E-EXBOT-001
**Test Type:** Acceptance
**Description:** Với investor đang có ExBot `status='active'`, khi gọi `POST /api/exbot/start`, hệ thống trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không có bot record mới nào được tạo.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_062
**Scenario Title:** Acceptance Criteria AC-03 — one-bot policy với bot ở trạng thái `safe_mode`
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-03, E-EXBOT-001
**Test Type:** Acceptance
**Description:** Với investor đang có ExBot `status='safe_mode'`, khi gọi `POST /api/exbot/start`, hệ thống trả về HTTP 409 với message "You already have an active ExBot. Close or wait for the existing bot to finish." Không có bot record mới nào được tạo. `safe_mode` nằm trong danh sách `status IN ('active','paused','closing','safe_mode','error')` theo BR-EXBOT-001.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_063
**Scenario Title:** Acceptance Criteria AC-04 — vault balance = 0 blocks start
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-04, E-EXBOT-025
**Test Type:** Acceptance
**Description:** Với investor chưa deposit on-chain (`BnzaExVault` balance = 0), khi gọi `POST /api/exbot/start`, hệ thống trả về HTTP 400 với message "No confirmed deposit found. Please complete an on-chain deposit before starting the bot." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_064
**Scenario Title:** Acceptance Criteria AC-06 — `key_status='provisioning'` blocks start
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-06, E-EXBOT-017
**Test Type:** Acceptance
**Description:** Với investor có `hl_agent_keys.key_status='provisioning'` (key đang trong quá trình provision), khi gọi `POST /api/exbot/start`, hệ thống trả về HTTP 400 với message "Bot cannot start: agent key not yet provisioned. Please complete an on-chain deposit to trigger automatic setup." Không tạo bot record.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_065
**Scenario Title:** Acceptance Criteria AC-09 — LP mint revert: `lifecycle_state='error'`, không có tiền di chuyển
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-09, E-EXBOT-028
**Test Type:** Acceptance
**Description:** Sau khi preflight pass, khi `vaultMint()` tx revert hoặc timeout, hệ thống trả về HTTP 502 với E-EXBOT-028 "Bot startup failed: LP mint transaction did not complete. No funds were moved. Please try again or contact support." `lifecycle_state='error'`. Xác nhận: không có tiền di chuyển; positions table sạch.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_066
**Scenario Title:** Acceptance Criteria AC-10 — HL unreachable tại hedge open: `safe_mode` + auto-recovery enqueued
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-10, spec.md FR-EXBOT-050
**Test Type:** Acceptance
**Description:** Sau khi preflight pass và LP mint success, khi HL API unreachable tại bước hedge open, hệ thống ghi `lifecycle_state='hedge_pre_open' -> 'safe_mode'`. Auto-recovery per FR-EXBOT-050 được enqueue. Xác nhận: (1) state là `safe_mode` (không phải `error`); (2) auto-recovery message tồn tại trong queue.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_067
**Scenario Title:** Acceptance Criteria AC-11 — HL reject IOC: `safe_mode` + E-EXBOT-026
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-11, E-EXBOT-026
**Test Type:** Acceptance
**Description:** Sau khi preflight pass và LP mint success, khi HL reject IOC order, hệ thống ghi `lifecycle_state='hedge_pre_open' -> 'safe_mode'`. E-EXBOT-026 "Hedge order rejected by Hyperliquid. Bot entered Safe Mode." được logged. Auto-recovery per FR-EXBOT-050 được enqueue.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-bot-start_068
**Scenario Title:** Acceptance Criteria AC-15 — stop_price populated, tính bằng BigDecimal với safetyFactor=0.70
**UC Reference:** UC-EXBOT-bot-start — Start ExBot
**Req-ID:** v5 audit AC-15, spec.md FR-EXBOT-030, NFR-EXBOT-008
**Test Type:** Acceptance
**Description:** Sau khi bot start thành công, `hedge_legs.stop_price` khác NULL và được tính chính xác bằng BigDecimal với `stopSafetyFactor = 0.70`. Với `entry_price = $3,000`, `liq_price = $3,300`: `stop_price = $3,210.00` (không có float error). `stop_price < liq_price` (stop fires trước liquidation price).
**Test Focus:** Boundary

---

## Bảng mã viết tắt

| Code / Prefix | Nghia + vai tro trong du an | Dinh nghia |
|---|---|---|
| BR-EXBOT-* | Business Rule ExBot — quy tac nghiep vu rang buoc toan bo module ExBot | spec.md §BR |
| E-EXBOT-* | Error code ExBot — ma loi/canh bao he thong cho ExBot module | message-list.md EXBOT section |
| FR-EXBOT-* | Functional Requirement ExBot — yeu cau chuc nang trong spec.md (canonical) | srs/spec.md |
| NFR-EXBOT-* | Non-Functional Requirement ExBot — yeu cau phi chuc nang | spec.md §NFR |
| AC-* | Acceptance Criteria — dieu kien chap nhan trong user story va audit report | us-001.md, v5 audit §8 |
| IOC | Immediate-Or-Cancel — loai lenh giao dich tren Hyperliquid: khop ngay hoac huy | Loai lenh giao dich |
| KMS | AWS Key Management Service — dich vu luu tru va ky bang khoa mat ma | AWS service |
| HL | Hyperliquid — san giao dich perpetual phi tap trung duoc dung de mo short hedge | Proper noun (platform) |
| BigDecimal | Kieu du lieu so chinh xac tuy y — dung de tranh sai so float trong tinh toan tai chinh | NFR-EXBOT-008 |
| LP | Liquidity Provider / Liquidity Position — vi the cung thanh khoan tren Uniswap V3 | industry term |

---

## Bien doi trang thai toan bo

| Tu trang thai | Den trang thai | Dieu kien | Ket qua neu sai |
|---|---|---|---|
| idle | preflight | POST /api/exbot/start; 6 preflight checks pass | Khong co transition |
| preflight | lp_opening | Bot record created; goi vaultMint() | Preflight fail -> khong co transition; fail request |
| lp_opening | lp_opened | VaultMinted event nhan duoc thanh cong | lp_opening -> error (neu revert/timeout, E-EXBOT-028) |
| lp_opened | hedge_pre_open | LP position duoc luu; chuan bi gui IOC | Khong co path loi tu lp_opened trong bot-start |
| hedge_pre_open | hedge_post_confirmed | IOC khop; reconcile xac nhan actual size | hedge_pre_open -> safe_mode (HL fail/reject: A7/A10) |
| hedge_post_confirmed | stop_placing | Tinh stop_trigger_px; bat dau gui stop order | A11: drift > threshold -> partial_repair, giu o hedge_post_confirmed |
| stop_placing | stop_verified | Stop order duoc HL confirm | stop_placing -> safe_mode (A8: stop fail) |
| stop_verified | active | All postconditions met | Khong co path loi tu stop_verified trong bot-start |
| lp_opening | error | vaultMint() revert/timeout (E-EXBOT-028) | Funds khong di chuyen |
| hedge_pre_open | safe_mode | HL unreachable (A7) hoac HL reject IOC (A10) | KHONG duoc chuyen sang error |
| stop_placing | safe_mode | Stop placement fail (A8) | KHONG duoc chuyen sang error |

---

## Out-of-Scope Flags

| Khu vuc scenario | Ly do | Hanh dong de nghi |
|---|---|---|
| A11 — Boundary test reconcile mismatch (drift_threshold chinh xac) | BLOCKED: OQ-EXBOT-011 — zen chua xac nhan formula `lpValueUsd x 3%`. TS_UC-EXBOT-bot-start_047 cover behavior logic nhung khong test gia tri boundary cu the. | Resolve qua qc-qna khi zen confirm OQ-EXBOT-011; sau do add boundary scenarios. |
| weth_index per-chain test voi pool address cu the (Base/Optimism) | BLOCKED: OQ-EXBOT-03 — pool addresses chua duoc zen xac nhan. TS_037/038 cover intent nhung khong co gia tri test cu the. | Resolve khi OQ-EXBOT-03 Closed; sau do update scenarios voi pool address chinh xac. |
| Builder fee HL endpoint weight va rate limit detail (preflight step 5) | BLOCKED: OQ-EXBOT-05 — HL endpoint va weight cho builder fee check chua duoc xac nhan. TS_024 cover functional block nhung khong verify rate limit. | Resolve khi OQ-EXBOT-05 Closed. |
| BnzaExVault contract internals (fund return mechanism khi LP mint fail) | BLOCKED: OQ-EXBOT-08 — BnzaExVault ABI chua duoc zen confirm. TS_034/035 cover state transition sang error nhung khong verify co che refund on-chain. | Resolve khi OQ-EXBOT-08 Closed. |
| Performance / load testing | Out-of-scope — khong thuoc functional/integration | Chuyen cho chuyen gia performance testing |
| Security testing ngoai functional auth (penetration, OWASP) | Out-of-scope — vuot ngoai pham vi skill nay | Chuyen cho security specialist |

