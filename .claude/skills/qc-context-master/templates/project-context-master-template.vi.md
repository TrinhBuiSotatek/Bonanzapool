# Project Context Master: [Tên dự án]

**Trạng thái:** Draft / Reviewed / Approved  
**Ngày tạo/cập nhật:** [YYYY-MM-DD]  
**Người chuẩn bị:** QC Context Agent  
**Người review:** QC Lead / [Tên]  
**Mục đích:** Cung cấp bối cảnh tổng quan cấp project để các QC Agent hiểu đúng hệ thống, phạm vi, rule chung, rủi ro và trạng thái tài liệu trước khi review spec, thiết kế scenario/test case, execute hoặc verify bug.

> File này là tài liệu high-level do Agent tổng hợp để QC Lead review và bổ sung.  
> File này không thay thế spec, wireframe, API document, use case detail hoặc các tài liệu chi tiết do BA/BE/Tech Lead cung cấp.  
> File này nên ngắn gọn, chỉ giữ thông tin có ảnh hưởng đến cách QC Agent hiểu dự án, đánh giá impact, review tài liệu hoặc thiết kế kiểm thử.

---

## Sources consolidated

> Bảng này liệt kê các file đã được đọc và tổng hợp ra nội dung phía dưới. Lần chạy update sau sẽ so version trong tên file (`_v<N>`) để biết source có thay đổi hay không.

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | [tên file đầy đủ, không có path] | v1 / không có version | Feature inventory / Scope / Architecture / Business rules / Site map / Release note / NFR / Other | [YYYY-MM-DD] |

---

## 1. Cách các QC Agent sử dụng file này

| Nhóm Agent / Skill | Cách sử dụng project context | Cần đọc thêm file nào |
|---|---|---|
| Site map / dashboard / high-level review | Hiểu cấu trúc tổng thể hệ thống, site/module/feature, trạng thái tài liệu và các vùng cần theo dõi | Site map, feature list, qc-dashboard, high-level BA docs |
| Spec review - level function | Dùng context tổng quan để kiểm tra spec function có đúng scope, role, flow, rule chung, data/state và integration không | Spec chi tiết, wireframe, API spec nếu có |
| Scenario design | Xác định flow, role, dependency, risk và regression impact trước khi thiết kế scenario | Spec chi tiết, feature list, site map, business flow |
| Test case design | Dùng rule chung, platform/environment, permission, data/state để tránh thiết kế thiếu expected result hoặc thiếu precondition | Scenario, spec, wireframe, API spec |
| Test execute | Hiểu scope, environment, test data, dependency và các lưu ý chung khi execute | Test cases, test data, environment note, defect workflow |
| Bug verify | Hiểu impacted area, expected behavior chung, regression area và rule liên quan khi verify bug | Bug report, spec, test case, regression note |

**Quy tắc sử dụng:**  
Nếu thông tin trong file này mâu thuẫn với spec/wireframe/API chi tiết đã approved, Agent phải báo conflict và ưu tiên tài liệu chi tiết đã approved, trừ khi QC Lead có chỉ định khác.

---

## 2. Tóm tắt dự án

| Hạng mục | Nội dung |
|---|---|
| Tên dự án / sản phẩm |  |
| Domain / nghiệp vụ |  |
| Loại dự án | New build / Enhancement / Migration / Integration / Maintenance / TBD |
| Mục tiêu chính của dự án/release |  |
| Người dùng chính |  |
| Release / phase hiện tại |  |
| Trạng thái tổng quan | Draft / In analysis / In development / In testing / Released / TBD |

**Tóm tắt ngắn:**  
[3-7 dòng mô tả dự án là gì, giải quyết vấn đề gì, hệ thống phục vụ ai, và release này tập trung vào điều gì.]

---

## 3. Phạm vi tổng thể và ranh giới kiểm thử

### 3.1 In scope cấp project/release

| Area / site / module / capability | Mô tả ngắn | Priority | Ghi chú |
|---|---|---|---|
|  |  | High / Medium / Low |  |

### 3.2 Out of scope / chưa làm trong phase này

| Area / site / module / capability | Lý do loại trừ / deferred | Ảnh hưởng đến QC |
|---|---|---|
|  |  |  |

### 3.3 Assumption, dependency, constraint quan trọng

| Loại | Nội dung | Ảnh hưởng đến QC Agent | Cần xác nhận? |
|---|---|---|---|
| Assumption / Dependency / Constraint |  |  | Yes / No |

---

## 4. Cấu trúc hệ thống và tài liệu high-level liên quan

### 4.1 System / site / portal overview

| Site / portal / app | Mục đích | Nhóm user chính | Module chính | Ghi chú |
|---|---|---|---|---|
|  |  |  |  |  |

### 4.2 Các file high-level liên quan

| File | Vai trò | Trạng thái | Ghi chú |
|---|---|---|---|
| Site map | Cung cấp cấu trúc site/module/screen tổng thể | Missing / Draft / Reviewed / Approved |  |
| Feature list | Danh sách feature/use case để đánh giá scope, impact, regression | Missing / Draft / Reviewed / Approved |  |
| qc-dashboard | Theo dõi trạng thái tài liệu/spec/scenario/test case/execute theo từng feature | Missing / Draft / In use / TBD |  |
| Project config | Cấu hình project, convention, path, naming, environment | Missing / Draft / Reviewed / Approved |  |
| Other |  |  |  |

