import argparse
import csv
import sqlite3
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import common


def fetch_rows(conn):
    rows = conn.execute("""
        SELECT contract_id, vendor_name, purpose, current_amount, is_diit
        FROM contracts_unified
        WHERE purpose IS NOT NULL AND purpose != ''
    """).fetchall()
    return rows


def rank_candidates(rows, top_n):
    seed_rows = [r for r in rows if r[4] == 1]
    candidate_rows = [r for r in rows if r[4] != 1]

    if not seed_rows:
        print("No is_diit=1 rows found - run diit_pipeline.py first.")
        sys.exit(1)
    if not candidate_rows:
        print("No unflagged rows found - nothing to search.")
        sys.exit(0)

    seed_texts = [r[2] for r in seed_rows]
    candidate_texts = [r[2] for r in candidate_rows]

    vectorizer = TfidfVectorizer(analyzer=common.stemmed_analyzer, min_df=1)
    vectorizer.fit(seed_texts + candidate_texts)

    seed_matrix = vectorizer.transform(seed_texts)
    candidate_matrix = vectorizer.transform(candidate_texts)

    sim_matrix = cosine_similarity(candidate_matrix, seed_matrix)
    best_seed_idx = sim_matrix.argmax(axis=1)
    best_sim = sim_matrix.max(axis=1)

    ranked = sorted(
        zip(candidate_rows, best_sim, best_seed_idx),
        key=lambda x: -x[1],
    )

    results = []
    for (contract_id, vendor_name, purpose, amount, _), score, seed_idx in ranked[:top_n]:
        results.append({
            "contract_id": contract_id,
            "vendor_name": vendor_name,
            "purpose": purpose,
            "current_amount": amount,
            "similarity_score": round(float(score), 4),
            "nearest_seed_purpose": seed_texts[seed_idx],
            "confirmed_diit": "",
        })
    return results


def write_csv(results, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "contract_id", "vendor_name", "purpose", "current_amount",
            "similarity_score", "nearest_seed_purpose", "confirmed_diit",
        ])
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(results)} candidates to {output_path}")
    print("Fill in the confirmed_diit column (Y/N), then re-run with --apply.")


def apply_labels(conn, reviewed_csv):
    confirmed_ids = []
    with open(reviewed_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("confirmed_diit", "").strip().upper() == "Y":
                confirmed_ids.append(row["contract_id"])

    if not confirmed_ids:
        print("No rows marked Y in confirmed_diit - nothing to apply.")
        return

    before = conn.execute("SELECT COUNT(*) FROM contracts_unified WHERE is_diit=1").fetchone()[0]
    placeholders = ",".join("?" for _ in confirmed_ids)
    conn.execute(
        f"UPDATE contracts_unified SET is_diit=1 WHERE contract_id IN ({placeholders})",
        confirmed_ids,
    )
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM contracts_unified WHERE is_diit=1").fetchone()[0]

    print(f"Applied {len(confirmed_ids)} manual confirmations.")
    print(f"is_diit=1 count: {before} -> {after}")
    print("Re-run diit_award_size_test.py / diit_award_method_fisher_test.py to pick up the change.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="One-time TF-IDF nearest-neighbor audit for missed DIIT contracts."
    )
    parser.add_argument("--db", required=True, help="Path to diit_contracts.db")
    parser.add_argument("--top-n", type=int, default=150, help="How many ranked candidates to output")
    parser.add_argument("--output", default="candidates_for_review.csv", help="Output CSV path")
    parser.add_argument("--apply", metavar="REVIEWED_CSV",
                        help="Apply hand-labeled confirmed_diit=Y rows from this CSV back to the db")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)

    if args.apply:
        apply_labels(conn, args.apply)
    else:
        rows = fetch_rows(conn)
        results = rank_candidates(rows, args.top_n)
        write_csv(results, args.output)

    conn.close()
