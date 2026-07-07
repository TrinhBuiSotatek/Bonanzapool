---
title: "UC Readiness Review — UC-EXBOT-user-redeem (User-Initiated Redemption)"
date_created: 2026-07-07
author: QC UC Read ExBot Agent
version: v4
source_uc: docs/BA/plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases/uc-user-redeem.md (updated 2026-07-04; committed 2026-07-06)
prior_report: docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_audited_20260704_v3.md
---

# UC Readiness Review — UC-EXBOT-user-redeem v4

## Feature Brief

**UC-EXBOT-user-redeem** mô tả luồng đổi thưởng do nhà đầu tư khởi tạo cho ExBot managed LP-hedge bot. Đây là luồng LP-first, được bảo đảm trên chuỗi (on-chain guarantee): nhà đầu tư gọi `BnzaExVault.redeem(tokenId)` trực tiếp trên chuỗi, lập tức thanh lý LP và hoàn trả LP-portion USDC trong cùng một giao dịch. Sau đó, Redeem Worker ngoài chuỗi đóng vị thế short hedge trên HL một cách độc lập (SLA: 5 phút). HL-portion USDC được gửi cho nhà đầu tư qua `RedemptionQueue` ledger sau khi hedge đóng thành công. Nếu hedge close thất bại (sau 3 lần thử hoặc reconcile không khớp), bot chuyển sang trạng thái `residual_hl_liability` và admin được thông báo qua E-EXBOT-024. LP-portion repayment là vô điều kiện và không bao giờ bị đảo ngược.

**Thay đổi trong phiên bản này (audit v4 — 2026-07-07):** BA đã commit các thay đổi vào ngày 2026-07-06 (commit c9a4682). Nội dung thay đổi ảnh hưởng đến UC-user-redeem:

1. **uc-user-redeem.md (updated: 2026-07-04, committed: 2026-07-06):** Thuật ngữ `UserLockDO` → `User Lock (Redis Redlock via ElastiCache)` tại step 8 — đây là thay đổi arc-migration terminology, không thay đổi logic.
2. **SRS files (spec.md, frd.md, erd.md, flows.md):** Cập nhật arc-migration (Cloudflare → AWS) toàn diện — đã được v3 cover.

**Phát hiện mới trong lần re-audit này:** Khi đọc kỹ spec.md và frd.md, phát hiện sự không nhất quán về số FR giữa hai tài liệu đối với Redlock interface (spec.md gọi là FR-EXBOT-092; frd.md gọi là FR-EXBOT-091). Đây là cross-source inconsistency mới cần ghi nhận.

**Score v3: 80/100 — Conditionally Ready.** Re-audit này đánh giá tác động của thay đổi từ commit 2026-07-06 lên score và issue register.

---

## Bảng mã viết tắt

| Code / Prefix | Meaning + role in this project | Defined in |
|---|---|---|
| UC-EXBOT-* | Use Case ID — module ExBot | usecases/index.md |
| FR-EXBOT-* | Functional Requirement — ExBot SRS spec | srs/spec.md |
| BR-EXBOT-* | Business Rule — module ExBot | srs/spec.md §4 Business Rules |
| E-EXBOT-* | Mã lỗi / thông báo — ExBot | backbone/message-list.md |
| SLA | Service Level Agreement — ràng buộc thời gian cho thao tác bất đồng bộ | industry term |
| HL | Hyperliquid — sàn perpetual DEX bên ngoài dùng để mở vị thế short delta-hedge | proper noun |
| LP | Liquidity Provider — vị thế Uniswap V3 do BnzaExVault quản lý | industry term |
| IOC | Immediate-or-Cancel — loại lệnh HL dùng cho hedge close | industry term |
| Redlock | Redis Redlock — thuật toán distributed mutex ngăn nhiều worker cùng thực hiện HL mutation cho một user | industry term |
| ElastiCache | AWS ElastiCache Redis — cụm Redis dùng cho rate limiter, UserLock, pool slot0 cache | proper noun |
| SQS | AWS Simple Queue Service — hàng đợi tin nhắn trong kiến trúc AWS | proper noun |

---

## §0 Scope & Linked Artifacts

| Item | Value |
|---|---|
| UC ID | UC-EXBOT-user-redeem |
| Linked User Story | US-EXBOT-004 |
| FR Trace | FR-EXBOT-070 (UC §7); FR-EXBOT-022, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-092 (spec.md) / FR-EXBOT-091 (frd.md) — xem I-N4 |
| SRS Baseline | srs/spec.md, srs/states.md, srs/flows.md, srs/erd.md (as of 2026-07-04) |
| Prior audit | UC-EXBOT-user-redeem_user-redeem_audited_20260704_v3.md (Conditionally Ready, 80/100) |

---

## §1 Summary of Changes (commit 2026-07-06)

