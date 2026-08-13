# Macro Allocation Agent — Design System

**Direction:** Iridescent Liquid Glass / light spatial finance portal

**Updated:** 2026-08-13

**Design dials:** Variance 6/10 · Motion 5/10 · Density 6/10

## Visual foundation

| Role | Value |
|---|---|
| Background | `#F4F6FF` with white, lavender and blue radial light |
| Surface | `rgba(255,255,255,.58)` |
| Strong surface | `rgba(255,255,255,.78)` |
| Primary | `#4266E8` |
| Primary dark | `#173B98` |
| Accent | `#775CF0` |
| Pink refraction | `#D98BD1` |
| Cyan refraction | `#82D4F8` |
| Text | `#0A1538` |
| Muted text | `#5F6B8B` |
| Border | `rgba(78,101,181,.16)` |

Use `Space Grotesk` for display headings and metric values, and `DM Sans` for body copy and controls. Keep Chinese system-font fallbacks enabled.

## Layout

- Maximum content width: `1440px`.
- Top-level navigation is a horizontally scrollable, sticky glass pill bar.
- Every feature page starts with a two-column editorial hero: large copy on the left and an iridescent CSS sphere/orbit on the right.
- Dashboard sections follow the hero and use one clear heading plus glass containers; do not create excessive nested cards.
- Desktop breakpoint: hero becomes two columns above `680px`; mobile stacks the artwork under the copy.

## Liquid Glass

Glass surfaces combine all four properties below:

1. Semi-transparent white fill.
2. Thin bright edge (`rgba(255,255,255,.88)`).
3. `backdrop-filter: blur(18–28px) saturate(150–170%)`.
4. Soft blue-violet shadow and a directional white highlight.

The glass is for navigation, controls, forms, KPI cards and chart frames. Data marks and body text remain solid and high-contrast.

## Interaction and motion

- Hover: translate by no more than `4px`; duration `220–320ms`; easing `cubic-bezier(.16,1,.3,1)`.
- Scroll reveal: fade from 18% opacity, move up `34px`, scale from `.975`, blur from `6px` using CSS View Timelines where supported.
- Hero artwork uses a subtle scroll-linked vertical drift and scale.
- All controls have a visible `3px` blue focus ring.
- `prefers-reduced-motion: reduce` disables animations and smooth scrolling.
- `prefers-contrast: more` increases surface opacity and removes backdrop blur.

## Components

- **Primary CTA:** dark navy gradient, white text, pill radius, 44px minimum height.
- **Secondary CTA:** translucent white glass pill, dark blue label.
- **Metric:** minimum height 116px desktop / 98px mobile; solid metric value; hover lift only.
- **Input:** 44px minimum height, 14px radius, translucent white fill and blue focus ring.
- **Plotly frame:** 20px radius, transparent canvas, blue/violet/pink/cyan/gold/red chart palette.
- **Status badge:** compact translucent pill with a small gradient dot; never use emoji as an icon.

## Accessibility and QA

- Body text contrast must remain at least 4.5:1; glass effects must never be the only state cue.
- All interactions need visible hover and keyboard-focus states.
- Navigation must remain horizontally scrollable at 375px without wrapping.
- Verify 375px, 768px, 1024px and 1440px layouts.
- Browser fallback must leave content fully visible when CSS View Timelines or backdrop filters are unavailable.
