import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DB_PATH = "diit_contracts.db"


def add_db_figures_args(parser, db_help: str = "Path to the SQLite database") -> None:
    parser.add_argument("--db", default=DB_PATH, help=db_help)
    parser.add_argument("--figures-dir", default=".", help="Directory to save chart PNGs")


def ensure_figures_dir(figures_dir: str) -> None:
    os.makedirs(figures_dir, exist_ok=True)


def save_chart(fig, output_path: str, dpi: int = 150) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
