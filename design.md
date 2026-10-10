# design.md: Design System aur Frontend Guide

> **Ye file visual aur interface decisions ke liye authoritative hai.** Antigravity ke default design choices ya Stitch ke default output se upar. Koi bhi UI kaam shuru karne se pehle ise padho.
> Ye file ka naam hamesha `design.md` rahega. `DESIGN.md` ki doosri copy mat banao.

---

## 1. Visual Direction (ek line me)

**High-utility minimalism:** warm neutral background, dark readable text, ek hi ember accent, patli grey dividers, **sab kuch 0px radius**, aur product khud (live map aur real data) hi sabse bada visual hai.

Reference Apple ki website ka **discipline** hai (typography hierarchy, whitespace, restraint, product focus). Unka layout, colors, branding ya assets copy nahi karne.

## 2. Non-negotiable Rules

**Kabhi nahi:**
- Inter, Roboto, Arial, Geist, Geist Mono, Space Grotesk, ya system fonts primary font ke roop me.
- Koi bhi rounded corner. **Har border-radius = `0px`**: buttons, inputs, menus, modals, cards, image containers, map popups, map controls, markers.
- Purple/blue gradients, glows, neon, dark background par accent glow.
- Shadows ya blur/frosted glass/soft UI/pill tags.
- Teen cards ki row jisme upar icon ho; generic bento grid; har section ek jaisa.
- Poora page centered. (Text left-aligned, deliberate asymmetric layouts.)
- Emoji as icons, sparkle icons, dot grids, orbs, decorative stripes, abstract vector illustrations, animated arrows.
- Taglines ("Your life, simplified" jaise), fake stats, invented testimonials/logos/customers, performance claims.
- Fake dashboards ya fake screenshots as real functionality.
- Website copy me em dash ya en dash.
- "Not X, but Y" jaisa formula. Benefit seedha likho.
- Final implementation me placeholder text (Lorem ipsum, "Coming soon" jaisi filler cheezein).

**Hamesha:**
- Har visual element ka ek clear purpose ho.
- Simulated ya estimated cheez clearly labelled ho ("Estimate", "Indicative").
- Severity sirf color se nahi, text label se bhi.

## 3. Typography

| Role | Font | Weights | Note |
|------|------|---------|------|
| Headings + Body | **Public Sans** | 400, 500, 600, 700 | Primary |
| Data values (coordinates, timestamps, FRP, ETA) | **IBM Plex Mono** | 400, 500 | Sirf numbers/data ke liye |
| Hindi text | **Noto Sans Devanagari** | 400, 600 | Public Sans me Devanagari glyphs nahi hain |

- Fonts **self-hosted** (npm `@fontsource/*` packages ya woff2 files). Google Fonts CDN nahi, taaki visitor IPs third party ko na jayein. Ye dependency ek concrete need se justified hai, agents.md me record karo.
- Hindi text ke liye `lang="hi"` aur line-height thoda zyada (Devanagari ko jagah chahiye).

**Type scale (desktop / mobile, size/line-height):**

| Token | Desktop | Mobile | Weight | Use |
|-------|---------|--------|--------|-----|
| `display` | 56/60 | 36/42 | 600, letter-spacing -0.02em | Home headline |
| `h1` | 40/46 | 30/36 | 600 | Page titles |
| `h2` | 28/36 | 24/32 | 600 | Section titles |
| `h3` | 20/28 | 18/26 | 600 | Sub-sections |
| `body` | 17/28 | 16/26 | 400 | Paragraphs |
| `small` | 14/20 | 14/20 | 400 | Captions, meta |
| `data` | 14/20 | 14/20 | Plex Mono 500 | Numbers |

Hierarchy size, weight, spacing se. Italic/underline/effects se nahi. Paragraph max width ~64ch.

## 4. Colors (tokens)

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#FAF8F5` | Page background (pure white nahi) |
| `--surface` | `#F3F0EB` | Panels, table header |
| `--text` | `#1C1917` | Primary text |
| `--text-muted` | `#57534E` | Secondary text |
| `--divider` | `#E5E1DA` | 1px lines |
| `--hover` | `#F0ECE6` | Hover tint |
| `--accent` | `#B3411B` | Primary buttons, links, high severity |
| `--accent-hover` | `#9A3716` | Accent hover |
| `--accent-mid` | `#C8643C` | Medium severity |
| `--neutral-low` | `#78716C` | Low severity |
| `--focus` | `#1C1917` | Focus outline |

- Ek hi accent. Koi doosra competing color nahi.
- **Contrast:** approximate calculation ke hisaab se `--accent` on `--bg` aur white on `--accent` dono 4.5:1 se upar hain, par **Antigravity ko real contrast tool se verify karna hai** aur result agents.md me record karna hai. Fail hone par value darker karo.
- Severity encoding: High = solid accent fill, Medium = `--accent-mid` fill, Low = hollow marker with `--neutral-low` border. Saath me hamesha text label.

## 5. Spacing aur Layout

- **Base unit 4px.** Tokens: `4, 8, 12, 16, 24, 32, 48, 64, 96, 128`.
- Section vertical spacing: desktop 96 ya 128, mobile 64.
- Max content width 1200px; reading width 64ch.
- Dividers: 1px `--divider`. Boxes ke liye border, shadow nahi.
- Sections ki composition **purpose ke hisaab se alag** ho. Consistency typography, spacing, color aur alignment se aaye, repeated layout se nahi.

## 6. Components

