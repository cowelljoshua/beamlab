---
version: alpha
colors:
  ink: "#172f43"
  muted: "#526877"
  primary: "#185f87"
  canvas: "#edf3f6"
  surface: "#ffffff"
  accent: "#ad4f26"
  line: "#ccd9e1"
typography:
  display:
    fontFamily: "Bahnschrift, Arial, sans-serif"
  body:
    fontFamily: "Segoe UI, Arial, sans-serif"
  data:
    fontFamily: "Consolas, monospace"
rounded:
  control: "6px"
  panel: "14px"
spacing:
  unit: "8px"
components:
  button:
    rounded: "6px"
---

# BeamLab design

## Overview

An engineering workbench for a mechanical-engineering applicant and recruiters.
Its job is to make the relationship between beam geometry, physics and a learned
surrogate visible. English, en-US numbers, local offline use on laptop and phone.
The signature is a large blue drafting viewport with a live beam, dimensions,
load arrow and exaggerated deflection. The rest is calm instrument-panel UI.
Avoid AI chat styling, promotional hero cards, dark neon and fake CAD controls.

This file owns tokens. `python scripts/export_tokens.py` generates
`web/tokens.css`: colors map to `--color-<name>`, type roles to `--font-<name>`,
radii to `--radius-<name>`, spacing to `--space-<name>`. No framework adapter.
Shared CSS consumes these variables. No third-party fonts or network requests.

## Colors

Cool blue-grey canvas, white controls, deep blue ink. Blue identifies neural
predictions and orange identifies physics references, always accompanied by
labels or different line styles. Muted text remains readable on light surfaces.
Only the drawing area uses ink as its background. Light theme only.

## Typography

Bahnschrift gives headings the character of engineering instruments; Segoe UI
supports readable explanations; Consolas aligns numbers and units. Fallbacks
are system-installed. Tabular numeric values prevent jumping controls.

## Layout

Max width 1440px, 32px desktop gutters, 16px mobile. Desktop uses a 300px controls
column and a flexible viewport/results column. Below 850px stack both naturally.
Document owns vertical scrolling; wide report tables scroll only horizontally.
No fixed page heights. Results reserve space during initialization and failure.

## Elevation & Depth

Borders and tonal changes define panels, with no decorative shadows. Drawing
depth comes from an isometric cross section, not gradients or blurred layers.

## Shapes

14px panels, 6px controls. Orthogonal dimension lines and circular node markers.

## Components

Native labeled ranges and numeric inputs share one input component built by
`app.js`. Numeric entry provides an alternative to dragging. Navigation uses
hash anchors with `aria-current`; sections preserve in-memory input state.
Buttons have hover, pressed, focus-visible and disabled states. A stable inline
live region handles validation and status. No modal, auth, CRUD, upload or select.
Charts are SVG with text summaries and downloadable numeric data. Animation is
limited to short color transitions and removed with reduced motion.

### Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Form | app.js input builder and validate | domain in physics.py/core.js | range plus number | invalid, keyboard, reset |
| Scrollbar | style.css global baseline | DESIGN.md | horizontal report overflow | browser computed style |
| Toast | app.js status() inline live region | DESIGN.md | warning/info | browser invalid-state check |

## Do's and Don'ts

- Show units, reference values and limits wherever they affect interpretation.
- Label illustrative deformation and synthesized training data explicitly.
- Never imply an engineering design is approved, safe, or ANSYS-trained.
- Keep prediction, validation and learning views in the same visual language.
