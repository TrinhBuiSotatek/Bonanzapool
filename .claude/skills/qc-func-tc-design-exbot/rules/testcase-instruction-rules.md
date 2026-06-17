## Testcase Instruction Rules (English output only)

### Output Language (READ FIRST)

This skill is **English-only**. All test cases — TC ID, Title, Pre-conditions, Steps,
Expected Result, Priority — and every generated report MUST be written in **English**.
Do NOT produce Vietnamese test cases and do NOT mix languages within an output file.
Keep technical identifiers, function names, endpoint paths, state names, message codes,
and on-chain addresses verbatim.

---

### Encoding & Converter (MANDATORY)

**Rule 1 — Use the shared converter; do NOT write a new script.** xlsx generation is
performed by `qc-func-tc-design-exbot/scripts/md_to_xlsx.py`, invoked exclusively from
`workflows/convert-md-to-xlsx.md` (auto-triggered by the skill — see `SKILL.md` →
"Skill Execution Steps"). The agent invokes this script and does NOT write its own
openpyxl populator. The script is UTF-8, opens md with `encoding='utf-8'`, writes
Unicode literals, and self-verifies before exit. If you must extend the script,
preserve these properties — never add `# -*- coding: cp1252 -*-`, never transliterate.

**Rule 2 — Self-verification before delivery.** After generating the xlsx, open it and
spot-check at least 3 rows. If any cell shows `?` boxes, mojibake (e.g., `Ä\x90`, `Ã©`),
or any character that does not match the source — STOP, debug the script, regenerate.
Do NOT deliver a corrupted output.

### Sheet Layout & Section Headers (MANDATORY)

**Columns** (matches the template `Test cases` sheet, row 1 — pin by column letter; the project uses one fixed template):

`A=ID_TC | B=Test Title/Summary of test cases | C=Pre-conditions | D=Step | E=Expected Result | F=Priority`

**Within the FUNC section, sort by logical flow:** Happy path → input / contract validation → core logic & decision tables → error / exception cases.

**Within the INTG (Integration & State) section, sort:** cross-service / queue / external-API calls → reconciliation (expected vs actual) → idempotency / concurrency / state-transition cases.

**Within the NFR (Non-functional, logic-accessible) section, sort:** security → reliability / resilience → performance / throughput → auditability / logging.

**Hierarchy (use Roman numerals I, II, III… — one per function / operation under test):**

| Header level | Pattern | Where it appears |
|---|---|---|
| Operation | `<RomanNumeral>. Operation: <operation name>` | One row per function / operation |
| FUNC section | `<RomanNumeral>.1. Functional verification — Operation: <operation name>` | Immediately below the operation header |
| INTG section | `<RomanNumeral>.2. Integration & State verification — Operation: <operation name>` | After all FUNC test cases for that operation |
| NFR section | `<RomanNumeral>.3. Non-functional (logic) verification — Operation: <operation name>` | After all INTG test cases for that operation |

> The `.3.` NFR section is optional — omit it for an operation that has no logic-accessible non-functional cases. Whenever it is present, it follows the `### <Roman>.3.` heading so the converter inserts a header row for it.

**Header row format:**
- Header text goes in column **B** (`Test Title/Summary of test cases`).
- All other columns on the header row stay empty (no TC ID, no Pre-condition, no Step, no Expected Result, no Priority).
- Header rows are NOT counted as test cases — they do not consume TC ID numbers and they are not subject to the `TC_XXX` rule.
- The operation name in the header MUST match the function / operation name used in the audited UC review report. Do NOT paraphrase or translate.

**Example 1 — Single-operation UC:**

```
I. Operation: Bot start (preflight)
I.1. Functional verification — Operation: Bot start (preflight)
TC_001 | FUNC | Verify preflight blocks start when HL margin is insufficient | …
TC_002 | FUNC | Verify one-bot policy rejects a second bot                  | …
…
I.2. Integration & State verification — Operation: Bot start (preflight)
TC_010 | INTG | Verify the idle→preflight→...→active transition sequence  | …
…
I.3. Non-functional (logic) verification — Operation: Bot start (preflight)
TC_020 | NFR  | Verify the agent key is never written to logs on decrypt   | …
```

**Example 2 — Multi-operation UC (3 operations):**

