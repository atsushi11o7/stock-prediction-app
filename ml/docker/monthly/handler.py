"""
Lambda handler for monthly finetuning pipeline
"""

import json
import subprocess
import sys


def lambda_handler(event, context):
    """
    Monthly pipeline Lambda handler

    Runs: enrich_universe.py + finetune.py
    """
    try:
        # Run monthly pipeline
        result = subprocess.run(
            [
                sys.executable,
                "src/pipeline/monthly_pipeline.py",
                "--enrich-config", "config/enrich_universe.yaml",
                "--finetune-config", "config/finetune.yaml",
            ],
            capture_output=True,
            text=True,
            timeout=840,  # 14 minutes (Lambda max is 15 min)
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
                "message": "Monthly pipeline completed successfully",
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
