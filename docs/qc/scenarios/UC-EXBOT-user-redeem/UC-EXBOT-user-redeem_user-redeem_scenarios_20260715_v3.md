# Test Scenarios — UC-EXBOT-user-redeem User-Initiated Redemption

> Source: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260715_v5.md (87/100 — Conditionally Ready)
> Generated: 2026-07-15
> Domain/Architecture: AWS Lambda + Aurora PostgreSQL + Redis Redlock (ElastiCache) + SQS FIFO + Hyperliquid API + BnzaExVault (on-chain) — logic-only, no UI

---

## UC-EXBOT-user-redeem — User-Initiated Redemption (LP-First)

---

### Scenario ID: TS_UC-EXBOT-user-redeem_001
**Scenario Title:** Happy path — full redemption flow, bot in `active` state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 main flow; FR-EXBOT-070; US-EXBOT-004 AC-004-1
**Test Type:** End-to-End
**Description:** Gọi `BnzaExVault.redeem(tokenId)` on-chain với bot đang ở `lifecycle_state = active`; xác nhận LP bị thanh lý và LP-portion USDC trả về investor trong cùng giao dịch on-chain; xác nhận `close_operations` đi qua đủ 6 trạng thái (`requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done`); xác nhận HL position size = 0 sau reconcile; xác nhận `bots.lifecycle_state = closed` sau khi hoàn tất.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_002
**Scenario Title:** Happy path — bot in `paused` state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); qc-responses-2026-07-14.md I-N1
**Test Type:** Functional
**Description:** Gọi `BnzaExVault.redeem(tokenId)` với bot đang ở `lifecycle_state = paused`; xác nhận luồng redeem được xử lý bình thường — không bị reject vì trạng thái `paused`; xác nhận `close_operations` đi qua đủ các transitions và bot chuyển sang `closed`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_003
**Scenario Title:** Happy path — bot in `hedge_stopped_cooldown` state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); states.md State Registry; qc-responses-2026-07-14.md I-N1
**Test Type:** Functional
**Description:** Gọi `BnzaExVault.redeem(tokenId)` với bot đang ở `lifecycle_state = hedge_stopped_cooldown`; xác nhận on-chain contract không kiểm tra `lifecycle_state` và LP NFT vẫn trong BnzaExVault — giao dịch được thực thi thành công; xác nhận Redeem Worker xử lý message và đóng hedge bình thường.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_004
**Scenario Title:** Happy path — bot in `safe_mode` state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); states.md; qc-responses-2026-07-14.md I-N1
**Test Type:** Functional
**Description:** Gọi `BnzaExVault.redeem(tokenId)` với bot đang ở `lifecycle_state = safe_mode`; xác nhận redeem được xử lý — SAFE_MODE không block user_redeem (LP NFT vẫn trong vault); xác nhận sau khi hedge close thành công, bot chuyển sang `closed` thay vì quay lại `active`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_005
**Scenario Title:** Happy path — bot in `error` state
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); states.md; qc-responses-2026-07-14.md I-N1
**Test Type:** Functional
**Description:** Gọi `BnzaExVault.redeem(tokenId)` với bot đang ở `lifecycle_state = error`; xác nhận on-chain `BnzaExVaultImpl` không có `lifecycle_state` gate và giao dịch được thực thi; xác nhận Redeem Worker xử lý bình thường kể cả khi bot ở `error` state.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_006
**Scenario Title:** Pre-state: `lp_rebalancing` — `redeem(oldTokenId)` revert an toàn mid-rebalance
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); qc-responses-2026-07-14.md I-N1; states.md
**Test Type:** Functional
**Description:** Trong khi bot đang ở `lifecycle_state = lp_rebalancing` (đang dùng `oldTokenId`), investor gọi `redeem(oldTokenId)` on-chain; xác nhận giao dịch revert an toàn vì LP NFT đã bị burn trong quá trình rebalance; xác nhận sau khi rebalance hoàn tất, `redeem(newTokenId)` thành công và luồng tiếp tục bình thường.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_007
**Scenario Title:** close_operations state machine — transition đầy đủ `requested → done`
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 3–16 (v5); flows.md F-04; states.md close_operations
**Test Type:** Data/State
**Description:** Sau khi Redeem Worker nhận message, kiểm tra DB `close_operations` ở mỗi bước: (1) state = `requested` ngay sau INSERT; (2) state = `lp_closed` sau khi on-chain confirm; (3) state = `funds_returned` sau khi LP-portion USDC trả về; (4) state = `hedge_close_pending` ngay sau khi acquire User Lock, trước khi gọi HL; (5) state = `hedge_closed` sau reconcile size=0; (6) state = `done` sau khi HL-portion gửi xong; xác nhận không có transition nào bị bỏ qua.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_008
**Scenario Title:** `hedge_close_pending` recovery checkpoint — Lambda crash sau lock acquire
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 9 (v5); qc-responses-2026-07-14.md I-N3; flows.md F-04
**Test Type:** Functional
**Description:** Simulate Lambda crash sau khi acquire User Lock và cập nhật `close_operations.state = hedge_close_pending`, nhưng trước khi gọi `closeShortReduceOnlyIoc`; xác nhận recovery worker đọc được `hedge_close_pending` và xác định hedge close đang in-progress; xác nhận recovery worker có thể resume mà không mở HL position mới hoặc bỏ sót hedge close.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_009
**Scenario Title:** Idempotency — SQS redelivers message sau khi close_operations đã INSERT
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; flows.md F-04; FR-EXBOT-070; project-context-master §7.1
**Test Type:** Integration
**Description:** Deliver lại SQS FIFO message `{botId, redeemTxHash, userAddress}` sau khi `close_operations` đã tồn tại; xác nhận Redeem Worker phát hiện idempotency row và thoát mà không tạo duplicate `close_operations` row, không gọi HL lần thứ hai, không double-send HL-portion USDC; final state không thay đổi.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_010
**Scenario Title:** User Lock — lock ordering: INSERT `close_operations` TRƯỚC khi acquire lock
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; flows.md F-04; FR-EXBOT-092; qc-responses-2026-07-14.md I-03
**Test Type:** Data/State
**Description:** Với network partition hoặc Redlock unavailable NGAY SAU khi INSERT `close_operations`, xác nhận `close_operations` row với `state = requested` vẫn tồn tại trong DB (idempotency đảm bảo); xác nhận khi Redlock recover, worker có thể acquire lock và resume từ đúng checkpoint; không có orphan lock; không mất trạng thái.
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_011
**Scenario Title:** User Lock contention — hedge-sync worker đang giữ lock
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A1; flows.md F-04; FR-EXBOT-092; NFR-EXBOT-003
**Test Type:** Integration
**Description:** Hedge-sync worker đang giữ User Lock (TTL=90s) khi Redeem Worker cố acquire với `idempotencyKey = user-redeem:{botId}:{redeemTxHash}`; xác nhận `acquired=false` → Redeem Worker re-queue message với delay; xác nhận SLA clock tiếp tục chạy từ event detection (không reset); xác nhận khi lock được giải phóng, lần re-deliver kế tiếp xử lý thành công.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_012
**Scenario Title:** SLA breach — tổng delay từ lock contention > 5 phút
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A1; NFR-EXBOT-003; E-EXBOT-010
**Test Type:** Functional
**Description:** Simulate chuỗi lock contention dẫn đến tổng thời gian từ event detection đến lock acquire > 5 phút; xác nhận admin và investor nhận cảnh báo E-EXBOT-010 ("Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned."); xác nhận LP-portion đã được trả và không bị đảo ngược (BR-EXBOT-006).
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_013
**Scenario Title:** User Lock idempotencyKey uniqueness — cùng `botId` khác `redeemTxHash`
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; FR-EXBOT-092; flows.md F-04
**Test Type:** Data/State
**Description:** Hai redeem event với cùng `botId` nhưng khác `redeemTxHash` đến gần nhau; xác nhận `idempotencyKey = user-redeem:{botId}:{redeemTxHash}` là unique per transaction — mỗi event được xử lý độc lập và không nhầm lẫn idempotency giữa hai event; xác nhận chỉ có một `close_operations` row được tạo (bot đã `lp_closing` sau event đầu tiên).
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_014
**Scenario Title:** `closeShortReduceOnlyIoc` — HL reject lần 1, thành công lần 2 (in-invocation retry)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 10 (v5); qc-responses-2026-07-14.md I-N2; FR-EXBOT-022
**Test Type:** Functional
**Description:** HL reject `closeShortReduceOnlyIoc` lần 1 (ví dụ: rate limit hoặc timeout); worker retry lần 2 trong cùng Lambda invocation, bên trong Redlock-acquired block; HL chấp nhận lần 2; xác nhận hedge close thành công mà không re-queue SQS, không thoát Redlock block giữa chừng; `close_operations.state` advance đúng sang `hedge_closed`.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_015
**Scenario Title:** `closeShortReduceOnlyIoc` — cloid deterministic: retry dùng cùng cloid không double-apply
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 10 (v5); FR-EXBOT-022; project-context-master §7.1
**Test Type:** Functional
**Description:** Retry `closeShortReduceOnlyIoc` với `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` — xác nhận HL nhận diện cloid đã được xử lý và không double-close; HL position size = 0 sau một lần close duy nhất kể cả khi gửi lại nhiều lần.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_016
**Scenario Title:** `closeShortReduceOnlyIoc` — thất bại 3 lần liên tiếp (A2: residual_hl_liability)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2; BR-EXBOT-006; E-EXBOT-024; US-EXBOT-004 AC-004-3
**Test Type:** Functional
**Description:** HL reject `closeShortReduceOnlyIoc` 3 lần liên tiếp trong cùng Lambda invocation; xác nhận sau lần 3: `close_operations.state = residual_hl_liability`, `bots.lifecycle_state = error`, User Lock được release, admin nhận E-EXBOT-024 ("User redemption hedge close failed. Manual intervention required."); xác nhận LP-portion USDC đã trả về investor KHÔNG bị đảo ngược (BR-EXBOT-006).
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_017
**Scenario Title:** Reconcile mismatch — HL position ≠ 0 sau `closeShortReduceOnlyIoc`
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2; qc-responses-2026-07-14.md I-08; BR-EXBOT-006; E-EXBOT-024
**Test Type:** Functional
**Description:** `closeShortReduceOnlyIoc` báo success nhưng `reconcilePosition` xác nhận HL position size ≠ 0 (partial fill hoặc mismatch); xác nhận outcome giống A2: `close_operations.state = residual_hl_liability`, `bots.lifecycle_state = error`, admin nhận E-EXBOT-024; xác nhận SAFE_MODE KHÔNG được kích hoạt (LP đã thanh lý — không còn gì để bảo vệ); LP-portion không bị đảo ngược.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_018
**Scenario Title:** A2: SAFE_MODE không áp dụng khi LP đã liquidated
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2; BR-EXBOT-007; qc-responses-2026-07-14.md I-08
**Test Type:** Functional
**Description:** Khi hedge close thất bại trong luồng user_redeem (A2 path), xác nhận hệ thống KHÔNG chuyển bot sang `safe_mode`; xác nhận `bots.lifecycle_state` chuyển thẳng sang `error` (không qua safe_mode); xác nhận không có hedge-sync suppression dựa trên safe_mode vì LP đã không còn tồn tại.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_019
**Scenario Title:** BR-EXBOT-006 — LP-portion repayment unconditional trong mọi outcome
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** BR-EXBOT-006; UC-EXBOT-user-redeem §4 A2; US-EXBOT-004 AC-004-2/3
**Test Type:** Functional
**Description:** Chạy 3 kịch bản khác nhau: (1) hedge close thành công, (2) hedge close thất bại hoàn toàn (A2), (3) SLA breach (A1); xác nhận trong cả 3 kịch bản, LP-portion USDC đã được trả về investor on-chain trong giao dịch `BnzaExVault.redeem(tokenId)` và không bị block hoặc đảo ngược bởi bất kỳ outcome nào của hedge close.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_020
**Scenario Title:** `cancelStop` via §19.5 replaceStopProtected — stop bị hủy sau hedge close
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 11 (v5); project-context-master §7.1 INV-STOP
**Test Type:** Functional
**Description:** Sau khi `closeShortReduceOnlyIoc` thành công (HL position = 0), xác nhận `cancelStop` được gọi với `size=0` qua §19.5 `replaceStopProtected`; xác nhận stop order trên HL bị hủy; xác nhận không còn active stop sau khi HL position = 0 (INV-STOP invariant: khi short = 0, không cần stop).
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_021
**Scenario Title:** User Lock TTL boundary — lock expire trong khi HL operation đang chạy
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; FR-EXBOT-092 (TTL=90s); flows.md F-04
**Test Type:** Functional
**Description:** Simulate tình huống HL operations (`closeShortReduceOnlyIoc` + retry) kéo dài gần hết TTL=90s của User Lock; xác nhận lock không auto-expire trong khi critical section đang thực thi (hoặc extend() được gọi trước khi hết TTL); xác nhận không có race condition với hedge-sync worker trong cùng khoảng thời gian.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-user-redeem_022
**Scenario Title:** On-chain ↔ off-chain consistency — `RedemptionEvent` emit và SQS enqueue
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 1–2; flows.md F-04; US-EXBOT-004 AC-004-1
**Test Type:** Integration
**Description:** `BnzaExVault.redeem(tokenId)` on-chain thành công và emit `RedemptionEvent(botId, redeemTxHash, userAddress)`; xác nhận Event Watcher detect event trong SLA window và enqueue message đúng vào SQS FIFO với đủ 3 fields (`botId`, `redeemTxHash`, `userAddress`); xác nhận không có message bị mất hoặc duplicate trong quá trình event → queue.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_023
**Scenario Title:** On-chain ↔ off-chain consistency — LP-portion USDC trả về on-chain, off-chain state advance
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 2; flows.md F-04; states.md close_operations
**Test Type:** Integration
**Description:** Sau khi `BnzaExVault.redeem(tokenId)` xác nhận on-chain (LP-portion USDC trả về investor), xác nhận off-chain `close_operations.state` advance từ `lp_closed → funds_returned` đúng thứ tự và chỉ sau khi on-chain confirmation; xác nhận không có state advance khi on-chain transaction chưa confirmed.
**Test Focus:** On-chain↔off-chain consistency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_024
**Scenario Title:** HL-portion USDC transfer — Worker + Operator thực hiện, tx hash không lưu
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 13–14 (v5); qc-responses-2026-07-14.md I-02bc
**Test Type:** Functional
**Description:** Sau khi hedge đóng thành công, xác nhận HL-portion USDC được gửi qua RedemptionQueue ledger bởi Worker + Operator address (không qua facade trung gian riêng); xác nhận `close_operations.hedge_close_tx` KHÔNG được cập nhật với transaction hash; xác nhận investor nhận đúng HL-portion (giá trị cụ thể — xem note I-02a).
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_025
**Scenario Title:** `bots.lifecycle_state = closed` sau happy path
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §5 Postconditions; states.md; US-EXBOT-004 AC-004-1
**Test Type:** Data/State
**Description:** Sau khi user_redeem hoàn tất thành công, xác nhận `bots.lifecycle_state = closed` và `bots.status = closed` trong Aurora PostgreSQL; xác nhận bot không còn xuất hiện trong kết quả scan worker (`status = active`); xác nhận hedge-sync, light-check, deep-audit đều skip bot này sau khi `lifecycle_state = closed`.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_026
**Scenario Title:** `bots.lifecycle_state = error` sau A2 hedge failure
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §4 A2 postconditions; qc-responses-2026-07-14.md I-06; states.md
**Test Type:** Data/State
**Description:** Sau khi hedge close thất bại (A2 path), xác nhận `bots.lifecycle_state = error` và `bots.status = error` trong DB; xác nhận `close_operations.state = residual_hl_liability`; xác nhận `close_operations.residual_amount` được set với outstanding HL liability amount; xác nhận bot ở trạng thái yêu cầu xử lý manual từ admin.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_027
**Scenario Title:** Invalid transition — cố redeem bot đã ở `lp_closing`
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); states.md State Registry
**Test Type:** Data/State
**Description:** Bot đang ở `lifecycle_state = lp_closing` (đang trong quá trình close); investor cố gọi `BnzaExVault.redeem(tokenId)` lần nữa; xác nhận on-chain transaction xử lý theo behavior của contract (tokenId đã không còn hoặc đang trong trạng thái closing); xác nhận hệ thống off-chain không tạo duplicate `close_operations` row nếu một row đã tồn tại.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_028
**Scenario Title:** Invalid transition — cố redeem bot đã `closed`
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §2 Preconditions (v5); states.md State Registry
**Test Type:** Data/State
**Description:** Bot đã ở `lifecycle_state = closed` (đã close trước đó); investor cố gọi `BnzaExVault.redeem(tokenId)` lần hai với cùng `tokenId`; xác nhận on-chain transaction revert (LP NFT đã burned không thể redeem lại); xác nhận không có `close_operations` row mới được tạo; hệ thống off-chain không xử lý duplicate event.
**Test Focus:** State transition

