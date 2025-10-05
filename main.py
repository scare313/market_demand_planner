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

def get_category(sku):
    for prefix in sorted(CATEGORY_MAP.keys(), key=lambda x: -len(x)):
        if sku.startswith(prefix):
            return CATEGORY_MAP[prefix]
    return sku.split('-')[0]

def get_multiplier(sku, multipliers):
    if sku in multipliers:
        return multipliers[sku]
    for key in multipliers:
        if key in sku:
            return multipliers[key]
    return 1

def base_sku(sku):
    return re.sub(r'(-P\d+|-PACKOF\d+|-PO\d+|-\d+)$', '', sku)

def process_sales(amazon_df, flipkart_df, multipliers, sales_days, purchase_days):
    combined_df = pd.concat([amazon_df, flipkart_df], ignore_index=True)
    combined_df["multiplied_qty"] = combined_df.apply(
        lambda row: row["qty"] * get_multiplier(row["sku"], multipliers), axis=1)
    combined_df["base_sku"] = combined_df["sku"].apply(base_sku)
    sku_sales = combined_df.groupby("base_sku", as_index=False).agg({"multiplied_qty": "sum"})
    sku_sales = sku_sales.rename(columns={"base_sku": "sku", "multiplied_qty": "qty"})
    sku_sales["category"] = sku_sales["sku"].apply(get_category)
    # Calculate recommended purchase qty
    sku_sales["recommended_purchase_qty"] = (sku_sales["qty"] / sales_days * purchase_days).round().astype(int)
    return sku_sales

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

# File uploaders
amazon_file = st.file_uploader("Upload Amazon Sales CSV", type=["csv"])
flipkart_file = st.file_uploader("Upload Flipkart Orders Excel", type=["xlsx"])

# User inputs
sales_days = st.number_input("How many days of sales data did you upload?", min_value=1, max_value=365, value=st.session_state.last_sales_days)
purchase_days = st.number_input("For how many days do you want to purchase inventory?", min_value=1, max_value=365, value=st.session_state.last_purchase_days)
output_name = st.text_input("Output file name (Excel):", value=st.session_state.last_output_name)

# Load multipliers config
multipliers = {}
try:
    with open("config/sku_multipliers.json") as f:
        multipliers = json.load(f)
except Exception:
    st.warning("Could not load sku_multipliers.json. All multipliers will be 1.")

if amazon_file and flipkart_file:
    amazon_df = pd.read_csv(amazon_file)
    # Try to auto-detect columns
    amazon_df = amazon_df.rename(columns=lambda x: x.strip())
    amazon_df = amazon_df.rename(columns={
        "SKU": "sku",
        "Units Ordered": "qty"
    })
    amazon_df["platform"] = "amazon"
    amazon_df["day"] = datetime.today().date()
    amazon_df = amazon_df[["sku", "qty", "platform", "day"]]

    flipkart_df = pd.read_excel(flipkart_file, sheet_name="Orders", engine="openpyxl")
    flipkart_df = flipkart_df.rename(columns=lambda x: x.strip())
    flipkart_df = flipkart_df.rename(columns={
        "sku": "sku",
        "quantity": "quantity",
        "order_item_status": "order_item_status",
        "order_date": "order_date"
    })
    flipkart_df["sku"] = flipkart_df["sku"].astype(str).str.extract(r'SKU:([^"]+)')[0].str.strip().fillna(flipkart_df["sku"])
    flipkart_df["quantity"] = pd.to_numeric(flipkart_df["quantity"], errors="coerce").fillna(0).astype(int)
    flipkart_df["order_date"] = pd.to_datetime(flipkart_df["order_date"]).dt.date

    def flipkart_qty(row):
        if row["order_item_status"] == "DELIVERED":
            return row["quantity"]
        elif row["order_item_status"] in ["RETURNED", "CANCELLED"]:
            return -row["quantity"]
        else:
            return 0

    flipkart_df["qty"] = flipkart_df.apply(flipkart_qty, axis=1)
    flipkart_df = flipkart_df[flipkart_df["qty"] != 0]
    flipkart_df["platform"] = "flipkart"
    flipkart_df = flipkart_df.rename(columns={"order_date": "day"})
    flipkart_df = flipkart_df[["sku", "qty", "platform", "day"]]

    # Process and display
    sku_sales = process_sales(amazon_df, flipkart_df, multipliers, sales_days, purchase_days)
    st.success("Processing complete! Preview below:")

    st.dataframe(sku_sales[["sku", "category", "qty", "recommended_purchase_qty"]])

    # Download as Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sku_sales.to_excel(writer, index=False, sheet_name='PurchasePlan')
    st.download_button(
        label="Download Excel",
        data=output.getvalue(),
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Save last-used values
    st.session_state.last_sales_days = sales_days
    st.session_state.last_purchase_days = purchase_days
    st.session_state.last_output_name = output_name

else:
    st.info("Please upload both Amazon and Flipkart files to continue.")