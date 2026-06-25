# Question Backlog — UC-EXBOT-hedge-sync

> Generated: 2026-06-19  
> Source files: `docs/qc/uc-read/UC-EXBOT-hedge-sync/UC-EXBOT-hedge-sync_hedge-sync_audited_20260618_v1.md`

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| I-09 | Low | UC §7 FR Trace; SRS FR-EXBOT-023 | UC §7 FR Trace liệt kê: `FR-EXBOT-022, FR-EXBOT-024, FR-EXBOT-025, FR-EXBOT-026, FR-EXBOT-027, FR-EXBOT-036` — nhưng bỏ sót `FR-EXBOT-021` (LP position amount calculation), `FR-EXBOT-023` (canonical RebalanceReason enum), `FR-EXBOT-030` (stop trigger price computation), `FR-EXBOT-035` (INV-STOP protocol), `FR-EXBOT-040` (circuit breaker), tất cả đều được mô tả trong Main Flow của UC. | Trace không đầy đủ làm khó khăn cho QC khi cần tìm nguồn gốc rule | Open |

Priority: High = blocks test design, Medium = affects scope/coverage, Low = cleanup/traceability  
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| I-02 | High | UC §A5; SRS FR-EXBOT-033; FRD §FR-EXBOT-031 | UC §A5 mô tả luồng khi `stop_replacing_started_at` stuck > 60s như sau: "Enter SAFE_MODE (see uc-deep-audit.md — FR-EXBOT-016 secondary detection path)". Đây là mô tả sai và thiếu vì primary detection là light-check (≤5 min), không phải deep-audit. | UC §A5 đã được viết lại: primary path = light-check enqueue `partial_repair(reason='stop_replacing_overrun')` + SAFE_MODE trong ≤5 min (FR-EXBOT-033); deep-audit chỉ là secondary backstop. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-03 | High | UC §A3; SRS FR-EXBOT-040; US-008 AC-1 | UC §A3 và SRS FR-EXBOT-040 đều ghi "3 consecutive failures within 24h" nhưng không định nghĩa rõ "consecutive" có nghĩa là gì. | "Consecutive" = rolling 24h window, không có lần success nào xen giữa. Nếu có 1 success giữa 3 fail thì failure_count reset. UC §6 BR đã được clarify. Nguồn: FR-EXBOT-040 AC. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-06 | Medium | SRS FR-EXBOT-080, FR-EXBOT-082; UC §3 Main Flow | UC không đề cập bước giải mã HL agent key (AES-GCM decrypt) trước khi ký lệnh HL. Không rõ failure path khi key bị revoke hoặc expired trong khi hedge-sync đang chạy. | UC §3 step 4 đã mô tả bước decrypt agent key (added in prior session). Key revoked mid-run → SAFE_MODE per FR-EXBOT-082. Nếu QC đang đọc snapshot cũ, file hiện tại đã có nội dung này. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-07 | Low | UC §3 (§5 Postconditions) | UC có 2 mục `## Postconditions` — mục thứ hai là placeholder template chưa được xóa ("System state reflects the completed operation", "NFR-ADM-005"). NFR-ADM-005 là NFR của module Admin, không phải ExBot. | Placeholder Postconditions thứ hai đã được xóa khỏi `uc-hedge-sync.md`. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |
| I-08 | Low | UC §Trigger; SRS flows.md F-01 | UC §Trigger ghi placeholder: "User navigates to the relevant screen or initiates the described action." — không mô tả đúng trigger thực tế. | UC §Trigger đã được cập nhật: trigger thực tế là light-check worker enqueue `hedge-sync` message khi phát hiện `RebalanceReason[]`. | BA (ba-response-to-qc-audit-20260620.md) | 2026-06-20 | Answered |

---

## Deferred Questions

| ID | Priority | Ref | Question | Reason Deferred | Deferred Until | Status |
|----|----------|-----|----------|-----------------|----------------|--------|
| I-01 | High | UC §3 Main Flow Bước 5-6; SRS FR-EXBOT-022 | UC không mô tả hành vi khi `delta = 0`. Tester không thể viết test case cho edge case delta = 0 vì expected result chưa được định nghĩa — cụ thể là `rebalance_attempts` ghi status gì, và có update `queue_idempotency.state='succeeded'` không? | BA đã thêm note vào Step 6: không gửi lệnh HL khi delta = 0. Tuy nhiên expected status cho `rebalance_attempts` vẫn pending OQ-EXBOT-013 (owner: Tech Lead). | Pending OQ-EXBOT-013 resolution | Deferred |
| I-04 | Medium | SRS FR-EXBOT-060; UC §3 Main Flow; FRD §4.7 | UC bỏ sót bước fetch `marginSummary` trước hedge-sync. Không rõ vị trí trong flow, hành vi khi `margin_status='warning'` hay `margin_critical`. | BA xác định đây là implementation ordering detail — không thuộc BA UC scope. OQ-EXBOT-014 đã tồn tại để capture câu hỏi này (owner: Tech Lead). | Pending OQ-EXBOT-014 resolution | Deferred |
| I-05 | Medium | SRS FR-EXBOT-091; UC §3 Main Flow | UC không đề cập interaction với `HLRateLimitDO`. Không rõ khi `allowed=false` trong khi đang hold `UserLockDO` lease, worker có release lock trước re-queue không. | BA xác định đây là implementation detail — không thuộc BA UC scope. OQ-EXBOT-015 đã tồn tại để capture câu hỏi này (owner: Tech Lead). | Pending OQ-EXBOT-015 resolution | Deferred |
