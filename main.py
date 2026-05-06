"""Command-line entry point for running the population simulation charts."""

from pathlib import Path  # File system path helpers.
from scripts.simulation import Simulador  # Main simulation engine.
from scripts.statistics_plot import build_chart, resolve_output_path  # Charting and output path utilities.

# MAIN --------------------------------------------------------------------
def main():
    """Run the statistics plot flow with fixed parameters."""
    output_path = resolve_output_path(Path("population_growth_standard_deviation.png"))
    final_pop = build_chart(
        male_count=100,
        female_count=100,
        years=100,
        output=output_path,
        runs=100,
        sigma=1,
        plot_all=False,
        show=False,
    )
    print(f"Mean final population across runs: {final_pop.__floor__()}")


if __name__ == "__main__":
    main()

