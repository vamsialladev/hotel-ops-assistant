"""Record the captioned demo video from the LIVE app: real questions, real streamed answers.

python scripts/record_demo.py                       # record + build docs/video/demo.mp4 and docs/images/demo.gif
python scripts/record_demo.py --rebuild             # rebuild from the last raw recording (no new questions)
python scripts/record_demo.py --web-out ../vamsi-portfolio/videos/hotel-ops-demo.mp4   # also a web copy + poster

Follows docs/DEMO_SCRIPT.md: welcome, the dog question at both hotels, the Gold member late checkout with
sources, a "check with a manager" answer, the fire assembly point refusal, New conversation, then the
Insights, Document library and How it works pages. Never opens the Admin page and never shows a setting.
Asks 5 real questions (well under $0.01 and 5 slots of the daily cap).

Dev-only: needs Playwright (pip install playwright && python -m playwright install chromium) and ffmpeg on PATH.
The video is git-ignored (docs/video/); publish the web copy to the portfolio repo instead.
"""

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "video"
WORK = OUT / "work"
GIF = ROOT / "docs" / "images" / "demo.gif"
APP = "https://hotel-ops-assistant.streamlit.app/~/+/"  # the app itself, without Streamlit Cloud's frame
SIZE = (1280, 720)
VIEW = (1280, 640)  # the app; the 80 px band under it holds the captions, so they never cover the UI
FPS = 30
MSG = "[data-testid=stChatMessage]"
GREEN, BRASS, CREAM, INK = "#1E4636", "#94702C", "#F4F1EA", "#FFFFFF"
TITLE = "Hotel Operations Knowledge Assistant · Vamsi Alla"
LINKS = [
    ("Portfolio", "vamsialladev.github.io"),
    ("Live app", "hotel-ops-assistant.streamlit.app"),
    ("GitHub", "github.com/vamsialladev/hotel-ops-assistant"),
]
TITLE_SECONDS, END_SECONDS = 3, 6
GIF_STEP = "beach_dog"  # the GIF is this step of the recording (about 12 seconds)


# ---------------------------------------------------------------- recording
class Recorder:
    def __init__(self, page):
        self.page, self.t0, self.steps = page, time.monotonic(), []

    def now(self) -> float:
        return round(time.monotonic() - self.t0, 2)

    def step(self, key: str, caption: str):
        self.steps.append({"key": key, "caption": caption, "start": self.now()})

    def pause(self, seconds: float):
        self.page.wait_for_timeout(int(seconds * 1000))

    def scroll(self, pixels: int, steps: int = 12):
        """Smooth scroll inside Streamlit's main area (Playwright's own scrolling jumps)."""
        self.page.mouse.move(800, 400)
        for _ in range(steps):
            self.page.mouse.wheel(0, pixels / steps)
            self.page.wait_for_timeout(45)


def ready(page):
    page.wait_for_selector("h1.hoa-title", timeout=240_000)
    page.wait_for_timeout(2000)


def pick(page, prop: str):
    page.locator("[data-testid=stButtonGroup] button", has_text=prop).first.click()
    page.wait_for_timeout(1500)


def to_bottom(page):
    """Scroll the chat to the bottom, so Streamlit keeps following the streaming answer."""
    page.mouse.move(800, 300)
    for _ in range(10):
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(30)


def wait_for_answer(page, before: int):
    """Wait until the answer has finished streaming (its status line appears only when it's complete)."""
    page.wait_for_function(f"document.querySelectorAll('{MSG}').length >= {before + 2}", timeout=90_000)
    answer = page.locator(MSG).nth(before + 1)
    answer.locator(".hoa-status, [data-testid=stAlert]").first.wait_for(timeout=90_000)
    answer.evaluate("el => el.scrollIntoView({block: 'end', behavior: 'smooth'})")  # the whole answer in view
    page.wait_for_timeout(600)
    return answer


def click_sample(page, text: str):
    before = page.locator(MSG).count()
    page.get_by_role("button", name=text).first.click()
    to_bottom(page)
    return wait_for_answer(page, before)


def type_question(page, text: str):
    before = page.locator(MSG).count()
    to_bottom(page)
    box = page.get_by_placeholder("Ask about a hotel policy")
    box.click()
    box.press_sequentially(text, delay=45)  # a natural typing speed
    page.wait_for_timeout(400)
    box.press("Enter")
    return wait_for_answer(page, before)


