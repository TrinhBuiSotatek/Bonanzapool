# Design Technical — Mobile Native (iOS / Android)

## When to use this rubric

Load this file when `project-context-master.md` §1 → "Product Platform Type" contains `mobile-native`.

Applies to: Native mobile apps built with Swift / Kotlin / React Native / Flutter / Xamarin etc. distributed via App Store / Play Store / enterprise channel. Differs from web because of: app lifecycle, OS permissions, gestures, hardware back, push, deep link, offline cache, biometrics, safe-area insets, dark mode, accessibility (VoiceOver / TalkBack).

## 6-Phase Drafting Rubric

### Phase 1: App & Screen Initialization (Static + Lifecycle States)

Verify static state in BOTH dimensions: state of the screen + state of the app lifecycle.

- **Cold start** — App launches from icon → splash → first screen renders correctly.
- **Warm start** — Backgrounded → foregrounded: UI / data state preserved (form draft, scroll position, selected tab, filter).
- **Killed → relaunch** — OS kills app: state restoration follows spec (preserved or reset?), deep-link target (if any) routes correctly.
- **Empty State (No Data)** — Placeholder, empty-state illustration, "Không có dữ liệu" message + CTA (e.g., "Tạo mới") if applicable.
- **Populated State (With Data)** — List / grid / card layout, default item state, badge / count accurate.
- **Loading State** — Skeleton screen / shimmer / spinner while fetching; no blank screen.
- **Error State** — 4xx / 5xx / network timeout / offline: friendly message + Retry CTA.
- **Permission-denied State** — When the screen needs an OS permission (Location, Camera, Notifications, Photo) and it is denied: show explainer + "Open Settings" button.

### Phase 2: Component & Gesture Interactions

Verify behavior of UI components and GESTURES — without triggering core business logic.

- **Touch target & feedback** — Tap area ≥ 44pt (iOS) / 48dp (Android); haptic / ripple feedback per design.
- **Gesture set** —
  - Tap, double-tap, long-press.
  - Swipe-to-delete / swipe-to-archive on list items.
  - Pull-to-refresh triggers reload with loading indicator.
  - Infinite scroll / lazy-load (NOT pagination as on web).
  - Pinch-zoom / drag-pan on image viewer / map.
  - Drag-and-drop reorder (if applicable).
- **Hardware back button (Android)** — Back stack correct, double-press-to-exit (if spec), no silent activity kill.
- **iOS swipe-back-edge** — Returns to previous screen, no conflict with tab / carousel swipe.
- **Soft keyboard** —
  - Opens correct IME type (numeric / email / phone / url / default).
  - autocorrect / autocapitalize / secure-entry per spec.
  - Tap-outside or "Done" dismisses keyboard.
  - Content scrolls so the input is NOT hidden under the keyboard.
- **Native pickers** — Date picker, time picker, wheel picker, action sheet, document picker — verify cancel + select.
- **Modals / Bottom sheets / Dialogs** — Open, dismiss (tap-outside / swipe-down / OS back), backdrop blur per spec.
- **Navigation containers** — Tab bar / drawer / sidebar: switching preserves per-tab state, badge count updates.
- **Component visual states** — enabled / disabled / pressed / selected / focused — feedback clear.

### Phase 3: Core Functional Testing (Logic + Mobile inputs)

Apply systematic techniques to every function — pay attention to inputs from HARDWARE / OS.

- **Happy Path** — Standard flow with valid inputs.
- **Validation** —
  - Required, Format (email / phone / CMND-CCCD / MST), Range, Length.
  - BVA at Min, Min-1, Max, Max+1.
  - IME-driven: numeric keypad rejects alpha; email keypad has '@'.
  - Auto-fill from device (contact picker, OS suggestion, password manager) — verify trust + edit-ability.
- **Exception / Error** —
  - Network: offline, slow 3G, timeout, 4xx / 5xx → message + Retry.
  - OS permission denied at runtime, permission revoked while app is running.
  - Storage full, low-power mode (background may be throttled).
  - Server returns malformed / partial JSON.
