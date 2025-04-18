# backend/api/results.py

from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter()

@router.get("/results", tags=["Results"])
def get_results():
    """
    Return the latest optimization results stored in results.json
    """
    result_path = "results/results.json"

    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="No results found. Please run the optimizer first.")

    with open(result_path, "r") as f:
        results = json.load(f)

    return results
