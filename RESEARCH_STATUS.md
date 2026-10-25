# Midterm research status

The project compares ChatGPT, Claude, Gemini, and Copilot on stock-index return forecasts.

- Implemented: input checks, identical prompt generation, chronological periods, locked final validation, two baselines, forecast scoring, graph exports, and calculation/integrity tests.
- Collected: real FRED market-close index observations. Run the downloader for local files and the collection manifest.
- Demonstration: `results/demo/` contains synthetic observations and toy forecasts only.
- Not yet collected: real assistant forecasts. No real-assistant rankings or trading-profit claims are available.

## Parent papers and the project extension

1. Zhang and Lu (2024), *Stock Trend Prediction with Machine Learning: Incorporating Inter-Stock Correlation Information through Laplacian Matrix*. https://doi.org/10.3390/bdcc8060056
2. Liang et al. (2025), *PriceSeer: Evaluating Large Language Models in Real-Time Stock Prediction*. https://arxiv.org/abs/2601.06088
3. Chen et al. (2026), *StockBench: Can LLM Agents Trade Stocks Profitably In Real-world Markets?*, v2. https://arxiv.org/abs/2510.02209v2

Our extension evaluates index percentage-return forecasts with a shared prompt and simple forecasting baselines. It does not train LOG models or reproduce StockBench's trading agents. The three real index series differ from the parent papers' individual-stock datasets.

## Dataset submission

The code and dataset retrieval documentation live in this repository. Original observations remain at the linked FRED sources because the providers restrict redistribution. The local cleaned dataset has columns `date,index,close`; all three indexes share the retained observation dates. See `data/DATA_SOURCE.md`.

The downloaded period is retrospective. A price-only prompt cannot eliminate model memorization of historical outcomes. Treat retrospective assistant results accordingly. Prospective forecasts must be archived before their outcomes occur.
