# Asset Allocation Analysis Tool

## Overview
This Python script analyzes your investment portfolio's asset allocation from a Fidelity Excel export file (`AssetAllocation.xls`). It provides detailed breakdowns of how your investments are distributed across different asset classes.

## What It Does

The script performs the following analyses:

### 1. **Asset Allocation Summary**
Displays a comprehensive table showing all your holdings with their distribution across asset classes:
- Symbol (fund/stock ticker)
- Description (fund/stock name)
- Allocation amounts for each asset class:
  - Domestic Stock
  - Foreign Stock
  - Bonds
  - Short-term investments
  - Other allocations
  - Convertibles
  - Preferred stocks

### 2. **Total Allocation by Asset Class**
Shows the total dollar amount and percentage breakdown across all asset classes across your entire portfolio.

### 3. **Detailed Allocation Summary**
Provides a formatted table showing:
- Asset class name
- Total dollars invested in each class
- Percentage of total portfolio

### 4. **Detailed Allocation Minus Cash**
Excludes cash/money market fund symbols (FZDXX, SPAXX, FZFXX) and recalculates percentages based on non-cash holdings. This is useful for understanding your investment allocation without cash drag.

### 5. **Final Aggregated Table (Stock vs Cash or Short Term)**
High-level summary that groups allocations into three categories:
- **Stock**: Domestic Stock + Foreign Stock
- **Cash or Short Term**: Bonds + Short-term investments
- **Other**: Remaining allocations

Shows both dollar amounts and percentages for each category.

## Usage

### Basic Usage (All Accounts)
```bash
python check_allocation.py
```
Analyzes all accounts in your portfolio.

### Account-Specific Analysis
```bash
python check_allocation.py --account "*1234"
```
Analyzes a specific account. Replace `*1234` with the desired account ID from your data.

### Help
```bash
python check_allocation.py --help
```
Displays available command-line options.

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Input File and Configuration

The script expects:
1. An Excel file specified in `config.json` (default: `AssetAllocation.xls`)
2. A `config.json` file in the same directory

### config.json
The configuration file controls:
- `excel_filename`: Path to your Fidelity export file
- `cash_symbols`: List of symbols to exclude from "Detailed Allocation Minus Cash"

Example `config.json`:
```json
{
  "excel_filename": "AssetAllocation.xls",
  "cash_symbols": ["FZDXX", "SPAXX", "FZFXX"]
}
```

### Excel File Format
The Excel file should be exported from Fidelity and contain the following columns:
- Symbol
- Description
- Account
- Domestic Stock
- Foreign Stock
- Bonds
- Short_term
- Unknown
- Other
- Convertibles
- Preferred

## Key Features
- ✅ Multi-account support with optional filtering
- ✅ Dollar amounts and percentage breakdowns
- ✅ Multiple levels of analysis (detailed, aggregated)
- ✅ Cash-exclusive analysis
- ✅ Clean, formatted output

## Example Output
```
Final Aggregated Table (Stock vs Cash or Short Term):
======================================================================
Stock                $     400,000.00    80.00%
Cash or Short Term   $     100,000.00    20.00%
Other                $           0.00     0.00%
----------------------------------------------------------------------
TOTAL                $     500,000.00   100.00%
```
