import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from nltk.stem import PorterStemmer

DB_PATH = "diit_contracts.db"

_stemmer = PorterStemmer()
_token_re = re.compile(r"[a-zA-Z]{2,}")
_STOPWORDS = {
    "the", "and", "for", "of", "to", "in", "on", "at", "by", "with", "or",
    "an", "as", "is", "are", "be", "this", "that", "from", "into",
}


def stemmed_analyzer(text):
    tokens = [
        _stemmer.stem(tok) for tok in _token_re.findall(text.lower())
        if tok not in _STOPWORDS
    ]
    bigrams = [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    return tokens + bigrams


def count_alpha_tokens(text: str) -> int:
    return len(_token_re.findall(text))


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
