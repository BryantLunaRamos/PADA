import argparse
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import fisher_exact

DB_PATH = "diit_contracts.db"

COMPETITIVE_METHODS = {
    "COMPETITIVE SEALED BIDDING",
    "REQUEST FOR  PROPOSAL (RFP)",
    "RFP FROM A PQVL",
    "MULTIPLE AWARDS",
}

NON_COMPETITIVE_METHODS = {
    "M/WBE SMALL PURCHASE",
    "SOLE SOURCE",
    "SMALL PURCHASE - WRITTEN",
    "EMERGENCY",
    "NEGOTIATED ACQUISITION AND DOE NEGOTIATED SERVICES",
    "ASSIGNMENT",
    "DETERMINED BY GOV'T MANDATE",
    "BORO NEEDS/DISCRETIONARY FUND",
    "INTERGOVERNMENTAL PROCUREMENT",
    "INTERGOVERNMENTAL PROCUREMENT RENEWAL",
    "GOVERNMENT TO GOVERNMENT",
    "GRANTS",
    "GRANT RENEWAL",
}

MWBE_CATEGORIES = [
    "Non-M/WBE", "Asian American", "Women (Non-Minority)",
    "Black American", "Hispanic American",
]


def classify_method(method):
    if method in COMPETITIVE_METHODS:
        return "competitive"
    if method in NON_COMPETITIVE_METHODS:
        return "non_competitive"
    return None


def fetch_classified_rows(conn):
    rows = conn.execute(
        "SELECT mwbe_category, award_method FROM contracts_unified WHERE is_diit = 1"
    ).fetchall()

    classified = []
    excluded = {}
    for mwbe_category, award_method in rows:
        bucket = classify_method(award_method)
        if bucket is None:
            excluded[award_method] = excluded.get(award_method, 0) + 1
        else:
            classified.append((mwbe_category, bucket))
    return classified, excluded


def build_2x2_table(classified):
    counts = {"M/WBE": {"competitive": 0, "non_competitive": 0},
              "Non-M/WBE": {"competitive": 0, "non_competitive": 0}}
    for mwbe_category, bucket in classified:
        group = "Non-M/WBE" if mwbe_category == "Non-M/WBE" else "M/WBE"
        counts[group][bucket] += 1
    table = [
        [counts["M/WBE"]["competitive"], counts["M/WBE"]["non_competitive"]],
        [counts["Non-M/WBE"]["competitive"], counts["Non-M/WBE"]["non_competitive"]],
    ]
    return table, counts


def build_5x2_table(classified):
    counts = {cat: {"competitive": 0, "non_competitive": 0} for cat in MWBE_CATEGORIES}
    for mwbe_category, bucket in classified:
        if mwbe_category in counts:
            counts[mwbe_category][bucket] += 1
    table = [[counts[cat]["competitive"], counts[cat]["non_competitive"]] for cat in MWBE_CATEGORIES]
    return table, counts


def build_competitive_rate_chart(counts_5x2, freeman_halton_p, output_path):
    labels, pcts, ns = [], [], []
    for cat in MWBE_CATEGORIES:
        comp = counts_5x2[cat]["competitive"]
        noncomp = counts_5x2[cat]["non_competitive"]
        total = comp + noncomp
        if total == 0:
            continue
        labels.append(cat)
        pcts.append(100 * comp / total)
        ns.append(total)

    order = sorted(range(len(pcts)), key=lambda i: -pcts[i])
    labels = [labels[i] for i in order]
    pcts = [pcts[i] for i in order]
    ns = [ns[i] for i in order]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.bar(labels, pcts, color="#2a78d6", width=0.6)
    for bar, n in zip(bars, ns):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"n={n}", ha="center", va="bottom", fontsize=9, color="#52514e")

    ax.set_ylabel("% of DIIT contracts awarded competitively")
    ax.set_title(
        "Share of DIIT contracts awarded competitively, by M/WBE category\n"
        f"Freeman-Halton p = {freeman_halton_p:.4f}",
        fontsize=10,
    )
    ax.set_ylim(0, max(pcts) + 10)
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fisher's exact / Freeman-Halton test: M/WBE status vs. competitive award method"
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to diit_contracts.db")
    parser.add_argument("--figures-dir", default=".", help="Directory to save chart PNGs")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    classified, excluded = fetch_classified_rows(conn)

    total = sum(excluded.values()) + len(classified)
    print(f"--- Award method classification coverage ---")
    print(f"  Classified: {len(classified)} / {total} ({100 * len(classified) / total:.1f}%)")
    print(f"  Excluded (ambiguous award method):")
    for method, count in sorted(excluded.items(), key=lambda x: -x[1]):
        print(f"    {method!r}: {count}")

    print("\n--- Primary test: M/WBE (any) vs. Non-M/WBE, competitive vs. non-competitive ---")
    table_2x2, counts_2x2 = build_2x2_table(classified)
    print(f"  {'':10} {'competitive':>12} {'non_competitive':>16}")
    for group in ("M/WBE", "Non-M/WBE"):
        print(f"  {group:10} {counts_2x2[group]['competitive']:>12} {counts_2x2[group]['non_competitive']:>16}")

    odds_ratio, p_value = fisher_exact(table_2x2, alternative="two-sided")
    print(f"\n  Odds ratio = {odds_ratio:.3f}, p = {p_value:.4f}")

    print("\n--- Sensitivity check: excluding M/WBE Small Purchase Method ---")
    print("  (that method is non competitive by law and only available to M/WBE vendors,")
    print("   so its presence mechanically inflates the M/WBE non-competitive count)")
    classified_no_mwbesp = [
        (mwbe_category, bucket) for mwbe_category, bucket in classified
    ]
    conn2_rows = conn.execute(
        "SELECT mwbe_category, award_method FROM contracts_unified "
        "WHERE is_diit = 1 AND award_method != 'M/WBE SMALL PURCHASE'"
    ).fetchall()
    classified_no_mwbesp = []
    for mwbe_category, award_method in conn2_rows:
        bucket = classify_method(award_method)
        if bucket is not None:
            classified_no_mwbesp.append((mwbe_category, bucket))

    table_no_mwbesp, counts_no_mwbesp = build_2x2_table(classified_no_mwbesp)
    print(f"  {'':10} {'competitive':>12} {'non_competitive':>16}")
    for group in ("M/WBE", "Non-M/WBE"):
        print(f"  {group:10} {counts_no_mwbesp[group]['competitive']:>12} {counts_no_mwbesp[group]['non_competitive']:>16}")
    odds_ratio_2, p_value_2 = fisher_exact(table_no_mwbesp, alternative="two-sided")
    print(f"\n  Odds ratio = {odds_ratio_2:.3f}, p = {p_value_2:.6f}")

    print("\n--- Supplementary: full M/WBE category breakdown (Freeman-Halton generalization) ---")
    table_5x2, counts_5x2 = build_5x2_table(classified)
    print(f"  {'':22} {'competitive':>12} {'non_competitive':>16}")
    for cat in MWBE_CATEGORIES:
        print(f"  {cat:22} {counts_5x2[cat]['competitive']:>12} {counts_5x2[cat]['non_competitive']:>16}")

    stat_5x2, p_value_5x2 = fisher_exact(table_5x2)
    print(f"\n  Freeman-Halton p = {p_value_5x2:.4f}")

    chart_path = f"{args.figures_dir}/competitive_award_rate_by_mwbe.png"
    build_competitive_rate_chart(counts_5x2, p_value_5x2, chart_path)
    print(f"\nSaved chart: {chart_path}")

    conn.close()