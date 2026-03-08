import streamlit as st
import requests

# ------------------------------------------------
# 1. STRICT DATABASES (Customize these as needed)
# ------------------------------------------------

# Strict list of clearly Haram or highly doubtful ingredients
HARAM_INGREDIENTS = [
    "pork", "gelatin", "gelatine", "alcohol", "wine", "beer", "liquor", 
    "carmine", "e120", "cochineal", "bacon", "lard", "animal fat", 
    "pepsin", "rennet", "e471", "e472"
]

# Custom blocklist for ethical/personal reasons
# You can add specific brands here that you strictly do not post 
BLOCKED_BRANDS = ["pepsi", "7up", "coca-cola", "starbucks", "nestle"]

# ------------------------------------------------
# 2. CORE FUNCTIONS
# ------------------------------------------------

def fetch_product_data(product_name):
    """Fetches product details from the Open Food Facts API."""
    # We use the UK/World database to find the product
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # If products are found, return the closest match (the first one)
        if data.get("count", 0) > 0:
            return data["products"][0]
        return None
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def analyze_product(product):
    """Checks the product against our strict databases."""
    brand = product.get("brands", "").lower()
    ingredients_text = product.get("ingredients_text", "").lower()
    
    # Check 1: Is it a blocked brand?
    for blocked in BLOCKED_BRANDS:
        if blocked in brand:
            return "REJECTED", f"Brand '{brand.title()}' is on your restricted list."

    # If there are no ingredients listed in the database, we can't be sure
    if not ingredients_text:
        return "DOUBTFUL", "No ingredient list found in the database. Cannot verify."

    # Check 2: Does it contain Haram ingredients?
    found_haram = []
    for haram_item in HARAM_INGREDIENTS:
        if haram_item in ingredients_text:
            found_haram.append(haram_item)
            
    if found_haram:
        return "HARAM", f"Contains strict restricted ingredients: {', '.join(found_haram).title()}"
        
    # If it passes all checks
    return "HALAL / PERMITTED", "No restricted brands or haram ingredients detected in the database."

# ------------------------------------------------
# 3. STREAMLIT UI
# ------------------------------------------------

st.set_page_config(page_title="Strict Product Checker", page_icon="🔍", layout="centered")

st.title("🔍 Strict Product Verifier")
st.markdown("Check product names against Haram ingredients and restricted brands before posting.")

# Input field for the user
product_query = st.text_input("Enter Product Name (e.g., 'Walkers Ready Salted Crisps'):")

if st.button("Check Product", type="primary"):
    if product_query:
        with st.spinner("Searching global database..."):
            product_data = fetch_product_data(product_query)
            
            if product_data:
                # Get the actual name and image from the database to confirm the match
                actual_name = product_data.get("product_name", "Unknown Product Name")
                image_url = product_data.get("image_url", "")
                ingredients = product_data.get("ingredients_text", "Not provided by database.")
                
                st.subheader(f"Found: {actual_name}")
                if image_url:
                    st.image(image_url, width=150)
                
                # Run the strict analysis
                status, reason = analyze_product(product_data)
                
                # Display the verdict with appropriate colors
                if status == "REJECTED" or status == "HARAM":
                    st.error(f"**STATUS: {status}**\n\n{reason}")
                elif status == "DOUBTFUL":
                    st.warning(f"**STATUS: {status}**\n\n{reason}")
                else:
                    st.success(f"**STATUS: {status}**\n\n{reason}")
                
                # Show raw ingredients so you can double-check manually
                with st.expander("View Raw Ingredients List"):
                    st.write(ingredients)
                    
            else:
                st.warning("Product not found in the database. You may need to check this one manually.")
    else:
        st.info("Please enter a product name first.")
