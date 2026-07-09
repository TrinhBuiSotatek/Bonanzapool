# Question Backlog

> Generated: 2026-06-30
> Updated: 2026-07-09
> Source files: UC-EXBOT-deep-audit_audited_20260630_v1.md, UC-EXBOT-deep-audit_audited_20260709_v3.md
> Re-audit: 2026-07-06 (BA document update 2026-07-04)
> BA responses: 2026-07-09 (qc-responses-2026-07-04.md)

---

## Open Questions

_(No open questions — all questions have been addressed or are not applicable.)_

Priority: H = High (blocks design), M = Medium (affects scope), L = Low (nice to know)
Status: Open | Answered | Deferred

---

## Answered Questions

| ID | Priority | Ref | Question | Answer | Answered By | Date | Status |
|----|----------|-----|----------|--------|-------------|------|--------|
| Q-DA-01 | ~~High~~ **Resolved** | UC A4; message-list.md | ~~Thiếu message content và E-code cho 2 stuck marker notifications~~ | **Đã confirmed.** BA đã thêm E-EXBOT-019 và E-EXBOT-020 vào message-list.md (2026-07-01). E-EXBOT-019: "Stop trigger marker stuck for over 30 minutes. Bot entered Safe Mode. Manual review required." E-EXBOT-020: "Stop replacement marker stuck for over 60 seconds. Bot entered Safe Mode. Manual review required." UC A4 đã được update để reference cả 2 E-code. | BA (@hienduong) | 2026-07-01 | Answered |
| Q-DA-02 | ~~Medium~~ **Resolved** | UC A2; states.md row 71 | ~~Không rõ deep-audit cho paused bot có check stuck markers không. Edge case: active bot → stop fires → user pause → marker stuck > 30min.~~ | **Đã confirmed.** Deep-audit chạy stuck marker detection (steps 4–5) cho cả paused bots. Nếu triggered, bot chuyển `paused → safe_mode`. UC A2 đã được update: "All detection paths (steps 3–7) execute normally, including stuck marker detection (steps 4–5); if triggered, bot transitions from `paused` to `safe_mode`." states.md row 71 đã được update. | BA (@hienduong) | 2026-07-01 | Answered |
| Q-DA-03 | ~~Medium~~ **Resolved** | UC Step 1; NFR-EXBOT-012 | ~~Shard iteration strategy cho AWS Lambda deep-audit worker: không rõ Lambda đọc tất cả shards một lần rồi xử lý tuần tự, hay có một EventBridge Scheduler trigger per shard.~~ | **Resolved.** Deep-audit Lambda không tự iterate shards. Kiến trúc v1: EventBridge trigger bot-scan (`rate: 1 minute`) → bot-scan query `bots WHERE status='active'` → fan-out per-bot SQS message → deep-audit Lambda xử lý 1 `botId` duy nhất per invocation. Shard iteration là concern của bot-scan layer, không phải deep-audit. Lưu ý: deep-audit queue đã deploy nhưng không nhận message tự động — `safe_mode_tier` column chưa có trong schema. Periodic 6h cadence (`next_deep_audit_at`) đã có trong DB schema nhưng chưa được wired. **Phase A test cho deep-audit defer sang v1.1.** | BA (@hienduong) | 2026-07-09 | Answered |
| Q-DA-04 | ~~Low~~ **Resolved** | UC A1; erd.md | ~~Cadence switching mechanism (6h→1h) được ghi vào đâu trong Aurora PostgreSQL chưa rõ.~~ | **Resolved.** Cadence switching dùng **Cách A — Lambda ghi `bots.next_deep_audit_at`**: Normal completion → `now + 6h`; HL unreachable (A1) → `now + 1h`; High-risk condition → `now + 1h`. Bot-scan query `WHERE status='active' AND next_deep_audit_at <= now` mỗi phút. EventBridge không tự switch schedule. Field `next_deep_audit_at` và index `idx_bots_due_audit` đã có sẵn trong v1 schema. Mechanism này là v1.1 implementation. | BA (@hienduong) | 2026-07-09 | Answered |
| Q-DA-05 | ~~Major~~ **Resolved** | UC; spec.md; flows.md; erd.md | ~~Cross-source conflict: UC và spec sử dụng "D1" và "HLRateLimitDO" (Cloudflare primitives) trong khi project context chuyển sang AWS architecture.~~ | **Đã resolved (2026-07-04).** BA arc-migration update tất cả files để sử dụng AWS equivalents: D1 → Aurora PostgreSQL, HLRateLimitDO → HL Rate Limiter (ElastiCache Redis), Cron scheduler → EventBridge Scheduler. UC, spec.md, flows.md, erd.md đã được updated. | BA (@hienduong) | 2026-07-04 | Answered |
| Q-DA-06 | ~~Medium~~ **Resolved** | UC Step 2; FR-EXBOT-091; OQ-EXBOT-15 | ~~Deep-audit Step 2 gọi HL qua HL Rate Limiter với weight=2. OQ-EXBOT-15 xác định Tech Lead cần xác định: HL Rate Limiter weight consumption nên được thực hiện trước hay sau khi acquire Redis Redlock?~~ | **Resolved (not applicable cho v1).** Deep-audit v1 không gọi HL thật — `observeDeepAudit()` là stub, không có rate limiter hay Redlock implementation. Với v1.1: deep-audit không dùng Redlock nên không có ordering question — chỉ cần consume weight trước khi gọi HL. OQ-EXBOT-15 chỉ ảnh hưởng hedge-sync, không ảnh hưởng deep-audit. | BA (@hienduong) | 2026-07-09 | Answered |
| Q-DA-07 | ~~Low~~ **Resolved** | UC Step 3; spec.md FR-EXBOT-016 | ~~UC Step 3 verify actual short size từ HL matches `last_known_hl_short_size`. Khi mismatch được phát hiện (→ SAFE_MODE), UC không mô tả rõ liệu `last_known_hl_short_size` có được update thành actual size từ HL không, hay để nguyên giá trị mismatch.~~ | **Resolved.** Worker update `bot_runtime_state.last_known_hl_short_size = actual HL size` và `last_hl_reconcile_at = now` **bất kể match hay mismatch** — trước khi trigger SAFE_MODE. UC đã được update (Step 3 + A3). Behavior này là v1.1 planned, consistent với pattern `§13.3`. Recovery test: Verify `bot_runtime_state.last_known_hl_short_size = actual HL size` trong DB ngay sau mismatch detection, trước khi test recovery path. | BA (@hienduong) | 2026-07-09 | Answered |

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
| 2026-07-09 | Q-DA-03 | Resolved | Shard iteration strategy confirmed: bot-scan fan-out per-bot SQS; deep-audit Lambda xử lý 1 botId per invocation. Phase A test defer sang v1.1 |
| 2026-07-09 | Q-DA-04 | Resolved | Cadence switching dùng Lambda ghi `bots.next_deep_audit_at`; EventBridge không tự switch schedule |
| 2026-07-09 | Q-DA-06 | Resolved | Not applicable cho v1: deep-audit v1 là stub, không gọi HL thật. OQ-EXBOT-15 chỉ ảnh hưởng hedge-sync |
| 2026-07-09 | Q-DA-07 | Resolved | Worker update `last_known_hl_short_size = actual HL size` bất kể match hay mismatch, trước khi trigger SAFE_MODE |
