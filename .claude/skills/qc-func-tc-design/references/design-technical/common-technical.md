# Common Technical Guideline for Test Case Design

## Purpose

This guideline defines the common technical checklist for designing test cases across all product platform types.

Use this file as the baseline checklist for every screen, feature, workflow, or user story before applying platform-specific add-ons such as Web, Mobile, or Desktop.

## How to use

For each screen or feature:

1. Identify the product platform type.
2. Apply all 6 common phases in this file.
3. Add the relevant platform-specific guideline:
   - `web-technical.md`
   - `mobile-technical.md`
   - `desktop-technical.md`
4. Check whether this feature is blockchain-dependent (see the trigger gate in the
    "Blockchain (Chain + Wallet) Add-on" section below). If YES, apply that add-on
    ON TOP OF the 6 common phases and the platform file. If NO, skip it entirely —
    do not generate wallet/chain cases for non-blockchain features.
5. Add business rules, role/permission matrix, data matrix, browser/device/OS matrix as needed.
6. Convert the checklist into concrete test cases with clear preconditions, steps, and expected results.

## Recommended test case fields

| Field | Description |
|---|---|
| Test Case ID | Unique ID, follow Rule 2 — Content Logic - `testcase-instruction-rules` |
| Platform Type | `web-static`, `web-responsive`, `mobile-native`, `mobile-hybrid`, `desktop-native` |
| Phase | Phase 1 to Phase 6 |
| Feature / Screen | Screen, module, or workflow under test |
| Test Objective | What the test case validates |
| Preconditions | Describe required User role/state, system/page state, test data/environment requirement |
| Test Data | Inputs, files, accounts, API mocks, boundary values |
| Steps | Clear execution steps |
| Expected Result | Observable and measurable expected behavior |
| Matrix | Browser, device, OS, breakpoint, permission, network condition |
| Priority | P0 / P1 / P2 |
| Test Type | Functional, UI, Integration, Security, Performance, Accessibility |
| Notes | Assumptions, constraints, out-of-scope items |

---

# 6-Phase Common Test Design Framework

## Phase 1: Initialization and Static States

Validate the screen or app state before the main user interaction starts.

### Empty state

Cover cases where no data is available.

- Empty grid, list, card, chart, table, report, or dashboard.
- Placeholder text or illustration is displayed correctly.
- Message is friendly and localized, for example `No Data`, `Không có dữ liệu`, or `Chưa có dữ liệu`.
- Primary CTA is displayed if the user is allowed to create data.
- CTA is hidden or disabled if the user has no permission.
- Layout does not collapse when there is no data.

### Populated state

Cover the default state when data exists.

- Default sort is correct.
- Default filter is correct.
- Default page size or item count is correct.
- Default selected tab, menu, segment, or category is correct.
- Default column order, visibility, and width are correct if applicable.
- Badge, count, status, and summary values are accurate.
- Component enabled/disabled state matches data and permission.

### Loading state

Cover loading and pending states.

- Skeleton, shimmer, spinner, overlay, or progress indicator is displayed.
- User does not see a blank screen or white-screen flash.
- Long-running jobs show progress if the design requires it.
- User cannot trigger duplicate actions while the request is pending.
- Loading state is cleared after success, failure, or cancellation.

### Error state

Cover recoverable and unrecoverable errors.

- 4xx error.
- 5xx error.
- Network timeout.
- Offline state.
- Permission or access denied.
- Malformed or partial server response.
- Error message is user-friendly and localized.
- Retry CTA is available when recovery is possible.
- The user is not navigated away unexpectedly on transient errors.
- Existing data is not lost unless explicitly expected.

### Permission-denied state

Apply when a feature depends on permission or access rights.

- User lacks business permission.
- User lacks OS permission.
- Permission is denied for the first time.
- Permission is permanently denied.
- Permission is revoked while the app is running.
- The system shows an explanation and a recovery action, such as `Open Settings`, `Request Access`, or `Contact Admin`.

---

## Phase 2: Component States and Basic Interactions

Validate individual UI components without focusing on the core business outcome yet.

### Navigation and reset controls

- Close icon `X` closes the popup, modal, drawer, or panel.
- Cancel button exits without saving.
- Reset filter restores default filters.
- Back action returns to the previous state as specified.
- Dismiss actions do not accidentally submit data.

