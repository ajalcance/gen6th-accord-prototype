"""Fixed loopback scanner readiness; protocol/freshness proof, never a clean-scan verdict."""

import asyncio
import sys

from accord.personas.photo_contracts import PhotoUnavailableError
from accord.personas.photo_scanner import ClamdScanner, ScanReceipt, definition_receipt

PROBE_SECONDS = 5


async def probe_scanner() -> ScanReceipt:
    """Require exact PONG and the existing fresh VERSION receipt inside one deadline."""
    scanner = ClamdScanner(host="127.0.0.1", port=3310)
    try:
        async with asyncio.timeout(PROBE_SECONDS):
            if await scanner.command(b"zPING\x00") != b"PONG\x00":
                raise PhotoUnavailableError("scanner readiness unavailable")
            return definition_receipt(await scanner.command(b"zVERSION\x00"))
    except Exception:
        raise PhotoUnavailableError("scanner readiness unavailable") from None


def main() -> None:
    """No arguments, endpoint overrides or private exception contents in CLI output."""
    if len(sys.argv) != 1:
        print("scanner_readiness=failed")
        raise SystemExit(1)
    try:
        asyncio.run(probe_scanner())
    except PhotoUnavailableError:
        print("scanner_readiness=failed")
        raise SystemExit(1) from None
    print("scanner_readiness=passed")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
