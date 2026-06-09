# Project Context Master: Monanzapool

**Trạng thái:** Draft  
**Ngày tạo/cập nhật:** 2026-06-09  
**Người chuẩn bị:** QC Context Agent  
**Người review:** QC Lead  
**Mục đích:** Cung cấp bối cảnh tổng quan cấp project để các QC Agent hiểu đúng hệ thống, phạm vi, rule chung, rủi ro và trạng thái tài liệu trước khi review spec, thiết kế scenario/test case, execute hoặc verify bug.

> File này là tài liệu high-level do Agent tổng hợp để QC Lead review và bổ sung.  
> File này không thay thế spec, wireframe, API document, use case detail hoặc các tài liệu chi tiết do BA/BE/Tech Lead cung cấp.  
> File này nên ngắn gọn, chỉ giữ thông tin có ảnh hưởng đến cách QC Agent hiểu dự án, đánh giá impact, review tài liệu hoặc thiết kế kiểm thử.

---

## Sources consolidated

| # | File | Version | Loại | Ngày đọc cuối |
|---|---|---|---|---|
| 1 | Copy of BNZA_EXBOT_Proposal.md | no-version | product or business brief | 2026-06-02 |
| 2 | SPEC_v5.2.5.md | 5.2.5 | architecture / tech overview / integration | 2026-06-02 |
| 3 | exbot-implementation-overview.md | no-version | architecture / tech overview / locked decisions / team model | 2026-06-09 |
| 4 | exbot-task-breakdown.md | no-version | feature inventory / WBS / acceptance criteria (SH-/EX-/BT-) | 2026-06-09 |
| 5 | Exbot_Backtest_WBS.xlsx | no-version | WBS backtest (binary — referenced only) | 2026-06-09 |

---

## 1. Cách các QC Agent sử dụng file này

| Nhóm Agent / Skill | Cách sử dụng project context | Cần đọc thêm file nào |
|---|---|---|
| Site map / dashboard / high-level review | Hiểu cấu trúc tổng thể hệ thống, site/module/feature, trạng thái tài liệu và các vùng cần theo dõi | Site map, feature list, qc-dashboard, high-level BA docs |
| Spec review - level function | Dùng context tổng quan để kiểm tra spec function có đúng scope, role, flow, rule chung, data/state và integration không | Spec chi tiết, wireframe, API spec nếu có |
| Scenario design | Xác định flow, role, dependency, risk và regression impact trước khi thiết kế scenario | Spec chi tiết, feature list, site map, business flow |
| Test case design | Dùng rule chung, platform/environment, permission, data/state để tránh thiết kế thiếu expected result hoặc thiếu precondition | Scenario, spec, wireframe, API spec |
| Test execute | Hiểu scope, environment, test data, dependency và các lưu ý chung khi execute | Test cases, test data, environment note, defect workflow |
| Bug verify | Hiểu impacted area, expected behavior chung, regression area và rule liên quan khi verify bug | Bug report, spec, test case, regression note |

**Quy tắc sử dụng:**  
Nếu thông tin trong file này mâu thuẫn với spec/wireframe/API chi tiết đã approved (ví dụ: `SPEC_v5.2.5.md`), Agent phải báo conflict và ưu tiên tài liệu chi tiết đã approved, trừ khi QC Lead có chỉ định khác.

---

## 2. Tóm tắt dự án

| Hạng mục | Nội dung |
|---|---|
| Tên dự án / sản phẩm | Monanzapool (Ex Bot) |
| Domain / nghiệp vụ | Blockchain (DeFi Yield / Delta-Hedged Liquidity Providing) |
| Loại dự án | New build & Integration |
| Mục tiêu chính của dự án/release | Tối ưu hóa lợi nhuận Uniswap V3 LP fee và giảm thiểu tổn thất vô thường (IL/drawdown) bằng cách tự động phòng vệ vị thế ETH (Hedge) qua Hyperliquid. |
| Người dùng chính | DeFi investors (USDC-based) mong muốn cung cấp thanh khoản nhưng e ngại rủi ro biến động giá ETH. |
| Release / phase hiện tại | Phase 0 & Phase A1 (Core server-side engine + BnzaExVault contract + API dry-run) |
| Trạng thái tổng quan | In development |

**Tóm tắt ngắn:**  
Dự án Monanzapool (phân hệ EXBOT) xây dựng một hệ thống bot quản lý thanh khoản tự động (Managed delta-hedged LP Bot). Hệ thống kết hợp việc gửi thanh khoản trên sàn phi tập trung Uniswap V3 (mạng Base/OP) để thu phí (LP fee) và tự động mở vị thế Short Perpetual đối ứng trên sàn Hyperliquid để phòng vệ rủi ro biến động giá của ETH (delta exposure). Mục tiêu cốt lõi của dự án là giảm thiểu tối đa mức sụt giảm tài sản (drawdown) do tổn thất vô thường (IL) mang lại, hướng tới tỷ suất lợi nhuận thực tế dương (Net positive APR) sau khi trừ chi phí bảo hiểm (hedge cost) và phí vận hành.