def open_page(page, title: str):
    page.locator("[data-testid=stSidebarNav] a", has_text=title).first.click()
    page.wait_for_selector(f"h1.hoa-title:has-text('{title}')", timeout=60_000)
    page.wait_for_timeout(1200)


def record() -> tuple[Path, dict]:
    from playwright.sync_api import sync_playwright

    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": VIEW[0], "height": VIEW[1]},
            record_video_dir=str(WORK),
            record_video_size={"width": VIEW[0], "height": VIEW[1]},
            color_scheme="light",
        )
        page = ctx.new_page()
        r = Recorder(page)
        page.goto(APP, timeout=180_000)
        ready(page)
        pick(page, "Beach Resort")
        trim = r.now()

        r.step("welcome", "Front-desk staff answer policy questions all day. Rules differ by hotel.")
        r.pause(5)

        r.step("beach_dog", "Beach Resort: ask in plain English. Every fact is cited.")
        click_sample(page, "Can a guest bring their dog?")
        r.pause(6.5)

        r.step("lodge_dog", "Mountain Lodge: same question, its own rules.")
        pick(page, "Mountain Lodge")
        click_sample(page, "Can a guest bring their dog?")
        r.pause(6.5)

        r.step("gold", "The hotel's weekend rule beats the loyalty perk. Sources show the text.")
        pick(page, "Beach Resort")
        answer = type_question(page, "A Gold member wants late checkout on Saturday. How late can they stay?")
        r.pause(2)
        answer.get_by_text("Sources", exact=True).first.click()
        page.wait_for_timeout(800)
        r.scroll(300)
        r.pause(6.5)

        r.step("manager", 'Refunds over the limit: "Check with a manager", quoting the rule.')
        type_question(page, "Can I give a guest a $300 refund myself?")
        r.pause(7)

        r.step("refusal", "Not in the documents? It refuses instead of guessing.")
        type_question(page, "Where is the fire assembly point?")
        r.pause(6.5)

        r.step("new_chat", "New conversation clears the chat for the next guest.")
        page.locator("[data-testid=stSidebar] button", has_text="New conversation").first.click()
        r.pause(3.5)

        r.step("insights", "Insights: what staff ask and where the policies have gaps.")
        open_page(page, "Insights")
        r.pause(2.5)
        r.scroll(700, 20)
        r.pause(4)

        r.step("library", "Document library: the only sources the AI may use.")
        open_page(page, "Document library")
        r.pause(2.5)
        r.scroll(400)
        r.pause(3)

        r.step("how", "How it works: 54 test questions, 96% answer accuracy on this live demo.")
        open_page(page, "How it works")
        r.pause(3)
        r.scroll(500)
        r.pause(4)
        page.locator("h2, h3", has_text="Model choice").first.scroll_into_view_if_needed()
        r.pause(4)
        end = r.now()

        video = page.video
        ctx.close()  # finishes writing the video file
        raw = Path(video.path())
        browser.close()
    timeline = {"trim": trim, "end": end, "steps": r.steps}
    raw = raw.rename(WORK / "raw.webm")
    (WORK / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return raw, timeline


# ---------------------------------------------------------------- building
def font(name: str, size: int):
    for candidate in (name, "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def centered(draw, y, text, fnt, fill):
    width = draw.textlength(text, font=fnt)
    draw.text(((SIZE[0] - width) / 2, y), text, font=fnt, fill=fill)


def title_card(path: Path):
    img = Image.new("RGB", SIZE, GREEN)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE[1] - 14, SIZE[0], SIZE[1]], fill=BRASS)
    centered(d, 250, "Hotel Operations Knowledge Assistant", font("georgiab.ttf", 58), INK)
    centered(d, 340, "Vamsi Alla", font("georgia.ttf", 38), "#E8D9B5")
    centered(d, 430, "Simulated client engagement · synthetic hotel documents", font("arial.ttf", 24), CREAM)
    img.save(path)