- **Submit debounce** — Double-tap MUST NOT create a duplicate request.

### Phase 4: Functional Integration (Cross-feature + Cross-app + System)

Verify synergy in-app AND with the OS / other apps.

- **In-app integration** — Search + filter + lazy-load list; submit form → list refreshes; tab switch preserves nested state.
- **Cross-app integration** —
  - Deep link / Universal Link (iOS) / App Link (Android) from Browser / Email / SMS / QR — COLD start vs WARM start MUST both route correctly.
  - Open external app: `tel:`, `mailto:`, `maps:`, `vneid://`, in-app browser fallback when target app not installed.
  - Camera / Photo picker intent → image returned; cancel returned cleanly.
  - Share extension: receive content from another app.
- **Push notification flow** —
  - Foreground: in-app banner / toast (NOT OS notification UI).
  - Background: OS notification → tap → deep-link to correct screen, mark-as-read correctly.
  - Killed: notification → cold start → route to correct screen, no crash.
  - Multiple notifications grouped per channel.
- **Auth integration** —
  - Biometric (Face ID / Touch ID / fingerprint) prompt → fallback to password on fail / cancel.
  - SSO (VNeID, Apple, Google) deep-link round-trip.
  - Token refresh silently on expiry — do NOT kick the user mid-flow.
- **Background sync** — Silent push wake-up, background fetch, job scheduler runs at correct cadence.

### Phase 5: Non-Functional & Mobile-Specific

- **Security** —
  - Sensitive screens masked in app switcher (iOS recents / Android recents) — privacy screen.
  - Tokens in Keychain (iOS) / Keystore (Android) — NOT plaintext / SharedPreferences.
  - Certificate pinning (if applicable).
  - Jailbreak / root detection (if applicable).
  - Clipboard: sensitive fields cannot be copied or auto-clear after N seconds.
  - Deep-link parameter sanitization (prevent injection into in-app WebView).
- **Performance** —
  - Cold start ≤ target Xs on baseline device.
  - Time-to-interactive on critical screens.
  - No memory leak after long session (image cache evicts correctly).
  - Battery drain in background ≤ threshold.
- **Network resilience** —
  - Offline → cached content displayed; write-queue flushes on reconnect.
  - Switch Wi-Fi ↔ cellular mid-request → graceful retry.
- **App lifecycle data** —
  - Form draft survives background → foreground (and optionally killed).
  - Auto-logout after idle timeout.
- **OS interruptions** — Incoming call, alarm, low-battery alert, audio focus loss while playing media → app pause / resume correctly.

### Phase 6: GUI, Visual & Device Compliance (Design-to-Code on Mobile)

- **Design alignment** vs Figma: position, color (HEX), spacing, font-size, line-height — at baseline device (e.g., iPhone 14 / Pixel 7).
- **Safe area insets** — Content NOT hidden under notch / dynamic island / home indicator / status bar / nav bar.
- **Device matrix** — verify on:
  - iPhone: SE (small), 14 (base), 14 Pro Max (large) — and Plus / mini if in scope.
  - Android: small (e.g., Pixel 4a), base (Pixel 7), large screen, foldable if in scope.
  - Tablet (iPad / Android tablet) — only if in scope.
- **Orientation** — Portrait baseline; landscape: locked / supported / adaptive per spec.
- **Dynamic Type / system font scaling** — XS → XXXL: text not truncated, layout reflows acceptably.
- **Dark mode + Light mode** — Both themes render correctly (icons, illustrations, contrast).
- **Localization** — Vietnamese diacritics render correctly; long-string locales (DE / RU) don't overflow if multi-locale.
- **Accessibility** —
  - VoiceOver (iOS) / TalkBack (Android): every interactive element has an accessibility label.
  - Color contrast ≥ WCAG AA on text.
  - Reduce motion respected.
  - Tap target ≥ 44pt / 48dp.
- **Animation & transition** — Native feel, 60fps, no jank on push/pop screen, modal slide-up, list scroll.
- **App branding** — App icon, launch image, splash match brand guideline; theme color of status bar correct.
