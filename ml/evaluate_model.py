"""Print the previously saved hold-out evaluation report."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("models/evaluation.json"))
    args = parser.parse_args()
    if not args.report.is_file():
        raise FileNotFoundError(f"Evaluation report not found: {args.report}")
    print(json.dumps(json.loads(args.report.read_text(encoding="utf-8")), indent=2))


if __name__ == "__main__":
    main()
