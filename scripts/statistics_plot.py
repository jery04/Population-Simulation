"""Generate a time vs population growth chart from the simulation."""

from pathlib import Path  # filesystem paths
import matplotlib.pyplot as plt  # chart rendering
import statistics  # mean/stdev calculations
import math
from scripts.simulation import Simulador  # simulation engine

ROOT_DIR = Path(__file__).resolve().parent.parent # Project root directory

# UTILS -------------------------------------------------------------------
METRICS = {
    "population": {"label": "Population", "ylabel": "Total population", "color": "#1f77b4"},
    "births": {"label": "Births", "ylabel": "Cumulative births", "color": "#2ca02c"},
    "deaths": {"label": "Deaths", "ylabel": "Cumulative deaths", "color": "#d62728"},
    "pairs": {"label": "Pairs formed", "ylabel": "Cumulative pairs formed", "color": "#9467bd"},
    "breaks": {"label": "Breakups", "ylabel": "Cumulative breakups", "color": "#8c564b"},
}

def build_timeline(years: int) -> list[int]:
    """Build a yearly grid for resampling."""
    return list(range(0, years + 1))

def resample_series(history: list[tuple[float, int]], timeline: list[int]) -> list[int]:
    """Resample a history series on a shared yearly grid using last-known values."""
    if not history:
        return [0] * len(timeline)

    values: list[int] = []
    idx = 0
    current_value = history[0][1]
    for year in timeline:
        # Advance through history until we reach the current year.
        while idx < len(history) and history[idx][0] <= year:
            current_value = history[idx][1]
            idx += 1
        values.append(current_value)

    return values

