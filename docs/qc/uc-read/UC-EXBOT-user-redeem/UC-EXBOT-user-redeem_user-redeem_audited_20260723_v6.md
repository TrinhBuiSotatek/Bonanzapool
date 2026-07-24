---
title: "UC Readiness Review — UC-EXBOT-user-redeem (User-Initiated Redemption)"
date_created: 2026-07-23
author: QC UC Read ExBot Agent
version: v6
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-user-redeem.md (updated 2026-07-20)
prior_report: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260715_v5.md
---

# UC Readiness Review — UC-EXBOT-user-redeem v6

## Feature Brief

**UC-EXBOT-user-redeem** mô tả luồng đổi thưởng do nhà đầu tư khởi tạo cho ExBot managed LP-hedge bot. Đây là luồng LP-first với bảo đảm trên chuỗi: nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` trực tiếp on-chain, lập tức thanh lý LP và hoàn trả LP-portion USDC trong cùng một giao dịch. Sau đó, Redeem Worker ngoài chuỗi đóng vị thế short hedge trên HL theo SLA 5 phút, rồi thực hiện chuỗi settlement HL-portion: `hl_withdraw → hl_fulfill` để gửi USDC cho nhà đầu tư qua `RedemptionQueue.fulfillRequest` on-chain (FIFO).

**Thay đổi trong phiên bản này (audit v6 — 2026-07-23):** BA đã cập nhật `uc-user-redeem.md` vào ngày 2026-07-20 với step 14 được mở rộng thành 3 sub-steps (14a/14b/14c): (14a) `hl_withdraw` — tính `principal_amount = initial clearinghouseState.withdrawable − final`, ghi vào `redemption_requests.principal_amount`; (14b) `hl_fulfill` — kiểm tra thanh khoản operator, bỏ qua CCTP nếu đã đủ tiền (reserved liquidity), hoặc burn/mint CCTP nếu thiếu; (14c) `RedemptionQueue.fulfillRequest` on-chain FIFO. I-02a (câu hỏi mở duy nhất từ v5) đã được giải đáp đầy đủ. Audit này đánh giá toàn bộ chuỗi settlement mới và phát hiện một số gap tài liệu mới trong ERD, states.md, flows.md, và liên kết tài liệu BA.

**Score v5: 87/100 — Conditionally Ready.** Re-audit này dự kiến cải thiện score cho Areas 2, 3 nhờ I-02a đóng, nhưng phát hiện thêm gap mới ở Area 4, 5.

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case ID — module ExBot | usecases/index.md |
| FR-EXBOT-* | Functional Requirement — ExBot SRS spec | srs/spec.md |
| BR-EXBOT-* | Business Rule — module ExBot | srs/spec.md §4 Business Rules |
| E-EXBOT-* | Mã lỗi / thông báo — ExBot | backbone/message-list.md |
| SLA | Service Level Agreement — ràng buộc thời gian cho thao tác bất đồng bộ. Trong UC này: hedge close ≤ 5 phút từ khi phát hiện sự kiện (NFR-EXBOT-003). | industry term |
| HL | Hyperliquid — sàn perpetual DEX bên ngoài dùng để mở vị thế short delta-hedge | proper noun |
| LP | Liquidity Provider — vị thế Uniswap V3 do BnzaExVault quản lý; khi redeem, LP bị thanh lý on-chain | industry term |
| IOC | Immediate-or-Cancel — loại lệnh HL dùng cho hedge close (`closeShortReduceOnlyIoc`) | industry term |
| Redlock | Redis Redlock — thuật toán distributed mutex, ngăn nhiều worker cùng thực hiện HL mutation cho một bot | industry term |
| CCTP | Circle Cross-Chain Transfer Protocol — giao thức burn-and-mint để chuyển USDC qua chain. Trong UC này: burn USDC trên Arbitrum, mint trên Base/Optimism để operator thanh toán cho nhà đầu tư. | industry term |
| FIFO | First-In First-Out — thứ tự thanh toán bắt buộc của `RedemptionQueue.fulfillRequest` on-chain. Contract revert nếu request không phải đầu hàng đợi. | industry term |

---

## §0 Scope & Linked Artifacts

| Item | Value |
|---|---|
| UC ID | UC-EXBOT-user-redeem |
| Linked User Story | US-EXBOT-004 |
| FR Trace (UC §7 — updated 2026-07-20) | FR-EXBOT-070 |
| SRS Baseline | srs/spec.md, srs/states.md, srs/flows.md, srs/erd.md (as of 2026-07-20) |
| FRD Baseline | frd.md (as of 2026-07-14 — FR renumbering: 091=Rate Limiter, 092=User Lock, 093=Pool Slot0 Cache) |
| BA Responses | docs/BA/qc-responses-2026-07-14.md; docs/BA/qc-responses-2026-07-20.md |
| BA Settlement Flow Doc | docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/flow-withdraw-close-settlement-ba.md (created 2026-07-15) |
| Prior audit | UC-EXBOT-user-redeem_user-redeem_audited_20260715_v5.md (Conditionally Ready, 87/100) |

---

## §1 Summary of Changes (2026-07-20 Updates)

### A. UC file changes (2026-07-20)

| Location | Before (v5 baseline) | After (v6) | Impact |
|---|---|---|---|
| §3 step 14 | "HL-portion settlement" — chỉ 1 dòng mô tả tổng quát: "send HL-portion USDC to user via RedemptionQueue ledger" | Mở rộng thành 3 sub-steps: **14a** (`hl_withdraw`: tính `principal_amount = initial − final clearinghouseState.withdrawable`), **14b** (`hl_fulfill`: kiểm tra thanh khoản, CCTP nếu cần, `ready_to_fulfill`), **14c** (`RedemptionQueue.fulfillRequest` on-chain FIFO) | **I-02a resolved** — formula, cơ chế, và bảng trạng thái settlement đã rõ |
| §3 step 14a | Không có | `redemption_requests.principal_amount = initial clearinghouseState.withdrawable − final` (USDC 6-decimal, net PnL/funding/fees — HL API tự tính) | Xác định source of truth cho HL-portion amount |
| §3 step 14b | Không có | Kiểm tra `operator dest-chain USDC ≥ amount owed`: nếu đủ → bỏ qua CCTP (reserved liquidity); nếu thiếu → burn Arb USDC + mint qua CCTP; mark `ready_to_fulfill` | Phân nhánh CCTP vs reserved liquidity rõ ràng |
| §3 step 14c | Không có | `RedemptionQueue.fulfillRequest` on-chain (FIFO contract-enforced); `safeTransferFrom(operator, investor, principal_amount)` | On-chain FIFO payout rõ ràng |
| §3 step 15–16 | Step 14–15 | Đánh số lại: step 14 → step 15 (UPDATE `close_operations.state='done'`), step 15 → step 16 (UPDATE `queue_idempotency.state='succeeded'`) | Không thay đổi logic |

### B. BA Q&A (qc-responses-2026-07-20.md)

| Question | Trả lời | Impact |
|---|---|---|
| I-02a (High) | `principal_amount = initial clearinghouseState.withdrawable − final` sau khi rút settled. Net PnL/funding/fees — HL API tự tính vào balance, không có breakdown. Ghi vào `redemption_requests.principal_amount`. Cả user_redeem lẫn bot_safe_close đều đi qua chain `hl_withdraw → hl_fulfill`. Reference: `flow-withdraw-close-settlement-ba.md` | I-02a **closed** — formula rõ ràng, có thể viết test case |

### C. Phát hiện gap mới trong quá trình cross-check

Khi đọc `uc-user-redeem.md` (updated 2026-07-20) đối chiếu với SRS baseline, phát hiện các gap sau chưa có trong v5:

| Gap ID | Tài liệu | Gap |
|---|---|---|
| G-01 | srs/erd.md | `redemption_requests` table không có trong ERD, mặc dù UC step 14a ghi `redemption_requests.principal_amount` |
| G-02 | srs/states.md | Vòng đời trạng thái settlement (`pending → hl_withdraw_submitted → bridge_pending_attestation → ready_to_fulfill → fulfilled / failed`) không có trong states.md |
| G-03 | srs/flows.md F-04 | F-04 không hiển thị chuỗi `hl_withdraw → CCTP → hl_fulfill` đã được bổ sung vào UC step 14 (2026-07-20) — F-04 đã lỗi thời |
| G-04 | flow-withdraw-close-settlement-ba.md | `linked_usecases` trong frontmatter chỉ liệt kê `UC-EXBOT-bot-safe-close`, thiếu `UC-EXBOT-user-redeem` mặc dù chuỗi settlement áp dụng cho cả hai UC |
| G-05 | userstories/us-004.md AC-004-1 | AC-004-1 chỉ nói "HL-portion USDC is sent to the investor after hedge close is confirmed" — chưa phản ánh chuỗi `hl_withdraw → CCTP → fulfillRequest` |
| G-06 | uc-user-redeem.md §3 step 15 / §5 Postconditions | `close_operations.state='done'` được set TRƯỚC khi `hl_withdraw` và `hl_fulfill` hoàn thành (settlement chạy async sau `done`). Timing này chưa được ghi rõ trong UC hoặc tài liệu — tester dễ nhầm `done` = nhà đầu tư đã nhận tiền |

---

## §F.1 — Inventory (Functions, Operations, Data Objects, Messages)

*(Kế thừa từ v5; cập nhật delta v6 — bổ sung F1-13a đến F1-13e cho chuỗi settlement mới)*

| # | Loại | Tên / ID | Trigger | Input | Output / Effect | Source |
|---|---|---|---|---|---|---|
| F1-01 | On-chain operation | `BnzaExVault.redeem(tokenId)` | Nhà đầu tư gọi trực tiếp on-chain | `tokenId` (LP NFT) | LP liquidated; LP-portion USDC trả về investor trong cùng tx; emit `RedemptionEvent` | uc §3 step 1–2; FR-EXBOT-070 |
| F1-02 | Event watcher | Redeem Event Watcher (Fargate/Lambda) | `RedemptionEvent` on-chain emit | `botId`, `redeemTxHash`, `userAddress` | Enqueue `user_redeem` message vào SQS FIFO queue (độ ưu tiên cao nhất) | flows.md F-04 |
| F1-03 | Queue processing | Redeem Worker (AWS Lambda) | SQS FIFO delivery (SLA: 5 min) | `{botId, redeemTxHash, userAddress}` | Thực hiện toàn bộ luồng hedge close | uc §3; flows.md F-04 |
| F1-04 | DB write (idempotency) | INSERT `queue_idempotency` | Trước mọi thao tác | `message_id`, `state=started` | Idempotency row; UNIQUE conflict → skip (A3) | uc §3 step 6 |
| F1-05 | DB write | INSERT + UPDATE `close_operations` | Sau F1-04 | `kind=user_redeem`, `state=requested` | Row được tạo; transitions `requested → lp_closed → funds_returned` | uc §3 step 7; flows.md F-04 |
| F1-06 | Distributed lock acquire | `User Lock (Redis Redlock)` acquire | Sau F1-05 | `holderToken`, `ttl=90s`, `idempotencyKey=user-redeem:{botId}:{redeemTxHash}` | `acquired=true` hoặc `acquired=false` → re-queue | FR-EXBOT-092; flows.md F-04 |
| F1-07 | DB write | UPDATE `close_operations.state = hedge_close_pending` | Sau lock acquired | — | Recovery checkpoint trước HL call | uc §3 step 9; flows.md F-04 |
| F1-08 | HL operation | `closeShortReduceOnlyIoc` (full close, target=0) | Trong Redlock block | `cloid = first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | HL position đóng; retry up to 3 lần in-invocation | uc §3 step 10; FR-EXBOT-022 |
| F1-09 | HL operation | `cancelStop` via §19.5 replaceStopProtected (size=0) | Trong Redlock block, sau F1-08 | `size=0` | Stop order bị hủy trên HL | uc §3 step 11 |
| F1-10 | HL operation | `reconcilePosition` | Trong Redlock block, sau F1-09 | — | Verify HL position size = 0 | uc §3 step 12 |
| F1-11 | DB write | UPDATE `close_operations.state = hedge_closed` | Sau reconcile confirms size=0 | — | Xác nhận hedge đã đóng; lock released | flows.md F-04; uc §3 step 13 |
| F1-12 | Distributed lock release | `User Lock` release | Sau F1-11 hoặc khi hedge close fails | — | Lock released | FR-EXBOT-092 |
| F1-13a | HL operation (hl_withdraw) | Query + sign `clearinghouseState.withdrawable` (initial) | Sau hedge_closed | `botId`, HL API | `initial_withdrawable` đọc từ HL API | uc §3 step 14a; flow-withdraw-close-settlement-ba.md §5 step 5 |
| F1-13b | HL operation (hl_withdraw) | Sign `master withdraw3` và poll balance | Sau F1-13a | Full withdrawable amount | HL USDC rút về operator Arbitrum; `final_withdrawable` sau khi rút settled | uc §3 step 14a; flow-withdraw-close-settlement-ba.md §8.2 C-06/C-07 |
| F1-13c | DB write | INSERT `redemption_requests` row; set `principal_amount` | Sau poll settled | `principal_amount = initial − final` (BigDecimal TEXT) | `redemption_requests.principal_amount` được ghi; `status = pending → hl_withdraw_submitted` | uc §3 step 14a; flow-withdraw-close-settlement-ba.md §7 |
| F1-13d | Settlement worker (hl_fulfill) | Kiểm tra `operator dest-chain USDC ≥ principal_amount` | Sau F1-13c | `principal_amount`, operator dest balance | Nếu đủ → `status = ready_to_fulfill` (reserved liquidity); nếu thiếu → burn Arb USDC + CCTP bridge → `status = bridge_pending_attestation` → poll Circle Iris → mint → `status = ready_to_fulfill` | uc §3 step 14b; flow-withdraw-close-settlement-ba.md §8.3 C-08/C-09/C-10/C-11; §11.2/11.3 |
| F1-13e | On-chain operation | `RedemptionQueue.fulfillRequest` | Sau `status = ready_to_fulfill` | `requestId`, operator USDC | FIFO enforced on-chain: `safeTransferFrom(operator, investor, principal_amount)`; contract revert nếu không phải queue head → SQS retry | uc §3 step 14c; flow-withdraw-close-settlement-ba.md §5 step 7, §11.4 |
| F1-14 | DB write | UPDATE `close_operations.state = done`; `bots.lifecycle_state = closed` | Sau hedge_closed + redemption_requests created (step 15 in uc) | — | Bot đóng về mặt `close_operations`; settlement chain tiếp tục async | uc §3 step 15; §5 Postconditions |
| F1-15 | DB write | UPDATE `queue_idempotency.state = succeeded` | Sau F1-14 | — | Idempotency record closed | uc §3 step 16 |
| F1-16 | Exception path | hedge close fails → `residual_hl_liability` | Sau 3 retries thất bại hoặc reconcile mismatch | — | `close_operations.state = residual_hl_liability`; `bots.lifecycle_state = error`; admin notified (E-EXBOT-024); LP-portion NOT reversed | uc §4 A2; BR-EXBOT-006 |
| F1-17 | SLA breach alert | A1: hedge close exceeds 5 min SLA | Tổng delay > 5 min từ detection | — | Admin + Investor nhận E-EXBOT-010; LP-portion funds already returned | uc §4 A1; NFR-EXBOT-003 |
| F1-18 | DB write (settlement failure) | UPDATE `redemption_requests.status = failed` | Sau `fulfillRequest` retry limit exhausted | — | Terminal failure; on-chain request vẫn là durable claim; cần ops intervention | flow-withdraw-close-settlement-ba.md §8.4 C-14; §9 A8 |
| MSG-01 | Admin message | E-EXBOT-024 | A2/reconcile failure | `residual_amount` | "User redemption hedge close failed. Manual intervention required." | message-list.md |
| MSG-02 | Admin+Investor message | E-EXBOT-010 | A1 SLA breach | — | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | message-list.md |
| BR-01 | Business rule | BR-EXBOT-006 | Luôn áp dụng | — | LP-portion repayment vô điều kiện — không bao giờ bị đảo ngược hoặc block | srs/spec.md BR-EXBOT-006 |
| BR-02 | Business rule | BR-EXBOT-007 | Khi LP đã liquidated | — | SAFE_MODE không áp dụng trong A2 user_redeem — LP đã thanh lý | srs/spec.md BR-EXBOT-007 |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations

