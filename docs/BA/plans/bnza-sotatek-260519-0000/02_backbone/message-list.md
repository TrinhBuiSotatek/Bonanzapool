---
type: message-list
status: draft
created: 2026-06-02
updated: 2026-06-09
owner: "@hien.duong"
changelog:
  - "2026-06-09 | /ba-do F4 | clarified E-codes vs MSG-codes scope in header"
  - "2026-06-02 | /ba-qc-export | initial compile: extracted E-MOB, E-pool, E-ADM, E-WLA from module srs/spec.md; EX inline matrix noted separately"
---

# Message List — Cross-Module Error & Info Messages

> **Scope of this file:** E-codes (`E-{MODULE}-{NNN}`) are API-layer error responses returned by the OPERATOR API and other backend services. They are the canonical source for SRS/UC error handling documentation and backend contract definitions.
>
> **E-codes are NOT the same as MSG-codes.** MSG-codes (`MSG-ERR-NN`, `MSG-WRN-NN`, `MSG-INF-NN`) are screen-local display text defined in each screen file §6. Do not merge the two systems.
>
> - E-codes → reference from SRS §Error Handling and UC flows
> - MSG-codes → defined locally in screen file §6; screen file is canonical source

> Canonical registry for all user-facing messages across the bonanzapool project.
> E-codes are prefixed by module. Inline messages without a registered E-code (e.g., bnza-ex) are noted in a separate section.
> **Do not define E-code message text inline in screen files** — reference by E-code from this registry.

---

## MOB — Mobile App

| E-ID | Type | Trigger | User-Facing Message |
|------|------|---------|---------------------|
| E-MOB-001 | Error | HTTP 401 — SIWE signature verification failed | "Signature verification failed. Please try again." |
| E-MOB-002 | Error | HTTP 403 — Tenant mismatch on SIWE | "Access not permitted for this domain." |
| E-MOB-003 | Error | HTTP 429 — Rate limit exceeded on SIWE sign-in | "Too many attempts. Please wait and try again." |
| E-MOB-004 | Error | `/api/mobile/summary` fetch fails | "Unable to load rewards. Pull to refresh." |
| E-MOB-005 | Error | `/api/mobile/positions` fetch fails | "Unable to load positions. Pull to refresh." |
| E-MOB-006 | Error | `/api/mobile/community` fetch fails | "Unable to load community data." |
| E-MOB-007 | Info | RewardDistributor contract is paused | "Receiving is currently paused." |
| E-MOB-008 | Warning | Insufficient ETH for gas on Claim | "A small amount of ETH is required on Base/OP to receive rewards." |
| E-MOB-009 | Error | Bot register call fails | "Bot registration failed. Please try again." |
| E-MOB-010 | Info | Wallet is on unsupported chain for Bot ops | "Please switch to Base or OP to continue." |
| E-MOB-011 | Error | App offline / no network connection | "No connection. Retry." |

> **Note on JWT expiry:** JWT expiry (24h) triggers a silent SIWE re-prompt per BR-MOB-002. It is not surfaced as a user-visible error and has no E-code.

---

## POOL — BNZA Pool (bnza-pool)

| E-ID | Code | Trigger | User-Facing Message |
|------|------|---------|---------------------|
| E-pool-001 | `forbidden_not_owner` | atomic-start: wallet is not owner | Fatal: "Contact support" |
| E-pool-002 | `not_allowed` | atomic-start: action not permitted | Fatal: "Contact support" |
| E-pool-003 | `blocked` | atomic-start: wallet blocked | Fatal: "Contact support" |
| E-pool-004 | `wallet_address_required` | atomic-start: missing wallet header | Fatal: "Contact support" |
| E-pool-005 | `invalid_status` | atomic-start: invalid bot status | Fatal: "Contact support" |
| E-pool-006 | `missing_required_fields` | atomic-start: incomplete body | Fatal: "Contact support" |
| E-pool-007 | `bot_config_not_found` | stop: bot config not found | Fatal: "Contact support" |
| E-pool-008 | `already_stopped` | stop: bot already stopped | Treated as success — no error shown |
| E-pool-009 | 5xx on atomic-start | API server error | Retry available (up to 3x per BR-PL-16) |
| E-pool-010 | Gas reserve insufficient | < 0.001 ETH in wallet before bot start | "Insufficient ETH for gas. Add at least 0.001 ETH." |

---

## ADM — BNZA Admin (bnza-admin)

