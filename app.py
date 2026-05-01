import streamlit as st
import extra_streamlit_components as stx
import requests
import re
import time
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & PAGE SETUP
# ==========================================
st.set_page_config(
    page_title="Amazon Deal Manager Pro",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a "Gorgeous" Look
st.markdown("""
    <style>
    .stTextArea textarea {
        font-family: 'Consolas', monospace;
        background-color: #black;
        border-radius: 10px;
    }
    .stButton button {
        border-radius: 8px;
        font-weight: bold;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Define Groups and IDs
GROUPS = {
    "Taha": "coolestbarg0c-20",
    "Junaid": "bargainsbasket4-20",
    "Waseeq": "wsq-wshlist-20"
}

# ==========================================
# 2. COOKIE MANAGER (Persistence Logic)
# ==========================================
# FIXED: Removed @st.cache_resource to fix the Widget Warning
cookie_manager = stx.CookieManager()

# ==========================================
# 3. CORE LOGIC (Redirects, Cleaning, API)
# ==========================================

def get_redirected_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.head(url, allow_redirects=True, headers=headers, timeout=10)
        return response.url 
    except requests.exceptions.RequestException:
        return None

def clean_amazon_url(url):
    # CHANGED: "amazon.co.uk" has been replaced with "amazon.com"
    if "amazon.com" in url and "/ref=" in url:
        return url.split("/ref=")[0]
    return url

def add_affiliate_tag(url, tag):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params["tag"] = tag
    updated_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=updated_query))

def create_shortlink(url):
    api_url = "https://creators.posttap.com/api/create-shortlink"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "accept-encoding": "gzip, deflate, br, zstd",
        "content-type": "application/json",
        "origin": "https://creators.posttap.com",
        "referer": "https://creators.posttap.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "connection": "keep-alive",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0",
        "priority": "u=0",
        "te": "trailers",
        # Updated cookies from the new Firefox cURL command
        "cookie": "btn_session=5fa6f7fa-b1bb-44b2-a151-b97dd0e49b90; btn_session.sig=BIvYiatwxm1t5N2es8gifFmTWSw; btn_logged_in=1; btn_logged_in.sig=Nssey5VTPZtPL4tY0GmKCSWryyI; intercom-session-esdk9pud=UmxHUldTMjIxaEdNTjJqdVdxS3hBcUR6elRuazF2bHM0Q1pqRllReVdOZkVOMzhFYmtYSFNrN3lJMmp5QXl2WG03OTR5dExOMUFyUnpmMG5xVjZwdE9aYkhScWlPOE9yUWRvRmlJZ0ZIOVZ0NGNKbURRUWZvM1Q0aHFybkNiQ1dlS1JrWXYwdzFYQmlGUEdQVGI0RjM5bFlBWFdNcFdJRG5ndDBGK1VCUU9xNEk1V2dYTmRBODJsemltUHJpaG1mQVFzdlR0b3JaMWowK040dkViRUw3UT09LS0vVFVIN1QyQXlHVmovOGVmWkJwMXJBPT0=--99055abe279c3513577b33382d7809bab8ce8f14; intercom-device-id-esdk9pud=10859c86-edb2-4f22-82e3-5df70d013e4c; btn_profile_reminder=1777596804154"
    }
    data = {
        "name": f"AmazonLink {datetime.now()}",
        "url": url,
        "tags": []
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=15)
        if response.status_code == 201:
            return response.json().get('object', {}).get('shortlink')
        return url 
    except requests.RequestException:
        return url

def run_processing(raw_text, selected_tag, status_container):
    exclude_phrases = ["GET THESE DEALS FEED", "Top Deals", "Huge Bargains", "Huge Bargains UK", "Thrifty Deals", "Price Glitches"]
    lines = raw_text.split('\n')
    updated_content_lines = []
    url_pattern = re.compile(r'(https?://\S+)')
    
    total_lines = len(lines)
    
    for i, line in enumerate(lines):
        # UI Update: Update status
        status_container.update(label=f"Processing Line {i+1}/{total_lines}...", state="running")
        
        if any(phrase in line for phrase in exclude_phrases):
            continue 
            
        urls = url_pattern.findall(line)
        for original_url in urls:
            redirected_url = get_redirected_url(original_url)
            if redirected_url:
                cleaned_url = clean_amazon_url(redirected_url)
                parsed_url = urlparse(cleaned_url)
                
                # Fix Typos
                path_segments = parsed_url.path.split('/')
                updated_path_segments = [seg for seg in path_segments if seg != 'prhoduct']
                updated_path = '/'.join(updated_path_segments)
                
                temp_url = urlunparse(parsed_url._replace(path=updated_path, query=''))
                tagged_url = add_affiliate_tag(temp_url, selected_tag)
                final_shortlink = create_shortlink(tagged_url)
                line = line.replace(original_url, final_shortlink)
        
        updated_content_lines.append(line)

    final_string = '\n'.join(updated_content_lines)
    final_string = final_string.replace("#ad", "\n#ad")
    return final_string

# ==========================================
# 4. APP LAYOUT
# ==========================================

st.title("🚀 Amazon Deal Manager Pro")
st.markdown("Automated redirection, cleaning, tagging, and short-linking.")
st.divider()

# --- SIDEBAR (Settings & Cookie Loading) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. READ COOKIE
    # Small delay to ensure cookies load smoothly on refresh
    time.sleep(0.1)
    
    saved_group = cookie_manager.get(cookie="target_group")
    
    # Determine default index
    group_keys = list(GROUPS.keys())
    default_index = 0
    
    if saved_group in group_keys:
        default_index = group_keys.index(saved_group)
    
    # 2. SELECT BOX
    selected_group_name = st.selectbox(
        "Select Target Group:", 
        group_keys, 
        index=default_index
    )
    
    # 3. SAVE COOKIE IF CHANGED
    if selected_group_name != saved_group:
        cookie_manager.set("target_group", selected_group_name)
        # We don't rerun immediately to avoid flickering, but it saves for next reload
    
    active_tag = GROUPS[selected_group_name]
    
    st.success(f"**Active Tag:** `{active_tag}`")
    st.info("ℹ️ Your group selection is saved automatically.")

# --- MAIN AREA ---
col_input, col_output = st.columns(2)

with col_input:
    st.subheader("📥 Paste Raw Deals")
    input_text = st.text_area(
        "Paste text here:", 
        height=400, 
        placeholder="Paste your raw Facebook/WhatsApp deals here..."
    )
    
    process_btn = st.button("✨ Convert Deals", type="primary", use_container_width=True)

with col_output:
    st.subheader("📤 Output Result")
    # Placeholder for output
    output_container = st.empty()

# --- ACTION LOGIC ---
if process_btn and input_text:
    # Use st.status for a gorgeous progress indicator
    with st.status("🚀 Processing deals...", expanded=True) as status:
        try:
            result_text = run_processing(input_text, active_tag, status)
            status.update(label="✅ Processing Complete!", state="complete", expanded=False)
            
            # Display Result
            with col_output:
                st.balloons()
                st.success("Deals converted successfully!")
                st.code(result_text, language="text")
                st.caption("Click the copy button in the top right of the code block above.")
                
        except Exception as e:
            status.update(label="❌ Error Occurred", state="error")
            st.error(f"Details: {e}")

elif process_btn and not input_text:
    st.warning("⚠️ Please paste some text in the input box first.")
