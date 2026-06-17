# Desktop Technical Guideline for Test Case Design

## Purpose

This guideline defines Desktop Native-specific technical checks for designing test cases.

Use it together with `common-technical.md`.

## Platform type

Use this guideline when the product platform type is `desktop-native`.

It applies to desktop applications installed on Windows, macOS, or Linux, including apps built with Electron, .NET WPF, WinUI, Qt, Java Swing, native Cocoa, or similar technologies.

Desktop native applications require additional test coverage because they involve window management, file-system access, OS dialogs, keyboard shortcuts, system tray, notifications, installer, updater, and deeper OS integration.

## Recommended composition

```text
Desktop Native = Common Technical + Desktop Add-on
```

---

# 1. Desktop Native Checklist

## Phase 1: App and Window Initialization

### First launch

- App launches correctly after installation.
- Onboarding appears only when expected.
- EULA appears only when expected.
- License activation appears only when expected.
- First-launch setup is skipped on subsequent launches if completed.
- First-launch failure can be retried.

### Cold start

- Splash screen appears if designed.
- Main window opens correctly.
- First content paint is within target.
- Last window size is restored if required.
- Last window position is restored if required.
- Last monitor is restored if required.
- App handles missing previous monitor gracefully.

### Warm start and restore

- Restore from minimized state.
- Restore from hidden state.
- Click taskbar or dock icon brings window forward.
- Scroll position is preserved if required.
- Unsaved form state is preserved if required.

### Multi-window

- Open a second main window.
- Independent state vs shared state follows spec.
- Same record opened in multiple windows behaves correctly.
- Closing one window does not unexpectedly close all windows unless specified.
- Last window close behavior follows OS convention and product spec.

### Static screen states

- Empty state.
- Populated state.
- Loading state.
- Error state.
- Offline state.
- File-system error state.
- Permission error state.

---

## Phase 2: Window, Component, and Input Interaction

### Window management

- Resize window.
- Layout reflows down to declared minimum size.
- Below minimum size behavior follows spec.
- Maximize.
- Restore.
- Minimize.
- Close.
- Full-screen mode if supported.
- Exit full-screen with Esc if specified.
- Menu bar behavior in full screen if applicable.

### Multi-monitor behavior

- Move window to second monitor.
- Move window between monitors with different scaling.
- Move window to monitor that is later disconnected.
- App opens gracefully when remembered monitor is unavailable.
- Modal/dialog appears on the expected monitor.

### Component verification

- Dropdown.
- Combobox.
- Treeview.
- Datagrid.
- Tabs.
- Docked panels.
- Date picker.
- Time picker.
- Textbox.
- Button.
- Checkbox.
- Radio.
- Toggle.

For each component:

- Enabled state.
- Disabled state.
- Read-only state.
- Focused state.
- Selected state.
- Error state.
- Keyboard navigation.

### Keyboard shortcuts

Validate platform conventions.

#### Common shortcuts

- Save: Ctrl+S on Windows/Linux, Cmd+S on macOS.
- Undo: Ctrl+Z or Cmd+Z.
- Redo: Ctrl+Y/Ctrl+Shift+Z or Cmd+Shift+Z according to platform.
- Copy: Ctrl+C or Cmd+C.
- Paste: Ctrl+V or Cmd+V.
- Cut: Ctrl+X or Cmd+X.
- Find: Ctrl+F or Cmd+F.
- Select all: Ctrl+A or Cmd+A.
- Help: F1 if supported.
- Cancel/close: Esc where expected.

#### Grid and list shortcuts

- Arrow keys.
- Home.
- End.
- Page Up.
- Page Down.
- Space selection.
- Shift multi-select.
- Ctrl/Cmd multi-select if supported.

### Mouse and pointer interaction

- Left click.
- Double click default action.
- Right-click context menu.
- Drag and drop within app.
- Drag and drop from OS into app.
- Drag and drop from app to OS if supported.
- Mouse wheel scroll.
- Trackpad scroll.
- Touch or pen input if device supports it.

---

## Phase 3: Desktop Core Functional Testing

In addition to common functional testing, cover desktop-specific inputs and local resources.

### Standard business flow

- Create.
- Read.
- Update.
- Delete.
- Search.
- Filter.
- Sort.
- Import.
- Export.
- Print.
- Save.
- Open.

### Validation

- Required.
- Format.
- Range.
- Length.
- Boundary values.
- Cross-field validation.
- Server validation.
- Local validation.

### File-system operations

#### Open file dialog

- Open dialog appears.
- Default folder is correct.
- File type filter is correct.
- Single file selection.
- Multiple file selection if supported.
- Cancel returns gracefully.
- Recent folder behavior follows spec.

#### Save file dialog

- Save dialog appears.
- Default file name is correct.
- Default folder is correct.
- File extension is appended automatically if required.
- Overwrite confirmation appears.
- Cancel returns gracefully.
- Save result is correct.

#### File path handling

- Unicode path.
- Vietnamese path.
- Path with spaces.
- Path with special characters.
- Long path.
- Network drive path if supported.
- External drive path if supported.

#### File error handling

- Read-only file.
- Locked file.
- Permission denied.
- Disk full.
- File deleted during operation.
- Unsupported file type.
- Corrupted file.
- Partial import.

### Bulk operation

- Bulk import.
- Bulk export.
- Bulk process.
- Progress indicator.
- Cancel operation.
- Resume or retry if supported.
- Partial success report.
- Failed item reason.

---

## Phase 4: Desktop Functional Integration

### In-app integration

- Filter + sort + pagination.
- Master-detail behavior.
- Multiple windows showing the same record.
- Same record update syncs across windows if required.
- Local IPC sync works if used.
- Unsaved changes warning across window close or app exit.

