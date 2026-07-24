# BnzaExVault Smart Contract Architecture

**Version:** v5.2.6  
**Status:** Implementation in progress (contracts + batch deploy + fork/unit tests + CI coverage)  
**Scope:** EXBOT — dual-venue strategy bot (Uniswap LP + Hyperliquid allocation)  
**Chains:** Base / Optimism (fork tests use Ethereum mainnet Uniswap + USDC)  
**Last Updated:** 2026-07-03 (multi-token vault, white-label net routing, `pullTokenForStrategy`)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Diagram Summary](#2-architecture-diagram-summary)
3. [Contract Inventory](#3-contract-inventory)
4. [Contract Descriptions](#4-contract-descriptions)
   - [BnzaExVault](#41-bnzaexvault)
   - [Strategy Contracts](#42-strategy-contracts)
   - [BnzaExPositionManager](#43-bnzaexpositionmanager)
   - [TokenRouter](#44-tokenrouter)
   - [RedemptionQueue](#45-redemptionqueue)
   - [EOA Addresses](#46-eoa-addresses)
   - [Third-Party Contracts](#47-third-party-contracts)
5. [Key Flows](#5-key-flows)
   - [Deposit + Fund Allocation Flow](#51-deposit--fund-allocation-flow)
   - [Redeem Flow](#52-redeem-flow)
   - [Rebalance Flow](#53-rebalance-flow)
   - [Fee Distribution Flow](#54-fee-distribution-flow)
   - [Collect Fee Flow](#55-collect-fee-flow)
6. [Roles & Authority Matrix](#6-roles--authority-matrix)
   - [Role Hierarchy](#61-role-hierarchy)
7. [Storage Pattern (ERC-7201)](#7-storage-pattern-erc-7201)
8. [Folder Structure](#8-folder-structure)
   - [Coding Conventions](#81-coding-conventions)
   - [Deploy & Testing](#82-deploy--testing)
9. [Security Model](#9-security-model)
10. [Integration with Off-Chain Operator](#10-integration-with-off-chain-operator)
11. [Design Principles & Non-Negotiable Rules](#11-design-principles--non-negotiable-rules)
12. [Appendix A: Key DataTypes](#appendix-a-key-datatypes)
13. [Appendix B: Custom Errors](#appendix-b-custom-errors)
14. [Appendix C: Events](#appendix-c-events)

---

## 1. Overview

BnzaExVault is the dedicated Solidity contract suite for the **BNZA Ex Bot**.

**Core concept:**

- Investors deposit into `BnzaExVault` per **`botId`** (primary quote token **USDC** by default; admin-allowlisted tokens supported — see **§4.1**), which **custodies deposits** until the Operator deploys them
- **`withdraw`** — investor recalls **unspent capital** (deposit token not yet allocated by the strategy)
- **`redeem` (product flow)** — investor **liquidates all positions** via POOL UI → **Operator relay** → `executeStrategy(RedeemStrategyV1, …)` (no dedicated on-chain `redeem` on the vault)
- The **strategy allocates deployed funds across two legs**: a **Uniswap portion** (on-chain LP) and a **Hyperliquid portion** (off-chain, via EXBOT Agent Wallet)
- `BnzaExVault` validates the requested strategy against the allowlist, then delegates to the appropriate Strategy contract
- LP NFTs received from Uniswap are held and managed by `BnzaExPositionManager` — investors cannot touch them directly
- LP operations (Open / Rebalance / Redeem) are handled by stateless Strategy contracts; new strategies can be added without changing the core architecture
- On **redeem**, all positions are liquidated: Uniswap leg settles on-chain immediately; Hyperliquid leg asynchronously via **Redemption Queue**
- Fees: **`LpFeeOps`** — 50 bps operation fee on open (USDC); earned-fee paths (redeem/rebalance/collect) charge op + 30% PF in **pair currency** via `TokenRouter`; BNZA buyback on open burns via configured recipient
- **White-label (WL):** when `wlMaster[user][botId]` is set, **earned LP fee net** (redeem / rebalance / collect) and **HL redemption profit** route to the WL master; **principal** always stays with the investor

**Investor exit paths:**

| Function              | When                                                            | Effect                                                             |
| --------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------ |
| `withdraw`            | Capital is **unspent** for a given **botId** (not yet deployed) | Returns idle deposit token for that bot                            |
| Redeem (via Operator) | Positions **exist** for a **botId** (capital deployed)          | Operator calls `executeStrategy(RedeemStrategyV1, user, botId, …)` |

**What this contract suite does NOT require from investors:**

- Any approval or delegation on Hyperliquid — investors do not set up HL agent wallets or grant trading authority on HL
- Any direct Hyperliquid interaction — fund allocation to the HL leg is handled by the Operator as part of strategy execution

**Terminology — Agent Wallet (EXBOT):**

In this architecture, **Agent Wallet** is the **EXBOT-operated wallet that receives the Hyperliquid-allocated portion** of deposited funds (and related token flows when that portion is moved or returned). It is **not** Hyperliquid's user-facing _agent wallet_ concept (where an end user approves a delegate to trade on their HL account). Do not conflate the two.

**Fund allocation model:**

| Leg                 | Venue                   | What happens on deposit/open                                                    |
| ------------------- | ----------------------- | ------------------------------------------------------------------------------- |
| Uniswap portion     | On-chain (Uniswap V3)   | Strategy swaps and mints LP; NFT held by `BnzaExPositionManager`                |
| Hyperliquid portion | Off-chain (Hyperliquid) | Strategy allocates the remaining share; tokens route via EXBOT **Agent Wallet** |

---

## 2. Architecture Diagram Summary

![BnzaExVault Architecture Diagram](architecture.png)

The diagram defines **two end-to-end flows**: **Deposit + fund allocation** (top) and **Redeem** (bottom).

### 2.1 Deposit + Fund Allocation (top diagram)

```
Investor ──(Deposit USDC)──► BnzaExVault ◄──(Execute Strategies)── Operator
                                    │
                             check allowlist
                                    │ Delegate
                                    ▼
┌───────────────────────────────────────────────────────────────────┐
│                        STRATEGY LAYER                             │
│  OpenPositionStrategyV1                                           │
│    • Allocates funds: Uniswap portion + Hyperliquid portion       │
│    • Uniswap: BNZA buyback + swap + NFPM.mint → PositionManager   │
└─────────────┬───────────────────────────────┬─────────────────────┘
              │ Uniswap portion               │ Hyperliquid portion
              ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│   Uniswap V3                │   │   Hyperliquid (off-chain)       │
│   V3Factory / NFPM /        │   │   Allocated funds ──►           │
│   V3SwapRouter              │   │   EXBOT Agent Wallet            │
│   WETH-USDC pool + LP NFT   │   │                                 │
└─────────────────────────────┘   └─────────────────────────────────┘
              │
              ▼ (fees on open / rebalance / redeem / collect)
┌───────────────────────────────────────────────────────────────────┐
│              FEE DISTRIBUTION (LpFeeOps → TokenRouter)            │
│  Open: USDC op fee (50 bps) → PerformanceFeeRecipient             │
│  Earned: op + PF in pair currency → configured recipients         │
│  BNZA buyback on open → BNZARecipient → Blackhole (0x0000)        │
└───────────────────────────────────────────────────────────────────┘
```

**Fund allocation on open:**

- Strategy splits deposited USDC per allocation policy (Uniswap portion + Hyperliquid portion)
- **Uniswap portion:** swapped and minted as LP on-chain; NFT registered in `BnzaExPositionManager`
- **Hyperliquid portion:** allocated off-chain; tokens route to the EXBOT **Agent Wallet** (see terminology above)
- Operator runs preflight checks (one-bot policy, LP simulation, Operator capacity) before calling `executeStrategy`
- **Investors do not approve anything on Hyperliquid**

**On-chain vs off-chain split on open:**

| Leg                 | Who triggers                                        | Where it executes                                                |
| ------------------- | --------------------------------------------------- | ---------------------------------------------------------------- |
| Uniswap portion     | Investor deposits; Operator calls `executeStrategy` | On-chain (`BnzaExVault` → `OpenPositionStrategyV1` → Uniswap V3) |
| Hyperliquid portion | Operator after Uniswap portion completes            | Off-chain (allocated via EXBOT Agent Wallet)                     |

### 2.2 Redeem (bottom diagram)

Redeem is a **two-step** flow. The **Uniswap leg** settles synchronously on-chain in the same transaction; the **Hyperliquid leg** is released asynchronously via the redemption queue.

```
Uniswap leg — immediate on-chain liquidation (same transaction):

Investor ──(Redeem request via POOL UI)──► Operator
                            │
                            └── executeStrategy(redeemStrategy, user, params)
                                        │ Delegate
                                        ▼
                                RedeemStrategyV1
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
 BnzaExPositionManager   Uniswap V3     TokenRouter
 (de-register position)  (remove LP      (earned fees →
                          liquidity)       Platform Fee Recipient)
            │               │
            └───────┬───────┘
                    ▼
            Payback ──► Investor wallet
            (Uniswap portion, same tx)

Hyperliquid leg — async release (Operator-fulfilled):

RedeemStrategyV1 ──► Redemption Queue ──(RequestCreated)──► Operator
                                                            │
                            close HL hedge (Agent Wallet)   │
                            approve queue + fulfillRequest  ▼
                                              RedemptionQueue ──► Investor wallet
                                              (FIFO pop, on-chain token payout)
```

**Uniswap leg — liquidate immediately:**

1. Operator calls `executeStrategy(redeemStrategy, user, botId, params)` on `BnzaExVault` (investor initiates via POOL UI relay)
2. `RedeemStrategyV1` de-registers the position in `BnzaExPositionManager` and `releaseNft`s the LP NFT to the strategy
3. `NFPM.decreaseLiquidity` + `collect` — **earned vs principal** split per token (BnzaRouter `_closeAndPayout` parity)
4. **Earned leg:** op/PF in **pair currency** via `LpFeeOps` → `TokenRouter` (dust threshold; no USDC swap on fees)
5. **Principal leg:** paid to user in pair currency by default; optional `convertPrincipalToUsdc` → `vault.payToUser(usdc, user, amount)`
6. `recordPositionClosed` → `vault.notifyPositionCapitalChange(…, CLOSED)`

**Hyperliquid leg — redemption queue:**

1. `RedeemStrategyV1` calls `redemptionQueue.createRequest(user, botId, tokenId, hlPortionId)` — one request per closed position; **multiple pending requests per bot** are allowed
2. Request is enqueued FIFO (`DoubleEndedQueue`); Operator is notified via `RequestCreated` (+ D1 sync)
3. Operator closes the Hyperliquid hedge off-chain; proceeds land in EXBOT **Agent Wallet**
4. Operator approves `RedemptionQueue` for payout token(s) and calls `fulfillRequest(fulfillments)` — **pops queue head**, pays principal to user and WL profit (if any) on-chain, emits `RequestFulfilled`

**Two distinct actor roles:**

- **Investor** — deposits USDC; `withdraw` for unspent capital; requests redeem via POOL UI (Operator signs `executeStrategy`)
- **Operator** — `executeStrategy` for open / redeem / rebalance / collect fees; routes HL-portion flows via EXBOT Agent Wallet; **fulfills Redemption Queue** entries

`BnzaExVault` checks against the **BNZA-USDC Pool** when opening a position. A 0.5% fee-tier swap on that pool is used to buy back BNZA tokens.

---

## 3. Contract Inventory

### EXBOT Contracts (new deployments)

| Contract                 | Type          | Deployment      | Purpose                                                                                                |
| ------------------------ | ------------- | --------------- | ------------------------------------------------------------------------------------------------------ |
| `BnzaExVault`            | Core          | Base + Optimism | Multi-token deposit custody; strategy dispatch via `executeStrategy`; investor deposit / withdraw only |
| `OpenPositionStrategyV1` | Strategy      | Base + Optimism | LP position open logic                                                                                 |
| `RedeemStrategyV1`       | Strategy      | Base + Optimism | LP redeem / liquidation logic; creates HL redemption requests                                          |
| `RebalanceStrategyV1`    | Strategy      | Base + Optimism | LP position rebalance logic; earned-fee payout on rebalance                                            |
| `CollectFeeStrategyV1`   | Strategy      | Base + Optimism | Operator collect of accrued LP fees (pair currency, §21.2)                                             |
| `BnzaExPositionManager`  | Manager       | Base + Optimism | LP NFT custody; multi-position ledger per user                                                         |
| `TokenRouter`            | Router        | Base + Optimism | Routes USDC and BNZA fees to the correct recipients                                                    |
| `RedemptionQueue`        | Queue         | Base + Optimism | Stores pending Hyperliquid-portion redemption requests awaiting Operator fulfillment                   |
| `ExbotAddressesProvider` | Registry      | Base + Optimism | On-chain address book for one EXBOT deployment (upgrade / indexing)                                    |
| `ExbotSetupBatch`        | Deploy helper | Per deploy tx   | Batch-deploys implementations, proxies, strategies, and wiring via `deployExbot`                       |

### EOA Addresses

These are plain wallet addresses, not smart contracts. `TokenRouter` sends funds directly to them; no contract code is involved.

| Address                   | Role                    | Receives                 | Notes                                                                                                     |
| ------------------------- | ----------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------- |
| `PerformanceFeeRecipient` | Admin wallet(s)         | USDC                     | Up to 10 separate EOA addresses; share ratios set by Operator                                             |
| `BNZARecipient`           | Burn address            | BNZA                     | Transfers BNZA onward to `Blackhole (0x0000)` for permanent burn                                          |
| `Agent Wallet`            | EXBOT settlement wallet | USDC / HL-portion tokens | Receives the Hyperliquid-allocated portion of strategy funds — **not** an HL user agent-delegation wallet |

### Third-Party Contracts

| Contract                            | Provider    | Purpose                                                                 |
| ----------------------------------- | ----------- | ----------------------------------------------------------------------- |
| `BNZA-USDC Pool`                    | Uniswap V3  | BNZA / USDC swap pool; used for BNZA buyback (0.5% fee tier)            |
| `WETH-USDC Pool`                    | Uniswap V3  | Primary LP pool for EXBOT positions (fee tier per deployment config)    |
| `V3Factory`                         | Uniswap V3  | Pool address resolution and existence check                             |
| `NonfungiblePositionManager (NFPM)` | Uniswap V3  | LP NFT mint / decreaseLiquidity / collect / burn                        |
| `V3SwapRouter`                      | Uniswap V3  | Token swap execution                                                    |
| `Hyperliquid`                       | Hyperliquid | Off-chain venue for the Hyperliquid portion of strategy fund allocation |

---

## 4. Contract Descriptions

### 4.1 BnzaExVault

The central contract of the EXBOT suite. **Investors** call `deposit` and `withdraw` (unspent capital) on-chain. **All strategy work** — open, redeem, rebalance, collect fees — is dispatched by the **Operator** via `executeStrategy`. The vault **custodies investor deposits** (USDC by default; admin-allowlisted ERC-20s per **§4.1**) until the Operator allocates them; LP NFTs are held separately by `BnzaExPositionManager`.

**Responsibilities:**

- Accepts and holds deposits from investors (`deposit`) until deployed by the Operator
- **Multi-token custody:** admin allowlist via `setAllowedDepositToken`; first deposit **binds** `botDepositToken[user][botId]`; per-token `unspentBalance` / `deployedCapital`
- Allows investors to **`withdraw` unspent capital** — deposit token not yet allocated by the strategy
- **Redeem (liquidate all positions)** is a **product flow**, not a vault entry point: POOL UI → Operator → `executeStrategy(RedeemStrategyV1, user, params)`
- Only the **Operator** may call `executeStrategy` (open, redeem, rebalance, collect fees, etc.)
- Validates that the requested strategy is registered in `registeredStrategies` mapping (with `StrategyExecutionOption`)
- Delegates execution via `StrategyExecutionLogic` (`CALL`, `DELEGATE_CALL`, or `STATIC_CALL`)
- Exposes admin controls via multi-sig (`DEFAULT_ADMIN_ROLE`: rotate operator, strategy registry, wiring, deposit-token allowlist, WL master binding)
- **`EMERGENCY_ROLE`** (dedicated emergency wallet / multi-sig): `pause`, `unpause`, and **`emergencyTransfer(user, botId)`** when paused — returns unspent **deposit token** plus every LP NFT for `(user, botId)` to `user` without on-chain liquidation
- **White-label:** `setBotWlMaster` / `unsetBotWlMaster` — strategies read `wlMasterOf(user, botId)` for earned-fee and HL profit routing (see **§4.1 WL**)

**Interface (excerpt):**

```solidity
interface IBnzaExVault {
  // Investor — capital is scoped per (user, botId)
  /// Primary quote token (USDC) overloads:
  function deposit(bytes32 botId, uint256 amount) external;
  function withdraw(bytes32 botId, uint256 amount) external;

  /// Allowlisted token (binds on first deposit):
  function deposit(bytes32 botId, address token, uint256 amount) external;
  function withdraw(bytes32 botId, address token, uint256 amount) external;

  // Operator-only — all strategy paths (open, redeem, rebalance, collect fees, …)
  function executeStrategy(
    address strategy,
    address user,
    bytes32 botId,
    bytes calldata params
  ) external returns (bytes memory result);

  /// EMERGENCY_ROLE only, whenPaused — return unspent deposit token + all LP NFTs for (user, botId) to user.
  function emergencyTransfer(address user, bytes32 botId) external;

  // Emergency (EMERGENCY_ROLE)
  function pause() external;
  function unpause() external;

  // Multi-sig admin (DEFAULT_ADMIN_ROLE)
  function rotateOperator(address oldOperator, address newOperator) external;
  function registerStrategy(
    address strategy,
    DataTypes.StrategyExecutionOption operation,
    bytes calldata extraParams
  ) external;
  function removeStrategy(address strategy) external;
  function setAllowedDepositToken(address token, bool allowed) external;
  function setBotWlMaster(address user, bytes32 botId, address master) external;
  function unsetBotWlMaster(address user, bytes32 botId) external;

  // Read-only
  function usdc() external view returns (address);
  function botDepositToken(
    address user,
    bytes32 botId
  ) external view returns (address);
  function isAllowedDepositToken(address token) external view returns (bool);
  function wlMasterOf(
    address user,
    bytes32 botId
  ) external view returns (address);
  function unspentBalance(
    address user,
    bytes32 botId
  ) external view returns (uint256);
  function unspentBalance(
    address user,
    bytes32 botId,
    address token
  ) external view returns (uint256);
  function deployedCapital(
    address user,
    bytes32 botId
  ) external view returns (uint256);
  function deployedCapital(
    address user,
    bytes32 botId,
    address token
  ) external view returns (uint256);
  function isAuthorizedOperator(address account) external view returns (bool);
  function isAuthorizedEmergency(address account) external view returns (bool);
  function isAllowedStrategy(address strategy) external view returns (bool);
}
```

**Multi-token custody:**

| Rule                | Behaviour                                                                                                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Allowlist           | Only `isAllowedDepositToken(token) == true` may be deposited (USDC enabled at `initialize`)                                                                                                                    |
| Binding             | First `deposit(botId, token, …)` sets `botDepositToken[user][botId] = token`                                                                                                                                   |
| Later deposits      | Must use the **same** token or revert `DepositTokenMismatch`                                                                                                                                                   |
| USDC overloads      | `deposit(botId, amount)` / `withdraw(botId, amount)` use vault `usdc`                                                                                                                                          |
| Open position today | `OpenPositionStrategyV1` pulls **USDC** via `pullTokenForStrategy(…, usdc, …)`. Non-USDC deposit tokens are supported for fund/withdraw; LP open requires USDC until strategies accept the bound deposit token |

**White-label routing:**

| Flow                                          | Principal                | Earned / profit net                              |
| --------------------------------------------- | ------------------------ | ------------------------------------------------ |
| Redeem / rebalance / collect (LP earned fees) | User                     | `wlMasterOf(user, botId)` if non-zero, else user |
| `RedemptionQueue.fulfillRequest` (HL leg)     | User (`principalAmount`) | WL master (`profitAmount`) when `wlMaster` set   |
| Open operation fee                            | N/A                      | Protocol via `TokenRouter` (unchanged)           |

Strategies emit **`WlNetSent(wlRecipient, user, botId, source, token, amount)`** on WL net payouts (`source`: 0=collect, 1=rebalance, 2=redeem) for off-chain indexing (see EXBOT WL spec mirror in `docs/WL_SPECv1.7.6_EN.md`).

**Vault strategy hooks** (callable only by registered strategies via `onlyRegisteredStrategy`):

```solidity
interface IVaultStrategyHooks {
  function pullTokenForStrategy(
    address user,
    bytes32 botId,
    address token,
    uint256 amount
  ) external;
  function payToUser(address token, address user, uint256 amount) external;
  function wlMasterOf(
    address user,
    bytes32 botId
  ) external view returns (address);
  function usdc() external view returns (address);
}
```

`payToUser` transfers `amount` of `token` from the **calling strategy** to `user` (`safeTransferFrom` — strategy must approve the vault first).

**Position-manager → vault capital ledger** (callable only by `BnzaExPositionManager`):

```solidity
interface IBnzaExVaultPositionLedger {
  function notifyPositionCapitalChange(
    address user,
    bytes32 botId,
    uint256 tokenId,
    uint256 deployedAmount,
    DataTypes.PositionCapitalChange change
  ) external;
}
```

---

### 4.2 Strategy Contracts

All strategy contracts are **stateless**. They contain only execution logic and **constructor immutables** — no persistent state and **no ERC-7201 storage**. Upgradeable core contracts (`BnzaExVault`, `BnzaExPositionManager`, etc.) use ERC-7201; strategies are deployed as plain, non-upgradeable contracts.

---

#### OpenPositionStrategyV1

Opens a new position by **allocating deposited USDC** across Uniswap and Hyperliquid per strategy policy. Triggered by the Operator via `BnzaExVault.executeStrategy` after the investor has deposited and Operator preflight has passed.

**Fees on open:** a single **operation fee** (default **50 bps**, `LpFeeOps.DEFAULT_OPERATION_FEE_BPS`) is deducted from the LP leg in USDC and routed via `TokenRouter` before mint. There is no separate swap fee on open.

**Execution steps (Uniswap portion — on-chain):**

1. `vault.pullTokenForStrategy(user, botId, usdc, totalUsdc)` — moves USDC from `(user, botId)` unspent balance to the strategy
2. BNZA buyback slice → `V3SwapRouter` → `TokenRouter.depositToken(BNZA, …)`
3. Hyperliquid slice → direct `safeTransfer` to `agentWallet` (not via TokenRouter)
4. LP leg: deduct operation fee → swap/mint via `UniswapOps` → NFT minted to `BnzaExPositionManager`
5. `positionManager.recordPositionOpened(…, botId, …)` — updates PM ledger + `vault.notifyPositionCapitalChange(…, botId, OPENED)`
6. Return surplus pair tokens to the investor

**Returns:** `DataTypes.OpenPositionResult` (tokenId, allocation breakdown, `operatorFeeUsdc`).

---

#### RedeemStrategyV1

Handles **redeem** (liquidate all positions) when invoked by the Operator via `BnzaExVault.executeStrategy`. Uniswap LP settles in the same transaction; Hyperliquid portion release is enqueued for async fulfillment. Close behaviour aligns with BnzaRouter `_closeAndPayout`: **earned** vs **principal** split after `decreaseLiquidity` + `collect`.

**Uniswap leg — immediate liquidation (same transaction):**

1. `positionManager.unregisterPosition(tokenId)`
2. `positionManager.releaseNft(tokenId, strategy)` — PM releases NFT to strategy (`IERC721.transferFrom`)
3. `NFPM.decreaseLiquidity` + `NFPM.collect` — split `fee = total − principal` per token
4. **Earned leg:** op/PF in **pair currency** via `LpFeeOps` (dust threshold on close; no USDC swap on fees)
5. **Principal leg:** paid to user in pair currency by default (`convertPrincipalToUsdc = false`); optional `payToUser(usdc, user, amount)` when `convertPrincipalToUsdc = true` (strategy swaps to USDC, approves vault, vault pays user)
6. `positionManager.recordPositionClosed(tokenId, user)` — PM marks deployment inactive + `vault.notifyPositionCapitalChange(…, CLOSED)`

**Hyperliquid leg — redemption request (async):**

7. `redemptionQueue.createRequest(user, botId, tokenId, hlPortionId)`
8. Operator closes HL hedge off-chain, approves queue, and calls `fulfillRequest(fulfillments)` — pops FIFO head; principal → user, profit → WL master when configured

**Note:** There is no on-chain `redeem` on `BnzaExVault`. Redeem, rebalance, and collect-fee paths all use `executeStrategy` with the appropriate allowlisted strategy.

---

#### RebalanceStrategyV1

Repositions the LP range when the price moves out of bounds, or when instructed by the Operator.

**Execution steps:**

1. `positionManager.releaseNft(oldTokenId, strategy)`
2. `NFPM.decreaseLiquidity` at 100% + `NFPM.collect` — split earned vs principal
3. If earned > dust threshold: `LpFeeOps.payoutEarnedFees` (pair currency op/PF, no USDC swap)
4. Rebalance token ratio via `V3SwapRouter` if needed; `NFPM.mint` → new NFT to `BnzaExPositionManager`
5. `positionManager.transferPosition(oldTokenId, newTokenId, user)` + `updatePosition(newTokenId, ticks, liquidity)`
6. Refund surplus pair tokens to user

**Note:** The old NFT remains on the strategy contract with zero liquidity (not returned to PM). Only the new `tokenId` is custodied by `BnzaExPositionManager`.

**Returned value:** `abi.encode(newTokenId, oldTokenId)`.

---

#### CollectFeeStrategyV1

Operator-only collect of **accrued Uniswap V3 LP fees** without removing liquidity (Spec §21.2 / §21.5.3).

**Execution steps:**

1. `positionManager.releaseNft(tokenId, strategy)` — strategy holds NFT for `NFPM.collect`
2. `NFPM.collect` → fees to strategy
3. `IERC721(nfpm).transferFrom(strategy, positionManager, tokenId)` — return NFT custody to PM
4. `LpFeeOps.payoutEarnedFees` — net fees to user in **pair currency**; op/PF via `TokenRouter` in native tokens; **$10 USDC-equivalent dust threshold** (pool-price conversion, USDC-paired pools only)

**Params:** `tokenId` alone uses `LpFeeOps.defaultCollectFeeParams()`; optional `(tokenId, CollectFeeParams)`.

---

### 4.3 BnzaExPositionManager

Receives LP NFTs from Uniswap's `NonfungiblePositionManager` after a mint, and acts as the on-chain registry for **multiple bots and positions per user** (keyed by `(user, botId)`). It holds LP NFTs and is the sole contract that strategies interact with to borrow or return an NFT.

**Responsibilities:**

- Custodies LP NFTs minted to this contract
- **`recordPositionOpened`** — stores `botId` on `PositionInfo`, increments per-bot `positionId`, notifies vault (`OPENED`)
- **`recordPositionClosed`** — marks deployment inactive, notifies vault (`CLOSED`)
- **`unregisterPosition`** — removes tokenId from user set before close (redeem path)
- **`updatePosition`** — tick/liquidity update after rebalance mint
- **`transferPosition(oldTokenId, newTokenId, owner)`** — rebalance registry migration (same `positionId`, new NFT)
- **`releaseNft(tokenId, to)`** — executor-only; `IERC721.transferFrom(PM, to, tokenId)` for strategy custody
- **Views:** `getBotPositionIds(user, botId)`, `getPositionDeployment(user, botId, positionId)`, `botIdForToken`, `deployedCapitalForPosition`, etc.

**Access:** vault proxy receives `EXECUTOR_ROLE` at `initialize` (for future vault-direct hooks). Strategy contracts receive `EXECUTOR_ROLE` via `grantExecutorAccess`.

---

### 4.4 TokenRouter

Helix-style deposit + withdraw routing. Admin configures recipients and withdrawal sources per token; authorized callers use symmetric entry points.

**Deposit path**

```solidity
setDepositTokenRecipient(usdc, performanceFeeRecipient);
depositToken(usdc, amount);  // caller → configured recipient
```

**Withdraw path** (for future fee recall / composability — sources must approve TokenRouter)

```solidity
setWithdrawTokenSources(usdc, [treasury, feeCollector, ...]);  // any number of sources
withdrawToken(usdc, amount);  // pull from sources → caller
availableToWithdraw(usdc);      // sum of source balances
```

**Investor withdraw (BnzaExVault)** — separate from TokenRouter; recalls **unspent** USDC for a bot only:

```solidity
vault.withdraw(botId, amount);  // msg.sender, capped at unspentBalance[msg.sender][botId]
```

Hyperliquid portion USDC in `OpenPositionStrategyV1` is sent directly to the agent wallet (not via TokenRouter).

---

### 4.5 RedemptionQueue

Stores **pending redemption requests** for the **Hyperliquid portion** created by `RedeemStrategyV1` at the end of the Uniswap close (same transaction). Pending request ids are kept in OpenZeppelin **`DoubleEndedQueue`** (FIFO); full request payloads live in a separate mapping. **No on-chain bot ownership registry** — `botId` is carried on each request for indexing only.

**Interface (excerpt):**

```solidity
interface IRedemptionQueue {
  function createRequest(
    address user,
    bytes32 botId,
    uint256 positionId,
    bytes32 hlPortionId
  ) external returns (uint256 requestId);

  /// @notice Pops the queue head (FIFO). Operator must approve this contract for each payout token.
  function fulfillRequest(
    DataTypes.RedemptionFulfillment[] calldata fulfillments
  ) external returns (uint256 requestId);

  function getRequest(
    uint256 requestId
  ) external view returns (DataTypes.RedemptionRequest memory);
  function pendingQueueLength() external view returns (uint256);
  function nextPendingRequestId() external view returns (uint256);
  function pendingRequestAt(uint256 index) external view returns (uint256);
}

struct RedemptionFulfillment {
  address token;
  uint256 principalAmount; // always → queued user
  uint256 profitAmount; // → user, or wlMasterOf(user, botId) when WL
}
```

**Responsibilities:**

- `createRequest(user, botId, positionId, hlPortionId)` — `REQUESTER_ROLE` (`RedeemStrategyV1` only); enqueues at the back; **multiple concurrent pending requests per `(user, botId)`** are allowed
- `fulfillRequest(fulfillments)` — `OPERATOR_ROLE`; pops the queue head (no `requestId` argument), transfers HL proceeds from operator via `safeTransferFrom`, splits principal vs profit per token line, marks request fulfilled
- `nextPendingRequestId()` — peek at FIFO head without fulfilling
- `pendingQueueLength()` / `pendingRequestAt(index)` / `getRequest(requestId)` — dashboard / D1 queries
- Emits `RequestCreated` / `RequestFulfilled` for D1 sync and alerting

**Operator fulfillment steps:**

1. Receive `RequestCreated` / D1 webhook (use `nextPendingRequestId()` + `getRequest` to inspect head)
2. Close Hyperliquid hedge; collect proceeds to EXBOT **Agent Wallet**
3. Approve `RedemptionQueue` for each payout token
4. Call `fulfillRequest(fulfillments)` — on-chain payout (principal → user, WL profit → master) + queue pop; repeat for each pending entry in FIFO order
5. Update D1 bot / position status

---

### 4.6 EOA Addresses

These are plain externally owned accounts, not smart contracts. `TokenRouter` transfers funds directly to them after calculating the split inside the Strategy contracts.

**Performance Fee Recipient**

Up to 10 separate EOA addresses configured by the Operator. Each receives a proportional share of the USDC performance fee.

```
Performance fee = Gross PnL × 30%
    → depositToken(USDC, amount) ──► PerformanceFeeRecipient EOA
```

- Recipient is set by admin via `setDepositTokenRecipient(usdc, …)` (single EOA or downstream splitter contract)
- Each Admin receives USDC directly to their wallet — no contract logic involved
- Maximum 10 recipients (per §2.3)

**BNZA Recipient**

A single EOA (or the zero address `0x0000...`) that receives BNZA tokens for permanent burn.

```
Operation fee = 100% BuyBack & Burn (BNZA token)
    → depositToken(BNZA, amount) ──► BNZARecipient ──► Blackhole (0x0000)
```

- Receives BNZA from `TokenRouter` and forwards it to `0x0000` for permanent destruction
- No contract logic; the burn is achieved by transferring to the non-recoverable zero address

---

### 4.7 Third-Party Contracts

#### BNZA-USDC Pool

An existing Uniswap V3 pool. `BnzaExVault` checks it before dispatching a strategy. A 0.5% fee-tier swap on this pool is used to **buy back BNZA tokens** — it is not involved in acquiring the paired LP token for position opening.

#### Uniswap V3

The external infrastructure for creating and managing LP positions.

| Contract                            | Used for                                         |
| ----------------------------------- | ------------------------------------------------ |
| `V3Factory`                         | Pool address resolution and existence check      |
| `NonfungiblePositionManager (NFPM)` | LP NFT mint / decreaseLiquidity / collect / burn |
| `V3SwapRouter`                      | Token swap execution                             |

---

## 5. Key Flows

### 5.1 Deposit + Fund Allocation Flow

On deposit/open, the strategy **splits funds** between Uniswap (on-chain) and Hyperliquid (off-chain).

```
Step 0 — Preflight (off-chain, before any on-chain open):

Investor ──► POOL UI: deposit USDC + start Ex Bot (no HL setup required)
Operator ──► preflight checks (one-bot policy, LP simulation, Operator capacity)

─────────────────────────────────────────────────────────────────────

Step 1 — Investor deposits (on-chain):

Investor ──(Deposit USDC)──► BnzaExVault  (USDC held until deployed, or `withdraw` if still unspent)

─────────────────────────────────────────────────────────────────────

Step 2 — Operator executes strategy: Uniswap portion (on-chain):

Operator ──(Execute Strategies)──► BnzaExVault
    │
    ├── Check: strategy is on the allowlist
    │
    └── Delegate ──► OpenPositionStrategyV1
            │
            ├── allocate Uniswap portion; deduct 50 bps op fee (LpFeeOps)
            ├── BNZA-USDC Pool (0.5%): BNZA buyback from strategy slice
            ├── V3SwapRouter + NFPM.mint → tokenId to BnzaExPositionManager
            │                           └── recordPositionOpened + vault.notifyPositionCapitalChange(OPENED)
            │
            └── surplus tokens ──► investor wallet

Post: Operator records positions row in D1 (Uniswap leg complete)

─────────────────────────────────────────────────────────────────────

Step 3 — Operator executes strategy: Hyperliquid portion (off-chain):

Operator ──► allocate Hyperliquid portion per strategy policy
    │
    └── funds route to EXBOT Agent Wallet (Hyperliquid portion)

Post: D1 updated with both legs; bot lifecycle → active
```

---

### 5.2 Redeem Flow

**Redeem liquidates all positions.** The Operator signs `executeStrategy(RedeemStrategyV1, …)` on behalf of the investor (POOL UI relay). Uniswap LP settles on-chain immediately; the Hyperliquid portion is queued for Operator fulfillment.

```
Investor ──(Redeem via POOL UI)──► Operator
    │
    └── executeStrategy(redeemStrategy, user, botId, abi.encode(tokenId))
            │
            └──► RedeemStrategyV1  — Uniswap leg (same transaction)
            │
            ├── BnzaExPositionManager.unregisterPosition(tokenId)
            ├── positionManager.releaseNft(tokenId, strategy)
            ├── NFPM.decreaseLiquidity(tokenId, 100%) + NFPM.collect
            ├── LpFeeOps: earned op/PF in pair currency → TokenRouter (dust threshold)
            ├── PrincipalPaid to user (pair currency, or `payToUser(usdc, …)` if convertPrincipalToUsdc)
            └── recordPositionClosed → vault.notifyPositionCapitalChange(CLOSED)  ✅ immediate

    └──► RedeemStrategyV1  — Hyperliquid leg (queue, end of same tx)
            │
            ├── RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId)
            └── emit RequestCreated ──► notify Operator

─────────────────────────────────────────────────────────────────────

Operator fulfillment (async):

Operator receives RequestCreated / D1 alert
    │
    ├── close / settle Hyperliquid hedge (proceeds → EXBOT Agent Wallet)
    ├── approve RedemptionQueue for HL payout token(s)
    ├── RedemptionQueue.fulfillRequest(fulfillments)  — FIFO pop + on-chain pay to queued user
    └── D1: position / bot status updated
```

**Timing guarantees:**

| Leg                              | When settled                                      | Who executes                                                              |
| -------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------- |
| Uniswap portion                  | Same block as `executeStrategy` (redeem)          | `RedeemStrategyV1` on-chain                                               |
| Hyperliquid portion              | After Operator `fulfillRequest` (on-chain payout) | Operator (Agent Wallet → queue → user)                                    |
| Earned LP fees / performance fee | Same block as redeem / rebalance / collect        | `LpFeeOps` → `TokenRouter` (pair currency on earned; USDC op fee on open) |

**Failure handling:**

- Uniswap liquidation failure → entire `executeStrategy` reverts; LP NFT and position record unchanged
- HL portion release failure after Uniswap close → Uniswap portion already returned; request stays `pending` in Redemption Queue; Operator retries or escalates

---

### 5.3 Rebalance Flow

```
Operator detects rangeState != 'in' (off-chain monitoring)
    │
    └── Operator ──► BnzaExVault.executeStrategy(
            rebalanceStrategy,
            user,
            abi.encode(tokenId, rebalanceParams)
        )
            │
            └──► RebalanceStrategyV1
                    ├── releaseNft(oldTokenId, strategy)
                    ├── NFPM.decreaseLiquidity + collect → LpFeeOps on earned (if above dust)
                    ├── V3SwapRouter: rebalance ratio (if needed) + NFPM.mint → newTokenId
                    ├── transferPosition(old, new) + updatePosition(new ticks, liquidity)
                    └── SurplusRefunded to user

Returns: abi.encode(newTokenId, oldTokenId)
Post: Operator updates D1 with newTokenId and new tick range,
      then runs hedge-sync from confirmed post-rebalance LP amount
```

---

### 5.4 Fee Distribution Flow

Fee logic is centralized in **`LpFeeOps`** (Spec §21.2 — EXBOT only). Defaults: **50 bps operation fee**, **30% performance fee** on earned amounts, **$10 USDC-equivalent dust threshold** before enforcing earned-fee payout on close/rebalance/collect.

| Path                             | Fee base                       | Routing                                                                                                                                           |
| -------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Open**                         | LP USDC leg                    | `chargeOperationFeeUsdc` → `TokenRouter.depositToken(USDC)` (50 bps only; no swap fee)                                                            |
| **Redeem / Rebalance / Collect** | Earned portion after `collect` | Op + PF deducted in **pair currency**; protocol legs → `TokenRouter`; **net earned** → user, or **WL master** when `wlMasterOf(user, botId) != 0` |
| **Principal (redeem)**           | Remaining liquidity            | Always **user** (pair currency or USDC via `convertPrincipalToUsdc`)                                                                              |
| **HL fulfill**                   | Operator-provided amounts      | `principalAmount` → user; `profitAmount` → WL master when configured                                                                              |

```
OpenPositionStrategyV1
    └── LpFeeOps.chargeOperationFeeUsdc ──► TokenRouter ──► PerformanceFeeRecipient (USDC)

RedeemStrategyV1 / RebalanceStrategyV1 / CollectFeeStrategyV1
    └── LpFeeOps.payoutEarnedFees(netRecipient = user or wlMaster)
            ├── op fee (50 bps default) ──► TokenRouter ──► configured recipient per token
            └── PF (30% default)      ──► TokenRouter ──► configured recipient per token
            └── net earned ──► user or WL master (+ WlNetSent when WL)
```

BNZA buyback on open still routes purchased BNZA through `TokenRouter` to the configured burn recipient.

---

### 5.5 Collect Fee Flow

Operator-only path for accrued LP fees **without** removing liquidity (Spec §21.5.3).

```
Operator ──► BnzaExVault.executeStrategy(
        collectFeeStrategy,
        user,
        abi.encode(tokenId)   // or abi.encode(tokenId, collectFeeParams)
    )
        └──► CollectFeeStrategyV1
                ├── releaseNft → NFPM.collect → return NFT to PM
                └── LpFeeOps.payoutEarnedFees (dust threshold, pair currency)
```

---

## 6. Roles & Authority Matrix

| Role                             | `deposit` | `withdraw`                | `executeStrategy`                             | `fulfillRedemption` | `emergencyTransfer` | `pause/unpause` | `rotateOperator` | `registerStrategy` |
| -------------------------------- | --------- | ------------------------- | --------------------------------------------- | ------------------- | ------------------- | --------------- | ---------------- | ------------------ |
| **Investor**                     | ✅        | ✅ (unspent capital only) | ❌                                            | ❌                  | ❌                  | ❌              | ❌               | ❌                 |
| **Operator** (`OPERATOR_ROLE`)   | ❌        | ❌                        | ✅ (open, redeem, rebalance, collect fees, …) | ✅                  | ❌                  | ❌              | ❌               | ❌                 |
| **Emergency** (`EMERGENCY_ROLE`) | ❌        | ❌                        | ❌                                            | ❌                  | ✅ (when paused)    | ✅              | ❌               | ❌                 |
| **Admin** (`DEFAULT_ADMIN_ROLE`) | ❌        | ❌                        | ❌                                            | ❌                  | ❌                  | ❌              | ✅               | ✅                 |
| **External / Anyone**            | ❌        | ❌                        | ❌                                            | ❌                  | ❌                  | ❌              | ❌               | ❌                 |

**Investor capabilities (on-chain):**

- `deposit(botId, amount)` or `deposit(botId, token, amount)` — fund a bot before open (token must match bound deposit token after first deposit)
- `withdraw(botId, amount)` or `withdraw(botId, token, amount)` — recall **unspent capital** for that bot
- **Redeem** — off-chain / POOL UI request; Operator signs `executeStrategy(RedeemStrategyV1, user, botId, params)`

**Operator authority details:**

- All strategy paths use `executeStrategy(…, botId, …)` — protected by `OPERATOR_ROLE` (`AccessControl`)
- Operator **fulfills Redemption Queue** via `fulfillRequest(fulfillments)` — closes HL hedge off-chain, approves queue, on-chain principal/profit split (FIFO; no `requestId` argument)
- The operator key is EXBOT-dedicated
- The key is stored with envelope encryption via Cloudflare Secrets Store

**Emergency authority details:**

- Holds `EMERGENCY_ROLE` on `BnzaExVault` (dedicated emergency wallet or multi-sig — **`EMERGENCY_ADDRESS`** at deploy)
- **`pause()` / `unpause()`** — halts or resumes investor `deposit`/`withdraw` and operator `executeStrategy`
- **`emergencyTransfer(user, botId)`** — **`whenPaused` only**; for `(user, botId)`:
  1. Transfers full **unspent balance in the bound deposit token** (`botDepositToken`, or `usdc` if unset) to `user`
  2. For each LP NFT in `getBotPositionIds(user, botId)`: unregisters, `releaseNft` to `user`, `recordPositionClosed` (decrements per-token `deployedCapital`)
- Does **not** liquidate LP on-chain, recover Hyperliquid balances, or sweep `TokenRouter` funds
- Reverts `NothingToRecover(user, botId)` if no unspent balance and no tracked positions
- Emits **`EmergencyRecovery(user, botId, token, amountReturned, tokenIds[])`**

**Admin details:**

- Holds `DEFAULT_ADMIN_ROLE` (multi-sig)
- `rotateOperator`, `registerStrategy` / `removeStrategy`, proxy upgrades via `ProxyAdmin`

### 6.1 Role Hierarchy

On-chain access uses **OpenZeppelin `AccessControl`** on each upgradeable core contract. Role constants live in `ExbotRoles.sol`. Each proxy has its **own role namespace** — granting `OPERATOR_ROLE` on `BnzaExVault` does not grant it on `TokenRouter`.

Strategy allowlisting on the vault uses the **`registeredStrategies` mapping**, not an AccessControl role.

#### Actor layers (off-chain → on-chain)

```
┌─────────────────────────────────────────────────────────────────┐
│  ProxyAdmin (multi-sig)                                         │
│  Upgrades Transparent proxy implementations — not AccessControl │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  DEFAULT_ADMIN_ROLE (multi-sig, one holder per core contract)   │
│  Administers registry + wiring on that proxy (not pause)        │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
    ┌───────────▼──────────┐      ┌───────────▼──────────────────┐
    │  OPERATOR_ROLE       │      │  EMERGENCY_ROLE (vault only)  │
    │  (hot operator EOA)  │      │  (cold emergency wallet)      │
    └───────────┬──────────┘      └───────────┬──────────────────┘
                │                             │
                │              ┌──────────────┼──────────────┐
                │              │              │              │
                │         EXECUTOR_ROLE  REQUESTER_ROLE   pause / unpause /
                │         (vault + strategies)  (RedeemStrategyV1)  emergencyTransfer
                │
    ┌───────────▼──────────┐
    │  Investor (no role)  │
    │  deposit / withdraw  │
    └──────────────────────┘
```

#### Role tree per contract

| Contract                  | Role                               | Typical holder                       | Granted by                                    | Protected actions                                                                                       |
| ------------------------- | ---------------------------------- | ------------------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **All core contracts**    | `DEFAULT_ADMIN_ROLE`               | Multi-sig                            | `initialize(admin)`                           | Role grants, registry, config setters                                                                   |
| **BnzaExVault**           | `OPERATOR_ROLE`                    | Operator EOA                         | Admin (`initialize` / `rotateOperator`)       | `executeStrategy`, `executeStrategyStatically`                                                          |
| **BnzaExVault**           | `EMERGENCY_ROLE`                   | Emergency wallet / multi-sig         | Admin (`initialize`)                          | `pause`, `unpause`, `emergencyTransfer` (when paused)                                                   |
| **TokenRouter**           | `OPERATOR_ROLE`                    | Operator EOA + registered strategies | Admin (`setAuthorizedOperator`)               | `depositToken`, `withdrawToken`                                                                         |
| **BnzaExPositionManager** | `EXECUTOR_ROLE`                    | Vault proxy + strategy contracts     | Admin (`initialize` / `grantExecutorAccess`)  | `recordPositionOpened/Closed`, `unregisterPosition`, `updatePosition`, `transferPosition`, `releaseNft` |
| **RedemptionQueue**       | `VAULT_ROLE`                       | Vault proxy                          | Admin (`initialize` / `setVault`)             | Reserved vault identity (future hooks)                                                                  |
| **RedemptionQueue**       | `OPERATOR_ROLE`                    | Operator EOA                         | Admin (`initialize`)                          | `fulfillRequest`                                                                                        |
| **RedemptionQueue**       | `REQUESTER_ROLE`                   | `RedeemStrategyV1`                   | Admin (`grantRequesterAccess`)                | `createRequest`                                                                                         |
| **BnzaExVault**           | _(mapping)_ `registeredStrategies` | Strategy contract addresses          | Admin (`registerStrategy` / `removeStrategy`) | Vault hooks: `pullTokenForStrategy`, `payToUser`, `wlMasterOf`; PM calls `notifyPositionCapitalChange`  |

In OpenZeppelin `AccessControl`, **`DEFAULT_ADMIN_ROLE` is the admin of every custom role** on that contract unless `setRoleAdmin` is overridden (EXBOT does not override it).

#### Deploy-time grant wiring

Production deploy uses **`ExbotSetupBatch.deployExbot`** (`src/deploy/ExbotSetupBatch.sol`), Foundry scripts under **`deploy/`** (`.s.sol`), and shell helpers under **`scripts/`**. Wiring is performed inside `_wireDeployment`:

```solidity
// 1. Vault strategy registry (allowlist + execution mode)
vault.registerStrategy(openStrategy,       DataTypes.StrategyExecutionOption.CALL, "");
vault.registerStrategy(redeemStrategy,     DataTypes.StrategyExecutionOption.CALL, "");
vault.registerStrategy(rebalanceStrategy,    DataTypes.StrategyExecutionOption.CALL, "");
vault.registerStrategy(collectFeeStrategy,   DataTypes.StrategyExecutionOption.CALL, "");

// 2. PositionManager EXECUTOR_ROLE — vault proxy gets this at initialize; strategies via grantExecutorAccess
positionManager.grantExecutorAccess(openStrategy, true);
positionManager.grantExecutorAccess(redeemStrategy, true);
positionManager.grantExecutorAccess(rebalanceStrategy, true);
positionManager.grantExecutorAccess(collectFeeStrategy, true);

// 3. TokenRouter authorized operators (strategies + operator EOA)
tokenRouter.setAuthorizedOperator(openStrategy, true);
tokenRouter.setAuthorizedOperator(redeemStrategy, true);
tokenRouter.setAuthorizedOperator(rebalanceStrategy, true);
tokenRouter.setAuthorizedOperator(collectFeeStrategy, true);
tokenRouter.setAuthorizedOperator(operator, true);

redemptionQueue.grantRequesterAccess(redeemStrategy, true);

// 4. TokenRouter recipients (admin config)
tokenRouter.setDepositTokenRecipient(usdc, performanceFeeRecipient);
tokenRouter.setDepositTokenRecipient(pairedToken, performanceFeeRecipient); // WETH earned leg
tokenRouter.setDepositTokenRecipient(bnzaToken, bnzaBurnRecipient);
```

**Deploy:** copy `.env.example` → `.env`, fill `ADMIN_ADDRESS`, `OPERATOR_ADDRESS`, `EMERGENCY_ADDRESS`, RPC URLs, then:

**Recommended deploy order:** Sepolia testnet first (MockUSDC → EXBOT), then Base + Optimism mainnet.

```bash
# 1. Mintable test USDC
BROADCAST=1 ./scripts/deploy-mock-usdc.sh
# → set USDC_ADDRESS in .env to logged address

# 2. EXBOT stack
./scripts/deploy-phase1.sh                    # simulate Sepolia (default)
BROADCAST=1 ./scripts/deploy-phase1.sh sepolia
BROADCAST=1 ./scripts/deploy-phase1.sh base   # mainnet after testnet validation
```

Or `npm run deploy:mock-usdc:broadcast` then `deploy:phase1:sepolia:broadcast`.

**Deployed testnet addresses:** [`docs/DEPLOYED_ADDRESSES.md`](DEPLOYED_ADDRESSES.md)  
**Front-end / back-end integration:** [`docs/INTEGRATION.md`](INTEGRATION.md) (strategy calls, params, events)

**Deploy caveat:** `registerStrategy`, `grantExecutorAccess`, and related admin calls require `msg.sender` = `DEFAULT_ADMIN_ROLE` holder. When invoking `deployExbot` through the batch contract, set **`input.admin` to the batch/deployer contract address** (or split wiring into a follow-up admin transaction). See `test/ExbotSetupBatchDeploy.t.sol`.

#### Runtime call chain (who acts as `msg.sender`)

```
Investor ──deposit/withdraw──► BnzaExVault                    (no role)

Operator ──executeStrategy──► BnzaExVault                     (OPERATOR_ROLE)
                                    │
                                    └── CALL ──► Strategy       (vault is msg.sender on strategy)
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────┐
                    ▼                                 ▼                             ▼
            vault hooks                      PositionManager                   TokenRouter
     (onlyRegisteredStrategy)          (EXECUTOR_ROLE on strategy)      (OPERATOR_ROLE on strategy)
                    │                                 │                             │
                    └─────────────────────────────────┴─────────────────────────────┘
                                                      │
                              RedemptionQueue ◄── REQUESTER_ROLE (RedeemStrategyV1 only)
```

#### Separation of duties

| Concern                               | Role / mechanism                            | Rationale                                                             |
| ------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------- |
| Day-to-day strategy execution         | `OPERATOR_ROLE` on vault                    | Hot key; can be rotated without upgrading contracts                   |
| Fee routing from strategies           | `OPERATOR_ROLE` on TokenRouter (strategies) | Strategies never hold fee recipient addresses                         |
| LP ledger mutations                   | `EXECUTOR_ROLE` on PositionManager          | Only allowlisted strategy bytecode can move NFTs                      |
| Hyperliquid queue intake              | `REQUESTER_ROLE` on RedemptionQueue         | Only redeem strategy enqueues HL redemption requests                  |
| Strategy bytecode allowlist           | `registeredStrategies` on vault             | Vault hooks reject unregistered callers even if they hold other roles |
| Emergency pause + user fund recovery  | `EMERGENCY_ROLE` on vault                   | Cold emergency wallet; cannot call `executeStrategy`                  |
| Strategy registry + operator rotation | `DEFAULT_ADMIN_ROLE`                        | Cold multi-sig; cannot pause or execute strategies                    |
| Implementation upgrades               | `ProxyAdmin` (outside AccessControl)        | Upgrade path isolated from operator key                               |

---

## 7. Storage Pattern (ERC-7201)

All contracts in this suite use **ERC-7201 Namespaced Storage** for application state, plus **OpenZeppelin `AccessControlUpgradeable`** / **`PausableUpgradeable`** for roles and pause. Core contracts deploy behind **Transparent Upgradeable Proxies** (`ProxyAdmin` manages upgrades — not UUPS).

**BnzaExVault storage example:**

```solidity
// BnzaExVaultStorage.sol
abstract contract BnzaExVaultStorage {
    /// @custom:storage-location erc7201:bnza.storage.BnzaExVault
    struct VaultStorage {
        /// @notice Primary quote token (legacy field; default for USDC overloads)
        address usdc;

        /// @notice BnzaExPositionManager proxy address
        address positionManager;

        /// @notice TokenRouter proxy address
        address tokenRouter;

        /// @notice Legacy per-user per-bot unspent USDC (deprecated — do not write)
        mapping(address => mapping(bytes32 => uint256)) unspentBalance;

        /// @notice Legacy deployed capital in USDC units (deprecated — do not write)
        mapping(address => mapping(bytes32 => uint256)) deployedCapital;

        /// @notice WL master recipient per (user, botId); zero = regular bot
        mapping(address => mapping(bytes32 => address)) wlMaster;

        /// @notice Registered strategy configuration keyed by strategy contract address
        mapping(address => DataTypes.RegisteredStrategy) registeredStrategies;

        /// @notice Admin allowlist for investor deposit tokens
        mapping(address => bool) allowedDepositTokens;

        /// @notice Deposit token bound on first deposit for (user, botId)
        mapping(address => mapping(bytes32 => address)) botDepositToken;

        /// @notice Per-token unspent balances keyed by (user, botId, token)
        mapping(address => mapping(bytes32 => mapping(address => uint256))) unspentBalanceByToken;

        /// @notice Per-token deployed capital keyed by (user, botId, token)
        mapping(address => mapping(bytes32 => mapping(address => uint256))) deployedCapitalByToken;
    }

    /// @dev 0x74ebde7f6ba3c0c6f2b7644d316d0f7dfd7139622179d4cea188e8dc96dce600
    bytes32 private constant VAULT_STORAGE_LOCATION = /* ERC-7201 slot */;

    function _getVaultStorage() internal pure returns (VaultStorage storage $) {
        assembly { $.slot := VAULT_STORAGE_LOCATION }
    }
}
```

**AccessControl roles** (`ExbotRoles` library + `BnzaExInitializable`):

| Contract                | Roles                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `BnzaExVault`           | `OPERATOR_ROLE` — strategy dispatch; `EMERGENCY_ROLE` — pause / unpause / emergency recovery |
| `TokenRouter`           | `OPERATOR_ROLE` — `depositToken`, `withdrawToken`                                            |
| `BnzaExPositionManager` | `EXECUTOR_ROLE` — vault proxy (at init) + strategy contracts                                 |
| `RedemptionQueue`       | `VAULT_ROLE`, `OPERATOR_ROLE` (fulfill), `REQUESTER_ROLE` (create)                           |

**BnzaExPositionManager storage (excerpt):**

```solidity
struct PositionManagerStorage {
  address nfpm;
  address vault;
  mapping(uint256 => DataTypes.PositionInfo) positions;
  mapping(address => mapping(bytes32 => EnumerableSet.UintSet)) botPositionIds;
  mapping(address => mapping(bytes32 => uint256)) botPositionCounter;
  mapping(address => mapping(bytes32 => mapping(uint256 => DataTypes.PositionDeployment))) positionDeployments;
}
```

Vault strategy allowlisting uses `registeredStrategies` mapping — not AccessControl roles.

**Storage rules:**

- **Upgradeable core contracts** — all state variables live inside an ERC-7201 Storage struct; `_get<Name>Storage()` is always `internal pure`
- **Strategy contracts** — stateless; no ERC-7201 scaffold; only `immutable` constructor wiring
- Every storage field is annotated with `/// @notice`

---

## 8. Folder Structure

```
src/
├── deploy/
│   ├── ExbotDeploymentTypes.sol        # ExbotDeployInput, ExbotDeployReport
│   ├── ExbotAddressesProvider.sol      # On-chain address registry
│   ├── ExbotSetupBatch.sol             # deployExbot() batch orchestration
│   └── IExbotAddressesProvider.sol
│
├── interfaces/
│   ├── IBnzaExVault.sol
│   ├── IBnzaExVaultPositionLedger.sol
│   ├── IVaultStrategyHooks.sol
│   ├── IStrategy.sol
│   ├── IBnzaExPositionManager.sol
│   ├── ITokenRouter.sol
│   └── IRedemptionQueue.sol
│
├── dependencies/
│   └── uniswap-v3/                     # NFPM, SwapRouter, Factory, math libs
│
├── misc/
│   ├── BnzaExInitializable.sol
│   └── ExbotRoles.sol
│
├── protocol/
│   ├── library/
│   │   ├── helpers/Errors.sol
│   │   ├── logic/
│   │   │   ├── StrategyExecutionLogic.sol
│   │   │   ├── UniswapOps.sol
│   │   │   └── LpFeeOps.sol            # Shared fee math (§21.2)
│   │   └── types/DataTypes.sol
│   │
│   ├── bnza-ex-vault/
│   ├── bnza-ex-position-manager/
│   ├── token-router/
│   ├── redemption-queue/
│   └── strategies/
│       ├── OpenPositionStrategyV1.sol
│       ├── RedeemStrategyV1.sol
│       ├── RebalanceStrategyV1.sol
│       └── CollectFeeStrategyV1.sol
│
└── instance/                           # Transparent proxy shells
    ├── BnzaExVault.sol
    ├── BnzaExPositionManager.sol
    ├── TokenRouter.sol
    └── RedemptionQueue.sol

deploy/                                 # Foundry on-chain deploy scripts (.s.sol)
├── DeployMockUSDC.s.sol                # Sepolia mintable USDC (deploy before EXBOT)
├── DeployExbotSepolia.s.sol            # Ethereum Sepolia (uses USDC_ADDRESS or Circle USDC)
├── DeployExbot.s.sol
├── DeployExbotBase.s.sol
└── DeployExbotOP.s.sol

scripts/                                # Shell helpers (invoke forge script)
├── deploy-mock-usdc.sh
└── deploy-phase1.sh

test/
├── utils/
│   ├── ExbotForkTestBase.sol           # Shared mainnet fork fixtures + deploy helper
│   └── MockERC20.sol
├── ExbotSetupBatchDeploy.t.sol         # Full stack deploy via batch
├── BnzaExVaultDeposit.t.sol            # Unit test (mock USDC)
└── BnzaExVaultDeposit.fork.t.sol       # Fork example (inherits ExbotForkTestBase)
```

---

## 8.1 Coding Conventions

All implementation contracts in this suite follow a consistent layout:

**Function ordering (strict):**

1. `external` — state-changing
2. `public` — state-changing
3. `external view` / `external pure`
4. `public view` / `public pure`
5. `internal`
6. `private`

Within each group, related functions are grouped logically (initializer → user flows → admin → hooks → views → internals).

**Other rules:**

- Custom errors only — no `require(..., "string")`
- Events declared at the top of each contract, before functions
- Modifiers declared after the constructor, before the first `external` function
- Upgradeable core contracts use ERC-7201 namespaced storage; strategy contracts are stateless (constructor immutables only)

---

## 8.2 Deploy & Testing

### Batch deploy

- **`ExbotSetupBatch.deployExbot(ExbotDeployInput)`** — deploys implementations, transparent proxies, four strategies, and wiring; registers addresses in **`ExbotAddressesProvider`**
- Foundry scripts: `deploy/DeployExbotSepolia.s.sol` (testnet first), then `DeployExbotBase.s.sol` / `DeployExbotOP.s.sol` — env vars in `.env.example`

### Tests

```bash
cd contracts/bnza-exbot
forge test                                    # unit tests (no RPC)
FOUNDRY_PROFILE=fork forge test --match-path "*fork*"   # requires MAINNET_RPC_URL in .env
```

- **`test/utils/ExbotForkTestBase.sol`** — mainnet fork at block `25_321_950` (override via `MAINNET_FORK_BLOCK`), USDC whale funding, `_deployExbotStack()` helper
- **`test/ExbotSetupBatchDeploy.t.sol`** — end-to-end deploy + wiring smoke test

---

## 9. Security Model

### 9.1 Access Control

See **[§6.1 Role Hierarchy](#61-role-hierarchy)** for the full role tree, deploy wiring, and runtime `msg.sender` chain.

Summary:

```
DEFAULT_ADMIN_ROLE (multi-sig, per core contract):
  - rotateOperator, registerStrategy / removeStrategy
  - grantExecutorAccess, setAuthorizedOperator, grantRequesterAccess
  - Transparent proxy upgrades via ProxyAdmin (outside AccessControl)

EMERGENCY_ROLE (cold emergency wallet / multi-sig — vault only):
  - pause / unpause
  - emergencyTransfer(user, botId) when paused — unspent deposit token + all LP NFTs → user

OPERATOR_ROLE (hot operator EOA — separate namespace per contract):
  - BnzaExVault: executeStrategy
  - TokenRouter: depositToken, withdrawToken
  - RedemptionQueue: fulfillRequest

Contract-scoped roles (granted by admin, not held by humans):
  - EXECUTOR_ROLE — vault proxy + strategy contracts on PositionManager
  - REQUESTER_ROLE — RedeemStrategyV1 on RedemptionQueue
  - VAULT_ROLE — vault proxy on RedemptionQueue only (reserved)

registeredStrategies mapping (BnzaExVault):
  - Allowlisted strategy addresses + StrategyExecutionOption
  - Required for vault hook callbacks (independent of other role grants)

Investor (no AccessControl role):
  - deposit(botId, …), withdraw(botId, …) (unspent capital only)
  - Redeem via POOL UI → Operator executeStrategy(RedeemStrategyV1, user, botId, …)
```

### 9.2 LP NFT Protection

- LP NFTs are held by `BnzaExPositionManager` after being received from Uniswap's NFPM
- Users cannot accidentally transfer or revoke approval on the NFT
- Strategies retrieve the NFT from `BnzaExPositionManager` only during a sanctioned close or rebalance
- **`emergencyTransfer(user, botId)`** (`EMERGENCY_ROLE`, when paused): last-resort path to return unspent vault USDC and all LP NFTs for that bot directly to the investor wallet without on-chain liquidation

### 9.3 USDC Custody Model

- `BnzaExVault` **holds user USDC deposits** after `deposit` and before the Operator executes strategy allocation
- Deposited USDC is **not** automatically deployed in the deposit transaction — it remains in the vault until the Operator calls `executeStrategy`
- **Unspent capital:** investor may **`withdraw(botId, …)`** to recall USDC not yet allocated for that bot
- **Deployed capital:** investor must request **redeem** via POOL UI; Operator signs `executeStrategy(RedeemStrategyV1, user, botId, …)` — `withdraw` does not apply once funds are deployed
- **Strategy deployment** of USDC to externals (Uniswap, `TokenRouter`, Hyperliquid portion via Agent Wallet, etc.) is **Operator-only**
- On redeem, Uniswap LP is liquidated and the Uniswap portion is paid to the investor **in the same transaction** (pair currency and/or `payToUser` per `RedeemParams`)
- Hyperliquid portion proceeds are paid **on-chain** by `RedemptionQueue.fulfillRequest` from the Operator / Agent Wallet — not held in the vault

### 9.4 Redemption Queue Safety

- Uniswap close must complete (LP de-registered, principal/earned paid, `recordPositionClosed`) before `RedemptionQueue.createRequest` is called in the same transaction
- **Multiple pending HL requests** may exist for the same `(user, botId)` (multi-position bots); fulfillment is strictly **FIFO** via `fulfillRequest` (no `requestId` argument)
- Operator must approve the queue for payout tokens; `fulfillRequest` reverts if the queue is empty (`RedemptionQueueEmpty`) or payout arrays are invalid
- Stale queue entries trigger admin alert if unfulfilled beyond SLA (Operator monitoring)

### 9.5 Reentrancy Protection

- All state-changing functions use a `nonReentrant` modifier
- Follows the Check-Effects-Interactions pattern throughout

### 9.6 Slippage Protection

- All swap operations accept a `slippageBps` parameter
- If the actual output falls below the tolerance, the transaction reverts

---

## 10. Integration with Off-Chain Operator

This contract suite works in tandem with the **off-chain Operator** (Cloudflare Workers). The Operator is the transaction signer for all on-chain calls, executes the **fund allocation strategy** (Uniswap + Hyperliquid portions), and maintains D1 database state.

**Responsibility split:**

| Concern                               | On-chain (this suite)                                                         | Off-chain (Operator)                                                      |
| ------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Investor USDC deposit                 | ✅ `BnzaExVault.deposit(botId, …)`                                            | Preflight (LP simulation)                                                 |
| Investor withdraw (unspent capital)   | ✅ `BnzaExVault.withdraw(botId, …)`                                           | —                                                                         |
| Investor redeem (liquidate positions) | ✅ `executeStrategy(RedeemStrategyV1, user, botId, …)` (Uniswap LP immediate) | POOL UI relay + HL hedge close + `fulfillRequest`                         |
| Strategy execution / fund allocation  | ✅ Strategy contracts (Uniswap portion)                                       | ✅ Hyperliquid portion via EXBOT Agent Wallet                             |
| Redemption Queue                      | ✅ FIFO queue + `RequestCreated` / `RequestFulfilled`                         | ✅ HL close off-chain; on-chain payout via `fulfillRequest(fulfillments)` |
| LP NFT custody                        | ✅ BnzaExPositionManager                                                      | —                                                                         |
| Uniswap V3 interaction                | ✅ NFPM / SwapRouter calls                                                    | —                                                                         |
| Position metadata                     | ✅ BnzaExPositionManager                                                      | Synced to D1                                                              |
| Fee distribution                      | ✅ TokenRouter / EOA recipients                                               | Records result                                                            |
| LP amount calculation                 | ❌                                                                            | ✅ PositionAmountCalculator (AMM math)                                    |
| Drift detection / rebalance decision  | ❌                                                                            | ✅ light-check (Operator monitoring)                                      |
| Operator signing / settlement keys    | —                                                                             | ✅ Envelope encryption (Cloudflare Secrets Store)                         |

**Example on-chain call sequence during a redeem:**

```
Investor (via POOL UI):
  1. Submits redeem request (tokenId / params) to Operator backend

Operator (on-chain signer):
  2. executeStrategy(redeemStrategy, user, botId, abi.encode(tokenId))
       or executeStrategy(redeemStrategy, user, botId, abi.encode(tokenId, redeemParams))
       → RedeemStrategyV1: LP liquidated, Uniswap payback in same tx
       → RedemptionQueue.createRequest(user, botId, tokenId, hlPortionId)

Off-chain Operator:
  3. Receives RequestCreated event / D1 alert
  4. Close Hyperliquid hedge; proceeds to EXBOT Agent Wallet
  5. approve(RedemptionQueue, …); fulfillRequest(fulfillments)  — FIFO head, on-chain user payout
  6. Repeat step 5 while pendingQueueLength() > 0 (strict FIFO order)
  7. D1: update position / bot status
```

**Example on-chain call sequence during a rebalance:**

```
Off-chain Operator:
  1. light-check detects rangeState != 'in'
  2. Enqueues hedge-sync
  3. Applies a conservative partial delta-only hedge adjustment (before LP rebalance)
  4. executeStrategy(rebalanceStrategy, user, abi.encode(tokenId, rebalanceParams))
       → RebalanceStrategyV1 retrieves NFT from BnzaExPositionManager, re-mints at new range,
         updates BnzaExPositionManager with newTokenId
  5. Updates D1: positions.token_id = newTokenId, new tick range
  6. Runs final hedge-sync from confirmed post-rebalance LP amount
```

---

## 11. Design Principles & Non-Negotiable Rules

**Contract-level rules:**

| #    | Rule                                                                                                                                                                                                                                                    |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C-1  | LP NFTs are held by `BnzaExPositionManager`. Strategies retrieve them only during a sanctioned close or rebalance.                                                                                                                                      |
| C-2  | `BnzaExVault` custodies user USDC between deposit and Operator-driven deployment. `withdraw` applies to unspent capital; redeem liquidates all positions via `executeStrategy(RedeemStrategyV1, …)`. Strategy deployment to externals is Operator-only. |
| C-3  | Strategy contracts are stateless. All persistent state belongs to `BnzaExPositionManager`.                                                                                                                                                              |
| C-4  | Every state-changing function must emit at least one event. Avoid duplicate **semantic** events across strategy + PM/queue (e.g. one `PositionOpened` on PM, not also on the strategy).                                                                 |
| C-5  | `require(condition, "string")` is forbidden. Use `revert Errors.X()` exclusively.                                                                                                                                                                       |
| C-6  | Upgradeable core contracts use ERC-7201 namespaced storage. Strategy contracts are stateless (constructor immutables only) and do not use ERC-7201.                                                                                                     |
| C-7  | Operator authority (`OPERATOR_ROLE`) and Emergency authority (`DEFAULT_ADMIN_ROLE`) are strictly separated via OpenZeppelin `AccessControl`.                                                                                                            |
| C-8  | Adding a new strategy requires only adding it to `BnzaExVault`'s allowlist — no changes to core contracts.                                                                                                                                              |
| C-9  | The `OPERATOR_ROLE` key is EXBOT-dedicated and must not be shared with any other product's operator.                                                                                                                                                    |
| C-10 | Investors use `deposit` and `withdraw` (unspent capital) on-chain; redeem is initiated via POOL UI and executed by Operator through `executeStrategy`. Fund allocation and Hyperliquid-portion fulfillment are Operator-only.                           |
| C-11 | Uniswap redeem leg (liquidation + payback) must complete atomically in one transaction. Hyperliquid portion release is async via Redemption Queue (`fulfillRequest` pays on-chain).                                                                     |
| C-12 | Redemption Queue fulfillment is FIFO; Operator passes payout `tokens` / `amounts` from HL close proceeds — no `requestId` argument on fulfill.                                                                                                          |

**Additional constraints:**

| #   | Rule                                                                                                                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A-1 | Capital and positions are scoped by **`(user, botId)`**; a user may run multiple bots and **multiple concurrent positions / HL redemption requests** per bot |
| A-2 | Hedge ratio is fixed at 70% Balanced                                                                                                                         |
| A-3 | LP range is ±5% single-tier (range ladder not in current scope)                                                                                              |

---

## Appendix A: Key DataTypes

```solidity
library DataTypes {
  enum StrategyExecutionOption {
    NONE,
    CALL,
    DELEGATE_CALL,
    STATIC_CALL
  }
  enum PositionCapitalChange {
    OPENED,
    CLOSED
  }

  struct RegisteredStrategy {
    address strategy;
    StrategyExecutionOption operation;
    bytes extraParams;
  }

  struct OpenPositionParams {
    address pairedToken;
    address bnzaToken;
    uint24 lpPoolFee;
    uint24 bnzaBuybackFee;
    int24 tickLower;
    int24 tickUpper;
    uint256 totalUsdc;
    uint256 bnzaBuybackUsdc;
    uint256 swapAmount;
    uint256 amountOutMinimum;
    uint256 hlPortionUsdc;
    address agentWallet;
    uint256 deadline;
  }

  struct OpenPositionResult {
    bytes32 botId;
    uint256 tokenId;
    uint256 totalUsdc;
    uint256 bnzaBuybackUsdc;
    uint256 hlPortionUsdc;
    uint256 lpUsdcGross;
    uint256 lpUsdcNet;
    uint256 operatorFeeUsdc;
  }

  struct RedeemParams {
    uint256 performanceFeeBps;
    bytes32 hlPortionId;
    uint256 amountOutMinimum;
    bytes swapPath;
    uint256 deadline;
    bool convertPrincipalToUsdc;
  }

  struct RebalanceParams {
    int24 newTickLower;
    int24 newTickUpper;
    uint256 slippageBps;
    uint256 amountOutMinimum;
    uint256 deadline;
  }

  struct CollectFeeParams {
    uint256 operationFeeBps;
    uint256 performanceFeeBps;
    uint256 minEarnedUsdc;
  }

  struct PositionInfo {
    uint256 tokenId;
    address owner;
    bytes32 botId;
    address pool;
    int24 tickLower;
    int24 tickUpper;
    uint128 liquidity;
    uint256 openedAt;
    uint256 positionId;
  }

  struct PositionDeployment {
    uint256 tokenId;
    uint256 totalUsdc;
    uint256 uniswapUsdc;
    uint256 hyperliquidUsdc;
    bool active;
  }

  struct RedemptionRequest {
    uint256 requestId;
    address user;
    bytes32 botId;
    uint256 positionId;
    bytes32 hlPortionId;
    uint256 createdAt;
    bool fulfilled;
  }

  struct RedemptionFulfillment {
    address token;
    uint256 principalAmount;
    uint256 profitAmount;
  }
}
```

---

## Appendix B: Custom Errors

```solidity
library Errors {
  error Unauthorized(address caller);
  error NotMultiSig(address caller);
  error StrategyNotAllowed(address strategy);
  error VaultStrategyExecUnsupportedOperation();
  error VaultStrategyExecStaticOperationViolated();
  error VaultStrategyFailedToExec(
    address strategy,
    bytes data,
    DataTypes.StrategyExecutionOption operation
  );

  error PositionNotFound(uint256 tokenId);
  error PositionOwnerMismatch(
    uint256 tokenId,
    address expected,
    address actual
  );
  error NftOwnershipLost(uint256 tokenId);
  error PositionNotTrackedForUser(address user, uint256 tokenId);

  error InvalidBotId();
  error BotIdMismatch(bytes32 expected, bytes32 actual);
  error UserAlreadyHasPosition(address user);
  error NoActivePosition(address user);
  error CapitalAlreadyDeployed(address user);

  error SlippageExceeded(uint256 amountOut, uint256 minAmountOut);
  error ZeroLiquidity();
  error InsufficientBalance(uint256 available, uint256 required);
  error InsufficientWithdrawTokens();

  error RedemptionAlreadyFulfilled(uint256 requestId);
  error RedemptionNotFound(uint256 requestId);
  error RedemptionQueueEmpty();

  error ZeroAddress();
  error SameAddress();
  error ActiveTokenIdMismatch(address user, uint256 expected, uint256 actual);
  error InvalidParameter();
  error NotVault();
  error NotOperator();
  error FeeRecipientNotSet();
  error NothingToRecover(address user, bytes32 botId);
  error DepositTokenNotAllowed(address token);
  error DepositTokenMismatch(address expected, address actual);
}
```

---

## Appendix C: Events

```solidity
// BnzaExVaultImpl.sol
event Deposited(address indexed user, bytes32 indexed botId, address indexed token, uint256 amount);
event Withdrawn(address indexed user, bytes32 indexed botId, address indexed token, uint256 amount);
event AllowedDepositTokenSet(address indexed token, bool allowed);
event DepositTokenBound(address indexed user, bytes32 indexed botId, address indexed token);
event BotWlMasterSet(address indexed user, bytes32 indexed botId, address indexed master);
event BotWlMasterUnset(address indexed user, bytes32 indexed botId, address indexed oldMaster);
event StrategyExecuted(address indexed strategy, address indexed user, bytes32 indexed botId);
event StrategyRegistered(address indexed strategy, DataTypes.StrategyExecutionOption operation);
event EmergencyRecovery(
    address indexed user, bytes32 indexed botId, address indexed token, uint256 amountReturned, uint256[] tokenIds
);

// BnzaExPositionManagerImpl.sol
event PositionOpened(
    address indexed owner,
    bytes32 indexed botId,
    uint256 indexed positionId,
    uint256 tokenId,
    address pool,
    int24 tickLower,
    int24 tickUpper,
    uint128 liquidity,
    uint256 totalUsdc,
    uint256 uniswapUsdc,
    uint256 hyperliquidUsdc
);
event PositionClosed(
    address indexed owner, bytes32 indexed botId, uint256 indexed positionId, uint256 tokenId, uint256 totalUsdc
);
event PositionTransferred(uint256 indexed oldTokenId, uint256 indexed newTokenId, address indexed owner);
event PositionUpdated(uint256 indexed tokenId, int24 tickLower, int24 tickUpper, uint128 liquidity);

// OpenPositionStrategyV1.sol — ledger event is PM `PositionOpened` only
event BnzaBuybackExecuted(uint256 usdcIn, uint256 bnzaOut);
event HlPortionRouted(address indexed agentWallet, uint256 amount);
event SurplusRefunded(address indexed user, address indexed token, uint256 amount);

// RedeemStrategyV1.sol
event PositionLiquidated(address indexed user, uint256 indexed tokenId, uint256 principalUsdc);
event CloseFeesCollected(
    address indexed user,
    uint256 indexed tokenId,
    address token0,
    address token1,
    uint256 gross0,
    uint256 gross1,
    uint256 operationFee0,
    uint256 operationFee1,
    uint256 performanceFee0,
    uint256 performanceFee1
);
event PrincipalPaid(address indexed user, address token0, address token1, uint256 amount0, uint256 amount1);
event WlNetSent(
    address indexed wlRecipient, address indexed user, bytes32 indexed botId, uint8 source, address token, uint256 amount
);

// RebalanceStrategyV1.sol / CollectFeeStrategyV1.sol — same WlNetSent shape (source 0 or 1)

// RedemptionQueueImpl.sol — canonical HL queue events
event RequestCreated(
    uint256 indexed requestId, address indexed user, bytes32 indexed botId, uint256 positionId, bytes32 hlPortionId
);

// RebalanceStrategyV1.sol — ledger events are PM `PositionTransferred` + `PositionUpdated`
event RebalanceFeesCollected(/* same shape as CloseFeesCollected */);

// CollectFeeStrategyV1.sol
event FeesCollected(
    address indexed user,
    uint256 indexed tokenId,
    address token0,
    address token1,
    uint256 gross0,
    uint256 gross1,
    uint256 operationFee0,
    uint256 operationFee1,
    uint256 performanceFee0,
    uint256 performanceFee1
);

// RedemptionQueueImpl.sol
event RequestFulfilled(
    uint256 indexed requestId,
    address indexed user,
    bytes32 indexed hlPortionId,
    address operator,
    bytes32 botId,
    uint256 positionId,
    address wlRecipient,
    address[] tokens,
    uint256[] principalAmounts,
    uint256[] profitAmounts
);
```

---

_Documentation aligned with bnza-exbot contracts (Spec v5.2.6). Last reviewed 2026-07-03._
