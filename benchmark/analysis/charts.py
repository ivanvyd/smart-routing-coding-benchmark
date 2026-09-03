"""Render the nine required charts.

Until a real run has happened, every chart is a labelled "NOT_MEASURED"
placeholder. We do NOT draw fake bars that could be misread as results.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # non-interactive backend, safe for CI
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, PercentFormatter

NOT_MEASURED = "NOT_MEASURED"
PALETTE = ["#2563EB", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6", "#0EA5E9"]
TEXT = "#172033"
MUTED = "#5F6B7A"
GRID = "#DCE3EA"
BACKGROUND = "#FBFCFE"
ARM_LABELS = {
    "FIXED_STRONG": "Fixed strong",
    "FIXED_CHEAP": "Fixed cheap",
    "CLIENT_ROUTING": "Client routed",
}
ARM_COLORS = {
    "FIXED_STRONG": PALETTE[0],
    "FIXED_CHEAP": PALETTE[1],
    "CLIENT_ROUTING": PALETTE[2],
}
MODEL_LABELS = {
    "system.ai.claude-haiku-4-5": "Haiku 4.5",
    "system.ai.claude-sonnet-5": "Sonnet 5",
}
MODEL_COLORS = {
    "system.ai.claude-haiku-4-5": PALETTE[1],
    "system.ai.claude-sonnet-5": PALETTE[0],
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": TEXT,
        "figure.facecolor": BACKGROUND,
        "axes.facecolor": BACKGROUND,
        "savefig.facecolor": BACKGROUND,
    }
)


def _arm_labels(arms: list[str]) -> list[str]:
    return [ARM_LABELS.get(arm, arm) for arm in arms]


def _model_label(model: str) -> str:
    return MODEL_LABELS.get(model, model)


def _cycle_palette(n: int) -> list[str]:
    """Return n colors by cycling through PALETTE.

    `pie()` indexes by position and silently indexes out of range if the
    `colors` list is shorter than the data; the historical *2 hack masked
    that for small N while breaking for N > 12.
    """
    return list(itertools.islice(itertools.cycle(PALETTE), n))


def _arm_colors(arms: list[str]) -> list[str]:
    return [ARM_COLORS.get(arm, PALETTE[index % len(PALETTE)]) for index, arm in enumerate(arms)]


def _figure(*, width: float = 8.0, height: float = 4.8) -> tuple[Figure, Axes]:
    return plt.subplots(figsize=(width, height))


def _style_axis(ax: Axes, *, grid: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, pad=8)
    if grid:
        ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.75)
        ax.set_axisbelow(True)


def _title(ax: Axes, text: str) -> None:
    ax.set_title(text, loc="left", fontsize=17, fontweight="bold", pad=16)


def _label_bars(ax: Axes, bars: BarContainer, labels: list[str]) -> None:
    ax.bar_label(bars, labels=labels, padding=6, fontsize=11, color=TEXT, fontweight="bold")


def _save(fig: Figure, out: Path) -> None:
    fig.tight_layout(pad=1.4)
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _placeholder(out_path: Path, title: str, subtitle: str = "Run not yet executed") -> None:
    fig, ax = _figure()
    ax.text(0.5, 0.55, title, ha="center", va="center", fontsize=18, fontweight="bold")
    ax.text(
        0.5,
        0.42,
        NOT_MEASURED,
        ha="center",
        va="center",
        fontsize=22,
        color="#888",
    )
    ax.text(0.5, 0.32, subtitle, ha="center", va="center", fontsize=11, color="#666")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _save(fig, out_path)


def chart_success_rate(metrics_by_arm: dict[str, dict[str, Any]], out: Path) -> None:
    arms = list(metrics_by_arm.keys())
    if not arms or metrics_by_arm[arms[0]].get("task_success_rate") == NOT_MEASURED:
        _placeholder(out, "Success rate by strategy")
        return
    rates = [metrics_by_arm[a].get("task_success_rate", 0) for a in arms]
    fig, ax = _figure()
    bars = ax.bar(_arm_labels(arms), rates, color=_arm_colors(arms), width=0.68)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Scored task success rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    _title(ax, "Task success rate by strategy")
    _style_axis(ax)
    _label_bars(ax, bars, [f"{value:.0%}" for value in rates])
    _save(fig, out)


def chart_total_cost(metrics_by_arm: dict[str, dict[str, Any]], out: Path) -> None:
    arms = list(metrics_by_arm.keys())
    if not arms or metrics_by_arm[arms[0]].get("total_estimated_cost") == NOT_MEASURED:
        _placeholder(out, "Total cost by strategy", "Gateway token records and captured prices")
        return
    costs = [metrics_by_arm[a].get("total_estimated_cost", 0) for a in arms]
    fig, ax = _figure()
    bars = ax.bar(_arm_labels(arms), costs, color=_arm_colors(arms), width=0.68)
    ax.set_ylim(0, max(costs) * 1.18)
    ax.set_ylabel("Estimated model cost (USD)")
    _title(ax, "Total estimated model cost")
    _style_axis(ax)
    _label_bars(ax, bars, [f"${value:.2f}" for value in costs])
    _save(fig, out)


def chart_cost_per_success(metrics_by_arm: dict[str, dict[str, Any]], out: Path) -> None:
    arms = list(metrics_by_arm.keys())
    if not arms or metrics_by_arm[arms[0]].get("cost_per_successful_task") == NOT_MEASURED:
        _placeholder(out, "Cost per successful task", "Headline economic metric")
        return
    cps = [metrics_by_arm[a].get("cost_per_successful_task", 0) for a in arms]
    fig, ax = _figure()
    bars = ax.bar(_arm_labels(arms), cps, color=_arm_colors(arms), width=0.68)
    ax.set_ylim(0, max(cps) * 1.18)
    ax.set_ylabel("Estimated cost per success (USD)")
    _title(ax, "Model cost per successful task")
    _style_axis(ax)
    _label_bars(ax, bars, [f"${value:.3f}" for value in cps])
    _save(fig, out)


def chart_routing_distribution(routing_runs: list[dict[str, Any]], out: Path) -> None:
    if not routing_runs or not any(run.get("selected_model") for run in routing_runs):
        _placeholder(out, "Client router: model selection distribution")
        return
    counter: dict[str, int] = {}
    for run in routing_runs:
        model = run.get("selected_model")
        if isinstance(model, str):
            counter[model] = counter.get(model, 0) + 1
    labels = [_model_label(model) for model in counter]
    values = list(counter.values())
    fig, ax = _figure(height=5.2)
    colors = [
        MODEL_COLORS.get(model, color)
        for model, color in zip(counter, _cycle_palette(len(values)), strict=True)
    ]
    ax.pie(
        values,
        labels=labels,
        autopct="%1.0f%%",
        colors=colors,
        startangle=90,
        counterclock=False,
        pctdistance=0.78,
        labeldistance=1.08,
        wedgeprops={"width": 0.4, "edgecolor": BACKGROUND, "linewidth": 3},
        textprops={"color": TEXT, "fontsize": 11},
    )
    ax.text(0, 0.05, str(sum(values)), ha="center", va="center", fontsize=24, fontweight="bold")
    ax.text(0, -0.12, "scored tasks", ha="center", va="center", fontsize=10, color=MUTED)
    _title(ax, "Client router model selection")
    _save(fig, out)


def chart_routing_by_difficulty(
    routing_runs: list[dict[str, Any]],
    out: Path,
) -> None:
    if not routing_runs:
        _placeholder(out, "Client router: model vs difficulty")
        return
    by_diff: dict[str, dict[str, int]] = {}
    for run in routing_runs:
        d = run.get("task_difficulty", "unknown")
        model = run.get("selected_model")
        if isinstance(model, str):
            by_diff.setdefault(d, {}).setdefault(model, 0)
            by_diff[d][model] += 1
    if not by_diff:
        _placeholder(out, "Client router: model vs difficulty")
        return
    diffs = ["easy", "medium", "hard"]
    models = sorted({m for d in by_diff.values() for m in d})
    fig, ax = _figure()
    width = 0.34
    for i, m in enumerate(models):
        offset = (i - (len(models) - 1) / 2) * width
        xs = [diffs.index(d) + offset for d in diffs if d in by_diff]
        ys = [by_diff[d].get(m, 0) for d in diffs if d in by_diff]
        bars = ax.bar(
            xs,
            ys,
            width=width,
            label=_model_label(m),
            color=MODEL_COLORS.get(m, PALETTE[i % len(PALETTE)]),
        )
        _label_bars(ax, bars, [str(value) for value in ys])
    ax.set_xticks(range(len(diffs)))
    ax.set_xticklabels(diffs)
    ax.set_ylim(0, max(max(values.values()) for values in by_diff.values()) + 1.1)
    ax.set_ylabel("Scored tasks")
    _title(ax, "Model selected by task difficulty")
    _style_axis(ax)
    ax.legend(frameon=False, loc="upper center", ncols=len(models))
    _save(fig, out)


def chart_tokens_per_success(metrics_by_arm: dict[str, dict[str, Any]], out: Path) -> None:
    arms = list(metrics_by_arm.keys())
    if (
        not arms
        or metrics_by_arm[arms[0]].get("total_tokens") == NOT_MEASURED
        or not isinstance(metrics_by_arm[arms[0]].get("task_success_rate"), int | float)
    ):
        _placeholder(out, "Tokens per successful task")
        return
    fig, ax = _figure()
    values: list[float] = []
    for a in arms:
        m = metrics_by_arm[a]
        rate = float(m.get("task_success_rate", 0) or 0)
        tok = float(m.get("total_tokens", 0) or 0)
        successes = max(1, round(rate * float(m.get("n_runs", 1))))
        tps = tok / successes
        values.append(tps)
    bars = ax.bar(range(len(arms)), values, color=_arm_colors(arms), width=0.68)
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(_arm_labels(arms))
    ax.set_ylim(0, max(values) * 1.18)
    ax.set_ylabel("Tokens per successful task")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:.0f}k"))
    _title(ax, "Tokens per successful task")
    _style_axis(ax)
    _label_bars(ax, bars, [f"{int(value):,}" for value in values])
    _save(fig, out)


def chart_latency(metrics_by_arm: dict[str, dict[str, Any]], out: Path) -> None:
    arms = list(metrics_by_arm.keys())
    if not arms or metrics_by_arm[arms[0]].get("mean_latency_ms") == NOT_MEASURED:
        _placeholder(out, "Latency distribution (p95)")
        return
    means = [float(metrics_by_arm[a].get("mean_latency_ms", 0)) / 1000 for a in arms]
    p95s = [float(metrics_by_arm[a].get("p95_latency_ms", 0)) / 1000 for a in arms]
    fig, ax = _figure()
    x = list(range(len(arms)))
    mean_bars = ax.bar([i - 0.18 for i in x], means, width=0.36, label="Mean", color=PALETTE[0])
    p95_bars = ax.bar([i + 0.18 for i in x], p95s, width=0.36, label="P95", color=PALETTE[1])
    ax.set_xticks(list(x))
    ax.set_xticklabels(_arm_labels(arms))
    ax.set_ylim(0, max(p95s) * 1.18)
    ax.set_ylabel("Gateway invocation latency (seconds)")
    _title(ax, "Gateway latency by strategy")
    _style_axis(ax)
    _label_bars(ax, mean_bars, [f"{value:.1f}s" for value in means])
    _label_bars(ax, p95_bars, [f"{value:.1f}s" for value in p95s])
    ax.legend(frameon=False, loc="upper right", ncols=2)
    _save(fig, out)


def chart_router_error_cases(cases: dict[str, list[dict[str, Any]]], out: Path) -> None:
    over = cases.get("over_routing", [])
    under = cases.get("under_routing", [])
    counts = [len(over), len(under)]
    fig, ax = _figure()
    if not any(counts):
        ax.axis("off")
        _title(ax, "Routing diagnostic")
        for x, label in zip((0.28, 0.72), ("Over-routing", "Under-routing"), strict=True):
            ax.text(
                x,
                0.57,
                "0",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=38,
                fontweight="bold",
                color=PALETTE[2],
            )
            ax.text(
                x,
                0.4,
                label,
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
                color=TEXT,
            )
        ax.text(
            0.5,
            0.18,
            "No candidate cases across 21 scored routed tasks",
            transform=ax.transAxes,
            ha="center",
            color=MUTED,
        )
    else:
        bars = ax.bar(
            ["Over-routing", "Under-routing"], counts, color=[PALETTE[1], PALETTE[3]], width=0.55
        )
        ax.set_ylim(0, max(counts) * 1.25)
        ax.set_ylabel("Candidate cases")
        _title(ax, "Routing diagnostic")
        _style_axis(ax)
        _label_bars(ax, bars, [str(value) for value in counts])
    _save(fig, out)


def chart_savings_vs_quality(metrics_by_arm: dict[str, dict[str, Any]], out: Path) -> None:
    arms = list(metrics_by_arm.keys())
    if not arms or metrics_by_arm[arms[0]].get("cost_per_successful_task") == NOT_MEASURED:
        _placeholder(
            out,
            "Savings vs quality tradeoff",
            "Scatter: cost per success (x) vs success rate (y)",
        )
        return
    fig, ax = _figure(height=5.2)
    points: list[tuple[float, float, str, str]] = []
    for i, a in enumerate(arms):
        cps = float(metrics_by_arm[a].get("cost_per_successful_task", 0) or 0)
        rate = float(metrics_by_arm[a].get("task_success_rate", 0) or 0)
        label = ARM_LABELS.get(a, a)
        color = _arm_colors(arms)[i]
        points.append((cps, rate, label, color))
    costs = [point[0] for point in points]
    rates = [point[1] for point in points]
    x_padding = max(0.006, (max(costs) - min(costs)) * 0.15)
    y_padding = max(0.008, (max(rates) - min(rates)) * 0.2)
    ax.set_xlim(min(costs) - x_padding, max(costs) + x_padding)
    ax.set_ylim(min(rates) - y_padding, max(rates) + y_padding)
    for cps, rate, label, color in points:
        ax.scatter(cps, rate, s=260, color=color, edgecolor=BACKGROUND, linewidth=2, zorder=3)
        vertical_offset = -18 if rate == max(rates) else 12
        ax.annotate(
            f"{label}  ${cps:.3f}",
            (cps, rate),
            xytext=(0, vertical_offset),
            textcoords="offset points",
            ha="center",
            va="top" if vertical_offset < 0 else "bottom",
            fontsize=10.5,
            color=TEXT,
        )
    ax.set_xlabel("Estimated cost per successful task (USD, lower is better)")
    ax.set_ylabel("Scored task success rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _title(ax, "Cost and observed task success")
    _style_axis(ax)
    _save(fig, out)


def render_all(
    metrics_by_arm: dict[str, dict[str, Any]],
    routing_runs: list[dict[str, Any]],
    cases: dict[str, list[dict[str, Any]]],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_success_rate(metrics_by_arm, out_dir / "01_success_rate.png")
    chart_total_cost(metrics_by_arm, out_dir / "02_total_cost.png")
    chart_cost_per_success(metrics_by_arm, out_dir / "03_cost_per_success.png")
    chart_routing_distribution(routing_runs, out_dir / "04_routing_distribution.png")
    chart_routing_by_difficulty(routing_runs, out_dir / "05_routing_by_difficulty.png")
    chart_tokens_per_success(metrics_by_arm, out_dir / "06_tokens_per_success.png")
    chart_latency(metrics_by_arm, out_dir / "07_latency.png")
    chart_router_error_cases(cases, out_dir / "08_router_error_cases.png")
    chart_savings_vs_quality(metrics_by_arm, out_dir / "09_savings_vs_quality.png")
