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
        
        # Standardize headers (strip spaces)
        df.columns = [c.strip() for c in df.columns]
        
        # Rename known columns
        col_map = {
            "SKU": "sku",
            "Units Ordered": "qty",
            "(Child) ASIN": "asin",
            "Title": "title"
        }
        df = df.rename(columns=col_map)
        
        # Validation
        if "sku" not in df.columns or "qty" not in df.columns:
            return None, "Amazon file missing 'SKU' or 'Units Ordered' columns."

        # Clean Data
        df["sku"] = df["sku"].apply(clean_sku)
        # Remove commas from numbers (e.g., "1,000" -> 1000)
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
        
        # Mapping
        col_map = {
            "sku": "sku",
            "quantity": "qty",
            "order_item_status": "status"
        }
        df = df.rename(columns=col_map)

        # Regex Extraction for messy Flipkart SKUs (e.g. "Tax:18% SKU:ABC-123")
        def extract_flipkart_sku(raw_val):
            raw_val = str(raw_val)
            match = re.search(r'SKU:([^"]+)', raw_val)
            if match:
                return match.group(1)
            return raw_val # Fallback

        df["sku"] = df["sku"].apply(extract_flipkart_sku).apply(clean_sku)
        df["qty"] = pd.to_numeric(df["qty"], errors='coerce').fillna(0)
        
        # Filter Returns/Cancellations
        # Net Sales = Delivered - (Returned + Cancelled)
        # Note: This logic assumes the report contains ALL status rows for the period.
        # If you only want positive sales, filter for 'DELIVERED'.
        # Adjusting to your previous logic: Only count valid sales?
        # Let's stick to: Count sales, ignore cancellations for Replenishment demand (usually safer).
        valid_statuses = ["DELIVERED", "SHIPPED", "APPROVED", "PACKED"]
        df = df[df["status"].isin(valid_statuses)]
        
        df["platform"] = "Flipkart"
        return df[["sku", "qty", "platform"]], None

    except Exception as e:
        return None, f"Error reading Flipkart file: {str(e)}"