"""Command-line entry point for running the population simulation charts."""

from pathlib import Path

from scripts.simulation import Simulador  # Main simulation engine.
from scripts.statistics_plot import build_chart, resolve_output_path


def simulate_final_population(h=100, m=100, anos=100):
    """Run the simulation and return the final population count."""
    sim = Simulador(H=h, M=m)
    history = sim.run(anos)
    return history[-1][1] if history else 0


def main():
    """Run the statistics plot flow with fixed parameters."""
    output_path = resolve_output_path(Path("population_growth.png"))
    build_chart(
        male_count=100,
        female_count=100,
        years=100,
        output=output_path,
        runs=100,
        sigma=1,
        plot_all=False,
        show=False,
    )


if __name__ == "__main__":
    main()

