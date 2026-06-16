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

Functional test cases are written into the **`Test cases` sheet**, starting from row 2, separated by section header rows. The agent MUST insert these header rows in addition to the test case rows.

**Within FUNC section, sort by logical flow:** Happy path first → API contract / validation → state transitions → exception / error cases.

**Hierarchy (use Roman numerals I, II, III… — one per operation / sub-UC). Pick the row that matches the output language:**

| Header level | VI pattern | EN pattern | Where it appears |
|---|---|---|---|
| Operation | `<RomanNumeral>. Nghiệp vụ: <tên nghiệp vụ>` | `<RomanNumeral>. Operation: <operation name>` | One row per operation / sub-UC |
| FUNC section | `<RomanNumeral>.1. Kiểm tra FUNC của nghiệp vụ: <tên nghiệp vụ>` | `<RomanNumeral>.1. Functional verification — Operation: <operation name>` | Immediately below the operation header |

**Header row format:**
- Header text goes in column **B** (`Test Title/Summary of test cases`).
- All other columns on the header row stay empty (no TC ID, no Pre-condition, no Step, no Expected Result, no Priority).
- Header rows are NOT counted as test cases — they do not consume TC ID numbers and they are not subject to Rule 2 (`TC_XXX`).
- The operation name in the header MUST match the operation name used in Section 6 of the audited UC file. Do NOT paraphrase or translate.

**Example 1 — Single-operation UC:**

| VI | EN |
|---|---|
| <pre>I. Nghiệp vụ: Bot Start<br>I.1. Kiểm tra FUNC của nghiệp vụ: Bot Start<br>TC_001 \| FUNC \| Kiểm tra POST /api/exbot/start thành công   \| …<br>TC_002 \| FUNC \| Kiểm tra preflight thất bại → 403           \| …<br>…</pre> | <pre>I. Operation: Bot Start<br>I.1. Functional verification — Operation: Bot Start<br>TC_001 \| FUNC \| Verify POST /api/exbot/start success path  \| …<br>TC_002 \| FUNC \| Verify preflight fail → 403                  \| …<br>…</pre> |

**Example 2 — Multi-operation UC (3 operations):**

| VI | EN |
|---|---|
| <pre>I. Nghiệp vụ: Bot Start<br>  I.1. Kiểm tra FUNC của nghiệp vụ: Bot Start<br>  …FUNC TCs for operation I<br>II. Nghiệp vụ: Hedge Sync<br>  II.1. Kiểm tra FUNC của nghiệp vụ: Hedge Sync<br>  …FUNC TCs for operation II<br>III. Nghiệp vụ: User Redeem<br>  III.1. Kiểm tra FUNC của nghiệp vụ: User Redeem<br>  …FUNC TCs for operation III</pre> | <pre>I. Operation: Bot Start<br>  I.1. Functional verification — Operation: Bot Start<br>  …FUNC TCs for operation I<br>II. Operation: Hedge Sync<br>  II.1. Functional verification — Operation: Hedge Sync<br>  …FUNC TCs for operation II<br>III. Operation: User Redeem<br>  III.1. Functional verification — Operation: User Redeem<br>  …FUNC TCs for operation III</pre> |

### Test Case Writing rules:

**Rule 1 — Notation Standard.** The Agent must utilize specific notations to differentiate values and identifiers.

`"Double Quotes"`: Use for field names, parameter names, error codes/messages, queue/DO identifiers, or specific values being tested.

| VI example | EN example |
|---|---|
| Gửi request với "user_id" thiếu | Send request with "user_id" missing |
| Queue "QUE-XB-08" được enqueue thành công | Queue "QUE-XB-08" is enqueued successfully |

**Rule 2 — Content Logic.**

**TC ID** (language-agnostic): Always strictly adhere to the format `TC_[XXX]` — XXX is an incremental number (3 digits). Example: `TC_001`, `TC_002`.

**Test Title:**
- Must begin with a verification verb.
- Must include the scenario context.

| VI — verbs | EN — verbs |
|---|---|
| `Kiểm tra`, `Xác nhận` | `Verify`, `Confirm` |

Functional Test Title — start with the verb plus the business action or API operation being verified.

| VI example | EN example |
|---|---|
| Kiểm tra POST /api/exbot/start khi preflight thành công | Verify POST /api/exbot/start when preflight passes |
| Kiểm tra trạng thái IDLE → STARTING khi nhận trigger hợp lệ | Verify IDLE → STARTING state transition on valid trigger |
| Kiểm tra lỗi 403 khi gọi endpoint không có quyền | Verify 403 error when calling endpoint without permission |
| Kiểm tra idempotency của queue consumer khi nhận message trùng | Verify queue consumer idempotency on duplicate message |

**Pre-conditions:** Must begin with an action describing what must be performed before executing the test case.

| VI example | EN example |
|---|---|
| Bot đang ở trạng thái IDLE trong D1. | Bot is in IDLE state in D1. |
| UserLockDO không có lease đang hoạt động. | UserLockDO has no active lease. |
| Gọi POST /api/exbot/start với token hợp lệ của ACT-02. | Call POST /api/exbot/start with a valid ACT-02 token. |

**Test Steps (Action-Oriented):**
- Each step must be a single, discrete action or call.
- Use active imperative verbs.

| VI — verbs | EN — verbs |
|---|---|
| `Gửi`, `Gọi`, `Kiểm tra`, `Chú ý vào`, `Truy vấn`, `Enqueue` | `Send`, `Call`, `Verify`, `Observe`, `Query`, `Enqueue` |

| VI example | EN example |
|---|---|
| <pre>1. Gọi POST /api/exbot/start với body:<br>    { "user_id": "uuid-valid" }<br>2. Kiểm tra response trả về.<br>3. Truy vấn D1: SELECT status FROM bots WHERE user_id = ?</pre> | <pre>1. Call POST /api/exbot/start with body:<br>    { "user_id": "uuid-valid" }<br>2. Verify the response returned.<br>3. Query D1: SELECT status FROM bots WHERE user_id = ?</pre> |

**Expected Result:**
- MUST begin with a step number (e.g., `1. <expected result>`).
- Do NOT write generic statements.

| VI — generic to avoid | EN — generic to avoid |
|---|---|
| "Hệ thống hoạt động bình thường" | "System works as expected" |

- Must explicitly describe the changed state: HTTP status code + response body, D1 state change, queue enqueue confirmation, DO lease status, error code + message exact text.

Functional Expected Result example:

| VI | EN |
|---|---|
| <pre>2. Response: 200 OK<br>   { "status": "STARTING", "bot_id": "uuid" }<br>3. D1: bots.status = "STARTING", started_at = now<br>   QUE-XB-01 enqueued với bot_id + epoch_slot</pre> | <pre>2. Response: 200 OK<br>   { "status": "STARTING", "bot_id": "uuid" }<br>3. D1: bots.status = "STARTING", started_at = now<br>   QUE-XB-01 enqueued with bot_id + epoch_slot</pre> |

### Test cases example reference (pick by output language):

- **Vietnamese projects** → read `qc-func-tc-design/references/Testcase-refer-vi.md`
- **English projects** → read `qc-func-tc-design/references/Testcase-refer-en.md`

The agent MUST read **only** the file matching the project's output language and align new/updated TCs to the same structural & writing style (TC ID format, Title phrasing, Pre-condition / Step / Expected Result layout, multi-line bullet style).
