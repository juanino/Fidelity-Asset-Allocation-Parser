"""
Asset Allocation Analysis Tool

Analyzes asset allocation from a Fidelity Excel export file, outputs summary tables, and logs all stdout to history.log with timestamps.
"""
import sys
import argparse
import json
import datetime
import atexit
import pandas as pd

# Load configuration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

excel_filename = config['excel_filename']
cash_symbols = config['cash_symbols']

# Set up command-line argument parser
parser = argparse.ArgumentParser(description='Analyze asset allocation from Excel file')
parser.add_argument('--account', type=str, default=None, help='Specify account to analyze (default: all accounts)')
args = parser.parse_args()

# Setup history log: capture stdout to a timestamped history.log (append mode)
HISTORY_PATH = 'history.log'

class TimestampedTee:
    """Write stdout to both terminal and a file, prefixing each line in the file with a timestamp."""
    def __init__(self, filepath):
        """Initialize tee with file path."""
        self.terminal = sys.stdout
        self._buf = ''
        self.filepath = filepath
        self.file = open(self.filepath, 'a', encoding='utf-8')

    def write(self, message):
        """Write message to terminal and to file with timestamp."""
        try:
            self.terminal.write(message)
        except (OSError, IOError) as err:
            print(f"Terminal write error: {err}", file=sys.__stderr__)
        text = self._buf + message
        lines = text.splitlines(True)
        if lines:
            for part in lines[:-1]:
                ts = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
                self.file.write(f"{ts} {part}")
            if lines[-1].endswith('\n'):
                ts = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
                self.file.write(f"{ts} {lines[-1]}")
                self._buf = ''
            else:
                self._buf = lines[-1]

    def flush(self):
        """Flush both terminal and file."""
        try:
            self.terminal.flush()
        except (OSError, IOError) as err:
            print(f"Terminal flush error: {err}", file=sys.__stderr__)
        try:
            if self.file and not self.file.closed:
                self.file.flush()
        except (OSError, IOError) as err:
            print(f"File flush error: {err}", file=sys.__stderr__)

    def close(self):
        """Flush buffer and close file."""
        if self._buf:
            ts = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
            self.file.write(f"{ts} {self._buf}\n")
            self._buf = ''
        try:
            self.file.close()
        except (OSError, IOError) as err:
            print(f"File close error: {err}", file=sys.__stderr__)

# Replace sys.stdout with the tee so all prints go to history.log as well
tee = TimestampedTee(HISTORY_PATH)
sys.stdout = tee

# Ensure file is closed at exit and stdout restored
def _cleanup():
    """Flush and close the tee at exit."""
    try:
        tee.flush()
        tee.close()
    except (OSError, IOError) as err:
        print(f"Cleanup error: {err}", file=sys.__stderr__)

atexit.register(_cleanup)

# Read the AssetAllocation.xls file into a pandas dataframe
df = pd.read_excel(excel_filename)

# The first row contains the actual headers, so set them properly
df.columns = df.iloc[0]
df = df.iloc[1:].reset_index(drop=True)

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Remove rows that are NaN or contain disclaimer text
df = df.dropna(subset=['Symbol'])

# Filter by account if specified
if args.account:
    df = df[df['Account'].str.strip() == args.account]
    print(f"Analyzing account: {args.account}")
    print("=" * 120)
else:
    print("Analyzing all accounts")
    print("=" * 120)

print()

# Get the asset allocation columns (everything except Symbol, Description, and Account)
asset_columns = [col for col in df.columns if col not in ['Symbol', 'Description', 'Account']]

# Convert asset allocation columns to numeric
for col in asset_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Create a pivot table with asset types as columns
pivot_table = df[['Symbol', 'Description'] + asset_columns].copy()

# Display the full table
print(
    "Asset Allocation Summary:"
)
print("=" * 120)
print(pivot_table.to_string())

# Also create a summary showing total allocation by asset class
print(
    "\n\nTotal Allocation by Asset Class:"
)
print("=" * 70)
summary = df[asset_columns].sum()
print(summary)

