---
source_skill: qc-site-map
handoff_type: site-map-feature-coverage
mode: initialization
generated_at: 2026-05-15T00:00:00+07:00
---

# Site Map Handoff for Dashboard

Site map vừa được tạo lần đầu (`docs/qc-lead/qc-site-map.md`). Handoff này chỉ chứa thông tin cấp **feature/UC** để `qc-dashboard-sync` cross-check/cập nhật note nếu cần. **Không** đề xuất ghi đè vào cột `Files stt`, `UC review stt`, `Scenario design stt`, `TC design stt`, `Execute stt`.

## Feature-level site map coverage

| Feature ID | Feature name | Site / Portal | Module | Mapped screen(s) | Folder alias(es) | In scope? | Site map status | Notes |
|---|---|---|---|---|---|---|---|---|
| UC1 | Trang chủ Dashboard | Mobile | B. Trang chủ & Điều hướng | SCR-020, 021, 022, 023 | — | Yes | Mapped | Sidebar (SCR-022) = Confirmed; còn lại Derived |
| UC2 | Tra cứu KCN/KKT/TMTD/PTQ/Mô hình (UC2-UC31) | Mobile | D. Tra cứu KCN/KKT | SCR-040..047 | — | Yes | Partial | SCR-047 (tab Hạ tầng/Nhà đầu tư) chờ BA — AI-UC-02 |
| UC40 | Tra cứu quỹ đất KCN | Mobile | D. Tra cứu KCN/KKT | SCR-048, 049 | — | Yes | Mapped | NV-06 trạng thái; KT-04 không export |
| UC42-44 | Quản lý đặt lịch | Mobile | C. Hồ sơ & Dịch vụ | SCR-030, 031 | — | Yes | Mapped | NV-01/02 no tạo/huỷ; SCR-031 detail Need confirm |
| UC45-51 | Quản lý hồ sơ | Mobile | C. Hồ sơ & Dịch vụ | SCR-032, 033 | — | Yes | Mapped | UX-05 search + tab; KT-06 PDF in-app |
| UC52 | Kho tài liệu cá nhân | Mobile | C. Hồ sơ & Dịch vụ | SCR-034, 035 | — | Yes | Mapped | NV-04 read-only; KT-07 |
| UC53_63-65 | Phản ánh kiến nghị | Mobile | C. Hồ sơ & Dịch vụ | SCR-036, 037, 038 | — | Yes | Mapped | UX-06 state; UX-07 auto-fill |
| UC54 | Báo cáo đã nộp | Mobile | C. Hồ sơ & Dịch vụ | SCR-039 | — | Yes | Mapped | NV-05 |
| UC55 | Tin tức / Chuyên trang đầu tư | Mobile | E. Tin tức / Hỗ trợ | SCR-064, 065, 066 | — | Yes | Partial | SCR-066 form đăng ký tư vấn — AI-UC55-01 chờ KH |
| UC56-57_66_68 | Tin tức (UC56-57, UC66, UC68) | Mobile | E. Tin tức / Hỗ trợ | SCR-060, 061, 062 | — | Yes | Mapped | KT-09 WebView |
| UC58 | Tin tức UC58 | Mobile | E. Tin tức / Hỗ trợ | SCR-060/061/062 (gom hub) | — | Need confirm | Need confirm | Q-013: gom row chưa khớp 1-1 |
| UC59 | Tin tức UC59 | Mobile | E. Tin tức / Hỗ trợ | SCR-060/061/062 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC60-61 | Tin tức UC60-61 | Mobile | E. Tin tức / Hỗ trợ | SCR-060, 061, 062 | — | Yes | Mapped | |
| UC62 | Tin tức UC62 | Mobile | E. Tin tức / Hỗ trợ | SCR-060/061/062 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC67 | Tin tức UC67 | Mobile | E. Tin tức / Hỗ trợ | SCR-060/061/062 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC69 | Văn bản pháp luật | Mobile | E. Tin tức / Hỗ trợ | SCR-067, 068 | — | Yes | Mapped | KT-09 |
| UC71-82 | Hướng dẫn & FAQ | Mobile | E. Tin tức / Hỗ trợ | SCR-075 | — | Yes | Mapped | UX-11 multi-expand |
| UC73 | Tra cứu TTHC | Mobile | E. Tin tức / Hỗ trợ | SCR-069, 070 | — | Need confirm | **Conflict** | UC73 vs UC70 Removed (Q-014) — cần BA + QC Lead xác nhận |
| UC83-86 | Điều khoản / Chính sách / Liên hệ / Giới thiệu | Mobile | E. Tin tức / Hỗ trợ | SCR-076, 077, 078, 079 | — | Yes | Mapped | KT-12/13 Liên hệ external; NV-10 Giới thiệu chờ BA |
| UC87 | Xúc tiến UC87 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC88 | Xúc tiến UC88 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC89 | Xúc tiến UC89 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC90 | Xúc tiến UC90 | Mobile | E. Tin tức / Hỗ trợ | SCR-071, 072, 073 | — | Yes | Mapped | KT-15 lazy 20 |
| UC91 | Xúc tiến UC91 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC92 | Xúc tiến UC92 (login required) | Mobile | E. Tin tức / Hỗ trợ | SCR-074 | — | Yes | Mapped | PQ-07 exception — high regression |
| UC93 | Xúc tiến UC93 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC94 | Xúc tiến UC94 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC95 | Xúc tiến UC95 | Mobile | E. Tin tức / Hỗ trợ | SCR-071/072/073 (gom hub) | — | Need confirm | Need confirm | Q-013 |
| UC249 | Cấu hình & QL TK | Mobile | A. Xác thực & QL TK | SCR-010, 011, 013 | — | Yes | Mapped | BS-07 invalidation; UX-12 no Avatar |
| UC250-254 | Đăng ký / Quên MK / Cập nhật DN | Mobile | A. Xác thực & QL TK | SCR-004..009, 012 | — | Yes | Mapped | BS-09/10/11; UX-13/14 |
| UC256 | Đăng nhập Mobile | Mobile | A. Xác thực & QL TK | SCR-001, 002, 003 | — | Yes | Mapped | BS-01 VNeID dependency |
| UC257 | Đăng xuất Mobile | Mobile | A. Xác thực & QL TK | SCR-014 | — | Yes | Mapped | BS-05 |
| UC258_UC259 | Thông báo hệ thống | Mobile | F. Thông báo | SCR-080, 081, 082 | — | Yes | Mapped | NV-09 chờ BA; KT-16/17/18 |

