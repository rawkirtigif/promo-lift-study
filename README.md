# The discount isn't the whole deal

**A promotional lift study on public grocery sales data**

👉 **[View the project](https://rawkirtigif.github.io/promo-lift-study/)**

I analyzed a public dunnhumby grocery sales and promotion dataset covering 156 weeks, 55 products and 77 stores, to see how different promotion strategies relate to unit sales.

## Key findings

| | Lift vs a normal week |
|---|---|
| Price cut only | +25% |
| Display only | +68% |
| Feature only (weekly ad) | +175% |
| Feature and display | +314% |

- At matched discounts of about 20.5% off (918 store and product pairs), feature and display still lifted sales +237% compared with +29% for a price cut alone.
- A price cut would need a 94% gross margin just to cover its own discount, so price-only events were the weakest use of promo budget.
- Heavy promo weeks weren't simply busy weeks. Unpromoted products sold at their normal pace in those weeks, and adjusting the baseline week by week barely changed the results.
- This is observational, so it shows a strong pattern rather than proof. The next step would be a controlled store test.

## What's in this repo

| File | What it is |
|---|---|
| `index.html` | The project page (published with GitHub Pages) |
| `Promo_Lift_Scorecard_Analysis.xlsx` | Excel workbook with live formulas, pivot-ready data and a README tab |
| `analysis/promo_lift_analysis.py` | Python script that rebuilds every number on the page from the raw data |

## Run it yourself

1. Download "Breakfast at the Frat" for free from [dunnhumby Source Files](https://www.dunnhumby.com/source-files/).
2. Put `dunnhumby - Breakfast at the Frat.xlsx` in `analysis/data/`.
3. Run:
   ```
   pip install pandas numpy openpyxl
   python analysis/promo_lift_analysis.py
   ```

The raw data isn't included here because it belongs to dunnhumby and is shared through their site.

## Methods in brief

- **Lift** compares each promoted week with the average unpromoted week for the same product in the same store.
- **Required margin to cover discount cost** is a modeled threshold, not realized profit, since the data has no real margins.
- **Price elasticity** uses a log-log regression within each store and product on price-only weeks, with standard errors clustered by store and product.
- **Limits.** No adjustment for cannibalization or stock-up buying, and display fees, ad costs and labor aren't in the data.

## Tools

Python (pandas, NumPy), Excel (SUMIFS, pivot-ready modeling), HTML and CSS

---

Made by **Kirti Rawat** | [LinkedIn](https://www.linkedin.com/in/rawatkirtik) | rawat.ki@northeastern.edu
