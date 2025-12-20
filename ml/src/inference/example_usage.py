#!/usr/bin/env python3
# ml/src/inference/example_usage.py

"""
Example usage of inference results
"""

import json
from pathlib import Path


def example_1_view_single_ticker():
    """Example 1: View prediction for a single ticker"""
    print("=" * 60)
    print("Example 1: Single Ticker Prediction")
    print("=" * 60)

    predictions_path = Path("/workspace/ml/predictions/latest.json")

    if not predictions_path.exists():
        print(f"\n[ERROR] Predictions file not found: {predictions_path}")
        print("Please run predict.py first to generate predictions.")
        return

    with open(predictions_path, "r") as f:
        results = json.load(f)

    # Find JT (2914.T)
    jt_pred = next(
        (p for p in results["predictions"] if p["ticker"] == "2914.T"),
        None
    )

    if jt_pred:
        print(f"\nTicker: {jt_pred['ticker']}")
        print(f"As of Date: {jt_pred['as_of_date']}")
        print(f"Current Price: ¥{jt_pred['current_price']:,.2f}")
        print(f"Predicted Price (12M): ¥{jt_pred['predicted_12m_price']:,.2f}")
        print(f"Expected Return: {jt_pred['predicted_12m_return']:+.2%}")
        print(f"Sector: {jt_pred['sector']}")
    else:
        print("\n[WARNING] Ticker 2914.T not found in predictions")


def example_2_top_predictions():
    """Example 2: Show top 10 predicted returns"""
    print("\n" + "=" * 60)
    print("Example 2: Top 10 Predicted Returns (12M)")
    print("=" * 60)

    predictions_path = Path("/workspace/ml/predictions/latest.json")

    if not predictions_path.exists():
        print(f"\n[ERROR] Predictions file not found: {predictions_path}")
        return

    with open(predictions_path, "r") as f:
        results = json.load(f)

    # Sort by predicted return
    sorted_preds = sorted(
        results["predictions"],
        key=lambda x: x["predicted_12m_return"],
        reverse=True
    )

    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Total predictions: {results['num_predictions']}\n")

    for i, pred in enumerate(sorted_preds[:10], 1):
        print(
            f"{i:2d}. {pred['ticker']:8s} | "
            f"¥{pred['current_price']:>7,.0f} → ¥{pred['predicted_12m_price']:>7,.0f} | "
            f"{pred['predicted_12m_return']:+6.2%} | "
            f"{pred['sector']}"
        )


def example_3_sector_analysis():
    """Example 3: Sector-wise average returns"""
    print("\n" + "=" * 60)
    print("Example 3: Sector Average Returns (12M)")
    print("=" * 60)

    predictions_path = Path("/workspace/ml/predictions/latest.json")

    if not predictions_path.exists():
        print(f"\n[ERROR] Predictions file not found: {predictions_path}")
        return

    with open(predictions_path, "r") as f:
        results = json.load(f)

    # Group by sector
    from collections import defaultdict
    sector_data = defaultdict(list)

    for pred in results["predictions"]:
        sector = pred["sector"]
        sector_data[sector].append(pred["predicted_12m_return"])

    # Calculate averages
    sector_avg = {
        sector: sum(returns) / len(returns)
        for sector, returns in sector_data.items()
    }

    # Sort by average return
    sorted_sectors = sorted(
        sector_avg.items(),
        key=lambda x: x[1],
        reverse=True
    )

    print()
    for sector, avg_return in sorted_sectors:
        count = len(sector_data[sector])
        print(f"  {sector:30s} ({count:2d} stocks): {avg_return:+6.2%}")


def example_4_price_changes():
    """Example 4: Show expected price changes"""
    print("\n" + "=" * 60)
    print("Example 4: Expected Price Changes (12M)")
    print("=" * 60)

    predictions_path = Path("/workspace/ml/predictions/latest.json")

    if not predictions_path.exists():
        print(f"\n[ERROR] Predictions file not found: {predictions_path}")
        return

    with open(predictions_path, "r") as f:
        results = json.load(f)

    # Calculate price change
    predictions_with_change = []
    for pred in results["predictions"]:
        price_change = pred["predicted_12m_price"] - pred["current_price"]
        predictions_with_change.append({
            **pred,
            "price_change": price_change
        })

    # Sort by absolute price change
    sorted_by_change = sorted(
        predictions_with_change,
        key=lambda x: abs(x["price_change"]),
        reverse=True
    )

    print()
    for i, pred in enumerate(sorted_by_change[:10], 1):
        direction = "↑" if pred["price_change"] > 0 else "↓"
        print(
            f"{i:2d}. {pred['ticker']:8s} | "
            f"¥{pred['current_price']:>7,.0f} {direction} ¥{abs(pred['price_change']):>6,.0f} | "
            f"{pred['predicted_12m_return']:+6.2%}"
        )


def example_5_summary_statistics():
    """Example 5: Summary statistics"""
    print("\n" + "=" * 60)
    print("Example 5: Summary Statistics")
    print("=" * 60)

    predictions_path = Path("/workspace/ml/predictions/latest.json")

    if not predictions_path.exists():
        print(f"\n[ERROR] Predictions file not found: {predictions_path}")
        return

    with open(predictions_path, "r") as f:
        results = json.load(f)

    import numpy as np

    returns = [p["predicted_12m_return"] for p in results["predictions"]]
    log_returns = [p["predicted_12m_log_return"] for p in results["predictions"]]

    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Model: {results['model_path']}")
    print(f"\nPredictions: {results['num_predictions']}")
    print(f"Errors: {results['num_errors']}")

    print("\nReturn Statistics:")
    print(f"  Mean:   {np.mean(returns):+.2%}")
    print(f"  Median: {np.median(returns):+.2%}")
    print(f"  Std:    {np.std(returns):.2%}")
    print(f"  Min:    {np.min(returns):+.2%}")
    print(f"  Max:    {np.max(returns):+.2%}")

    print("\nLog Return Statistics:")
    print(f"  Mean:   {np.mean(log_returns):+.6f}")
    print(f"  Median: {np.median(log_returns):+.6f}")
    print(f"  Std:    {np.std(log_returns):.6f}")
    print(f"  Min:    {np.min(log_returns):+.6f}")
    print(f"  Max:    {np.max(log_returns):+.6f}")

    # Count positive/negative predictions
    positive = sum(1 for r in returns if r > 0)
    negative = sum(1 for r in returns if r < 0)
    neutral = sum(1 for r in returns if r == 0)

    print(f"\nDirection:")
    print(f"  Positive: {positive} ({positive/len(returns)*100:.1f}%)")
    print(f"  Negative: {negative} ({negative/len(returns)*100:.1f}%)")
    print(f"  Neutral:  {neutral} ({neutral/len(returns)*100:.1f}%)")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Inference Results - Usage Examples")
    print("=" * 60)

    try:
        example_1_view_single_ticker()
        example_2_top_predictions()
        example_3_sector_analysis()
        example_4_price_changes()
        example_5_summary_statistics()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
