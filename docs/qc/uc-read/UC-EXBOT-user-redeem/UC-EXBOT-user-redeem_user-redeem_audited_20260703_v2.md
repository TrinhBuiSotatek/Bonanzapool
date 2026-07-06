# Bao cao ra soat muc do san sang cua Use Case

**Ten tai lieu:** UC-EXBOT-user-redeem Readiness Review v2 (Re-audit sau BA responses 2026-07-03)
**Ngay tao:** 2026-07-03
**Nguoi tao / Agent:** QC UC Read ExBot Agent
**Version:** v2

---

## Feature Brief - Tom tat nghiep vu

UC-EXBOT-user-redeem mo ta luong nha dau tu (Investor) tu dong ExBot va rut von bang cach goi ham `BnzaExVault.redeem(tokenId)` truc tiep tren blockchain. Day la luong "LP-first" — vi the LP tren Uniswap V3 duoc thanh ly ngay trong cung transaction on-chain, va phan USDC tu LP (LP-portion) duoc tra lai cho nha dau tu ngay lap tuc theo business rule bat dieu kien (BR-EXBOT-006).

Sau khi BA tra loi cac cau hoi trong v2 questions (2026-07-03), cac van de Blocker va High tu v1 da duoc giai quyet: (1) FR-EXBOT-071 xac nhan la loi citation — UC §7 FR Trace da cap nhat chi con FR-EXBOT-070; (2) Initial state `close_operations` = `requested`, da expand day du 3 buoc transition; (3) E-EXBOT-024 da dang ky va UC A2 da cite dung; (4) A2 postconditions da ro rang (`bots.lifecycle_state='error'`); (5) Reconcile failure = A2 path (khong apply SAFE_MODE); (6) Retry count = 3 da document.

Con lai 2 items "Outdated vs AWS arc" (I-02, I-03) chua giai quyet do dang cho Tech Lead xac nhan mechanism HL-portion transfer va advisory lock behavior duoi kien truc AWS moi. Cac items nay khong block happy path test design nhung can duoc giai quyet truoc khi thiet ke test case cho alternate flows.


---

## Bang ma viet tat (Reference code glossary)

| Ma / Tien to | Y nghia + vai tro trong du an | Dinh nghia tai |
|---|---|---|
| FR-EXBOT-* | Functional Requirement — yeu cau chuc nang cua module ExBot. Moi FR mo ta mot capability hoac behavior cu the cua Worker/Queue/DO. | frd.md |
| BR-EXBOT-* | Business Rule — rang buoc kinh doanh khong thay doi, ap dung toan module. BR-EXBOT-006 la rule quan trong nhat cho UC nay. | 02_backbone/common-rules.md |
| E-EXBOT-* | Error / System Message — ma thong bao loi hoac notification cua ExBot Worker, canonical source la message-list.md. | 02_backbone/message-list.md |
| NFR-EXBOT-* | Non-Functional Requirement — yeu cau phi chuc nang (SLA, throughput, security, idempotency). | frd.md §5 |
| INV-STOP | Invariant Stop — giao thuc protected stop replacement: cancel va place stop duoc bao ve tranh race condition. | frd.md FR-EXBOT-032 |
| LP-portion | Phan USDC thu duoc tu thanh ly LP position. Duoc tra on-chain ngay trong cung tx voi `redeem()`. | uc-user-redeem.md, FR-EXBOT-070(A) |
| HL-portion | Phan USDC thu duoc tu dong vi the hedge tren Hyperliquid. Duoc gui sau khi hedge close confirmed. | uc-user-redeem.md, FR-EXBOT-070(A) |
| RedemptionQueue | So cai FIFO de thanh toan USDC cho nha dau tu sau khi hedge dong (dung cho ca user_redeem va bot_safe_close). | frd.md FR-EXBOT-070 |
| UserLockDO / advisory lock | Cloudflare Durable Object (kien truc cu) hoac Postgres advisory lock (kien truc AWS moi) — mutex ngan concurrent HL mutations cho cung mot user. | frd.md FR-EXBOT-091 / AWS arc migration |
| KMS | AWS Key Management Service — noi luu va quan ly private key cua bot. Private key khong bao gio roi khoi KMS. | FR-EXBOT-080, flows.md F-03 |
| SLA | Service Level Agreement — thoa thuan muc do dich vu. Trong UC nay, SLA 5 phut cho hedge close. | NFR-EXBOT-003 |

---

## 0. Thong tin tai lieu

| UC ID | Ten feature / use case | Version | Trang thai tai lieu |
|---|---|---|---|
| UC-EXBOT-user-redeem | User-Initiated LP-First Redemption | Draft (updated 2026-07-03) | Draft |

| Nguoi viet / BA | Nguoi duyet | Ngay tao | Cap nhat lan cuoi |
|---|---|---|---|
| @hienduong | — | 2026-06-12 | 2026-07-03 |

| Artefact da doc | Version / ngay cap nhat | Vai tro cua artefact | Ghi chu |
|---|---|---|---|
| uc-user-redeem.md | 2026-07-03 | UC | File UC chinh — da cap nhat 7 changes theo BA responses |
| us-004.md | 2026-06-12 | User Story | US-EXBOT-004, linked story |
| frd.md | 2026-06-29 | FRD | FR-EXBOT-070 (two close systems), FR-EXBOT-080 (KMS), NFR-003 |
| srs/spec.md | 2026-06-29 | SRS spec | FR-070 through FR-073, NFR-003, E-010, E-012, E-024 |
| srs/states.md | 2026-07-03 | State diagram | close_operations states, lifecycle_state enum |
| srs/flows.md | 2026-06-29 | Flow diagram | F-04 user_redeem, F-05 bot_safe_close (acknowledged outdated) |
| srs/erd.md | 2026-06-29 | ERD | close_operations table schema, residual_amount field |
| 02_backbone/common-rules.md | 2026-06-26 | Common rule | BR-EXBOT-006 verbatim |
| 02_backbone/message-list.md | 2026-07-03 | Message list | E-EXBOT-010, E-EXBOT-012, E-EXBOT-024 |
| docs/qc/uc-read/UC-EXBOT-user-redeem/UC-EXBOT-user-redeem_user-redeem_questions_20260703_v2.md | v2 | Question backlog | 9 answered, 2 open (AWS arc), 1 deferred |
| docs/BA/qc-responses-2026-07-03.md | 2026-07-03 | BA response | @hienduong answers for user-redeem I-01 to I-11 |

---

## 1. Muc tieu va pham vi

### 1.1 Muc tieu nghiep vu

UC nay ton tai de dam bao nha dau tu co the thoat ExBot bat ky luc nao bang mot thao tac on-chain duy nhat (`redeem(tokenId)`), va nhan lai toan bo von (LP-portion ngay lap tuc, HL-portion sau khi hedge dong). Muc tieu nghiep vu cot loi: bao ve von nha dau tu bat ke trang thai cua he thong hedge — LP-portion khong bao gio bi giu lai hoac rollback do loi hedge.

### 1.2 Pham vi trong use case

