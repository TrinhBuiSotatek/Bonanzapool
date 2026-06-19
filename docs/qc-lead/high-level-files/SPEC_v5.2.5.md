# BNZA Ex Bot 統合技術仕様書 v5.2.5 Final Approved

**Last Updated**: 2026-05-20
**Status**: v5.2.5 Final Approved — 3 AI APPROVED 取得済 (Codex / GPT / Claude Code) + zen approval 確定。Phase 0 着手 OK (4 件の着手条件は §0.3 / §30 を参照)
**Target Audience**: Claude Code 実装用
**Base**: v5.2.4 への直接パッチ。Codex 摘出 minor notes 2 件 (Status canonical 化 + §16.5 版数中立化) のみ反映。設計内容ゼロ変更
**Patch chain**: v5.2 → v5.2.1 (P0 11 件) → v5.2.2 (Codex 同期漏れ 5 件) → v5.2.3 (P1/P2 doc-sync 3 件) → v5.2.4 (自己完結化) → v5.2.5 (minor notes 反映 / Final Approved 確定)。v5.3 は欠番。本 SPEC §30 patch chain で全項目サマリ完結。git history で完全な diff 履歴を保持

> 🚨 v5.2.5 適用済み minor notes 反映 patch (Codex 摘出、設計変更ゼロ):
> Codex v5.2.4 軽量再検証で APPROVED with minor notes 取得後、指摘 2 件を反映: v5.2.5-N1 §30 Status / §30.2 次プロセスの段階差を解消、Final Approved に統一 / v5.2.5-N2 §16.5 Phase B 注記の旧版数依存表現を版数中立 "本 SPEC では" に更新
> 設計内容は v5.2.4 から不変。
>
> 🚨 v5.2.4 適用済み doc-self-containment patch (自己完結化、設計変更ゼロ):
> 過去 PATCH_NOTES.md への外部参照を削除し、本 SPEC v5.2.5 単体で
> 全 patch chain (v5.2 → v5.2.1 → v5.2.2 → v5.2.3 → v5.2.4 → v5.2.5) の情報が
> 完結する状態にした。設計内容は v5.2.3 から不変。
>
> 🚨 v5.2.3 適用済み P1/P2 (Claude Code 摘出・極小 doc-sync 3 件):
> v5.2.3-P1-A §21.5.4 sanitize regex に dek パターン追加 + 列名明記(セキュリティ defense-in-depth) /
> v5.2.3-P1-B §10.1 hedge-sync queue / §17.2 関数引数を canonical RebalanceReason[] 型に統一(§7.6 P0-11 の最終マイル) /
> v5.2.3-P2-A §0.3 着手条件 1 の版数 staleness 修正(§30 と完全一致)
>
> 構造変更ゼロ。設計思想・API・schema・enum 値・Solidity ABI・運用 flow すべて v5.2.2 から不変。
> 全 patch (v5.2 → v5.2.1 P0 11 件 / v5.2.1 → v5.2.2 同期漏れ 5 件 /
>  v5.2.2 → v5.2.3 doc-sync 3 件 / v5.2.3 → v5.2.4 自己完結化 /
>  v5.2.4 → v5.2.5 minor notes 反映) の
> サマリは §30 patch chain を参照。git history で完全な diff 履歴を保持。

---

## 0. Final Review Judgment (v5.1 で追加)

### 0.1 v5.2 の Status

```yaml
v5.0 Status:        "Final Draft for GPT / Codex Validation"
v5.0 検証結論:       "戦略・インフラ方針は妥当。22 個の必須修正を反映後 v5.1 として実装着手 OK"
v5.2 Status:        "Final Candidate — Phase 0 着手 OK after zen approval"
根本見直し:         不要 (戦略骨子・インフラ骨子は維持)
```

### 0.2 v5.0 → v5.1 で何を変えたか (要旨)

```yaml
変えたこと (22 必須修正の要旨):
  - 戦略表現の現実化 ("全相場 net ≥ 0" を削除、IL 完全削除なしを明記)
  - Cloudflare 制約の数値正確化
  - UserLockDO を function-callback 方式から lease-based 方式に変更 (実装可能性)
  - LP NFT custody / control model を新規セクションで明記
  - Hedge 実行を delta-only adjustment へ修正 (毎回 full close/open は禁止)
  - Stop / Liquidation model の再定義 (stop は損失制限、清算回避ではない)
  - Stop trigger 後の stale state 対策 (priority audit + crossed marker)
  - D1 schema の不整合を修正 (ALTER TABLE で追加、削除はしない)
  - Security / key handling を新規セクションで明文化
  - Insufficient margin UX (preflight + warning + critical + SAFE_MODE)
  - LP close authority (BnzaExVault による close flow を明記)
  - Phase A の現実的細分化 (Phase 0 / A1 / A2 / A3) と Defer list 明示
  - Funding ledger を Phase 別に簡素化
  - Analytics Engine の high-cardinality 警告
  - One-user one-bot policy (Phase A) を明記
  - LP operation state machine (LP_OPENING / LP_REBALANCING / LP_CLOSING / LP_FAILURE)
  - Backtest 順序の修正 (Step 0: PositionAmountCalculator mini を先に)
  - 競合差別化表現の現実化 (Panoptic / Neutra に対する数学的優位性主張を削除)

変えなかったこと:
  - 戦略骨子: LP fee engine + adaptive hedge overlay (70% short, 3x isolated)
  - インフラ骨子: CF Workers + D1 sharding + Queue fan-out + DO
  - 商品ラインナップ: LP / Ex / LP Plus / AI Pro
  - Phase の方向性: Correctness MVP → 1k → 10k bots
  - 採用/非採用判断: carter2099 / Panoptic との比較骨子
```

### 0.3 実装開始条件 (Phase 0 着手 OK の判断条件)

```yaml
🚨 v5.2.1 (P0-7 + P0-10): 着手条件を 4 件に統一 (§30 と完全一致)。
  旧 §0.3 は「3 条件」だったが §30 の「4 conditions」と矛盾していた → 4 に統一。

実装開始の 4 条件 (4 つすべて満たした時点で Phase 0 着手):
  1. 本 v5.2.5 を zen が読んで approval (ドキュメント確定)
     🚨 v5.2.5: §30 と完全一致(v5.2.3 P2-A の anti-staleness 原則を継承)。
  2. LP NFT custody 統合方針確定:
     🚨 v5.2.1 確定 (Option C / Section 3.4) — EXBOT 専用 BnzaExVault を
        新規開発・新規デプロイ。現行 BnzaRouter v2.2.1 / BnzaLpBot v1.1 は
        改修しない。Phase 0 開始前に zen が deploy address / operator /
        multiSig を確定 (Section 15.5.6 zen task)
  3. Hyperliquid agent key 暗号化保存方式の詳細設計が Phase 0 開始時に
     確定可能であること:
     🚨 v5.2.1 確定 — Phase A default = Cloudflare Secrets Store
        (Section 21.5.2 / 21.5.2.1 runbook、P0-4)
  4. WL 5/15 ローンチ後の不安定期 gate (🚨 v5.2.1 P0-10 で再定義):
     - WL 5/15 ローンチは既に実施済み (旧「5/15 と競合回避」は失効)
     - Stage 3 rollback (multi-relayer 関連) 等のインシデント対応が
       落ち着いていること
     - 具体 gate: 過去 7 日間 SAFE_MODE 発生ゼロ・major incident なし
     - zen が「POOL ローンチ後の不安定期は脱した」と判定した時点

4 条件未達なら実装着手しない。
特に条件 2・3 は Phase A で着手したらやり直しが大きいため、Phase 0 完了前に固める。
条件 4 は POOL 運用安定性を守るための gate (品質最優先方針、延期許容)。
```

---

## 0.4 検証依頼 (旧 Section 0、v5.0 から維持)

### 0.4.1 検証目的

この仕様書 v5.2 は以下を統合した版:

- **v1-v3 (Claude)**: 戦略コンセプト、商品設計、Marketing
- **v3.1 検証 (前 AI)**: 数学的修正、清算計算、Funding 取り扱い
- **v4.1 検証 (前 AI)**: インフラ層、CF Workers / D1 / Queue 設計、10,000 bot scale
- **carter2099 解析 (Claude Code)**: 実装パターン採用/非採用判断
- **v5.0 検証レポート (GPT / Codex 統合版)**: 22 必須修正

### 0.4.2 検証してほしいポイント (v5.0 から維持、v5.2 用に調整)

```yaml
1. v3.1 戦略層と v4.1 インフラ層の整合性 (v5.1 修正後も維持されているか)
2. 数学的妥当性 (Position amount / Hedge / 清算 / Drift)
3. Cloudflare 制約への適合性 (Section 5.2 の数値)
4. Hyperliquid 仕様への適合性 (Rate limit / subaccount / native stop / cloid)
5. 10,000 bot scale の実現可能性 (Throughput / Sharding / Concurrency)
6. 致命的な見落とし (Edge case / Failure / Recovery)
7. Implementation roadmap の現実性 (Phase 細分化、zen 1 人体制)
8. v5.1 で追加された LP NFT custody / Security / Margin UX / LP state machine の妥当性
```

---

## Part 1: Strategy & Product

## 1. Product Scope

### 1.1 Product Identity

```yaml
Product name: BNZA Ex Bot
Tagline: Managed delta-hedged LP Bot powered by Hyperliquid
Position in BNZA Lineup:
  LP Bot (現行):   Pure LP, no hedge        — DeFi 初心者向け
  Ex Bot (本仕様): LP + HL hedge            — 中級者、IL drawdown 抑制狙い
  LP Plus (Phase 2): LP + Revert Lend       — Capital Efficiency 重視 (Defer)
  AI Pro (Phase 3): LP + Aave + Hedge       — 上級者、市場最適化 (Defer)
```

### 1.2 Core Strategy (v5.1 で表現修正)

```yaml
Strategy Concept: LP Fee Engine + Adaptive Hedge Overlay

Primary revenue: Uniswap V3 LP fee
Hedge role:
  - ETH directional exposure の部分ヘッジ
  - IL の "削減" を狙う (完全削除ではない)
  - LP fee で hedge cost を凌駕する設計目標

Mathematical principle:
  net = LP_fee
        - IL/LVR/gamma_loss
        - hedge_cost
        - funding_cost
        - gas/bridge
        - performance_fee

🚨 v5.1 で表現修正:
  ❌ 旧 (v5.0): "全相場で net ≥ 0、特に下落相場で純LPより drawdown を抑える"
  ✅ 新 (v5.1):
     "Goal: 純 LP に対する drawdown を抑制し、median シナリオで net positive APR を狙う。
      ただし全相場で net ≥ 0 は保証しない。
      IL は本 Bot では削減対象であり、削除対象ではない。
      Hedge cost / funding / gamma loss が LP fee を上回る相場 (低 vol + ranging-out)
      では net negative も発生し得る。"

🚨 IL elimination guarantee の不存在 (v5.1 で明記):
  本 Bot は IL を削減 (reduce drawdown) する設計であり、IL を削除 (eliminate / hedge out)
  する保証は持たない。
  - LP gamma loss は hedge では完全に消せない
  - hedge cost (funding / spread / slippage) は常に発生する
  - hedge と LP の delta は離散調整であり、連続 hedging ではない
  - rebalance threshold 内では未 hedge の delta が残る
```

### 1.3 Phase 1 Scope (本仕様)

```yaml
Chain: Base default
  - 現行 LP Bot 統合 (Base 5 bot 中 3 bot 稼働中)
  - Optimism は backtest で >10% 勝てば Phase 2 で対応

LP:
  Pool: USDC/ETH 0.3% (Uniswap V3)
  Range: ±5% 単一 (ladder は Phase 2 / Defer)
  
Hedge:
  Venue: Hyperliquid
  Asset: ETH-USD perpetual short
  Hedge ratio: 70% (Balanced 固定、Phase 1)
  Leverage: 3x configured (effective leverage は dynamic)
  Margin mode: Isolated (絶対)
  Builder fee: 5bps

Risk Management:
  HL native stop: 必須 (損失制限、清算回避ではない、Section 19 参照)
  Reconcile after order: 必須
  Circuit breaker: 24h で 3 連続失敗で停止
  Stop trigger crossed marker: 必須 (Section 19 参照)

User policy:
  Phase A: 1 user = 1 active Ex Bot (Section 16.5 参照)
  Phase B+: multiple bot per user (subaccount allocation で隔離)
```

---

## 2. Target User & Marketing

### 2.1 Target User

```yaml
Persona:
  - DeFi 中級者 (LP の概念を理解)
  - USDC ベース思考
  - 純 LP の IL リスクを下げたい (削除ではなく削減)
  - 高 APR より drawdown 抑制志向
  - 自己責任で参加可能
  - Bot UI で十分、自分で hedge 計算したくない

Expected APR (Net、PF 30% 控除後):
  Best case:    +25-35%
  Median:       +10-20%
  Bad case:     -5% to +5%
  Tail event:   -10% to -20% (Stop trigger 発生 / SAFE_MODE 連発時)

🚨 v5.1 注記:
  上記はモデルケース。実際の APR は backtest と乖離し得る。
  特に "全相場で net ≥ 0" は保証しない (Section 1.2 参照)。
```

### 2.2 Marketing 表現規定 (v5.1 で再強調)

```yaml
✅ OK 表現:
  - "Uniswap V3 LP fee を主収益にしつつ、ETH directional exposure を Hyperliquid short で部分的に抑える managed LP Bot"
  - "純 LP より drawdown を抑える設計 (削除ではなく削減)"
  - "ETH directional exposure を自動ヘッジ (部分的)"
  - "BNZA POOL に統合された managed delta-hedged LP Bot"

❌ NG 表現 (v5.1 で再確認):
  - "ILヘッジで安全"
  - "元本保証"
  - "元本割れなし"
  - "IL を 90% 削減" (具体数値の保証)
  - "完璧な hedge"
  - "IL を完全に消す / IL elimination"
  - "全相場で net positive"
  - "世界初" / "唯一の実装"

⚠️ Risk Disclosure (必須明記):
  - LP gamma loss (hedge では完全に消せない)
  - Hedge stop trigger による損失確定リスク (清算ではないが loss は確定)
  - HL liquidation risk (stop が遅延した場合の最終 fallback)
  - Funding rate cost (negative funding 期間)
  - HL API 障害リスク (SAFE_MODE 突入時の hedge 不変動)
  - Bridge / CCTP 障害リスク
  - USDC depeg リスク
  - Operator bug リスク
  - Performance fee 控除後のリターン低下
  - Insufficient margin による hedge 不能 / SAFE_MODE 突入リスク
```

### 2.3 Performance Fee 表示

```yaml
Fee 構造 (既存と同じ):
  Operation fee: onchain で 100% BuyBack&Burn (BNZA トークン)
  Performance fee: offchain 30%、最大 10 recipients

UI 表示の透明化 (必須):
  ユーザーには両方を併記:
    - Gross APR (PF 控除前)
    - Net APR (PF 30% 控除後)
  
  例:
    "Expected Gross APR: 25%"
    "Expected Net APR: 17.5% (after 30% performance fee)"

月次レポート:
  LP fee 収入: $42
  Funding 受取/支払: ±$5
  Hedge 損益: -$15
  Hedge 調整 cost: -$8
  Bridge cost: $0
  Gross PnL: $14-24
  Performance fee (30%): -$X
  Net to user: $Y
```

---

## 3. Critical Design Decisions

### 3.1 carter2099/delta_neutral から採用するもの

```yaml
copy:
  - asset leg 単位の hedge 管理
  - target_short = pool_amount × target_ratio (絶対値式)
  - tolerance 判定の絶対値式
  - rebalance attempt 履歴
  - 24h 内 3 失敗 circuit breaker (history-based)
  - nested order error parser
  - subaccount isolation の考え方
  - subgraph collected + RPC uncollected の max() merge
  - per-asset independence
```

### 3.2 carter2099 から採用しないもの (致命的バグ含む)

```yaml
discard:
  - 🚨 deposited - withdrawn + collectedFees による LP amount 算出 (range out で破綻)
  - 🚨 tick / liquidity / sqrtPriceX96 を使わない計算 (Uniswap V3 数式無視)
  - 単一 subgraph URL (multi-network 偽装)
  - market order only (stop / TP-SL なし)
  - order 後 reconcile なし (Atomicity 欠落)
  - failed rebalance 通知なし
  - active=false で short を残す曖昧な pause
  - cross margin default (isolated 必須)
  - 全 hedge を 1 job で逐次処理 (CF Workers では破綻)
  - 1 分ごと PnlSnapshot (D1 で破綻)
  - 🚨 (v5.1 追加) 毎回 full close → full open (subrequest 浪費 + nonce burn)
```

### 3.3 BNZA で新規実装するもの

```yaml
new:
  - PositionAmountCalculator (正しい AMM 数式)
  - HyperliquidAdapter (rate limit / cloid / nested error / reconcile 統合)
  - HL native reduce-only stop (損失制限、清算回避ではない)
  - Reconcile flow (post-order)
  - Funding ledger (Phase 別 — Phase A: daily aggregate のみ)
  - Queue fan-out (light-check / hedge-sync 分離)
  - UserLockDO (lease-based mutation lock — Section 11 参照)
  - HL global/user rate limiter (HLRateLimitDO)
  - D1 sharding (16 shards for 10,000 bot — Phase C で導入)
  - MarketData cache (Durable Objects)
  - R2 / Analytics Engine archive (Phase B+)
  - Hedge budget cap (LP fee × 30%)
  - Edge filter (expectedEdge ベース)
  - 🆕 (v5.1) LP NFT custody model (BnzaExVault 所有、Section 15.5 参照)
  - 🆕 (v5.1) HL Agent Key envelope encryption (Section 21.5 参照)
  - 🆕 (v5.1) Delta-only hedge adjustment (Section 17 参照)
  - 🆕 (v5.1) Stop trigger crossed marker / priority audit (Section 19 参照)
  - 🆕 (v5.1) Insufficient margin preflight + warning + critical (Section 18.4 参照)
  - 🆕 (v5.1) LP operation state machine (Section 16.6 参照)
  - 🆕 (v5.2.1) BnzaExVault (EXBOT 専用 LP NFT custody contract、Section 15.5.6 参照)
```

### 3.4 Contract 構造の責務分離 (🆕 v5.2.1 — Option C 確定)

BNZA エコシステムは以下の 2 つの**独立した** custody model を持つ:

| 商品 | Custody Contract | デプロイ状況 | LP NFT 保有者 |
|---|---|---|---|
| BNZA POOL(現行) | BnzaRouter v2.2.1 | Optimism + Base 稼働中 | user(user-owned NFT) |
| EXBOT(本 SPEC 対象) | BnzaExVault(新規開発) | 未デプロイ | Vault contract |

```yaml
🚨 v5.2.1 zen 決定 (Option C):
  EXBOT は BNZA POOL とは独立した Solidity contract suite を新規開発・
  新規デプロイする。本 SPEC で「Vault」「BnzaExVault」と呼称するのは
  EXBOT 専用の新規 contract であり、現行 BnzaRouter v2.2.1 を
  改修するものではない。

責務分離の原則:
  - BnzaRouter v2.2.1 / BnzaLpBot v1.1: BNZA POOL 専用、改修なし、稼働継続
  - BnzaExVault: EXBOT 専用、新規、本 SPEC §15.5.6 で仕様規定
  - 両者は contract レベルで非干渉 (Section 15.5.4 INV-5)
  - 共有は BNZAToken (BuyBack&Burn) と Uniswap V3 NFPM のみ

⚠️ 用語衝突の注意 (重要):
  Solidity の「BnzaExVault / Vault」と、Hyperliquid の「vaultAddress
  (subaccount address)」は**完全に無関係**。本 SPEC で:
    - "BnzaExVault" / "Vault custody" = EXBOT LP NFT custody contract
    - "vaultAddress" / "subaccount" = Hyperliquid 上の subaccount 識別子
  混同しないこと。
```

---

## Part 2: Technical Architecture

## 4. High-Level Architecture

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  BNZA POOL UI (Next.js / Vercel)             │
│        - Bot 起動 / 停止 / 状態表示                          │
│        - HL margin 残高確認 / Onboarding                     │
│        - Margin warning / Critical / SAFE_MODE 表示          │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│            BNZA OPERATOR (Cloudflare Workers)                │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Cron Scheduler Worker (every 1 minute)              │   │
│  │   shard window scan / enqueue only                  │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Queue: bot-scan → light-check → hedge-sync          │   │
│  │         → reconcile → deep-audit → stop-audit       │   │
│  └────────┬──────────────────────┬─────────────────────┘   │
│           │ rebalance candidate  │ priority audit          │
│           ▼                      ▼                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ UserLockDO (lease-based) + HLRateLimitDO            │   │
│  │   + HyperliquidAdapter                              │   │
│  │   - per-user mutation serialization (lease lock)    │   │
│  │   - global/user token bucket                        │   │
│  │   - delta-only hedge adjustment (Section 17)        │   │
│  │   - reconcile after order                           │   │
│  └────────┬────────────────────────────────────────────┘   │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│ D1 (Phase 別 shard 数)   │  │ R2 / Analytics Engine        │
│   - Phase A: 1 shard    │  │   - raw logs (Phase B+)      │
│   - Phase B: 4 shards   │  │   - old attempts (>90d)      │
│   - Phase C: 16 shards  │  │   - low-cardinality metrics  │
│   - hot state           │  │   ❌ bot_id / user_id を      │
│   - rebalance attempts  │  │      dimension にしない       │
│   - circuit breakers    │  │                              │
│   - hl_agent_keys       │  │                              │
│   - hourly/daily metrics│  │                              │
└─────────────────────────┘  └──────────────────────────────┘

External:
  - Hyperliquid API (orders, info, trigger orders)
  - Uniswap V3 (Base / OP)
  - The Graph (subgraph per chain)
  - On-chain RPC (per chain)
  - Across / CCTP (bridge, ユーザー側で実行)
  - 🆕 BnzaExVault (Solidity, LP NFT custody — Section 15.5)
```

### 4.2 Key Architectural Principles

```yaml
1. Light-check と Hedge-sync の分離
   Light-check: HL 触らない、5 分ごと、全 bot
   Hedge-sync: HL mutation のみ、必要時のみ、event-driven
   Hedge-sync は delta-only adjustment (Section 17 参照)

2. Per-user mutation serialization (lease-based)
   UserLockDO で同一 user の HL 操作を直列化
   Lease (TTL) ベースで lock acquire / release
   Function-callback 方式 (v5.0) は廃止 (Section 11 参照)

3. Shared market cache
   MarketDataDO で pool slot0 を共有 cache
   全 bot が個別に RPC fetch しない

4. Sharded state (Phase 別)
   Phase A: 1 shard / Phase B: 4 shards / Phase C: 16 shards
   bot_id hash で shard 決定

5. Hot state only in D1
   履歴は R2 (Phase B+)、metrics は Analytics Engine (Phase B+)
   D1 行数を最小化

6. Idempotent mutations
   Cloid (deterministic) で重複防止
   Retry safe

7. Post-order reconcile
   Order 投入と success 記録を分離
   実 position 確認後に DB 更新

8. 🆕 Delta-only hedge adjustment (v5.1)
   毎回 full close → full open は禁止
   targetSize - actualSize の delta のみ調整
   Full close は target=0 / emergency / manual reset のみ

9. 🆕 LP NFT custody by BnzaExVault (v5.1)
   LP NFT は ユーザー wallet ではなく BnzaExVault が保有
   詳細: Section 15.5

10. 🆕 Security: master private key は保持しない (v5.1)
    Agent key のみ envelope encryption で D1 / KMS-like に保管
    詳細: Section 21.5
```

---

## 5. 10,000 Bot Throughput Model

### 5.1 Required Throughput

```
10,000 bots / 5 minutes light-check
= 10,000 / 300 sec
= 33.3 bots/sec
= 2,000 bots/min
```

### 5.2 Bottleneck Analysis (v5.1 で Cloudflare 数値正確化)

```yaml
🚨 v5.1 注記: 以下は v5.0 検証で指摘された "Cloudflare 制約の数値間違い" を修正したもの。
                公式 docs と一致する数値を採用。
                (Cloudflare の plan 名は変わり得るので Phase 0 開始時に再確認推奨。
                 ⚠️ 確認必要 (zen task): Phase 0 着手時 Cloudflare 公式 docs で
                  最新値を確認し、表が古ければ更新)

1. Cloudflare Workers subrequest limit (1 invocation あたり):
   Free plan:        50 subrequests / invocation
   Paid (Standard):  10,000 subrequests / invocation (旧 v5.0 の "Paid 50" は誤り)
   1 hedge sync = 6-10 fetches (close + open + stop + reconcile, delta-only でも 4-8)
   → Paid plan であれば 1 invocation で複数 hedge をまとめても余裕がある
   → ただし HL rate limit が別の bottleneck なので fan-out は引き続き必要

2. D1 queries per Worker invocation:
   Free plan:        50 queries / invocation
   Paid:             1,000 queries / invocation
   1 invocation 内では 1 つの DO / Worker が複数 D1 query を発行可能
   → light-check 1 件で 5-10 query 程度
   → 100 bot を 1 invocation で sequential 処理しても上限内
   → ただし queue lag / retry risk を抑えるため fan-out は引き続き必要

