---
type: message-list
status: draft
created: 2026-06-02
updated: 2026-06-26
module: bnza-backbone
owner: "@hien.duong"
changelog:
  - "2026-06-26 | /ba-do | register MSG-SUC-79/80 for master wallet deactivate/activate (whitelabel SCR-ADM-02)"
  - "2026-06-26 | manual | consolidate duplicate MSG-ERR-92 system error to MSG-ERR-79 and renumber subsequent codes"
  - "2026-06-26 | manual | format MSG-ERR-R01 to MSG-ERR-96, MSG-WRN-R01 to MSG-WRN-02, and restore deprecated MSG-SUC-57/58/64 as stubs"
  - "2026-06-25 | manual | register MSG-ERR-95 for plans screen saving bot type configuration error"
  - "2026-06-25 | manual | sync and resolve conflicts for MSG-ERR-82/83/85, MSG-SUC-71/73, MSG-ERR-79, MSG-ERR-75, MSG-ERR-68/69/70 and register relayer messages"
  - "2026-06-25 | manual | update MSG-ERR-72 text to match fee-distribution screen and remove deprecated MSG-SUC-57/58"
  - "2026-06-25 | manual | resolve MSG-ERR-65 and MSG-ERR-67 duplicates by renaming to MSG-ERR-87 and MSG-ERR-88"
  - "2026-06-25 | manual | register MSG-SUC-73, MSG-SUC-75, and MSG-SUC-76 success messages for whitelabel"
  - "2026-06-25 | manual | assign MSG-SUC-74 for force stop success in bots screen and message list"
  - "2026-06-25 | manual | align MSG-ERR-65 to VR-15 regex and sync Rotate API Key messages with whitelabel screen"
  - "2026-06-24 | manual | register E-ADM-018/019/025 and admin MSG codes"
  - "2026-06-09 | /ba-do F4 | clarified E-codes vs MSG-codes scope in header"
  - "2026-06-26 | manual | add E-EXBOT-016 for approve expired agent key (I-18 fix)"
  - "2026-06-26 | manual | add E-EXBOT-014/015 for agent key submit rejection cases (pending and approved)"
  - "2026-06-26 | manual | register E-EXBOT-001..013 section from srs/spec.md §5 — ExBot module error codes missing from registry"
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
| E-ADM-016 | 409 | Whitelabel suspended during registration | "Registration blocked. This Whitelabel partner is currently suspended." |
| E-ADM-017 | 409 | Optimistic locking state check failure | "The operation failed due to a state mismatch. The page will reload. Please retry." |
| E-ADM-018 | 409 | A master wallet already exists for this chain | "A master wallet already exists for this chain." |
| E-ADM-019 | 409 | This wallet is already active in another Whitelabel partner program | "This wallet is already active in another Whitelabel partner program." |
| E-ADM-025 | 409 | Member or wl_code not active | "Member or wl_code not active - retry not allowed" |

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

## MSG-POOL — BNZA Pool UI Messages (bnza-pool)

> Screen-local display codes defined in each screen file §6. Same code number may carry different text depending on the originating screen. `Screen` column identifies the canonical source.