### OS integration

#### System tray or menu bar icon

- Tray icon appears.
- Right-click menu appears.
- Double-click activates app.
- Status indicator updates correctly.
- Quit from tray works correctly.

#### OS notification

- Notification appears in OS notification center.
- Notification content is correct.
- Clicking notification activates window.
- Clicking notification routes to the correct source screen.
- Notification permission or system setting behavior is handled.

#### File association

- Double-click associated file from Explorer/Finder/file manager.
- App launches if not running.
- App opens file if already running.
- Unsupported version or corrupted file shows friendly error.

#### Protocol handler

- Custom protocol URL opens app.
- App routes to the correct screen.
- Cold start and warm start both work.
- URL parameters are sanitized.
- Invalid protocol payload is rejected gracefully.

#### Start on boot

- Toggle start-on-boot on.
- Toggle start-on-boot off.
- Setting persists after restart.
- Uninstall respects user choice or cleans up correctly.

#### Print integration

- Print dialog opens.
- Default printer is selected.
- Page range works.
- Copies works.
- Print preview is correct.
- Cancel returns gracefully.

### Auto-update flow

- Check for update on launch if supported.
- Scheduled update check if supported.
- Download update in background.
- Progress is shown if required.
- Prompt user to restart.
- User can defer update if supported.
- Failed download can retry.
- Update payload is verified.
- Rollback path is documented or testable according to project scope.

### Concurrent edit

- Two users edit the same server-backed record.
- Two app instances edit the same record.
- Conflict detection works.
- Merge, warning, or last-write-wins follows spec.
- User does not lose data silently.

---

## Phase 5: Desktop Non-Functional Testing

### Security

- App is code signed.
- Windows Authenticode signing is valid if applicable.
- macOS Developer ID signing is valid if applicable.
- Installer is not flagged by SmartScreen or Gatekeeper unexpectedly.
- Credentials are stored in OS secure storage:
  - Windows Credential Manager.
  - macOS Keychain.
  - Linux Secret Service.
- Tokens or passwords are not stored in plaintext config files.
- Auto-update payload is signed and verified.
- File-system access is scoped according to OS guideline.
- IPC is authenticated.
- No anonymous or unauthorized process can call sensitive IPC methods.
- Logs do not contain PII, tokens, passwords, or secrets.

### Performance

Define project-specific thresholds.

- Cold start time on baseline hardware.
- First content paint.
- Memory usage during normal session.
- Memory usage during long-running session, for example 8 hours.
- CPU usage at idle.
- CPU usage during heavy operation.
- Battery wake-up behavior on laptop.
- Large file open/save performance.
- Large import/export performance.

### Compatibility matrix

Use the project-defined matrix first.

Potential coverage:

#### Windows

- Windows 10.
- Windows 11.
- x64.
- ARM64 if supported.

#### macOS

- Last 3 macOS releases if required.
- Intel Mac.
- Apple Silicon.

#### Linux

- Declared distribution.
- Declared version.
- Package format if relevant.

### Installer and uninstaller

#### Installer

- Install completes successfully.
- Expected files are created.
- Shortcuts are created.
- Registry entries are created on Windows if applicable.
- App appears in Applications folder on macOS if applicable.
- App appears in application menu on Linux if applicable.
- Install for current user vs all users follows spec.
- Upgrade from previous version works.

#### Uninstaller

- App files are removed.
- Shortcuts are removed.
- Registry entries are cleaned if applicable.
- User data is kept or removed according to selected option.
- Background service, tray process, or helper process is removed.
- Auto-start entry is removed.

### Crash recovery

- Unhandled exception creates crash dump if required.
- User sees friendly apology dialog.
- App can relaunch after crash.
- Next launch offers to restore unsaved work if supported.
- Corrupted session recovery works.

### Logging

- Log file is created.
- Log rotation works.
- Log level is configurable if required.
- Log location follows OS convention.
- Logs exclude PII and secrets.
- Error logs are useful for diagnosis.

---

## Phase 6: Desktop GUI, Visual, and OS Compliance

### Design alignment

- Position.
- Size.
- Color.
- Spacing.
- Font size.
- Line height.
- Icon.
- Window title.
- Menu item label.
- Status bar text.
- Dialog layout.

### DPI scaling

Test according to project scope:

- 100%.
- 125%.
- 150%.
- 175%.
- 200%.
- Fractional scaling if supported.

Expected behavior:

- No blurry icons.
- No clipped controls.
- Layout remains usable.
- Text remains readable.
- Hit targets remain correct.

### Multi-monitor mixed DPI

- Drag window from 100% monitor to 200% monitor.
- Drag window from high DPI monitor to low DPI monitor.
- Window adapts on the fly.
- Modal/dialog appears correctly scaled.
- Tooltip and context menu scale correctly.

### Theme and OS appearance

- Light mode.
- Dark mode.
- System theme switch while app is running.
- High contrast mode on Windows if in scope.
- Native menu, scrollbar, dialog, and control style follow OS convention unless intentionally custom.

### Localization

- Vietnamese diacritics render correctly.
- Long labels do not truncate critical information.
- Menu and dialog text fit correctly.
- File paths with Vietnamese characters display correctly.

### Accessibility

- Keyboard-only navigation.
- Complete tab order.
- Visible focus indicator.
- Screen reader labels:
  - NVDA on Windows.
  - JAWS on Windows if required.
  - VoiceOver on macOS.
- Color contrast meets WCAG AA where applicable.
- High contrast and large text OS settings are respected if in scope.

### App branding

- App icon sizes are correct.
- Windows icon sizes include required variants if applicable.
- macOS `.icns` is correct if applicable.
- Splash screen follows brand guideline.
- About dialog shows correct app name, version, build number, copyright, and license.

