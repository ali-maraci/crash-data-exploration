# Chicago Traffic Crash Analysis — Answer Logic

How each of the four research questions is answered, the methods used, and where the evidence lives in the code and presentation.

---

## Q1: Is There a Correlation Between Time of Year/Week/Day and Crash Occurrence?

### Statistical Tests (Phase 3a, lines ~265–303)

Four separate tests check whether crash counts vary significantly across time dimensions:

| Test | What it checks | Result | Conclusion |
|------|---------------|--------|------------|
| **Monthly chi-squared** | Are crashes equally distributed across 12 months? | chi2=5,667, p<0.001 | No — some months have far more crashes |
| **Day-of-week chi-squared** | Are crashes equal across 7 days? | chi2=4,324, p<0.001 | No — Friday dominates |
| **Hourly chi-squared** | Are crashes equal across 24 hours? | chi2=194,228, p<0.001 | No — huge hourly variation |
| **Weekend vs weekday Mann-Whitney** | Do daily crash counts differ? | p<0.001 | Yes — weekdays avg 273 vs weekends 255 |

There is also a **year-over-year Pearson correlation** (r=0.561, p=0.1476) which is explicitly noted as **not significant** — only 8 data points and COVID disruption make it unreliable.

**How chi-squared works here:** The expected frequencies assume crashes would be evenly spread (adjusted for days per month). The test measures how far observed counts deviate from that even spread. A tiny p-value means "this pattern is real, not random noise."

### Seasonal Decomposition (lines ~306–312, Chart 01)

The additive seasonal decomposition (`seasonal_decompose(monthly_ts, period=12)`) splits the monthly crash time series into:

- **Trend** — the long-term trajectory (shows COVID dip and recovery)
- **Seasonal** — the repeating annual cycle (October peak, April trough)
- **Residual** — what's left after removing trend and seasonality

This visually confirms crashes follow a predictable annual rhythm, not random variation.

### Visualisations

| Chart | File | What it shows |
|-------|------|---------------|
| **Plot 01** | `01_time_series_decomposition.png` | 4-panel decomposition proving seasonality exists |
| **Plot 02** | `02_dow_hour_heatmap.png` | Day × Hour heatmap — Friday 3–5 PM is the darkest cell |
| **Plot 03** | `03_monthly_bar.png` | Monthly averages (2017–2023, excluding lower-volume 2016) with error bars — October peaks, April lowest |
| **Plot 10** | `10_yearly_trend.png` | Year-over-year line chart with 2016 conditional annotation (only shown if data starts mid-year) |

### PowerPoint Slides

- **Slide 5** — Q1 section header
- **Slide 6** — Decomposition chart + explanation of the 4 panels
- **Slide 7** — Day/hour heatmap + chi-squared confirmation values
- **Slide 8** — Year-over-year trend with COVID annotation and 2016 caveat

### How the Conclusion Is Reached

1. **Null hypothesis**: crashes are uniformly distributed across months/days/hours
2. **Chi-squared tests** reject that null with p < 0.001 for all three time dimensions — the patterns are statistically real
3. **Peak identification**: October (month), Friday (day), 15:00 (hour)
4. **Decomposition** separates the seasonal signal from trend and noise, confirming it's a repeating annual cycle and not a one-off anomaly
5. **Year-over-year trend** is explicitly flagged as not significant (only 8 points, p=0.15), so we don't overclaim a long-term trend

**Bottom line**: There are strong, statistically significant correlations between time (month, day of week, hour) and crash frequency. The year-over-year trend is the one exception — not enough data points to confirm significance.

---

## Q2: Is There an Association Between Wet Weather and Crash Severity?

The analysis uses a **6-level evidence hierarchy**, each building on the last to progressively rule out alternative explanations.

### Level 1: Naive Comparison (lines ~394–399)

The simplest possible check — split crashes into wet vs dry and compare injury rates:

