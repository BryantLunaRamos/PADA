import argparse
import sqlite3
import statistics

from scipy.stats import mannwhitneyu

DB_PATH = "diit_contracts.db"

def fetch_amounts(conn, mwbe_filter):
    query = (
        "SELECT current_amount FROM contracts_unified "
        "WHERE is_diit = 1 AND " + mwbe_filter
    )
    return [r[0] for r in conn.execute(query).fetchall()]

def summarize(label, amounts):
    print(f"{label}: n={len(amounts)}  median=${statistics.median(amounts):,.2f}  "
          f"mean=${statistics.mean(amounts):,.2f}  "
          f"min=${min(amounts):,.2f}  max=${max(amounts):,.2f}")

def rank_biserial_effect_size(u_stat, n1, n2):
    return u_stat / (n1 * n2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wilcoxon rank-sum test: DIIT contract award size, M/WBE vs non-M/WBE"
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to diit_contracts.db")
    args = parser.parse_args()

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

    print("\n--- Supplementary: median award by M/WBE category (descriptive only since n is too small for a test on most rows) ---")
    for category in ["Non-M/WBE", "Asian American", "Women (Non-Minority)", "Black American", "Hispanic American"]:
        amounts = fetch_amounts(conn, f"mwbe_category = '{category}'")
        if amounts:
            print(f"  {category:<22} n={len(amounts):<4} median=${statistics.median(amounts):,.2f}")

    conn.close()
