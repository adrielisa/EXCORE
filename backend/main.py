
import os
import logging
from fastapi import FastAPI
from services.data_loader import load_excel_data
from core.optimization_engine import run_optimization
from api import upload, optimize, results, health

# Configurar logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI()

app.include_router(upload.router)
app.include_router(optimize.router)
app.include_router(results.router)
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    file_path = "Hackaton DB Final 04.21.xlsx"

    logging.info("Starting backend initialization...")
    logging.info(f"Looking for Excel file at: {file_path}")

    if not os.path.exists(file_path):
        logging.error(f"File '{file_path}' not found.")
        return

    try:
        logging.info("Loading Excel file...")
        data = load_excel_data(file_path)
        logging.info(f"Excel file loaded successfully. Sheets: {list(data.keys())}")

        logging.info("Running optimization model with real initial inventory...")
        run_optimization(data)

    except Exception as e:
        logging.error(f"An error occurred during startup optimization: {str(e)}", exc_info=True)
