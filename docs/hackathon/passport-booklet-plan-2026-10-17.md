# Passport booklet and submission plan

Date: 2026-10-17. Status: plan and paper mock approved by the owner. Source is prepared under ADR-0075;
566 frontend tests/types/lint/build pass on Node24; Node22/render/print/cloud/live proof remains open.
Hackathon deadline: 2026-10-18. Related: [reviewer brief owner steps](gemini-reviewer-brief-owner-steps-2026-10-17.md).

## The feature

On the Passports page of a saved performer, a **View passport** button opens a booklet drawn in the browser from that performer's
real records, in the visual style the owner approved (two facing pages, portrait, seal, QR). Left page: portrait, persona name, passport
reference, signing key, date of issue, issuing authority. Right page: approved references, creation evidence, recorded permissions,
signature seal and QR code. The button sits above the production-offer list in `frontend/app/passport/saved-passports.tsx`, so it works for
a performer with no offer yet.

The visual reference is a picture kept outside the repository. The build session receives it with the handoff. The booklet is built from
text and SVG, not from the picture.

## Rules

- It displays records only. No new data, claim or route.
- Two states. **Registered preview**: dashed seal, no QR, the line "Registration record, not yet signed". **Issued**: seal and QR only
  when a signed package and a public share link exist.
- The seal says "digitally signed", so it never appears on an unsigned record.
- A visible line states that it is an Accord record and not a government document.
- Current permission is shown live and separately from the signature.
- System serif and monospace fonts only, because the content security policy allows no web fonts.
- Real text and SVG, with a portrait alt text, a print stylesheet and a stacked layout on narrow screens.

## Field mapping

| Field | Source | Ready now |
|---|---|---|
| Persona name | Saved version | Yes |
| Portrait | Approved portrait through the existing authorised thumbnail | Yes |
| Passport reference | Derived from the production offer or publication id (decision A) | Derived, not stored |
| Signing key | Tail of the key version in the signed package (decision B) | After issuance |
| Date of issue | Issued time in the package | After issuance |
| Issuing authority | Constant plus the disclaimer | Yes |
| Approved references | Reference list in the package, else the approved portrait | Yes |
| Creation evidence | Human contribution and AI disclosure on the version | Yes |
| Recorded permissions | Production scope: assets, recipient, purpose, dates | When an offer exists |
| Seal and QR | Signed package and the QR helper in `frontend/lib/passport-qr.ts` on the public share link | After signing is live |
| Machine line | Accord-specific, from real fields, hidden from screen readers (decision C) | Yes |

Until Cloud KMS signing is deployed, the live site can show only the registered preview.

## Decisions (approved)

| | Decision |
|---|---|
| A | The passport number is a **passport reference** derived from the offer or publication id. No sequential registry number. |
| B | The key line shows the key version tail. A real SHA-256 fingerprint needs a backend addition and is later work. |
| C | Keep the machine line as an Accord-specific line, not the international passport format. |
| D | The button shows for a performer with no approved portrait, with an empty frame and "Portrait not approved". |
| E | The booklet on the public page `/p/...` comes later. |
| F | The frontend rebuild step in the owner steps is held until the booklet is ready, so the brief and the booklet ship in one deploy. |
| G | Withdrawn on 2026-10-17. The owner decided that everything the pitch shows will be built, so the real packaged scanner is repaired and shipped as part of the wider plan. |
| H | ADR-0074 stays with the reviewer brief. The booklet ADR is 0075. The unmerged scanner ADRs in the owner's checkout renumber when they land. |

## Priorities

The booklet is one track of a wider plan. On 2026-10-17 the owner decided that everything the pitch deck shows will be built and deployed: the reviewer
brief, the booklet, the repaired packaged scanner, the Google runtime (Vision, embeddings, Cloud Tasks and a reference worker, Cloud KMS), signed passports,
evidence upload and claims, Gemini image comparison, and a calibration run for Appearance check. One orchestrating session splits that work across agents.
The pitch deck only shows an item as Deployed once its evidence exists on the live service.

Inside the booklet track: the registered preview comes first. The issued state needs the signing path from the wider plan. The booklet on the public page,
a downloadable image or PDF, and a signed release remain later work.

## Sequence

Order for the booklet: a standalone HTML design mock for owner approval, then the component and tests, then a local branch and an updated frontend demo
bundle, then one frontend deploy that carries the brief and the booklet. The mock comes first because the authoring environment has no Node and no
browser, so it is the fastest way to approve the look. The owner owns the schedule.

## After approval

One short ADR for the booklet (display only, two states, derived fields, honesty rules), then the usual records: current state, plan,
lessons and changelog.
