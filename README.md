# Stock Index Forecast Comparison

This DS340W project compares ChatGPT, Claude, Gemini, and Microsoft Copilot on
3-, 5-, and 10-trading-day return forecasts for the S&P 500, Nasdaq-100, and Dow.
The benchmarks are zero return and same-horizon momentum.

## Week 12 demo

Download and extract the GitHub ZIP. Open PowerShell in the extracted folder
and use Python 3.10 or newer. The scoring commands need no extra packages.

Place the exact files used for the paper in `data/local/`:

- `market_prices.csv` with the fixed closing-price history.
- `forecasts.csv` with the saved responses from all four assistants.

Run these commands for the September 1, 2026 test window with origins every
three trading observations. The fixed price CSV ends on November 6, 2026.
Use the same settings and prices for collecting and scoring the forecasts.

```powershell
py -m unittest discover -s tests -v
py src/project.py run
```

If you use different filenames, pass `--prices` and `--predictions`. For a
repeat run, use a new output folder, such as `--out results/real_four_models_2`.

Open `results/real_four_models/REPORT.md` for the overall comparison and
`metrics_by_horizon.csv` in the same folder for the horizon breakdown.
Lower mean absolute error (MAE) means a smaller average forecast miss.

To create a blank template and prompts using the same calendar, run:

```powershell
py src/project.py prepare --prices data/local/market_prices.csv --forecast-start 2026-09-01 --step 3 --out results/real_collection
```

Use `prediction_template.csv` and `prompt_text/` from that folder to collect
forecasts. See [setup and collection](QUICK_START.md) and
[price data sources](data/DATA_SOURCE.md).
