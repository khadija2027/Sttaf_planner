# 🏥 Medical Staff Planner – Weekly, Monthly & Yearly Optimization

This project provides a **medical scheduling system** that optimizes the weekly, monthly, and yearly shift planning of doctors across various departments. It uses **linear programming (PuLP)** to assign staff while balancing workload, respecting availability, and covering all activity needs for a given hospital or clinic.

---

## 🧠 Core Objective

To **generate fair, feasible, and optimized medical duty schedules** by:

- Covering all department shift needs (e.g., Pédiatrie, Urgences, Néonatologie, etc.)
- Respecting each doctor's **specialty** and **availability**
- Limiting daily and weekly workload
- Automatically calculating **missing staff** (remplaçants)
- Providing **visual analytics** on assignments

---

## 📁 Project Structure

The project is modular, with 3 main files:

| File                | Description                                                  |
|---------------------|--------------------------------------------------------------|
| `weekly_medical_staff_planner.py` | Generates a doctor schedule week by week.                   |
| `monthly_medical_staff_planner.py`| Monthly planning with optimization and output export (CSV). |
| `yearly_medical_staff_planner.py` | (Planned) Consolidates all months for full-year optimization.|

---

## ⚙️ Technologies Used

- 🐍 Python 3.10+
- 📦 [PuLP](https://coin-or.github.io/pulp/) – Linear Programming solver
- 📊 Matplotlib – Data visualization
- 📁 Pandas – CSV export and data handling
- 🧮 `datetime` – Date manipulation

---

## 📌 Key Features

- ✅ **Shift assignment** based on availability and specialization
- 🧮 **Linear optimization** to minimize overwork and unmet needs
- 💤 Ensures rest after night shifts (`GA`)
- 📈 Weekly assignment tracking and load-balancing visualization
- 📄 CSV Export of:
  - All doctor assignments (`affectations_mois.csv`)
  - Missing staff (remplaçants) per shift (`remplacants_mois.csv`)
- 📷 Automatically generates a workload chart (`charges_medecins.png`)

---

## 🔍 Optimization Hints

- The planner uses **multi-objective optimization** to:
  - Minimize unfilled needs (`Z1`)
  - Balance non-priority tasks based on specialty weights (`Z3`)
- You can tweak priorities or weights in the `priorites` dictionary to test different strategies.
- Doctors unavailable during periods (e.g., leave) are excluded from assignment via constraints.

---

## 📤 Outputs

After solving the planning model, the system exports:

- ✅ Shift assignment summary
- ✅ Weekly breakdowns per doctor
- 📊 Doctor workload plot
- 📁 CSVs with all assignments and missing staff

---

## 🚀 How to Run

1. Install required packages:
   ```bash
   pip install pulp pandas matplotlib
