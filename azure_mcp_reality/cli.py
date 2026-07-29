from __future__ import annotations

import argparse
import json
import sys

from .config import ConfigurationError, RealitySettings
from .observer import ObservationError, observe_current_reality


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit one bounded, non-secret Azure and repository reality observation."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of indented JSON.",
    )
    args = parser.parse_args()

    try:
        settings = RealitySettings.from_env()
        result = observe_current_reality(settings)
    except (ConfigurationError, ObservationError, OSError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": "azure-mcp-reality.observation-error.v1",
                    "observation_status": "observation_failed",
                    "error": str(exc),
                    "mutations_performed": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            result,
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
