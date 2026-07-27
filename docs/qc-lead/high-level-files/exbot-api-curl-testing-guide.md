# Test the EXBOT Dev Flow with Postman or Bruno

This guide covers the current EXBOT dev control-plane, the required Base contract checks, and the
intended end-to-end flow. API and read-only RPC requests can be imported into Postman or Bruno.
Contract writes must be signed in an approved connected wallet.

## 1. Scope and safety

> [!CAUTION]
> **The dev API targets Base mainnet contracts.** Contract writes spend real Base ETH for gas and can
> move real Circle USDC. A live-configured queue consumer can submit real LP and Hyperliquid
> transactions. Do not approve or deposit tokens until an EXBOT owner approves a live test, verifies
> the deployed revision and runtime configuration, specifies the test wallet and amount, and confirms
> a recovery procedure.

Never put a seed phrase, private key, raw signed transaction, or unrelated API-client credential
into this guide, Postman, or Bruno. Keep the EXBOT internal token as a local sensitive value.

Source behavior; deployed AWS revision and runtime configuration are not verified by this guide:

| Component | Source behavior | Runtime boundary |
|---|---|---|
| <code>start-bot</code> | Creates the Vault client with <code>onlyRead: true</code>, reads the deposit, persists runtime state, moves the bot to <code>lp_opening</code>, and enqueues <code>hedge-sync</code> | Read-only mode does not require <code>OPERATOR_MNEMONIC</code>. The deployed revision, RPC/contract read configuration, and actual API result remain unverified |
| <code>hedge-sync</code> | The SQS consumer runs the LP leg, derives the hedge target after mint, submits and reconciles the hedge, verifies the stop, then moves the bot to <code>active</code> | The source and infrastructure template describe this flow but do not prove the deployed event mapping, dry-run setting, signer configuration, or runtime health |

Configured Base contracts:

- BnzaExVault proxy: <code>0x71C6Bc7d0Ca95C1d901A2A185E8c90d4530e3005</code>
- Circle USDC: <code>0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913</code>
- USDC/WETH pool: <code>0xd0b53D9277642d899DF5C87A3966A349A798F224</code>

On-chain reads confirm <code>vault.usdc()</code> is the listed USDC, USDC is an allowed deposit
token, and the Vault is not paused.

## 2. Set up Postman or Bruno

### 2.1 Create an environment

Create and activate an environment named <code>EXBOT dev</code> in the client you use. In Postman,
use **Environments**. In Bruno, create/select the environment for the collection. Add the same
variables in either client:

| Variable | Local value | Notes |
|---|---|---|
| <code>exbotInternalAuth</code> | Obtain through the approved team channel | Mark sensitive; never share or export |
| <code>userAddress</code> | Approved lowercase <code>0x</code> EOA | Must match the wallet that signs approve/deposit |
| <code>chainId</code> | <code>8453</code> | Base mainnet |
| <code>vaultAddress</code> | <code>0x71C6Bc7d0Ca95C1d901A2A185E8c90d4530e3005</code> | Use the proxy, not the implementation |
| <code>usdcAddress</code> | <code>0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913</code> | Circle native USDC |
| <code>depositAmountRaw</code> | Leave empty | Approved amount in 6-decimal raw units; this guide recommends no amount |
| <code>custodyAddress</code> | Leave empty | Returned by Provision custody wallet |
| <code>botId</code> | Leave empty | Saved after Create |
| <code>botIdBytes32</code> | Leave empty | Keccak-256 of the UTF-8 API bot ID |
| <code>unspentBalanceRaw</code> | Leave empty | Saved from the Vault read |

The scripts create <code>botIdUtf8Hex</code> and <code>unspentBalanceCallData</code> as
request-scoped variables; do not add them to the environment.

### 2.2 Import raw cURL

Every cURL block intentionally contains the full API Gateway or public Base RPC URL. Postman and
Bruno cURL importers do not reliably resolve variables embedded in an imported URL. Header and body
values, including <code>{{exbotInternalAuth}}</code>, <code>{{userAddress}}</code>, and
<code>{{botId}}</code>, remain environment variables so secrets and test identities are not inlined.

