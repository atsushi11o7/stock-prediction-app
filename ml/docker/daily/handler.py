"""
Lambda handler for daily inference pipeline
"""

import json
import subprocess
import sys


def lambda_handler(event, context):
    """
    Daily pipeline Lambda handler

    Runs: fetch_daily_universe.py + predict.py
    """
    try:
        # Run daily pipeline
        result = subprocess.run(
            [
                sys.executable,
                "src/pipeline/daily_pipeline.py",
                "--fetch-config", "config/fetch_daily_universe.yaml",
                "--predict-config", "config/predict.yaml",
            ],
            capture_output=True,
            text=True,
            timeout=540,  # 9 minutes (Lambda max is 15 min)
        )

        if result.returncode != 0:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": "Pipeline failed",
                    "stderr": result.stderr[-1000:] if result.stderr else None,
                }),
            }

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Daily pipeline completed successfully",
                "stdout": result.stdout[-1000:] if result.stdout else None,
            }),
        }

    except subprocess.TimeoutExpired:
        return {
            "statusCode": 504,
            "body": json.dumps({"error": "Pipeline timeout"}),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
