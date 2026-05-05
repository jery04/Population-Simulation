"""Generate a time vs population growth chart from the simulation."""

from pathlib import Path  # filesystem paths
import matplotlib.pyplot as plt  # chart rendering
import statistics  # mean/stdev calculations
from scripts.simulation import Simulador  # simulation engine

ROOT_DIR = Path(__file__).resolve().parent.parent

def resample_population(history: list[tuple[float, int]], years: int) -> tuple[list[int], list[int]]:
    """Resample population history on a yearly grid using last-known values."""
    # Build a yearly grid and carry forward the last known population.
    timeline = list(range(0, years + 1))
    if not history:
        return timeline, [0] * len(timeline)

    pops: list[int] = []
    idx = 0
    current_pop = history[0][1]
    for year in timeline:
        # Advance through history until we reach the current year.
        while idx < len(history) and history[idx][0] <= year:
            current_pop = history[idx][1]
            idx += 1
        pops.append(current_pop)

    return timeline, pops

def resolve_output_path(output: Path | None) -> Path | None:
    """Resolve relative output paths inside the repository results folder."""
    if output is None:
        return None

    if output.is_absolute():
        return output

    # Keep relative outputs inside results/.
    return ROOT_DIR / "results" / output.name

def build_chart(
    male_count: int,
    female_count: int,
    years: int,
    output: Path | None,
    runs: int = 1,
    sigma: int = 1,
    plot_all: bool = False,
    show: bool = False,
) -> None:
    """Run the simulation multiple times and plot population statistics over time.

    If `runs` == 1 the behaviour is identical to before. For `runs` > 1 the
    function executes the simulation repeatedly, collects the population time
    series, computes mean and standard deviation per year and plots either
    the mean with ±sigma bands or all runs in grey + mean in red.
    """

    if runs <= 1:
        # Single run keeps the original event timeline.
        simulation = Simulador(H=male_count, M=female_count)
        history = simulation.run(years)
        timeline = [t for t, _ in history]
        population = [p for _, p in history]

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(timeline, population, color="#1f77b4", linewidth=2.5, label="Población")
        ax.fill_between(timeline, population, color="#1f77b4", alpha=0.12)
    else:
        all_populations: list[list[float]] = []
        timeline = None
        print(f"Ejecutando {runs} corridas de la simulación ({years} años cada una)...")
        for i in range(runs):
            print(f"  Corrida {i+1}/{runs}...", end="\r")
            sim = Simulador(H=male_count, M=female_count)
            history = sim.run(years)
            if timeline is None:
                # Resample to a shared yearly grid for comparison.
                timeline, pops = resample_population(history, years)
            else:
                _, pops = resample_population(history, years)
            all_populations.append(pops)
        print(f"  Corrida {runs}/{runs}... ✓")

        # Transpose to compute statistics per year.
        per_year = list(zip(*all_populations))

        means = [statistics.mean(col) for col in per_year]
        stdevs = [statistics.pstdev(col) for col in per_year]

        fig, ax = plt.subplots(figsize=(12, 7))

        if plot_all:
            # Plot each run in light gray for context.
            for pops in all_populations:
                ax.plot(timeline, pops, color="#777777", alpha=0.25, linewidth=0.8)
            # Highlight the mean in red.
            ax.plot(timeline, means, color="#d62728", linewidth=2.8, label=f"Media ({runs} corridas)", zorder=10)
        else:
            # Plot mean with sigma bands.
            ax.plot(timeline, means, color="#1f77b4", linewidth=2.8, label=f"Media ({runs} corridas)")
            lower = [m - sigma * s for m, s in zip(means, stdevs)]
            upper = [m + sigma * s for m, s in zip(means, stdevs)]
            ax.fill_between(
                timeline,
                lower,
                upper,
                color="#1f77b4",
                alpha=0.2,
                label=f"Intervalo ±{sigma}σ",
            )

        ax.legend(fontsize=11, loc="best", framealpha=0.95)

    ax.set_title(
        f"Convergencia Poblacional - {runs} {'corrida' if runs == 1 else 'corridas'} ({years} años)",
        fontsize=16,
        fontweight="bold",
        pad=16,
    )
    ax.set_xlabel("Tiempo simulado (años)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Población total", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.3, linewidth=0.7)
    ax.set_facecolor("#f8f9fa")

    fig.tight_layout()

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=160, bbox_inches="tight", facecolor="white")
        print(f"✓ Gráfica guardada en: {output}")

    if show or output is None:
        plt.show()



