📦 Master Inventory Planner (Multi-Channel)

===========================================

An intelligent inventory forecasting tool designed for e-commerce sellers managing **Amazon, Flipkart, and Meesho**. It unifies sales data from multiple platforms, converts packs into base units, and calculates precise replenishment needs based on sales velocity.

🚀 Features
-----------
*   **Multi-Channel Aggregation:** Merges sales reports from Amazon (CSV), Flipkart (Excel), and Meesho (CSV) into a single view.
*   **Smart Unit Conversion:** Automatically detects "Pack of 4" or "Pack of 2" from SKUs and calculates demand for the _Base Unit_ (Internal SKU).
*   **Velocity-Based Forecasting:** Calculates Average Daily Sales (ADS) to recommend purchase quantities.
*   **Customizable Logic:** Adjust Lead Time, Safety Stock, and Purchase Period on the fly.
*   **Orphan Detection:** Identifies new SKUs sold that are missing from your Master Catalog.

📂 Project Structure
--------------------
Ensure your folder looks like this:
Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`  ```
Inventory_Planner/
│
├── main.py                   # The App Interface (Streamlit)
├── start_mdp.bat             # Double-click to run
│
├── config/
│   ├── master_product_list.csv   # SOURCE OF TRUTH (You edit this)
│   └── settings.json             # Default app settings
│
├── src/
│   ├── __init__.py
│   ├── data_loaders.py       # Logic to parse platform files
│   └── inventory_engine.py   # The math engine
│
└── exports/                  # Generated Excel plans save here

````

🛠️ Setup Guide
---------------
1\.  **Install Python:** Ensure Python is installed on your system.
2\.  pip install streamlit pandas openpyxl xlsxwriter
3\.  **Configure Master Data:**
    *   Open config/master\_product\_list.csv.
    *   Add your products. Ensure pack\_qty is correct (e.g., if PLANTER-P04 contains 4 pots, set pack\_qty to 4).

🖱️ How to Use
--------------
1\.  **Start the App:** Double-click start\_mdp.bat
2\.  **Upload Sales:**
    *   **Amazon:** Upload "Business Report" (CSV).
    *   **Flipkart:** Upload "Orders Report" (Excel).
    *   **Meesho:** Upload "Orders Report" (CSV).
3\.  **Adjust Settings (Sidebar):**
    *   _Sales Days:_ How many days of history did you upload? (e.g., 30).
    *   _Days to Cover:_ How many days of stock do you want to buy? (e.g., 15).
    *   _Lead Time:_ Days for supplier to deliver.
4\.  **Analyze:** The app calculates Net Units to Buy based on velocity.
5\.  **Download:** Click "Download Purchase Plan" to get the final Excel sheet.

📊 The Math Behind It
---------------------
The tool uses a standard Reorder Point formula:
1\.  **ADS (Average Daily Sales):** Total Base Units Sold / Sales Days
2\.  **Safety Stock:** ADS \* Safety Stock Days
3\.  **Lead Time Demand:** ADS \* Lead Time Days
4\.  **Cycle Stock:** ADS \* Days to Cover
5\.  **Recommended Qty:** Cycle Stock + Safety Stock + Lead Time Demand

_Built for efficiency. Happy Selling!_ 📈