"""High-resolution, tightly cropped captures for the presentation (2x pixel density).

Start the app first, then:  python scripts/deck_shots.py
Writes docs/screenshots/deck-*.jpg
"""
import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def save(png: bytes, name: str):
    Image.open(io.BytesIO(png)).convert("RGB").save(OUT / f"deck-{name}.jpg", quality=90)
    print("saved", name)


def region(page, top_sel, bottom_sel=None, max_h=None, pad=10):
    a = page.locator(top_sel).first.bounding_box()
    b = page.locator(bottom_sel).first.bounding_box() if bottom_sel else a
    y0, y1 = a["y"] - pad, b["y"] + b["height"] + pad
    if max_h:
        y1 = min(y1, y0 + max_h)
    x0 = min(a["x"], b["x"]) - pad
    x1 = max(a["x"] + a["width"], b["x"] + b["width"]) + pad
    return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
    page.goto(URL)
    page.request.post(f"{URL}/api/reset")
    page.reload()
    page.wait_for_selector("#topcl .tl")
    page.wait_for_timeout(1200)
    save(page.screenshot(), "overview")

    page.click("nav >> text=Live demo controls")
    page.click("text=Drop a new incident")
    page.wait_for_selector("#dout .pipe")
    page.wait_for_timeout(600)
    save(page.screenshot(clip=region(page, "#dout .card")), "pipeline")

    page.click("nav >> text=Recurrence clusters")
    page.wait_for_selector("#clist .tl")
    page.click("text=WHY THIS? >> nth=0")
    page.wait_for_selector("[id^=why-] table")
    page.wait_for_timeout(900)
    # keep the card clear of the sticky header before measuring it
    page.evaluate("document.querySelector('[id^=why-] .card').scrollIntoView({block:'start'}); window.scrollBy(0,-120)")
    page.wait_for_timeout(500)
    save(page.screenshot(clip=region(page, "[id^=why-] .card", "[id^=why-] table")), "why")

    page.click("nav >> text=Pre-flight check")
    page.click("text=Load example")
    page.wait_for_timeout(300)
    page.click("text=Run pre-flight")
    page.wait_for_selector("#pout .c-amb")
    page.wait_for_timeout(500)
    save(page.screenshot(clip=region(page, "#pout > .card")), "preflight")

    page.click("nav >> text=Live demo controls")
    page.click("text=Drop a poisoned postmortem")
    page.wait_for_selector("#banner", state="visible")
    page.wait_for_timeout(800)
    page.click("nav >> text=Actions & policy")
    page.wait_for_selector("#lanes .lane")
    page.click("text=Try: email the vault")
    page.wait_for_timeout(700)
    save(page.screenshot(clip=region(page, "#banner", "#lanes")), "policy")

    page.click("nav >> text=Audit ledger")
    page.wait_for_selector("#alog .blk")
    page.click("text=Tamper with an entry")
    page.wait_for_selector("#alog .blk.broken")
    page.wait_for_timeout(600)
    save(page.screenshot(clip=region(page, "#vstat", "#alog .blk >> nth=3")), "audit")

    page.request.post(f"{URL}/api/reset")
    b.close()
