import streamlit as st
import extra_streamlit_components as stx
import requests
import re
import time
import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime


# ==========================================
# 1. CONFIGURATION & PAGE SETUP
# ==========================================
st.set_page_config(
    page_title="USA Deals Filter",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a "Gorgeous" Look
st.markdown("""
    <style>
    .stTextArea textarea {
        font-family: 'Consolas', monospace;
        background-color: #f0f2f6;
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
    "Junaid": "bargainsbasket4-20"
    
}

# ==========================================
# 2. COOKIE MANAGER (Persistence Logic)
# ==========================================
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
    
    # Updated headers based on the new Edge/Chromium curl request
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://creators.posttap.com",
        "priority": "u=1, i",
        "referer": "https://creators.posttap.com/",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
        # Updated cookies
        "cookie": "_ga=GA1.1.202930833.1751362584; curatedby-prime-day=true; btn_hide_help=true; cb-collections-launch-modal=true; _ga_0J5KXPW971=GS2.1.s1759930983$o19$g0$t1759930984$j59$l0$h0; intercom-device-id-esdk9pud=9c3d0119-e327-499a-aa0a-1cb9905c5957; user_notify_geolocation_opt_in=true; btn_logged_in=1; btn_logged_in.sig=Nssey5VTPZtPL4tY0GmKCSWryyI; btn_session=cff6840c-f9f6-4a0d-af92-6b3391ef69d9; btn_session.sig=B_qOI4i4wPEUHvpB8sK3R-cZcPM; intercom-session-esdk9pud=UGJrcHA0N2JQYjlieXVPVTIxdG9wMTlFaExYRDF1ckJuaG1WeFdBL3RRYXJxem53N2ZSUVRNRGQ0Um5sTy94Q1VJaHVUdmEwY3NYcjJBQUgwelpDMDJ1NTh3bXJIdm1BenNFZ3N4aFFJcUZBVTVRVWh1NFBGckNEWWZ0YnFYSWhyTjRuWVFOUyszbEVLVjRkQ0l1emh6RmxEL1pvRUxhelZiNHJLbjVBQWZsY0hiRnpyRm85ajhjTTVBaUFvZElxM1JUVFVqRG1ZSFhjYzJnTGN1czltQT09LS16N3Nhb0dXWTJDNDAwWVdVYzVPTWN3PT0=--c6e514137b37533165494377fb3a8c7bae949cf6"
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
        status_container.update(label=f"Processing Line {i+1}/{total_lines}...", state="running")
        
        if any(phrase in line for phrase in exclude_phrases):
            continue 
            
        urls = url_pattern.findall(line)
        for original_url in urls:
            redirected_url = get_redirected_url(original_url)
            if redirected_url:
                cleaned_url = clean_amazon_url(redirected_url)
                parsed_url = urlparse(cleaned_url)
                
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

# --- NEW: AI GENERATOR LOGIC ---
# --- NEW: AI GENERATOR LOGIC (DIRECT API - BULLETPROOF) ---
# --- NEW: AI GENERATOR LOGIC (DIRECT API - BULLETPROOF) ---
# --- NEW: AI GENERATOR LOGIC (DIRECT API - BULLETPROOF) ---
# --- NEW: AI GENERATOR LOGIC (GROQ API - STREAMLIT SAFE) ---
def generate_ai_taglines(raw_text, api_key):
    # Direct Groq API URL (Bypasses Google's regional blocks)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    mega_prompt = f"""
    You are a high-energy, FOMO-inducing Facebook Deal Group Admin in the UK. 
    Your ONLY job is to take the raw deal data below and generate exactly 3 highly engaging Facebook posts.
    
    STRICT RULES (DO NOT CROSS THESE LIMITS):
    1. NEVER FORGET PRICE AND LINK: You absolutely MUST extract the exact Price and the Link from the raw data and put them in your output. If you drop the link, you fail.
    2. EXACT LENGTH: The text tagline MUST be between 10 to 20 words. Do NOT write just 3 words, and do NOT write paragraphs. 
    3. VIBE: High panic, UK influencer energy, lots of emojis (😱🔥‼️🏃‍♀️💨).
    4. BANNED WORDS: Sale, Clearance, Discount, Amazon.
    
    MANDATORY OUTPUT STRUCTURE (Copy this exactly for all 3 options):
    [10-20 Word Hype Tagline with Emojis]
    [Exact Price Extracted]
    Ad 👉 [Exact Link Extracted]
    
    HERE ARE YOUR BENCHMARK EXAMPLES FOR VIBE AND LENGTH:
    "OMG OMG OMG!!! THIS IS AN OOPSIE FOR SURE!!! 😱😱🔥🔥‼️‼️"
    "UNDER £8 for a 360° looping race track?! This WILL sell out 🏁💥"
    "SO CHEAPPPP, you might end up buying one for every ROOM! 🤑😜😂😂"
    "This CAN’T be right!! Hurry before they change itttt!! 🤯💨‼️"
    "£40.98 !!? This HAS to be an oopsie!! RUN before they fix itttt!! 🤯💨"

    RAW DEAL DATA TO PROCESS:
    {raw_text}
    """
    
    # Payload for Groq (Using the ultra-smart Llama 3 model)
    data = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "user", "content": mega_prompt}],
        "temperature": 0.7
    }
    
    # Send request using basic requests library
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"AI API Error: {response.status_code} - {response.text}")

# ==========================================
# 4. APP LAYOUT
# ==========================================

st.title("🚀 Amazon Deal Manager Pro")
st.markdown("Automated redirection, cleaning, tagging, and short-linking.")
st.divider()

# --- SIDEBAR (Settings & Cookie Loading) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    time.sleep(0.1)
    
    saved_group = cookie_manager.get(cookie="target_group")
    
    group_keys = list(GROUPS.keys())
    default_index = 0
    
    if saved_group in group_keys:
        default_index = group_keys.index(saved_group)
    
    selected_group_name = st.selectbox(
        "Select Target Group:", 
        group_keys, 
        index=default_index
    )
    
    if selected_group_name != saved_group:
        cookie_manager.set("target_group", selected_group_name)
    
    active_tag = GROUPS[selected_group_name]
    
    st.success(f"**Active Tag:** `{active_tag}`")
    st.info("ℹ️ Your group selection is saved automatically.")

# ==========================================
# TABS SETUP
# ==========================================
tab1, tab2 = st.tabs(["🔗 1. Standard Link Converter", "🤖 2. AI Tagline Generator (Stealth)"])

# ------------------------------------------
# TAB 1: YOUR ORIGINAL APP LOGIC
# ------------------------------------------
with tab1:
    col_input, col_output = st.columns(2)

    with col_input:
        st.subheader("📥 Paste Raw Deals")
        input_text = st.text_area(
            "Paste text here:", 
            height=400, 
            placeholder="Paste your raw Facebook/WhatsApp deals here...",
            key="tab1_input"
        )
        
        process_btn = st.button("✨ Convert Deals", type="primary", use_container_width=True)

    with col_output:
        st.subheader("📤 Output Result")
        output_container = st.empty()

    if process_btn and input_text:
        with st.status("🚀 Processing deals...", expanded=True) as status:
            try:
                result_text = run_processing(input_text, active_tag, status)
                status.update(label="✅ Processing Complete!", state="complete", expanded=False)
                
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

# ------------------------------------------
# TAB 2: NEW AI TAGLINE GENERATOR
# ------------------------------------------
with tab2:
    st.info("🕒 **Best Posting Times Advisor:** Target 1:00 PM - 3:00 PM or 8:00 AM on Wed/Thu/Sat for max reach.")
    
    # API KEY IS NOW HARDCODED HERE
    MY_SECRET_API_KEY = "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"
    
    col_ai_in, col_ai_out = st.columns(2)
    
    with col_ai_in:
        st.subheader("📥 Deal Information")
        st.caption("Paste price, link, and any random text. AI will figure it out.")
        ai_input_text = st.text_area(
            "Raw Deal Snippet:", 
            height=250, 
            placeholder="£11.85\nAd 👉🏼 https://amzlink.to/az0CgnMFgoeGH", 
            key="tab2_input"
        )
        ai_process_btn = st.button("🧠 Generate Viral Taglines", type="primary", use_container_width=True)
        
    with col_ai_out:
        st.subheader("📤 Output Variations")
        
    if ai_process_btn:
        if not MY_SECRET_API_KEY:
            st.error("⚠️ Developer Error: Please put your actual API Key in the code first!")
        elif not ai_input_text:
            st.warning("⚠️ Please paste the deal info first.")
        else:
            with st.spinner("🧠 Consulting the Andromeda Algorithm..."):
                try:
                    ai_result = generate_ai_taglines(ai_input_text, MY_SECRET_API_KEY)
                    with col_ai_out:
                        st.success("Variations Generated! Choose one:")
                        st.markdown(ai_result)
                        st.code(ai_result, language="text")
                except Exception as e:
                    st.error(f"AI Generation Error: {e}")
