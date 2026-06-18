---
type: srs-erd
module: exbot
status: draft
created: 2026-06-12
updated: 2026-06-12
owner: "@hienduong"
changelog:
  - 2026-06-12 | /ba-start srs | initial draft
---

# SRS ERD — BNZA-EXBOT Infrastructure

## D1 Entity Relationship Diagram

```mermaid
erDiagram
    %% control_db
    users {
        TEXT id PK
        TEXT email
        TEXT wallet_address
        TEXT hl_user_address
        TEXT hl_agent_key_id FK
        TEXT created_at
        TEXT updated_at
    }

    bot_registry {
        TEXT bot_id PK
        TEXT user_id FK
        INTEGER shard_id FK
        TEXT status
        TEXT chain
        TEXT bot_type
        TEXT created_at
        TEXT updated_at
    }

    shard_registry {
        INTEGER shard_id PK
        TEXT db_binding_name
        TEXT status
        INTEGER bot_count
        TEXT created_at
    }

    hl_agent_keys {
        TEXT id PK
        TEXT user_id FK
        TEXT hl_user_address
        TEXT agent_address
        BLOB encrypted_secret
        BLOB secret_iv
        BLOB secret_auth_tag
        BLOB wrapped_dek
        BLOB dek_iv
        INTEGER encryption_key_version
        TEXT approval_status
        TEXT approved_at
        TEXT expires_at
        TEXT rotated_from FK
        TEXT created_at
        TEXT updated_at
    }

    %% state_db_shard
    bots {
        TEXT id PK
        TEXT user_id
        TEXT status
        TEXT lifecycle_state
        TEXT chain
        TEXT wallet_address
        TEXT position_id FK
        TEXT hedge_leg_id FK
        TEXT next_light_check_at
        TEXT next_deep_audit_at
        TEXT created_at
        TEXT updated_at
    }

    positions {
        TEXT id PK
        TEXT bot_id FK
        TEXT token_id
        TEXT pool_address
        TEXT token0
        TEXT token1
        INTEGER fee
        INTEGER tick_lower
        INTEGER tick_upper
        TEXT liquidity
        INTEGER weth_index
        INTEGER token0_decimals
        INTEGER token1_decimals
        TEXT custodian
        TEXT custodian_address
        TEXT updated_at
    }

    hedge_legs {
        TEXT id PK
        TEXT bot_id FK
        TEXT hl_asset
        TEXT target_ratio
        TEXT tolerance_ratio
        INTEGER leverage
        TEXT margin_mode
        TEXT hl_account_address
        TEXT stop_order_id
        TEXT stop_cloid
        TEXT stop_price
        TEXT stop_size
        TEXT stop_last_verified_at
        TEXT circuit_state
        TEXT entry_price
        TEXT liquidation_price
        TEXT effective_leverage
        TEXT isolated_margin_usd
        TEXT stop_distance_pct
        TEXT last_stop_audit_at
        TEXT stop_trigger_crossed_at
        TEXT margin_status
        TEXT margin_balance_usd
        TEXT margin_required_usd
        TEXT stop_replacing_started_at
        INTEGER scale_step_pct
        TEXT scale_baseline_lp_usd
        TEXT last_scale_change_at
        TEXT budget_breach_since
        TEXT updated_at
    }

    bot_runtime_state {
        TEXT bot_id PK
        INTEGER state_version
        INTEGER current_tick
        TEXT sqrt_price_x96
        TEXT lp_amount0_raw
        TEXT lp_amount1_raw
        TEXT lp_eth_amount
        TEXT eth_price_usd
        TEXT lp_value_usd
        TEXT target_short_size
        TEXT last_known_hl_short_size
        TEXT last_hl_reconcile_at
        TEXT last_light_check_at
        TEXT last_deep_audit_at
        TEXT last_rebalance_attempt_id
        TEXT health_status
        TEXT updated_at
    }

    circuit_breakers {
        TEXT hedge_leg_id PK
        TEXT bot_id FK
        TEXT asset
        TEXT state
        TEXT opened_at
        TEXT reason
        INTEGER failure_count
        TEXT last_failure_at
        TEXT reset_at
        INTEGER half_open_probe_used
        TEXT updated_at
    }

    rebalance_attempts {
        TEXT id PK
        TEXT bot_id FK
        TEXT user_id
        TEXT hedge_leg_id FK
        TEXT asset
        INTEGER state_version
        TEXT status
        TEXT reason
        TEXT old_short_size
        TEXT target_short_size
        TEXT reconciled_short_size
        TEXT adjust_cloid
        TEXT close_cloid
        TEXT open_cloid
        TEXT stop_cloid
        TEXT error_code
        TEXT error_message
        TEXT started_at
        TEXT finished_at
    }

    lp_operations {
        TEXT id PK
        TEXT bot_id FK
        TEXT op_type
        TEXT idempotency_key
        TEXT tx_hash
        TEXT pre_token_id
        TEXT post_token_id
        TEXT status
        TEXT submitted_at
        TEXT confirmed_at
    }

    close_operations {
        TEXT id PK
        TEXT bot_id FK
        TEXT kind
        TEXT state
        TEXT idempotency_key
        TEXT hedge_close_tx
        TEXT lp_close_tx
        TEXT usdc_amount
        TEXT residual_amount
        TEXT created_at
        TEXT updated_at
    }

    queue_idempotency {
        TEXT key PK
        TEXT message_id
        TEXT kind
        TEXT state
        INTEGER attempt
        TEXT bot_id
        TEXT result_json
        TEXT created_at
        TEXT updated_at
        TEXT expires_at
    }

    funding_daily_metrics {
        TEXT bot_id PK
        TEXT bucket_day PK
        TEXT funding_paid_usd
        TEXT funding_received_usd
        TEXT funding_net_usd
        INTEGER events_count
    }

    %% Relationships
    users ||--o{ bot_registry : "owns"
    users ||--o{ hl_agent_keys : "has"
    hl_agent_keys ||--o| hl_agent_keys : "rotated_from"
    shard_registry ||--o{ bot_registry : "hosts"

    bots ||--|| positions : "has one LP position"
    bots ||--|| hedge_legs : "has one hedge leg"
    bots ||--|| bot_runtime_state : "has hot state"
    hedge_legs ||--|| circuit_breakers : "has circuit"
    bots ||--o{ rebalance_attempts : "logged in"
    bots ||--o{ lp_operations : "LP ops ledger"
    bots ||--o{ close_operations : "close/redeem ledger"
    bots ||--o{ queue_idempotency : "message dedup"
    bots ||--o{ funding_daily_metrics : "daily funding"
```

