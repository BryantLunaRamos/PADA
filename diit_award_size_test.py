import argparse
import os
import sqlite3
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy.stats import mannwhitneyu

DB_PATH = "diit_contracts.db"


def fetch_amounts(conn, mwbe_filter):
    query = (
        "SELECT current_amount FROM contracts_unified "
        "WHERE is_diit = 1 AND NOT (current_amount = 1 AND original_amount = 1) AND " + mwbe_filter
    )
    return [r[0] for r in conn.execute(query).fetchall()]


def summarize(label, amounts):
    print(f"{label}: n={len(amounts)}  median=${statistics.median(amounts):,.2f}  "
          f"mean=${statistics.mean(amounts):,.2f}  "
          f"min=${min(amounts):,.2f}  max=${max(amounts):,.2f}")


def rank_biserial_effect_size(u_stat, n1, n2):
    return u_stat / (n1 * n2)


def dollar_formatter(x, _):
    if x >= 1_000_000:
        return f"${x/1_000_000:.0f}M"
    if x >= 1000:
        return f"${x/1000:.0f}K"
    return f"${x:.0f}"


def build_boxplot(non_mwbe, mwbe, p_value, output_path):
    fig, ax = plt.subplots(figsize=(7, 7))
    bp = ax.boxplot(
        [non_mwbe, mwbe],
        tick_labels=[f"Non-M/WBE\n(n={len(non_mwbe)})", f"M/WBE\n(n={len(mwbe)})"],
        patch_artist=True, showmeans=True, meanline=True, whis=1.5,
    )
    for patch, color in zip(bp["boxes"], ["#2a78d6", "#eb6834"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)

    ax.set_yscale("log")
    ax.yaxis.set_major_locator(mticker.LogLocator(base=10, subs=[1, 2, 5]))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(dollar_formatter))
    ax.set_ylabel("DIIT contract award amount")
    ax.set_title(
        "DIIT contract award size by M/WBE status (placeholder $1 rows excluded)\n"
        f"Mann-Whitney U p = {p_value:.5f}  |  "
        f"medians: ${statistics.median(non_mwbe):,.0f} vs ${statistics.median(mwbe):,.0f}",
        fontsize=10,
    )
    ax.grid(axis="y", alpha=0.3, which="major")
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def build_ecdf(non_mwbe, mwbe, p_value, output_path):
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for data, label, color in [
        (np.sort(non_mwbe), f"Non-M/WBE (n={len(non_mwbe)})", "#2a78d6"),
        (np.sort(mwbe), f"M/WBE (n={len(mwbe)})", "#eb6834"),
    ]:
        y = np.arange(1, len(data) + 1) / len(data) * 100
        ax.step(data, y, where="post", label=label, color=color, linewidth=2)

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(dollar_formatter))
    ax.set_xlabel("DIIT contract award amount")
    ax.set_ylabel("Cumulative % of contracts at or below this amount")
    ax.set_title(f"DIIT contract award size distribution: M/WBE vs. Non-M/WBE\nMann-Whitney U p = {p_value:.5f}")
    ax.grid(alpha=0.3, which="major")
    ax.legend(loc="lower right", frameon=False)
    ax.set_ylim(0, 100)
    ax.axhline(50, color="gray", linewidth=0.7, linestyle=":")
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wilcoxon rank-sum test: DIIT contract award size, M/WBE vs non-M/WBE."
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to diit_contracts.db")
    parser.add_argument("--figures-dir", default=".", help="Directory to save chart PNGs")
    args = parser.parse_args()
    os.makedirs(args.figures_dir, exist_ok=True)

    conn = sqlite3.connect(args.db)

    non_mwbe = fetch_amounts(conn, "mwbe_category = 'Non-M/WBE'")
    mwbe = fetch_amounts(
        conn,
        "mwbe_category IS NOT NULL AND mwbe_category != 'Non-M/WBE' AND mwbe_category != ''"
    )

    print("--- DIIT contract award size by M/WBE status ---")
    summarize("Non-M/WBE", non_mwbe)
    summarize("M/WBE    ", mwbe)

    u_stat, p_value = mannwhitneyu(non_mwbe, mwbe, alternative="two-sided")
    effect = rank_biserial_effect_size(u_stat, len(non_mwbe), len(mwbe))

    print(f"\nMann-Whitney U = {u_stat:.1f}, p = {p_value:.6f}")
    print(f"P(random non-M/WBE contract > random M/WBE contract) = {effect:.3f}")

    print("\n--- Supplementary: median award by M/WBE category (descriptive only, n too small for a test on most rows) ---")
    for category in ["Non-M/WBE", "Asian American", "Women (Non-Minority)", "Black American", "Hispanic American"]:
        amounts = fetch_amounts(conn, f"mwbe_category = '{category}'")
        if amounts:
            print(f"  {category:<22} n={len(amounts):<4} median=${statistics.median(amounts):,.2f}")

    boxplot_path = f"{args.figures_dir}/award_size_boxplot.png"
    ecdf_path = f"{args.figures_dir}/award_size_ecdf.png"
    build_boxplot(non_mwbe, mwbe, p_value, boxplot_path)
    build_ecdf(non_mwbe, mwbe, p_value, ecdf_path)
    print(f"\nSaved charts: {boxplot_path}, {ecdf_path}")

    conn.close()