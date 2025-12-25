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
from rich.console import Console
from rich.table import Table

# Load configuration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

excel_filename = config['excel_filename']
cash_symbols = config['cash_symbols']

# Set up command-line argument parser
parser = argparse.ArgumentParser(description='Analyze asset allocation from Excel file')
parser.add_argument('--account', type=str, nargs='+', default=None, help='Specify account(s) to analyze (default: all accounts). Use: --account *1234 or --account *1234 *5678')
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

# Create rich console for formatted output
console = Console(file=sys.stdout, force_terminal=True)

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
    df = df[df['Account'].str.strip().isin(args.account)]
    print(f"Analyzing accounts: {', '.join(args.account)}")
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
print("\nAsset Allocation Summary:")
print("=" * 120)
table = Table(title="Asset Allocation Details", show_header=True, header_style="bold magenta")
for col in pivot_table.columns:
    table.add_column(col, style="cyan" if col in ['Symbol', 'Description'] else "green")
for _, row in pivot_table.iterrows():
    table.add_row(*[str(val) for val in row])
console.print(table)

# Also create a summary showing total allocation by asset class
print(
    "\n\nTotal Allocation by Asset Class:"
)
print("=" * 70)
summary = df[asset_columns].sum()
print(summary)

# Create a detailed summary with dollars and percentages
print("\n\nDetailed Allocation Summary:")
print("=" * 70)
total_value = summary.sum()

summary_df = pd.DataFrame({
    'Asset Class': summary.index,
    'Dollars': summary.values,
    'Percentage': (summary.values / total_value * 100).round(2)
})

# Format the output nicely with rich table
table = Table(title="Detailed Allocation Summary", show_header=True, header_style="bold cyan")
table.add_column("Asset Class", style="yellow", width=20)
table.add_column("Dollars", style="green", justify="right")
table.add_column("Percentage", style="magenta", justify="right")
for _, row in summary_df.iterrows():
    table.add_row(
        row['Asset Class'],
        f"${row['Dollars']:,.2f}",
        f"{row['Percentage']:.2f}%"
    )
table.add_row("TOTAL", f"${total_value:,.2f}", "100.00%", style="bold white")
console.print(table)

# Cash positions by account and symbol
print("\n\nUninvested Money by Account and Symbol:")
print("=" * 70)

# Get cash positions from the current dataframe (could be filtered by account)
df_cash = df[df['Symbol'].isin(cash_symbols)].copy()

# Convert asset columns to numeric for cash dataframe
for col in asset_columns:
    df_cash[col] = pd.to_numeric(df_cash[col], errors='coerce')

# Calculate total value for each cash position
df_cash['Total'] = df_cash[asset_columns].sum(axis=1)

# Group by Account and Symbol, summing the totals
if len(df_cash) > 0:
    cash_by_account = df_cash.groupby(['Account', 'Symbol'])['Total'].sum().reset_index()
    cash_by_account = cash_by_account.sort_values(['Account', 'Total'], ascending=[True, False])
else:
    cash_by_account = pd.DataFrame()

# Create table
table = Table(title="Uninvested Money by Account and Symbol", show_header=True, header_style="bold cyan")
table.add_column("Account", style="yellow", width=20)
table.add_column("Symbol", style="cyan", width=10)
table.add_column("Dollars", style="green", justify="right")

if len(cash_by_account) > 0:
    for _, row in cash_by_account.iterrows():
        table.add_row(
            str(row['Account']),
            str(row['Symbol']),
            f"${row['Total']:,.2f}"
        )
    # Add total row
    total_cash_by_account = cash_by_account['Total'].sum()
    table.add_row("TOTAL", "", f"${total_cash_by_account:,.2f}", style="bold white")
else:
    table.add_row("No cash positions", "", "", style="dim")

console.print(table)

# Cash totals by account
print("\n\nCash in Each Account:")
print("=" * 70)

