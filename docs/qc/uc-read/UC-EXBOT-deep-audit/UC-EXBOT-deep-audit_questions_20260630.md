# Question Backlog

> Generated: 2026-06-30
> Updated: 2026-07-02
> Source files: UC-EXBOT-deep-audit_audited_20260630_v1.md, qc-notes-temp.md (BA responses)

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q-DA-03 | Medium | UC Step 1; NFR-EXBOT-012; qc-notes-temp.md | UC Step 1 nói worker reads bots từ D1 nhưng không rõ deep-audit worker đọc tất cả bots một lần rồi xử lý tuần tự, hay đọc theo shard. BA xác nhận đây là Tech Lead decision về implementation architecture. Behavior nghiệp vụ không thay đổi dù theo cách nào. | Multi-shard test design cho Phase B (4 shards) phụ thuộc vào shard iteration strategy. Phase A test không bị ảnh hưởng. | Open |
| Q-DA-04 | Low | UC A1; erd.md; qc-notes-temp.md | UC A1 nói "update cadence to high-risk interval (1 hour)" khi HL unreachable nhưng không rõ điều này được ghi vào đâu trong D1. Tech Lead cần xác nhận: Khi cadence switch 6h → 1h, worker có update `bots.next_deep_audit_at` không, hay cron tự handle? | Tester cần verify cadence switching mechanism để design test đúng behavior. Đây là Tech Lead decision về implementation. | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q-DA-01 | ~~High~~ **Resolved** | UC A4; message-list.md; qc-notes-temp.md | ~~Thiếu message content và E-code cho 2 stuck marker notifications~~ | **Đã confirmed.** BA đã thêm E-EXBOT-019 và E-EXBOT-020 vào message-list.md (2026-07-01). E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required." UC A4 đã được update để reference cả 2 E-code. | BA (@hienduong) | 2026-07-01 | Answered |
| Q-DA-02 | ~~Medium~~ **Resolved** | UC A2; states.md row 71; qc-notes-temp.md | ~~Không rõ deep-audit cho paused bot có check stuck markers không. Edge case: active bot → stop fires → user pause → marker stuck > 30min.~~ | **Đã confirmed.** Deep-audit chạy stuck marker detection (steps 4–5) cho cả paused bots. Nếu triggered, bot chuyển `paused → safe_mode`. UC A2 đã được update: "All detection paths (steps 3–7) execute normally, including stuck marker detection (steps 4–5); if triggered, bot transitions from `paused` to `safe_mode`." states.md row 71 đã được update. | BA (@hienduong) | 2026-07-01 | Answered |

---

## Deferred Questions

_(No deferred questions — all questions from audited report have been addressed or remain open pending Tech Lead.)_
