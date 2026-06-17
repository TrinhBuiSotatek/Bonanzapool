---
name: qc-writting-rules
description: Writing rules for QC outputs — universal rules for all skills, plus an audit-prose tier for reports that cite codes
sections:
  - "§1 Language policy — all skills"
  - "§2 Universal rules — all skills listed in applies_to_skills.universal"
  - "§3 Code-reference reporting rules — only skills listed in applies_to_skills.audit_prose_only"
applies_to_skills:
  universal:                    # §1 + §2 apply
    - qc-uc-read
    - qc-uc-smoke
    - qc-func-scenario-design
    - qc-context-master
    - qc-site-map
  audit_prose_only:             # §3 applies in addition to §1 + §2
    - qc-uc-read
    - qc-uc-smoke
excluded_skills: all skills not listed under applies_to_skills.universal
---

# QC Output Writing & Reference Readability Rules

Use these rules when writing quality control (QC) reports and artifacts for the skills being applied.

Supported output languages:

- **English**
- **Vietnamese**

Intended readers: QC Lead, BA, Tester, and delivery stakeholders.

Goal: make QC outputs easy to understand, easy to trace back to source documents, and reusable for downstream test design and execution.

This file is organized in two tiers:

- **§2 Universal rules** apply to every QC output (both atomic structured artifacts and prose reports).
- **§3 Code-reference reporting rules** apply ONLY to human-read prose that cites codes (audit reports, gap reports, scenario rationale, project/site-map summaries). They do NOT apply to atomic structured artifacts (test cases, RTM tables, dashboard rows, site-map rows) — those have fixed-role cells and do not need code-glossary, citation, or meaning-first prose conventions.

--- 

## §1. Language policy

- If the requested output language is **English**, apply the **Common rules** of §2 (and §3 if applicable).
- If the requested output language is **Vietnamese**, apply both **Common rules** and **Vietnamese rules** of §2 (and §3 if applicable).
- Keep official IDs, codes, file paths, API names, screen names, message keys, and product terms unchanged unless the source provides an official localized name.
- Write human-readable explanations in the requested output language.
- English examples are illustrative; do not copy them word-for-word into Vietnamese output.
- Vietnamese examples are style guidance only for Vietnamese output.

---

## §2. Universal rules (apply to all QC outputs)

These rules apply to every output produced by skills listed in `applies_to_skills.universal`, regardless of whether the artifact is prose (audit report) or atomic structured (test case, RTM, dashboard row, site-map row).

### §2.A — Common rules (EN + VI)

#### Rule 2A1 — Write for the reader, not for source lookup

Write for readers who need to understand the meaning quickly and act on it.

- For audit reports the reader reviews issues and decides next steps.
- For test cases the reader (Tester) executes steps and verifies expected results.
- For site-map / dashboard rows the reader scans for coverage status.

In all cases, the output must stand alone — the reader should not need to reopen the source UC, FRD, or design file to understand the line in front of them.

#### Rule 2A2 — Use complete, self-contained sentences in standalone units

Each finding, question, recommendation, test step, expected result, or table prose cell must be clear without reopening the source document.

Prefer:

`subject + condition + system behavior + expected result / business or test impact`

Avoid vague phrases such as:

- “system works as expected”
- “mapping issue”
- “downstream flow”
- “4x/5x cases”
- code-only explanations

#### Rule 2A3 — Preserve official identifiers

Keep official identifiers unchanged when needed for traceability. 
It is preferable to use the names of identifiers or descriptions accompanying the code within parentheses.

Examples:

- `UC-*`
- `FR-*`
- `BR-*`
- `CRULE-*`
- `FOQ-*`
- `Q\d+`
- `AC-*`
- `SCR-*`
- `MSG_*`
- `ERR_*`
- `WCAG x.x.x`
- API names
- file names 
- screen names (SCR-*)
- message keys

### §2.B — Vietnamese rules (VI output only)

Apply this sub-section only when the requested output language is **Vietnamese**.

#### Rule 2B1 — Preserve Vietnamese diacritics

All Vietnamese text written in any output file / report / plan MUST be written in Vietnamese with diacritics. It MUST NOT be removed, standardized, or converted to ASCII.

- ✅ Correct: `"Đăng nhập hệ thống bằng tài khoản NĐT"`, `"Kiểm tra màn hình khởi tạo"`, `"Truy cập menu Báo cáo định kỳ 6 tháng ĐTRNN"`
- ❌ Wrong: `"Dang nhap he thong bang tai khoan NDT"`, `"Kiem tra man hinh khoi tao"`, `"Truy cap menu Bao cao dinh ky 6 thang DTRNN"`

#### Rule 2B2 — Write in natural Vietnamese

