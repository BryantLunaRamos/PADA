import argparse
import subprocess
import sys

DB_PATH = "diit_contracts.db"

STAT_TEST_SCRIPTS = [
    "diit_award_size_test.py",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the DIIT database (optional fyi) and run every registered statistical test against it"
    )
    parser.add_argument("--registered", help="Checkbook registered contracts CSV")
    parser.add_argument("--pending", help="Checkbook pending contracts CSV")
    parser.add_argument("--sources", nargs="+", metavar="FILE",
                        help="Additional PASSPort/other source files (CSV or XLSX)")
    parser.add_argument("--db", default=DB_PATH, help="Path to diit_contracts.db")
    args = parser.parse_args()

    if args.registered or args.pending:
        pipeline_cmd = [sys.executable, "diit_pipeline.py", "--db", args.db]
        if args.registered:
            pipeline_cmd += ["--registered", args.registered]
        if args.pending:
            pipeline_cmd += ["--pending", args.pending]
        if args.sources:
            pipeline_cmd += ["--sources"] + args.sources

        print(f"\n{'=' * 70}\nRunning diit_pipeline.py (build + ownership clustering)\n{'=' * 70}")
        result = subprocess.run(pipeline_cmd, check=False)
        if result.returncode != 0:
            print(f"\ndiit_pipeline.py exited with code {result.returncode}, stopping")
            sys.exit(result.returncode)
    else:
        print(f"No raw source files given, using existing database at {args.db}")

    for script in STAT_TEST_SCRIPTS:
        print(f"\n{'=' * 70}\nRunning {script}\n{'=' * 70}")
        result = subprocess.run(
            [sys.executable, script, "--db", args.db],
            check=False,
        )
        if result.returncode != 0:
            print(f"\n{script} exited with code {result.returncode}, stopping")
            sys.exit(result.returncode)

    print(f"\n{'=' * 70}\nAll analyses complete!\n{'=' * 70}")
