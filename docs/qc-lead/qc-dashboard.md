# QC Dashboard

> **Source of truth** cho trạng thái artifact của tất cả features/use cases trong dự án.
>
> **Ownership:**
> - `qc-dashboard-sync` — **owner duy nhất** của file này. Quản lý cột: `Site`, `Feature ID`, `Folder ID`, `Module`, `Feature/Use case name`, `In scope?`, `Files stt`. Tạo file từ template khi chưa có; tự thêm row khi phát hiện folder UC mới qua bottom-up; KHÔNG tự quyết định `In scope?` (chỉ copy từ site-map handoff hoặc set `Need confirm` cho bottom-up).
> - `qc-uc-read` quản lý cột: `UC review stt`.
> - `qc-func-scenario-design` quản lý cột: `Scenario design stt`.
> - `qc-func-tc-design` quản lý cột: `TC design stt`.
> - `qc-site-map` là nguồn duy nhất quyết định feature list + In scope? (qua handoff `site-map-handoff.md` và Mode 3 reconcile của orphans).
> - `qc-context-master` produce project context (KHÔNG tự ghi vào dashboard).
> - Cột `Execute stt` hiện đang pending (chưa có skill quản lý — để trống).
>
> **DO NOT delete rows.** Feature/UC ra khỏi scope vẫn giữ row, user có thể edit `In scope?` về `No` thủ công nếu cần.

