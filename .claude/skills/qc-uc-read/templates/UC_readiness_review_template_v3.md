# Báo cáo rà soát mức độ sẵn sàng của Use Case

**Template rà soát requirement phục vụ thiết kế test**

---

> ## Cách sử dụng template này
>
> Template này dùng để tạo file `*_audited_*.md` sau khi Agent đọc và rà soát use case, tài liệu liên quan, common rules, wireframe/mockup, API hoặc các artefact hỗ trợ khác.
>
> File audited có 2 mục đích:
>
> 1. **Tổng hợp lại cách Agent hiểu nghiệp vụ của use case** để QC Lead / BA / user có thể review xem Agent đã hiểu đúng chưa.
> 2. **Rà soát độ đầy đủ, rõ ràng, nhất quán và khả năng test được của tài liệu**, bao gồm việc đối chiếu với use case liên quan, common rules, site map, project context và các nguồn khác để phát hiện thiếu sót, mâu thuẫn hoặc điểm cần xác nhận.
>
> Không được để trống section. Nếu không áp dụng, ghi `N/A` và giải thích ngắn gọn lý do.
> Không được chỉnh sửa các đầu mục của template.
> Khi viết file phải xoá bỏ các phần nội dung hướng dẫn.

---

## Nguyên tắc viết nội dung audited

Khi viết file audited, Agent phải **tổng hợp ý nghĩa nghiệp vụ**, không chỉ copy lại heading hoặc label trong tài liệu nguồn.

### 1. Viết rõ ràng, tự nhiên

- Viết câu đầy đủ, dễ hiểu cho QC Lead / BA / Tester.
- Không viết kiểu dịch máy hoặc nửa Anh nửa Việt nếu không cần thiết.
- Không dùng các cụm khó hiểu như: `UC cổng`, `UC xuôi dòng`, `hiện thực hoá`, `gắn ngữ cảnh`, `4x case`, `5x exception`.
- Nếu cần giữ thuật ngữ tiếng Anh vì đó là tên chính thức trong sản phẩm, giữ nguyên thuật ngữ đó.

### 2. Không dùng heading/label nguồn thay cho nội dung nghiệp vụ

Các heading, label hoặc mã trong tài liệu nguồn chỉ dùng để trace, không được dùng thay cho phần giải thích.

Ví dụ label nguồn:
- `4x`, `5x`
- `Happy path`, `Alternative flow`, `Exception`
- `Business process`
- tên dòng trong bảng
- tiêu đề section
- mã rule / mã message như `BR-006`, `MSG_E001`, `COMMON-xxx`

Agent phải giải thích ý nghĩa nghiệp vụ trước, sau đó mới đặt mã/label gốc trong ngoặc hoặc phần trích nguồn.

### 3. Bắt buộc trích nội dung nguồn kèm mã/mục gốc

Với mỗi rule, điều kiện, exception, validation, error case, common rule, common message hoặc item được tham chiếu, Agent phải ghi:

1. Diễn giải nghiệp vụ bằng câu rõ ràng.
2. Mã / heading / label gốc nếu có.
3. Nội dung nguồn liên quan, hoặc quote ngắn nhất đủ chứng minh ý đó.

Định dạng khuyến nghị:

```text
[Diễn giải nghiệp vụ]. (Nguồn: <file/section>; mã/mục gốc: <code hoặc heading>; nội dung nguồn: "<trích dẫn ngắn từ source>")
```

Với common rules: với các rule là quy định cần tuân thủ hoặc tránh thì nội dung chính là diễn giải với context hiện tại kèm ghi chú mã/nguồn và nội dung gốc trong dấu ().

```text
[Diễn giải nghiệp vụ]. (Nguồn: common rules; mã: <BR/COMMON ID>; nội dung nguồn: "<nội dung rule gốc>")
```

Với error/message common file: thì trích dẫn chính xác nội dung error/message kèm ghi chú mã/nguồn trong dấu ().

```text
[Trích xuất nội dung message/thông báo]. (Nguồn: common messages; mã: <message ID>; nội dung nguồn: "<nội dung message gốc>")
```

