# UC Quality Reference — Smoke Edition / Tham chiếu chất lượng UC bản smoke

> **Mục đích:** Bộ tiêu chí **light** dùng cho `qc-uc-smoke` — kiểm tra UC ở mức cấu trúc, đầy đủ thông tin, và chất lượng ngôn ngữ. **Không** thay thế audit sâu (đó là việc của `qc-uc-read`).
> **Phạm vi smoke:** Đủ section / đủ field UI / ngôn ngữ rõ ràng. Logic flow, AC atomicity, cross-reference deep, scoring rubric → thuộc `qc-uc-read`.
> **Trạng thái vấn đề khi smoke:** không gắn severity Blocker/Major/Minor; chỉ ghi nhận theo nhóm `Thiếu`, `Mâu thuẫn`, `Chưa rõ`, `Chưa nhất quán`, `Thuộc design system`.

---

## 1. Danh mục section UC

Mọi UC tổ chức theo 4 section. Section bổ sung optional có thể thêm khi cần.

| # | Section | Trạng thái | Tiêu chí có / không |
|---|---|---|---|
| H | Header (metadata) | Required | Luôn có |
| 1 | Mô tả chức năng | Required | Luôn có |
| 2 | Mô tả giao diện | Required nếu UC có UI | Bỏ khi UC backend-only / API-only / batch |
| 3 | Mô tả các xử lý | Required | Luôn có |
| 4 | Lịch sử cập nhật | Required | Luôn có |

> Smoke **chỉ kiểm tra sự tồn tại** của các section trên + tồn tại của sub-section Main flow / Exception / AC trong Section 3. Đánh giá **chất lượng nội dung** Section 3 (logic, AC atomicity, exception 7 cột) thuộc `qc-uc-read`.

---

## 2. Quy ước nội dung — Header

**Phải có:**
- UC ID + tên (`UC<số> — <tên chức năng>`)
- Phiên bản `v<X.Y>` + ngày tạo
- BA owner (1 người, không "TBD" / không bỏ trống)
- Phân hệ + đối tượng thực hiện
- Status: `draft` / `in-review` / `signed-off` / `deprecated`

**Nên có:**
- Source SRS / requirement (đường dẫn)
- Common rules referenced (list CMR-XX đang dùng)
- Wireframe / design reference (nếu có UI)

**Ví dụ đạt:**
```
**Tiêu đề:** UC60 — Tra cứu thông tin với chatbot
**Phiên bản:** v1.5  **Ngày tạo:** 06/05/2026
| BA phụ trách | huyen.dinh2 |
| Phân hệ | Mobile App |
| Status | in-review |
| Source SRS | /docs/ba/SRS-mobile/SRS_v3.2.md §8.4 |
| Common rules | CMR-06, CMR-07, CMR-09, CMR-17 |
```

---

## 3. Quy ước nội dung — Section 1: Mô tả chức năng (smoke check)

**Phải có:**
- Tên chức năng đầy đủ (không viết tắt)
- Mô tả 1–3 câu nêu: ai dùng, làm gì, vì sao
- Phân quyền cụ thể (≥ 2 actor → nêu rõ "cùng hành vi" hoặc liệt kê khác biệt)
- Phạm vi ngoài UC (Exclusions) — ≥ 2 mục
- Truy cập / Entry point cụ thể
- Preconditions — bullet, mỗi dòng 1 điều kiện atomic
- Postconditions tách riêng `success` / `failure` khi UC có exception

**Không được có:**
- Postcondition mơ hồ ("và/hoặc", "trong trường hợp lỗi", "có thể", "tuỳ thuộc")
- Phân quyền chung chung kiểu "user đã đăng nhập" mà không định role
- Exclusions 1 dòng "không bao gồm gì khác"
- TBD / TODO / dev-comment

---

## 4. Quy ước nội dung — Section 2: Mô tả giao diện (smoke check)

**Phải có:**
- Mỗi state / màn hình = 1 sub-section riêng
- Mỗi sub-section: wireframe reference (đường dẫn cụ thể) + mô tả layout
- Bảng field 7 cột chuẩn: `# | Tên trường | Kiểu trường | Giá trị mặc định | Được sửa | Bắt buộc | Mô tả/Ghi chú`
- Cột **Được sửa** và **Bắt buộc**: dùng `Y` / `N` (không dùng `—`)
- Mọi UI element xuất hiện trên wireframe **phải** có field entry tương ứng (kiểm kê đối chiếu)

