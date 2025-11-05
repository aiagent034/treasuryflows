#!/usr/bin/env python3
"""
Treasury Department Data Extractor - Fiscal Year Analysis with Visualizations
Extracts U.S. Treasury deposits and withdrawals data by department for fiscal year analysis

Author: Automated Treasury Analysis System
License: MIT
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import time
import json
from datetime import datetime
from pathlib import Path
import sys
import argparse
import warnings

warnings.filterwarnings('ignore')

# Configuration
BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/deposits_withdrawals_operating_cash"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"

# Default fiscal years - last 5 complete fiscal years
# Note: FY runs Oct 1 - Sept 30, so FY 2024 ends Sept 30, 2024
DEFAULT_FISCAL_YEARS = {
    'FY2020': '2020-09-30',
    'FY2021': '2021-09-30',
    'FY2022': '2022-09-30',
    'FY2023': '2023-09-30',
    'FY2024': '2024-09-30',
}


class TreasuryDataExtractor:
    """Main class for extracting and analyzing Treasury data"""

    def __init__(self, output_dir=None, fiscal_years=None):
        """Initialize extractor with configuration"""
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fiscal_years = fiscal_years or DEFAULT_FISCAL_YEARS
        self.all_data = []
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Set plot style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (14, 8)
        plt.rcParams['font.size'] = 10

    def fetch_fiscal_year_data(self, date_str, fiscal_year):
        """Fetch all data for a fiscal year end date with pagination"""
        print(f"\n📥 Fetching {fiscal_year} ({date_str})...")

        all_records = []
        page = 1
        max_retries = 3

        while True:
            params = {
                "filter": f"record_date:eq:{date_str}",
                "format": "json",
                "page[size]": "1000",
                "page[number]": str(page)
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; TreasuryDataAnalyzer/1.0)"
            }

            retry_count = 0
            while retry_count < max_retries:
                try:
                    response = requests.get(
                        BASE_URL,
                        params=params,
                        headers=headers,
                        timeout=30
                    )

                    if response.status_code == 404:
                        print(f"  ⚠️  No data available for {fiscal_year} (date may not exist yet)")
                        return pd.DataFrame()

                    if response.status_code == 403:
                        print(f"  ⚠️  Access restricted for {fiscal_year} (HTTP 403)")
                        print(f"     This may be due to:")
                        print(f"     - API rate limiting")
                        print(f"     - Temporary access restrictions")
                        print(f"     - Network/firewall blocking")
                        print(f"     Skipping {fiscal_year}...")
                        return pd.DataFrame()

                    if response.status_code != 200:
                        print(f"  ❌ Error: HTTP {response.status_code}")
                        if page == 1:
                            return pd.DataFrame()
                        break

                    data = response.json()

                    if 'data' not in data or len(data['data']) == 0:
                        if page == 1:
                            print(f"  ⚠️  No records found for {fiscal_year}")
                        break

                    all_records.extend(data['data'])

                    # Check pagination
                    meta = data.get('meta', {})
                    total_pages = meta.get('total-pages', 1)
                    total_count = meta.get('total-count', len(all_records))

                    print(f"  📄 Page {page}/{total_pages} - {len(data['data'])} records (Total: {len(all_records)}/{total_count})")

                    if page >= total_pages:
                        break

                    page += 1
                    time.sleep(0.3)  # Be respectful to the API
                    break  # Success, exit retry loop

                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    print(f"  ⚠️  Network error on page {page}, attempt {retry_count}/{max_retries}: {e}")
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)  # Exponential backoff
                    else:
                        if page == 1:
                            return pd.DataFrame()
                        break
                except Exception as e:
                    print(f"  ❌ Unexpected error: {e}")
                    if page == 1:
                        return pd.DataFrame()
                    break

        if all_records:
            df = pd.DataFrame(all_records)
            print(f"  ✅ Retrieved {len(df)} total records for {fiscal_year}")
            return df

        return pd.DataFrame()

    def fetch_all_years(self):
        """Fetch data for all configured fiscal years"""
        print("="*70)
        print("🏛️  U.S. TREASURY DEPARTMENT DATA - FISCAL YEAR ANALYSIS")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for fiscal_year, date_str in self.fiscal_years.items():
            df = self.fetch_fiscal_year_data(date_str, fiscal_year)

            if not df.empty:
                df['fiscal_year'] = fiscal_year
                self.all_data.append(df)

            time.sleep(0.5)  # Pause between years

        if not self.all_data:
            print("\n" + "="*70)
            print("❌ NO DATA RETRIEVED")
            print("="*70)
            print("\nPossible reasons:")
            print("  1. Network connectivity issues")
            print("  2. API is temporarily unavailable or rate limited (HTTP 403)")
            print("  3. Requested fiscal year data may not be available yet")
            print("  4. Firewall or security restrictions blocking access")
            print("\nRecommendations:")
            print("  - Try again in a few minutes (rate limiting)")
            print("  - Test with a single recent year: --years FY2023")
            print("  - Check API status: https://fiscaldata.treasury.gov/")
            print("  - Run the test script: python src/test_api.py")
            return False

        # Report partial success if some years failed
        years_requested = len(self.fiscal_years)
        years_retrieved = len(self.all_data)
        if years_retrieved < years_requested:
            print(f"\n⚠️  Warning: Retrieved {years_retrieved} of {years_requested} requested fiscal years")
            print(f"   Some years may not be available yet or encountered access restrictions")

        return True

    def process_data(self):
        """Process and clean all fetched data"""
        if not self.all_data:
            return None, None, None

        print("\n" + "="*70)
        print("📊 PROCESSING AND AGGREGATING DATA")
        print("="*70)

        # Combine all years
        combined = pd.concat(self.all_data, ignore_index=True)

        # Convert amounts to numeric
        amount_columns = [col for col in combined.columns if 'amt' in col.lower()]
        for col in amount_columns:
            combined[col] = pd.to_numeric(combined[col], errors='coerce')

        # Extract main department name
        if 'transaction_type' in combined.columns:
            combined['main_department'] = combined['transaction_type'].str.extract(
                r'(Dept of [A-Za-z\s&]+|Department of [A-Za-z\s&]+)',
                expand=False
            )
            combined['main_department'] = combined['main_department'].fillna(
                combined['transaction_type'].str.extract(r'^([^-,]+)', expand=False)
            )
            combined['main_department'] = combined['main_department'].str.strip()

        # Create detailed view
        detail_cols = ['fiscal_year', 'record_date', 'account_type', 'transaction_type',
                       'main_department', 'fiscal_year_amt']

        # Add transaction_catg if it exists
        if 'transaction_catg' in combined.columns:
            detail_cols.insert(5, 'transaction_catg')

        detailed = combined[detail_cols].copy()
        detailed = detailed.sort_values(['fiscal_year', 'main_department', 'transaction_type'])

        # Create department summary (aggregated by main department)
        dept_summary = combined.groupby(
            ['fiscal_year', 'main_department', 'account_type']
        )['fiscal_year_amt'].sum().reset_index()

        dept_pivot = dept_summary.pivot_table(
            index=['main_department', 'account_type'],
            columns='fiscal_year',
            values='fiscal_year_amt',
            fill_value=0
        )

        # Calculate year-over-year changes
        fiscal_years_sorted = sorted([fy for fy in self.fiscal_years.keys() if fy in dept_pivot.columns])
        for i in range(1, len(fiscal_years_sorted)):
            prev_year = fiscal_years_sorted[i-1]
            curr_year = fiscal_years_sorted[i]
            if prev_year in dept_pivot.columns and curr_year in dept_pivot.columns:
                dept_pivot[f'{curr_year}_YoY_Change'] = dept_pivot[curr_year] - dept_pivot[prev_year]
                dept_pivot[f'{curr_year}_YoY_Pct'] = (
                    (dept_pivot[curr_year] - dept_pivot[prev_year]) /
                    dept_pivot[prev_year].replace(0, pd.NA) * 100
                )

        # Create transaction-level summary
        transaction_summary = combined.groupby(
            ['fiscal_year', 'transaction_type', 'account_type']
        )['fiscal_year_amt'].sum().reset_index()

        transaction_pivot = transaction_summary.pivot_table(
            index=['transaction_type', 'account_type'],
            columns='fiscal_year',
            values='fiscal_year_amt',
            fill_value=0
        )

        print("✅ Data processing complete")

        return detailed, dept_pivot, transaction_pivot

    def create_visualizations(self, detailed, dept_summary):
        """Create comprehensive data visualizations"""
        print("\n" + "="*70)
        print("📈 GENERATING VISUALIZATIONS")
        print("="*70)

        viz_files = []

        try:
            # 1. Top Departments by Total Amount (Deposits)
            print("  Creating: Top Departments - Deposits...")
            deposits = detailed[detailed['account_type'] == 'Deposits']
            top_dept_deposits = deposits.groupby('main_department')['fiscal_year_amt'].sum().sort_values(ascending=False).head(10)

            fig, ax = plt.subplots(figsize=(12, 8))
            top_dept_deposits.plot(kind='barh', ax=ax, color='#2E7D32')
            ax.set_xlabel('Total Amount (Millions USD)', fontsize=12)
            ax.set_ylabel('Department', fontsize=12)
            ax.set_title('Top 10 Departments by Total Deposits (All Years)', fontsize=14, fontweight='bold')
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
            plt.tight_layout()

            file1 = self.output_dir / f'top_departments_deposits_{self.timestamp}.png'
            plt.savefig(file1, dpi=300, bbox_inches='tight')
            plt.close()
            viz_files.append(file1)
            print(f"    ✅ Saved: {file1.name}")

            # 2. Top Departments by Total Amount (Withdrawals)
            print("  Creating: Top Departments - Withdrawals...")
            withdrawals = detailed[detailed['account_type'] == 'Withdrawals']
            top_dept_withdrawals = withdrawals.groupby('main_department')['fiscal_year_amt'].sum().sort_values(ascending=False).head(10)

            fig, ax = plt.subplots(figsize=(12, 8))
            top_dept_withdrawals.plot(kind='barh', ax=ax, color='#C62828')
            ax.set_xlabel('Total Amount (Millions USD)', fontsize=12)
            ax.set_ylabel('Department', fontsize=12)
            ax.set_title('Top 10 Departments by Total Withdrawals (All Years)', fontsize=14, fontweight='bold')
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
            plt.tight_layout()

            file2 = self.output_dir / f'top_departments_withdrawals_{self.timestamp}.png'
            plt.savefig(file2, dpi=300, bbox_inches='tight')
            plt.close()
            viz_files.append(file2)
            print(f"    ✅ Saved: {file2.name}")

            # 3. Year-over-Year Trends (Top 5 Departments)
            print("  Creating: Year-over-Year Trends...")
            top_5_depts = deposits.groupby('main_department')['fiscal_year_amt'].sum().sort_values(ascending=False).head(5).index

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            # Deposits trend
            for dept in top_5_depts:
                dept_data = deposits[deposits['main_department'] == dept].groupby('fiscal_year')['fiscal_year_amt'].sum()
                ax1.plot(dept_data.index, dept_data.values, marker='o', linewidth=2, label=dept[:30])

            ax1.set_xlabel('Fiscal Year', fontsize=12)
            ax1.set_ylabel('Amount (Millions USD)', fontsize=12)
            ax1.set_title('Deposits Trend - Top 5 Departments', fontsize=14, fontweight='bold')
            ax1.legend(loc='best', fontsize=9)
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
            ax1.grid(True, alpha=0.3)

            # Withdrawals trend
            top_5_withdrawal_depts = withdrawals.groupby('main_department')['fiscal_year_amt'].sum().sort_values(ascending=False).head(5).index
            for dept in top_5_withdrawal_depts:
                dept_data = withdrawals[withdrawals['main_department'] == dept].groupby('fiscal_year')['fiscal_year_amt'].sum()
                ax2.plot(dept_data.index, dept_data.values, marker='o', linewidth=2, label=dept[:30])

            ax2.set_xlabel('Fiscal Year', fontsize=12)
            ax2.set_ylabel('Amount (Millions USD)', fontsize=12)
            ax2.set_title('Withdrawals Trend - Top 5 Departments', fontsize=14, fontweight='bold')
            ax2.legend(loc='best', fontsize=9)
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            file3 = self.output_dir / f'yoy_trends_{self.timestamp}.png'
            plt.savefig(file3, dpi=300, bbox_inches='tight')
            plt.close()
            viz_files.append(file3)
            print(f"    ✅ Saved: {file3.name}")

            # 4. Total Deposits vs Withdrawals by Year
            print("  Creating: Deposits vs Withdrawals Comparison...")
            yearly_summary = detailed.groupby(['fiscal_year', 'account_type'])['fiscal_year_amt'].sum().unstack(fill_value=0)

            fig, ax = plt.subplots(figsize=(12, 7))
            x = range(len(yearly_summary.index))
            width = 0.35

            if 'Deposits' in yearly_summary.columns:
                ax.bar([i - width/2 for i in x], yearly_summary['Deposits'], width, label='Deposits', color='#2E7D32')
            if 'Withdrawals' in yearly_summary.columns:
                ax.bar([i + width/2 for i in x], yearly_summary['Withdrawals'], width, label='Withdrawals', color='#C62828')

            ax.set_xlabel('Fiscal Year', fontsize=12)
            ax.set_ylabel('Amount (Millions USD)', fontsize=12)
            ax.set_title('Total Deposits vs Withdrawals by Fiscal Year', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(yearly_summary.index, rotation=0)
            ax.legend()
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
            ax.grid(True, alpha=0.3, axis='y')

            plt.tight_layout()

            file4 = self.output_dir / f'deposits_vs_withdrawals_{self.timestamp}.png'
            plt.savefig(file4, dpi=300, bbox_inches='tight')
            plt.close()
            viz_files.append(file4)
            print(f"    ✅ Saved: {file4.name}")

            # 5. Growth Rate Heatmap (if we have YoY data in dept_summary)
            if not dept_summary.empty:
                print("  Creating: Year-over-Year Growth Heatmap...")
                yoy_cols = [col for col in dept_summary.columns if '_YoY_Pct' in col]

                if yoy_cols:
                    # Get top 10 departments by total amount
                    top_10 = detailed.groupby('main_department')['fiscal_year_amt'].sum().sort_values(ascending=False).head(10).index

                    heatmap_data = dept_summary.loc[top_10][yoy_cols] if isinstance(dept_summary.index, pd.MultiIndex) else pd.DataFrame()

                    if not heatmap_data.empty and len(heatmap_data) > 0:
                        fig, ax = plt.subplots(figsize=(12, 8))

                        # Clean column names
                        heatmap_data.columns = [col.replace('_YoY_Pct', '') for col in heatmap_data.columns]

                        sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
                                   cbar_kws={'label': 'YoY Growth %'}, ax=ax, linewidths=0.5)
                        ax.set_title('Year-over-Year Growth Rate - Top 10 Departments', fontsize=14, fontweight='bold')
                        ax.set_xlabel('Fiscal Year', fontsize=12)
                        ax.set_ylabel('Department', fontsize=12)

                        plt.tight_layout()

                        file5 = self.output_dir / f'growth_heatmap_{self.timestamp}.png'
                        plt.savefig(file5, dpi=300, bbox_inches='tight')
                        plt.close()
                        viz_files.append(file5)
                        print(f"    ✅ Saved: {file5.name}")

            print(f"\n✅ Created {len(viz_files)} visualizations")

        except Exception as e:
            print(f"  ⚠️  Warning: Error creating some visualizations: {e}")

        return viz_files

    def save_outputs(self, detailed, dept_summary, transaction_summary, viz_files):
        """Save all outputs to Excel file with visualizations"""

        excel_filename = self.output_dir / f'Treasury_Analysis_{self.timestamp}.xlsx'

        print(f"\n💾 Saving outputs to {excel_filename.name}...")

        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            # Write data sheets
            if detailed is not None and not detailed.empty:
                detailed.to_excel(writer, sheet_name='Detailed_Data', index=False)
                print(f"  ✅ Sheet: Detailed_Data ({len(detailed):,} rows)")

            if dept_summary is not None and not dept_summary.empty:
                dept_summary.to_excel(writer, sheet_name='Department_Summary')
                print(f"  ✅ Sheet: Department_Summary ({len(dept_summary):,} rows)")

            if transaction_summary is not None and not transaction_summary.empty:
                transaction_summary.to_excel(writer, sheet_name='Transaction_Summary')
                print(f"  ✅ Sheet: Transaction_Summary ({len(transaction_summary):,} rows)")

            # Create overview sheet with metadata
            years_retrieved = sorted(detailed['fiscal_year'].unique()) if detailed is not None else []
            overview_data = {
                'Metric': [
                    'Analysis Date',
                    'Fiscal Years Covered',
                    'Total Records',
                    'Unique Departments',
                    'Unique Transactions',
                    'Data Source',
                    'Visualizations Created'
                ],
                'Value': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    ', '.join(years_retrieved),
                    f"{len(detailed):,}" if detailed is not None else '0',
                    detailed['main_department'].nunique() if detailed is not None else 0,
                    detailed['transaction_type'].nunique() if detailed is not None else 0,
                    'U.S. Treasury Fiscal Data API',
                    len(viz_files)
                ]
            }
            overview_df = pd.DataFrame(overview_data)
            overview_df.to_excel(writer, sheet_name='Overview', index=False)
            print(f"  ✅ Sheet: Overview")

            # Add summary statistics
            if detailed is not None:
                stats_data = []
                for fy in years_retrieved:
                    fy_data = detailed[detailed['fiscal_year'] == fy]
                    deposits = fy_data[fy_data['account_type'] == 'Deposits']['fiscal_year_amt'].sum()
                    withdrawals = fy_data[fy_data['account_type'] == 'Withdrawals']['fiscal_year_amt'].sum()
                    net = deposits - withdrawals

                    stats_data.append({
                        'Fiscal Year': fy,
                        'Total Deposits ($M)': f"{deposits:,.0f}",
                        'Total Withdrawals ($M)': f"{withdrawals:,.0f}",
                        'Net Position ($M)': f"{net:,.0f}",
                        'Num Departments': fy_data['main_department'].nunique()
                    })

                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Summary_Statistics', index=False)
                print(f"  ✅ Sheet: Summary_Statistics")

        print(f"\n✅ Excel file saved: {excel_filename}")

        # Save metadata JSON
        metadata = {
            'extraction_date': datetime.now().isoformat(),
            'fiscal_years': list(self.fiscal_years.keys()),
            'excel_file': excel_filename.name,
            'visualizations': [f.name for f in viz_files],
            'record_count': len(detailed) if detailed is not None else 0
        }

        metadata_file = self.output_dir / f'metadata_{self.timestamp}.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Metadata saved: {metadata_file.name}")

        return excel_filename

    def print_summary(self, detailed):
        """Print summary statistics to console"""
        print("\n" + "="*70)
        print("📈 SUMMARY STATISTICS")
        print("="*70)

        if detailed is None or detailed.empty:
            print("No data to summarize")
            return

        years_retrieved = sorted(detailed['fiscal_year'].unique())
        print(f"Fiscal Years: {', '.join(years_retrieved)}")
        print(f"Total Records: {len(detailed):,}")
        print(f"Unique Departments: {detailed['main_department'].nunique()}")
        print(f"Unique Transactions: {detailed['transaction_type'].nunique()}")

        print(f"\n💰 Financial Summary by Fiscal Year:")
        for fy in years_retrieved:
            fy_data = detailed[detailed['fiscal_year'] == fy]
            deposits = fy_data[fy_data['account_type'] == 'Deposits']['fiscal_year_amt'].sum()
            withdrawals = fy_data[fy_data['account_type'] == 'Withdrawals']['fiscal_year_amt'].sum()
            net = deposits - withdrawals

            print(f"\n  {fy}:")
            print(f"    Deposits:    ${deposits:,.0f}M")
            print(f"    Withdrawals: ${withdrawals:,.0f}M")
            print(f"    Net:         ${net:,.0f}M")

    def run(self):
        """Execute the complete extraction and analysis pipeline"""
        try:
            # Step 1: Fetch data
            if not self.fetch_all_years():
                return False

            # Step 2: Process data
            detailed, dept_summary, transaction_summary = self.process_data()

            if detailed is None:
                print("❌ No data to process")
                return False

            # Step 3: Create visualizations
            viz_files = self.create_visualizations(detailed, dept_summary)

            # Step 4: Save outputs
            excel_file = self.save_outputs(detailed, dept_summary, transaction_summary, viz_files)

            # Step 5: Print summary
            self.print_summary(detailed)

            print("\n" + "="*70)
            print(f"✨ Analysis complete!")
            print(f"📊 Excel Report: {excel_file}")
            print(f"📈 Visualizations: {len(viz_files)} charts created")
            print(f"📁 Output Directory: {self.output_dir}")
            print("="*70)

            return True

        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Extract and analyze U.S. Treasury Department data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python treasury_extractor.py
  python treasury_extractor.py --output ./my_reports
  python treasury_extractor.py --years FY2022,FY2023,FY2024
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output directory for reports and visualizations (default: outputs/)'
    )

    parser.add_argument(
        '--years', '-y',
        type=str,
        default=None,
        help='Comma-separated fiscal years to extract (e.g., FY2022,FY2023,FY2024)'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()

    # Parse custom fiscal years if provided
    fiscal_years = DEFAULT_FISCAL_YEARS
    if args.years:
        custom_years = {}
        for fy in args.years.split(','):
            fy = fy.strip()
            if fy.startswith('FY'):
                year = fy[2:]
                custom_years[fy] = f"20{year[-2:]}-09-30" if len(year) == 2 else f"{year}-09-30"
        if custom_years:
            fiscal_years = custom_years

    # Create and run extractor
    extractor = TreasuryDataExtractor(
        output_dir=args.output,
        fiscal_years=fiscal_years
    )

    success = extractor.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
