# Agent Work Log — Per-Device JSONL

Mỗi máy 1 file: `worklog_<hostname>.jsonl`. Mọi skill MUST log vào đây ở mỗi phase boundary. Skill `qc-get-work-log` gom vào `../agent-work-log.md`.

## Schema (1 entry = 1 dòng JSONL)

```json
{"run_id":"run-20260519-143022-chrisle3","device":"DESKTOP-ABC123","git_user_name":"Joy","git_user_email":"chris.le3@basao.com","branch":"mbfs","commit":"f7d673a","skill":"qc-uc-read","status":"Running (Phase 2)","input":["docs/BA/UC1/UC1.md"],"output":[],"issue":null,"start":"2026-05-19T14:30:22+07:00","end":null,"duration_min":null}
```

| Field | Cách lấy / quy tắc |
|---|---|
| `run_id` | `run-<YYYYMMDD>-<HHMMSS>-<userslug>` (local time + `git config user.email` phần trước `@`, lowercase, chỉ ký tự `[a-z0-9]`). Sub-skill trong cùng run: nối `.1`, `.2`, … |
| `device` | `$env:COMPUTERNAME` (Win) hoặc `hostname` (Unix) |
| `git_user_name`, `git_user_email` | từ `git config user.name` / `user.email` |
| `branch`, `commit` | `git rev-parse --abbrev-ref HEAD` / `git rev-parse --short HEAD` |
| `status` | `Running (Phase N)` / `Phase N done` / `Done` / `Stopped (<reason>)` / `Interrupted (last: Phase N)` |
| `input`, `output` | array các path file. Loại trừ `process-logging/`. Rỗng = `[]` |
| `issue` | string hoặc `null` |
| `start`, `end` | ISO 8601 với offset `+07:00` (UTC+7). KHÔNG convert timezone |
| `duration_min` | `(end − start) / 60`, làm tròn 1 chữ số. `null` khi đang chạy |

## Lifecycle (write-before-work)

| Thời điểm | Hành động trên JSONL |
|---|---|
| Skill bắt đầu | Nếu `worklog_<hostname>.jsonl` không tồn tại → tạo file rỗng. Append entry mới: `status = "Running (Phase 1)"`, `start = now`, `end = null` |
| Trước phase N (N ≥ 2) | Rewrite dòng cuối: `status = "Running (Phase N)"`. Append `input` files mới (nếu có) |
| Sau phase N done | Rewrite dòng cuối: `status = "Phase N done"`. Append `output` files mới (nếu có) |
| Terminal (Done / Stopped / Interrupted) | Rewrite dòng cuối: terminal `status`, `end = now`, `duration_min` tính ra |

**Rule**: update JSONL **trước** khi bắt đầu phase, không phải sau. Nếu bị interrupt giữa phase, file vẫn phản ánh trạng thái "in progress" gần nhất.

## Notes

- File lẻ được commit vào git. Mỗi máy 1 file → không bao giờ conflict cùng dòng.
- User có thể xóa file lẻ thủ công bất kỳ lúc nào. Dedup theo `(device, start)` đảm bảo `qc-get-work-log` không kéo trùng kể cả khi `run_id` bị reset.
- `qc-get-work-log` KHÔNG tự xóa file lẻ.
