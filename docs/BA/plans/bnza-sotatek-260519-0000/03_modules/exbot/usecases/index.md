---
type: usecases-index
module: exbot
generated_at: 2026-06-12
stale_status: unknown
---

# Use Cases Index — exbot

| Field | Value |
|---|---|
| index_type | `usecases_index` |
| source_artifact | `plans/bnza-sotatek-260519-0000/03_modules/exbot/usecases` |
| source_hash | `` |
| generated_at | `2026-06-12` |
| generated_by_command | `/ba-start srs --slug bnza-sotatek-260519-0000 --module exbot` |
| validated_at | `` |
| validated_by | `` |
| stale_status | `unknown` |

## Use Case Index

| UC ID | File | Actor(s) | Description | Linked Stories | FR Trace | Stale |
|---|---|---|---|---|---|---|
| UC-EXBOT-bot-start | `uc-bot-start.md` | USDC Investor, ExBot Worker, BnzaExVault, HL | Start ExBot: preflight → LP mint → hedge open → stop place → active | US-EXBOT-001 | FR-001,002,003,004,020,030,031 | unknown |
| UC-EXBOT-light-check | `uc-light-check.md` | ExBot System Operator (Cron→Scan→LC Workers) | Periodic light-check: zero HL calls, evaluate rebalance reasons, fan-out | US-EXBOT-005 | FR-012,013,014,015,016,032 | unknown |
| UC-EXBOT-hedge-sync | `uc-hedge-sync.md` | ExBot System Operator (Hedge-Sync Worker), HL | Delta-only hedge adjustment + stop replace via INV-STOP protocol | US-EXBOT-006 | FR-020,021,022,024,025,026,027,035 | unknown |
| UC-EXBOT-user-redeem | `uc-user-redeem.md` | USDC Investor, BnzaExVault, Redeem Worker, HL | User-initiated LP-first redemption + HL hedge close SLA 5 min | US-EXBOT-004 | FR-070,071 | unknown |
| UC-EXBOT-bot-safe-close | `uc-bot-safe-close.md` | ExBot System Operator, HL, BnzaExVault | System hedge-first close + USDC park + automatic re-entry closed loop | US-EXBOT-009 | FR-070,071,072,073 | unknown |
| UC-EXBOT-agent-key | `uc-agent-key.md` | USDC Investor, ExBot Admin, Cloudflare Secrets Store | Submit + encrypt + approve HL agent key (AES-GCM envelope) | US-EXBOT-011 | FR-080,081,082,083 | unknown |
