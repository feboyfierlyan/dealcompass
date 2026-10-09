# Desktop simplification — 10 October 2026

## Brief and research

Users still found the Mixpanel-inspired iteration overwhelming. The new target is a
clear first task with fewer competing visual blocks, not more instructional copy.
Desktop only; this extends PR #29. The core workflow remains: select a priority →
understand its action and conditions → prepare a plan → inspect evidence when needed.

Mobbin MCP was used directly (`search_screens`, deep, web; `search_flows`, web).
Inspected the returned screen images and all three preview images from the flow.
These are observed product patterns, not evidence of measured usability or a universal
industry standard. No product assets were copied.

| Reference | Observed pattern | Application |
| --- | --- | --- |
| [Linear issue detail](https://mobbin.com/screens/cef36326-d8ec-4c6f-acd4-a9f1e1060d33) | Task title dominates; properties and activity have lower visual weight. | One action title, inline owner, compact deal properties; remove KPI-sized metric cards. |
| [Linear issue detail flow](https://mobbin.com/flows/c3a5e094-420e-4732-bf9f-3c865dc8728f) | List → detail → expanded subissues; stable surrounding navigation. | Stable deal queue and tabs, optional disclosures for conditions and full proposal. |
| [Attio populated company record](https://mobbin.com/screens/d76ba56f-98c3-463f-9e1d-bbe4831ee47a) | Record identity, activity tabs and contextual properties are grouped predictably. | Deal identity above tabs; source records open in an inspector without losing the selected deal. |
| [Attio empty company record](https://mobbin.com/screens/cf4f2b49-652f-4c76-8a7c-1ea4f57c10cf) | Quiet canvas, compact property list. | Remove the permanent onboarding banner and decorative proof statistics. |

Also inspected [Linear's activity-scrolled state](https://mobbin.com/screens/9f60b2e0-f2e9-4c19-afcc-f85910b88182).
It repeats the same shell, not a separate pattern. The flow returned was **Issue details**,
not an overflow-menu flow; no claim that the tool supplied that requested pattern.
Earlier Mixpanel research remains in `UX_MIXPANEL_RESEARCH.md`; the purple palette and
light desktop shell are retained. Linear/Attio inform this density correction.

## Implementation inventory

- Queue: compact rows; refresh becomes an icon with accessible name and tooltip. Optional
  help replaces the permanent three-step banner. Methodology remains available.
- Deal header: one identity, rank and snapshot date; three short tabs.
- Overview: three metric cards become a single property strip. One primary CTA,
  **Siapkan tindak lanjut**, has a text label. Familiar utility controls use icons;
  unfamiliar business actions do not become unexplained symbols.
- Action: owner is inline; goal and visible condition precede preparation. The condition's
  full wording expands on demand. Complete recommendation remains in Rincian tindakan.
- Evidence entry: two compact links replace the large proof sidebar and its count KPIs.
- Re-analysis: optional Versi & analisis ulang groups provenance, versions and explicit
  request control. Pending/error feedback stays outside the closed disclosure.
- Reasons: no introductory hero/instruction paragraph; source previews are compact rows.
  Original customer quotes, historical decisions, paths, facts/inferences and limitations
  remain accessible. Critical constraints remain visible again in the preparation dialog.
- Source browser: source type, direct/inferred label, date, title and human conversation
  excerpt remain. JSON dumps and composite IDs are removed from list previews; original
  records, IDs, provenance and source search remain available in the inspector/search.
- Graph: compact segmented navigation and one visual solid/dashed/arrow legend. Original
  edges, direction, path highlighting, filters, bounded nodes and drill-down are unchanged.
- Plan: short heading and draft status, one copy action. Full action, approvals, unknowns
  and provenance remain in the copyable brief. It does not send messages or update CRM.
- Micro interactions: existing hover/selected/focus/pressed states, disclosure chevron,
  short transform-only transitions and reduced-motion handling; no new animation library.

## Business invariants

Gate labels translate exact API gate values, never deal IDs. Session recommendations
never inherit a priority gate label. Explicit approvals always produce a visible warning.
P01: decision-maker identity needs confirmation. P02: VP Sales decision/log required.
P03/P04: candidate consent unknown. P05: discovery needed, not a failed or risk-free deal.
Full negations/conditions are preserved in detail and plan. No automatic POST, changed
ranking, fabricated confidence, synthetic chart, new dependency or backend change.

## Verification (Main/Codex, 01:29 WIB)

- Build passed. 31 ESM checks + 47 compiled CJS checks = **78/78 passed**.
- HTTP tests use a separate explicitly rules-mode backend at port 8001, PID 40514.
  No Jev calls made for this redesign. Browser reads the existing API via Vite 5174.
- Browser: real app in the development viewport harness, **1280×720 and 1440×900**.
  Both had `scrollWidth === viewport width`. Default P04 CTA row bottom about 620 CSS px,
  visible without scrolling at both sizes. Harness border/caption is outside the app.
- All five deal action/gate states inspected. P02 warning disclosure retains the full
  VP Sales requirement. P04 plan retains unknown consent and full original action.
- Modal initial focus, Tab to close, Escape and return to preparation button verified.
- P02 original I0348 source → focused graph verified (3 actual nodes, 2 actual edges).
- Evidence search no-match → clear → restored results verified. List previews no longer
  show JSON objects. Full source still inspected through the record panel.
- Screenshots: `tests/screenshots/compact-desktop-1280.png`, `compact-desktop-1440.png`.
- Mobile, broad new browser error-state matrix, copy across external applications and
  human sales usability were not retested. Prior tests cover request/session errors.
  No claim of measured cognitive-load reduction, conversion improvement or contest result.

## Human acceptance check

Ask a teammate who did not implement the screen to identify the first deal, its next
step, its owner and unmet condition; then prepare the plan and find the original source.
Observe without explaining the interface. Record hesitation before claiming it is easy
for a first-time user. This short check remains outstanding.
