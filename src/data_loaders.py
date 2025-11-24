import pandas as pd
import re
from datetime import datetime

def clean_sku(sku):
    """Standardizes SKU format: Uppercase, stripped of whitespace."""
    if pd.isna(sku):
        return "UNKNOWN"
    return str(sku).strip().upper()

def load_amazon_sales(uploaded_file):
    """Parses Amazon Business Report CSV."""
    try:
        df = pd.read_csv(uploaded_file)
        
        df.columns = [c.strip() for c in df.columns]
        
        col_map = {
            "SKU": "sku",
            "Units Ordered": "qty",
            "(Child) ASIN": "asin",
            "Title": "title"
        }
        df = df.rename(columns=col_map)
        
        if "sku" not in df.columns or "qty" not in df.columns:
            return None, "Amazon file missing 'SKU' or 'Units Ordered' columns."

        df["sku"] = df["sku"].apply(clean_sku)
        df["qty"] = pd.to_numeric(df["qty"].astype(str).str.replace(",", ""), errors='coerce').fillna(0)
        
        df["platform"] = "Amazon"
        return df[["sku", "qty", "platform"]], None
        
    except Exception as e:
        return None, f"Error reading Amazon file: {str(e)}"

def load_flipkart_sales(uploaded_file):
    """Parses Flipkart Orders Excel."""
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Orders", engine="openpyxl")
        df.columns = [c.strip() for c in df.columns]
        
        col_map = {
            "sku": "sku",
            "quantity": "qty",
            "order_item_status": "status"
        }
        df = df.rename(columns=col_map)

        def extract_flipkart_sku(raw_val):
            raw_val = str(raw_val)
            match = re.search(r'SKU:([^"]+)', raw_val)
            if match:
                return match.group(1)
            return raw_val

        df["sku"] = df["sku"].apply(extract_flipkart_sku).apply(clean_sku)
        df["qty"] = pd.to_numeric(df["qty"], errors='coerce').fillna(0)
        
        valid_statuses = ["DELIVERED", "SHIPPED", "APPROVED", "PACKED"]
        df = df[df["status"].isin(valid_statuses)]
        
        df["platform"] = "Flipkart"
        return df[["sku", "qty", "platform"]], None

    except Exception as e:
        return None, f"Error reading Flipkart file: {str(e)}"

def load_meesho_sales(uploaded_file):
    """Parses Meesho Orders CSV."""
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip() for c in df.columns]
        
        # Mapping based on your file structure
        col_map = {
            "SKU": "sku",
            "Quantity": "qty",
            "Reason for Credit Entry": "status"
        }
        df = df.rename(columns=col_map)
        
        if "sku" not in df.columns or "qty" not in df.columns:
            return None, "Meesho file missing 'SKU' or 'Quantity' columns."

        df["sku"] = df["sku"].apply(clean_sku)
        df["qty"] = pd.to_numeric(df["qty"], errors='coerce').fillna(0)
        
        # We include all rows (Delivered & RTO) as 'Demand'. 
        # If you want to exclude RTOs later, we can filter by 'status' here.
        
        df["platform"] = "Meesho"
        return df[["sku", "qty", "platform"]], None
        
    except Exception as e:
        return None, f"Error reading Meesho file: {str(e)}"

def load_stock_levels(uploaded_file):
    """Parses Current Stock Levels (CSV or Excel)."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        df.columns = [c.strip().lower() for c in df.columns]
        
        sku_col = next((c for c in df.columns if 'sku' in c), None)
        qty_col = next((c for c in df.columns if 'qty' in c or 'stock' in c), None)
        
        if not sku_col or not qty_col:
            return None, "Stock file must have 'sku' and 'qty' columns."
            
        df = df.rename(columns={sku_col: "internal_sku", qty_col: "stock_on_hand"})
        
        df["internal_sku"] = df["internal_sku"].apply(clean_sku)
        df["stock_on_hand"] = pd.to_numeric(df["stock_on_hand"], errors='coerce').fillna(0)
        
        return df[["internal_sku", "stock_on_hand"]], None

    except Exception as e:
        return None, f"Error reading Stock file: {str(e)}"