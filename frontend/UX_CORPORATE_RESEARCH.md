# Corporate desktop redesign — 10 October 2026

## Task and research method

Implement the supplied MerchantRail-style references: restrained dark corporate shell,
English controls, clear next action and subtle motion. Desktop is the target. Mobbin MCP
screen search was used with web/deep mode; four returned images were inspected. The
screens are design references, not evidence of measured usability or sales outcomes.

## Observed references

- [Linear dark issue list](https://mobbin.com/screens/e142df2a-3527-499c-8f81-1b715947ac0c):
  compact left navigation, quiet dark surfaces, thin row dividers, small status accents.
  Adapted to our existing five-deal priority queue and flat detail surface.
- [Linear light priority list](https://mobbin.com/screens/610d34b6-6ad8-45ab-80fb-2107b31ed01e):
  clear selected row and compact grouping. This screen is light, not a dark-theme reference.
- [Attio company detail](https://mobbin.com/screens/3f58982f-fb3f-46de-a123-70350ebfa604):
  identity, tabs and properties separated from the activity content; light theme.
- [Attio activity detail](https://mobbin.com/screens/070de66a-5dcc-4049-ae06-b0ff0babcdd4):
  activity timeline alongside record properties; adapted into source inspection on demand.

No brand assets, fabricated integrations or decorative analytics were copied. The user's
MerchantRail images guided dark color balance and flat hierarchy. Static Mobbin images do
not demonstrate motion; motion timings below are our implementation choices.

## Screen and flow decisions

1. **Queue → next step:** priority, company and stage/value remain compact. The action title,
   owner, target and visible gate lead to one primary button, Prepare follow-up.
2. **Plan:** English proposal, outcome and approval/consent conditions. Copy produces a
   working note, not an email, CRM update or proof of completion. Original analysis and
   source locators remain in an appendix.
3. **Evidence:** source rows and disclosures retain original quotations and IDs. Source
   inspector opens the original graph; direct/inferred meaning and arrow direction remain.
4. **Graph and methodology:** muted nodes, teal supporting paths, dashed amber inferred
   relationships. Methodology is retained here; its duplicate sidebar entry was removed.
5. **Errors/loading:** translated recovery controls; no automatic paid analysis request or
   fabricated success. Existing version switching and stale-request protections retained.

## Language and motion

English shell, controls, errors, stage labels and reviewed presentation translations for
all five initial recommendations. `englishText` is exact-string lookup, not deal-ID logic;
unknown service wording passes through unchanged. Original source text, methodology and
raw payloads remain in their source language to preserve auditability. This is not a
complete backend localization framework, and arbitrary Jev output may retain its language.

Queue hover 160–180 ms; tab/dialog entry 220 ms; inspector 240 ms; small icon movement and
pressed-button feedback. No initial opacity-zero content. Reduced-motion disables motion.
Keyboard focus, semantic tabs and native dialog are preserved.

## Verification and limits

- 80 frontend tests pass: 47 API/component, 31 existing module, 2 translation-integrity.
- Production TypeScript/Vite build passes. No backend, dataset or dependency changes.
- Browser: 1440×900 overview, evidence → I0335 → graph, retained methodology; 1280×720
  overview and P02 plan; no horizontal overflow at 1280, CTA bottom 626 px. Modal wraps
  keyboard focus in both directions; Escape restores Prepare follow-up focus.
- Screenshots in `tests/screenshots/corporate-*.png`.
- No paid Jev calls, mobile polish, human usability study or full accessibility audit.
  A cleaner hierarchy is a design hypothesis, not a measured improvement in closing rate.