Với các nội dung trích xuất một mục từ tài liệu nguồn thì trích xuất cả mã kèm tiêu đề, nếu mục không có tiêu đề thì trích xuất kèm tiêu đề của mục cha.

```text
[Nội dung mô tả, diễn giải]. (Nguồn: mục X.tiêu đề mục; mã - hoặc nội dung)
[Nội dung mô tả, diễn giải]. (Nguồn: mục X trong phần X.Tiêu đề)
```
### 4. Ví dụ viết đúng

**Ví dụ sai:**

> Banner cảnh báo cho 3 trường hợp 4x (sai credential, account suspended, tenant suspended) + toast cho exception 5x system error.

**Ví dụ nên làm:**

> Khi đăng nhập thất bại do thông tin đăng nhập không đúng, tài khoản người dùng bị tạm ngưng hoặc tổ chức bị tạm ngưng, hệ thống cần hiển thị banner cảnh báo tương ứng trên màn hình đăng nhập. Đây là các trường hợp lỗi do dữ liệu hoặc trạng thái nghiệp vụ không hợp lệ. (Nguồn: mục 4x trong Phần Exception Flow thuộc mục 1; nội dung nguồn: "<trích đúng phần mô tả nhóm 4x trong UC>")

**Ví dụ sai:**

> UC-ORGUSER-001 hiện thực hoá FR-001 và là UC cổng duy nhất cho mọi chức năng nghiệp vụ trong Org Portal.

**Ví dụ nên làm:**

> UC-ORGUSER-001 mô tả quy trình đăng nhập vào Org Portal. Use case này đáp ứng FR-001 về xác thực phiên đăng nhập của người dùng. Người dùng chỉ được truy cập các chức năng trong Org Portal sau khi đăng nhập thành công và hệ thống xác định được tổ chức mà người dùng đang làm việc. (Nguồn: UC §2 Business process; mã/mục gốc: `FR-001`; nội dung nguồn: "<trích đúng nội dung FR-001 hoặc đoạn UC liên quan>")

---

## Feature Brief - Tóm tắt nghiệp vụ

Viết 1-3 đoạn ngắn để mô tả use case theo cách dễ hiểu.

Nội dung cần có:
- use case này dùng để làm gì;
- ai sử dụng;
- điều kiện nào cần có trước khi thực hiện;
- hệ thống xử lý các nghiệp vụ chính nào;
- rule, exception, audit, permission, integration hoặc data/state nào ảnh hưởng đến thiết kế test;
- các use case / module / common rule liên quan nếu có.

Không copy heading hoặc shorthand label từ source làm nội dung giải thích. Nếu heading/mã nguồn quan trọng, hãy giải thích ý nghĩa nghiệp vụ trước, sau đó giữ heading/mã gốc trong phần trích nguồn.

---

## 0. Thông tin tài liệu

| UC ID | Tên feature / use case | Version | Trạng thái tài liệu |
|---|---|---|---|
|  |  |  | Draft / In Review / Finalized / TBD |

| Người viết / BA | Người duyệt | Ngày tạo | Cập nhật lần cuối |
|---|---|---|---|
|  |  |  |  |

| Artefact đã đọc | Version / ngày cập nhật | Vai trò của artefact | Ghi chú |
|---|---|---|---|
|  |  | UC / Wireframe / API / Common rule / Site map / Project context / Other |  |

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu nghiệp vụ

[Giải thích use case tồn tại để giải quyết vấn đề gì, phục vụ ai, mang lại kết quả nghiệp vụ gì.]

### 1.2 Phạm vi trong use case

| Hạng mục / chức năng | Mô tả | Nguồn |
|---|---|---|
|  |  |  |

### 1.3 Ngoài phạm vi / chưa bao gồm

| Hạng mục | Lý do ngoài phạm vi / chưa rõ | Ảnh hưởng đến test |
|---|---|---|
|  |  |  |

---

## 2. Actor, vai trò và quyền hạn

