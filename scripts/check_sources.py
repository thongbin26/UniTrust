from app.db.database import init_database
from app.sources.health import check_all_sources
from app.sources.repository import seed_sources


def main() -> None:

    init_database()
    seed_sources()

    print()
    print("UniTrust Source Health Check")
    print("=" * 80)

    results = check_all_sources()

    for result in results:

        print(
            f"{result.source_id:<20} "
            f"{result.health_status.value:<10} "
            f"HTTP={result.http_status or '-':<4} "
            f"bytes={result.content_length}"
        )

        if result.error:
            print(
                f"  reason: {result.error}"
            )

    print("=" * 80)


if __name__ == "__main__":
    main()