### Buttons

- Enabled state.
- Disabled state.
- Pressed or active state.
- Loading state after click or tap.
- Debounce prevents repeated submission.
- Button label matches the action.
- Button visibility follows role and permission.

### Text input and form fields

- Default value.
- Placeholder.
- Read-only state.
- Disabled state.
- Focus state.
- Clear action if available.
- Copy, paste, select-all if allowed.
- Max length behavior.
- Auto-formatting behavior if applicable.

### Dropdown, combobox, and multi-select

- Component opens correctly.
- Correct option list is displayed.
- Search-as-you-type works if supported.
- Long option list handles scrolling or virtualization.
- Single select and multi-select behavior is correct.
- Clear selection works if available.
- Disabled options cannot be selected.
- Selected value is displayed correctly after save, refresh, or reopen.

### Checkbox, radio, toggle

- Default state is correct.
- Checked and unchecked behavior is correct.
- Radio group allows only one selected value.
- Toggle state persists after save or navigation if required.
- Indeterminate state is handled if applicable.

### Date, time, and date-time picker

- Manual input works if supported.
- Picker selection works.
- Cancel does not change the value.
- Date format is correct.
- Min and max date are enforced.
- Invalid date is rejected.
- Timezone handling is correct if relevant.

### Modal, popup, drawer, bottom sheet, dialog

- Opens from the correct trigger.
- Displays correct title, content, and actions.
- Close, Cancel, Save, Confirm actions behave correctly.
- Dismiss by outside click/tap, Esc, swipe-down, or OS back follows spec.
- Backdrop, overlay, and focus trap behave correctly.
- Nested modal behavior is defined and works correctly.

### Keyboard interaction

- Tab order is logical and complete.
- Focus indicator is visible.
- Enter submits only where expected.
- Esc closes modal or cancels only where expected.
- Arrow keys work for lists, menus, trees, grids, or dropdowns if supported.
- Keyboard-only users can complete the workflow.

---

## Phase 3: Core Functional Testing

Validate the business logic and functional outcome of each feature.

### Happy path

- Standard successful workflow with valid input.
- Save, create, update, delete, submit, approve, reject, search, export, import, or process works as expected.
- Success message, toast, navigation, or list refresh appears correctly.

### Required validation

- Leave each mandatory field empty.
- Leave all mandatory fields empty.
- Clear prefilled mandatory values.
- Required message is displayed near the correct field.
- Submit is blocked when required data is missing.

### Format validation

Apply to fields such as:

- Email.
- Phone number.
- Date.
- Time.
- URL.
- Tax code.
- ID number.
- Postal code.
- File name.
- File extension.
- Custom business format.

### Range and length validation

- Minimum value.
- Maximum value.
- Less than minimum.
- Greater than maximum.
- Minimum length.
- Maximum length.
- Special handling for decimal, negative number, zero, and large number.

### Boundary Value Analysis

For every field with a defined boundary, include at least:

- Min - 1.
- Min.
- Min + 1 if relevant.
- Max - 1 if relevant.
- Max.
- Max + 1.

### Cross-field validation

Examples:

- End date must be greater than or equal to start date.
- Discount cannot exceed total amount.
- Confirm password must match password.
- Selected role must be compatible with selected department.
- Status transition must match the current workflow state.

### Decision table and business rule combinations

Use when behavior depends on multiple conditions.

Examples:

- Role x status x action.
- Customer type x product type x approval level.
- Payment method x currency x country.
- Permission x data ownership x workflow state.

### Exception and error handling

- Server validation error.
- Duplicate data.
- Conflict or optimistic locking error.
- API timeout.
- API returns 4xx or 5xx.
- API returns malformed or partial data.
- External dependency fails.
- User cancels a required external step.

### Duplicate action prevention

- Double click.
- Double tap.
- Press Enter multiple times.
- Refresh during submission.
- Back and resubmit.
- Retry after timeout.

Expected behavior must prevent duplicate records, duplicate payments, duplicate requests, or inconsistent workflow state.

### Bulk operation

Apply if the feature supports multiple records.

- Select one item.
- Select multiple items.
- Select all on current page.
- Select all across pages if supported.
- Bulk approve, reject, delete, export, assign, import, or process.
- Partial success is displayed clearly.
- Failed records include reason and recovery option.

---

## Phase 4: Functional Integration

