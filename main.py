"""Command-line entry point for running the population simulation."""

from scripts.simulation import Simulador  # Main simulation engine.


if __name__ == "__main__":

    sim = Simulador(H=100, M=100)
    history = sim.run(100)

    # history es ahora [(tiempo, poblacion)], extraer la poblacion final
    final_time, final_pop = history[-1]
    print("Población final:", history[-1][1])
