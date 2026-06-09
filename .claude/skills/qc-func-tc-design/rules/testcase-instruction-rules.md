## Testcase Instruction Rules

### Output Language Selection (READ FIRST)

The output language of test cases is governed by `rules/global-rules.md`:
- **Input UC = Vietnamese** → output test cases in **Vietnamese** → follow the **VI** column of every example below and use `references/Testcase-refer-vi.md` as the style reference.
- **Input UC = English (or any non-Vietnamese language)** → output test cases in **English** → follow the **EN** column of every example below and use `references/Testcase-refer-en.md` as the style reference.

The agent MUST detect the project's working language from the source UC document before applying any rule below, and MUST NOT mix languages within the same output file.

---

### Language & Encoding (MANDATORY)

> **Scope note:** Rules **0a–0d** apply **only when the output language is Vietnamese**. For English-output projects, only Rule 0c's "use the shared converter, do not write a new script" and Rule 0d's "self-verify before delivery (no `?` boxes / mojibake)" still apply — diacritic-preservation and the forbidden-transformation list are not relevant.

**Rule 0a — Preserve Vietnamese diacritics.** All Vietnamese text written into the test cases (Title, Pre-conditions, Steps, Expected Result, Function name, Sub-function) MUST preserve the original diacritics from the source UC document. Do NOT strip, normalize, or transliterate to ASCII.
- ✅ Correct: `"Đăng nhập hệ thống bằng tài khoản NĐT"`, `"Kiểm tra màn hình khởi tạo"`, `"Truy cập menu Báo cáo định kỳ 6 tháng ĐTRNN"`
- ❌ Wrong: `"Dang nhap he thong bang tai khoan NDT"`, `"Kiem tra man hinh khoi tao"`, `"Truy cap menu Bao cao dinh ky 6 thang DTRNN"`

**Rule 0b — Forbidden transformations.** Do NOT use any of the following on Vietnamese strings before writing to the xlsx:
- `unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()` — strips dấu
- `unidecode(s)` / `text_unidecode(s)` — strips dấu
- Manual replacement maps (`'à' → 'a'`, `'Đ' → 'D'`, …)
- `.encode('latin-1', 'ignore')` / `.encode('cp1252', 'ignore')` — corrupts non-Latin-1 chars
- Any transliteration library

**Rule 0c — Use the shared converter; do NOT write a new script.** xlsx generation is performed by `qc-func-tc-design/scripts/md_to_xlsx.py`, invoked exclusively from `workflows/convert-md-to-xlsx.md` (auto-triggered by the skill — see `SKILL.md` → "Skill Execution Steps"). The agent invokes this script and does NOT write its own openpyxl populator. The script is UTF-8, opens md with `encoding='utf-8'`, writes Unicode literals, and self-verifies before exit. If you must extend the script, preserve these properties — never add `# -*- coding: cp1252 -*-`, never normalize/transliterate.

**Rule 0d — Self-verification before delivery.** After generating the xlsx, open it and spot-check at least 3 rows containing non-ASCII text. If any cell shows: ASCII-only Vietnamese (no dấu, VI projects only), `?` boxes, mojibake (e.g., `Ä\x90`, `Ã©`), or any character that doesn't match the source — STOP, debug the script, regenerate. Do NOT deliver a partially-stripped output.

### Sheet Layout & Section Headers (MANDATORY)

**Columns** (matches the template `Test cases` sheet, row 1 — pin by column letter; the project uses one fixed template):

`A=ID_TC | B=Test Title/Summary of test cases | C=Pre-conditions | D=Step | E=Expected Result | F=Priority`

GUI and Functional test cases are written into the **same sheet** (the `Test cases` sheet), starting from row 2, separated by section header rows. The agent MUST insert these header rows in addition to the test case rows.