---

## 3. Phạm vi tổng thể và ranh giới kiểm thử

### 3.1 In scope cấp project/release (Phase A1)

| Area / site / module / capability | Mô tả ngắn | Priority | Ghi chú |
|---|---|---|---|
| Mạng hỗ trợ & Pool | Hỗ trợ mạng Base (mặc định). Pool USDC/ETH 0.3% trên Uniswap V3 với biên độ giá cố định ±5%. | High | Optimism được trì hoãn sang Phase 2. |
| Phòng vệ vị thế (Hedge) | Mở vị thế Short Perpetual ETH-USD trên Hyperliquid. Tỷ lệ phòng vệ (Hedge ratio) cố định ở mức 70%. Đòn bẩy 3x, Isolated Margin Mode. Phí builder 5bps. | High | Tỷ lệ phòng vệ khác được trì hoãn. |
| Bộ tính toán vị thế (PositionAmountCalculator) | Sử dụng công thức toán học Uniswap V3 chuẩn xác dựa trên liquidity, tickLower, tickUpper, sqrtPriceX96, currentTick để tính lpEthAmount. | High | Loại bỏ cách tính sai lệch của phiên bản cũ. |
| Bộ kích hoạt Rebalance | Đánh giá điều kiện rebalance 5 phút một lần (light-check) dựa trên: drift_threshold, drift_relative, range_out, range_boundary_near, margin_warning, funding_alert, time_fallback, manual_admin. | High | Không gọi API HL khi không cần thiết. |
| Cơ chế khớp lệnh phòng vệ | Thực hiện điều chỉnh delta-only (chỉ mua/bán phần chênh lệch) thay vì đóng/mở lại toàn bộ vị thế. Tự động kiểm tra budget cap (30% LP fee). | High | Delta-only giúp tối ưu phí gas và trượt giá. |
| Quản lý Stop Loss | Tạo lệnh Stop Loss dạng Native Reduce-only trên Hyperliquid. Ghi nhận nhãn stop_trigger_crossed_at khi stop bị cắn và kích hoạt priority audit. | High | Stop loss đóng vai trò giới hạn lỗ, không phải tránh thanh lý hoàn toàn. |
| Hợp đồng BnzaExVault | Hợp đồng Solidity mới trên Base để custody (giữ hộ) LP NFT của người dùng, độc lập hoàn toàn với BnzaRouter v2.2.1 hiện tại. | High | Option C của đề xuất custody. |
| Kiểm soát Concurrency & Rate Limit | Sử dụng UserLockDO (lease-based lock) để khóa tiến trình ghi trên mỗi user và HLRateLimitDO để kiểm soát rate limit của Hyperliquid. | High | Tránh xung đột nonce và lỗi trùng lặp mutation. |
| Bảo mật khóa Agent | Mã hóa khóa Agent bằng secret store của Cloudflare (envelope encryption) thay vì lưu trữ master private key trực tiếp. | High | Đảm bảo an toàn khóa đầu tư của người dùng. |
| Reconcile & Deep Audit | Cơ chế đối soát sau giao dịch (post-order reconcile) và audit định kỳ (6h một lần hoặc 1h nếu rủi ro) để đồng bộ trạng thái thực tế giữa D1 DB và Hyperliquid. | High | Ngăn chặn lệch trạng thái (stale/desync). |

### 3.2 Out of scope / chưa làm trong phase này (Deferred)

| Area / site / module / capability | Lý do loại trừ / deferred | Ảnh hưởng đến QC |
|---|---|---|
| Mobile UI & Admin/Config UI | Hoàn thiện phần core backend và contract trước. Giao diện được phát triển ở phase sau. | QC thực hiện kiểm thử và vận hành thông qua các công cụ API/CLI hoặc gọi trực tiếp smart contract. |
| Nhiều bot trên mỗi người dùng | Quy định 1 user = 1 active Ex Bot trong Phase A để đơn giản hóa quản lý tài khoản phụ. | Thiết kế kịch bản thử nghiệm đảm bảo ràng buộc single-active-bot trên mỗi tài khoản phụ. |
| Mạng Optimism | Trì hoãn sang Phase 2 (chờ kết quả backtest). | Chỉ thiết kế bộ test case chạy trên Base. |
| LP Range dạng Ladder (Nhiều dải) | Chỉ hỗ trợ single range ±5% trong Phase 1. | Chưa cần test các kịch bản nhiều range ghép. |

### 3.3 Assumption, dependency, constraint quan trọng