| Actor / Role | Loại | Vai trò trong use case | Quyền hạn / giới hạn liên quan | Nguồn |
|---|---|---|---|---|
|  | Primary / Secondary / System / External |  |  |  |

**Nhận xét readiness:**  
[Đánh giá actor/role đã đủ rõ để thiết kế test theo role chưa. Nếu chưa, nêu rõ thiếu gì.]

---

## 3. Điều kiện trước và kết quả sau

### 3.1 Điều kiện trước

| # | Điều kiện trước | Bắt buộc? | Nguồn |
|---|---|---|---|
| 1 |  | Yes / No / TBD |  |

### 3.2 Kết quả sau khi hoàn tất

| Thao tác | Trạng thái hệ thống / dữ liệu sau khi hoàn tất | Nguồn |
|---|---|---|
| Thêm bản ghi | Bản ghi mới xuất hện ở hàng đầu tiên của danh sách. Thông báo thành công hiển thị |  |

**Lưu ý:** Nếu điều kiện trước hoặc kết quả sau được tham chiếu từ common rule / common function, phải resolve nội dung gốc và ghi rõ mã trong ngoặc.

---

## 4. Danh sách UI object và mapping

> Section này dùng khi có wireframe, mockup, screen spec hoặc mô tả UI. Nếu use case không có UI, ghi `N/A` và giải thích.

| # | Màn hình / khu vực | Label gốc trên UI | Loại component | Bắt buộc? | Giá trị mặc định | Placeholder | Danh sách giá trị / enum | Mô tả / constraint | Nguồn |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  | Text input / Dropdown / Button / Table column / Modal / Toast / Other | Yes / No / N/A |  |  |  |  |  |

Nguyên tắc:
- Mỗi UI element là một dòng riêng.
- Không viết kiểu “9 fields”, “4 buttons”, “N values”.
- Với dropdown/radio/checkbox, liệt kê đầy đủ các giá trị nếu source có.
- Giữ nguyên label gốc trên UI để phục vụ trace và test case.

---

## 5. Thuộc tính và hành vi của UI object

| Object / Component | Trạng thái hệ thống liên quan | Tương tác của user | Hành vi / phản hồi của hệ thống | Nguồn |
|---|---|---|---|---|
|  | Enabled / Disabled / Hidden / Read-only / Loading / Error / Other | Click / Tap / Input / Hover / Submit / Other |  |  |

Nguyên tắc:
- Mỗi object quan trọng ở Section 4 nên có hành vi tương ứng ở Section 5.
- Nếu object không có hành vi đặc biệt, vẫn ghi rõ `Không có hành vi đặc biệt được mô tả trong source`.
- Nếu hành vi được suy luận từ UI hoặc flow, ghi `Suy luận cần xác nhận`.

---

## 6. Phân rã nghiệp vụ và luồng xử lý

> Phân tích các chức năng / sub-flow chính trong use case. Có thể nhân bản block 6.x cho từng function như: đăng nhập, tìm kiếm, tạo mới, cập nhật, xoá, export, phê duyệt, gửi thông báo...

### 6.1 Tên chức năng / luồng: [Tên chức năng]

#### A. Luồng xử lý

| Bước | Actor | Hành động / trigger | Phản hồi hệ thống - happy path | Luồng thay thế | Luồng lỗi / exception | Nguồn |
|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |

#### B. Business rules và validation

| Field / Object / Rule | Điều kiện / constraint | Bắt buộc? | Kết quả khi hợp lệ | Kết quả khi không hợp lệ | Nguồn |
|---|---|---|---|---|---|
|  |  | Yes / No / N/A |  |  |  |

Nếu rule được tham chiếu bằng mã, phải viết rõ nội dung rule:

```text
[Diễn giải rule]. (Nguồn: common rules; mã: <BR/COMMON ID>; nội dung nguồn: "<nội dung rule gốc>")
```

#### C. Thông báo, lỗi và phản hồi UI/UX

| Trường hợp | Loại phản hồi | Nội dung hiển thị / message | Mã / mục gốc | Nguồn |
|---|---|---|---|---|
|  | Banner / Toast / Inline error / Modal / Loading / Empty state / Other |  |  |  |