**Within GUI section, sort in this order (4 buckets):**
1. **Screen Initialization** — initial render, default state, empty / populated state of every object on the screen.
2. **Item Interactions** — every UI object on the screen: textboxes, dropdowns, buttons, icons, labels — clickability, default state, list values, enabled / disabled, placeholder.
3. **Common UI cases** — browser / keyboard interactions: F5 / Refresh, Back / Next browser, Tab / Shift+Tab, Enter, Backspace, zoom in / zoom out, message consistency.
4. **UI elements verify** — visual fidelity vs design: position, color (HEX), spacing, font size, responsive across resolutions.

**Within FUNC section, sort by logical flow:** Happy path first → validation → error / exception cases.

**Hierarchy (use Roman numerals I, II, III… — one per screen / sub-UC). Pick the row that matches the output language:**

| Header level | VI pattern | EN pattern | Where it appears |
|---|---|---|---|
| Screen | `<RomanNumeral>. Màn hình: <tên màn hình>` | `<RomanNumeral>. Screen: <screen name>` | One row per screen / sub-UC |
| GUI section | `<RomanNumeral>.1. Kiểm tra UI/UX của màn hình: <tên màn hình>` | `<RomanNumeral>.1. UI/UX verification — Screen: <screen name>` | Immediately below the screen header |
| FUNC section | `<RomanNumeral>.2. Kiểm tra FUNC của màn hình: <tên màn hình>` | `<RomanNumeral>.2. Functional verification — Screen: <screen name>` | After all GUI test cases for that screen |

**Header row format:**
- Header text goes in column **B** (`Test Title/Summary of test cases`).
- All other columns on the header row stay empty (no TC ID, no Pre-condition, no Step, no Expected Result, no Priority).
- Header rows are NOT counted as test cases — they do not consume TC ID numbers and they are not subject to Rule 2 (`TC_XXX`).
- The screen name in the header MUST match the screen name used in Section 4 of the audited UC file. Do NOT paraphrase or translate.

**Example 1 — Single-screen UC:**

| VI | EN |
|---|---|
| <pre>I. Màn hình: Danh sách báo cáo<br>I.1. Kiểm tra UI/UX của màn hình: Danh sách báo cáo<br>TC_001 \| GUI  \| Kiểm tra màn hình khởi tạo            \| …<br>TC_002 \| GUI  \| Kiểm tra trạng thái mặc định bộ lọc    \| …<br>…<br>I.2. Kiểm tra FUNC của màn hình: Danh sách báo cáo<br>TC_012 \| FUNC \| Kiểm tra hiển thị các kỳ báo cáo      \| …<br>TC_013 \| FUNC \| Kiểm tra trạng thái nộp báo cáo       \| …<br>…</pre> | <pre>I. Screen: Report List<br>I.1. UI/UX verification — Screen: Report List<br>TC_001 \| GUI  \| Verify screen initialization              \| …<br>TC_002 \| GUI  \| Verify default state of filter bar       \| …<br>…<br>I.2. Functional verification — Screen: Report List<br>TC_012 \| FUNC \| Verify display of reporting periods       \| …<br>TC_013 \| FUNC \| Verify report submission state            \| …<br>…</pre> |

**Example 2 — Multi-screen UC (3 screens):**

| VI | EN |
|---|---|
| <pre>I. Màn hình: Danh sách báo cáo<br>  I.1. Kiểm tra UI/UX của màn hình: Danh sách báo cáo<br>  …GUI test cases for screen I<br>  I.2. Kiểm tra FUNC của màn hình: Danh sách báo cáo<br>  …FUNC test cases for screen I<br>II. Màn hình: Tạo mới báo cáo<br>  II.1. Kiểm tra UI/UX của màn hình: Tạo mới báo cáo<br>  …GUI test cases for screen II<br>  II.2. Kiểm tra FUNC của màn hình: Tạo mới báo cáo<br>  …FUNC test cases for screen II<br>III. Màn hình: Chi tiết báo cáo<br>  III.1. Kiểm tra UI/UX của màn hình: Chi tiết báo cáo<br>  …GUI test cases for screen III<br>  III.2. Kiểm tra FUNC của màn hình: Chi tiết báo cáo<br>  …FUNC test cases for screen III</pre> | <pre>I. Screen: Report List<br>  I.1. UI/UX verification — Screen: Report List<br>  …GUI test cases for screen I<br>  I.2. Functional verification — Screen: Report List<br>  …FUNC test cases for screen I<br>II. Screen: Create Report<br>  II.1. UI/UX verification — Screen: Create Report<br>  …GUI test cases for screen II<br>  II.2. Functional verification — Screen: Create Report<br>  …FUNC test cases for screen II<br>III. Screen: Report Detail<br>  III.1. UI/UX verification — Screen: Report Detail<br>  …GUI test cases for screen III<br>  III.2. Functional verification — Screen: Report Detail<br>  …FUNC test cases for screen III</pre> |