| Code | Type | Screen | Text |
|------|------|--------|------|
| MSG-ERR-01 | ERR | bot (SCR-POOL-03) | "Unsupported network. Please switch to OP Mainnet or Base." |
| MSG-ERR-01 | ERR | bot-monitor (SCR-POOL-02) | "Unable to load bots. Please try again." |
| MSG-ERR-01 | ERR | bot-create (SCR-POOL-01) | "Unsupported network. Please switch to OP Mainnet or Base." |
| MSG-ERR-01 | ERR | pairs (SCR-POOL-05) | "Unsupported network. Please switch to OP Mainnet or Base." |
| MSG-ERR-01 | ERR | positions (SCR-POOL-07) | "Unsupported network. Please switch to OP Mainnet or Base." |
| MSG-ERR-01 | ERR | rules (SCR-POOL-08) | "Unsupported network. Please switch to OP Mainnet or Base." |
| MSG-ERR-01 | ERR | pool-list (SCR-POOL-06, superseded) | "Unable to load pools. Please try again." |
| MSG-ERR-02 | ERR | bot (SCR-POOL-03) | "Unable to resolve pool on-chain. Please try again." |
| MSG-ERR-02 | ERR | bot-monitor (SCR-POOL-02) | "Stop transaction failed. Please try again." |
| MSG-ERR-02 | ERR | bot-create (SCR-POOL-01) | "Unable to resolve pool on-chain. Please try again." |
| MSG-ERR-02 | ERR | positions (SCR-POOL-07) | "Unable to resolve pool on-chain. Please try again." |
| MSG-ERR-03 | ERR | bot (SCR-POOL-03) | "Amount must be greater than 0." |
| MSG-ERR-03 | ERR | bot-monitor (SCR-POOL-02) | "Fatal error stopping bot. Please contact support." |
| MSG-ERR-03 | ERR | bot-create (SCR-POOL-01) | "Amount must be greater than 0." |
| MSG-ERR-04 | ERR | bot (SCR-POOL-03) | "Amount exceeds your wallet balance." |
| MSG-ERR-04 | ERR | bot-create (SCR-POOL-01) | "Amount exceeds your wallet balance." |
| MSG-ERR-05 | ERR | bot (SCR-POOL-03) | "Insufficient ETH for gas. Add at least 0.001 ETH." |
| MSG-ERR-05 | ERR | bot-create (SCR-POOL-01) | "Insufficient ETH for gas. Add at least 0.001 ETH." |
| MSG-ERR-05 | ERR | positions (SCR-POOL-07) | "Insufficient ETH for gas. Add at least 0.001 ETH." |
| MSG-ERR-06 | ERR | bot (SCR-POOL-03) | "Bot registration failed. Please retry." |
| MSG-ERR-06 | ERR | bot-create (SCR-POOL-01) | "Bot registration failed. Please retry." |
| MSG-ERR-06 | ERR | rules (SCR-POOL-08) | "Rule registration failed. Please retry." |
| MSG-ERR-07 | ERR | bot (SCR-POOL-03) | "Fatal error. Please contact support." |
| MSG-ERR-07 | ERR | bot-create (SCR-POOL-01) | "Fatal error. Please contact support." |
| MSG-ERR-08 | ERR | bot (SCR-POOL-03) | "Transaction failed. Please try again." |
| MSG-ERR-08 | ERR | dashboard (SCR-POOL-04) | "Failed to load dashboard data. Please try again." |
| MSG-ERR-09 | ERR | bot (SCR-POOL-03) | "Failed to stop bot. Please try again." |
| MSG-ERR-09 | ERR | dashboard (SCR-POOL-04) | "Failed to claim fees. Please try again." |
| MSG-ERR-10 | ERR | bot (SCR-POOL-03) | "Failed to fetch bot configurations. Please refresh." |
| MSG-ERR-10 | ERR | settings (SCR-POOL-09) | "Failed to send test notification. Check your configuration." |
| MSG-ERR-11 | ERR | bot (SCR-POOL-03) | "Failed to fetch positions. Please refresh." |
| MSG-ERR-11 | ERR | settings (SCR-POOL-09) | "Failed to create API key. Please try again." |
| MSG-ERR-12 | ERR | bot (SCR-POOL-03) | "Amount must be at least $1,000 USD equivalent." |
| MSG-ERR-12 | ERR | settings (SCR-POOL-09) | "API key name is required and must be 50 characters or fewer." |
| MSG-ERR-13 | ERR | bot (SCR-POOL-03) | "Position registration failed after multiple retries. Please contact support." |
| MSG-ERR-13 | ERR | buy (SCR-POOL-10) | "Please enter a valid payment amount." |
| MSG-ERR-14 | ERR | bot (SCR-POOL-03) | "Pool resolution failed. Please try again or select a different pool." |
| MSG-ERR-14 | ERR | buy (SCR-POOL-10) | "Purchase failed. Please try again." |
| MSG-WRN-01 | WRN | bot (SCR-POOL-03) | "You have reached the maximum of 10 bots on this chain." |
| MSG-WRN-01 | WRN | bot-monitor (SCR-POOL-02) | "Your position is out of range. The bot is not earning fees." |
| MSG-WRN-01 | WRN | bot-create (SCR-POOL-01) | "You have reached the maximum of 10 bots on this chain." |
| MSG-WRN-01 | WRN | pairs (SCR-POOL-05) | "You have reached the maximum of 10 bots on this chain." |
| MSG-WRN-01 | WRN | positions (SCR-POOL-07) | "You have reached the maximum of 10 bots on this chain." |
| MSG-WRN-01 | WRN | rules (SCR-POOL-08) | "You have reached the maximum of 5 rules for this position." |
| MSG-WRN-01 | WRN | pool-list (SCR-POOL-06, superseded) | "You have reached the maximum of 10 bots on this chain." |
| MSG-WRN-02 | WRN | bot (SCR-POOL-03) | "Insufficient ETH balance. Please bridge more ETH to this network." |
| MSG-WRN-02 | WRN | dashboard (SCR-POOL-04) | "Dashboard data may be stale. Last updated: {timestamp}." |
| MSG-WRN-02 | WRN | positions (SCR-POOL-07) | "Position is out of range. Consider rebalancing." |
| MSG-WRN-02 | WRN | rules (SCR-POOL-08) | "Rule execution failed. Check logs for details." |
| MSG-INF-01 | INF | bot (SCR-POOL-03) | "ETH will be wrapped to WETH before deposit." |
| MSG-INF-01 | INF | bot-monitor (SCR-POOL-02) | "This action is irreversible. The bot will be stopped and your position will be withdrawn." |
| MSG-INF-01 | INF | bot-create (SCR-POOL-01) | "ETH will be wrapped to WETH before deposit." |
| MSG-INF-01 | INF | pairs (SCR-POOL-05) | "ETH will be wrapped to WETH before deposit." |
| MSG-INF-01 | INF | positions (SCR-POOL-07) | "ETH will be wrapped to WETH before deposit." |
| MSG-INF-01 | INF | rules (SCR-POOL-08) | "ETH will be wrapped to WETH before deposit." |
| MSG-INF-01 | INF | pool-list (SCR-POOL-06, superseded) | "No pools match your filter." |
| MSG-INF-02 | INF | bot (SCR-POOL-03) | "This setting cannot be changed after bot creation." |
| MSG-INF-02 | INF | bot-create (SCR-POOL-01) | "This setting cannot be changed after bot creation." |
| MSG-INF-02 | INF | pairs (SCR-POOL-05) | "No pools found. Try changing the chain or filter." |
| MSG-INF-02 | INF | positions (SCR-POOL-07) | "Position data refreshed successfully." |
| MSG-INF-02 | INF | rules (SCR-POOL-08) | "Rule deleted successfully." |
| MSG-INF-02 | INF | pool-list (SCR-POOL-06, superseded) | "No favorite pools yet. Click ☆ to add." |
| MSG-INF-03 | INF | dashboard (SCR-POOL-04) | "Connect your wallet to view your positions." |
| MSG-INF-04 | INF | dashboard (SCR-POOL-04) | "Loading dashboard data…" |
| MSG-INF-05 | INF | dashboard (SCR-POOL-04) | "No positions found on this chain." |
| MSG-INF-06 | INF | settings (SCR-POOL-09) | "Test notification sent successfully." |
| MSG-INF-07 | INF | settings (SCR-POOL-09) | "API key created." |
| MSG-INF-08 | INF | settings (SCR-POOL-09) | "API key deleted." |
| MSG-INF-09 | INF | buy (SCR-POOL-10) | "Redirecting to Banxa…" |
| MSG-INF-10 | INF | buy (SCR-POOL-10) | "Transaction ID copied to clipboard." |
| MSG-SUC-01 | SUC | bot (SCR-POOL-03) | "Bot started successfully!" |
| MSG-SUC-01 | SUC | bot-monitor (SCR-POOL-02) | "Bot stopped. Funds returned to wallet." |
| MSG-SUC-01 | SUC | settings (SCR-POOL-09) | "Language updated successfully." |
| MSG-SUC-02 | SUC | buy (SCR-POOL-10) | "Purchase request submitted." |

