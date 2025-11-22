import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from io import BytesIO

# Import our custom modules
from src import data_loaders, inventory_engine

# Page Config
st.set_page_config(page_title="Master Inventory Planner", layout="wide", page_icon="📦")

# --- Sidebar: Configuration ---
st.sidebar.title("⚙️ Settings")

# Load defaults
try:
    with open("config/settings.json", "r") as f:
        config = json.load(f)
        defaults = config.get("defaults", {})
except FileNotFoundError:
    defaults = {"sales_period_days": 30, "purchase_period_days": 15, "lead_time_days": 10, "safety_stock_days": 7}

# Inputs
sales_days = st.sidebar.number_input("Days of Sales Data Uploaded", min_value=1, value=defaults["sales_period_days"])
purchase_days = st.sidebar.number_input("Days to Cover (Purchase Period)", min_value=1, value=defaults["purchase_period_days"])
lead_time = st.sidebar.number_input("Supplier Lead Time (Days)", min_value=0, value=defaults["lead_time_days"])
safety_stock = st.sidebar.number_input("Safety Stock Buffer (Days)", min_value=0, value=defaults["safety_stock_days"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Update `config/master_product_list.csv` to change pack sizes or suppliers.")

# --- Main UI ---
st.title("📦 Inventory Purchase Planner")
st.markdown("Upload your sales reports to generate a Master Purchase Plan based on base unit velocity.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Amazon Business Report")
    amz_file = st.file_uploader("Upload CSV", type=["csv"], key="amz")

with col2:
    st.subheader("Flipkart Orders")
    fk_file = st.file_uploader("Upload Excel", type=["xlsx"], key="fk")

# Load Master Data
master_path = "config/master_product_list.csv"
if os.path.exists(master_path):
    master_df, err = inventory_engine.load_master_data(master_path)
    if err:
        st.error(f"Error loading Master Data: {err}")
        st.stop()
    else:
        st.success(f"✅ Master Data Loaded: {len(master_df)} SKUs configured.")
else:
    st.warning(f"⚠️ Master Data not found at {master_path}. Please create it.")
    st.stop()

# Process
if amz_file and fk_file:
    st.markdown("---")
    with st.spinner("Processing Sales Data..."):
        # 1. Load Data
        amz_df, amz_err = data_loaders.load_amazon_sales(amz_file)
        fk_df, fk_err = data_loaders.load_flipkart_sales(fk_file)
        
        if amz_err:
            st.error(amz_err)
        elif fk_err:
            st.error(fk_err)
        else:
            # 2. Run Engine
            plan_df, orphans_df = inventory_engine.generate_purchase_plan(
                amz_df, fk_df, master_df, 
                sales_days, purchase_days, lead_time, safety_stock
            )
            
            # 3. Display KPIs
            kpi1, kpi2, kpi3 = st.columns(3)
            total_units = plan_df["total_sold_units"].sum()
            total_purchase = plan_df["recommended_qty"].sum()
            
            kpi1.metric("Total Base Units Sold", f"{total_units:,.0f}")
            kpi2.metric("Total Units to Buy", f"{total_purchase:,.0f}")
            kpi3.metric("Unique Products", len(plan_df))
            
            # 4. Display Plan
            st.subheader("📋 Purchase Recommendation")
            
            # Category Filter
            cats = ["All"] + sorted(list(plan_df["category"].unique()))
            selected_cat = st.selectbox("Filter by Category", cats)
            
            if selected_cat != "All":
                display_df = plan_df[plan_df["category"] == selected_cat]
            else:
                display_df = plan_df
            
            st.dataframe(display_df.style.background_gradient(subset=['recommended_qty'], cmap='Greens'), use_container_width=True)
            
            # 5. Download
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                plan_df.to_excel(writer, index=False, sheet_name='Purchase Plan')
                if not orphans_df.empty:
                    orphans_df.to_excel(writer, index=False, sheet_name='Unknown SKUs')
                
            st.download_button(
                label="📥 Download Purchase Plan (Excel)",
                data=output.getvalue(),
                file_name=f"Purchase_Plan_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # 6. Warning for Orphans
            if not orphans_df.empty:
                with st.expander("⚠️ Unknown SKUs Found (Action Required)"):
                    st.write("These SKUs were found in your sales data but are MISSING from `master_product_list.csv`. They defaulted to Pack Qty = 1.")
                    st.dataframe(orphans_df)