"""Atomic V2 retrieval publication, only after a material monitor event."""
from app.retrieval.chunking import build_corpus
from app.retrieval.dense import DenseRetriever


def rebuild_current_corpus() -> None:
    """The persisted cache is whole-corpus fingerprinted; publish atomically.

    At the current small corpus size a changed-cycle rebuild is safer than a
    partial manifest rewrite.  Unchanged and failed cycles never call this.
    """
    dense = DenseRetriever(local_files_only=True)
    dense.index(build_corpus())
