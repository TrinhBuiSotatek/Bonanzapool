# QC Site Map: [Tên dự án]

**Trạng thái:** Draft / Reviewed / Approved  
**Mode:** Initialization / Update  
**Ngày tạo/cập nhật:** [YYYY-MM-DD]  
**Người chuẩn bị:** QC Site Map Agent  
**Người review:** QC Lead / [Tên]  
**Baseline:** `project-context-master.md`  
**Mục đích:** Cung cấp bản đồ site/screen/navigation theo góc nhìn QC để hỗ trợ review spec, thiết kế scenario/test case, đánh giá impact, regression và verify bug.

> File này là screen-first QC site map.  
> File này không thay thế `project-context-master.md`, feature list, spec, wireframe, API doc hoặc `qc-dashboard.md`.

---

## 1. Metadata

| Thuộc tính | Giá trị |
|---|---|
| Project / Product |  |
| Platform | Web / Mobile / API / Desktop / Backend / TBD |
| Source baseline | `project-context-master.md` |
| Site map readiness | Ready / Partial / Blocked |
| Source quality | Official / Derived / Mixed / Low confidence |
| Dashboard relationship | Feature-level handoff only |
| Ghi chú |  |

---

## 2. Sources consolidated

> Bảng này liệt kê các file đã được đọc và tổng hợp ra nội dung phía dưới. Lần chạy update sau sẽ so version trong tên file (`_v<N>`) để biết source có thay đổi hay không.

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | project-context-master.md | no-version | Project baseline | [YYYY-MM-DD] |
| 2 | [tên file đầy đủ, không có path] | v1 / no-version | Site map / Menu / Feature list / Wireframe / Role matrix / User flow / Release note / Other | [YYYY-MM-DD] |

---

## 3. Site / Portal / App overview

| Site / Portal / App | Mục đích | Nhóm user chính | Module / Area chính | Ghi chú QC |
|---|---|---|---|---|
|  |  |  |  |  |

---

## 4. Screen-first site map tree

```text
[System / Product]
├── [Site / Portal / App]
│   ├── [Area / Module]
│   │   ├── [Screen / Page]
│   │   │   ├── [Sub-screen / Tab / Modal]
│   │   │   └── [Action / Entry point]
```

---

## 5. Screen / Page inventory

| Screen ID | Site / Portal | Area / Module | Screen / Page | Type | Platform | Source | Status |
|---|---|---|---|---|---|---|---|
| SCR-001 |  |  |  | Page / Modal / Tab / Dashboard / Form / Report | Web / Mobile / API / Admin / TBD |  | Confirmed / Derived / Need confirm / Conflict |

---

## 6. Navigation & screen flow

| Flow ID | Flow name | Role | Start screen | Main path | End screen / outcome | Related feature(s) | Notes |
|---|---|---|---|---|---|---|---|
| FLOW-001 |  |  |  |  |  |  |  |

---

## 7. Role / access by screen

| Role / User type | Accessible site/module | Accessible screen | Key actions | Restriction / Rule | Source | Status |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  | Confirmed / Derived / Need confirm / Conflict |

---

## 8. Screen ↔ Feature mapping

| Screen ID | Screen / Page | Feature ID | Feature name | Mapping type | Regression anchor? | Notes |
|---|---|---|---|---|---|---|
| SCR-001 |  |  |  | Primary / Supporting / Shared / Unknown | Yes / No / Need review |  |

### Feature-level coverage summary for dashboard

| Feature ID | Feature name | Mapped screen(s) | Site map status | Gap / Note |
|---|---|---|---|---|
|  |  |  | Mapped / Partial / Missing / Conflict / Need confirm |  |

---

## 9. Screen ↔ Data / API / Integration / State touchpoints

| Screen / Flow | Data object / API / Integration / State | Rule / lifecycle liên quan | QC impact | Source |
|---|---|---|---|---|
|  |  |  |  |  |

---

## 10. Regression / impact anchors

| Anchor | Type | Related feature(s) | Related screen(s) | Vì sao quan trọng | Suggested regression focus |
|---|---|---|---|---|---|
|  | Core flow / Shared component / Permission / Integration / Data state / Report |  |  |  |  |

---

## 11. Gaps / conflicts / assumptions

| ID | Issue | Type | Impact to QC | Suggested owner | Priority | Status |
|---|---|---|---|---|---|---|
| GAP-001 |  | Missing / Conflict / Assumption / Unclear |  | QC Lead / BA / Tech Lead / TBD | High / Medium / Low | Open |

---

## 12. Readiness assessment

| Area | Status | Reason | Required action |
|---|---|---|---|
| Screen inventory | Ready / Partial / Blocked |  |  |
| Navigation flow | Ready / Partial / Blocked |  |  |
| Role/access by screen | Ready / Partial / Blocked |  |  |
| Screen-feature mapping | Ready / Partial / Blocked |  |  |
| Data/API/integration/state touchpoints | Ready / Partial / Blocked / N/A |  |  |
| Regression/impact usage | Ready / Partial / Blocked |  |  |
| Dashboard feature-level handoff | Ready / Partial / Blocked |  |  |

**Kết luận:** Đủ / Tạm đủ / Chưa đủ  
**Ghi chú cho QC Lead:** [Các điểm cần review hoặc bổ sung trước khi downstream QC Agents sử dụng.]