| Loại | Nội dung | Ảnh hưởng đến QC Agent | Cần xác nhận? |
|---|---|---|---|
| Dependency | Địa chỉ deploy BnzaExVault, Operator, và cấu hình Multi-sig cần được xác định từ trước W3. | Không có contract deploy và cấu hình thì không thể thực hiện kiểm thử tích hợp. | Yes |
| Constraint | Giới hạn rate limit của Hyperliquid REST API (1200 weight/phút/IP). | QC cần giả lập các tình huống rate limit bị vượt quá để kiểm chứng HLRateLimitDO hoạt động tốt. | No |
| Assumption | Phí tổn thất vô thường (IL) chỉ được giảm thiểu chứ không thể bị xóa bỏ hoàn toàn bởi chiến lược hedge. | Cần lưu ý khi thiết kế kịch bản nghiệm thu PnL, không được kỳ vọng rủi ro IL về 0. | No |

---

## 4. Cấu trúc hệ thống và tài liệu high-level liên quan

### 4.1 System / site / portal overview

| Site / portal / app / component | Mục đích | Nhóm user chính | Module chính | Ghi chú |
|---|---|---|---|---|
| **BNZA POOL UI** | Giao diện người dùng Next.js để xem thông tin vị thế bot, quản lý nạp/rút, theo dõi số dư margin và các cảnh báo rủi ro. | DeFi User | Dashboard, Bot Control | Defer trong Phase A1, điều khiển bằng API. |
| **BNZA Operator (CF Workers)** | Hệ thống backend trung tâm chạy trên Cloudflare Workers xử lý cron định kỳ, queue mutation, và kết nối APIs bên ngoài. | System/API | Cron, Queue Processor, HyperliquidAdapter | Xử lý bất đồng bộ thông qua các hàng đợi (Queue). |
| **Durable Objects (DOs)** | Quản lý trạng thái chia sẻ có tính nhất quán cao gồm UserLockDO (khóa ghi song song), HLRateLimitDO (rate limit), MarketDataDO (cache slot0). | Backend Services | Concurrency, Caching, Rate Limiting | Chạy độc lập trong cụm DO. |
| **D1 Database** | Cơ sở dữ liệu SQLite sharded của Cloudflare để lưu trữ trạng thái hiện tại (hot state), lịch sử rebalance, circuit breakers, và API keys mã hóa. | Backend Services | Database Storage | Phase A1 dùng 1 DB shard. Phase C chia làm 16 DB shards. **EXBOT dùng DB riêng biệt `bnza-exbot-db`**, tách khỏi OPERATOR D1. |
| **BnzaExVault** | Hợp đồng Solidity quản lý tài sản ký gửi (custody) của người dùng trên mạng Base. | Smart Contract | NFT Vault, Emergency controller | Operator chỉ được quyền điều phối LP (rebalance/close/collect) không được chiếm đoạt tài sản. |
| **packages/exbot-core** | Pure logic dùng chung cho cả live EXBOT và Backtest — position math, hedge math, rebalance/risk rules, lifecycle, PnL model. | Shared Library | Position, Hedge, Lifecycle, PnL | Build trước, freeze types + signatures sớm. Không chứa side effect (không gọi D1/HL/env/secret). |
| **backtests/exbot** | Offline simulation và reporting: data crawl, LP/hedge/strategy simulator, scenario/parameter testing, reports. | Backtest Track | Data Pipeline, Simulation, Reporting | Imports `exbot-core` — logic không duplicate so với live. |
| **Hyperliquid & Uniswap V3** | Sàn giao dịch phái sinh perpetual và sàn giao dịch AMM spot ngoại vi mà hệ thống tích hợp trực tiếp. | External Protocol | Margin Account, Perpetuals, Spot LP pool | Tích hợp qua REST/WebSocket API và JSON-RPC. |

**Data store boundary:**
- `bnza-operator D1`: user/wallet/whitelist, POOL existing tables.
- `bnza-exbot-db (DEDICATED)`: bots (+lifecycle_state), positions (custodian=vault), hedge_legs, bot_runtime_state, rebalance_attempts, circuit_breakers, funding_daily_metrics, queue_idempotency, hl_agent_keys (envelope-encrypted).

### 4.2 Các file high-level liên quan

