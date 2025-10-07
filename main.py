import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from io import BytesIO

# --- Configs ---
CATEGORY_MAP = {
    "L-CAP": "CAP",
    "CAP": "CAP",
    "MASK": "MASK",
    "BANDANA": "BANDANA",
    "PLANTER": "PLANTER"
}

def get_category(sku: str) -> str:
    # Match longest prefix first (so L-CAP wins over CAP)
    for prefix in sorted(CATEGORY_MAP.keys(), key=lambda x: -len(x)):
        if sku.startswith(prefix):
            return CATEGORY_MAP[prefix]
    return sku.split('-')[0]

def _to_int(val, default=1) -> int:
    try:
        return int(float(val))
    except Exception:
        return default

def get_multiplier(sku: str, multipliers: dict) -> int:
    # Exact match
    if sku in multipliers:
        return _to_int(multipliers[sku], 1)
    # Pattern match if key is contained anywhere in SKU
    for key, val in multipliers.items():
        if key in sku:
            return _to_int(val, 1)
    return 1

def base_sku(sku: str) -> str:
    # Strip pack suffixes at END only
    return re.sub(r'(-P\d+|-PACKOF\d+|-PO\d+|-\d+)$', '', sku)

def process_sales(amazon_df: pd.DataFrame,
                  flipkart_df: pd.DataFrame,
                  multipliers: dict,
                  sales_days: int,
                  purchase_days: int) -> pd.DataFrame:
    combined_df = pd.concat([amazon_df, flipkart_df], ignore_index=True)

    # Normalize SKU & force qty numeric (defensive)
    combined_df["sku"] = combined_df["sku"].astype(str).str.strip().str.upper()
    combined_df["qty"] = pd.to_numeric(combined_df["qty"], errors="coerce").fillna(0.0)

    # Vectorized multiplier lookup
    mult_series = combined_df["sku"].map(lambda s: get_multiplier(s, multipliers)).astype(float)
    combined_df["multiplied_qty"] = (combined_df["qty"].astype(float) * mult_series).astype(float)

    # Base SKU & category
    combined_df["base_sku"] = combined_df["sku"].apply(base_sku)
    combined_df["category"] = combined_df["base_sku"].map(get_category)

    # Aggregate
    sku_sales = (
        combined_df.groupby("base_sku", as_index=False)["multiplied_qty"]
        .sum(min_count=1)
        .rename(columns={"base_sku": "sku", "multiplied_qty": "qty"})
    )

    # Attach category consistently
    base_to_cat = combined_df.drop_duplicates("base_sku").set_index("base_sku")["category"]
    sku_sales["category"] = sku_sales["sku"].map(base_to_cat)

    # Recommendation = (qty / sales_days) * purchase_days
    sku_sales["recommended_purchase_qty"] = (
        (sku_sales["qty"].astype(float) / float(sales_days)) * float(purchase_days)
    ).round().astype(int)

    # Optional: whole unit qty
    sku_sales["qty"] = sku_sales["qty"].round().astype(int)

    # Order columns
    return sku_sales[["sku", "category", "qty", "recommended_purchase_qty"]]

# --- Streamlit UI ---
st.set_page_config(page_title="Inventory Estimator", layout="centered")
st.title("🛒 Inventory Purchase Estimator")

# Cache for user inputs
if "last_sales_days" not in st.session_state:
    st.session_state.last_sales_days = 30
if "last_purchase_days" not in st.session_state:
    st.session_state.last_purchase_days = 15
if "last_output_name" not in st.session_state:
    st.session_state.last_output_name = "purchase_plan.xlsx"
if "last_category" not in st.session_state:
    st.session_state.last_category = "All Categories"

# File uploaders
amazon_file = st.file_uploader("Upload Amazon Sales CSV", type=["csv"])
flipkart_file = st.file_uploader("Upload Flipkart Orders Excel", type=["xlsx"])

# User inputs
sales_days = st.number_input(
    "How many days of sales data did you upload?", min_value=1, max_value=365,
    value=st.session_state.last_sales_days
)
purchase_days = st.number_input(
    "For how many days do you want to purchase inventory?", min_value=1, max_value=365,
    value=st.session_state.last_purchase_days
)
output_name = st.text_input("Output file name (Excel):", value=st.session_state.last_output_name)

