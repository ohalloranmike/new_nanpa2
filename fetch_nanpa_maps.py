"""
Download US state area-code map GIFs from nanpa.com into map_fetch_review/ for review.

Output uses static/USACMaps/ file names ({ST}.gif, optional insets) so approved
files can be copied into production. Not part of refresh_data.py.
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from app.config import Config
from app.constants import STATES

NANPA_INLINE_IMAGE_BASE = "https://www.nanpa.com/sites/default/files/inline-images"
OUTPUT_FOLDER = "USACMaps"
MIN_BYTES = 400
REQUEST_PAUSE_SEC = 0.35


@dataclass
class FetchResult:
    filename: str
    url: str | None = None
    status: str = "pending"
    detail: str = ""
    bytes: int = 0


@dataclass
class RunReport:
    output_root: Path
    results: list[FetchResult] = field(default_factory=list)

    def add(self, result: FetchResult) -> None:
        self.results.append(result)

    def write_manifest(self) -> Path:
        path = self.output_root / "manifest.json"
        payload = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "output_root": str(self.output_root),
            "source": NANPA_INLINE_IMAGE_BASE,
            "summary": self.summary(),
            "files": [
                {
                    "filename": r.filename,
                    "status": r.status,
                    "url": r.url,
                    "bytes": r.bytes,
                    "detail": r.detail,
                    "copy_to": f"static/{OUTPUT_FOLDER}/{r.filename}",
                }
                for r in self.results
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.results:
            counts[row.status] = counts.get(row.status, 0) + 1
        return counts


def _candidate_urls(filename: str) -> list[str]:
    lc_name = filename.lower()
    stem = filename[:-4]
    code = stem.split("-")[0].lower()
    urls = [f"{NANPA_INLINE_IMAGE_BASE}/{lc_name}"]
    if stem.upper() == code.upper():
        urls.append(f"{NANPA_INLINE_IMAGE_BASE}/{code}_0.gif")
    return list(dict.fromkeys(urls))


def _looks_like_gif(content: bytes, content_type: str) -> bool:
    if len(content) < MIN_BYTES:
        return False
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return True
    lowered = content_type.lower()
    return "image" in lowered or "octet-stream" in lowered


def _fetch_one(
    session: requests.Session,
    verify: bool,
    dest: Path,
    urls: list[str],
) -> FetchResult:
    result = FetchResult(filename=dest.name)

    for url in urls:
        result.url = url
        try:
            response = session.get(url, allow_redirects=True, verify=verify, timeout=60)
        except requests.RequestException as exc:
            result.detail = str(exc)
            continue

        if response.status_code == 404:
            result.detail = "404"
            continue
        if response.status_code != 200:
            result.detail = f"HTTP {response.status_code}"
            continue

        content = response.content
        content_type = response.headers.get("content-type", "")
        if not _looks_like_gif(content, content_type):
            result.detail = f"Not a GIF ({content_type or 'unknown type'})"
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        result.status = "saved"
        result.bytes = len(content)
        result.detail = "OK"
        return result

    result.status = "missing"
    if len(urls) > 1 and result.detail:
        result.detail = f"Tried {len(urls)} URLs; last: {result.detail}"
    elif not result.detail:
        result.detail = "No URL returned a usable GIF"
    return result


def _job_filenames(state_codes: list[str]) -> list[str]:
    names: list[str] = []
    for code in state_codes:
        for suffix in ("", "-inset1", "-inset2"):
            names.append(f"{code}{suffix}.gif")
    return names


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch US state area-code map GIFs from nanpa.com into map_fetch_review/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Review folder (default: <project>/map_fetch_review)",
    )
    parser.add_argument(
        "--state",
        action="append",
        metavar="ST",
        help="Two-letter state/DC code (repeatable). Default: all states.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print URLs only; do not download")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = Config()

    if args.state:
        codes = [code.upper() for code in args.state]
        unknown = [code for code in codes if code not in STATES]
        if unknown:
            print(f"Unknown state codes: {', '.join(unknown)}", file=sys.stderr)
            return 2
    else:
        codes = sorted(STATES.keys())

    output_root = args.output or (config.BASE_DIR / "map_fetch_review")
    report = RunReport(output_root=output_root)
    filenames = _job_filenames(codes)

    session = requests.Session()
    session.headers["User-Agent"] = "nanpa2-map-fetch/1.0 (manual review; +https://github.com/mohal2_nike/nanpa2)"

    verify = config.REQUESTS_VERIFY
    if not verify:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for filename in filenames:
        dest = output_root / OUTPUT_FOLDER / filename
        urls = _candidate_urls(filename)
        if args.dry_run:
            for url in urls:
                report.add(FetchResult(filename=filename, url=url, status="dry_run"))
                print(f"[dry-run] {OUTPUT_FOLDER}/{filename} <- {url}")
            continue

        result = _fetch_one(session, verify, dest, urls)
        report.add(result)
        label = f"{OUTPUT_FOLDER}/{filename}"
        if result.status == "saved":
            print(f"[saved]   {label} ({result.bytes} bytes) <- {result.url}")
        else:
            print(f"[{result.status}] {label} ({result.detail})")
        time.sleep(REQUEST_PAUSE_SEC)

    manifest = report.write_manifest()
    summary = report.summary()
    print()
    print(f"Review folder: {output_root}")
    print(f"Manifest:      {manifest}")
    print(f"Summary:       {summary}")
    print()
    print("Copy approved files into static/, e.g.:")
    print(f"  xcopy /Y /I {output_root}\\{OUTPUT_FOLDER}\\*.gif static\\{OUTPUT_FOLDER}\\")
    print()
    print("Note: nanpa.com usually hosts the main {ST}.gif only; inset maps may stay missing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
