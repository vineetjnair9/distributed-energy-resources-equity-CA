"""Write the API's OpenAPI document to docs/openapi.json.

The frontend generates its TypeScript types from this file
(npm --prefix frontend run gen:types), and CI fails if it is stale:

    python scripts/export_openapi.py --check
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.api.api import app  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the file is out of date.")
    args = parser.parse_args(argv)
    document = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != document:
            sys.exit(f"{OUTPUT} is stale. Run: python scripts/export_openapi.py")
        print("OpenAPI document is current.")
        return
    OUTPUT.write_text(document)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
