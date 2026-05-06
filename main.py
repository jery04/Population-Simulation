"""Command-line entry point for running the population simulation charts."""

import argparse
from pathlib import Path  # File system path helpers.
from scripts.simulation import Simulador  # Main simulation engine.
from scripts.statistics_plot import build_chart, resolve_output_path  # Charting and output path utilities.

# MAIN --------------------------------------------------------------------
def main():
    """Run the statistics plot flow with configurable parameters."""
    parser = argparse.ArgumentParser(
        description="Simular crecimiento de población con parámetros ajustables."
    )
    parser.add_argument(
        "--male_count",
        type=int,
        default=100,
        help="Cantidad inicial de hombres (default: 100)"
    )
    parser.add_argument(
        "--female_count",
        type=int,
        default=100,
        help="Cantidad inicial de mujeres (default: 100)"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=100,
        help="Cantidad de años a simular (default: 100)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=100,
        help="Cantidad de corridas para la convergencia (default: 100)"
    )
    
    args = parser.parse_args()
    
    output_path = resolve_output_path(Path("population_growth_standard_deviation.png"))
    final_pop = build_chart(
        male_count=args.male_count,
        female_count=args.female_count,
        years=args.years,
        output=output_path,
        runs=args.runs,
        sigma=1,
        plot_all=False,
        show=False,
    )
    print(f"\n\033[32mMean final population across runs: {final_pop.__floor__()}\033[0m")


if __name__ == "__main__":
    main()

