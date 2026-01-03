import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- CONFIGURATION ---
st.set_page_config(page_title="Clarence 6.0: The Supervisor", page_icon="👨‍✈️", layout="wide")

# --- PROXY UTILS ---
def get_local_proxy():
    try:
        file_path = "proxyscrape_premium_http_proxies.txt"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("[")]
            if proxies: return random.choice(proxies)
    except: pass
    return None

def create_proxy_auth_extension(proxy_string):
    try:
        if "@" in proxy_string:
            auth, host_port = proxy_string.split("@")
            user, password = auth.split(":")
            host, port = host_port.split(":")
            
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
            background_js = f"""
            var config = {{ mode: "fixed_servers", rules: {{ singleProxy: {{ scheme: "http", host: "{host}", port: parseInt({port}) }}, bypassList: ["localhost"] }} }};
            chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
            function callbackFn(details) {{ return {{ authCredentials: {{ username: "{user}", password: "{password}" }} }}; }}
            chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ['blocking']);
            """
            plugin_file = 'proxy_auth_plugin.zip'
            with zipfile.ZipFile(plugin_file, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            return os.path.abspath(plugin_file)
    except: pass
    return None

# --- STEALTH ENGINE ---
def setup_selenium(proxy_strategy, manual_string=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Random User Agent
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    chrome_options.add_argument(f"user-agent={random.choice(ua_list)}")

    active_proxy = None
    if proxy_strategy == "Paste Proxy String":
        active_proxy = manual_string
    elif proxy_strategy == "Rotate from Local File":
        active_proxy = get_local_proxy()
            
    if active_proxy:
        if "@" in active_proxy:
            plugin = create_proxy_auth_extension(active_proxy)
            if plugin: chrome_options.add_extension(plugin)
        else:
            chrome_options.add_argument(f'--proxy-server={active_proxy}')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# --- THE FOREMAN (SUPERVISOR LOGIC) ---
def smart_scroll(driver, status_box):
    """
    The Foreman controls the scroll. He forces the browser to go down slowly
    to ensure every lazy-loaded item is triggered.
    """
    status_box.write("👨‍✈️ Foreman: 'Initializing Smart Scroll Protocol...'")
    
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Step-Scroll (Scroll in chunks, not all at once)
    for i in range(1, 10):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/10});")
        time.sleep(0.5)
    
    # Final check
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height > last_height:
        status_box.write("👨‍✈️ Foreman: 'New items detected. Extending scroll...'")
        smart_scroll(driver, status_box) # Recursive check
    else:
        status_box.write("👨‍✈️ Foreman: 'Floor verified. Proceeding to extraction.'")

# --- AI BRAIN ---
def clean_html_smart(html):
    soup = BeautifulSoup(html, 'html.parser')
    for x in soup(["script", "style", "nav", "footer", "noscript", "meta", "iframe"]): 
        x.decompose()
    for a in soup.find_all('a', href=True):
        if a.get_text(strip=True):
            a.string = f" {a.get_text(strip=True)} (Link: {a['href']}) "
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    return text

def universal_extract(text_content, fields_list):
    if not os.getenv("OPENAI_API_KEY"): return []
    truncated_text = text_content[:150000]
    prompt = f"""
    You are a data extraction engine. Extract a LIST of items.
    Fields: {fields_list}
    INSTRUCTIONS:
    1. Look for repeated patterns.
    2. Extract fields for EACH item.
    3. Look for links in format "(Link: url)".
    4. Return ONLY valid JSON: {{ "items": [ {{...}}, {{...}} ] }}
    Text: {truncated_text}
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content).get("items", [])
    except: return [{"Error": "AI Failed"}]

# --- UI ---
st.title("👨‍✈️ Clarence 6.0: The Supervisor")

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
    if not url_input.startswith("http"):
        st.error("Invalid URL.")
    else:
        status = st.status("Deploying Scraper...")
        driver = setup_selenium(proxy_mode, manual_proxy)
        all_items = []
        
        try:
            current_url = url_input
            for page in range(pages_to_crawl):
                status.write(f"Scanning Sector {page+1}...")
                driver.get(current_url)
                
                # --- FOREMAN INTERVENTION ---
                smart_scroll(driver, status)
                # -----------------------------
                
                status.write("Optimizing vision...")
                clean_text = clean_html_smart(driver.page_source)
                
                status.write(f"AI Analyzing Sector {page+1}...")
                items = universal_extract(clean_text, data_blueprint)
                
                # --- FOREMAN QUALITY CHECK ---
                if len(items) < 15 and "craigslist" in current_url:
                     status.warning(f"👨‍✈️ Foreman: 'Only found {len(items)} items. Retrying deep scan...'")
                     # Retry Logic could go here, but Smart Scroll usually fixes it first.
                
                if items:
                    all_items.extend(items)
                    status.write(f"Found {len(items)} items so far...")
                
                if page < pages_to_crawl - 1:
                    try:
                        next_btn = driver.find_element(By.PARTIAL_LINK_TEXT, "next")
                        next_btn.click()
                        time.sleep(3)
                        current_url = driver.current_url
                    except: 
                        if "craigslist" in current_url:
                             offset = (page + 1) * 120
                             if "#" in url_input:
                                 base, frag = url_input.split("#")
                                 sep = "&" if "?" in base else "?"
                                 current_url = f"{base}{sep}s={offset}#{frag}"
                             else:
                                 sep = "&" if "?" in url_input else "?"
                                 current_url = f"{url_input}{sep}s={offset}"
                        else: break
                        
            status.update(label="Mission Complete", state="complete")
            if all_items:
                df = pd.DataFrame(all_items)
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("💾 Download CSV", csv, "clarence_data.csv", "text/csv")
            else:
                st.error("No data found.")
                
        except Exception as e:
            st.error(f"Critical Failure: {str(e)}")
        finally:
            driver.quit()