import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
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
from typing import List, Dict, Optional, Tuple
import hashlib
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clarence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Validate critical environment variables
if not openai.api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    st.error("⚠️ Configuration Error: OPENAI_API_KEY not set. Please configure environment variables.")

# --- CONFIGURATION ---
st.set_page_config(page_title="Clarence 7.0: The Supervisor Pro", page_icon="👨‍✈️", layout="wide")

# --- SECURITY & VALIDATION UTILITIES ---
def validate_url(url: str) -> bool:
    """Validate URL format and security."""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception as e:
        logger.error(f"URL validation failed: {e}")
        return False

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    # Remove potential dangerous characters
    sanitized = re.sub(r'[<>\"\'%;()&+]', '', text)
    return sanitized[:max_length].strip()

# --- PROXY UTILS ---
def get_local_proxy() -> Optional[str]:
    """Retrieve a random proxy from local file with error handling."""
    try:
        file_path = "proxyscrape_premium_http_proxies.txt"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("[")]
            if proxies:
                selected_proxy = random.choice(proxies)
                logger.info(f"Selected proxy from pool: {selected_proxy[:20]}...")
                return selected_proxy
        else:
            logger.warning(f"Proxy file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading proxy file: {e}")
    return None

def create_proxy_auth_extension(proxy_string: str) -> Optional[str]:
    """Create Chrome extension for authenticated proxy with proper error handling."""
    try:
        if "@" not in proxy_string:
            logger.warning("Proxy string does not contain authentication")
            return None

        auth, host_port = proxy_string.split("@", 1)
        if ":" not in auth or ":" not in host_port:
            logger.error("Invalid proxy format")
            return None

        user, password = auth.split(":", 1)
        host, port = host_port.split(":", 1)

        # Validate port number
        try:
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                raise ValueError("Invalid port range")
        except ValueError as e:
            logger.error(f"Invalid port number: {port} - {e}")
            return None

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

        # Escape special characters to prevent injection
        escaped_user = user.replace("\\", "\\\\").replace('"', '\\"')
        escaped_password = password.replace("\\", "\\\\").replace('"', '\\"')

        background_js = f"""
        var config = {{ mode: "fixed_servers", rules: {{ singleProxy: {{ scheme: "http", host: "{host}", port: parseInt({port}) }}, bypassList: ["localhost"] }} }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        function callbackFn(details) {{ return {{ authCredentials: {{ username: "{escaped_user}", password: "{escaped_password}" }} }}; }}
        chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ['blocking']);
        """

        plugin_file = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        logger.info(f"Created proxy extension for {host}:{port}")
        return os.path.abspath(plugin_file)

    except Exception as e:
        logger.error(f"Failed to create proxy extension: {e}")
        return None

