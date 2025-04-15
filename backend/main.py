from fastapi import FastAPI
from pydantic import BaseModel
from pulp import LpProblem, LpVariable, lpSum, LpMinimize

app = FastAPI()

# Modelo de datos para la API
class OptimizationRequest(BaseModel):
    cycles: int  # Número de ciclos de producción
    yielded_supply: int
    on_hand: int
    safety_stock_target: int
    sellable_supply: int
    effective_demand: int
    total_inventory_balance: int
    inventory_excess: int
    seedstock: int
    max_capacity: int
    production_cost: float
    storage_cost: float

# Ruta para optimización
@app.post("/optimize")
def optimize(data: OptimizationRequest):
    # Crear el modelo de programación lineal
    model = LpProblem("Semiconductor_Production_Optimization", LpMinimize)

    # Variables de decisión por ciclo
    SP = {t: LpVariable(f"Produced_Supply_{t}", lowBound=0, cat="Integer") for t in range(1, data.cycles + 1)}
    I_t = {t: LpVariable(f"Projected_Inventory_{t}", lowBound=0, cat="Integer") for t in range(1, data.cycles + 1)}
    E_t = {t: LpVariable(f"Excess_Inventory_{t}", lowBound=0, cat="Integer") for t in range(1, data.cycles + 1)}
    RO = {t: LpVariable(f"Reorder_Optimization_{t}", lowBound=0, cat="Integer") for t in range(1, data.cycles + 1)}

    # Función objetivo: Minimizar costos de producción y almacenamiento
    model += lpSum(
        SP[t] * data.production_cost + I_t[t] * data.storage_cost for t in range(1, data.cycles + 1)
    ), "Cost_Minimization"

    # Restricciones por ciclo
    for t in range(1, data.cycles + 1):
        model += SP[t] <= data.max_capacity, f"Max_Capacity_{t}"
        model += SP[t] + data.on_hand >= data.effective_demand, f"Meet_Demand_{t}"
        model += I_t[t] >= data.safety_stock_target, f"Safety_Stock_{t}"
        model += E_t[t] == I_t[t] - data.safety_stock_target, f"Excess_Inventory_{t}"
        model += RO[t] == data.effective_demand - (SP[t] + I_t[t] - data.safety_stock_target), f"Reorder_Optimization_{t}"

    # Resolver el modelo
    model.solve()

    # Resultados por ciclo
    results = []
    for t in range(1, data.cycles + 1):
        results.append({
            "cycle": t,
            "optimal_production": SP[t].varValue,
            "final_inventory": I_t[t].varValue,
            "excess_inventory": E_t[t].varValue,
            "reorder_optimization": RO[t].varValue,
        })

    # Costo total
    total_cost = sum(SP[t].varValue * data.production_cost + I_t[t].varValue * data.storage_cost for t in range(1, data.cycles + 1))

    return {
        "results": results,
        "total_cost": total_cost
    }