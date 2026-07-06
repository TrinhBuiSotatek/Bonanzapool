# Question Backlog

> Generated: 2026-06-30
> Updated: 2026-07-06
> Source files: UC-EXBOT-deep-audit_audited_20260630_v1.md, UC-EXBOT-deep-audit_audited_20260630_v2.md
> Re-audit: 2026-07-06 (BA document update 2026-07-04)

---

## Open Questions

| ID | Priority | Ref | Question | Why It Matters | Status |
|----|----------|-----|----------|----------------|--------|
| Q-DA-03 | Medium | UC Step 1; NFR-EXBOT-012 | UC Step 1 nói worker reads bots từ Aurora PostgreSQL nhưng không rõ deep-audit worker đọc tất cả bots một lần rồi xử lý tuần tự, hay đọc theo shard. BA xác nhận đây là Tech Lead decision về implementation architecture. Behavior nghiệp vụ không thay đổi dù theo cách nào. | Multi-shard test design cho Phase B (4 shards) phụ thuộc vào shard iteration strategy. Phase A test không bị ảnh hưởng. | Open |
| Q-DA-04 | Low | UC A1; erd.md | UC A1 nói "update cadence to high-risk interval (1 hour)" khi HL unreachable nhưng không rõ điều này được ghi vào đâu trong Aurora PostgreSQL. Tech Lead cần xác nhận: Khi cadence switch 6h → 1h, worker có update `bots.next_deep_audit_at` không, hay EventBridge Scheduler tự handle? | Tester cần verify cadence switching mechanism để design test đúng behavior. Đây là Tech Lead decision về implementation. | Open |
| Q-DA-06 | Medium | UC Step 2; FR-EXBOT-091; OQ-EXBOT-15 | **MỚI (2026-07-06 Re-audit):** Deep-audit Step 2 gọi HL qua HL Rate Limiter (ElastiCache Redis) với weight=2. OQ-EXBOT-15 (vẫn Open trong spec.md §9) xác định Tech Lead cần xác định: HL Rate Limiter weight consumption nên được thực hiện **trước** hay **sau** khi acquire Redis Redlock? Điều này ảnh hưởng đến retry behavior khi rate limit hit trong khi lock đang held. **Deep-audit không sử dụng Redis Redlock** (không có hedge mutation), nên câu hỏi này ít ảnh hưởng trực tiếp đến deep-audit. Tuy nhiên, FR-EXBOT-091 được thiết kế chung cho cả hedge-sync và deep-audit. | Tech Lead decision về rate limiter ordering ảnh hưởng đến system design tổng thể. Phase A deep-audit test không bị ảnh hưởng trực tiếp. | Open |
| Q-DA-07 | Low | UC Step 3; spec.md FR-EXBOT-016 | **MỚI (2026-07-06 Re-audit):** UC Step 3 verify actual short size từ HL matches `last_known_hl_short_size`. Khi mismatch được phát hiện (→ SAFE_MODE), UC không mô tả rõ liệu `last_known_hl_short_size` có được update thành actual size từ HL không, hay để nguyên giá trị mismatch. Nếu không update, subsequent deep-audit sẽ tiếp tục phát hiện mismatch → potential loop. | Tester cần biết state của `last_known_hl_short_size` sau mismatch detection để design recovery test đúng. Recovery test design phụ thuộc vào behavior này. | Open |

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q-DA-01 | ~~High~~ **Resolved** | UC A4; message-list.md | ~~Thiếu message content và E-code cho 2 stuck marker notifications~~ | **Đã confirmed.** BA đã thêm E-EXBOT-019 và E-EXBOT-020 vào message-list.md (2026-07-01). E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required." UC A4 đã được update để reference cả 2 E-code. | BA (@hienduong) | 2026-07-01 | Answered |
| Q-DA-02 | ~~Medium~~ **Resolved** | UC A2; states.md row 71 | ~~Không rõ deep-audit cho paused bot có check stuck markers không. Edge case: active bot → stop fires → user pause → marker stuck > 30min.~~ | **Đã confirmed.** Deep-audit chạy stuck marker detection (steps 4–5) cho cả paused bots. Nếu triggered, bot chuyển `paused → safe_mode`. UC A2 đã được update: "All detection paths (steps 3–7) execute normally, including stuck marker detection (steps 4–5); if triggered, bot transitions from `paused` to `safe_mode`." states.md row 71 đã được update. | BA (@hienduong) | 2026-07-01 | Answered |
| Q-DA-05 | ~~Major~~ **Resolved** | UC; spec.md; flows.md; erd.md | ~~Cross-source conflict: UC và spec sử dụng "D1" và "HLRateLimitDO" (Cloudflare primitives) trong khi project context chuyển sang AWS architecture.~~ | **Đã resolved (2026-07-04).** BA arc-migration update tất cả files để sử dụng AWS equivalents: D1 → Aurora PostgreSQL, HLRateLimitDO → HL Rate Limiter (ElastiCache Redis), Cron scheduler → EventBridge Scheduler. UC, spec.md, flows.md, erd.md đã được updated. | BA (@hienduong) | 2026-07-04 | Answered |

---

## Deferred Questions

_(No deferred questions — all questions from audited report have been addressed or remain open pending Tech Lead.)_

---

## Change Log

| Date | ID | Action | Description |
|------|----|--------|-------------|
| 2026-07-06 | Q-DA-05 | Resolved | Cross-source conflict (Cloudflare → AWS) đã được BA resolve trong arc-migration 2026-07-04 |
| 2026-07-06 | Q-DA-06 | Added | NEW: OQ-EXBOT-15 (HL Rate Limiter ordering) still Open in spec; minor impact on deep-audit |
| 2026-07-06 | Q-DA-07 | Added | NEW: `last_known_hl_short_size` update behavior after mismatch detection undefined |
