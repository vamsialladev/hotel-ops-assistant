"""Record the narrated, captioned demo video from the LIVE app: real questions, real streamed answers.

python scripts/record_demo.py                       # record + build docs/video/demo.mp4 and docs/images/demo.gif
python scripts/record_demo.py --rebuild             # rebuild from the last recording (no new questions)
python scripts/record_demo.py --no-voice            # captions only, no narration
python scripts/record_demo.py --web-out ../vamsi-portfolio/videos/hotel-ops-demo.mp4   # + web copy, poster, .vtt

Follows docs/DEMO_SCRIPT.md, with a cited answer on screen within the first 10 seconds: the dog question at
both hotels, a property rule overriding a loyalty perk (sources open), a "check with a manager" answer, the
fire assembly point refusal, "Did you mean" recovery, the welcome guidance after New conversation, topic
chips, then the Insights, Document library and How it works pages. Never opens the Admin page and never
shows a setting. Asks 6 real questions (well under $0.01).

Narration: an AI voice from Piper (open source, runs offline, no voice cloning), timed to each step: every
step waits for its line to finish, so the voice never runs ahead of the screen. Mixed to about -16 LUFS,
AAC audio. Also writes docs/video/narration-script.txt (the exact words, to record your own voice) and a
WebVTT captions track. The voice model (about 110 MB) is downloaded once into docs/video/voices/.

Dev-only: needs Playwright, piper-tts (requirements-dev.txt) and ffmpeg on PATH. docs/video/ is git-ignored;
publish the web copy to the portfolio repo instead.
"""

import argparse
import json
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "video"
WORK = OUT / "work"
VOICES = OUT / "voices"
VOICE = "en_US-lessac-high"
GIF = ROOT / "docs" / "images" / "demo.gif"
APP = "https://hotel-ops-assistant.streamlit.app/~/+/"  # the app itself, without Streamlit Cloud's frame
SIZE = (1280, 720)
VIEW = (1280, 640)  # the app; the 80 px band under it holds the captions, so they never cover the UI
FPS = 30
MSG = "[data-testid=stChatMessage]"
GREEN, BRASS, CREAM, INK = "#1E4636", "#94702C", "#F4F1EA", "#FFFFFF"
LINKS = [
    ("Portfolio", "vamsialladev.github.io"),
    ("Live app", "hotel-ops-assistant.streamlit.app"),
    ("GitHub", "github.com/vamsialladev/hotel-ops-assistant"),
]
TITLE_SECONDS = 3
LEAD, GAP = 0.4, 0.35  # narration starts LEAD s into a step; GAP s of silence between lines
SPEED = 1.08  # Piper length scale: slightly slower than its default, easier to follow
GIF_STEP = "beach_dog"  # the GIF is this step: the first cited answer

# What is said (narration) and shown (caption) at each step. Captions are short for muted viewers.
NARRATION = {
    "title": "Hotel Operations Knowledge Assistant: a simulated client project.",
    "beach_dog": "A front-desk agent at Beach Resort asks if a guest can bring their dog. In seconds, a short "
    "answer appears, with the source for every fact.",
    "lodge_dog": "At Mountain Lodge, the same question gets that hotel's own rules. It never mixes up properties, "
    "and related questions are one tap away.",
    "gold": "Here, the loyalty program promises a two p.m. checkout, but this hotel caps weekends at noon. "
    "The assistant applies the hotel's rule and shows the exact text.",
    "manager": "A refund over the front-desk limit gets a check-with-a-manager note, quoting the policy.",
    "refusal": "When the documents don't say, it refuses instead of guessing. A wrong safety answer is worse "
    "than none.",
    "recover": "And instead of a dead end, it suggests close questions it can answer.",
    "new_chat": "Every new conversation starts with guidance: how to use it, what this demo knows, and good "
    "questions to ask.",
    "topics": "Topic chips show example questions for each area, like the spa.",
    "insights": "Managers see what staff ask, how they ask, and which questions point to gaps in the policies.",
    "library": "Every answer comes only from these documents, all synthetic, for a simulated client.",
    "how": "It's measured on fifty-four test questions: ninety-eight percent answer accuracy on this live demo, "
    "at about seventeen cents per thousand questions.",
    "end": "Try the live app, or read the code and the decisions. The links are on screen.",
}
CAPTIONS = {
    "beach_dog": "Ask in plain English. A cited answer in seconds.",
    "lodge_dog": "Mountain Lodge: same question, its own rules.",
    "gold": "The hotel's weekend rule beats the loyalty perk. Sources show the text.",
    "manager": 'Over the refund limit? "Check with a manager", quoting the rule.',
    "refusal": "Not in the documents? It refuses instead of guessing.",
    "recover": "Can't answer? It suggests questions that work.",
    "new_chat": "Every new conversation starts with guidance on what to ask.",
    "topics": "Topic chips show example questions for each policy area.",
    "insights": "Insights: what staff ask, how they ask, and policy gaps.",
    "library": "Answers come only from these synthetic documents.",
    "how": "How it works: 54 test questions, 98% answer accuracy on this live demo.",
}


