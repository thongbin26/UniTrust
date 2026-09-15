import argparse
import json

from app.crawler.repository import (
    count_notices,
    init_notice_tables,
    list_notices,
)
from app.db.database import (
    init_database,
)


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    init_database()
    init_notice_tables()

    total = count_notices()

    print()
    print(
        f"Total notices: {total}"
    )
    print("=" * 90)

    rows = list_notices(
        limit=args.limit
    )

    for row in rows:

        attachments = json.loads(
            row[
                "attachment_links_json"
            ]
        )

        print(
            f"[{row['notice_id']}] "
            f"{row['source_id']}"
        )

        print(
            f"Title: "
            f"{row['title']}"
        )

        print(
            f"Published: "
            f"{row['publication_date']}"
        )

        print(
            f"Parse: "
            f"{row['parse_mode']}"
        )

        print(
            f"Text chars: "
            f"{len(row['raw_text'])}"
        )

        print(
            f"Attachments: "
            f"{len(attachments)}"
        )

        print(
            f"URL: "
            f"{row['canonical_url']}"
        )

        print("-" * 90)


if __name__ == "__main__":
    main()