3. Hyperliquid REST rate limit:
   Official hard limit: 1,200 weight/min/IP
   clearinghouseState weight: 2
   全 bot 5 分ごと poll = 4,000 weight/min
   → 上限の 3.3 倍超過、不可能
   → light-check で HL 触らない設計が必須

4. D1 制約:
   Free:     5 GB / DB
   Paid:     10 GB / DB
   Paid:     50,000 DB / account (理論上、実運用では 16-32 shard 想定)
   Single-threaded per DB (concurrent write は serialize)
   → sharding 必須 (Phase C の 16 shard 設計は維持)

5. Queue 制約:
   Per-queue throughput: 5,000 msg/sec
   Batch size: max 100
   Push consumer concurrency: 250
   Wall time: 15 min
   → fan-out には十分

6. Same-user mutation collision:
   1 user の HL nonce は単調増加
   並列 mutation で衝突
   → DO で per-user lock (lease-based、Section 11)

7. Execution time:
   Workers Paid CPU time: up to 5 min
   Queue consumer wall clock duration: 15 min
   Design target:
     1 hedge-sync should normally complete well below 30 sec
     to reduce queue lag and retry risk.
```

### 5.3 解決策: Shared cache + Light-check + Event-driven

```yaml
Light-check (HL 触らない):
  source:
    - D1 hot state (last_known_short_size)
    - MarketDataDO (sqrtPriceX96, currentTick)
    - Local TickMath (LP amount calculation)
  weight on HL: 0
  
Hedge-sync (mutation 候補のみ、delta-only):
  trigger conditions:
    # 🚨 v5.2.1 (P0-11): canonical RebalanceReason (§7.6) を参照。
    #   §7.3 / §13.4 / §17.1 と同一集合。独自の別名・別集合を作らない。
    - drift_threshold / drift_relative   (light-check で検出)
    - range_out / range_boundary_near
    - margin_warning                     (§18.4、margin_critical は SAFE_MODE)
    - funding_alert / time_fallback
    - manual_admin / recovery_reconcile  (deep audit mismatch / repair flow)
  excluded (hedge-sync の reason ではない):
    - stop_trigger_crossed_at marker set / near-stop
      → priority stop-audit/reconcile に route (Section 19.3 / §17.1)
  weight on HL: 4-8 weight/hedge (HL rate-limit weight、delta-only により減少)
    ※ CF subrequest 数とは別単位 (subrequest は §5.2-1 を参照、P1)
  
Deep audit (定期 reconcile):
  cadence: 6h normal / 1h high-risk
  full HL clearinghouseState fetch
  全 bot を distribute (時間分散)

Stop integrity audit:
  cadence: 6h normal
  trigger:
    - near-stop (price ±2% to stop)
    - 🆕 (v5.1) ETH price >= stop_price (priority audit、即時 enqueue)
    - 🆕 (v5.1) stop_trigger_crossed_at marker set

Forbidden at scale:
  ❌ 全 bot 5 分ごと clearinghouseState fetch
  ❌ 全 bot 5 分ごと openOrders fetch
  ❌ 全 bot 5 分ごと userFunding fetch
  ❌ (v5.1) 毎 hedge-sync で full close → full open
```

---

## 6. Position Amount Calculation

### 6.1 Fundamental Rule

```yaml
Hedge size MUST be based on current Uniswap V3 position amount.

❌ DO NOT USE (carter2099 のバグ):
  amount = depositedToken - withdrawnToken + collectedFees
  
✅ USE (正しい AMM 数式):
  liquidity (from NFT)
  tickLower (from NFT)
  tickUpper (from NFT)
  sqrtPriceX96 (from pool)
  currentTick (from pool)
```

### 6.2 Mathematical Foundation

```
S = sqrt(P) (現在価格の sqrt)
A = sqrt(P_lower) (range 下限の sqrt)
B = sqrt(P_upper) (range 上限の sqrt)
L = liquidity

Range states:
  current_tick < tick_lower:
    amount0 = L * (1/A - 1/B)
    amount1 = 0
  
  tick_lower <= current_tick < tick_upper:
    amount0 = L * (1/S - 1/B) = L * (B - S) / (S * B)
    amount1 = L * (S - A)
  
  current_tick >= tick_upper:
    amount0 = 0
    amount1 = L * (B - A)
```

### 6.3 Data Sources

```yaml
Static data (LP open / rebalance 時に保存):
  NonfungiblePositionManager.positions(tokenId):
    - token0
    - token1
    - fee
    - tickLower
    - tickUpper
    - liquidity (再 read 可)
  
  Pool:
    - poolAddress
    - token0
    - token1
    - fee
  
  ERC20:
    - token0_decimals
    - token1_decimals

Dynamic data (MarketDataDO から):
  Pool.slot0:
    - sqrtPriceX96
    - currentTick
    - blockNumber
    - updatedAt
```

### 6.4 PositionAmountCalculator Interface

```typescript
export type PositionAmountResult = {
  positionId: string;
  token0: Address;
  token1: Address;
  wethIndex: 0 | 1;
  currentTick: number;
  tickLower: number;
  tickUpper: number;
  sqrtPriceX96: string;
  amount0Raw: string;
  amount1Raw: string;
  amount0Human: string;
  amount1Human: string;
  lpEthAmount: string;
  rangeState: "below" | "in" | "above";
};

async function calculatePositionAmount(
  position: PositionStatic,
  market: PoolMarketState,
): Promise<PositionAmountResult> {
  const sqrtA = TickMath.getSqrtRatioAtTick(position.tickLower);
  const sqrtB = TickMath.getSqrtRatioAtTick(position.tickUpper);
  
  const [amount0Raw, amount1Raw] = LiquidityAmounts.getAmountsForLiquidity(
    BigInt(market.sqrtPriceX96),
    sqrtA,
    sqrtB,
    BigInt(position.liquidity),
  );
  
  const amount0Human = formatUnits(amount0Raw, position.token0Decimals);
  const amount1Human = formatUnits(amount1Raw, position.token1Decimals);
  const lpEthAmount = position.wethIndex === 0 ? amount0Human : amount1Human;
  
  const rangeState =
    market.currentTick < position.tickLower ? "below" :
    market.currentTick >= position.tickUpper ? "above" :
    "in";
  
  return {
    positionId: position.id,
    token0: position.token0,
    token1: position.token1,
    wethIndex: position.wethIndex,
    currentTick: market.currentTick,
    tickLower: position.tickLower,
    tickUpper: position.tickUpper,
    sqrtPriceX96: market.sqrtPriceX96,
    amount0Raw: amount0Raw.toString(),
    amount1Raw: amount1Raw.toString(),
    amount0Human,
    amount1Human,
    lpEthAmount,
    rangeState,
  };
}
```

### 6.5 Required Test Cases

```yaml
test_cases:
  - in range: amount0 > 0, amount1 > 0
  - below lower: amount0 = full, amount1 = 0
  - above upper: amount0 = 0, amount1 = full
  - WETH is token0
  - WETH is token1
  - negative tick (low ETH price)
  - zero liquidity
  - very small liquidity (precision)
  - decimals 18 (WETH) / 6 (USDC)
  - currentTick == tickLower (boundary)
  - currentTick == tickUpper (boundary)
  - currentTick == tickLower - 1 (just outside)
  - currentTick == tickUpper - 1 (just inside upper)
```

---

## 7. Hedge Math

### 7.1 Target Short Calculation

```typescript
// 概念式:
targetShortEth = lpEthAmount × hedgeRatio
```

🚨 v5.2.1 (P0-6): 実装では float を経由しない。`hedgeRatio` は bps 整数
(`target_ratio_bps`) として正規化し、ETH 量は BigDecimal で計算する。
正準ルールと正規化関数は **§7.6** を参照 (§13.4 / §15.3 / §17 と統一)。

### 7.2 Hedge Ratio Modes (Phase 1)

```yaml
Phase 1: Balanced 70% 固定 (シンプル化)

Phase 2 で追加検討 (Defer):
  Conservative: hedgeRatio = 0.50
  Balanced:     hedgeRatio = 0.70 (default)
  Aggressive:   disabled in Phase 1-2 (Phase 3 で検討)
```

### 7.3 Rebalance Trigger

```typescript
// 🚨 v5.2.1 (P0-6): BigDecimal で計算。Math.abs/JS float の生演算は禁止。
const deltaErrorEth = BigDecimal(targetShortEth).sub(lastKnownShortEth).abs();
const deltaErrorUsd = deltaErrorEth.mul(ethPriceUsd);
const lpValueUsd = BigDecimal(/* bot_runtime_state.lp_value_usd */);
const relativeDrift =
  BigDecimal(targetShortEth).gt(minSizeEth)
    ? deltaErrorEth.div(targetShortEth)
    : BigDecimal(0);

// 🚨 v5.2.1 (P0-11): rebalance reason は §7.6 canonical RebalanceReason に統一。
//   §5.3 / §13.4 / §17.1 はすべてこの集合を参照する (別名・別集合を作らない)。
const reasons: RebalanceReason[] = [];
// 🚨 v5.2.2 (P0-1): float 経由禁止。toNumber()/Math.max を BigDecimal 比較に統一。
//   定数は文字列で BigDecimal('...') として保持する。
const driftThreshold = BigDecimal.max(BigDecimal('25'), lpValueUsd.mul('0.03'));
if (deltaErrorUsd.gt(driftThreshold))                             reasons.push('drift_threshold');
if (relativeDrift.gt(BigDecimal('0.15')))                         reasons.push('drift_relative');
if (rangeOut)                                                     reasons.push('range_out');
if (rangeBoundaryNear)                                            reasons.push('range_boundary_near'); // 90% to upper/lower
if (marginStatus === 'warning')                                   reasons.push('margin_warning');
if (fundingAlert)                                                 reasons.push('funding_alert');       // 7d funding < -15% APR
if (timeFallback)                                                 reasons.push('time_fallback');       // 4h since last adjustment
const shouldRebalance = reasons.length > 0;

// stopTriggerCrossed / near-stop は normal hedge-sync の reason ではない。
// priority stop-audit/reconcile にのみ route する (Section 19.3 / §17.1)。
// margin_critical は §18.4.3 SAFE_MODE path に route (hedge-sync では emit しない)。
```

```yaml
relative drift:
  Use:
    abs(targetShort - actualShort) / targetShort
  If targetShort <= minSize:
    relativeDrift = 0
  Do not use:
    abs(targetShort - actualShort) / initialHedgeEth
```

### 7.4 Light-check vs Hedge-sync の判定差

```yaml
light-check:
  source: lastKnownShortEth from D1 (cached)
  purpose: drift 判定のみ
  HL fetch: なし
  
hedge-sync:
  source: actual HL position (fresh fetch)
  purpose: delta-only mutation 実行 (Section 17 参照)
  HL fetch: あり
  
success record:
  light-check では作成しない
  hedge-sync の post-order reconcile 後のみ作成
```

### 7.5 Hedge Budget Cap

```yaml
Hedge cost ≤ trailing 7d LP fee × 30%

Cold start (first 7d):
  budget = expected_LP_fee_APR × LP_capital × 7d × 30%
  例: 30% × $850 × (7/365) × 30% = $1.47/週

After 7d:
  budget = realized_trailing_7d_fee × 30%

超過時の挙動:
  - hedge 縮小
  - もしくは pause (Bot status = paused)
  - notification
```

### 7.6 Canonical: RebalanceReason enum + target_ratio bps 規定 (🆕 v5.2.1 / P0-6 + P0-11)

```typescript
// 🚨 CANONICAL rebalance reason enum (P0-11)
// §5.3 / §7.3 / §13.4 / §17.1 はすべてこの型のみを参照する。
// 別名・別集合 (trigger / cause / reason 等の独自表現) を新設しない。
type RebalanceReason =
  | 'drift_threshold'      // deltaErrorUsd > max($25, lpValueUsd * 3%)
  | 'drift_relative'       // |target - actual| / target > 0.15
  | 'range_out'            // rangeState != 'in'
  | 'range_boundary_near'  // price 90% to range upper/lower
  | 'margin_warning'       // hedge_legs.margin_status == 'warning' (§18.4)
  | 'margin_critical'      // §18.4.3 SAFE_MODE path 専用 (hedge-sync では emit しない)
  | 'funding_alert'        // 7d funding < -15% APR
  | 'time_fallback'        // 4h since last adjustment
  | 'manual_admin'         // admin invoked
  | 'recovery_reconcile';  // reconcile/repair flow

// 注: stop_trigger_crossed / near-stop は RebalanceReason ではない。
//     priority stop-audit に route する (§19.3 / §17.1)。
```

```typescript
// 🚨 CANONICAL target_ratio implementation rule (P0-6)
// D1 schema: hedge_legs.target_ratio TEXT '0.7' は表示・後方互換のため維持。
// 内部計算は必ず bps 整数 (bigint) に正規化し、float 経由を禁止する。
//   0.70 -> 7000n,  0.50 -> 5000n,  1.00 -> 10000n
function normalizeTargetRatioBps(targetRatioText: string): bigint {
  // 文字列 "0.70" を 10^4 スケールの整数へ。Number(x) * 10000 は禁止
  // (0.73 * 10000 = 7300.0000001 等の float 誤差で BigInt() throw のため)。
  const [intPart, fracRaw = ''] = targetRatioText.trim().split('.');
  const frac = (fracRaw + '0000').slice(0, 4);          // 4 桁 (bps) に padding/truncate
  const bps = BigInt(intPart) * 10000n + BigInt(frac);
  if (bps < 0n || bps > 10000n) throw new Error(`invalid target_ratio: ${targetRatioText}`);
  return bps;                                            // e.g. "0.70" -> 7000n
}

// 使用例 (§17.1 / §17.2 と一致):
//   const targetRatioBps = normalizeTargetRatioBps(data.hedge.targetRatio);
//   const targetShort = BigDecimal(amount.lpEthAmount).mul(targetRatioBps).div(10000);
```

```yaml
Phase 2 で hedge ratio mode を増やす場合 (Defer):
  - D1 に target_ratio_bps INTEGER を ALTER ADD (Section 13.0 原則: ADD のみ)
  - target_ratio TEXT は表示・後方互換のため残す (DROP/RENAME しない)
  - 全 normalization は normalizeTargetRatioBps() を経由 (float 経由を一切作らない)
```

---

## 8. Hyperliquid Adapter

### 8.1 Adapter Responsibility

HyperliquidAdapter は thin wrapper ではない。以下を所有する:

```yaml
責務:
  - HL rate limit reservation
  - Agent key decryption (Section 21.5 参照)
  - Order payload creation
  - Cloid generation (deterministic)
  - Nested error parsing
  - Order submission
  - Post-order reconciliation
  - Error classification
  - Safe logging (private key 等を sanitize、Section 21.5 参照)
  - 🆕 (v5.1) Delta-only adjustment helper (Section 17 参照)
```

### 8.2 Interface

```typescript
export interface HyperliquidAdapter {
  // Read operations
  getPositions(account: HlAccountRef): Promise<HlPosition[]>;
  getPosition(account: HlAccountRef, asset: string): Promise<HlPosition | null>;
  getOpenOrders(account: HlAccountRef): Promise<HlOpenOrder[]>;
  getUserFunding(account: HlAccountRef, startTime?: number, endTime?: number): Promise<HlFundingEntry[]>;
  getUserRateLimit(userAddress: Address): Promise<HlUserRateLimit>;
  getMarginSummary(account: HlAccountRef): Promise<HlMarginSummary>;  // 🆕 (v5.1)
  
  // Mutations (Section 17 で delta-only adjustment helper を追加)
  placeIocOrder(input: PlaceIocOrderInput): Promise<HlOrderResult>;
  openShortIoc(input: OpenShortInput): Promise<HlOrderResult>;
  closeShortReduceOnlyIoc(input: CloseShortInput): Promise<HlOrderResult | null>;
  adjustShortDelta(input: AdjustShortDeltaInput): Promise<HlOrderResult>;  // 🆕 (v5.1)
  placeReduceOnlyStopMarket(input: PlaceStopMarketInput): Promise<HlOrderResult>;
  cancelByOid(account: HlAccountRef, assetIndex: number, oid: number): Promise<void>;
  cancelByCloid(account: HlAccountRef, assetIndex: number, cloid: `0x${string}`): Promise<void>;
  updateLeverage(account: HlAccountRef, assetIndex: number, leverage: number, isCross: boolean): Promise<void>;
  updateIsolatedMargin(account: HlAccountRef, assetIndex: number, isBuy: boolean, ntli: number): Promise<void>;
  
  // Reconcile
  reconcilePosition(account: HlAccountRef, asset: string, expectedAbsSize: string): Promise<ReconcileResult>;
}
```

### 8.3 Account Reference

```typescript
export type HlAccountRef = {
  userAddress: Address;        // master account (NOT agent address)
  agentKeyId: string;          // encrypted approved agent key reference (Section 21.5)
  vaultAddress?: Address | null; // subaccount/vault if applicable
};
```

```yaml
🚨 Critical:
  - userAddress は master account の address
  - agent address を userAddress として使うと info query が空になる (HL 仕様)
  - vaultAddress を持つ場合、order 時に vaultAddress 指定で subaccount 操作
  - 🆕 (v5.1) BNZA は user の master private key を絶対に保管しない (Section 21.5)
  - 🆕 (v5.1) agent key は envelope encryption で D1 (hl_agent_keys) に保管
```

### 8.4 Native Stop Implementation

```typescript
await exchange.order({
  orders: [{
    a: ethAssetIndex,      // ETH の asset index
    b: true,                // buy = close short
    p: orderPx,             // fallback/aggressive price (slippage tolerance)
    s: size,                // close size
    r: true,                // reduce-only
    t: {
      trigger: {
        isMarket: true,
        triggerPx: stopTriggerPx,  // 🆕 (v5.1) liquidationPx ベースで動的計算 (Section 19)
        tpsl: "sl",                // Stop Loss
      },
    },
    c: cloid,               // deterministic client order id
  }],
  grouping: "na",
  vaultAddress: account.vaultAddress ?? undefined,
});
```

### 8.5 Cloid Generation (Idempotency)

```typescript
function makeCloid(input: {
  botId: string;
  attemptId: string;
  stage: "close" | "open" | "stop" | "cancel" | "adjust";  // 🆕 (v5.1) "adjust"
  version: number;
}): `0x${string}` {
  return first128BitsHex(
    keccak256(`bnza:${input.botId}:${input.attemptId}:${input.stage}:${input.version}`)
  );
}

Rules:
  same retry: same cloid
  payload changed: increment version
  duplicate cloid detected: do not blindly retry, reconcile first
```

### 8.6 Nested Error Parser

HL SDK は `status: "ok"` でも nested status に error を含むことがある。

```typescript
export function parseOrderResponse(result: any): HlOrderResult[] {
  const statuses = result?.response?.data?.statuses ?? [];
  const errors = statuses
    .map((s: any) => typeof s === "object" ? s.error : undefined)
    .filter(Boolean);
  
  if (errors.length > 0) {
    throw new HlOrderRejectedError(errors.join("; "), {
      errors,
      raw: sanitize(result),  // private key / nonce / secret を除外 (Section 21.5)
    });
  }
  
  return statuses.map(parseStatus);
}
```

---

## 9. Hyperliquid Rate Limiting

### 9.1 Rate Limit Policy

```yaml
HLGlobalRateLimitDO:
  official hard limit: 1,200 weight/min/IP
  BNZA operating budget: 700-800 weight/min (60% margin)
  excess handling: queue + delay

HLUserRateLimitDO:
  per-user/address action budget
  informed by userRateLimit endpoint
  
UserLockDO:
  same-user mutation serialization (lease-based、Section 11)
```

### 9.2 API Class & Usage

```yaml
info.position (clearinghouseState):
  weight: 2
  use only for:
    - mutation candidate (hedge-sync 直前)
    - post-order reconcile
    - deep audit
    - stop_trigger_crossed marker set 時の priority audit (v5.1)
  forbidden:
    - 全 bot 5 分ごと poll

info.history (funding/fills):
  low frequency only
  daily aggregation 推奨

info.marginSummary:
  - preflight margin check (Section 18.4)
  - margin warning / critical evaluation
  - SAFE_MODE 突入判定

exchange.order:
  mutation only
  rate limit reservation 必須
  delta-only adjustment が default (Section 17)

light-check:
  weight: 0 (HL 触らない)
```

### 9.3 Forbidden at Scale

```yaml
🚨 全 bot / 5 分ごとに以下を実行することは禁止:
  - clearinghouseState
  - openOrders
  - userFunding
  - userRateLimit
  - stop cancel/recreate (毎 light-check で recreate は浪費)
```

---

## 10. Queue Architecture

### 10.1 Queue List

```yaml
bot-scan:
  purpose: shard/window scan
  producer: cron worker (1 min)
  consumer: scan worker
  message: { shardId, cursor, limit, now }

light-check:
  purpose: 1 message = 1 bot light check
  producer: scan worker
  consumer: light-check worker
  message: { botId, userId, shardId }

hedge-sync:
  purpose: delta-only mutation candidate
  producer: light-check worker
  consumer: hedge-sync worker
  message: { botId, reasons: RebalanceReason[], expectedTargetSize, stateVersion }
    // 🚨 v5.2.3 (P1-B): RebalanceReason[] (canonical, §7.6) に統一。
    //   旧 reason (単数 string) は使わない。
    //   producer §17.1 が canonical 配列を送出するため一貫性確保。

reconcile:
  purpose: post-order reconciliation
  producer: hedge-sync worker
  consumer: reconcile worker
  message: { botId, attemptId, expectedAbsSize, hedgeLegId }

deep-audit:
  purpose: distributed full audit
  producer: cron worker (6h)
  consumer: deep-audit worker
  message: { botId, urgency }

price-near-stop-audit:
  purpose: stop/range boundary priority audit
  producer: light-check worker (price near stop / >= stop detected)
  consumer: stop-audit worker
  message: { botId, ethPriceUsd, stopPriceUsd, crossed }

notification:
  purpose: user/admin alert
  producer: any worker
  consumer: notification worker

metrics-rollup:
  purpose: hourly/daily aggregation
  producer: cron worker (hourly)
  consumer: rollup worker

dead-letter:
  purpose: poison messages
  producer: any queue
  consumer: admin review
```

### 10.2 Cron Worker

```typescript
// 🚨 v5.2.2 (P0-4): 共通 chunking helper。Cloudflare Queues の sendBatch は
//   1 回あたり最大 100 件。SPEC 内の全 producer はこの helper を経由する
//   (§10.2 cron / §10.3 scan / deep-audit / notification 等、例外なし)。
const SEND_BATCH_MAX = 100; // Cloudflare Queues hard limit per sendBatch

async function chunkSendBatch<T>(
  queue: Queue<T>,
  messages: { body: T }[],
): Promise<void> {
  for (let i = 0; i < messages.length; i += SEND_BATCH_MAX) {
    await queue.sendBatch(messages.slice(i, i + SEND_BATCH_MAX));
  }
}

export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    const shardWindows = dueShardWindows(Date.now());

    const messages = shardWindows.map((w) => ({
      body: {
        shardId: w.shardId,
        cursor: w.cursor,
        limit: 500,
        now: Date.now(),
      },
    }));

    await chunkSendBatch(env.BOT_SCAN_QUEUE, messages); // §10.2 共通 helper 経由
  },
};
```

### 10.3 Scan Worker

```typescript
async function scanDueBots(msg: BotScanMessage, env: Env) {
  const db = shardDb(env, msg.shardId);
  
  const bots = await db.prepare(`
    SELECT id, user_id, shard_id
    FROM bots
    WHERE status = 'active'
      AND next_light_check_at <= ?
    ORDER BY next_light_check_at
    LIMIT ?
  `).bind(nowIso(), msg.limit).all();
  
  // 🚨 v5.2.1 (P0-3) / v5.2.2 (P0-4): 共通 helper chunkSendBatch (§10.2 定義) を経由。
  //   scan limit (msg.limit, 例 500) のまま流しても helper が 100 件ずつ送る。
  const messages = bots.results.map((bot) => ({
    body: { botId: bot.id, userId: bot.user_id, shardId: bot.shard_id },
  }));
  await chunkSendBatch(env.LIGHT_CHECK_QUEUE, messages); // §10.2 共通 helper 経由

  await jitterNextCheckForBots(db, bots.results);
}
```

```yaml
🚨 v5.2.1 (P0-3) / v5.2.2 (P0-4) sendBatch chunking 規定:
  - scan の SELECT LIMIT (msg.limit) は 500 を維持してよい
  - ただし全ての *.sendBatch() は §10.2 の共通 helper chunkSendBatch()
    (SEND_BATCH_MAX=100) を必ず経由する。生 queue.sendBatch() の直接呼び出しは禁止
  - 適用範囲: cron worker (§10.2)、scan worker (§10.3)、deep-audit producer、
    notification producer、metrics-rollup producer など全 producer (例外なし)
  - §5.2-5 「Batch size: max 100」と整合
