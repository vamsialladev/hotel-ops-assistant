"""The demo recorder's caption timing (pure functions; nothing is recorded and no API is called)."""

import importlib.util
from pathlib import Path

import pytest

from src.config import ROOT

pytest.importorskip("PIL")  # dev-only dependency of the script
spec = importlib.util.spec_from_file_location("record_demo", ROOT / "scripts" / "record_demo.py")
record_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(record_demo)

TIMELINE = {
    "trim": 6.0,
    "end": 40.0,
    "steps": [
        {"key": "welcome", "caption": "First caption", "start": 6.0},
        {"key": "beach_dog", "caption": "Second, with a comma", "start": 11.5},
        {"key": "how", "caption": "Last caption", "start": 30.0},
    ],
}


def test_ass_time_format():
    assert record_demo.ass_time(0) == "0:00:00.00"
    assert record_demo.ass_time(75.256) == "0:01:15.26"
    assert record_demo.ass_time(-1) == "0:00:00.00"


def test_captions_follow_the_steps_after_the_title_card():
    events = [line for line in record_demo.captions(TIMELINE, 3).splitlines() if line.startswith("Dialogue:")]
    assert len(events) == 3
    # recording time 6.0 is the trimmed start, so the first caption starts right after the 3 s title card
    assert events[0].startswith("Dialogue: 0,0:00:03.00,0:00:08.45,Cap,,0,0,0,,First caption")
    assert events[1].endswith(",Second, with a comma")  # text is the last field, so commas are safe
    assert ",0:00:27.00,0:00:36.95," in events[2]  # the last caption runs to the end of the recording


def test_cards_are_full_size_and_links_point_to_the_public_pages(tmp_path):
    record_demo.title_card(tmp_path / "title.png")
    record_demo.end_card(tmp_path / "end.png")
    from PIL import Image

    assert Image.open(tmp_path / "title.png").size == record_demo.SIZE == (1280, 720)
    assert Image.open(tmp_path / "end.png").size == (1280, 720)
    assert [url for _, url in record_demo.LINKS] == [
        "vamsialla.com",
        "hotel-ops-assistant.streamlit.app",
        "github.com/vamsialladev/hotel-ops-assistant",
    ]
    assert "/admin" not in record_demo.APP


def test_caption_cues_match_the_burned_in_captions():
    cues = record_demo.caption_cues(TIMELINE, 3)
    assert [text for _, _, text in cues] == ["First caption", "Second, with a comma", "Last caption"]
    assert cues[0] == (3.0, 8.45, "First caption")  # same times as the ASS captions
    assert cues[-1][1] == 36.95  # the last cue runs to the end of the recording


def test_webvtt():
    cues = [(0.4, 2.5, "Hello."), (65.0, 67.25, "Second line.")]
    vtt = record_demo.webvtt(cues)
    assert vtt.startswith("WEBVTT\n\n00:00:00.400 --> 00:00:02.500 line:6% position:50% align:center\nHello.")
    assert "00:01:05.000 --> 00:01:07.250 line:6% position:50% align:center\nSecond line." in vtt


def test_no_ai_voice_and_every_caption_fits_one_line():
    assert not hasattr(record_demo, "NARRATION") and not hasattr(record_demo, "synthesize")
    assert "Piper" not in Path(record_demo.__file__).read_text(encoding="utf-8")
    assert all(len(c) <= 75 for c in record_demo.CAPTIONS.values())  # one line in the caption band
