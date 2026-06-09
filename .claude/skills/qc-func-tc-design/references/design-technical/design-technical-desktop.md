# Design Technical — Desktop Native

## When to use this rubric

Load this file when `project-context-master.md` §1 → "Product Platform Type" contains `desktop-native`.

Applies to: Desktop applications installed on Windows / macOS / Linux — built with Electron / .NET WPF / WinUI / Qt / Java Swing / native Cocoa / etc. Differs from web: window management, file-system access, OS dialogs, keyboard shortcuts, system tray, OS notifications, installer / updater, deep OS integration.

## 6-Phase Drafting Rubric

### Phase 1: App & Window Initialization (Static + Lifecycle States)

- **First launch (post-install)** — Onboarding / EULA / license activation flow appears once; subsequent launches skip.
- **Cold start** — Splash → main window opens at remembered position / size / monitor; content first-paint within target.
- **Multi-window** — Open second main window: independent state vs shared state per spec.
- **Restore from minimized / hidden** — Click dock / taskbar icon → window comes forward, scroll position preserved.
- **Empty State (No Data)** — Placeholder, empty-state illustration, "No items" + Create CTA.
- **Populated State (With Data)** — Default sort, default column order, default zoom level.
- **Loading State** — Spinner / progress bar; long-running jobs show non-blocking progress in status bar.
- **Error State** — 4xx / 5xx / network / file-system error: dialog or inline panel with Retry; no silent failure.

### Phase 2: Component, Window & Input Interactions

- **Window management** —
  - Resize: layout reflows down to declared min size; below min → enforce min size or show warning per spec.
  - Maximize / restore / minimize / close — buttons behave per OS conventions.
  - Multi-monitor: drag window to second monitor, DPI-scaling adapts (1x → 2x → fractional).
  - Full-screen mode (if applicable): menu bar auto-hide, exit on Esc.
- **Component verification** —
  - Dropdowns / Combobox / Treeview / Datagrid: keyboard navigation (arrow keys, Home / End, PgUp / PgDn).
  - Textboxes / Buttons: enabled / disabled / read-only states.
  - Date / time pickers: keyboard input + calendar pick.
  - Tabs / docked panels: tear-off / re-dock if spec supports it.
- **Keyboard shortcuts** — Standard OS shortcuts (Ctrl+S / Cmd+S, Ctrl+Z, Ctrl+C/V/X, Ctrl+F find, F1 help, Esc cancel) work per platform conventions.
- **Mouse interactions** — Right-click context menus, double-click default action, drag-and-drop within app + from OS (file dropped into app).
- **Touch / pen** (if device supports) — Tap = click, long-press = right-click, pinch-zoom on canvas / map.

### Phase 3: Core Functional Testing (Logic + Desktop inputs)

- **Happy Path** — Standard CRUD + workflow with valid input.
- **Validation** — Required, Format, Range, Length, BVA, cross-field.
- **File-system operations** —
  - Open file dialog: file selection, multiple selection, file-type filter, cancel returns gracefully.
  - Save file dialog: default filename, default folder, overwrite confirmation, file extension auto-append.
  - Drag-and-drop file from OS: accepted MIME types, rejected types show error.
  - File path with Unicode / Vietnamese / spaces / special chars handled.
  - Read-only / locked file: error handled, not crash.
- **Exception / Error Handling** —
  - Network offline: offline mode (if supported) or error dialog with Retry.
  - Server validation echoed inline.
  - Disk full / file locked / permission denied: graceful error, no data loss.
- **Bulk operations** — Bulk import / export / process: progress indicator, cancellable, partial-success handled.

### Phase 4: Functional Integration (Cross-feature + Cross-app + OS)

- **In-app** — Filter + sort + pagination compose; master-detail; multiple windows of same record sync via local IPC.
- **OS integration** —
  - System tray icon: balloon / toast notifications, right-click menu, double-click activate.
  - OS notifications: shown via OS notification center; click → activate window + route to source.
  - File association: open `.<ext>` from Explorer / Finder → app launches, opens that file.
  - Protocol handler: `myapp://...` URL from browser → app launches, routes correctly.
  - Login items / start-on-boot (if spec): toggle works, respects user choice on uninstall.
  - Default printer / Print dialog: preview, page-range, copies, cancel.
- **Auto-update flow** —
  - Check-for-update on launch + scheduled.
  - Download in background, prompt user to restart.
  - Failed download: retry, user can defer.
  - Rollback path documented (NOT necessarily tested by QC, but spec must mention).
- **Concurrent edit** — Two users / two app instances editing same server-backed record: conflict detection, last-write-wins or merge per spec.

### Phase 5: Non-Functional & Desktop-Specific

- **Security** —
  - Code signed (Authenticode on Windows, Developer ID on macOS) — installer not flagged by SmartScreen / Gatekeeper.
  - Token / credential storage: Windows Credential Manager / macOS Keychain / Linux Secret Service — NOT plaintext config file.
  - Auto-update payload signed and verified.
  - File-system access scoped to user profile / app sandbox per OS guideline.
  - Inter-process communication (IPC) authenticated; no anonymous access from other processes.
- **Performance** —
  - Cold start ≤ target Xs on baseline hardware.
  - Memory: long-running session (8h+) — no leak.
  - CPU at idle: ≤ threshold.
  - Battery (laptop) — no excessive wake-ups.
- **Compatibility matrix** — Per project spec:
  - Windows: 10 / 11; x64 / ARM64.
  - macOS: last 3 releases; Intel + Apple Silicon.
  - Linux: declared distro / version.
- **Installer / Uninstaller** — Install creates expected files / shortcuts / registry entries; uninstall removes them cleanly (with explicit "keep user data" option per spec).
- **Crash recovery** — Unhandled exception → crash dump created, user shown apology dialog, on next launch offer to restore unsaved work.
- **Logging** — Log file rotation, log level configurable, no PII in logs.

### Phase 6: GUI, Visual & OS Compliance

- **Design alignment** — Position, color, spacing, font-size match Figma / mockup at baseline DPI (100%).
- **DPI scaling** — Render correctly at 100% / 125% / 150% / 175% / 200% / fractional. No blurry icons, no clipped controls.
- **Multi-monitor mixed DPI** — Drag window between 100% and 200% monitor: layout adapts on the fly.
- **OS theme & dark mode** — Follows OS dark / light theme; high-contrast mode supported on Windows.
- **Native widgets vs custom widgets** — Per spec: dialogs, scrollbars, menus look native (or intentionally custom).
- **Localization** — Vietnamese diacritics render correctly; long-label locales don't truncate.
- **Accessibility** —
  - Screen reader: NVDA / JAWS (Windows), VoiceOver (macOS) — every control labelled.
  - Keyboard-only navigation: Tab order complete, focus indicator visible.
  - Color contrast ≥ WCAG AA.
  - High-contrast / large-text OS settings respected.
- **App branding** — App icon at all required sizes (16 / 32 / 48 / 256 px on Windows; .icns on macOS), splash, About dialog version string correct.
