# Visayar assessment engine — specification

The engine is **data-driven**: `shared/dataset.json` describes every route as a
list of scoring criteria and eligibility gates, and both implementations
(Python: `backend/app/engine/engine.py`, JavaScript: `mobile/src/core/engine.js`)
evaluate the same rules. A change to a country's rules never requires a code change.

## 1. Profile

| Field | Type | Notes |
|---|---|---|
| `age` | int | Age at the date of application |
| `maritalStatus` | enum | `single`, `married`, `divorced`, `widowed` |
| `spouse` | object | `educationId`, `languageClb`, `workYears` |
| `educationId` | enum | Reference to `educationLevels[].id` |
| `educationStem` | bool | STEM/engineering flag |
| `languages` | array | `{testId, skills:{listening,reading,writing,speaking,overall}, cefr}` |
| `work` | object | `totalYears`, `overseasYears`, `inCountryYears`, `occupationCode`, `jobOffer`, `salaryAnnualLocal`, `salaryCurrency`, `licensing` |
| `funds` | object | `availableUsd`, `cashUsd`, `assetsUsd` |
| `adaptability` | object | `relativeInCountry`, `priorStudyInCountry`, `priorWorkInCountry`, `eca` |
| `goal` | enum | `work`, `study`, `startup`, `investment`, `selfsponsored` |
| `familySize` | int | 1–9, drives settlement-fund thresholds |
| `investmentUsd`, `remoteIncomeUsd` | number | Investment and digital-nomad routes |
| `startupBacking`, `studyOffer`, `achievement`, `nomination`, `recentGraduate` | bool | Evidence flags |

## 2. Language normalisation

Every test declares per-skill thresholds `[minRawScore, clb]` in
`dataset.languageTests`. Raw scores are mapped to CLB, then CLB to CEFR:

```
CLB 10+ → C2 · CLB 9 → C1 · CLB 7–8 → B2 · CLB 5–6 → B1 · CLB 3–4 → A2 · CLB 0–2 → A1
```

* `kind: "band"` — four skills; route scores each skill separately.
* `kind: "cefr"` (Goethe/telc) — the certificate level maps to a single CLB.
* `overallOnly: true` (Duolingo) — one score applies to all four skills.
* If several certificates exist for one language group, the engine uses the one
  with the highest **minimum** skill CLB (most conservative, no cherry-picking).

## 3. Rule kinds

| Kind | Evaluation |
|---|---|
| `age_band` | `[[minAge, maxAge, points]]`; first matching band wins |
| `education_rank` | maps `educationId → points` via the education level rank |
| `language_skills` | per-skill band points summed, then capped by `cap` |
| `language_best` | band points evaluated against the certificate's minimum CLB |
| `experience_band` | `scope` ∈ `any`/`overseas`/`inCountry`, optional `teer` filter |
| `flag` | full `points` when the named boolean profile flag is true |
| `salary_band` | band points against the annual salary converted to USD |
| `numeric_band` | band points against `investmentUsd` or `remoteIncomeUsd` |
| `funds_ratio` | `points × min(1, availableUsd / settlementUsd / scale)` |
| `adaptability` | `each` points per true factor, capped |
| `spouse` | summed spouse points (language/education/work), capped |

Bands are always declared **descending by floor** and evaluated as
"highest floor that is ≤ value" — implemented identically in both engines.

## 4. Gates

A gate either passes or produces a blocker. `advisory: true` produces a warning
that does not block the route.

| Gate | Passes when |
|---|---|
| `age_gate` | `age <= max` |
| `language_gate` | certificate exists and minimum skill CLB ≥ `minClb` |
| `experience_gate` | total years ≥ `minYears` and (if `teer`) occupation TEER in list |
| `points_gate` | scored total ≥ `min` (or `scale`-adjusted) |
| `funds_gate` | `funds.availableUsd` ≥ route settlement requirement |
| `education_gate` | education rank ≥ `minRank` (IT-experience override allowed) |
| `flag_gate` | named boolean flag is true |
| `salary_gate` | converted salary ≥ threshold; supports `under30Min`, `reducedMin` (shortage occupation), `shortageMin`, `newEntrantMin`, `monthly`, `hourly` |
| `investment_gate` | `investmentUsd` ≥ converted minimum |
| `remote_income_gate` | `remoteIncomeUsd` ≥ monthly minimum |
| `custom_points` | `chancenkarte` or `nz_smc` grid ≥ `min` |

Reading a gate with no data (for example a salary gate with an empty salary) fails
with a dedicated message asking the user to fill the field, instead of silently
awarding a pass.

## 5. Scoring and chance

```
achieved  = Σ min(criterion_points, criterion.max)
readiness = 100 × achieved / maxPoints
blockers  = gates without advisory that failed
```

```
if blockers:  chance = 5 + 26 × (achieved/maxPoints) × max(0.35, 1 − 0.12 × min(n,4))
else:         chance = 100 × (achieved/maxPoints) × (0.62 + 0.38 × selectivity)
              if achieved < passMark: chance ×= 0.72
chance ← clamp(chance, 3, 96), rounded to 1 decimal
```

Characteristics: monotonic in every scoreable input, bounded, never 100%, and
explicitly reduced when a hard eligibility condition is unmet.

## 6. Roadmap

For the best route, each criterion with a gap ≥ 1 point becomes an action with
`gain`, `effort` (`locked` for age, `hard` for education/experience, `medium` for
language/funds/adaptability) and `priority` 1 for blockers, 2 otherwise. Items are
sorted by priority then by gain, and the top six are shown.

## 7. Parity and regression safety

* `tools/make_fixtures.py` runs six representative profiles through the Python
  engine and stores every route's `chance`, `readiness`, `achieved`, eligibility and
  blocker list in `shared/engine-fixtures.json`.
* `tools/parity_check.js` re-runs the same profiles through the JavaScript engine
  and asserts equality within 0.25 points, including identical blocker sets.
  Current status: 1482 checks, 0 mismatches.
* `tools/build_dataset.py` refuses to emit a dataset with unknown rule kinds,
  duplicated visa ids, `passMark > maxPoints`, unknown currencies, or Latin
  characters in Persian copy.