#### Postman import

1. Select **Import** and paste one complete cURL block.
2. Import it into an <code>EXBOT dev</code> collection.
3. Add the Postman variant under **Scripts → Pre-request** or **Scripts → Post-response**.
4. Activate the <code>EXBOT dev</code> environment before sending.

#### Bruno import

1. Import one complete cURL block and save it in an <code>EXBOT dev</code> collection.
2. Add the Bruno variant under the request's **Scripts → Pre Request** or
   **Scripts → Post Response** tab.
3. Select the <code>EXBOT dev</code> environment before sending.

Terminal users must replace environment placeholders manually or generate cURL from the imported
request in Postman or Bruno.

## 3. Authentication and roles

<code>user_address</code> is the canonical auth-context field. The examples build the header inline
from <code>{{userAddress}}</code>:

- User: <code>{"user_address":"{{userAddress}}","role":"operator"}</code>
- Admin: <code>{"user_address":"{{userAddress}}","role":"admin"}</code>

Provision custody wallet, Create, and Start use the user role. Status, Pause, and Resume require
<code>admin</code> or <code>super_admin</code>. The same <code>userAddress</code> must own the API bot
and sign any on-chain funding calls.

## 4. Create the API identity and bot

### 4.1 Provision custody wallet

This API call creates or returns EXBOT custody metadata. **It performs no ERC-20 approval, token
transfer, or Vault deposit.**

~~~bash
curl --request POST \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/deposit-wallet' \
  --header 'Content-Type: application/json' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"operator"}' \
  --data-raw '{"chain_id": {{chainId}}}'
~~~

Expected success: <code>200</code> with <code>custody_address</code>. Optionally save it as
<code>custodyAddress</code>; it is not the signer for the user funding calls below.

### 4.2 Create

~~~bash
curl --request POST \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/create' \
  --header 'Content-Type: application/json' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"operator"}' \
  --data-raw '{"chain_id": {{chainId}}}'
~~~

Expected success: <code>200</code> with a non-empty <code>bot_id</code> and
<code>lifecycle_state: "idle"</code>.

#### Chain gate (Base mainnet only)

<code>create-bot</code> enforces <code>chain_id=8453</code>. Any other value is rejected with
<code>400 INVALID_CHAIN</code> with <code>{ allowed_chain_id, received }</code> in the body. Sending a
non-number or omitting <code>chain_id</code> returns <code>400 INVALID_BODY</code>. These are
distinct reasons so the OPERATOR can tell "wrong chain" from "malformed body".

#### Postman post-response

~~~javascript
let body = {};

try {
  body = pm.response.json();
} catch (error) {
  console.warn("Create response was not JSON; botId was not changed.");
}

const createdBotId =
  body && typeof body.bot_id === "string" ? body.bot_id.trim() : "";

if (pm.response.code >= 200 && pm.response.code < 300 && createdBotId) {
  pm.environment.set("botId", createdBotId);
}
~~~

#### Bruno post-response

~~~javascript
const status = Number(res.getStatus());
const rawBody = res.getBody();
let body = rawBody;

if (typeof rawBody === "string") {
  try {
    body = JSON.parse(rawBody);
  } catch (error) {
    throw new Error("Create response was not valid JSON; botId was not changed.");
  }
}

if (!Number.isInteger(status) || status < 200 || status >= 300) {
  throw new Error(`Create failed with HTTP status ${res.getStatus()}.`);
}
if (!body || typeof body !== "object" || Array.isArray(body)) {
  throw new Error("Create response must be a JSON object.");
}

const createdBotId =
  typeof body.bot_id === "string" ? body.bot_id.trim() : "";

if (!createdBotId) {
  throw new Error("Create response did not contain a non-empty bot_id.");
}

bru.setEnvVar("botId", createdBotId, { persist: true });
~~~