| File | Vai trò | Trạng thái | Ghi chú |
|---|---|---|---|
| **project-config.md** | Cấu hình thông tin tổng quan dự án, các link tài liệu, cấu hình môi trường, tài khoản test và APIs bên thứ ba. | Approved (v3) | Chứa các thông tin cơ sở cho toàn dự án. |
| **path-registry.md** | Khai báo toàn bộ đường dẫn logic (logical names) của các artifact dùng chung cho các AI Agent. | Approved | Đảm bảo tính nhất quán của cấu trúc thư mục. |
| **project-context-master.md** | File tổng hợp tri thức dự án (chính là tài liệu này), cung cấp bối cảnh tổng quan cho các QC Agent. | Draft (Đang cập nhật) | Đầu ra của skill `qc-context-master`. |
| **SPEC_v5.2.5.md** | Tài liệu đặc tả kỹ thuật đầy đủ — luồng nghiệp vụ, tính toán, API, hợp đồng, NFR. | Approved (v5.2.5) | Nguồn tham chiếu chính cho spec review và scenario design. |
| **exbot-implementation-overview.md** | Tổng quan triển khai: quyết định đã khóa, kiến trúc component, mô hình đội nhóm (track), cấu trúc source. | Approved (no-version) | Giúp QC Agent hiểu ranh giới giữa các package và trách nhiệm từng track. |
| **exbot-task-breakdown.md** | Phân rã task chi tiết theo SH-/EX-/BT- với acceptance criteria và trạng thái tiến độ (☐/◐/☑). | Approved (no-version) | Nguồn chính để lập Feature Inventory và đánh giá scope kiểm thử. |
| **Exbot_Backtest_WBS.xlsx** | WBS cho backtest track (Excel). | Approved (no-version) | Binary — tham chiếu bổ sung cho Track 2 Backtest. |
| **qc-dashboard.md** | Dashboard theo dõi trạng thái thiết kế và kiểm thử của từng feature theo từng usecase. | Missing / TBD | Sẽ được bootstrap sau khi chạy xong `qc-site-map`. |
| **agent-work-log.md** | Nhật ký ghi nhận các phiên chạy của các AI Agent trên từng thiết bị làm việc. | In use | Tự động tổng hợp từ các file JSONL trong thư mục `agent-work-log.local/`. |

---

## 5. Users, roles và permission tổng quan

| Role / actor | Mô tả | Workflow chính | Permission / responsibility tổng quan | Ghi chú QC |
|---|---|---|---|---|
| **DeFi User (Bot Owner)** | Chủ sở hữu vị thế đầu tư. Người cung cấp vốn ban đầu và thụ hưởng lợi nhuận ròng. | - Khởi tạo bot<br>- Nạp LP WETH/USDC vào BnzaExVault<br>- Ký quyền ủy quyền Operator<br>- Rút vốn / Yêu cầu đóng vị thế khẩn cấp. | - Xem báo cáo hiệu suất (PnL, APR).<br>- Điều khiển trạng thái active/pause của bot.<br>- Thực hiện yêu cầu đóng bot thu hồi tiền mặt.<br>- *Không* có quyền ký lệnh giao dịch trực tiếp trên Hyperliquid (thông qua Agent Key ủy quyền). | Phải kiểm chứng ràng buộc giới hạn: 1 user chỉ được có tối đa 1 Ex Bot hoạt động tại Phase A. |
| **BNZA Operator (System Worker)** | Hệ thống backend tự động (Cloudflare Workers) đóng vai trò là Operator thực thi chiến lược. | - Chạy Light-check mỗi 5 phút<br>- Kích hoạt và gửi lệnh Hedge-sync<br>- Thực hiện Post-order Reconcile và Deep Audit. | - Quyền gọi các hàm được phân quyền (Operator-only) trên hợp đồng BnzaExVault (rebalance, close, collect fees).<br>- Quyền đặt lệnh (Short, Stop Loss, Delta-adjust) trên tài khoản phụ Hyperliquid thông qua Agent Key.<br>- *Không* có quyền chuyển tiền ra khỏi hợp đồng BnzaExVault về ví hệ thống (bảo vệ tài sản người dùng). | Cần kiểm thử trường hợp Operator bị tấn công hoặc lỗi logic: hợp đồng thông minh phải chặn việc rút tài sản sang địa chỉ khác Operator/User. |
| **Admin / Emergency Multi-sig** | Ban quản trị dự án, kiểm soát các trường hợp khẩn cấp hoặc sự cố hệ thống nghiêm trọng. | - Tạm dừng hợp đồng BnzaExVault khi có sự cố hack/exploit<br>- Giải phóng Circuit Breaker<br>- Kích hoạt khôi phục dữ liệu thủ công (manual_admin). | - Pause/Unpause hợp đồng BnzaExVault.<br>- Kích hoạt rút tiền khẩn cấp (Emergency Withdraw) về ví của người dùng.<br>- Cấu hình nâng cấp thông số hệ thống và mở khóa các bot bị dừng do Circuit Breaker. | Kiểm thử tính đúng đắn của Multi-sig trong các tình huống khẩn cấp (Emergency Flow). |

---

## 6. Business flow, module relationship và impact area

### 6.1 Flow chính cấp project

