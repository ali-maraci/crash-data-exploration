# Chicago Traffic Crash Analysis — Implementation Plan

## Context
We have a 785K-row Chicago traffic crashes dataset (2016–2023, Chicago area) and must answer four analytical questions, then present findings in a PowerPoint. The user wants to demonstrate technical breadth by using multiple tools/techniques. The system has Python 3.14 but requires library installation. All work will be delivered as a single Jupyter notebook plus a generated PowerPoint file.

---

## Implementation Format
Single Jupyter notebook (`traffic_crash_analysis.ipynb`) built as JSON, with markdown cells separating each phase. Executed via `jupyter nbconvert --execute --to notebook --ExecutePreprocessor.timeout=600` to populate all cell outputs. Charts are saved to `output/` for PowerPoint embedding AND displayed inline in the notebook.

### Execution Strategy
1. Write the `.ipynb` file as JSON (code cells + markdown cells)
2. Execute via `jupyter nbconvert --execute` to run all cells and capture outputs
3. The PowerPoint generation is the final cell — it reads saved PNGs from `output/` and assembles the `.pptx`
4. If nbconvert fails (timeout, Python 3.14 compatibility), fallback: run as a `.py` script via bash and separately create the notebook with code only

---

## Phase 0: Environment Setup

```bash
pip3 install pandas numpy matplotlib seaborn scipy scikit-learn statsmodels python-pptx openpyxl folium pyarrow
mkdir -p output
```

**Note**: `pyarrow` is needed for parquet I/O. If any package fails to install on Python 3.14, fall back to CSV for intermediate storage and check for compatible versions.

**Compatibility check cell**: Import all libraries and print versions to verify.

---

## Phase 1: Data Loading, Cleaning & Feature Engineering

### 1.1 Load CSV
- Use `pd.read_csv()` with `parse_dates=['CRASH_DATE']` and explicit `dtype` mapping for integer columns (use `'Int64'` nullable integer type to handle NaN)
- Date format is mixed (`MM/DD/YYYY HH:MM:SS AM/PM` and `MM/DD/YYYY HH:MM`). Use `format='mixed'` in pandas or let it infer.
- Expect ~785,871 rows, 32 columns

### 1.2 Validate Data Quality
- Print shape, dtypes, null counts
- Verify `CRASH_HOUR` is 0–23 integer (no string corruption — earlier exploration confirmed pandas parses correctly)
- Verify `CRASH_DAY_OF_WEEK` is 1–7 (metadata: **1=Sunday, 7=Saturday**)
- Verify `CRASH_MONTH` is 1–12
- Check lat/lon bounds (Chicago: lat 41.6–42.1, lon -87.9 to -87.5)
- Count and report missing values per column

