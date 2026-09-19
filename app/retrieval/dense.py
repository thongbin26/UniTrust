import hashlib
import io
import json
import logging
import os
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import List

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.retrieval.base import Retriever, RetrievalChunk, RetrievalResult
from app.retrieval.model_cache import DEFAULT_MODEL_NAME, model_files, resolve_local_model
from app.core.config import settings


# Uvicorn configures this logger for the demo process, so cache decisions stay
# visible in the backend log used for startup recovery.
logger = logging.getLogger("uvicorn.error")
_CACHE_VERSION = 1


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _model_identity(snapshot: Path) -> str:
    """Hash actual model/tokenizer/config bytes, independent of machine paths."""
    digest = hashlib.sha256()
    for path in model_files(snapshot):
        digest.update(path.relative_to(snapshot).as_posix().encode("utf-8"))
        digest.update(b"\0")
        file_digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                file_digest.update(block)
        digest.update(file_digest.digest())
    return digest.hexdigest()


class DenseRetriever(Retriever):
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, cache_dir: str | None = None,
                 local_files_only: bool | None = None):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is not installed.")

        self.model_name = model_name
        self.cache_dir = Path(settings.retrieval_cache_dir if cache_dir is None else cache_dir)
        local_only = settings.dense_local_files_only if local_files_only is None else local_files_only
        try:
            snapshot = resolve_local_model(model_name)
        except FileNotFoundError:
            if local_only:
                raise
            logger.info("Dense model not prepared locally; developer mode allows Hub loading.")
            self.model = SentenceTransformer(model_name)
            try:
                snapshot = resolve_local_model(model_name)
            except FileNotFoundError:
                snapshot = None
        else:
            # A snapshot path avoids remote revision and optional-file lookups.
            self.model = SentenceTransformer(str(snapshot), local_files_only=True)
            logger.info("Dense model loaded from local snapshot (no Hub requests).")

        self.model_identity = _model_identity(snapshot) if snapshot is not None else None
        if self.model_identity is None:
            logger.warning("Dense model files could not be identified; persistent cache disabled.")
        self.chunks: List[RetrievalChunk] = []
        self.embeddings: np.ndarray | None = None

    def _get_passage_text(self, chunk: RetrievalChunk) -> str:
        # Asymmetric retrieval format for e5 models
        return f"passage: {chunk.title} {chunk.text}"

    def _get_query_text(self, query: str) -> str:
        return f"query: {query}"

    def _embedding_config(self) -> dict:
        dimension_getter = getattr(
            self.model,
            "get_embedding_dimension",
            self.model.get_sentence_embedding_dimension,
        )
        return {
            "model_name": self.model_name,
            "model_files_sha256": self.model_identity,
            "passage_format": "passage: {title} {text}",
            "query_format": "query: {query}",
            "normalize_embeddings": True,
            "precision": "float32",
            "batch_size": 32,
            "max_seq_length": self.model.max_seq_length,
            "dimensions": dimension_getter(),
            "device": str(self.model.device),
            "libraries": {name: version(name) for name in (
                "sentence-transformers", "transformers", "torch", "tokenizers", "numpy"
            )},
        }

    def _fingerprint(self, chunks: List[RetrievalChunk]) -> str:
        # Full ordered chunks include provenance, versions, offsets and content.
        # A chunking change invalidates naturally; sorting would alter tie behavior.
        return hashlib.sha256(_json_bytes({
            "cache_version": _CACHE_VERSION,
            "embedding": self._embedding_config(),
            "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        })).hexdigest()

    def index(self, chunks: List[RetrievalChunk]) -> None:
        if self.model_identity is not None and self.load_cache(chunks):
            return
        self.chunks = chunks
        texts = [self._get_passage_text(c) for c in chunks]
        if not texts:
            self.embeddings = np.array([])
            return

        logger.info("Generating dense embeddings for %s chunks...", len(texts))
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        self.embeddings = np.array(embeddings)
        if self.model_identity is not None:
            self._save_cache()

    def _save_cache(self) -> None:
        pending_paths = []
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix=".npy", delete=False) as handle:
                pending_paths.append(Path(handle.name))
                np.save(handle, self.embeddings, allow_pickle=False)
                handle.flush()
                os.fsync(handle.fileno())
            embedding_digest = hashlib.sha256(pending_paths[0].read_bytes()).hexdigest()
            manifest = {
                "cache_version": _CACHE_VERSION,
                "fingerprint": self._fingerprint(self.chunks),
                "embeddings_sha256": embedding_digest,
                "chunks": [c.model_dump(mode="json") for c in self.chunks],
            }
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix=".json", delete=False) as handle:
                pending_paths.append(Path(handle.name))
                handle.write(_json_bytes(manifest))
                handle.flush()
                os.fsync(handle.fileno())
            # Publish manifest last; the checksum detects partial/interleaved writes.
            os.replace(pending_paths[0], self.cache_dir / "embeddings.npy")
            os.replace(pending_paths[1], self.cache_dir / "manifest.json")
        except OSError:
            logger.warning("Dense cache could not be saved; using the rebuilt in-memory index.", exc_info=True)
        finally:
            for path in pending_paths:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove temporary dense cache file: %s", path)

    def load_cache(self, expected_chunks: List[RetrievalChunk] | None = None) -> bool:
        if self.model_identity is None:
            return False
        try:
            manifest = json.loads((self.cache_dir / "manifest.json").read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or manifest.get("cache_version") != _CACHE_VERSION:
                raise ValueError("legacy or unsupported manifest")
            stored_chunks = [RetrievalChunk(**item) for item in manifest["chunks"]]
            chunks = expected_chunks if expected_chunks is not None else stored_chunks
            fingerprint = self._fingerprint(chunks)
            if manifest["fingerprint"] != fingerprint or self._fingerprint(stored_chunks) != fingerprint:
                raise ValueError("retrieval inputs or model configuration changed")
            data = (self.cache_dir / "embeddings.npy").read_bytes()
            if hashlib.sha256(data).hexdigest() != manifest["embeddings_sha256"]:
                raise ValueError("embedding checksum mismatch")
            embeddings = np.load(io.BytesIO(data), allow_pickle=False)
            dimension_getter = getattr(
                self.model,
                "get_embedding_dimension",
                self.model.get_sentence_embedding_dimension,
            )
            expected_shape = (len(chunks), dimension_getter())
            if embeddings.shape != expected_shape or not np.issubdtype(embeddings.dtype, np.floating):
                raise ValueError("embedding dimensions or dtype mismatch")
            if not np.isfinite(embeddings).all():
                raise ValueError("non-finite embedding values")
            self.chunks = chunks
            self.embeddings = embeddings
            logger.info("Dense cache HIT: %s chunks.", len(chunks))
            return True
        except (OSError, ValueError, KeyError, TypeError, EOFError) as exc:
            logger.info("Dense cache INVALID -> REBUILD: %s", exc)
            return False

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        if self.embeddings is None or len(self.chunks) == 0:
            return []

        q_text = self._get_query_text(query)
        q_emb = self.model.encode([q_text], normalize_embeddings=True)[0]

        # Cosine similarity (since vectors are normalized, dot product is equivalent)
        scores = np.dot(self.embeddings, q_emb)
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices):
            results.append(RetrievalResult(
                chunk=self.chunks[idx],
                rank=rank + 1,
                score=float(scores[idx]),
                retrieval_method="dense"
            ))
        return results
