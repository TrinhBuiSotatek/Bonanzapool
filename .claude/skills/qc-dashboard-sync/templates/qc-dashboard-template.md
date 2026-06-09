# QC Dashboard

> **Source of truth** cho trạng thái artifact của tất cả features/use cases trong dự án.
>
> **Ownership:**
> - `qc-dashboard-sync` — **owner duy nhất** của file này. Quản lý cột: `Site`, `{{ID_LABEL}}`, `Folder ID`, `Module`, `Feature/Use case name`, `In scope?`, `Files stt`. Tạo file từ template khi chưa có; tự thêm row khi phát hiện folder UC mới qua bottom-up; KHÔNG tự quyết định `In scope?` (chỉ copy từ site-map handoff hoặc set `Need confirm` cho bottom-up).
> - `qc-uc-read` quản lý cột: `UC review stt`.
> - `qc-func-scenario-design` quản lý cột: `Scenario design stt`.
> - `qc-func-tc-design` quản lý cột: `TC design stt`.
> - `qc-site-map` là nguồn duy nhất quyết định feature list + In scope? (qua handoff `site-map-handoff.md` và Mode 3 reconcile của orphans).
> - `qc-context-master` produce project context (KHÔNG tự ghi vào dashboard).
> - Cột `Execute stt` hiện đang pending (chưa có skill quản lý — để trống).
>
> **DO NOT delete rows.** Feature/UC ra khỏi scope vẫn giữ row, user có thể edit `In scope?` về `No` thủ công nếu cần.

| Site | {{ID_LABEL}} | Folder ID | Module | Feature/Use case name | In scope? | Files stt | UC review stt | Scenario design stt | TC design stt | Execute stt |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

---

## Ghi chú trạng thái

- **Site:** Portal/site mà feature/UC thuộc về (vd: Admin, Vendor, User, App, Web...).
- **{{ID_LABEL}}:** Định danh canonical của feature/UC theo site-map. Tên cột adapt theo cách dự án gọi (`Use Case ID`, `Feature ID`, `Story ID`, ...). Sau khi `qc-site-map` Mode 3 reconcile xong, đây là ID chính thức.
- **Folder ID:** ID/tên folder thực tế trên disk (do `qc-dashboard-sync` extract từ tên sub-folder khi scan). Dùng để map disk scan ↔ row.
  - Với row đi qua top-down chuẩn (folder name khớp canonical ID): `Folder ID` = `{{ID_LABEL}}` (self-reference).
  - Với row alias (folder name khác canonical, đã được Mode 3 reconcile): `Folder ID` giữ tên folder gốc, `{{ID_LABEL}}` được update về canonical từ site-map.
  - Với row bottom-up chưa reconcile: `Folder ID` = `{{ID_LABEL}}` = ID extract từ folder (chờ Mode 3 reconcile).
- **Module:** Module / nhóm chức năng.
- **Feature/Use case name:** Tên human-readable (do site-map cung cấp; bottom-up để trống chờ user / Mode 3 cập nhật).
- **In scope?:** `Yes` (in scope) / `No` (out of scope) / `Need confirm` (chưa reconcile bởi site-map Mode 3 — sẽ tự cập nhật sau khi Mode 3 chạy). `qc-dashboard-sync` KHÔNG tự đổi giá trị này; user có thể edit thủ công bất cứ lúc nào.
- **Files stt:** Trạng thái tồn tại của 6 loại file artifact cho UC. Format trong cell: 6 dòng nối bằng `<br>`, theo thứ tự cố định:
  ```
  Specs: V<N> | Missing
  WF: V<N> | Missing
  Audited: V<N> | Missing
  Scenario: V<N> | Missing
  TC md: V<N> | Missing
  TC xlsx: V<N> | Missing
  ```
  Mỗi item tham chiếu folder qua path-registry logical name, lookup folder bằng giá trị `Folder ID` của row:
  - `Specs` ← `requirement-files/<Folder ID>/` (file `.md/.docx/.pdf`, không kể image, không kể `_extracted_`)
  - `WF` ← `requirement-files/<Folder ID>/` (file image: `.png/.jpg/.fig/.svg/...`)
  - `Audited` ← `uc-review-report/<Folder ID>/` (file `*_audited_*.md`)
  - `Scenario` ← `func-test-scenarios/<Folder ID>/` (file có `_scenarios_` trong tên)
  - `TC md` ← `func-test-cases-draft/<Folder ID>/` (file `_testcases_*.md`)
  - `TC xlsx` ← `func-test-cases/<Folder ID>/` (file `_testcases_*_v<N>.xlsx`)
- **UC review stt:** Trạng thái run của `qc-uc-read`. Giá trị:
  - *(trống)* — chưa từng chạy `qc-uc-read`.
  - `Running — <phase friendly name>` — đang chạy phase đó.
  - `<phase friendly name> done` — vừa hoàn thành phase, chưa sang phase tiếp.
  - `<Verdict> v<N> (Score X/100)` — đã review xong (ví dụ: `Conditionally Ready v2 (Score 73.1/100)`, `Ready v1 (Score 92/100)`, `Not Ready v1 (Score 45/100)`).
- **Scenario design stt:** Trạng thái run của `qc-func-scenario-design`. Giá trị:
  - *(trống)* — chưa từng chạy `qc-func-scenario-design`.
  - `Running — <phase friendly name>` — đang chạy phase đó.
  - `<phase friendly name> done` — vừa hoàn thành phase, chưa sang phase tiếp.
  - `v<N> generated` — workflow chạy xong, tạo `V<N>`.
- **TC design stt:** Trạng thái run của `qc-func-tc-design`. Giá trị:
  - *(trống)* — chưa từng chạy `qc-func-tc-design`.
  - `Running — <phase friendly name>` — đang chạy phase đó.
  - `<phase friendly name> done` — vừa hoàn thành phase, chưa sang phase tiếp.
  - `v<N> generated` — workflow `generate-test-cases` chạy xong.
  - `v<N> updated` — workflow `update-test-cases` chạy xong.
- **Execute stt:** Pending (chưa có skill quản lý — placeholder).
