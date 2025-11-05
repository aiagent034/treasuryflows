# 🏛️ Treasury Data Flow Analyzer

Automated extraction and analysis of U.S. Treasury Department deposits and withdrawals data using the official Treasury Fiscal Data API.

## 📋 Overview

This project pulls fiscal year-end data from the U.S. Department of Treasury's Daily Treasury Statement (DTS) to analyze long-term trends in government cash flows by department. Instead of aggregating daily data, it intelligently retrieves the September 30 report for each fiscal year, which contains complete annual totals.

## ✨ Features

- **🔄 Automated Data Extraction**: GitHub Actions workflow runs monthly
- **📊 Rich Visualizations**: Automatically generates 5+ charts and graphs
- **📈 Trend Analysis**: Year-over-year comparisons and growth rates
- **📁 Excel Reports**: Multi-sheet workbooks with detailed data and summaries
- **🎯 Department-Level Insights**: Aggregated and detailed views
- **⚡ Smart API Handling**: Pagination, retry logic, and rate limiting
- **🔧 Flexible Configuration**: Command-line options for custom analysis

## 📦 What You Get

Each execution produces:

### 📊 Excel Report
- **Overview**: Metadata and execution summary
- **Detailed Data**: All transactions with department categorization
- **Department Summary**: Aggregated by department with YoY changes
- **Transaction Summary**: Granular transaction-level aggregations
- **Summary Statistics**: Financial totals by fiscal year

### 📈 Visualizations
1. **Top 10 Departments by Deposits** (horizontal bar chart)
2. **Top 10 Departments by Withdrawals** (horizontal bar chart)
3. **Year-over-Year Trends** (line charts for top 5 departments)
4. **Deposits vs Withdrawals Comparison** (grouped bar chart)
5. **Growth Rate Heatmap** (YoY percentage changes)

All visualizations are saved as high-resolution PNG files (300 DPI).

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd treasuryflows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the extractor**
   ```bash
   python src/treasury_extractor.py
   ```

4. **Check the outputs**
   ```bash
   ls outputs/
   ```

## 💻 Usage

### Basic Usage

Extract data for the default fiscal years (last 5 years):
```bash
python src/treasury_extractor.py
```

### Custom Fiscal Years

Extract specific years:
```bash
python src/treasury_extractor.py --years FY2022,FY2023,FY2024
```

### Custom Output Directory

Save outputs to a different location:
```bash
python src/treasury_extractor.py --output ./my_reports
```

### Combined Options

```bash
python src/treasury_extractor.py --years FY2020,FY2021,FY2022,FY2023,FY2024 --output ./historical_analysis
```

### Help

```bash
python src/treasury_extractor.py --help
```

## 🤖 Automated Execution (GitHub Actions)

### How It Works

The project includes a GitHub Actions workflow that:
- ✅ Runs automatically on the **1st of every month at 9 AM UTC**
- ✅ Can be triggered **manually** from the GitHub Actions tab
- ✅ Uploads all reports and visualizations as **artifacts**
- ✅ Stores outputs for **90 days**
- ✅ Provides execution summary in the workflow

### Manual Trigger

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Treasury Data Extraction** workflow
4. Click **Run workflow** button
5. (Optional) Enter custom fiscal years
6. Click **Run workflow**

### Download Results

1. Navigate to the completed workflow run
2. Scroll to the **Artifacts** section at the bottom
3. Download:
   - `treasury-report-XXX` - Excel file
   - `treasury-visualizations-XXX` - PNG charts
   - `treasury-metadata-XXX` - JSON metadata

### Modify Schedule

Edit `.github/workflows/treasury-data-extraction.yml`:

```yaml
schedule:
  - cron: '0 9 1 * *'  # Monthly on the 1st at 9 AM UTC
  # Examples:
  # - cron: '0 9 1 */3 *'  # Quarterly
  # - cron: '0 9 * * 1'    # Weekly on Monday
  # - cron: '0 9 1 1 *'    # Yearly on Jan 1
```

## 📊 Understanding the Data

### Fiscal Year

- **Runs**: October 1 - September 30
- **FY 2024**: Oct 1, 2023 - Sept 30, 2024
- **Data Source**: September 30 report contains full year totals

### Account Types

- **Deposits**: Money coming into the Treasury
- **Withdrawals**: Money going out of the Treasury