```

### 10.4 Jitter Strategy

```typescript
next_light_check_at = now + 5m + random(-45s, +45s)

理由:
  全 bot が 00:00, 00:05, ... に集中するのを防ぐ
  HL rate limit / D1 write spike 緩和
```

---

## 11. User-Level Concurrency Control (v5.1 で実装モデル変更)

### 11.1 Required Invariant

```yaml
同一 user の Hyperliquid mutation は同時実行しない。
理由:
  - HL nonce は単調増加
  - 並列 mutation で nonce 衝突
  - Rate limit 共有
```

### 11.2 Implementation: UserLockDO (Lease-based、v5.1 で書き直し)

```yaml
🚨 v5.1 修正:
  v5.0 の "function-callback 方式" (DO に work() を渡して実行) は
  Cloudflare Durable Object の RPC 設計上 直接実装できない
  (cross-DO で関数オブジェクトを渡せない)。
  v5.1 では lease-based lock pattern に変更。

設計方針:
  - DO は acquire / release / heartbeat の API のみ提供
  - 呼び出し側 (hedge-sync worker) は lease を取得し、自分で work を実行し、
    完了時に release を呼ぶ
  - Lease には TTL (90s) と holderToken (UUID) を持たせる
  - holderToken が一致しない release は noop / error
  - TTL 超過後は別 holder が acquire 可能 (stale lock 自動解除)
```

```typescript
// Durable Object: UserLockDO:userId
// Single-threaded per instance

export type LeaseAcquireInput = {
  holderToken: string;       // UUID v4 (caller-generated)
  ttlMs: number;             // recommended: 90_000
  idempotencyKey?: string;   // optional, for replay-safe behaviors
};

export type LeaseAcquireResult =
  | { acquired: true; expiresAt: number; idempotentReplay: false }
  | { acquired: false; currentHolderExpiresAt: number; reason: "held" }
  | { acquired: true; expiresAt: number; idempotentReplay: true; cachedResult?: unknown };

export class UserLockDO {
  // Acquire (or replay) a lease.
  async acquire(input: LeaseAcquireInput): Promise<LeaseAcquireResult> {
    const now = Date.now();

    // 1. Idempotency replay check (cached results from prior completed work)
    if (input.idempotencyKey) {
      const cached = await this.state.storage.get<{ result: unknown; recordedAt: number }>(
        `idem:${input.idempotencyKey}`,
      );
      if (cached) {
        return {
          acquired: true,
          expiresAt: now,             // already finished — no new lease needed
          idempotentReplay: true,
          cachedResult: cached.result,
        };
      }
    }

    // 2. Existing lease check
    const existing = await this.state.storage.get<{ holderToken: string; expiresAt: number }>("lease");
    if (existing && existing.expiresAt > now && existing.holderToken !== input.holderToken) {
      return { acquired: false, currentHolderExpiresAt: existing.expiresAt, reason: "held" };
    }

    // 3. Acquire (fresh or re-acquire by same holder)
    const expiresAt = now + input.ttlMs;
    await this.state.storage.put("lease", { holderToken: input.holderToken, expiresAt });
    return { acquired: true, expiresAt, idempotentReplay: false };
  }

  // Heartbeat to extend the lease while still holding it
  async heartbeat(input: { holderToken: string; ttlMs: number }): Promise<{ ok: boolean; expiresAt?: number }> {
    const existing = await this.state.storage.get<{ holderToken: string; expiresAt: number }>("lease");
    if (!existing || existing.holderToken !== input.holderToken) return { ok: false };
    const expiresAt = Date.now() + input.ttlMs;
    await this.state.storage.put("lease", { holderToken: input.holderToken, expiresAt });
    return { ok: true, expiresAt };
  }

  // Release. holderToken mismatch is a noop (stale releaser).
  // If idempotencyKey provided, cache the result for replay-safe behavior.
  async release(input: { holderToken: string; idempotencyKey?: string; result?: unknown }): Promise<{ released: boolean }> {
    const existing = await this.state.storage.get<{ holderToken: string; expiresAt: number }>("lease");
    if (!existing || existing.holderToken !== input.holderToken) {
      return { released: false };
    }
    await this.state.storage.delete("lease");
    if (input.idempotencyKey) {
      await this.state.storage.put(`idem:${input.idempotencyKey}`, {
        result: input.result ?? null,
        recordedAt: Date.now(),
      });
      // optional: alarm() で 24-72h 後に削除
    }
    return { released: true };
  }
}
```

### 11.3 Caller-side Usage (acquire / release pattern)

```typescript
import { randomUUID } from "node:crypto";

async function withUserLock<T>(args: {
  userId: string;
  ttlMs: number;
  idempotencyKey?: string;
  work: () => Promise<T>;
  env: Env;
}): Promise<T> {
  const stub = args.env.USER_LOCK_DO.get(args.env.USER_LOCK_DO.idFromName(args.userId));
  const holderToken = randomUUID();

  // 1. acquire
  const acq = await stub.fetch("/acquire", {
    method: "POST",
    body: JSON.stringify({ holderToken, ttlMs: args.ttlMs, idempotencyKey: args.idempotencyKey }),
  }).then(r => r.json() as Promise<LeaseAcquireResult>);

  if ("idempotentReplay" in acq && acq.idempotentReplay) {
    return acq.cachedResult as T;  // already executed, replay cached result
  }
  if (!acq.acquired) {
    throw new UserLockHeldError(args.userId, acq.currentHolderExpiresAt);
  }

  // 2. execute work in caller (NOT inside DO)
  let result: T;
  try {
    result = await args.work();
  } catch (e) {
    // best-effort release on failure (idempotency cache 不要)
    await stub.fetch("/release", {
      method: "POST",
      body: JSON.stringify({ holderToken }),
    });
    throw e;
  }

  // 3. release with optional idempotency caching
  await stub.fetch("/release", {
    method: "POST",
    body: JSON.stringify({ holderToken, idempotencyKey: args.idempotencyKey, result }),
  });

  return result;
}

// Usage at hedge-sync worker
const result = await withUserLock({
  env,
  userId: data.user.id,
  ttlMs: 90_000,
  idempotencyKey: `hedge-sync:${botId}:${stateVersion}`,
  work: async () => await hedgeSyncInner(data, reasons),
});
```

```yaml
🚨 注意点:
  - holderToken は caller が生成 (UUID v4)
  - lease 取得後、wall time 30s 内に完了しない場合は heartbeat() で延長
  - work() 中に Worker が timeout した場合、TTL 超過後に lease は自動解放
  - idempotencyKey で同 stateVersion の重複実行を防止
  - release() で result を cache しておくことで重複呼び出し時に replay 可能

lock holder crash 後の reconcile:
  - lease expires automatically
  - next worker must not assume previous operation succeeded
  - next worker must fetch and reconcile actual Hyperliquid state before any mutation
  - if state mismatch is detected, enter SAFE_MODE or run repair flow
```

---

## 12. D1 Architecture

### 12.1 Database Layout

```yaml
control_db (1):
  - users
  - bot_registry
  - shard_registry
  - billing
  - global config
  - hl_agent_keys (🆕 v5.1、Section 13.9 / 21.5 参照)

state_db_shard_xx (Phase 別):
  Phase A: 1 shard
  Phase B: 4 shards
  Phase C: 16 shards (Defer to Phase C)
  Phase D: 32 shards
  
  tables:
  - bots
  - positions
  - hedge_legs
  - bot_runtime_state
  - circuit_breakers
  - rebalance_attempts
  - hourly_bot_metrics
  - daily_bot_metrics
  - funding_daily_metrics (🆕 v5.1、Phase 別簡素化、Section 13.6)
  - queue_idempotency

archive (R2、Phase B+):
  - raw logs
  - old rebalance_attempts (>90d)
  - raw HL/RPC response samples
  - JSONL gzip by day/shard

observability (Analytics Engine、Phase B+):
  - queue lag
  - worker latency
  - error counters (low cardinality only)
  - RPC cache hit rate
  - HL token usage
  - D1 shard latency
  ❌ bot_id / user_id は dimension にしない (Section 14.3)
```

### 12.2 Shard Plan

```yaml
Phase A (1-100 bot):     1 shard
Phase B (1,000 bot):     4 shards
Phase C (10,000 bot):    16 shards (Defer until Phase B 安定)
Phase D (10,000+ bot):   32 shards (resharding)

shard_id = hash(bot_id) % shard_count

理由:
  - bot_id ベース (user_id ではない)
  - user の bot 数偏りに対応
  - User-level lock は別途 DO で実装 (lease-based)
```

---

## 13. D1 Schema (v5.1 で ALTER TABLE 追加 — DROP 禁止)

### 13.0 Schema 変更原則 (v5.1)

```yaml
🚨 原則:
  - v5.0 で定義した CREATE TABLE は維持
  - v5.1 で必要なフィールドは ALTER TABLE ADD COLUMN で追加
  - 既存カラムの DROP / RENAME は禁止 (実装後の migration 互換性)
  - 新規テーブル (hl_agent_keys, funding_daily_metrics) は CREATE TABLE で追加
  - PRIMARY KEY 変更が必要な場合 (circuit_breakers) は新テーブル + view migration とする
    (本仕様書では DDL 例を Section 13.7 に記載)
```

### 13.1 Control DB

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  wallet_address TEXT,
  hl_user_address TEXT,
  hl_agent_key_id TEXT,         -- references hl_agent_keys.id (v5.1)
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE bot_registry (
  bot_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  shard_id INTEGER NOT NULL,
  status TEXT NOT NULL,          -- active, paused, closing, closed, safe_mode, error
  chain TEXT NOT NULL,           -- 'base' | 'optimism'
  bot_type TEXT NOT NULL,        -- 'lp' | 'ex'
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_bot_registry_user ON bot_registry(user_id);
CREATE INDEX idx_bot_registry_shard_status ON bot_registry(shard_id, status);

CREATE TABLE shard_registry (
  shard_id INTEGER PRIMARY KEY,
  db_binding_name TEXT NOT NULL,
  status TEXT NOT NULL,           -- active, draining, readonly
  bot_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
```

### 13.2 State Shard DB

```sql
CREATE TABLE bots (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  status TEXT NOT NULL,           -- 粗粒度: active, paused, closing, closed, safe_mode, error
  -- 🆕 v5.2.1 (P0-8): 細粒度 lifecycle。§16.1/§16.6 の state machine を表現。
  --   status は粗粒度のまま、状態機械の遷移は lifecycle_state で追跡する。
  --   値: idle | preflight | lp_opening | lp_opened | hedge_pre_open |
  --       hedge_post_confirmed | stop_placing | stop_verified | active |
  --       lp_rebalancing | lp_closing | closed | safe_mode | error
  lifecycle_state TEXT NOT NULL DEFAULT 'idle',
  chain TEXT NOT NULL,
  wallet_address TEXT NOT NULL,
  position_id TEXT NOT NULL,
  hedge_leg_id TEXT NOT NULL,
  next_light_check_at TEXT NOT NULL,
  next_deep_audit_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
-- v5.2.1 ALTER (既存環境向け、新規 DB は上記 CREATE TABLE で OK)
-- ALTER TABLE bots ADD COLUMN lifecycle_state TEXT NOT NULL DEFAULT 'idle';
CREATE INDEX idx_bots_due_light ON bots(status, next_light_check_at);
CREATE INDEX idx_bots_due_audit ON bots(status, next_deep_audit_at);
CREATE INDEX idx_bots_user ON bots(user_id);
CREATE INDEX idx_bots_lifecycle ON bots(lifecycle_state);

CREATE TABLE positions (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL UNIQUE,
  token_id TEXT NOT NULL,         -- Uniswap V3 NFT token id
  pool_address TEXT NOT NULL,
  token0 TEXT NOT NULL,
  token1 TEXT NOT NULL,
  fee INTEGER NOT NULL,
  tick_lower INTEGER NOT NULL,
  tick_upper INTEGER NOT NULL,
  liquidity TEXT NOT NULL,        -- BigInt string
  weth_index INTEGER NOT NULL,    -- 0 or 1
  token0_decimals INTEGER NOT NULL,
  token1_decimals INTEGER NOT NULL,
  -- 🆕 v5.1: LP NFT custody (Section 15.5 参照)
  custodian TEXT NOT NULL DEFAULT 'vault',   -- 'vault' | 'user' (EXBOT Phase A は 'vault' 固定、v5.2.1)
  custodian_address TEXT NOT NULL,           -- BnzaExVault address (chain ごと)
  updated_at TEXT NOT NULL
);

-- v5.1 ALTER (既存環境向け、新規 DB は上記 CREATE TABLE で OK)
-- ALTER TABLE positions ADD COLUMN custodian TEXT NOT NULL DEFAULT 'vault';
-- ALTER TABLE positions ADD COLUMN custodian_address TEXT NOT NULL DEFAULT '';

CREATE TABLE hedge_legs (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL UNIQUE,
  hl_asset TEXT NOT NULL,         -- 'ETH'
  target_ratio TEXT NOT NULL,     -- '0.7' (Phase 1 fixed)
  tolerance_ratio TEXT NOT NULL,  -- '0.10' or similar
  leverage INTEGER NOT NULL DEFAULT 3,
  margin_mode TEXT NOT NULL DEFAULT 'isolated',  -- 🚨 isolated 必須
  hl_account_address TEXT,        -- subaccount address if applicable
  stop_order_id TEXT,
  stop_cloid TEXT,
  stop_price TEXT,
  stop_size TEXT,
  stop_last_verified_at TEXT,
  circuit_state TEXT NOT NULL DEFAULT 'closed',  -- closed | open | half_open
  -- 🆕 v5.1: Stop / Liquidation model 再定義 (Section 19)
  entry_price TEXT,
  liquidation_price TEXT,
  effective_leverage TEXT,         -- notional / isolatedMargin ベース
  isolated_margin_usd TEXT,
  stop_distance_pct TEXT,          -- (stop_price - entry_price) / entry_price
  -- 🆕 v5.1: Stop trigger 後の stale state 対策 (Section 19)
  last_stop_audit_at TEXT,
  stop_trigger_crossed_at TEXT,    -- ETH price >= stop_price で観測時の timestamp
  -- 🆕 v5.1: Margin status (Section 18.4)
  margin_status TEXT NOT NULL DEFAULT 'ok',  -- ok | warning | critical | safe_mode
  margin_balance_usd TEXT,
  margin_required_usd TEXT,
  updated_at TEXT NOT NULL
);

-- v5.1 ALTER (既存環境向け)
-- ALTER TABLE hedge_legs ADD COLUMN entry_price TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN liquidation_price TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN effective_leverage TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN isolated_margin_usd TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN stop_distance_pct TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN last_stop_audit_at TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN stop_trigger_crossed_at TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN margin_status TEXT NOT NULL DEFAULT 'ok';
-- ALTER TABLE hedge_legs ADD COLUMN margin_balance_usd TEXT;
-- ALTER TABLE hedge_legs ADD COLUMN margin_required_usd TEXT;
```

### 13.3 Runtime State (Hot)

```sql
CREATE TABLE bot_runtime_state (
  bot_id TEXT PRIMARY KEY,
  state_version INTEGER NOT NULL DEFAULT 0,
  current_tick INTEGER,
  sqrt_price_x96 TEXT,
  lp_amount0_raw TEXT,
  lp_amount1_raw TEXT,
  lp_eth_amount TEXT,             -- WETH 量 (USDC ペアの場合)
  -- 🆕 v5.1: drift 計算に必要 (Section 7.3)
  eth_price_usd TEXT,
  lp_value_usd TEXT,
  target_short_size TEXT,
  last_known_hl_short_size TEXT,
  last_hl_reconcile_at TEXT,
  last_light_check_at TEXT,
  last_deep_audit_at TEXT,
  last_rebalance_attempt_id TEXT,
  health_status TEXT NOT NULL DEFAULT 'ok',  -- ok | warning | critical
  updated_at TEXT NOT NULL
);

-- v5.1 ALTER
-- ALTER TABLE bot_runtime_state ADD COLUMN eth_price_usd TEXT;
-- ALTER TABLE bot_runtime_state ADD COLUMN lp_value_usd TEXT;
```

### 13.4 Rebalance Attempts

```sql
CREATE TABLE rebalance_attempts (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  -- 🆕 v5.1: leg / asset / version の追跡
  hedge_leg_id TEXT NOT NULL,
  asset TEXT NOT NULL,            -- 'ETH'
  state_version INTEGER NOT NULL, -- bot_runtime_state.state_version 一致確認用
  status TEXT NOT NULL,           -- success, failed, partial, skipped
  reason TEXT,                    -- 🚨 v5.2.1 (P0-11): canonical RebalanceReason (§7.6).
                                  --   値: drift_threshold | drift_relative | range_out |
                                  --       range_boundary_near | margin_warning | margin_critical |
                                  --       funding_alert | time_fallback | manual_admin |
                                  --       recovery_reconcile
                                  --   reasons[] 複数時は CSV (canonical 値のみ、別名禁止)
  old_short_size TEXT,
  target_short_size TEXT,
  reconciled_short_size TEXT,     -- 🚨 reconcile 後の actual size
  -- 🆕 v5.1: delta-only adjustment 用 cloid
  adjust_cloid TEXT,              -- delta-only adjust の cloid
  close_cloid TEXT,               -- target=0 / emergency / manual reset 時のみ
  open_cloid TEXT,                -- 同上
  stop_cloid TEXT,
  close_order_id TEXT,
  open_order_id TEXT,
  adjust_order_id TEXT,
  error_code TEXT,
  error_message TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT
);
CREATE INDEX idx_attempts_bot_time ON rebalance_attempts(bot_id, started_at);
CREATE INDEX idx_attempts_status_time ON rebalance_attempts(status, started_at);
CREATE INDEX idx_attempts_leg ON rebalance_attempts(hedge_leg_id, started_at);

-- v5.1 ALTER
-- ALTER TABLE rebalance_attempts ADD COLUMN hedge_leg_id TEXT NOT NULL DEFAULT '';
-- ALTER TABLE rebalance_attempts ADD COLUMN asset TEXT NOT NULL DEFAULT 'ETH';
-- ALTER TABLE rebalance_attempts ADD COLUMN state_version INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE rebalance_attempts ADD COLUMN adjust_cloid TEXT;
-- ALTER TABLE rebalance_attempts ADD COLUMN adjust_order_id TEXT;
-- CREATE INDEX idx_attempts_leg ON rebalance_attempts(hedge_leg_id, started_at);
```

### 13.5 Metrics

```sql
CREATE TABLE hourly_bot_metrics (
  bot_id TEXT NOT NULL,
  bucket_hour TEXT NOT NULL,
  checks_count INTEGER NOT NULL,
  rebalance_count INTEGER NOT NULL,
  failure_count INTEGER NOT NULL,
  max_abs_drift_bps INTEGER,
  last_lp_eth_amount TEXT,
  funding_received_usd TEXT,
  funding_paid_usd TEXT,
  hedge_pnl_usd TEXT,
  PRIMARY KEY (bot_id, bucket_hour)
);

CREATE TABLE daily_bot_metrics (
  bot_id TEXT NOT NULL,
  bucket_day TEXT NOT NULL,
  checks_count INTEGER NOT NULL,
  rebalance_count INTEGER NOT NULL,
  failure_count INTEGER NOT NULL,
  max_abs_drift_bps INTEGER,
  total_lp_fee_usd TEXT,
  total_il_realized_usd TEXT,
  total_funding_usd TEXT,
  total_hedge_cost_usd TEXT,
  net_pnl_usd TEXT,
  PRIMARY KEY (bot_id, bucket_day)
);
```

### 13.6 Funding Ledger (v5.1 で Phase 別簡素化)

```yaml
🚨 v5.1 修正:
  v5.0 の funding_history (per-record raw entry) は Phase A では over-engineered。
  Phase 別に保管粒度を変える。

Phase A (10-100 bot):
  raw funding events を D1 に保存しない
  → daily aggregate のみ保管 (funding_daily_metrics)

Phase B (1,000 bot):
  + 24h / 7d / 30d realized aggregate (rolling) を保管

Phase C (10,000 bot):
  + raw funding events を R2 に archive (JSONL gzip)
  D1 には引き続き daily / rolling aggregate のみ
```

```sql
-- 🆕 v5.1 (Phase A から使用)
CREATE TABLE funding_daily_metrics (
  bot_id TEXT NOT NULL,
  bucket_day TEXT NOT NULL,
  funding_paid_usd TEXT NOT NULL DEFAULT '0',
  funding_received_usd TEXT NOT NULL DEFAULT '0',
  funding_net_usd TEXT NOT NULL DEFAULT '0',
  events_count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (bot_id, bucket_day)
);
CREATE INDEX idx_funding_daily_day ON funding_daily_metrics(bucket_day);

-- 🆕 v5.1 (Phase B+)
CREATE TABLE funding_rolling_metrics (
  bot_id TEXT PRIMARY KEY,
  funding_24h_usd TEXT,
  funding_7d_usd TEXT,
  funding_30d_usd TEXT,
  funding_apr_24h_pct TEXT,
  funding_apr_7d_pct TEXT,
  funding_apr_30d_pct TEXT,
  computed_at TEXT NOT NULL
);

-- v5.0 の funding_history (per-record) は廃止予定
-- 既存 LP Bot の funding_history は維持 (互換)、Ex Bot では使わない
-- DROP しないが INSERT もしない。Phase B 移行時に archive (R2)。
```

### 13.7 Circuit Breaker (v5.1 で PK 変更)

```yaml
🚨 v5.1 修正:
  v5.0 では PRIMARY KEY (id TEXT) で bot_id, asset を別カラムにしていたが、
  hedge_leg 単位で circuit を管理するのが正しい (1 leg = 1 circuit)。
  PK を hedge_leg_id ベースに変更する。

DDL 表現:
  既存 DB が既にあれば DROP できないので、
  view ベースの migration を行う:
    1. 新テーブル circuit_breakers_v2 を hedge_leg_id PK で作成
    2. 既存 circuit_breakers から copy
    3. 既存テーブル名を _legacy にリネーム (DROP しない)
    4. v2 を circuit_breakers にリネーム
  
  ⚠️ 確認必要 (zen task): Phase 0 開始時に migration script を別途用意。
                          本仕様書では新 schema のみ記載。
```

```sql
-- 🆕 v5.1 (新規環境はこれを使う)
CREATE TABLE circuit_breakers (
  hedge_leg_id TEXT PRIMARY KEY,        -- 🆕 v5.1: 1 leg = 1 circuit
  bot_id TEXT NOT NULL,
  asset TEXT NOT NULL,
  state TEXT NOT NULL,            -- closed | open | half_open
  opened_at TEXT,
  reason TEXT,
  failure_count INTEGER NOT NULL DEFAULT 0,
  last_failure_at TEXT,
  reset_at TEXT,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_breaker_bot ON circuit_breakers(bot_id);
```

### 13.8 Queue Idempotency

```sql
CREATE TABLE queue_idempotency (
  key TEXT PRIMARY KEY,
  bot_id TEXT,
  result_json TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX idx_idempotency_expires ON queue_idempotency(expires_at);
```

### 13.9 HL Agent Keys (🆕 v5.1、Section 21.5 参照)

```sql
-- control_db に新規追加
-- 🚨 v5.2.2 (P0-2 / Option A): envelope fields を独立 BLOB column 化。
--   §21.5.2 / §21.5.2.1 runbook と完全同期 (1 agent key row = 1 DEK)。
CREATE TABLE hl_agent_keys (
  id TEXT PRIMARY KEY,                  -- agent_key_id (UUID)
  user_id TEXT NOT NULL,
  hl_user_address TEXT NOT NULL,        -- master account
  agent_address TEXT NOT NULL,          -- agent (signing) address
  encrypted_secret BLOB NOT NULL,       -- agent key, AES-256-GCM, per-row DEK で暗号化
  secret_iv BLOB NOT NULL,              -- 🆕 v5.2.2: IV used for encrypted_secret
  secret_auth_tag BLOB NOT NULL,        -- 🆕 v5.2.2: AES-GCM auth tag for encrypted_secret
  wrapped_dek BLOB NOT NULL,            -- 🆕 v5.2.2: DEK, Master Key (Secrets Store) で wrap
  dek_iv BLOB NOT NULL,                 -- 🆕 v5.2.2: IV used for wrapped_dek
  encryption_key_version INTEGER NOT NULL,  -- Master Key version (rotation chain)
  approval_status TEXT NOT NULL,        -- 'pending' | 'approved' | 'revoked' | 'expired'
  approved_at TEXT,
  expires_at TEXT,                      -- HL agent key expiry
  rotated_from TEXT,                    -- previous hl_agent_keys.id (rotation chain)
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_hl_agent_keys_user ON hl_agent_keys(user_id);
CREATE INDEX idx_hl_agent_keys_status ON hl_agent_keys(approval_status, expires_at);

-- v5.2.2 ALTER (既存環境向け、新規 DB は上記 CREATE TABLE で OK)
-- ALTER TABLE hl_agent_keys ADD COLUMN secret_iv BLOB NOT NULL DEFAULT x'';
-- ALTER TABLE hl_agent_keys ADD COLUMN secret_auth_tag BLOB NOT NULL DEFAULT x'';
-- ALTER TABLE hl_agent_keys ADD COLUMN wrapped_dek BLOB NOT NULL DEFAULT x'';
-- ALTER TABLE hl_agent_keys ADD COLUMN dek_iv BLOB NOT NULL DEFAULT x'';
```

