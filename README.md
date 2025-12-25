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

### 6. **PDF Report**
Automatically generates a professional PDF report containing all the analysis tables with timestamps.

## Installation

### Using Make (Recommended)
```bash
make install
```
This will create a virtual environment and install all dependencies.

### Manual Installation

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Using Make (Recommended)
```bash
make run
```
Analyzes all accounts in your portfolio and generates a PDF report.

### Manual Usage

#### Basic Usage (All Accounts)
```bash
python check_allocation.py
```
Analyzes all accounts in your portfolio.

#### Account-Specific Analysis
```bash
python check_allocation.py --account "*1234"
```
Analyzes a specific account. Replace `*1234` with the desired account ID from your data.

#### Help
```bash
python check_allocation.py --help
```
Displays available command-line options.

## Make Commands

- `make install` - Create virtual environment and install dependencies
- `make run` - Run the asset allocation analysis
- `make clean` - Remove generated PDF reports
- `make lint` - Run pylint on the code
- `make help` - Show available make targets

## Input File and Configuration

The script expects:
1. An Excel file specified in `config.json` (default: `AssetAllocation.xls`)
2. A `config.json` file in the same directory
3. (Optional) An `account_nicknames.json` file for friendly account names

### Account Nicknames (Optional)

You can create an `account_nicknames.json` file to assign friendly names to your accounts. This makes the reports easier to read.

1. Copy the example file:
```bash
cp account_nicknames.json.example account_nicknames.json
```

2. Edit `account_nicknames.json` with your account names:
```json
{
  "nicknames": {
    "*****1234": "Roth IRA",
    "*****5678": "401(k)",
    "*****9101": "Brokerage"
  }
}
```

The nicknames will appear in both console output and PDF reports as "Nickname (Account ID)". If no nickname file exists, the tool will work normally using just the account IDs.

**Note:** The `account_nicknames.json` file is excluded from git to protect your privacy.

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