### Key Fields

- `fiscal_year_amt`: Total amount for the entire fiscal year
- `transaction_type`: Specific transaction category (detailed)
- `main_department`: Extracted department name (aggregated)
- `account_type`: Deposits or Withdrawals

## 🏗️ Project Structure

```
treasuryflows/
├── .github/
│   └── workflows/
│       └── treasury-data-extraction.yml  # GitHub Actions workflow
├── src/
│   └── treasury_extractor.py            # Main extraction script
├── outputs/                              # Generated reports (gitignored)
│   └── .gitkeep
├── requirements.txt                      # Python dependencies
├── .gitignore                           # Git ignore rules
└── README.md                            # This file
```

## 📚 API Information

**Data Source**: U.S. Treasury Fiscal Data API
**Endpoint**: `deposits_withdrawals_operating_cash`
**Base URL**: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/`
**Documentation**: https://fiscaldata.treasury.gov/api-documentation/

### API Features Used

- ✅ Date filtering (`record_date:eq:YYYY-MM-DD`)
- ✅ JSON format
- ✅ Pagination (1000 records per page)
- ✅ No authentication required
- ✅ Rate-limited with respectful delays

## 🔧 Customization

### Add More Visualizations

Edit `src/treasury_extractor.py` in the `create_visualizations()` method:

```python
def create_visualizations(self, detailed, dept_summary):
    # Add your custom visualization here
    fig, ax = plt.subplots()
    # ... your plotting code
    plt.savefig(self.output_dir / 'my_chart.png', dpi=300)
```

### Modify Data Processing

Edit the `process_data()` method to add custom aggregations or filters.

### Change Default Fiscal Years

Edit `DEFAULT_FISCAL_YEARS` at the top of `treasury_extractor.py`:

```python
DEFAULT_FISCAL_YEARS = {
    'FY2019': '2019-09-30',
    'FY2020': '2020-09-30',
    # ... add more years
}
```

## 🐛 Troubleshooting

### Issue: GitHub Actions workflow failed

**Common causes**:
- API rate limiting (HTTP 403) - too many requests in short time
- Network connectivity from GitHub to Treasury API
- Fiscal year data not yet available

**Solutions**:
1. **Wait and retry**: GitHub's IP may be temporarily rate-limited. Try again in 15-30 minutes.
2. **Manual trigger with fewer years**: Go to Actions → Run workflow → Enter `FY2023,FY2024` instead of all 5 years
3. **Check workflow logs**: Look for specific error messages (403, 404, timeout)
4. **Test API connectivity**: Run `python src/test_api.py` locally to verify API is accessible

### Issue: No data retrieved (local)

**Possible causes**:
- Fiscal year data not yet available (e.g., FY 2025 before Sept 30, 2025)
- API temporarily unavailable or rate limited
- Network connectivity issues
- Firewall blocking requests

**Solution**:
```bash
# Test API connectivity first
python src/test_api.py

# Try with a single recent year
python src/treasury_extractor.py --years FY2023

# Wait 5 minutes and try again (rate limiting)
sleep 300 && python src/treasury_extractor.py --years FY2023

# Check API status
curl -I https://fiscaldata.treasury.gov/
```

### Issue: Import errors

**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: Permission denied on outputs/

**Solution**:
```bash
chmod +x src/treasury_extractor.py
mkdir -p outputs
```

## 📈 Future Enhancements

Potential additions for future versions:

- [ ] Monthly aggregation (in addition to yearly)
- [ ] Email notifications on completion
- [ ] Interactive dashboards (Plotly/Dash)
- [ ] Database storage (SQLite/PostgreSQL)
- [ ] Comparison with budget projections
- [ ] Historical trend forecasting
- [ ] Web interface
- [ ] Real-time monitoring alerts

## 📄 License

This project is provided as-is for educational and analytical purposes.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check the troubleshooting section above
- Review the API documentation

## 📚 Additional Resources

- [U.S. Treasury Fiscal Data](https://fiscaldata.treasury.gov/)
- [Daily Treasury Statement Dataset](https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/)
- [API Documentation](https://fiscaldata.treasury.gov/api-documentation/)
- [Federal Fiscal Year Information](https://www.fiscal.treasury.gov/reports-statements/)

---

**Made with 💙 for transparent government finance analysis**
