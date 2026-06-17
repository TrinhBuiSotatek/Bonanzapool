## Testcase Instruction Rules

### Output Language Selection (READ FIRST)

The output language of test cases is governed by `rules/global-rules.md`:
- **Input UC = Vietnamese** → output test cases in **Vietnamese** → follow the **VI** column of every example below and use `references/Testcase-refer-vi.md` as the style reference.
- **Input UC = English (or any non-Vietnamese language)** → output test cases in **English** → follow the **EN** column of every example below and use `references/Testcase-refer-en.md` as the style reference.

The agent MUST detect the project's working language from the source UC document before applying any rule below, and MUST NOT mix languages within the same output file.

--- 

### Language & Encoding (MANDATORY)

> **Scope note:** 
- If the output language is Vietnamese: apply rule 1, rule 2 and rule 3.
- If the output language is English: apply rule 2 and rule 3.

**Rule 1 — Forbidden transformations.** Do NOT use any of the following on Vietnamese strings before writing to the xlsx:
- `unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()` — strips dấu
- `unidecode(s)` / `text_unidecode(s)` — strips dấu
- Manual replacement maps (`'à' → 'a'`, `'Đ' → 'D'`, …)
- `.encode('latin-1', 'ignore')` / `.encode('cp1252', 'ignore')` — corrupts non-Latin-1 chars
- Any transliteration library

**Rule 2 — Use the shared converter; do NOT write a new script.** xlsx generation is performed by `qc-func-tc-design/scripts/md_to_xlsx.py`, invoked exclusively from `workflows/convert-md-to-xlsx.md` (auto-triggered by the skill — see `SKILL.md` → "Skill Execution Steps"). The agent invokes this script and does NOT write its own openpyxl populator. The script is UTF-8, opens md with `encoding='utf-8'`, writes Unicode literals, and self-verifies before exit. If you must extend the script, preserve these properties — never add `# -*- coding: cp1252 -*-`, never normalize/transliterate.

**Rule 3 — Self-verification before delivery.** After generating the xlsx, open it and spot-check at least 3 rows containing non-ASCII text. If any cell shows: ASCII-only Vietnamese (no dấu, VI projects only), `?` boxes, mojibake (e.g., `Ä\x90`, `Ã©`), or any character that doesn't match the source — STOP, debug the script, regenerate. Do NOT deliver a partially-stripped output.

### Sheet Layout & Section Headers (MANDATORY)

**Columns** (matches the template `Test cases` sheet, row 1 — pin by column letter; the project uses one fixed template):

`A=ID_TC | B=Test Title/Summary of test cases | C=Pre-conditions | D=Step | E=Expected Result | F=Priority`

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

**Rule 1 - DATA HANDLING CONSTRAINT**
- Do NOT hardcode specific values such as system paths, account names, or concrete test data into any part of the test case.
- ALWAYS use the generic name, UI label, or logical placeholder for the information. Do not use the ID, Code.
- When test data requires clarification, provide a short description or example enclosed in parentheses () immediately following the object name.

Examples:
Correct: Kiểm tra màn hình khởi tạo modal: Gán thiết bị cho bệnh nhân.
Correct: Enter email into the "Email" textbox (e.g., a valid formatted email).
Correct: Select a platform from the "Platform" dropdown ("Select platform" placeholder).
Incorrect: Kiểm tra màn hình khởi tạo modal: variant patient-first.
Incorrect: Enter "admin123" into the Username field.
Incorrect: Upload file from "D:\test_data\image.png".

**Rule 2 — UI Notation Standard.** The Agent must utilize specific notations to differentiate on-screen components.

`"Double Quotes"`: Use for interactive components such as Buttons, Menus, Tabs, Icons; or Labels, Placeholders, input values, or selected values from a list.

| VI example | EN example |
|---|---|
| Nhập email vào "Email" textbox | Enter email into the "Email" textbox |
| "Platform" dropdown, "Select platform" placeholder | "Platform" dropdown, "Select platform" placeholder |

**Rule 3 — Content Logic.**

- The content of all parts MUST NOT contain code or ID; all the UI objects must be referred to by their object names (the names used in the audited documentation), in "Double Quotes".
- The Test title MUST begin with the verification verb (exp: Verify, Confirm, Check, Ensure that; Kiểm tra, Đảm bảo rằng).
- The Test title MUST folow this pattern: `Verification verb + test subject name/function name/flow + state + context (if any)` (exp: Kiểm tra màn hình Tạo tài khoản admin khởi tạo khi mở từ Danh sách Admin - Verify the Create Admin screen initialization in case opening from Admin list screen, Kiểm tra nút "Create" - Check "Create" button, Kiểm tra Tạo Admin thành công - Verify that the Admin account is created successfully, Kiểm tra tạo tài khoản admin không thành công trong trường hợp bỏ trống trường email. - Verify Admin account creation fails when Email field is blank.)
- The Test case ID always strictly adhere to the format `TC_[XXX]` — XXX is an incremental number (3 digits). Example: `TC_001`, `TC_002`.
- The Pre-conditions MUST be written in present simple, follow this pattern: System/Subject + is/are + State + Context (if any) (exp: Màn hình "Create Admin account" đang mở - The "Create Admin Account" page is displayed, Người dùng đang đăng nhập là Super Admin - User is logged in as a Super Admin, Dữ liệu email "test@admin.com" đã được tạo trong hệ thống và có trạng thái hoạt động - The email "test@admin.com" already exists and actively in the system).
- The Pre-conditions MUST be a single, one condition per row.
- The Test steps must be a single, follow this pattern: `Imperative Verb + data describe (if any) + UI subject name` (exp: Đi tới trang Đăng nhập của hệ thống Admin - Navigate to the Login screen of the Admin portal, Nhấn vào nút "Đăng nhập" - Click/Tap on "Login" button, Nhập dữ liệu email hợp lệ (phuong.tran@gmail.com) vào trường "Email" - Enter a valid email (phuong.tran@gmail.com) into "Email" field, Để trống trường "Email" - Leave the "Email" field blank).
- The Expected result MUST begin with a step number, explicitly describe the changed state of the UI ov
- The Expected result MUST folow this pattern: 

**Expected Result (UI Verification):**
- MUST begin with a step number (e.g., `1. <expected result>`).
- Do NOT write generic statements.
- Must explicitly describe the changed state of the UI: messages displayed (with full text), popups/screens opened or closed, field states (enabled / disabled / placeholder), display rules (sort order, color), system reactions (allow / block input).
- Do not write expected results from the API or database.

### Test cases example reference (pick by output language):

- **Vietnamese projects** → read `qc-func-tc-design/references/Testcase-refer-vi.md`
- **English projects** → read `qc-func-tc-design/references/Testcase-refer-en.md`

The agent MUST read **only** the file matching the project's output language and align new/updated TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style).