| Flow ID | Flow name | Actor chính | Module/site liên quan | Trigger | Kết quả chính | Ghi chú impact/regression |
|---|---|---|---|---|---|---|
| **FLOW-001** | Khởi tạo Bot & Ký gửi Tài sản | DeFi User, Operator | BnzaExVault, D1, Hyperliquid, UI | Người dùng thực hiện lệnh Start Bot trên UI/API và nạp LP NFT. | Bot được chuyển trạng thái `LP_OPENING` -> `LP_OPEN`. Tài sản NFT nằm an toàn trong Vault. Vị thế phòng vệ ban đầu được thiết lập trên HL. | Lỗi ở luồng này sẽ khiến bot bị kẹt ở trạng thái `LP_OPENING` hoặc NFT bị chuyển vào vault nhưng không kích hoạt được hedge. |
| **FLOW-002** | Light-check & Rebalance tự động | Operator (Worker) | D1, MarketDataDO, UserLockDO, Hyperliquid | Cron chạy định kỳ mỗi 5 phút hoặc khi nhận sự kiện. | Đánh giá điều kiện Rebalance. Nếu thỏa mãn và thỏa điều kiện Phí (Hedge budget cap < 30%), thực hiện lệnh điều chỉnh Delta-only trên HL và cập nhật D1. | Luồng này chạy liên tục. Lỗi tính toán vị thế sẽ dẫn tới mở sai khối lượng Hedge (gây lỗ cho user). |
| **FLOW-003** | Khớp Stop Loss & Đóng Vị thế Khẩn cấp | Hyperliquid, Operator | Hyperliquid, BnzaExVault, Queue, D1 | Giá ETH chạm ngưỡng stop_price đặt trên Hyperliquid. | Lệnh Native Stop Loss khớp trên HL. Operator ghi nhận nhãn `stop_trigger_crossed_at`, tự động đóng vị thế LP trên Uniswap qua Vault, rút thanh khoản về ví user và chuyển trạng thái bot về `LP_CLOSED` hoặc `LP_FAILURE`. | Luồng rủi ro cao. Nếu HL khớp Stop Loss nhưng Operator không phát hiện hoặc không đóng được LP Uniswap, user sẽ chịu rủi ro biến động giá trần mà không còn vị thế bảo hiểm. |
| **FLOW-004** | Đối soát Trạng thái (Reconcile & Audit) | Operator (Worker) | D1, Hyperliquid, Uniswap, RPC | Chạy định kỳ mỗi 6 giờ (hoặc 1 giờ nếu cảnh báo rủi ro). | Phát hiện và khắc phục các sai lệch trạng thái giữa database D1 và thực tế sàn HL/Uniswap (do nghẽn mạng, lỗi API). | Đảm bảo tính nhất quán (Atomicity). Nếu đối soát sai hoặc bỏ qua lệch vị thế lớn, hệ thống có thể liên tục gửi lệnh sai gây lỗi lặp. |

### 6.2 Quan hệ giữa module / data / integration

| Area A | Liên quan đến Area B | Kiểu liên quan | Ảnh hưởng QC |
|---|---|---|---|
| **Tính toán vị thế LP (Uniswap)** | **Khối lượng Hedge (Hyperliquid)** | Data dependency | Mọi sự sai lệch trong tính toán lượng WETH thực tế của LP NFT trên Uniswap (do giá trượt, tick thay đổi) sẽ ảnh hưởng trực tiếp đến khối lượng vị thế Short cần mở trên HL. QC cần test kỹ các biên giá (out of range, boundary). |
| **Tài khoản phụ (Subaccount)** | **Khóa ghi UserLockDO** | Permission / Concurrency | Hyperliquid sử dụng cơ chế tăng nonce tuần tự cho mỗi giao dịch của subaccount. Do đó, UserLockDO phải đảm bảo không có 2 tiến trình ghi nào cùng thực thi lệnh trên một subaccount tại một thời điểm để tránh lỗi đè nonce (nonce collision). |
| **Tích lũy Phí LP (Uniswap)** | **Hedge Budget Cap (Hyperliquid)** | Integration | Phí thu được từ Uniswap LP (thu thập qua subgraph/RPC) được dùng để tính toán budget cap 30% cho chi phí rebalance. Nếu phí được lấy sai hoặc trễ, hệ thống có thể chặn rebalance sai hoặc cho phép rebalance quá tay làm hao hụt vốn. |

---

## 7. Rule chung, data/state và integration cần nhớ

### 7.1 Rule chung áp dụng nhiều function

