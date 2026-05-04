# 👥 Human Population Simulation

A discrete-event population simulator modeling demographic dynamics with realistic life events and probabilistic behaviors.

## 📖 Overview

This project simulates population evolution over time by modeling individuals with realistic life cycles. Each person has attributes such as age, sex, and partnership status; the simulator processes monthly events that affect population dynamics.

## 🎯 Key Features

- **Individual agents**: Each person is modeled with age, sex, partnership status, and reproductive desires.
- **Life events**: Deaths, partnership formation and breakups, births, monthly aging, and emotional recovery periods.
- **Probabilistic models**: Age-based tables for mortality, pregnancy, desire for partnership, success in forming partnerships, and multiplicity distribution for births.
- **Time-series tracking**: Record population size month by month.

## 🏗️ Structure (brief)

- `Person`: represents an individual (age, sex, partner, children, alive status)
- `Simulador`: manages populations, runs monthly steps, and processes demographic events

Typical monthly step order: age → deaths → recovery after breakups → partnership desire → partnership formation → breakups → pregnancies/births.

## 🚀 How to run

Requirements:

- Python 3.8 or newer

From the project root (Windows):

```powershell
py index.py
```

Or (Linux/macOS / environments with `python`):

```bash
python index.py
```

If `index.py` accepts parameters, pass them as needed; by default it runs an example simulation.

## 🔧 Quick customization

Adjust probability tables and parameters in the code (search for variables like `PROB_MUERTE_H`, `PROB_EMBARAZO`, `PROB_QUERER_PAREJA`, `PROB_BEBES`) to explore different demographic scenarios.

## 📊 Output format

The population history is returned as a list where each index represents a month and contains the total number of living individuals at that month.

```python
history = [200, 205, 203, 198, ...]
```

## 🎓 Educational uses

- Teaching agent-based simulations
- Studies in population dynamics
- Examples of applied probabilistic models

---

**Contribute / Contact**: To improve probabilities, add visualizations, or build a web interface, open an issue or a pull request.

**License**: Add license information here if desired (e.g., MIT).

<p align="center">
  <strong>Created with ❤️ and curiosity for modeling</strong> 🧬
</p>