Validate how functions work together across components, screens, or systems.

### In-screen integration

- Search + filter.
- Search + sort.
- Filter + pagination.
- Sort + pagination.
- Search + filter + sort + pagination.
- Create/update/delete refreshes list, count, summary, and badges.
- Master-detail panel updates when a row or card is selected.
- Form submission redirects or stays on page according to spec.

### Cross-screen integration

- Back navigation preserves search, filter, pagination, and scroll position if required.
- Direct link opens the correct record or screen.
- Related screens receive updated data after changes.
- Previous screen does not show stale data after update.
- Unsaved changes warning appears when navigating away.

### Multi-session or multi-window integration

- Same record opened in two tabs, windows, devices, or app instances.
- Concurrent edit is detected.
- Conflict strategy is clear: last-write-wins, merge, or warning.
- User sees a meaningful message when data has changed elsewhere.

### Auth and session integration

- Token expiry during a workflow.
- Silent token refresh.
- Forced logout after idle timeout.
- User is redirected to login when session is invalid.
- User returns to the intended destination after re-authentication if supported.

### Notification and routing integration

Apply if the platform supports notification or deep link.

- Notification opens the correct screen.
- Deep link opens the correct screen and state.
- Direct URL or route works on cold start and warm start if relevant.
- Permission and authentication are checked before routing.

---

## Phase 5: Non-Functional Testing

Validate quality attributes that affect security, reliability, performance, and usability.

### Security

- Sensitive data is masked.
- Password fields are not displayed in plain text by default.
- Input is sanitized against XSS and injection attacks.
- State-changing actions are protected against CSRF where applicable.
- Role-based access controls hide or disable restricted actions.
- Restricted APIs cannot be called through UI manipulation.
- Sensitive data is not stored in insecure storage.
- Sensitive data is not exposed in logs, error messages, URL, local storage, clipboard, or screenshots.

### Performance

Define measurable targets per project.

- Initial render time.
- Time to interactive.
- Search response time.
- Save/submit response time.
- Grid/list rendering time.
- Export/import processing time.
- Memory consumption.
- CPU usage.
- Long-session stability.

### Network resilience

- Offline before opening the feature.
- Offline during submission.
- Slow network.
- Timeout.
- Reconnect after offline.
- Retry behavior.
- Request cancellation.
- Duplicate prevention after retry.

### UX and loading behavior

- Spinner or skeleton appears during API calls.
- Button loading state appears during submission.
- User cannot submit duplicate requests.
- Optimistic UI reverts on failure if used.
- Success, warning, and error messages are visible and understandable.
- Empty, loading, and error states are visually distinct.

### Data persistence

- Form draft preservation if required.
- User preferences persist correctly.
- Filter and sort state persist correctly if required.
- Logout clears sensitive local data.
- Refresh or relaunch behavior follows spec.

### Auditability and logging

Apply if the system handles sensitive or regulated actions.

- Sensitive action creates audit log.
- Log includes actor, action, timestamp, target object, and result.
- Log does not include PII or secrets.
- Error log is useful for diagnosis.

---

## Phase 6: GUI, Visual, Localization, and Accessibility

Validate design-to-code quality and accessibility.

### Design alignment

Compare with Figma, mockup, or design specification.

- Position.
- Size.
- Color.
- Font family.
- Font size.
- Font weight.
- Line height.
- Spacing.
- Border radius.
- Icon.
- Shadow.
- Empty-state illustration.

### Visual state coverage

- Default.
- Hover if applicable.
- Focus.
- Pressed.
- Selected.
- Disabled.
- Loading.
- Error.
- Success.

### Localization

- Vietnamese diacritics render correctly.
- Long Vietnamese labels do not truncate critical information.
- Long-string languages do not break layout if multi-language support exists.
- Date, time, number, currency, and address formats are correct.
- Error messages are translated consistently.

### Accessibility basics

- Color contrast meets WCAG AA for text where applicable.
- Form fields have labels.
- Images have alt text if meaningful.
- Interactive controls are reachable by keyboard or platform assistive technology.
- Focus order is logical.
- Focus indicator is visible.
- Error messages are associated with the correct fields.
- Screen reader labels are meaningful.
- Motion is reduced if user setting requires it.

---
## Blockchain (Chain + Wallet) Add-on

