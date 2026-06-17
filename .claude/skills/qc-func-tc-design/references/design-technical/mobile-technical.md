# Mobile Technical Guideline for Test Case Design

## Purpose

This guideline defines Mobile-specific technical checks for designing test cases.

Use it together with `common-technical.md`.

This file supports two Mobile modes:

1. `mobile-native`: native or cross-platform mobile apps.
2. `mobile-hybrid`: WebView wrapper apps that inherit Mobile Native concerns and add WebView-specific concerns.

## How to choose the mode

| Mode | Use when | Main testing focus |
|---|---|---|
| `mobile-native` | App is built with Swift, Kotlin, React Native, Flutter, Xamarin, or similar mobile framework | Lifecycle, OS permission, gestures, push, deep link, biometric, offline cache, device matrix |
| `mobile-hybrid` | App UI is rendered inside WebView with native wrapper, such as Cordova, Capacitor, Ionic, wrapped PWA, or native app with WebView screens | All native checks plus WebView lifecycle, JS-native bridge, cookie sync, CSP, viewport |

## Recommended composition

```text
Mobile Native = Common Technical + Mobile Base + Native OS Add-on
Mobile Hybrid = Common Technical + Mobile Base + Native OS Add-on + WebView Add-on
```

---

# 1. Mobile Base Checklist

Apply this section to both `mobile-native` and `mobile-hybrid`.

## Phase 1: App and Screen Initialization

### App lifecycle

- Cold start from app icon.
- Splash screen appears and transitions correctly.
- First screen renders correctly.
- Warm start from background.
- UI state is preserved after background to foreground if required.
- App killed by OS and relaunched.
- State restoration follows spec.
- App launched from notification.
- App launched from deep link.

### Screen state

- Empty state.
- Populated state.
- Loading state.
- Error state.
- Permission-denied state.
- Offline state.
- Cached data state if supported.

### Permission-dependent screen

For screens using OS resources, test:

- Permission not requested yet.
- Permission allowed.
- Permission denied.
- Permission permanently denied.
- Permission revoked from Settings while app is running.
- Explainer screen or dialog.
- Open Settings action.

Common permissions:

- Camera.
- Photo library.
- Location.
- Microphone.
- Notifications.
- Contacts.
- Calendar.
- Files or media.
- Bluetooth if applicable.

## Phase 2: Component and Gesture Interaction

### Touch targets and feedback

- Tap target is at least 44pt on iOS and 48dp on Android where applicable.
- Tap feedback, ripple, pressed state, or haptic feedback follows design.
- Disabled components do not respond to tap.
- Loading buttons cannot be tapped repeatedly.

### Gestures

Cover gestures supported by the feature:

- Tap.
- Double tap.
- Long press.
- Swipe to delete.
- Swipe to archive.
- Pull to refresh.
- Infinite scroll or lazy-load.
- Pinch zoom.
- Drag pan.
- Drag and drop reorder.
- Carousel swipe.
- Bottom sheet swipe down.

### Platform navigation

#### Android

- Hardware back button pops the correct screen.
- Back closes modal, drawer, dropdown, keyboard, or bottom sheet in the correct order.
- Double-press-to-exit works if specified.
- Back does not silently kill the activity unexpectedly.

#### iOS

- Swipe-back-edge returns to the previous screen.
- Swipe-back does not conflict with carousel, tabs, or map gestures.
- Navigation bar back button behaves consistently with swipe-back.

### Soft keyboard

- Correct keyboard type appears: numeric, email, phone, URL, default.
- Secure input masks sensitive data.
- Autocorrect and autocapitalization follow spec.
- Done, Next, Search, Send action is correct.
- Tapping outside dismisses keyboard if specified.
- Focused input is not hidden by keyboard.
- Error message remains visible after keyboard opens.

### Native pickers and system UI

- Date picker.
- Time picker.
- Wheel picker.
- Action sheet.
- Document picker.
- Photo picker.
- Camera intent.
- Share sheet.
- Permission dialog.
- Biometric prompt.

For each picker:

- Open.
- Select.
- Cancel.
- Permission denied if relevant.
- Returned value is correct.

## Phase 3: Mobile Core Functional Testing

In addition to common functional testing, cover mobile-specific input and OS behavior.

### Input validation

- Required field.
- Format validation.
- Range validation.
- Length validation.
- Boundary values.
- IME-driven input restriction.
- Paste into restricted field.
- Autofill from OS suggestion.
- Password manager autofill.
- Contact picker autofill if supported.

### Network and API error

- Offline before opening screen.
- Offline during submit.
- Slow 3G or throttled connection.
- Timeout.
- 4xx.
- 5xx.
- Malformed JSON.
- Partial JSON.
- Retry action.
- Duplicate prevention after retry.

### Runtime interruption

- Incoming call.
- Alarm.
- Low battery alert.
- App moves to background during form entry.
- App moves to background during upload.
- App moves to background during payment or SSO.
- App returns to foreground.
- Low power mode.
- Storage full.

