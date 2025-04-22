import os
import json
import logging
from fastapi import FastAPI
from services.data_loader import load_excel_data
from core.optimization_engine import run_optimization
from api import upload, optimize, results, health
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO, encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("backend.log"),  # Save logs to a file
        logging.StreamHandler()  # Print logs to the console
    ]
)

app = FastAPI()

app.include_router(upload.router)
app.include_router(optimize.router)
app.include_router(results.router)
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    """
    Automatically load the Excel file and run optimization on backend startup.
    """
    file_path = "Hackaton DB Final 04.21.xlsx"  # Path to the predefined Excel file

    logging.info("Starting backend initialization...")
    logging.info(f"Looking for Excel file at: {file_path}")

    # Check if the file exists
    if not os.path.exists(file_path):
        logging.error(f"File '{file_path}' not found. Please ensure it exists in the backend directory.")
        return

    try:
        # Load and parse the Excel file
        logging.info("Loading Excel file...")
        data = load_excel_data(file_path)
        logging.info(f"Excel file loaded successfully. Sheets: {list(data.keys())}")

        # Run optimization
        logging.info("Running optimization...")
        results = run_optimization(data)
        logging.info(f"Optimization completed successfully. Objective: {results['summary']['objective']}")

        # Save results to results.json
        os.makedirs("results", exist_ok=True)  # Ensure the results directory exists
        with open("results/results.json", "w") as f:
            json.dump(results, f, indent=2)
        logging.info("Results saved to 'results/results.json'.")

    except Exception as e:
        logging.error(f"An error occurred during startup optimization: {str(e)}", exc_info=True)
