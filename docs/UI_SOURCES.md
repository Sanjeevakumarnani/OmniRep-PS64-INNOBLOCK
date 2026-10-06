# OmniRep UI sources

The interface uses source-adapted patterns from the 21st.dev community registry, while keeping OmniRep-specific information architecture and data views rather than a generic AI-generated dashboard.

Patterns used:

- **Spotlight Card** — pointer position is written to CSS variables, avoiding React state per pointer frame.
- **Shimmer Button** — primary action treatment.
- **Border Beam** — reserved for featured surfaces so motion does not overwhelm the information architecture.
- **Number Ticker** — score transitions and trajectory.
- **Timeline pattern** — recent proof events.

21st.dev documents its components as editable source code that lands in the project, and its public registry currently includes Spotlight Card, Shimmer Button, Border Beam, Number Ticker and timeline variants. citeturn854423search2turn854423search1turn854423search12turn377946search0

Performance rule: visual motion is used sparingly. The spotlight implementation writes CSS variables rather than setting React state for every pointer update, and reduced-motion users get static surfaces.
