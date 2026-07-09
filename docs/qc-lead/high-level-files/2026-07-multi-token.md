<!-- archived snapshot: current release also lives in ../DEPLOYED_ADDRESSES.md -->

# EXBOT deployed contract addresses (testnet)

Canonical list of on-chain deployments for EXBOT.
**Current release:** [`2026-07-multi-token`](releases/README.md) · **Integration:** [`INTEGRATION.md`](INTEGRATION.md)
**Last updated:** July 2026

**Latest redeploy:** Multi-token vault, unified pullTokenForStrategy API, full stack redeploy.

**Deployer / default roles** (admin, operator, proxy admin owner, performance fee recipient):
`0xCFE217b11Aed9B8018fbe2A19285A5B2A19E2369`

Older address sets: [`docs/releases/`](releases/README.md)

## Networks

| Network | chainId | Explorer | EXBOT stack | MockUSDC |
|---------|---------|----------|-------------|----------|
| Optimism Sepolia | `11155420` | [sepolia-optimism.etherscan.io](https://sepolia-optimism.etherscan.io) | Complete (July 2026) | Yes (reused) |
| Arbitrum Sepolia | `421614` | [sepolia.arbiscan.io](https://sepolia.arbiscan.io) | Complete (July 2026) | Yes (reused) |
| Ethereum Sepolia | `11155111` | [sepolia.etherscan.io](https://sepolia.etherscan.io) | Not deployed | Yes |

MockUSDC minter: deployer EOA. Initial mint: 1M USDC (6 decimals) to deployer on each testnet.

---

## MockUSDC (test token)

| Network | Address | Broadcast |
|---------|---------|-----------|
| Optimism Sepolia | [`0x8BF6C353143D6C68Ba4255b3C2c917A1BDa1C7f7`](https://sepolia-optimism.etherscan.io/address/0x8BF6C353143D6C68Ba4255b3C2c917A1BDa1C7f7) | `broadcast/DeployMockUSDC.s.sol/11155420/run-latest.json` |
| Arbitrum Sepolia | [`0x4C2F87b29f2e157e442Fb735a4C0b257D9303a13`](https://sepolia.arbiscan.io/address/0x4C2F87b29f2e157e442Fb735a4C0b257D9303a13) | `broadcast/DeployMockUSDC.s.sol/421614/run-latest.json` |
| Ethereum Sepolia | [`0x83D088D15e10b00ed9430fa84D8f5C6ecd6A6b99`](https://sepolia.etherscan.io/address/0x83D088D15e10b00ed9430fa84D8f5C6ecd6A6b99) | `broadcast/DeployMockUSDC.s.sol/11155111/run-latest.json` |

---

## EXBOT — use proxy addresses for integrations

| Contract | Optimism Sepolia | Arbitrum Sepolia |
|----------|------------------|------------------|
| **ExbotAddressesProvider** | [`0x73649A1F67f251A321945C6bB0F08f8fBFaae62a`](https://sepolia-optimism.etherscan.io/address/0x73649A1F67f251A321945C6bB0F08f8fBFaae62a) | [`0x6Ecef032AD6578cFbD3EaAe1AC03C33fB814c4b2`](https://sepolia.arbiscan.io/address/0x6Ecef032AD6578cFbD3EaAe1AC03C33fB814c4b2) |
| **BnzaExVault** (proxy) | [`0x0bd88B5f2d183A8cFC7D7CC83990A712D49fcDFD`](https://sepolia-optimism.etherscan.io/address/0x0bd88B5f2d183A8cFC7D7CC83990A712D49fcDFD) | [`0xa275fdD42079fe3FcF1f9EdC97b5592aA65F9598`](https://sepolia.arbiscan.io/address/0xa275fdD42079fe3FcF1f9EdC97b5592aA65F9598) |
| **BnzaExPositionManager** (proxy) | [`0x158C6f9Bc83512e897725D3eDcC1887e18FB164F`](https://sepolia-optimism.etherscan.io/address/0x158C6f9Bc83512e897725D3eDcC1887e18FB164F) | [`0x1dD0c8DeeD006e7285c268E19eb8c41625B4914D`](https://sepolia.arbiscan.io/address/0x1dD0c8DeeD006e7285c268E19eb8c41625B4914D) |
| **TokenRouter** (proxy) | [`0x9335489b50F550653ec9Fd0C2fF7De8661C56b51`](https://sepolia-optimism.etherscan.io/address/0x9335489b50F550653ec9Fd0C2fF7De8661C56b51) | [`0x4359b44B0e3096e3b85D3b8A5A34Fe7121E460C0`](https://sepolia.arbiscan.io/address/0x4359b44B0e3096e3b85D3b8A5A34Fe7121E460C0) |
| **RedemptionQueue** (proxy) | [`0xa5Ef69C0af6a87693eFb60d37e74005efc129F3d`](https://sepolia-optimism.etherscan.io/address/0xa5Ef69C0af6a87693eFb60d37e74005efc129F3d) | [`0x36FD545018B136518f0f651A7B639A89765b7b9F`](https://sepolia.arbiscan.io/address/0x36FD545018B136518f0f651A7B639A89765b7b9F) |

Stack deploy broadcast:
`broadcast/DeployExbotOptimismSepolia.s.sol/11155420/run-latest.json` ·
`broadcast/DeployExbotArbitrumSepolia.s.sol/421614/run-latest.json`

---

## EXBOT — implementations

| Contract | Optimism Sepolia | Arbitrum Sepolia |
|----------|------------------|------------------|
| BnzaExVault (impl) | [`0xd973c7bE6605Faf3E80DCD0eBF63A56E4463a3cd`](https://sepolia-optimism.etherscan.io/address/0xd973c7bE6605Faf3E80DCD0eBF63A56E4463a3cd) | [`0xe437023c53b05DD21aCc3272163AD63bbafd521e`](https://sepolia.arbiscan.io/address/0xe437023c53b05DD21aCc3272163AD63bbafd521e) |
| BnzaExPositionManager (impl) | [`0x7a0AD6C29949C314417373aC94277D25a83E63D8`](https://sepolia-optimism.etherscan.io/address/0x7a0AD6C29949C314417373aC94277D25a83E63D8) | [`0x2A84121AE4cbdeFAd04858851401299bD93489A6`](https://sepolia.arbiscan.io/address/0x2A84121AE4cbdeFAd04858851401299bD93489A6) |
| TokenRouter (impl) | [`0x9E25f3d4dB07e1d522fC8B2983930c3B4049C82e`](https://sepolia-optimism.etherscan.io/address/0x9E25f3d4dB07e1d522fC8B2983930c3B4049C82e) | [`0x1535d0D06B4e2C8B52bdf328e3961CC264c69Ef7`](https://sepolia.arbiscan.io/address/0x1535d0D06B4e2C8B52bdf328e3961CC264c69Ef7) |
| RedemptionQueue (impl) | [`0xaea5f1f5440f2301AF3E0e7041d07DAF1A3E90e8`](https://sepolia-optimism.etherscan.io/address/0xaea5f1f5440f2301AF3E0e7041d07DAF1A3E90e8) | [`0x5A175761D74afeF00aB1f44F1681B33eD623233F`](https://sepolia.arbiscan.io/address/0x5A175761D74afeF00aB1f44F1681B33eD623233F) |

---

## EXBOT — strategies

| Contract | Optimism Sepolia | Arbitrum Sepolia |
|----------|------------------|------------------|
| OpenPositionStrategyV1 | [`0x33A9a1e8194023EC32A692590C51dc6366aA6E99`](https://sepolia-optimism.etherscan.io/address/0x33A9a1e8194023EC32A692590C51dc6366aA6E99) | [`0x8F69e1BFf5515C56357577280175F82cC20FE9e9`](https://sepolia.arbiscan.io/address/0x8F69e1BFf5515C56357577280175F82cC20FE9e9) |
| RedeemStrategyV1 | [`0x560CB02a8B69cB3f5BDF31944C3B4D1e22CfA3C7`](https://sepolia-optimism.etherscan.io/address/0x560CB02a8B69cB3f5BDF31944C3B4D1e22CfA3C7) | [`0x416b0d0AcaA1909fDfe91462cC6466e4a849a455`](https://sepolia.arbiscan.io/address/0x416b0d0AcaA1909fDfe91462cC6466e4a849a455) |
| RebalanceStrategyV1 | [`0xA048981C3188656660591Ea9099C4157681E3454`](https://sepolia-optimism.etherscan.io/address/0xA048981C3188656660591Ea9099C4157681E3454) | [`0xa1cB53665dAddb7f1eE30a9a8bc78Cf9E692b119`](https://sepolia.arbiscan.io/address/0xa1cB53665dAddb7f1eE30a9a8bc78Cf9E692b119) |
| CollectFeeStrategyV1 | [`0xD8E24167968420B48dEf8627001424950C347342`](https://sepolia-optimism.etherscan.io/address/0xD8E24167968420B48dEf8627001424950C347342) | [`0x9523B051eC3d02d1CF283deFa5A78EFc8e91618c`](https://sepolia.arbiscan.io/address/0x9523B051eC3d02d1CF283deFa5A78EFc8e91618c) |

All strategies redeployed July 2026 as part of the full-stack redeploy.
Broadcast: `broadcast/DeployExbotOptimismSepolia.s.sol/11155420/run-latest.json` · `broadcast/DeployExbotArbitrumSepolia.s.sol/421614/run-latest.json`

---

## EXBOT — proxy admins (TransparentUpgradeableProxy)

| Proxy | Optimism Sepolia ProxyAdmin | Arbitrum Sepolia ProxyAdmin |
|-------|----------------------------|----------------------------|
| BnzaExVault | [`0x6c2d749dd1220b23cf48a942a4bc1922dbca9431`](https://sepolia-optimism.etherscan.io/address/0x6c2d749dd1220b23cf48a942a4bc1922dbca9431) (`0x0bd8…cDFD`) | [`0x9f8b535ce90dd2df6f643c619eda30f80ba6fc11`](https://sepolia.arbiscan.io/address/0x9f8b535ce90dd2df6f643c619eda30f80ba6fc11) (`0xa275…9598`) |
| BnzaExPositionManager | [`0x980842ffa5ddff5ce27ff18eda6ea1e80eddb526`](https://sepolia-optimism.etherscan.io/address/0x980842ffa5ddff5ce27ff18eda6ea1e80eddb526) (`0x158C…164F`) | [`0x4f98d84ed42b97c24e6c8294c154db15aa1b5713`](https://sepolia.arbiscan.io/address/0x4f98d84ed42b97c24e6c8294c154db15aa1b5713) (`0x1dD0…914D`) |
| TokenRouter | [`0xa7c262c02988aea120656831c94b0ee641bfcc9d`](https://sepolia-optimism.etherscan.io/address/0xa7c262c02988aea120656831c94b0ee641bfcc9d) (`0x9335…6b51`) | [`0xfff0fec22710597ebb9025467690a0e1aa4f6e99`](https://sepolia.arbiscan.io/address/0xfff0fec22710597ebb9025467690a0e1aa4f6e99) (`0x4359…60C0`) |
| RedemptionQueue | [`0x3ebc0e58649405d53e55e9bfefac065533a2b042`](https://sepolia-optimism.etherscan.io/address/0x3ebc0e58649405d53e55e9bfefac065533a2b042) (`0xa5Ef…9F3d`) | [`0x9d6954f14004cfc3dacc47519005253eb1c797cf`](https://sepolia.arbiscan.io/address/0x9d6954f14004cfc3dacc47519005253eb1c797cf) (`0x36FD…7b9F`) |

---

## External dependencies

| Token / protocol | Optimism Sepolia | Arbitrum Sepolia | Ethereum Sepolia |
|------------------|------------------|------------------|------------------|
| USDC (MockUSDC in vault) | `0x8BF6C353143D6C68Ba4255b3C2c917A1BDa1C7f7` | `0x4C2F87b29f2e157e442Fb735a4C0b257D9303a13` | `0x83D088D15e10b00ed9430fa84D8f5C6ecd6A6b99` |
| Circle USDC (fallback) | — | — | `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238` |
| WETH | `0x4200000000000000000000000000000000000006` | `0x1bdc540dEB9Ed1fA29964DeEcCc524A8f5e2198e` | `0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14` |
| Uniswap V3 Factory | `0x8CE191193D15ea94e11d327b4c7ad8bbE520f6aF` | `0x248AB79Bbb9bC29bB72f7Cd42F17e054Fc40188e` | `0x0227628f3F023bb0B980b67D528571c95c6DaC1c` |
| Uniswap V3 NPM | `0xdA75cEf1C93078e8b736FCA5D5a30adb97C8957d` | `0x6b2937Bde17889EDCf8fbD8dE31C3C2a70Bc4d65` | `0x1238536071E1c677A632429e3655c799b22cDA52` |
| Uniswap SwapRouter02 | `0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4` | `0x101F443B4d1b059569D643917553c771E1b9663E` | `0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E` |

---

## Deploy & verify

```bash
BROADCAST=1 ./scripts/deploy-phase1.sh op-sepolia
BROADCAST=1 ./scripts/deploy-phase1.sh arb-sepolia

RELEASE_ID=2026-08-my-release RELEASE_SUMMARY='one-line change summary' \
  ./scripts/record-deployed-release.sh

./scripts/verify-exbot-op-sepolia.sh
./scripts/verify-exbot-arb-sepolia.sh
./scripts/verify-mock-usdc.sh op-sepolia
./scripts/verify-mock-usdc.sh arb-sepolia
```

**Integration guide:** [`INTEGRATION.md`](INTEGRATION.md)
