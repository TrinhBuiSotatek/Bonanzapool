---
name: qc-uc-smoke
description: Performs a lightweight Smoke Review on a UC requirement document — checks structural completeness, UI coverage vs. wireframe, and linguistic clarity, BEFORE deep audit by `qc-uc-read`. Trigger when user says `smoke check use case`, `smoke UC`, `kiểm tra nhanh UC`, `/qc-uc-smoke <UC-ID>`.
---

# Skill: UC Smoke Review

## 1. Mục tiêu & Phạm vi

Smoke Review là **bước gate nhẹ** chạy trước `qc-uc-read`. Mục tiêu: phát hiện nhanh các vấn đề **cấu trúc, đầy đủ, ngôn ngữ** ở mức bề mặt — không đánh giá logic flow, AC atomicity, hay rubric scoring (đó là việc của `qc-uc-read`).

**Output:** danh sách vấn đề có quote/location, phân nhóm `Thiếu / Mâu thuẫn / Chưa rõ / Chưa nhất quán / Note design system`, kèm verdict mềm `Sẵn sàng cho audit sâu` hoặc `Cần điều chỉnh trước khi audit sâu`. **Giọng văn mềm, hợp tác** — không phán xét.

---

## 2. Input Contract

Tra `path-registry.md` để lấy đường dẫn thực tế cho các logical name dưới:

- `requirement-files` (highest version) — tài liệu UC cần smoke.
- `requirement-common-files` (optional) — tra cứu khi UC reference CMR/BR/error code; chỉ inline phần text liên quan.
- `uc-smoke-report` (existing highest version, nếu có) — để xác định số version tiếp theo (không overwrite).

Reference cố định trong skill folder:

- `.claude/skills/qc-uc-smoke/templates/UC-quality-reference.md` — bộ tiêu chí smoke (đã slim cho scope smoke).

> Nếu user chỉ đưa UC-ID mà chưa tồn tại folder UC trong `requirement-files` → STOP và hỏi user xác nhận đường dẫn / tên file UC nguồn.

---

## 3. Output Contract

- **Logical name:** `uc-smoke-report`
- **Path:** `docs/qc/uc-smoke/<UC-ID>/`
- **File pattern:** `<UC-ID>_<feature>_smoke_<YYYYMMDD>_v<N>.md`
- **Versioning:** scan folder, nếu `v<N>` tồn tại → tạo `v<N+1>`. **NEVER overwrite.**
- **Output language:** theo ngôn ngữ tài liệu UC nguồn (tài liệu Vietnamese → output Vietnamese; ngược lại → output English).
- **Header bắt buộc** (theo `global-rules.md` Output Quality Standards):
  - Document title (`Báo cáo Smoke Review — <UC-ID> — <YYYY-MM-DD>`)
  - Tên file requirement nguồn (cùng version đã đọc)
  - Tham chiếu (`UC-quality-reference.md` smoke edition, version)
  - Agent: `qc-uc-smoke`
  - Version: `v<N>`

---

## 4. Worklog (bắt buộc)

Skill này MUST log vào `worklog-per-device` JSONL (resolve path qua `path-registry.md`). Schema và lifecycle theo `docs/qc-lead/agent-work-log.local/README.md` — quy tắc **write-before-work**: append entry mới TRƯỚC khi bắt đầu Phase 1, rewrite dòng cuối ở mỗi phase boundary.

| Thời điểm | Hành động |
|---|---|
| Skill bắt đầu | Append entry mới: `skill=qc-uc-smoke`, `status="Running (Phase 1)"`, `start=now`, `input=[<UC file path>]`, `output=[]` |
| Trước Phase 2 | Rewrite dòng cuối: `status="Running (Phase 2)"` |
| Trước Phase 3 | Rewrite dòng cuối: `status="Running (Phase 3)"` |
| Sau Phase 3 (smoke report đã ghi) | Rewrite dòng cuối: `status="Done"`, `end=now`, `duration_min=...`, `output=[<smoke report path>]` |
| Nếu interrupt | Dòng cuối giữ trạng thái "Running (Phase N)" gần nhất — đây là design |

> Không tự ghi vào `agent-work-log.md` master — đó là quyền của `qc-get-work-log`.

---

## 5. Execution Workflow

Đọc `templates/UC-quality-reference.md` trước khi vào Phase 1.

### Phase 1 — Cấu trúc & Đầy đủ

Đối chiếu UC với quality-reference §1–§5 + §8 (checklist 1–8).

**1.1 Các section bắt buộc**
Lập bảng đối chiếu: Header / Section 1 / Section 2 / Section 3 / Section 4 — `Có mặt`, `Trạng thái`, ghi chú thiếu trường nếu có.
Kiểm tra sub-section trong Section 3 (Main flow / Exception / AC) — **chỉ check sự tồn tại**, không đánh giá chất lượng nội dung.