**Buttons**
- Primary: `--accent` background, white text, `min-height: 44px`, padding 12/20, radius 0.
- Secondary: transparent, 1px `--text` border, same size.
- Hover: primary -> `--accent-hover`; secondary -> `--hover` tint. Koi movement ya animated arrow nahi.
- Labels batate hain kya hoga: "Subscribe to alerts for Chandigarh", "Print report". "Submit"/"Click here" nahi.

**Inputs:** visible `<label>` (placeholder label nahi), 1px border, radius 0, error message field ke neeche aur `aria-describedby` se linked.

**Focus:** `:focus-visible` par `2px solid var(--focus)`, `outline-offset: 2px`. Hatana nahi.

**Tables:** header `--surface`, rows ke beech 1px divider, numbers `data` font me right-aligned.

**Links:** accent color, underline default me (accessibility), hover par underline thickness ya tint change.

**Icons:** default me nahi. Sirf tab jab action clear karna ho. Koi icon library tab tak install nahi.

## 7. Map Styling (Leaflet / react-leaflet)

Leaflet ke default styles me rounded corners hain. Ye sab override honge:

- **Markers:** `L.divIcon` se **square** markers (0 radius). Size = FRP ke hisaab se (min/max clamp). Circle markers use nahi hone.
- **Popups, zoom controls, attribution:** radius 0, 1px border, shadow nahi. Zoom buttons text ("+" aur "-") hon.
- **Attribution (OpenStreetMap contributors) hamesha visible.** Hatani nahi.
- **Smoke path:** patli (2px) accent line, direction dikhane ke liye line ke end me simple arrowhead (static, animation nahi). Label: "Estimated smoke direction".
- **Tiles:** muted look ke liye optional CSS filter (grayscale) allowed hai. Tile provider decision Q-07.
- **Keyboard:** map ke saath hamesha ek text alternative ho (cities-at-risk list + clusters table), kyunki map akela keyboard/screen reader user ke liye kaafi nahi.

## 8. Pages aur Composition Guidance

| Page | Composition (direction, final layout Stitch se aayega) |
|------|-------------------------------------------------------|
| **Home** | Left-aligned headline + 2 line explanation + primary action; right/neeche **real live map** (large). Neeche "How the estimate works" ek vertical, numbered, text-first list (teen cards nahi). Live counts API se computed. |
| **Map** | Full-width app layout: map left (zyada width), right panel me cities at risk aur subscribe. Top par stats bar. |
| **Report** | Simple table layout, date picker, Print button. Print stylesheet: nav/footer hidden, black on white. |
| **Method** | Long-form reading layout (64ch), sources aur limitations. |
| **Terms / Privacy** | Plain reading layout, "Draft" notice top par. |

**Home par product hi visual hai:** real map + real numbers. Agar API unavailable ho to error state dikhao, fake numbers nahi.

## 9. Copy Guidelines

- Seedha, specific, short. Product ka kaam pehle section me clear ho.
- Fire detection ko "possible crop-residue fire" ya "fire detection" likho. "Confirmed stubble burning" nahi (prd.md limitations dekho).
- "Near real-time" likho, "real-time" nahi. Smoke path = "estimate".
- Pricing nahi, testimonials nahi, stats nahi jo data se compute na hon.
- Em/en dash nahi. Comma, period ya hyphen use karo.

**Draft headline (owner confirm kare, Q-01 ke baad):**
- Headline: "Fire detections across Punjab and Haryana, and where the smoke may go next"
- Sub: "Satellite fire data and wind forecasts, updated through the day. Pick your city and get an email when smoke is likely to reach it."
- Primary button: "See the live map"; Secondary: "How the estimate works"

> Ye drafts hain. Final copy owner approve karega (M-13). Antigravity apni taraf se naya marketing text invent nahi karega.

## 10. Motion aur States

- Motion minimal. Sirf hover tint aur focus. Page scroll normal.
- `prefers-reduced-motion: reduce` par saari transitions band.
- **Loading:** skeleton blocks (real async content ke liye), koi artificial delay nahi.
- **Error:** kya hua + kya kare ("Retry" button).
- **Empty:** "No fire detections in this period for the selected region." jaisa specific message.
- **Success:** subscribe ke baad "Check your inbox to confirm your subscription".

## 11. Responsive

- Test widths: **360, 768, 1280**.
- Horizontal scroll nahi (wide tables apne container me `overflow-x: auto`).
- Mobile par map aur list stacked; list pehle ya map ke neeche, dono reachable.
- Touch targets kam se kam 44px.

## 12. Stitch aur Antigravity ka Workflow

1. **Stitch par pehle sirf ek representative section** (Home hero + map region) generate karo (prompt `docs/prompt.md` me S-01). Poora site ek saath nahi.
2. Desktop aur mobile dono par check: typography, spacing, alignment, contrast, generic/AI-look wali cheezein.
3. Fixes ke baad hi baaki pages (S-02).
4. **Stitch ka map area sirf layout ke liye hai.** Final product me real map aur real data aayega. Stitch ke mock numbers final site me kabhi copy nahi hone chahiye.
5. Antigravity Stitch design ko faithfully implement kare. Agar design change zaroori ho to reason agents.md me record kare.
6. Implement ke baad rendered page browser me dekho (agar browser nahi chala sakte to clearly bolo, "inspected" mat likho).

## 13. Final Review Checklist (T-076 me)

Generic SaaS layout? Repeated cards? Gradients/shadows/rounded corners kahin? Vague headlines? Fake stats? Unnecessary icons? Placeholder text? Fake interactions? Mobile problems? Stitch se mismatch? `design.md` se contradiction? Jo mile use fix karo, phir dobara dekho.
