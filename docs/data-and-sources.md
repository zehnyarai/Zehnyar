# Data coverage and source register

Verification date for the whole dataset: **2026-10-25** (مهر ۱۴۰۵).

## 1. Countries and official authorities

| Country | Authority | Official portal | Routes |
|---|---|---|---|
| کانادا / Canada | IRCC | canada.ca/en/immigration-refugees-citizenship | 5 (FSW, PNP, study, start-up, work permit) |
| استرالیا / Australia | Department of Home Affairs | immi.homeaffairs.gov.au | 5 (189, 190, 491, 482, student) |
| بریتانیا / United Kingdom | Home Office | gov.uk/browse/visas-immigration | 5 (Skilled Worker, Global Talent, student, Innovator, HPI) |
| آلمان / Germany | BAMF | make-it-in-germany.com | 5 (Blue Card, Opportunity Card, job seeker, student, self-employment) |
| آمریکا / United States | USCIS | uscis.gov | 5 (EB-1A, EB-2 NIW, H-1B, EB-5, F-1) |
| هلند / Netherlands | IND | ind.nl/en | 5 (HSM, Blue Card, orientation year, student, startup) |
| نیوزیلند / New Zealand | Immigration NZ | immigration.govt.nz | 4 (SMC, AEWV, student, investor) |
| فرانسه / France | Ministry of the Interior | service-public.fr | 3 (Talent Passport, student, business creation) |
| ایتالیا / Italy | Ministry of the Interior | vistoperitalia.esteri.it | 3 (Blue Card, digital nomad, student) |
| اسپانیا / Spain | Ministry of Inclusion | inclusion.gob.es | 3 (digital nomad, highly qualified, student) |
| سوئد / Sweden | Migrationsverket | migrationsverket.se | 3 (work, student, researcher) |
| دانمارک / Denmark | SIRI | nyidanmark.dk | 3 (pay limit, positive list, student) |
| ترکیه / Turkey | Presidency of Migration Management | en.goc.gov.tr | 3 (work, investment, student) |
| امارات / UAE | ICP | u.ae visa and Emirates ID | 3 (Golden Visa, employment, virtual work) |
| عمان / Oman | Ministry of Labour / ROP | rop.gov.om | 3 (employment, investor, student) |

**Total: 15 countries, 58 visa routes.**

## 2. Visa type coverage

`skilled` · `work` · `study` · `startup` · `business` · `investment` ·
`digitalnomad` · `talent` · `jobseeker` — all nine requested categories exist in
the dataset and are filterable in the app.

## 3. Verified 2026 figures used in scoring

### Canada (IRCC, fee list effective 30 April 2026)
- Economic-class principal applicant: **CAD 990**; RPRF **CAD 600**; child **CAD 270**; biometrics **CAD 85** (family cap CAD 170).
- Express Entry proof of funds (updated 7 July 2025): 1 → **CAD 15,263**, 2 → 19,001, 3 → 23,360, 4 → **28,362**, 5 → 32,168, 6 → 36,280, 7 → 40,392, each extra +4,112.
- FSW grid pass mark **67/100**; minimum CLB 7 in all four skills; one year of continuous TEER 0–3 experience.

### Australia (Home Affairs pricing from 1 July 2026)
- Subclass 189 **AUD 6,135**; 190 and 491 **AUD 6,140**; additional adult **AUD 3,070**; child **AUD 1,540**.
- Points test minimum **65**; age ceiling under 45 at invitation; competent English CLB 6.
- 2026–27 planning levels: 189 → 21,090 places, 190 → 35,500, regional → 14,110 (context for `selectivity`).

### United Kingdom (Home Office 2026)
- Skilled Worker general threshold **GBP 41,700** (new entrant 33,400, STEM PhD 33,400, non-STEM PhD 37,500, ISL 33,400, health/education 25,000).
- Fees: **GBP 819** up to 3 years, **1,618** over 3 years outside the UK; IHS **1,035/year** adult, 776/year under 18; CoS **525** (employer); Immigration Skills Charge 1,320/year (employer).
- English requirement rose to B2 on 8 January 2026. Global Talent, HPI and Innovator Founder fees per current schedule.

### Germany (BMI notice, 18 December 2025 — in force 1 January 2026)
- EU Blue Card standard **EUR 50,700**; reduced (shortage occupations, recent graduates, IT specialists without a degree) **EUR 45,934.20** (3,827.85/month).
- Opportunity Card grid: **6 points** minimum.

### Netherlands (IND, 1 January 2026)
- Highly skilled migrant, 30+: **EUR 5,942/month**; under 30: **4,357**; reduced criterion: **3,122**.
- EU Blue Card: **5,942**; reduced **4,754**. 30% ruling unchanged in 2026, dropping to 27% for new rulings from 2027.

### Other destinations
Figures flagged `verified: false` in the dataset are indicative and displayed as
"تقریبی / indicative" in the app (for example German blocked account,
Swedish and Danish application fees, UAE and Oman permit fees). They are still
bounded by the published 2026 ranges, but must be confirmed on the portal.

## 4. Occupations

`shared/dataset.json → occupations` holds 50 curated occupations with Canadian
**NOC 2021** code, **TEER** level, Australian **ANZSCO** code, bilingual titles and
a demand list per destination. Codes are indicative; the app shows them as
identifiers so an applicant can confirm against the official NOC/ANZSCO editions
before filing.

## 5. Maintenance procedure

1. Update the relevant figure in `tools/countries_a.py` or `tools/countries_b.py`.
2. Set `verified: true` only when the number comes from the official fee list or
   regulation for the current year.
3. Run `python3 tools/build_dataset.py` — it validates rule kinds, currencies,
   pass marks, duplicate ids and Persian copy purity.
4. Run `node tools/sync_mobile_data.js`, `python3 tools/make_fixtures.py`,
   `node tools/parity_check.js`, `node tools/check_i18n.js`.
5. Update `LAST_VERIFIED` in `tools/dataset_lib.py` and the date shown in the app
   dictionary (`home.verifiedValue`), then commit the regenerated dataset.