### Test Case Writing rules:

**Rule 1 — UI Notation Standard.** The Agent must utilize specific notations to differentiate on-screen components.

`"Double Quotes"`: Use for interactive components such as Buttons, Menus, Tabs, Icons; or Labels, Placeholders, input values, or selected values from a list.

| VI example | EN example |
|---|---|
| Nhập email vào "Email" textbox | Enter email into the "Email" textbox |
| "Platform" dropdown, "Select platform" placeholder | "Platform" dropdown, "Select platform" placeholder |

**Rule 2 — Content Logic.**

**TC ID** (language-agnostic): Always strictly adhere to the format `TC_[XXX]` — XXX is an incremental number (3 digits). Example: `TC_001`, `TC_002`.

**Test Title:**
- Must begin with a verification verb.
- Must include the scenario context.

| VI — verbs | EN — verbs |
|---|---|
| `Kiểm tra`, `Xác nhận` | `Verify`, `Confirm` |

GUI Test Title examples:

| VI | EN |
|---|---|
| Kiểm tra màn hình khởi tạo | Verify screen initialization |
| Kiểm tra UI của màn hình | Verify UI of the screen |
| Kiểm tra khi zoom in/zoom out màn hình | Verify zoom in / zoom out behavior |
| Kiểm tra dữ liệu với độ dài tối đa (maxlength) | Verify data at maximum length (maxlength) |
| Kiểm tra nhấn phím F5 | Verify F5 key press |
| Kiểm tra nút Back của trình duyệt | Verify browser Back button |
| Kiểm tra nút Next của trình duyệt | Verify browser Next button |
| Kiểm tra nút Refresh của trình duyệt | Verify browser Refresh button |
| Kiểm tra thao tác Tab và Shift + Tab | Verify Tab and Shift+Tab navigation |
| Kiểm tra phím Backspace | Verify Backspace key |
| Kiểm tra phím Enter | Verify Enter key |
| Kiểm tra tính nhất quán của message | Verify message consistency |

Functional Test Title — start with the verb plus the business action being verified (e.g., `Kiểm tra <flow>` / `Verify <flow>`).

**Pre-conditions:** Must begin with an action describing what must be performed before executing the test case.

| VI example | EN example |
|---|---|
| Đăng nhập vào hệ thống Admin tại [URL]. | Log in to the Admin system at [URL]. |
| Điều hướng đến màn hình Danh sách Sản phẩm. | Navigate to the Product List screen. |
| Nhấp vào nút "Tạo" và đợi cửa sổ bật lên "Tạo Sản phẩm" mở hoàn toàn. | Click the "Create" button and wait for the "Create Product" popup to fully open. |

**Test Steps (Action-Oriented):**
- Each step must be a single, discrete action on the UI.
- Use active imperative verbs.

| VI — verbs | EN — verbs |
|---|---|
| `Truy cập`, `Nhấp vào`, `Chọn`, `Nhập`, `Di chuột qua`, `Chú ý vào` | `Access`, `Click on`, `Select`, `Enter`, `Hover over`, `Observe` |

