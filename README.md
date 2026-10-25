# Real market data is now available

Run `python scripts/download_market_data.py` to retrieve the dataset locally.
The verified collection contains **704 common dates and 2,112 index observations**,
from **2024-01-02 through 2026-10-21**, across S&P 500, Nasdaq-100, and Dow.
Requested end date: 2026-10-23. Later incomplete dates are excluded.

See [data sources](data/DATA_SOURCE.md), [quick start](QUICK_START.md), and
[research status](RESEARCH_STATUS.md). The public source package includes a downloader
and provenance manifest. Observed prices and price-containing prompts remain local
because FRED's index providers restrict redistribution.

# DS340W Group 46 — Stock-index return forecast comparison

This code implements the project described in the earlier Group 46 check-in:
compare ChatGPT, Claude, Gemini, and Copilot using identical historical information
to forecast percentage returns of several indexes. This version supports 3, 5,
and 10 trading-observation horizons, two baselines, chronological splits, reproducible
experiment files, and presentation graphs.

**Start here:** Follow `QUICK_START.md`. The included `results/demo/` is a verified
synthetic demonstration. Its toy forecasts are not real assistant forecasts or
research findings. The evaluation code never calls an assistant service. The added `scripts/download_market_data.py` downloads real index observations from FRED.

## What the code does

1. Reads and checks `date,index,close` CSV data for all selected indexes.
2. Uses the earliest 70% of dates for training/development, the next 20% for the
   working test set, and the final 10% for validation, following the course's terminology.
3. Requires both forecast origin and target to be within the selected split. This
   removes forecasts whose labels cross a split boundary. Prior historical prices
   may appear as context in later splits; that is legitimate past information.
4. Creates identical price-only prompts and blank rows for the four assistants.
5. Freezes source-data and prompt checksums, horizons, lookback, and sampling step
   in `experiment.json`. Scoring uses those saved settings.
6. Rejects incomplete comparisons, duplicate rows, invalid numeric forecasts, missing
   collection metadata, and changed data or prompts.
7. Compares assistant forecasts with zero-return and same-horizon past-momentum baselines.
8. Writes overall, per-horizon, and per-index/per-horizon metrics, case-level details,
   a readable report, and four PNG/SVG graph types.

## Forecast target and scores

Actual return (%) = 100 × (target closing level / origin closing level − 1).
A prediction of `1.5` means +1.5%, not a decimal return of 0.015.

- MAE: mean absolute difference between predicted and actual returns, in percentage points.
- RMSE: square root of mean squared return error, in percentage points.
- Mean error: signed average error; positive means forecasts were too high on average.
- Direction accuracy: fraction with the same sign (positive, negative, or exactly zero).
  The zero baseline is neutral, so its direction score can be zero even when its
  return-error score is competitive. Do not interpret it as an up/down guessing model.

Metrics retain full numeric precision. Reports round only for display. Each row
receives equal weight. Default sampling uses the same origins across horizons and
all indexes, with a step of 10 observations to limit overlapping target windows.
Changing the step to less than the longest horizon permits overlap.

## Experiment design

Defaults: horizons 3/5/10, 20 supplied prices per prompt, origin step 10.
The supplied-data calendars define "trading days"; the program does not independently
verify market holidays or completeness. All indexes must share the same dates.
For a useful final validation set, use roughly a full trading year or more of data;
the ten-day horizon can leave few or no final cases in a short dataset.

Use `--split train` to develop the prompt/protocol. Use `--split test` for working
checks. Use `--split validation --unlock-validation` only after fixing all choices.
The switch blocks accidental prompt generation and scoring, not manual viewing of
the raw input CSV. The program reads the complete CSV for calendar/integrity checks.
No model is fitted: the "train" period here is for protocol development. Assistants
are externally trained services; this project evaluates their supplied outputs.

Use a fresh chat for every prompt; paste only the actual prompt, excluding the
prompt ID heading. Disable browsing and tools where available. Record the actual
model/version or product label; do not claim a version you cannot identify. Preserve
raw responses separately under `results/.../raw_responses/` for audit. Enter UTC
collection times such as `2026-10-01T01:30:00Z`. If a model refuses or returns no
number, log it rather than inventing a forecast. Complete the balanced set before scoring.

Instructions alone cannot prevent an assistant from using memorized market history.
A stronger design is prospective collection: obtain forecasts at each origin before
outcomes exist, archive them, and score only after the future close is available.
This batch workflow expects a fixed CSV with observed outcomes, so retrospective
results must acknowledge possible prior-knowledge leakage. For prospective collection,
create prompts from currently available histories using the same `prompt_text` helper,
archive forecasts, and prepare/score the final fixed experiment after outcomes arrive.
Do not tune the protocol using validation outcomes.

## Data format

UTF-8 CSV header: `date,index,close`. Dates use `YYYY-MM-DD`. Closing levels must be
positive finite numbers. The names SP500, NASDAQ100, and DOW are examples, not a
requirement. Complete `data/DATA_SOURCE.md` with the provider, price convention,
collection time, and source URL. Real observations can be downloaded with the included script. The four assistants' outputs must be collected by the group. No API keys are required.

## Project contribution and scope

The implemented extension is a controlled, generalized **index-return** comparison,
including Copilot and simple baselines, rather than an individual-stock closing-price
comparison. These are project choices inspired by the existing PriceSeer summary;
this is not a reproduction of every PriceSeer experiment and does not implement
news manipulation, technical-indicator ablation, portfolio optimization, or the
first parent paper's neural-network/regularization methods. Check that the instructor
accepts this proposed contribution as the course's novel approach.

The program reports descriptive forecasting scores, not statistical significance,
profits, or investment recommendations. Correlated indexes/dates and overlapping
horizons need a suitable dependent-data analysis before claims about model superiority.

## Files

- `src/project.py`: complete command-line workflow and documented functions.
- `tests/test_project.py`: calculation, split, leakage, integrity, and completeness tests.
- `QUICK_START.md`: Windows-friendly setup and run commands.
- `CODE_EXPLANATION.md`: plain-language walkthrough for presenting the code.
- `CHECKIN_EVIDENCE.txt`: actual test/demo verification recorded for this package.
- `results/demo/`: generated toy results and graphs for a working demonstration.
- `data/prices_template.csv`: header-only template; not real market data.

The previous starter remains unchanged. This package is a separate expanded version.
