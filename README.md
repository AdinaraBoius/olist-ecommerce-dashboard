# Proyek Analisis Data: Brazilian E-Commerce Public Dataset (Olist)

## Deskripsi Proyek
Dashboard interaktif dan analisis data transaksi e-commerce Olist Brasil periode 2016–2018, mencakup analisis tren revenue, performa pengiriman, kepuasan pelanggan, dan segmentasi pelanggan menggunakan RFM Analysis.

## Struktur Direktori
```
submission
├── dashboard
│   ├── dashboard.py
│   └── main_data.csv
├── data
│   ├── customers_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── orders_dataset.csv
│   ├── product_category_name_translation.csv
│   ├── products_dataset.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment

```bash
pip install -r requirements.txt
```

## Menjalankan Dashboard

```bash
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka otomatis di browser pada alamat `http://localhost:8501`.