| Rule | Áp dụng cho | Ảnh hưởng đến review/spec/scenario/test case |
|---|---|---|
| **Hedge Budget Cap (Giới hạn Phí)** | Tác vụ Rebalance | Chi phí rebalance (gas + trượt giá + phí giao dịch) của 1 bot không được vượt quá **30%** lượng phí thu về trong 7 ngày gần nhất của LP đó. QC cần tạo test case giả lập khi phí LP tích lũy thấp thì hệ thống phải chặn/giảm tần suất rebalance. |
| **Delta-only Adjustment** | Khớp lệnh Hedge | Chỉ mua/bán thêm lượng chênh lệch (delta = targetSize - actualSize). Nghiêm cấm đóng toàn bộ vị thế rồi mở lại (trừ khi rút vốn toàn bộ). QC cần verify khối lượng order thực tế gửi lên HL phải khớp với delta tính toán. |
| **Circuit Breaker (Tự ngắt)** | Trạng thái Bot | Nếu bot có **3 lần rebalance thất bại liên tiếp trong vòng 24 giờ**, hệ thống phải tự ngắt, chuyển bot sang trạng thái dừng bảo vệ (`SAFE_MODE` hoặc `LP_FAILURE`) và bắn cảnh báo. QC cần test case lỗi API HL liên tiếp để kích hoạt ngắt. |
| **Chính sách 1-User 1-Bot** | Đăng ký & Tạo Bot | Giới hạn mỗi người dùng chỉ được chạy tối đa 1 bot active trong Phase A. QC cần kiểm tra xem hệ thống có chặn tạo bot thứ 2 khi bot 1 đang hoạt động không. |
| **Hedge Ratio & Đòn bẩy cố định** | Giao dịch | Tỷ lệ hedge cố định **70%** (Balanced), đòn bẩy Isolated **3x**. QC cần kiểm thử đầu vào các giá trị này không đổi trong suốt vòng đời bot ở Phase A. |
| **No Float (Không dùng số thực)** | Toàn bộ logic tính toán (exbot-core, D1, config) | Tất cả tỷ lệ, ngưỡng và khối lượng phải dùng bigint hoặc decimal-string. Nghiêm cấm dùng float/number cho các phép tính quan trọng. QC cần verify `SH-02`, `SH-03`, `SH-04` với test vector biên (boundary values). |
| **No Plaintext Key (Không lưu khóa thô)** | Quản lý Agent Key, Logging | HL Agent Key và Master Private Key không được lưu dưới dạng raw text trong D1, Cloudflare Logs hoặc bất kỳ log output nào. QC cần kiểm tra log sanitization trong `EX-45` và `EX-07`. |
| **EXBOT không public internet** | Kiến trúc / Transport | `apps/bnza-exbot` chỉ được gọi qua Cloudflare service binding từ OPERATOR — không có public endpoint. QC cần xác nhận không có route nào của EXBOT expose ra internet public. |

### 7.2 Data object / state quan trọng cấp project

| Object / entity | Mô tả | State / lifecycle chính | Ghi chú QC |
|---|---|---|---|
| **Ex Bot (Bot State)** | Đối tượng bot đại diện cho vị thế đầu tư của user. Lưu trong D1 database. | `LP_OPENING` -> `LP_OPEN` <br> `LP_REBALANCING` <br> `LP_CLOSING` -> `LP_CLOSED` <br> `LP_FAILURE` (khi ngắt hoặc cắn stop loss) | QC cần thiết kế ma trận chuyển trạng thái (State Transition Matrix) để test đầy đủ các trường hợp chuyển đổi hợp lệ và không hợp lệ. |
| **Hedge Leg (Vị thế Hedge)** | Ghi nhận vị thế phòng vệ trên Hyperliquid tương ứng với Bot. | `Active` (đang hedge)<br> `Rebalancing` (đang khớp delta)<br> `Closed` (đã đóng vị thế) | Cần đối chiếu chính xác trạng thái của Hedge Leg trong DB D1 với vị thế thực tế trên sàn Hyperliquid. |
| **Circuit Breaker Log** | Nhật ký lỗi phục vụ tự ngắt bot. | `Open` (bình thường) -> `Tripped` (đã kích hoạt tự ngắt) | QC kiểm tra cơ chế ghi log lỗi và reset log sau 24h hoặc sau khi Admin can thiệp. |

### 7.3 Integration / API / job / notification quan trọng

| Item | Loại | Module liên quan | Ghi chú QC / risk |
|---|---|---|---|
| **Hyperliquid REST/WS API** | API tích hợp | HyperliquidAdapter, Hedge-sync, Audit | Rủi ro: Nghẽn mạng, lỗi rate limit (1200 weight/phút). Cần kiểm thử cơ chế retry bất đồng bộ với exponential backoff. |
| **Uniswap V3 Subgraph & RPC** | API tích hợp | MarketDataDO, PositionAmountCalculator | Rủi ro: Subgraph bị đồng bộ chậm (stale block). Hệ thống cần lấy giá trị max() giữa dữ liệu subgraph và dữ liệu RPC trực tiếp của node. |
| **Cloudflare Secrets Store** | API bảo mật | Key Management, Authentication | Mã hóa Agent Key bằng khóa KMS/Envelope. QC cần đảm bảo private key của ví user và admin không bao giờ bị ghi log thô (raw print). |

---

## 8. Platform, environment, device và NFR/ràng buộc

### 8.1 Platform và environment tổng quan

