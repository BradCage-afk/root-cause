"""High-resolution, tightly cropped captures for the presentation (2x pixel density).

Start the app first, then:  python scripts/deck_shots.py [URL] [--light]
Writes docs/screenshots/deck-*.jpg. Dark theme by default, to match the deck.
"""
import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
URL = args[0] if args else "http://127.0.0.1:8000"
THEME = "light" if "--light" in sys.argv else "dark"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def save(png: bytes, name: str):
    Image.open(io.BytesIO(png)).convert("RGB").save(OUT / f"deck-{name}.jpg", quality=90)
    print("saved", name)


def region(page, top_sel, bottom_sel=None, max_h=None, pad=10):
    # bring the crop into the viewport, clear of the sticky header
    page.locator(top_sel).first.evaluate("e => { e.scrollIntoView({block:'start'}); window.scrollBy(0,-120) }")
    page.wait_for_timeout(300)
    a = page.locator(top_sel).first.bounding_box()
    b = page.locator(bottom_sel).first.bounding_box() if bottom_sel else a
    y0, y1 = a["y"] - pad, b["y"] + b["height"] + pad
    if max_h:
        y1 = min(y1, y0 + max_h)
    x0 = min(a["x"], b["x"]) - pad
    x1 = max(a["x"] + a["width"], b["x"] + b["width"]) + pad
    return {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}


def task(page, k):
    page.evaluate(f"runTask('{k}')")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=2)
    page.add_init_script(f"try{{localStorage.setItem('rc-theme','{THEME}')}}catch(e){{}}")
    page.goto(URL)
    page.request.post(f"{URL}/api/reset")
    page.reload()
    page.wait_for_selector("#topproblem .tl")
    page.wait_for_timeout(1200)
    save(page.screenshot(), "overview")

    task(page, "drop")
    page.wait_for_selector("#dout .steps")
    page.wait_for_timeout(600)
    save(page.screenshot(clip=region(page, "#dout .card")), "pipeline")

    page.click("nav button[data-p=problems]")
    page.wait_for_selector("#plist .tl")
    page.evaluate("why('CLU-001')")
    page.wait_for_selector("#why-CLU-001 table")
    page.wait_for_timeout(900)
    # keep the section clear of the sticky header before measuring it
    page.evaluate("document.querySelector('#why-CLU-001').scrollIntoView({block:'start'}); window.scrollBy(0,-120)")
    page.wait_for_timeout(500)
    save(page.screenshot(clip=region(page, "#why-CLU-001 h3", "#why-CLU-001 table")), "why")

    task(page, "change")
    page.wait_for_selector("#pout .callout.warn")
    page.wait_for_timeout(500)
    save(page.screenshot(clip=region(page, "#pout > .card")), "preflight")

    task(page, "poison")
    page.wait_for_selector("#banner", state="visible")
    page.wait_for_timeout(600)
    task(page, "block")
    page.wait_for_selector("#pending .callout.bad")
    page.wait_for_timeout(600)
    save(page.screenshot(clip=region(page, "#banner", "#lanes")), "policy")

    page.click("nav button[data-p=audit]")
    task(page, "tamper")
    page.wait_for_selector("#events .event.broken")
    page.wait_for_timeout(600)
    save(page.screenshot(clip=region(page, "#seal", "#events .event.broken")), "audit")

    page.click("nav button[data-p=scale]")
    page.wait_for_selector("#sout .card")
    page.wait_for_timeout(800)
    save(page.screenshot(clip=region(page, "#sout", max_h=720)), "scale")

    page.request.post(f"{URL}/api/reset")
    b.close()