### Submit debounce

- Double tap Save/Submit.
- Tap Submit then hardware back.
- Tap Submit then app background.
- Tap Submit then reconnect.
- Only one request or one business transaction is created.

## Phase 4: Mobile Functional Integration

### In-app integration

- Search + filter + lazy-load list.
- Submit form then list refreshes.
- Tab switch preserves nested state.
- Badge count updates.
- Detail screen reflects updated data.
- Back navigation preserves previous state if required.

### Deep link and universal/app link

Test launch source:

- Browser.
- Email.
- SMS.
- QR code.
- Push notification.
- Another app.

Test app state:

- Cold start.
- Warm start.
- Already on target screen.
- User not logged in.
- User lacks permission.

### Cross-app integration

- `tel:`.
- `mailto:`.
- `maps:`.
- In-app browser.
- External browser.
- Third-party app scheme.
- Share extension.
- Receive content from another app.
- Return from external app.
- Target app not installed fallback.

### Push notification

- Foreground notification uses in-app banner or toast if specified.
- Background notification appears in OS notification UI.
- Killed app opens correctly from notification.
- Notification tap routes to the correct screen.
- Notification is marked as read.
- Multiple notifications are grouped by channel if supported.
- Permission denied behavior.

### Authentication

- Biometric prompt success.
- Biometric fail.
- Biometric cancel.
- Fallback to password or PIN.
- SSO round-trip.
- Token refresh silently on expiry.
- User is not kicked out mid-flow unless required.
- Auto-logout after idle timeout.

### Background sync

- Silent push.
- Background fetch.
- Job scheduler.
- Queue flush on reconnect.
- App resumes with consistent data.

## Phase 5: Mobile Non-Functional Testing

### Security

- Sensitive screens are masked in app switcher or recent apps.
- Tokens are stored in Keychain on iOS or Keystore on Android.
- Tokens are not stored in plaintext storage.
- Certificate pinning if applicable.
- Jailbreak or root detection if applicable.
- Clipboard restriction for sensitive fields if applicable.
- Clipboard auto-clear after configured time if applicable.
- Deep-link parameters are sanitized.
- Screenshot prevention on Android if required.
- Logs do not contain PII, token, password, or secret.

### Performance

- Cold start time on baseline device.
- Time to interactive on critical screen.
- Screen transition smoothness.
- List scrolling performance.
- Image cache memory usage.
- Long session memory leak.
- Battery drain in foreground.
- Battery drain in background.
- Background task cadence.

### Network resilience

- Cached content displayed offline.
- Write queue works offline if supported.
- Queue flushes after reconnect.
- Wi-Fi to cellular switch during request.
- Cellular to Wi-Fi switch during request.
- Retry is graceful and does not duplicate transactions.

### App lifecycle data

- Form draft survives background to foreground if required.
- Form draft survives killed app if required.
- Sensitive data is cleared after logout.
- Idle timeout works.
- Re-authentication preserves or resets workflow according to spec.

## Phase 6: Mobile GUI, Visual, and Accessibility

### Device matrix

Use the project-defined device matrix first. If none is defined, consider:

#### iOS

- Small device, such as iPhone SE.
- Base device, such as iPhone 14 or equivalent.
- Large device, such as Pro Max.
- iPad if in scope.

#### Android

- Small Android phone.
- Base Android phone.
- Large Android phone.
- Foldable if in scope.
- Android tablet if in scope.

### Orientation

- Portrait baseline.
- Landscape locked or supported according to spec.
- Rotation during form input.
- Rotation during video, map, camera, or document view if relevant.

### Safe area and system bars

- Content is not hidden under notch, dynamic island, status bar, home indicator, or navigation bar.
- Status bar style and color are correct.
- Navigation bar color is correct on Android if specified.
- Bottom action area is reachable.

### Dynamic type and font scaling

- Small font setting.
- Default font setting.
- Large font setting.
- Extra-large accessibility font.
- Text does not truncate critical content.
- Layout reflows acceptably.

### Theme

- Light mode.
- Dark mode.
- System theme switch while app is running.
- Icons and illustrations are visible in both themes.
- Contrast remains acceptable.

### Accessibility

- VoiceOver on iOS.
- TalkBack on Android.
- Every interactive element has an accessibility label.
- Reading order is logical.
- Error messages are announced where applicable.
- Color contrast meets WCAG AA where applicable.
- Reduce motion setting is respected.
- Tap target size is acceptable.

---

# 2. Native OS Add-on

Use this section for `mobile-native`. It is also inherited by `mobile-hybrid` unless the hybrid app explicitly excludes a native capability.

## Native app distribution

- App Store distribution if applicable.
- Play Store distribution if applicable.
- Enterprise distribution if applicable.
- App version and build number are correct.
- Upgrade from previous version preserves or migrates data correctly.
- First install vs upgrade behavior is clear.

## Native storage

