"""
Lambda handler for monthly finetuning pipeline
"""

import json
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, "/var/task/src")


def lambda_handler(event, context):
    """
    Monthly pipeline Lambda handler

    Runs: enrich_universe + finetune
    """
    print("Lambda handler started", flush=True)

    try:
        # Import pipeline functions
        from pipeline.monthly_pipeline import run_enrich_universe, run_finetuning

        enrich_config = Path("config/enrich_universe.yaml")
        finetune_config = Path("config/finetune.yaml")

        print(f"Enrich config: {enrich_config}", flush=True)
        print(f"Finetune config: {finetune_config}", flush=True)

        # Step 1: Enrich universe
        print("Step 1: Enriching universe...", flush=True)
        enrich_success = run_enrich_universe(enrich_config)

        if not enrich_success:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Universe enrichment failed"}),
            }

        print("Step 1 completed successfully", flush=True)

        # Step 2: Run finetuning
        print("Step 2: Running finetuning...", flush=True)
        finetune_success = run_finetuning(finetune_config)

        if not finetune_success:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Finetuning failed"}),
            }

        print("Step 2 completed successfully", flush=True)
        print("Monthly pipeline completed!", flush=True)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Monthly pipeline completed successfully"}),
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
