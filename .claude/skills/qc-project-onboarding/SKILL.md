---
name: qc-project-onboarding
description: Project onboarding skill for the QC Lead. MUST be the very first skill executed when applying the QC Kit to a new project. Validates and populates the two configuration files (project-config.md in docs/qc-lead/ and path-registry.md in .claude/config/), then auto-triggers qc-context-master to generate project-context-master.md and bootstrap qc-dashboard.md if all inputs are ready. Trigger ONLY when the user explicitly invokes this skill (e.g., /qc-project-onboarding).
---

# QC Project Onboarding Skill

## Trigger Conditions 

- Run ONLY when the user explicitly invokes the skill (e.g., `/qc-project-onboarding`).
- Do NOT auto-trigger on natural-language phrases — onboarding is a deliberate action by the QC Lead.

## Inputs

| Input | Source |
|---|---|
| Existing `project-config.md` | `docs/qc-lead/project-config.md` (resolved via `project-config` logical-name) |
| Existing `path-registry.md` | `.claude/config/path-registry.md` |
| User answers during interview | Interactive |

## Outputs

| Output  | Versioning |
|---|---|
| `project-config.md` | In-place. Header `Version` bumps `v1 → v2 → v3 …` ONLY if content actually changed. |
| `path-registry.md` | `.claude/config/path-registry.md` | In-place. Bumps version if a header version field exists; else just updates content. |

> **Versioning exception:** both files have fixed paths because every downstream skill references them. Filename and path do NOT change; only the `Version` header field is bumped.

> **Indirect outputs (via auto-trigger):** when pre-flight passes, this skill invokes `qc-context-master` which produces `project-context-master.md` and `qc-dashboard.md`. This skill itself NEVER writes those two artifacts directly.

## Workflow

### Phase 0 — Silent Audit (NO user-facing output)

Run silently — do NOT print any audit table or analysis.

1. Read both meta-config files. Treat as missing-content if a section uses placeholder tokens (`[Insert ...]`, `[Cung cấp ...]`, template URLs `https://[company]....`, `docs/???`, etc.).
2. Determine `mode`:
   - **First-time mode** — BOTH files entirely empty/placeholder.
   - **Update mode** — at least one file has real content.
3. Proceed directly to Phase 1.

### Phase 1 — Greeting + Step 1: project-config.md

Output exactly ONE of the two greeting blocks below (verbatim, hard-coded — do NOT paraphrase), then immediately show the current content of `project-config.md` and ask for input.

#### Greeting A — First-time mode

```
👋 Chào bạn! Tôi là skill `qc-project-onboarding` — bước đầu tiên khi áp dụng QC Kit cho một dự án mới.

Tôi nhận thấy đây là **lần đầu** bạn chạy onboarding cho dự án này (`project-config.md` và `path-registry.md` chưa có dữ liệu thực).

Quy trình gồm **2 bước cấu hình** + tự động tổng hợp tri thức dự án:

1. **Bước 1 — `project-config.md`:** thông tin tổng quan dự án (6 mục, mục 1–2 bắt buộc).
2. **Bước 2 — `path-registry.md`:** đường dẫn thật cho từng loại artifact.
3. **Tự động:** sau khi xong Bước 2, nếu common files đã sẵn sàng, tôi sẽ tự gọi `qc-context-master` để tạo `project-context-master.md` và `qc-dashboard.md`.

Bắt đầu **Bước 1** ngay dưới đây 👇
```

#### Greeting B — Update mode

```
👋 Chào bạn! Tôi là skill `qc-project-onboarding`.

Tôi thấy ít nhất 1 trong 2 file cấu hình đã có nội dung — bạn đang muốn **cập nhật**.

Quy trình:

1. **Bước 1 — `project-config.md`:** rà soát + cập nhật.
2. **Bước 2 — `path-registry.md`:** rà soát + cập nhật.
3. **Tự động:** sau khi xong Bước 2, nếu common files sẵn sàng, tôi sẽ tự gọi `qc-context-master` để đồng bộ `project-context-master.md` và `qc-dashboard.md`.

Bắt đầu **Bước 1** ngay dưới đây 👇

> 💡 Lưu ý: nếu bạn chỉ muốn update `project-context-master.md` hoặc `qc-dashboard.md` mà KHÔNG cần đụng meta-config, hãy gọi trực tiếp `/qc-context-master`.
```

