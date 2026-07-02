# qc-uc-read progress — UC-EXBOT-bot-safe-close

- run_id: run-20260618-090000-udemysen
- uc_id: UC-EXBOT-bot-safe-close
- mode: first-audit
- started_at: 2026-06-18T09:00:00+07:00
- last_phase_done: 0
- next_phase: 1
- updated_at: 2026-06-18T09:00:00+07:00

## Notes
- Input language: English
- Branch: joy
- Output path: docs/qc/uc-read/UC-EXBOT-bot-safe-close/
- LOGIC-only UC (backend worker — no UI). PTL-04 CF Workers.
- Blockchain-dependent UC: on-chain calls to BnzaExVault (redeem, uninvestedBalanceOf, vaultClose, redeploy) — §6b checklist applies.
- Key integration constraint: IC-EXBOT-002 (BnzaExVault ABI not yet finalized — OQ-EXBOT-08 open)
- Sub-agents B/C/D: skip (no UI)
