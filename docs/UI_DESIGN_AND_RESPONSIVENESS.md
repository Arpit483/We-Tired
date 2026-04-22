# VitalRadar UI Design & Responsiveness

## Overview
VitalRadar is a radar-based survivor detection system designed for earthquake and collapsed-structure rescue missions. It assists rescue teams (such as the NDRF or local emergency responders) in locating individuals trapped under rubble by detecting breathing-related micro-motions.

The system utilizes dual radar sensors (Left and Right) to provide:
- Survivor detection confidence (%)
- Distance to the target
- Movement direction (Left, Center, Right)
- Terminal-style live logs for operational debugging

## Target Users & Environment
The UI is strictly designed for **civilian disaster-response teams**, prioritizing a technical, rugged, and humane field-usable aesthetic over military or generic SaaS styles. 
The software runs on a **Raspberry Pi 4 (4GB)** and is viewed on various field devices (tablets, rugged phones, Pi touchscreen displays). Therefore, the interface must be highly responsive, readable in harsh lighting, and extremely lightweight (avoiding heavy animations that consume CPU/RAM).

## Responsiveness Decisions & Cleanup
To ensure smooth operation on the Raspberry Pi and perfect scaling across mobile, tablet, and desktop displays, the following design decisions were made:

1. **Removal of Heavy Decorative Elements:**
   - The original "Tactical" HTML contained oversized, fixed-width `w-64 h-64` spinning SVG/CSS reticles. These consumed massive CPU power due to continuous CSS animations and broke horizontal scrolling on mobile. 
   - *Resolution:* They were removed and replaced with a clean, responsive "Primary Status Panel" (the Center Panel) that communicates exactly what the responder needs (Status, Confidence, Direction) without overflow or lag.

2. **Responsive Stacking Layout:**
   - The hardcoded grid (`grid-cols-12`) was updated to a responsive Flex/Grid architecture (`flex-col md:grid md:grid-cols-12`). 
   - On mobile, the **Fused Center Status** jumps to the top (`order-1`), followed by the Left Sensor (`order-2`) and Right Sensor (`order-3`). This ensures the most critical information is immediately visible without scrolling.

3. **Terminal Scaling:**
   - The live log terminal was moved to the bottom of the content flow with a flexible height (`h-48 md:h-56`). On mobile, it scrolls naturally within the page content above the mobile navigation bar.

4. **Sidebar/Navigation:**
   - Instead of a fixed wide sidebar that hides content, the application leverages React Router with a fixed Desktop sidebar (`md:w-64`) and a convenient bottom-bar navigation on mobile devices.

## Key UI Sections
- **Header:** Displays System Ready state and active connection pulse.
- **Center Fused Panel:** Shows the aggregated detection status (e.g., `DETECTED - MOVE LEFT`) and a large confidence percentage.
- **Left / Right Sensor Panels:** Show individual radar telemetry, including distance, confidence bars, and segmented voting grids to visualize model agreement.
- **System Console (Terminal):** A scrolling list of real-time SSE data from the Python backend for diagnostic purposes.

## Implementation Notes
This UI has been fully integrated into the **React + Vite** stack using Tailwind CSS.
- **Styling:** Colors leverage the `tailwind.config.js` theme (`neon-lime`, `neon-coral`, `neon-cyan`) to maintain the "dark rescue" identity.
- **State Management:** Sensor data is piped through the `SensorContext.jsx` using Server-Sent Events (SSE). 
- **Performance:** `React.memo` is used on high-frequency components (`SensorPanel`, `TerminalLog`) to prevent unnecessary re-renders when data updates multiple times per second.
