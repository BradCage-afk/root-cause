"""Drive the running UI through the guided demo and save screenshots to docs/screenshots/.

Start the app first (python -m rootcause.app), then:
    pip install playwright && python -m playwright install chromium
    python scripts/screenshots.py [URL] [--dark]
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
URL = args[0] if args else "http://127.0.0.1:8000"
THEME = "dark" if "--dark" in sys.argv else "light"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name, wait=700):
    page.wait_for_timeout(wait)
    page.evaluate("document.querySelectorAll('.toast').forEach(t => t.remove())")
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    print("saved", name)


def nav(page, p):
    page.click(f"nav button[data-p={p}]")
    page.wait_for_timeout(400)


def task(page, k):
    page.evaluate(f"runTask('{k}')")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
    page.add_init_script(f"try{{localStorage.setItem('rc-theme','{THEME}')}}catch(e){{}}")
    page.goto(URL)
    page.request.post(f"{URL}/api/reset")
    page.reload()
    page.wait_for_selector("#topproblem .tl")
    shot(page, "00-overview", wait=1000)

    task(page, "ask")
    page.wait_for_selector("#ans .cite")
    page.click("#ans .cite >> nth=0")
    shot(page, "01-ask-cited-answer")

    page.fill("#q", "How many gears does a tractor have?")
    page.click("#askbtn")
    page.wait_for_selector("#ans .callout.info")
    shot(page, "01b-ask-not-in-records")

    task(page, "drop")
    page.wait_for_selector("#dout .steps")
    shot(page, "02-new-incident-linked")

    nav(page, "problems")
    page.wait_for_selector("#plist .tl")
    shot(page, "04-recurring-problems")
    page.evaluate("why('CLU-001')")
    page.wait_for_selector("#why-CLU-001 table")
    page.wait_for_timeout(900)
    page.evaluate("document.querySelector('#why-CLU-001').scrollIntoView({block:'start'}); window.scrollBy(0,-110)")
    shot(page, "03-why-linked")

    nav(page, "debt")
    page.wait_for_selector("#dlist .card")
    shot(page, "05-failure-debt")

    task(page, "change")
    page.wait_for_selector("#pout .callout.warn")
    shot(page, "06-check-a-change")

    task(page, "poison")
    page.wait_for_selector("#banner", state="visible")
    shot(page, "07-hidden-instructions-blocked", wait=1200)

    task(page, "block")
    page.wait_for_selector("#pending .callout.bad")
    shot(page, "08-policy-blocks-external-send")
    task(page, "approve")
    page.wait_for_selector("#pending .btn.good")
    page.click("#pending .btn.good >> nth=0")
    page.wait_for_timeout(700)

    nav(page, "audit")
    page.wait_for_selector("#events .event")
    shot(page, "09-audit-intact")
    task(page, "tamper")
    page.wait_for_selector("#events .event.broken")
    shot(page, "10-audit-tamper-detected")

    nav(page, "scale")
    page.wait_for_selector("#sout .card")
    shot(page, "11-scale-test", wait=900)

    nav(page, "demo")
    shot(page, "12-guided-demo")

    page.request.post(f"{URL}/api/reset")
    b.close()
