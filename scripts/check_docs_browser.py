#!/usr/bin/env python3
"""Browser checks on Linux, with generated output served only on loopback.

Setup in the execution checkout:
  .tools/docs/bin/python -m pip install playwright==1.56.0
  PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers" .tools/docs/bin/python -m playwright install chromium
Run:
  .tools/docs/bin/python scripts/check_docs_browser.py
  .tools/docs/bin/python scripts/check_docs_browser.py --base-url https://xieweikai.github.io/mcap-ops/
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".tools/browsers"))


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith("/mcap-ops/"):
            path = path[len("/mcap-ops"):]
        return super().translate_path(path)

    def log_message(self, *_):
        pass


def wait_diagram(page):
    # Material renders SVG inside a closed shadow root; observe the rendered host.
    page.wait_for_function("""() => {
      const diagrams = [...document.querySelectorAll('.mermaid')];
      return diagrams.length > 0 && diagrams.every(el => el.clientHeight > 20);
    }""")


def check(base_url):
    from playwright.sync_api import sync_playwright

    screenshots = ROOT / ".artifacts/docs/screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            permissions=["clipboard-read", "clipboard-write"],
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base_url, wait_until="networkidle")
        assert page.locator("h1").inner_text().strip().startswith("From streams to model steps.")
        assert page.locator(".md-tabs").get_by_role("link", name="Tutorials", exact=True).is_visible()
        assert page.locator(".md-tabs").get_by_role("link", name="Documentation", exact=True).is_visible()
        wait_diagram(page)
        page.screenshot(path=str(screenshots / "home-desktop.png"), full_page=True)
        page.goto(base_url + "reference/python/resample/", wait_until="networkidle")
        page.get_by_role("button", name="Copy to clipboard").first.click()
        page.wait_for_function(
            "async () => (await navigator.clipboard.readText()).includes('mcap_ops.resample')"
        )
        page.screenshot(path=str(screenshots / "reference-desktop.png"), full_page=True)
        page.get_by_role("button", name="Select language").click()
        page.locator('a[hreflang="zh"]').click()
        page.wait_for_url("**/zh/reference/python/resample/")
        assert page.locator("html").get_attribute("lang") == "zh"
        assert page.get_by_role("heading", name="参数").first.is_visible()
        search = page.locator(".md-search__input")
        search.fill("重采样")
        page.wait_for_function("document.querySelectorAll('.md-search-result__item').length > 0")
        assert "重采样" in page.locator(".md-search-result__list").inner_text()
        search.press("Escape")
        page.goto(base_url + "reference/", wait_until="networkidle")
        search.fill("history_windows")
        page.wait_for_function("document.querySelectorAll('.md-search-result__item').length > 0")
        assert "history_windows" in page.locator(".md-search-result__list").inner_text()
        search.press("Escape")
        for route in ("tutorials/first-pipeline/", "tutorials/quality/", "reference/types/",
                      "rsi/", "zh/tutorials/first-pipeline/", "zh/reference/types/", "zh/rsi/"):
            page.goto(base_url + route, wait_until="networkidle")
            wait_diagram(page)
        page.goto(base_url + "rustdoc/mcap_ops_core/struct.Signal.html", wait_until="networkidle")
        assert page.locator('[id="method.new"]').count() == 1
        assert page.locator('[id="method.into_parts"]').count() == 1
        page.goto(base_url + "rustdoc/mcap_ops_io/mcap_ops/trait.SignalDecoder.html",
                  wait_until="networkidle")
        assert page.locator('[id="tymethod.decode"]').count() == 1
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(base_url, wait_until="networkidle")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.get_by_role("link", name="Start the tutorial", exact=True).click()
        page.wait_for_url("**/tutorials/first-pipeline/")
        page.locator('.md-header label[for="__drawer"]').click()
        assert page.locator("#__drawer").is_checked()
        page.locator(".md-sidebar--primary").get_by_role("link", name="Inspect and select", exact=True).click()
        page.wait_for_url("**/tutorials/quality/")
        page.screenshot(path=str(screenshots / "tutorial-mobile.png"), full_page=True)
        page.goto(base_url + "zh/reference/python/resample/", wait_until="networkidle")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(screenshots / "reference-mobile.png"), full_page=True)
        assert not errors, errors
        browser.close()
    print("Browser checks passed: desktop/mobile, locale switching, bilingual search, "
          "clipboard, Mermaid, Rust types/methods; screenshots in .artifacts/docs/screenshots")


def main():
    if sys.platform != "linux":
        raise SystemExit("Run browser checks in the configured Linux execution checkout")
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    args = parser.parse_args()
    if args.base_url:
        check(args.base_url.rstrip("/") + "/")
        return
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Handler, directory=str(ROOT / ".artifacts/docs/site"))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        check(f"http://127.0.0.1:{server.server_port}/mcap-ops/")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