| Hang muc / chuc nang | Mo ta | Nguon |
|---|---|---|
| On-chain redeem | Nha dau tu goi `BnzaExVault.redeem(tokenId)` on-chain; LP thanh ly ngay trong cung tx; LP-portion USDC ve vi nha dau tu | uc-user-redeem.md §3 step 1-3, FR-EXBOT-070(A) |
| Event detection & enqueue | Event watcher phat hien `RedemptionEvent`, enqueue vao `user_redeem` queue (priority cao nhat) | uc-user-redeem.md §3 step 4-5, flows.md F-04 |
| queue_idempotency insert | Worker insert `message_id` vao `queue_idempotency` (state='started'); UNIQUE conflict -> skip | uc-user-redeem.md §3 step 6, FR-EXBOT-010 |
| close_operations record creation (3 transitions) | Worker tao bang ghi `close_operations` voi `kind='user_redeem'`: Insert (state='requested') -> update state='lp_closed' -> update state='funds_returned' | uc-user-redeem.md §3 step 7, erd.md, states.md |
| UserLockDO / advisory lock acquire | Worker acquire lease truoc khi thuc hien HL mutations | uc-user-redeem.md §3 step 8, FR-EXBOT-026 |
| HL hedge close | Worker dong vi the short HL bang `closeShortReduceOnlyIoc` (full close, cloid) — retry toi da 3 lan khi reject/timeout | uc-user-redeem.md §3 step 9, flows.md F-04 |
| Stop cancel (INV-STOP) | Huy stop order qua `§19.5 replaceStopProtected` voi size=0 | uc-user-redeem.md §3 step 10, FR-EXBOT-032 |
| Reconcile | Verify vi the HL = 0 sau khi dong | uc-user-redeem.md §3 step 11, flows.md F-04 |
| HL-portion USDC transfer | Sau khi hedge close xac nhan, gui HL-portion USDC ve nha dau tu qua RedemptionQueue ledger | uc-user-redeem.md §3 step 13 |
| SLA monitoring | SLA 5 phut tu luc phat hien event. Neu qua -> admin alert E-EXBOT-010 (A1) | uc-user-redeem.md §4 A1, NFR-EXBOT-003 |
| Hedge close failure (A2) | HL close that bai sau 3 retries HOAC reconcile mismatch -> `residual_hl_liability`, `bots.lifecycle_state='error'`, admin nhan E-EXBOT-024 | uc-user-redeem.md §4 A2 |
| Duplicate message handling (A3) | Worker nhan message da xu ly -> detect qua `queue_idempotency` UNIQUE hoac `close_operations.idempotency_key` UNIQUE -> skip | uc-user-redeem.md §4 A3 |

### 1.3 Ngoai pham vi / chua bao gom

| Hang muc | Ly do ngoai pham vi / chua ro | Anh huong den test |
|---|---|---|
| bot_safe_close flow | FR-EXBOT-070(B), US-EXBOT rieng, khong thuoc UC nay | Khong anh huong UC nay |
| LP liquidation logic (Solidity) | zen-proprietary, SOTATEK chi tich hop qua ABI | Tester khong verify noi bo contract |
| HL-portion USDC amount calculation | UC va BA response xac nhan: co the xac minh qua RedemptionQueue ledger, nhung cong thuc chi tiet (HL close P&L minus fees/funding) chua duoc document chinh thuc. Pending Tech Lead confirmation duoi AWS arc (I-02) | Anh huong expected result khi test buoc 13 — xem I-02 |
| residual_hl_liability recovery flow | UC mota postcondition (lifecycle_state='error') nhung khong mo ta luong admin xu ly tiep theo | Tester khong biet bot chuyen sang trang thai nao sau khi admin can thiep |
| AWS arc migration details | UserLockDO -> Postgres advisory lock behavior chua duoc document day du duoi kien truc AWS (I-03) | Anh huong test case lock contention |
| flows.md F-05 (bot_safe_close flow) | BA xac nhan outdated vs AWS arc, se duoc viet lai trong migration pass | Khong anh huong UC nay |

---

## 2. Actor, vai tro va quyen han

| Actor / Role | Loai | Vai tro trong use case | Quyen han / gioi han lien quan | Nguon |
|---|---|---|---|---|
| ACT-I — Investor (End User) | Primary | Goi `BnzaExVault.redeem(tokenId)` on-chain de khoi tao luong. Khong tuong tac truc tiep voi Worker. | Chi co the redeem tokenId thuoc so huu cua minh. | uc-user-redeem.md §1, us-004.md |
| ACT-O — OPERATOR (System / Worker) | System | Redeem event watcher phat hien su kien; Redeem Worker thuc hien dong hedge, ghi `close_operations`, gui HL-portion | Worker hanh dong thay nha dau tu; khong can xac nhan them tu nha dau tu | uc-user-redeem.md §3, flows.md F-04 |
| ACT-A — Admin (zen) | Secondary | Nhan alert khi SLA bi vi pham (E-EXBOT-010) hoac khi hedge close that bai (E-EXBOT-024 — `residual_hl_liability`) | Khong co action tu dong trong UC nay; chi nhan notification | uc-user-redeem.md §4 A1, A2, message-list.md E-EXBOT-024 |
| BnzaExVault (on-chain contract) | External | Thuc hien LP liquidation, phat `RedemptionEvent`, tra LP-portion USDC trong cung tx | Contract do zen phat trien; SOTATEK tich hop qua ABI | uc-user-redeem.md §3 step 1-4 |
| Hyperliquid API | External | Dong vi the short, huy stop order | HL rate limit budget: <=800 weight/min (NFR-EXBOT-004) | flows.md F-04, frd.md |

**Nhan xet readiness:** Actor day du ro cho thiet ke test theo role. UC §2 preconditions v2 mo rong: "Bot `status='active'` (or paused/safe_mode — user may redeem from any non-closed state)" — day la thong tin moi so voi v1 nhung CHUA co trong states.md; xem I-N1.

---

## 3. Dieu kien truoc va ket qua sau

### 3.1 Dieu kien truoc

| # | Dieu kien truoc | Bat buoc? | Nguon |
|---|---|---|---|
| 1 | Bot ton tai va dang o trang thai `active`, `paused`, hoac `safe_mode` — user co the redeem tu bat ky trang thai nao ngoai trang thai da dong | Yes | uc-user-redeem.md §2 (v2 update 2026-07-03) |
| 2 | `bots.status` khong phai `closing` hoac `closed` | Yes | states.md, E-EXBOT-012 |
| 3 | Nha dau tu so huu `tokenId` hop le tren BnzaExVault | Yes | uc-user-redeem.md §2 |
| 4 | Event watcher dang hoat dong va co the nhan `RedemptionEvent` tu on-chain | Yes | flows.md F-04 |
| 5 | HL agent key co `key_status='active'` (can thiet de Worker ky lenh dong hedge qua Signing Lambda + KMS) | Yes (implicit) | frd.md FR-EXBOT-080, FR-EXBOT-001 |

**Luu y:** Precondition 1 da mo rong so voi v1 — `paused` va `safe_mode` gio cho phep redeem. Dieu nay can duoc verify voi states.md (xem I-N1 ben duoi).

### 3.2 Ket qua sau khi hoan tat

| Thao tac | Trang thai he thong / du lieu sau khi hoan tat | Nguon |
|---|---|---|
| Happy path hoan tat | `close_operations.state='done'`, `bots.lifecycle_state='closed'`, `bots.status='closed'`, LP-portion USDC da tra on-chain, HL-portion USDC da gui qua RedemptionQueue | uc-user-redeem.md §5, flows.md F-04 |
| Hedge close that bai (A2) — gom ca reconcile mismatch | `close_operations.state='residual_hl_liability'`, `bots.lifecycle_state='error'`, `bots.status='error'`, LP-portion da tra (khong bi dao nguoc), admin nhan E-EXBOT-024 | uc-user-redeem.md §4 A2, §5 (A2 postconditions), I-06 Answered |
| SLA breach (A1) | Admin alert E-EXBOT-010 da gui. Hedge close van tiep tuc (SLA breach chi trigger alert, khong abort) | uc-user-redeem.md §4 A1, message-list.md |
| Duplicate message (A3) | Khong co hanh dong nao duoc thuc hien them; Worker tra ve som | uc-user-redeem.md §4 A3 |
| Bot da dong (E-EXBOT-012) | Worker tra E-EXBOT-012 (409): "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |

---

## 6. Phan ra nghiep vu va luong xu ly

### 6.1 Luong chinh: User-Initiated LP-First Redemption

