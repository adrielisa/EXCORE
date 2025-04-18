# backend/api/optimize.py
from fastapi import APIRouter
from services.data_loader import load_excel_data
from core.optimization_engine import run_optimization
import json

router = APIRouter()

@router.post("/optimize")
async def optimize_model():
    """
    Run the optimization model using the last uploaded Excel file.
    """
    file_path = "temp/Hackaton DB Final.xlsx"  # You can improve this later to support custom filenames

    try:
        data = load_excel_data(file_path)
        results = run_optimization(data)

        # Save results to results.json
        with open("results/results.json", "w") as f:
            json.dump(results, f, indent=2)

        return {"message": "Optimization complete", "results_summary": results.get("summary", {})}

    except Exception as e:
        return {"error": str(e)}
