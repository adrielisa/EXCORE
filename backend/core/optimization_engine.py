# core/optimization_engine.py

import pandas as pd
import json
import logging
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, value
from services.data_preparation import transform_sheet_to_long_format, build_data_dict

def run_optimization(excel_data: dict) -> dict:
    logging.info("Starting optimization process...")
    try:
        # === STEP 1: Load and transform Excel sheets ===
        long_data = []
        for sheet in ["Supply_Demand", "Yield", "Wafer Plan", "Boundary Conditions", "Density per Wafer"]:
            logging.info(f"Processing sheet: {sheet}")
            df_long = transform_sheet_to_long_format(excel_data[sheet], sheet)
            long_data.append(df_long)
        combined_df = pd.concat(long_data, ignore_index=True)
        logging.info("Data transformation completed.")
        logging.info(f"Combined DataFrame preview:\n{combined_df.head(20)}")

        logging.info("Building effective demand dictionary...")
        effective_demand = build_data_dict(combined_df, "Supply_Demand", "EffectiveDemand")
        if not effective_demand:
            raise ValueError("Effective demand dictionary is empty. Check the input data.")
        logging.info(f"Effective demand dictionary: {effective_demand}")

        yielded_supply = build_data_dict(combined_df, "Supply_Demand", "Yielded Supply")
        safety_stock = build_data_dict(combined_df, "Supply_Demand", "Safety Stock Target")

        try:
            initial_inventory = build_data_dict(combined_df, "Supply_Demand", "On Hand (Finished Goods)")
        except ValueError:
            logging.warning("'On Hand (Finished Goods)' no se encontró. Continuando sin inventario inicial.")
            initial_inventory = {}

        yield_values = build_data_dict(combined_df, "Yield")

        try:
            wafer_plan = build_data_dict(combined_df, "Wafer Plan", attribute_filter="Available Capacity")
        except ValueError:
            logging.warning("'Available Capacity' no se encontró en 'Wafer Plan'. Continuando sin plan de wafers.")
            wafer_plan = {}

        try:
            density = build_data_dict(combined_df, "Density per Wafer")
        except ValueError:
            logging.warning("'Density per Wafer' no se encontró. Continuando sin densidad.")
            density = {}

        # === STEP 3: Declare model and variables ===
        model = LpProblem("Production_Planning_Model", LpMinimize)
        products = list(effective_demand.keys())
        periods = list(next(iter(effective_demand.values())).keys())

        x = {(p, t): LpVariable(f"x_{p}_{t}", lowBound=0) for p in products for t in periods}
        I = {(p, t): LpVariable(f"I_{p}_{t}", lowBound=0) for p in products for t in periods}
        S = {(p, t): LpVariable(f"S_{p}_{t}", lowBound=0) for p in products for t in periods}
        E = {(p, t): LpVariable(f"E_{p}_{t}", lowBound=0) for p in products for t in periods}
        W = {(p, t): LpVariable(f"W_{p}_{t}", lowBound=0) for p in products for t in periods}
        SSV = {(p, t): LpVariable(f"SSV_{p}_{t}", cat=LpBinary) for p in products for t in periods}

        # === STEP 4: Improved Constraints ===
        M = 1e6  # Reduced to prevent exaggerated values

        for p in products:
            for i, t in enumerate(periods):
                I_prev = 0 if i == 0 else I[(p, periods[i - 1])]
                D = effective_demand.get(p, {}).get(t, 0)
                SST = safety_stock.get(p, {}).get(t, 0)
                yield_factor = yield_values.get(p, {}).get(t, 1)
                density_factor = list(density.get(p, {}).values())[0] if p in density else 1

                # Restricciones condicionales válidas
                YS = yielded_supply.get(p, {}).get(t)
                if YS is not None:
                    model += x[(p, t)] <= YS, f"ProductionLimit_{p}_{t}"

                wafer_cap = wafer_plan.get(p, {}).get(t)
                if wafer_cap is not None:
                    model += W[(p, t)] <= wafer_cap, f"WaferLimit_{p}_{t}"

                # Restricciones normales
                model += I[(p, t)] == I_prev + x[(p, t)] - D + S[(p, t)], f"InventoryBalance_{p}_{t}"
                model += I[(p, t)] >= SST - M * SSV[(p, t)], f"SafetyStock_{p}_{t}"
                model += S[(p, t)] >= D - (x[(p, t)] + I_prev), f"Shortage_{p}_{t}"
                model += E[(p, t)] >= I[(p, t)] - SST, f"Excess_{p}_{t}"
                model += x[(p, t)] == yield_factor * density_factor * W[(p, t)], f"WaferConversion_{p}_{t}"


        # === STEP 5: Improved Objective Function ===
        alpha = 10    # Cost per unit of unmet demand
        beta = 5      # Cost per unit of excess inventory
        delta = 1000  # High penalty for violating safety stock
        gamma = 1     # Small penalty for holding inventory

        model += lpSum(
            alpha * S[(p, t)] +
            beta * E[(p, t)] +
            delta * SSV[(p, t)] +
            gamma * I[(p, t)]
            for p in products for t in periods
        ), "MinimizeTotalCost"

        # === STEP 6: Solve the model ===
        model.solve()

        # === STEP 7: Build and save results ===
        results = {
            "summary": {
                "status": model.status,
                "objective": value(model.objective)
            },
            "production_plan": {
                p: {
                        t: x[(p, t)].varValue for t in periods
                    } for p in products
    }
        }

        with open("results/results.json", "w") as f:
            json.dump(results, f, indent=2)

        return results

    except Exception as e:
        logging.error(f"Error during optimization: {str(e)}", exc_info=True)
        raise