def compute_series_stats(
    all_series: list[list[float]],
    runs: int,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Compute mean, stdev, and 95% confidence bounds across runs."""
    per_year = list(zip(*all_series))
    means = [statistics.mean(col) for col in per_year]
    stdevs = [statistics.pstdev(col) for col in per_year]

    # 95% confidence interval for the mean (approx normal assumption)
    # margin = z * (sigma / sqrt(n)), z ~ 1.96 for 95%
    z95 = 1.96
    margins95 = [z95 * (s / math.sqrt(runs)) for s in stdevs]
    lower95 = [m - d for m, d in zip(means, margins95)]
    upper95 = [m + d for m, d in zip(means, margins95)]

    return means, stdevs, lower95, upper95

def build_ci_path(out_path: Path | None, metric: str) -> Path:
    """Build a 95% confidence interval output path for the given metric."""
    if out_path is not None:
        base_dir = out_path.parent
        base_stem = out_path.stem
        suffix = out_path.suffix
    else:
        base_dir = ROOT_DIR / "results"
        base_stem = "population_growth"
        suffix = ".png"

    if base_stem.endswith("_standard_deviation"):
        base_stem = base_stem[: -len("_standard_deviation")]

    if metric == "population":
        name = f"{base_stem}_confidence_interval"
    else:
        name = f"{base_stem}_{metric}_confidence_interval"

    return base_dir / f"{name}{suffix}"

def plot_ci_chart(
    timeline: list[int],
    means: list[float],
    lower95: list[float],
    upper95: list[float],
    title: str,
    ylabel: str,
    color: str,
    output_path: Path,
) -> None:
    """Render and save a 95% confidence interval chart."""
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(timeline, means, color=color, linewidth=2.8, label="Mean")
    ax.fill_between(timeline, lower95, upper95, color=color, alpha=0.25, label="95% confidence interval")

    # Corner callouts keep the key CI values visible inside the image.
    final_mean = means[-1]
    final_lower = lower95[-1]
    final_upper = upper95[-1]
    corner_box = dict(boxstyle="round,pad=0.60", facecolor="white", edgecolor=color, alpha=0.92)
    ax.text(
        0.98,
        0.02,
        f"$\\bf{{Mean}}$: {int(round(final_mean))}\n$\\bf{{95\\%\\ CI}}$: [{int(round(final_lower))}, {int(round(final_upper))}]",
        transform=ax.transAxes,
        va="bottom",
        ha="right",
        fontsize=11,
        linespacing=1.25,
        bbox=corner_box,
    )
    ax.set_title(title, fontsize=16, fontweight="bold", pad=16)
    ax.set_xlabel("Simulated time (years)", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.3, linewidth=0.7)
    ax.legend(fontsize=11, loc="best", framealpha=0.95)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight", facecolor="white")
    print(f"✓ 95% confidence interval chart saved to: {output_path}")

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
) -> float:
    """Run the simulation multiple times and plot population statistics over time.

    If `runs` == 1 the behaviour is identical to before. For `runs` > 1 the
    function executes the simulation repeatedly, collects the population time
    series, computes mean and standard deviation per year and plots either
    the mean with ±sigma bands or all runs in grey + mean in red. It also
    saves 95% confidence interval charts for population and event counters.
    Returns the mean final population across all runs.
    """

    final_populations: list[int] = []

    # Resolve output inside results/ when a relative path is provided.
    out_path = resolve_output_path(output) if output is not None else None

    stats_by_metric: dict[str, tuple[list[float], list[float], list[float], list[float]]] | None = None
    timeline: list[float] | list[int]

    if runs <= 1:
        # Single run keeps the original event timeline.
        simulation = Simulador(H=male_count, M=female_count)
        history = simulation.run(years)
        population_history = history["population"]
        final_populations.append(population_history[-1][1] if population_history else 0)
        timeline = [t for t, _ in population_history]
        population = [p for _, p in population_history]

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(timeline, population, color="#1f77b4", linewidth=2.5, label="Population")
        ax.fill_between(timeline, population, color="#1f77b4", alpha=0.12)
    else:
        all_series: dict[str, list[list[float]]] = {key: [] for key in METRICS}
        timeline = build_timeline(years)
        print(f"Running {runs} simulation runs ({years} years each)...")

        for i in range(runs):
            print(f"  Run {i+1}/{runs}...", end="\r")
            sim = Simulador(H=male_count, M=female_count)
            history = sim.run(years)
            population_history = history["population"]
            final_populations.append(population_history[-1][1] if population_history else 0)

            for key in METRICS:
                series = resample_series(history[key], timeline)
                all_series[key].append(series)
        print(f"  Run {runs}/{runs}... ✓")

        stats_by_metric = {key: compute_series_stats(all_series[key], runs) for key in METRICS}
        means, stdevs, _, _ = stats_by_metric["population"]

        fig, ax = plt.subplots(figsize=(12, 7))

        if plot_all:
            # Plot each run in light gray for context.
            for pops in all_series["population"]:
                ax.plot(timeline, pops, color="#777777", alpha=0.25, linewidth=0.8)
            # Highlight the mean in red.
            ax.plot(timeline, means, color="#d62728", linewidth=2.8, label=f"Mean ({runs} runs)", zorder=10)
        else:
            # Plot mean with standard deviation bands.
            ax.plot(timeline, means, color="#1f77b4", linewidth=2.8, label=f"Mean ({runs} runs)")
            lower = [m - sigma * s for m, s in zip(means, stdevs)]
            upper = [m + sigma * s for m, s in zip(means, stdevs)]
            ax.fill_between(
                timeline,
                lower,
                upper,
                color="#1f77b4",
                alpha=0.2,
                label=f"±{sigma} standard deviations",
            )

        ax.legend(fontsize=11, loc="best", framealpha=0.95)

    ax.set_title(
        f"Population Convergence - {runs} {'run' if runs == 1 else 'runs'} ({years} years)",
        fontsize=16,
        fontweight="bold",
        pad=16,
    )
    ax.set_xlabel("Simulated time (years)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Total population", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.3, linewidth=0.7)
    ax.set_facecolor("#f8f9fa")

    fig.tight_layout()

    # Use resolved path (keeps results/ as the place for relative outputs).
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
        print(f"✓ Chart saved to: {out_path}")

    # If we ran multiple simulations, also save confidence interval plots for each metric.
    if runs > 1 and stats_by_metric is not None:
        for key, meta in METRICS.items():
            means, _, lower95, upper95 = stats_by_metric[key]
            ci_path = build_ci_path(out_path, key)
            if key == "population":
                title = f"Population Convergence - 95% Confidence Interval ({runs} runs, {years} years)"
            else:
                title = f"{meta['label']} - 95% Confidence Interval ({runs} runs, {years} years)"
            plot_ci_chart(
                timeline=timeline,
                means=means,
                lower95=lower95,
                upper95=upper95,
                title=title,
                ylabel=meta["ylabel"],
                color=meta["color"],
                output_path=ci_path,
            )

    if show or output is None:
        plt.show()

    return statistics.mean(final_populations) if final_populations else 0.0
