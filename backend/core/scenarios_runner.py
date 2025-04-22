# core/scenarios_runner.py

import json
import logging
from services.data_loader import load_excel_data
from core.optimization_engine import run_optimization

def run_all_scenarios():
    excel_path = "Hackaton DB Final 04.21.xlsx"
    data = load_excel_data(excel_path)

    # Escenario 1: inventario inicial = 0
    logging.info("Running scenario: Initial Inventory = 0")
    results_zero = run_optimization(data, initial_inventory_zero=True, output_suffix="_zero")
    with open("results/results_zero.json", "w") as f:
        json.dump(results_zero, f, indent=2)

    # Escenario 2: inventario inicial real
    logging.info("Running scenario: Initial Inventory = real")
    results_real = run_optimization(data, initial_inventory_zero=False, output_suffix="_real")
    with open("results/results_real.json", "w") as f:
        json.dump(results_real, f, indent=2)
