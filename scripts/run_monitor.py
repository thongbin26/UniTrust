"""Run the opt-in V2 official-source monitor against isolated data only."""
import argparse
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _copy_if_missing(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True, help="V2 development data root; never the RC repository data directory.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=600)
    parser.add_argument("--limit", type=int, default=3, help="Maximum detail notices per source in one bounded cycle.")
    parser.add_argument("--bootstrap-from", type=Path, default=Path("unitrust.db"))
    args = parser.parse_args()
    if args.interval_seconds < 300:
        parser.error("--interval-seconds must be at least 300")
    if args.limit < 1 or args.limit > 20:
        parser.error("--limit must be between 1 and 20")
    root = args.data_root.resolve()
    repo_root = PROJECT_ROOT
    protected = (repo_root / "unitrust.db").resolve()
    database = root / "unitrust-v2.db"
    if database == protected or root == repo_root:
        parser.error("V2 monitor data root must be outside protected repository runtime paths.")
    _copy_if_missing(args.bootstrap_from.resolve(), database)
    os.environ["DATABASE_URL"] = f"sqlite:///{database}"
    os.environ["RETRIEVAL_CACHE_DIR"] = str(root / "retrieval")
    os.environ["MONITORING_RAW_DATA_DIR"] = str(root / "raw")
    os.environ["MONITORING_ENABLED"] = "true"
    os.environ["DENSE_LOCAL_FILES_ONLY"] = "true"
    from app.core.config import settings
    from app.monitoring.retrieval import rebuild_current_corpus
    from app.monitoring.service import MonitoringService, conditional_listing_probe
    from app.crawler.service import crawl_source
    service = MonitoringService(
        interval_seconds=args.interval_seconds,
        raw_data_dir=Path(settings.monitoring_raw_data_dir),
        retrieval_sync=rebuild_current_corpus,
        conditional_probe=conditional_listing_probe,
        crawl=lambda source_id, **kwargs: crawl_source(source_id, limit=args.limit, **kwargs),
    )
    if args.once:
        print(service.run_once().model_dump_json())
        return 0
    service.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
