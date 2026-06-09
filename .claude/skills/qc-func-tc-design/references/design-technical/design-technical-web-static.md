# Design Technical — Web Static (Non-Responsive)

## When to use this rubric

Load this file when `project-context-master.md` §1 → "Product Platform Type" contains `web-static`.

Applies to: Web applications designed for desktop/laptop only (fixed-width layout, no mobile/tablet adaptation). Typical for internal back-office tools, admin panels, ERP screens with dense data tables.

## 6-Phase Drafting Rubric

### Phase 1: Screen Initialization (Static States)

- **Empty State (No Data)** — placeholder, empty-state illustration, "No Data" / "Chưa có dữ liệu" messaging on grids, lists, charts.
- **Populated State (With Data)** — default sort, default page size, default filter, column visibility defaults.
- **Loading State** — skeleton row / spinner overlay while grid fetches; long-running jobs show progress bar.
- **Error State** — 4xx / 5xx / network: inline error in panel + Retry; do NOT navigate away on transient error.

### Phase 2: Item Interactions (Component States)

- **Navigation & Reset** — 'X' icons, 'Cancel', 'Close', 'Reset filter' restore defaults.
- **Screen Initialization Triggers** — Buttons open correct sub-panel / popup / drawer.
- **Component Verification** —
  - Dropdowns / Multi-select / Combobox with search: Clickability, search-as-you-type, virtualized long list.
  - Textboxes / Buttons: states (Clickable, Disabled, Read-only) per business rules.
  - Data grid: column resize, column reorder, column hide/show, frozen columns, row selection (single / multi / all).
  - Date / DateTime pickers: keyboard input + calendar pick.
- **Navigation Tools** — Pagination (Active page, Next/Prev, jump-to-page, page-size selector).
- **Keyboard shortcuts** — Tab order, Enter to submit, Esc to close, Ctrl+S save (if spec), arrow keys in grid.

### Phase 3: Core Functional Testing (Logic Analysis)

- **Happy Path** — Standard CRUD + workflow flow with valid inputs.
- **Validation** —
  - Required, Format, Range, Length, BVA.
  - Cross-field validation (e.g., end-date ≥ start-date).
  - Decision-table-driven business rules (combinations of role × status × action).
- **Exception / Error Handling** — Server validation echoed inline, optimistic locking conflict, concurrent edit detection.
- **Bulk operations** — Bulk delete, bulk export, bulk approve: partial-success handling.

### Phase 4: Functional Integration

- Filter + sort + pagination + column-config composition.
- Master-detail screens: select a row → detail panel updates without page reload.
- Cross-screen navigation preserves filter/search state on back-navigation.
- Multi-tab / multi-window same-record edit conflict.

### Phase 5: UI-Level Non-Functional Testing

- **Security** — Field-level masking (SSN, salary), SQL Injection / XSS sanitization, CSRF on POST/PUT/DELETE, role-based field visibility, audit log entry on sensitive actions.
- **Performance** — Grid renders < 1s with X rows; virtualized scrolling for ≥ 1000 rows; export-to-Excel of N rows completes within target.
- **UX / Loading** — Spinner on AJAX, button debounce, unsaved-changes warning on navigation.
- **Browser back / forward / refresh** — Form state preserved or explicit warning; URL deep-link to specific record works.
- **Print view** — Print stylesheet renders cleanly (if spec has printable reports).

### Phase 6: GUI & Visual Compliance

- **Design Alignment** — Position, color (HEX), spacing, font-size, line-height match Figma / mockup at the declared min resolution.
- **Min screen resolution** — Verify at the project's declared minimum (commonly 1366×768 or 1280×720). Below min → may show "screen too small" warning OR allow horizontal scroll per spec.
- **Browser compatibility matrix** — Per project spec (often latest-2 Chrome/Edge for back-office).
- **Localization** — Vietnamese diacritics render correctly; long labels don't truncate critical info.
- **Accessibility basics** — Color contrast ≥ WCAG AA, semantic HTML, form labels, keyboard navigation.

> **Out of scope for this rubric:** mobile / tablet viewport rendering, touch gestures, hamburger nav. If the product later adds responsive support, switch to `design-technical-web-responsive.md`.