def end_card(path: Path):
    img = Image.new("RGB", SIZE, GREEN)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE[1] - 14, SIZE[0], SIZE[1]], fill=BRASS)
    centered(d, 170, "Try it, read the code, see the decisions", font("georgiab.ttf", 46), INK)
    label_font, link_font = font("arialbd.ttf", 26), font("arial.ttf", 32)
    for i, (label, url) in enumerate(LINKS):
        y = 290 + i * 90
        centered(d, y, label.upper(), label_font, "#E8D9B5")
        centered(d, y + 34, url, link_font, INK)
    img.save(path)


def ass_time(seconds: float) -> str:
    seconds = max(seconds, 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def captions(timeline: dict, offset: float) -> str:
    """ASS subtitles: white text in the dark band under the app, one caption per step.
    `offset` shifts them past the title card."""
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        # White bold text, no outline, centered in the 80 px band (colours are &HAABBGGRR)
        "Style: Cap,Arial,28,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,2,40,40,24,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    steps, lines = timeline["steps"], []
    for i, step in enumerate(steps):
        start = step["start"] - timeline["trim"] + offset
        stop = (steps[i + 1]["start"] if i + 1 < len(steps) else timeline["end"]) - timeline["trim"] + offset
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(stop - 0.05)},Cap,,0,0,0,,{step['caption']}")
    return head + "\n".join(lines) + "\n"


def ffmpeg(*args: str):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True, cwd=WORK)


def build(timeline: dict) -> Path:
    title_card(WORK / "title.png")
    end_card(WORK / "end.png")
    (WORK / "captions.ass").write_text(captions(timeline, TITLE_SECONDS), encoding="utf-8")
    length = timeline["end"] - timeline["trim"]
    scale = f"scale={SIZE[0]}:{SIZE[1]},fps={FPS},format=yuv420p,setsar=1"
    band = f"scale={VIEW[0]}:{VIEW[1]},pad={SIZE[0]}:{SIZE[1]}:0:0:color=0x111111,fps={FPS},format=yuv420p,setsar=1"
    graph = (
        f"[0:v]{scale},fade=t=out:st={TITLE_SECONDS - 0.4}:d=0.4[t];"
        f"[1:v]{band},fade=t=in:st=0:d=0.4[m];"
        f"[2:v]{scale},fade=t=in:st=0:d=0.4[e];"
        "[t][m][e]concat=n=3:v=1:a=0,subtitles=captions.ass[v]"
    )
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "demo.mp4"
    ffmpeg(
        *("-loop", "1", "-t", str(TITLE_SECONDS), "-i", "title.png"),
        *("-ss", f"{timeline['trim']:.2f}", "-t", f"{length:.2f}", "-i", "raw.webm"),
        *("-loop", "1", "-t", str(END_SECONDS), "-i", "end.png"),
        *("-filter_complex", graph, "-map", "[v]"),
        *("-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart"),
        str(out),
    )
    return out


def gif(timeline: dict, step_key: str = GIF_STEP):
    """10-15 s GIF of one step for the top of the README (captions included, 960 px wide)."""
    steps = timeline["steps"]
    i = next(n for n, s in enumerate(steps) if s["key"] == step_key)
    start = steps[i]["start"] - timeline["trim"] + TITLE_SECONDS
    length = min(max(steps[i + 1]["start"] - steps[i]["start"], 10), 15)
    palette = (
        "fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer"
    )
    ffmpeg("-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(OUT / "demo.mp4"), "-vf", palette, str(GIF))


def web_copy(src: Path, dest: Path):
    """Smaller H.264 copy for the portfolio site (starts playing at once), plus a poster from the title card."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        *("-i", str(src), "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-profile:v", "high"),
        *("-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest)),
    )
    ffmpeg("-ss", "1.5", "-i", str(src), "-frames:v", "1", "-q:v", "3", str(dest.with_suffix(".jpg")))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rebuild", action="store_true", help="reuse the last raw recording")
    parser.add_argument("--web-out", type=Path, help="also write a web copy (and .jpg poster) here")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install it (winget install Gyan.FFmpeg) and open a new terminal.")
    if args.rebuild:
        timeline = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    else:
        _, timeline = record()
    out = build(timeline)
    gif(timeline)
    print(f"saved {out.relative_to(ROOT)} and {GIF.relative_to(ROOT)}")
    if args.web_out:
        web_copy(out, args.web_out.resolve())
        print(f"saved {args.web_out} and its .jpg poster")


if __name__ == "__main__":
    main()
