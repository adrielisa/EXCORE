# EXCORE - Micron HackathoN

This project is a functionald backend API built using FastAPI and PuLP to optimize production planning using linear programming and Excel data.

---

## Overview

The backend application performs production planning optimization by:

* Reading a pre-defined Excel file with supply chain data.
* Structuring the data from key sheets.
* Solving a linear programming model tailored to Micron's constraints.
* Exporting the results as CSV and JSON files for analysis and integration.


## How It Works

When the server starts:

1. The system automatically loads a fixed Excel file located in the backend.
2. The data from relevant sheets is transformed into a long format.
3. A linear programming model is built, considering real-world manufacturing constraints.
4. The model is solved using the CBC solver.
5. The optimized production plan and metrics are saved into `results/results.json` and `results/production_plan.csv`.


## Model Logic

The model incorporates:

* **Effective Demand**
* **Yielded Supply**
* **Safety Stock Targets (SST)**
* **Yield Rate**
* **Wafer Density**
* **Wafer Availability**
* **Inventory Balancing**
* **Shortage and Excess Costs**

### Constraints Implemented

* Demand and inventory balance per period.
* Weekly wafer ramp-up limit (≤ 560 wafers).
* Production must be in multiples of 5.
* SST bounds between 70M and 140M units.
* Minimum of 350 wafers per week (across all products).
* Zero inventory at the end of the planning horizon.

### Objective Function

The model minimizes the total cost by penalizing:

* Product shortages (weighted by product priority).
* Excess inventory.
* Safety stock violations.
* Holding inventory.


## Alignment with Micron's Requirements

The system addresses Micron’s optimization challenge by:

* Integrating Excel-based real production data.
* Applying custom constraints provided in the hackathon.
* Producing a detailed, structured output for analysis.
* Generating a functional backend suitable for real-world deployment and visualization in Power BI.


## Deliverables

* Backend source code (FastAPI + PuLP)
* Integrated Excel data processing pipeline
* Optimization results in CSV and JSON formats
* Power BI-ready data
* Documentation (README and presentation slides)


## Tech Stack

* Python 3.11
* FastAPI
* PuLP (Linear Programming)
* Pandas
* Uvicorn