*(Kế thừa từ v5; cập nhật delta v6 — bổ sung redemption_requests, settlement status lifecycle)*

### close_operations

| Field | Type | Valid values / Constraints | Business rule | Source |
|---|---|---|---|---|
| `id` | TEXT PK | UUID | — | erd.md |
| `kind` | TEXT | `user_redeem`, `bot_safe_close` | — | erd.md; states.md |
| `state` | TEXT | `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done`; nhánh lỗi: `→ residual_hl_liability` | Transition forward-only; không rollback lp_closed sau khi on-chain confirmed | states.md close_operations; flows.md F-04 |
| `usdc_amount` | TEXT | BigDecimal TEXT (USDC 6-decimal) | LP-portion amount — KHÔNG phải HL-portion | erd.md |
| `residual_amount` | TEXT | Nullable; set khi `state = residual_hl_liability` | Lưu outstanding HL liability amount khi hedge close thất bại | erd.md; qc-responses I-05-B |
| `hedge_close_tx` | TEXT | **KHÔNG** lưu tx hash của HL-portion transfer | Tech Lead confirmed (I-02bc, v5) | qc-responses-2026-07-14.md |

> **Lưu ý quan trọng (G-06):** `close_operations.state = 'done'` và `bots.lifecycle_state = 'closed'` được set ở step 15, TRƯỚC khi chuỗi `hl_withdraw → hl_fulfill` hoàn thành. Settlement chạy **async** sau khi `done`. Tester không được nhầm `done` = investor đã nhận USDC — cần kiểm tra `redemption_requests.status = 'fulfilled'` để xác nhận nhà đầu tư thực sự nhận được tiền.