### Trigger gate — apply this add-on ONLY when at least one is true

Apply this add-on to the feature under test if ANY of the following holds:

- the feature requires connecting or signing with a wallet (MetaMask,
  WalletConnect, Coinbase Wallet, Reown AppKit, etc.); OR
- the feature reads on-chain state (balance, allowance, token metadata, view calls); OR
- the feature sends a transaction or asks the user to sign a message; OR
- the feature displays data that must stay consistent with on-chain truth.

If NONE of these holds, SKIP this entire add-on. Do not invent wallet, gas, or
network test cases for a purely off-chain feature.

### How to apply (when triggered)

1. Keep applying the 6 common phases and the platform file as usual — this add-on
   does NOT replace them.
2. Add the 5 extra test case fields below (Wallet / Chain / Balance Precondition,
   On-chain Expected Result, Off-chain Expected Result) to every blockchain case.
3. Walk the four areas in order and generate cases for each that applies:
   A. Wallet Connection & Identity
   B. On-chain Transactions
   C. Network & Chain
   D. On-chain <-> Off-chain Consistency
   Plus the two cross-cutting sections (Security, Test environment & determinism).
4. Scope filter — generate a case only when the trigger for that sub-area is present:
   - No signing in this feature -> skip A3 (message signing).
   - Read-only feature (no tx) -> skip Area B, keep A/C/D as relevant.
   - Not a swap/LP/staking feature -> skip B4 (DeFi-specific).
5. Mandatory rule: every transaction case states BOTH the on-chain expected result
   AND the off-chain (UI/backend) expected result. UI-only assertions are incomplete.
6. Out of scope — do NOT generate: smart-contract unit/property tests, gas
   optimization, on-chain security audit, or key-management cryptography. Flag them
   as out-of-scope instead (owned by dev / audit).

### Extra test case fields for blockchain features

Add these to the standard fields. They keep preconditions and expected results
unambiguous for chain-dependent cases:

| Field | Description |
|---|---|
| Wallet Precondition | Wallet installed? connected? locked? which account? which provider? |
| Chain Precondition | Expected network (mainnet/testnet + chainId), wallet's current network |
| Balance Precondition | Native token (for gas) + relevant token balances |
| On-chain Expected Result | What MUST be true on-chain (tx status, event emitted, state change) |
| Off-chain Expected Result | What the UI / backend MUST show after the on-chain result |

> Rule: every transaction test case MUST state BOTH the on-chain expected result AND the off-chain (UI/backend) expected result. A case that only checks the UI toast is incomplete.

#### Area A — Wallet Connection & Identity

A1. Connect / disconnect

- No wallet extension/app installed -> install prompt or fallback is shown.
- Wallet installed but locked -> unlock prompt; flow resumes after unlock.
- User rejects the connection request -> graceful message, no broken state.
- Successful connect -> address shown (correctly truncated, e.g. 0xa5B8…C969),
  connected state persisted per spec.
- Multiple wallet providers available -> provider picker works for each option.
- WalletConnect via QR / deep link -> pairing, timeout, and cancel all handled.
- Auto-reconnect on page refresh / cold start follows spec (reconnect vs ask again).
- Manual disconnect -> session cleared, protected UI hidden, no stale address.

A2. Account & identity changes

- User switches account inside the wallet -> app detects `accountsChanged`,
  refreshes balances/permissions, or forces re-auth per spec.
- Connected account has zero native balance (cannot pay gas).
- Connected account is not whitelisted / not registered -> correct gating message.
- Multiple accounts: switching back and forth never mixes data between accounts.
- Wallet disconnected from the app side (in the wallet) while app is open.

A3. Message signing (authentication / SIWE)

- Sign-in message (e.g. SIWE) is human-readable and shows domain, address, nonce.
- User rejects the signature request -> no session created, clear feedback.
- Signature request times out / wallet popup closed -> recoverable, retry works.
- Replay/expired nonce -> rejected by backend.
- Signer address != connected address -> rejected.

A4. Mid-flow wallet events (CRITICAL, often missed)

- Account changed mid-transaction -> in-flight action is cancelled or re-validated.
- Network changed mid-flow -> app reacts (block action, prompt switch back).
- Wallet locked mid-flow -> next action prompts unlock, no silent failure.
- Wallet disconnected mid-flow -> protected screen handles loss of session.

