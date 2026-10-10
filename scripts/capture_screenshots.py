"""Capture the README and portfolio screenshots from the running app: real questions, real answers.

Start the app first (streamlit run app.py), then:
  python scripts/capture_screenshots.py                    # everything -> docs/images/
  python scripts/capture_screenshots.py --out some/folder  # somewhere else

Asks about 9 real questions (about $0.002 of API use, and 9 slots of the daily cap). Public pages only:
the Admin page is never captured. Needs the dev-only Playwright package:
  pip install playwright && python -m playwright install chromium
"""

import argparse
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DESKTOP, PHONE = (1280, 900), (390, 844)
MESSAGES = "[data-testid=stChatMessage]"


def viewport(size):
    return {"width": size[0], "height": size[1]}


def ready(page):
    page.wait_for_selector("h1.hoa-title", timeout=180_000)
    page.wait_for_timeout(1500)  # fonts and layout settle


def content_height(page) -> int:
    return int(
        page.evaluate(
            "() => Math.max(...Array.from(document.querySelectorAll('*'))"
            ".filter(el => !el.closest('[data-testid=stSidebar]')).map(el => el.scrollHeight))"
        )
    )


def shot(page, path: Path, size):
    """Full page: Streamlit scrolls inside its own container, so grow the viewport to the content first."""
    page.set_viewport_size({"width": size[0], "height": max(size[1], content_height(page))})
    page.evaluate("() => document.querySelectorAll('*').forEach(el => { if (el.scrollTop > 0) el.scrollTop = 0; })")
    page.wait_for_timeout(600)
    page.screenshot(path=path)
    page.set_viewport_size(viewport(size))
    print("saved", path.name)


def pick(page, prop: str):
    page.locator("[data-testid=stButtonGroup] button", has_text=prop).first.click()
    page.wait_for_timeout(1200)


def ask(page, question: str) -> int:
    """Ask a question and wait for the finished answer. Returns the index of the question bubble."""
    before = page.locator(MESSAGES).count()
    box = page.get_by_placeholder("Ask about a hotel policy")
    box.fill(question)
    box.press("Enter")
    page.wait_for_function(f"document.querySelectorAll('{MESSAGES}').length >= {before + 2}", timeout=60_000)
    page.locator(MESSAGES).nth(before + 1).locator(".hoa-status, [data-testid=stAlert]").first.wait_for(timeout=60_000)
    page.wait_for_timeout(1200)
    return before


def turn_image(page, first_index: int) -> Image.Image:
    """Screenshot of one question + answer pair, with a viewport tall enough that nothing scrolls."""
    page.set_viewport_size({"width": DESKTOP[0], "height": max(DESKTOP[1], content_height(page))})
    page.wait_for_timeout(500)
    q, a = page.locator(MESSAGES).nth(first_index), page.locator(MESSAGES).nth(first_index + 1)
    top, bottom = q.bounding_box(), a.bounding_box()
    clip = {
        "x": top["x"] - 8,
        "y": top["y"] - 8,
        "width": top["width"] + 16,
        "height": bottom["y"] + bottom["height"] - top["y"] + 16,
    }
    image = Image.open(io.BytesIO(page.screenshot(clip=clip)))
    page.set_viewport_size(viewport(DESKTOP))
    return image


def save(image: Image.Image, path: Path):
    image.save(path, optimize=True)
    print("saved", path.name)


def side_by_side(images, labels, path: Path):
    bold = Path("C:/Windows/Fonts/segoeuib.ttf")
    font = ImageFont.truetype(str(bold), 26) if bold.exists() else ImageFont.load_default(26)
    w = max(im.width for im in images)
    h = max(im.height for im in images) + 56
    canvas = Image.new("RGB", (len(images) * w + (len(images) + 1) * 24, h + 24), "#F5F7F6")
    d = ImageDraw.Draw(canvas)
    for i, (im, label) in enumerate(zip(images, labels, strict=True)):
        x = 24 + i * (w + 24)
        d.text((x, 14), label, fill="#1E4636", font=font)
        canvas.paste(im, (x, 56))
    save(canvas, path)