### redemption_requests *(⚠️ WARNING: table không có trong srs/erd.md — G-01)*

> Bảng này được tham chiếu trong UC step 14a và `flow-withdraw-close-settlement-ba.md §7` nhưng **chưa được định nghĩa trong `srs/erd.md`**. Thông tin dưới đây được tổng hợp từ `flow-withdraw-close-settlement-ba.md` và UC step 14a.

| Field | Type | Valid values / Constraints | Business rule | Source |
|---|---|---|---|---|
| `principal_amount` | TEXT | BigDecimal TEXT (USDC 6-decimal) | `= initial clearinghouseState.withdrawable − final` sau khi HL withdraw settled | uc §3 step 14a; qc-responses-2026-07-20.md I-02a |
| `status` (settlement status) | TEXT | Xem bảng settlement status lifecycle bên dưới | Lifecycle forward-only; `fulfilled` là terminal success; `failed` là terminal fail | flow-withdraw-close-settlement-ba.md §7 |

### Settlement status lifecycle (redemption_requests)

> ⚠️ **G-02:** Lifecycle này không có trong `srs/states.md`. Định nghĩa duy nhất: `flow-withdraw-close-settlement-ba.md §7`.

| Status | Ý nghĩa | Chuyển sang | Điều kiện |
|---|---|---|---|
| `pending` | Settlement chưa bắt đầu; LP/redeem hoàn tất | `hl_withdraw_submitted` hoặc `ready_to_fulfill` (reserved) | Sau hedge_closed + redemption_requests row created |
| `hl_withdraw_submitted` | HL withdraw instruction đã gửi | `bridge_pending_attestation` hoặc `ready_to_fulfill` | Withdraw submitted to HL |
| `bridge_pending_attestation` | CCTP burn done; đang chờ Circle Iris attestation | `ready_to_fulfill` | Circle attestation ready → mint on dest |
| `ready_to_fulfill` | Operator đủ USDC trên redemption chain | `fulfilled` hoặc `failed` | `fulfillRequest` on-chain |
| `fulfilled` | On-chain payout thành công — terminal success | — | `fulfillRequest` OK |
| `failed` | Fulfill retry limit exhausted — terminal fail; cần ops | — | C-14 retry threshold exceeded |

