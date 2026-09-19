"""Resolve the prepared E5 snapshot without loading torch or contacting the Hub."""

import json
import os
from pathlib import Path

from huggingface_hub import try_to_load_from_cache


DEFAULT_MODEL_NAME = "intfloat/multilingual-e5-small"
_REQUIRED_JSON = (
    "config.json", "modules.json", "sentence_bert_config.json",
    "tokenizer_config.json", "special_tokens_map.json", "tokenizer.json",
    "1_Pooling/config.json",
)


def resolve_local_model(model_name: str = DEFAULT_MODEL_NAME) -> Path:
    """Find a complete local snapshot; raise FileNotFoundError if not prepared.

    The Hub resolver honors HF_HOME/HF_HUB_CACHE and cached revision refs.
    SENTENCE_TRANSFORMERS_HOME overrides that cache just as in SentenceTransformer.
    No model loading, weight hashing, downloads or network checks happen here.
    """
    configured_path = Path(model_name)
    if configured_path.is_dir():
        snapshot = configured_path
    else:
        cached = try_to_load_from_cache(
            model_name, "config.json",
            cache_dir=os.environ.get("SENTENCE_TRANSFORMERS_HOME") or None,
        )
        if not isinstance(cached, str):
            raise FileNotFoundError(
                f"Local model {model_name} is unavailable. Prepare its complete "
                "Hugging Face cache while online before the offline demo."
            )
        snapshot = Path(cached).parent
    try:
        for relative in _REQUIRED_JSON:
            path = snapshot / relative
            if path.stat().st_size == 0:
                raise ValueError(f"empty file: {relative}")
            # tokenizer.json is large; presence suffices for lightweight preflight.
            if relative != "tokenizer.json":
                with path.open(encoding="utf-8") as handle:
                    json.load(handle)
        weights = (snapshot / "model.safetensors", snapshot / "pytorch_model.bin")
        if not any(path.is_file() and path.stat().st_size > 0 for path in weights):
            raise ValueError("model weights are absent")
    except (OSError, ValueError) as exc:
        raise FileNotFoundError(
            f"Local model {model_name} is incomplete ({exc}). Prepare the complete "
            "model cache while online before the offline demo."
        ) from exc
    return snapshot


def model_files(snapshot: Path) -> list[Path]:
    """Inference inputs, excluding documentation and Hub bookkeeping."""
    return sorted(
        path for path in snapshot.rglob("*")
        if path.is_file() and path.suffix in {".json", ".safetensors", ".bin", ".model", ".txt"}
        and ".cache" not in path.relative_to(snapshot).parts
    )
