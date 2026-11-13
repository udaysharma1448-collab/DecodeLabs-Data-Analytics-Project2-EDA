"""DecodeLabs Data Analytics - Project 2: Exploratory Data Analysis (EDA)
Run:  python eda_analysis.py   (reads data/Dataset_for_Dat__Analytics.xlsx; needs pandas, numpy, scipy, matplotlib, openpyxl)
Reads the dataset, computes every statistic, saves charts + CSV tables.
Every number in the PDF report is produced by this script (nothing typed by hand)."""
import pandas as pd, numpy as np, json
from scipy import stats
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys, os
os.makedirs("output", exist_ok=True); os.makedirs("charts", exist_ok=True)   # create folders if missing
SRC = sys.argv[1] if len(sys.argv) > 1 else "data/Dataset_for_Dat__Analytics.xlsx"
df = pd.read_excel(SRC)
R = {}   # results dictionary used by report builder
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 12, "axes.titleweight": "bold", "figure.dpi": 130})
C1, C2, C3 = "#1f5f8b", "#e07b39", "#6b8e23"

# ---------- 1. Overview & quality ----------
R["rows"], R["cols"] = df.shape
R["date_min"], R["date_max"] = df.Date.min().date().isoformat(), df.Date.max().date().isoformat()
R["dup_rows"] = int(df.duplicated().sum()); R["dup_orderid"] = int(df.OrderID.duplicated().sum())
R["missing"] = {k: int(v) for k, v in df.isna().sum().items() if v}
R["total_mismatch"] = int((abs((df.Quantity*df.UnitPrice).round(2) - df.TotalPrice) > 0.011).sum())
R["n_customers"] = int(df.CustomerID.nunique())
vc = df.CustomerID.value_counts(); R["repeat_customers"] = int((vc > 1).sum())
R["total_value"] = float(df.TotalPrice.sum())

# ---------- 2. Descriptive statistics ----------
num = ["Quantity", "UnitPrice", "ItemsInCart", "TotalPrice"]
d = df[num].agg(["count", "mean", "median", "std", "min", "max", "skew"]).T
d["Q1"] = df[num].quantile(.25); d["Q3"] = df[num].quantile(.75)
d = d[["count", "mean", "median", "std", "min", "Q1", "Q3", "max", "skew"]]
d.round(2).to_csv("output/descriptive_statistics.csv"); R["desc"] = d
cats = ["Product", "OrderStatus", "PaymentMethod", "ReferralSource"]
cat_tabs = {}
for c in cats:
    t = df[c].value_counts().rename("count").to_frame(); t["percent"] = (t["count"]/len(df)*100)
    cat_tabs[c] = t; t.round(1).to_csv(f"output/count_{c}.csv")
cp = df.CouponCode.fillna("No coupon").value_counts().rename("count").to_frame(); cp["percent"] = cp["count"]/len(df)*100
cat_tabs["CouponCode"] = cp; R["cats"] = cat_tabs

# ---------- 3. Outliers (IQR and Z-score) ----------
out = []
for c in num:
    q1, q3 = df[c].quantile([.25, .75]); i = q3-q1; lo, hi = q1-1.5*i, q3+1.5*i
    z = (df[c]-df[c].mean())/df[c].std()
    out.append(dict(column=c, lower_fence=lo, upper_fence=hi, iqr_outliers=int(((df[c] < lo) | (df[c] > hi)).sum()),
                    z_outliers=int((z.abs() > 3).sum())))
out = pd.DataFrame(out); out.round(2).to_csv("output/outlier_summary.csv", index=False); R["out"] = out
hi_fence = float(out.loc[out.column == "TotalPrice", "upper_fence"].iloc[0])
hi_rows = df[df.TotalPrice > hi_fence].sort_values("TotalPrice", ascending=False)
hi_rows[["OrderID", "Date", "Product", "Quantity", "UnitPrice", "TotalPrice", "OrderStatus"]].to_csv("output/totalprice_outliers.csv", index=False)
R["hi_rows"] = hi_rows; R["hi_fence"] = hi_fence
R["hi_all_qty5"] = bool((hi_rows.Quantity == 5).all()); R["hi_min_unit"] = float(hi_rows.UnitPrice.min())
R["top10_share"] = float(df.TotalPrice.nlargest(int(len(df)*.1)).sum()/df.TotalPrice.sum())
R["tp_p"] = df.TotalPrice.quantile([.1, .9]).round(0).tolist()