### bots.lifecycle_state (user_redeem relevant — kế thừa v5)

| lifecycle_state | bots.status | user_redeem allowed | On-chain rationale |
|---|---|---|---|
| `active` | active | ✓ | — |
| `paused` | paused | ✓ | — |
| `hedge_stopped_cooldown` | active | ✓ | LP NFT vẫn trong BnzaExVault; contract không check lifecycle_state |
| `lp_rebalancing` | active | ✓ | `RedeemStrategyV1` chỉ validate tokenId ownership; `redeem(oldTokenId)` revert an toàn mid-rebalance |
| `safe_mode` | safe_mode | ✓ | LP NFT vẫn trong vault |
| `error` | error | ✓ | LP NFT vẫn trong vault; user có quyền redeem |
| `lp_closing` | closing | ✗ — Already closing | — |
| `closed` | closed | ✗ — Already closed | — |

### User Lock (Redis Redlock) — kế thừa v5

| Attribute | Value | Source |
|---|---|---|
| TTL | 90s | FR-EXBOT-092 |
| `idempotencyKey` pattern | `user-redeem:{botId}:{redeemTxHash}` | FR-EXBOT-092; flows.md F-04 |
| Lock ordering | Sau INSERT `close_operations` (idempotency first); trước mọi HL operation | qc-responses-2026-07-14.md I-03 |
| `acquired=false` behavior | Re-queue với delay; SLA clock tiếp tục; > 5 min tổng → A1 SLA breach | flows.md F-04 |
| Release | Sau reconcile confirms size=0, hoặc trước `residual_hl_liability` khi fails | qc-responses-2026-07-14.md I-03 |

### Business Rules summary

| BR | Nội dung | Applies to | Source |
|---|---|---|---|
| BR-EXBOT-006 | LP-portion repayment vô điều kiện — không bao giờ bị block hoặc đảo ngược | user_redeem luôn | srs/spec.md |
| BR-EXBOT-007 | SAFE_MODE không áp dụng khi LP đã liquidated (A2 path) | user_redeem A2 | srs/spec.md |
| NFR-EXBOT-003 | hedge close SLA: ≤ 5 phút từ event detection | user_redeem | srs/spec.md |
| C-06/C-07 (flow) | HL withdraw soft-fail: nếu withdraw thất bại, settlement vẫn có thể tiếp tục nếu operator dest-chain đã có đủ USDC | hl_withdraw step | flow-withdraw-close-settlement-ba.md §8.2 |
| C-08 (flow) | Nếu operator dest-chain USDC ≥ amount owed → bỏ qua CCTP, mark `ready_to_fulfill` trực tiếp | hl_fulfill step | flow-withdraw-close-settlement-ba.md §8.3 |
| C-10 (flow) | Nếu CCTP burn đã được khởi tạo, mint phải hoàn tất — không được bỏ dở dù dest balance trông đủ | hl_fulfill CCTP path | flow-withdraw-close-settlement-ba.md §8.3 C-10 |
| C-15 (flow) | `fulfillRequest` idempotent: nếu `redemption_requests.status = fulfilled`, lần giao hàng lại không được thực hiện thanh toán thứ hai | hl_fulfill redelivery | flow-withdraw-close-settlement-ba.md §8.4 C-15 |

---

## §F.3 — Functional Logic & Workflow Decomposition

### Happy Path (F-04 main flow — full với settlement chain v6)

| Bước | Actor | Hành động | System response | Source |
|---|---|---|---|---|
| 1 | Investor | Gọi `BnzaExVault.redeem(tokenId)` on-chain | LP liquidated; LP-portion USDC trả về cùng tx; emit `RedemptionEvent` | uc §3 step 1–2 |
| 2 | Event Watcher | Detect `RedemptionEvent` | Enqueue `{botId, redeemTxHash, userAddress}` vào user_redeem SQS FIFO queue | flows.md F-04 |
| 3 | Redeem Worker | INSERT `queue_idempotency` (`state=started`) | UNIQUE conflict → A3 (skip); bình thường → tiếp tục | uc §3 step 6 |
| 4 | Redeem Worker | INSERT + UPDATE `close_operations` | `requested → lp_closed → funds_returned` | uc §3 step 7; F-04 |
| 5 | Redeem Worker | Acquire User Lock | `idempotencyKey=user-redeem:{botId}:{redeemTxHash}`, TTL=90s | FR-EXBOT-092; F-04 |
| 6 | Redeem Worker | UPDATE `close_operations.state = hedge_close_pending` | Recovery checkpoint đặt trước HL call | uc §3 step 9 |
| 7 | Redeem Worker | Gọi `closeShortReduceOnlyIoc` (full close, target=0) | HL position đóng; cloid per FR-EXBOT-022; retry up to 3 lần in-invocation | uc §3 step 10; FR-EXBOT-022 |
| 8 | Redeem Worker | Gọi `cancelStop` via §19.5 | Stop order hủy trên HL | uc §3 step 11 |
| 9 | Redeem Worker | `reconcilePosition` — verify size=0 | Xác nhận HL position = 0 | uc §3 step 12 |
| 10 | Redeem Worker | UPDATE `close_operations.state = hedge_closed`; release lock | Lock released sau xác nhận | flows.md F-04; uc §3 step 13 |
| 11 | hl_withdraw worker | Query `clearinghouseState.withdrawable` (initial) từ HL API | `initial_withdrawable` lưu tạm | uc §3 step 14a |
| 12 | hl_withdraw worker | Sign `master withdraw3`; poll đến khi HL balance ≤ threshold (final) | HL USDC rút về operator Arbitrum; `final_withdrawable` xác định | uc §3 step 14a; flow §8.2 C-06/C-07 |
| 13 | hl_withdraw worker | INSERT `redemption_requests` (`status=pending`); SET `principal_amount = initial − final` | `redemption_requests.principal_amount` là BigDecimal TEXT; `status → hl_withdraw_submitted` | uc §3 step 14a; flow §7 |
| 14a | hl_fulfill worker | Kiểm tra `operator dest-chain USDC ≥ principal_amount` | Nếu đủ → `status = ready_to_fulfill` (reserved liquidity path — bỏ qua CCTP) | uc §3 step 14b; flow §8.3 C-08; §11.3 |
| 14b | hl_fulfill worker (CCTP path) | Burn Arb USDC thiếu hụt; poll Circle Iris attestation | `status = bridge_pending_attestation`; cron poll đến khi Circle confirm; mint on dest → `status = ready_to_fulfill` | uc §3 step 14b; flow §8.3 C-09/C-11; §11.2 |
| 15 | hl_fulfill worker | `RedemptionQueue.fulfillRequest` on-chain | FIFO contract-enforced: `safeTransferFrom(operator, investor, principal_amount)`; `status = fulfilled` | uc §3 step 14c; flow §11.4 |
| 16 | Redeem Worker | UPDATE `close_operations.state = done`; `bots.lifecycle_state = closed` | Bot đóng từ góc nhìn `close_operations`; settlement đã được enqueue async | uc §3 step 15; §5 |
| 17 | Redeem Worker | UPDATE `queue_idempotency.state = succeeded` | Idempotency closed | uc §3 step 16 |

