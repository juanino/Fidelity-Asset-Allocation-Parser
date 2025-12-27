"""
Asset Allocation Analysis Tool

Analyzes asset allocation from a Fidelity Excel export file, outputs summary tables, and logs all stdout to history.log with timestamps.
"""
import sys
import os
import argparse
import json
import datetime
import atexit
import pandas as pd
from rich.console import Console
from rich.table import Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def print_usage():
    """Print usage information and exit."""
    print("\nUsage: python check_allocation.py [--account ACCOUNT [ACCOUNT ...]]\n")
    print("This tool analyzes asset allocation from a Fidelity Excel export file.")
    print("\nRequired files:")
    print("  - config.json: Configuration file containing excel_filename and cash_symbols")
    print("  - Excel file: The asset allocation export file specified in config.json\n")
    print("Options:")
    print("  --account ACCOUNT [ACCOUNT ...]  Analyze specific account(s) only")
    print("                                   Example: --account *1234 *5678\n")
    print("Example config.json format:")
    print("  {\"excel_filename\": \"AssetAllocation.xls\", \"cash_symbols\": [\"SPAXX\", \"FCASH\"]}\n")
    sys.exit(1)

# Load configuration
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print("\nError: config.json file not found in the current directory.", file=sys.stderr)
    print_usage()
except json.JSONDecodeError as e:
    print(f"\nError: Failed to parse config.json: {e}", file=sys.stderr)
    print_usage()

# Validate configuration
try:
    excel_filename = config['excel_filename']
    cash_symbols = config['cash_symbols']
except KeyError as e:
    print(f"\nError: Missing required key in config.json: {e}", file=sys.stderr)
    print_usage()

# Check if Excel file exists
if not os.path.isfile(excel_filename):
    print(f"\nError: Excel file '{excel_filename}' not found.", file=sys.stderr)
    print("Please ensure the file exists in the current directory.", file=sys.stderr)
    print(f"Current directory: {os.getcwd()}\n", file=sys.stderr)
    print_usage()

# Load account nicknames (optional)
account_nicknames = {}
try:
    with open('account_nicknames.json', 'r', encoding='utf-8') as f:
        nicknames_data = json.load(f)
        account_nicknames = nicknames_data.get('nicknames', {})
except FileNotFoundError:
    pass  # Nicknames file is optional
except json.JSONDecodeError as e:
    print(f"\nWarning: Failed to parse account_nicknames.json: {e}", file=sys.stderr)
    print("Continuing without nicknames.\n", file=sys.stderr)

def get_account_display_name(account_id):
    """Get the display name for an account, using nickname if available."""
    # Remove asterisks for cleaner display
    clean_id = account_id.replace('*', '')
    if account_id in account_nicknames:
        return f"{account_nicknames[account_id]} ({clean_id})"
    return clean_id


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

def _create_pdf_table(data, has_total_row=True):
    """Create a styled ReportLab table."""
    pdf_table = RLTable(data)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]
    if has_total_row:
        style.extend([
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ])
    pdf_table.setStyle(TableStyle(style))
    return pdf_table

def _add_allocation_summary(elements, heading_style, summary_data, total_val, title_text):
    """Add allocation summary section to PDF."""
    elements.append(Paragraph(title_text, heading_style))
    data = [['Asset Class', 'Dollars', 'Percentage']]
    for _, item in summary_data.iterrows():
        data.append([item['Asset Class'], f"${item['Dollars']:,.2f}", f"{item['Percentage']:.2f}%"])
    data.append(['TOTAL', f"${total_val:,.2f}", "100.00%"])
    elements.append(_create_pdf_table(data))
    elements.append(Spacer(1, 0.3*inch))