Write as a business document for BAs / QCs / Testers, not a word-for-word translation from English.
Do not use a mix of Vietnamese and English if the English term is not an official product term.
If the English term is an official term, it can be kept as is, but an explanation must be provided the first time.

Do not write:
> Hệ thống hiện thực hoá trạng thái người dùng trong ngữ cảnh tổ chức.
> UC này trigger downstream flow để resolve org context.

Write:
> Hệ thống cần xác định rõ trạng thái tài khoản của người dùng trong từng tổ chức để BA và Tester biết khi nào người dùng được phép đăng nhập, bị chặn, hoặc cần xử lý ngoại lệ.
> UC này kích hoạt luồng xử lý tiếp theo để xác định tổ chức mà người dùng đang thao tác.

#### Rule 2B3 — Avoid ambiguous phrases

Do not use ambiguous phrases or phrases that sound like machine translations:

- "UC cổng"
- "UC xuôi dòng"
- "hiện thực hoá"
- "gắn ngữ cảnh tổ chức"
- "4x/5x cases"
- "system error exception"
- "luồng downstream"
- "context binding"
- "rule mapping bị hở"

Replace them with clear descriptions of the conditions, system behavior, results, and consequences of the test.

#### Rule 2B4 — Default to Vietnamese; keep English only when it falls into one of three exception categories
Target reader: a Junior QC with ~1–2 years experience, Vietnamese-first, familiar with basic QA concepts (test case, scenario, regression, defect) but NOT fluent in casual English tech jargon used by Devs/PMs.

Default: write Vietnamese. An English word may be kept verbatim ONLY when it falls into one of the three exception categories below. Any English word outside these categories must be translated into Vietnamese.

Three exception categories (English allowed):

Technical identifiers — function names, table/column/field names, file names, endpoint paths, state machine state names, ID codes, on-chain addresses, environment variables.
Examples: addRewards(), wl_partners, convert_to_usdc, backbone.md, /api/wl/ledger, pending_set, BOT_SYNC, 0xa5B8…C969, FM-WLA-01, BR-ADM-001.

Proper nouns — names of platforms, products, smart contracts, SDKs, brands, or organisations that the project uses verbatim.
Examples: Hyperliquid, RewardDistributor, BnzaSplitter, Cloudflare, Reown AppKit, Uniswap V3, MEGABUCKS, Helix.

Industry terms / acronyms that have a row in the glossary (§3A4) — kept English but MUST be backed by a glossary entry.
Examples: SIWE, HMAC, PWA, RBAC, NFR, WCAG, MLM, LP, WL, AUM, TVL, PF.
If an industry acronym is not yet in the glossary, add a glossary row before using it — do not skip.

Self-check before submitting a sentence:

Read the sentence aloud. Ask: "Can a Junior QC restate this sentence in pure Vietnamese without pausing to mentally translate any English word?"

If the reader has to pause (e.g., "uh, 'retry' means 'thử lại'… 'blocker' means 'cái chặn'… 'validation' means 'kiểm chứng'…"), then that English word should have been written in Vietnamese from the start.

Decision procedure when uncertain about a specific word:

Is it the name of a concrete thing in the codebase, product, or smart contract layer? → Yes = Category 1 or 2. Keep English.
Is it an acronym or industry term where translating it to Vietnamese would lose meaning or produce something so long that even the QC Lead would not use it? → Yes = Category 3. Keep English and add a glossary row.
Otherwise — is this just a casual shorthand from Dev/PM speech, where translating to Vietnamese loses no meaning? → Not in any of the three categories. Translate to Vietnamese.
Illustrative examples (these are illustrations of the principle, not a closed list — apply the self-check to every word):

❌ "test design vẫn bị block" → ✅ "việc thiết kế test vẫn bị chặn" (block is casual shorthand, not a proper noun or identifier — translate)
❌ "reward engine validation" → ✅ "kiểm chứng bộ máy tính reward" (reward is in glossary → keep; validation/engine are generic → translate)
❌ "go-live ngày 2026-06-02" → ✅ "đưa vào vận hành ngày 2026-06-02"
❌ "2 line delivery song song" → ✅ "2 luồng triển khai song song"
✅ "Hyperliquid testnet" — Hyperliquid is Category 2 (platform name); testnet is Category 3 (blockchain term — must have glossary row)
✅ "kích hoạt setBotWlMaster() qua Relayer" — setBotWlMaster() is Category 1 (function), Relayer is Category 2 (component proper noun); "trigger" was generic English → translated to "kích hoạt"

---

## §3. Code-reference reporting rules (audit-style prose only)

### §3.A — Common rules (EN + VI)

#### Rule 3A1 — Do not use source labels as explanations

Source labels and anchors are evidence, not explanation.
Examples of source labels:

