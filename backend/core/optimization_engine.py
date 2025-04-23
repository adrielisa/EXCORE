
import pandas as pd
import json
import logging
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, value
from services.data_preparation import transform_sheet_to_long_format, build_data_dict

def run_optimization(excel_data: dict) -> dict:
    logging.info("Starting optimization process...")

    long_data = []
    for sheet in ["Supply_Demand", "Yield", "Wafer Plan", "Boundary Conditions", "Density per Wafer"]:
        logging.info(f"Processing sheet: {sheet}")
        df_long = transform_sheet_to_long_format(excel_data[sheet], sheet)
        long_data.append(df_long)
    combined_df = pd.concat(long_data, ignore_index=True)
    logging.info("Data transformation completed.")

    # Diccionarios clave
    effective_demand = build_data_dict(combined_df, "Supply_Demand", "EffectiveDemand")
    yielded_supply = build_data_dict(combined_df, "Supply_Demand", "Yielded Supply")
    safety_stock = build_data_dict(combined_df, "Supply_Demand", "Safety Stock Target")
    initial_inventory = build_data_dict(combined_df, "Supply_Demand", "Total Projected Inventory Balance")
    yield_values = build_data_dict(combined_df, "Yield")
    wafer_plan = {}  # 'Wafer Plan' no se usará, ya que 'Boundary Conditions' contiene los límites relevantes
    density = build_data_dict(combined_df, "Density per Wafer")
    boundary_conditions = build_data_dict(combined_df, "Boundary Conditions")

    # Variables
    model = LpProblem("Production_Optimization", LpMinimize)
    products = list(effective_demand.keys())
    periods = list(next(iter(effective_demand.values())).keys())

    x = {(p, t): LpVariable(f"x_{p}_{t}", lowBound=0) for p in products for t in periods}
    I = {(p, t): LpVariable(f"I_{p}_{t}", lowBound=0) for p in products for t in periods}
    W = {(p, t): LpVariable(f"W_{p}_{t}", lowBound=0) for p in products for t in periods}
    W5 = {(p, t): LpVariable(f"W5_{p}_{t}", lowBound=0, cat='Integer') for p in products for t in periods}

    
    # Congelar producción en Q+1 y Q+2 (ajustar los periodos según corresponda)
    frozen_periods = ['Q2 03', 'Q3 03']
    for p in products:
        for t in frozen_periods:
            if (p, t) in x:
                model += x[(p, t)] == 0
                model += W[(p, t)] == 0
                model += W5[(p, t)] == 0

    E = {(p, t): LpVariable(f"E_{p}_{t}", lowBound=0) for p in products for t in periods}
# Restricciones
    for p in products:
        for i, t in enumerate(periods):
            I_prev = initial_inventory.get(p, {}).get(t, 0) if i == 0 else I[(p, periods[i - 1])]
            W_prev = 0 if i == 0 else W[(p, periods[i - 1])]
            D = effective_demand.get(p, {}).get(t, 0)
            SST = safety_stock.get(p, {}).get(t, 0)
            Y = yield_values.get(p, {}).get(t, 1)
            dens = list(density.get(p, {}).values())[0] if p in density else 1

            if (YS := yielded_supply.get(p, {}).get(t)) is not None:
                model += x[(p, t)] <= YS
            if (cap := wafer_plan.get(p, {}).get(t)) is not None:
                model += W[(p, t)] <= cap
            if (bound := boundary_conditions.get(p, {}).get(t)) is not None:
                model += W[(p, t)] <= bound

            model += I[(p, t)] == I_prev + x[(p, t)] - D
            model += x[(p, t)] == Y * dens * W[(p, t)]
            model += W[(p, t)] == 5 * W5[(p, t)]
            if i > 0:
                model += W[(p, t)] - W_prev <= 560
            if SST and SST > 0:
                model += I[(p, t)] >= 70_000_000
                model += I[(p, t)] <= 140_000_000

    for t in periods:
        model += lpSum(W[(p, t)] for p in products) >= 350

    for p in products:
        model += I[(p, periods[-1])] == 0

    
    # Restricciones para calcular el exceso de inventario por producto y periodo
    for p in products:
        for t in periods:
            model += E[(p, t)] >= I[(p, t)] - safety_stock.get(p, {}).get(t, 0)
# Función objetivo: minimizar inventario total
    # Función objetivo ponderada por prioridad de productos
    weights = {"21A": 1, "22B": 3, "23C": 5}
    # Función objetivo ponderada por prioridad de productos + penalización del exceso
    weights = {"21A": 1, "22B": 3, "23C": 5}
    excess_penalty = {"21A": 1, "22B": 2, "23C": 5}
    model += lpSum(weights[p] * I[(p, t)] + excess_penalty[p] * E[(p, t)] for p in products for t in periods), "MinimizeInventoryAndExcess"

    model.solve()

    results = {
        "summary": {
            "status": model.status,
            "objective": value(model.objective)
        },
        "production_plan": {
            p: {t: x[(p, t)].varValue for t in periods}
            for p in products
        },
        "inventory": {
            p: {t: I[(p, t)].varValue for t in periods}
            for p in products
        },
        "wafer_production": {
            p: {t: W[(p, t)].varValue for t in periods}
            for p in products
        },
        "wafer_multiples": {
            p: {t: W5[(p, t)].varValue for t in periods}
            for p in products
        },
        "excess": {
            p: {t: E[(p, t)].varValue for t in periods}
            for p in products
        }
    }

    with open("results/results.json", "w") as f:
        json.dump(results, f, indent=2)

    rows = []
    for p in products:
        for t in periods:
            rows.extend([
                {"Product ID": p, "Period": t, "Variable": "x", "Value": x[(p, t)].varValue},
                {"Product ID": p, "Period": t, "Variable": "W", "Value": W[(p, t)].varValue},
                {"Product ID": p, "Period": t, "Variable": "W5", "Value": W5[(p, t)].varValue},
                {"Product ID": p, "Period": t, "Variable": "I", "Value": I[(p, t)].varValue},
                {"Product ID": p, "Period": t, "Variable": "E", "Value": E[(p, t)].varValue}
            ])
    pd.DataFrame(rows).to_csv("results/production_plan.csv", index=False)
    return results
