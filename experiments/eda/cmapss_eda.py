"""Exploratory analysis of C-MAPSS for the paper.

Run from the repository root:

    python -m mindtwin.data.cmapss download
    python experiments/eda/cmapss_eda.py

Writes figures to ``paper/figures/`` (PDF, for the paper) and ``docs/figures/`` (PNG, for the
docs), and summary statistics to ``experiments/results/eda/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from mindtwin.data.cmapss import SENSOR_COLS, SENSOR_INFO, SUBSETS, load_cmapss  # noqa: E402
from mindtwin.data.preprocessing import (  # noqa: E402
    ConditionNormalizer,
    informative_sensors,
    operating_condition,
)

ROOT = Path(__file__).resolve().parents[2]
PAPER_FIG = ROOT / "paper" / "figures"
DOCS_FIG = ROOT / "docs" / "figures"
RESULTS = ROOT / "experiments" / "results" / "eda"

# Reference palette (dataviz skill): categorical slots 1 and 2, text and context inks.
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_2, CONTEXT, GRID = "#0b0b0b", "#52514e", "#c9c8c2", "#e6e5e0"

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.edgecolor": INK_2,
        "axes.labelcolor": INK,
        "axes.titlesize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "legend.frameon": False,
        "savefig.bbox": "tight",
        "figure.constrained_layout.use": True,
    }
)


def sensor_label(col: str) -> str:
    return f"{col} ({SENSOR_INFO[col][0]})"


def save(fig, name: str) -> None:
    PAPER_FIG.mkdir(parents=True, exist_ok=True)
    DOCS_FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(PAPER_FIG / f"{name}.pdf")
    fig.savefig(DOCS_FIG / f"{name}.png", dpi=160)
    plt.close(fig)


def rank_corr_with_rul(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    return df[cols + ["rul"]].rank().corr()["rul"].drop("rul")


def fig_lifetimes(data: dict) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 1.9), sharey=True)
    for ax, (name, d) in zip(axes, data.items(), strict=True):
        life = d.train.groupby("unit")["cycle"].max()
        ax.hist(life, bins=range(100, 560, 20), color=BLUE, edgecolor="white", linewidth=1)
        ax.set_title(f"{name} (n={len(life)})")
        ax.set_xlabel("Cycles to failure")
    axes[0].set_ylabel("Engines")
    save(fig, "cmapss_lifetimes")


def fig_degradation(d, sensors: list[str]) -> None:
    train = d.train.assign(t=-d.train["rul"])
    fig, axes = plt.subplots(1, len(sensors), figsize=(7.2, 1.9), sharex=True)
    for ax, col in zip(axes, sensors, strict=True):
        for _, g in train.groupby("unit"):
            ax.plot(g["t"], g[col], color=CONTEXT, linewidth=0.4, alpha=0.6)
        mean = train.groupby("t")[col].mean().loc[-250:]
        ax.plot(mean.index, mean.values, color=BLUE, linewidth=2)
        ax.set_title(sensor_label(col))
        ax.set_xlim(-250, 0)
        ax.set_xlabel("Cycles before failure")
    save(fig, "cmapss_degradation_fd001")


def fig_condition_normalisation(d, col: str, sensors: list[str]) -> dict:
    train = d.train.assign(t=-d.train["rul"])
    norm = ConditionNormalizer(sensors).fit_transform(train)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.1), sharex=True)
    for ax, df, title in [(axes[0], train, "Raw"), (axes[1], norm, "Normalised per condition")]:
        sample = df.sample(6000, random_state=0)
        ax.scatter(sample["t"], sample[col], s=2, color=BLUE, alpha=0.25, linewidths=0)
        ax.set_title(f"{d.subset} {sensor_label(col)}: {title}")
        ax.set_xlabel("Cycles before failure")
        ax.set_xlim(-300, 0)
    axes[0].set_ylabel("Sensor value")
    axes[1].set_ylabel("z-score")
    save(fig, f"cmapss_condition_normalisation_{d.subset.lower()}")
    raw_r = rank_corr_with_rul(train, sensors).abs()
    norm_r = rank_corr_with_rul(norm, sensors).abs()
    return {
        "max_abs_rank_corr_raw": round(raw_r.max(), 3),
        "max_abs_rank_corr_norm": round(norm_r.max(), 3),
    }


def fig_fault_signatures(d1, d3) -> pd.DataFrame:
    sensors = [s for s in informative_sensors(d1.train) if s in informative_sensors(d3.train)]
    r1 = rank_corr_with_rul(d1.train, sensors)
    r3 = rank_corr_with_rul(d3.train, sensors)
    table = pd.DataFrame({"FD001 (HPC fault)": r1, "FD003 (HPC + fan faults)": r3})
    table = table.loc[table["FD001 (HPC fault)"].abs().sort_values().index]

    fig, ax = plt.subplots(figsize=(4.2, 3.6))
    y = range(len(table))
    for i, (_, row) in enumerate(table.iterrows()):
        ax.plot([row.iloc[0], row.iloc[1]], [i, i], color=CONTEXT, linewidth=1.5, zorder=1)
    ax.scatter(
        table.iloc[:, 0],
        y,
        s=36,
        color=BLUE,
        label=table.columns[0],
        zorder=2,
        edgecolors="white",
        linewidths=1.5,
    )
    ax.scatter(
        table.iloc[:, 1],
        y,
        s=36,
        color=ORANGE,
        label=table.columns[1],
        zorder=2,
        edgecolors="white",
        linewidths=1.5,
    )
    ax.set_yticks(list(y), [sensor_label(c) for c in table.index])
    ax.axvline(0, color=INK_2, linewidth=0.8)
    ax.set_xlim(-1, 1)
    ax.set_xlabel("Rank correlation with RUL")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1)
    save(fig, "cmapss_fault_signatures")
    return table.round(3)


def main() -> None:
    data = {s: load_cmapss(s) for s in SUBSETS}
    summary: dict = {}
    for name, d in data.items():
        life = d.train.groupby("unit")["cycle"].max()
        summary[name] = {
            "train_units": int(d.train["unit"].nunique()),
            "test_units": int(d.test["unit"].nunique()),
            "train_rows": len(d.train),
            "test_rows": len(d.test),
            "conditions": int(operating_condition(d.train).nunique()),
            "informative_sensors": informative_sensors(d.train),
            "flat_sensors": [c for c in SENSOR_COLS if c not in informative_sensors(d.train)],
            "lifetime_cycles": {
                "min": int(life.min()),
                "median": float(life.median()),
                "max": int(life.max()),
            },
            "test_rul": {"min": int(d.test_rul.min()), "max": int(d.test_rul.max())},
        }

    fig_lifetimes(data)
    fig_degradation(data["FD001"], ["s4", "s11", "s12", "s21"])
    sens2 = informative_sensors(data["FD002"].train)
    summary["FD002"]["normalisation"] = fig_condition_normalisation(data["FD002"], "s11", sens2)
    signatures = fig_fault_signatures(data["FD001"], data["FD003"])

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
    signatures.to_csv(RESULTS / "fault_signatures.csv")
    print(json.dumps(summary, indent=2))
    print(signatures)


if __name__ == "__main__":
    main()