| E-ID | HTTP | Trigger | User-Facing Message |
|------|------|---------|---------------------|
| E-ADM-001 | 409 | `wl_code` already exists | "WL code already in use. Choose a unique code." |
| E-ADM-002 | 409 | `referral_code` already exists | "Referral code already taken. Try auto-generate." |
| E-ADM-003 | 400 | `fixed_deposit_usd` invalid value | "Deposit tier must be 1000, 5000, or 10000." |
| E-ADM-004 | 400 | Logo file too large (> 5 MB) | "Logo file must be under 5MB." |
| E-ADM-005 | 400 | Logo file wrong format | "Logo must be PNG or SVG format." |
| E-ADM-006 | 400 | Fee distribution sum ≥ 1.0 | "Total allocation cannot reach or exceed 100%. Adjust share ratios." |
| E-ADM-007 | 400 | No remainder entry in fee distribution | "At least one entry must be designated as the remainder recipient." |
| E-ADM-008 | 400 | Fee distribution max entries exceeded | "Maximum 10 distribution entries allowed." |
| E-ADM-009 | 400 | `cooldown_range_min` out of range | "Cooldown must be between 10 and 180 minutes." |
| E-ADM-010 | 403 | Insufficient role for write operation | "You don't have permission to perform this action." |
| E-ADM-011 | 404 | WL partner not found | "Partner not found or has been removed." |
| E-ADM-012 | 404 | System config key not found | "Configuration key not recognized." |
| E-ADM-013 | 504 | OPERATOR API timeout | "Data could not be loaded. Retry or contact support." |
| E-ADM-014 | 502 | Dashboard stats API error | "Dashboard data unavailable. Last refresh: {timestamp}." |
| E-ADM-015 | 500 | Report export failed | "Export failed. Try a shorter date range or retry." |

---

## WLA — WL Admin (wl-admin)

| E-ID | HTTP | Trigger | User-Facing Message |
|------|------|---------|---------------------|
| E-WLA-001 | 409 | Distribution job already exists for today | "Distribution job already exists for today" |
| E-WLA-002 | 409 | ABANDONED without prior BLOCKED recovery attempt | "Cannot abandon: BLOCKED recovery not attempted" |
| E-WLA-003 | 400 | Invalid pipeline state transition | "Invalid state transition: {from} → {to}" |
| E-WLA-004 | 503 | BNZA Ledger API error during LEDGER_FETCH | "BNZA Ledger API error: {api_error}" |
| E-WLA-005 | 503 | BNZA Position API error during BOT_SYNC | "BNZA Position API error: {api_error}" |
| E-WLA-006 | 400 | Distributor balance insufficient for payout | "Distributor balance insufficient for payout" |
| E-WLA-007 | 409 | clientNonce already used for this job | "clientNonce already used for this job" |
| E-WLA-008 | 400 | Referral edge creates cycle in tree | "Referral edge creates cycle" |
| E-WLA-009 | 400 | Parent wallet not found in users table | "Parent wallet not found in users table" |
| E-WLA-010 | 400 | Cap multiplier must be > 0 | "Cap multiplier must be > 0" |
| E-WLA-011 | 400 | Rank fee_rate_pct sum exceeds 100% | "Rank fee_rate_pct sum exceeds 100%" |
| E-WLA-012 | 400 | Title diff_bonus_pct must be non-negative | "Title diff_bonus_pct must be non-negative" |
| E-WLA-013 | 400 | Referral level rate sum must not exceed 100% | "Referral level rate sum must not exceed 100%" |
| E-WLA-014 | 403 | Insufficient role — Super required | "Insufficient role: Super required" |
| E-WLA-015 | 400 | Reason note absent or < 10 chars on write action | "Reason note required (minimum 10 characters)" |
| E-WLA-016 | 400 | Attempt to change read-only `wl_code` after init | "Cannot modify wl_code after initialization" |
| E-WLA-017 | 409 | Snapshot regeneration on already-snapshotted job | "Snapshot already exists for this job" |
| E-WLA-018 | 503 | Slack webhook call fails (audit log still written) | "Slack mirror failed; retry queued" |

---

## EX — BNZA Exchange (bnza-ex)

> bnza-ex does not use registered E-codes. Error scenarios are documented as an inline Error Handling Matrix in `03_modules/bnza-ex/srs/spec.md §12`.

| Scenario | Trigger | Message shown to user | Retryable |
|----------|---------|----------------------|-----------|
| User declines Agent approval in MetaMask | User clicks Reject in MetaMask popup | "Agent approval required to trade. Please try again." | Yes |
| User declines Builder Fee approval | User clicks Reject in second MetaMask popup | "Builder fee approval required. Please try again." | Yes |
| Wrong network (not Arbitrum) | Wallet connected to non-Arbitrum chain | Prompt to switch to Arbitrum | Yes — after switching |
| Network error during approval | No internet / Hyperliquid API down | "Approval failed. Please retry." | Yes |
| Insufficient margin | Order notional > available margin | "Insufficient margin" (inline) | Yes — reduce size or add margin |
| Order size too small | Size below Hyperliquid minimum | "Order size too small" (inline) | Yes |
| Agent wallet not set up | User tries to place before completing setup | Place Order button disabled; tooltip: "Wallet setup required" | N/A — complete setup first |
| Hyperliquid API timeout | No response within timeout | "Order submission failed. Please retry." | Yes |
| Order rejected by Hyperliquid | e.g. post-only conflict, invalid price | Hyperliquid's error message shown verbatim | Depends on error |
| Order filled on cancel attempt | Order filled between cancel request and HL processing | No error — treated as successful cancel | N/A |
| TradingView library missing | `charting_library/` folder absent from repo | "TradingView Charting Library coming soon" (chart area) | N/A — dev task |
| Candle data API unavailable | Hyperliquid info API down | "No data" (chart area) | Auto-retries |
| WebSocket disconnected | Network interruption | Chart freezes on last known candle | Auto-reconnects |
| Symbol not found | Symbol removed from Hyperliquid | "Symbol not found" (chart) | User can search another symbol |
