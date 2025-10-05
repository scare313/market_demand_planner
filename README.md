Certainly! Here’s your **README.md** in Markdown format, ready to copy-paste:

```markdown
# 🛒 Inventory Estimator

A user-friendly tool to help e-commerce sellers (Amazon, Flipkart, etc.) estimate inventory purchase requirements based on recent sales data.  
Upload your Amazon and Flipkart sales reports, specify your planning window, and instantly get a downloadable Excel file with recommended purchase quantities—no coding required!

---

## 🚀 Features

- **Upload Amazon and Flipkart sales files** (CSV/XLSX)
- **Flexible planning**: Enter how many days of sales data you uploaded, and for how many days you want to purchase inventory
- **SKU multipliers**: Handles bundle/multi-pack SKUs (e.g., packs of 6, 12, etc.)
- **Category detection**: Groups SKUs by product category (e.g., CAP, PLANTER, BANDANA)
- **User-friendly web UI**: Built with Streamlit
- **Remembers your last-used settings** (caching)
- **Download results as Excel**
- **One-click launch with a `.bat` file** (Windows)

---

## 📦 Folder Structure

```
your_project/
├── app.py
├── config/
│   └── sku_multipliers.json
├── exports/
│   └── (output files will appear here)
├── run_inventory_app.bat
├── requirements.txt
└── README.md
```

---

## 🛠️ Requirements

- Python 3.8+
- pip

**Python packages:**  
- streamlit
- pandas
- openpyxl
- xlsxwriter

Install all requirements with:

```bash
pip install -r requirements.txt
```

**Example `requirements.txt`:**
```
streamlit
pandas
openpyxl
xlsxwriter
```

---

## ⚙️ Configuration

### SKU Multipliers

- Place your `sku_multipliers.json` in the `config/` folder.
- This file maps SKUs or SKU patterns to their “units per sale” multiplier (e.g., packs of 6, 12, etc.).
- Example:

```json
{
  "PLANTER-MULTICOLOUR-DOUBLEHOOK9-P06": 6,
  "BANDANA-PACKOF5": 5,
  "CAPS-PARA-WHITE": 1
}
```

---

## 🖥️ How to Use

### 1. **Start the App**

**Option A: Command Line**

```bash
streamlit run app.py
```

**Option B: Double-Click (Windows)**

- Use the provided `run_inventory_app.bat` file:
    ```bat
    @echo off
    cd /d "%~dp0"
    streamlit run app.py
    pause
    ```
- Double-click `run_inventory_app.bat` to launch the app.

---

### 2. **Using the Web UI**

1. **Upload Files**
    - Upload your Amazon sales CSV (e.g., BusinessReport-*.csv)
    - Upload your Flipkart orders Excel (e.g., *.xlsx)

2. **Enter Parameters**
    - **How many days of sales data did you upload?**  
      (e.g., 30 if you uploaded 30 days of sales)
    - **For how many days do you want to purchase inventory?**  
      (e.g., 15 if you want to plan for the next 15 days)
    - **Output file name**  
      (e.g., `purchase_plan.xlsx`)

3. **Download Results**
    - Preview the table in the browser.
    - Click **Download Excel** to save your purchase plan.

---

### 3. **Output**

- The Excel file will contain:
    - `sku`: The normalized SKU (pack suffixes removed)
    - `category`: Product category (e.g., CAP, PLANTER)
    - `qty`: Total units sold in your sales window
    - `recommended_purchase_qty`: How many units to purchase for your planning window

---

## 🧠 How It Works

- **SKU normalization**: Handles SKUs with pack/bundle suffixes (e.g., `-P06`, `-PACKOF5`)
- **Multipliers**: Uses your `sku_multipliers.json` to convert bundle sales to unit sales
- **Category detection**: Maps SKUs to categories using a customizable prefix map
- **Purchase recommendation**:  
    $$ \text{recommended\_purchase\_qty} = \text{Total Sold in Sales Window} \times \frac{\text{Purchase Days}}{\text{Sales Days}} $$
- **Caching**: Remembers your last-used settings for a smoother workflow

---

## 📝 Customization

- **Add new categories**: Edit the `CATEGORY_MAP` dictionary in `app.py`
- **Add new multipliers**: Edit `sku_multipliers.json`
- **Change output columns**: Edit the `process_sales` function in `app.py`

---

## 🛡️ Troubleshooting

- **App won’t start?**  
  Make sure you have all required Python packages installed.
- **Multipliers not applied?**  
  Check your `sku_multipliers.json` for correct keys and values.
- **Wrong category?**  
  Update the `CATEGORY_MAP` in `app.py` to match your SKU prefixes.

---

## 💡 Tech Stack

- **Python** (data processing)
- **Streamlit** (web UI)
- **Pandas** (data wrangling)
- **Openpyxl/XlsxWriter** (Excel output)
- **JSON** (config)

---

## 🙋 FAQ

**Q: Can I use this for other marketplaces?**  
A: Yes! Just adjust the input file parsing logic in `app.py`.

**Q: Can I add more fields to the output?**  
A: Yes! Edit the `process_sales` function to add more columns.

**Q: Can I run this on Mac/Linux?**  
A: Yes! Just use the command line: `streamlit run app.py`

---

## 📬 Support

For questions, suggestions, or help, open an issue or contact the project maintainer.

---

**Enjoy fast, accurate inventory planning!**  
*— The Inventory Estimator Team*
```

Let me know if you want to add screenshots, badges, or more advanced usage examples!