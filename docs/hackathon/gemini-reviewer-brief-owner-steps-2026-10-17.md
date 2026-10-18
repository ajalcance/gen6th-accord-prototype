# Reviewer brief on Gemini: owner steps

Date: 2026-10-17. Decision: [ADR-0074](../decisions/0074-advisory-reviewer-brief.md).

## Status

The code, tests and documentation are prepared. Backend tests, lint, strict typing and the coverage
guards pass locally. The frontend tests could not run where this was written and are left to CI.
Nothing is deployed, and no real Gemini call has been made. Until step 1 prints its success line,
the model identifier and the output shape are assumptions.

## What the feature does

On a saved performer version a button sends the name, biography, human contribution and AI
disclosure to Gemini on Vertex AI. The reply is a short summary, up to four gaps and up to four
neutral questions, shown with a fixed advisory notice. Nothing is stored. It approves, identifies
and decides nothing. It is off unless `PERSONA_ASSISTANT_ENABLED` is true.

## Steps, in order

All steps run in Cloud Shell for project `gen6th-accord-production`, signed in as the owner account.
Each script checks that account, is safe to run again and prints a marker line to paste back.

1. **Enable and test Gemini.** Run the enable script. It enables the Vertex AI API, grants the API
   service identity the Vertex AI user and service usage consumer roles, then sends the exact
   request the API will send. Success ends with `SMOKE_OK`. If the model is not found, run it again
   with a different model identifier in the `MODEL` variable.
2. **Build and deploy the API.** Upload the backend bundle, the new service definition and the API
   script, then run the script. Success shows health 200 and a brief route status of 401, which
   means the route exists and wants a session. It also prints two rollback commands.
3. **Build and deploy the frontend.** **On hold.** The passport booklet ships in the same deploy,
   see [the booklet plan](passport-booklet-plan-2026-10-17.md). Run this only when told the new
   bundle contains the booklet. Then upload the frontend bundle and its script and run it. Success
   shows home 200 and a brief route status of 401 through the frontend.
4. **Prove it in the browser.** Sign in, create or open a fictional performer, open the saved
   version and press the button. Capture the panel with the summary, the gaps, the questions and the
   notice. Also capture the sentence above the button that says what is sent and to whom.

## If something fails

- **Step 1 returns 403.** The API or role grant has not propagated yet. The script retries for
  about two minutes. Paste the printed response if it still fails.
- **Step 1 returns 404.** The model identifier is wrong for this project. Paste the response.
- **Step 2 build fails.** Paste the build log link and the last lines. Nothing was deployed.
- **The button shows the unavailable message.** Read the API logs for the incident line. It names
  the error type and never the record content.

## Roll back

Set `PERSONA_ASSISTANT_ENABLED=false` on the API service, or move traffic back to the previous
revision. Both commands are printed by the API script. The frontend panel stays visible but answers
that a brief is unavailable.

## What this does not claim

It does not show that the summaries are accurate, that the model resists every instruction hidden in
a field, or that the deployment limits hold across several instances. The record text does leave the
deployment for Google when the button is pressed. Do not describe this as verification or as an
approval step.
