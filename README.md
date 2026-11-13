# DecodeLabs Data Analytics – Project 2: Exploratory Data Analysis (EDA)

**Author:** Manish Chahar
**Dataset:** E-commerce orders – 1,200 orders × 14 columns (2023-01-01 to 2025-06-30)
**Tools:** Python (pandas, NumPy, SciPy, Matplotlib)

📄 **Full report:** [EDA_Report_Project2.pdf](EDA_Report_Project2.pdf)

## Project structure
```
Project2-EDA/
├── README.md
├── requirements.txt
├── eda_analysis.py            # computes every statistic, test, chart and CSV table
├── build_report.py            # builds the PDF report from the computed numbers
├── EDA_Report_Project2.pdf    # final report
├── data/
│   └── Dataset_for_Dat__Analytics.xlsx
├── output/                    # CSV tables (descriptive stats, outliers, trends, summaries)
└── charts/                    # 6 charts used in the report
```

## How to run
```bash
pip install -r requirements.txt
python eda_analysis.py            # reads data/Dataset_for_Dat__Analytics.xlsx
python build_report.py            # optional: rebuilds the PDF (needs DejaVu fonts, see note)
```
`eda_analysis.py` creates the `output/` and `charts/` folders automatically. Every number in the report is produced by this script, nothing is typed by hand.

> **Note:** `build_report.py` loads DejaVu fonts from `/usr/share/fonts/truetype/dejavu/` (Linux). On Windows/Mac, change the font path at the top of the file. The PDF is already included, so this step is optional.

## What the analysis covers
1. Data quality checks (duplicates, missing values, arithmetic consistency)
2. Descriptive statistics (mean, median, std, quartiles, skewness)
3. Outlier detection (IQR rule and Z-score)
4. Trends over time (monthly, Jan–Jun year comparison, seasonality)
5. Correlation and segment analysis with significance tests (ANOVA, Kruskal-Wallis, chi-square, Mann-Whitney, linear regression)

## Headline findings
- Data is clean: 0 duplicates, TotalPrice = Quantity × UnitPrice in all rows; only CouponCode has blanks (= no coupon used).
- TotalPrice is right-skewed (mean 1,054 vs median 824); 8 genuine high-value outliers, all with Quantity = 5.
- 41.4% of orders are Cancelled or Returned, the biggest business issue in the data.
- Jan–Jun orders fell 8.3% and order value 19.1% (2023 → 2025), but the decline is not statistically significant.
- Product, coupon, payment method and referral channel show no significant difference in order value.

## Caveats
- Coupon discounts are not reflected in TotalPrice, so real revenue may be lower.
- Value figures are gross booked value, including cancelled/returned orders.
- 2025 has only six months, so half-year comparisons were used.
