# ADR-0029: Compact, evidence-focused persona console

**Status:** Proposed; owner authorized local implementation on 2026-10-02. PR/release review remains.
**Date:** 2026-10-02
**Builds on:** [ADR-0028](0028-persona-console-design-system.md).

## Context

Owner screenshots showed too much space devoted to headings, portraits and footer controls.
The owner approved a third pass across all five screens, a five-column gallery and a calmer
console for executive browsing. Visual credibility cannot establish security or connectivity.

## Decision

- Use productive typography: 24–28px page titles, 18px section headings, 14px working text
  and 12px metadata. Replace editorial headlines with explicit task titles.
- Use semantic density tokens for 36px desktop controls, a 48px header, 36px footer,
  20px panel padding and 6–8px radii. Mobile controls remain at least 44px tall.
- Keep the footer outside the scrolling workspace. Monitoring is an inline control with
  a focus indicator fitting the compact row. Remove slogans and idle pulsing; running
  simulations retain meaningful progress and reduced-motion support.
- Put sidebar collapse beside the logo. Preserve accessible navigation names in the icon
  rail; remove promotional copy from the bottom area. Connection details open local readiness.
- Size the gallery from its workspace container, including space recovered by sidebar collapse:
  one column below 480px, two at 480px, three at 720px, four at 940px and five at 1140px.
  Preserve the three original fixtures; column count does not fabricate records.
- Reduce preview emphasis, gaps and decoration across creation, analysis, campaign and public
  projection. Keep evidence, exact version, blockers and decisions prominent.
  Biography/contribution share two columns with full-width name/disclosure; mobile stacks them.
- Gallery cards use small names, restrained status badges and an inline Open record/arrow action,
  without badge piles, large arrow buttons or repeated studio labels. Badges stay visible; the
  card stays keyboard operable. Pending-review and passport context share two columns at 720px.
- Progressive disclosure applies to secondary controls: gallery actions reveal on hover/focus
  and remain visible on touch; demo failure exercises use native expandable details. Required
  confirmations and primary decisions remain visible. No action depends on hover alone.
- Security readiness distinguishes local UI presence, disconnected identity/monitoring and
  unavailable signing. No breach verdict, live threat feed or health polling is implied.

## Rationale and alternatives

Productive type and consistent grouping support scanning and task execution. Hero headings
and image-heavy cards were rejected for this console. Shrinking every control was rejected
because touch/keyboard operation needs usable targets and visible focus. Five columns at
every viewport were rejected because cards would become unreadable.

Sources: [Carbon productive typography](https://carbondesignsystem.com/elements/typography/type-sets/),
[W3C target sizing](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
[W3C contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[NN/G credibility research](https://www.nngroup.com/articles/trustworthy-design/).
These inform the design; the measurements still need browser validation.

## Consequences and verification

No dependency, model, route, identity, deployment or publication activation. Fixture invalidation,
private-note exclusion and unsigned export boundaries remain. DOM tests cover navigation,
modal focus and anchored-footer structure; they do not measure CSS geometry. Browser review
must cover all five screens, sidebar states, narrow widths, zoom, focus clipping and reduced
motion. See [console review](../hackathon/h1-console-review.md). Commercial release still requires
live integration, measured accessibility/performance and full gates.
