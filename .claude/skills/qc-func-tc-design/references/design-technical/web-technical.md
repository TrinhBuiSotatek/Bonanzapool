# Web Technical Guideline for Test Case Design

## Purpose

This guideline defines Web-specific technical checks for designing test cases.

Use it together with `common-technical.md`.

This file supports two Web modes:

1. `web-static`: desktop/laptop fixed-width Web application.
2. `web-responsive`: Web application that adapts across desktop, tablet, and mobile breakpoints.

## How to choose the mode

| Mode | Use when | Main testing focus |
|---|---|---|
| `web-static` | The product is designed for desktop/laptop only with fixed-width layout | Data grid, dense admin UI, min resolution, keyboard interaction, pagination, bulk operation |
| `web-responsive` | The product adapts to multiple viewport widths | Breakpoints, layout reflow, touch target, responsive navigation, mobile/tablet rendering |

## Recommended composition

```text
Web Static = Common Technical + Web Base + Static Add-on
Web Responsive = Common Technical + Web Base + Responsive Add-on
```

---

# 1. Web Base Checklist

Apply this section to both `web-static` and `web-responsive`.

## Phase 1: Screen Initialization

In addition to the common checklist, verify:

- Empty grids, tables, lists, cards, dashboards, and charts display the correct message.
- Populated state shows the correct default filter, sort, page size, and selected tab.
- Loading state uses spinner, skeleton row, overlay, or progress indicator as specified.
- Error state is displayed inline when possible and does not navigate the user away unexpectedly.
- Browser refresh behavior follows the spec.
- Direct URL access opens the correct screen or redirects properly when authentication is required.

## Phase 2: Web Component Interaction

### Navigation and page controls

- Breadcrumb navigation.
- Browser back and forward.
- In-page back button.
- Close, Cancel, Reset filter.
- Deep link route and query parameters.

### Forms

- Textbox.
- Text area.
- Password field.
- Number input.
- Date and date-time input.
- Dropdown.
- Combobox.
- Multi-select.
- Checkbox.
- Radio group.
- Toggle.
- File upload.

### Keyboard behavior

- Tab order.
- Shift + Tab order.
- Enter to submit only where expected.
- Esc to close modal or dropdown where expected.
- Focus ring is visible.
- Keyboard-only user can complete the workflow.

### Pagination and list controls

- Current page indicator.
- Previous and Next.
- First and Last if available.
- Jump to page if available.
- Page size selector.
- Empty result after filtering.
- Pagination reset after search or filter if required.

## Phase 3: Web Core Functional Testing

In addition to common functional testing, cover:

- Required field validation.
- Format validation for email, phone, date, URL, code, tax ID, ID number.
- Boundary values for text, number, date, amount, percentage.
- Cross-field validation.
- Server validation displayed inline near the correct field.
- Duplicate submit prevention on double-click or Enter key.
- File upload type, size, extension, cancel, retry, and failed upload.
- Browser autofill and password manager behavior if relevant.

## Phase 4: Web Functional Integration

Cover integration between:

- Search + filter.
- Filter + sort.
- Sort + pagination.
- Search + filter + sort + pagination.
- Create/update/delete + list refresh.
- Detail page + back navigation preserving previous list state.
- Modal form + parent page update.
- Multi-tab same-record edit.
- Auth session expiry + redirect + return path.
- URL query parameters + screen state.

## Phase 5: Web Non-Functional Testing

### Security

- Password and sensitive data masking.
- XSS prevention in input fields, rich text, table cell, toast, tooltip, and URL parameter.
- SQL injection or command injection prevention through UI inputs.
- CSRF token or equivalent protection on state-changing forms.
- Role-based visibility for fields, buttons, tabs, and menu items.
- Direct URL access does not bypass permission.
- Sensitive data is not exposed in URL, browser history, localStorage, sessionStorage, or console log.

### Storage

- Cookie behavior.
- LocalStorage behavior.
- SessionStorage behavior.
- Token or preference persistence.
- Logout clears sensitive local data.
- Remember-me behavior if supported.

### Browser behavior

- Refresh during editing.
- Back/forward during editing.
- Unsaved changes warning.
- Open in new tab.
- Direct paste URL.
- Expired session in existing tab.

### Performance

- Page initial load.
- Time to interactive.
- Table or list rendering.
- Search/filter response time.
- Export/import duration.
- Large dataset behavior.

## Phase 6: Web GUI, Visual, and Accessibility

- Design alignment with Figma/mockup.
- Color, spacing, typography, line height, icon, border, shadow.
- Hover, focus, selected, disabled, loading, error states.
- Browser zoom behavior if required.
- Vietnamese diacritics and long labels.
- Semantic HTML for heading, button, nav, table, form.
- Associated labels for form fields.
- Alt text for meaningful images.
- Color contrast meets WCAG AA where applicable.

---

# 2. Static Web Add-on

Use this section only when platform type is `web-static`.

## Definition

