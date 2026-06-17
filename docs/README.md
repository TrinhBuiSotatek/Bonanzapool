# docs

Top-level documentation root for the BNZA project. Contains client-provided specs, white-label specs, and SOTATEK team artifacts.

---

## client-docs — từ phía client (zen / MEGABUCKS, Inc.)

> **Rule:** Do not freely edit these. They are reference specs handed over by the client. Propose changes back to the client rather than editing in place.

| Folder | Content | Notes |
|--------|---------|-------|
| `bnza-docs/en/` | English specs, strategy, infrastructure (for SOTATEK) | Keep in sync with `jp/` |
| `bnza-docs/jp/` | 日本語版 (for zen) | Keep in sync with `en/` — update **both** on any change |
| `bnza-exbot/` | EXBOT spec (zen-confidential) | Do not share outside authorized team |

---

## wl — White-label product specs

| Folder | Content |
|--------|---------|
| `wl/OVERVIEW.en.md` | White-label product overview (English) |
| `wl/OVERVIEW.ja.md` | White-label product overview (Japanese) |
| `wl/wl-bnza/en/` | WL-BNZA spec (English) — `SPEC_v5.2.5.md` |
| `wl/wl-bnza/ja/` | WL-BNZA spec (Japanese) |
| `wl/wl-mlm/en/` | WL-MLM specs — Admin, Mobile, Platform Core |
| `wl/wl-mlm/ja/` | WL-MLM specs (Japanese) |

---

## sotatek — SOTATEK team artifacts

### sotatek/ba — BA team

Business-analysis artifacts authored by the BA team. See `sotatek/ba/README.md` for full structure.

| Folder | Content |
|--------|---------|
| `sotatek/ba/01_intake/` | Intake, escalation notes, high-level plan |
| `sotatek/ba/02_backbone/` | Backbone doc, feature map |
| `sotatek/ba/03_modules/` | Per-module: FRDs, use-cases, ASCII screen specs (admin, ex, exbot, mobile, operator, pool) |

### sotatek/dev — Dev team

Engineering docs and bug reports authored by the dev team.

| Folder | Content |
|--------|---------|
| `sotatek/dev/bugs/` | Bug report files (dated, per-issue) |