---

### Scenario ID: TS_UC-EXBOT-user-redeem_029
**Scenario Title:** SQS FIFO message delivery order — user_redeem queue nhận trước hedge-sync queue
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; flows.md F-04; project-context-master §7.3
**Test Type:** Integration
**Description:** Cả user_redeem message và hedge-sync message cùng được enqueue trong cùng khoảng thời gian; xác nhận user_redeem SQS FIFO queue có độ ưu tiên cao nhất và được deliver trước hedge-sync queue; xác nhận bot không bị hedge-sync mutation trong khi user_redeem đang trong critical section (User Lock ngăn chặn).
**Test Focus:** Integration

---

### Scenario ID: TS_UC-EXBOT-user-redeem_030
**Scenario Title:** Concurrency — user_redeem và hedge-sync cùng cố acquire User Lock
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; FR-EXBOT-092; flows.md F-04
**Test Type:** Integration
**Description:** user_redeem worker và hedge-sync worker cùng cố acquire User Lock với cùng `botId` cùng lúc; xác nhận Redlock đảm bảo chỉ một worker acquire thành công (`acquired=true`); worker còn lại nhận `acquired=false` và xử lý theo behavior đúng (hedge-sync re-queue, user_redeem re-queue với SLA tracking); xác nhận không có double mutation.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_031
**Scenario Title:** Idempotency — User Lock `idempotencyKey` ngăn double close khi lock contention resolve
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; FR-EXBOT-092; qc-responses-2026-07-14.md I-03
**Test Type:** Integration
**Description:** Sau khi Redeem Worker bị re-queue do `acquired=false`, một Redeem Worker khác (từ SQS redelivery) cũng cố acquire lock với cùng `idempotencyKey = user-redeem:{botId}:{redeemTxHash}`; xác nhận Redlock idempotencyKey đảm bảo chỉ một worker trong số các workers re-queued thực sự acquire được lock và thực hiện hedge close; không có double-close.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_032
**Scenario Title:** HL `reconcilePosition` — HL timeout trong khi lock đang giữ
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3 step 12 (v5); FR-EXBOT-092; flows.md F-04
**Test Type:** Functional
**Description:** `reconcilePosition` call đến HL bị timeout hoặc error trong khi User Lock đang giữ; xác nhận behavior: worker xử lý timeout như thế nào (timeout tính vào retry count không, hay riêng biệt); xác nhận User Lock được release đúng cách kể cả khi reconcile timeout; xác nhận không có dangling lock.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_033
**Scenario Title:** NFR-EXBOT-003 — SLA boundary: hedge close hoàn thành đúng 5 phút
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** NFR-EXBOT-003; UC-EXBOT-user-redeem §4 A1; E-EXBOT-010
**Test Type:** Functional
**Description:** Hedge close hoàn thành trong đúng 5 phút tính từ event detection (boundary value tại limit); xác nhận không có SLA breach alert (E-EXBOT-010) được gửi; xác nhận `close_operations.state = done` và `bots.lifecycle_state = closed` được set trước hoặc đúng deadline.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-user-redeem_034
**Scenario Title:** NFR-EXBOT-003 — SLA boundary: hedge close hoàn thành trước 5 phút (limit − ε)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** NFR-EXBOT-003; E-EXBOT-010
**Test Type:** Functional
**Description:** Hedge close hoàn thành ở t = 4 phút 59 giây (dưới limit); xác nhận E-EXBOT-010 KHÔNG được gửi; flow kết thúc bình thường.
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-user-redeem_035
**Scenario Title:** NFR-EXBOT-003 — SLA breach: hedge close vượt 5 phút (limit + ε)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** NFR-EXBOT-003; E-EXBOT-010
**Test Type:** Functional
**Description:** Hedge close chưa hoàn thành ở t = 5 phút 1 giây (vượt limit); xác nhận E-EXBOT-010 ("Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned.") được gửi đến admin và investor; xác nhận LP-portion đã trả không bị ảnh hưởng (BR-EXBOT-006).
**Test Focus:** Boundary