---

## MSG-ADM — BNZA Admin UI Messages (bnza-admin)

> Screen-local display codes defined in each screen file §6. Same code number may carry different text depending on the originating screen. `Screen` column identifies the canonical source.

| Code | Type | Screen | Text |
|------|------|--------|------|
| MSG-ERR-15 | ERR | reports (SCR-ADM-11) | "Export failed. Try a shorter date range or retry." |
| MSG-ERR-51 | ERR | access-control (SCR-ADM-14) | "Unrecognized access mode. Refresh and try again." |
| MSG-ERR-52 | ERR | access-control (SCR-ADM-14) | "Invalid wallet address. Must be a 0x… EVM address." |
| MSG-ERR-53 | ERR | access-control (SCR-ADM-14) | "This address is already in the list." |
| MSG-ERR-54 | ERR | access-control (SCR-ADM-14) | "Cannot add address to both Whitelist and Blacklist." |
| MSG-ERR-55 | ERR | access-control (SCR-ADM-14) | "Failed to save access mode. Please retry." |
| MSG-ERR-56 | ERR | access-control (SCR-ADM-14) | "Failed to remove address. Please retry." |
| MSG-ERR-57 | ERR | whitelabel (SCR-ADM-02) | "This field is required." |
| MSG-ERR-58 | ERR | whitelabel (SCR-ADM-02) | "WL code already in use. Choose a unique code." |
| MSG-ERR-59 | ERR | whitelabel (SCR-ADM-02) | "Logo file must be under 5 MB." |
| MSG-ERR-60 | ERR | whitelabel (SCR-ADM-02) | "Logo must be PNG, JPG, or SVG format." |
| MSG-ERR-61 | ERR | whitelabel (SCR-ADM-02) | "Referral code already taken. Try auto-generate." |
| MSG-ERR-62 | ERR | whitelabel (SCR-ADM-02) | "Deposit tier must be 1000, 5000, or 10000." |
| MSG-ERR-63 | ERR | whitelabel (SCR-ADM-02) | "This wallet is already active or leaving in another WL." |
| MSG-ERR-64 | ERR | whitelabel (SCR-ADM-02) | "A master wallet for this chain already exists for this WL." |
| MSG-ERR-65 | ERR | system-settings (SCR-ADM-09) | "Invalid value. Please check the field constraints." |
| MSG-ERR-66 | ERR | whitelabel (SCR-ADM-02) | "Failed to rotate API key. Please retry." |
| MSG-ERR-67 | ERR | system-settings (SCR-ADM-09) | "Failed to save settings. Please retry." |
| MSG-ERR-68 | ERR | system-settings (SCR-ADM-09) | "Emergency stop failed. Please retry or contact support." |
| MSG-ERR-69 | ERR | users (SCR-ADM-17) | "Failed to block wallet. Please retry." |
| MSG-ERR-70 | ERR | fee-distribution (SCR-ADM-04) | "Recipient name is required." |
| MSG-ERR-71 | ERR | fee-distribution (SCR-ADM-04) | "Total share exceeds 100%. Adjust values before saving." |
| MSG-ERR-72 | ERR | fee-distribution (SCR-ADM-04) | "At least one remainder entry is required." |
| MSG-ERR-73 | ERR | fee-distribution (SCR-ADM-04) | "Maximum 10 distribution entries reached." |
| MSG-ERR-74 | ERR | bot (SCR-ADM-20) | "Failed to stop bot. Please retry." |
| MSG-ERR-75 | ERR | ib (SCR-ADM-07) | "Partner name is required." |
| MSG-ERR-76 | ERR | wl-monitor (SCR-ADM-18) | "Retry failed. Preconditions not met (WL member or WL code is not active)." |
| MSG-ERR-77 | ERR | wl-monitor (SCR-ADM-18) | "Force-normalize failed. Please retry." |
| MSG-ERR-78 | ERR | wl-monitor (SCR-ADM-18) | "Reason must be between 10 and 255 characters." |
| MSG-ERR-79 | ERR | wl-monitor (SCR-ADM-18) | "Action failed due to system error. Please try again." |
| MSG-ERR-80 | ERR | users (SCR-ADM-17) | "You cannot block your own wallet address." |
| MSG-ERR-81 | ERR | users (SCR-ADM-17) | "Failed to unblock wallet. Please retry." |
| MSG-ERR-82 | ERR | plans (SCR-ADM-03) | "Failed to save plan settings. Please try again." |
| MSG-ERR-83 | ERR | plans (SCR-ADM-03) | "Failed to load plan specifications. Please refresh." |
| MSG-ERR-84 | ERR | audit-log (SCR-ADM-19) | "Failed to load audit entry detail. Please retry." |
| MSG-ERR-85 | ERR | audit-log (SCR-ADM-19) | "Failed to load audit log. Please retry." |
| MSG-ERR-86 | ERR | ib (SCR-ADM-07) | "Commission rate must be between 0 and 100%." |
| MSG-ERR-87 | ERR | whitelabel (SCR-ADM-02) | "WL Code must be 2–32 uppercase letters, digits, or underscores." |
| MSG-ERR-88 | ERR | whitelabel (SCR-ADM-02) | "Reason note must be between 10 and 255 characters." |
| MSG-ERR-89 | ERR | plans (SCR-ADM-03) | "Failed to create version" |
| MSG-ERR-90 | ERR | dashboard (SCR-ADM-01) | "Failed to load dashboard data. Please retry." |
| MSG-ERR-91 | ERR | bot (SCR-ADM-20) | "Bot is already stopped." |
| MSG-ERR-92 | ERR | whitelabel (SCR-ADM-02) | "Registration blocked. This Whitelabel partner is currently suspended." |
| MSG-ERR-93 | ERR | whitelabel (SCR-ADM-02) | "The operation failed due to a state mismatch. The page will reload. Please retry." |
| MSG-ERR-94 | ERR | plans (SCR-ADM-03) | "Failed to save bot type configuration. Please retry." |
| MSG-ERR-95 | ERR | relayer (SCR-ADM-12) | "Status unavailable — API error" |
| MSG-INF-70 | INF | dashboard (SCR-ADM-01) | "Dashboard data updates every 30s." |
| MSG-SUC-50 | SUC | access-control (SCR-ADM-14) | "Access mode updated." |
| MSG-SUC-51 | SUC | access-control (SCR-ADM-14) | "Address added to list." |
| MSG-SUC-52 | SUC | access-control (SCR-ADM-14) | "Address removed." |
| MSG-SUC-53 | SUC | whitelabel (SCR-ADM-02) | "WL partner saved." |
| MSG-SUC-54 | SUC | whitelabel (SCR-ADM-02) | "API key rotated successfully." |
| MSG-SUC-55 | SUC | whitelabel (SCR-ADM-02) | "Member registered." |
| MSG-SUC-56 | SUC | whitelabel (SCR-ADM-02) | "Master wallet registered." |
| MSG-SUC-57 | SUC | whitelabel (SCR-ADM-02) | [Deprecated — superseded by MSG-SUC-75/76] |
| MSG-SUC-58 | SUC | whitelabel (SCR-ADM-02) | [Deprecated — superseded by MSG-SUC-75/76] |
| MSG-SUC-59 | SUC | system-settings (SCR-ADM-09) | "Settings saved." |
| MSG-SUC-60 | SUC | system-settings (SCR-ADM-09) | "Emergency stop executed. All bots halted." |
| MSG-SUC-61 | SUC | users (SCR-ADM-17) | "Wallet added to blacklist." |
| MSG-SUC-62 | SUC | fee-distribution (SCR-ADM-04) | "Recipient saved." |
| MSG-SUC-63 | SUC | fee-distribution (SCR-ADM-04) | "Recipient deleted." |
| MSG-SUC-64 | SUC | bot (SCR-ADM-20) | [Deprecated — superseded by MSG-SUC-74] |
| MSG-SUC-65 | SUC | ib (SCR-ADM-07) | "IB partner saved." |
| MSG-SUC-66 | SUC | ib (SCR-ADM-07) | "IB partner status updated." |
| MSG-SUC-67 | SUC | ib (SCR-ADM-07) | "IB partner deleted." |
| MSG-SUC-68 | SUC | wl-monitor (SCR-ADM-18) | "Retry queued." |
| MSG-SUC-69 | SUC | wl-monitor (SCR-ADM-18) | "Force-normalize initiated." |
| MSG-SUC-70 | SUC | users (SCR-ADM-17) | "Wallet removed from blacklist." |
| MSG-SUC-71 | SUC | plans (SCR-ADM-03) | "Plan settings saved successfully." |
| MSG-SUC-72 | SUC | plans (SCR-ADM-03) | "Save bot type configuration successful" |
| MSG-SUC-73 | SUC | whitelabel (SCR-ADM-02) | "WL code created successfully." |
| MSG-SUC-74 | SUC | bot (SCR-ADM-20) | "Bot #{id} stopped successfully" |
| MSG-SUC-75 | SUC | whitelabel (SCR-ADM-02) | "WL code suspended. Bot delivery paused." |
| MSG-SUC-76 | SUC | whitelabel (SCR-ADM-02) | "WL code resumed." |
| MSG-SUC-77 | SUC | plans (SCR-ADM-03) | "Version {version} created" |
| MSG-SUC-79 | SUC | whitelabel (SCR-ADM-02) | "Master wallet deactivated." |
| MSG-SUC-80 | SUC | whitelabel (SCR-ADM-02) | "Master wallet activated." |
| MSG-WRN-01 | WRN | whitelabel (SCR-ADM-02) | "Bots are still being unset. Please wait before confirming leave." *(tooltip on disabled [Confirm Leave] — GAP-ITEM-02)* |
| MSG-WRN-02 | WRN | relayer (SCR-ADM-12) | "Balance data may be stale — last synced {timestamp}" |

