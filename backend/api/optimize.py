# backend/api/optimize.py
from fastapi import APIRouter
from services.data_loader import load_excel_data
from core.optimization_engine import run_optimization
import json
import os

router = APIRouter()

@router.post("/optimize")
async def optimize_model():
    """
    Run the optimization model using the predefined Excel file.
    """
    file_path = "Hackaton DB Final 04.21.xlsx"  # Directly use the predefined file

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"error": f"File '{file_path}' not found. Please ensure it exists in the backend directory."}

    try:
        # Load and parse the Excel file
        data = load_excel_data(file_path)
        results = run_optimization(data)

        # Save results to results.json
        with open("results/results.json", "w") as f:
            json.dump(results, f, indent=2)

        return {"message": "Optimization complete", "results_summary": results.get("summary", {})}

    except Exception as e:
        return {"error": str(e)}

@router.get("/export-results")
async def export_results():
    """
    Export optimization results to CSV for Power BI integration.
    """
    results_file = "results/results.json"
    csv_file = "results/production_plan.csv"

    # Check if results.json exists
    if not os.path.exists(results_file):
        return {"error": "No optimization results found. Please run the optimization first."}

    try:
        # Load results from JSON
        with open(results_file, "r") as f:
            results = json.load(f)

        # Convert production plan to CSV
        production_plan = results.get("production_plan", {})
        if not production_plan:
            return {"error": "No production plan found in results."}

        os.makedirs("results", exist_ok=True)  # Ensure the results directory exists
        with open(csv_file, "w") as f:
            f.write("Product ID,Period,Value\n")
            for product, periods in production_plan.items():    
                for period, value in periods.items():
                    f.write(f"{product},{period},{value}\n")

        return {"message": "Results exported successfully", "csv_path": csv_file}

    except Exception as e:
        return {"error": f"An error occurred while exporting results: {str(e)}"}