---

### Scenario ID: TS_UC-EXBOT-user-redeem_036
**Scenario Title:** `close_operations` — không cho phép tạo row mới nếu row với `kind=user_redeem` và `botId` đã tồn tại
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §3; flows.md F-04; states.md close_operations
**Test Type:** Data/State
**Description:** Khi `close_operations` row với `kind=user_redeem` và `botId` đã tồn tại (đang ở bất kỳ state nào ngoài `done`), một second event cùng `redeemTxHash` cố INSERT row mới; xác nhận UNIQUE constraint hoặc idempotency check ngăn duplicate INSERT; xác nhận worker trả về hoặc resume từ row hiện có.
**Test Focus:** Idempotency/Concurrency

---

### Scenario ID: TS_UC-EXBOT-user-redeem_037
**Scenario Title:** E2E — full redemption flow từ on-chain call đến `lifecycle_state = closed`, US-004 AC-004-1
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** US-EXBOT-004 AC-004-1; UC-EXBOT-user-redeem main flow; NFR-EXBOT-003
**Test Type:** Acceptance
**Description:** Chạy đầy đủ luồng US-EXBOT-004 AC-004-1: LP liquidated on-chain → user_redeem job enqueued → hedge closed trong vòng 5 phút → HL-portion USDC gửi cho investor → `lifecycle_state = closed`; xác nhận mỗi acceptance criterion của US-004 AC-004-1 được thỏa mãn theo đúng thứ tự.
**Test Focus:** Happy path