> **Lưu ý timing:** Step 16 (set `done`) xảy ra SAU khi `redemption_requests` row được tạo nhưng TRƯỚC khi `hl_fulfill` hoàn thành. Settlement (steps 14–15) tiếp tục **async** sau khi `close_operations.state = done`.

### Alternative Path A1 — SLA breach

| Điều kiện | Hành động | Kết quả |
|---|---|---|
| Lock held bởi hedge-sync → `acquired=false` | Re-queue với delay | SLA clock tiếp tục; tổng delay > 5 min → A1 |
| Tổng thời gian từ detection > 5 min | Admin + Investor notified | E-EXBOT-010 |
| LP-portion | Không bị ảnh hưởng | BR-EXBOT-006 |

### Alternative Path A2 — hedge close failure

| Điều kiện | Hành động | Kết quả |
|---|---|---|
| `closeShortReduceOnlyIoc` fails 3 lần in-invocation hoặc reconcile mismatch | Release lock; UPDATE `close_operations.state = residual_hl_liability` | `bots.lifecycle_state = error` |
| Admin notification | E-EXBOT-024 | "User redemption hedge close failed. Manual intervention required." |
| SAFE_MODE | Không áp dụng | LP đã liquidated |
| LP-portion | Không bị đảo ngược | BR-EXBOT-006 |

### Alternative Path A3 — duplicate message

| Điều kiện | Hành động |
|---|---|
| SQS redelivery → `queue_idempotency` UNIQUE conflict tại step 6 | Return immediately; không tạo duplicate close |

### Exception path: HL withdraw soft-fail (C-06/C-07)

| Điều kiện | Hành động |
|---|---|
| HL withdraw không khả dụng hoặc thất bại | Log skip; settlement **vẫn được thử** nếu dest-chain đã được fund (reserved liquidity) |

### Exception path: FIFO revert (C-14)

| Điều kiện | Hành động |
|---|---|
| `fulfillRequest` revert (request không phải queue head hoặc lỗi khác) | SQS retry; không có off-chain wait branch; sau retry limit → `status = failed` |

---

## §F.4 — Functional Integration & Data Consistency

