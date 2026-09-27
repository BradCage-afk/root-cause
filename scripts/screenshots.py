"""Drive the running UI through the demo and save screenshots to docs/screenshots/.

Start the app first (python -m rootcause.app), then:
    pip install playwright && python -m playwright install chromium
    python scripts/screenshots.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name, wait=600):
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    print("saved", name)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
    page.goto(URL)
    page.request.post(f"{URL}/api/reset")
    page.reload()
    page.wait_for_timeout(1500)

    page.fill("#q", "What caused the checkout timeouts in January?")
    page.click("#ask .btn")
    page.wait_for_selector("#ans .tag")
    page.click("#ans .cite >> nth=0")
    shot(page, "01-ask-cited-answer")

    page.click("nav >> text=Live demo controls")
    page.click("text=Drop new incident INC-301")
    page.wait_for_selector("#dout .evi")
    shot(page, "02-live-ingest-links-cluster")

    page.click("nav >> text=Recurrence clusters")
    page.wait_for_selector("#clist .card")
    page.click("text=WHY THIS? >> nth=0")
    page.wait_for_selector("[id^=why-] .card")
    page.evaluate("document.querySelector('[id^=why-] .card').scrollIntoView({block:'start'})")
    shot(page, "03-why-this-evidence")
    page.evaluate("window.scrollTo(0,0)")
    shot(page, "04-recurrence-clusters")

    page.click("nav >> text=Failure debt")
    page.wait_for_selector("#dlist .card")
    shot(page, "05-failure-debt-and-predictions")

    page.click("nav >> text=Pre-flight check")
    page.click("text=Load CHG-88")
    page.wait_for_timeout(400)
    page.click("text=Run pre-flight")
    page.wait_for_selector("#pout .card")
    shot(page, "06-preflight-warning")

    page.click("nav >> text=Live demo controls")
    page.click("text=Drop poisoned postmortem PM-199")
    page.wait_for_selector("#banner", state="visible")
    shot(page, "07-prompt-injection-quarantined", wait=1500)

    page.click("nav >> text=Recurrence clusters")
    page.wait_for_selector("#clist .card")
    page.click("text=Write note to Obsidian vault >> nth=0")
    page.wait_for_selector("#alist .card")
    page.click("text=Propose: email vault to external address")
    page.wait_for_timeout(600)
    shot(page, "08-policy-gate")
    page.click("text=Approve >> nth=0")
    page.wait_for_timeout(600)

    page.click("nav >> text=Audit ledger")
    page.wait_for_selector("#alog table")
    shot(page, "09-audit-chain-intact")
    page.click("text=Tamper with an entry")
    shot(page, "10-audit-tamper-detected", wait=900)

    page.request.post(f"{URL}/api/reset")
    b.close()