Nguyên tắc:
- Không ghi chỉ `4x`, `5x`, `error`, `exception`.
- Phải giải thích nguyên nhân lỗi và phản hồi hệ thống.
- Nếu có message code, phải resolve nội dung message gốc.

---

## 7. Phân tích liên kết và ảnh hưởng giữa các chức năng

| Chức năng / hành động kích hoạt | Khu vực / UC / module bị ảnh hưởng | Ảnh hưởng nghiệp vụ | Kiểm tra nhất quán dữ liệu | Nguồn |
|---|---|---|---|---|
|  |  |  |  |  |

Gợi ý phân tích:
- Dữ liệu được tạo/cập nhật ở UC này có xuất hiện ở màn hình hoặc UC khác không?
- Trạng thái thay đổi ở UC này có ảnh hưởng permission, notification, dashboard, report hoặc integration không?
- Có use case nào phụ thuộc vào kết quả của use case này không?

---

## 8. Acceptance Criteria

> Nếu source có AC rõ ràng, tổng hợp lại theo format có thể test được. Nếu source thiếu AC nhưng flow/rule đủ rõ, Agent có thể đề xuất AC từ phần hiểu nghiệp vụ và đánh dấu `Suy luận cần xác nhận`.

| AC # | Scenario | Given - điều kiện | When - hành động | Then - kết quả mong đợi | Nguồn / ghi chú |
|---|---|---|---|---|---|
| AC-01 |  |  |  |  |  |

Nguyên tắc:
- AC phải có thể pass/fail.
- Không viết AC quá chung như “system works correctly”.
- Với AC suy luận, ghi rõ `Suy luận cần xác nhận`.

---

## 9. Yêu cầu phi chức năng

| Nhóm | Requirement | Ảnh hưởng đến test | Nguồn |
|---|---|---|---|
| Performance |  |  |  |
| Security |  |  |  |
| Compatibility |  |  |  |
| Accessibility |  |  |  |
| Audit / Logging |  |  |  |
| Privacy / Compliance |  |  |  |

Nếu không tìm thấy NFR trong source, ghi rõ là thiếu thay vì tự suy đoán.

---

## 10. Gap, mâu thuẫn và câu hỏi mở

### 10.1 Bảng gap và câu hỏi cần xác nhận

| ID | Mức ưu tiên | Loại vấn đề | Tham chiếu nguồn | Nội dung vấn đề / câu hỏi cần xác nhận | Vì sao quan trọng | Owner đề xuất | Trạng thái |
|---|---|---|---|---|---|---|---|
| Q1 | High / Medium / Low | Missing / Unclear / Conflict / Assumption / Suggestion |  |  |  | BA / QC Lead / Tech Lead / PO / TBD | Open |

Nguyên tắc viết câu hỏi:
- Viết bằng tiếng Việt rõ ràng.
- Nêu đúng vấn đề cần BA/QC Lead trả lời.
- Không hỏi chung chung như “Please clarify”.
- Nếu là mâu thuẫn, ghi rõ hai nguồn đang mâu thuẫn như thế nào.
- Nếu là thiếu thông tin, ghi rõ thiếu thông tin nào và ảnh hưởng gì đến test design.

**Ví dụ câu hỏi tốt:**

> UC mô tả trường hợp tài khoản bị tạm ngưng sẽ hiển thị banner lỗi, nhưng chưa nêu nội dung message cụ thể. BA vui lòng xác nhận exact message cần hiển thị cho trường hợp này. Nếu chưa có message, test case không thể kiểm tra đúng expected result của UI.

### 10.2 Dependency cần theo dõi

| Dependency | Loại | Ảnh hưởng | Owner | Trạng thái |
|---|---|---|---|---|
|  | UC / API / Common rule / Data / Integration / Environment / Other |  |  | Open / In Progress / Resolved |

---

## 11. Change log

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1 | YYYY-MM-DD | QC UC Read Agent | Tạo báo cáo audited lần đầu |

---

*Template audited UC readiness - Vietnamese headings version*
