# Explaining the code in your check-in

The project asks whether different AI assistants can predict stock-index returns
when they receive the same historical information. The program handles the data,
prompt preparation, evaluation, and graphs. The group supplies real index prices
and collects forecasts from the assistants.

`read_prices` checks dates and prices and requires a matching calendar across indexes.
This makes the number of trading observations comparable.

`partitions` assigns dates chronologically: 70% train, 20% working test, 10% final
validation. `make_cases` selects forecast origins and targets, keeps both within
one split, and gives each prompt only the historical lookback ending at its origin.
All horizons share forecast origins, allowing a more consistent horizon comparison.

For example, if the index closes at 100 on the origin and 102 three observations
later, the actual return is 100 × (102/100 − 1) = 2%. If an assistant predicts 1.5%,
its absolute error is |1.5 − 2| = 0.5 percentage points. Its direction is correct
because both numbers are positive.

`save_experiment` generates identical prompts and a blank prediction table. It also
records settings and checksums. `score_experiment` verifies these before evaluating
so changed data or edited prompts cannot silently change an existing experiment.

`evaluate` checks that each assistant has a valid prediction for every case. It adds
zero-return and historical-momentum forecasts. A momentum forecast uses the return
from the prior same-length period; it does not use the target closing price.

`aggregate` calculates MAE, RMSE, signed error, and direction accuracy. `charts`
creates graphs of return error, direction accuracy, horizon error, and actual versus
predicted returns. A dashed diagonal in the last graph marks perfect forecasts.

`demo` creates synthetic prices and toy forecasting rules to exercise the program.
Those toy models are deliberately named Toy momentum and Toy contrarian. Their
scores demonstrate functioning code and are not ChatGPT/Claude/Gemini/Copilot results.

The tests check the return formula, absence of future data in prompts, unchanged
past-only forecasts after future prices are modified, holdout gating, balanced
comparison requirements, and reproducible experiment settings.

What remains for actual research: collect documented market data and raw assistant
responses, fix the protocol, then perform the final holdout evaluation. The code
cannot verify that a supplied row genuinely came from the claimed assistant or
prevent the assistant from remembering historical outcomes.
