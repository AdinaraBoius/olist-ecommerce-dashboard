import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import streamlit as st
from matplotlib.patches import Patch

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Olist E-Commerce Dashboard",
    page_icon="🛒",
    layout="wide"
)

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard/main_data.csv")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
    df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])
    return df

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.title("🔍 Filter Data")

min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()

start_date, end_date = st.sidebar.date_input(
    "Rentang Tanggal Order",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

all_states = sorted(df["customer_state"].unique())
selected_states = st.sidebar.multiselect(
    "Filter State",
    options=all_states,
    default=all_states
)

mask = (
    (df["order_purchase_timestamp"].dt.date >= start_date) &
    (df["order_purchase_timestamp"].dt.date <= end_date) &
    (df["customer_state"].isin(selected_states))
)
filtered_df = df[mask].copy()

# ── Header ────────────────────────────────────────────────────
st.title("🛒 Olist E-Commerce Dashboard")
st.caption("Analisis data transaksi Olist Brasil, 2016–2018")

# ── KPI Metrics ───────────────────────────────────────────────
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

total_revenue = filtered_df["price"].sum()
total_orders  = filtered_df["order_id"].nunique()
avg_review    = filtered_df["review_score"].mean()
late_pct      = filtered_df["is_late"].mean() * 100

col1.metric("💰 Total Revenue",        f"R${total_revenue:,.0f}")
col2.metric("📦 Total Order",          f"{total_orders:,}")
col3.metric("⭐ Avg Review Score",     f"{avg_review:.2f}")
col4.metric("⏰ Tingkat Keterlambatan", f"{late_pct:.1f}%")

st.markdown("---")

# ══════════════════════════════════════════════════════════════
# Q1 — Revenue Trend & Top Categories
# ══════════════════════════════════════════════════════════════
st.subheader("📈 Q1: Tren Revenue Bulanan & Kategori Produk Teratas")

q1_df = filtered_df[
    (filtered_df["order_purchase_timestamp"].dt.year >= 2017) &
    (filtered_df["order_purchase_timestamp"].dt.year <= 2018)
].copy()
q1_df["year_month"] = q1_df["order_purchase_timestamp"].dt.to_period("M")

monthly_rev = (
    q1_df.groupby("year_month")["price"]
    .sum()
    .reset_index()
    .rename(columns={"price": "total_revenue"})
    .sort_values("year_month")
)
monthly_rev["year_month_str"] = monthly_rev["year_month"].astype(str)

category_rev = (
    q1_df.groupby("product_category_name_english")["price"]
    .sum()
    .reset_index()
    .rename(columns={"price": "total_revenue"})
    .sort_values("total_revenue", ascending=False)
    .head(10)
)

# Chart 1a: Line chart revenue bulanan
fig, ax = plt.subplots(figsize=(14, 4))
x = monthly_rev["year_month_str"]
y = monthly_rev["total_revenue"]
ax.plot(x, y, marker='o', linewidth=2, color='steelblue', markersize=5)

if "2017-11" in monthly_rev["year_month_str"].values:
    nov_idx = list(monthly_rev["year_month_str"]).index("2017-11")
    nov_val = y.iloc[nov_idx]
    ax.plot(x.iloc[nov_idx], nov_val, 'o', color='crimson', markersize=10, zorder=5)
    ax.annotate(
        f"Black Friday\nR${nov_val:,.0f}",
        xy=(nov_idx, nov_val),
        xytext=(nov_idx - 2.5, nov_val - 100000),
        arrowprops=dict(arrowstyle="->", color="crimson"),
        fontsize=9, color="crimson"
    )

ax.set_title("Tren Revenue Bulanan (2017-2018)", fontweight='bold')
ax.set_xlabel("Bulan")
ax.set_ylabel("Total Revenue")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
ax.set_xticks(range(len(x)))
ax.set_xticklabels(x, rotation=45, ha='right', fontsize=8)
ax.grid(axis='y', alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close()

# Tabel ringkasan bulanan
with st.expander("📋 Lihat Tabel Revenue Bulanan"):
    tbl = monthly_rev[["year_month_str", "total_revenue"]].copy()
    tbl.columns = ["Bulan", "Total Revenue"]
    tbl["Total Revenue"] = tbl["Total Revenue"].apply(lambda v: f"R${v:,.0f}")
    st.dataframe(tbl.set_index("Bulan"), use_container_width=True)

# Chart 1b: Horizontal bar kategori
fig, ax = plt.subplots(figsize=(14, 5))
cat_sorted = category_rev.sort_values("total_revenue", ascending=True)
ax.barh(cat_sorted["product_category_name_english"],
        cat_sorted["total_revenue"], color='steelblue')
ax.set_title("Top 10 Kategori Produk berdasarkan Revenue", fontweight='bold')
ax.set_xlabel("Total Revenue")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
ax.grid(axis='x', alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close()

st.markdown("---")

# ══════════════════════════════════════════════════════════════
# Q2 — Late Delivery by State
# ══════════════════════════════════════════════════════════════
st.subheader("🗺️ Q2: Keterlambatan Pengiriman per State")

late_state = (
    filtered_df.groupby("customer_state")["is_late"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "late_orders", "count": "total_orders"})
    .reset_index()
)
late_state["late_pct"] = (late_state["late_orders"] / late_state["total_orders"] * 100).round(2)
late_state = late_state.sort_values("late_pct", ascending=True)

nordeste_top5 = {"AL", "MA", "PI", "CE", "SE"}
colors_state = [
    "crimson" if s in nordeste_top5 else "steelblue"
    for s in late_state["customer_state"]
]

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(late_state["customer_state"], late_state["late_pct"], color=colors_state)
for bar, val in zip(bars, late_state["late_pct"]):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va='center', fontsize=8)

legend_elements = [
    Patch(facecolor='crimson',   label='Wilayah Nordeste (5 teratas)'),
    Patch(facecolor='steelblue', label='State lainnya')
]
ax.legend(handles=legend_elements, loc='lower right')
ax.set_title("Persentase Keterlambatan Pengiriman per State (2016-2018)", fontweight='bold')
ax.set_xlabel("Persentase Order Terlambat (%)")
ax.set_xlim(0, late_state["late_pct"].max() + 5)
ax.grid(axis='x', alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close()

# Tabel detail per state
with st.expander("📋 Lihat Tabel Detail per State"):
    tbl2 = late_state[["customer_state", "late_orders", "total_orders", "late_pct"]].copy()
    tbl2.columns = ["State", "Order Terlambat", "Total Order", "Keterlambatan (%)"]
    tbl2 = tbl2.sort_values("Keterlambatan (%)", ascending=False)
    st.dataframe(tbl2.set_index("State"), use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════
# Q3 — Review Score vs Delivery
# ══════════════════════════════════════════════════════════════
st.subheader("⭐ Q3: Ketepatan Pengiriman & Review Score")

review_df = filtered_df.dropna(subset=["review_score"]).copy()
review_df["is_late_label"] = review_df["is_late"].map({0: "Tepat Waktu", 1: "Terlambat"})

score_dist = (
    review_df.groupby(["is_late_label", "review_score"])
    .size()
    .reset_index(name="count")
)

fig, ax = plt.subplots(figsize=(12, 5))
scores = [1, 2, 3, 4, 5]
on_time = score_dist[score_dist["is_late_label"] == "Tepat Waktu"].set_index("review_score")["count"]
late    = score_dist[score_dist["is_late_label"] == "Terlambat"].set_index("review_score")["count"]

x = np.arange(len(scores))
width = 0.35
ax.bar(x - width/2, [on_time.get(s, 0) for s in scores], width,
       label="Tepat Waktu", color="steelblue")
ax.bar(x + width/2, [late.get(s, 0) for s in scores], width,
       label="Terlambat", color="tomato")

ax.set_title("Distribusi Review Score: Tepat Waktu vs Terlambat", fontweight='bold')
ax.set_xlabel("Review Score")
ax.set_ylabel("Jumlah Order")
ax.set_xticks(x)
ax.set_xticklabels([f"Score {s}" for s in scores])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.legend()
ax.grid(axis='y', alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close()

# Tabel ringkasan review
summary = (
    review_df.groupby("is_late_label")["review_score"]
    .agg(["mean", "median", "count"])
    .reset_index()
    .rename(columns={
        "is_late_label": "Status Pengiriman",
        "mean":   "Rata-rata Score",
        "median": "Median Score",
        "count":  "Total Order"
    })
)
summary["Rata-rata Score"] = summary["Rata-rata Score"].round(2)
st.dataframe(summary.set_index("Status Pengiriman"), use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════
# Q4 — New vs Repeat + RFM
# ══════════════════════════════════════════════════════════════
st.subheader("👥 Q4: New vs Repeat Customers & RFM Segmentation")

customer_df = (
    filtered_df.groupby("customer_unique_id")
    .agg(order_count=("order_id", "nunique"), total_revenue=("price", "sum"))
    .reset_index()
)
customer_df["customer_type"] = customer_df["order_count"].apply(
    lambda x: "Repeat" if x > 1 else "New"
)
type_summary = (
    customer_df.groupby("customer_type")
    .agg(total_customers=("customer_unique_id", "count"),
         total_revenue=("total_revenue", "sum"))
    .reset_index()
)
type_summary["customer_pct"] = (
    type_summary["total_customers"] / type_summary["total_customers"].sum() * 100
).round(2)
type_summary["revenue_pct"] = (
    type_summary["total_revenue"] / type_summary["total_revenue"].sum() * 100
).round(2)

# Chart Q4a: Stacked bar
fig, ax = plt.subplots(figsize=(10, 5))
categories = ["Jumlah Pelanggan", "Kontribusi Revenue"]
new_vals    = [
    type_summary[type_summary["customer_type"] == "New"]["customer_pct"].values[0],
    type_summary[type_summary["customer_type"] == "New"]["revenue_pct"].values[0],
]
repeat_vals = [
    type_summary[type_summary["customer_type"] == "Repeat"]["customer_pct"].values[0],
    type_summary[type_summary["customer_type"] == "Repeat"]["revenue_pct"].values[0],
]
x = np.arange(len(categories))
ax.bar(x, new_vals,    0.5, label="New Customers",    color="steelblue")
ax.bar(x, repeat_vals, 0.5, bottom=new_vals,          label="Repeat Customers", color="tomato")
for i, (n, r) in enumerate(zip(new_vals, repeat_vals)):
    ax.text(i, n / 2,     f"{n:.1f}%", ha='center', va='center',
            fontsize=12, fontweight='bold', color='black')
    ax.text(i, n + r / 2, f"{r:.1f}%", ha='center', va='center',
            fontsize=12, fontweight='bold', color='black')
ax.set_title("Perbandingan New vs Repeat Customers", fontweight='bold')
ax.set_ylabel("Persentase (%)")
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylim(0, 110)
ax.legend()
ax.grid(axis='y', alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close()

# Chart Q4b: RFM revenue per segmen
rfm_summary = (
    filtered_df.dropna(subset=["Segment"])
    .groupby("Segment")
    .agg(
        total_customers=("customer_unique_id", "nunique"),
        total_revenue=("Monetary", "sum"),
        avg_recency=("Recency", "mean"),
        avg_monetary=("Monetary", "mean"),
    )
    .round(1)
    .reset_index()
    .sort_values("total_revenue", ascending=True)
)

segment_colors = {
    "Champions":      "#2ecc71",
    "Promising":      "#3498db",
    "Needs Attention":"#f39c12",
    "At Risk":        "#e67e22",
    "Lost":           "#e74c3c",
}

fig, ax = plt.subplots(figsize=(12, 5))
colors = [segment_colors.get(s, "gray") for s in rfm_summary["Segment"]]
bars = ax.barh(rfm_summary["Segment"], rfm_summary["total_revenue"], color=colors)
for bar, val in zip(bars, rfm_summary["total_revenue"]):
    ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
            f"R${val:,.0f}", va='center', ha='center',
            fontsize=9, fontweight='bold', color='white')
ax.set_title("Total Revenue per Segmen RFM", fontweight='bold')
ax.set_xlabel("Total Revenue")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v:,.0f}"))
ax.grid(axis='x', alpha=0.4)
plt.tight_layout()
st.pyplot(fig)
plt.close()

# Tabel RFM detail
with st.expander("📋 Lihat Tabel Detail Segmen RFM"):
    tbl3 = rfm_summary.copy()
    tbl3.columns = ["Segmen", "Total Pelanggan", "Total Revenue", "Avg Recency (hari)", "Avg Monetary"]
    tbl3["Total Revenue"]  = tbl3["Total Revenue"].apply(lambda v: f"R${v:,.0f}")
    tbl3["Avg Monetary"]   = tbl3["Avg Monetary"].apply(lambda v: f"R${v:,.2f}")
    tbl3 = tbl3.sort_values("Total Pelanggan", ascending=False)
    st.dataframe(tbl3.set_index("Segmen"), use_container_width=True)

st.markdown("---")
st.caption("Dashboard dibuat sebagai bagian dari Proyek Analisis Data | Dataset: Brazilian E-Commerce Public Dataset by Olist")