### 1.3 Filter & Clean
- Extract `CRASH_YEAR` from `CRASH_DATE`
- Keep only 2016–2023 (drop partial 2013–2015 data, ~9.8K rows)
- Drop `DOORING_I` column (99.7% blank — unusable)
- Drop `LANE_CNT` column (74.7% missing — unusable; note as limitation)
- Treat blank `HIT_AND_RUN_I` as "N" (it's an indicator flag; 540K blanks + 688 explicit "N" vs 14,955 "Y")
- Drop rows where `CRASH_HOUR` or `CRASH_DAY_OF_WEEK` is null (if any)

### 1.4 Feature Engineering
| Feature | Definition |
|---------|-----------|
| `IS_WET_WEATHER` | 1 if WEATHER_CONDITION in {RAIN, SNOW, FREEZING RAIN/DRIZZLE, SLEET/HAIL, BLOWING SNOW} |
| `IS_WET_SURFACE` | 1 if ROADWAY_SURFACE_COND in {WET, SNOW OR SLUSH, ICE} |
| `HAS_INJURY` | 1 if INJURIES_TOTAL > 0 |
| `HAS_FATAL` | 1 if INJURIES_FATAL > 0 |
| `IS_SEVERE` | 1 if MOST_SEVERE_INJURY in {INCAPACITATING INJURY, FATAL} |
| `IS_WEEKEND` | 1 if CRASH_DAY_OF_WEEK in {1, 7} (Sunday, Saturday) |
| `TIME_PERIOD` | Categorical: Morning Rush (6–9), Midday (10–15), Evening Rush (16–19), Night (20–23), Late Night (0–5) |
| `DAY_NAME` | Mapped from CRASH_DAY_OF_WEEK: {1→Sunday, 2→Monday, ..., 7→Saturday} |
| `MONTH_NAME` | Mapped from CRASH_MONTH via `calendar.month_abbr` |
| `SPEED_CATEGORY` | Binned: 0–20 / 25–30 / 35–40 / 45+ mph |
| `DAMAGE_LEVEL` | Ordinal: $500 OR LESS→1, $501-$1,500→2, OVER $1,500→3 |
| `IS_DARK` | 1 if LIGHTING_CONDITION contains "DARK" |

### 1.5 Save Cleaned Data
- Save to parquet (requires pyarrow): `crashes_clean.parquet`
- If pyarrow unavailable, fall back to `crashes_clean.csv`

---

## Phase 2: SQL-Based Exploration (Tool: SQLite)

**Purpose**: Demonstrate SQL proficiency alongside Python. SQLite is used as an in-process database.

### 2.1 Load into SQLite
- Create SQLite database: `crashes.db`
- Load cleaned dataframe into `crashes` table via `df.to_sql()`

### 2.2 Run Exploratory Queries
Display results as formatted tables in notebook:

| Query | Purpose |
|-------|---------|
| Crashes by year with injury/fatality counts & rates | Overview trend |
| Day-of-week × hour cross-tab counts | Temporal heatmap data |
| Weather condition → total, injury count, injury rate % | Weather impact |
| Top 15 contributory causes by volume + injury rate | Cause ranking |
| Hit-and-run: count, injury rate, avg injuries | H&R overview |
| Top 20 streets by crash volume + injury/fatal counts | Location hotspots |

### 2.3 Key Observations
- Print summary observations from SQL output to guide deeper analysis

---

## Phase 3: Statistical Analysis

### 3a: Temporal Correlation (Q1: Is there a correlation between time of year/week/day and crashes?)

**Tools**: scipy.stats, statsmodels

| Analysis | Method | What It Tests |
|----------|--------|---------------|
| Monthly distribution | Chi-squared goodness-of-fit | H0: crashes uniformly distributed across 12 months |
| Day-of-week distribution | Chi-squared goodness-of-fit | H0: crashes uniformly distributed across 7 days |
| Hourly distribution | Chi-squared goodness-of-fit | H0: crashes uniformly distributed across 24 hours |
| Monthly time series | `seasonal_decompose(model='additive', period=12)` | Extract trend, seasonal, residual components |
| Weekend vs weekday | Mann-Whitney U test | Compare daily crash counts: weekday vs weekend |
| Year-over-year trend | Pearson correlation (year vs annual count) | Linear trend over time |

**Expected findings**: All chi-squared tests reject H0 (p << 0.05). October likely peak month, Friday peak day, 3–5 PM peak hours. 2020 COVID dip visible in trend. Weekend nights show late-night spike (alcohol-related pattern).

**Critical detail**: For the time series decomposition, aggregate to a monthly time series (count per calendar month). Ensure all months are present (no gaps). The decomposition requires at least 2 full cycles — we have 8 years = 96 months, which is sufficient.

### 3b: Wet Weather & Crashes (Q2: Is there a causal relationship?)

**Tools**: scipy.stats, statsmodels

**Methodological note**: Observational data cannot definitively prove causation. We use progressively rigorous approaches to establish whether there is a strong, consistent association that survives confounding adjustment — the closest we can get to causal inference without experimental design or instrumental variables.

**Five escalating levels of evidence**:

1. **Naive count comparison**: Count crashes in wet vs dry weather. This is misleading alone because it ignores how often each weather type occurs.

2. **Exposure-adjusted crash rates**: Compare the proportion of crashes in each weather type vs the proportion of time that weather occurs.
   - Use published NOAA Chicago O'Hare climate normals for weather frequency:
     - ~124 precipitation days/year (34% of days)
     - ~28 snow days/year (8%)
     - ~213 clear/dry days (58%)
   - **Limitation**: These are annual averages, not matched to the exact dates in our dataset. Note this and suggest obtaining daily weather station data as a further step.
   - Calculate: Crash Rate Index = (% of crashes in condition) / (% of days with condition). Index > 1 means elevated crash rate.

3. **Chi-squared test of independence**: Contingency table: Wet/Dry weather × Injury/No-injury. Tests whether injury probability depends on weather.

4. **Odds ratio with 95% CI**: Compute unadjusted odds ratio for wet weather → injury. Formula: OR = (a×d)/(b×c). CI via log-OR ± 1.96 × SE.

5. **Logistic regression controlling for confounders**:
   - Model: `P(HAS_INJURY) ~ IS_WET_WEATHER + IS_DARK + POSTED_SPEED_LIMIT + C(CRASH_HOUR) + C(CRASH_DAY_OF_WEEK)`
   - `C(CRASH_HOUR)` treats hour as categorical (23 dummies), which is correct since crash risk is not linearly related to hour
   - Extract the adjusted OR for `IS_WET_WEATHER` — this is the isolated effect after removing confounding from time-of-day, darkness, and speed limit
   - Also report the adjusted OR for `IS_DARK` and `POSTED_SPEED_LIMIT` for comparison

6. **Stratified analysis** (robustness check): Compute separate odds ratios for wet weather within each lighting condition stratum (DAYLIGHT, DARKNESS LIGHTED, DARKNESS). If the OR is consistent across strata, the association is robust and not confounded by lighting.

**Conclusions cell**: Synthesise all five levels. State explicitly: "We observe a statistically significant association between wet weather and [increased/decreased] crash injury rates, which persists after controlling for confounders. However, this is an observational association, not a proven causal relationship. Unmeasured confounders (e.g., traffic volume, driver behaviour changes in rain) may exist."

### 3c: Key Findings (Q3: Investigate 2–3 findings of your choice)

**Finding 1: Hit-and-Run Patterns**
- Prevalence: What % of crashes are hit-and-run?
- Temporal: H&R rate by hour-of-day and day-of-week (peak late night? weekends?)
- Severity: Compare injury rate for H&R vs non-H&R (chi-squared test)
- Location: Are H&R concentrated on specific streets?
- Insight: Late-night hit-and-runs may correlate with impaired driving; targeted enforcement recommendation

**Finding 2: Speed Limit & Crash Severity**
- Dose-response: Injury rate and fatality rate by speed category (bar chart showing clear escalation)
- Statistics: Spearman rank correlation (POSTED_SPEED_LIMIT vs INJURIES_TOTAL), point-biserial correlation (POSTED_SPEED_LIMIT vs HAS_FATAL)
- Insight: Higher posted speed limits are associated with more severe injuries — supports speed management interventions

**Finding 3: Most Dangerous Contributory Causes**
- Filter out "UNABLE TO DETERMINE" and "NOT APPLICABLE"
- Rank by: (a) total crash volume, (b) injury rate per cause, (c) composite "danger score" = volume × injury rate
- Top 15 causes displayed
- Insight: Identify which behaviours cause the most harm (e.g., failing to yield, distracted driving, DUI) — informs enforcement and education priorities

### 3d: Hotspot Identification (Q4: Key crash areas & safety measures)

**Tools**: scikit-learn (DBSCAN), folium

**DBSCAN Clustering** on injury crash coordinates:
- Input: lat/lon of all crashes where `HAS_INJURY == 1` (expected ~250K–300K rows)
- Convert to radians for haversine metric
- **Parameters**: `eps = 0.5 / 6371` (≈ 0.0000785 radians = 500 metres), `min_samples=50`, `metric='haversine'`, `algorithm='ball_tree'`
  - **Why these values**: 500m radius captures intersection-level clusters; min_samples=50 ensures statistical significance
  - **Why DBSCAN over K-means**: (1) doesn't require pre-specifying number of clusters, (2) identifies noise/outliers, (3) finds arbitrary-shaped clusters (street corridors)
- **Performance note**: Ball-tree with haversine on ~300K points should complete in minutes. If too slow, subsample to 100K (random sample preserving spatial distribution).

**Hotspot profiling**: For each of the top 20 clusters, compute:
- Cluster centre (mean lat/lon)
- Crash count, total injuries, fatal count
- Dominant `PRIM_CONTRIBUTORY_CAUSE` (mode)
- Dominant `LIGHTING_CONDITION` (mode)
- Mean `POSTED_SPEED_LIMIT`
- Nearest street name (most frequent `STREET_NAME` in cluster)

**Folium Maps** (2 HTML outputs):
1. **All-crashes heatmap**: 50K random sample plotted as heatmap, top 10 cluster centres marked with red CircleMarkers (size proportional to crash count)
2. **Fatal crashes map**: Every fatal crash as a dark-red CircleMarker

**Static map for PowerPoint**: Matplotlib scatter plot of all crash locations (alpha=0.02 for density), with cluster centres overlaid as sized red dots. Lat/lon axes with Chicago bounding box.

**Safety Recommendations Framework** (derived from hotspot profiles):

| Hotspot Characteristic | Recommended Intervention |
|----------------------|-------------------------|
| High-speed corridor (45+ mph) with many rear-end crashes | Reduce speed limits, add speed cameras, road diet (lane reduction) |
| Dark intersection with pedestrian injuries | Enhanced street lighting (LED), high-visibility crosswalks, pedestrian countdown signals |
| Intersection with "failing to yield" as top cause | Protected turn phases, roundabout conversion study, red-light cameras |
| Corridor with high H&R rate | CCTV installation, increased patrol presence, public awareness campaigns |
| School zone or residential area | Traffic calming (speed bumps, chicanes), reduced speed limits, crossing guards |
| Wet-surface crashes concentrated | Improved drainage, anti-skid surface treatment, advance warning signs |

---

## Phase 4: Visualization Generation (Tools: matplotlib, seaborn)

**Styling standard**: All charts use `sns.set_theme(style='whitegrid')`, consistent colour palette (`tab10` or custom), 200 DPI, Calibri font where possible, white background. Saved as PNG to `output/`.

| # | Chart | Type | Key Design Choices |
|---|-------|------|--------------------|
| 1 | Monthly time series + seasonal decomposition | 4-panel line chart (observed, trend, seasonal, residual) | `figsize=(14, 10)`, shared x-axis, annotate 2020 COVID dip |
| 2 | Day-of-week × hour crash density | Seaborn heatmap | Rows labelled Mon→Sun (reorder from 1=Sun data), `annot=False` (too dense), `cmap='YlOrRd'` |
| 3 | Crashes by month (mean ± std) | Bar chart + error bars | Group by month across years, error bars show inter-year variation |
| 4 | Weather condition impact | Dual-axis bar chart | Left axis: crash count, right axis: injury rate %, exclude UNKNOWN |
| 5 | Logistic regression odds ratios | Forest plot with 95% CI | Horizontal, line at OR=1, key variables highlighted |
| 6 | Hit-and-run temporal pattern | Dual-panel: (a) H&R rate by hour, (b) H&R rate by DOW | Line chart with shaded CI band |
| 7 | Speed limit vs crash severity | Grouped bar | Speed category on x, bars for injury rate and fatality rate (×1000 scale) |
| 8 | Top contributory causes | Horizontal bar chart | Top 15, bars coloured by injury rate (green→red gradient) |
| 9 | Crash density map (static) | Matplotlib scatter | All crashes alpha=0.02, cluster centres as sized red dots, Chicago bbox |
| 10 | Year-over-year trend | Line chart with markers | Annotate 2020 with "COVID-19" label |

---

## Phase 5: PowerPoint Presentation (Tool: python-pptx)

Widescreen 16:9 (13.333" × 7.5"). Consistent branding: dark blue title bar (#005B96), white body, Calibri font.

| Slide | Title | Content |
|-------|-------|---------|
| 1 | Chicago Traffic Crash Analysis (2016–2023) | Title slide, subtitle: "Data-Driven Insights for Road Safety", author, date |
| 2 | Executive Summary | 4–5 bullet points: top findings with key numbers |
| 3 | Methodology & Tools | Tools diagram: pandas→SQL→scipy→statsmodels→sklearn→folium→pptx. Methods: chi-squared, logistic regression, DBSCAN, time series decomposition. Data: 775K+ records. |
| 4 | Data Overview | Table: rows, columns, date range, geographic scope. Data quality notes (missing LANE_CNT, H&R coding). Pie chart or summary stats. |
| 5 | Temporal: Monthly Seasonality | Chart 1 (decomposition) + chi-squared p-value + narrative |
| 6 | Temporal: Day & Hour Patterns | Chart 2 (heatmap) + interpretation of rush-hour and late-night patterns |
| 7 | Temporal: Year-over-Year Trend | Chart 10 (yearly trend) + COVID-19 commentary |
| 8 | Weather: Crash Distribution by Condition | Chart 4 (weather impact) + raw count comparison |
| 9 | Weather: Exposure-Adjusted Analysis | Table comparing crash % vs weather % + Crash Rate Index. Interpretation of whether wet weather truly elevates crash rate per unit exposure. |
| 10 | Weather: Causal Inference | Chart 5 (forest plot) + adjusted OR table. Key result: "After controlling for time-of-day, darkness, and speed limit, wet weather [does/does not] significantly increase injury risk." |
| 11 | Weather: Conclusions & Limitations | Synthesis of 5 evidence levels. Explicit caveat on causation vs association. Limitations: no traffic volume data, approximate weather exposure, self-selection bias. |
| 12 | Finding 1: Hit-and-Run Patterns | Chart 6 + key stats (prevalence, peak times, severity comparison) |
| 13 | Finding 2: Speed & Severity | Chart 7 + Spearman correlation + interpretation |
| 14 | Finding 3: Dangerous Behaviours | Chart 8 + danger score ranking + top 3 causes narrative |
| 15 | Crash Hotspot Map | Chart 9 (static map) + table of top 10 hotspot locations with street names |
| 16 | Safety Recommendations | Targeted recommendations per hotspot type (see table in Phase 3d). Each recommendation tied to a specific data finding. |
| 17 | Further Steps & Recommendations | Next analyses: (1) obtain AADT traffic volume data for true crash rates, (2) link to vehicle/person-level datasets, (3) obtain daily weather station data for precise exposure, (4) before/after studies on past interventions, (5) predictive modelling (random forest, XGBoost) for crash risk scoring |
| 18 | Appendix: SQL Queries Used | Formatted SQL code from Phase 2 |
| 19 | Appendix: Interactive Maps | Note that two interactive HTML maps are provided separately: all-crashes heatmap + fatal-crashes map |

---

## Tools & Techniques Summary (9 distinct tools)

| Tool | Purpose |
|------|---------|
| pandas / numpy | Data wrangling, aggregation, feature engineering |
| SQLite (sqlite3) | SQL-based exploration, demonstrating BI-style querying |
| scipy.stats | Chi-squared, Mann-Whitney U, Spearman, point-biserial, odds ratio |
| statsmodels | Time series decomposition, logistic regression with confounders |
| scikit-learn (DBSCAN) | Geographic hotspot clustering with haversine distance |
| folium | Interactive geographic heatmaps (HTML) |
| matplotlib | 10 static publication-quality charts |
| seaborn | Styled heatmaps and enhanced chart aesthetics |
| python-pptx | Automated PowerPoint generation with embedded images |

---

## Potential Pitfalls & Mitigations

| Risk | Mitigation |
|------|-----------|
| Python 3.14 package incompatibility | Check each import, pin compatible versions if needed |
| Parquet write fails (pyarrow issue) | Fall back to CSV intermediate files |
| DBSCAN too slow on 300K points | Subsample to 100K; use ball_tree algorithm |
| `seasonal_decompose` fails on irregular series | Ensure no missing months; fill gaps with 0 if needed |
| Logistic regression convergence | Increase `maxiter=200`; use `method='lbfgs'`; scale continuous vars |
| CRASH_DATE mixed format parsing | Use `pd.to_datetime(format='mixed')` or `dayfirst=False` |
| Notebook execution timeout | Set `--ExecutePreprocessor.timeout=600` (10 min per cell) |

---

## Verification Checklist
- [ ] All packages install successfully on Python 3.14
- [ ] Cleaned dataset has ~775K+ rows (after dropping 2013–2015)
- [ ] 6 SQL query outputs display correctly in notebook
- [ ] All 6 statistical tests produce p-values (no NaN/errors)
- [ ] Logistic regression converges and produces interpretable coefficients
- [ ] DBSCAN produces at least 10 meaningful clusters (not all noise)
- [ ] 10 PNG files generated in `output/` directory
- [ ] 2 HTML files (heatmap + fatal map) open correctly in browser
- [ ] PowerPoint has 19 slides, all images render, no broken layouts
- [ ] Folium maps centred on Chicago (41.88, -87.63) at appropriate zoom

## Key Files
- **Input**: `Traffic_Crashes.csv` (325MB, 785K rows), `Traffic_crashes_metadata.xlsx`
- **Intermediate**: `crashes_clean.parquet` (or `.csv`), `crashes.db`
- **Output**: `output/*.png` (10 charts), `output/crash_heatmap.html`, `output/fatal_crashes_map.html`, `output/Chicago_Traffic_Crash_Analysis.pptx`
- **Notebook**: `traffic_crash_analysis.ipynb`
