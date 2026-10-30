#!/usr/bin/env python3
"""Render docs/assets/showcase/showcase.html into one 2x PNG per example.

Run: uv run --with playwright python tools/capture_showcase.py
First use: uv run --with playwright playwright install chromium
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "docs/assets/showcase"
EXAMPLES = ("development", "review", "documentation", "api-design")
FRAME_SIZE = (1200, 900)
SCALE = 2


def capture(out_dir: Path) -> list[Path]:
    written = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1280, "height": 960}, device_scale_factor=SCALE
        )
        page.goto((SHOWCASE / "showcase.html").as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        for name in EXAMPLES:
            frame = page.locator(f"section.frame:has(#{name})")
            box = frame.bounding_box()
            if box is None or (round(box["width"]), round(box["height"])) != FRAME_SIZE:
                sys.exit(f"{name}: frame is {box}, expected {FRAME_SIZE}; content overflowed")
            overflow = page.evaluate(
                "(id) => { const b = document.querySelector('#' + id + ' .body');"
                " return b.scrollHeight > b.clientHeight; }",
                name,
            )
            if overflow:
                sys.exit(f"{name}: content overflows the card")
            target = out_dir / f"{name}.png"
            frame.screenshot(path=str(target))
            written.append(target)
        browser.close()
    return written


def compress(paths: list[Path]) -> None:
    pngquant = shutil.which("pngquant")
    if pngquant is None:
        print("pngquant not found; skipping compression", file=sys.stderr)
        return
    for path in paths:
        subprocess.run(
            [pngquant, "--force", "--skip-if-larger", "--quality=85-98", "--output", str(path), str(path)],
            check=False,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--out", type=Path, default=SHOWCASE, help="output directory")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    paths = capture(args.out)
    compress(paths)
    for path in paths:
        print(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