```yaml
🚨 取り扱い (v5.2.2 / P0-2 で §21.5.2 / §21.5.2.1 と完全同期):
  - 1 agent key row = 1 DEK。DEK は Master Key (Cloudflare Secrets Store)
    で wrap し wrapped_dek に保管。agent key は per-row DEK で暗号化し
    encrypted_secret に保管 (AES-256-GCM, secret_iv / secret_auth_tag)
  - DB dump にも生 secret / 生 DEK は出ない
  - 復号は OPERATOR Worker 内のみ。復号 flow は §21.5.2 を参照
    (Master Key で wrapped_dek を unwrap → DEK で encrypted_secret 復号)
  - 復号後の plain DEK / plain agent key は関数 scope のみ、使用後即破棄
  - rotation 時は新行を insert (新 DEK + 新 wrap)、旧行は status='revoked'
  - approval_status = 'pending' の key は使わない
```

---

## 14. Retention Policy

### 14.1 Keep in D1

```yaml
bot_runtime_state:
  permanent, 1 row per bot

rebalance_attempts:
  90 days

hourly_bot_metrics:
  30 days

daily_bot_metrics:
  365 days

queue_idempotency:
  24-72h

funding_daily_metrics (v5.1):
  365 days (Phase A)

funding_rolling_metrics (v5.1):
  permanent, 1 row per bot (Phase B+)

circuit_breakers:
  permanent (1 row per hedge_leg)

hl_agent_keys (v5.1):
  permanent (audit trail として revoked 後も残す)
```

### 14.2 Forbidden in D1

```yaml
🚨 D1 に保存しない:
  - 5-minute snapshot for all bots
  - raw RPC responses
  - raw HL responses
  - high-cardinality logs
  - full execution traces
  - 🆕 (v5.1) raw funding events (Phase A は funding_daily_metrics のみ、
                                   Phase C+ は R2 へ)

理由:
  10,000 bot × 288 checks/day = 2.88M rows/day
  30 日: 86.4M rows
  → D1 制約 (10GB / 1 DB) 超過
```

### 14.3 Archive (v5.1 で Analytics Engine 警告強化)

```yaml
R2 (Phase B+):
  - raw logs (JSONL gzip by day/shard)
  - rebalance_attempts > 90d
  - HL/RPC response samples (sanitized — Section 21.5)
  - debug traces
  - raw funding events (Phase C+)

Analytics Engine (Phase B+):
  Allowed dimensions (low cardinality):
    - shard_id
    - chain
    - queue_name
    - error_code (enumerated)
    - phase / env
    - hl_action_type ('order' | 'cancel' | 'info')
  
  🚨 Forbidden dimensions (high cardinality):
    ❌ bot_id
    ❌ user_id
    ❌ hl_user_address
    ❌ position_id
    ❌ tx_hash
    ❌ cloid
    ❌ order_id
  
  理由:
    Analytics Engine は high-cardinality dimension で cost / latency が爆発する。
    Per-bot / per-user metrics は D1 (hourly_bot_metrics / daily_bot_metrics)
    の aggregate でしか保管しない。
  
  Per-bot 詳細が必要な場合:
    - D1 aggregate (hourly / daily)
    - R2 raw logs (offline analysis)
```

---

## 15. MarketData Cache

### 15.1 Pool State Cache

```yaml
Durable Object: MarketDataDO
key format: chain:poolAddress

stored:
  - sqrtPriceX96
  - currentTick
  - blockNumber
  - updatedAt
  - ethPriceUsd (derived)
```

### 15.2 Refresh Policy

```yaml
maxAge:
  normal volatility:    15-30 sec
  high volatility:      5-10 sec
  fallback:             RPC provider failover (Phase C で multi-RPC、Phase A は single)

refresh trigger:
  - on read if updatedAt > maxAge
  - background refresh (proactive) for high-traffic pools
  - manual on rebalance attempt
```

### 15.3 Light-check Usage (MarketDataDO の利用例)

```yaml
🚨 v5.2.1 修正 (P0-2 / canonical 一本化):
  light-check の正準 (canonical) 実装は **Section 17.1** に一本化した。
  本 §15.3 は MarketDataDO の "利用例" 説明に縮約し、pseudocode 本体は
  Section 17.1 を参照する (二重定義による乖離・NN#14 無効化バグの再発防止)。

  旧 §15.3 pseudocode に存在した以下の問題は §17.1 canonical 版で解消済み:
    - stop_trigger_crossed marker を無条件に再 mark していた
      → §17.1 では guarded: 既に set 済みなら stop_trigger_crossed_at を
        上書きしない。これにより §18.3 / NN#14 の
        "marker stuck > 30 min → SAFE_MODE" が正しく発火する
        (timestamp が毎 light-check で now に巻き戻らない)。
    - targetShort を float (`*`) で算出していた
      → §17.1 では BigDecimal、targetRatio は bps 整数化 (§7.6 / P0-6)。

MarketDataDO がこの flow で果たす役割 (利用例としての要点):
  - light-check は MarketDataDO の shared pool cache
    (sqrtPriceX96 / currentTick / ethPriceUsd) のみを読む
  - HL は一切 fetch しない (weight 0、NN#3)
  - calculatePositionAmount は §6.4 に従い純関数 (HL/RPC fetch なし)
  - 実 flow (stop-crossed guarded 検出 / drift trigger / hot state update /
    hedge-sync enqueue) は Section 17.1 を唯一の規範とする
```

---

## 15.5 LP NFT Custody / Control Model (🆕 v5.1)

### 15.5.1 設計方針 (v5.2.1: Option C 確定)

```yaml
🚨 v5.1 で新規追加 / v5.2.1 で Option C 確定:
  v5.0 では LP NFT の所有者が暗黙 (≒ user wallet 想定) だったが、
  EXBOT では LP NFT を専用 custody contract BnzaExVault が保有する。

🚨 v5.2.1 確定 (zen 決定 — Option C):
  EXBOT は EXBOT 専用 Solidity contract suite (BnzaExVault) を新規開発・
  新規デプロイする。現行 BNZA POOL の BnzaRouter v2.2.1 / BnzaLpBot v1.1 は
  改修しない (責務分離。詳細は Section 3.4 を参照)。
  - EXBOT custody = BnzaExVault (新規、未デプロイ、本 SPEC §15.5.6 で仕様規定)
  - BNZA POOL custody = BnzaRouter v2.2.1 (現行、Optimism+Base 稼働中、変更なし)

理由:
  - rebalance / close を Operator から trustless かつ atomic に呼べる
  - user が誤って NFT を transfer したり approve を revoke するリスクを排除
  - subaccount + LP NFT を一括で BNZA 管理化に置くことで failure mode を集約
  - EXBOT と POOL を完全に別商品・別 contract として隔離し、
    POOL の WL ローンチ後運用安定性に EXBOT 開発が一切影響しない

Phase A の custody 方針:
  custodian: 'vault' (Phase A 固定、EXBOT は BnzaExVault custody)
  custodian_address: BnzaExVault address (chain ごと、Optimism + Base)
  不変条件: NFPM.ownerOf(tokenId) == BnzaExVault address
  user 持ち分の表現: BnzaExVault 内部 ledger (mapping(user => positionId))
                     もしくは BnzaExVault が発行する receipt token
  
  既存 BNZA-LPBOT (BnzaLpBot.sol) / BnzaRouter v2.2.1 とは
  contract レベルで完全非干渉 (Section 15.5.4 / Section 3.4)。
```

### 15.5.2 Authority Matrix

```yaml
| Role            | Read  | Mint  | Increase | Decrease | Collect | Burn  | Transfer |
|-----------------|-------|-------|----------|----------|---------|-------|----------|
| Operator (BNZA) |  ✅   |  ✅   |   ✅     |   ✅     |   ✅    |  ✅   |    ❌    |
| User            |  ✅   |  ❌   |   ❌     |   ❌     |   ❌    |  ❌   |    ❌    |
| Emergency Admin |  ✅   |  ❌   |   ❌     |   ✅(*)  |   ✅    |  ❌   |    ✅(*) |
| External        |  ✅   |  ❌   |   ❌     |   ❌     |   ❌    |  ❌   |    ❌    |

(*) Emergency Admin は multi-sig 経由のみ。BnzaExVault の emergency path 仕様は本 SPEC §15.5.6 で規定。

Operator authority:
  - LP rebalance (Decrease + Increase)
  - LP close (Decrease 100% + Burn)
  - Fee collect (event-based、Section 21)
  - Bot state machine 駆動 (Section 16)

User rights (Phase A):
  - Bot 起動 / 停止 (start / pause / close リクエスト)
  - Position 確認 (read-only)
  - Withdraw リクエスト (LP close → USDC 返却までの flow を triggers)
  - HL agent key approval (Section 21.5)

User does NOT have:
  - LP NFT direct transfer
  - LP NFT direct burn
  - HL master private key (BNZA に保管されない、Section 21.5)

Emergency permissions:
  - LP forced close (multi-sig + admin)
  - LP NFT recovery (in case of operator failure)
  - User funds rescue path
```

### 15.5.3 LP Operation Flow と権限関係

```yaml
LP Open (Bot 起動時) — 🆕 v5.2.2 (P0-3-2): 関数名を §15.5.6 ABI に統一:
  1. user → POOL UI: deposit USDC + start Ex Bot
  2. UI → Operator → BnzaExVault.vaultMint(user, MintParams)
  3. BnzaExVault.vaultMint: USDC → swap → NFPM.mint (Uniswap V3)
  4. BnzaExVault: LP NFT を BnzaExVault 自身が保有 (returns tokenId)
  5. BnzaExVault: positionOwner[tokenId] = user に記録
  6. Operator: positions テーブルに custodian='vault', custodian_address=BnzaExVault,
     token_id=返却 tokenId を記録

LP Rebalance (Operator 駆動):
  1. Operator が rebalance 必要を判断 (range out 等)
  2. Operator → BnzaExVault.vaultRebalance(tokenId, newTickLower, newTickUpper, slippageBps)
  3. BnzaExVault (msg.sender == authorizedOperator check) なら実行
  4. BnzaExVault.vaultRebalance: NFPM decreaseLiquidity 100% → collect → swap
     → NFPM.mint new range (旧 tokenId burn) → returns newTokenId
  5. Operator: D1 positions row を新 tickLower/tickUpper + token_id=newTokenId で更新

LP Close (Operator or User initiated):
  Section 16.4 (LP close authority) と Section 16.6 (LP_CLOSING) を参照
```

### 15.5.4 既存 BNZA POOL contract との非干渉 (v5.2.1: Option C)

```yaml
🚨 v5.2.1 確定: EXBOT は新規 contract suite (BnzaExVault) を新規開発する。
  現行 BNZA POOL の contract は一切改修しない (Option C / Section 3.4)。

既存 BNZA POOL contract (変更なし・参照のみ):
  ~/Desktop/BNZA-LPBOT/src/BnzaLpBot.sol      -- POOL 用、改修しない
  ~/Desktop/BNZA-LPBOT/docs/SPEC.md           -- 設計パターン参考のみ
  ~/Desktop/BNZA-ROUTER/src/BnzaRouter.sol    -- POOL 用 v2.2.1、改修しない
  ~/Desktop/BNZA-ROUTER/docs/SPEC.md          -- 設計パターン参考のみ
  ~/Desktop/BNZA-ROUTER/docs/SPEC_V2.md       -- 設計パターン参考のみ
  ~/Desktop/bnza-contracts/src/BNZAToken.sol  -- BuyBack&Burn 対象、共有

新規 EXBOT contract (本 SPEC で仕様規定):
  BnzaExVault.sol           -- 新規開発、§15.5.6 で API/不変条件を規定
  デプロイ予定: Optimism + Base (BnzaRouter v2.2.1 と同一 chain、別 address)

非干渉の保証 (Phase 0 開始前に zen 確認):
  1. BnzaExVault は BnzaRouter v2.2.1 / BnzaLpBot v1.1 の
     storage / function / authority を一切呼ばない・変更しない
  2. 共有するのは BNZAToken (BuyBack&Burn 先) のみで、これは read/transfer のみ
  3. NFPM (Uniswap V3 NonfungiblePositionManager) は共有インフラだが
     position は tokenId 単位で独立、衝突しない
  4. Operator key / multi-sig は EXBOT 専用に分離 (§21.5.5)
  5. POOL の WL ローンチ後運用 (cron / relayer / Stage 3 rollback 状況) に
     EXBOT 開発・デプロイが影響しないこと

設計パターンの再利用方針:
  既存 BnzaRouter/BnzaLpBot の custody パターン (internal ledger / operator
  authority / emergency multi-sig) は BnzaExVault 設計の参考にする。
  ただし code 共有はせず、EXBOT 専用に新規実装する (責務分離)。
```

### 15.5.5 Failure Modes

```yaml
Operator が compromise された場合:
  - Operator key の rotation
  - Emergency Admin (multi-sig) で全 Bot を SAFE_MODE / forced close

BnzaExVault contract bug:
  - Pause 機能 (BnzaExVault 自身に implement)
  - Emergency Admin による LP NFT recovery
  - User funds への迅速な return path

User が abuse 試行:
  - User は BnzaExVault の public function 以外を呼べない
  - Bot start/stop/withdraw 経由でしか LP に触れない

LP NFT が unexpected transfer された場合:
  - Operator は次回 light-check で NFPM.ownerOf 異常を検出
  - bot.status を 'error' に遷移、admin alert
  - User funds は LP value 分まで保護される設計
```

### 15.5.6 BnzaExVault Solidity 仕様 (🆕 v5.2.1、新規 contract)

```yaml
🚨 BnzaExVault は EXBOT 専用の新規 Solidity contract。
  本 SPEC が EXBOT 全体仕様書であるため、Solidity 側 API / 不変条件も
  ここで一元管理する (別 SPEC に分離しない、整合性管理のため)。
  デプロイ: Optimism + Base (BnzaRouter v2.2.1 とは別 contract / 別 address)。
```

```solidity
// 不変条件 (Invariants — 常に保持):
//  INV-1: 全ての管理下 tokenId について NFPM.ownerOf(tokenId) == address(this)
//  INV-2: positionOwner[tokenId] は単一 user を指す (1 LP NFT = 1 user)
//  INV-3: USDC は同一 tx 内でしか contract に滞留しない (close 時 1 tx で return)
//  INV-4: operator 関数は authorizedOperator のみ、emergency は multiSig のみ
//  INV-5: BnzaRouter v2.2.1 / BnzaLpBot v1.1 の storage/function を呼ばない

interface IBnzaExVault {
  // --- Operator authority (authorizedOperator only) ---
  function vaultMint(
    address user,
    MintParams calldata params      // pool, tickLower, tickUpper, amounts, slippage
  ) external returns (uint256 tokenId);
  // 効果: USDC 受領 → swap → NFPM.mint → NFT を本 contract が保有
  //       positionOwner[tokenId] = user

  function vaultRebalance(
    uint256 tokenId,
    int24 newTickLower,
    int24 newTickUpper,
    uint256 slippageBps
  ) external returns (uint256 newTokenId);   // 🆕 v5.2.2 (P0-3-1)
  // 効果: decreaseLiquidity 100% → collect → swap → mint new range
  //       同一 tokenId は burn、新 tokenId を本 contract 保有、ledger 引継
  //       newTokenId を返却し Operator が D1 positions.token_id を更新可能にする

  function vaultClose(
    uint256 tokenId
  ) external returns (uint256 token0Amount, uint256 token1Amount);
  // 効果: decreaseLiquidity 100% → collect → WETH→USDC swap →
  //       同一 tx 内で performance fee 配分 + user wallet へ USDC return

  function collectFees(uint256 tokenId) external; // event/threshold-based (§21)

  // --- Emergency (multiSig only) ---
  function emergencyTransfer(uint256 tokenId, address recipient) external;
  // multiSig のみ。operator 障害時に LP NFT を user wallet へ直接 transfer

  function pause() external;   // multiSig / guardian
  function unpause() external;

  function rotateOperator(     // 🆕 v5.2.2 (P0-3-3) — §21.5.5 / §21.5.6 と整合
    address oldOperator,
    address newOperator
  ) external;
  // 効果: authorizedOperator を更新。multiSig 経由のみ実行可。
  //       進行中 tx には影響しない (transaction レベル atomicity を保証)。

  // --- Read ---
  function ownerOfPosition(uint256 tokenId) external view returns (address);
  function isAuthorizedOperator(address a) external view returns (bool);
}
```

```yaml
Authority (Section 15.5.2 と整合):
  authorizedOperator:
    - vaultMint / vaultRebalance / vaultClose / collectFees
    - msg.sender == authorizedOperator の require
    - operator key は EXBOT 専用 (§21.5.5)、POOL の operator とは別 key
  multiSig (Emergency Admin):
    - emergencyTransfer / pause / unpause / rotateOperator
  User:
    - 直接 call 不可。POOL UI → Operator API 経由でのみ LP に触れる
  Transfer 禁止:
    - operator は LP NFT を transfer 不可 (INV-1 維持)
    - emergencyTransfer のみ multiSig 経由で例外

非干渉 (INV-5、Section 15.5.4 / Section 3.4):
  - BnzaExVault は BnzaRouter v2.2.1 を import / delegatecall / 呼出ししない
  - 共有は BNZAToken (BuyBack&Burn) と NFPM のみ (tokenId 単位で独立)

Phase 0 で確定する zen task:
  - chain ごとの BnzaExVault deploy address
  - authorizedOperator address (EXBOT 専用)
  - multiSig signer set / threshold
  - performance fee 配分ロジック (最大 10 recipients、§2.3 と整合)
  - 既存 BnzaRouter/BnzaLpBot の custody パターンを参考にした最終 ABI 確定
```

---

## 16. Bot Lifecycle State Machine

### 16.1 Initialization States

```yaml
🚨 v5.2.1 (P0-8): 下記の細粒度 state は bots.lifecycle_state に格納する
  (§13.2)。bots.status は粗粒度 6 値 (active/paused/closing/closed/
  safe_mode/error) のまま。両者の対応:
    lifecycle_state                | status
    -------------------------------|------------------
    idle/preflight/lp_opening/     | (status は遷移前後の粗粒度値)
      lp_opened/hedge_pre_open/    |
      hedge_post_confirmed/        |
      stop_placing/stop_verified   |
    active                         | active
    lp_rebalancing                 | active   (light-check は §17.1 P0-9 で skip)
    lp_closing                     | closing
    closed                         | closed
    safe_mode                      | safe_mode
    error                          | error
  「bot.status='lp_opened'」等、旧記述で status に細粒度値を代入していた
  箇所は、すべて lifecycle_state への代入として読み替える。
```

```
INIT  (lifecycle_state='idle')
  ↓
PREFLIGHT  (lifecycle_state='preflight')
  - user HL margin check (sufficient? — Section 18.4)
  - agent approval check (approved? — Section 21.5)
  - builder fee approval check (approved?)
  - LP mint simulation (will succeed?)
  - one-bot policy check (Phase A、Section 16.5)
  ↓
LP_OPENING (Section 16.6 に詳細)
  ↓
LP_OPENED
  ↓
HEDGE_OPENING
  - HL short open (IOC)
  ↓
HEDGE_RECONCILING
  - 🚨 must reconcile actual position
  ↓
STOP_PLACING
  - HL native reduce-only stop market (Section 19)
  ↓
STOP_VERIFIED
  ↓
ACTIVE
```

### 16.2 Runtime States

```yaml
ACTIVE:
  description: normal monitoring
  light-check: every 5 min
  hedge-sync: event-driven (delta-only adjustment、Section 17)
  deep-audit: every 6h

PAUSED:
  description: no new adjustments, existing hedge remains
  UI 表示: 明確に "Paused" 表示
  light-check: skip
  hedge-sync: skip
  deep-audit: every 6h (still verify state)
  🚨 hedge は close されない (carter2099 と異なる)

CLOSING:
  description: closing LP and hedge
  detail: Section 16.6 LP_CLOSING flow

CLOSED:
  description: fully closed
  no further actions

SAFE_MODE:
  trigger:
    - HL API unreachable > 5 min
    - reconcile mismatch
    - suspicious state detected
    - margin critical (Section 18.4)
  behavior:
    - no new mutations
    - keep existing stop in place
    - continue monitoring price
    - alert user/admin
    - retry every 1 min
  recovery:
    - auto: when HL responsive + reconcile matches + margin recovered
    - manual: admin intervention

ERROR:
  description: admin intervention required
  trigger:
    - critical bug
    - data corruption
    - irrecoverable state
    - LP NFT ownership unexpected (Section 15.5)
  behavior: pause all activity, alert admin
```

### 16.3 Pause vs Close Semantics (重要)

```yaml
🚨 必須: PAUSED ≠ CLOSED

PAUSED:
  - hedge は維持される
  - LP も維持される
  - 新規 mutation のみ stop
  - ユーザー意図: "一時停止、後で再開"

CLOSED:
  - hedge close 済み
  - LP close 済み
  - USDC 全額返却 (BnzaExVault 経由、Section 16.4)
  - ユーザー意図: "完全終了"

UI で明確に区別:
  Pause ボタン: "Pause Bot (hedge は維持)"
  Close ボタン: "Close Bot (全 close、USDC 返却)"
```

### 16.4 LP Close Authority (🆕 v5.1)

```yaml
LP NFT custodian = BnzaExVault (Section 15.5) なので、
LP close は Operator → BnzaExVault 経由でしか実行できない。

Standard Close Flow (User initiated):
  1. User: POOL UI で "Close Bot" 押下
  2. UI → Operator API: closeBot(botId)
  3. Operator: bot.status を 'closing' へ遷移
  4. Operator: hedge close 先行 (Section 17 の delta-only で size→0)
  5. Operator: hedge reconciled = 0 を確認
  6. Operator: HL stop cancel
  7. Operator → BnzaExVault.vaultClose(tokenId)   // 🆕 v5.2.2 (P0-3-2): §15.5.6 ABI
  8. BnzaExVault (msg.sender == authorizedOperator check) なら実行
  9. BnzaExVault.vaultClose: NFPM decreaseLiquidity 100% → collect → WETH→USDC swap
     → returns (token0Amount, token1Amount)
  10. BnzaExVault: USDC を user wallet へ transfer (BnzaExVault 内部 ledger 経由、同一 tx)
  11. Operator: bot.status を 'closed' へ
  12. Operator: final PnL 記録 (daily_bot_metrics に書き込み)

Operator-initiated Close:
  Trigger:
    - Circuit breaker open + retry exhausted
    - Margin critical (SAFE_MODE recovery 不能)
    - Stop trigger 発動後 hedge size > 0 (異常)
    - Compliance / admin force close
  Same flow as standard close, but originated by Operator.
  User notification 必須。

Emergency Close Path:
  Trigger:
    - Multi-sig admin による緊急停止
    - BnzaExVault contract バグ検出
    - User wallet が compromised (User からの emergency withdraw)
  Flow:
    1. Multi-sig 承認
    2. BnzaExVault emergency function (paused state でも動く close path)
    3. LP NFT を BnzaExVault から user wallet へ直接 transfer
       (BNZA は仲介せず、user 自身で V3 NFT を解決可能にする)
    4. Operator は bot status = 'error' へ
    5. HL hedge は別途 user による close もしくは admin による close
       (HL agent key が valid なら admin close 可能、Section 21.5)

USDC 返却の権限関係:
  BnzaExVault が close 後の USDC を保持する期間: very short (1 tx 内)
  User wallet への transfer は同 tx 内で実行
  BNZA は USDC を保管しない (custody risk 排除)
  
  Performance fee は別途、BnzaExVault が close 時に operator address 経由で支払う
  (operation_fee → BNZA Token BuyBack&Burn、performance_fee → 10 recipients)
```

### 16.5 One-User One-Bot Policy (🆕 v5.1)

