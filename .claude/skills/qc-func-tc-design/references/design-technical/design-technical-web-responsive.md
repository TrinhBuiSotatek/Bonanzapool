# Design Technical — Web Responsive

## When to use this rubric

Load this file when `project-context-master.md` §1 → "Product Platform Type" contains `web-responsive`.

Applies to: Web applications that adapt layout across desktop, tablet, and mobile viewport widths (single codebase, responsive CSS / Tailwind / Bootstrap / etc.). The rubric MUST be applied at each declared breakpoint, not only at desktop.

## 6-Phase Drafting Rubric

> Apply all 6 phases to every screen. The phases are content categories (systematic coverage buckets), NOT separate checkpoint boundaries — they all contribute to the same in-memory TC list.

### Phase 1: Screen Initialization (Static States)

Verify the landing state of the screen before any user interaction.

- **Empty State (No Data)** — Verify the visibility and specific default attributes of every object on the screen.
  - Explicitly describe placeholders, empty-state icons, or "No Data" messages.
- **Populated State (With Data)** — Verify the default appearance of all items.
  - Describe the default state (Enabled / Disabled) of all components relative to the data present.
- **Loading State** — Skeleton / spinner / progress indicator while data fetches; no white-screen flash.
- **Error State** — 4xx / 5xx / network timeout: friendly message + Retry CTA.

### Phase 2: Item Interactions (Component States)

Verify the behavior of individual UI components without triggering core business logic.

- **Navigation & Reset** — Check 'X' icons, 'Cancel' buttons, and 'Close' controls to ensure they exit or reset the view as intended.
- **Screen Initialization Triggers** — Verify that clicking functional buttons correctly opens or initializes the relevant sub-functions or popups.
- **Component Verification** —
  - Dropdowns: Verify clickability and ensure the correct list of values is displayed.
  - Textboxes / Buttons: Verify states (Clickable, Disabled, Read-only) based on the design or business rules.
  - Checkboxes / Radio / Toggles: default state, group exclusivity, indeterminate state.
- **Navigation Tools** — Pagination behavior (Active page, Next/Prev arrows, page-size selector).
- **Keyboard interactions** — Tab order, Enter to submit, Esc to close modal, focus ring visible.

### Phase 3: Core Functional Testing (Logic Analysis)

Apply systematic testing techniques for every specific function available on the screen.

- **Happy Path** — Execute the successful flow using valid inputs.
- **Validation** —
  - Required Fields: Ensure the system blocks saving if mandatory fields are empty.
  - Format: Email, Phone, Date, or specific data formats.
  - Range: Character length or numeric limits.
  - Boundary Value Analysis (BVA): Test at the limits (Min, Max, Min-1, Max+1).
- **Exception / Error Handling** — Trigger and verify system responses to invalid logic, server errors, or external errors.

### Phase 4: Functional Integration

Verify the synergy between different functions on the same screen or across screens.

- Examples: How a 'Search' action affects 'Pagination'; how 'Deleting' an item updates the list count in real-time; how filter + sort + pagination compose; how submit redirects + flashes a success toast.
- Cross-tab / multi-window: opening the same record in two tabs and editing — last-write-wins or conflict warning?

### Phase 5: UI-Level Non-Functional Testing

- **Security** — Sensitive data masking (passwords), input sanitization (SQL Injection / XSS) in UI fields, CSRF token presence on state-changing forms.
- **UX / Loading** — Loading indicators (spinners) during data fetching, button debounce to prevent double-clicks, optimistic UI revert on failure.
- **Browser back / forward / refresh** — Form state preservation or warning on unsaved changes; URL deep-link works on direct paste.
- **Cookie / LocalStorage / SessionStorage** — Auth token / preferences persisted correctly; cleared on logout.

### Phase 6: GUI & Visual Compliance (Design-to-Code)

This phase focuses on visual fidelity AT EACH DECLARED BREAKPOINT.

- **Design Alignment** — Compare every object against the design file (Figma / Mockup) for position, color (HEX), spacing, font size, line-height — at each breakpoint declared in the design.
- **Responsive Breakpoints** — Render at desktop (≥ 1280px), laptop (1024px), tablet (768px), mobile (375–414px). Verify:
  - Layout reflows correctly (no horizontal scroll, no clipped content).
  - Navigation collapses to hamburger / drawer at small breakpoints.
  - Tap targets ≥ 44px on touch breakpoints.
  - Font scales legibly; no overflow with long Vietnamese diacritics.
- **Browser compatibility matrix** — Latest-2 versions of Chrome, Safari, Firefox, Edge (or per project spec).
- **Localization** — Vietnamese diacritics render correctly; long-string locales don't overflow if multi-locale.
- **Accessibility basics** — Color contrast ≥ WCAG AA on text, semantic HTML (h1/h2/nav/button), alt text on images, form labels associated with inputs.
