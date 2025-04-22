# core/optimization_engine.py

import pandas as pd
import json
import logging
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, value
from services.data_preparation import transform_sheet_to_long_format, build_data_dict

def run_optimization(excel_data: dict) -> dict:
    logging.info("Starting optimization process...")
    try:
        # STEP 1: Transformación
        long_data = []
        for sheet in ["Supply_Demand", "Yield", "Wafer Plan", "Boundary Conditions", "Density per Wafer"]:
            logging.info(f"Processing sheet: {sheet}")
            df_long = transform_sheet_to_long_format(excel_data[sheet], sheet)
            long_data.append(df_long)
        combined_df = pd.concat(long_data, ignore_index=True)

        logging.info("Data transformation completed.")
        logging.info(f"Combined DataFrame preview:\n{combined_df.head(20)}")

        # STEP 2: Diccionarios
        effective_demand = build_data_dict(combined_df, "Supply_Demand", "EffectiveDemand")
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
        try:
            boundary_conditions = build_data_dict(combined_df, "Boundary Conditions")
        except ValueError:
            logging.warning("'Boundary Conditions' no se encontró. Continuando sin límites adicionales.")
            boundary_conditions = {}
    

        # STEP 3: Variables
        model = LpProblem("Production_Planning_Model", LpMinimize)
        products = list(effective_demand.keys())
        periods = list(next(iter(effective_demand.values())).keys())

        x = {(p, t): LpVariable(f"x_{p}_{t}", lowBound=0) for p in products for t in periods}
        I = {(p, t): LpVariable(f"I_{p}_{t}", lowBound=0) for p in products for t in periods}
        S = {(p, t): LpVariable(f"S_{p}_{t}", lowBound=0) for p in products for t in periods}
        E = {(p, t): LpVariable(f"E_{p}_{t}", lowBound=0) for p in products for t in periods}
        W = {(p, t): LpVariable(f"W_{p}_{t}", lowBound=0) for p in products for t in periods}
        W5 = {(p, t): LpVariable(f"W5_{p}_{t}", lowBound=0, cat="Integer") for p in products for t in periods}
        SSV = {(p, t): LpVariable(f"SSV_{p}_{t}", cat=LpBinary) for p in products for t in periods}
        
        # STEP 4: Restricciones
        M = 1e6
        for p in products:
            for i, t in enumerate(periods):
                I_prev = 0 if i == 0 else I[(p, periods[i - 1])]
                W_prev = 0 if i == 0 else W[(p, periods[i - 1])]
                D = effective_demand.get(p, {}).get(t, 0)
                SST = safety_stock.get(p, {}).get(t, 0)
                yield_factor = yield_values.get(p, {}).get(t, 1)
                density_factor = list(density.get(p, {}).values())[0] if p in density else 1

                # Límite por Yielded Supply
                if (YS := yielded_supply.get(p, {}).get(t)) is not None:
                    model += x[(p, t)] <= YS, f"ProductionLimit_{p}_{t}"

                # Límite por Wafer Plan
                if (wafer_cap := wafer_plan.get(p, {}).get(t)) is not None:
                    model += W[(p, t)] <= wafer_cap, f"WaferLimit_{p}_{t}"

                # 🔥 Nuevo: límite por Boundary Conditions
                if (boundary_limit := boundary_conditions.get(p, {}).get(t)) is not None:
                    model += W[(p, t)] <= boundary_limit, f"BoundaryLimit_{p}_{t}"

                # Balance de inventario
                model += I[(p, t)] == I_prev + x[(p, t)] - D + S[(p, t)], f"InventoryBalance_{p}_{t}"

                # Stock mínimo requerido
                model += I[(p, t)] >= SST - M * SSV[(p, t)], f"SafetyStock_{p}_{t}"

                # Faltantes y excesos
                model += S[(p, t)] >= D - (x[(p, t)] + I_prev), f"Shortage_{p}_{t}"
                model += E[(p, t)] >= I[(p, t)] - SST, f"Excess_{p}_{t}"

                # Conversión de Wafers a productos
                model += x[(p, t)] == yield_factor * density_factor * W[(p, t)], f"WaferConversion_{p}_{t}"

                # Múltiplos de 5
                model += W[(p, t)] == 5 * W5[(p, t)], f"MúltiplosDe5_{p}_{t}"

                # Ramp-up
                if i > 0:
                    model += W[(p, t)] - W_prev <= 560, f"RampUpLimit_{p}_{t}"

                # SST entre 70M y 140M
                if SST is not None and not pd.isna(SST) and SST > 0:
                    model += I[(p, t)] >= 70_000_000, f"SST_Min_{p}_{t}"
                    model += I[(p, t)] <= 140_000_000, f"SST_Max_{p}_{t}"

                # Restricción nueva: evitar sobreproducción innecesaria
                if D > 0 and SST > 0:
                    model += x[(p, t)] <= D + SST - I_prev + M * SSV[(p, t)], f"NoOverproduction_{p}_{t}"

        # Restricción: Mínimo de 350 wafers por semana entre todos los productos
        for t in periods:
            wafers_totales = lpSum(W[(p, t)] for p in products)
            model += wafers_totales >= 350, f"MinWafersTotal_{t}"

        # Restricción: Inventario final igual a 0
        for p in products:
            model += I[(p, periods[-1])] == 0, f"FinalInventoryZero_{p}"

        # STEP 5: Función objetivo con prioridad
        prioridad_pesos = {"21A": 3, "22B": 2, "23C": 1}
        alpha = 10
        beta = 5
        delta = 1000
        gamma = 1

        model += lpSum(
            prioridad_pesos.get(p, 1) * alpha * S[(p, t)] +
            beta * E[(p, t)] +
            delta * SSV[(p, t)] +
            gamma * I[(p, t)]
            for p in products for t in periods
        ), "MinimizeTotalCostWithPriorities"

        # STEP 6: Solve
        model.solve()

        # STEP 7: Resultados
        results = {
            "summary": {
                "status": model.status,
                "objective": value(model.objective)
            },
            "production_plan": {
                p: {t: x[(p, t)].varValue for t in periods}
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
                    {"Product ID": p, "Period": t, "Variable": "I", "Value": I[(p, t)].varValue},
                    {"Product ID": p, "Period": t, "Variable": "S", "Value": S[(p, t)].varValue},
                    {"Product ID": p, "Period": t, "Variable": "E", "Value": E[(p, t)].varValue},
                    {"Product ID": p, "Period": t, "Variable": "SSV", "Value": SSV[(p, t)].varValue},
                ])
        pd.DataFrame(rows).to_csv("results/production_plan.csv", index=False)

        logging.info(f"Optimization completed successfully. Objective: {value(model.objective)}")
        return results

    except Exception as e:
        logging.error(f"Error during optimization: {str(e)}", exc_info=True)
        raise