```yaml
Phase A:
  1 user = 1 active Ex Bot

  理由:
    - subaccount 1 つで HL hedge を完結させる (margin / nonce 集中管理)
    - Failure mode を集約しデバッグ効率化
    - LP NFT custody の mapping を 1:1 に簡素化
  
  実装:
    - bot 起動 PREFLIGHT で
       SELECT count(*) FROM bot_registry
        WHERE user_id = ? AND bot_type = 'ex' AND status IN ('active','paused','closing','safe_mode')
      が 0 でなければ起動拒否
    - UI: 既に active な Ex Bot がある場合は "新規起動" を無効化、表示で誘導

Phase B+:
  multiple bot per user 解禁

  🚨 v5.2.1 (P0-5) / v5.2.2 (P0-5): Hyperliquid subaccount 制限に整合させた
    現実的構造。**1 bot = 1 subaccount に統一**(内部矛盾を解消)。
    HL subaccount 制限 (公式):
      - 初期: master account あたり 10 subaccount
      - 最大: 50 subaccount (trading volume 条件付きで段階解放)
    → 「事前作成した subaccount pool」のような無制限前提の表現は廃止。

  実装方針 (現実的構造、v5.2.2 で 1 bot = 1 subaccount に統一):
    - 1 user = N bot (N は plan によって制限、例: 3 / 10)
    - 各 bot は別の HL subaccount で隔離 (nonce 衝突 / margin 競合回避)
    - **1 bot = 1 subaccount で固定**
      (旧「1 user 1 subaccount を基本」表現は廃止。matrix は bot 単位)
    - master account 容量計算:
       - 1 master account = 最大 50 subaccount (HL 制限、volume 条件付き)
       - 50 subaccount を超える場合は master account を増設
         (operator が複数 master account を管理、master/IP 分散と併せ設計)
    - plan ごとの bot 数上限例 (master 容量に基づく hard cap):
       - Basic plan:      1 user 1 bot  (= 1 subaccount)
       - Pro plan:        1 user 3 bot  (= 3 subaccount)
       - Enterprise plan: 1 user 10 bot (= 10 subaccount)
       - ※ unlimited plan は削除 (HL subaccount 制限と整合しないため)
    - bot 起動時に空き subaccount を allocate (足りなければ master 増設待ち)
    - subaccount 不足は onboarding を block (preflight で容量チェック)
    - UserLockDO は user_id 単位。subaccount 並列化のため lock 粒度は
      Phase B 開始時に再設計 (既知の defer、§30.1)

  ⚠️ 確認必要 (zen task): Phase B 開始時に master account 増設ポリシー /
       subaccount allocation 詳細 / master・IP 分散を別途 SPEC 化。
       本 SPEC では Phase B 詳細は scope 外
       (v5.2.2 patch cycle で HL 制限の事実のみ反映、以降の patch でも scope 外を維持)。
```

### 16.6 LP Operation State Machine (🆕 v5.1)

```yaml
LP_OPENING (PREFLIGHT 通過後):
  states:
    LP_OPEN_REQUESTED → LP_OPEN_SWAPPING → LP_OPEN_MINTING → LP_OPENED
  
  detailed flow:
    1. LP_OPEN_REQUESTED:
       - user wallet → BnzaExVault: deposit USDC
       - BnzaExVault: receive event 確認
    2. LP_OPEN_SWAPPING:
       - BnzaExVault: half USDC → WETH (V3 swap)
       - 失敗時: revert (USDC は user wallet に残る)
    3. LP_OPEN_MINTING:
       - BnzaExVault: NonfungiblePositionManager.mint(tickLower, tickUpper, USDC, WETH)
       - BnzaExVault 自身が NFT 受領
       - 失敗時: USDC + WETH を user wallet に return
    4. LP_OPENED:
       - Operator: D1 positions に row 作成 (custodian='vault')
       - Operator: bots.lifecycle_state を 'lp_opened' へ (P0-8。status は粗粒度のまま)
       - 次は HEDGE_OPENING へ遷移
  
  failure handling (LP_FAILURE):
    - LP_OPEN_SWAPPING failed → bot.status='error', user funds returned
    - LP_OPEN_MINTING failed → bot.status='error', user funds returned
    - Hedge open でこの後失敗した場合は Section 16.6 LP_CLOSING を逆走

LP_REBALANCING (range out 等):
  trigger:
    - light-check で rangeState != 'in'
    - manual reset
    - Operator policy change (range pct 変更等)

  🚨 v5.2.1 (P0-9): 進入時に bots.lifecycle_state='lp_rebalancing' を set。
    while lifecycle_state=='lp_rebalancing':
      - §17.1 canonical light-check は early-return で skip
        (normal な range_out hedge-sync を発火させない)
      - hedge は本 state machine の "defensive partial pre-hedge" のみが制御
      - LP_REBAL_DONE で lifecycle_state='active' に戻し light-check 再開
    これにより §16.6 hedge policy「確定前に hedge を盲目移動しない」が
    実行 path (light-check) と整合する (旧 v5.2 は status 非変更で
    light-check が rebalance 中も range_out hedge-sync を発火し得た)。

  states:
    LP_REBAL_REQUESTED → LP_REBAL_DECREASING → LP_REBAL_SWAPPING → LP_REBAL_MINTING
                      → LP_REBAL_HEDGING → LP_REBAL_DONE
  
  hedge policy:
    - Do not blindly move hedge to future target before LP rebalance is confirmed.
    - Pre-hedge is allowed only as defensive partial adjustment.
    - Final hedge must be based on confirmed post-rebalance LP amount.

  recommended flow:
    1. Compute expected post-rebalance LP ETH amount.
    2. If current hedge is dangerously under-hedged, perform partial defensive
       delta-only hedge adjustment only.
    3. Operator → BnzaExVault.vaultRebalance(tokenId, newTickLower,
       newTickUpper, slippageBps)   // 🆕 v5.2.2 (P0-3-2): §15.5.6 ABI
    4. BnzaExVault.vaultRebalance internal: NFPM decreaseLiquidity 100% on old position
    5. BnzaExVault.vaultRebalance internal: collect fees
    6. BnzaExVault.vaultRebalance internal: swap (必要なら)
    7. BnzaExVault.vaultRebalance internal: NFPM.mint new range
       → 旧 tokenId burn、returns newTokenId
    8. After LP rebalance is confirmed onchain, recompute actual LP ETH amount.
    9. Operator: D1 positions update (token_id=newTokenId, tickLower,
       tickUpper, liquidity, ...)
    10. Run hedge-sync to final target from confirmed actual LP amount.
    11. LP_REBAL_DONE → ACTIVE 復帰

  if LP rebalance fails:
    - do not assume new LP state
    - enter SAFE_MODE
    - reconcile hedge against current confirmed LP state
    - alert admin/user

LP_CLOSING:
  trigger:
    - user close request
    - Operator force close (Section 16.4)
  
  states:
    LP_CLOSE_REQUESTED → HEDGE_CLOSING → LP_CLOSE_DECREASING → LP_CLOSE_COLLECTING
                      → LP_CLOSE_SWAPPING → LP_CLOSE_RETURNING → CLOSED
  
  detailed flow:
    1. LP_CLOSE_REQUESTED:
       - bot.status='closing' かつ bots.lifecycle_state='lp_closing' (P0-8/P0-9)
       - §17.1 canonical light-check は lifecycle_state in
         ('lp_closing','lp_rebalancing') で early-return skip (並行制御は
         state machine 側)
    2. HEDGE_CLOSING:
       - Section 17 の delta-only で targetSize=0 へ
       - HL stop cancel
       - reconcile = 0 を確認
       - 失敗時: SAFE_MODE 突入、admin alert (LP は触らない)
    # 🆕 v5.2.2 (P0-3-2): step 3-6 は単一 API BnzaExVault.vaultClose(tokenId)
    #   の内部段階。Operator は vaultClose を 1 回呼ぶ (§15.5.6 ABI)。
    3. LP_CLOSE_DECREASING (vaultClose internal):
       - NFPM decreaseLiquidity 100%
    4. LP_CLOSE_COLLECTING (vaultClose internal):
       - NFPM collect (USDC + WETH 両方)
    5. LP_CLOSE_SWAPPING (vaultClose internal):
       - WETH → USDC swap
    6. LP_CLOSE_RETURNING (vaultClose internal):
       - USDC を user wallet へ transfer (同一 tx)
       - Performance fee は同 tx 内で計算 / 配分
       - vaultClose returns (token0Amount, token1Amount)
    7. CLOSED:
       - Operator: D1 で final 記録
       - 通知

LP_FAILURE handling:
  invariants:
    - LP NFT が宙に浮く (どの bot にも紐付かない) ことを許容しない
    - User funds が BnzaExVault 内に滞留することを許容しない (1 tx 内で return)
    - 失敗時は必ず admin alert + bot.status='error'
  
  代表的な failure mode:
    - swap slippage > tolerance → revert + retry with relaxed slippage
    - mint failed (gas / liquidity) → revert + return user funds
    - decrease failed (V3 contract issue) → admin manual recovery
    - WETH→USDC swap failed → bot.status='error', WETH を user に返却
    - hedge close failed → SAFE_MODE 突入 (LP は触らない)
  
  recovery:
    - admin manual flow から re-attempt 可能
    - emergency multi-sig で LP NFT を user wallet へ直接 transfer
```

---

## 17. Hedge Execution Flow (v5.1 で delta-only 化)

### 17.0 v5.1 修正の要旨

```yaml
🚨 v5.1 修正:
  v5.0 は hedge-sync で "close existing → open new" の full close/open を
  毎回行う設計だった。これを delta-only adjustment に変更する。

理由:
  - 毎回 full close/open は subrequest を浪費 (HL rate limit, CF subrequest)
  - 部分調整で済むときに余計な fill cost / spread / funding 切れ目が発生
  - cloid / nonce が無駄に進む
  - 監視・reconcile も冗長

新方針:
  delta = targetSize - actualSize
  
  if (|delta| <= dust)         → no-op
  if (delta > 0)                → 追加 short open IOC (size = delta)
  if (delta < 0 && targetSize>0) → reduce-only IOC (size = |delta|)
  if (delta < 0 && targetSize=0) → reduce-only full close + stop cancel
  
  Full close/open は以下のみ許容:
    - target size = 0 (= bot close / pause for full close 選択時)
    - emergency reset (admin)
    - manual reset (state corruption recovery 時)
```

### 17.1 Light Check Flow (HL 触らない) — 🚨 CANONICAL light-check 実装 (v5.2.1)

```yaml
🚨 v5.2.1 (P0-2): 本 §17.1 が light-check の唯一の規範 (canonical) 実装。
  §15.3 は MarketDataDO 利用例の説明に縮約済みで pseudocode 本体を持たない。
  reason は §7.6 RebalanceReason enum を参照 (P0-11)。
  targetRatio は bps 整数化、float 経由禁止 (§7.6 / P0-6)。
  LP operation state machine (§16.6) 進行中は light-check 抑制 (P0-9)。
```

```typescript
// rebalance reason は §7.6 の canonical RebalanceReason 型を使用 (P0-11)
async function lightCheck(botId: string) {
  const data = await repo.getBotWithPositionAndState(botId);

  // P0-9: status / lifecycle_state ガード。
  //   LP operation state machine (§16.6) 進行中は light-check / hedge-sync を抑制。
  //   LP_CLOSING だけでなく LP_REBALANCING も skip (並行制御は state machine 側)。
  if (data.bot.status !== 'active') return;            // paused/closing/safe_mode/etc
  if (data.bot.lifecycleState === 'lp_closing' ||
      data.bot.lifecycleState === 'lp_rebalancing') {
    return; // LP operation in progress (§16.6); hedge は state machine が制御
  }

  const breaker = await getCircuitBreaker(data.hedge.id);
  if (breaker.state === 'open') return;

  const market = await marketData.getPoolState(data.position.poolAddress);
  const amount = calculatePositionAmount(data.position, market); // §6.4 純関数, HL fetch なし

  // P0-6: targetRatio は bps 整数化して BigDecimal 計算。float 経由 (* 10000) 禁止。
  const targetRatioBps = normalizeTargetRatioBps(data.hedge.targetRatio); // bigint, §7.6
  const targetShort = BigDecimal(amount.lpEthAmount).mul(targetRatioBps).div(10000);
  const currentShort = data.runtime.lastKnownHlShortSize;
  const drift = calculateDrift(targetShort, currentShort);

  await repo.updateRuntimeState(botId, {
    lpEthAmount: amount.lpEthAmount,
    targetShortSize: targetShort.toString(),
    currentTick: amount.currentTick,
    sqrtPriceX96: amount.sqrtPriceX96,
    ethPriceUsd: market.ethPriceUsd.toString(),
    lpValueUsd: drift.lpValueUsd.toString(),
    healthStatus: drift.health,
    lastLightCheckAt: nowIso(),
  });

  // 🆕 v5.1 / v5.2.1 (P0-2): stop trigger crossed marker — GUARDED.
  //   既に marker set 済みなら stop_trigger_crossed_at を上書きしない。
  //   上書きすると §18.3 / NN#14 の "marker stuck > 30 min → SAFE_MODE" が
  //   永久に発火しなくなる (timestamp が毎 light-check で now に巻き戻るため)。
  //   crossed は normal hedge-sync の reason ではなく priority stop-audit のみ
  //   に route する (§19.3 / §7.3)。
  if (data.hedge.stopPrice && market.ethPriceUsd >= Number(data.hedge.stopPrice)) {
    if (!data.hedge.stopTriggerCrossedAt) {
      await repo.markStopTriggerCrossed(data.hedge.id, nowIso()); // guarded: set once
    }
    await stopAuditQueue.send({
      botId,
      ethPriceUsd: market.ethPriceUsd.toString(),
      stopPriceUsd: data.hedge.stopPrice,
      crossed: true,
      priority: "high",
    }, { delaySeconds: 0 });
    return; // stop-audit が actual HL state を reconcile するまで hedge-sync 凍結
  }

  // near-stop (price within 2% of stop) も normal hedge-sync ではなく
  // priority stop-audit に route (§19.3 urgent audit / §7.3)。
  if (priceNearStop(market.currentPrice, data.hedge.stopPrice)) {
    await stopAuditQueue.send({
      botId,
      ethPriceUsd: market.ethPriceUsd.toString(),
      stopPriceUsd: data.hedge.stopPrice,
      crossed: false,
      priority: "high",
    }, { delaySeconds: 0 });
    return;
  }

  // Canonical rebalance reasons (§7.6 RebalanceReason / P0-11)。
  // light-check は HL を触らないため margin/funding は D1 永続値から判定。
  const reasons: RebalanceReason[] = [];
  // 🚨 v5.2.2 (P0-1): drift.* は BigDecimal。Math.max/float 比較は禁止。
  //   定数は文字列で BigDecimal('...')。calculateDrift は BigDecimal を返す。
  const driftThreshold = BigDecimal.max(BigDecimal('25'), drift.lpValueUsd.mul('0.03'));
  if (drift.usd.gt(driftThreshold))                       reasons.push('drift_threshold');
  if (drift.relative.gt(BigDecimal('0.15')))              reasons.push('drift_relative');
  if (amount.rangeState !== 'in')                         reasons.push('range_out');
  if (drift.rangeBoundaryNear)                            reasons.push('range_boundary_near');
  if (data.hedge.marginStatus === 'warning')              reasons.push('margin_warning');
  if (data.funding.alert7dAprLtMinus15Pct)                reasons.push('funding_alert');
  if (sinceLastAdjustmentHours(data) > 4)                 reasons.push('time_fallback');
  // 注: margin_critical は hedge-sync ではなく §18.4.3 SAFE_MODE path に route
  //     (RebalanceReason enum には含むが light-check からは emit しない)。

  if (reasons.length > 0) {
    await hedgeSyncQueue.send({
      botId,
      reasons,                                   // canonical RebalanceReason[]
      expectedTargetSize: targetShort.toString(),
      stateVersion: data.runtime.stateVersion,
    });
  }
}
```

### 17.2 Hedge Sync Flow — Delta-only adjustment (mutation あり)

```typescript
async function hedgeSync(
  botId: string,
  reasons: RebalanceReason[],   // 🚨 v5.2.3 (P1-B): canonical 型 (§7.6) 使用
  stateVersion: number,
) {
  const data = await repo.getBotWithEverything(botId);
  
  // 0. Stale message guard
  if (data.runtime.stateVersion !== stateVersion) {
    return; // newer state already applied
  }
  
  // 1. Acquire UserLockDO (lease-based, Section 11)
  return await withUserLock({
    env,
    userId: data.user.id,
    ttlMs: 90_000,
    idempotencyKey: `hedge-sync:${botId}:${stateVersion}`,
    work: async () => await hedgeSyncInner(data, reasons),
  });
}

async function hedgeSyncInner(data: BotData, reasons: RebalanceReason[]) {
  // 🚨 v5.2.3 (P1-B): canonical 型 (§7.6) 使用
  // 2. Reserve HL rate limit
  await hlRateLimit.reserve({ weight: 8, userAddress: data.user.hlUserAddress });
  
  // 3. Fetch actual HL position
  const account = {
    userAddress: data.user.hlUserAddress,
    vaultAddress: data.hedge.hlAccountAddress,
    agentKeyId: data.user.hlAgentKeyId,
  };
  const actualPosition = await hl.getPosition(account, 'ETH');
  const actualSize = BigDecimal(actualPosition?.size ?? '0');
  
  // 4. Recompute target from fresh market cache
  const market = await marketData.getPoolState(data.position.poolAddress);
  const amount = calculatePositionAmount(data.position, market);
  // 🚨 v5.2.2 (P0-1): canonical bps 経路を経由 (§7.6)。
  //   data.hedge.targetRatio を直接 BigDecimal に渡さない (float 経由禁止)。
  const targetRatioBps = normalizeTargetRatioBps(data.hedge.targetRatio); // bigint, §7.6
  const targetSize = BigDecimal(amount.lpEthAmount).mul(targetRatioBps).div(10000);
  
  // 5. Margin preflight (Section 18.4)
  const margin = await hl.getMarginSummary(account);
  const marginCheck = evaluateMargin(margin, targetSize, market.ethPriceUsd);
  if (marginCheck.status === 'critical') {
    await enterSafeMode(data, marginCheck);
    return;
  }
  
  // 6. Compute delta
  const delta = targetSize.sub(actualSize);
  const dust = computeDust(market.ethPriceUsd);  // e.g. $5 worth in ETH
  if (delta.abs().lt(dust)) {
    return; // no-op
  }
  
  // 7. Create rebalance_attempt
  const attemptId = await repo.createAttempt(data.bot.id, {
    hedgeLegId: data.hedge.id,
    asset: 'ETH',
    stateVersion: data.runtime.stateVersion,
    oldSize: actualSize.toString(),
    targetSize: targetSize.toString(),
    // 🚨 v5.2.3 (P1-B): reasons は RebalanceReason[] (canonical, §7.6)。
    //   .join(',') は string[] 同様に動作するため runtime 変更なし。
    reason: reasons.join(','),
  });
  
  try {
    // 8. Cancel old stop (must precede order changes for clean re-place)
    if (data.hedge.stopCloid) {
      await hl.cancelByCloid(account, ETH_ASSET_INDEX, data.hedge.stopCloid as `0x${string}`);
    }
    
    // 9. Delta-only adjustment (v5.1 core change)
    if (targetSize.eq(0)) {
      // target = 0: full close (only allowed exit path for size=0)
      if (actualSize.gt(0)) {
        const closeCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'close', version: 1 });
        await hl.closeShortReduceOnlyIoc({
          account, asset: 'ETH', size: actualSize.toString(), cloid: closeCloid,
        });
      }
    } else if (delta.gt(0)) {
      // target > actual: open additional short
      const adjustCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'adjust', version: 1 });
      await hl.adjustShortDelta({
        account, asset: 'ETH', deltaSize: delta.toString(), direction: 'increase', cloid: adjustCloid,
      });
    } else {
      // target < actual: reduce short (reduce-only IOC)
      const adjustCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'adjust', version: 1 });
      await hl.adjustShortDelta({
        account, asset: 'ETH', deltaSize: delta.abs().toString(), direction: 'decrease', cloid: adjustCloid,
      });
    }
    
    // 10. Reconcile actual position
    await sleep(2000); // wait for HL to settle
    const reconciled = await hl.reconcilePosition(account, 'ETH', targetSize.toString());
    
    // 11. Place / re-place native stop AFTER reconcile (Section 19)
    if (BigDecimal(reconciled.actualSize).gt(0)) {
      const stopCloid = makeCloid({ botId: data.bot.id, attemptId, stage: 'stop', version: 1 });
      const stopTriggerPx = computeStopTriggerPx({
        entryPrice: reconciled.entryPrice,
        liquidationPrice: reconciled.liquidationPrice,
        effectiveLeverage: reconciled.effectiveLeverage,
        // Section 19.1 参照
      });
      await hl.placeReduceOnlyStopMarket({
        account, asset: 'ETH',
        size: reconciled.actualSize,
        triggerPx: stopTriggerPx.toString(),
        cloid: stopCloid,
      });
    }
    
    // 12. Mark success/partial/failed
    if (reconciled.match) {
      await repo.markAttemptSuccess(attemptId, reconciled.actualSize);
      await repo.updateRuntimeState(data.bot.id, {
        lastKnownHlShortSize: reconciled.actualSize,
        lastHlReconcileAt: nowIso(),
        stateVersion: data.runtime.stateVersion + 1,
      });
    } else {
      await repo.markAttemptPartial(attemptId, reconciled.actualSize, reconciled.expectedSize);
      // schedule retry or admin alert
    }
    
    // 13. Update circuit breaker
    await resetCircuitBreaker(data.hedge.id);
    
  } catch (e) {
    await repo.markAttemptFailed(attemptId, e);
    await incrementCircuitBreaker(data.hedge.id, e);
    await notifyFailedRebalance(data.user, attemptId, e);
    throw e;
  }
}
```

### 17.3 Reconcile Flow (重要)

```yaml
🚨 重要: success ≠ order submitted
🚨 重要: success = actual position confirmed

Reconcile steps:
  1. Order 投入後、2 秒待機 (HL 内部 settlement)
  2. clearinghouseState fetch
  3. 期待 size と actual size 比較
  4. tolerance 以内なら success
  5. 乖離あれば partial、retry 検討

🆕 v5.1:
  reconcile 結果から entry_price / liquidation_price / effective_leverage を抽出し、
  hedge_legs テーブルに保存 (Section 19 で stop 計算に使う)
```

### 17.4 Full Close/Open が許容されるケース (v5.1)

```yaml
v5.1 では原則 delta-only。以下のみ full close/open を許容:

1. target size = 0:
   - bot close 経路 (Section 16.6 LP_CLOSING)
   - emergency stop (admin force)
   → close 一発、open は不要

2. emergency reset (admin invoked):
   - state corruption recovery
   - circuit breaker manual reset
   - HL state vs DB の整合修復
   → close → open (with new cloid version) で全クリア

3. manual reset (user invoked、Phase B+):
   - 範囲変更 (range pct を Phase B+ で変更可能にする場合)
   - hedge ratio 変更
   - subaccount 移行
   → close → open

その他のケース (drift / range out / near stop / time fallback / stop crossed) は
全て delta-only adjustment。
```

---

## 18. Failure Handling

### 18.1 Error Classification

```yaml
| Error                          | Retry? | Circuit | Action                     |
|-------------------------------|--------|---------|----------------------------|
| Network timeout               | yes    | no      | retry with jitter          |
| HL 429 rate limit             | delayed| no      | route through rate limiter |
| Min order / min notional      | no     | yes     | pause leg, notify          |
| Insufficient margin           | no     | yes     | user action required (18.4)|
| Unauthorized agent            | no     | yes     | re-approval required (21.5)|
| Duplicate cloid               | no     | no      | reconcile first            |
| Reduce-only rejected          | maybe  | maybe   | reconcile state            |
| Stop would immediately trigger| no     | maybe   | recompute / alert          |
| Open failed after close       | controlled | maybe | reconcile first         |
| Partial fill mismatch         | yes    | no      | repair job                 |
| HL API unreachable            | yes    | no      | enter SAFE_MODE            |
| RPC unreachable               | yes    | no      | failover provider (Phase C)|
| LP NFT ownerOf mismatch       | no     | yes     | bot.status='error', alert  |
```

### 18.2 Circuit Breaker Logic (PK = hedge_leg_id)

```typescript
async function checkCircuitBreaker(hedgeLegId: string): Promise<boolean> {
  const recent = await db.prepare(`
    SELECT status FROM rebalance_attempts
    WHERE hedge_leg_id = ?
      AND started_at > ?
    ORDER BY started_at DESC
    LIMIT 3
  `).bind(hedgeLegId, hoursAgo(24)).all();
  
  if (recent.results.length === 3 && 
      recent.results.every(r => r.status === 'failed')) {
    return false; // circuit open, skip
  }
  return true; // circuit closed, proceed
}

Open conditions:
  - 3 failed attempts within 24h
  - permanent validation error
  - unauthorized agent
  - insufficient margin (repeated)

Reset conditions:
  - successful rebalance
  - manual reset (admin)
  - config changed (target ratio etc)
  - 24h half-open probe succeeds
```

### 18.3 SAFE_MODE Behavior

