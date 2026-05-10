"""Random sampling helpers used by the population simulation."""

import math    # Provides mathematical functions.
import random  # Random number utilities for probabilistic sampling.
from scripts.tables import MEDIA_SOLO, prob_by_age  # Probability tables and lookup helper.


# RANDOM SAMPLER ---------------------------------------------
class RandomSampler:
    """Utilities for random sampling from probability distributions."""
    
    @staticmethod
    def sample(dic):
        """Sample a value from a dictionary of probabilities."""
        items = list(dic.items())
        if not items:
            raise ValueError("sample() cannot receive an empty dictionary")

        # Calculate total probability
        total = sum(prob for _, prob in items)
        if total <= 0:
            raise ValueError("sample() requires positive probabilities")

        # Generate random threshold and accumulate probabilities
        umbral = random.random() * total
        acumulado = 0.0

        for valor, prob in items:
            acumulado += prob
            if umbral < acumulado:
                return valor

        return items[-1][0]

    @staticmethod
    def lambda_solo(age):
        """Calculate the rate parameter for exponential distribution of solitude time."""
        # Compute lambda for exponential distribution based on age group
        media = prob_by_age(age, MEDIA_SOLO)
        return 1/media if media > 0 else 0

    @staticmethod
    def sample_exponencial(lmbda):
        """Sample from exponential distribution using inverse transform.
        Returns time in years (assuming lambda is per month)."""

        if lmbda <= 0:
            return 0

        # Uniform(0,1)
        u = random.random()

        # Inverse transform: X = -ln(U) / lambda
        x_months = -math.log(u) / lmbda

        # Convert months → years
        return x_months / 12
    
    @staticmethod
    def time_step(lam=1.5, min_dias=1, max_anos=5):
        """Return a random time jump (in years) sampled from an exponential
        distribution with rate `lam`, constrained to fall between `min_dias`
        and `max_anos`, using inverse transform sampling."""

        # Convert constraints to years
        min_t = min_dias / 365
        max_t = max_anos

        while True:
            # Uniform(0,1)
            u = random.random()
            # Inverse transform: X = -ln(U) / lambda
            dt = -math.log(u) / lam

            # Accept only if within bounds
            if min_t <= dt <= max_t:
                return dt