#### A. Luong xu ly (v2 — cap nhat theo BA responses 2026-07-03)

| Buoc | Actor | Hanh dong / trigger | Phan hoi he thong - happy path | Luong thay the | Luong loi / exception | Nguon |
|---|---|---|---|---|---|---|
| 1 | ACT-I | Goi `BnzaExVault.redeem(tokenId)` on-chain | LP position duoc thanh ly ngay trong cung tx; LP-portion USDC tra ve vi nha dau tu on-chain | — | Tx bi reverted (tokenId khong ton tai hoac khong thuoc so huu) — ngoai pham vi SOTATEK | uc-user-redeem.md §3 step 1-2 |
| 2 | BnzaExVault | Phat `RedemptionEvent(botId, redeemTxHash, userAddress)` + LP-portion USDC da ve vi (on-chain guarantee) | Event watcher nhan duoc event | — | Event watcher bo lo event — khong co retry mo ta trong UC | uc-user-redeem.md §3 step 2-4, flows.md F-04 |
| 3 | Event watcher | Enqueue `{botId, redeemTxHash, userAddress}` vao `user_redeem` queue (priority cao nhat) | Message duoc enqueue | — | — | uc-user-redeem.md §3 step 5, flows.md F-04, frd.md FR-EXBOT-010 |
| 4 | Worker | Nhan message tu queue; SLA timer bat dau (5 phut) | SLA tracking bat dau | A1: neu SLA bi vi pham -> admin alert E-EXBOT-010 | A3: neu duplicate message -> detect qua queue_idempotency -> exit | uc-user-redeem.md §3 step 5-6, NFR-EXBOT-003 |
| 5 | Worker | Insert `message_id` vao `queue_idempotency` (state='started'); UNIQUE conflict -> return immediately (A3) | message_id ghi nhan thanh cong | — | UNIQUE conflict -> A3 duplicate detection | uc-user-redeem.md §3 step 6, frd.md FR-EXBOT-010 |
| 6 | Worker | Kiem tra trang thai bot — dam bao khong phai `closing`/`closed` | Bot o trang thai hop le | — | Bot da `closed` -> E-EXBOT-012 (409) | states.md, message-list.md E-EXBOT-012 |
| 7a | Worker | Tao bang ghi `close_operations`: Insert (kind='user_redeem', state='requested', idempotency_key UNIQUE) | Bang ghi duoc tao | — | idempotency_key da ton tai (duplicate) -> skip | uc-user-redeem.md §3 step 7, erd.md |
| 7b | Worker | Update `close_operations.state='lp_closed'` (LP da thanh ly on-chain — da xac nhan tu step 1) | State updated | — | — | uc-user-redeem.md §3 step 7 |
| 7c | Worker | Update `close_operations.state='funds_returned'` (LP-portion USDC da ve vi — on-chain guarantee tu step 2) | State updated | — | — | uc-user-redeem.md §3 step 7 |
| 8 | Worker | Acquire `UserLockDO` lease (hoac Postgres advisory lock duoi AWS arc) cho user nay | Lock acquired | — | Lock contention — behavior duoi AWS arc chua duoc document (xem I-03) | uc-user-redeem.md §3 step 8 |
| 9 | Worker | Goi `closeShortReduceOnlyIoc` (full close, cloid theo FR-EXBOT-022) tren HL — retry toi da 3 lan khi reject/timeout | HL short position dong thanh cong | — | A2: het 3 retries -> `residual_hl_liability` | uc-user-redeem.md §3 step 9, I-11 Answered |
| 10 | Worker | Huy stop order qua `§19.5 replaceStopProtected(size=0)` | Stop order da huy | — | Stop cancel that bai — khong mo ta separate trong UC | uc-user-redeem.md §3 step 10, FR-EXBOT-032 |
| 11 | Worker | Reconcile — fetch `clearinghouseState` de verify vi the HL = 0 | Vi the xac nhan = 0 | — | A2: reconcile mismatch (vi the != 0) -> `residual_hl_liability` (SAME path as hedge close failure) | uc-user-redeem.md §3 step 11, I-08 Answered |
| 12 | Worker | Cap nhat `close_operations.state='hedge_closed'` | State updated | — | — | uc-user-redeem.md §3 step 12 |
| 13 | Worker | Gui HL-portion USDC ve nha dau tu qua RedemptionQueue ledger | USDC transferred | — | Transfer that bai — khong mo ta trong UC | uc-user-redeem.md §3 step 13 |
| 14 | Worker | Cap nhat `close_operations.state='done'`; `bots.lifecycle_state='closed'` | Bot hoan toan dong | — | — | uc-user-redeem.md §3 step 14 |
| 15 | Worker | Cap nhat `queue_idempotency.state='succeeded'` | Processing hoan thanh | — | — | uc-user-redeem.md §3 step 15 |

#### B. Business rules va validation

| Field / Object / Rule | Dieu kien / constraint | Bat buoc? | Ket qua khi hop le | Ket qua khi khong hop le | Nguon |
|---|---|---|---|---|---|
| BR-EXBOT-006 — LP-portion repayment bat dieu kien | Hedge close failure KHONG duoc block hoac rollback LP-portion da tra | Yes (P0) | LP-portion duoc giu nguyen | Vi pham nghiem trong: day la business rule P0 | common-rules.md BR-EXBOT-006: "`user_redeem` LP-portion repayment is unconditional. Hedge close failure must never block or reverse the LP-portion return to the user." |
| close_operations idempotency | `idempotency_key UNIQUE` tren bang `close_operations` | Yes | Insert thanh cong -> tiep tuc xu ly | UNIQUE constraint violation -> duplicate delivery -> skip | erd.md, FR-EXBOT-070 |
| SLA 5 phut | Hedge close phai hoan tat <= 5 phut tu luc phat hien event | Yes (NFR) | Hoan tat dung han | SLA breach -> E-EXBOT-010 admin alert (khong abort hedge close) | NFR-EXBOT-003, message-list.md E-EXBOT-010 |
| INV-STOP protocol | Stop cancel phai qua `replaceStopProtected(size=0)` — direct cancel-then-place khong duoc phep | Yes | Stop order huy an toan | Vi pham INV-STOP invariant | FR-EXBOT-032 |
| Full close (not delta-only) | user_redeem dung `closeShortReduceOnlyIoc` (full close) — ngoai le hop le theo FR-EXBOT-022 exception #1 | Yes | Toan bo vi the short dong | — | FR-EXBOT-022: "Full close/open is ONLY allowed for: 1. target size = 0 (bot close path)" |
| queue_idempotency | Consumer insert `message_id` vao `queue_idempotency` voi `state='started'` tai dau xu ly; UNIQUE conflict -> return immediately | Yes | Processing tiep tuc | UNIQUE conflict -> duplicate delivery -> return immediately | frd.md FR-EXBOT-010 |
| closeShortReduceOnlyIoc retry cap | Retry toi da 3 lan khi HL reject/timeout truoc khi chuyen sang A2 | Yes | Dong thanh cong trong 3 lan | Het 3 retries -> A2 path | uc-user-redeem.md §3 step 9, I-11 Answered |
| Reconcile failure = A2 path | Neu reconcile xac nhan vi the HL != 0 sau closeShortReduceOnlyIoc -> same outcome as hedge close failure | Yes | Vi the xac nhan = 0 | residual_hl_liability, lifecycle_state='error', E-EXBOT-024 | uc-user-redeem.md §4 A2 (expanded), I-08 Answered |
| SAFE_MODE khong ap dung | SAFE_MODE KHONG ap dung khi hedge close that bai trong user_redeem (LP da thanh ly, khong con gi de bao ve) | Yes | N/A | N/A — SAFE_MODE explicitly excluded from A2 path | I-08 Answered |
| Deterministic cloid (FR-EXBOT-022) | Cloid cho `closeShortReduceOnlyIoc` tuan theo cong thuc: `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | Yes | Cloid xac dinh duoc tao dung cong thuc | Moi retry dung cung cloid (same attemptId+stage+version) | FR-EXBOT-022, I-11-A Answered |

#### C. Thong bao, loi va phan hoi he thong

| Truong hop | Loai phan hoi | Noi dung phan hoi / message | Ma / muc goc | Nguon |
|---|---|---|---|---|
| SLA 5 phut bi vi pham | Admin notification (internal alert) | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | E-EXBOT-010 | message-list.md E-EXBOT-010 |
| Close attempted on already-closed bot | API error response | "Bot is already closed. No action needed." | E-EXBOT-012, HTTP 409 | message-list.md E-EXBOT-012 |
| Hedge close that bai hoac reconcile mismatch sau 3 retries | State transition + admin notification | `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; `bots.status='error'`; admin notification E-EXBOT-024 | E-EXBOT-024 (dang ky 2026-07-03) | message-list.md E-EXBOT-024: "User redemption hedge close failed. Manual intervention required." |
| Bot lifecycle hoan tat dong | State transition | `bots.lifecycle_state='closed'`, `bots.status='closed'`, `close_operations.state='done'` | Happy path postcondition | uc-user-redeem.md §5 |