#### After greeting — show project-config.md content

Display the current content of `project-config.md` as a single block, broken down by all 6 sections. Format:

```
📄 **Nội dung hiện tại của `project-config.md`:**

**Header**
| Project | <giá trị hiện tại> |
| Created | <giá trị hiện tại> |
| Author  | <giá trị hiện tại> |
| Version | <giá trị hiện tại> |

**Mục 1 — Project Overview** ✅ Bắt buộc
- Description: <giá trị hiện tại hoặc "(chưa có)">
- Domain: <giá trị hiện tại hoặc "(chưa có)">
- Target Audience: <giá trị hiện tại hoặc "(chưa có)">

**Mục 2 — Associated Links & Resources** ⚠️ Khuyến nghị
<bảng hiện tại hoặc "(chưa có — vẫn dùng template)">

**Mục 3 — Environments** ⚠️ Khuyến nghị
<bảng hiện tại hoặc "(chưa có — vẫn dùng template)">

**Mục 4 — Accounts & Credentials Structure** ⚠️ Khuyến nghị
<bảng hiện tại hoặc "(chưa có — vẫn dùng template)">
> Lưu ý: chỉ cung cấp tài khoản TEST. KHÔNG nhập tài khoản production.

**Mục 5 — Third-Party Integrations / APIs** ⚠️ Khuyến nghị
<nội dung hiện tại hoặc "(chưa có)">
```

Then ask the user (verbatim — hard-coded):

```
👉 Bạn muốn **cập nhật** mục nào? Vui lòng trả lời cho TẤT CẢ 6 mục theo định dạng:
- Mục 1: <nội dung mới> hoặc "giữ nguyên"
- Mục 2: <nội dung mới> hoặc "giữ nguyên" hoặc "bỏ qua"
- Mục 3: <nội dung mới> hoặc "giữ nguyên" hoặc "bỏ qua"
- Mục 4: <nội dung mới> hoặc "giữ nguyên" hoặc "bỏ qua"
- Mục 5: <nội dung mới> hoặc "giữ nguyên" hoặc "bỏ qua"

⚠️ Mục 1 là **bắt buộc** — không được "bỏ qua". Nếu chưa có dữ liệu cho 2 mục này, các skill khác sẽ KHÔNG chạy được.
```

**Refusal handling for Step 1:** If after this prompt the user still leaves Section 1 or 2 unfilled, stop the skill and output:
> "⚠️ Mục 1 và 2 của `project-config.md` là bắt buộc. Khi nào có thông tin, vui lòng chạy lại `qc-project-onboarding`. Tôi sẽ KHÔNG ghi gì vào file lần này."

### Phase 2 — Step 2: path-registry.md

After the user finishes Step 1, immediately proceed to Step 2. Show the current `## Artifact Path Table` content (full table, every row — do NOT skip).

Output exactly:

```
✅ Đã ghi nhận thông tin Bước 1.

📄 **Bước 2 — Nội dung hiện tại của `path-registry.md` (`## Artifact Path Table`):**

| Logical Name | Path hiện tại | Mô tả hiện tại | Trạng thái |
|---|---|---|---|
| <row 1>      | <path>        | <mô tả>        | ✅ Configured / ⚠️ Unconfigured |
| ...          |               |                | |

📌 **Hướng dẫn cung cấp path:**
- Mỗi `Path` là **đường dẫn folder thật** trên ổ đĩa.
- Giữ nguyên gốc `docs/` để đảm bảo tương thích với các skill khác.
- `Chỉ` update path, không thay đổi logical name vì nó đã được mention ở các skills và workflows.