# ---------------------------------------------------------------- narration
def voice_model() -> Path:
    model = VOICES / f"{VOICE}.onnx"
    if not model.exists():
        VOICES.mkdir(parents=True, exist_ok=True)
        subprocess.run(["python", "-m", "piper.download_voices", VOICE, "--download-dir", str(VOICES)], check=True)
    return model


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def synthesize(lines: dict, folder: Path) -> dict:
    """One WAV per line with Piper (offline). Returns {key: seconds}."""
    from piper import PiperVoice, SynthesisConfig

    voice = PiperVoice.load(str(voice_model()))
    config = SynthesisConfig(length_scale=SPEED)
    folder.mkdir(parents=True, exist_ok=True)
    durations = {}
    for key, text in lines.items():
        path = folder / f"{key}.wav"
        with wave.open(str(path), "wb") as w:
            voice.synthesize_wav(text, w, syn_config=config)
        durations[key] = round(wav_seconds(path), 2)
    return durations


# ---------------------------------------------------------------- recording
class Recorder:
    """Keeps the screen and the narration in step. Times are video seconds (after the title card)."""

    def __init__(self, page, durations: dict):
        self.page, self.t0, self.steps, self.durations = page, time.monotonic(), [], durations
        self.trim = None
        self.cursor = LEAD + durations.get("title", 0) + GAP  # the title line plays over the title card

    def now(self) -> float:
        return round(time.monotonic() - self.t0, 2)

    def video_time(self) -> float:
        return self.now() - self.trim + TITLE_SECONDS

    def step(self, key: str):
        start = self.video_time()
        audio = max(start + LEAD, self.cursor)
        self.cursor = audio + self.durations.get(key, 0) + GAP
        self.steps.append({"key": key, "caption": CAPTIONS[key], "start": self.now(), "audio": round(audio, 2)})

    def settle(self, at_least: float):
        """Pause at least this long, and until this step's narration has finished."""
        self.pause(at_least)
        while self.video_time() < self.cursor - GAP:
            self.page.wait_for_timeout(100)

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
    page.locator("[data-testid=stMain] [data-testid=stButtonGroup] button", has_text=prop).first.click()
    page.wait_for_timeout(1500)


def to_bottom(page):
    """Scroll the chat to the bottom, so Streamlit keeps following the streaming answer."""
    page.mouse.move(800, 300)
    for _ in range(10):
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(30)


def wait_for_answer(page, before: int):
    """Wait until the reply is complete (its status line or suggestions appear only then)."""
    page.wait_for_function(f"document.querySelectorAll('{MSG}').length >= {before + 2}", timeout=90_000)
    answer = page.locator(MSG).nth(before + 1)
    answer.locator(".hoa-status, [data-testid=stButton]").first.wait_for(timeout=90_000)
    page.wait_for_timeout(400)
    answer.evaluate("el => el.scrollIntoView({block: 'end', behavior: 'smooth'})")  # the whole answer in view
    page.wait_for_timeout(600)
    return answer


def click_question(page, text: str):
    before = page.locator(MSG).count()
    page.locator("[data-testid=stMain]").get_by_role("button", name=text).first.click()
    to_bottom(page)
    return wait_for_answer(page, before)


def type_question(page, text: str):
    before = page.locator(MSG).count()
    to_bottom(page)
    box = page.locator("[data-testid=stChatInputTextArea]")
    box.click()
    box.press_sequentially(text, delay=40)  # a natural typing speed
    page.wait_for_timeout(300)
    box.press("Enter")
    return wait_for_answer(page, before)


def open_page(page, title: str):
    page.locator("[data-testid=stSidebarNav] a", has_text=title).first.click()
    page.wait_for_selector(f"h1.hoa-title:has-text('{title}')", timeout=60_000)
    page.wait_for_timeout(1000)


