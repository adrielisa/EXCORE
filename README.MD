# EXCORE - Micron HackathoN

This project is a functionald backend API built using FastAPI and PuLP to optimize production planning using linear programming and Excel data.

---

## Overview

The API automates production planning by:

* Accepting Excel files with product data.
* Running a linear programming model to optimize supply and demand.
* Providing the optimized production schedule and cost.

---

## 📂 API Endpoints

### `POST /upload-xlsx`

**Upload Excel File**

* Accepts a `.xlsx` file containing sheets like:
  * `Supply_Demand`
  * `Yield`
  * `Wafer Plan`
  * `Boundary Conditions`
  * `Density per Wafer`

**Returns:** JSON confirmation with available sheet names.

### `POST /optimize`

**Run Optimization Model**

* Processes the previously uploaded Excel file.
* Structures the data.
* Builds and solves a linear programming model.
* Saves the results into `results/results.json`.

**Returns:** Objective value and model status.

### `GET /results`

**Get Optimization Results**

* Reads the `results.json` file.
* Returns the final production plan (units per product per week).

**Returns:** JSON summary with:

* Status
* Objective value
* Production plan

### `POST /health`

**Health Check**

* Confirms backend availability.

---

## 🧠 What Does the Model Consider?

The model uses:

* `Effective Demand`
* `Yielded Supply`
* `On Hand Inventory`
* `Safety Stock Targets`
* `Wafer Availability`
* `Yield %`
* `Density per Wafer`

It minimizes the total cost using:

* Shortage penalties
* Excess inventory penalties
* Safety stock violations
* Inventory holding cost

---

## 🛠️ Technologies

* **Python 3.11**
* **FastAPI**
* **PuLP** (Linear Programming)
* **Pandas**
* **Uvicorn** (ASGI server)

---

## 🧪 How to Use

1. Start the backend:

```bash
uvicorn main:app --reload
```

2. Access Swagger UI at:

```
http://localhost:8000/docs
```

3. Upload Excel file → Run optimization → Fetch results.

---

## 🎯 Goal Alignment with Micron

This system fulfills Micron's challenge by:

* Automating production planning based on demand and constraints.
* Using real manufacturing data from Excel.
* Applying linear programming to maximize efficiency.
* Delivering a **fully functional prototype** ready for demonstration.

---

## 🧾 Deliverables

* ✅ API source code
* ✅ Excel sample (from Micron)
* ✅ Functional results file (`results.json`)
* ✅ README + Documentation

---

## Author

Talent Land 2025 - Micron Hackathon
