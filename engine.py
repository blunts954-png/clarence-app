
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import json
import zipfile
import random
import re
import requests
from dotenv import load_dotenv
import openai
import logging
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
from urllib.parse import urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import argparse

# --- CONFIGURATION & LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ENGINE - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('synapse_ai_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- ENVIRONMENT & API KEYS ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --- CORE FUNCTIONS ---

def send_email_notification(recipient_email: str, subject: str, body: str, data_df: Optional[pd.DataFrame] = None, filename: str = "extraction_data.csv"):
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, recipient_email]):
        logger.warning("Email configuration is incomplete. Skipping notification.")
        return

    logger.info(f"Preparing email notification for {recipient_email}")
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    if data_df is not None and not data_df.empty:
        try:
            csv_data = data_df.to_csv(index=False).encode('utf-8')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(csv_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
            logger.info(f"Attached {filename} to email.")
        except Exception as e:
            logger.error(f"Failed to attach CSV to email: {e}")

    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info("Email notification sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

def get_proxies_from_env() -> List[str]:
    proxy_list_str = os.getenv("PROXY_LIST")
    if not proxy_list_str:
        return []
    return [proxy.strip() for proxy in proxy_list_str.split(',') if proxy.strip()]

def create_proxy_auth_extension(proxy_string: str) -> Optional[str]:
    try:
        auth, host_port = proxy_string.split("@", 1)
        user, password = auth.split(":", 1)
        host, port = host_port.split(":", 1)
        
        plugin_file = f'proxy_auth_plugin_{hashlib.md5(proxy_string.encode()).hexdigest()}.zip'
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": ["proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"],
            "background": {"scripts": ["background.js"]},
            "minimum_chrome_version": "22.0.0"
        }
        """
        background_js = f'''
        var config = {{ mode: "fixed_servers", rules: {{ singleProxy: {{ scheme: "http", host: "{host}", port: parseInt({port}) }}, bypassList: ["localhost"] }} }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        function callbackFn(details) {{ return {{ authCredentials: {{ username: "{user}", password: "{password}" }} }}; }}
        chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ['blocking']);
        '''
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        return plugin_file
    except Exception as e:
        logger.error(f"Failed to create proxy extension: {e}")
        return None

def setup_selenium(proxy_list: List[str]) -> webdriver.Chrome:
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        ua_list = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"]
        selected_ua = random.choice(ua_list)
        chrome_options.add_argument(f"user-agent={selected_ua}")

        if proxy_list:
            active_proxy = random.choice(proxy_list)
            logger.info(f"Using proxy: {active_proxy[:30]}...")
            if "@" in active_proxy:
                plugin = create_proxy_auth_extension(active_proxy)
                if plugin:
                    chrome_options.add_extension(plugin)
            else:
                chrome_options.add_argument(f'--proxy-server={active_proxy}')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Selenium: {e}")
        raise WebDriverException(f"WebDriver initialization failed: {e}")

def extract_craigslist_items(driver) -> List[Dict]:
    # This is a simplified version for the engine.
    # The full version from app.py should be used if more detail is needed.
    items_data = []
    items = driver.find_elements(By.CSS_SELECTOR, "li.cl-static-search-result, li.result-row")
    for item in items:
        try:
            title_elem = item.find_element(By.CSS_SELECTOR, "a.main, div.title a")
            data = {
                'Title': title_elem.text.strip(),
                'Link': title_elem.get_attribute('href')
            }
            items_data.append(data)
        except Exception:
            continue
    return items_data


def run_mission(url: str, is_craigslist: bool, data_blueprint: str, pages: int) -> pd.DataFrame:
    logger.info(f"Starting mission for URL: {url}")
    proxy_list = get_proxies_from_env()
    driver = None
    all_items = []

    try:
        driver = setup_selenium(proxy_list)
        current_url = url
        for page_num in range(pages):
            logger.info(f"Scanning Page {page_num + 1}/{pages}...")
            driver.get(current_url)
            time.sleep(3) # Wait for page load

            if is_craigslist:
                items = extract_craigslist_items(driver)
                all_items.extend(items)

            # Placeholder for AI extraction and pagination logic
            # This would need to be filled in to match app.py for full functionality

        if all_items:
            return pd.DataFrame(all_items)
        else:
            return pd.DataFrame()

    finally:
        if driver:
            driver.quit()
            # Clean up proxy plugin files
            for item in os.listdir('.'):
                if item.startswith("proxy_auth_plugin_") and item.endswith(".zip"):
                    os.remove(item)

def main():
    parser = argparse.ArgumentParser(description="Synapse AI Autonomous Engine")
    parser.add_argument("url", help="The target URL to scan.")
    parser.add_argument("--recipient", required=True, help="Email address to send the report to.")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to scan.")
    parser.add_argument("--fields", default="Title,Link", help="Data blueprint for AI extraction.")
    args = parser.parse_args()

    logger.info(f"AUTONOMOUS MISSION START: URL={args.url}, Recipient={args.recipient}")

    is_craigslist = "craigslist.org" in args.url.lower()

    try:
        results_df = run_mission(args.url, is_craigslist, args.fields, args.pages)

        if not results_df.empty:
            logger.info(f"Mission complete. Extracted {len(results_df)} items.")
            email_subject = f"Synapse AI Report: {len(results_df)} Items from {args.url}"
            email_body = f"<p>Autonomous mission completed.</p><p><b>Target:</b> {args.url}</p><p><b>Assets Acquired:</b> {len(results_df)}</p>"
            send_email_notification(args.recipient, email_subject, email_body, results_df)
        else:
            logger.warning("Mission completed with no items extracted.")
            # Optionally send an email even if no results
            # send_email_notification(args.recipient, f"Synapse AI Report: No Items Found for {args.url}", "...")
    
    except Exception as e:
        logger.critical(f"A critical error occurred during the autonomous mission: {e}")
        # Optionally send an error email
        # send_email_notification(args.recipient, f"Synapse AI Mission FAILED for {args.url}", f"Error: {e}")

if __name__ == "__main__":
    main()
