#!/usr/bin/env python3
"""Capture screenshots of the live CloudFront app."""
import os
import time
from playwright.sync_api import sync_playwright

APP_URL = "https://d2vuz8nfxuvkbe.cloudfront.net"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_screens")
os.makedirs(OUT_DIR, exist_ok=True)

def screenshot(page, name: str, wait_ms: int = 2000):
    page.wait_for_timeout(wait_ms)
    path = os.path.join(OUT_DIR, name)
    page.screenshot(path=path, full_page=True)
    print(f"  saved {name}")

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    print("01_dashboard.png")
    page.goto(f"{APP_URL}/", wait_until="networkidle")
    screenshot(page, "01_dashboard.png", 3000)

    print("02_notification_list.png")
    page.goto(f"{APP_URL}/notifications", wait_until="networkidle")
    screenshot(page, "02_notification_list.png", 3000)

    print("03_notification_list_filtered.png")
    page.goto(f"{APP_URL}/notifications", wait_until="networkidle")
    page.wait_for_timeout(2000)
    # select Critical urgency
    page.select_option("select:nth-of-type(2)", "Critical")
    screenshot(page, "03_notification_list_filtered.png", 2000)

    print("04_notification_detail.png")
    page.goto(f"{APP_URL}/notifications", wait_until="networkidle")
    page.wait_for_timeout(2500)
    rows = page.locator("table tbody tr")
    if rows.count() > 0:
        rows.first.click()
        page.wait_for_timeout(2500)
        screenshot(page, "04_notification_detail.png", 1000)
    else:
        page.screenshot(path=os.path.join(OUT_DIR, "04_notification_detail.png"))

    browser.close()
    print("Done.")