---

## EX — BNZA Exchange (bnza-ex)

> bnza-ex does not use registered E-codes. Error scenarios are documented as an inline Error Handling Matrix in `03_modules/bnza-ex/srs/spec.md §12`.
>
> **E-EX policy (intentional):** bnza-ex uses inline error handling. No `E-EX-NNN` codes are registered in this backbone registry by design. The module-level error matrix is the canonical source — see `03_modules/bnza-ex/srs/spec.md §12`.

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

---

## EXBOT — ExBot Module (bnza-exbot)

> E-EXBOT codes are API-level error codes returned by ExBot Worker via OPERATOR Facade. Canonical source: `03_modules/exbot/srs/spec.md §5`.

| E-Code | Scenario | Message | HTTP |
|--------|----------|---------|------|
| E-EXBOT-001 | One-bot policy violation | "You already have an active ExBot. Close or wait for the existing bot to finish." | 409 |
| E-EXBOT-002 | Insufficient HL margin at preflight | "Required HL margin: $X (with 100% buffer). Current: $Y. Please deposit $Z to HL." | 400 |
| E-EXBOT-003 | Agent key status is pending | "Agent key is awaiting approval. Please complete the approval process before starting." | 400 |
| E-EXBOT-004 | Agent key expired | "Your HL agent key has expired. Please submit a new one." | 400 |
| E-EXBOT-005 | Builder fee not approved | "HL builder fee (5bps) approval required before starting ExBot." | 400 |
| E-EXBOT-006 | LP mint simulation failed | "LP mint simulation failed. Check pool liquidity or adjust deposit amount." | 400 |
| E-EXBOT-007 | HL order rejected (insufficient margin during sync) | "Hedge adjustment rejected: insufficient margin on Hyperliquid. Deposit additional margin." | 502 |
| E-EXBOT-008 | HL API unreachable | "Hyperliquid API is currently unreachable. Bot entered Safe Mode. Retrying automatically." | 503 |
| E-EXBOT-009 | Stop placement failed | "Failed to place native stop on Hyperliquid. Bot cannot activate without a stop." | 502 |
| E-EXBOT-010 | user_redeem SLA breached | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | — (internal alert) |
| E-EXBOT-011 | Reconcile mismatch | "Hedge position mismatch detected. Bot entered Safe Mode pending reconciliation." | — (internal) |
| E-EXBOT-012 | Close attempted on already-closed bot | "Bot is already closed. No action needed." | 409 |
| E-EXBOT-013 | Pause attempted in SAFE_MODE | "Bot is in Safe Mode. You can close the bot instead." | 409 |
| E-EXBOT-014 | Submit agent key while existing key is pending | "Your agent key is awaiting admin approval. You cannot submit a new key until the current one is reviewed." | 409 |
| E-EXBOT-015 | Submit agent key while existing key is approved | "You already have an active agent key. You can only submit a new key after your current key has expired." | 409 |
| E-EXBOT-016 | Approve agent key that has already expired | "This agent key has already expired and cannot be approved. Please ask the investor to submit a new key." | 409 |
| Symbol not found | Symbol removed from Hyperliquid | "Symbol not found" (chart) | User can search another symbol |