# Create a detailed summary with dollars and percentages
print(
    "\n\nDetailed Allocation Summary:"
)
print("=" * 70)
total_value = summary.sum()

summary_df = pd.DataFrame({
    'Asset Class': summary.index,
    'Dollars': summary.values,
    'Percentage': (summary.values / total_value * 100).round(2)
})

# Format the output nicely
for idx, row in summary_df.iterrows():
    print(f"{row['Asset Class']:20s} "
          f"${row['Dollars']:>15,.2f}  "
          f"{row['Percentage']:>7.2f}%")

print("-" * 70)
print(f"{'TOTAL':20s} "
      f"${total_value:>15,.2f}  "
      f"{100.00:>7.2f}%")

# Detailed Allocation Minus Cash
print(
    "\n\nDetailed Allocation Minus Cash:"
)
print("=" * 70)
df_minus_cash = df[~df['Symbol'].isin(cash_symbols)]
summary_minus_cash = df_minus_cash[asset_columns].sum()
total_value_minus_cash = summary_minus_cash.sum()

summary_minus_cash_df = pd.DataFrame({
    'Asset Class': summary_minus_cash.index,
    'Dollars': summary_minus_cash.values,
    'Percentage': (summary_minus_cash.values / total_value_minus_cash * 100).round(2)
})

for idx, row in summary_minus_cash_df.iterrows():
    print(f"{row['Asset Class']:20s} "
          f"${row['Dollars']:>15,.2f}  "
          f"{row['Percentage']:>7.2f}%")

print("-" * 70)
print(f"{'TOTAL':20s} "
      f"${total_value_minus_cash:>15,.2f}  "
      f"{100.00:>7.2f}%")

# Final table: Stock and Bonds/CDs aggregation
print(
    "\n\nFinal Aggregated Table (Stock vs Bonds or CDs):"
)
print("=" * 70)

# Aggregate columns
stock_total = summary_minus_cash_df.loc[summary_minus_cash_df['Asset Class'].isin(['Domestic Stock', 'Foreign Stock']), 'Dollars'].sum()
cash_total = summary_minus_cash_df.loc[summary_minus_cash_df['Asset Class'].isin(['Bonds', 'Short_term']), 'Dollars'].sum()
other_total = summary_minus_cash_df.loc[~summary_minus_cash_df['Asset Class'].isin(['Domestic Stock', 'Foreign Stock', 'Bonds', 'Short_term']), 'Dollars'].sum()
total_agg = stock_total + cash_total + other_total

agg_df = pd.DataFrame({
    'Category': ['Stock', 'Bonds or CDs', 'Other'],
    'Dollars': [stock_total, cash_total, other_total],
    'Percentage': [round(stock_total/total_agg*100,2), round(cash_total/total_agg*100,2), round(other_total/total_agg*100,2)]
})

for idx, row in agg_df.iterrows():
    print(f"{row['Category']:20s} "
          f"${row['Dollars']:>15,.2f}  "
          f"{row['Percentage']:>7.2f}%")

print("-" * 70)
print(f"{'TOTAL':20s} "
      f"${total_agg:>15,.2f}  "
      f"{100.00:>7.2f}%")

# Display list of accounts for reference
print(
    "\n\nAvailable Accounts:"
)
print("=" * 70)
print(
    "Use --account option to analyze a specific account:"
)
print(
    "Example: python check_allocation.py --account \"*1234\""
)
print("=" * 70)

# Read the original dataframe to get all accounts
df_original = pd.read_excel(excel_filename)
df_original.columns = df_original.iloc[0]
df_original = df_original.iloc[1:].reset_index(drop=True)
df_original.columns = df_original.columns.str.strip()
df_original = df_original.dropna(subset=['Symbol'])

# Get unique accounts and their holdings
accounts = df_original['Account'].dropna().unique()
account_df = pd.DataFrame({
    'Account': accounts,
    'Holdings': [len(df_original[df_original['Account'] == acc]) for acc in accounts]
})

for idx, row in account_df.iterrows():
    print(f"{str(row['Account']):20s} "
          f"{int(row['Holdings']):3d} holdings")