👉 Bạn muốn **cập nhật** dòng nào? Vui lòng trả lời cho TẤT CẢ các dòng theo định dạng:
- `<logical-name>`: Path = `<path mới>` | Mô tả = `<mô tả mới>` — hoặc "giữ nguyên"
```

**Required logical names for auto-trigger to succeed:** `High-level-files`, `qc-dashboard`, `project-context-master`, `requirement-common-files`. Onboarding ensures these rows exist in the table; if any is missing, append it during this step (ask user for path).

**Refusal handling for Step 2:** If a row stays at `docs/???` (Unconfigured) and user picks "giữ nguyên", warn once:
> "⚠️ Artifact `<logical-name>` vẫn chưa có path thật. Skill nào cần đọc/ghi artifact này sẽ dừng lại và hỏi bạn sau. Bạn có chắc muốn để vậy? (yes/no)"

### Phase 3 — Write Back & Version Bumps

1. Apply Step 1 user answers to `project-config.md`. Bump `Version` IF anything actually changed. On first-time mode (header was placeholder), also fill `Created` (today, `YYYY-MM-DD`) and `Author` (from `userEmail` context if known, else ask).
2. Apply Step 2 user answers to `path-registry.md`. Bump version IF anything changed.

### Phase 4 — Pre-flight Check + Auto-trigger qc-context-master

1. Resolve `High-level-files` logical name from path-registry. Pass conditions:
   - Logical name exists in `## Artifact Path Table`.
   - Path is concrete (no `docs/???`).
   - Folder exists on disk.
   - Folder contains at least 1 file.

2. **Pre-flight PASS:**
   Output exactly:
   ```
   ✅ Bước 1 & 2 hoàn tất.
   - `project-config.md`: <new version> — đã update: <list> | giữ nguyên: <list>
   - `path-registry.md`: đã update: <list logical-names> | giữ nguyên: <list>

   ➡️ high-level files đã sẵn sàng tại `<High-level-files path>`. Tôi sẽ tự động gọi `qc-context-master` để tạo `project-context-master.md` và cập nhật `qc-dashboard.md`...
   ```
   Then **invoke `qc-context-master` skill via the Skill tool**. Do NOT ask the user — this is the documented kit flow.

3. **Pre-flight FAIL:**
   Output:
   ```
   ✅ Bước 1 & 2 hoàn tất.
   - `project-config.md`: <new version> — đã update: <list> | giữ nguyên: <list>
   - `path-registry.md`: đã update: <list logical-names> | giữ nguyên: <list>

   ⚠️ Tôi CHƯA thể tự động gọi `qc-context-master` vì:
   <reason — e.g., "High-level-files chưa cấu hình", "folder <path> chưa tồn tại", "folder rỗng">

   📋 **Bước tiếp theo:** chuẩn bị các tài liệu sau (WBS, Product Brief, System Architecture Diagram, Tech Stack, ...) tại `<resolved path>`, sau đó gọi `/qc-context-master` để hoàn tất tổng hợp tri thức dự án.
   ```
   Then STOP. Do NOT invoke qc-context-master.

## Usage Guideline (TBD)

> _Placeholder — kit owner will provide the full guideline content._

## Boundaries

- This skill ONLY edits `docs/qc-lead/project-config.md` and `.claude/config/path-registry.md`. It MUST NOT directly create or edit `project-context-master.md`, `qc-dashboard.md`, or any other artifact — those belong to `qc-context-master`.
- It MUST NOT invent project information. If user does not provide a value, leave the placeholder untouched.
- For Section 5 of `project-config.md` (test account credentials), the skill MAY collect passwords (test-only). It MUST refuse to record any credential the user identifies as production.
- Auto-trigger of `qc-context-master` happens ONLY when pre-flight passes; otherwise the skill instructs the user to run it manually.
- Output language follows source-input language per `global-rules.md`. SKILL.md itself is in English.