```yaml
trigger conditions:
  - HL API unreachable > 5 min
  - reconcile mismatch (actual ≠ expected)
  - suspicious state detected
  - 🆕 (v5.1) margin status = 'critical' (Section 18.4)
  - 🆕 (v5.1) stop_trigger_crossed_at marker stuck > 30 min

🚨 v5.2.1 (P0-2) — marker stuck 検出が正しく発火する保証:
  判定式: now - hedge_legs.stop_trigger_crossed_at > 30 min
  前提: stop_trigger_crossed_at は §17.1 canonical light-check が
        GUARDED に set する (既に非 NULL なら上書きしない)。
        これにより 5 分毎の light-check で timestamp が now に
        巻き戻らず、30 分経過を確実に検出できる。
        (旧 v5.2 §15.3 の無条件 re-mark では本条件が永久に
         発火しなかった — P0-2 で修正済み / NN#14)。
  resolve 経路: priority stop-audit が case A-D のいずれかで
        marker を resolve するか、本 SAFE_MODE に遷移する (§19.3)。

forbidden in SAFE_MODE:
  ❌ cancel existing stops
  ❌ open new positions
  ❌ rebalance hedge
  ❌ rebalance LP
  ❌ change leverage
  ❌ withdraw margin

allowed in SAFE_MODE:
  ✅ read state
  ✅ retry HL connectivity
  ✅ alert user/admin
  ✅ continue light-check (HL なし部分)
  ✅ deep audit (when HL recovers)
  ✅ priority stop audit (when stop_trigger_crossed flagged)

recovery:
  auto: HL responsive + 3 successful reconciles + margin status returned to 'ok'
  manual: admin intervention via dashboard
```

### 18.4 Insufficient Margin UX (🆕 v5.1)

```yaml
3 段階で margin を扱う:
  ok       → normal operation
  warning  → notify user, light-check 継続、hedge-sync 慎重に
  critical → SAFE_MODE 突入

定義:
  marginUsage = 1 - (marginBalanceUsd - marginRequiredUsd) / marginBalanceUsd
              ≒ 使われている margin の比率
  
  ok:        marginUsage < 0.50
  warning:   0.50 <= marginUsage < 0.75
  critical:  marginUsage >= 0.75
  
  上記閾値は Phase 0 backtest で再調整 (⚠️ 確認必要 (zen task))
```

#### 18.4.1 Preflight Margin Check (Bot 起動時)

```yaml
PREFLIGHT で実行:
  1. user の HL margin balance fetch
  2. expected target hedge notional 計算
     notional = lpEthAmount × hedgeRatio × ethPriceUsd
  3. required margin = notional / leverage
  4. expected post-deposit margin balance >= required margin × 1.5 (50% buffer)
     を満たさないと bot 起動不可
  5. UI 表示:
     "Required HL margin: $X (with 50% buffer)
      Current HL margin: $Y
      Status: [Sufficient / Insufficient — please deposit $Z to HL]"

不足時:
  - bot 起動を block
  - "HL に $Z を追加 deposit してから再度起動してください" を案内
  - HL deposit 手順を UI で説明 (CCTP / Across 経由、ユーザー側で実行)
```

#### 18.4.2 Active 中の Margin Warning / Critical

```yaml
light-check でも margin status を更新する条件:
  - 30 分に 1 回 (light-check 内で margin fetch を allow、weight 2)
  - もしくは hedge-sync 直前 (Section 17.2 step 5)

hedge_legs.margin_status の遷移:
  ok → warning:
    - alert を user に push (POOL UI banner + email、Phase A は UI banner のみ)
    - hedge-sync で size 増加方向の調整は disable (size 削減のみ allow)
    - Bot は active のまま
  
  warning → critical:
    - SAFE_MODE 突入 (Section 18.3)
    - admin にも alert
    - User に "HL に追加 deposit が必要" と案内
  
  critical → warning:
    - margin が回復 (user が追加 deposit) したら自動遷移
    - SAFE_MODE recovery 条件の一部
  
  warning → ok:
    - margin が更に回復したら自動遷移
    - hedge-sync の制約解除
```

#### 18.4.3 SAFE_MODE 突入条件 (Margin 観点、v5.1 で再整理)

```yaml
margin 起因で SAFE_MODE 突入する条件:
  1. margin_status = 'critical' を 2 回連続検出 (false positive 防止)
  2. HL から insufficient margin error が返却された hedge-sync 失敗
  3. effective_leverage > 4.5 (3x configured を超えた = 危険水準)
     ※ effective_leverage は notional_usd / isolated_margin_usd で算出
  4. liquidation_price が現在 ETH price と 5% 以内
```

---

## 19. Native Stop Lifecycle (v5.1 で再定義)

### 19.0 Stop の意味再定義 (重要)

```yaml
🚨 v5.1 修正:
  v5.0 では stop を "清算 (liquidation) を回避するための保険" と表現していたが、
  正確には stop は損失制限 (loss cap) であり、清算回避とは別物。

  - 清算は HL の自動執行 (margin 不足時)
  - stop は意図的な損失確定 (price が trigger を超えたら reduce-only で close)
  
  実態としては:
    stop が trigger される ≒ 損失確定 + position size 0 化 + LP との delta 不均衡
  
  v5.1 では以下を明示する:
  
  - stop は損失を "抑える" 装置であり、清算より前に発動するよう設計する
  - ただし stop が発動しても、その時点の loss は確定する
  - stop が発動した後の bot は SAFE_MODE / LP は維持され、user の意思で
    "hedge を再構築するか、LP も close するか" を決められるべき
  - stop は LP 側を救う仕組みではない (LP 側の IL は別途発生する)
```

### 19.1 stopTriggerPx の動的計算 (v5.1)

```yaml
v5.0 では stopTriggerPx = entry × 1.10 と固定値を使っていたが、
v5.1 では実際の liquidationPx を優先し、取得できない場合のみ
effective_leverage ベースの fallback approximation で動的算出する。

入力 (HL reconcile から取得、hedge_legs に保存):
  entry_price        = position.entryPx
  liquidation_price  = position.liquidationPx (取得できる場合は必ず優先)
  notional_usd       = abs(position_size_eth) × entry_price
  effective_leverage = notional_usd / isolated_margin_usd
  not:
    isolated_margin_usd / notional_usd
	  
計算式 (短ポジション、ETH-USD short):
  if liquidation_price is available:
    liq_distance_pct = (liquidation_price - entry_price) / entry_price
  else:
    liq_distance_pct ≒ 1 / effective_leverage
    ※ fallback approximation only

  実際の liquidation は maintenance margin / funding / mark-oracle price /
  isolated margin の変化によりズレる。effective_leverage からの距離は
  safety estimate であり、HL position の liquidationPx を置き換えない。
  
  stop_distance_pct = liq_distance_pct × stopSafetyFactor
  
  stopSafetyFactor:
    Phase A:  0.70  (清算前 70% の地点で stop)
    Phase B+: backtest で調整 (⚠️ 確認必要 (zen task))
  
  stop_trigger_px = entry_price × (1 + stop_distance_pct)
  
例: entry $3000, effective_leverage = 3.1x
  liq_distance_pct ≒ 32.3%
  stop_distance_pct = 32.3% × 0.70 = 22.6%
  stop_trigger_px = $3000 × 1.226 = $3678
  
  これは v5.0 の "entry × 1.10" よりも liquidation までの buffer を確保し、
  かつ早すぎる stop (= 不要な loss 確定) を避ける。
```

```typescript
function computeStopTriggerPx(input: {
  entryPrice: number;
  liquidationPrice?: number;
  effectiveLeverage: number;
  safetyFactor?: number;  // default 0.70 (Phase A)
}): number {
  const safety = input.safetyFactor ?? 0.70;
  const liqDistancePct = input.liquidationPrice
    ? (input.liquidationPrice - input.entryPrice) / input.entryPrice
    : 1 / input.effectiveLeverage; // fallback approximation only
  const stopDistancePct = liqDistancePct * safety;
  return input.entryPrice * (1 + stopDistancePct);
}

function computeEffectiveLeverage(input: {
  sizeEth: Decimal;
  entryPrice: Decimal;
  isolatedMarginUsd: Decimal;
}): Decimal {
  const notionalUsd = input.sizeEth.abs().mul(input.entryPrice);
  if (input.isolatedMarginUsd.lte(0)) {
    throw new Error("invalid isolated margin");
  }
  return notionalUsd.div(input.isolatedMarginUsd);
}
```

### 19.2 Stop Placement (delta-only との連携)

```yaml
on hedge open (size 0 → > 0):
  1. open short (IOC)
  2. wait for fill
  3. reconcile actual size
  4. extract entry_price / liquidation_price / effective_leverage
  5. save to hedge_legs (Section 13.2)
  6. compute stop_trigger_px (Section 19.1)
  7. place reduce-only stop with computed trigger
  8. verify stop placed (single confirmation)
  9. record stop_cloid, stop_order_id, stop_price, stop_size, stop_distance_pct in DB

on hedge resize (delta-only adjustment):
  v5.0: cancel old stop → close diff → place new stop
  v5.1: cancel old stop → adjust delta → reconcile → place new stop
  
  Stop placement order (v5.1):
    Step A: cancel old stop (by cloid)
    Step B: delta adjust (open additional / reduce-only)
    Step C: reconcile new size
    Step D: extract updated entry_price / liquidation_price (HL は重み付き平均で更新)
    Step E: re-compute stop_trigger_px
    Step F: place new stop with new cloid (version + 1)
    Step G: verify

on hedge close (size > 0 → 0):
  1. cancel stop
  2. close position
  3. reconcile (size = 0)
  4. clear stop_cloid / stop_price / stop_distance_pct in DB

Hyperliquid Stop Direction Live Test:
  Short position close requires buy reduce-only trigger.
  Confirm on testnet/live-small:
    - side: buy for short close
    - reduce-only flag
    - triggerPx direction
    - tpsl value
    - mark-price trigger behavior
    - immediate-trigger rejection
    - p/orderPx behavior for trigger market
    - vaultAddress + agent key compatibility
    - cancelByCloid behavior
```

### 19.3 Stop Audit (v5.1 で priority audit 追加)

```yaml
periodic audit:
  cadence: 6h normal
  scope: distribute across all bots (avoid burst)
  check:
    - stop exists in HL openOrders?
    - stop size matches DB?
    - stop side correct (buy)?
    - stop reduce-only?
    - stop trigger based on mark price?
    - 🆕 v5.1: hedge_legs.last_stop_audit_at update

urgent audit triggers (priority):
  - ETH price within 2% of stop trigger
  - 🆕 v5.1: ETH price >= stop_price (即時 enqueue、stop_trigger_crossed_at marker)
  - HL API/order error detected
  - reconcile mismatch
  - bot status change

Stop trigger crossed (v5.1 詳細):
  light-check で ETH price >= stop_price を観測したら、
    1. hedge_legs.stop_trigger_crossed_at = now を marking
    2. stop-audit queue に priority 投入 (delaySeconds=0)
    3. normal hedge-sync は enqueue しない
    4. stop-audit が actual HL state を reconcile するまで normal hedge adjustment を freeze
    5. reconciliation 完了まで lastKnownHlShortSize は stale として扱う
  
  stop-audit worker:
    - HL clearinghouseState fetch
    - native stop が発動済みか確認
    - actual short size を reconcile
       case A: stop triggered + position size = 0
              → DB 整合性 update (lastKnownHlShortSize = 0、stop_cloid clear)
              → stop_trigger_crossed_at resolve
              → bot は LP のみ active 状態に (新 hedge は user の判断で再開)
              → user 通知
       case B: stop is still pending (price spike だが市場で fill されていない)
              → 様子見 (next audit cycle で再確認)
       case C: stop missing / mismatch (cloid not found, size/side mismatch)
              → SAFE_MODE 突入 + admin alert
       case D: position size > 0 だが stop は triggered (= partial fill 異常)
              → SAFE_MODE 突入 + admin alert
    - stop order missing / partial / mismatch は SAFE_MODE
    - stop_trigger_crossed_at は resolve するか SAFE_MODE に移行する

  light-check pseudocode:
    // 🚨 v5.2.1 (P0-2): canonical 実装は §17.1。ここは §19.3 観点の抜粋。
    //   markStopTriggerCrossed は GUARDED (既に set 済みなら timestamp を
    //   上書きしない)。上書きすると §18.3 / NN#14 の stuck>30min 検出が
    //   無効化される。canonical と完全に同一ロジックであること。
    if (data.hedge.stopPrice && market.ethPriceUsd.gte(data.hedge.stopPrice)) {
      if (!data.hedge.stopTriggerCrossedAt) {
        await repo.markStopTriggerCrossed(data.hedge.id, nowIso()); // guarded: set once
      }
      await stopAuditQueue.send({
        botId,
        ethPriceUsd: market.ethPriceUsd.toString(),
        stopPriceUsd: data.hedge.stopPrice,
        crossed: true,
        priority: "high",
      }, { delaySeconds: 0 });

      // Important:
      // Do not run normal hedge-sync until stop-audit reconciles actual HL state.
      return;
    }

🚨 forbidden:
  ❌ check every stop for every bot every 5 min (subrequest 上限超過)
  ❌ stop_trigger_crossed marker を set したまま 30 分以上放置
     (set 後は priority audit 経路で必ず resolve させる)
```

### 19.4 Stop と Liquidation の関係 (明示)

```yaml
Stop placement の意図:
  - stop_trigger_px は liquidation_price より手前
  - stop が trigger されれば、liquidation には到達しない (理想)
  - ただし stop は market order なので slippage で fill 価格が悪い可能性あり
  - Mark price ベースなので、自分の last trade ではなく oracle / book mid で発火

Liquidation が発生するケース:
  - HL API 障害で stop の cancel/replace ができない間に price 急変
  - 市場流動性枯渇で stop が fill できない (= liquidation engine が拾う)
  - margin が想定外に減少 (funding payment / 別 leg の損失)
  - stop が user の手動操作で消されていた (要 audit)

User への明示:
  "stop は損失を限定する仕組みであり、liquidation を完全に防ぐものではない。
   特に flash crash や API 障害時には stop が間に合わない可能性がある。"
```

---

## 20. Deep Audit

### 20.1 Cadence

```yaml
normal bots:
  every 6h
  
high-risk bots (recent failures, low margin):
  every 1h

recent rebalance bots:
  5 min, 30 min, 2h follow-up
  
near-stop bots:
  immediate (price within 2% of stop)
  
🆕 v5.1: stop_trigger_crossed bots:
  immediate priority (Section 19.3)
  
ladder for SAFE_MODE recovery:
  1 min initially, exponential backoff
```

### 20.2 Audit Work

```yaml
per-bot audit:
  1. NFPM.positions refresh (liquidity, ticks)
  2. NFPM.ownerOf check (custodian == BnzaExVault?)  -- 🆕 v5.1
  3. pool.slot0 refresh
  4. HL clearinghouseState fetch
  5. actual short size reconcile
  6. stop order existence check
  7. funding/fills low-frequency sync (Phase A は daily aggregate)
  8. HL marginSummary fetch (Section 18.4)
  9. update bot_runtime_state (eth_price_usd, lp_value_usd 含む)
  10. hedge_legs update (entry_price, liquidation_price, effective_leverage,
                       isolated_margin_usd, stop_distance_pct, last_stop_audit_at)
  11. mark next_deep_audit_at

work splitting:
  - 1 audit message = 1 bot
  - parallel consumers process queue
  - HL rate limit 共有
```

---

## 21. Fee Collection

### 21.1 Daily Fee Collect 廃止

```yaml
🚨 carter2099 から学んだ反省:
  daily collect は gas/operation cost が増える
  10,000 bot で daily = 大量 tx → 高 cost

新方針:
  threshold-based + event-based
```

### 21.2 Collection Triggers

```yaml
collect fee when:
  - LP rebalance (range out)
  - Bot close
  - uncollected fee > threshold (e.g. $10)
  - weekly scheduled claim
  - user manual claim

display:
  - estimated/static-call fee data
  - actual collect は threshold/event based
  
do not:
  ❌ collect for all bots daily
  ❌ swap fee → USDC every collect (token balance を維持)
```

---

## 21.5 Security / Secret Handling (🆕 v5.1)

### 21.5.1 大原則

```yaml
🚨 v5.1 で明文化:

1. BNZA は user の HL master private key を持たない / 受け取らない
   - user は HL 公式 UI / wallet で master account を管理
   - BNZA に送信されるのは agent key (master が approve したもの) のみ
   - master private key を BNZA UI / API に貼り付ける機能は提供しない

2. BNZA は user の wallet private key (Base / OP) を持たない
   - user wallet は metamask / WalletConnect で接続
   - user wallet signs:
       - initial start / deposit request
       - approvals where applicable
       - user-requested close confirmation if UI requires explicit confirmation
       - agent / builder fee approval flows where applicable

3. Operator signs BnzaExVault operational tx
   - BnzaExVault operational rebalance
   - BnzaExVault fee collect
   - BnzaExVault LP close after authorized user/admin trigger
   - emergency actions, if authorized by contract role
   - LP NFT custody model (Section 15.5) と整合させるため、
     "すべての onchain tx を user が署名する" とは定義しない

4. BNZA が絶対に保管しないもの
   - user EVM wallet private key
   - user HL master private key

5. BNZA が保管し得るもの
   - encrypted HL approved agent key
   - operator key, separately managed and rotated

6. Agent key (HL signing key) は envelope encryption で保管する
   - 暗号化保存 (envelope encryption)
   - 復号は OPERATOR Worker 内で必要時のみ
   - 平文を log / DB dump / Analytics に出さない

7. 任意の secret (API key、webhook secret 等) も同様に envelope encryption
```

### 21.5.2 Envelope Encryption Model (Agent Key)

```yaml
階層:
  - Master Key (Phase A default 確定: 🚨 v5.2.1 / P0-4):
       Phase A の default は **Cloudflare Secrets Store** に確定 (zen 決定)。
         a) Cloudflare Secrets Store + Worker bindings  ← Phase A 確定
         b) HashiCorp Vault Cloud / AWS KMS via internal proxy ← Phase B 以降で検討
         c) 自前管理 (HSM)  ← Phase D 以降
       外部 KMS (AWS/GCP KMS) への移行可否は Phase B で評価。
       Phase 0 では a) の DEK 生成/保存/rotation runbook を確定 (§21.5.2.1)。
  
  - Master Key の保持 (🚨 v5.2.2 / P0-2 で DEK lifecycle 矛盾を解消):
       Master Key は Worker 起動時に Cloudflare Secrets Store binding 経由で
       memory に保持 (account-level secret、memory-only)。
       ※ 旧記述「DEK を Worker 起動時に復号 memory-only 保持」は誤りのため削除。
         DEK は起動時には触らない。

  - Data Encryption Key (DEK) — per agent key row 単位:
       hl_agent_keys row ごとに 1 DEK (bot/hedge_leg 単位ではない)。
       agent key を使うたびに D1 から wrapped_dek を読み、Master Key で
       unwrap して memory に得る (関数 scope のみ、使用後即破棄)。
       agent key rotation のたびに新 DEK を生成・新 wrap。

  - Agent Key (encrypted) — D1.hl_agent_keys に格納 (Option A 列):
       encrypted_secret (AES-256-GCM ciphertext)
       secret_iv / secret_auth_tag (per-record random IV + GCM tag)
       wrapped_dek / dek_iv (Master Key で wrap した DEK + IV)
       encryption_key_version (Master Key version、rotation chain)

復号 flow (§13.9 Option A schema と完全一致):
  1. hedge-sync worker が agent key 必要
  2. D1 から {wrapped_dek, dek_iv, encrypted_secret, secret_iv,
     secret_auth_tag, encryption_key_version} を読み出し
  3. Master Key を Secrets Store binding から取得 (Worker 起動時 memory cache)
  4. Master Key + dek_iv で wrapped_dek を unwrap → 平文 DEK (memory)
  5. DEK + secret_iv + secret_auth_tag で encrypted_secret を AES-256-GCM 復号
  6. 平文 agent key を memory に保持 (関数 scope のみ)
  7. HL order 署名後、平文 DEK / 平文 agent key を破棄
  8. log / error 出力には絶対含めない (§21.5.4 sanitize)
```

#### 21.5.2.1 Phase A Default Runbook: Cloudflare Secrets Store (🆕 v5.2.1 / P0-4)

```yaml
🚨 v5.2.1 確定: Phase A の envelope encryption は Cloudflare Secrets Store を使用。

Master Key:
  - Cloudflare Secrets Store の account-level secret として保管
  - Worker bindings 経由で OPERATOR Worker のみが参照可
  - 平文は memory-only、D1/ディスク/ログに出さない (§21.5.4)

DEK (Data Encryption Key) — 🚨 v5.2.2 (P0-2): per agent key row 単位:
  - hl_agent_keys row ごとに 1 DEK を生成 (AES-256-GCM 用 32-byte random)。
    bot/hedge_leg 単位ではない (DEK lifecycle 矛盾を解消)
  - Master Key で wrap し D1.hl_agent_keys.wrapped_dek に保存
    (dek_iv / encryption_key_version も同 row に)
  - Agent Key 本体は per-row DEK で暗号化 (encrypted_secret, secret_iv,
    secret_auth_tag)

生成 (agent key approval / rotation 時。1 row = 1 DEK):
  1. crypto.getRandomValues で DEK 生成 (memory-only)
  2. Master Key (Secrets Store) で DEK を wrap → {wrapped_dek, dek_iv}
  3. DEK で agent key を AES-256-GCM 暗号化 → {encrypted_secret,
     secret_iv, secret_auth_tag}
  4. §13.9 Option A の各 column に保存:
     {encrypted_secret, secret_iv, secret_auth_tag, wrapped_dek, dek_iv,
      encryption_key_version}。平文 DEK / agent key は即破棄

復号 (hedge-sync 時):
  §21.5.2 復号 flow に従う (Master Key→unwrap DEK→decrypt agent key→
  関数 scope のみ→署名後破棄)

Rotation:
  - 月次自動 (§21.5.3 と整合)。Master Key version を上げ、
    既存 row は旧 version chain で復号可能、新規 row は新 version で wrap
  - rotation 中も無停止 (key version chain、§21.5.3)

外部 KMS 移行:
  - Phase B 以降で AWS/GCP KMS proxy を評価 (本 runbook を差し替える形)
  - Phase A は本 runbook で freeze (着手条件 3 を満たす、§0.3 / §30)
```

### 21.5.3 Key Versioning / Rotation

```yaml
encryption_key_version:
  - hl_agent_keys.encryption_key_version で管理
  - Master Key rotation 時、新 key version を割り当て
  - 旧 version で暗号化された row も復号可能 (key version chain)

agent key rotation:
  trigger:
    - HL agent key expiry (HL 仕様の expiry)
    - user の意思 (security event 後)
    - 定期 rotation (90 日推奨)
  flow:
    1. user に再 approval を要求
    2. 新 agent key 生成 (browser / wallet 側)
    3. user が HL master で approve sign
    4. BNZA が新 key を envelope encrypt して INSERT
    5. 旧 row の approval_status='revoked', rotated_from=new.id
    6. hedge-sync は新 key を使用

rotated_from chain で audit trail を残す。
DROP しない。
```

### 21.5.4 Logging / Sanitization

# 🚨 v5.2.3 (P1-A): sanitize regex を envelope encryption fields (wrapped_dek /
#   dek_iv / secret_iv / secret_auth_tag) も redact するよう拡張。
#   §21.5.4 本文「DEK / Master Key を絶対 log に書かない」と regex を完全整合化。
```yaml
ログに絶対書かない:
  - private keys (agent key 平文)
  - master account private key (受け取らない前提だが念のため)
  - signed payload の signature 部
  - DEK / Master Key
  - wrapped_dek (Master Key で暗号化済だが念のため log に出さない)
  - dek_iv (DEK 復号用 IV、暗号文を弱めないが log に出さない)
  - secret_iv (agent key 復号用 IV、同上)
  - secret_auth_tag (AES-GCM 認証 tag、同上)
  - cloudflare secrets binding 内容
  - 任意の "secret" / "auth" / "key" / "token" を含む string

sanitize 関数:
  HL response の raw object には agent key / signature が含まれる場合がある
  → parseOrderResponse / R2 archive 前に sanitize() を必ず通す
  envelope encryption 関連の field (wrapped_dek / dek_iv /
  secret_iv / secret_auth_tag) も同関数で redact する。
  
  function sanitize(obj: unknown): unknown {
    // recursively redact keys matching:
    // 🚨 v5.2.3 (P1-A): dek / master.*key パターン追加
    // /private|secret|signature|agent.*key|auth|dek|master.*key/i
    // また値が長い hex (>= 64 bytes) はマスク
  }

R2 archive:
  - sanitize 済み JSON のみ
  - sanitize miss が発覚した場合は当該日付 archive を削除 + 再生成

Analytics Engine:
  - 無条件で sensitive dimension を排除 (Section 14.3)
```

### 21.5.5 Operator Key Management

```yaml
Operator (BnzaExVault の operator function 呼び出し権限):
  - Cloudflare Workers が保持する operator address の private key
  - これも envelope encryption で管理 (§21.X Phase A default = Cloudflare Secrets Store)
  - rotation 可能 (BnzaExVault contract 側に rotateOperator function を実装)
  
  🚨 v5.2.1 確定 (Option C / Section 3.4):
    EXBOT の Operator key は EXBOT 専用に分離する。
    現行 BNZA POOL の BnzaRouter v2.2.1 operator key とは
    別 key・別 rotation lifecycle とし、相互に影響しない。
    BnzaExVault.rotateOperator は EXBOT multiSig のみ呼び出し可。
    chain ごとの operator address / multiSig signer set は
    Phase 0 開始前に zen が確定 (§15.5.6 zen task と同期)。
```

### 21.5.6 Compromise Response