| Hạng mục | Nội dung | Ghi chú QC |
|---|---|---|
| Platform type | API-only / backend-job (Phase A1) <br> Web-responsive (Next.js - Phase B+) | Hầu hết công việc kiểm thử ở Phase A1 sẽ chạy trên backend/API. Giao diện người dùng sẽ được kiểm thử ở phase sau. |
| Browser / OS / device cần quan tâm | API Clients (Postman/Curl), Linux/macOS CLI | Môi trường triển khai production của bot là Cloudflare Workers (V8 runtime). |
| Test environment | **Base Sepolia Testnet** (cho Smart Contract & Uniswap V3) <br> **Hyperliquid Testnet** (cho vị thế Hedge) | QC cần chuẩn bị faucet ETH trên Base Sepolia và tài khoản Testnet có USDC trên Hyperliquid để thực hiện test. |
| Integration mode | Real Testnet Sandbox | Kết nối trực tiếp đến testnet thực của Uniswap V3 (Base Sepolia) và Hyperliquid Testnet API. |
| Test data / account tổng quan | Cấu hình tài khoản test được lưu trữ và mô tả trong `project-config.md`. | Chỉ sử dụng các tài khoản và Agent Keys thử nghiệm, tuyệt đối không dùng khóa có chứa tài sản thực (Mainnet). |

### 8.2 NFR, security, compliance, legal, audit

| Loại ràng buộc | Nội dung đã biết | Ảnh hưởng QC |
|---|---|---|
| **Bảo mật (Security)** | Agent Key phải được mã hóa phong bì (envelope encryption) thông qua Cloudflare Secrets Store. Hệ thống không lưu trữ Master Private Key của người dùng. | QC cần kiểm tra tính bảo mật trong log: đảm bảo không có API keys hay private keys nào bị hiển thị dưới dạng raw text trong Cloudflare Logs hay D1 database. |
| **Hiệu năng (Performance)** | - Thời gian thực thi cron light-check: < 50ms CPU time.<br>- Thời gian hoàn thành 1 phiên rebalance (hedge-sync): < 30 giây để tránh nghẽn hàng đợi (Queue lag). | QC cần thực hiện kiểm thử tải (Load test) hoặc đo đạc latency của tiến trình hedge-sync trong điều kiện mạng lag để đảm bảo không bị quá 15 phút timeout của Queue consumer. |
| **Tuân thủ & Kiểm toán (Audit)** | Hợp đồng thông minh `BnzaExVault` bắt buộc phải được audit độc lập bởi bên thứ 3 (chi phí dự kiến 8.000$ - 25.000$) trước khi triển khai Mainnet. | QC cần rà soát mã nguồn contract dựa trên các file test Foundry đi kèm trước khi bàn giao cho bên audit. |
| **Pháp lý (Legal / Risk Disclosure)** | UI hiển thị minh bạch 2 mức APR: Gross APR (trước phí) và Net APR (sau khi trừ 30% phí hiệu suất). Cảnh báo rõ ràng về việc không bảo lãnh hoàn vốn và rủi ro trượt giá Stop Loss. | QC cần rà soát kỹ các nhãn hiển thị thông tin APR và cảnh báo rủi ro trên UI ở các phase sau. |

---

## 9. Đánh giá mức độ đủ context cấp project

| Nhóm context | Trạng thái | Độ tin cậy | Ảnh hưởng nếu thiếu/sai | Cần QC Lead bổ sung gì |
|---|---|---:|---|---|
| **Project goal & scope** | Ready | High | Thiếu thông số có thể làm sai lệch mục tiêu giảm thiểu drawdown | Xác nhận mục tiêu PnL cụ thể. |
| **System/site/module overview** | Ready | High | Hiểu sai kiến trúc 5-package + service binding có thể thiết kế kịch bản test concurrency không thực tế | N/A |
| **Feature/use case inventory** | Ready | High | Bỏ sót các track SH-/EX-/BT- khi thiết kế plan kiểm thử | Rà soát + ưu tiên test phase Phase 0 → A1 → A2. |
| **Users/roles/permission overview** | Ready | High | Kiểm thử sai phân quyền có thể gây lỗ hổng bảo mật (ví dụ: Operator tự ý chuyển NFT) | Xác nhận tính năng BnzaExVault chỉ cho phép Operator rút LP về ví User. |
| **Business flows & module relationship** | Ready | High | Thiết kế kịch bản test thiếu luồng lỗi hoặc không kiểm tra vùng ảnh hưởng (regression) | N/A |
| **Common rules/data/state/integration** | Ready | High | Bỏ sót quy tắc 30% fee cap, no-float, no-plaintext-key hoặc đè nonce | Xác nhận Hyperliquid error code mapping cho các kịch bản lỗi. |
| **Platform/environment/device/NFR** | Partial | Medium | Gặp lỗi rate limit RPC hoặc hết tài nguyên Cloudflare trong quá trình test | Xác nhận RPC endpoints dự phòng và tài khoản Cloudflare Paid. |
| **Document status tracking** | Partial | Medium | Khó theo dõi tiến độ thiết kế và thực thi kiểm thử theo tính năng | Chạy `qc-site-map` để tự động khởi tạo dashboard. |