---

## 7. Phan tich lien ket va anh huong giua cac chuc nang

| Chuc nang / hanh dong kich hoat | Khu vuc / UC / module bi anh huong | Anh huong nghiep vu | Kiem tra nhat quan du lieu | Nguon |
|---|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` on-chain | Event watcher (Fargate/chain indexer) -> `user_redeem` queue | Su kien on-chain trigger toan bo luong off-chain; neu event watcher bo lo event, luong khong bat dau | On-chain: LP thanh ly, LP-portion USDC ve vi. Off-chain: bang ghi `close_operations` duoc tao sau khi Worker xu ly | uc-user-redeem.md §3, flows.md F-04 |
| `close_operations` record creation (state='requested') | hedge-sync, light-check workers; `bots.lifecycle_state` | Khi `lifecycle_state='lp_closing'`, light-check va hedge-sync bi skip (states.md). Ngan hedge mutation dong thoi voi close | `close_operations.idempotency_key UNIQUE` ngan double settlement. Verify `bots.lifecycle_state` chuyen sang `lp_closing` | states.md, erd.md |
| HL hedge close (`closeShortReduceOnlyIoc`) | `close_operations`, `hedge_legs` | Vi the short tren HL = 0; `close_operations.state` tien toi `hedge_closed` sau reconcile | Reconcile confirm HL position = 0 truoc khi cap nhat state; reconcile mismatch -> A2 (khong phai SAFE_MODE) | flows.md F-04, I-08 Answered |
| Stop cancel (`replaceStopProtected(size=0)`) | `hedge_legs.stop_order_id`, `stop_cloid` | Stop order tren HL bi huy; INV-STOP invariant bao ve window 0-stop | Sau cancel, `hedge_legs.stop_cloid` va `stop_order_id` can duoc clear hoac marked as cancelled | FR-EXBOT-032 |
| `residual_hl_liability` state (A2) — gom ca reconcile mismatch | Admin dashboard, future reconciliation | Bot bi ket voi HL liability; `bots.lifecycle_state='error'`, `bots.status='error'`; admin phai dong thu cong residual HL position | `close_operations.residual_amount` ghi lai so tien con no; verify field nay duoc populate dung | uc-user-redeem.md §4 A2, erd.md, I-06/I-08 Answered |
| SLA breach alert (A1) | Admin notification system | Admin nhan thong bao nhung hedge close van tiep tuc; khong co interrupt hay abort | UC khong mo ta lieu SLA breach alert co duoc gui mot lan duy nhat hay co the gui lap | uc-user-redeem.md §4 A1, E-EXBOT-010 |
| HL-portion USDC transfer qua RedemptionQueue | `close_operations.state` -> `done`, `bots.lifecycle_state` -> `closed` | Sau khi nha dau tu nhan HL-portion, bot hoan toan dong | Tong USDC nha dau tu nhan = LP-portion (on-chain, ngay) + HL-portion (sau hedge close). Verify khong co double payment | uc-user-redeem.md §3 step 13-14 |

---

## 8. Acceptance Criteria

| AC # | Scenario | Given - dieu kien | When - hanh dong | Then - ket qua mong doi | Nguon / ghi chu |
|---|---|---|---|---|---|
| AC-01 | Happy path — hedge close thanh cong trong SLA | Bot dang `active`; nha dau tu so huu `tokenId` hop le | Nha dau tu goi `BnzaExVault.redeem(tokenId)` on-chain | LP-portion USDC tra trong cung tx on-chain; Worker dong hedge HL trong <=5 phut; `close_operations.state='done'`; `bots.lifecycle_state='closed'`; HL-portion USDC gui qua RedemptionQueue | us-004.md AC-004-1, NFR-EXBOT-003 |
| AC-02 | SLA breach — hedge close qua 5 phut | Bot dang `active`; hedge close Worker bi cham hoac HL co su co | Nha dau tu redeem; hedge close keo dai >5 phut | Admin nhan E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned."; hedge close van tiep tuc (khong abort) | us-004.md AC-004-2, message-list.md E-EXBOT-010 |
| AC-03 | Hedge close that bai sau LP da thanh ly (A2 — bat ky nguyen nhan: 3 retries OR reconcile mismatch) | Bot dang `active`; LP-portion da tra on-chain | Hedge close Worker het 3 retries HOAC reconcile xac nhan vi the != 0 | `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; `bots.status='error'`; LP-portion da tra KHONG bi rollback; admin nhan E-EXBOT-024: "User redemption hedge close failed. Manual intervention required." | us-004.md AC-004-3, BR-EXBOT-006, I-08 Answered |
| AC-04 | Duplicate message delivery | `close_operations` da ton tai voi `idempotency_key` cho lan redeem nay | Worker nhan lai cung message tu queue | Worker phat hien duplicate qua `queue_idempotency` UNIQUE hoac `close_operations.idempotency_key`; khong thuc hien bat ky HL mutation nao; exit gracefully | uc-user-redeem.md §4 A3 |
| AC-05 | Redeem tren bot da dong | Bot da co `bots.lifecycle_state='closed'` | Worker nhan message user_redeem | Worker tra E-EXBOT-012 (409): "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |
| AC-06 | LP-portion bat dieu kien khi HL API unavailable | HL API khong phan hoi; LP-portion da tra on-chain | Worker co dong hedge HL nhung HL unreachable (het 3 retries) | LP-portion khong bi block. Hedge close fail -> A2: `residual_hl_liability`. BR-EXBOT-006 duoc bao dam | BR-EXBOT-006, I-08 Answered |
| AC-07 | Bot o `lp_closing` state thi light-check bi skip | close_operations duoc tao, `lifecycle_state` chuyen sang `lp_closing` | Light-check worker chay cho bot nay | Light-check worker bo qua bot vi `lifecycle_state='lp_closing'` — khong enqueue hedge-sync | states.md |
| AC-08 | Redeem tu trang thai `paused` | Bot dang `paused` (`lifecycle_state` = paused variant); nha dau tu so huu tokenId | Nha dau tu goi `BnzaExVault.redeem(tokenId)` | Luong user_redeem chay binh thuong; LP-portion va HL-portion duoc tra; bot chuyen sang `closed` | uc-user-redeem.md §2 (v2 update 2026-07-03) — SUA LUÂN CAN XAC NHAN theo I-N1 |
| AC-09 (Suy luan can xac nhan) | Deterministic cloid cho retry closeShortReduceOnlyIoc | HL reject lan dau; Worker retry lan 2 | Worker retry closeShortReduceOnlyIoc | Same `botId`, `attemptId`, `stage` -> same cloid duoc su dung; HL dedup hoac detect duplicate | FR-EXBOT-022, I-11-A Answered |