| File | Thay đổi | Loại thay đổi | Tác động |
|---|---|---|---|
| uc-user-redeem.md step 8 | `UserLockDO` → `User Lock (Redis Redlock via ElastiCache)` | Terminology only — arc-migration | Đã được v3 cover; không có issue mới từ thay đổi này |
| spec.md, frd.md, erd.md, flows.md | Cập nhật arc-migration toàn diện (Cloudflare → AWS) | Terminology only | Đã được v3 cover |
| message-list.md | Thêm các message mới cho WL module (không liên quan user-redeem) | Additive — WL scope | Không ảnh hưởng UC-user-redeem |

**Phát hiện mới khi đọc spec.md và frd.md song song:** spec.md đánh số FR-EXBOT-092 cho Redlock interface, trong khi frd.md đánh số FR-EXBOT-091 cho cùng tính năng. Đây là cross-source inconsistency mới — xem I-N4.

---

## §2 Cross-Check: UC vs SRS (v4 delta only)

Tất cả §F.1–§F.5, business rules, alternate flows và issue register từ v3 vẫn còn hiệu lực. Các thay đổi dưới đây áp dụng:

### Terminology consistency (confirmed resolved)

| Item | v3 status | v4 status |
|---|---|---|
| UC step 8 dùng `UserLockDO` vs SRS dùng `Redlock/ElastiCache` | Resolved trong v3 | **Confirmed** — UC committed 2026-07-06 với text `User Lock (Redis Redlock via ElastiCache)`. Hoàn toàn nhất quán với FR-EXBOT-026. |

### New gap: FR number inconsistency giữa spec.md và frd.md cho Redlock

| Issue ID | Type | Severity | Source Trace | Finding | Impact | Status |
|---|---|---|---|---|---|---|
| I-N4 | CROSS_SOURCE_CONFLICT | Low | spec.md FR-EXBOT-092; frd.md FR-EXBOT-091 | spec.md đặt tên `FR-EXBOT-092 — User Lock (Redis Redlock via ElastiCache)`; frd.md đặt tên `FR-EXBOT-091 — User Lock (Redis Redlock)` cho cùng một tính năng. Cả hai đều reference FM-XB-03 và FR-EXBOT-026 nhưng dùng số khác nhau. V3 audit report tham chiếu `FR-EXBOT-092` (theo spec.md). UC file dùng `FR-EXBOT-092` trong FR Trace §7 (theo spec.md). | Tester cần biết số FR chính xác để truy nguồn gốc khi thiết kế test case boundary/negative cho lock behavior. Minor — behavior của Redlock (acquire, extend, release, TTL=90s) nhất quán ở cả hai nguồn; chỉ có số FR khác. | Open — Low priority; BA cần đồng bộ số FR giữa spec.md và frd.md |

### Carry-forward: Open issues từ v3 (không thay đổi)

| ID | Priority | Status | Note |
|---|---|---|---|
| I-02 | High | Open — pending AWS arc update | HL-portion USDC transfer mechanism chưa được xác định: (a) ai tính toán HL-portion amount; (b) ai thực hiện on-chain transfer; (c) tx hash có được lưu trong close_operations không. Commit 2026-07-06 không giải quyết. |
| I-N3 | Medium | Open — unaddressed | `hedge_close_pending` state có trong states.md close_operations table (user_redeem column) nhưng vắng mặt trong UC §3 main flow (nhảy thẳng từ `funds_returned` sang `hedge_closed`). Commit 2026-07-06 không giải quyết. |
| I-N1 | Medium | Open — unaddressed | UC §2 nói "any non-closed state" nhưng states.md chỉ xác nhận `active→lp_closing`. Các trạng thái `hedge_stopped_cooldown`, `lp_rebalancing`, `error` chưa được xác nhận. Commit 2026-07-06 không giải quyết. |
| I-03 | Medium | Partially Resolved | F-04 sequence diagram trong flows.md vẫn chưa có Redlock participant. Commit 2026-07-06 không bổ sung. |
| I-N2 | Low | Open — no block | Retry strategy cho `closeShortReduceOnlyIoc`: in-invocation vs re-queue, backoff delay chưa được xác định. Commit 2026-07-06 không giải quyết. |

---

## §10.3 Audit Summary

### Scoring Table