def _add_allocation_summaries_side_by_side(elements, heading_style, data_dict):
    """Add allocation summary and allocation minus cash tables side by side."""
    # Build left table (Detailed Allocation Summary)
    left_heading = Paragraph("Detailed Allocation Summary", heading_style)
    left_data = [['Asset Class', 'Dollars', 'Percentage']]
    for _, item in data_dict['summary_data'].iterrows():
        left_data.append([item['Asset Class'], f"${item['Dollars']:,.2f}", f"{item['Percentage']:.2f}%"])
    left_data.append(['TOTAL', f"${data_dict['total_val']:,.2f}", "100.00%"])
    left_table = _create_pdf_table(left_data)

    # Build right table (Detailed Allocation Minus Cash)
    right_heading = Paragraph("Detailed Allocation Minus Cash", heading_style)
    right_data = [['Asset Class', 'Dollars', 'Percentage']]
    for _, item in data_dict['summary_minus_cash_data'].iterrows():
        right_data.append([item['Asset Class'], f"${item['Dollars']:,.2f}", f"{item['Percentage']:.2f}%"])
    right_data.append(['TOTAL', f"${data_dict['total_minus_cash']:,.2f}", "100.00%"])
    right_table = _create_pdf_table(right_data)

    # Create a container table to hold both tables side by side
    container_data = [
        [left_heading, right_heading],
        [left_table, right_table]
    ]
    container_table = RLTable(container_data, colWidths=[4.25*inch, 4.25*inch])
    container_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(container_table)
    elements.append(Spacer(1, 0.3*inch))