---

## 9. Yeu cau phi chuc nang

| Nhom | Requirement | Anh huong den test | Nguon |
|---|---|---|---|
| Performance / SLA | Hedge close <= 5 phut tu luc phat hien event (NFR-EXBOT-003) | Test case can co timer verification; can moi truong simulate event detection timestamp | NFR-EXBOT-003 |
| Reliability / Resilience | LP-portion repayment unconditional (BR-EXBOT-006) — hedge failure khong block return | Test case can verify LP-portion khong bi rollback khi inject hedge failure sau on-chain redeem | BR-EXBOT-006 |
| Idempotency | `close_operations.idempotency_key UNIQUE`; `queue_idempotency` message dedup; cloid deterministic (FR-EXBOT-022) | Test case can verify redelivery khong tao duplicate settlement; retry dung cung cloid | frd.md FR-EXBOT-010, FR-EXBOT-022 |
| Security | HL agent key signing qua AWS KMS Signing Lambda; private key khong lo ra memory hay log | Tester verify khong co key material trong log/response | FR-EXBOT-080, frd.md NFR-006 |
| Audit / Logging | `close_operations` ledger ghi lai toan bo trang thai. `queue_idempotency` ghi lai message processing lifecycle | Test verify `close_operations` state transitions day du; `queue_idempotency.state` chuyen thanh 'succeeded' sau success | erd.md |
| Precision | Cac so tien USDC tinh bang BigDecimal (no float) — luu duoi dang TEXT string trong D1 | Test verify amount khong bi floating-point error | erd.md (no float storage invariant) |

---

## 10. Gap, mau thuan va cau hoi mo

### 10.1 Bang gap va cau hoi can xac nhan (Issue Register v2)

| ID | Muc uu tien | Loai van de | Tham chieu nguon | Noi dung van de | Vi sao quan trong | Trang thai |
|---|---|---|---|---|---|---|
| I-02 | High | MISSING_INFO | uc-user-redeem.md §3 step 13; flows.md F-04 | UC mo ta Worker "gui HL-portion USDC ve nha dau tu qua RedemptionQueue ledger" nhung khong dinh nghia: (a) HL-portion duoc tinh nhu the nao (tong so tien tu HL closing position minus fees? minus funding?); (b) ai thuc su la nguoi thuc hien on-chain transfer USDC duoi AWS arc (Worker goi truc tiep hay qua mechanism khac?); (c) transaction hash cua HL-portion transfer co duoc luu vao `close_operations.hedge_close_tx` khong? | Khong co cong thuc hoac mo ta source of truth cho HL-portion amount -> tester khong the verify so tien nha dau tu nhan dung khong. Mechanism chuyen doi duoi AWS arc chua duoc confirm. | **Outdated vs AWS arc — pending Tech Lead** |
| I-03 | Medium | MISSING_INFO | uc-user-redeem.md §3 step 8; spec.md FR-EXBOT-026; flows.md F-04 | Duoi AWS arc, UserLockDO duoc thay bang Postgres advisory lock + SQS FIFO. UC step 8 xac nhan "Worker acquires UserLockDO lease" nhung: (a) Behavior khi lock dang bi giu boi hedge-sync worker chua duoc document duoi AWS arc (re-queue voi delay nhu FR-EXBOT-026 hay spin-wait hay fail ngay?); (b) flows.md F-04 khong hien thi lock trong sequence diagram. Voi user_redeem co SLA 5 phut, re-queue voi delay co the vi pham SLA. | Behavior khi lock contention xay ra anh huong truc tiep den test case SLA va concurrency. | **Outdated vs AWS arc — pending Tech Lead** |
| I-N1 | Medium | UNCLEAR_INFO | uc-user-redeem.md §2 Preconditions (v2) | UC §2 v2 mo rong precondition: "Bot `status='active'` (or paused/safe_mode — user may redeem from any non-closed state)". Thong tin nay la moi so voi v1 va CHUA duoc phan anh trong states.md State Registry. Cu the: (a) Bot o `hedge_stopped_cooldown` co the duoc redeem khong? (b) Bot o `lp_rebalancing` co the duoc redeem khong? (c) Bot o `error` co the duoc redeem khong? states.md chi liet ke `lp_closing` nhu la buoc chuyen tiep khi close request, nhung khong noi ro cac trang thai nao DUOC PHEP khoi tao close request. | Tester can biet chinh xac cac trang thai bat dau hop le de thiet ke pre-condition cho test case. Neu precondition sai -> test case fail vi ly do sai. | **Open — can BA confirm va update states.md** |
| I-N2 | Minor | UNCLEAR_INFO | uc-user-redeem.md §3 step 9 | UC step 9 chi nhu "retries up to 3 times on reject/timeout" nhung khong noi ro: (a) Retry strategy: trong cung Worker invocation hay re-queue message? (b) Co backoff delay giua cac retry khong? Tester can biet de simulate HL partial failure. | Anh huong test case retry behavior va timing, nhung khong block happy path design. | **Open — Minor, thong tin phu tro** |

### Issues da duoc giai quyet (tu v1 -> v2)

| ID (v1) | Mo ta van de goc | Trang thai giai quyet | Nguon giai quyet |
|---|---|---|---|
| I-01 | FR-EXBOT-071 khong ton tai trong frd.md | Resolved — FR-071 la loi citation tu uc-bot-safe-close. UC §7 FR Trace da cap nhat chi con FR-EXBOT-070. | @hienduong 2026-07-03, uc-user-redeem.md §7 |
| I-04 | Close_operations initial state bat nhat giua UC va states.md | Resolved — Initial state = `requested`. UC step 7 da expand thanh 3 buoc ro rang: requested -> lp_closed -> funds_returned. | @hienduong 2026-07-03 |
| I-05 | Admin notification A2 khong co message code | Resolved — E-EXBOT-024 da dang ky: "User redemption hedge close failed. Manual intervention required." | @hienduong 2026-07-03, message-list.md |
| I-06 | bots.lifecycle_state sau A2 chua duoc dinh nghia | Resolved — A2: `bots.lifecycle_state='error'`, `bots.status='error'`. UC §5 da cap nhat. | @hienduong 2026-07-03 |
| I-07 | Lock contention behavior khong duoc document | Merged vao I-03 — chi tiet duoi AWS arc pending Tech Lead. | Merged |
| I-08 | Reconcile failure behavior khong duoc dinh nghia | Resolved — Reconcile failure = A2 path (residual_hl_liability). SAFE_MODE khong ap dung. UC A2 da expand. | @hienduong 2026-07-03 |
| I-09 | Duplicate Postconditions section | Resolved — phan du da xoa. §5 gio la nguon duy nhat. | @hienduong 2026-07-03 |
| I-10 | flows.md F-05 outdated | Acknowledged — se duoc viet lai trong AWS arc migration pass. Khong anh huong UC nay. | @hienduong 2026-07-03 |
| I-11 | Retry count cho closeShortReduceOnlyIoc chua duoc dinh nghia | Resolved — 3 retries, thong nhat voi bot_safe_close. UC step 9 va A2 da cap nhat. | @hienduong 2026-07-03 |
| I-12 | Queue name ambiguous | Deferred — resolve duoc tu frd.md FR-EXBOT-010 ma khong can BA. | frd.md FR-EXBOT-010 |

### 10.2 Dependency can theo doi