# Load multipliers config
multipliers = {}
try:
    with open("config/sku_multipliers.json") as f:
        multipliers = json.load(f)
except Exception:
    st.warning("Could not load config/sku_multipliers.json. All multipliers will default to 1.")

if amazon_file and flipkart_file:
    # ---------- Amazon ----------
    amazon_df = pd.read_csv(amazon_file)
    amazon_df = amazon_df.rename(columns=lambda x: str(x).strip())
    amazon_df = amazon_df.rename(columns={
        "SKU": "sku",
        "Units Ordered": "qty",
    })
    # Normalize SKU & qty (remove thousands separators)
    amazon_df["sku"] = amazon_df["sku"].astype(str).str.strip().str.upper()
    amazon_df["qty"] = pd.to_numeric(
        amazon_df["qty"].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    ).fillna(0.0)

    amazon_df["platform"] = "amazon"
    amazon_df["day"] = datetime.today().date()
    amazon_df = amazon_df[["sku", "qty", "platform", "day"]]

    # ---------- Flipkart ----------
    flipkart_df = pd.read_excel(flipkart_file, sheet_name="Orders", engine="openpyxl")
    flipkart_df = flipkart_df.rename(columns=lambda x: str(x).strip())
    # Adjust these if your Flipkart column names differ
    flipkart_df = flipkart_df.rename(columns={
        "sku": "sku",
        "quantity": "quantity",
        "order_item_status": "order_item_status",
        "order_date": "order_date",
    })
    # Extract true SKU if embedded like: ... SKU:"ABC-123" ...
    extracted = flipkart_df["sku"].astype(str).str.extract(r'SKU:([^"]+)')[0]
    flipkart_df["sku"] = extracted.fillna(flipkart_df["sku"]).astype(str).str.strip().str.upper()

    flipkart_df["quantity"] = pd.to_numeric(flipkart_df["quantity"], errors="coerce").fillna(0.0)
    flipkart_df["order_date"] = pd.to_datetime(flipkart_df["order_date"], errors="coerce").dt.date

    def flipkart_qty(row):
        if row["order_item_status"] == "DELIVERED":
            return row["quantity"]
        elif row["order_item_status"] in ["RETURNED", "CANCELLED"]:
            return -row["quantity"]
        else:
            return 0.0

    flipkart_df["qty"] = flipkart_df.apply(flipkart_qty, axis=1)
    flipkart_df = flipkart_df[flipkart_df["qty"] != 0]
    flipkart_df["platform"] = "flipkart"
    flipkart_df = flipkart_df.rename(columns={"order_date": "day"})
    flipkart_df = flipkart_df[["sku", "qty", "platform", "day"]]

    # ---------- Process ----------
    sku_sales = process_sales(amazon_df, flipkart_df, multipliers, sales_days, purchase_days)

    # ---------- Category dropdown filter ----------
    categories = ["All Categories"] + sorted(c for c in sku_sales["category"].dropna().unique())
    selected_category = st.selectbox("Filter by category", categories, index=categories.index(st.session_state.last_category) if st.session_state.last_category in categories else 0)

    if selected_category != "All Categories":
        filtered = sku_sales[sku_sales["category"] == selected_category].copy()
    else:
        filtered = sku_sales.copy()

    st.success(f"Processing complete! Showing {len(filtered)} SKU(s).")
    st.dataframe(filtered[["sku", "category", "qty", "recommended_purchase_qty"]])

    # Download as Excel (filtered)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered.to_excel(writer, index=False, sheet_name='PurchasePlan')
    st.download_button(
        label="Download Excel",
        data=output.getvalue(),
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Persist last-used values
    st.session_state.last_sales_days = int(sales_days)
    st.session_state.last_purchase_days = int(purchase_days)
    st.session_state.last_output_name = output_name
    st.session_state.last_category = selected_category

else:
    st.info("Please upload both Amazon and Flipkart files to continue.")