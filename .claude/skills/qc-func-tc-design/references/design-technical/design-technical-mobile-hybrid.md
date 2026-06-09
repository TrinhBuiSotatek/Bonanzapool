# Design Technical — Mobile Hybrid (WebView Wrapper)

## When to use this rubric

Load this file when `project-context-master.md` §1 → "Product Platform Type" contains `mobile-hybrid`.

Applies to: Mobile apps where the UI is rendered inside a WebView wrapped by a native shell (Cordova / Capacitor / Ionic / wrapped PWA / Native + WebView screens). Inherits MOST native concerns from `design-technical-mobile-native.md` AND adds WebView-specific concerns.

## 6-Phase Drafting Rubric

### Phase 1: App & Screen Initialization (Static + Lifecycle + WebView readiness)

All native concerns from `mobile-native.md` Phase 1, PLUS:

- **WebView load lifecycle** — Splash stays until WebView's `load` event (or first-meaningful-paint), not just WebView creation. Verify no white-flash between splash and first content.
- **WebView cold start vs warm start** — On warm start, WebView state preserved (cookies, sessionStorage); on killed → relaunch, WebView reloads from URL.
- **Offline initial load** — If first-launch is offline AND no cached bundle: show native error screen with Retry, NOT a default browser "Cannot connect" page.
- **Service Worker availability** — If used: register on first launch, fall back gracefully on platforms where SW is restricted in WebView.

### Phase 2: Component, Gesture & WebView Bridge Interactions

All native gesture concerns, PLUS:

- **Native ↔ WebView bridge calls** — JS calls `bridge.invoke(method, args)` → native handler → callback. Verify:
  - Async callback fires correctly on success.
  - Error callback fires with structured error on failure.
  - Bridge unavailable (e.g., loaded outside the app shell) → graceful degradation.
- **WebView scroll vs native scroll** — Pull-to-refresh: who owns it (WebView or native)? Avoid double-handling.
- **iOS swipe-back-edge inside WebView** — May conflict with WebView history. Spec: which wins?
- **Android hardware back inside WebView** — Should pop WebView history first, then exit native screen, then exit app per spec.
- **Form inputs inside WebView** — IME type respected (`<input type="tel">` opens numeric on iOS/Android), keyboard avoidance scrolls input into view.
- **Native modals invoked from JS** — Action sheet, date picker, file picker — verify the native UI is shown (not a WebView simulation).

### Phase 3: Core Functional Testing (Logic + Bridge calls + Web validation)

All native logic checks, PLUS:

- **Validation runs on the Web side** — Required, Format, Range, BVA — as in web. Confirm error messages localize correctly inside WebView.
- **Bridge-mediated flows** —
  - Camera: JS requests → native camera opens → image returned to JS callback.
  - Geolocation: WebView Geolocation API permission prompt vs native permission prompt — which is asked? Spec must clarify.
  - File upload: `<input type="file">` opens native picker on iOS / Android.
  - Biometric: `bridge.requestBiometric()` → native prompt → JS callback.
- **Server response handling** — JSON parse errors handled in JS layer; native crash NOT triggered by malformed payload.
- **Network errors** — fetch() fails → in-app retry UI (NOT browser default error page).

### Phase 4: Functional Integration (Cross-feature + WebView ↔ Native + Cross-app)

All native cross-app flows, PLUS:

- **Native screens ↔ WebView screens** — Navigation between native and WebView preserves auth state (token shared via bridge or cookie sync).
- **Deep link → WebView route** — App opens via deep link → bridges into the WebView with a target route param → WebView navigates to correct page on cold start vs warm start.
- **Push notification → WebView route** — Tap notification → app launches → WebView navigates to correct route, scroll position default.
- **Cookie sync** — Cookies set in WebView visible to native HTTP layer (and vice versa) per spec.
- **Third-party iframes inside WebView** — Maps, payment gateway, OAuth provider: verify iframe loads, redirect-back to in-app callback works.

### Phase 5: Non-Functional & Hybrid-Specific

All native NFR, PLUS:

- **Security** —
  - Bridge whitelist: only approved native methods callable from JS — verify malicious JS injected via XSS CANNOT call sensitive native methods (camera, contacts, file system).
  - WebView CSP enforced.
  - Mixed-content blocked (HTTPS WebView refuses HTTP subresources).
  - Disable JS file:// URL access.
  - Token storage: prefer native Keychain via bridge over WebView localStorage (which is unencrypted).
- **Performance** —
  - WebView initialization cost on cold start (often the largest contributor).
  - JS bundle size + parse time.
  - Memory: WebView instances are heavyweight — verify no leak when navigating between WebView screens.
- **WebView version drift** —
  - iOS: WKWebView ties to Safari version (per OS).
  - Android: WebView is updated separately via Play Store — minimum supported version stated.
- **Offline & cache** — Service Worker / app-cache strategy for offline browsing; cache invalidation on app version bump.

### Phase 6: GUI, Visual & Device Compliance

All native visual concerns, PLUS:

- **WebView viewport meta** — `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` — verify content respects safe-area insets (env(safe-area-inset-*)).
- **CSS dark-mode** — `@media (prefers-color-scheme: dark)` follows the native theme switch.
- **Native font vs Web font** — System font availability (`-apple-system`, `Roboto`) consistent with native screens.
- **Status bar color** — Native status bar color overlays correctly with WebView content; no z-fighting.
- **Keyboard appearance** — IME pushes WebView content up correctly (no overlap).
- **Long-string Vietnamese diacritics** — Render correctly inside WebView at all device sizes.