> Smoke **không** đánh giá độ sâu cell "Mô tả" (3 sub-block display/action/validate) — đó là việc của `qc-uc-read`. Smoke chỉ flag khi cell hoàn toàn trống / một dòng cụt / thiếu trường hiển nhiên.

---

## 5. Quy ước nội dung — Section 4: Lịch sử cập nhật

**Phải có:** bảng 6 cột `Ngày | Phiên bản | Mục cập nhật | Before | After | Ghi chú / Lý do`, ≥ 1 entry.

**Không được có:**
- Entry không có lý do
- Gộp nhiều thay đổi không liên quan vào 1 entry

---

## 6. Quy ước ngôn ngữ & câu chữ (xuyên suốt)

### 6.1 Từ định lượng mơ hồ — flag
> "có thể", "thường", "đôi khi", "thi thoảng", "khá", "tương đối", "khoảng", "có lẽ", "thường xuyên", "ít khi"

→ Đề xuất thay bằng số / range / điều kiện cụ thể.

### 6.2 Từ chất lượng mơ hồ — flag
> "linh hoạt", "phù hợp", "ổn định", "đầy đủ", "thân thiện", "trực quan", "tối ưu", "hợp lý"

→ Đề xuất thay bằng behavior testable.

### 6.3 Open-ended — flag
> "v.v.", "...", "etc.", "và những thứ khác", "tuỳ trường hợp", "trong nhiều tình huống"

→ Đề xuất liệt kê đủ hoặc khai báo "chỉ những trường hợp sau".

### 6.4 Thuật ngữ & viết tắt
- Viết tắt chưa expand lần đầu (NLP, PII, AI…) — flag tại lần xuất hiện đầu tiên.
- Thuật ngữ nghiệp vụ riêng (BR, CMR, FRD…) chưa định nghĩa — flag.

### 6.5 Nhất quán động từ / thuật ngữ
- Cùng hành động → cùng động từ. Ví dụ: chọn 1 trong "Tap" / "Nhấn" / "Click" / "Chọn" và dùng nhất quán toàn UC.
- Cùng đối tượng UI → cùng tên gọi. Ví dụ: "ô nhập liệu" ≠ "input field" ≠ "text box" trong cùng UC.
- Phát hiện biến thể → liệt kê các nơi xuất hiện và đề xuất 1 dạng chuẩn.

---

## 7. Forbidden / Out-of-scope content (note Phase 2)

Các nội dung dưới đây thường thuộc design system / common rules — smoke chỉ **ghi nhận** (không yêu cầu sửa), gửi gợi ý cho BA xem có nên tách ra file design / CMR riêng hay không.

| Loại nội dung | Ghi nhận khi xuất hiện trong UC |
|---|---|
| Mã màu cụ thể (`#FF0000`, "đỏ đậm", "hồng nhạt") | Note — thuộc design system |
| Font / spacing / size pixel | Note — thuộc design system |
| Border radius cụ thể (`12px`, `pill`) | Note — thuộc design system |
| Mô tả icon pixel-perfect | Note — thuộc design system (mô tả ý nghĩa OK) |
| Marketing speak ("trải nghiệm tuyệt vời", "công nghệ tiên tiến") | Note — không testable |
| Quy trình triển khai dev (CI/CD, DB schema, deployment) | Note — ngoài scope UC |
| Data thật (số ĐT cá nhân, email cá nhân, CMND, tài khoản NH) | Cảnh báo Privacy / PII |

---

## 8. Smoke quick checklist (Agent quét nhanh)

**Phase 1 — Cấu trúc & Đầy đủ:**
1. Header có đủ 5 dòng required (UC ID, version, BA owner, phân hệ, status)?
2. Section 1, 2, 3, 4 đều có?
3. Mỗi state / màn hình trong Section 2 có sub-section riêng?
4. Mọi UI element trên wireframe đều có field entry trong bảng field?
5. Cột "Được sửa" / "Bắt buộc" dùng Y/N (không `—`)?
6. Section 3 có Main flow + Exception flow + AC (chỉ check sự tồn tại)?
7. Section 4 changelog có ≥ 1 entry?
8. Có nội dung mâu thuẫn giữa tài liệu và wireframe?

