# Damped momentum on the working test split

Each method was scored on the same 126 forecasts across the S&P 500, Nasdaq-100, and Dow Jones Industrial Average. The code uses the submitted train and test files. Both the forecast origin and the target fall within the test period. The validation file is held out.

MAE is measured in percentage points. Lower is better.

| Method | 3 days | 5 days | 10 days | Overall |
|---|---:|---:|---:|---:|
| Zero baseline | 1.022 | 1.640 | 2.072 | 1.578 |
| Momentum baseline | 1.502 | 2.375 | 2.609 | 2.162 |
| 25% momentum | 1.016 | 1.737 | 1.985 | 1.579 |
| 50% momentum | 1.126 | 1.907 | 2.109 | 1.714 |

Run with `py novel_market_demo.py` on Windows. These results compare forecasting rules using observed index prices.
