"""Probability tables and age-based lookup utilities for the simulation."""


def prob_by_age(age, tabla, is_death_table=False):
    """
    Return the probability for an age range lookup table.
    If is_death_table=True, convert tramo probability to monthly probability.
    """
    for a, b, p in tabla:
        if a <= age < b:
            if not is_death_table:
                return p  # normal tables (embarazo, pareja, etc.)
            
            # death table → convert tramo probability to monthly probability
            months = (b - a) * 12
            p_month = 1.0 - (1.0 - p) ** (1.0 / months)
            return p / (b-a)

    return 0.0


# Probability of death for males by age range (annualized rates)
PROB_MUERTE_H = [(0,12,0.25),(12,45,0.1),(45,76,0.3),(76,125,0.7), (125, 999, 1.0)]

# Probability of death for females by age range (annualized rates)
PROB_MUERTE_M = [(0,12,0.25),(12,45,0.15),(45,76,0.35),(76,125,0.65), (125, 999, 1.0)]

# Probability of pregnancy by age range
PROB_EMBARAZO = [(12,15,0.2),(15,21,0.45),(21,35,0.8),(35,45,0.4),(45,60,0.2),(60,126,0.05)]

# Probability of wanting a partner by age range
PROB_QUERER_PAREJA = [(12,15,0.6),(15,21,0.65),(21,35,0.8),(35,45,0.6),(45,60,0.5),(60,126,0.2)]

# Probability of forming a couple depending on age difference
PROB_FORMAR_PAREJA = [(0,5,0.45),(5,10,0.4),(10,15,0.35),(15,20,0.25),(20,999,0.15)]

# Probability of breakup (constant across ages)
PROB_RUPTURA = 0.2

# Average time spent alone after breakup, by age range (in months)
MEDIA_SOLO = [(12,15,3),(15,21,6),(21,35,6),(35,45,12),(45,60,24),(60,126,48)]

# Raw distribution of number of babies per pregnancy (weights)
_bebes_raw = {1:0.7,2:0.18,3:0.08,4:0.04,5:0.02}

# Normalize so probabilities sum exactly to 1.0
_bebes_total = sum(_bebes_raw.values())
PROB_BEBES = {k: v/_bebes_total for k,v in _bebes_raw.items()}

# Raw distribution of desired number of children
DESEO_RAW = {1:0.6,2:0.75,3:0.35,4:0.2,5:0.1,6:0.016,7:0.016,8:0.016}

# Normalize so probabilities sum exactly to 1.0
total = sum(DESEO_RAW.values())
PROB_DESEO = {k:v/total for k,v in DESEO_RAW.items()}