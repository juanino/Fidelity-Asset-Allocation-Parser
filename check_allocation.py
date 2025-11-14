import pandas as pd
import argparse
import json

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

excel_filename = config['excel_filename']
cash_symbols = config['cash_symbols']

# Set up command-line argument parser
parser = argparse.ArgumentParser(description='Analyze asset allocation from Excel file')
parser.add_argument('--account', type=str, default=None, help='Specify account to analyze (default: all accounts)')
args = parser.parse_args()

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
print("Asset Allocation Summary:")
print("=" * 120)
print(pivot_table.to_string())

# Also create a summary showing total allocation by asset class
print("\n\nTotal Allocation by Asset Class:")
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

# Format the output nicely
for idx, row in summary_df.iterrows():
    print(f"{row['Asset Class']:20s} ${row['Dollars']:>15,.2f}  {row['Percentage']:>7.2f}%")

print("-" * 70)
print(f"{'TOTAL':20s} ${total_value:>15,.2f}  {100.00:>7.2f}%")

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

for idx, row in summary_minus_cash_df.iterrows():
    print(f"{row['Asset Class']:20s} ${row['Dollars']:>15,.2f}  {row['Percentage']:>7.2f}%")

print("-" * 70)
print(f"{'TOTAL':20s} ${total_value_minus_cash:>15,.2f}  {100.00:>7.2f}%")

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

for idx, row in agg_df.iterrows():
    print(f"{row['Category']:20s} ${row['Dollars']:>15,.2f}  {row['Percentage']:>7.2f}%")

print("-" * 70)
print(f"{'TOTAL':20s} ${total_agg:>15,.2f}  {100.00:>7.2f}%")

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

for idx, row in account_df.iterrows():
    print(f"{str(row['Account']):20s}  {int(row['Holdings']):3d} holdings")