```yaml
agent key compromise (疑い):
  1. Operator: 当該 user の bot を即時 SAFE_MODE
  2. user に通知
  3. user に re-approval を要求
  4. 旧 key を revoked へ
  5. HL 側でも user が agent revoke を実行 (HL UI)

operator key compromise:
  1. 全 bot を pause
  2. operator key rotation
  3. 影響調査
  4. user 再開告知

KMS / Master Key compromise (重大):
  1. 全 hl_agent_keys を revoked
  2. 全 user に再 approval を要求
  3. KMS rotation + service 再起動
  4. 過去の DB dump も再暗号化 / または旧 dump 廃棄
```

---

## Part 3: Implementation Roadmap

## 22. Pre-Launch Process (v5.1 で Phase 細分化 + Backtest 順序修正)

### 22.0 v5.1 修正の要旨

```yaml
🚨 v5.1 修正:
  v5.0 の Phase 1 = "4-6 weeks" は楽観的すぎる。
  v5.1 では Phase を Phase 0 / A1 / A2 / A3 に細分化し、現実的な Total を提示する。
  (🚨 v5.2.1 P0-7: 旧表記「A0」は実ロードマップの「Phase 0」と同一。命名統一)
  
  Phase 0 (Backtest + PositionCalculator + HL testnet validation):  4-6 weeks
  Phase A1 (single-user dry-run):                                     3-4 weeks
  Phase A2 (live $1k):                                                3-4 weeks
  Phase A3 (closed beta):                                             4 weeks
  Total Phase 0+A:                                                    14-18 weeks (4-5 months)

  Defer list (Phase A では実装しない):
  - 16 D1 shards (Phase A は 1 shard)
  - Analytics Engine (Phase A は D1 集計のみ、Phase B+ で導入)
  - R2 raw log archive (Phase A は基本 D1、log は CF Logs / Tail)
  - DLQ operator UI (Phase A は admin が直接 D1 query)
  - Multi-RPC failover (Phase A は single RPC、Phase C で multi)
  - LP range ladder (Phase A は ±5% 単一)
  - Revert Lend integration (LP Plus)
  - AI Pro (dynamic leverage / Aave 統合)
  - Multiple bot per user (Phase A は 1 user 1 bot、Section 16.5)
```

### 22.1 Phase 0: Backtest + Mini-implementation (Step ordering 修正)

```yaml
duration: 4-6 weeks
tool: zelos-research/Demeter (Python OSS) + custom HL module
goal: パラメータ確定 + PositionAmountCalculator の正確性検証 + HL testnet 動作確認

🚨 v5.1 修正: Step ordering
  v5.0 では "data → simulation → parameter sweep → choose" の順。
  v5.1 では Step 0 として PositionAmountCalculator (mini) を先に作る。
  理由: Backtest シミュレーターも同じ AMM 数式を使うので、
        本実装と backtest で計算 logic を共通化できる。

Step 0: PositionAmountCalculator mini implementation (Week 1)
  - TypeScript で TickMath / LiquidityAmounts を実装 (本 OPERATOR で使うのと同じ)
  - Python wrapper or 同等 logic を Demeter に組み込む
  - test cases (Section 6.5) を全て pass
  - WETH token0/token1 両ケース確認
  - boundary tick の挙動確認
  - 出力: PositionAmountCalculator package + test suite (Phase A1 でそのまま使用)

Step 1: Data preparation (Week 1-2)
  - Base USDC/ETH 0.3% pool: 6-12 months historical
    - slot0, liquidity, ticks, swap events
  - HL ETH funding history (fundingHistory API)
  - HL ETH mark/oracle price
  - estimated orderbook impact

Step 2: Simulator (Week 2-3)
  - Demeter ベースで LP simulator
  - Step 0 の PositionAmountCalculator を組み込む
  - HL hedge module (funding / spread / stop trigger 含む)
  - Phase 1 strategy (70% short, 3x isolated, ±5% range, threshold trigger) を再現

Step 3: Parameter sweep (Week 3-4)
  range: ±3%, ±5%, ±8%, ±12%
  hedge ratio: 50%, 70%, 90%
  leverage: 2x, 3x
  trigger threshold: delta error 10%, 15%, 25%
  cooldown: 30min, 60min, 120min
  stopSafetyFactor: 0.60, 0.70, 0.80   -- 🆕 v5.1 (Section 19.1)

Step 4: Metrics evaluation (Week 4-5)
  metrics:
    - net APR (after PF, gas, fees)
    - max drawdown
    - liquidation distance min
    - out-of-range time
    - rebalance count (delta-only adjustment 前提)
    - hedge turnover
    - funding paid/received
    - worst 1d / 7d loss
    - Sharpe ratio
    - 🆕 stop trigger 発動回数 / 平均 stop loss size

Step 5: Decision + HL testnet validation (Week 5-6)
  parameter set 採用条件:
    ✅ net positive APR (median scenario)
    ✅ max drawdown < 20%
    ✅ worst 7d loss < 10%
    ✅ avg liquidation distance > 5%
    ✅ Sharpe ratio > 1.5
    ✅ stop trigger 発動回数 / 月 < 1 (median scenario)
  
  HL testnet validation (mini-implementation 一部):
    - Hyperliquid testnet で agent key 作成 + envelope encryption の往復
    - testnet で IOC short open / reduce-only close / native stop
    - cloid / nested error / reconcile の挙動
    - subaccount + vaultAddress の挙動
```

### 22.2 Phase A1: Single-User Dry-Run (3-4 weeks)

```yaml
duration: 3-4 weeks
goal: 実装の動作確認 + dry-run mode で full flow 検証
funds: $0 (実発注なし)

scope:
  - PositionAmountCalculator (Phase 0 の Step 0 をそのまま採用)
  - HyperliquidAdapter (テストネット → 本番、ただし dry-run mode)
  - D1 hot state (1 shard、Phase A 既定)
  - Cron + Queue fan-out (light-check のみ、hedge-sync は dry-run)
  - UserLockDO (lease-based)
  - HL native stop placement (テストネット)
  - Reconcile after order
  - PREFLIGHT margin check (Section 18.4)
  - Bot lifecycle state machine (Section 16)
  - LP NFT custody (Section 15.5、BnzaExVault 統合確認)
  - 1 user / 1 bot policy (Section 16.5)

forbidden in A1:
  ❌ live HL mutation
  ❌ live LP open / close
  ❌ live USDC transfer
  ❌ Multi-shard
  ❌ R2 / Analytics Engine
  ❌ Multi-RPC failover

完了基準:
  - PREFLIGHT が確実に block するべきパターンで block
  - LP_OPENING / HEDGE_OPENING / STOP_PLACING の simulation が成功
  - light-check が想定通り発火
  - hedge-sync の delta-only logic が正しく size を出す (実発注なし)
  - SAFE_MODE 突入条件が想定通り
  - Cron / Queue 全体が wall time 内で完了
```

### 22.3 Phase A2: Live $1,000 Test (3-4 weeks)

```yaml
duration: 3-4 weeks
goal: 実 fund 運用、本番条件で安定性検証
funds: zen 自己資金 $1,000 (1 bot)
user: zen のみ (1 user 1 bot policy)

scope:
  - A1 全機能を live mode で稼働
  - 実 LP open (Base USDC/ETH 0.3%, ±5%)
  - 実 HL hedge (70% short, 3x isolated)
  - 実 stop placement
  - 実 reconcile
  - 実 fee collect (event-based、Section 21)
  - 実 close path (途中で close 試行、再 open も検証)
  - 全 metric 詳細 log
  - 毎日結果 review
  - margin warning / critical の triggering 確認 (低 margin で意図的に発生)

pass criteria:
  - Net APR が backtest 想定の ±30% 以内
  - Stop trigger 発動なし or 発動時に正常動作 (Section 19.3 case A)
  - Reconcile 100% 一致
  - Critical bug ゼロ
  - HL native stop が想定通り placement / cancel / re-place
  - delta-only adjustment が full close/open より subrequest を消費していない
  - LP NFT custody (BnzaExVault 内) が確認できる (NFPM.ownerOf == BnzaExVault)
```

### 22.4 Phase A3: Closed Beta (4 weeks)

```yaml
duration: 4 weeks
goal: 複数 user での運用、UX / Onboarding 検証
users: WL 5-10 名、各 $1,000-5,000、各 user 1 bot まで (Section 16.5)
total AUM: $5,000-50,000

process:
  - Real users で運用
  - 週次 user feedback collection
  - Weekly metric review
  - 毎週 Phase B 移行可否を評価

pass criteria:
  - Critical bug ゼロ
  - User satisfaction (survey 平均 4/5 以上)
  - Backtest との乖離 < 30%
  - Critical SAFE_MODE 発生なし
  - Operator-initiated close が 0 件 or 想定パターンのみ
  - Stop trigger crossed marker が正常に resolve (Section 19.3)
  - Onboarding (HL agent approval / margin deposit) が 5 user 全員で成功
```

### 22.5 Phase A → Phase B 移行条件 (Public Launch 前)

```yaml
prerequisites:
  - Phase A3 完了 + pass criteria 全達成
  - Conservative marketing 準備
  - Risk disclosure 完備
  - Customer support 体制
  - Legal / compliance review (Terms / Risk Disclosure)

launch path:
  - Phase A scope (10-100 bot 想定) で Public Open
  - 段階的 invitation (Whitelist → Public)
  - Phase B 機能 (multi-shard, multi-bot per user, R2 archive 等)
    は Public Launch 後に追加
```

### 22.6 Total Timeline (v5.1 確定値)

```yaml
Phase 0 (Backtest + PositionCalculator + HL testnet):  4-6 週間
Phase A1 (single-user dry-run):                         3-4 週間
Phase A2 (live $1k):                                    3-4 週間
Phase A3 (closed beta):                                 4 週間
合計:                                                   14-18 週間 (4-5 ヶ月)

zen 1 人体制 + Claude Code を前提にした見積もり。
並行作業 (BnzaExVault 新規開発 / BNZA-LPBOT・BnzaRouter v2.2.1 非干渉確認)
があれば +2〜4 週間程度のバッファ (BnzaExVault は新規 Solidity のため)。

⚠️ 確認必要 (zen task) — 着手条件 4 (v5.2.1 で再定義、§0.3 / §30 と同期):
  WL 5/15 ローンチは既に実施済み。Phase 0 開始日は「POOL ローンチ後の
  不安定期を脱した」と zen が判定した時点とする。具体的 gate は §0.3 / §30
  の着手条件 4 を参照 (過去 7 日 SAFE_MODE ゼロ・major incident なし)。
```

---

## 23. Implementation Phases (Technical) — v5.1 で Defer 明示

### 23.1 Phase A: Correctness MVP (Phase A1+A2+A3 の合算)

```yaml
cap: 1-100 bots
duration: 約 10-12 週間 (Phase 0 を除く Phase A 全体)

must_have (Phase A):
  ✅ PositionAmountCalculator (正しい AMM 数式、Phase 0 で確立)
  ✅ HyperliquidAdapter (cloid, nested error, reconcile, delta-only adjust)
  ✅ HL native reduce-only stop (動的 stopTriggerPx、Section 19)
  ✅ Reconcile after order
  ✅ D1 hot state (1 shard)
  ✅ Queue fan-out (light-check, hedge-sync, reconcile, stop-audit)
  ✅ UserLockDO (lease-based)
  ✅ Circuit breaker (history-based, hedge_leg_id PK)
  ✅ Failure notification (POOL UI banner + email)
  ✅ MarketDataDO
  ✅ LP NFT custody via BnzaExVault (Section 15.5)
  ✅ HL agent key envelope encryption (Section 21.5)
  ✅ Margin status (ok / warning / critical / safe_mode、Section 18.4)
  ✅ Stop trigger crossed marker + priority audit (Section 19.3)
  ✅ One user one bot policy (Section 16.5)
  ✅ Funding daily metrics (Section 13.6 Phase A 簡素版)

forbidden in Phase A (Defer list):
  ❌ D1 sharding (16 shard は Phase C)
  ❌ R2 raw log archive (Phase B+)
  ❌ Analytics Engine (Phase B+)
  ❌ DLQ operator UI (Phase B+)
  ❌ Multi-RPC failover (Phase C)
  ❌ LP range ladder (Phase 2 / Defer)
  ❌ Revert Lend (LP Plus、Defer)
  ❌ AI Pro (Defer)
  ❌ Multiple bots per user (Phase B+)
  ❌ D1 snapshots (1 min granularity)
  ❌ 全 bot 5 min HL poll
  ❌ Per-bot RPC fetch in light-check
  ❌ Per-record funding ledger (Phase A は daily aggregate のみ)
```

### 23.2 Phase B: 1,000 Bot Readiness

```yaml
trigger: Phase A 安定運用 + user 増加
duration: 2-3 weeks
add:
  - 4 D1 shards
  - MarketDataDO (shared pool cache 強化)
  - HLRateLimitDO (token bucket)
  - Stop audit queue 強化
  - Deep audit queue (distributed)
  - Dead-letter queue + admin UI
  - Metrics rollup (hourly/daily)
  - Funding rolling metrics (24h/7d/30d、Section 13.6)
  - R2 raw log archive
  - Analytics Engine (low-cardinality dimensions only、Section 14.3)
  - Hedge ratio 2 modes (Conservative 50% / Balanced 70%)
  - Multiple bot per user (subaccount allocation、Section 16.5)
  # 🚨 v5.2.1/v5.2.2 (P0-5): 1 bot = 1 subaccount に統一。HL subaccount 制限
  #   (初期 10 / 最大 50, volume 条件付) に整合。master account あたり最大
  #   ~50 subaccount (= ~50 bot)、超過時は master 増設。plan は Basic 1 /
  #   Pro 3 / Enterprise 10 bot (unlimited は廃止)。master/IP 分散ポリシーを
  #   Phase B 開始時に別途 SPEC 化 (§16.5 zen task)。
```

### 23.3 Phase C: 10,000 Bot Readiness

```yaml
trigger: 1,000 bot 安定運用
duration: 3-4 weeks
add:
  - 16 D1 shards
  - Shard-aware scheduler
  - Adaptive audit priority
  - R2 archive (raw funding events 含む)
  - Multi-RPC provider failover
  - Queue lag backpressure
  - Operator dashboard
```

### 23.4 Phase D: 10,000+ / Enterprise

```yaml
trigger: 10,000 bot 安定運用 + 更なる scale 需要
add:
  - 32 shards
  - Online resharding tool
  - Per-chain worker split
  - Multiple RPC providers per chain
  - Stronger observability
  - LP Plus Bot (Revert Lend leveraged)
  - AI Pro Bot (Aave + dynamic optimization)
```

---

## 24. Live Test Checklist

### 24.1 Hyperliquid

```yaml
must_test:
  □ agent key can place order without main private key
  □ agent key + vaultAddress works correctly
  □ clearinghouseState with vaultAddress returns subaccount position
  □ clearinghouseState with master returns master position only
  □ IOC sell opens short
  □ IOC buy reduce-only closes short
  □ delta-only adjust (size 増加 / 減少) で正しい delta が市場に投入される (v5.1)
  □ updateLeverage works (3x)
  □ isolated margin update works
  □ trigger stop market accepted
  □ stop triggers on mark price
  □ openOrders contains cloid / reduceOnly flags
  □ cancelByCloid works
  □ duplicate cloid behavior understood
  □ nested min-notional error parsed correctly
  □ userRateLimit endpoint usable
  □ funding query bounded by time works
  □ subaccount creation works
  □ subaccount transfer works
  □ marginSummary が effective_leverage / liquidation_price を含む (v5.1)
  □ envelope-encrypted agent key 復号 → 署名 → log sanitize の flow が動作 (v5.1)
```

### 24.2 Uniswap

```yaml
must_test:
  □ Base WETH/USDC 0.3% pool: WETH is token0
  □ Pool where WETH is token1 (verify)
  □ in range: amount0 > 0, amount1 > 0
  □ below lower: all token0
  □ above upper: all token1
  □ negative tick handling
  □ currentTick == tickLower (boundary)
  □ currentTick == tickUpper (boundary)
  □ zero liquidity case
  □ decimals 18/6 correct conversion
  □ NFPM.collect static call works
  □ Subgraph indexing lag observed
  □ NFPM.ownerOf returns BnzaExVault (Phase A custody check、v5.1)
  □ BnzaExVault rebalance / decreaseLiquidity / collect / mint authority (v5.1)
```

### 24.3 Cloudflare

```yaml
must_test:
  □ Queue fan-out correctness (no message loss)
  □ Queue idempotency (no duplicate execution)
  □ D1 shard routing (correct shard selected)
  □ UserLockDO lease acquire/release (no concurrent mutation、v5.1)
  □ UserLockDO heartbeat extends lease (v5.1)
  □ UserLockDO TTL 超過で stale lock 自動解放 (v5.1)
  □ HLRateLimitDO backpressure (within budget)
  □ DLQ handling (poison messages quarantined)
  □ MarketDataDO cache consistency
  □ Subrequest count under plan limit (Free 50 / Paid 10,000、Section 5.2)
  □ D1 query count under plan limit (Free 50 / Paid 1,000 per invocation、Section 5.2)
  □ KMS / Secrets での Master Key 復号往復 (v5.1)
```

### 24.4 BnzaExVault (🆕 v5.1)

```yaml
must_test (Phase 0 / Phase A1):
  □ BnzaExVault LP open (USDC deposit → mint NFT、custody = BnzaExVault)
  □ BnzaExVault LP rebalance (decrease 100% → mint new range)
  □ BnzaExVault LP close (decrease 100% → collect → swap → return USDC)
  □ BnzaExVault emergency NFT recovery (multi-sig 経由、v5.1)
  □ Operator authority check (msg.sender check)
  □ BnzaExVault pause / unpause
  □ User receipt token / internal ledger (どちらを採用したか)
  □ 既存 BNZA-LPBOT (BnzaLpBot.sol) との互換性 (zen task)
```

---

## 25. Must-Fix Before 1,000 Bots

```yaml
🚨 1,000 bot scale 前に必須 (Phase A → Phase B 移行前):
  1. Correct Uniswap V3 amount calculation (PositionAmountCalculator)
  2. Queue fan-out (no cron direct processing)
  3. No HL fetch in light check
  4. User-level mutation lock (UserLockDO lease-based、v5.1)
  5. Order idempotency (cloid)
  6. Post-order reconcile
  7. D1 hot state only (no snapshots)
  8. MarketDataDO cache
  9. Circuit breaker (history-based, hedge_leg_id PK、v5.1)
  10. HL native reduce-only stop (動的 stopTriggerPx、v5.1)
  11. Failed rebalance notification
  12. Bridge state machine (LP first, atomicity)
  13. 🆕 v5.1: LP NFT custody via BnzaExVault (Section 15.5)
  14. 🆕 v5.1: Agent key envelope encryption + sanitize logging (Section 21.5)
  15. 🆕 v5.1: Delta-only hedge adjustment (Section 17)
  16. 🆕 v5.1: Margin status + insufficient margin UX (Section 18.4)
  17. 🆕 v5.1: Stop trigger crossed marker + priority audit (Section 19.3)
  18. 🆕 v5.1: LP operation state machine (Section 16.6)
```

---

## 26. Must-Fix Before 10,000 Bots

```yaml
🚨 10,000 bot scale 前に必須 (Phase B → Phase C 移行前):
  1. 16 D1 shards
  2. Shard-aware scanner
  3. HL global/user token bucket (HLRateLimitDO)
  4. Distributed deep audit
  5. Distributed stop audit
  6. R2 / Analytics Engine offload (low-cardinality dimensions only、Section 14.3)
  7. DLQ operator UI
  8. Queue lag backpressure
  9. Per-pool MarketDataDO monitoring
  10. RPC provider failover (multi-RPC)
  11. Daily collect removal (event-based のみ、既に Phase A から)
  12. Snapshot ban (D1 行数管理、既に Phase A から)
  13. 🆕 v5.1: Per-bot funding raw events を R2 archive (Section 13.6)
  14. 🆕 v5.1: Master Key rotation drill (Section 21.5)
```

---

## Part 4: Conclusion

## 27. Final Technical Conclusion

### 27.1 Non-Negotiable Rules (v5.1 で更新)

```yaml
🚨 絶対遵守 (違反すると scale 破綻 / 信頼破綻):

1. Do not fork carter2099/delta_neutral.
   → TypeScript で BNZA OPERATOR に再実装

2. Do not copy carter2099 LP amount calculation.
   → 正しい AMM 数式で実装

3. Do not poll Hyperliquid for every bot every 5 minutes.
   → light-check で HL 触らない

4. Do not store 5-minute snapshots in D1.
   → hot state のみ、履歴は R2 (Phase B+)

5. Do not process all bots inside cron worker.
   → cron は dispatcher のみ、queue で fan-out

6. Do not record success before reconcile.
   → post-order reconcile 必須

7. Do not use cross margin by default.
   → isolated 必須 (Phase 1)

8. Do not keep pause/close semantics ambiguous.
   → PAUSED ≠ CLOSED を UI/code で明確に

9. 🆕 v5.1: Do not full-close → full-open every hedge-sync.
   → delta-only adjustment が default (Section 17)

10. 🆕 v5.1: Do not store HL master private key, ever.
    → agent key only, envelope-encrypted (Section 21.5)

11. 🆕 v5.1: Do not log raw HL responses without sanitize().
    → secret / signature を含み得る (Section 21.5)

12. 🆕 v5.1: Do not promise "全相場で net positive" or "IL elimination".
    → drawdown 抑制を狙う設計、保証はしない (Section 1.2)

13. 🆕 v5.1: Do not use bot_id / user_id as Analytics Engine dimension.
    → low-cardinality only (Section 14.3)

14. 🆕 v5.1: Do not let stop_trigger_crossed_at marker stuck > 30 min.
    → 必ず priority audit で resolve (Section 19.3)
    → 🆕 v5.2.1 (P0-2): marker は §17.1 canonical light-check で GUARDED に
      set すること (既に set 済みなら上書き禁止)。§15.3 のような無条件
      re-mark は timestamp を毎回 now に巻き戻し、本 NN の stuck 検出
      (§18.3) を無効化するため厳禁。canonical light-check は §17.1 のみ。
```

### 27.2 Implementation Model Summary

```
TypeScript rewrite
+ Correct Uniswap V3 position math (LiquidityAmounts)
+ Shared pool market cache (MarketDataDO)
+ Lightweight 5m checks (no HL fetch)
+ Event-driven HL execution (hedge-sync queue)
+ Delta-only adjustment (v5.1 — full close/open は target=0/emergency のみ)
+ Native reduce-only stops with dynamic trigger (v5.1)
+ Post-order reconciliation (mandatory)
+ Phase 別 D1 sharding (Phase A: 1 / Phase B: 4 / Phase C: 16)
+ R2 / Analytics Engine archive (Phase B+, low-cardinality only)
+ Queue fan-out (no direct cron processing)
+ Lease-based Durable Object user lock (v5.1 — function-callback ではない)
+ Hyperliquid rate limiter (HLRateLimitDO)
+ LP NFT custody by BnzaExVault (v5.1)
+ HL agent key envelope encryption (v5.1)
+ Margin status state machine (v5.1)
+ Stop trigger crossed priority audit (v5.1)
+ One user one bot policy (Phase A、v5.1)
+ LP operation state machine (v5.1)
```

### 27.3 Scaling Path

```
Phase 0 (4-6w):          Backtest + PositionCalc + HL testnet (parameters fixed)
Phase A1 (3-4w):         Single-user dry-run (1 shard, no live mutation)
Phase A2 (3-4w):         Live $1k test (1 user, 1 bot)
Phase A3 (4w):           Closed beta (5-10 users, 1 bot each)
Phase B (2-3w + ongoing):4 shards + R2 + Analytics + multiple bot per user
Phase C (3-4w):          16 shards + multi-RPC + full distributed audit
Phase D (ongoing):       32 shards + online resharding + LP Plus / AI Pro
```

### 27.4 BNZA Differentiation vs Competitors (v5.1 で表現修正)

```yaml
🚨 v5.1 修正:
  Panoptic / Neutra に対する "数学的優位性" 主張は削除する。
  BNZA の差別化は (a) 既存 BNZA POOL UI 統合 (b) HL 流動性活用
  (c) BNZA Token BuyBack&Burn fee 構造 (d) operational simplicity に絞る。
  carter2099 (OSS) との比較は v5.0 表現を維持する。

vs carter2099/delta_neutral (OSS):
  ✅ Multi-tenant SaaS
  ✅ BNZA POOL UI 統合
  ✅ HL builder revenue share
  ✅ Performance fee model
  ✅ HL native stop (delta-only adjustment + dynamic stop trigger)
  ✅ Funding rate management
  ✅ Multi-chain (実装伴う)
  ✅ Atomicity (post-order reconcile)
  ✅ AMM 数式での正確な LP 量計算

vs Panoptic (商用 option-based):
  ✅ HL 流動性活用 (perpetual の仕組みで実現できる範囲)
  ✅ シンプルな perpetual hedge (option pricing 不要)
  ✅ 既存 BNZA POOL / LP Bot との統合
  ❌ "数学的に優位" とは主張しない (異なるアプローチであり、それぞれ trade-off がある)

vs Neutra Finance / Orange Finance (Aave + Uniswap):
  ✅ HL hedge (Phase 1) — hedge venue がよりシンプル
  ✅ Optimism / Base 両対応 (Phase 2)
  ✅ Phase 2 で Aave も統合可能 (AI Pro、Defer)
  ❌ "より優れた hedge" とは主張しない (hedge venue が異なるだけ)

vs Arrakis / Gamma (LP only):
  ✅ Optional hedge overlay で IL drawdown を抑える設計
  ❌ IL elimination とは主張しない (Section 1.2)
```