- Secure storage for tokens and secrets.
- Local database migration if used.
- Cache invalidation.
- Storage full behavior.
- Clear cache or logout behavior.

## Native hardware and OS capability

- Camera.
- Photo library.
- Geolocation.
- Biometrics.
- Push notification.
- Contact picker.
- Calendar integration.
- Document picker.
- Bluetooth or NFC if applicable.
- Background audio or media session if applicable.

---

# 3. WebView Add-on for Mobile Hybrid

Use this section only when platform type is `mobile-hybrid`.

## Definition

`mobile-hybrid` means a mobile app where the UI is rendered inside a WebView wrapped by a native shell. It inherits most native mobile checks and adds WebView-specific checks.

## Phase 1: WebView Initialization

- Splash remains visible until WebView load event or first meaningful paint.
- No white flash between splash and content.
- Cold start creates and loads WebView correctly.
- Warm start preserves WebView state according to spec.
- Cookies and sessionStorage are preserved on warm start if expected.
- Killed app relaunch reloads from URL or local bundle according to spec.
- Offline first launch with no cached bundle shows native error screen with Retry.
- Default browser error page is not shown inside the app.
- Service Worker registers if used.
- Service Worker fallback works on platforms where it is restricted.

## Phase 2: WebView Interaction and Bridge

### JS-native bridge

For each bridge method:

- JS calls native method successfully.
- Native handler receives correct method and arguments.
- Success callback fires once with correct payload.
- Error callback fires with structured error.
- Timeout is handled.
- Bridge unavailable outside app shell degrades gracefully.
- Invalid method is rejected.
- Unauthorized method is rejected.

### Scroll and navigation ownership

- Pull-to-refresh is owned by either WebView or native layer, not both.
- Native scroll and WebView scroll do not conflict.
- iOS swipe-back-edge behavior is defined.
- Android hardware back pops WebView history first if specified.
- After WebView history is empty, Android back exits native screen or app according to spec.

### Form inputs inside WebView

- `<input type="tel">` opens numeric keypad.
- `<input type="email">` opens email keypad.
- `<input type="file">` opens native file picker.
- Keyboard avoidance scrolls focused input into view.
- Autocomplete and autofill behavior follows spec.

### Native UI invoked from WebView

- Camera opened from JS bridge.
- Geolocation requested from WebView and native layer consistently.
- File picker opened from WebView.
- Date picker or action sheet opened as native UI if specified.
- Biometric prompt opened from JS bridge.
- Cancel and failure return cleanly to JS callback.

## Phase 3: Hybrid Core Functional Testing

- Web-side validation works inside WebView.
- Required, format, range, length, and boundary validation match Web behavior.
- Error messages localize correctly inside WebView.
- JSON parse errors are handled in JS layer.
- Malformed server response does not crash native app.
- `fetch()` network failure shows in-app retry UI.
- Browser default network error page is not shown.
- Bridge-mediated flows return correct result to Web layer.

## Phase 4: Hybrid Functional Integration

- Native screen to WebView screen preserves auth state.
- WebView screen to native screen preserves auth state.
- Token sharing via bridge or cookie sync works as specified.
- Deep link opens app and routes into the correct WebView page.
- Deep link works on cold start and warm start.
- Push notification opens the correct WebView route.
- Cookie set in WebView is visible to native HTTP layer if required.
- Cookie set in native HTTP layer is visible to WebView if required.
- Third-party iframe loads if allowed.
- Payment gateway redirect returns to in-app callback.
- OAuth provider redirect returns to app and WebView route.

## Phase 5: Hybrid Non-Functional Testing

### Security

- Bridge whitelist allows only approved native methods.
- Malicious JS cannot call sensitive native methods.
- WebView Content Security Policy is enforced.
- Mixed content is blocked.
- HTTPS WebView refuses HTTP subresources unless explicitly allowed.
- JS file URL access is disabled.
- Token is not stored in WebView localStorage if native secure storage is required.
- XSS cannot escalate into native bridge abuse.

### Performance

- WebView initialization cost is within target.
- JS bundle size is acceptable.
- JS parse time is acceptable.
- Multiple WebView screens do not leak memory.
- WebView is destroyed or reused according to architecture.
- Long session remains stable.

### WebView version drift

- iOS WKWebView behavior is checked on supported iOS versions.
- Android System WebView minimum supported version is stated.
- Unsupported WebView version shows graceful message or fallback.

### Offline and cache

- Service Worker cache strategy works if used.
- Cached content is available offline if required.
- Cache invalidates on app version bump.
- Stale cache does not show incompatible UI or API data.

## Phase 6: Hybrid Visual and Device Compliance

- Viewport meta is correct.
- Content respects safe-area insets.
- CSS `prefers-color-scheme` follows native theme if required.
- Native status bar overlays correctly with WebView content.
- No z-index conflict with status bar, notch, or safe area.
- System font and Web font are consistent with native screens.
- Keyboard pushes or resizes WebView content correctly.
- Vietnamese diacritics render correctly inside WebView at all device sizes.
