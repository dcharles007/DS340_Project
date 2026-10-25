# Run the real-data project

Use Python 3.10 or later. Open a terminal in this project folder. On Windows,
use `py` instead of `python` if needed.

## 1. Download real observations

```sh
python scripts/download_market_data.py
```

This writes `data/local/market_prices.csv`, the untouched source CSV, and a
collection manifest. Default requested period: 2024-01-01 through 2026-10-23.
The common available sample in the verified collection ends 2026-10-21.

## 2. Verify the code

```sh
python -m unittest discover -s tests -v
```

## 3. Prepare a development experiment

```sh
python src/project.py prepare --prices data/local/market_prices.csv --split train --out results/real_development
```

Use the development period to finalize your protocol. For working tests, use:

```sh
python src/project.py prepare --prices data/local/market_prices.csv --split test --out results/real_test
```

The final 10% is locked validation. Do not unlock or tune against it before fixing
all experimental choices. The code fits no assistant models itself.

## 4. Collect actual assistant forecasts

For every case in `prompt_text/`, paste the prompt (without its ID heading) into
fresh chats in ChatGPT, Claude, Gemini, and Copilot. Disable browsing/tools where
available. Keep the original response, actual model/product label, and UTC collection
time. Enter numeric percentage-return predictions into the prediction template.
A prediction of `1.5` means +1.5%. Do not replace refusals with invented forecasts.
Retrospective predictions can be affected by memorized market history.

## 5. Score complete forecasts

After saving your completed template as `results/real_test/predictions.csv`:

```sh
python src/project.py score --prices data/local/market_prices.csv --experiment results/real_test --predictions results/real_test/predictions.csv
python -m pip install -r requirements.txt
python src/project.py charts --experiment results/real_test
```

Do not score the blank template as if it contained real forecasts. Synthetic toy
results already exist in `results/demo/` and do not establish assistant performance.

## Public repository and dataset submission

Keep `data/local/` and `results/real_*/` out of public Git. They contain provider
observations or prompts embedding those observations. Link the FRED sources and
`data/DATA_SOURCE.md` for the dataset deliverable. The private course-use download
is also supplied separately for analysis. Source data retain provider terms.