`web-static` means the product is designed for desktop/laptop only, usually with a fixed-width layout. It is common for back-office systems, admin panels, ERP, CRM, reporting tools, and dense data-entry screens.

Mobile and tablet rendering are out of scope unless the project explicitly says otherwise.

## Additional checks

### Screen resolution

- Verify at the declared minimum resolution, commonly `1366x768` or `1280x720`.
- Below minimum resolution, behavior must follow spec:
  - show `screen too small` warning, or
  - allow horizontal scroll, or
  - keep fixed layout with acceptable clipping rules.

### Dense data grid

Cover if the screen includes a table or grid.

- Default column order.
- Default column width.
- Column resize.
- Column reorder.
- Column hide/show.
- Frozen column.
- Sticky header.
- Row selection: single, multi, select all.
- Select all current page.
- Select all matching records across pages if supported.
- Inline edit.
- Cell validation.
- Row expansion.
- Master-detail panel.
- Empty grid.
- Grid loading state.
- Grid error state.

### Admin-style filtering

- Basic filter.
- Advanced filter.
- Multiple filters combined.
- Reset filter.
- Saved filter if supported.
- Date range filter.
- Status filter.
- Search within dropdown or combobox.

### Bulk operation

- Bulk delete.
- Bulk export.
- Bulk approve/reject.
- Bulk assign.
- Bulk import.
- Partial success.
- Permission handling for bulk actions.
- Confirmation dialog.
- Audit log for sensitive bulk action.

### Business rule matrix

Use decision tables for combinations such as:

- Role x status x action.
- Department x permission x data ownership.
- Approval level x amount range x workflow status.

### Print and export

- Print stylesheet.
- Printable report layout.
- Export to Excel/CSV/PDF.
- Export selected records.
- Export all filtered records.
- Large export performance.
- File name and timestamp format.

### Static web out of scope by default

Do not include these unless the project explicitly supports them:

- Mobile viewport rendering.
- Tablet layout.
- Touch gesture.
- Hamburger menu.
- Safe area inset.
- Device orientation.

---

# 3. Responsive Web Add-on

Use this section only when platform type is `web-responsive`.

## Definition

`web-responsive` means the same Web application adapts layout across multiple viewport widths using responsive CSS, Tailwind, Bootstrap, custom breakpoints, or similar techniques.

The full 6-phase checklist must be applied at every declared breakpoint, not only desktop.

## Breakpoint matrix

Use the project-defined breakpoints first. If none are defined, use this baseline matrix:

| Viewport | Example width | Notes |
|---|---:|---|
| Desktop | >= 1280px | Full layout |
| Laptop | 1024px | Reduced horizontal space |
| Tablet | 768px | Touch-friendly layout may begin |
| Mobile | 375px to 414px | Single-column and compact navigation |

## Responsive layout checks

- Layout reflows correctly at each breakpoint.
- No unintended horizontal scroll.
- No clipped content.
- Important actions remain visible or reachable.
- Columns stack correctly.
- Cards, tables, charts, and forms adapt correctly.
- Spacing remains visually balanced.
- Images scale without distortion.
- Sticky headers or footers do not cover content.

## Responsive navigation

- Desktop navigation is displayed correctly.
- Navigation collapses to hamburger, drawer, tab bar, or compact menu at small breakpoints.
- Menu open/close works on touch and keyboard.
- Active menu item remains clear.
- Nested menu behavior is usable on mobile.
- Backdrop and scroll lock work when drawer is open.

## Responsive forms

- Labels and inputs align correctly at each breakpoint.
- Multi-column forms collapse into one column where required.
- Error messages do not break layout.
- Required markers remain visible.
- Keyboard focus order follows visual order.
- Submit action remains reachable on mobile.

## Responsive tables and lists

Choose behavior based on spec:

- Table scrolls horizontally.
- Table converts to cards.
- Columns are hidden by priority.
- Summary view is shown on mobile.
- User can still access full row details.
- Sort/filter controls remain usable.

## Touch breakpoint checks

- Tap target is at least 44px where touch is expected.
- Hover-only behavior has a touch alternative.
- Tooltips are accessible on touch devices.
- Dropdowns, date pickers, and menus are usable with touch.
- No interaction depends only on mouse hover.

## Mobile browser behavior

- Address bar show/hide does not break layout.
- Virtual keyboard does not hide focused input.
- Viewport height issues are handled.
- Sticky footer does not overlap form fields.
- Pull-to-refresh conflict is acceptable or prevented by design.

## Localization at breakpoints

- Vietnamese diacritics render correctly.
- Long labels do not overflow.
- Buttons do not become too small.
- Error messages wrap properly.
- Card/table layout remains readable with long data.

## Browser compatibility matrix

Use the project-defined matrix first. If none is defined, use:

- Latest 2 versions of Chrome.
- Latest 2 versions of Safari.
- Latest 2 versions of Firefox.
- Latest 2 versions of Edge.

For responsive testing, include both desktop and mobile browser engines where relevant.