| Site | Feature ID | Folder ID | Module | Feature/Use case name | In scope? | Files stt | UC review stt | Scenario design stt | TC design stt | Execute stt |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PTL-02 ADMIN | FM-ADM-01 | FM-ADM-01 | WL Partners | WL Partner Onboarding | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-02 | FM-ADM-02 | PF Distribution | PF Distribution | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-03 | FM-ADM-03 | IB Management | IB Management | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-04 | FM-ADM-04 | Bot Config | Bot Type Config | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-05 | FM-ADM-05 | Dashboard | Dashboard (Admin) | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-06 | FM-ADM-06 | Reports | Reports | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-07 | FM-ADM-07 | TOKEN | TOKEN Management | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-08 | FM-ADM-08 | System | System Settings | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-09 | FM-ADM-09 | System | Relayer Monitor | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-10 | FM-ADM-10 | WL Partners | WL Bot Lifecycle Monitor | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-02 ADMIN | FM-ADM-11 | FM-ADM-11 | Users | User Management | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-03 EX | FM-EX-01 | FM-EX-01 | Trading | TradingView Integration | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-03 EX | FM-EX-02 | FM-EX-02 | Trading | Chart Data Feed | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-03 EX | FM-EX-03 | FM-EX-03 | Trading | Order Placement | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-03 EX | FM-EX-04 | FM-EX-04 | Trading | i18n (BNZA-EX) | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-01 | FM-XB-01 | Backend | D1 Schema | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-02 | FM-XB-02 | Backend | Queue Topology | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-03 | FM-XB-03 | Backend | Durable Objects | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-04 | FM-XB-04 | Backend | Cron Jobs | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-05 | FM-XB-05 | Backend | HL Adapter | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-06 | FM-XB-06 | Backend | OPERATOR Facade API | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-07 | FM-XB-07 | Backend | Lifecycle State Machine | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-08 | FM-XB-08 | Backend | Close/Redeem Operations | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-09 | FM-XB-09 | Backend | Phase A1 Dry Run | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | FM-XB-12 | FM-XB-12 | Backend | Envelope Encryption | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-05 POOL | FM-PL-01 | FM-PL-01 | AI Bot | Step 7 Multi-Bot | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-05 POOL | FM-PL-02 | FM-PL-02 | OPS (Admin) | Step 8 plan_specs | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-01 | FM-OPW-01 | Backend | DB Migrations 0024–0027 | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-02 | FM-OPW-02 | Backend | Ledger API | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-03 | FM-OPW-03 | Backend | Bot API | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-04 | FM-OPW-04 | Backend | Post-Record Webhook | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-05 | FM-OPW-05 | Backend | WlNetSent Scanner | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-06 | FM-OPW-06 | Backend | Reconcilers | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT (backend) | FM-OPW-07 | FM-OPW-07 | Backend | fee_collections Exclusion | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | UC-EXBOT-bot-start | UC-EXBOT-bot-start | ExBot | Start ExBot (preflight → LP mint → hedge open → stop place → active) | Need confirm | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | Running — Chấm điểm & xác định gap | | | |
| PTL-04 EXBOT | UC-EXBOT-light-check | UC-EXBOT-light-check | ExBot | Periodic Light-Check (zero HL calls, evaluate rebalance reasons, fan-out) | Need confirm | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | UC-EXBOT-hedge-sync | UC-EXBOT-hedge-sync | ExBot | Delta-only Hedge Adjustment + Stop Replace (INV-STOP protocol) | Need confirm | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | UC-EXBOT-user-redeem | UC-EXBOT-user-redeem | ExBot | User-initiated LP-first Redemption + HL hedge close (SLA 5 min) | Need confirm | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | UC-EXBOT-bot-safe-close | UC-EXBOT-bot-safe-close | ExBot | System Hedge-first Close + USDC park + automatic re-entry closed loop | Need confirm | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-04 EXBOT | UC-EXBOT-agent-key | UC-EXBOT-agent-key | ExBot | Submit + Encrypt + Approve HL Agent Key (AES-GCM envelope) | Need confirm | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| Smart Contract | FM-WLC-01 | FM-WLC-01 | Blockchain | WL Contract Upgrades (A–K) | Yes | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-01 | FM-WLA-01 | WL Admin OOS | WL Admin — Module 1 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-02 | FM-WLA-02 | WL Admin OOS | WL Admin — Module 2 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-03 | FM-WLA-03 | WL Admin OOS | WL Admin — Module 3 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-04 | FM-WLA-04 | WL Admin OOS | WL Admin — Module 4 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-05 | FM-WLA-05 | WL Admin OOS | WL Admin — Module 5 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-06 | FM-WLA-06 | WL Admin OOS | WL Admin — Module 6 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-06 WL Admin [OOS] | FM-WLA-07 | FM-WLA-07 | WL Admin OOS | WL Admin — Module 7 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-01 | FM-MOB-01 | WL Mobile OOS | WL Mobile — Module 1 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-02 | FM-MOB-02 | WL Mobile OOS | WL Mobile — Module 2 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-03 | FM-MOB-03 | WL Mobile OOS | WL Mobile — Module 3 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-04 | FM-MOB-04 | WL Mobile OOS | WL Mobile — Module 4 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-05 | FM-MOB-05 | WL Mobile OOS | WL Mobile — Module 5 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-06 | FM-MOB-06 | WL Mobile OOS | WL Mobile — Module 6 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-07 | FM-MOB-07 | WL Mobile OOS | WL Mobile — Module 7 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-08 | FM-MOB-08 | WL Mobile OOS | WL Mobile — Module 8 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-09 | FM-MOB-09 | WL Mobile OOS | WL Mobile — Module 9 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-10 | FM-MOB-10 | WL Mobile OOS | WL Mobile — Module 10 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |
| PTL-01 WL Mobile [OOS] | FM-MOB-11 | FM-MOB-11 | WL Mobile OOS | WL Mobile — Module 11 | No | Specs: Missing<br>WF: Missing<br>Audited: Missing<br>Scenario: Missing<br>TC md: Missing<br>TC xlsx: Missing | | | | |

---

## Ghi chú trạng thái

- **Site:** Portal/site mà feature/UC thuộc về (vd: Admin, Vendor, User, App, Web...).
- **Feature ID:** Định danh canonical của feature/UC theo site-map. Sau khi `qc-site-map` Mode 3 reconcile xong, đây là ID chính thức.
- **Folder ID:** ID/tên folder thực tế trên disk (do `qc-dashboard-sync` extract từ tên sub-folder khi scan). Dùng để map disk scan ↔ row.
  - Với row đi qua top-down chuẩn (folder name khớp canonical ID): `Folder ID` = `Feature ID` (self-reference).
  - Với row alias (folder name khác canonical, đã được Mode 3 reconcile): `Folder ID` giữ tên folder gốc, `Feature ID` được update về canonical từ site-map.
  - Với row bottom-up chưa reconcile: `Folder ID` = `Feature ID` = ID extract từ folder (chờ Mode 3 reconcile).
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