if len(df_cash) > 0:
    cash_by_account_totals = df_cash.groupby('Account')['Total'].sum().reset_index()
    cash_by_account_totals = cash_by_account_totals.sort_values('Total', ascending=False)

    table = Table(title="Cash in Each Account", show_header=True, header_style="bold cyan")
    table.add_column("Account", style="yellow", width=20)
    table.add_column("Cash Amount", style="green", justify="right")

    for _, row in cash_by_account_totals.iterrows():
        table.add_row(
            str(row['Account']),
            f"${row['Total']:,.2f}"
        )
    total_cash = cash_by_account_totals['Total'].sum()
    table.add_row("TOTAL", f"${total_cash:,.2f}", style="bold white")
    console.print(table)
else:
    print("No cash positions found")

# Detailed Allocation Minus Cash
print("\n\nDetailed Allocation Minus Cash:")
print("=" * 70)
df_minus_cash = df[~df['Symbol'].isin(cash_symbols)]
summary_minus_cash = df_minus_cash[asset_columns].sum()
total_value_minus_cash = summary_minus_cash.sum()

summary_minus_cash_df = pd.DataFrame({
    'Asset Class': summary_minus_cash.index,
    'Dollars': summary_minus_cash.values,
    'Percentage': (summary_minus_cash.values / total_value_minus_cash * 100).round(2)
})

table = Table(title="Detailed Allocation Minus Cash", show_header=True, header_style="bold cyan")
table.add_column("Asset Class", style="yellow", width=20)
table.add_column("Dollars", style="green", justify="right")
table.add_column("Percentage", style="magenta", justify="right")
for _, row in summary_minus_cash_df.iterrows():
    table.add_row(
        row['Asset Class'],
        f"${row['Dollars']:,.2f}",
        f"{row['Percentage']:.2f}%"
    )
table.add_row("TOTAL", f"${total_value_minus_cash:,.2f}", "100.00%", style="bold white")
console.print(table)

# Final table: Stock and Bonds/CDs aggregation
print("\n\nFinal Aggregated Table (Stock vs Bonds or CDs):")
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

table = Table(title="Stock vs Bonds or CDs", show_header=True, header_style="bold cyan")
table.add_column("Category", style="yellow", width=20)
table.add_column("Dollars", style="green", justify="right")
table.add_column("Percentage", style="magenta", justify="right")
for _, row in agg_df.iterrows():
    table.add_row(
        row['Category'],
        f"${row['Dollars']:,.2f}",
        f"{row['Percentage']:.2f}%"
    )
table.add_row("TOTAL", f"${total_agg:,.2f}", "100.00%", style="bold white")
console.print(table)

# Display list of accounts for reference
print("\n\nAvailable Accounts:")
print("=" * 70)
print("Use --account option to analyze a specific account:")
print("Example: python check_allocation.py --account \"*1234\"")
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

table = Table(title="Available Accounts", show_header=True, header_style="bold cyan")
table.add_column("Account", style="yellow", width=20)
table.add_column("Holdings", style="green", justify="right")
for _, row in account_df.iterrows():
    table.add_row(str(row['Account']), str(int(row['Holdings'])))
console.print(table)
# Invested vs Not Invested summary
print("\n\nInvested vs Not Invested:")
print("=" * 70)

# Calculate cash (not invested) and invested amounts
cash_amount = df[df['Symbol'].isin(cash_symbols)][asset_columns].sum().sum()
invested_amount = total_value - cash_amount

invested_df = pd.DataFrame({
    'Status': ['Invested', 'Not Invested (Cash)'],
    'Dollars': [invested_amount, cash_amount],
    'Percentage': [round(invested_amount/total_value*100, 2), round(cash_amount/total_value*100, 2)]
})

table = Table(title="Invested vs Not Invested", show_header=True, header_style="bold cyan")
table.add_column("Status", style="yellow", width=25)
table.add_column("Dollars", style="green", justify="right")
table.add_column("Percentage", style="magenta", justify="right")
for _, row in invested_df.iterrows():
    table.add_row(
        row['Status'],
        f"${row['Dollars']:,.2f}",
        f"{row['Percentage']:.2f}%"
    )
table.add_row("TOTAL", f"${total_value:,.2f}", "100.00%", style="bold white")
console.print(table)