**1.2 Phạm vi màn hình**
Liệt kê mọi wireframe có trong folder asset, đối chiếu với sub-section §2.x trong tài liệu. Flag:
- Wireframe tồn tại nhưng không có sub-section mô tả tương ứng.
- Sub-section mô tả màn hình nhưng wireframe reference không tồn tại / không truy cập được.
- Nội dung mô tả trong tài liệu **mâu thuẫn** với hiển thị trên wireframe (text/icon/state).

**1.3 Kiểm kê đối tượng UI**
Với mỗi màn hình: đối chiếu mọi UI element hiển thị trên wireframe với field entry trong bảng field tương ứng. Flag:
- Element trên wireframe nhưng không có field entry (nhãn ngày, timestamp, label người gửi, icon…).
- Field entry có nhưng cột `Được sửa` / `Bắt buộc` để `—` thay vì `Y/N`.

### Phase 2 — Out-of-scope notes

Đối chiếu UC với quality-reference §7. **Không yêu cầu sửa**, chỉ ghi nhận và gợi ý hợp tác:

- Mô tả màu sắc cụ thể, font, spacing, border radius pixel → ghi nhận "có thể thuộc design system".
- Mô tả triển khai dev (CI/CD, schema DB, deployment) → ghi nhận "ngoài scope UC".
- Data thật / PII trong ví dụ → **cảnh báo Privacy** (mục này tone hơi mạnh hơn, vì là risk).

> **Bỏ** đánh giá logic nghiệp vụ ở Phase 2 — đó thuộc `qc-uc-read`.

### Phase 3 — Ngôn ngữ

Đối chiếu UC với quality-reference §6 (checklist 12–16).

**3.1 Vấn đề mơ hồ**
Quét toàn UC tìm từ định lượng mơ hồ (§6.1) + từ chất lượng mơ hồ (§6.2) + cụm open-ended (§6.3). Lập bảng: vị trí | nội dung trích | lý do | gợi ý cụ thể hơn.

**3.2 Nhất quán thuật ngữ / động từ**
Phát hiện biến thể của cùng 1 hành động / cùng 1 đối tượng UI (ví dụ "Tap" ↔ "Nhấn" ↔ "Click" cho cùng 1 nút). Lập bảng: hành động | các biến thể | vị trí | gợi ý 1 dạng chuẩn.
Kiểm viết tắt chưa expand lần đầu (§6.4) — list ra.

**3.4 Quét từ cấm**
Đếm số lần và vị trí xuất hiện của các từ trong §6.1–6.3. Bảng: từ | số lần | vị trí.

> **Bỏ** rule "câu > 40 từ" (3.3 cũ) — không thuộc scope smoke.

---

## 6. Output Format

Smoke report theo format quy định trong `templates/UC-quality-reference.md` §10.

**Nguyên tắc giọng văn (BẮT BUỘC):**
- Mềm, hợp tác — "đề xuất bổ sung", "có thể cân nhắc làm rõ", "xin BA xác nhận lại", "nếu phù hợp thì..."
- Tránh: "Thiếu", "Sai", "Vi phạm", "Phải sửa", "Bắt buộc fix" — ngay cả khi vấn đề rõ ràng.
- Mọi vấn đề **phải có quote nguyên văn** và **vị trí cụ thể** (`§X.Y`, `Field #<n>`, `dòng <N>` nếu có) — để BA tra cứu nhanh.
- Phân nhóm vấn đề theo: `Thiếu` / `Mâu thuẫn` / `Chưa rõ` / `Chưa nhất quán` / `Note design system / out-of-scope`. **Không** dùng severity Blocker/Major/Minor (đó là của `qc-uc-read`).

**Verdict mềm (theo §9 template):**
- `Sẵn sàng cho audit sâu` — không có nhóm `Thiếu` hoặc `Mâu thuẫn`.
- `Cần điều chỉnh trước khi audit sâu` — có ≥ 1 nhóm `Thiếu` hoặc `Mâu thuẫn`.

**Section "Gợi ý hành động hợp tác" ở cuối báo cáo** — phải kết thúc bằng câu hợp tác:
> "Nếu các điểm trên được điều chỉnh, tài liệu sẵn sàng để chuyển sang `qc-uc-read` cho audit sâu."

---

## 7. Handoff

- **Verdict = Sẵn sàng cho audit sâu** → gợi ý user chạy `qc-uc-read` trên cùng UC.
- **Verdict = Cần điều chỉnh** → gợi ý user gửi báo cáo này cho BA xem; sau khi BA chỉnh, chạy lại `qc-uc-smoke` lên version UC mới, hoặc nhảy thẳng `qc-uc-read` nếu BA tự tin.
- Smoke **không** auto-invoke skill nào khác.

---

## 8. Quy tắc chung

- KHÔNG overwrite file smoke đã có version — luôn tạo `v<N+1>`.
- KHÔNG ghi vào `agent-work-log.md` master — chỉ ghi `worklog-per-device` JSONL.
- Trích dẫn từ UC nguồn phải để **trong ngoặc kép `""`** đúng nguyên văn (không paraphrase).
- Output language theo input language (Vietnamese-first cho project sotacare).