---

## 5. Users, roles và permission tổng quan

| Role / actor | Mô tả | Workflow chính | Permission / responsibility tổng quan | Ghi chú QC |
|---|---|---|---|---|
|  |  |  |  |  |

**Lưu ý:**  
Chỉ ghi permission tổng quan hoặc rule dùng chung. Permission chi tiết theo từng function nên nằm trong spec/function detail.

---

## 6. Business flow, module relationship và impact area

### 6.1 Flow chính cấp project

| Flow ID | Flow name | Actor chính | Module/site liên quan | Trigger | Kết quả chính | Ghi chú impact/regression |
|---|---|---|---|---|---|---|
| FLOW-001 |  |  |  |  |  |  |

### 6.2 Quan hệ giữa module / data / integration

| Area A | Liên quan đến Area B | Kiểu liên quan | Ảnh hưởng QC |
|---|---|---|---|
|  |  | Data dependency / Permission / Integration / Workflow / Reporting / Notification |  |

---

## 7. Rule chung, data/state và integration cần nhớ

### 7.1 Rule chung áp dụng nhiều function

| Rule | Áp dụng cho | Ảnh hưởng đến review/spec/scenario/test case |
|---|---|---|
|  |  |  |

### 7.2 Data object / state quan trọng cấp project

| Object / entity | Mô tả | State / lifecycle chính | Ghi chú QC |
|---|---|---|---|
|  |  |  |  |

### 7.3 Integration / API / job / notification quan trọng

| Item | Loại | Module liên quan | Ghi chú QC / risk |
|---|---|---|---|
|  | API / Integration / Job / Report / Notification / Import / Export |  |  |

---

## 8. Platform, environment, device và NFR/ràng buộc

### 8.1 Platform và environment tổng quan

| Hạng mục | Nội dung | Ghi chú QC |
|---|---|---|
| Platform type | web-responsive / web-static / mobile-native / mobile-hybrid / desktop-native / API-only / backend-job / TBD |  |
| Browser / OS / device cần quan tâm |  |  |
| Test environment | DEV / QA / STG / PROD-like / TBD |  |
| Integration mode | Mock / sandbox / real service / TBD |  |
| Test data / account tổng quan |  |  |

### 8.2 NFR, security, compliance, legal, audit

| Loại ràng buộc | Nội dung đã biết | Ảnh hưởng QC |
|---|---|---|
| Performance / Security / Accessibility / Privacy / Legal / Compliance / Audit / Logging |  |  |

---

## 9. Đánh giá mức độ đủ context cấp project

| Nhóm context | Trạng thái | Độ tin cậy | Ảnh hưởng nếu thiếu/sai | Cần QC Lead bổ sung gì |
|---|---|---:|---|---|
| Project goal & scope | Ready / Partial / Missing / Conflict / N/A | High / Medium / Low |  |  |
| System/site/module overview | Ready / Partial / Missing / Conflict / N/A |  |  |  |
| Feature/use case inventory | Ready / Partial / Missing / Conflict / N/A |  |  |  |
| Users/roles/permission overview | Ready / Partial / Missing / Conflict / N/A |  |  |  |
| Business flows & module relationship | Ready / Partial / Missing / Conflict / N/A |  |  |  |
| Common rules/data/state/integration | Ready / Partial / Missing / Conflict / N/A |  |  |  |
| Platform/environment/device/NFR | Ready / Partial / Missing / Conflict / N/A |  |  |  |
| Document status tracking | Ready / Partial / Missing / Conflict / N/A |  |  |  |

**Kết luận:**  
[Context cấp project hiện đã đủ/chưa đủ để các QC Agent hiểu tổng quan và làm việc đúng chưa? Nếu chưa, thiếu gì có rủi ro cao nhất?]

---

## 10. Open questions và việc cần QC Lead xác nhận

| ID | Câu hỏi / thông tin cần xác nhận | Vì sao quan trọng | Ảnh hưởng nếu chưa rõ | Priority | Owner | Status |
|---|---|---|---|---|---|---|
| Q-001 |  |  |  | High / Medium / Low | QC Lead / BA / Tech Lead / TBD | Open |

---

## Phụ lục A. Nguyên tắc giữ file gọn

- Chỉ ghi thông tin cấp project hoặc thông tin dùng chung cho nhiều Agent/skill.
- Không copy toàn bộ nội dung từ spec, wireframe, API document hoặc use case detail.
- Không ghi test case chi tiết trong file này.
- Không lặp lại danh sách feature dài nếu đã có `feature list` hoặc `qc-dashboard`.
- Nếu thông tin đã có ở file khác, chỉ tóm tắt vai trò và dẫn Agent đọc file đó.
- Nếu một thông tin chỉ ảnh hưởng một function cụ thể, đưa vào function-level context/spec review, không đưa vào file này.