```
I. Operation: Bot start (preflight)
  I.1. … FUNC cases
  I.2. … INTG/State cases
  I.3. … NFR-logic cases
II. Operation: Hedge-sync (delta-only)
  II.1. … FUNC cases
  II.2. … INTG/State cases
  II.3. … NFR-logic cases
III. Operation: Close bot (user_redeem)
  III.1. … FUNC cases
  III.2. … INTG/State cases
  III.3. … NFR-logic cases
```

### Test Case Writing rules

**Rule 1 — DATA HANDLING CONSTRAINT**
- Do NOT hardcode specific environment values such as system paths, wallet addresses, private keys, account names, or concrete production data into any part of the test case.
- ALWAYS use a generic name, operation / field name, state name, or logical placeholder. When a value matters, describe its boundary or category, not a fixed literal.
- When test data requires clarification, provide a short description or example enclosed in parentheses () immediately following the object name.
- NEVER place a concrete amount, balance, price, count, or threshold inside the Pre-condition / Step / Expected Result sentence. Describe the boundary or category in plain words (e.g. "below the required margin", "exactly at the buffer threshold", "one unit below the limit"). If a concrete number helps the reader picture the case, put it ONLY in an `(Example: …)` note at the END of the cell — see Rule 6. The case MUST still be executable without that example.

Examples:
Correct: Deposit ETH to the HL wallet with the deposit amount ≥ the minimum deposit amount (the amount sits exactly at the boundary threshold).
Correct: Submit a hedge-sync message whose stateVersion is lower than the current `bot_runtime_state.state_version` (a stale message).
Correct: Open the short with a delta computed from `targetShortEth − actualShortEth` (a positive delta at the drift threshold boundary).
Incorrect: Deposit exactly 0.5 ETH into wallet 0xA5B8…C969.
Incorrect: Set `stateVersion = 7` and `botId = "bot_abc123"`.
Incorrect: Call `https://api.hyperliquid.testnet/exchange` with key `0xdeadbeef…`.

**Rule 2 — Logic Notation Standard.** There are NO UI objects. Use these notations to keep logic artifacts unambiguous:

- `` `backticks` ``: Use for technical identifiers — function / method names, endpoint paths, queue names, table / column names, state-machine state names, event names, ID codes, environment variables (e.g. `placeReduceOnlyStopMarket()`, `/api/exbot/start`, `hedge-sync` queue, `bots.lifecycle_state`, `safe_mode`, `VaultMinted`, `E-EXBOT-002`).
- `"Double Quotes"`: Use only for the human-readable text of a returned message / error string when quoting it verbatim (e.g. "You already have an active ExBot.").
- Describe each action by the operation it performs and the condition to verify — never by a button, field, or screen.

Examples:
- Send a `hedge-sync` message with a `stateVersion` lower than the current `bot_runtime_state` value.
- Call `BnzaExVault.redeem(tokenId)` on-chain to redeem the LP.

**Rule 3 — Content Logic.**

- The content of all parts MUST refer to operations, inputs, states, and effects by their logical / technical names (the names used in the audited documentation), in `backticks` for identifiers. There are NO UI objects to name.
- The Test title MUST begin with a verification verb (e.g. Verify, Confirm, Check, Ensure that).
- The Test title MUST follow this pattern: `Verification verb + operation/function/flow + state/condition + context (if any)`. Examples: Verify preflight blocks the start when HL margin is insufficient; Verify hedge-sync computes the correct delta at the drift threshold; Verify the `hedge_pre_open`→`safe_mode` transition when the HL order fails; Verify redelivery of the same `message_id` produces no double effect.
- Keep the Test title SHORT and readable: name the operation/object and the situation in plain words. Do NOT stack several identifiers/values in the title — keep at most one key identifier (e.g. an error code or a state) and move the rest to the body. The title must answer "what is being checked, and in what situation" at a glance.
- The Test case ID always strictly adheres to the format `TC_[XXX]` — XXX is an incremental 3-digit number. Example: `TC_001`, `TC_002`.
- The Pre-conditions MUST be written in present simple, following this pattern: System/Subject + is/are + State + Context (if any). Examples: The bot is in `active` state with an open hedge leg; The circuit breaker state (`circuit_breakers.state`) is `open`; The user's agent key is `approved` and not expired.
- The Pre-conditions MUST be a single condition per row.
- The Test steps must be a single action + condition, following this pattern: `Imperative verb + data / boundary description (if any) + operation or target` — NO UI object. Examples: Deposit ETH to the HL wallet with the deposit amount ≥ the minimum deposit amount; Re-deliver the same `hedge-sync` message a second time with the same `idempotencyKey`; Set `markPrice` above `stop_price`.
- The Expected result MUST begin with a step number and explicitly describe the observable system effect.