## DB Separation

| Database | Tables | Phase |
|----------|--------|-------|
| `control_db` (global, 1) | users, bot_registry, shard_registry, hl_agent_keys | Phase A |
| `state_db_shard_00` (1 shard) | bots, positions, hedge_legs, bot_runtime_state, circuit_breakers, rebalance_attempts, lp_operations, close_operations, queue_idempotency, funding_daily_metrics, hourly_bot_metrics, daily_bot_metrics | Phase A |
| `state_db_shard_00..03` (4 shards) | same as above | Phase B |
| `state_db_shard_00..15` (16 shards) | same as above — deferred until Phase B stable + 10k load benchmark | Phase C |

Shard key: `shard_id = hash(bot_id) % shard_count`

## Key Invariants

| Invariant | Rule |
|-----------|------|
| 1 bot : 1 position | `positions.bot_id UNIQUE` |
| 1 bot : 1 hedge_leg | `hedge_legs.bot_id UNIQUE` |
| 1 hedge_leg : 1 circuit_breaker | `circuit_breakers.hedge_leg_id PK` |
| close idempotency | `close_operations.idempotency_key UNIQUE` |
| LP op idempotency | `lp_operations.idempotency_key UNIQUE` |
| message dedup | `queue_idempotency.message_id UNIQUE INDEX` |
| no float storage | All financial amounts stored as TEXT (BigDecimal string) |
| no DROP/RENAME | Schema change = ADD COLUMN only after Phase A deploy |
