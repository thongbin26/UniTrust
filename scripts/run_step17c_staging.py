import argparse
import hashlib
import json
from pathlib import Path

from app.core.config import settings
from app.crawler.repository import (
    count_notices,
    init_notice_tables,
    migrate_notice_discoveries,
)
from app.crawler.service import crawl_source
from app.db.database import get_database_path, init_database
from app.sources.repository import list_sources, seed_sources


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Step 17C against an isolated staging DB.")
    parser.add_argument("--database", required=True)
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--source", action="append", dest="sources")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    production_db = (project_root / "unitrust.db").resolve()
    staging_root = (project_root / "tmp" / "step17c-staging").resolve()
    staging_db = Path(args.database).resolve()

    if production_db == staging_db:
        raise SystemExit("Refusing to use the production database.")
    if staging_root not in staging_db.parents:
        raise SystemExit(f"Staging database must be under {staging_root}")
    if not staging_db.exists():
        raise SystemExit("Create the staging DB as a copy of unitrust.db before running.")

    production_hash_before = sha256(production_db)
    settings.database_url = f"sqlite:///{staging_db}"

    init_database()
    seed_sources()
    init_notice_tables()
    migrate_notice_discoveries()

    configured = [source for source in list_sources() if source.enabled]
    selected_ids = args.sources or [source.source_id for source in configured]
    raw_dir = staging_root / "raw"
    notice_count_before = count_notices()
    rows = []

    for source_id in selected_ids:
        try:
            result = crawl_source(
                source_id,
                limit=args.max_items,
                delay_seconds=args.delay_seconds,
                raw_data_dir=raw_dir,
            )
        except Exception as exc:
            result = {
                "source_id": source_id,
                "discovered": 0,
                "detail_fetches": 0,
                "created": 0,
                "updated": 0,
                "unchanged": 0,
                "duplicate": 0,
                "failed": 1,
                "warnings": [f"{type(exc).__name__}: {exc}"],
                "duration_seconds": 0,
            }
        rows.append(result)

    production_hash_after = sha256(production_db)
    report = {
        "staging_database": str(staging_db),
        "production_hash_before": production_hash_before,
        "production_hash_after": production_hash_after,
        "production_unchanged": production_hash_before == production_hash_after,
        "registered_sources": len(list_sources()),
        "enabled_sources": len(configured),
        "notice_count_before": notice_count_before,
        "notice_count_after": count_notices(),
        "sources": rows,
    }
    if not report["production_unchanged"]:
        raise RuntimeError("Production database hash changed during staging crawl.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