Both variants persist <code>botId</code> for later requests and do not overwrite it from an error
response.

### 4.3 Derive <code>botIdBytes32</code>

Contracts use <code>keccak256(UTF-8 botId)</code>, not a padded UUID. Import this request:

~~~bash
curl --request POST \
  --url 'https://mainnet.base.org' \
  --header 'Content-Type: application/json' \
  --data-raw '{"jsonrpc":"2.0","method":"web3_sha3","params":["{{botIdUtf8Hex}}"],"id":1}'
~~~

#### Postman pre-request

~~~javascript
const botId = pm.environment.get("botId");

if (typeof botId !== "string" || !botId || botId !== botId.trim()) {
  throw new Error("botId must be a non-empty exact string.");
}
if (!/^[\x20-\x7E]+$/.test(botId)) {
  throw new Error("botId must contain printable ASCII characters only.");
}

const botIdUtf8Hex =
  "0x" +
  Array.from(botId, function (character) {
    return character.charCodeAt(0).toString(16).padStart(2, "0");
  }).join("");

pm.variables.set("botIdUtf8Hex", botIdUtf8Hex);
~~~

#### Bruno pre-request

~~~javascript
const botId = bru.getEnvVar("botId");

if (typeof botId !== "string" || !botId || botId !== botId.trim()) {
  throw new Error("botId must be a non-empty exact string.");
}
if (!/^[\x20-\x7E]+$/.test(botId)) {
  throw new Error("botId must contain printable ASCII characters only.");
}

const botIdUtf8Hex =
  "0x" +
  Array.from(botId, function (character) {
    return character.charCodeAt(0).toString(16).padStart(2, "0");
  }).join("");

bru.setVar("botIdUtf8Hex", botIdUtf8Hex);
~~~

#### Postman post-response

~~~javascript
let body;

try {
  body = pm.response.json();
} catch (error) {
  throw new Error("RPC response was not valid JSON.");
}

if (pm.response.code < 200 || pm.response.code >= 300) {
  throw new Error(`RPC failed with HTTP status ${pm.response.code}.`);
}
if (body && body.error) {
  throw new Error(`RPC error: ${body.error.message || JSON.stringify(body.error)}`);
}

const result = body && body.result;
const zeroBytes32 = "0x" + "0".repeat(64);

if (
  typeof result !== "string" ||
  !/^0x[0-9a-fA-F]{64}$/.test(result) ||
  result.toLowerCase() === zeroBytes32
) {
  throw new Error("RPC did not return a valid non-zero bytes32 bot ID.");
}

pm.environment.set("botIdBytes32", result.toLowerCase());
~~~

#### Bruno post-response

~~~javascript
const status = Number(res.getStatus());
const rawBody = res.getBody();
let body = rawBody;

if (typeof rawBody === "string") {
  try {
    body = JSON.parse(rawBody);
  } catch (error) {
    throw new Error("RPC response was not valid JSON.");
  }
}

if (!Number.isInteger(status) || status < 200 || status >= 300) {
  throw new Error(`RPC failed with HTTP status ${res.getStatus()}.`);
}
if (!body || typeof body !== "object" || Array.isArray(body)) {
  throw new Error("RPC response must be a JSON object.");
}
if (body.error) {
  const message =
    typeof body.error.message === "string"
      ? body.error.message
      : JSON.stringify(body.error);
  throw new Error(`RPC error: ${message}`);
}

const result = body.result;
const zeroBytes32 = "0x" + "0".repeat(64);

if (
  typeof result !== "string" ||
  !/^0x[0-9a-fA-F]{64}$/.test(result) ||
  result.toLowerCase() === zeroBytes32
) {
  throw new Error("RPC did not return a valid non-zero bytes32 bot ID.");
}

bru.setEnvVar("botIdBytes32", result.toLowerCase(), { persist: true });
~~~

Confirm <code>botIdBytes32</code> is populated in the active environment before continuing.

## 5. On-chain funding checkpoint