def record(durations: dict) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": VIEW[0], "height": VIEW[1]},
            record_video_dir=str(WORK),
            record_video_size={"width": VIEW[0], "height": VIEW[1]},
            color_scheme="light",
        )
        page = ctx.new_page()
        r = Recorder(page, durations)
        page.goto(APP, timeout=180_000)
        ready(page)
        pick(page, "Beach Resort")
        r.trim = r.now()

        r.step("beach_dog")  # the first cited answer, within 10 seconds of the start
        click_question(page, "Can a guest bring their dog?")
        r.settle(3)

        r.step("lodge_dog")
        pick(page, "Mountain Lodge")
        click_question(page, "Can a guest bring their dog?")
        r.settle(3)

        r.step("gold")
        pick(page, "Beach Resort")
        answer = type_question(page, "A Gold member wants late checkout on Saturday. How late can they stay?")
        answer.get_by_text("Sources", exact=True).first.click()
        page.wait_for_timeout(700)
        r.scroll(300)
        r.settle(3)

        r.step("manager")
        type_question(page, "Can I give a guest a $300 refund myself?")
        r.settle(3)

        r.step("refusal")
        type_question(page, "Where is the fire assembly point?")
        r.settle(3)

        r.step("recover")
        type_question(page, "Can you book me a room for Friday?")
        r.settle(3)

        r.step("new_chat")
        page.locator("[data-testid=stSidebar] button", has_text="New conversation").first.click()
        r.settle(4)

        r.step("topics")
        page.locator("[data-testid=stMain] [data-testid=stButtonGroup] button", has_text="Spa").first.click()
        r.settle(3)

        r.step("insights")
        open_page(page, "Insights")
        r.pause(2)
        r.scroll(600, 20)
        r.settle(2)

        r.step("library")
        open_page(page, "Document library")
        r.pause(1.5)
        r.scroll(400)
        r.settle(2)

        r.step("how")
        open_page(page, "How it works")
        r.settle(4)
        end = r.now()

        video = page.video
        ctx.close()  # finishes writing the video file
        raw = Path(video.path())
        browser.close()
    raw.rename(WORK / "raw.webm")
    timeline = {"trim": r.trim, "end": end, "steps": r.steps, "durations": durations, "end_audio": None}
    (WORK / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return timeline


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


def end_card(path: Path, narrated: bool = True):
    img = Image.new("RGB", SIZE, GREEN)
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE[1] - 14, SIZE[0], SIZE[1]], fill=BRASS)
    centered(d, 150, "Try it, read the code, see the decisions", font("georgiab.ttf", 46), INK)
    label_font, link_font = font("arialbd.ttf", 26), font("arial.ttf", 32)
    for i, (label, url) in enumerate(LINKS):
        y = 260 + i * 90
        centered(d, y, label.upper(), label_font, "#E8D9B5")
        centered(d, y + 34, url, link_font, INK)
    if narrated:
        centered(d, 600, "Narration: AI voice (Piper, open source)", font("arial.ttf", 22), CREAM)
    img.save(path)


def ass_time(seconds: float) -> str:
    seconds = max(seconds, 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def vtt_time(seconds: float) -> str:
    seconds = max(seconds, 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


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


def narration_cues(timeline: dict) -> list[tuple[float, float, str]]:
    """(start, end, text) for every spoken line, in video time, split into sentences (timed by length)."""
    durations = timeline["durations"]
    lines = [(LEAD, "title")] + [(s["audio"], s["key"]) for s in timeline["steps"]]
    if timeline.get("end_audio") is not None:
        lines.append((timeline["end_audio"], "end"))
    cues = []
    for start, key in lines:
        text, length = NARRATION[key], durations.get(key, 0)
        sentences = [s for s in re.split(r"(?<=[.:?!])\s+(?=[A-Z])", text) if s]  # not after "p.m. checkout"
        total, t = sum(len(s) for s in sentences), start
        for s in sentences:
            span = length * len(s) / total
            cues.append((round(t, 2), round(t + span, 2), s))
            t += span
    return cues


def webvtt(cues) -> str:
    return "WEBVTT\n\n" + "\n".join(f"{vtt_time(a)} --> {vtt_time(b)}\n{text}\n" for a, b, text in cues)


def script_text(cues) -> str:
    out = [
        "Hotel Operations Knowledge Assistant: demo narration (exact words, with start times in the video).",
        "Read these lines over docs/video/demo.mp4 to record your own voice version.",
        "",
    ]
    out += [f"[{int(a // 60)}:{a % 60:04.1f}] {text}" for a, _, text in cues]
    return "\n".join(out) + "\n"


def ffmpeg(*args: str):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True, cwd=WORK)


def mix_narration(timeline: dict, total: float) -> Path:
    """Place each line at its time, then normalise loudness to about -16 LUFS (true peak -1.5 dB), AAC."""
    clips = [("title", LEAD)] + [(s["key"], s["audio"]) for s in timeline["steps"]] + [("end", timeline["end_audio"])]
    inputs, chains = [], []
    for i, (key, at) in enumerate(clips):
        inputs += ["-i", f"voice/{key}.wav"]
        ms = int(at * 1000)
        chains.append(f"[{i}:a]adelay={ms}|{ms},aresample=48000[a{i}]")
    graph = ";".join(chains) + ";" + "".join(f"[a{i}]" for i in range(len(clips)))
    graph += f"amix=inputs={len(clips)}:normalize=0,apad=whole_dur={total:.2f},loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    ffmpeg(
        *inputs,
        "-filter_complex",
        graph,
        "-map",
        "[out]",
        "-t",
        f"{total:.2f}",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-ar",
        "48000",
        "narration.m4a",
    )
    return WORK / "narration.m4a"


