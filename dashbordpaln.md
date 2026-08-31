# CyberForensix Dashboard Redesign

Redesign the existing dashboard from a long-scroll, mixed-purpose layout to a visually impressive, decision-oriented forensic analysis dashboard that wins over hackathon judges at first glance.

## Spec Grill Summary

| Dimension | Decision |
|---|---|
| **Audience** | Forensic investigator + SOC analyst + hackathon judges |
| **Primary decision** | Per-email triage → campaign detection → aggregate posture |
| **Cadence** | Batch upload, review together |
| **Above-the-fold** | Fraud score + risk tier → Auth status → Geo map → AI explanation |
| **Campaign graph** | Always prominent, key differentiator |
| **Analytics** | All charts kept, relocated to dedicated section |
| **Visual direction** | Brighter, colorful, visually impressive, hackathon-ready |
| **Screen target** | Desktop/laptop/projector responsive |

## Design Principles Applied

1. **Visual hierarchy (Gestalt)**: Fraud score is the focal point — largest, most colorful element top-left. Auth status and geo map sit beside it. Everything else flows down.
2. **Above the fold**: The four critical elements (score, auth, geo, explanation) must fit in a single viewport without scrolling.
3. **Progressive disclosure**: Campaign graph + analytics visible on scroll, not competing with triage.
4. **Color for meaning**: Semantic risk colors (green→amber→red) for status. Vibrant gradients and glows for visual impact.
5. **No pie charts**: Tier distribution uses stacked bar or donut with clear labels.

## Proposed Changes

### Design System Overhaul

#### [MODIFY] [App.css](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/App.css)

Major visual redesign:
- **Brighter color palette**: More saturated accent colors, vibrant gradients, stronger glows
- **Animated backgrounds**: Subtle particle/mesh gradient effects for visual wow-factor
- **Enhanced glassmorphism**: Stronger blur, more visible glass effects
- **Better grid layout**: Restructured grid for above-the-fold priority
- **Micro-animations**: Slide-in, scale-up, pulse effects for card reveals
- **Responsive breakpoints**: Ensure clean layout from 1366px to 1920px+
- **Typography refinement**: Larger hero numbers, cleaner type scale

### Layout Restructure

#### [MODIFY] [App.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/App.jsx)

Restructure the results layout:
- **Row 1** (hero): Fraud Score (left, ~30%) + AI Explanation + Auth Summary (right, ~70%) — all above the fold
- **Row 2**: Geo Trace Map (left, 50%) + Campaign Graph (right, 50%) — visible with minimal scroll
- **Row 3**: Analytics section with clear "Intelligence Analytics" section header
- Move feature contribution chart inline with fraud score card

### Component Polish

#### [MODIFY] [FraudScoreCard.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/components/FraudScoreCard.jsx)

- Larger, more dramatic score ring with animated gradient stroke
- Pulsing glow effect keyed to risk tier
- Feature contribution bars integrated directly below the score
- Risk tier badge with stronger visual weight

#### [MODIFY] [HeaderTable.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/components/HeaderTable.jsx)

- Compact auth status row: 3 pill badges (SPF/DKIM/DMARC) in a horizontal strip — not a full table
- Envelope details collapsed behind a "Show Details" toggle
- Reduce vertical space consumed

#### [MODIFY] [Navbar.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/components/Navbar.jsx)

- Add a third nav tab: "📊 Analytics" to separate aggregate views
- Animated gradient underline on active tab
- Subtle brand animation

#### [MODIFY] [AnalyticsDashboard.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/components/AnalyticsDashboard.jsx)

- Cleaner card layout with consistent sizing
- Smoother SVG chart animations
- Better empty states with call-to-action

#### [MODIFY] [CampaignGraph.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/components/CampaignGraph.jsx)

- Larger default height
- Glow effects on nodes
- "No campaign detected" state that's visually clean, not broken-looking

#### [MODIFY] [TraceMap.jsx](file:///c:/Users/akyas/Desktop/Desktop/sih/frontend/src/components/TraceMap.jsx)

- Dark tile layer for map (matches dark theme)
- Pulsing marker animation at threat origin
- Cleaner info bar below map

## Verification Plan

### Manual Verification
- Start Vite dev server (`npm run dev`)
- Visual inspection at 1366×768, 1536×864, and 1920×1080
- Verify above-the-fold priority: score + auth + geo + explanation visible without scrolling
- Upload test `.eml` to verify all components render correctly with real data
- Check all analytics charts render in the analytics section