---

## 28. Appendix: 検証で確認された致命的論点

### A.1 v1 (初期 Claude) → v3.1 で修正された論点

```yaml
1. ±2% range / ±3% threshold の数学的矛盾
   → ±5% range / delta error trigger に修正

2. 5x leverage + Auto Close +15% の安全幅不足
   → 3x leverage + HL native stop + reconcile に修正

3. "IL 90% 削減" 表現の数学的不正確性
   → "70% directional exposure hedge" に修正

4. Performance fee 未計上のシミュレーション
   → Gross/Net 分離表示

5. Bridge Bot 内部実行の事故リスク
   → ユーザー事前準備モデルに修正

6. Funding +3-10% 期待の楽観論
   → bonus/cost 扱い、収益前提にしない

7. Auto Close 清算計算ミス (3x で +14.7% は誤、+30.7% が正)
   → 動的計算 (effective leverage ベース)

8. State machine LP first vs Hedge first
   → LP_OPEN → HEDGE_OPEN → STOP_PLACE が正解

9. HL API unreachable で close 不可能
   → SAFE_MODE 突入、close 試行しない

10. Agent wallet vs main private key の表現混乱
    → user-approved agent key のみ BNZA 保管
```

### A.2 v3.1 → v4.1 で追加された論点

```yaml
1. CF Workers / D1 制約の再整理
   → v4.1 時点では subrequest 50 を保守的前提として扱ったが、
      v5.2 では現行公式値に合わせて修正。
      Workers Paid subrequests: 10,000/request
      D1 queries per invocation: 1,000 on Workers Paid
      主要 bottleneck は HL rate limit / D1 single-thread / queue orchestration。

2. HL rate limit の正確な計算
   → 1,200 weight/min/IP、全 bot poll は不可能

3. D1 行数制約
   → 1 min snapshot は 10,000 bot で破綻

4. carter2099 の隠れたバグ
   → LP 量計算が累積差分で range out で破綻

5. carter2099 にない BNZA 差別化点
   → HL native stop, funding monitor, atomicity, multi-tenant

6. Cloudflare 制約への適合
   → Queue + DO + sharding が必須

7. 10,000 bot scale の throughput model
   → light-check + event-driven + shared cache

8. Cloid idempotency
   → deterministic, retry-safe, version-aware

9. carter2099 の cross margin default を否定
   → BNZA は isolated default 必須

10. Pause vs Close semantics
    → carter2099 の曖昧さを排除、明確に区別
```

### A.3 v4.1 → v5.0 → v5.1 で追加された論点 (🆕)

```yaml
1. UserLockDO 実装可能性
   → function-callback 方式は不可、lease-based に修正 (Section 11)

2. LP NFT custody が暗黙だった
   → BnzaExVault が保有する明示モデル (Section 15.5)

3. Hedge 毎回 full close/open による subrequest / nonce 浪費
   → delta-only adjustment 化 (Section 17)

4. stopTriggerPx を固定 1.10 にしていた
   → liquidationPx ベースの動的計算 (Section 19.1)

5. Stop = 清算回避 という誤解
   → Stop は損失制限、清算回避ではない を明示 (Section 19.0)

6. Stop trigger 後の stale state 放置リスク
   → stop_trigger_crossed_at marker + priority audit (Section 19.3)

7. Schema 不整合 (eth_price_usd / lp_value_usd 等)
   → ALTER TABLE で追加、DROP しない (Section 13)

8. circuit_breakers の PK が bot_id ベース
   → hedge_leg_id ベースに変更 (1 leg = 1 circuit、Section 13.7)

9. HL agent key 暗号化方式が未定義
   → envelope encryption + KMS-like + key versioning (Section 21.5)

10. raw log に secret 混入リスク
    → sanitize() を必須、Analytics は low-cardinality only

11. Insufficient margin の UX flow が未定義
    → Preflight + warning / critical / SAFE_MODE 三段階 (Section 18.4)

12. LP close authority が未定義
    → BnzaExVault 経由、emergency multi-sig path 明示 (Section 16.4)

13. Phase A scope が楽観的 (4-6 週間)
    → Phase 0 / A1 / A2 / A3 に細分化、Total 14-18 週間 (Section 22.6)
      (🚨 v5.2.1 P0-7: 旧「A0」表記を「Phase 0」に統一)

14. Funding ledger が over-engineered
    → Phase 別簡素化 (Phase A: daily aggregate のみ、Section 13.6)

15. Analytics Engine high-cardinality risk
    → bot_id / user_id を dimension にしない (Section 14.3)

16. One-user one-bot か multi-bot か未定義
    → Phase A: 1 user 1 bot、Phase B+: subaccount で複数化 (Section 16.5)

17. LP operation state machine が暗黙
    → LP_OPENING / LP_REBALANCING / LP_CLOSING / LP_FAILURE 明示 (Section 16.6)

18. Backtest 順序が "data → simulation → ..."
    → Step 0 として PositionAmountCalculator mini を先に作る (Section 22.1)

19. 競合に対する数学的優位性主張
    → Panoptic / Neutra に対しては主張しない (Section 27.4)

20. Cloudflare Workers Paid subrequest 数値間違い
    → Free 50 / Paid 10,000 に修正 (Section 5.2、⚠️ Phase 0 で再確認)

21. 戦略表現 "全相場で net ≥ 0"
    → 削除、median scenario で net positive を狙うへ (Section 1.2)

22. IL elimination guarantee の不存在を明示していなかった
    → "IL は削減対象であり削除対象ではない" 明示 (Section 1.2)
```

---

## 29. 検証してほしい最終ポイント (v5.1 修正後の最終 review 用)

```yaml
1. v3 戦略層と v4.1 インフラ層の融合 (本 v5.2) が破綻していないか
   - 戦略 (Phase 1: 70% hedge, 3x leverage) と
     技術 (10,000 bot scale architecture) が整合するか

2. Position amount calculation の数学的正確性
   - LiquidityAmounts.getAmountsForLiquidity の式
   - 境界条件 (currentTick == tickLower) の挙動
   - Negative tick handling

3. Cloudflare 制約への適合性 (v5.1 で更新済み)
   - Subrequest Free 50 / Paid 10,000 / 1 invocation
   - D1 query Free 50 / Paid 1,000 / 1 invocation
   - D1 10GB / shard, single-threaded
   - Queue 5,000 msg/sec, 250 concurrency
   - DO single-threaded per instance
   - UserLockDO lease pattern (v5.1)

4. Hyperliquid 仕様への適合性
   - Rate limit 1,200 weight/min/IP
   - Subaccount + vault_address の正しい使用
   - Native stop の trigger order 仕様 (動的 stopTriggerPx, v5.1)
   - Cloid + idempotency
   - Agent key envelope encryption flow (v5.1)

5. State machine の漏れ
   - SAFE_MODE 遷移条件 (margin critical 含む)
   - PAUSED → ACTIVE/CLOSED への遷移
   - Reconcile mismatch 時の挙動
   - LP_OPENING / LP_REBALANCING / LP_CLOSING の各 step (v5.1)

6. Failure handling の網羅性
   - Network timeout, rate limit, validation error
   - HL/RPC 障害時の振る舞い
   - Circuit breaker reset 条件
   - LP NFT ownerOf mismatch 時の error 遷移 (v5.1)

7. Pre-launch process の現実性 (v5.1 で再見積もり)
   - Phase 0 で 4-6 週間で十分か
   - Phase A1 + A2 + A3 で 10-12 週間で十分か
   - Total 14-18 週間で十分か

8. Phase A scope (v5.1 で defer 明示) の妥当性
   - zen 1 人 + Claude Code で完了可能か
   - Defer list に漏れがないか

9. 致命的な見落とし
   - Edge case
   - Security risk (Section 21.5 で網羅されているか)
   - Operational risk (margin critical / stop crossed)

10. 競合差別化の妥当性 (v5.1 で表現修正済み)
    - carter2099 / Panoptic / Neutra に対して
    - 表現が現実的か (誇張していないか)

11. 🆕 v5.1 で追加した LP NFT custody model の妥当性
    - 既存 BNZA-LPBOT (Solidity) との統合可能性 (zen task)
    - Operator authority / Emergency multi-sig の妥当性

12. 🆕 v5.1 で追加した envelope encryption / KMS-like の妥当性
    - Phase 0 開始前に KMS 候補を確定可能か
    - rotation flow が実装可能か
```

---

## 30. Document Status (v5.2 で更新)

```yaml
Version: v5.2.5
Status: Final Approved — 3 AI APPROVED (Codex / GPT / Claude Code) + zen approval 確定 + Codex v5.2.4 軽量再検証 APPROVED with minor notes 反映済。Phase 0 着手 OK (4 件の着手条件は §0.3 / §30 を参照)
Authors:
  - Strategy: Claude (BNZA Technical Advisor)
  - Math/Risk: 検証 AI #1 (Code Review)
  - Infrastructure: 検証 AI #2 (Scale Architecture)
  - Implementation Reference: Claude Code (carter2099 analysis)
  - v5.0 → v5.1 修正: GPT / Codex 検証レポート統合 (22 必須修正)
  - v5.1 → v5.2 lightweight patch: final sanity corrections
  - v5.2 → v5.2.1 patch: Codex/GPT/Claude Code 統合 P0 11 件 (Claude Code 適用)
  - v5.2.1 → v5.2.2 patch: Codex 再検証指摘 5 件 / P0 同期漏れ (Claude Code 適用)
  - v5.2.2 → v5.2.3 patch: Claude Code 摘出 P1/P2 / 極小 doc-sync 3 件 (Claude Code 適用)
  - v5.2.3 → v5.2.4 patch: doc-self-containment / 外部 PATCH_NOTES 参照削除 (Claude Code 適用)
  - v5.2.4 → v5.2.5 patch: Codex 摘出 minor notes 2 件反映 / Final Approved 確定 (Codex 適用)
  - Approval: zen (BNZA Founder)

v5.1 → v5.2 lightweight patch:
  - fixed effective_leverage definition
  - replaced initialHedgeEth drift denominator with targetShort-based relative drift
  - stop_trigger_crossed now routes to priority stop-audit/reconcile only, not normal hedge-sync
  - aligned security/onchain signing text with Router/Vault custody model
  - weakened LP_REBALANCING hedge-first into defensive partial pre-hedge + final post-confirm hedge
  - added Hyperliquid stop direction live-test requirement
  - added UserLockDO crash/reconcile rule

v5.2 → v5.2.1 patch (3 AI 統合 P0 11 件、Claude Code 直接適用):
  - P0-1  Option C: EXBOT custody を新規 BnzaExVault に分離 (現行 BnzaRouter
          v2.2.1 / BnzaLpBot v1.1 は非改修)。Router 用語置換 + §3.4 責務分離 +
          §15.5.6 BnzaExVault Solidity 仕様 + HL vaultAddress との用語衝突注記
  - P0-2  §15.3 を例示縮約し canonical light-check を §17.1 に一本化。
          markStopTriggerCrossed を guarded 化 → NN#14 / §18.3 の
          "marker stuck > 30 min → SAFE_MODE" を実効化 (安全網修復)
  - P0-3  全 sendBatch を 100 件 chunking (Cloudflare Queues 制限、§10.3)
  - P0-4  envelope encryption Phase A default = Cloudflare Secrets Store
          確定 + runbook (§21.5.2 / §21.5.2.1)
  - P0-5  HL subaccount 制限 (初期10/最大50) に整合、subaccount pool 表現を
          現実的構造へ (§16.5 / §23.2)
  - P0-6  target_ratio を bps 整数規定、float 経由禁止 (§7.6 canonical)
  - P0-7  Phase 命名を「Phase 0 / A1 / A2 / A3」に統一 (A0 表記廃止)
  - P0-8  bots.lifecycle_state カラム追加、§16 細粒度 state machine と整合
  - P0-9  LP_REBALANCING で §17.1 light-check を抑制 (LP_CLOSING と同 pattern)
  - P0-10 Phase 0 着手条件 4 を再定義 (5/15 既了 → 不安定期 gate)、
          §0.3 と §30 を 4 条件で完全一致
  - P0-11 RebalanceReason enum を canonical 一本化
          (§7.6 定義、§5.3/§7.3/§13.4/§17.1 が参照)

v5.2.1 → v5.2.2 patch (Codex 再検証・P0 統合の同期漏れ 5 件、Claude Code 直接適用):
  - v5.2.2-P0-1 §17.2 hedge-sync を canonical bps 経路へ
                (normalizeTargetRatioBps)。§7.3/§17.1 の toNumber()/Math.max/
                float 比較を BigDecimal 比較に統一 (定数は文字列 BigDecimal)
  - v5.2.2-P0-2 hl_agent_keys DDL に envelope fields 追加 (Option A:
                secret_iv/secret_auth_tag/wrapped_dek/dek_iv)。DEK lifecycle
                矛盾を解消 (per agent key row 単位、§13.9/§21.5.2/§21.5.2.1 同期)
  - v5.2.2-P0-3 BnzaExVault ABI 整合: vaultRebalance returns newTokenId /
                §15.5.3·§16.4·§16.6 を vaultMint/vaultRebalance/vaultClose に
                統一 / rotateOperator を interface に追加 (§15.5.6)
  - v5.2.2-P0-4 共通 helper chunkSendBatch を §10.2 に規定。§10.2 cron /
                §10.3 scan が helper 経由。生 sendBatch 直接呼び出し禁止
  - v5.2.2-P0-5 §16.5 を 1 bot = 1 subaccount に統一、unlimited plan 削除、
                master 容量計算明示。§23.2 を同期

v5.2.2 → v5.2.3 patch (Claude Code 摘出・P1/P2 極小 doc-sync 3 件、Claude Code 直接適用):
  - v5.2.3-P1-A §21.5.4 sanitize regex に dek/master.*key パターン追加 +
                「ログに絶対書かない」列挙に wrapped_dek / dek_iv / secret_iv /
                secret_auth_tag を明記(セキュリティ defense-in-depth)。
                §21.5.4 本文「DEK / Master Key を絶対 log に書かない」と完全整合
  - v5.2.3-P1-B §10.1 hedge-sync queue message の reason (単数 string) を
                reasons: RebalanceReason[] (canonical, §7.6) に統一。
                §17.2 hedgeSync / hedgeSyncInner 関数引数も同型に統一。
                §7.6 P0-11 canonical enum の最終マイル伝播
  - v5.2.3-P2-A §0.3 着手条件 1 の版数を「本 v5.2.3 を…approval」に更新。
                §30 と完全一致(v5.2.2 patch で取りこぼした自己導入 staleness 修正)

v5.2.3 → v5.2.4 patch (doc-self-containment、Claude Code 直接適用):
  - SPEC v5.2.3 までは過去 patch の詳細を別紙 PATCH_NOTES.md
    (SPEC_v5.2_to_v5.2.1_PATCH_NOTES.md /
     SPEC_v5.2.1_to_v5.2.2_PATCH_NOTES.md /
     SPEC_v5.2.2_to_v5.2.3_PATCH_NOTES.md) に分離していた
  - v5.2.4 では本 SPEC §30 patch chain (上記) を patch サマリの
    canonical source とし、別紙 PATCH_NOTES.md への外部参照を削除
  - 各 patch の precise diff は git history で完全保持 (削除した
    PATCH_NOTES.md も含めて git log / git show で復元可能)
  - 設計内容 (戦略、Phase 構造、API、schema、enum、Solidity ABI、運用 flow、
    着手条件 4 件、全 NN ルール) は v5.2.3 から完全不変
  - SPEC v5.2.4.md 単体で BNZA Ex Bot の全実装規範が完結する状態を達成

v5.2.4 → v5.2.5 patch (Codex 摘出 minor notes 2 件反映 / Final Approved 確定、Codex 直接適用):
  - v5.2.5-N1 §30 Status と §30.2 次プロセスの段階差解消。Codex v5.2.4 軽量再検証で APPROVED with minor notes を取得した段階で「Final」と「Final Approved」の使い分けが曖昧との指摘。本 v5.2.5 で「Final Approved」に統一し、§30.2 次プロセスから「Codex 軽量再検証 → Final Approved 化」の段階表現を削除。実装者が状態を一語で機械的に読める canonical SPEC に整理。
  - v5.2.5-N2 §16.5 Phase B+ 注記の旧版数依存表現を版数中立の現行 SPEC scope 宣言に書き換え。
              旧表現は v5.2.4 正本の読者に stale に見える (patch cycle の判断記録ではなく現行 SPEC scope 宣言として読まれる)。
              括弧書きで「v5.2.2 patch cycle で HL 制限の事実のみ反映、以降の patch でも scope 外を維持」と履歴を保持。
  - 設計内容 (戦略、Phase 構造、API、schema、enum、Solidity ABI、運用 flow、
    着手条件 4 件、全 NN ルール) は v5.2.4 から完全不変
  - Codex は本 patch を自身が指摘した修正として直接適用 (再々検証不要)
  - 本 v5.2.5 をもって SPEC v5.2.x 系列は Final Approved 確定

Implementation may start ONLY AFTER 4 conditions are all met
(🚨 v5.2.1: §0.3 と完全一致するよう統一 — P0-7/P0-10):
  1. zen が本 v5.2.5 を読んで approval (ドキュメント確定)
  2. LP NFT custody 統合方針確定 = Option C 確定 (BnzaExVault 新規開発、
     Section 3.4 / 15.5.6)。Phase 0 開始前に deploy address / operator /
     multiSig を zen が確定
  3. Hyperliquid agent key 暗号化方式 = Phase A default Cloudflare Secrets
     Store 確定 (Section 21.5.2 / 21.5.2.1 runbook、P0-4)
  4. WL 5/15 ローンチ後の不安定期 gate (P0-10 で再定義、§0.3 と同一):
     5/15 は既了。過去 7 日 SAFE_MODE ゼロ・major incident なし、かつ
     zen が「POOL ローンチ後の不安定期を脱した」と判定した時点
     (Section 22.6 / §0.3 参照)

Review process (v5.0 から維持):
  1. v5.0 → GPT / Codex validation (完了)
  2. Final corrections incorporated → v5.1 (本書、完了)
  3. v5.1 final sanity corrections → v5.2 Final Candidate (本書、完了)
  4. zen approval → Phase 0 着手
  5. Phase 0 (Backtest + PositionCalculator + HL testnet) 開始

Implementation start: TBD (Phase 0 着手日は zen が確定)
Phase A1 開始予定: Phase 0 完了 + 1-2 週間後 (見積もり)
Public Launch (Phase B 移行): 14-18 週間後 (Q3-Q4 2026 想定、Section 22.6)
```

### 30.1 Defer List Summary (v5.1 まとめ)

```yaml
Phase A では実装しない (Defer):
  - 16 D1 shards         → Phase C
  - Analytics Engine     → Phase B
  - R2 raw log archive   → Phase B (debug log は CF Logs / Tail)
  - DLQ operator UI      → Phase B (admin が直接 D1 query で代用)
  - Multi-RPC failover   → Phase C (Phase A は single RPC、必要なら fallback alert)
  - LP range ladder      → Phase 2 (Defer)
  - Revert Lend (LP Plus)→ Defer (Phase 3)
  - AI Pro               → Defer (Phase 3)
  - Multiple bot per user→ Phase B+ (Section 16.5)
  - Per-record funding ledger → Phase C (Phase A は daily aggregate)
  - Aggressive hedge mode (90%+) → Phase 3 (Defer)
```

### 30.2 v5.2.5 Final Approved Statement

```yaml
v5.1 では v5.0 の戦略・インフラ方針は維持し 22 必須修正を反映。
v5.2 は final sanity check の軽微修正のみ。
v5.2.1 は 3 AI Final 承認検証の統合結果 P0 11 件を直接パッチ。

🚨 v5.2.2: Codex 再検証 (2026-05-19) で発覚した「P0 修正の
canonical 化が一部 section に届いていない」同期漏れ 5 件を v5.2.1 に
直接パッチした。設計思想の問題ではなく波及範囲の同期。構造変更・
根本見直しは行っていない。
  - 戦略骨子・インフラ骨子は v5.2 から不変
  - v5.2.2-P0-1〜5 はすべて canonical ルール (bps / chunking helper /
    vaultXxx ABI / envelope schema / 1 bot=1 subaccount) を SPEC 全体へ
    完全伝播させたもの (§30 patch list)
  - grep ベースで全 section の伝播を検証済み (実施レポート参照)

🚨 v5.2.3: v5.2.2 (3 AI: Codex / GPT / Claude Code いずれも
APPROVED) に対し、Claude Code 検証時に摘出した P1/P2 のうち Final
ブロッカーではないが SPEC 内部矛盾を解消する 3 件のみ doc-sync した。
構造変更ゼロ。設計思想・API・schema・enum 値・Solidity ABI・運用
flow すべて v5.2.2 から不変。
  - v5.2.3-P1-A §21.5.4 sanitize regex を envelope encryption fields も
    redact (dek/master.*key パターン + 列名明記、defense-in-depth)
  - v5.2.3-P1-B §10.1 hedge-sync queue / §17.2 hedgeSync 関数引数を
    canonical RebalanceReason[] (§7.6 P0-11) に型統一 (runtime 不変)
  - v5.2.3-P2-A §0.3 着手条件 1 の版数 staleness 修正 (§30 と完全一致)
  - Codex 軽量再検証で APPROVED 取得済 (本日)

🚨 v5.2.4: v5.2.3 までは過去 patch の precise diff を別紙
PATCH_NOTES.md (SPEC_v5.2_to_v5.2.1_PATCH_NOTES.md /
SPEC_v5.2.1_to_v5.2.2_PATCH_NOTES.md /
SPEC_v5.2.2_to_v5.2.3_PATCH_NOTES.md) に分離していた。v5.2.4 では
これら外部参照を削除し、本 SPEC §30 patch chain を patch サマリの
canonical source とすることで SPEC_v5.2.4.md 単体で自己完結する状態を
達成した。設計内容 (戦略・インフラ骨子・API・schema・enum・Solidity
ABI・運用 flow・着手条件・全 NN ルール) は v5.2.3 から完全不変。
過去 PATCH_NOTES.md の precise diff は git history に保存され、
git log / git show で復元可能。

🚨 v5.2.5 (本版): Codex v5.2.4 軽量再検証で「APPROVED with minor notes」を取得後、指摘された minor notes 2 件を反映した。Final 化を妨げる問題はなかったが、zen の "妥協なし、再発防止" 原則に従い canonical SPEC として完成度を上げるため極小 patch を適用。
  - v5.2.5-N1 §30 Status を「Final」→「Final Approved」に統一。
              §30.2 次プロセスから「Codex 軽量再検証 → Final Approved 確定」の段階表現を削除し、状態を一語で機械的に読める形に整理。
  - v5.2.5-N2 §16.5 Phase B+ 注記を版数中立「本 SPEC では」に書き換え、
              括弧書きで v5.2.2 patch cycle の履歴を保持。
設計内容は v5.2.4 から完全不変。Codex 自身が指摘した修正のため再々検証不要。
本 v5.2.5 をもって SPEC v5.2.x 系列は Final Approved 確定、Phase 0 着手可能
(4 件の着手条件は §0.3 / §30 を参照)。

次プロセス: 本 v5.2.5 は Final Approved 確定。Phase 0 着手条件 4 件 (§0.3 / §30) のうち、条件 2 (BnzaExVault deploy address / operator / multiSig) と 条件 4 (WL 5/15 後の不安定期 gate / 過去 7 日 SAFE_MODE ゼロ・major incident なし) を zen 側で確定後、Phase 0 着手。
構造変更ゼロのため GPT / Claude Code / Codex の v5.2.5 再検証は不要 (数学的妥当性 / SPEC 統合視点 / 実装可能性視点は v5.2.4 まで取得済の APPROVED がそのまま有効、Codex 摘出 minor notes も v5.2.5 で反映済)。

着手条件 (4 件、§0.3 / §30 で完全一致):
  1. zen の v5.2.5 approval (本 v5.2.5 minor notes 反映まで確定後)
  2. Option C (BnzaExVault 新規開発) — deploy/operator/multiSig 確定
  3. Cloudflare Secrets Store KMS 設計 freeze
  4. WL 5/15 後の不安定期 gate (過去 7 日 SAFE_MODE ゼロ・incident なし)
全項目 summary: 22 項目 = §28.A.3 / P0 11 件 + 同期漏れ 5 件 +
doc-sync 3 件 + 自己完結化 1 件 + minor notes 反映 2 件 = §30 patch chain 全体。
```

---

End of Document.