---

### Scenario ID: TS_UC-EXBOT-user-redeem_038
**Scenario Title:** E2E — SLA breach path, US-004 AC-004-2
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** US-EXBOT-004 AC-004-2; UC-EXBOT-user-redeem §4 A1; E-EXBOT-010; BR-EXBOT-006
**Test Type:** Acceptance
**Description:** Chạy đầy đủ luồng US-EXBOT-004 AC-004-2: LP liquidated → hedge close exceed 5 min SLA → admin alert (E-EXBOT-010) → LP-portion không bị đảo ngược (BR-EXBOT-006); xác nhận mỗi AC-004-2 criterion được thỏa mãn.
**Test Focus:** Alternative flow

---

### Scenario ID: TS_UC-EXBOT-user-redeem_039
**Scenario Title:** E2E — hedge close failure (residual HL liability), US-004 AC-004-3
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** US-EXBOT-004 AC-004-3; UC-EXBOT-user-redeem §4 A2; E-EXBOT-024; BR-EXBOT-006
**Test Type:** Acceptance
**Description:** Chạy đầy đủ luồng US-EXBOT-004 AC-004-3: LP liquidated → hedge close thất bại → `close_operations.state = residual_hl_liability` → `bots.lifecycle_state = error` → admin nhận E-EXBOT-024 ("User redemption hedge close failed. Manual intervention required.") → LP-portion không bị đảo ngược; xác nhận mỗi AC-004-3 criterion được thỏa mãn.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_040
**Scenario Title:** AC-007 — hedge_close_pending recovery checkpoint (Acceptance)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §F.5 AC-007; UC §3 step 9 (v5); qc-responses-2026-07-14.md I-N3
**Test Type:** Acceptance
**Description:** Xác nhận AC-007: nếu Lambda crash sau khi `close_operations.state = hedge_close_pending` được set, recovery worker đọc trạng thái này và xác định hedge close đang in-progress; recovery worker có thể resume hedge close mà không mở position mới hoặc double-close; `close_operations` cuối cùng advance sang `hedge_closed` hoặc `residual_hl_liability`.
**Test Focus:** Error/Exception

