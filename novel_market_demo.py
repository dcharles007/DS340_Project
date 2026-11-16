"""Compare damped momentum forecasts on the submitted working test split."""
from pathlib import Path

from src.project import BASELINES, aggregate, make_test_cases, score_forecasts, write_csv

ROOT = Path(__file__).resolve().parent
METHODS = {
    BASELINES[0]: 0.0,
    BASELINES[1]: 1.0,
    "25% momentum": 0.25,
    "50% momentum": 0.50,
}


def forecasts_for_case(case):
    """Reduce the size of the previous same-horizon return toward zero."""
    past_return = case["momentum_baseline_pct"]
    return [(case, method, weight * past_return) for method, weight in METHODS.items()]


def main():
    cases = make_test_cases(ROOT / "splits/train.csv", ROOT / "splits/test.csv")
    details = score_forecasts(
        forecast for case in cases for forecast in forecasts_for_case(case)
    )
    overall = aggregate(details, ["model"])
    by_horizon = aggregate(details, ["horizon_trading_days", "model"])
    output = ROOT / "results/novel_momentum"
    write_csv(output / "metrics_overall.csv", overall, lineterminator="\n")
    write_csv(output / "metrics_by_horizon.csv", by_horizon, lineterminator="\n")
    errors = {
        (row["model"], row["horizon_trading_days"]): row["mae_percentage_points"]
        for row in by_horizon
    }
    overall_errors = {row["model"]: row["mae_percentage_points"] for row in overall}
    summary = [
        "# Damped momentum on the working test split",
        "",
        f"Each method was scored on the same {len(cases)} forecasts across the S&P 500, "
        "Nasdaq-100, and Dow Jones Industrial Average. The code uses the submitted "
        "train and test files. Both the forecast origin and the target fall within "
        "the test period. The validation file is held out.",
        "",
        "MAE is measured in percentage points. Lower is better.",
        "",
        "| Method | 3 days | 5 days | 10 days | Overall |",
        "|---|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        scores = [errors[method, h] for h in (3, 5, 10)] + [overall_errors[method]]
        summary.append(f"| {method} | " + " | ".join(f"{v:.3f}" for v in scores) + " |")
    summary.extend([
        "",
        "Run with `py novel_market_demo.py` on Windows. These results compare "
        "forecasting rules using observed index prices.",
    ])
    report = "\n".join(summary) + "\n"
    (output / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
