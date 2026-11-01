# Submission kit — Make "Scenario of the Month" (English, paste-ready)

Fill-in-the-blank copy for the [submission form](https://tally.so/r/MePybX). Replace anything in `{braces}`.
Keep the "why it should win" answer **short, specific, and numeric** — judges read dozens of these.

---

## 0. Scenario name (as it appears on the public page)

> **Visa Policy Change Radar — automated monitoring for 58 visa routes (Visayar)**

Alternative (shorter): `Visa Policy Change Radar`

---

## 1. Public scenario page description (1–3 lines, shown on the Share page)

> Monitors 58 official visa-route pages across 15 countries, detects real changes with a cheap hash diff, and uses AI only to *propose* the changed facts — then routes them to a GitHub issue, a Telegram summary and a review log. **A human approves; nothing is published automatically.**

---

## 2. "Why it should win" — the form field

### Option A — short (≈70 words, recommended)

> Real problem: Visayar (an immigration-assessment app) tracks 58 visa routes across 15 countries, and its rules go stale because every figure has to be re-checked by hand each month. This scenario turns that manual grind into a 2-minute review: it hashes each official source page, spends AI tokens only when something actually changed, extracts a structured before/after with the source and effective date, and opens a labelled GitHub issue plus a Telegram digest. The human still decides — the automation only proposes.

### Option B — medium (≈130 words)

> **Utility.** Visayar is a live product that assesses immigration routes for 58 visa paths across 15 countries. Data staleness is its biggest risk: fees, points thresholds and occupation lists change quietly, and today a person re-opens every official page every month. This scenario automates the *monitoring*, not the *judging*: it fetches each official source, fingerprints the text, and only when the fingerprint changes does it call an AI model to return a structured diff (field, before, after, effective date, exact quote). Thirty-eight pages that didn't change cost almost nothing.
>
> **Creativity.** Most "AI watches the web" builds stop at a notification, or worse, let the model rewrite the data. Here the AI is deliberately demoted to a proposer: output goes to a GitHub issue with a `data-review` label, a Telegram digest and a review log, and a human gate must approve before any dataset change ships. Cheap diff first, expensive reasoning second, human decision last — that ordering is the idea worth copying.

### Option C — one-liner (for social posts / LinkedIn)

> Hashing 58 government pages first and calling the AI second makes monthly visa-policy review a 2-minute job instead of a manual crawl — and a human still signs off on every change.

---

## 3. Numbers to quote (use the real ones from your run)

| Metric | Value |
|---|---|
| Routes monitored | 58 |
| Countries | 15 |
| Manual review before | {e.g. 4–6 hours / month} |
| Review after | {e.g. 12 minutes} |
| AI calls per month (after hashing) | {e.g. 2 of 58 pages changed} |
| Human approval gate | 1 (required) |

Validate these with an actual run before submitting — never quote a number you did not measure.

---

## 4. Demo video script (60–90 s)

| Time | Shot |
|---|---|
| 0–10 s | The problem: 58 routes, monthly manual re-check, stale data risk |
| 10–25 s | The scenario canvas, modules named in plain language |
| 25–45 s | Run: pages fetched, 56 unchanged (filtered out), 2 flagged |
| 45–65 s | AI diff output + the GitHub issue it created (show the real issue) |
| 65–80 s | Telegram digest + the human approval step |
| 80–90 s | Closed loop: approved change → dataset update → CI green |

Blur emails, tokens, phone numbers and channel IDs.

---

## 5. Pre-submit security pass

- [ ] No API keys, tokens or webhook URLs hard-coded in any module
- [ ] Public Share page reviewed in an incognito window
- [ ] Screenshots/video free of personal data
- [ ] Test data removed or clearly labelled as sample data
- [ ] Scheduling left sensible for anyone who copies the scenario

---

## 6. Social post draft

> Most "AI watches the web" automations fire a notification and stop — or let the model rewrite the data.
>
> I flipped the order for our immigration app: hash the 58 official visa pages first, call the AI only on the ones that changed, and make a human approve every diff before it touches the dataset.
>
> Result: monthly policy review went from a manual crawl to a 12-minute review with a source and an effective date attached to every change.
>
> Built in @Make_hq. Scenario: {public link} #Make #Automation #ScenarioOfTheMonth

---

## 7. If you're submitting as a Scout instead

- Pick a scenario from community.make.com that is genuinely useful and *under-exposed* (few likes, strong build).
- Ask the creator for permission before nominating.
- Fill the creator's email in the form as well as your own.
- Skip anything already featured by Make — judges have seen it.