- `4x`
- `5x`
- `UC §3`
- `FRD §6`
- `prototype note`
- `file.jsx:line`

Convert them into clear business meaning before adding the reference.

#### Rule 3A2 — Explain first, put codes in parentheses

When a sentence references codes or anchors, write the meaning first, then put the code at the end as trace evidence.
Do not write a finding that is only a list of references.

Do not write:

> `FOQ-ORGUSER-005 (Q1 High)` is still open: bcrypt cost? argon2id? KMS provider?
> `FRD §6`, `BR-USER-001`, `Q3`

Write:

> The password-storage approach is not finalized: the requirement does not say whether to use bcrypt, argon2id, or scrypt, and it does not identify the KMS provider for encrypting audit logs at rest. (Reference: `FOQ-ORGUSER-005` in `FRD §10`; audit question `Q1`, priority High.)
> The user deactivation behavior is not test-ready because the expected result after disabling an account is not defined. (Reference: `BR-USER-001` in `FRD §6`; audit question `Q3`.)

#### Rule 3A3 — Make table prose cells readable

For table cells that summarize a finding, question, issue, recommendation, or impact, use this pattern:

`clear issue + short business/test impact + (Reference: ...)`

Code-only columns such as `ID`, `Ref`, `Code`, or `Source` may remain code-only. Prose columns must be self-contained.

#### Rule 3A4 — Include a code glossary in full reports
For full audit, scenario, or context reports, include a code glossary near the top if the report uses codes or code prefixes.

Only list prefixes or terms that actually appear in the report.

English heading: ## Reference code glossary
Vietnamese heading: ## Bảng mã viết tắt
Recommended columns:
| Code / Prefix | Meaning + role in this project | Defined in |
The "Meaning + role in this project" column must contain two parts, separated by an em-dash or period:

- Expansion / literal translation of the acronym or term.
- Short description of how the term is used in this specific project (≥ 1 sentence). This is the part that lets a downstream reader understand the term's function, not just its expansion.

Do not write a glossary row that only expands the acronym — that defeats the purpose. A reader who only sees MLM | Multi-Level Marketing still does not know what role MLM plays in this codebase.

Do not write:
| Code / Prefix | Meaning	Defined in |
|MLM	| Multi-Level Marketing	|(industry term)|
|LP	| Liquidity Provider	|(industry term)|
Write:

| Code / Prefix | Meaning + role in this project | Defined in |
| MLM | Multi-Level Marketing — referral-based commission model. In this project, MLM is used to distribute referral rewards from the MLM pool across an upline tree (V1–V7 titles) using the title-differential method. | (industry term) |
| LP | Liquidity Provider — a user-supplied Uniswap V3 position. In this project, every LP position is wrapped as a bot (managed by Router/LPBot contracts); raw uncollected LP fees are NEVER surfaced to end users — only post-allocation amounts are shown. | (industry term) |

#### Rule 3A5 — Explain technical terms on first use

Explain technical or domain terms the first time they appear in a report.

Examples:

- WCAG levels
- KDF algorithms
- regex syntax
- HTML attributes
- authentication methods
- authorization models
- encryption and key-management terms
- audit logging terms

After the first explanation, the shorter term can be used.

### §3.B — Vietnamese rules (qc-uc-read output only)

Apply this sub-section only when the requested output language is **Vietnamese** AND the artifact falls within §3 scope.

#### Rule 3B1 — Explanation of technical terms in Vietnamese

Do not write:

> Q10: chưa chốt WCAG 2.1 AA hay AAA.

Write:

> Mức độ tuân thủ tiêu chuẩn tiếp cận web (WCAG — Web Content Accessibility Guidelines) chưa được chốt: tài liệu chưa nói hệ thống cần đạt mức AA, là mức phổ biến cho phần mềm doanh nghiệp, hay mức AAA, là mức cao hơn và thường có nhiều ràng buộc hơn về tương phản, ngôn ngữ, và điều hướng. (Mã tham chiếu: câu hỏi `Q10`.)

#### Rule 3B2 — Write the meaning first, then the reference code

Do not begin a sentence with a code unless it is a code-only column.
Do not use quotations, source code, or links in place of explanations.

Do not write:

> `FOQ-ORGUSER-005 (Q1 High)` còn open: bcrypt cost? argon2id? scrypt? KMS provider?

Write:

> Thuật toán băm mật khẩu khi lưu vào cơ sở dữ liệu chưa được chốt: tài liệu chưa nói dùng bcrypt với cost factor bao nhiêu, argon2id, hay scrypt; nhà cung cấp KMS dùng để mã hoá audit log lúc nghỉ cũng chưa được xác định. (Mã tham chiếu: `FOQ-ORGUSER-005` trong `FRD §10`; câu hỏi audit `Q1`, priority High.)
