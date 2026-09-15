import argparse

from app.crawler.service import (
    crawl_source,
)


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        required=True,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    print()
    print(
        "UniTrust DUT Notice Crawler"
    )
    print("=" * 70)

    stats = crawl_source(
        source_id=args.source,
        limit=args.limit,
    )

    for key, value in stats.items():
        print(
            f"{key:<12}: {value}"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()