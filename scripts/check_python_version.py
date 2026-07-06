"""Fail fast when local bootstrap uses an unsupported Python runtime."""

from __future__ import annotations

import sys

MIN_VERSION = (3, 12)


def main() -> int:
    current = sys.version_info[:3]
    if current >= MIN_VERSION:
        return 0

    current_text = ".".join(str(part) for part in current)
    required_text = ".".join(str(part) for part in MIN_VERSION)
    sys.stderr.write(
        "grant-radar-public requires Python "
        f"{required_text}+ for local bootstrap; found {current_text}.\n"
        "Use python3.12 explicitly, create the virtualenv with a 3.12 interpreter,\n"
        "or use the Docker workflow from README.md / CONTRIBUTING.md.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
