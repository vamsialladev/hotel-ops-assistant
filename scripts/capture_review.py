"""Design-review screenshots: every public page in light and dark mode, laptop and optionally phone size.

Start the app first (streamlit run app.py), then:
  python scripts/capture_review.py --out review            # public pages, light and dark
  python scripts/capture_review.py --out review --phone    # also a phone-sized set

README and portfolio images come from scripts/capture_screenshots.py instead. Asks one real question per
color scheme and size (about $0.0002 each). The Admin page is never captured.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "assistant": "",
    "insights": "insights",
    "library": "library",
    "how-it-works": "how_it_works",
    "privacy": "privacy",
}
SIZES = {"desktop": (1280, 900), "phone": (390, 844)}


def wait_ready(page):
    page.wait_for_selector("h1.hoa-title", timeout=180_000)
    page.wait_for_timeout(1500)  # let fonts and charts settle


def shot(page, path: Path, width: int, height: int):
    """Streamlit scrolls inside its main container, so grow the viewport to the content height first."""
    content = page.evaluate(  # tallest scrolling area, ignoring the (possibly collapsed) sidebar
        "() => Math.max(...Array.from(document.querySelectorAll('*'))"
        ".filter(el => !el.closest('[data-testid=stSidebar]')).map(el => el.scrollHeight))"
    )
    page.set_viewport_size({"width": width, "height": max(height, int(content))})
    page.evaluate(
        "() => { window.scrollTo(0, 0);"
        " document.querySelectorAll('*').forEach(el => { if (el.scrollTop > 0) el.scrollTop = 0; }); }"
    )
    page.wait_for_timeout(500)
    page.screenshot(path=path)
    page.set_viewport_size({"width": width, "height": height})


def ask(page, question: str):
    page.get_by_placeholder("Ask about a hotel policy").fill(question)
    page.keyboard.press("Enter")
    page.wait_for_selector(".hoa-status", timeout=60_000)
    page.wait_for_timeout(1500)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:8501")
    p.add_argument("--out", default=str(ROOT / "review"))
    p.add_argument("--phone", action="store_true")
    p.add_argument("--question", default="A Gold member wants late checkout on Saturday. How late can they stay?")
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sizes = ["desktop", "phone"] if a.phone else ["desktop"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for scheme in ("light", "dark"):
            for size in sizes:
                w, h = SIZES[size]
                context = browser.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                page = context.new_page()
                for name, path in PAGES.items():
                    page.goto(f"{a.url}/{path}")
                    wait_ready(page)
                    if name == "assistant":
                        shot(page, out / f"welcome-{scheme}-{size}.png", w, h)
                        page.set_viewport_size({"width": w, "height": 2200})  # no scrolling while the chat grows
                        ask(page, a.question)
                        page.set_viewport_size({"width": w, "height": h})
                        page.wait_for_timeout(800)
                    suffix = "" if size == "desktop" else f"-{size}"
                    shot(page, out / f"{name}-{scheme}{suffix}.png", w, h)
                    print("saved", name, scheme, size)
                context.close()
        browser.close()


if __name__ == "__main__":
    main()