> [!CAUTION]
> These calls use **real Base mainnet USDC and gas**. Do not execute them based on source behavior
> alone. Proceed only under an approved live-test runbook after the deployed Start revision,
> RPC/contract configuration, SQS mapping, dry-run setting, and required signer configuration have
> been verified without exposing credential values.

The signer must be the connected wallet whose address exactly matches <code>{{userAddress}}</code>.
Do not sign from <code>custody_address</code>, an operator wallet, or an agent wallet. The Vault
credits deposits to <code>msg.sender</code>, while Start reads the balance for
<code>userAddress</code>.

### 5.1 Read-only preflight

Use [BnzaExVault Read as Proxy](https://basescan.org/address/0x71C6Bc7d0Ca95C1d901A2A185E8c90d4530e3005#readProxyContract)
and the [USDC contract](https://basescan.org/address/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913#readContract)
to verify:

| Call | Expected |
|---|---|
| Vault <code>usdc()</code> | <code>{{usdcAddress}}</code> |
| Vault <code>isAllowedDepositToken({{usdcAddress}})</code> | <code>true</code> |
| Vault <code>paused()</code> | <code>false</code> |
| USDC <code>balanceOf({{userAddress}})</code> | Sufficient only for the separately approved amount |
| USDC <code>allowance({{userAddress}}, {{vaultAddress}})</code> | Inspect before changing |

USDC has 6 decimals. <code>depositAmountRaw</code> is an integer in raw units. No amount is supplied
or recommended by this guide.

### 5.2 Wallet-signed calls

Postman and Bruno cannot safely sign these transactions. Use a connected wallet on Base through the
verified contract pages:

1. On [USDC Write Contract](https://basescan.org/address/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913#writeContract),
   call <code>approve(address spender,uint256 amount)</code> with
   <code>spender={{vaultAddress}}</code> and <code>amount={{depositAmountRaw}}</code>.
2. Wait for a successful receipt.
3. On [BnzaExVault Write as Proxy](https://basescan.org/address/0x71C6Bc7d0Ca95C1d901A2A185E8c90d4530e3005#writeProxyContract),
   call <code>deposit(bytes32 botId,uint256 amount)</code> with
   <code>botId={{botIdBytes32}}</code> and <code>amount={{depositAmountRaw}}</code>.
4. Wait for a successful receipt before any API Start attempt.

Do not paste private keys into Postman or Bruno, and do not construct or submit raw signed
transactions from this guide.

### 5.3 Verify <code>unspentBalance</code> in Postman or Bruno

The selector for <code>unspentBalance(address,bytes32)</code> is <code>0xa2a4c2c0</code>. Import:

~~~bash
curl --request POST \
  --url 'https://mainnet.base.org' \
  --header 'Content-Type: application/json' \
  --data-raw '{"jsonrpc":"2.0","method":"eth_call","params":[{"to":"{{vaultAddress}}","data":"{{unspentBalanceCallData}}"},"latest"],"id":1}'
~~~

#### Postman pre-request

~~~javascript
const userAddress = pm.environment.get("userAddress");
const botIdBytes32 = pm.environment.get("botIdBytes32");

if (!/^0x[0-9a-fA-F]{40}$/.test(userAddress || "")) {
  throw new Error("userAddress must be a 20-byte EVM address.");
}
if (!/^0x[0-9a-fA-F]{64}$/.test(botIdBytes32 || "")) {
  throw new Error("botIdBytes32 must be a 32-byte hex value.");
}

const selector = "a2a4c2c0";
const paddedUser = userAddress.slice(2).toLowerCase().padStart(64, "0");
const encodedBotId = botIdBytes32.slice(2).toLowerCase();

pm.variables.set(
  "unspentBalanceCallData",
  "0x" + selector + paddedUser + encodedBotId
);
~~~

#### Bruno pre-request

~~~javascript
const userAddress = bru.getEnvVar("userAddress");
const botIdBytes32 = bru.getEnvVar("botIdBytes32");

if (!/^0x[0-9a-fA-F]{40}$/.test(userAddress || "")) {
  throw new Error("userAddress must be a 20-byte EVM address.");
}
if (!/^0x[0-9a-fA-F]{64}$/.test(botIdBytes32 || "")) {
  throw new Error("botIdBytes32 must be a 32-byte hex value.");
}

const selector = "a2a4c2c0";
const paddedUser = userAddress.slice(2).toLowerCase().padStart(64, "0");
const encodedBotId = botIdBytes32.slice(2).toLowerCase();

bru.setVar(
  "unspentBalanceCallData",
  "0x" + selector + paddedUser + encodedBotId
);
~~~

#### Postman post-response

~~~javascript
let body;

try {
  body = pm.response.json();
} catch (error) {
  throw new Error("RPC response was not valid JSON.");
}

if (pm.response.code < 200 || pm.response.code >= 300) {
  throw new Error(`RPC failed with HTTP status ${pm.response.code}.`);
}
if (body && body.error) {
  throw new Error(`RPC error: ${body.error.message || JSON.stringify(body.error)}`);
}

const result = body && body.result;

if (typeof result !== "string" || !/^0x[0-9a-fA-F]{64}$/.test(result)) {
  throw new Error("RPC did not return an ABI-encoded uint256.");
}

const decimalBalance = BigInt(result).toString();
pm.environment.set("unspentBalanceRaw", decimalBalance);
console.log("Vault unspent balance (raw USDC):", decimalBalance);
~~~

#### Bruno post-response

~~~javascript
const status = Number(res.getStatus());
const rawBody = res.getBody();
let body = rawBody;

if (typeof rawBody === "string") {
  try {
    body = JSON.parse(rawBody);
  } catch (error) {
    throw new Error("RPC response was not valid JSON.");
  }
}

if (!Number.isInteger(status) || status < 200 || status >= 300) {
  throw new Error(`RPC failed with HTTP status ${res.getStatus()}.`);
}
if (!body || typeof body !== "object" || Array.isArray(body)) {
  throw new Error("RPC response must be a JSON object.");
}
if (body.error) {
  const message =
    typeof body.error.message === "string"
      ? body.error.message
      : JSON.stringify(body.error);
  throw new Error(`RPC error: ${message}`);
}

const result = body.result;

if (typeof result !== "string" || !/^0x[0-9a-fA-F]{64}$/.test(result)) {
  throw new Error("RPC did not return an ABI-encoded uint256.");
}

const decimalBalance = BigInt(result).toString();
bru.setEnvVar("unspentBalanceRaw", decimalBalance, { persist: true });
console.log("Vault unspent balance (raw USDC):", decimalBalance);
~~~

After an approved deposit, verify:

- both transaction receipts have <code>status=success</code>;
- the Vault receipt contains <code>Deposited(user, botId, token, amount)</code>;
- <code>botDepositToken({{userAddress}}, {{botIdBytes32}})</code> equals
  <code>{{usdcAddress}}</code>;
- <code>unspentBalanceRaw</code> increased by the deposited raw amount.

## 6. Start and inspect the lifecycle

### 6.1 Start

~~~bash
curl --request POST \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/start' \
  --header 'Content-Type: application/json' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"operator"}' \
  --data-raw '{"bot_id":"{{botId}}"}'
~~~

With the current source deployed and its dependencies configured, expected success is an immediate
HTTP <code>200</code> after Start completes these synchronous steps:

1. read the active on-chain LP position for <code>userAddress</code> + <code>botId</code>
   (hard blocker — see <code>LP_ALREADY_ACTIVE</code> below);
2. read Vault unspent USDC for <code>userAddress</code> and <code>botIdBytes32</code>;
3. split the amount <strong>20% HL / 80% LP</strong> by default; the live value is read from
   <code>system_config.hl_portion_ratio</code> so ops can retune without redeploying. Values
   outside the open interval <code>(0, 1)</code> fall back to the 20/80 default;
4. derive <code>lpEthAmount</code> via spot-quote of the LP portion against the pool snapshot,
   then run viability + margin preflight;
5. persist runtime amounts and move the bot to <code>lp_opening</code>;
6. enqueue the open request via <code>initiateFlow(action='open')</code> with
   <code>expectedTargetSize: '0'</code> (intentional — the LP hasn't minted yet, so
   <code>hedge-sync</code> recomputes the target after <code>vaultMint</code>).

Success body:

~~~json
{
  "bot_id": "<id>",
  "status": "<status>",
  "custody_address": "<userAddress>",
  "total_usdc": "<raw USDC string>",
  "dry_run": <boolean>
}
~~~

The <code>200</code> confirms the database work and SQS enqueue completed; it does **not** prove the LP
or Hyperliquid position is open. Those steps are asynchronous. The lifecycle should subsequently
advance through queue-owned LP, hedge, reconcile, and stop states toward <code>active</code>. Poll
Status after Start and investigate any stalled or failed state before retrying or taking another
action.

Start may fail synchronously. The handler returns these errors before any DB transition:

| Status | Reason | When |
|---|---|---|
| 400 | <code>INVALID_BODY</code> | body is not JSON / <code>bot_id</code> missing or non-string |
| 401 | <code>INVALID_AUTH_CONTEXT</code> | auth-context header missing or malformed |
| 403 | <code>FORBIDDEN</code> | bot owner ≠ <code>userAddress</code> |
| 404 | <code>BOT_NOT_FOUND</code> | unknown <code>bot_id</code> |
| 409 | <code>BOT_NOT_IDLE</code> <code>{ current_state }</code> | bot not in <code>idle</code> |
| 409 | <code>LP_ALREADY_ACTIVE</code> <code>{ active_token_id }</code> | on-chain LP exists; close it first |
| 409 | <code>INSUFFICIENT_HL_MARGIN</code> <code>{ margin_required_usd, margin_required_with_buffer_usd, margin_available_after_deposit_usd }</code> | HL margin preflight fails |
| 409 | <code>FLOW_ALREADY_ACTIVE</code> <code>{ existing_flow_id }</code> | another flow is already running for this bot |
| 422 | <code>INSUFFICIENT_VAULT_BALANCE</code> <code>{ unspent_balance, topUpUsdc }</code> | top up USDC; <code>topUpUsdc</code> is human-formatted (USDC, 6 dp) |
| 503 | <code>LP_POOL_NOT_CONFIGURED</code> / <code>LP_POOL_SNAPSHOT_UNAVAILABLE</code> / <code>USDC_TOKEN_NOT_CONFIGURED</code> | environment/chain not configured |
| 503 | <code>QUEUE_UNAVAILABLE</code> | SQS enqueue failed after <code>lp_opening</code> was persisted — do not retry blindly, check Status |

> If Start returns <code>QUEUE_UNAVAILABLE</code>, the bot may already be
> <code>lp_opening</code>. Do not blindly retry. Check Status and ask the EXBOT operator to recover
> or reconcile the state.

### 6.2 Status

Status is admin-only:

~~~bash
curl --request GET \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/status/{{botId}}' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"admin"}'
~~~

The current Status handler queries Vault views with <code>custodyAddress</code>, while funding and
Start use <code>userAddress</code>. Its smart-contract balances can therefore show a false zero even
when the user-funded Vault balance is non-zero. Use the direct RPC read above as the funding check.

### 6.3 Pause and Resume

Both routes are admin-only and still require compatible lifecycle states.

~~~bash
curl --request POST \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/pause' \
  --header 'Content-Type: application/json' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"admin"}' \
  --data-raw '{"bot_id":"{{botId}}"}'
~~~

~~~bash
curl --request POST \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/resume' \
  --header 'Content-Type: application/json' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"admin"}' \
  --data-raw '{"bot_id":"{{botId}}"}'
~~~

## 7. Intended full flow and remaining validation risks

The intended sequence is:

1. API provisions the KMS custody wallet.
2. API creates the idle bot.
3. The matching user wallet approves USDC and deposits it into BnzaExVault.
4. API Start reads the deposit, splits it **20% HL / 80% LP** (default; live value in
   <code>system_config.hl_portion_ratio</code>), moves the lifecycle to <code>lp_opening</code>, and
   enqueues an open message with <code>expectedTargetSize: "0"</code>.
5. The SQS event source automatically invokes <code>hedge-sync</code>. Its LP leg mints the position;
   operator signer credentials sign the underlying Vault transaction. No backend operator manually
   calls <code>executeStrategy</code> in this queue flow.
6. After minting, <code>hedge-sync</code> reads the LP WETH amount and recomputes the short target as
   LP ETH multiplied by the configured target ratio. The initial zero target is intentional because
   Start cannot know the minted LP composition in advance.
7. The consumer performs agent approval, submits the KMS-signed Hyperliquid adjustment, reconciles
   the position, verifies the protective stop, and moves the lifecycle to <code>active</code>.

Source review leaves these runtime and integration risks:

- The deployed Lambda revisions, RPC/contract configuration, SQS event mapping, dry-run settings,
  and signer configuration have not been freshly verified.
- If <code>hedge-sync</code> cannot resolve the freshly minted LP state, it falls back to the message's
  <code>expectedTargetSize</code>. For Start's intentional <code>"0"</code> sentinel, that can leave a
  zero target instead of opening a non-zero hedge.
- No implemented bridge or deposit path was found that moves the Base custody USDC into
  Hyperliquid margin before the order.
- Status reads contract balances under <code>custodyAddress</code>, but funding and Start use
  <code>userAddress</code>.

The source and infrastructure template show a live-capable <code>hedge-sync</code> path and an SQS
consumer mapping, but they do not establish what is running in AWS. Do not bypass these checks or
infer credential readiness from the repository.

## 8. Close

<code>POST /internal/exbot/close</code> initiates an asynchronous close flow. The synchronous
part only flips the bot to <code>lifecycle_state='lp_closing'</code> +
<code>status='closing'</code> and enqueues the close flow; the actual LP exit, hedge unwind,
HL withdrawal, and HL fulfillment happen in the 4-step queue chain
<code>lp_leg_exec</code> → <code>hedge_sync</code> → <code>hl_withdraw</code> →
<code>hl_fulfill</code>.

~~~bash
curl --request POST \
  --url 'https://clt2zj884m.execute-api.ap-northeast-1.amazonaws.com/internal/exbot/close' \
  --header 'Content-Type: application/json' \
  --header 'X-Exbot-Internal-Auth: {{exbotInternalAuth}}' \
  --header 'X-Exbot-Auth-Context: {"user_address":"{{userAddress}}","role":"operator"}' \
  --data-raw '{"bot_id":"{{botId}}"}'
~~~

Expected success: <code>200</code> with body
<code>{ bot_id, status: "close_flow_initiated", flow_id }</code>. A <code>200</code> confirms
the DB transition and the flow was queued; it does **not** prove funds have been returned or
safely parked. Poll Status after Close and investigate any stalled or failed lifecycle state
before retrying or taking another action.

Close returns these errors synchronously:

| Status | Reason | When |
|---|---|---|
| 400 | <code>MISSING_BOT_ID</code> | body missing or <code>bot_id</code> is not a string |
| 401 | <code>UNAUTHORIZED_INTERNAL_CALL</code> / <code>INVALID_AUTH_CONTEXT</code> | auth gate failed |
| 409 | <code>INVALID_STATE_FOR_CLOSE</code> | bot is already <code>closed</code>, <code>lp_closing</code>, or <code>error</code> |
| 409 | <code>CLOSE_ALREADY_IN_PROGRESS</code> <code>{ existing_flow_id }</code> | a close flow is already running for this bot |
| 500 | <code>INTERNAL</code> | unexpected — inspect Lambda logs |

## 9. Troubleshooting

| Result | Action |
|---|---|
| Unresolved <code>{{variable}}</code> | Activate <code>EXBOT dev</code> in Postman or Bruno and fill its local value |
| Imported request has a variable in its URL | Re-import the cURL from this guide; full URLs are intentional for importer compatibility |
| <code>pm is not defined</code> in Bruno | Replace the script with the Bruno variant from the same workflow section |
| <code>bru</code> or <code>res</code> is unavailable in Postman | Replace the script with the Postman variant from the same workflow section |
| <code>401 UNAUTHORIZED_INTERNAL_CALL</code> | Check the approved local internal token |
| <code>401 INVALID_AUTH_CONTEXT</code> | Check lowercase <code>userAddress</code> and inline JSON |
| <code>403</code> or <code>admin_required</code> | Use the admin role for Status, Pause, or Resume |
| <code>409 EXBOT_ALREADY_OPEN</code> | The user already has an open bot; stop and request an approved cleanup or identity |
| Start <code>500 INTERNAL</code> | Inspect the actual Lambda logs and non-secret configuration. Start's <code>onlyRead</code> Vault client does not require <code>OPERATOR_MNEMONIC</code>; verify the deployed revision and RPC/contract read configuration instead of assuming the cause |
| Start <code>200</code> but positions are not yet visible | Expected asynchronous behavior immediately after enqueue; poll Status for lifecycle progress toward <code>active</code> |
| Start <code>QUEUE_UNAVAILABLE</code> | Stop retries; bot may already be <code>lp_opening</code> |
| Status reports zero after a verified deposit | Use direct <code>unspentBalance(userAddress, botIdBytes32)</code>; Status currently uses the custody address |
| Create <code>400 INVALID_CHAIN</code> | <code>chain_id</code> must be <code>8453</code> (Base mainnet); use <code>INVALID_CHAIN.allowed_chain_id</code> to confirm |
| <code>409 LP_ALREADY_ACTIVE</code> | bot already has an on-chain LP position; close that bot before starting a new one |
| <code>422 INSUFFICIENT_VAULT_BALANCE</code> | top up Vault USDC; <code>topUpUsdc</code> is the additional raw amount needed |
| <code>409 INSUFFICIENT_HL_MARGIN</code> | HL margin preflight failed; either top up vault USDC or wait for lower leverage/mark |
| <code>409 BOT_NOT_IDLE</code> | bot is mid-lifecycle (<code>current_state</code> field); wait for it to reach <code>active</code> or <code>idle</code> before starting |
| <code>409 FLOW_ALREADY_ACTIVE</code> | a flow is already running for this bot (<code>existing_flow_id</code>); do not retry |
| Close <code>409 INVALID_STATE_FOR_CLOSE</code> | bot already <code>closed</code> / <code>lp_closing</code> / <code>error</code>; poll Status before retrying |
| Close <code>409 CLOSE_ALREADY_IN_PROGRESS</code> | a close flow is already in flight (<code>existing_flow_id</code>); poll Status |
| Close <code>400 MISSING_BOT_ID</code> | body missing <code>bot_id</code> or wrong type |

## 10. References

- [EXBOT deployed addresses](../../contracts/bnza-exbot/docs/DEPLOYED_ADDRESSES.md)
- [BnzaExVault proxy on Basescan](https://basescan.org/address/0x71C6Bc7d0Ca95C1d901A2A185E8c90d4530e3005)
- [Circle USDC on Basescan](https://basescan.org/address/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
- [Import cURL commands](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-curl-commands)
- [Manage Postman environments](https://learning.postman.com/latest-v-12/docs/use/send-requests/variables/managing-environments)
- [Write Postman scripts](https://learning.postman.com/docs/tests-and-scripts/write-scripts/test-scripts/)
- [Bruno documentation](https://docs.usebruno.com/)
- [Import collections into Bruno](https://docs.usebruno.com/get-started/import-export-data/import-collections)