| Dependency | Loai | Anh huong | Owner | Trang thai |
|---|---|---|---|---|
| HL-portion USDC transfer mechanism (AWS arc) | AWS arc migration | Tester can biet mechanism transfer duoi AWS de thiet ke test case cho buoc 13 | Tech Lead | Pending (I-02) |
| Postgres advisory lock behavior (AWS arc) | AWS arc migration | Tester can biet re-queue vs fail behavior khi lock contention | Tech Lead | Pending (I-03) |
| Preconditions for redeem from non-active states | UC clarification | states.md can duoc cap nhat de confirm cac trang thai bat dau hop le (I-N1) | BA | Open |
| BnzaExVault ABI + `RedemptionEvent` schema | Integration | Tester can ABI de verify on-chain event params (`botId`, `redeemTxHash`, `userAddress`) | zen / BA | Open |
| residual_hl_liability recovery flow | UC dependency | Neu bot roi vao `residual_hl_liability`, luong admin xu ly tiep theo chua duoc document | BA | Open |

---

## 11. Change log

| Version | Ngay | Nguoi cap nhat | Noi dung thay doi |
|---|---|---|---|
| v1 | 2026-07-01 | QC UC Read ExBot Agent | Tao bao cao audited lan dau — SRS-first cross-check |
| v2 | 2026-07-03 | QC UC Read ExBot Agent | Re-audit sau BA responses 2026-07-03: giai quyet I-01 (Blocker), I-04, I-05, I-06, I-08, I-09, I-10, I-11; carry forward I-02/I-03 (AWS arc pending Tech Lead); them I-N1 (precondition mo rong chua co trong states.md); cap nhat scoring tu 67/100 (Not Ready) len 81/100 (Conditionally Ready) |

---

## §F.1 — Inventory (v2)

| # | Function / Operation | Trigger | Input | Output | Data Object / Field | Type | Enum / Valid Values | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | On-chain LP liquidation | `BnzaExVault.redeem(tokenId)` goi boi Investor | `tokenId` (uint256) | LP position thanh ly, LP-portion USDC tra ve vi investor ngay trong cung tx, `RedemptionEvent` emit | BnzaExVault (on-chain), LP NFT | on-chain | — | uc-user-redeem.md §3 step 1-3, FR-EXBOT-070(A) |
| 2 | Event detection & enqueue | `RedemptionEvent(botId, redeemTxHash, userAddress)` emit on-chain | botId, redeemTxHash, userAddress | Message enqueue trong `user_redeem` queue (priority cao nhat) | queue message | queue | — | flows.md F-04, frd.md FR-EXBOT-010 |
| 3 | queue_idempotency insert | Worker dequeue message | message_id | Bang ghi insert; UNIQUE conflict -> A3 skip | `queue_idempotency.message_id` (UNIQUE), `queue_idempotency.state` | TEXT | `state`: `started` -> `succeeded` | uc-user-redeem.md §3 step 6, FR-EXBOT-010 |
| 4 | Bot status check | Worker truoc khi xu ly | bots.lifecycle_state | Proceed hoac E-EXBOT-012 (409) | `bots.lifecycle_state`, `bots.status` | TEXT | Hop le: khong phai `closing`/`closed`; Invalid: `closed` -> E-EXBOT-012 | states.md, message-list.md |
| 5 | close_operations record creation — 3 transitions | Worker sau bot check | botId, redeemTxHash, userAddress | `close_operations` row voi 3 state transitions: requested -> lp_closed -> funds_returned | `close_operations.id`, `kind`, `state`, `idempotency_key`, `bot_id`, `created_at` | TEXT | `kind`: `user_redeem`; `state` initial: `requested` -> `lp_closed` -> `funds_returned` | uc-user-redeem.md §3 step 7, erd.md, states.md, I-04 Answered |
| 6 | UserLockDO / advisory lock acquire | Worker truoc HL mutations | userId, ttl=90s (hoac equivalent trong AWS arc) | Lock acquired | Lock mechanism (UserLockDO hoac Postgres advisory lock) | external | acquired: true/false | uc-user-redeem.md §3 step 8, FR-EXBOT-026, I-03 |
| 7 | HL short position full close | Worker sau lock acquire | botId, cloid (deterministic per FR-EXBOT-022), retry cap=3 | HL short position dong; `close_operations.state` -> `hedge_closed` sau reconcile | HL position (external), `close_operations.state` | external + TEXT | — | uc-user-redeem.md §3 step 9, flows.md F-04 |
| 8 | Stop order cancel | Worker sau hedge close (concurrently per UC) | cloid, size=0 | Existing stop order cancel via `replaceStopProtected(size=0)` INV-STOP protocol | `hedge_legs.stop_order_id`, `stop_cloid`, `stop_price`, `stop_size` | TEXT | — | uc-user-redeem.md §3 step 10, FR-EXBOT-032 |
| 9 | Post-close reconcile | Sau HL close order | botId | HL position verified = 0; neu != 0 -> A2 | HL `clearinghouseState` (external) | external | actualSize = 0 expected | flows.md F-04, I-08 Answered |
| 10 | hedge_closed state update | Sau reconcile success | botId | `close_operations.state='hedge_closed'` | `close_operations.state` | TEXT | `hedge_closed` | uc-user-redeem.md §3 step 12 |
| 11 | HL-portion USDC transfer | Sau reconcile confirms close | botId, userAddress, amount | HL-portion USDC gui ve investor qua RedemptionQueue ledger | `close_operations.usdc_amount` | TEXT (BigDecimal string) | — | uc-user-redeem.md §3 step 13, erd.md, I-02 (pending) |
| 12 | Bot close finalization | Sau HL-portion transfer | botId | `close_operations.state='done'`; `bots.lifecycle_state='closed'`; `bots.status='closed'`; `queue_idempotency.state='succeeded'` | `close_operations.state`, `bots.lifecycle_state`, `bots.status` | TEXT | `state`: `done`; `lifecycle_state`: `closed` | uc-user-redeem.md §3 step 14-15, states.md |
| 13 | SLA monitoring | Lien tuc tu event detection | SLA timer (5 phut) | Admin alert E-EXBOT-010 neu >= 5 phut troi qua | — (admin notification queue) | — | threshold: 300s | NFR-EXBOT-003, message-list.md E-EXBOT-010 |
| 14 | Hedge close failure handling (A2) — gom ca reconcile mismatch | HL close attempt het 3 retries HOAC reconcile != 0 | botId, failure reason | `close_operations.state='residual_hl_liability'`; `bots.lifecycle_state='error'`; admin notification E-EXBOT-024 | `close_operations.state`, `close_operations.residual_amount`, `bots.lifecycle_state`, `bots.status` | TEXT | `state`: `residual_hl_liability`; `lifecycle_state`: `error` | uc-user-redeem.md §4 A2, BR-EXBOT-006, I-06/I-08 Answered |
| 15 | Duplicate message detection (A3) | Worker nhan message da xu ly | message_id | Skip processing; return early | `queue_idempotency.message_id` (UNIQUE), `close_operations.idempotency_key` (UNIQUE) | TEXT | — | uc-user-redeem.md §4 A3 |
| 16 | close_operations state machine | close_operations lifecycle | Current state | Next state per transition | `close_operations.state` | TEXT | `requested` -> `lp_closed` -> `funds_returned` -> `hedge_close_pending` -> `hedge_closed` -> `done`; OR `hedge_close_pending` -> `residual_hl_liability` | states.md, I-04 Answered |
| 17 | bots lifecycle transition during close | Close operation initiated | bots.lifecycle_state | `active`/`paused`/`safe_mode` -> `lp_closing` -> `closed` (happy); -> `error` (A2) | `bots.lifecycle_state`, `bots.status` | TEXT | `lp_closing`: light-check/hedge-sync skipped | states.md, uc-user-redeem.md §2/§5 |

---

## §F.2 — Data Object / State Attributes, Business Rules, Validations (v2)

