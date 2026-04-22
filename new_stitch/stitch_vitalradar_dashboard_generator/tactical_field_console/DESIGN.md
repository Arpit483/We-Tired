---
name: Tactical Field Console
colors:
  surface: '#101508'
  surface-dim: '#101508'
  surface-bright: '#353b2c'
  surface-container-lowest: '#0b1005'
  surface-container-low: '#181d10'
  surface-container: '#1c2114'
  surface-container-high: '#262c1d'
  surface-container-highest: '#313728'
  on-surface: '#dfe5cf'
  on-surface-variant: '#c1caad'
  inverse-surface: '#dfe5cf'
  inverse-on-surface: '#2d3224'
  outline: '#8b947a'
  outline-variant: '#414a34'
  surface-tint: '#91db00'
  primary: '#ffffff'
  on-primary: '#213600'
  primary-container: '#a6fa00'
  on-primary-container: '#486f00'
  inverse-primary: '#436900'
  secondary: '#ffb3af'
  on-secondary: '#68000d'
  secondary-container: '#920418'
  on-secondary-container: '#ff9994'
  tertiary: '#ffffff'
  on-tertiary: '#412d00'
  tertiary-container: '#ffdea7'
  on-tertiary-container: '#835e00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#a6fa00'
  primary-fixed-dim: '#91db00'
  on-primary-fixed: '#111f00'
  on-primary-fixed-variant: '#324f00'
  secondary-fixed: '#ffdad7'
  secondary-fixed-dim: '#ffb3af'
  on-secondary-fixed: '#410005'
  on-secondary-fixed-variant: '#920418'
  tertiary-fixed: '#ffdea7'
  tertiary-fixed-dim: '#fcbc32'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5e4200'
  background: '#101508'
  on-background: '#dfe5cf'
  surface-variant: '#313728'
typography:
  heading-caps:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  ui-label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 14px
  ui-label-reg:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
  telemetry-lg:
    fontFamily: IBM Plex Mono
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 20px
  telemetry-md:
    fontFamily: IBM Plex Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 18px
  telemetry-sm:
    fontFamily: IBM Plex Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
spacing:
  unit: 4px
  gutter: 8px
  margin: 12px
  container-padding: 16px
  density-high: 4px
  density-medium: 8px
---

## Brand & Style
This design system is engineered for high-stakes disaster response environments where clarity and speed of information processing are paramount. The aesthetic is **Utilitarian Brutalism**: a rugged, non-decorative framework that prioritizes functional density over visual flair. 

The brand personality is authoritative, reliable, and austere. It evokes the feeling of a mission-critical military or aerospace instrument panel. By stripping away all non-essential styling—eliminating gradients, shadows, and blurs—the design system ensures that the user's focus remains entirely on actionable data. The emotional response is one of controlled urgency and technical precision.

## Colors
The color palette is optimized for low-light environments and high-contrast readability. 

- **Backgrounds:** The foundation is a deep matte black (`#0A0A0A`) to minimize eye strain and screen glare during night operations.
- **Surfaces:** UI elements use layered grays (`#141414`, `#1E1E1E`) to create structural hierarchy without relying on shadows.
- **Action/Status (S1):** Neon Lime (`#AAFF00`) is the primary interactive color, used for active states, primary actions, and "Normal" operational status.
- **Critical (S2):** Coral Red (`#FF5C5C`) is reserved strictly for emergencies, critical failures, or life-safety alerts.
- **Warning:** Muted Amber (`#D59A00`) signals caution, non-critical telemetry drift, or system warnings.

## Typography
The system employs a dual-font strategy to separate interface controls from raw data.

1. **Inter:** Used for all UI labels, navigation, and structural headers. It provides maximum legibility in a compact, sans-serif form.
2. **IBM Plex Mono:** Used for all telemetry, coordinates, timestamps, and sensor data. The monospaced nature ensures that fluctuating numerical values do not cause layout shifts and align perfectly in vertical columns for rapid scanning.

All text should favor high-contrast white or light gray against the dark backgrounds, with the exception of status-specific alerts.

## Layout & Spacing
This design system utilizes a strict **Technical Grid Alignment** based on a 4px baseline. 

- **Grid Model:** A 12-column fluid grid for primary modules, with nested 1px internal separators.
- **Density:** High information density is required. Gutters are kept to a minimum (8px) to maximize the "data-per-square-inch" ratio.
- **Separators:** Use 1px solid borders (`#2A2A2A`) to define sections rather than whitespace.
- **Alignment:** All elements must snap to the 4px grid. No fluid or organic spacing is permitted.

## Elevation & Depth
In this design system, depth is communicated through **Tonal Layering** and **Outline Containment** rather than shadows or blurs.

- **Stacking:** The further "forward" an element is (like a modal or a popover), the lighter its background hex value becomes (moving from `#0A0A0A` up to `#1E1E1E`).
- **Borders:** Every functional module is contained within a 1px solid border. This creates a "panel" effect reminiscent of physical rack-mounted hardware.
- **Interaction:** State changes (hover/active) are indicated by color fills or border-color shifts to Neon Lime, never by increasing shadow depth.

## Shapes
Shapes are strictly **geometric and squared**. 

- **Corners:** Default to 0px (sharp) for all primary containers, panels, and input fields. 
- **Exceptions:** A maximum radius of 4px may be applied only to small interactive components like buttons or checkboxes to provide a subtle tactile hint, but the preference is 0px for a seamless grid look.
- **Geometry:** Avoid circles unless representing specific physical hardware (e.g., a dial or a radial sensor icon). All status indicators should be square or rectangular.

## Components
- **Buttons:** Rectangular with 1px borders. Primary buttons use a solid Neon Lime background with black text. Secondary buttons use a transparent background with a Lime border.
- **Data Tables:** High-density rows with 1px separators. Every second row is slightly tinted (`#141414`) for legibility. Headers use uppercase Inter bold.
- **Status Chips:** Small, rectangular blocks of color. No text labels inside chips if the color alone conveys the status (e.g., a 10x10px square of Coral Red for "Alert").
- **Input Fields:** Inset appearance using a darker background than the surface it sits on. Focus state is a 1px Neon Lime border.
- **Telemetry Readouts:** Grouped in boxes with labels in the top-left corner. Use IBM Plex Mono for the primary value, significantly larger than the label.
- **Crosshairs/Markers:** 1px lines used for map overlays and sensor alignment, utilizing the accent palette to denote target type.