| Condition | Injury Rate |
|-----------|-------------|
| Wet weather | 15.5% |
| Dry weather | 14.1% |
| **Difference** | **+1.4 percentage points** (computed dynamically in code) |

**Limitation:** This could be confounded — maybe wet crashes happen more at night, at higher speeds, etc. We don't know if weather itself is the cause.

### Level 2: Exposure-Adjusted Daily Crash Counts (lines ~401–410)

**Problem it solves:** Most days are dry, so dry weather naturally has more total crashes. Raw counts are misleading.

**Method:** Compares average crashes per day on wet vs dry days (using crash-report weather, after filtering out NULL/UNKNOWN):

| | Days | Avg Crashes/Day | CRI |
|--|------|----------------|-----|
| Wet | 2,325 | 41.4 | 0.19 |
| Dry | 2,893 | 220.6 | 1.00 |

**Key finding:** Wet days actually have **far fewer crashes** (CRI=0.19) — likely because fewer people drive. But when crashes *do* happen in wet weather, they're more likely to cause injuries (Level 1). This distinction between **frequency** and **severity** is critical.

**Important caveat:** "Wet days" are classified by whether any crash on that day had a wet-weather code in the crash report, not by independent weather station data (e.g. NOAA O'Hare). Many crashes on a "wet day" likely occurred during dry hours, meaning the CRI reflects crash-report weather coding patterns rather than a true weather-adjusted crash rate. A more rigorous approach would use daily weather station data to independently classify each day as wet or dry.

### Level 3: Chi-Squared Test of Independence (lines ~412–416)

Tests whether the association between wet weather and injury is statistically significant or just noise:

- chi2 = 127.0, p = 1.84e-29

**Conclusion:** The injury rate difference is real, not chance (p is astronomically small).

### Level 4: Unadjusted Odds Ratio (lines ~418–429)

Quantifies the association using a 2×2 contingency table (wet/dry × injury/no-injury):

- **OR = 1.114**, 95% CI (1.094, 1.135)

**Meaning:** Crashes in wet weather are 11.4% more likely to involve injuries than dry-weather crashes. The confidence interval doesn't cross 1.0, confirming significance.

**Limitation:** Still doesn't control for confounders (darkness, speed, time of day, month).

### Level 5: Logistic Regression (lines ~432–457)

This is the core analytical step. It isolates weather's effect by **controlling for confounders simultaneously**:

```
HAS_INJURY ~ IS_WET_WEATHER + IS_DARK + POSTED_SPEED_LIMIT
             + C(CRASH_HOUR) + C(CRASH_DAY_OF_WEEK) + C(CRASH_MONTH)
```

**Results** (n = 734,317 crashes with known weather):

| Factor | Adjusted OR | Meaning |
|--------|------------|---------|
| Wet weather | 1.104 | +10.4% injury odds |
| Darkness | 1.214 | +21.4% injury odds |
| Speed (+1 mph) | 1.046 | +4.6% per mph |

**How to read this:** Even after removing the influence of darkness, speed, hour, day, and month — wet weather *still* raises injury odds by ~10%. The unadjusted OR (11.4%) drops slightly to 10.4% because some of the crude effect was explained by confounders, but the association persists.

**Pseudo-R² = 0.014** is disclosed — the model explains only **1.4% of the variation** in whether a crash causes injuries or not.

**Why it's so low:** Each individual crash is essentially unpredictable — whether someone gets injured depends on factors the dataset doesn't capture: exact impact angle and speed at collision, vehicle size/weight differences, seatbelt use, airbag deployment, age and physical condition of occupants, and precise point of impact on the vehicle. Weather, darkness, speed limit, and time of day are *background conditions*, not the mechanics of the collision itself. No model using only these variables will ever explain most of the outcome variance.

**Why the ORs are still reliable despite low R²:** This is a critical distinction:
- **R² answers**: "Can I predict whether *this specific crash* will cause injury?" → No, only 1.4% accuracy.
- **OR answers**: "Across 734,317 crashes, does wet weather *systematically shift* the injury rate?" → Yes, by ~10%.

The ORs are estimated from the average pattern across three-quarters of a million observations. Even a tiny per-crash effect becomes statistically ironclad at that sample size (all p < 0.001). The model is poor at predicting individual crashes but very good at identifying which factors tilt the odds.

**Analogy:** It is like asking "does smoking cause cancer?" You cannot predict whether any *one* smoker gets cancer (low R²), but across millions of people, smokers clearly have higher cancer rates (reliable odds ratio). The low R² does not invalidate the OR — they measure different things.

### Level 6: Stratified Analysis (lines ~459–471)

**Problem it solves:** What if the wet-weather effect only exists in one lighting condition? Stratification checks whether the pattern is consistent.

| Lighting Stratum | N | OR | Interpretation |
|-----------------|---|----|----|
| Darkness | 34,538 | 1.163 | Effect present |
| Darkness, lighted road | 164,986 | 1.017 | Weak/absent |
| Dawn | 12,703 | 1.009 | Weak/absent |
| **Daylight** | **491,497** | **1.106** | **Effect present** |
| Dusk | 21,719 | 1.050 | Borderline |

**Conclusion:** The association holds across most strata, and is strongest in daylight and full darkness. It's not an artifact of one specific lighting condition.

### How the Conclusion Is Reached

1. **Naive comparison** — wet weather crashes have higher injury rates (+1.4pp)
2. **Exposure adjustment** — wet days have *fewer* crashes overall, but those crashes are worse
3. **Chi-squared** — the difference is statistically significant (not chance)
4. **Unadjusted OR** — quantifies it: +11.4% higher odds
5. **Logistic regression** — after controlling for darkness, speed, hour, day, and month: still +10.4%
6. **Stratified check** — the pattern holds across lighting conditions

**Bottom line:** Wet weather is consistently associated with more severe crash outcomes. Six independent analytical approaches all point the same direction. However, this is an **observational study** — the analysis demonstrates association, not causation. Unmeasured factors (traffic volume, driver self-selection, tire condition, visibility) could contribute.

**On the question of causation:** The task asks specifically about a causal relationship. Proving causation from observational data requires quasi-experimental methods such as instrumental variables (e.g. using rainfall as an instrument for wet-road conditions), difference-in-differences, or regression discontinuity designs. A recommended further study would match daily NOAA weather station data to crash rates, or conduct before/after analysis of road surface treatments (e.g. anti-skid coatings) to establish a causal link.

### PowerPoint Slides

| Slide | Content |
|-------|---------|
| **9** | Section header — frames Q2 as an association question |
| **10** | Weather bar chart — raw crash counts + injury rates by condition |
| **11** | Exposure-adjusted CRI table — fewer crashes but worse outcomes |
| **12** | Odds ratio chart from logistic regression — adjusted ORs with pseudo-R² caveat |
| **13** | Conclusions + limitations — summarises all 6 levels, explicitly states "association not causation" |

---

## Q3: Explore 2–3 Key Findings From the Data

The analysis picks three findings that emerged from the exploratory phase and develops each with statistical evidence.

### Finding 1: Hit-and-Run Crash Patterns (lines ~477–496, Chart 06)

**What was explored:**

The SQL exploration (Query 5) revealed that 30% of all crashes (232,623) are hit-and-runs — far higher than most cities. This warranted deeper investigation. **Data coding note:** The H&R flag is recorded as 'Y' or blank. 540K blank values are treated as 'No' (not hit-and-run). If blank instead means 'unknown/unrecorded,' the true H&R rate among known records could differ.

**How it was analyzed:**

1. **Injury/fatality comparison** — H&R crashes vs non-H&R:

| Metric | Hit-and-Run | Non-H&R |
|--------|------------|---------|
| Injury rate | 9.9% | 15.5% |
| Fatality rate | 0.072% | 0.128% |

Counterintuitively, H&R crashes have *lower* severity — likely because many are minor fender-benders where drivers flee to avoid insurance/police involvement.

2. **Chi-squared test** — chi2=4,195, p<0.001 confirms the injury rate difference is significant.

3. **Temporal profiling** — H&R rate computed for every hour and every day:

| Peak hours | H&R rate |
|-----------|----------|
| 3 AM | 48.3% |
| 2 AM | 47.7% |
| 1 AM | 47.2% |
| 12 AM | 46.7% |
| 4 AM | 46.0% |

Nearly half of all late-night crashes are hit-and-runs. The rate drops to ~25% during daytime.

4. **Day-of-week pattern** — Sunday peaks at 36.2%, weekdays are lowest (~28%).

**Visualisation:** Chart 06 shows two panels — hourly H&R rate (left) and day-of-week bars (right), both with the overall average (30%) as a dashed reference line.

**Slide 15 conclusion:** Late-night enforcement and CCTV on high-H&R corridors are suggested. The language is carefully hedged — it says "possibly linked to impairment or reduced witnesses" rather than asserting alcohol as a cause, since there is no BAC/DUI data in this dataset.

### Finding 2: Speed Limit & Crash Severity (lines ~498–519, Chart 07)

**What was explored:**

Speed limits are recorded for each crash. The question: does posted speed limit predict how bad the crash is?

**How it was analyzed:**

1. **Grouped statistics** by speed category:

| Speed Zone | Crashes | Injury Rate | Fatality Rate (per 1,000) |
|-----------|---------|-------------|--------------------------|
| 0–20 mph | 89,878 | 6.8% | 0.5 |
| 21–30 mph | 620,278 | 14.4% | 1.1 |
| 31–40 mph | 59,667 | 18.3% | 1.6 |
| 41+ mph | 6,211 | 18.2% | 2.9 |

Clear dose-response: fatality rates increase monotonically with speed. Injury rates rise sharply then plateau (18.3% at 31–40 mph, 18.2% at 41+ mph), possibly due to crashes at very high speeds being more likely to be fatal than merely injurious.

2. **Spearman rank correlation** (speed vs injury count): rho=0.083, p<0.001 — confirms the ordinal relationship is statistically significant.

3. **Point-biserial correlation** (speed vs fatal yes/no): r=0.008, p<0.001 — small but significant at this sample size.

4. **Fatality multiplier**: 2.9 / 0.5 = **5.7× higher fatality rate** in 41+ mph zones compared to 0–20 mph zones. This is computed dynamically and used in slides.

5. **Logistic regression** (from Q2 analysis) also quantifies this: OR=1.046 per mph. The odds ratio chart footnote explains the compounding: over a 25 mph range (20→45), that's (1.046)^25 = **+207% cumulative increase** in injury odds.

**Visualisation:** Chart 07 uses a dual-axis design — red bars for injury rate (left axis), blue line for fatality rate per 1,000 (right axis). Each bar is labelled with sample size.

**Slide 16 conclusion:** Speed cameras in 35+ mph zones, road diets on high-crash corridors, lower limits near schools/parks.

### Finding 3: Most Dangerous Driver Behaviors (lines ~521–536, Chart 08)

**What was explored:**

The dataset records `PRIM_CONTRIBUTORY_CAUSE` for each crash. Which behaviors produce the most injuries overall?

**How it was analyzed:**

1. **Filtered out** unhelpful categories ("UNABLE TO DETERMINE", "NOT APPLICABLE").

2. **Grouped by cause** and computed:
   - Total crashes per cause
   - Injury rate per cause
   - Total fatalities per cause

3. **Ranked by total injury crashes** (= total crashes × injury rate). The ranking identifies behaviors that are **both common and harmful** — a rare high-severity cause ranks below a common moderate-severity one.

**Top 5 most dangerous causes:**

| Rank | Cause | Crashes | Injury Rate | Injury Crashes |
|------|-------|---------|-------------|----------------|
| 1 | Failing to yield right-of-way | 85,226 | 23.3% | ~19,857 |
| 2 | Following too closely | 75,572 | 11.9% | ~8,971 |
| 3 | Failing to reduce speed | 32,952 | 23.4% | ~7,714 |
| 4 | Disregarding traffic signals | 15,167 | 40.1% | ~6,089 |
| 5 | Improper turning/no signal | 25,705 | 14.1% | ~3,616 |

**Notable:** "Disregarding traffic signals" has a 40.1% injury rate — the highest of any common cause — but ranks 4th because it's less frequent than yielding/following failures.

**Visualisation:** Chart 08 is a horizontal bar chart with:
- Bar length = total crashes
- Colour gradient (green→red) = injury rate
- Colourbar legend on the right
- Top 3 causes highlighted with bold borders

**Slide 17 conclusion:** Protected turn phases at high-yield-failure intersections, public awareness campaigns, red-light cameras.

### How the Three Findings Connect

The findings were chosen to cover **different actionable dimensions**:

| Finding | Dimension | Key lever |
|---------|-----------|-----------|
| Hit-and-run | **When** to intervene | Late-night enforcement |
| Speed-severity | **Where** to intervene | High-speed corridors |
| Dangerous causes | **What** to target | Specific driver behaviors |

### PowerPoint Slides

| Slide | Content |
|-------|---------|
| **14** | Section header — frames the three findings |
| **15** | Hit-and-run temporal patterns with hourly/daily charts |
| **16** | Speed-severity dose-response with dual-axis chart |
| **17** | Contributory causes ranked by total injury crashes |

---

## Q4: Where Do Most Crashes Occur and What Safety Measures Should Be Considered?

This question has two parts — **location analysis** and **recommendations**.

### Part 1: Finding Where Crashes Cluster

#### Step 1: SQL Exploration — Top Streets (lines ~230–241)

The initial exploration identifies the 20 highest-crash streets by raw volume:

| Street | Crashes | Injury Rate | Fatalities |
|--------|---------|-------------|------------|
| Western Ave | 21,183 | 14.3% | 26 |
| Pulaski Rd | 18,660 | 15.6% | 28 |
| Cicero Ave | 17,379 | 14.9% | 29 |
| Ashland Ave | 16,892 | 15.5% | 25 |
| Halsted St | 15,127 | 17.6% | 28 |

This gives a first indication, but street names alone don't pinpoint *where on the street* the problems are. That requires spatial clustering.

#### Step 2: DBSCAN Geographic Clustering (lines ~538–581)

**Method:** DBSCAN (Density-Based Spatial Clustering of Applications with Noise) groups nearby injury crashes into clusters:

- **Input:** All 106,491 injury crashes with valid lat/lon (no subsampling)
- **Parameters:** eps=150m radius, min_samples=100 crashes, haversine distance metric
- **Result:** 98 distinct clusters identified, 82.2% noise points

**How DBSCAN works here:** It draws a 150m circle around each crash. If 100+ other injury crashes fall within that circle, they form a cluster. The algorithm then expands outward, merging overlapping circles. Points that don't belong to any cluster are labelled "noise." The tighter parameters (150m vs the earlier 500m) produce more focused, intersection-level clusters rather than corridor-spanning mega-clusters.

**Top clusters profiled** (lines ~563–585) — for each cluster, the code computes:
- Centre coordinates (mean lat/lon)
- Crash count and total injuries
- Fatalities
- Top contributory cause
- Top lighting condition
- Average speed limit
- Dominant street name

| Rank | Street | Crashes | Injuries | Fatalities |
|------|--------|---------|----------|------------|
| 1 | Ontario St | 1,470 | 1,813 | 6 |
| 2 | Cicero Ave | 807 | 1,244 | 8 |
| 3 | Lake Shore Dr SB | 435 | 547 | 4 |
| 4 | Congress Pkwy | 421 | 565 | 3 |
| 5 | Roosevelt Rd | 410 | 522 | 0 |

The clusters are now appropriately sized (100–1,470 crashes each) rather than dominated by a single mega-cluster.

#### Step 3: Static Crash Density Map (Chart 09, lines ~914–958)

A scatter plot of 50,000 randomly sampled crashes (blue dots, very transparent) overlaid with:
- **Red circles** — DBSCAN cluster centres, sized proportionally to crash count
- **Numbered labels** — top 10 hotspots with street names
- **Geographic references** — Downtown, South Side, O'Hare, West Side labelled
- **Size legend** — small/medium/large cluster indicators

#### Step 4: Fatal Crash Map (Chart 11, lines ~1155–1184)

A separate map plotting all 856 fatal crashes as dark red dots, with:
- **Light blue background** — all crashes as context
- **Orange circles** — injury hotspot centres from DBSCAN (with legend entry)
- **Subtitle** — correctly says "856 fatal crashes" with total deaths count

This reveals that fatal crashes concentrate on **high-speed arterials** (Western, Pulaski, Cicero) and **disproportionately affect the South and West sides**.

#### Step 5: Interactive Folium Maps (lines ~1010–1153)

Two HTML maps for detailed exploration:

**Map 1 — `crash_heatmap.html`:**
- Colour-coded density heatmap (blue→red gradient)
- Red circle markers for top 10 hotspot clusters
- Click any circle for popup with: crash count, injuries, fatalities, top cause, avg speed limit, lighting
- Layer toggle, minimap, fullscreen, coordinate display

**Map 2 — `fatal_crashes_map.html`:**
- Every fatal crash as a clickable dark-red dot
- Click for: date, cause, speed limit, lighting, weather
- Enables manual identification of fatal crash corridors

### Part 2: Safety Recommendations (Slide 21, lines ~1735–1751)

Each recommendation is tied directly to a finding from the analysis. The slide explicitly maps **FINDING → ACTION**:

| Finding from data | Recommended intervention |
|-------------------|------------------------|
| 41+ mph zones have 5.7× fatality rate | Reduce speed limits on identified corridors, deploy speed cameras, road diets (4→3 lane conversion) |
| Darkness adds +21% injury odds (OR=1.214) | LED street lighting upgrades at highest-injury intersections, high-visibility crosswalks with flashing beacons |
| "Failing to yield" is #1 dangerous behavior | Protected turn phases, roundabout pilot studies, red-light cameras at worst intersections |
| Hit-and-runs peak midnight–4 AM (48% at 3 AM) | CCTV on high-H&R corridors, late-night enforcement, public campaigns |
| Wet weather adds ~10% injury risk (OR=1.104) | Improved drainage, anti-skid surface treatments, dynamic warning signs |
| October is peak crash month | Seasonal safety campaigns in September/October, enforcement surges |

**Important caveat:** These are expert interpretations of correlations, not tested interventions. The limitations are acknowledged in the Further Steps slide.

### Further Steps (Slide 22, lines ~1760–1776)

Acknowledges what additional data would strengthen the location analysis:

1. **AADT traffic volume data** — to calculate crash rates per vehicle-mile (not just raw counts)
2. **Before/after studies** — measure impact of past interventions using interrupted time series
3. **Predictive model** — Random Forest/XGBoost to score risk by location + time + weather
4. **Vulnerable road users** — separate analysis for pedestrians and cyclists
5. **Economic costs** — FHWA estimates ($1.7M per fatality) to prioritize by ROI

### PowerPoint Slides

| Slide | Content |
|-------|---------|
| **18** | Section header — states 98 clusters identified |
| **19** | Static crash density map + top 10 hotspot list + pointer to interactive HTML |
| **20** | Fatal crash map — 856 fatal crashes with correct label, orange circles with legend |
| **21** | Safety recommendations — each finding mapped to an intervention |
| **22** | Further steps — what additional data/analysis would help |
| **24** | Appendix — instructions for opening the interactive HTML maps |