def record_gif(page, question: str, path: Path):
    """Real frames while typing and while the answer streams in, assembled into a GIF."""
    frames, durations = [], []

    def grab(ms):
        png = page.screenshot(clip={"x": 300, "y": 0, "width": 980, "height": 900})
        frames.append(Image.open(io.BytesIO(png)).convert("RGB").resize((735, 675)))
        durations.append(ms)

    for _ in range(4):
        grab(500)
    box = page.get_by_placeholder("Ask about a hotel policy")
    box.click()
    for i in range(0, len(question), 3):
        box.press_sequentially(question[i : i + 3], delay=20)
        grab(110)
    grab(700)
    before = page.locator(MESSAGES).count()
    box.press("Enter")
    page.wait_for_function(f"document.querySelectorAll('{MESSAGES}').length >= {before + 2}", timeout=60_000)
    answer = page.locator(MESSAGES).nth(before + 1)
    for _ in range(60):  # streaming, about 150 ms per frame
        grab(150)
        if answer.locator(".hoa-status").count():
            break
    page.wait_for_timeout(800)
    for _ in range(3):
        grab(1600)  # hold on the finished answer with its sources
    quantized = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    quantized[0].save(path, save_all=True, append_images=quantized[1:], duration=durations, loop=0, optimize=True)
    print("saved", path.name, f"{path.stat().st_size / 1e6:.1f} MB, {sum(durations) / 1000:.1f}s")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:8501")
    p.add_argument("--out", default=str(ROOT / "docs" / "images"))
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # Light mode, laptop: the main story
        page = browser.new_context(viewport=viewport(DESKTOP), color_scheme="light").new_page()
        page.goto(a.url)
        ready(page)
        pick(page, "Beach Resort")
        shot(page, out / "assistant-welcome.png", DESKTOP)

        i = ask(page, "A Gold member wants late checkout on Saturday. How late can they stay?")
        page.locator(MESSAGES).nth(i + 1).get_by_text("Sources").first.click()
        page.wait_for_timeout(900)
        save(turn_image(page, i), out / "answer-sources.png")
        page.locator(MESSAGES).nth(i + 1).get_by_role("button", name="👍").click()  # a real rating of a correct answer
        page.wait_for_timeout(800)
        shot(page, out / "assistant-light.png", DESKTOP)

        beach_dog = turn_image(page, ask(page, "Can a guest bring their dog?"))
        save(turn_image(page, ask(page, "Can I give a guest a $300 refund myself?")), out / "check-with-manager.png")
        save(turn_image(page, ask(page, "Where is the fire assembly point?")), out / "refusal.png")

        pick(page, "Mountain Lodge")
        lodge_dog = turn_image(page, ask(page, "Can a guest bring their dog?"))
        side_by_side([beach_dog, lodge_dog], ["Beach Resort", "Mountain Lodge"], out / "two-properties.png")
        ask(page, "Can a guest check in early?")

        for name, path in (("insights", "insights"), ("library", "library"), ("how-it-works", "how_it_works")):
            page.goto(f"{a.url}/{path}")
            ready(page)
            shot(page, out / f"{name}.png", DESKTOP)

        # The streaming GIF, starting from the welcome screen of a fresh conversation
        page.goto(a.url)
        ready(page)
        pick(page, "Beach Resort")
        page.get_by_role("button", name="New conversation").click()
        page.wait_for_timeout(1200)
        record_gif(page, "What time is breakfast served?", out / "demo.gif")

        # Dark mode, laptop
        page = browser.new_context(viewport=viewport(DESKTOP), color_scheme="dark").new_page()
        page.goto(a.url)
        ready(page)
        pick(page, "Mountain Lodge")
        ask(page, "Where should a guest park their RV?")
        shot(page, out / "assistant-dark.png", DESKTOP)

        # Phone width
        page = browser.new_context(viewport=viewport(PHONE), color_scheme="light").new_page()
        page.goto(a.url)
        ready(page)
        pick(page, "Beach Resort")
        ask(page, "How much is valet parking?")
        shot(page, out / "phone.png", PHONE)
        browser.close()


if __name__ == "__main__":
    main()