def _add_cash_tables_side_by_side(elements, heading_style, cash_data, cash_totals_data):
    """Add cash summary and cash by account tables side by side on a new page."""
    # Page title
    elements.append(Paragraph("Cash Analysis", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    # Build left table (Uninvested Money by Account and Symbol)
    left_heading = Paragraph("Uninvested Money by Account and Symbol", heading_style)
    if len(cash_data) > 0:
        left_data = [['Account', 'Symbol', 'Dollars']]
        for _, item in cash_data.iterrows():
            left_data.append([get_account_display_name(str(item['Account'])), str(item['Symbol']), f"${item['Total']:,.2f}"])
        total_cash_sum = cash_data['Total'].sum()
        left_data.append(['TOTAL', '', f"${total_cash_sum:,.2f}"])
    else:
        left_data = [['Account', 'Symbol', 'Dollars'], ['No cash positions', '', '']]
    left_table = _create_pdf_table(left_data)

    # Build right table (Cash in Each Account)
    right_heading = Paragraph("Cash in Each Account", heading_style)
    if len(cash_totals_data) > 0:
        right_data = [['Account', 'Cash Amount']]
        for _, item in cash_totals_data.iterrows():
            right_data.append([get_account_display_name(str(item['Account'])), f"${item['Total']:,.2f}"])
        total = cash_totals_data['Total'].sum()
        right_data.append(['TOTAL', f"${total:,.2f}"])
    else:
        right_data = [['Account', 'Cash Amount'], ['No cash positions', '']]
    right_table = _create_pdf_table(right_data)

    # Create a container table to hold both tables side by side
    container_data = [
        [left_heading, right_heading],
        [left_table, right_table]
    ]
    container_table = RLTable(container_data, colWidths=[5*inch, 3.5*inch])
    container_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(container_table)
    elements.append(Spacer(1, 0.3*inch))

def _add_aggregated_table(elements, heading_style, agg_data, total_agg_value):
    """Add aggregated stock vs bonds section to PDF."""
    elements.append(Paragraph("Stock vs Bonds or CDs", heading_style))
    data = [['Category', 'Dollars', 'Percentage']]
    for _, item in agg_data.iterrows():
        data.append([item['Category'], f"${item['Dollars']:,.2f}", f"{item['Percentage']:.2f}%"])
    data.append(['TOTAL', f"${total_agg_value:,.2f}", "100.00%"])
    elements.append(_create_pdf_table(data))

def _add_invested_summary(elements, heading_style, invested_data):
    """Add invested vs not invested section to PDF."""
    elements.append(Paragraph("Invested vs Not Invested", heading_style))
    data = [['Status', 'Dollars', 'Percentage']]
    for _, item in invested_data.iterrows():
        data.append([item['Status'], f"${item['Dollars']:,.2f}", f"{item['Percentage']:.2f}%"])
    data.append(['TOTAL', f"${invested_data['Dollars'].sum():,.2f}", "100.00%"])
    elements.append(_create_pdf_table(data))

def _add_accounts_list(elements, heading_style, accounts_data):
    """Add available accounts section to PDF."""
    elements.append(Paragraph("Available Accounts", heading_style))
    data = [['Account', 'Holdings']]
    for _, item in accounts_data.iterrows():
        data.append([get_account_display_name(str(item['Account'])), str(int(item['Holdings']))])
    elements.append(_create_pdf_table(data, has_total_row=False))

def generate_pdf(data_dict, accounts_filter=None):
    """Generate a PDF report of the asset allocation analysis.

    Args:
        data_dict: Dictionary containing all data needed for PDF generation with keys:
                  'summary_data', 'total_val', 'cash_data', 'cash_totals_data',
                  'summary_minus_cash_data', 'total_minus_cash', 'agg_data',
                  'total_agg_val', 'invested_data', 'accounts_data'
        accounts_filter: Optional list of account names to filter by
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if accounts_filter:
        filename = f"asset_allocation_report_{'-'.join(accounts_filter)}_{timestamp}.pdf"
    else:
        filename = f"asset_allocation_report_all_{timestamp}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                 fontSize=16, textColor=colors.HexColor('#1f77b4'))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                   fontSize=10, spaceAfter=8)

    # Title
    if accounts_filter:
        title_text = f"Asset Allocation Report - Accounts: {', '.join(accounts_filter)}"
    else:
        title_text = "Asset Allocation Report - All Accounts"
    title = Paragraph(title_text, title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))

    # Timestamp
    timestamp_text = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(timestamp_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    # 1 & 2. Allocation summaries side by side
    _add_allocation_summaries_side_by_side(elements, heading_style, data_dict)

    # 3. Stock vs Bonds or CDs (same page)
    _add_aggregated_table(elements, heading_style, data_dict['agg_data'],
                         data_dict['total_agg_val'])

    # Page break before cash analysis
    elements.append(PageBreak())

    # 4 & 5. Cash tables on their own page
    _add_cash_tables_side_by_side(elements, heading_style, data_dict['cash_data'],
                                  data_dict['cash_totals_data'])

    # 6. Invested vs Not Invested (same page as cash analysis)
    _add_invested_summary(elements, heading_style, data_dict['invested_data'])

    # Page break before available accounts
    elements.append(PageBreak())

    # 7. Available Accounts
    _add_accounts_list(elements, heading_style, data_dict['accounts_data'])

    # Build PDF
    doc.build(elements)
    return filename


# Read the AssetAllocation.xls file into a pandas dataframe
try:
    df = pd.read_excel(excel_filename)
except (FileNotFoundError, PermissionError, ValueError, ImportError) as e:
    print(f"\nError: Failed to read Excel file '{excel_filename}': {e}", file=sys.stderr)
    sys.exit(1)

# The first row contains the actual headers, so set them properly
df.columns = df.iloc[0]
df = df.iloc[1:].reset_index(drop=True)

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Remove rows that are NaN or contain disclaimer text
df = df.dropna(subset=['Symbol'])

# Filter by account if specified
if args.account:
    # Support shorthand: remove asterisks from provided account names for comparison
    account_patterns = [acc.replace('*', '') for acc in args.account]
    df = df[df['Account'].str.strip().str.replace('*', '').isin(account_patterns)]
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
            get_account_display_name(str(row['Account'])),
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
            get_account_display_name(str(row['Account'])),
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
    table.add_row(get_account_display_name(str(row['Account'])), str(int(row['Holdings'])))
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

# Generate PDF report
print("\n\nGenerating PDF Report...")
print("=" * 70)
try:
    pdf_data = {
        'summary_data': summary_df,
        'total_val': total_value,
        'cash_data': cash_by_account,
        'cash_totals_data': cash_by_account_totals if len(df_cash) > 0 else pd.DataFrame(),
        'summary_minus_cash_data': summary_minus_cash_df,
        'total_minus_cash': total_value_minus_cash,
        'agg_data': agg_df,
        'total_agg_val': total_agg,
        'invested_data': invested_df,
        'accounts_data': account_df
    }
    print(f"PDF report successfully generated: {generate_pdf(pdf_data, accounts_filter=args.account)}")
except (IOError, OSError, ValueError) as e:
    print(f"Error generating PDF: {e}", file=sys.stderr)
