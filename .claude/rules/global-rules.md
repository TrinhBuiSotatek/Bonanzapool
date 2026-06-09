# Global Rules

## Common
- SKIP all other knowledge, histories that not stored in this project.

## Language & Communication
- Communication language: Vietnamese is the default language for all exchanges, reports, and explanations.
- All outputs of any "skill" MUST be determined by the source input language according to the following logic:
    - IF Input Language is Vietnamese THEN Output Language is Vietnamese.
    - IF Input Language is Any other language THEN Output Language is English.
- All skill.md files MUST be written in English.
- All labels/messages MUST be kept in their original language (e.g., Korean, Japanese, Chinese, etc.) and annotated with the English translation in parentheses, except when they are written in Vietnamese.
- All requirement documents, input materials, and output deliverables are in Vietnamese. MUST read and understand them accurately, write in grammatically correct Vietnamese, and preserve the clarity, naturalness, and integrity of the Vietnamese language.

## File & Naming Standards

- All output files MUST follow the naming convention defined in `rules/naming-convention.md`.
- NEVER overwrite a file. Create a new version instead (`v1`, `v2`, etc.).
- All files MUST include a header with: document title, date created, author/agent name, and version.
- Read the path-registry.md to find the path of the Input/Output files.

## Output Quality Standards

- Every output MUST be **evidence-based** — cite sources, reference specific sections of requirements.
- NEVER fabricate data, make up statistics, or assume requirements that are not documented.
- When uncertain, MUST explicitly state the uncertainty and ask the user for clarification.

## Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity First
Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Security & Privacy
- Data Security: NEVER share sensitive data (PII, passwords, proprietary code) with public models.
- NEVER store passwords or sensitive credentials in any output file.

## Agent Work Log

- Every skill MUST log to its device's JSONL file under `worklog-per-device` (resolve path via `path-registry.md`). If the file does not exist yet, create it. Schema and lifecycle: see the README at the same folder (`docs/qc-lead/agent-work-log.local/README.md`). Do NOT write directly to the master `agent-work-log` — that is owned exclusively by `qc-get-work-log`.