**Expected Result (Logic Verification):**
- MUST begin with a step number (e.g., `1. <expected result>`).
- Do NOT write generic statements such as "works as expected".
- Must explicitly describe the observable system effect: API / RPC response (status + payload), state-machine transition (the `lifecycle_state` / circuit / margin value before → after), DB row or column value, on-chain state / balance, emitted event, or returned message / error code (e.g. `E-EXBOT-002`).
- For an on-chain operation, state BOTH the on-chain effect AND the off-chain (DB / ledger / backend) effect.
- Do NOT write a visual / layout / screen assertion — this skill produces NO UI test cases.

### Readability rules — write for a junior QC (MANDATORY)

> Goal: a junior QC must understand every cell at a glance, WITHOUT a dictionary/translator and WITHOUT mentally parsing variables. These rules apply to the Title, Pre-condition, Step, and Expected Result.

**Rule 4 — Meaning first, identifiers in parentheses.**
Lead every sentence with the plain-language meaning. Put the technical identifier / status / field / value in parentheses as supporting evidence — never let the identifier BE the sentence.

Pattern: `<plain-language meaning> (<identifier / status / field = value, as evidence>)`

| ❌ Identifier-first (hard to read) | ✅ Meaning-first (identifier in parentheses) |
|---|---|
| "The user has no ExBot whose `status` is one of `active`, `paused`, `closing`, `safe_mode`, `error`." | "The user has no running ExBot (status is not one of `active`, `paused`, `closing`, `safe_mode`, `error`)." |
| "The user's HL agent key has `approval_status='approved'` and `expires_at` is in the future." | "The user's HL agent key is approved and not expired (`approval_status='approved'` and `expires_at` is in the future)." |
| "`circuit_breakers.state` is `open`." | "The circuit breaker is open (`circuit_breakers.state='open'`)." |

**Rule 5 — Plain, common QA vocabulary.**
Use simple words a tester uses every day: check / make sure / reject / block / allow / succeed / fail / retry / duplicate / missing / not enough / on time / roll back. Do NOT use academic or rare words that force the reader to a translator. If a domain term is unavoidable, gloss it once in parentheses.

Avoid words like: "shortfall", "mediated", "granular", "idempotent" (without a gloss), "accurate to the nearest dollar", "deterministic" (without a gloss).

| ❌ Hard / academic | ✅ Plain |
|---|---|
| "Verify the `E-EXBOT-002` shortfall amount is accurate to the nearest dollar." | "Verify the suggested top-up amount is not rounded down when the user's balance is below the required margin." |
| "Verify the marginSummary fetch is mediated by `HLRateLimitDO`." | "Make sure the margin check asks `HLRateLimitDO` for permission before calling Hyperliquid, and waits when it is told to wait." |

**Rule 6 — No concrete numbers in the case body; put them in an `(Example: …)` note.**
Keep the Pre-condition / Step / Expected Result value-free — describe the boundary or category in words. Place any concrete number ONLY in an `(Example: …)` note at the end of the relevant cell, purely to help the reader picture the case. The case must remain executable if the example is removed.

| ❌ Numbers baked into the body | ✅ Words in the body, numbers in the Example note |
|---|---|
| Pre-condition: "The user's HL margin is `$300`; required margin (2.0x buffer) is `$700`." | Pre-condition: "The user's HL margin is below the required margin including the 2.0x buffer. (Example: balance ≈ 300, required ≈ 700.)" |
| Expected: "…the message reads \"…Please deposit $400 to HL.\"" | Expected: "1. The start is blocked (`E-EXBOT-002`, HTTP 400) and the message shows the exact amount the user still needs to deposit. (Example: required 700, current 300 → message asks to deposit 400.)" |

### Test cases example reference

Read `qc-func-tc-design-exbot/references/Testcase-refer-en.md` and align new/updated TCs
to the same structural & writing style (TC ID format, Title phrasing, Pre-condition /
Step / Expected Result layout, multi-line bullet style).
