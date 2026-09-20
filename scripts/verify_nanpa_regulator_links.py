"""Check NANP regulator URLs (HTTPS + valid certificate). Run from repo root."""

from __future__ import annotations

import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.nanpa_regulators import CANADIAN_NUMBERING_ADMIN, NANPA_US, NANP_MEMBER_REGULATORS

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Sites that block simple HTTP clients but load in a normal browser (verified manually).
MANUAL_BROWSER_OK = frozenset(
    {
        "https://www.ntrc.kn/",
        "https://tatt.org.tt/",
    }
)


def check(url: str) -> tuple[int | None, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as response:
            return response.status, response.geturl()
    except Exception as exc:
        return None, str(exc)


def main() -> int:
    entries: list[tuple[str, str]] = [("US/CAN default", NANPA_US["url"]), ("Canada", CANADIAN_NUMBERING_ADMIN["url"])]
    for key, reg in sorted(NANP_MEMBER_REGULATORS.items()):
        entries.append((key, reg["url"]))

    failed = 0
    for label, url in entries:
        status, detail = check(url)
        if status is not None and 200 <= status < 400:
            print(f"OK  {status:3}  {label}: {detail}")
        elif url in MANUAL_BROWSER_OK:
            print(f"OK  browser {label}: {url} (automated check blocked; loads in a normal browser)")
        else:
            failed += 1
            print(f"FAIL      {label}: {url}")
            print(f"          {detail}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
