# VitalRadar UI Documentation

## Project Overview
**VitalRadar** is a non-invasive survivor detection system designed for emergency disaster response and search & rescue (SAR) missions (e.g., NDRF teams operating in earthquake zones). 

Utilizing dual LD2410 mmWave radar sensors connected to a Raspberry Pi 4, the system detects micro-movements, specifically human respiration, under rubble. By analyzing confidence scores, frequency, and signal strength across both sensors, the system establishes a voting consensus to confidently verify the presence of a living person before authorizing dangerous extraction operations. 

## Target Users
The primary users are field-deployed **Emergency Responders** and **Rescue Team Commanders**. They operate in high-stress, time-critical environments where data must be immediately legible. The dashboard relies on a dark, technical, civilian-rescue aesthetic—eschewing "military command" themes or generic SaaS layouts in favor of raw, rugged instrumentation.

---

## Screen Purpose & Responsiveness Decisions

### 1. Dashboard (Live Telemetry)
**Purpose**: The primary operational screen displaying real-time distance, confidence, frequency, and voting consensus from both sensors.
**Responsiveness Adjustments**:
- **Removed fixed heights**: Replaced rigid `calc(100vh - 48px)` constraints with fluid `min-h-screen` allowing panels to naturally push down content on mobile.
- **Bento Grid Reflow**: Changed the 3-column grid breakpoint from `768px` to `1024px` so tablets display the S1, S2, and Merged Telemetry panels stacked vertically, preventing text overlap and cramping.
- **DirectionRing Simplification**: The complex ASCII radar schematic was removed. While visually interesting on desktop, it breaks on narrow screens. It was replaced with a responsive, high-contrast stats block focusing on the Target Vector and Agreement metrics.

### 2. Analytics / History
**Purpose**: Post-event log review to trace breathing detection events and identify stable confidence zones over time.
**Responsiveness Adjustments**:
- **Grid Stacking**: The top stat blocks now collapse from 4 columns down to 2, and then 1 on mobile (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`).
- **Responsive Tables**: The `DetectionTable` is wrapped in an `overflow-x-auto` container, allowing horizontal swiping on mobile rather than forcing column truncation or word breaks.

### 3. System Health (Config)
**Purpose**: Monitors the Raspberry Pi 4 hardware integrity (CPU load, Temp, RAM) and pipeline status (ttyUSB ports, model params).
**Responsiveness Adjustments**:
- **Column Spans**: Switched `md:col-span-6` to `lg:col-span-6`. Hardware and Model blocks will now neatly stack on tablets and mobile displays to prevent squished ASCII progress bars.
- **ASCII Bars**: Implemented boundary checks inside the `<AsciiBar />` component to ensure the string length doesn't overflow container widths.

### 4. About / Landing
**Purpose**: Initializing screen showing mission intent and system readiness before launching into the live dashboard.
**Responsiveness Adjustments**:
- **Removed Decorative Flowcharts**: The complex SVG schematic (FIG 1.0) with absolute positioned lines and "Subject Target" bounding boxes was entirely stripped out. It relied heavily on rigid aspect ratios that broke on mobile.
- **Operational Protocol Card**: Replaced the diagram with a responsive, stacked instruction card detailing the 3-step operational protocol. This is infinitely scalable and highly legible on constrained displays.

---

## Global Design Principles Applied
- **No Horizontal Overflow**: Guaranteed by eliminating absolute SVGs and fixed-width canvas blocks.
- **Hardware Restraint**: Kept CSS animations to minimal opacity pulses (no heavy transforms). Dropped unnecessary re-renders in `App.jsx` by converting the desktop sidebar into a pure CSS hidden element on mobile, and replacing it with a static Bottom Navigation Bar.
- **Mobile Navigation**: Implemented a fixed `h-14` bottom tab bar for mobile screens ensuring navigational control without requiring complex hamburger menu state logic.

## Next Steps for React + Flask Integration
1. **Dependency Installation**: Ensure the Raspberry Pi has Node installed to run `npm run build` inside `app/frontend/`.
2. **Flask Serving**: The Flask backend will serve the bundled `dist` folder via `app/static`.
3. **Socket Validation**: Verify that the Python Eventlet server is successfully broadcasting the `sensor_update` JSON payload at 100ms intervals over the local network without bottlenecking the Pi's CPU.
