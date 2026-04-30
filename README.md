# 👥 Population Simulation

A discrete-event population simulator that models demographic dynamics through realistic life events and probabilistic behaviors.

## 📖 Overview

This project simulates the evolution of a population over time by modeling individuals with realistic life cycles. Each person has characteristics like age, gender, and partnership status, and the simulator processes monthly events that affect population dynamics.

## 🎯 Features

- **👤 Individual Agents**: Each person is modeled as an individual with age, gender, relationship status, and desires
- **💔 Life Events**: 
  - 💀 Death (age and gender-dependent mortality rates)
  - 💑 Partnership formation and breakups
  - 👶 Births based on age and partnership status
  - ⏳ Aging (monthly progression)
  - 💔 Emotional recovery periods after breakups

- **📊 Probabilistic Models**: Age-dependent probability tables for:
  - Mortality rates (different for males and females)
  - Pregnancy probability
  - Desire for partnership
  - Partnership formation success
  - Number of babies per birth

- **📈 Population Tracking**: Monitor total population across simulation months

## 🏗️ Architecture

### Core Classes

**`Persona`** - Individual entity with:
- `edad` (age in years)
- `sexo` (gender: 'H' for hombre/male, 'M' for mujer/female)
- `pareja` (current partner reference)
- `hijos` (number of children)
- `deseo_hijos` (desired number of children)
- `viva` (alive status)

**`Simulador`** - Population simulator that:
- Maintains populations of males and females
- Runs discrete monthly time steps
- Processes all demographic events

### Key Processes

Each simulation month executes in order:
1. **Aging**: All individuals age by 1 month
2. **Deaths**: Apply age-based mortality
3. **Solo time reduction**: Recovery from breakups
4. **Partnership desire**: Update who wants a partner
5. **Partnership formation**: Match available singles
6. **Breakups**: Random partnership dissolutions
7. **Pregnancies**: Generate new individuals

## 🚀 Usage

```python
# Create simulator with initial population
sim = Simulador(H=100, M=100)  # 100 males, 100 females

# Run for 1200 months (100 years)
historia = sim.run(meses=1200)

# Get results
print(historia)  # List of population sizes per month
```

## 📊 Probability Tables

The simulator uses realistic probability distributions:

- **Mortality**: Higher for very young and elderly populations
- **Pregnancy**: Peaks at reproductive years (15-35 for females)
- **Partnership desire**: Varies by age, higher in young adults
- **Baby distribution**: 70% singles, 18% twins, 8% triplets, etc.

## 🔧 Customization

Modify the probability tables to simulate different demographic scenarios:
- `PROB_MUERTE_H` / `PROB_MUERTE_M` - Mortality by gender
- `PROB_EMBARAZO` - Pregnancy rates by age
- `PROB_QUERER_PAREJA` - Partnership desire by age
- `PROB_BEBES` - Birth multiplicity distribution

## 💾 Data Structure

Population history is returned as a list where each index represents a month and contains the total number of living individuals at that time point.

```python
historia = [200, 205, 203, 198, ...]  # Population per month
```

## 🎓 Educational Uses

- Demographic simulation and modeling
- Agent-based simulation tutorials
- Population dynamics study
- Probability and statistics applications

## 📝 Notes

- Age ranges: 0-126 years
- Simulations use exponential distributions for solo period recovery
- Partnerships require mutual desire and age compatibility
- Breakups trigger emotional recovery periods before seeking new partners

---

<p align="center">
  <strong>Created with ❤️ by a simulation enthusiast</strong> 🧬
</p>