## Feature-level gaps

| Feature ID | Feature name | Gap | Impact to QC | Owner | Priority |
|---|---|---|---|---|---|
| UC2 | Chi tiết KCN — tab Hạ tầng/Nhà đầu tư | Tab structure + KT-03 (bảng/biểu đồ) chưa rõ | Không design được scenario chi tiết tab | BA | High |
| UC55 | Đăng ký tư vấn đầu tư | Form spec / màn đích chưa có | FLOW-CONSULT không design được | KH (qua BA) | High |
| UC73 | Tra cứu TTHC | **Conflict** UC73 vs UC70 Removed | Có thể tạo/bỏ sót màn TTHC | BA + QC Lead | High |
| UC58 / UC59 / UC62 / UC67 | Tin tức UC riêng | Gom hub không có evidence riêng | Coverage tracking sai số | QC Lead + BA | Medium |
| UC87 / UC88 / UC89 / UC91 / UC93 / UC94 / UC95 | Xúc tiến UC riêng | Gom hub không có evidence riêng | Coverage tracking sai số | QC Lead + BA | Medium |
| UC83-86 (UC86) | Giới thiệu | NV-10 tĩnh/CMS chưa rõ | Test offline vs CMS-driven khác nhau | BA | Low |
| UC258_UC259 | Thông báo | NV-09 loại thông báo + deep-link routing | Cold-start mapping cho push chưa có | BA | Medium |
| (cross) | Auth + Token lifecycle | BS-07 đổi MK → bắt buộc logout — regression critical | High regression risk | Tech Lead + QC | High |

## Unmapped screens

| Screen ID | Screen / Page | Why unmapped | Suggested action |
|---|---|---|---|
| SCR-050 | Quản lý cho thuê đất | UC41 chưa có row dashboard (AI-UC-01 chờ BA) | Khi BA hoàn tất UC41 → bổ sung row dashboard `Mobile / UC41 / D / Cho thuê đất KCN / Need confirm`. **KHÔNG** tự thêm row UC41 ngay vì BA chưa cấp content. |
| SCR-090 | Toast messages | Cross-cutting, AI-UX-01 chưa thiết kế | Khi UI/UX team có design → review tích hợp; không tạo row dashboard riêng |
| SCR-091 | Empty — Search NULL | AI-UX-02 chưa thiết kế | Same |
| SCR-092 | Empty — List rỗng | AI-UX-03 chưa thiết kế | Same |
| SCR-093 | Error — Network/500/404/Timeout | AI-UX-04 chưa thiết kế | Same |

## Dashboard update recommendation

`qc-dashboard-sync` **không cần thay đổi cấu trúc dashboard** (cột `Files stt`, `UC review stt`, `Scenario design stt`, `TC design stt`, `Execute stt` không ảnh hưởng bởi site map). Đây chỉ là handoff thông tin cấp feature để cross-check.

| Feature ID | Recommended dashboard note/status | Reason |
|---|---|---|
| UC73 | Cân nhắc đánh `Conflict` hoặc giữ `Need confirm` cho tới khi BA + QC Lead resolve UC73 vs UC70 | Site map: Conflict |
| UC55 | Giữ `Yes` nhưng note "SCR-066 chờ KH (AI-UC55-01)" | Site map: Partial |
| UC2 | Giữ `Yes` nhưng note "SCR-047 chờ BA (AI-UC-02)" | Site map: Partial |
| UC58/59/62/67 | Giữ `Need confirm` (đã đúng) | Site map: Need confirm |
| UC87/88/89/91/93/94/95 | Giữ `Need confirm` (đã đúng) | Site map: Need confirm |
| UC41 (chưa có row) | **KHÔNG** auto-add. Đợi BA cấp content UC41 (AI-UC-01) | Site map: Unmapped — pending |

**Lưu ý cho QC Lead:** Sau khi BA cung cấp lại folder `docs/BA/<UC-ID>/` (Q-015) — `qc-dashboard-sync` chạy lại sẽ tự cập nhật cột `Files stt` (hiện đang stale toàn bộ `Missing`).