| VI example | EN example |
|---|---|
| <pre>1. Tại màn hình Đăng nhập, click vào textbox "Tên đăng nhập"<br>    1.1 Nhập kí tự chữ (không phân biệt chữ hoa, chữ thường) (Eg:Thao)<br>    1.2 Nhập kí tự số (Eg:123456)<br>    1.3 Nhập kí tự đặc biệt (Eg:!@#$%^&*())<br>    1.4 Nhập kí tự chữ và số (Eg:Thao123456)<br>2. Nhấp vào "Đăng nhập" button.<br>3. Kiểm tra trường "Tên đăng nhập"</pre> | <pre>1. On the Login screen, click on the "Username" textbox<br>    1.1 Enter alphabetic characters (case-insensitive) (Eg: Thao)<br>    1.2 Enter numeric characters (Eg: 123456)<br>    1.3 Enter special characters (Eg: !@#$%^&*())<br>    1.4 Enter alphanumeric characters (Eg: Thao123456)<br>2. Click on the "Login" button.<br>3. Verify the "Username" field</pre> |

**Expected Result (UI Verification):**
- MUST begin with a step number (e.g., `1. <expected result>`).
- Do NOT write generic statements.

| VI — generic to avoid | EN — generic to avoid |
|---|---|
| "Hệ thống hoạt động bình thường" | "System works as expected" |

- Must explicitly describe the changed state of the UI: messages displayed (with full text), popups/screens opened or closed, field states (enabled / disabled / placeholder), display rules (sort order, color), system reactions (allow / block input).

GUI Expected Result example:

| VI | EN |
|---|---|
| <pre>2. Hiển thị màn hình "Danh sách báo cáo" giống design (Refer Item I. Danh sách Báo cáo tại sheet WF/Design)<br>- Thanh tìm kiếm: mặc định trống, cho phép nhập dữ liệu<br>- Dropdown [Năm]: mặc định trống, cho phép chọn dữ liệu<br>- Dropdown [Trạng thái kỳ]: mặc định trống, cho phép chọn dữ liệu<br>- Dropdown [Trạng thái hồ sơ]: mặc định trống, cho phép chọn dữ liệu<br>- Danh sách các kỳ báo cáo, gồm các cột:<br> + Năm báo cáo<br> + Trạng thái kỳ báo cáo<br>- Trong từng kỳ báo cáo, gồm các cột<br> + Mã bộ hồ sơ<br> + Số báo cáo đang xử lý<br> + Trạng thái hồ sơ<br> + Ngày cập nhật/nộp<br> + Hành động<br>- Phân trang theo kỳ báo cáo:<br> + Default: 10 kỳ báo cáo / trang<br> + Dropdown chọn số kỳ hiển thị: mặc định là 10</pre> | <pre>2. The "Report List" screen is displayed per design (Refer Item I. Report List in sheet WF/Design)<br>- Search bar: empty by default, allows input<br>- Dropdown [Year]: empty by default, allows selection<br>- Dropdown [Period Status]: empty by default, allows selection<br>- Dropdown [Submission Status]: empty by default, allows selection<br>- Reporting period list with columns:<br> + Reporting year<br> + Reporting period status<br>- Within each reporting period, columns:<br> + Submission code<br> + Number of reports in progress<br> + Submission status<br> + Update/submission date<br> + Action<br>- Pagination by reporting period:<br> + Default: 10 reporting periods / page<br> + Dropdown to select page size: default is 10</pre> |

Functional Expected Result example:

| VI | EN |
|---|---|
| 3. Hiển thị lỗi dưới chân trường dữ liệu: "Tên đăng nhập". Lỗi sẽ biến mất khi user nhập lại dữ liệu vào trường dữ liệu. | 3. An error is displayed below the "Username" field. The error disappears when the user re-enters data into the field. |

### Test cases example reference (pick by output language):

- **Vietnamese projects** → read `qc-func-tc-design/references/Testcase-refer-vi.md`
- **English projects** → read `qc-func-tc-design/references/Testcase-refer-en.md`

The agent MUST read **only** the file matching the project's output language and align new/updated TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style).
