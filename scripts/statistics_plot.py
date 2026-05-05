"""Generate a time vs population growth chart from the simulation."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import matplotlib.pyplot as plt


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.simulation import Simulador


def resolve_output_path(output: Path | None) -> Path | None:
    """Resolve relative output paths inside the repository results folder."""
    if output is None:
        return None

    if output.is_absolute():
        return output

    return ROOT_DIR / "results" / output.name


def build_chart(male_count: int, female_count: int, years: int, output: Path | None) -> None:
    """Run the simulation and plot population growth over time."""
    simulation = Simulador(H=male_count, M=female_count)
    history = simulation.run(years)

    # history ahora es una lista de tuplas (tiempo, poblacion)
    timeline = [t for t, _ in history]
    population = [p for _, p in history]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(timeline, population, color="#1f77b4", linewidth=2.5)
    ax.fill_between(timeline, population, color="#1f77b4", alpha=0.12)

    ax.set_title("Tiempo vs Crecimiento poblacional", fontsize=16, pad=14)
    ax.set_xlabel("Tiempo simulado (años)")
    ax.set_ylabel("Población total")
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()

    if output is None:
        plt.show()
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=160, bbox_inches="tight")
        print(f"Gráfica guardada en: {output}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Grafica el crecimiento poblacional en función del tiempo simulado."
    )
    parser.add_argument("--hombres", type=int, default=100, help="Cantidad inicial de hombres.")
    parser.add_argument("--mujeres", type=int, default=100, help="Cantidad inicial de mujeres.")
    parser.add_argument("--anios", type=int, default=100, help="Duración de la simulación en años.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results") / "population_growth.png",
        help="Ruta del archivo PNG de salida. Usa una ruta vacía para mostrar la ventana.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Muestra la ventana del gráfico en lugar de guardarlo.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_path = None if args.show else resolve_output_path(args.output)
    build_chart(args.hombres, args.mujeres, args.anios, output_path)