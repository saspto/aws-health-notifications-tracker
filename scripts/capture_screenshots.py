#!/usr/bin/env python3
"""Capture screenshots of the live CloudFront app."""
import os
import urllib.parse
from playwright.sync_api import sync_playwright

APP_URL = "https://d2vuz8nfxuvkbe.cloudfront.net"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_screens")
os.makedirs(OUT_DIR, exist_ok=True)

# Known Critical/High event with llmProcessed=true for the detail screenshot
DETAIL_ARN     = "arn:aws:health:us-east-1::event/RDS/AWS_RDS_SECURITY_BULLETIN/0001"
DETAIL_ACCOUNT = "222222222222"

def save(page, name: str, wait_ms: int = 2500):
    page.wait_for_timeout(wait_ms)
    path = os.path.join(OUT_DIR, name)
    page.screenshot(path=path, full_page=True)
    print(f"  saved {name}")

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 01 — Dashboard
    print("01_dashboard.png")
    page.goto(f"{APP_URL}/", wait_until="networkidle")
    save(page, "01_dashboard.png", 3000)

    # 02 — Notifications list (all events)
    print("02_notification_list.png")
    page.goto(f"{APP_URL}/notifications", wait_until="networkidle")
    save(page, "02_notification_list.png", 3000)

    # 03 — Filtered to Critical
    print("03_notification_list_filtered.png")
    page.goto(f"{APP_URL}/notifications", wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.select_option("select:nth-of-type(2)", "Critical")
    save(page, "03_notification_list_filtered.png", 2000)

    # 04 — Event detail (navigate directly to known event URL)
    print("04_notification_detail.png")
    detail_url = (
        f"{APP_URL}/notifications"
        f"/{urllib.parse.quote(DETAIL_ARN, safe='')}"
        f"/{urllib.parse.quote(DETAIL_ACCOUNT, safe='')}"
    )
    page.goto(detail_url, wait_until="networkidle")
    save(page, "04_notification_detail.png", 3000)

    browser.close()
    print("Done.")