# ---------- 4. Trends ----------
df["Month"] = df.Date.dt.to_period("M")
m = df.groupby("Month").agg(orders=("OrderID", "count"), revenue=("TotalPrice", "sum")); m.index = m.index.to_timestamp()
m.round(2).to_csv("output/monthly_trend.csv"); R["m"] = m
x = np.arange(len(m))
R["trend_orders"] = stats.linregress(x, m.orders); R["trend_rev"] = stats.linregress(x, m.revenue)
h1 = df[df.Date.dt.month <= 6]; g = h1.groupby(h1.Date.dt.year)
h1t = g.agg(orders=("OrderID", "count"), revenue=("TotalPrice", "sum"), aov_mean=("TotalPrice", "mean"), aov_median=("TotalPrice", "median"))
h1t.round(2).to_csv("output/h1_year_comparison.csv"); R["h1"] = h1t
a, b = h1[h1.Date.dt.year == 2023].TotalPrice, h1[h1.Date.dt.year == 2025].TotalPrice
R["aov_mw_p"] = float(stats.mannwhitneyu(a, b).pvalue); R["aov_t_p"] = float(stats.ttest_ind(a, b, equal_var=False).pvalue)
moy = df.groupby(df.Date.dt.month).size() / df.groupby(df.Date.dt.month).Date.apply(lambda s: s.dt.year.nunique())
R["moy"] = moy
dow = df.groupby(df.Date.dt.day_name()).size().reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
R["dow"] = dow; R["dow_p"] = float(stats.chisquare(dow)[1])

# ---------- 5. Segments, relationships, status ----------
prod = df.groupby("Product").agg(orders=("OrderID", "count"), units=("Quantity", "sum"), revenue=("TotalPrice", "sum"),
                                 mean_order=("TotalPrice", "mean"), median_order=("TotalPrice", "median")).sort_values("revenue", ascending=False)
prod.round(2).to_csv("output/product_summary.csv"); R["prod"] = prod
R["anova_prod_p"] = float(stats.f_oneway(*[x.TotalPrice for _, x in df.groupby("Product")]).pvalue)
R["anova_coupon_p"] = float(stats.f_oneway(*[x.TotalPrice for _, x in df.groupby(df.CouponCode.fillna("None"))]).pvalue)
R["chi_prod_uniform_p"] = float(stats.chisquare(df.Product.value_counts())[1])
st = df.groupby("OrderStatus").agg(orders=("OrderID", "count"), value=("TotalPrice", "sum")); st["pct_orders"] = st.orders/len(df)*100
st.round(2).to_csv("output/status_summary.csv"); R["st"] = st
bad = df.OrderStatus.isin(["Cancelled", "Returned"])
R["bad_n"], R["bad_pct"], R["bad_val"], R["bad_val_pct"] = int(bad.sum()), float(bad.mean()*100), float(df[bad].TotalPrice.sum()), float(df[bad].TotalPrice.sum()/df.TotalPrice.sum()*100)
R["chi_ref_status_p"] = float(stats.chi2_contingency(pd.crosstab(df.ReferralSource, df.OrderStatus))[1])
R["chi_ref_bad_p"] = float(stats.chi2_contingency(pd.crosstab(df.ReferralSource, bad))[1])
R["chi_pay_status_p"] = float(stats.chi2_contingency(pd.crosstab(df.PaymentMethod, df.OrderStatus))[1])
R["chi_prod_status_p"] = float(stats.chi2_contingency(pd.crosstab(df.Product, df.OrderStatus))[1])
corr = df[num].corr(); corr.round(3).to_csv("output/correlation_pearson.csv"); R["corr"] = corr
R["spearman"] = df[num].corr(method="spearman")
kw = lambda col: float(stats.kruskal(*[x.TotalPrice for _, x in df.groupby(col)]).pvalue)
R["kw"] = {"Product": kw("Product"), "Coupon": kw(df.CouponCode.fillna("None")), "PaymentMethod": kw("PaymentMethod"), "ReferralSource": kw("ReferralSource")}
R["lost_p"] = {c: float(stats.chi2_contingency(pd.crosstab(df[c], bad))[1]) for c in ["Product", "PaymentMethod", "ReferralSource"]}
R["lost_p"]["Coupon"] = float(stats.chi2_contingency(pd.crosstab(df.CouponCode.fillna("None"), bad))[1])
R["qty5_share"] = float((df.Quantity == 5).mean()*100)

