"""Generate realistic, messy demo PDFs into data/raw/ (re-runnable).

  python scripts/make_demo_pdfs.py

Creates:
  beach-resort/restaurant_menu.pdf       multi-page, repeated header/footer, price tables
  mountain-lodge/events_weddings.pdf   policy PDF with deposit/fee rules
  beach-resort/fire_safety_scan.pdf      image-only "scanned" page (no text -> needs OCR)
"""

import io
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
W, H = letter


def header_footer(c, title, page, total):
    c.setFont("Helvetica", 8)
    c.drawString(50, H - 30, "CONFIDENTIAL - INTERNAL STAFF USE ONLY")
    c.drawString(50, 25, f"{title} | Rev. 2026-02 | Page {page} of {total}")


def write_lines(c, lines, y=H - 70):
    for kind, text in lines:
        if kind == "h":
            c.setFont("Helvetica-Bold", 14)
            y -= 8
        elif kind == "row":
            c.setFont("Courier", 10)
        else:
            c.setFont("Helvetica", 10)
        c.drawString(50, y, text)
        y -= 18
    return y


def restaurant_menu():
    title = "Restaurant Menu - Beach Resort"
    pages = [
        [
            ("h", "Main Restaurant - Beach Resort"),
            ("p", "Breakfast 6:30 AM - 10:30 AM. Lunch 12:00 PM - 3:00 PM. Dinner 5:30 PM - 10:00 PM."),
            ("p", "Room service available 6:30 AM - 11:00 PM. $7 delivery fee plus 18% gratuity."),
            ("h", "Breakfast"),
            ("row", "Item                          Price"),
            ("row", "Continental Buffet            $28"),
            ("row", "Full Breakfast Buffet         $38"),
            ("row", "Avocado Toast                 $18"),
            ("row", "Kids Breakfast (under 12)     $14"),
        ],
        [
            ("h", "Dinner"),
            ("row", "Item                          Price"),
            ("row", "Grilled Mahi-Mahi             $36"),
            ("row", "Cuban Pork Shoulder           $32"),
            ("row", "Key Lime Pie                  $12"),
            ("p", "Gluten-free and vegan options are marked on the in-room menu."),
            ("p", "Allergy requests must be passed to the chef by the server. Never guarantee"),
            ("p", "a dish is allergen-free; the kitchen handles nuts and shellfish."),
        ],
        [
            ("h", "Guest Credits"),
            ("p", "Platinum members receive one free breakfast buffet per guest per day."),
            ("p", "Gold members receive 15% off food (not alcohol)."),
            ("p", "Outside food delivery is accepted at the front desk only, not the restaurant."),
        ],
    ]
    path = RAW / "beach-resort" / "restaurant_menu.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    for i, lines in enumerate(pages, 1):
        header_footer(c, title, i, len(pages))
        write_lines(c, lines)
        c.showPage()
    c.save()
    return path


def events_weddings():
    title = "Events & Weddings Policy - Mountain Lodge"
    lines = [
        ("h", "Events & Weddings Policy - Mountain Lodge"),
        ("p", "The garden lawn holds up to 150 guests. The indoor event room holds up to 60."),
        ("p", "A 30% non-refundable deposit is required to confirm any event date."),
        ("p", "Wedding room blocks: minimum 10 rooms, released 30 days before arrival."),
        ("p", "Outdoor amplified music must end by 10:00 PM (county noise rules)."),
        ("p", "Outside caterers allowed with a $15 per person kitchen fee."),
        ("p", "Sparklers and open flames are not permitted. Confetti cleanup fee: $300."),
        ("p", "All event questions go to the Events Manager, never quote prices at the desk."),
    ]
    path = RAW / "mountain-lodge" / "events_weddings.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    header_footer(c, title, 1, 1)
    write_lines(c, lines)
    c.save()
    return path


def scanned_page():
    """Image-only page: text extraction returns nothing, like a real scan."""
    img = Image.new("RGB", (1275, 1650), "white")
    d = ImageDraw.Draw(img)
    text = [
        "FIRE SAFETY PROCEDURE - BEACH RESORT",
        "Assembly point: north side of the main parking lot.",
        "Never use elevators during an alarm.",
    ]
    for i, t in enumerate(text):
        d.text((100, 150 + i * 60), t, fill="black")
    buf = io.BytesIO()
    img.rotate(1.2, fillcolor="white").save(buf, format="PNG")
    buf.seek(0)
    path = RAW / "beach-resort" / "fire_safety_scan.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawImage(ImageReader(buf), 0, 0, W, H)
    c.save()
    return path


if __name__ == "__main__":
    for p in (restaurant_menu(), events_weddings(), scanned_page()):
        print("created", p.relative_to(RAW.parent.parent))
