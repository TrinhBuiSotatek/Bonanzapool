# Gap and Readiness

## Gap classification

| Gap | Type | Impact | Owner | Priority | Status |
|---|---|---|---|---|---|
| Vault deploy params (deploy address, authorizedOperator, multiSig signer set + threshold, fee distribution, final ABI) | Needs BA/Tech Lead source | Blocks EX-32 deploy and A2 Live $1k integration | Tech Lead / Multi-sig owners | High | Open |
| Subgraph API key (Graph Studio, GRT/credits) | QC-fillable / Ops | Blocks BT-01 Uniswap data crawl on Base | Ops / Tech Lead | High | Open |
| Verify 0.3% fee-tier USDC/WETH pool liquidity on Base (vs 0.05% tier) | Needs BA/Tech Lead source | If liquidity too thin, BT-01 must switch to archive-RPC fallback | Tech Lead | Medium | Open |
| OPERATOR status-mirror decision (mirror minimal status vs always live-query EXBOT) | QC-fillable (decision pending) | Affects EX-43; QC needs to know which path to test | Tech Lead | Medium | Open |
| Authority for strategy parameter adjustment when live diverges from backtest | Needs BA/Tech Lead source | Decide before validation phase | QC Lead / Tech Lead / PM | Medium | Open |
| Public UI feature inventory (POOL/MOBILE) | Derivable from detailed requirement docs | Phase B+ — does not block Phase A QC | BA | Low | Open |
| Stop Loss simulation method on HL Testnet | QC-fillable | Affects FLOW-003 testability | Tech Lead / QC Lead | Medium | Open (Q-003 carryover) |
| Backup RPC endpoints for Base Sepolia | QC-fillable | Avoid test-suite flakiness from RPC rate limits | Tech Lead | Low | Open (Q-004 carryover) |
| Cloudflare Paid plan confirmation for test/prod | QC-fillable | Prod-like CPU/subrequest limits | QC Lead / zen | Medium | Open (Q-005 carryover) |

## Readiness draft for Section 9

| Nhóm context | Trạng thái | Độ tin cậy | Ảnh hưởng nếu thiếu/sai | Cần QC Lead bổ sung gì |
|---|---|---:|---|---|
| Project goal & scope | Ready | High | Hiểu sai mục tiêu giảm drawdown / Net APR | Xác nhận target Net APR cụ thể cho Phase A |
| System/site/module overview | Ready | High | Hiểu sai kiến trúc 5-package + service binding | N/A |
| Feature/use case inventory | Ready | High | Bỏ sót tracks SH-/EX-/BT- khi thiết kế plan | Rà soát + ưu tiên test phase Phase 0 → A1 → A2 |
| Users/roles/permission overview | Ready | High | Test sai phân quyền operator/multiSig | Xác nhận BnzaExVault chỉ Operator được điều phối, không chuyển NFT |
| Business flows & module relationship | Ready | High | Bỏ sót facade flow (OPERATOR ↔ EXBOT) | N/A |
| Common rules/data/state/integration | Ready | High | Bỏ sót rule no-float, no-plaintext-key, hedge budget cap 30% | Xác nhận HL error-code mapping cho test exception flows |
| Platform/environment/device/NFR | Partial | Medium | Backtest TS-only (không Python); Foundry SC tests | Xác nhận RPC dự phòng + Cloudflare Paid plan |
| Document status tracking | Partial | Medium | Khó theo dõi tiến độ thiết kế kiểm thử theo task | Chạy `qc-site-map` → bootstrap dashboard |

**Kết luận:**  
Tạm đủ để bắt đầu thiết kế kiểm thử cho Phase 0 + A1. Rủi ro cao nhất: thiếu tham số deploy của BnzaExVault và phương pháp giả lập Stop Loss trên HL Testnet.

## Open questions draft for Section 10 (carryover + new)

| ID | Câu hỏi | Vì sao quan trọng | Ảnh hưởng nếu chưa rõ | Priority | Owner | Status |
|---|---|---|---|---|---|---|
| Q-001 | Địa chỉ deploy BnzaExVault, Operator address, multiSig signers cụ thể? | Cần để cấu hình test tích hợp | Không thể chạy A2 Live $1k | High | QC Lead / zen | Open (carryover) |
| Q-002 | Quy trình ký Multi-sig khi Circuit Breaker bị ngắt? | Đảm bảo recovery time | Khó test recovery flow | Low | Tech Lead | Open (carryover) |
| Q-003 | Cách giả lập sự kiện chạm Stop Loss trên HL Testnet? | Stop loss là feature an toàn tối thượng | Không test được luồng đóng vị thế khẩn cấp | Medium | Tech Lead / QC Lead | Open (carryover) |
| Q-004 | RPC endpoint dự phòng cho Base Sepolia? | Tránh test flakiness | Test suite fail ngẫu nhiên | Low | Tech Lead | Open (carryover) |
| Q-005 | Cloudflare Paid plan cho test/deploy? | Kiểm chứng giới hạn CPU/subrequest giống prod | Phát hiện muộn lỗi quá giới hạn Workers | Medium | QC Lead / zen | Open (carryover) |
| Q-006 | OPERATOR có duy trì minimal status mirror hay luôn query live EXBOT status? | Quyết định kiến trúc EX-43 | QC không biết design test cho cache vs live-query | Medium | Tech Lead | Open (NEW) |
| Q-007 | Ai có quyền điều chỉnh tham số chiến lược khi live ≠ backtest? | Cần quyết định trước validation phase | Không rõ quyền/thủ tục thay đổi config | Medium | PM / Tech Lead | Open (NEW) |
| Q-008 | API key của Graph Studio (subgraph) đã được procurement chưa? | Block BT-01 Uniswap data crawl | Backtest không có data nguồn primary | High | Ops / Tech Lead | Open (NEW) |
| Q-009 | Pool USDC/WETH 0.3% trên Base có đủ thanh khoản cho backtest không (vs tier 0.05%)? | Quyết định lock pool target | Phải fallback sang archive-RPC, tốn effort | Medium | Tech Lead | Open (NEW) |
| Q-010 | Final BnzaExVault ABI freeze date? | Block Track 1 vault-client integration | Track 1 không freeze được interface | High | SC team | Open (NEW) |

## Resolved carry-over questions
| ID | Resolution | Source |
|---|---|---|
| (none) | (no questions resolved this run) | — |