# ---------- 6. Charts ----------
fig, ax = plt.subplots(2, 2, figsize=(9, 6))
for a_, c, col in zip(ax.ravel(), num, [C1, C2, C3, C1]):
    a_.hist(df[c], bins=20 if c != "Quantity" else np.arange(0.5, 6.5, 1), color=col, edgecolor="white", alpha=.9)
    a_.axvline(df[c].mean(), color="black", ls="--", lw=1.2, label=f"mean {df[c].mean():.1f}")
    a_.axvline(df[c].median(), color="red", ls=":", lw=1.5, label=f"median {df[c].median():.1f}")
    a_.set_title(f"{c} (skew {df[c].skew():.2f})"); a_.legend(fontsize=7, frameon=False)
fig.suptitle("Distribution of numeric columns", fontweight="bold"); fig.tight_layout(); fig.savefig("charts/1_distributions.png"); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(9, 3.8))
ax[0].boxplot(df.TotalPrice, orientation="horizontal", flierprops=dict(marker="o", markerfacecolor="red", markeredgecolor="red", ms=4), patch_artist=True, boxprops=dict(facecolor="#cfe3f1"))
ax[0].axvline(hi_fence, color="red", ls="--", lw=1); ax[0].set_title("TotalPrice boxplot"); ax[0].set_yticks([]); ax[0].set_xlabel("TotalPrice")
ax[0].text(hi_fence, 1.28, f"upper fence {hi_fence:,.0f}", color="red", fontsize=7, ha="right")
order = prod.index.tolist()
ax[1].boxplot([df[df.Product == p].TotalPrice for p in order], tick_labels=order, flierprops=dict(marker="o", markerfacecolor="red", markeredgecolor="red", ms=3))
ax[1].set_title("TotalPrice by product"); ax[1].tick_params(axis="x", rotation=45)
fig.tight_layout(); fig.savefig("charts/2_boxplots.png"); plt.close()

fig, ax = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True)
ax[0].plot(m.index, m.orders, marker="o", ms=3, color=C1); ax[0].plot(m.index, m.orders.rolling(3).mean(), color=C2, lw=2, label="3-month average")
ax[0].set_title("Orders per month"); ax[0].legend(frameon=False, fontsize=8)
ax[1].plot(m.index, m.revenue, marker="o", ms=3, color=C3); ax[1].plot(m.index, m.revenue.rolling(3).mean(), color=C2, lw=2)
ax[1].set_title("Order value (TotalPrice) per month"); fig.tight_layout(); fig.savefig("charts/3_monthly_trend.png"); plt.close()

fig, ax = plt.subplots(1, 3, figsize=(9, 3.2))
for a_, col, t, c in zip(ax, ["orders", "revenue", "aov_mean"], ["Orders (Jan-Jun)", "Order value (Jan-Jun)", "Mean order value (Jan-Jun)"], [C1, C3, C2]):
    bars = a_.bar([str(i) for i in h1t.index], h1t[col], color=c)
    a_.set_title(t, fontsize=10); a_.bar_label(bars, fmt="%.0f", fontsize=8)
fig.tight_layout(); fig.savefig("charts/4_h1_comparison.png"); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].barh(prod.index[::-1], prod.revenue[::-1], color=C1); ax[0].set_title("Order value by product")
stc = st.sort_values("orders"); ax[1].barh(stc.index, stc.orders, color=[C2 if i in ("Cancelled", "Returned") else C1 for i in stc.index])
ax[1].set_title("Orders by status (orange = lost)"); ax[1].bar_label(ax[1].containers[0], fontsize=8)
fig.tight_layout(); fig.savefig("charts/5_product_status.png"); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(9, 3.9))
im = ax[0].imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1); ax[0].set_xticks(range(4)); ax[0].set_yticks(range(4))
ax[0].set_xticklabels(num, rotation=45, ha="right", fontsize=8); ax[0].set_yticklabels(num, fontsize=8)
for i in range(4):
    for j in range(4): ax[0].text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center", fontsize=8)
ax[0].set_title("Pearson correlation"); fig.colorbar(im, ax=ax[0], fraction=.046)
ax[1].scatter(df.UnitPrice, df.TotalPrice, c=df.Quantity, cmap="viridis", s=8, alpha=.7); ax[1].set_xlabel("UnitPrice"); ax[1].set_ylabel("TotalPrice")
ax[1].set_title("UnitPrice vs TotalPrice (colour = Quantity)")
fig.tight_layout(); fig.savefig("charts/6_correlation.png"); plt.close()

pd.to_pickle(R, "output/R.pkl")
print("done"); print(json.dumps({k: v for k, v in R.items() if isinstance(v, (int, float, str, bool))}, indent=1, default=str))
