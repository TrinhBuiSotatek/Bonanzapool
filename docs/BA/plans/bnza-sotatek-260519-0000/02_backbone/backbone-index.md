---
name: backbone-index
description: Navigator index for bnza-sotatek-260519-0000 backbone — section anchors, trace IDs, module/feature hints
metadata:
  type: project
  index_type: backbone
  source_artifact: plans/bnza-sotatek-260519-0000/02_backbone/backbone.md
  source_hash: 34db19208a5caf2fd3c236e76aa2d96793c1b44a69153a4941cfa261a00ce912
  generated_at: 2026-06-08T00:00:00Z
  generated_by_command: ba-start srs --slug bnza-sotatek --date 260519-0000 --module operator
  stale_status: ok
  validated_at: "2026-06-09"
  validated_by: ""
  coverage_summary: Actors, Portal Matrix, Permissions, Feature Map (PTL-01–06), Cross-Project Deps, Priority Ordering, System Constraints, Delivery Structure
---

# Backbone Index — bnza-sotatek-260519-0000

> Navigator only. Section names, trace anchors, and short summaries. Full text lives in `backbone.md`.

## Section Index

| Section | Heading | Trace IDs | Module / Feature | Short Summary |
|---|---|---|---|---|
| §0 | Delivery Structure | — | All | Line 1 (WL+MLM, SOTATEK) vs Line 2 (ExBot, deferred). M1 = June 2. |
| §1 | Shared Actors | ACT-01→07 | All | 7 actors: End User, WL Partner, WL End User (OOS), Admin, Trader, OPERATOR System, WL Operator Admin (OOS) |
| §2 | Portal Matrix | PTL-01→06 | All | 6 portals: WL Mobile (OOS), ADMIN, EX, OPERATOR API, POOL, WL Admin (OOS) |
| §3 | Permissions — Cross-Project | ACT-01→07 × PTL-01→06 | All | Actor × Portal access summary matrix |
| §4.2 | Permissions — BNZA-ADMIN | ACT-04 | bnza-admin | Admin actions: WL partners, PF, IB, bots, dashboard, reports, system settings |
| §4.4 | Permissions — EXBOT Infra (PTL-04) | ACT-06, ACT-04 | operator | OPERATOR system actions; admin: force-stop, wrangler tail |
| §5.0 | Feature Map — WL Admin (PTL-06) | FM-WLA-01→07 | wl-admin | OOS (Helix scope). Distribution pipeline, reward engine, RewardDistributor, reconciliation. |
| §5.0B | Feature Map — WL Mobile (PTL-01) | FM-MOB-01→11 | wl-mobile | OOS (Helix scope). SIWE auth, reward display, claim, bot ops, community, multi-tenant. |
| §5.2 | Feature Map — BNZA-ADMIN (PTL-02) | FM-ADM-01→11 | bnza-admin | P0 WL launch critical. WL partner onboarding (FM-ADM-01), PF config (FM-ADM-02), WL bot monitor (FM-ADM-10), IB (FM-ADM-03), bot type config (FM-ADM-04), dashboard (FM-ADM-05), reports (FM-ADM-06), user management (FM-ADM-11). |
| §5.3 | Feature Map — BNZA-EX (PTL-03) | FM-EX-01→06 | bnza-ex | P2 non-blocking. Hyperliquid integration, PnL display, margin deposit (CCTP), leaderboard. |
| §5.4 | Feature Map — EXBOT Infra (PTL-04) | FM-XB-01→08 | operator / exbot | P0 WL launch critical. Bot lifecycle API, fee collection, access control, queue v2, relayer, EXBOT endpoints (FM-XB-06/08 deferred post-WL). |
| §5.5 | Feature Map — BNZA-POOL (PTL-05) | FM-POOL-01→09 | bnza-pool | P1 post-WL. Steps 7–8. ZapMint UI, position management, earnings display, rebalance, stop. |
| §6 | Cross-Project Dependency Graph | — | All | OPERATOR → POOL, ADMIN; ADMIN → OPERATOR (WL lifecycle); EXBOT → OPERATOR; WL Admin → OPERATOR |
| §7 | Priority Ordering | — | All | Line 1 Tier 0: WL+MLM core (M1 June 2); Tier 1: post-WL; Tier 2: enhancements. Line 2: ExBot (deferred). |
| §8.1 | Auth Model | — | All | Wallet connect (POOL/ADMIN), SIWE/JWT (WL Mobile), CF Access (ADMIN/WL Admin), internal system (OPERATOR) |
| §8.2 | Fee Model | — | operator, bnza-pool | Router v2.2.2: swap fee 0.5%, opFee 0.5%, PF 30% of earnings. WL split: 70% master, 30% BNZA. |
| §8.3 | Scale Requirements | — | operator | 10k bots, 3h daily collect SLO (UTC 00:01–03:00), 50 relayers, 60s lock timeout |
| §8.4 | Deployment Topology | — | All | CF Workers (OPERATOR), CF Pages (ADMIN/EX/POOL), Vercel (POOL alt), D1 (22 migrations), Queues (3), DO (2 active) |
| §8.5 | Shared Design Language | — | All | shadcn/ui, Tailwind 4, React 19, TypeScript 5.9 |
| §8.6 | Testing Standards | — | All | Resolved OQ-7: unit + integration per module; E2E for critical paths |
| §8.7 | EXBOT Contract Architecture | — | exbot | BnzaExVault Option C selected. Phase 0 gate conditions (4 conditions, not yet met). |
| §8.8 | WL+MLM System Architecture | FM-WLA, FM-ADM-01/10 | wl-admin, bnza-admin | wlMaster mapping, net/principal split, WlNetSent event, member lifecycle, money flow (§8.8.3) |
| §10 | Recommended Next Steps | — | All | FRD order, remaining commands |
| §11 | Source Traceability | — | All | Intake → backbone trace anchors |
