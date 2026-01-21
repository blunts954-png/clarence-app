
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from urllib.parse import urlparse
import subprocess

# --- CONFIGURATION & LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - APP - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('synapse_ai_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- ENVIRONMENT ---
load_dotenv()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="🧠 Synapse AI: Cockpit", page_icon="🧠", layout="wide")

# --- UTILITIES ---
def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception: return False

# --- UI ---
st.title("🧠 Synapse AI: Mission Control")
st.caption("Manual Mission Execution Cockpit")

with st.sidebar:
    st.header("⚙️ Engine Parameters")
    st.info("The autonomous engine uses proxies from your .env file automatically.")
    
    st.divider()
    st.header("📡 Comms Channel")
    recipient_email_default = os.getenv("RECIPIENT_EMAIL", "")
    recipient_email = st.text_input("Recipient Email", value=recipient_email_default, placeholder="Enter email for mission report")
    
    st.divider()
    st.header("🎯 Craigslist Helper")
    target_city = st.text_input("Target City", value="bakersfield").lower().strip()
    target_job = st.text_input("Job / Niche", placeholder="e.g. Admin")
    platform = st.selectbox("Source", ["Jobs", "Gigs", "For Sale"])
    
    if st.button("🔗 Generate Craigslist URL"):
        if target_city:
            cat = {"Jobs": "jjj", "Gigs": "ggg", "For Sale": "sss"}.get(platform)
            query = f"query={target_job.replace(' ', '+')}" if target_job else ""
            st.session_state['generated_url'] = f"https://{target_city}.craigslist.org/search/{cat}?{query}#search=1~list~0"
        else:
            st.error("City is required.")

st.subheader("🚀 Launch Mission")
default_url = st.session_state.get('generated_url', '')
url_input = st.text_input("Target URL", value=default_url, placeholder="https://...")

col1, col2 = st.columns(2)
with col1:
    pages_to_crawl = st.number_input("Scan Depth (Pages)", min_value=1, value=1)
with col2:
    data_blueprint = st.text_area("Data Blueprint (for AI)", value="Title,Link,Price,Location", height=100)

if st.button("EXECUTE MANUAL SCAN", type="primary"):
    if not url_input.strip() or not validate_url(url_input):
        st.error("⚠️ A valid Target URL is required.")
        st.stop()
    if not recipient_email:
        st.error("⚠️ A Recipient Email is required to receive the report.")
        st.stop()

    mission_cmd = [
        "python3",
        "engine.py",
        url_input,
        "--recipient",
        recipient_email,
        "--pages",
        str(pages_to_crawl),
        "--fields",
        data_blueprint
    ]

    logger.info(f"Initiating manual mission with command: {' '.join(mission_cmd)}")
    status = st.status("🚀 Mission Launched. Engine is running...", expanded=True)

    try:
        # Using subprocess to run the engine in the background.
        # This is a simplified approach. For production, a robust task queue (e.g., Celery, RQ) is recommended.
        process = subprocess.Popen(mission_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Display engine output in real-time
        with st.expander("🤖 Engine Output"):
            stdout_container = st.empty()
            stderr_container = st.empty()
            stdout_log = ""
            stderr_log = ""
            while process.poll() is None:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    stdout_log += stdout_line
                    stdout_container.text(stdout_log)
                
                stderr_line = process.stderr.readline()
                if stderr_line:
                    stderr_log += stderr_line
                    stderr_container.warning(stderr_log)
                time.sleep(0.1)

        if process.returncode == 0:
            status.update(label="✅ Mission Complete. Report sent via email.", state="complete")
            st.success("Engine finished successfully. Check your email for the data.")
            logger.info("Manual mission completed successfully.")
        else:
            status.update(label="❌ Mission Failed.", state="error")
            st.error("Engine encountered an error. Check the logs for details.")
            logger.error(f"Manual mission failed with return code {process.returncode}")

    except Exception as e:
        st.error(f"A critical error occurred while launching the engine: {e}")
        logger.critical(f"Failed to launch engine subprocess: {e}")
