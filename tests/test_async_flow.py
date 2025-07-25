import os
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_MODULE = "src.api:app"


@pytest.fixture(scope="session")
def api_server():
    """Start uvicorn server in background for tests."""
    env = os.environ.copy()
    env["TEST_MODE"] = "1"  # ensure dummy data

    # Use --no-access-log to keep output clean
    proc = subprocess.Popen([
        "uvicorn",
        API_MODULE,
        "--port",
        "8000",
        "--log-level",
        "warning",
    ], env=env)

    # Wait briefly for server to start
    time.sleep(2)
    yield
    proc.terminate()
    proc.wait()


def test_async_flow(api_server):
    """End-to-end test of async flow using local FastAPI and frontend demo."""
    demo_url = "http://localhost:8000/docs/async_process_demo.html"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(demo_url)

        # Click start button
        start_btn = page.get_by_role("button", name="Starta")
        start_btn.click()

        # Button should be disabled and spinner visible
        page.wait_for_selector(".spinner", timeout=5000)
        assert start_btn.is_disabled()

        # Wait up to 10s for result with dummy loan
        page.wait_for_selector("text=Dummy Loan", timeout=10000)
        result_box = page.locator(".result")
        assert "Dummy Loan" in result_box.inner_text()

        browser.close() 