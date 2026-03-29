# Chicago Traffic Crash Analysis (2016–2023)

Statistical analysis of 785,000+ traffic crashes in Chicago, exploring temporal patterns, weather–severity relationships, dangerous behaviours, and geographic hotspots.

## Research Questions

1. **Temporal Correlation** — Is there a correlation between time of year/week/day and crash occurrence?
2. **Wet Weather & Severity** — Is there a causal relationship between wet weather and crash severity?
3. **Key Exploratory Findings** — What patterns emerge in hit-and-run incidents, speed–severity relationships, and contributory causes?
4. **Geographic Hotspots** — Where do crashes cluster and what safety interventions could help?

## Methods

| Technique | Purpose |
|-----------|---------|
| Chi-squared tests | Temporal distribution significance |
| Mann-Whitney U | Weekday vs weekend comparison |
| Seasonal decomposition | Annual crash rhythm extraction |
| Odds ratios & logistic regression | Weather–severity association (with confounders) |
| DBSCAN clustering | Geographic hotspot identification (150m radius) |
| Folium heatmaps | Interactive crash density mapping |

## Key Findings

- **October** is peak crash month; **Friday 3–5 PM** is the most dangerous window
- Wet weather is associated with **10.4% higher injury odds** after controlling for darkness, speed, hour, and day
- **30% of all crashes** are hit-and-run, peaking at 3 AM (48% H&R rate)
- Speed zones above 40 mph have **5.7x higher fatality rates** than 0–20 mph zones
- **98 geographic clusters** identified; Ontario Street tops the list with 1,470 injury crashes

## Output

The `output/` folder contains:

- 11 publication-quality charts (PNG, 250 DPI)
- 2 interactive HTML maps (crash heatmap and fatal crash map)
- 24-slide PowerPoint presentation

## Project Structure

```
run_analysis.py              # Main analysis script (generates all outputs)
create_notebook.py           # Builds the Jupyter notebook programmatically
traffic_crash_analysis.ipynb # Executable Jupyter notebook
answerslogic.md              # Detailed methodology and reasoning
implementation_plan.md       # Original project plan
output/                      # Charts, maps, and presentation
```

## Data

This project uses the [Chicago Traffic Crashes](https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if) public dataset. Download `Traffic_Crashes.csv` and place it in the project root before running.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the full analysis pipeline:

```bash
python run_analysis.py
```

Or explore interactively via the Jupyter notebook:

```bash
jupyter notebook traffic_crash_analysis.ipynb
```