# --- STEALTH ENGINE ---
def setup_selenium(proxy_strategy: str, manual_string: Optional[str] = None) -> webdriver.Chrome:
    """
    Setup Selenium WebDriver with advanced stealth features and error handling.

    Args:
        proxy_strategy: Proxy mode selection
        manual_string: Manual proxy string if applicable

    Returns:
        Configured Chrome WebDriver instance

    Raises:
        WebDriverException: If driver setup fails
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Updated headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")

        # Enhanced anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 2  # Disable images for faster loading
        })

        # Expanded User Agent pool
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        selected_ua = random.choice(ua_list)
        chrome_options.add_argument(f"user-agent={selected_ua}")
        logger.info(f"Using User-Agent: {selected_ua[:50]}...")

        # Proxy configuration with validation
        active_proxy = None
        if proxy_strategy == "Paste Proxy String" and manual_string:
            active_proxy = manual_string.strip()
        elif proxy_strategy == "Rotate from Local File":
            active_proxy = get_local_proxy()

        if active_proxy:
            logger.info(f"Configuring proxy: {active_proxy[:30]}...")
            if "@" in active_proxy:
                plugin = create_proxy_auth_extension(active_proxy)
                if plugin:
                    chrome_options.add_extension(plugin)
                else:
                    logger.warning("Failed to create proxy extension, proceeding without proxy")
            else:
                chrome_options.add_argument(f'--proxy-server={active_proxy}')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)

        # Additional stealth JavaScript
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": selected_ua})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        logger.info("WebDriver initialized successfully")
        return driver

    except Exception as e:
        logger.error(f"Failed to setup Selenium: {e}")
        raise WebDriverException(f"WebDriver initialization failed: {e}")

# --- THE FOREMAN (SUPERVISOR LOGIC) ---
def smart_scroll(driver, status_box, max_scrolls: int = 20) -> int:
    """
    Advanced scroll mechanism to load all lazy-loaded content.

    Args:
        driver: Selenium WebDriver instance
        status_box: Streamlit status container
        max_scrolls: Maximum scroll iterations to prevent infinite loops

    Returns:
        Number of items detected on page
    """
    status_box.write("👨‍✈️ Foreman: 'Initializing Advanced Scroll Protocol...'")
    logger.info("Starting smart scroll sequence")

    scroll_pause_time = 1.5
    scroll_increment = 500
    last_height = driver.execute_script("return document.body.scrollHeight")
    items_detected = 0

    for scroll_attempt in range(max_scrolls):
        # Gradual scroll in smaller increments
        current_position = driver.execute_script("return window.pageYOffset")
        new_position = current_position + scroll_increment

        driver.execute_script(f"window.scrollTo(0, {new_position});")
        time.sleep(scroll_pause_time)

        # Check for new content every few scrolls
        if scroll_attempt % 3 == 0:
            new_height = driver.execute_script("return document.body.scrollHeight")

            # Count items (Craigslist specific)
            try:
                items = driver.find_elements(By.CSS_SELECTOR, "li.cl-static-search-result, li.result-row")
                items_detected = len(items)
                logger.info(f"Scroll {scroll_attempt + 1}: Detected {items_detected} items")
            except Exception as e:
                logger.warning(f"Could not count items during scroll: {e}")

            if new_height > last_height:
                status_box.write(f"👨‍✈️ Foreman: '{items_detected} items loaded, continuing scan...'")
                last_height = new_height
            else:
                # Scroll to absolute bottom to ensure everything loads
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Final count
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, "li.cl-static-search-result, li.result-row")
                    items_detected = len(items)
                except:
                    pass

                status_box.write(f"👨‍✈️ Foreman: 'Scan complete. {items_detected} items detected. Proceeding to extraction.'")
                logger.info(f"Smart scroll completed with {items_detected} items")
                return items_detected

    status_box.write(f"👨‍✈️ Foreman: 'Max scroll reached. {items_detected} items detected.'")
    logger.warning(f"Max scroll iterations reached: {items_detected} items")
    return items_detected

# --- DIRECT HTML EXTRACTION (More Reliable than AI) ---
def extract_craigslist_items(driver, status_box) -> List[Dict]:
    """
    Direct HTML extraction for Craigslist - more reliable and faster than AI.
    Extracts ALL items with previews.

    Returns:
        List of dictionaries containing item data
    """
    status_box.write("🔍 Analyst: 'Initiating direct extraction protocol...'")
    logger.info("Starting direct HTML extraction")

    items_data = []

    try:
        # Try modern Craigslist structure first
        items = driver.find_elements(By.CSS_SELECTOR, "li.cl-static-search-result")

        if not items:
            # Fallback to older structure
            items = driver.find_elements(By.CSS_SELECTOR, "li.result-row")
            logger.info("Using legacy Craigslist structure")

        logger.info(f"Found {len(items)} items to extract")
        status_box.write(f"🔍 Analyst: 'Processing {len(items)} items with preview extraction...'")

        for idx, item in enumerate(items, 1):
            try:
                data = {}

                # Extract Title
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, "a.main, div.title a")
                    data['Title'] = title_elem.text.strip()
                    data['Link'] = title_elem.get_attribute('href')
                except:
                    data['Title'] = "N/A"
                    data['Link'] = "N/A"

                # Extract Price/Pay
                try:
                    price_elem = item.find_element(By.CSS_SELECTOR, "span.priceinfo, span.price, div.price")
                    data['Price'] = price_elem.text.strip()
                except:
                    data['Price'] = "N/A"

                # Extract Location
                try:
                    location_elem = item.find_element(By.CSS_SELECTOR, "span.location, div.location")
                    data['Location'] = location_elem.text.strip()
                except:
                    data['Location'] = "N/A"

                # Extract Date/Time
                try:
                    date_elem = item.find_element(By.CSS_SELECTOR, "div.meta time, time")
                    data['Posted'] = date_elem.get_attribute('datetime') or date_elem.text.strip()
                except:
                    data['Posted'] = "N/A"

                # Extract Preview Image - CRITICAL FIX
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, "img")
                    img_url = img_elem.get_attribute('src')

                    # Handle lazy-loaded images
                    if not img_url or 'data:image' in img_url:
                        img_url = img_elem.get_attribute('data-src') or img_elem.get_attribute('data-lazy')

                    data['Preview_Image'] = img_url if img_url else "No Image"
                except:
                    data['Preview_Image'] = "No Image"

                # Extract Description/Meta
                try:
                    desc_elem = item.find_element(By.CSS_SELECTOR, "div.meta, span.meta")
                    data['Description'] = desc_elem.text.strip()
                except:
                    data['Description'] = "N/A"

                items_data.append(data)

                if idx % 20 == 0:
                    logger.info(f"Processed {idx}/{len(items)} items")

            except Exception as e:
                logger.warning(f"Failed to extract item {idx}: {e}")
                continue

        status_box.write(f"✅ Analyst: 'Successfully extracted {len(items_data)} items with previews!'")
        logger.info(f"Extraction complete: {len(items_data)} items")

        return items_data

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        status_box.write(f"❌ Analyst: 'Extraction error: {str(e)}'")
        return []


def clean_html_smart(html: str) -> str:
    """Clean and prepare HTML content for processing."""
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "noscript", "meta", "iframe", "svg"]):
            tag.decompose()

        # Process links
        for a in soup.find_all('a', href=True):
            if a.get_text(strip=True):
                a.string = f" {a.get_text(strip=True)} (Link: {a['href']}) "

        # Extract and normalize text
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)

        return text

    except Exception as e:
        logger.error(f"HTML cleaning failed: {e}")
        return ""


def universal_extract_ai(text_content: str, fields_list: str) -> List[Dict]:
    """
    AI-powered extraction (fallback method for non-Craigslist sites).

    Args:
        text_content: Cleaned HTML text
        fields_list: Comma-separated list of fields to extract

    Returns:
        List of extracted items
    """
    if not openai.api_key:
        logger.error("OpenAI API key not configured")
        return [{"Error": "API key not configured"}]

    # Increase limit to handle more content
    truncated_text = text_content[:250000]

    prompt = f"""
    You are an advanced data extraction engine. Extract ALL items from this listing page.

    Target Fields: {fields_list}

    CRITICAL INSTRUCTIONS:
    1. Extract EVERY SINGLE item - do not limit results
    2. Look for repeated structural patterns
    3. Extract the specified fields for EACH item
    4. Look for links in format "(Link: url)" and extract them
    5. Look for image URLs and extract them as "Preview_Image"
    6. If a field is missing, use "N/A"
    7. Return ONLY valid JSON in this exact format: {{"items": [{{field1: value1, field2: value2}}, ...]}}

    Text Content:
    {truncated_text}
    """

    try:
        logger.info("Initiating AI extraction")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precision data extraction engine. Extract ALL items without limiting the count."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=16000  # Increased to handle more items
        )

        result = json.loads(response.choices[0].message.content)
        items = result.get("items", [])

        logger.info(f"AI extracted {len(items)} items")
        return items

    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return [{"Error": f"AI extraction failed: {str(e)}"}]

# --- UI ---
st.title("👨‍✈️ Clarence 7.0: The Supervisor Pro")
st.caption("Production-Grade Web Scraping Engine | All Items + Previews")

with st.sidebar:
    st.header("⚙️ Stealth Ops")
    proxy_mode = st.radio("Proxy Strategy", 
                         ["No Proxy (Fastest)", 
                          "Rotate from Local File", 
                          "Paste Proxy String"])
    
    manual_proxy = ""
    if proxy_mode == "Rotate from Local File":
        st.info("Reading 'proxyscrape_premium_http_proxies.txt'")
    elif proxy_mode == "Paste Proxy String":
        manual_proxy = st.text_input("Proxy String", placeholder="user:pass@ip:port")
    
    st.divider()
    
    st.header("🕵️ Lead Detective Pro")
    target_city = st.text_input("Target City", value="bakersfield").lower().strip()
    target_job = st.text_input("Job / Niche", placeholder="e.g. Admin")
    platform = st.selectbox("Source", ["Craigslist Jobs", "Craigslist Gigs", "Craigslist For Sale"])
    
    if st.button("📍 Lock Target"):
        if not target_city:
            st.error("City required.")
        else:
            if "Jobs" in platform: cat_code = "jjj"
            elif "Gigs" in platform: cat_code = "ggg"
            else: cat_code = "sss"
            
            # FORCE LIST VIEW
            fragment = "#search=1~list~0"
            base_url = f"https://{target_city}.craigslist.org/search/{cat_code}"
            
            if target_job:
                clean_job = target_job.replace(" ", "+")
                gen_url = f"{base_url}?query={clean_job}{fragment}"
            else:
                gen_url = f"{base_url}{fragment}"
            
            st.session_state['generated_url'] = gen_url
            st.success(f"Target Locked: {target_city.upper()}")

st.subheader("Mission Console")
default_url = st.session_state.get('generated_url', '')
url_input = st.text_input("Target URL", value=default_url, placeholder="https://...")

col1, col2 = st.columns(2)
with col1:
    data_blueprint = st.text_area("Data Blueprint", value="Title, Price/Pay, Email, Link", height=100)
with col2:
    pages_to_crawl = st.number_input("Scan Depth", min_value=1, value=1)

if st.button("🚀 Execute Extraction", type="primary"):
    # Validate input
    if not url_input.strip():
        st.error("⚠️ URL cannot be empty")
        st.stop()

    if not validate_url(url_input):
        st.error("⚠️ Invalid URL format. Must start with http:// or https://")
        st.stop()

    logger.info(f"Starting extraction for URL: {url_input}")
    status = st.status("🚀 Deploying Production Scraper...", expanded=True)

    driver = None
    all_items = []

    try:
        # Initialize WebDriver
        status.write("🔧 Initializing stealth browser...")
        driver = setup_selenium(proxy_mode, manual_proxy)

        current_url = url_input
        is_craigslist = "craigslist" in current_url.lower()

        for page_num in range(pages_to_crawl):
            status.write(f"📡 Scanning Page {page_num + 1} of {pages_to_crawl}...")
            logger.info(f"Processing page {page_num + 1}: {current_url}")

            try:
                driver.get(current_url)
                time.sleep(2)  # Allow initial load

                # Execute smart scroll
                items_detected = smart_scroll(driver, status)

                # Choose extraction method
                if is_craigslist:
                    status.write("🎯 Using direct Craigslist extraction (Fast & Accurate)...")
                    items = extract_craigslist_items(driver, status)
                else:
                    status.write("🤖 Using AI-powered universal extraction...")
                    clean_text = clean_html_smart(driver.page_source)
                    items = universal_extract_ai(clean_text, data_blueprint)

                # Validate extraction
                if not items:
                    status.warning(f"⚠️ No items extracted from page {page_num + 1}")
                    logger.warning(f"No items found on page {page_num + 1}")
                elif len(items) < 10 and is_craigslist and items_detected > 20:
                    status.warning(f"⚠️ Low extraction count ({len(items)} items) despite {items_detected} detected. Possible parsing issue.")
                    logger.warning(f"Extraction mismatch: {len(items)} extracted vs {items_detected} detected")

                if items:
                    all_items.extend(items)
                    status.write(f"✅ Extracted {len(items)} items (Total: {len(all_items)})")
                    logger.info(f"Page {page_num + 1}: {len(items)} items extracted")

                # Handle pagination
                if page_num < pages_to_crawl - 1:
                    status.write("🔄 Navigating to next page...")

                    try:
                        # Try clicking "next" button
                        next_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "next"))
                        )
                        next_btn.click()
                        time.sleep(3)
                        current_url = driver.current_url
                        logger.info(f"Navigated to next page: {current_url}")

                    except TimeoutException:
                        # Fallback: Manual pagination for Craigslist
                        if is_craigslist:
                            offset = (page_num + 1) * 120
                            if "#" in url_input:
                                base, frag = url_input.split("#", 1)
                                sep = "&" if "?" in base else "?"
                                current_url = f"{base}{sep}s={offset}#{frag}"
                            else:
                                sep = "&" if "?" in url_input else "?"
                                current_url = f"{url_input}{sep}s={offset}"
                            logger.info(f"Manual pagination: {current_url}")
                        else:
                            status.warning("No 'next' button found. Stopping pagination.")
                            logger.warning("Pagination ended: no next button")
                            break

            except TimeoutException as e:
                logger.error(f"Page load timeout on page {page_num + 1}: {e}")
                status.warning(f"⏱️ Page {page_num + 1} timed out. Skipping...")
                continue

            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {e}")
                status.warning(f"⚠️ Error on page {page_num + 1}: {str(e)[:100]}")
                continue

        # Display results
        status.update(label=f"✅ Mission Complete - {len(all_items)} Items Extracted", state="complete")

        if all_items:
            logger.info(f"Extraction successful: {len(all_items)} total items")

            # Create DataFrame
            df = pd.DataFrame(all_items)

            # Display with image previews if available
            st.success(f"🎉 Successfully extracted {len(all_items)} items with full data!")

            if 'Preview_Image' in df.columns:
                st.info("📸 Preview images included in dataset")

            # Show data table
            st.dataframe(df, use_container_width=True)

            # Download options
            col_a, col_b = st.columns(2)
            with col_a:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"clarence_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            with col_b:
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📦 Download JSON",
                    data=json_data,
                    file_name=f"clarence_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            # Summary stats
            with st.expander("📊 Extraction Summary"):
                st.write(f"**Total Items:** {len(all_items)}")
                st.write(f"**Columns:** {', '.join(df.columns)}")
                st.write(f"**Pages Scanned:** {pages_to_crawl}")

                if 'Preview_Image' in df.columns:
                    images_count = df[df['Preview_Image'] != "No Image"].shape[0]
                    st.write(f"**Items with Images:** {images_count}/{len(all_items)}")

        else:
            st.error("❌ No data extracted. Please check the URL and try again.")
            logger.error("Extraction failed: no items found")

    except WebDriverException as e:
        error_msg = f"Browser Error: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        status.update(label="❌ Browser Error", state="error")

    except Exception as e:
        error_msg = f"Critical Error: {str(e)}"
        logger.exception(error_msg)
        st.error(f"❌ {error_msg}")
        status.update(label="❌ Extraction Failed", state="error")

    finally:
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")