| Hành động | Downstream effect | Data consistency check | Source |
|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` on-chain | LP liquidated on-chain; LP-portion USDC trả về in-tx; emit `RedemptionEvent` | Off-chain phải detect event và enqueue trong SLA window | flows.md F-04; UC §3 |
| INSERT `queue_idempotency` | Nếu SQS redelivery: UNIQUE conflict → A3 skip | Row tồn tại kể cả khi flow bị interrupt | uc §3 step 6 |
| INSERT `close_operations` (idempotency) | Nếu re-queue sau lock fail: duplicate INSERT bị reject bởi idempotency check | `close_operations` row tồn tại trước lock — orphan lock không xảy ra | qc-responses-2026-07-14.md I-03 |
| User Lock acquire | Ngăn hedge-sync worker can thiệp trong critical section | Lock contention → re-queue → SLA clock tiếp tục | FR-EXBOT-092; flows.md F-04 |
| `hedge_close_pending` checkpoint | Recovery worker có thể xác định hedge close đang in-progress sau Lambda crash | Không bỏ sót state | uc §3 step 9 |
| `closeShortReduceOnlyIoc` + `reconcilePosition` | HL position size = 0 confirmed trước khi `close_operations.state = hedge_closed` | Off-chain state advance chỉ sau on-chain/HL confirmation | flows.md F-04 |
| INSERT `redemption_requests` + set `principal_amount` | HL-portion amount được ghi ngay sau `hedge_closed`; settlement pipeline có thể bắt đầu | `close_operations.usdc_amount` (LP-portion) ≠ `redemption_requests.principal_amount` (HL-portion) — hai bảng riêng biệt | uc §3 step 14a; flow-withdraw-close-settlement-ba.md §7 |
| `hl_withdraw` → operator Arbitrum | Tiền HL về Arb trước khi CCTP bridge; soft-fail không chặn settlement nếu dest đã fund | Nếu withdraw thất bại nhưng dest funded: CCTP skip; settlement tiếp tục | flow §8.2 C-06/C-07 |
| CCTP burn on Arbitrum | Sau khi burn khởi tạo, mint phải hoàn tất — C-10 rule | Không được bỏ dở CCTP in-flight dù dest balance trông đủ | flow §8.3 C-10 |
| `RedemptionQueue.fulfillRequest` on-chain | FIFO enforced on-chain; `safeTransferFrom(operator, investor, principal_amount)` | Contract revert nếu không phải queue head → SQS retry; idempotent khi `status=fulfilled` (C-15) | uc §3 step 14c; flow §11.4; §8.4 C-15 |
| `close_operations.state = done` | Bot không còn trong active queue scan | `done` không có nghĩa settlement hoàn tất; `redemption_requests.status = fulfilled` là terminal confirmation | uc §3 step 15; §5 Postconditions |
| `redemption_requests.status = failed` | On-chain request vẫn là durable claim; không có auto-retry sau `failed` | Cần ops intervention; queue trên chuỗi là source of truth cho đến khi resolve | flow §9 A8 |
| A2: `residual_hl_liability` | `bots.lifecycle_state = error`; admin nhận E-EXBOT-024 | LP-portion đã trả (BR-EXBOT-006); HL residual cần xử lý manual | uc §4 A2; spec.md |

---

## §F.5 — Acceptance Criteria Candidates

*(Kế thừa từ v5; cập nhật delta v6 — AC-009 resolved; bổ sung AC-010 đến AC-016 cho settlement chain)*

| AC # | Scenario | Given | When | Then | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-001 | Happy path — LP-first, full settlement thành công | Bot ở bất kỳ `lifecycle_state` được phép, LP NFT trong vault | Investor gọi `redeem(tokenId)` on-chain | LP liquidated; LP-portion USDC trả về trong cùng tx; `close_operations` đi qua: `requested → lp_closed → funds_returned → hedge_close_pending → hedge_closed → done`; `redemption_requests.principal_amount = initial − final clearinghouseState.withdrawable`; `redemption_requests.status = fulfilled`; investor nhận USDC on-chain từ RedemptionQueue; `bots.lifecycle_state = closed` | uc §3; flow-withdraw-close-settlement-ba.md §5 |
| AC-002 | SLA breach — lock contention | Lock held bởi hedge-sync worker | Tổng delay > 5 phút từ event detection | Admin + Investor nhận E-EXBOT-010; LP-portion không bị đảo ngược (BR-EXBOT-006) | uc §4 A1; NFR-EXBOT-003 |
| AC-003 | hedge close failure — residual HL liability | HL API từ chối `closeShortReduceOnlyIoc` 3 lần liên tiếp in-invocation | Sau 3 retries thất bại | `close_operations.state = residual_hl_liability`; `bots.lifecycle_state = error`; admin nhận E-EXBOT-024; LP-portion không bị đảo ngược | uc §4 A2; BR-EXBOT-006 |
| AC-004 | Idempotency — SQS redelivery | SQS redelivers message sau khi `queue_idempotency` đã INSERT | Redeem Worker xử lý message lần 2 | UNIQUE conflict → worker skip; không tạo duplicate close | uc §3 step 6; FR-EXBOT-070 |
| AC-005 | Precondition: `lp_rebalancing` | Bot ở `lp_rebalancing`, đang rebalance với `oldTokenId` | Investor gọi `redeem(oldTokenId)` on-chain | Tx revert an toàn; investor gọi `redeem(newTokenId)` sau rebalance thành công | qc-responses-2026-07-14.md I-N1 |
| AC-006 | Lock ordering: idempotency before lock | Normal redemption flow | Worker tạo `close_operations` trước khi acquire User Lock | `close_operations` row tồn tại kể cả khi lock acquire fails | qc-responses-2026-07-14.md I-03 |
| AC-007 | Recovery checkpoint | Lambda crash sau lock acquire, trước `closeShortReduceOnlyIoc` | Recovery worker chạy | `close_operations.state = hedge_close_pending` → recovery worker biết in-progress và resume | uc §3 step 9 |
| AC-009 | HL-portion formula — principal_amount | Hedge close thành công; HL withdraw settled | Worker tính `principal_amount` | `redemption_requests.principal_amount = initial clearinghouseState.withdrawable − final` (BigDecimal TEXT, net PnL/funding/fees) | uc §3 step 14a; qc-responses-2026-07-20.md I-02a |
| AC-010 | Settlement: reserved liquidity path | Operator dest-chain USDC ≥ `principal_amount` | hl_fulfill worker chạy | CCTP được bỏ qua; `redemption_requests.status = ready_to_fulfill` → `fulfilled` trực tiếp | uc §3 step 14b; flow §8.3 C-08; §11.3 |
| AC-011 | Settlement: CCTP path | Operator dest-chain USDC < `principal_amount`; Arb USDC đủ | hl_fulfill worker chạy | Burn Arb → `status = bridge_pending_attestation`; Circle attestation → mint → `status = ready_to_fulfill` → `status = fulfilled` | uc §3 step 14b; flow §8.3 C-09/C-11; §11.2 |
| AC-012 | Settlement: HL withdraw soft-fail | HL withdraw thất bại nhưng operator dest-chain đã có đủ USDC | hl_fulfill worker chạy | Settlement tiếp tục qua reserved liquidity path; không bị block bởi withdraw failure | flow §8.2 C-06/C-07 |
| AC-013 | Settlement: FIFO revert + retry | `fulfillRequest` revert vì request không phải queue head | hl_fulfill worker cố gắng payout | Contract revert → SQS retry; không có off-chain wait branch | uc §3 step 14c; flow §11.4 |
| AC-014 | Settlement: fulfill idempotency | `redemption_requests.status = fulfilled` | SQS redelivery → hl_fulfill chạy lần 2 | Không có second payout; C-15 idempotent skip | flow §8.4 C-15 |
| AC-015 | Settlement: fulfill failed | `fulfillRequest` retry limit exhausted | — | `redemption_requests.status = failed`; on-chain request vẫn là durable claim; cần ops | flow §9 A8; §8.4 C-14 |
| AC-016 | `close_operations.state = done` timing | Hedge close thành công + `redemption_requests` row created | Worker set `close_operations.state = done` | `done` xảy ra TRƯỚC khi settlement hoàn thành; `bots.lifecycle_state = closed` nhưng `redemption_requests.status` vẫn `pending` hoặc `hl_withdraw_submitted` tại thời điểm này | uc §3 step 15; G-06 timing note |

---

## §10.1 Issue Register

| ID | Type | Severity | Area | Source trace | Finding | Impact on tester | Suggested fix | Status |
|---|---|---|---|---|---|---|---|---|
| I-02a | MISSING_INFO | High (resolved) | Area 2, 3 | uc §3 step 14a; qc-responses-2026-07-20.md | Công thức tính HL-portion amount: `principal_amount = initial clearinghouseState.withdrawable − final` (net PnL/funding/fees). Ghi vào `redemption_requests.principal_amount` dạng BigDecimal TEXT. | — | — | **Closed** 2026-07-20 (BA) |
| G-01 | MISSING_INFO | Major | Area 4, 5 | uc §3 step 14a ("record `redemption_requests.principal_amount`"); flow-withdraw-close-settlement-ba.md §7 vs srs/erd.md | `redemption_requests` table được UC step 14a tham chiếu ghi field `principal_amount` và `status`, nhưng bảng này **không có trong `srs/erd.md`**. Tester không có định nghĩa chuẩn về schema, field types, constraints, hay primary key của bảng này. Thông tin duy nhất đến từ flow-withdraw-close-settlement-ba.md và UC prose. | Tester không thể xác nhận field types, null constraints, index/uniqueness. Khi viết test case DB-level (kiểm tra INSERT, field giá trị), không có tài liệu chuẩn để so sánh. | Thêm `redemption_requests` table vào `srs/erd.md` với đầy đủ fields, types, constraints. | Open |
| G-02 | MISSING_INFO | Major | Area 2, 5 | flow-withdraw-close-settlement-ba.md §7 vs srs/states.md | Vòng đời trạng thái settlement của `redemption_requests` (`pending → hl_withdraw_submitted → bridge_pending_attestation → ready_to_fulfill → fulfilled / failed`) không có trong `srs/states.md`. `states.md` chỉ chứa `close_operations` và `bots.lifecycle_state`. | Tester không có nguồn tham chiếu canonical cho settlement states. Phải đọc flow-withdraw-close-settlement-ba.md để biết states — tài liệu BA, không phải SRS. | Bổ sung settlement status lifecycle vào `srs/states.md` với đầy đủ transitions và conditions. | Open |
| G-03 | CROSS_SOURCE_CONFLICT | Major | Area 3, 5 | uc-user-redeem.md §3 step 14 (updated 2026-07-20) vs srs/flows.md F-04 | F-04 trong `flows.md` không hiển thị chuỗi `hl_withdraw → CCTP bridge → hl_fulfill → RedemptionQueue.fulfillRequest` đã được mô tả trong UC step 14 (2026-07-20). F-04 chỉ có dòng `UREW->>VAULT: send HL-portion USDC to user (RedemptionQueue ledger)` — bỏ qua toàn bộ settlement chain. Tester đọc F-04 sẽ không thấy: (a) worker hl_withdraw, (b) CCTP path, (c) Circle attestation cron, (d) reserved liquidity path, (e) on-chain FIFO. | F-04 là sequence diagram canonical; nếu tester chỉ đọc F-04, họ sẽ thiết kế test case không đầy đủ cho chuỗi settlement. Mâu thuẫn rõ ràng giữa UC prose và flows.md. | Cập nhật F-04 trong `flows.md` để hiển thị đầy đủ: hl_withdraw → CCTP (hoặc reserved liquidity) → hl_fulfill → `fulfillRequest`. | Open |
| G-04 | MISSING_INFO | Minor | Area 4, 5 | flow-withdraw-close-settlement-ba.md frontmatter `linked_usecases: [UC-EXBOT-bot-safe-close]` | `flow-withdraw-close-settlement-ba.md` chỉ liệt kê `UC-EXBOT-bot-safe-close` trong `linked_usecases`, thiếu `UC-EXBOT-user-redeem` mặc dù BA response I-02a xác nhận cả hai UC đều đi qua cùng chain settlement. Tester tìm kiếm tài liệu settlement từ góc nhìn user-redeem có thể bỏ lỡ tài liệu này. | Nguy cơ tester bỏ sót flow-withdraw-close-settlement-ba.md khi thiết kế test case cho user_redeem; ảnh hưởng traceability. | Thêm `UC-EXBOT-user-redeem` vào `linked_usecases` trong frontmatter của `flow-withdraw-close-settlement-ba.md`. | Open |
| G-05 | CROSS_SOURCE_CONFLICT | Minor | Area 2, 3 | userstories/us-004.md AC-004-1 vs uc-user-redeem.md §3 step 14 | US-EXBOT-004 AC-004-1 nói "HL-portion USDC is sent to the investor after hedge close is confirmed" — không phản ánh chuỗi `hl_withdraw → CCTP → fulfillRequest`. Tester đọc AC-004-1 có thể hiểu nhầm rằng HL-portion được gửi ngay sau hedge_closed, trong khi thực tế cần qua chuỗi settlement async. | Tester dùng AC-004-1 như acceptance criterion có thể viết test case không đúng timing (kiểm tra ngay sau hedge_closed thay vì chờ `status=fulfilled`). | Cập nhật AC-004-1 trong us-004.md để phản ánh settlement chain. | Open |
| G-06 | UNCLEAR_INFO | Minor | Area 3, 4 | uc-user-redeem.md §3 step 15 vs step 14a–14c; §5 Postconditions | UC step 15 set `close_operations.state='done'` và §5 Postconditions liệt kê "HL-portion USDC sent post-hedge-close" như postcondition — nhưng không nêu rõ rằng `done` được set **trước khi** settlement (`hl_withdraw → hl_fulfill`) hoàn thành. Settlement chạy async sau `done`. Tester đọc Postconditions có thể nhầm `done` = investor đã nhận USDC. | Test case happy path có thể kiểm tra `close_operations.state = done` và kết luận sai rằng investor đã nhận tiền, trong khi `redemption_requests.status` vẫn `pending`. | Bổ sung note vào UC §3 step 15 và §5 Postconditions giải thích rõ `done` = hedge close + redemption_requests created (settlement async); `fulfilled` = investor nhận USDC. | Open |

### Issues resolved in this audit pass

| ID | Resolution |
|---|---|
| I-02bc | Closed v5 — Worker + Operator address thực hiện USDC transfer; tx hash không lưu. |
| I-03 | Closed v5 — F-04 đầy đủ với Redlock participant; idempotency-first ordering. |
| I-N1 | Closed v5 — 6 lifecycle_state confirmed; UC preconditions cập nhật. |
| I-N2 | Closed v5 — retry strategy in-invocation xác nhận. |
| I-N3 | Closed v5 — `hedge_close_pending` thêm vào UC step 9. |
| I-N4 | Closed v5 — frd.md renumbered đồng bộ spec.md. |
| I-02a | **Closed v6** — `principal_amount = initial − final clearinghouseState.withdrawable`; UC step 14a updated 2026-07-20; source BA confirmed. |

---

## §10.2 Dependency

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
| G-01: `redemption_requests` schema không có trong ERD | MISSING_INFO | Tester không có DB schema canonical cho bảng settlement | BA | Open |
| G-02: Settlement status lifecycle không có trong states.md | MISSING_INFO | Tester cần đọc flow doc để biết settlement states | BA | Open |
| G-03: F-04 chưa cập nhật settlement chain | CROSS_SOURCE_CONFLICT | Mâu thuẫn giữa UC prose và flows.md F-04 | BA | Open |
| flow-withdraw-close-settlement-ba.md | BA doc | Settlement chain canonical; cần được linked vào uc-user-redeem | BA | Open (G-04) |
| NFR-EXBOT-003: SLA 5 min | NFR | Test case cho A1 phải verify SLA boundary | BA | Resolved |

---

## §10.3 Audit Summary

### Scoring Table

| Area | Max | v1 | v2 | v3 | v4 | v5 | v6 Score | Delta v5→v6 | Notes v6 |
|---|---|---|---|---|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 14 | 16 | 18 | 18 | 19 | **19** | 0 | F1-13a–F1-13e (settlement chain) bổ sung đầy đủ; F1-18 (failed state). Trừ 1: `redemption_requests` schema không có trong ERD (G-01) — inventory F1-13c không thể tracing sang canonical source. |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 12 | 16 | 16 | 16 | 20 | **23** | +3 | I-02a closed (+3): formula rõ ràng, settlement status lifecycle documented (dù từ flow doc chứ không phải states.md). Trừ 2: G-01 (redemption_requests schema thiếu ERD) + G-02 (settlement lifecycle thiếu states.md) là Minor/Major nhưng behavior đã được mô tả đủ cho test design từ flow-withdraw-close-settlement-ba.md. |
| 3. Functional Logic & Workflow Decomposition | 25 | 14 | 16 | 16 | 16 | 20 | **23** | +3 | I-02a closed (+3): happy path step 14a–14c có thể viết test case đầy đủ; all paths documented (reserved liquidity, CCTP, FIFO revert, soft-fail). Trừ 2: G-06 (timing `done` vs `fulfilled` chưa rõ trong UC) + G-03 (F-04 lỗi thời gây nhầm cho tester đọc flows.md). |
| 4. Functional Integration & Data Consistency | 15 | 12 | 13 | 13 | 13 | 14 | **12** | -2 | G-01 (-1): `redemption_requests` không có ERD; integration cross-check không đầy đủ vì không rõ DB schema. G-03 (-1): F-04 không phản ánh settlement chain mới — tester không thể trace cross-service flow từ flows.md. G-04 (-0.5 bù đắp một phần): flow doc chứa thông tin đủ nếu tester tìm được. Net -2. |
| 5. UC / Spec Documentation Quality Issues | 15 | 14 | 16 | 17 | 17 | 14 | **11** | -3 | G-01 Major (-2): ERD thiếu bảng quan trọng được UC tham chiếu. G-03 Major (-2): F-04 mâu thuẫn rõ với UC prose. G-04 Minor (-0.5): flow doc không linked tới UC user-redeem. G-05 Minor (-0.5): US-004 AC-004-1 lỗi thời. G-06 Minor (-0.5): timing `done` vs async settlement chưa documented rõ trong UC. Bù đắp: FR Trace issue từ v5 vẫn còn (FR-092, FR-022 thiếu) nhưng không tăng penalty vì đã tính v5. Net -3 do các gap mới G-01/G-03. |
| **Total** | **100** | **66** | **77** | **80** | **80** | **87** | **88** | **+1** | |

**Score: 88/100 — Conditionally Ready**

> Score tăng nhẹ +1 từ v5 (87→88): I-02a closed cải thiện Areas 2 và 3 (+6), nhưng các gap tài liệu mới phát hiện trong Areas 4 và 5 giảm điểm (-5). Net gain nhỏ do penalty documentation mới.

### Verdict: CONDITIONALLY READY (88/100)

**Cải thiện trong v6:**
- **I-02a (High) closed:** `principal_amount = initial clearinghouseState.withdrawable − final`; ghi vào `redemption_requests.principal_amount` (BigDecimal TEXT). Chuỗi settlement `hl_withdraw → hl_fulfill` được mô tả đầy đủ trong UC step 14a/14b/14c. Tester có thể viết test case cho toàn bộ settlement chain.
- Settlement chain covered đầy đủ: reserved liquidity path (C-08), CCTP path (C-09/C-10/C-11), FIFO on-chain (C-13/C-14), idempotency (C-15), soft-fail withdraw (C-06/C-07).
- `close_operations.state = done` timing được làm rõ: set async trước khi settlement hoàn thành.

**Open issues (4 Major/Minor documentation gaps):**
- **G-01 (Major):** `redemption_requests` table không có trong `srs/erd.md` — thiếu canonical DB schema.
- **G-02 (Major):** Settlement status lifecycle không có trong `srs/states.md` — tester phải đọc BA flow doc.
- **G-03 (Major):** `flows.md` F-04 lỗi thời — không có `hl_withdraw → CCTP → fulfillRequest`; mâu thuẫn với UC step 14.
- **G-04 (Minor):** `flow-withdraw-close-settlement-ba.md` không linked tới UC-EXBOT-user-redeem.
- **G-05 (Minor):** US-EXBOT-004 AC-004-1 lỗi thời — không phản ánh settlement chain.
- **G-06 (Minor):** UC không ghi rõ `done` được set trước khi settlement async hoàn thành.

**Recommendation:**
88/100 — Đủ điều kiện để tiến hành thiết kế và thực thi test case cho toàn bộ luồng (happy path steps 1–17 bao gồm settlement chain, A1 SLA breach, A2 hedge failure, settlement paths, FIFO revert, idempotency). BA cần: (1) Bổ sung `redemption_requests` vào `srs/erd.md` (G-01); (2) Bổ sung settlement status lifecycle vào `srs/states.md` (G-02); (3) Cập nhật F-04 trong `flows.md` để hiển thị chuỗi hl_withdraw → CCTP → fulfillRequest (G-03). Các gap này không chặn test execution vì `flow-withdraw-close-settlement-ba.md` có thông tin đủ, nhưng làm tăng rủi ro tester bỏ sót nếu không đọc flow doc.

---

## §11 Change Log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-28 | QC UC Read ExBot Agent | Initial audit; score 66/100 |
| v2 | 2026-07-03 | QC UC Read ExBot Agent | Re-audit sau BA Q&A (qc-responses-2026-07-03.md): các issue I-01/I-04/I-05/I-06/I-08/I-09/I-10/I-11 closed; score 77/100 |
| v3 | 2026-07-04 | QC UC Read ExBot Agent | Re-audit sau BA arc-migration update (2026-07-04): UserLockDO → Redis Redlock terminology sync; I-03 partially resolved; I-N1/I-N2/I-N3 new issues; score 80/100 |
| v4 | 2026-07-07 | QC UC Read ExBot Agent | Re-audit sau commit 2026-07-06 (c9a4682): terminology-only; phát hiện I-N4 (FR numbering mismatch); score không đổi 80/100 |
| v5 | 2026-07-15 | QC UC Read ExBot Agent | Re-audit sau BA updates 2026-07-14 + BA responses: I-02bc/I-03/I-N1/I-N2/I-N3/I-N4 closed; step 9 hedge_close_pending thêm vào UC; 6 lifecycle_state confirmed; I-02a vẫn Open; score 87/100 |
| v6 | 2026-07-23 | QC UC Read ExBot Agent | Re-audit sau BA update 2026-07-20 (UC step 14 mở rộng) + I-02a answered: I-02a closed; settlement chain (hl_withdraw → CCTP → fulfillRequest) documented; phát hiện G-01/G-02/G-03/G-04/G-05/G-06 (ERD/states/flows gaps); score 88/100 |

---

*Report generated by: QC UC Read ExBot Agent | Device: MTS-978 | Run ID: run-20260723-aud001-trinhbui*