| # | Item | States / Lifecycle | Preconditions | Validation / Business Rule | Dependencies | Resolved Messages | Source |
|---|---|---|---|---|---|---|---|
| 1 | `close_operations` | `requested -> lp_closed -> funds_returned -> hedge_close_pending -> hedge_closed -> done` (happy); `hedge_close_pending -> residual_hl_liability` (A2 — ca reconcile mismatch) | Bot must be valid (non-closed); `idempotency_key` must be unique | `idempotency_key UNIQUE` — duplicate insert -> skip. `kind` in {`user_redeem`, `bot_safe_close`} | `bots.bot_id` FK | — | erd.md, states.md, I-04 Answered |
| 2 | `bots.lifecycle_state` during close | `active`/`paused`/`safe_mode` -> `lp_closing`; `lp_closing` -> `closed` (happy); `lp_closing` -> `error` (A2) | — | Khi `lp_closing`: light-check skip; hedge-sync skip | `bots.status` coarse field | — | states.md, uc-user-redeem.md §2 v2 |
| 3 | BR-EXBOT-006 — LP-portion bat dieu kien | Ap dung moi luc trong user_redeem | LP-portion da tra on-chain (cung tx, khong the dao nguoc) | Hedge close failure KHONG duoc block hoac dao nguoc LP-portion | BnzaExVault (on-chain tx is irreversible) | — | common-rules.md BR-EXBOT-006 |
| 4 | SLA 5 phut (NFR-EXBOT-003) | Tu event detection den hedge close completion | Event detection timestamp phai duoc ghi lai | <= 5 phut; vi pham -> E-EXBOT-010 admin alert only (khong abort) | E-EXBOT-010 | "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | NFR-EXBOT-003, message-list.md E-EXBOT-010 |
| 5 | INV-STOP protocol (stop cancel) | Trong close operation | Existing stop order phai ton tai tren HL | `replaceStopProtected(size=0)` la CACH DUY NHAT cho phep stop cancel | `hedge_legs.stop_cloid`, `stop_order_id` | — | FR-EXBOT-032 |
| 6 | Full close exception | Trong user_redeem | Bot co active HL short position | `closeShortReduceOnlyIoc` full close duoc phep cho bot close path (FR-EXBOT-022 exception #1) | — | — | FR-EXBOT-022 |
| 7 | queue_idempotency | Message processing start | message_id available | Insert `message_id` at start; UNIQUE conflict -> return immediately | `queue_idempotency.message_id` UNIQUE INDEX | — | FR-EXBOT-010 |
| 8 | `close_operations.residual_amount` (A2) | Set on hedge close failure hoac reconcile mismatch | A2 path triggered (3 retries het hoac reconcile != 0) | Outstanding HL liability amount luu vao field nay | `close_operations.residual_amount` TEXT (BigDecimal) | Admin: E-EXBOT-024: "User redemption hedge close failed. Manual intervention required." | erd.md, I-05/I-06/I-08 Answered |
| 9 | Deterministic cloid | Moi HL hedge mutation | botId, attemptId, stage, version | `first128BitsHex(keccak256("bnza:{botId}:{attemptId}:{stage}:{version}"))` | retry dung cung cloid (same params) | — | FR-EXBOT-022, I-11-A Answered |

---

## §F.3 — Functional Logic & Workflow Decomposition (v2)

| Function | Path | Trigger | Input | Output | Actor/Permission | System Response | Source |
|---|---|---|---|---|---|---|---|
| User-initiated redeem | Happy path | `BnzaExVault.redeem(tokenId)` on-chain | tokenId (investor-owned) | LP-portion USDC tra on-chain ngay; close_operations tao (3 transitions); hedge dong <= 5 phut; HL-portion gui; bot dong | ACT-I on-chain; ACT-O Worker off-chain | `close_operations.state='done'`; `bots.lifecycle_state='closed'` | uc-user-redeem.md §3, flows.md F-04 |
| User-initiated redeem | SLA breach (A1) | Hedge close khong hoan tat trong 5 phut | SLA timer expiry | Admin alert E-EXBOT-010 gui; hedge close tiep tuc | ACT-O (system), ACT-A (nhan alert) | E-EXBOT-010: "Hedge close for redemption exceeded 5-minute SLA. Escalated to admin. LP funds already returned." | uc-user-redeem.md §4 A1, NFR-EXBOT-003 |
| User-initiated redeem | Hedge close failure hoac reconcile mismatch (A2) | HL close het 3 retries HOAC reconcile xac nhan vi the != 0 | Hedge close error hoac reconcile mismatch | `residual_hl_liability` state; admin E-EXBOT-024; LP-portion KHONG bi dao nguoc; `bots.lifecycle_state='error'`; SAFE_MODE KHONG ap dung | ACT-O (system), ACT-A (nhan alert) | `close_operations.state='residual_hl_liability'`; `close_operations.residual_amount` set; E-EXBOT-024 gui | uc-user-redeem.md §4 A2, BR-EXBOT-006, I-06/I-08 Answered |
| User-initiated redeem | Duplicate message (A3) | Queue redeliver already-processed message | Same message_id | Khong co action; Worker thoat som | ACT-O (system) | Return early; khong co HL mutation; khong co state change | uc-user-redeem.md §4 A3 |
| Already-closed bot detection | Exception | Worker nhan redeem cho bot da dong | bots.lifecycle_state = 'closed' | E-EXBOT-012 (409) | ACT-O (system) | "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |

---

## §F.4 — Functional Integration & Data Consistency (v2)

| Trigger | Cross-function Effect | On-chain / Off-chain Consistency | Data Verification | Source |
|---|---|---|---|---|
| `BnzaExVault.redeem(tokenId)` on-chain | LP thanh ly on-chain; LP-portion USDC tai dia chi investor; `RedemptionEvent` emit -> event watcher -> queue | On-chain la source of truth cho LP liquidation. Off-chain `close_operations` tao SAU khi event duoc detect. Gap: neu event watcher bo lo event, off-chain khong bao gio bat kip. | Verify: `close_operations` duoc tao match `redeemTxHash`; LP-portion amount match on-chain tx | uc-user-redeem.md §3, flows.md F-04 |
| `close_operations` tao voi state='requested' | `bots.lifecycle_state` chuyen sang `lp_closing` -> light-check skip -> hedge-sync bi suppress | Ca `close_operations` va `bots.lifecycle_state` phai nhat quan. Neu `lifecycle_state` khong duoc update atomic voi `close_operations` creation, race condition co the xay ra. | Verify: sau `close_operations` insert, `bots.lifecycle_state='lp_closing'` trong cung transaction | states.md, erd.md |
| HL short `closeShortReduceOnlyIoc` (3 retries) | `close_operations.state` -> `hedge_closed` (sau reconcile); stop order cancel; HL position = 0 | HL la source of truth cho position. Reconcile failure (vi the != 0) = A2 path (residual_hl_liability), KHONG phai SAFE_MODE. | Verify: sau reconcile, HL `clearinghouseState.size = 0`; `hedge_legs.stop_order_id` cleared | flows.md F-04, I-08 Answered |
| HL-portion USDC transfer qua RedemptionQueue | `close_operations.state` -> `done`; `bots.lifecycle_state` -> `closed`; `bots.status` -> `closed`; `queue_idempotency.state` -> `succeeded` | USDC transfer la su kien off-chain cuoi. Khong duoc xu ly hai lan. | Verify: `close_operations.usdc_amount` populated; `close_operations.state = 'done'`; khong co duplicate transfer khi redelivery | uc-user-redeem.md §3 step 13-15, erd.md |
| `residual_hl_liability` (A2 — gom ca reconcile mismatch) | LP-portion da gui; HL-portion CHUA gui; admin duoc thong bao E-EXBOT-024; `bots.lifecycle_state='error'` | On-chain: LP-portion khong the dao nguoc. Off-chain: `close_operations.state='residual_hl_liability'` bieu hieu pending manual resolution. | Verify: `close_operations.residual_amount` = expected outstanding HL liability; E-EXBOT-024 admin notification da duoc enqueue; `bots.lifecycle_state='error'` | uc-user-redeem.md §4 A2 §5, erd.md, I-06/I-08 Answered |

---

## §F.5 — AC Candidates (v2)

| AC # | Scenario | Given | When | Then | Source / Note |
|---|---|---|---|---|---|
| AC-F5-01 | Happy path hedge close | Bot active; investor so huu tokenId; HL short open; stop order placed | Investor calls `redeem(tokenId)` | LP-portion USDC trong vi investor (cung tx); `close_operations.state='done'` trong <= 5 phut; `bots.lifecycle_state='closed'`; HL position=0; stop da cancel | us-004.md AC-004-1 |
| AC-F5-02 | SLA breach alert | Bot active; HL close > 5 phut | Hedge close delay vuot 5 phut | E-EXBOT-010 admin alert gui; hedge close tiep tuc sau alert; LP-portion KHONG bi dao nguoc | us-004.md AC-004-2 |
| AC-F5-03 | Hedge close fails HOAC reconcile mismatch, LP da tra | Bot active; LP-portion tra on-chain | HL close Worker het 3 retries HOAC reconcile xac nhan vi the != 0 | `close_operations.state='residual_hl_liability'`; `residual_amount` set; `bots.lifecycle_state='error'`; LP-portion KHONG bi dao nguoc; admin nhan E-EXBOT-024 | us-004.md AC-004-3, BR-EXBOT-006, I-08 Answered |
| AC-F5-04 | Duplicate queue delivery | close_operations voi idempotency_key da ton tai | Worker nhan cung user_redeem message lan nua | Khong co HL mutation them; khong co duplicate `close_operations` row; Worker thoat gracefully | uc-user-redeem.md §4 A3 |
| AC-F5-05 | Redeem tren bot da dong | bots.lifecycle_state='closed' | Worker xu ly user_redeem message | E-EXBOT-012 (409): "Bot is already closed. No action needed." | message-list.md E-EXBOT-012 |
| AC-F5-06 | light-check suppressed khi lp_closing | close_operations tao; bots.lifecycle_state='lp_closing' | Light-check worker evaluate bot nay | Worker skip bot hoan toan; khong co hedge-sync enqueue | states.md |
| AC-F5-07 | INV-STOP: stop cancel qua replaceStopProtected | Active stop order ton tai tren HL | Worker call cancel trong close flow | Stop cancel qua size=0 replace; `hedge_legs.stop_order_id` cleared; khong co naked stop removal | FR-EXBOT-032 |
| AC-F5-08 | Redeem tu trang thai paused | Bot dang paused | Investor goi `redeem(tokenId)` | Luong user_redeem chay binh thuong; bot chuyen sang `closed` | uc-user-redeem.md §2 v2 — xem I-N1 de xac nhan |
| AC-F5-09 | Deterministic cloid cho hedge close retry | HL reject lan dau; Worker retry | Worker retry closeShortReduceOnlyIoc (lan 2, 3) | Same cloid duoc dung (same attemptId+stage+version); HL dedup hoac detect duplicate | FR-EXBOT-022, I-11-A Answered |

---

## Tong quan danh gia va diem (v2)

### Scoring Summary (v2 vs v1)

| Scoring Area | Max | v1 Score | v2 Score | Delta | Rationale |
|---|---|---|---|---|---|
| 1. Function / Operation & Data Object Inventory | 20 | 15 | 17 | +2 | I-04 resolved (initial state ro rang, 3 transitions duoc mo ta day du); I-11 resolved (retry count + cloid formula); I-02 van open nhung chi anh huong buoc 13 |
| 2. Data Object / State Attributes, Business Rules, Validations | 25 | 17 | 21 | +4 | I-05 (E-EXBOT-024), I-06 (A2 lifecycle='error'), I-08 (reconcile failure = A2 path, SAFE_MODE khong ap dung) da duoc giai quyet va doc vao spec |
| 3. Functional Logic & Workflow Decomposition | 25 | 16 | 19 | +3 | A2 path mo rong (gom reconcile mismatch); A2 postconditions ro rang; retry count = 3 document; I-03 van partial (AWS arc lock behavior) |
| 4. Functional Integration & Data Consistency | 15 | 11 | 12 | +1 | I-10 acknowledged (F-05 outdated); I-02 van blocking HL-portion transfer verification; data consistency rules update voi reconcile failure path |
| 5. UC / Spec Documentation Quality Issues | 15 | 8 | 12 | +4 | I-01 Blocker da resolved (khong con auto-fail); I-09 resolved (duplicate Postconditions xoa); I-12 Deferred; I-N1 la issue moi Minor/Medium |
| **Tong diem** | **100** | **67/100** | **81/100** | **+14** | |

> **Auto-cap da xoa:** I-01 (Blocker) da resolved — khong con auto-cap. Khong co Blocker nao con ton tai.
> **Open issues anh huong score:** I-02 (High, AWS arc pending) -> Area 1/3/4 bi giu lai (~-3 pts tong); I-03 (Medium, AWS arc pending) -> Area 3 bi giu lai (~-2 pts); I-N1 (Medium, states.md chua cap nhat) -> Area 5 giu lai (~-2 pts).

### §10.3 Audit Summary (v2)

**Verdict: Conditionally Ready (Score: 81/100)**

UC-EXBOT-user-redeem sau khi duoc BA cap nhat ngay 2026-07-03 da giai quyet toan bo cac van de Blocker va High tu v1:

- **I-01 (Blocker) RESOLVED**: FR-EXBOT-071 la loi citation; UC §7 chi con FR-EXBOT-070 — FR Trace chinh xac.
- **I-04 RESOLVED**: Initial state `close_operations` = `requested`; UC step 7 da mo ta day du 3 transitions (requested -> lp_closed -> funds_returned) nhat quan voi states.md.
- **I-05 RESOLVED**: E-EXBOT-024 "User redemption hedge close failed. Manual intervention required." da duoc dang ky va UC A2 da cite dung.
- **I-06 RESOLVED**: A2 postconditions: `bots.lifecycle_state='error'`, `bots.status='error'` da ro rang.
- **I-08 RESOLVED**: Reconcile failure = A2 path (residual_hl_liability), SAFE_MODE khong ap dung vi LP da thanh ly.
- **I-11 RESOLVED**: Retry count = 3, thong nhat voi bot_safe_close.

Hai van de con lai (I-02, I-03) thuoc nhom "Outdated vs AWS arc" — dang cho Tech Lead confirm mechanism HL-portion transfer va advisory lock behavior duoi kien truc AWS moi. Cac van de nay khong block happy path test design (tester co the thiet ke test case cho main flow, SLA breach, A2 failure, A3 duplicate). Tuy nhien, test case expected result cho buoc 13 (HL-portion transfer amount) va test case lock contention behavior se can duoc supplement khi Tech Lead tra loi.

Issue I-N1 la thong tin moi: UC §2 v2 mo rong precondition ("user may redeem from any non-closed state") nhung states.md chua duoc cap nhat de phan anh dieu nay. Ba ask BA update states.md hoac xac nhan chinh thuc danh sach cac trang thai duoc phep khoi tao redeem.

**Khuyen nghi:** Tester co the tien hanh thiet ke test scenario va test case cho cac luong sau:
1. **Co the thiet ke ngay:** Happy path, SLA breach (A1), Hedge close failure (A2 — ca 3 retries va reconcile mismatch), Duplicate delivery (A3), Already-closed bot.
2. **Can cho Tech Lead (I-02, I-03):** Test case verify HL-portion amount chinh xac; test case lock contention behavior.
3. **Can BA confirm (I-N1):** Test case redeem tu trang thai `paused`/`safe_mode`/`hedge_stopped_cooldown`/etc.

