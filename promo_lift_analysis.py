"""
Promotional lift study: reproduces every number on the project page.

Data: dunnhumby "Breakfast at the Frat" (free from dunnhumby.com/sourcefiles).
Put "dunnhumby - Breakfast at the Frat.xlsx" in a folder called data/ next to this script, then run:
    python promo_lift_analysis.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data" / "dunnhumby - Breakfast at the Frat.xlsx"
MIN_BASE_WEEKS = 8  # store-product pairs need at least this many unpromoted weeks

# 1. Load
tx = pd.read_excel(DATA, sheet_name="dh Transaction Data", header=1)
prod = pd.read_excel(DATA, sheet_name="dh Products Lookup", header=1)
store = pd.read_excel(DATA, sheet_name="dh Store Lookup", header=1).drop_duplicates("STORE_ID")
raw_rows = len(tx)
tx = tx.dropna(subset=["PRICE", "BASE_PRICE"])
missing = raw_rows - len(tx)

# 2. Promo type (mutually exclusive)
f, d, tpr = tx.FEATURE, tx.DISPLAY, tx.TPR_ONLY
tx["PROMO"] = np.select(
    [(f == 1) & (d == 1), f == 1, d == 1, tpr == 1],
    ["Feature and display", "Feature only", "Display only", "Price cut only"],
    "No promotion",
)

# 3. Baseline: average weekly units in the same store and product's unpromoted weeks
base = (tx[tx.PROMO == "No promotion"].groupby(["STORE_NUM", "UPC"]).UNITS
        .agg(BASE_UNITS="mean", BASE_WEEKS="size"))
tx = tx.join(base, on=["STORE_NUM", "UPC"])
dropped = int((tx.BASE_WEEKS.fillna(0) < MIN_BASE_WEEKS).sum())
tx = tx[tx.BASE_WEEKS >= MIN_BASE_WEEKS].copy()
tx["DISC_PCT"] = ((tx.BASE_PRICE - tx.PRICE) / tx.BASE_PRICE).clip(lower=0)
tx["DISC_DOLLARS"] = (tx.BASE_PRICE - tx.PRICE).clip(lower=0) * tx.UNITS
tx["UNITS_X_BASE"] = tx.UNITS * tx.BASE_PRICE
tx["BASE_X_BASE"] = tx.BASE_UNITS * tx.BASE_PRICE
tx = (tx.merge(prod[["UPC", "CATEGORY", "MANUFACTURER"]], on="UPC", how="left")
        .merge(store[["STORE_ID", "SEG_VALUE_NAME"]], left_on="STORE_NUM", right_on="STORE_ID", how="left"))
print(f"Rows: {raw_rows:,} raw, {missing} missing a price, {dropped} without {MIN_BASE_WEEKS} baseline weeks, {len(tx):,} kept")

promo = tx[tx.PROMO != "No promotion"]

def pooled(g):
    return pd.Series({
        "store_weeks": len(g),
        "lift": g.UNITS.sum() / g.BASE_UNITS.sum() - 1,
        "avg_discount": g.DISC_PCT.mean(),
        # modeled threshold: margin needed for incremental units to cover the discount
        "required_margin": g.DISC_DOLLARS.sum() / (g.UNITS_X_BASE.sum() - g.BASE_X_BASE.sum()),
    })

# 4. Headline results by promo type
by_type = promo.groupby("PROMO").apply(pooled)
print("\nBy promo type\n", by_type.round(3))

# 5. Variation across store-product pairs (pairs with 4+ promoted weeks)
pair = promo.groupby(["PROMO", "STORE_NUM", "UPC"]).agg(u=("UNITS", "sum"), b=("BASE_UNITS", "sum"), w=("UNITS", "size"))
pair = pair[pair.w >= 4]
pair["lift"] = pair.u / pair.b - 1
print("\nStore-product lift spread\n", pair.groupby("PROMO").lift.quantile([.25, .5, .75]).unstack().round(2))

# 6. Matched comparison: same store and product, average discounts within 3 points
agg = promo.groupby(["STORE_NUM", "UPC", "PROMO"]).agg(u=("UNITS", "sum"), b=("BASE_UNITS", "sum"), disc=("DISC_PCT", "mean"), w=("UNITS", "size")).reset_index()
pc = agg[agg.PROMO == "Price cut only"].set_index(["STORE_NUM", "UPC"])
fd = agg[agg.PROMO == "Feature and display"].set_index(["STORE_NUM", "UPC"])
m = pc.join(fd, lsuffix="_pc", rsuffix="_fd", how="inner")
m = m[(m.disc_pc - m.disc_fd).abs() <= 0.03]
print(f"\nMatched pairs: {len(m)}  price cut lift {m.u_pc.sum()/m.b_pc.sum()-1:+.0%}  feature and display lift {m.u_fd.sum()/m.b_fd.sum()-1:+.0%}  avg discount {m.disc_pc.mean():.1%}")

# 7. Discount bands (by each store-product's average discount for that promo type)
agg["band"] = pd.cut(agg.disc, [-.001, .10, .20, .30, 1], labels=["under 10%", "10 to 20%", "20 to 30%", "30%+"])
bands = agg.groupby(["band", "PROMO"], observed=True).apply(lambda g: g.u.sum() / g.b.sum() - 1).unstack()
print("\nLift by discount band\n", bands.round(2))

# 8. By category
print("\nLift by category\n", promo.groupby(["CATEGORY", "PROMO"]).apply(lambda g: g.UNITS.sum() / g.BASE_UNITS.sum() - 1).unstack().round(2))

# 9. Illustrative dollars at assumed margins (thousands of dollars)
for margin in (0.25, 0.35, 0.45):
    net = promo.groupby("PROMO").apply(lambda g: margin * (g.UNITS_X_BASE.sum() - g.BASE_X_BASE.sum()) - g.DISC_DOLLARS.sum()) / 1000
    print(f"\nNet at {margin:.0%} margin ($k)\n", net.round(0))

# 10. Timing check: were heavy promo weeks just busy weeks?
weekly = tx.groupby("WEEK_END_DATE").apply(lambda g: pd.Series({
    "fd_share": (g.PROMO == "Feature and display").mean(),
    "unpromoted_index": g.loc[g.PROMO == "No promotion", "UNITS"].sum() / g.loc[g.PROMO == "No promotion", "BASE_UNITS"].sum(),
}))
print(f"\nCorrelation, feature and display share vs unpromoted sales index: {weekly.fd_share.corr(weekly.unpromoted_index):.2f}")
cwi = (tx[tx.PROMO == "No promotion"].groupby(["CATEGORY", "WEEK_END_DATE"])
       .apply(lambda g: g.UNITS.sum() / g.BASE_UNITS.sum()).rename("week_index"))
adj = promo.join(cwi, on=["CATEGORY", "WEEK_END_DATE"])
print("Week-adjusted lift\n", adj.groupby("PROMO").apply(lambda g: g.UNITS.sum() / (g.BASE_UNITS * g.week_index).sum() - 1).round(3))

# 11. Price elasticity: log-log within store-product, price-only weeks, SEs clustered by store-product
e = tx[(tx.FEATURE == 0) & (tx.DISPLAY == 0) & (tx.UNITS > 0) & (tx.PRICE > 0)].copy()
e["pair"] = e.STORE_NUM.astype(str) + "_" + e.UPC.astype(str)
e["lu"], e["lp"] = np.log(e.UNITS), np.log(e.PRICE)
for c in ("lu", "lp"):
    e[c + "_d"] = e[c] - e.groupby("pair")[c].transform("mean")
print("\nElasticity (95% range) and model-implied change from a 10% price cut")
for cat, x in e.groupby("CATEGORY"):
    sxx = (x.lp_d ** 2).sum()
    beta = (x.lp_d * x.lu_d).sum() / sxx
    score = (x.lp_d * (x.lu_d - beta * x.lp_d)).groupby(x.pair).sum()
    G = len(score)
    se = np.sqrt((score ** 2).sum() / sxx ** 2 * G / (G - 1))
    print(f"  {cat:24s} {beta:.2f} ({beta-1.96*se:.2f} to {beta+1.96*se:.2f})  10% cut: {0.9**beta-1:+.1%}")