---

### Scenario ID: TS_UC-EXBOT-user-redeem_041
**Scenario Title:** AC-008 — HL-portion transfer tx hash không được lưu vào DB (Acceptance)
**UC Reference:** UC-EXBOT-user-redeem — User-Initiated Redemption
**Req-ID:** UC-EXBOT-user-redeem §F.5 AC-008; qc-responses-2026-07-14.md I-02bc
**Test Type:** Acceptance
**Description:** Sau khi hedge close và HL-portion transfer hoàn thành, query `close_operations.hedge_close_tx` trong Aurora PostgreSQL; xác nhận field này là NULL / không được populate với transaction hash; xác nhận cả hai: HL-portion được gửi thành công VÀ field không được lưu — đây là behavior được thiết kế, không phải bug.
**Test Focus:** Integration

---

## ⚠️ Out-of-Scope Flags

| Scenario Area | Reason | Recommended Action |
|---|---|---|
| HL-portion amount formula — expected value verification (step 13) | BLOCKED: I-02a (High) — công thức tính HL-portion amount chưa được BA/Tech Lead định nghĩa. Không có source of truth cho số tiền cụ thể investor nhận từ HL portion. | Resolve I-02a qua qc-qna + re-audit UC trước khi thiết kế test case cho step 13 expected amount. Sau khi BA confirm formula, bổ sung scenario cho HL-portion amount boundary/negative. |
| Performance / load testing | NFR: PERFORMANCE — SLA 5 min là functional SLA trace (covered by TS_033-035), không phải load test | Defer to performance specialist sau khi ExBot Phase A deploy vào staging. |
| Security testing (key management, HL API auth) | NFR: SECURITY — nằm ngoài phạm vi functional scenario design | Đưa vào security review riêng với spec FR-EXBOT-080 (KMS) và agent key rotation. |