#### Area B — On-chain Transactions

B1. Pre-flight checks

- Insufficient native token for gas -> action blocked with clear reason.
- Insufficient token balance for the requested amount.
- ERC-20 allowance required: approve step appears before the main action.
  - Exact-amount approval vs unlimited approval (per spec).
  - Re-approval needed when allowance < amount.
  - User rejects the approval -> main action does not proceed.
- Gas estimation failure (would-revert tx) -> surfaced BEFORE sending, not after.
- Amount precision: decimals handled correctly (wei <-> token units), no rounding
  loss; "Max" button leaves enough native token for gas where required.

B2. Transaction lifecycle (state-transition testing)

Treat the tx as a state machine and cover each transition:

    idle -> submitted -> pending -> confirmed
                       \-> failed / reverted
                       \-> dropped / replaced (speed-up / cancel from wallet)

- User rejects the transaction in the wallet -> return to idle cleanly.
- Submitted: pending UI shown, action button disabled, tx hash + explorer link
  (correct explorer for the active chain).
- Pending for a long time -> UI stays in pending, no false success/timeout.
- Confirmed after required N confirmations -> success state + data refresh.
- Reverted on-chain (e.g. require failed) -> UI shows failure, no optimistic
  success left dangling.
- Dropped / replaced (speed-up or cancel done in wallet) -> app reconciles.
- Reorg: a "confirmed" tx is rolled back -> state reverts correctly.

B3. Idempotency & duplicates

- Double-click / double-submit does NOT broadcast two transactions.
- Refresh during pending -> app recovers the pending tx (does not resend).
- Retry after timeout -> uses same nonce / does not create a duplicate.

B4. DeFi-specific (apply only if relevant: swap / LP / staking)

- Slippage tolerance respected; "price moved beyond slippage" path covered.
- Deadline passed -> tx rejected with clear message.
- Quote/price refresh between preview and confirm.

#### Area C — Network & Chain

- Wallet on the wrong network -> prompt to switch chain; switch accepted vs rejected.
- Target chain not yet added to wallet -> "add network" flow handled.
- Unsupported chain selected -> feature gated with clear message.
- Switch network mid-session -> balances, contracts, and explorer links update.
- Testnet vs mainnet guard -> environment-correct chainId; warning if mismatched.
- RPC endpoint down -> error + retry; RPC slow/timeout -> loading not infinite.
- RPC rate-limited -> backoff / fallback RPC behaves per spec.
- Block explorer URL is correct PER chain (not hard-coded to one network).
- Multi-chain: same address shows independent state per chain (no cross-bleed).

#### Area D — On-chain <-> Off-chain Consistency

The hardest defects in dApps live here: the UI/backend disagreeing with the chain.

- Indexer / subgraph lag: after a confirmed tx, UI may show stale data until
  indexed -> spec'd behavior (optimistic update, polling, or "syncing" hint).
- Optimistic UI then on-chain failure -> UI reverts to the true state.
- Backend-reported balance/price vs on-chain truth -> reconciliation rule defined;
  on-chain is the source of truth where the spec says so.
- Missed event (listener offline) -> manual refresh recovers the correct state.
- Cache invalidation after a confirmed tx -> stale cache not shown.
- Read-after-write: immediately re-reading state after a tx returns consistent data
  or a clearly-labelled pending state (never a silent wrong value).

#### Cross-cutting — Security (blockchain-specific, extends common Security phase)

- Private key / seed phrase is NEVER requested, stored, logged, or transmitted.
- The amount/contract/parameters shown to the user MATCH what is actually signed.
- Spender contract address in an approval is verified / displayed; warn on
  unlimited approvals.
- Phishing-resistant: signature/transaction requests show enough context to judge.
- Contract addresses are the expected, verified ones (no swapped address).

#### Cross-cutting — Test environment & determinism

- Prefer testnet / forked node (Anvil, Hardhat) / mocked RPC for deterministic runs.
- Use seeded accounts with known balances and known nonces.
- Flag tests whose result depends on live mainnet conditions (gas price, congestion)
  as non-deterministic; isolate them from the regression suite.
---

# Output principle

A good test suite should not simply list UI objects. It should combine:

```text
Common 6 phases
+ Platform-specific risks
+ Business rules
+ Data matrix
+ Environment matrix
+ Clear expected results
```