def build(timeline: dict, voice: bool) -> Path:
    length = timeline["end"] - timeline["trim"]
    durations = timeline["durations"]
    end_audio = TITLE_SECONDS + length + LEAD if voice else None
    end_seconds = max(6.0, (durations.get("end", 0) + LEAD + 1.2) if voice else 6.0)
    timeline["end_audio"] = end_audio
    total = TITLE_SECONDS + length + end_seconds
    title_card(WORK / "title.png")
    end_card(WORK / "end.png", narrated=voice)
    (WORK / "captions.ass").write_text(captions(timeline, TITLE_SECONDS), encoding="utf-8")
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
    audio = ["-i", str(mix_narration(timeline, total)), "-map", "3:a", "-c:a", "copy"] if voice else []
    ffmpeg(
        *("-loop", "1", "-t", str(TITLE_SECONDS), "-i", "title.png"),
        *("-ss", f"{timeline['trim']:.2f}", "-t", f"{length:.2f}", "-i", "raw.webm"),
        *("-loop", "1", "-t", f"{end_seconds:.2f}", "-i", "end.png"),
        *audio[:2],
        *("-filter_complex", graph, "-map", "[v]"),
        *audio[2:],
        *("-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart"),
        *("-t", f"{total:.2f}"),
        str(out),
    )
    if voice:
        cues = narration_cues(timeline)
        (OUT / "demo.vtt").write_text(webvtt(cues), encoding="utf-8")
        (OUT / "narration-script.txt").write_text(script_text(cues), encoding="utf-8")
    (WORK / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return out


def gif(timeline: dict, step_key: str = GIF_STEP):
    """10-15 s GIF of one step for the top of the README (captions included, 960 px wide, no sound)."""
    steps = timeline["steps"]
    i = next(n for n, s in enumerate(steps) if s["key"] == step_key)
    start = steps[i]["start"] - timeline["trim"] + TITLE_SECONDS
    length = min(max(steps[i + 1]["start"] - steps[i]["start"], 10), 15)
    palette = (
        "fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer"
    )
    ffmpeg("-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(OUT / "demo.mp4"), "-vf", palette, str(GIF))


def web_copy(src: Path, dest: Path):
    """Smaller H.264 + AAC copy for the portfolio site (starts playing at once), a poster from the title card,
    and the narration captions track."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        *("-i", str(src), "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-profile:v", "high"),
        *("-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest)),
    )
    ffmpeg("-ss", "1.5", "-i", str(src), "-frames:v", "1", "-q:v", "3", str(dest.with_suffix(".jpg")))
    if (OUT / "demo.vtt").exists():
        shutil.copy(OUT / "demo.vtt", dest.with_suffix(".vtt"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rebuild", action="store_true", help="reuse the last recording and narration")
    parser.add_argument("--no-voice", action="store_true", help="captions only, no narration")
    parser.add_argument("--web-out", type=Path, help="also write a web copy (+ .jpg poster and .vtt) here")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install it (winget install Gyan.FFmpeg) and open a new terminal.")
    voice = not args.no_voice
    if args.rebuild:
        timeline = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    else:
        shutil.rmtree(WORK, ignore_errors=True)
        WORK.mkdir(parents=True)
        durations = synthesize(NARRATION, WORK / "voice") if voice else {}
        timeline = record(durations)
    out = build(timeline, voice)
    gif(timeline)
    print(f"saved {out.relative_to(ROOT)} and {GIF.relative_to(ROOT)}")
    if args.web_out:
        web_copy(out, args.web_out.resolve())
        print(f"saved {args.web_out} with its .jpg poster and .vtt captions")


if __name__ == "__main__":
    main()
