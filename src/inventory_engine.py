import pandas as pd
import numpy as np

def load_master_data(filepath):
    try:
        df = pd.read_csv(filepath)
        # Ensure critical columns exist
        required = ["marketplace_sku", "internal_sku", "pack_qty"]
        if not all(col in df.columns for col in required):
            return None, f"Master CSV missing columns: {required}"
        
        # Convert columns to correct types
        df["marketplace_sku"] = df["marketplace_sku"].astype(str).str.strip().str.upper()
        df["internal_sku"] = df["internal_sku"].astype(str).str.strip().str.upper()
        df["pack_qty"] = pd.to_numeric(df["pack_qty"], errors='coerce').fillna(1)
        return df, None
    except Exception as e:
        return None, str(e)

def generate_purchase_plan(amazon_df, flipkart_df, meesho_df, master_df, sales_days, purchase_days, lead_time, safety_stock_days):
    """
    1. Merges Sales Data (Amazon + Flipkart + Meesho)
    2. Maps to Master Data (Base SKU & Pack Qty)
    3. Calculates Daily Velocity (ADS)
    4. Computes Reorder Point logic
    """
    
    # 1. Combine Sales
    # We filter out None or Empty dataframes to prevent errors if a file wasn't uploaded
    dfs_to_merge = [df for df in [amazon_df, flipkart_df, meesho_df] if df is not None and not df.empty]
    
    if not dfs_to_merge:
        # Return empty structures if no data is available
        return pd.DataFrame(), pd.DataFrame()

    sales_data = pd.concat(dfs_to_merge, ignore_index=True)
    
    # 2. Merge with Master Data
    # Left join ensures we keep sales data even if it's missing from Master (so we can show orphans)
    merged = pd.merge(
        sales_data, 
        master_df, 
        left_on="sku", 
        right_on="marketplace_sku", 
        how="left"
    )
    
    # 3. Identify Orphan SKUs (Items sold but not in Master List)
    orphans = merged[merged["internal_sku"].isna()].copy()
    orphans = orphans.groupby(["sku", "platform"])["qty"].sum().reset_index()
    
    # 4. Fill missing master data defaults for calculation (assume 1:1 mapping if unknown)
    merged["internal_sku"] = merged["internal_sku"].fillna(merged["sku"])
    merged["pack_qty"] = merged["pack_qty"].fillna(1)
    merged["supplier"] = merged["supplier"].fillna("Unknown")
    merged["category"] = merged["category"].fillna("Uncategorized")
    
    # 5. Calculate Total BASE Units Sold
    # If I sell 10 packs of 5, I sold 50 base units.
    merged["base_units_sold"] = merged["qty"] * merged["pack_qty"]
    
    # 6. Group by INTERNAL SKU (The item sitting in the warehouse)
    # We aggregate demand across all marketplaces and pack sizes.
    group_cols = ["internal_sku", "supplier", "category"]
    plan = merged.groupby(group_cols).agg(
        total_sold_units=('base_units_sold', 'sum'),
        sku_count=('marketplace_sku', 'nunique') # How many listings map to this base item
    ).reset_index()
    
    # 7. The Math
    # Average Daily Sales (ADS)
    plan["ads"] = plan["total_sold_units"] / sales_days
    
    # Lead Time Demand = ADS * Lead Time
    plan["lead_time_demand"] = plan["ads"] * lead_time
    
    # Safety Stock = ADS * Safety Stock Days
    plan["safety_stock"] = plan["ads"] * safety_stock_days
    
    # Cycle Stock (Demand for the period we are buying for)
    plan["cycle_stock"] = plan["ads"] * purchase_days
    
    # Gross Requirement (Simplified Reorder Formula)
    # Total Needed = Cycle Stock + Safety Stock + Lead Time Demand
    plan["recommended_qty"] = (plan["cycle_stock"] + plan["safety_stock"] + plan["lead_time_demand"]).round().astype(int)
    
    # Cleanup for Display
    plan["ads"] = plan["ads"].round(2)
    plan["total_sold_units"] = plan["total_sold_units"].astype(int)
    
    # Sort by highest demand
    plan = plan.sort_values(by="recommended_qty", ascending=False)
    
    return plan, orphans