| Area | Max | v1 Score | v2 Score | v3 Score | v4 Score | Delta v3→v4 | Notes |
|---|---|---|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 14 | 16 | 18 | **18** | 0 | Không có thay đổi logic. I-N4 (cross-source FR numbering) là Low — không trừ điểm Area 1. |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 12 | 16 | 16 | **16** | 0 | I-02 (High, mechanism HL-portion transfer chưa rõ) và I-N3 (Medium, hedge_close_pending missing) vẫn open. I-N4 không ảnh hưởng Area 2. |
| 3. Functional Logic & Workflow Decomposition | 25 | 14 | 16 | 16 | **16** | 0 | I-N1 (precondition states) và I-N3 (state transition) vẫn open. Không có logic change. |
| 4. Functional Integration & Data Consistency | 15 | 12 | 13 | 13 | **13** | 0 | I-03 (F-04 diagram thiếu Redlock) vẫn chưa được giải quyết. Terminology thống nhất đã được xác nhận trong v3. |
| 5. UC / Spec Documentation Quality Issues | 15 | 14 | 16 | 17 | **17** | 0 | I-N4 mới (Low — FR numbering mismatch giữa spec.md và frd.md) được ghi nhận nhưng không ảnh hưởng testability của behavior. Không trừ điểm. |
| **Total** | **100** | **66*** | **77** | **80** | **80** | **0** | |

*v1 score đã được điều chỉnh trong v3 (Blocker auto-cap được gỡ khi I-01 resolved).

**Score: 80/100 — Conditionally Ready** (không thay đổi verdict; thay đổi từ commit 2026-07-06 không tạo ra issue mới có trọng số)

### Verdict: CONDITIONALLY READY (80/100)

**Kết quả re-audit (commit 2026-07-06):**
- Thay đổi trong commit 2026-07-06 đối với UC-user-redeem chỉ là terminology arc-migration (`UserLockDO` → `User Lock (Redis Redlock via ElastiCache)`), đã được v3 cover hoàn toàn.
- Không có logic change, không có business rule mới, không có state transition mới từ commit này.
- Phát hiện mới: I-N4 (Low) — cross-source FR numbering inconsistency giữa spec.md (FR-EXBOT-092) và frd.md (FR-EXBOT-091) cho Redlock. Không ảnh hưởng test design vì behavior nhất quán ở cả hai nguồn.

**Remaining blockers / high issues (không đổi từ v3):**
- **I-02 (High):** Cơ chế gửi HL-portion USDC cho nhà đầu tư (step 13) vẫn chưa được xác định — ai tính, ai thực thi, tx hash lưu ở đâu. Tester không thể xác minh expected result của step 13.
- **I-N3 (Medium):** Trạng thái `close_operations.hedge_close_pending` được xác nhận trong states.md cho user_redeem nhưng vắng mặt trong UC §3 main flow. Tester không thể thiết kế test case state-transition cho trạng thái này.

**Open medium issues (không đổi từ v3):**
- **I-N1 (Medium):** Điều kiện tiên quyết "any non-closed state" không được phản ánh trong states.md — các trạng thái cụ thể (hedge_stopped_cooldown, lp_rebalancing, error) chưa được xác nhận là cho phép user_redeem.
- **I-03 (Medium — Partially Resolved):** F-04 sequence diagram trong flows.md vẫn thiếu Redlock participant. Behavior đã được xác nhận qua FR-EXBOT-026/092.

**Open low issues:**
- **I-N2 (Low):** Chi tiết retry strategy (in-invocation vs re-queue, backoff) chưa được xác định.
- **I-N4 (Low — New):** FR numbering cho Redlock: spec.md dùng FR-EXBOT-092, frd.md dùng FR-EXBOT-091. Không chặn test design.

**Khuyến nghị:**
80/100 — Tiến hành thiết kế test scenario và test case cho tất cả luồng đã xác nhận (happy path, A2, A3). Giữ test case cho step 13 (HL-portion) đến khi I-02 được giải quyết. Bổ sung test case `hedge_close_pending` sau khi BA xác nhận I-N3. I-N1 không chặn happy-path design nhưng chặn boundary/negative test trên pre-states được phép.

---

## §11 Change Log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | 2026-06-28 | QC UC Read ExBot Agent | Initial audit; score 66/100 |
| v2 | 2026-07-03 | QC UC Read ExBot Agent | Re-audit sau BA Q&A (qc-responses-2026-07-03.md): các issue I-01/I-04/I-05/I-06/I-08/I-09/I-10/I-11 closed; score 77/100 |
| v3 | 2026-07-04 | QC UC Read ExBot Agent | Re-audit sau BA arc-migration update (2026-07-04): UserLockDO → Redis Redlock terminology sync; I-03 partially resolved; I-N1/I-N2/I-N3 new issues; score 80/100 |
| v4 | 2026-07-07 | QC UC Read ExBot Agent | Re-audit sau commit 2026-07-06 (c9a4682): xác nhận thay đổi commit là terminology-only (đã cover trong v3); phát hiện I-N4 (Low — FR numbering mismatch spec.md vs frd.md); score không đổi 80/100 |

---

*Report generated by: QC UC Read ExBot Agent | Device: MTS-978 | Run ID: run-20260707-000022-trinhbui*