**Phase 2 — Phạm vi & Out-of-scope notes:**
9. UC có lẫn nội dung design system (màu/font/spacing/border cụ thể)?
10. UC có lẫn nội dung dev/CI/CD/DB schema?
11. UC có lộ dữ liệu thật / PII?

**Phase 3 — Ngôn ngữ:**
12. Có từ định lượng mơ hồ (§6.1)?
13. Có từ chất lượng mơ hồ (§6.2)?
14. Có cụm open-ended "v.v." / "..." / "etc." (§6.3)?
15. Có viết tắt chưa expand lần đầu?
16. Có biến thể động từ / thuật ngữ không nhất quán?

---

## 9. Verdict mềm cho smoke

Smoke **không** dùng verdict READY/CONDITIONAL/NOT READY (đó là của `qc-uc-read`). Dùng 1 trong 2:

| Verdict | Khi nào |
|---|---|
| **Sẵn sàng cho audit sâu** | Không có vấn đề nhóm "Thiếu" hoặc "Mâu thuẫn"; chỉ có vấn đề "Chưa nhất quán" / "Chưa rõ" / "Note design system" ở mức nhẹ |
| **Cần điều chỉnh trước khi audit sâu** | Có ≥ 1 vấn đề nhóm "Thiếu" (section/field) hoặc "Mâu thuẫn" (UC ↔ wireframe / UC ↔ UC) |

> Verdict là gợi ý hợp tác, không phải gate cứng. BA quyết định khi nào chuyển sang `qc-uc-read`.

---

## 10. Output format cho báo cáo smoke

Smoke report follow đúng format dưới. Giọng văn **mềm, hợp tác**: "đề xuất bổ sung", "có thể cân nhắc làm rõ", "xin xác nhận lại"… thay vì "Thiếu", "Sai", "Phải sửa".

```markdown
# Báo cáo Smoke Review — <UC-ID> — <YYYY-MM-DD>

**Tài liệu:** <tên file requirement nguồn>
**Tham chiếu:** UC-quality-reference.md (smoke edition)
**Kết luận:** Sẵn sàng cho audit sâu / Cần điều chỉnh trước khi audit sâu

---

## Phase 1 — Cấu trúc & Đầy đủ

### 1.1 Các section bắt buộc
<bảng đối chiếu 5 section + sub-section bắt buộc trong §3>

### 1.2 Phạm vi màn hình
<bảng đối chiếu màn hình ↔ wireframe ↔ section tài liệu>

### 1.3 Kiểm kê đối tượng UI
<bảng đối chiếu element wireframe ↔ field entry; flag element trên wireframe nhưng chưa được khai báo>

## Phase 2 — Out-of-scope notes
<bảng liệt kê các vị trí có nội dung thuộc design system / dev / PII — tone gợi ý "có thể cân nhắc tách ra">

## Phase 3 — Ngôn ngữ

### 3.1 Vấn đề mơ hồ
<bảng: vị trí | nội dung trích | lý do | gợi ý>

### 3.2 Nhất quán thuật ngữ / động từ
<bảng: hành động/đối tượng | các biến thể đang dùng | vị trí | gợi ý 1 dạng chuẩn>

### 3.4 Quét từ cấm
<bảng: từ | số lần | vị trí>

---

## Tổng hợp

| Nhóm | Số lượng | Tham chiếu |
|---|---|---|
| Thiếu | <n> | <ref §...> |
| Mâu thuẫn | <n> | <ref §...> |
| Chưa rõ | <n> | <ref §...> |
| Chưa nhất quán | <n> | <ref §...> |
| Note design system / out-of-scope | <n> | <ref §...> |

## Gợi ý hành động hợp tác

1. <bullet — tone mềm: "BA xem giúp...", "có thể cân nhắc...", "xin xác nhận lại...">
2. ...
3. Nếu các điểm trên được điều chỉnh, tài liệu sẵn sàng để chuyển sang `qc-uc-read` cho audit sâu.
```

---

**Hết.** File này maintain bởi QC team.

| Version | Ngày | Người update | Ghi chú |
|---|---|---|---|
| v0.1 | 2026-05-26 | QC + AI | Initial draft, base từ format UC60-61_Chatbot + best practice sotacare |
| v0.2 | 2026-05-26 | QC + AI | Slim cho smoke: bỏ §5 logic, §8 cross-ref deep, §11 verdict 3 mức, §12 output cũ; gộp checklist 21 item về 16 item phù hợp smoke scope |
