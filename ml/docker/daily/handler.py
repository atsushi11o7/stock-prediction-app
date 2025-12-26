"""
Lambda handler for daily inference pipeline
"""

import json
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, "/var/task/src")


def lambda_handler(event, context):
    """
    Daily pipeline Lambda handler

    Runs: fetch_daily_universe + predict
    """
    print("Lambda handler started", flush=True)

    try:
        # Import pipeline functions
        from pipeline.daily_pipeline import run_daily_data_fetch, run_daily_inference

        fetch_config = Path("config/fetch_daily_universe.yaml")
        predict_config = Path("config/predict.yaml")

        print(f"Fetch config: {fetch_config}", flush=True)
        print(f"Predict config: {predict_config}", flush=True)

        # Step 1: Fetch daily data
        print("Step 1: Fetching daily data...", flush=True)
        fetch_success = run_daily_data_fetch(fetch_config)

        if not fetch_success:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Data fetch failed"}),
            }

        print("Step 1 completed successfully", flush=True)

        # Step 2: Run inference
        print("Step 2: Running inference...", flush=True)
        inference_success = run_daily_inference(predict_config)

        if not inference_success:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Inference failed"}),
            }

        print("Step 2 completed successfully", flush=True)
        print("Daily pipeline completed!", flush=True)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Daily pipeline completed successfully"}),
        }

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        tb = traceback.format_exc()
        print(f"Error: {error_msg}", flush=True)
        print(f"Traceback:\n{tb}", flush=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": error_msg,
                "traceback": tb[-2000:] if tb else None,
            }),
        }
