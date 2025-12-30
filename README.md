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

### 6. **US vs International Stocks (Minus Cash)**
Breakdown of stock allocation between:
- **US (Domestic)**: Percentage of stock allocated to US equities
- **International (Foreign)**: Percentage of stock allocated to international equities

This section excludes cash symbols to focus on invested stock holdings. Displays dollars and percentages relative to total stock (Domestic + Foreign).

### 7. **Asset Location (Tax Efficiency Planning)**
Shows where your stocks and bonds are located across accounts, sorted by account type. This table helps you optimize tax efficiency by placing the right assets in the right account types.

**Columns:**
- **Account**: Account name and number
- **Type**: Account type (see Account Types section below)
- **Stocks**: Total stock holdings (Domestic + Foreign)
- **Bonds**: Total bond holdings (Bonds + Short-term), excluding cash
- **Total**: Sum of stocks and bonds in the account

**Note:** Cash positions (defined in `config.json`) are excluded from bonds to show only actual bond holdings.

### 8. **Asset Location by Account Type**
Aggregates stocks and bonds by account type with an efficiency rating for tax planning.

**Columns:**
- **Type**: Account type
- **Stocks**: Total stocks in this account type
- **Bonds**: Total bonds in this account type
- **Total**: Combined total
- **Efficiency**: Tax efficiency rating
  - **Efficient** (green): Bonds in tax-deferred accounts
  - **X% Inefficient** (red): Bonds in taxable/Roth accounts (shows % of total bonds)
  - **N/A**: No bonds in this account type

**Tax Efficiency Guidelines:**
- Bonds generate ordinary income, so they're most tax-efficient in tax-deferred accounts
- Stocks are tax-efficient in taxable accounts (long-term capital gains treatment)
- Roth accounts are best for high-growth assets

### 9. **PDF Report**
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

You can create an `account_nicknames.json` file to assign friendly names and account types to your accounts. This makes the reports easier to read and enables tax efficiency analysis.

1. Copy the example file:
```bash
cp account_nicknames.json.example account_nicknames.json
```

2. Edit `account_nicknames.json` with your account names and types:
```json
{
  "comment": "Account configuration file. Add your account nicknames and types for tax efficiency planning. Supported types: taxable, tax-deferred, roth; unknown is used as a fallback.",
  "nicknames": {
    "*****1234": {
      "name": "Roth IRA",
      "type": "roth"
    },
    "*****5678": {
      "name": "401(k)",
      "type": "tax-deferred"
    },
    "*****9101": {
      "name": "Brokerage",
      "type": "taxable"
    }
  }
}
```

**Account Types:**
- **taxable**: Standard brokerage accounts (dividends/gains taxed annually)
- **tax-deferred**: Traditional IRA, 401(k), Rollover IRA, 403(b), etc. (taxed on withdrawal)
- **roth**: Roth IRA, Roth 401(k) (tax-free growth and withdrawals)
- **unknown**: Default when type is not specified

The nicknames and types will appear in both console output and PDF reports. Account types are used in the Asset Location tables for tax efficiency analysis.

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