**Kết luận:**  
Context cấp project hiện tại đã **Tạm đủ** để các QC Agent hiểu tổng quan hệ thống và bắt đầu thiết kế kịch bản kiểm thử cho Phase 0 + A1. Thiếu sót lớn nhất và có rủi ro cao nhất là các địa chỉ deploy BnzaExVault, phương pháp test Stop Loss giả lập trên HL Testnet, và xác nhận pool 0.3% có đủ thanh khoản cho backtest.

---

## 10. Open questions và việc cần QC Lead xác nhận

| ID | Câu hỏi / thông tin cần xác nhận | Vì sao quan trọng | Ảnh hưởng nếu chưa rõ | Priority | Owner | Status |
|---|---|---|---|---|---|---|
| Q-001 | Địa chỉ deploy BnzaExVault, Operator address, và danh sách ví Multi-sig signers cụ thể là gì? | Cần thiết để cấu hình môi trường test tích hợp và chạy các script giao dịch. | Không thể chạy test tích hợp A2 Live $1k. | High | QC Lead / zen | Open |
| Q-002 | Quy trình ký và phối hợp Multi-sig trong trường hợp Circuit Breaker bị ngắt được thực hiện như thế nào? | Đảm bảo tính sẵn sàng và thời gian khôi phục (recovery time) khi bot gặp sự cố. | Khó thiết lập kịch bản kiểm thử luồng phục vụ (recovery/admin flow). | Low | Tech Lead | Open |
| Q-003 | Cách thức giả lập sự kiện chạm Stop Loss trên Hyperliquid Testnet để kiểm chứng luồng tự động đóng vị thế LP trên Uniswap? | Stop loss là tính năng an toàn tối thượng của Ex Bot để bảo vệ tiền của người dùng. | Không thể kiểm thử đầy đủ độ tin cậy của luồng đóng vị thế khẩn cấp. | Medium | Tech Lead / QC Lead | Open |
| Q-004 | RPC endpoint dự phòng cho Base Sepolia Testnet là gì để tránh bị nghẽn lệnh khi chạy test suite? | Tránh gián đoạn trong quá trình chạy test tự động. | Test suite có thể bị fail ngẫu nhiên do lỗi rate limit RPC. | Low | Tech Lead | Open |
| Q-005 | Xác nhận tài khoản Cloudflare Paid plan sẽ được sử dụng cho môi trường kiểm thử và deploy thật? | Kiểm chứng giới hạn CPU time và subrequest limit ở môi trường giống production. | Có thể phát hiện muộn lỗi quá giới hạn tài nguyên của Cloudflare Workers. | Medium | QC Lead / zen | Open |
| Q-006 | OPERATOR có duy trì minimal status mirror của EXBOT hay luôn query live EXBOT status? (Quyết định EX-43) | Quyết định kiến trúc ảnh hưởng đến test path: cache vs live-query. | QC không xác định được đúng test design cho EX-43 | Medium | Tech Lead | Open |
| Q-007 | Ai có quyền điều chỉnh tham số chiến lược (hedge ratio, drift threshold, v.v.) khi kết quả live khác với backtest? | Cần xác định trước validation phase để biết ai ký duyệt thay đổi config. | Không rõ quyền/thủ tục → không test được luồng thay đổi tham số. | Medium | PM / Tech Lead | Open |
| Q-008 | API key của The Graph Studio (subgraph Uniswap V3 trên Base) đã được procurement chưa? | Không có API key → không thể crawl data primary cho BT-01. | Backtest Track 2 bị block hoàn toàn ở bước data pipeline. | High | Ops / Tech Lead | Open |
| Q-009 | Pool USDC/WETH fee tier 0.3% trên Base có đủ thanh khoản/volume đại diện không (so với tier 0.05%)? | Nếu pool 0.3% quá mỏng, phải fallback sang archive-RPC — tốn effort và làm chậm BT-01. | Quyết định sai có thể làm backtest không representative với môi trường live. | Medium | Tech Lead | Open |
| Q-010 | Ngày freeze final ABI của BnzaExVault là khi nào? | Track 1 (EX-23 vault-client) cần interface bị đóng để code song song với SC track. | Nếu ABI thay đổi muộn, Track 1 phải rework vault-client integration. | High | SC team | Open |

---

## Phụ lục A. Nguyên tắc giữ file gọn

- Chỉ ghi thông tin cấp project hoặc thông tin dùng chung cho nhiều Agent/skill.
- Không copy toàn bộ nội dung từ spec, wireframe, API document hoặc use case detail.
- Không ghi test case chi tiết trong file này.
- Không lặp lại danh sách feature dài nếu đã có `feature list` hoặc `qc-dashboard`.
- Nếu thông tin đã có ở file khác, chỉ tóm tắt vai trò và dẫn Agent đọc file đó.
- Nếu một thông tin chỉ ảnh hưởng một function cụ thể, đưa vào function-level context/spec review, không đưa vào file này.
